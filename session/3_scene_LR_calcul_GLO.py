# -*- coding: utf-8 -*-
"""
Mini-projet : SVF et flux grandes longueurs d'onde sur une scene urbaine.

Le script est volontairement decoupe en deux parties :
1. calculer le Sky View Factor de chaque maille a partir des facteurs de forme ;
2. imposer des temperatures de surface sur 24 h et calculer les flux GLO.

Hypotheses principales
----------------------
- La matrice F suit la convention de pyviewfactor :
  F[j, i] est le facteur de forme de la maille i vers la maille j.
- Le ciel est le complement de fermeture :
  SVF_i = F_i->sky = 1 - sum_j(F_i->j).
- Les temperatures de surface sont estimees avec un modele 1R1C simple par
  cellule : convection avec l'air, absorption solaire calculee avec pvlib,
  echange GLO avec le ciel et conduction vers une couche profonde simplifiee.
- La temperature radiative du ciel est approximee par T_sky = T_air - 15 degC.
"""

from pathlib import Path
import csv
from datetime import datetime, timezone, timedelta

import numpy as np
import pandas as pd
import pvlib
import pyvista as pv
import pyviewfactor as pvf


# =============================================================================
# Parametres utilisateur
# =============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "src_data"

MESH_FILE = DATA_DIR / "scene_LR_oriented_normals.vtk"
EPW_FILE = DATA_DIR / "FRA_AR_Lyon-Bron.AP.074800_TMYx.epw"

OUTPUT_DIR = SCRIPT_DIR / "output"
OUTPUT_ALL_FIELDS_FILE = OUTPUT_DIR / "scene_LR_GLO_18mai_Lyon_all_fields.vtk"
OUTPUT_TIMESERIES_DIR = OUTPUT_DIR / "scene_LR_GLO_18mai_Lyon_steps"
OUTPUT_TIMESERIES_FILE = OUTPUT_DIR / "scene_LR_GLO_18mai_Lyon.pvd"

MONTH = 5
DAY = 18

STRICT_VISIBILITY = False
STRICT_OBSTRUCTION = False
ROUNDING_DECIMAL = 5
EPSILON_INTEGRATION = 1e-3

SIGMA = 5.670374419e-8

# Proprietes simplifiees pour le modele thermique de surface.
# thickness_m represente une epaisseur active, pas forcement toute l'epaisseur
# constructive. Les valeurs sont des ordres de grandeur pedagogiques.
MATERIALS = {
    "ground": {
        "name": "asphalte / sol mineral",
        "conductivity_W_mK": 1.2,
        "density_kg_m3": 2100.0,
        "specific_heat_J_kgK": 920.0,
        "thickness_m": 0.08,
        "emissivity": 0.95,
        "solar_absorptivity": 0.85,
    },
    "facade": {
        "name": "beton / enduit clair",
        "conductivity_W_mK": 1.4,
        "density_kg_m3": 2200.0,
        "specific_heat_J_kgK": 880.0,
        "thickness_m": 0.12,
        "emissivity": 0.92,
        "solar_absorptivity": 0.55,
    },
    "roof": {
        "name": "membrane bitumineuse",
        "conductivity_W_mK": 0.8,
        "density_kg_m3": 1800.0,
        "specific_heat_J_kgK": 1000.0,
        "thickness_m": 0.06,
        "emissivity": 0.94,
        "solar_absorptivity": 0.80,
    },
}
MATERIALS["other"] = MATERIALS["facade"]

SURFACE_HEAT_TRANSFER_COEFF_W_M2K = 8.0
TIME_STEP_SECONDS = 3600.0
GROUND_ALBEDO = 0.20

# Orientation geographique de la geometrie.
# Par defaut : x = Est, y = Nord. Modifier cette valeur si la scene doit etre
# tournee par rapport au nord geographique.
SCENE_AZIMUTH_OFFSET_DEG = 0.0

# Affichage interactif. Mettre False si le script est lance en batch.
SHOW_SVF_PLOT = True
SHOW_FLUX_PLOT = True
PLOT_FLUX_HOUR = 14


def print_section(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def print_stats(label, values, unit=""):
    values = np.asarray(values, dtype=float)
    suffix = f" {unit}" if unit else ""
    print(
        f"  {label:<28} "
        f"min={values.min():8.3f}{suffix} | "
        f"mean={values.mean():8.3f}{suffix} | "
        f"max={values.max():8.3f}{suffix}"
    )


# =============================================================================
# Lecture meteo EPW
# =============================================================================

def read_epw_location(epw_file):
    with open(epw_file, newline="", encoding="utf-8", errors="replace") as f:
        row = next(csv.reader(f))

    if row[0] != "LOCATION":
        raise ValueError(f"{epw_file} ne commence pas par une ligne LOCATION EPW.")

    return {
        "name": row[1],
        "latitude": float(row[6]),
        "longitude": float(row[7]),
        "timezone": float(row[8]),
        "altitude": float(row[9]),
    }


def read_epw_day(epw_file, month, day):
    """Return hourly weather data for one EPW day."""
    print_section("Lecture du fichier meteo EPW")
    print(f"Fichier : {epw_file}")
    print(f"Jour selectionne : {day:02d}/{month:02d}")

    location = read_epw_location(epw_file)
    print(
        "Station : "
        f"{location['name']} | lat={location['latitude']:.4f} | "
        f"lon={location['longitude']:.4f} | UTC{location['timezone']:+.1f}"
    )

    tzinfo = timezone(timedelta(hours=location["timezone"]))
    records = []

    with open(epw_file, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)

        for _ in range(8):
            next(reader)

        for row in reader:
            row_month = int(row[1])
            row_day = int(row[2])

            if row_month != month or row_day != day:
                continue

            epw_hour = int(row[3])  # EPW hours are 1..24, end of interval.
            hour = epw_hour - 1
            year = int(row[0])

            records.append({
                "hour": hour,
                "time": datetime(year, month, day, hour, 30, tzinfo=tzinfo),
                "tair_c": float(row[6]),
                "ghi": float(row[13]),
                "dni": float(row[14]),
                "dhi": float(row[15]),
            })

    if len(records) != 24:
        raise ValueError(
            f"{epw_file} : {len(records)} lignes trouvees pour "
            f"{day:02d}/{month:02d}, 24 attendues."
        )

    records.sort(key=lambda item: item["hour"])

    hours = np.array([r["hour"] for r in records], dtype=int)
    times = pd.DatetimeIndex([r["time"] for r in records])
    tair_c = np.array([r["tair_c"] for r in records], dtype=float)
    ghi = np.array([r["ghi"] for r in records], dtype=float)
    dni = np.array([r["dni"] for r in records], dtype=float)
    dhi = np.array([r["dhi"] for r in records], dtype=float)

    print(f"Nombre de pas horaires : {len(records)}")
    print_stats("Tair", tair_c, "degC")
    print_stats("GHI", ghi, "W/m2")
    print_stats("DNI", dni, "W/m2")
    print_stats("DHI", dhi, "W/m2")

    return location, hours, times, tair_c, ghi, dni, dhi


# =============================================================================
# Classification geometrique
# =============================================================================

def load_scene(mesh_file):
    print_section("Chargement et preparation de la geometrie")
    print(f"Fichier : {mesh_file}")

    mesh = pv.read(mesh_file)
    mesh = mesh.extract_surface().triangulate()
    mesh = mesh.compute_normals(
        cell_normals=True,
        point_normals=False,
        auto_orient_normals=False,
        inplace=False,
    )

    print(f"Nombre de points : {mesh.n_points}")
    print(f"Nombre de faces  : {mesh.n_cells}")
    print(f"Bornes           : {tuple(round(v, 3) for v in mesh.bounds)}")

    return mesh


def classify_surface_cells(mesh, ground_height_tol=0.20, horizontal_limit=0.70):
    """
    Classify cells as ground, roof or facade from cell centers and normals.

    This keeps the exercise independent from a specific cell-data label.
    """
    centers = mesh.cell_centers().points
    normals = mesh.cell_data["Normals"]

    z_min = centers[:, 2].min()
    nz = normals[:, 2]

    is_horizontal_up = nz > horizontal_limit
    ground = is_horizontal_up & (centers[:, 2] <= z_min + ground_height_tol)
    roof = is_horizontal_up & ~ground
    facade = np.abs(nz) <= horizontal_limit
    other = ~(ground | roof | facade)

    surface_id = np.full(mesh.n_cells, 3, dtype=int)
    surface_id[ground] = 0
    surface_id[facade] = 1
    surface_id[roof] = 2

    mesh.cell_data["surface_id"] = surface_id
    mesh.cell_data["is_ground"] = ground.astype(int)
    mesh.cell_data["is_facade"] = facade.astype(int)
    mesh.cell_data["is_roof"] = roof.astype(int)

    print("\nClassification des mailles")
    print("  sol     :", int(ground.sum()))
    print("  facade  :", int(facade.sum()))
    print("  toiture :", int(roof.sum()))
    print("  autre   :", int(other.sum()))

    return surface_id


# =============================================================================
# Facteurs de forme et SVF
# =============================================================================

def compute_viewfactor_matrix(mesh):
    print_section("Calcul de la matrice des facteurs de forme")
    print(f"Nombre de faces        : {mesh.n_cells}")
    print(f"Visibilite strict      : {STRICT_VISIBILITY}")
    print(f"Obstruction strict     : {STRICT_OBSTRUCTION}")
    print(f"Arrondi geometrie      : {ROUNDING_DECIMAL}")
    print(f"Epsilon integration    : {EPSILON_INTEGRATION}")

    viewfactor_matrix = pvf.compute_viewfactor_matrix(
        mesh,
        obstacles=mesh,
        strict_visibility=STRICT_VISIBILITY,
        strict_obstruction=STRICT_OBSTRUCTION,
        rounding_decimal=ROUNDING_DECIMAL,
        epsilon=EPSILON_INTEGRATION,
        verbose=True,
    )

    print("Matrice calculee :", viewfactor_matrix.shape)
    print_stats("Somme vers scene", viewfactor_matrix.sum(axis=0), "-")

    return viewfactor_matrix


def compute_svf(viewfactor_matrix):
    sum_to_scene = viewfactor_matrix.sum(axis=0)
    svf = 1.0 - sum_to_scene

    # Les tres operations suivantes evitent les petits depassements numeriques.
    svf = np.where(np.abs(svf) < 1e-10, 0.0, svf)
    svf = np.clip(svf, 0.0, 1.0)

    print_section("Calcul du Sky View Factor")
    print("SVF = 1 - somme des facteurs de forme vers les surfaces de la scene")
    print_stats("SVF", svf, "-")

    return svf


def plot_cell_scalar(mesh, scalar_name, title, cmap="viridis"):
    plotter = pv.Plotter(notebook=False)
    plotter.add_mesh(
        mesh,
        scalars=scalar_name,
        cmap=cmap,
        show_edges=True,
        show_scalar_bar=False,
    )
    plotter.add_scalar_bar(title=title)
    plotter.add_axes()
    plotter.add_title(title)
    plotter.show()


# =============================================================================
# Temperatures de surface et flux GLO
# =============================================================================

def compute_cell_orientation(mesh):
    """
    Return surface tilt and azimuth from cell normals.

    Convention: x is East, y is North, z is Up. The azimuth convention follows
    pvlib: 0 deg North, 90 deg East, 180 deg South, 270 deg West.
    """
    normals = mesh.cell_data["Normals"]
    nx = normals[:, 0]
    ny = normals[:, 1]
    nz = np.clip(normals[:, 2], -1.0, 1.0)

    tilt = np.degrees(np.arccos(nz))
    azimuth = (
        np.degrees(np.arctan2(nx, ny)) + SCENE_AZIMUTH_OFFSET_DEG
    ) % 360.0

    return tilt, azimuth


def compute_cell_shortwave_poa(mesh, location, times, ghi, dni, dhi):
    """
    Compute incident shortwave radiation on each cell using pvlib.

    The result has shape (n_hours, n_cells) and is expressed in W/m2.
    """
    print_section("Calcul du rayonnement solaire incident avec pvlib")
    print("Modele : get_total_irradiance(..., model='isotropic')")
    print(f"Albedo sol : {GROUND_ALBEDO:.2f}")
    print(f"Offset azimut scene : {SCENE_AZIMUTH_OFFSET_DEG:.1f} deg")

    tilt, azimuth = compute_cell_orientation(mesh)
    mesh.cell_data["surface_tilt_deg"] = tilt
    mesh.cell_data["surface_azimuth_deg"] = azimuth

    print_stats("Tilt des faces", tilt, "deg")
    print_stats("Azimut des faces", azimuth, "deg")

    pv_location = pvlib.location.Location(
        latitude=location["latitude"],
        longitude=location["longitude"],
        tz=location["timezone"],
        altitude=location["altitude"],
        name=location["name"],
    )
    solar_position = pv_location.get_solarposition(times)
    zenith_column = (
        "apparent_zenith"
        if "apparent_zenith" in solar_position
        else "zenith"
    )

    poa = np.zeros((len(times), mesh.n_cells), dtype=float)

    for k in range(len(times)):
        total_irrad = pvlib.irradiance.get_total_irradiance(
            surface_tilt=tilt,
            surface_azimuth=azimuth,
            solar_zenith=float(solar_position[zenith_column].iloc[k]),
            solar_azimuth=float(solar_position["azimuth"].iloc[k]),
            dni=float(dni[k]),
            ghi=float(ghi[k]),
            dhi=float(dhi[k]),
            albedo=GROUND_ALBEDO,
            model="isotropic",
        )
        poa[k, :] = np.maximum(np.asarray(total_irrad["poa_global"]), 0.0)

    print_stats("Zenith solaire", solar_position[zenith_column].to_numpy(), "deg")
    print_stats("Azimut solaire", solar_position["azimuth"].to_numpy(), "deg")
    print_stats("K_down toutes cellules", poa, "W/m2")
    for target_hour in (9, 12, 15):
        matches = np.where(times.hour == target_hour)[0]
        if len(matches) > 0:
            print_stats(f"K_down {target_hour:02d}h", poa[matches[0], :], "W/m2")

    return poa


def compute_surface_temperatures_1r1c(mesh, tair_c, tsky_k, shortwave_w_m2):
    """
    Explicit 1R1C surface temperature model for every cell.

    C dT_s/dt =
        h_c (T_air - T_s)
      + alpha K_down
      + epsilon sigma (T_sky^4 - T_s^4)
      + k/e (T_core - T_s)
    """
    heat_capacity = (
        mesh.cell_data["vol_heat_capacity_J_m3K"]
        * mesh.cell_data["active_thickness_m"]
    )
    conductance_core = (
        mesh.cell_data["conductivity_W_mK"]
        / mesh.cell_data["active_thickness_m"]
    )
    alpha = mesh.cell_data["solar_absorptivity"]
    epsilon = mesh.cell_data["emissivity"]

    print_section("Calcul des temperatures de surface 1R1C")
    print("Equation : C dTs/dt = h(Tair-Ts) + alpha*K_down + eps*sigma(Tsky^4-Ts^4) + k/e(Tcore-Ts)")
    print(f"h convectif uniforme : {SURFACE_HEAT_TRANSFER_COEFF_W_M2K:.2f} W/m2/K")
    print(f"Pas de temps         : {TIME_STEP_SECONDS:.0f} s")
    print(f"Tsky                 : Tair - 15 degC")
    print_stats("Capacite C", heat_capacity, "J/m2/K")
    print_stats("Conductance k/e", conductance_core, "W/m2/K")
    print_stats("Absorptivite solaire", alpha, "-")
    print_stats("Emissivite", epsilon, "-")

    tair_k = tair_c + 273.15
    tcore_k = np.full_like(tair_k, tair_k.mean())
    surface_k = np.zeros((len(tair_k), mesh.n_cells), dtype=float)
    surface_k[0, :] = tair_k[0]

    print(f"Tcore approxime      : {tcore_k[0] - 273.15:.2f} degC")

    for k in range(1, len(tair_c)):
        previous = surface_k[k - 1, :]

        q_conv = SURFACE_HEAT_TRANSFER_COEFF_W_M2K * (tair_k[k] - previous)
        q_solar = alpha * shortwave_w_m2[k, :]
        q_lw_sky = epsilon * SIGMA * (tsky_k[k]**4 - previous**4)
        q_cond = conductance_core * (tcore_k[k] - previous)

        surface_k[k, :] = previous + (
            TIME_STEP_SECONDS / heat_capacity
        ) * (q_conv + q_solar + q_lw_sky + q_cond)

    print_stats("Ts toutes heures", surface_k - 273.15, "degC")
    for target_hour in (6, 12, 18):
        if target_hour < len(tair_c):
            print_stats(f"Ts {target_hour:02d}h", surface_k[target_hour, :] - 273.15, "degC")

    return surface_k


def assign_cell_emissivity(surface_id):
    emissivity = np.empty(surface_id.shape[0], dtype=float)
    emissivity[surface_id == 0] = MATERIALS["ground"]["emissivity"]
    emissivity[surface_id == 1] = MATERIALS["facade"]["emissivity"]
    emissivity[surface_id == 2] = MATERIALS["roof"]["emissivity"]
    emissivity[surface_id == 3] = MATERIALS["other"]["emissivity"]
    return emissivity


def add_material_properties_to_mesh(mesh, surface_id):
    print_section("Affectation des proprietes materiaux")

    mesh.cell_data["emissivity"] = assign_cell_emissivity(surface_id)

    absorptivity = np.empty(surface_id.shape[0], dtype=float)
    conductivity = np.empty(surface_id.shape[0], dtype=float)
    heat_capacity = np.empty(surface_id.shape[0], dtype=float)
    active_thickness = np.empty(surface_id.shape[0], dtype=float)

    material_by_id = {
        0: MATERIALS["ground"],
        1: MATERIALS["facade"],
        2: MATERIALS["roof"],
        3: MATERIALS["other"],
    }

    for sid, material in material_by_id.items():
        mask = surface_id == sid
        absorptivity[mask] = material["solar_absorptivity"]
        conductivity[mask] = material["conductivity_W_mK"]
        heat_capacity[mask] = (
            material["density_kg_m3"] * material["specific_heat_J_kgK"]
        )
        active_thickness[mask] = material["thickness_m"]

        print(
            f"  id={sid} | {material['name']:<24} | "
            f"n={int(mask.sum()):4d} | "
            f"k={material['conductivity_W_mK']:.2f} W/m/K | "
            f"rho={material['density_kg_m3']:.0f} kg/m3 | "
            f"cp={material['specific_heat_J_kgK']:.0f} J/kg/K | "
            f"e={material['thickness_m']:.3f} m | "
            f"eps={material['emissivity']:.2f} | "
            f"alpha={material['solar_absorptivity']:.2f}"
        )

    mesh.cell_data["solar_absorptivity"] = absorptivity
    mesh.cell_data["conductivity_W_mK"] = conductivity
    mesh.cell_data["vol_heat_capacity_J_m3K"] = heat_capacity
    mesh.cell_data["active_thickness_m"] = active_thickness


def compute_lw_flux(viewfactor_matrix, svf, surface_temperature_k, tsky_k,
                    emissivity):
    """
    Net longwave flux received by each cell.

    Positive values mean net radiative gain for the cell.
    """
    t4 = surface_temperature_k**4
    sum_to_scene = viewfactor_matrix.sum(axis=0)

    scene_exchange = viewfactor_matrix.T @ t4 - sum_to_scene * t4
    sky_exchange = svf * (tsky_k**4 - t4)

    return emissivity * SIGMA * (scene_exchange + sky_exchange)


def compute_24h_lw_fluxes(mesh, viewfactor_matrix, svf, surface_id,
                          hours, tair_c, ghi, dni, dhi, shortwave_w_m2):
    print_section("Calcul des flux grandes longueurs d'onde")
    print("Le flux positif correspond a un gain radiatif net pour la cellule.")

    tsky_k = tair_c - 15.0 + 273.15
    print_stats("Tsky", tsky_k - 273.15, "degC")

    surface_temperatures = compute_surface_temperatures_1r1c(
        mesh,
        tair_c,
        tsky_k,
        shortwave_w_m2,
    )
    emissivity = assign_cell_emissivity(surface_id)

    all_fluxes = []
    all_surface_temperatures = []

    print("\nResume horaire")
    for k, hour in enumerate(hours):
        surface_temp_k = surface_temperatures[k, :]
        q_lw = compute_lw_flux(
            viewfactor_matrix,
            svf,
            surface_temp_k,
            tsky_k[k],
            emissivity,
        )

        mesh.cell_data[f"T_surface_{hour:02d}h_C"] = surface_temp_k - 273.15
        mesh.cell_data[f"K_down_{hour:02d}h_Wm2"] = shortwave_w_m2[k, :]
        mesh.cell_data[f"q_GLO_{hour:02d}h_Wm2"] = q_lw
        all_fluxes.append(q_lw)
        all_surface_temperatures.append(surface_temp_k)

        print(
            f"  {hour:02d}h | Tair={tair_c[k]:5.1f} degC | "
            f"Tsky={tsky_k[k] - 273.15:5.1f} degC | "
            f"GHI={ghi[k]:6.1f} | DNI={dni[k]:6.1f} | DHI={dhi[k]:6.1f} W/m2 | "
            f"Kdown moy={shortwave_w_m2[k, :].mean():7.2f} W/m2 | "
            f"Ts moy={surface_temp_k.mean() - 273.15:6.2f} degC | "
            f"q moyen={q_lw.mean():7.2f} W/m2"
        )

    mesh.cell_data["q_GLO_mean_24h_Wm2"] = np.mean(np.vstack(all_fluxes), axis=0)
    all_fluxes_array = np.vstack(all_fluxes)
    print_stats("q_GLO toutes heures", all_fluxes_array, "W/m2")
    print_stats("q_GLO moyen 24h", mesh.cell_data["q_GLO_mean_24h_Wm2"], "W/m2")

    return all_surface_temperatures, all_fluxes, tsky_k


def save_pvd_time_series(mesh, hours, surface_temperatures_k, fluxes,
                         shortwave_w_m2,
                         output_dir, output_pvd):
    """
    Save one VTP file per hour and a PVD collection file for ParaView.

    The mesh is a surface PolyData, so VTP is the native XML VTK format. Opening
    the PVD file in ParaView exposes the 24 files as a single time series.
    """
    print_section("Export des resultats")
    print(f"Dossier serie temporelle : {output_dir}")
    print(f"Collection ParaView      : {output_pvd}")

    output_dir.mkdir(parents=True, exist_ok=True)
    datasets = []

    for k, hour in enumerate(hours):
        frame = mesh.copy(deep=True)

        for name in list(frame.cell_data.keys()):
            del frame.cell_data[name]

        frame.cell_data["SVF"] = mesh.cell_data["SVF"]
        frame.cell_data["surface_id"] = mesh.cell_data["surface_id"]
        frame.cell_data["emissivity"] = mesh.cell_data["emissivity"]
        frame.cell_data["solar_absorptivity"] = mesh.cell_data["solar_absorptivity"]
        frame.cell_data["K_down_Wm2"] = shortwave_w_m2[k, :]
        frame.cell_data["q_GLO_Wm2"] = fluxes[k]
        frame.cell_data["T_surface_C"] = surface_temperatures_k[k] - 273.15

        filename = f"scene_LR_GLO_18mai_Lyon_{hour:02d}h.vtp"
        path = output_dir / filename
        frame.save(path)

        rel_path = path.relative_to(output_pvd.parent).as_posix()
        datasets.append((hour, rel_path))
        print(f"  pas {hour:02d}h -> {path.name}")

    lines = [
        '<?xml version="1.0"?>',
        '<VTKFile type="Collection" version="0.1" byte_order="LittleEndian">',
        '  <Collection>',
    ]
    for hour, rel_path in datasets:
        lines.append(
            f'    <DataSet timestep="{hour}" group="" part="0" file="{rel_path}"/>'
        )
    lines.extend([
        '  </Collection>',
        '</VTKFile>',
        '',
    ])

    output_pvd.write_text("\n".join(lines), encoding="utf-8")


# =============================================================================
# Main
# =============================================================================

def main():
    print_section("Mini-projet SVF et flux GLO")
    print(f"Script              : {Path(__file__).name}")
    print(f"Geometrie           : {MESH_FILE}")
    print(f"Meteo               : {EPW_FILE}")
    print(f"Date EPW            : {DAY:02d}/{MONTH:02d}")

    mesh = load_scene(MESH_FILE)
    surface_id = classify_surface_cells(mesh)
    add_material_properties_to_mesh(mesh, surface_id)

    viewfactor_matrix = compute_viewfactor_matrix(mesh)

    # -------------------------------------------------------------------------
    # Partie 1 : SVF
    # -------------------------------------------------------------------------
    svf = compute_svf(viewfactor_matrix)
    mesh.cell_data["SVF"] = svf

    if SHOW_SVF_PLOT:
        print("Affichage interactif du SVF")
        plot_cell_scalar(mesh, "SVF", "Sky View Factor", cmap="viridis")

    # -------------------------------------------------------------------------
    # Partie 2 : flux grandes longueurs d'onde
    # -------------------------------------------------------------------------
    location, hours, times, tair_c, ghi, dni, dhi = read_epw_day(
        EPW_FILE,
        MONTH,
        DAY,
    )
    shortwave_w_m2 = compute_cell_shortwave_poa(
        mesh,
        location,
        times,
        ghi,
        dni,
        dhi,
    )

    surface_temperatures_k, fluxes, _ = compute_24h_lw_fluxes(
        mesh,
        viewfactor_matrix,
        svf,
        surface_id,
        hours,
        tair_c,
        ghi,
        dni,
        dhi,
        shortwave_w_m2,
    )

    OUTPUT_DIR.mkdir(exist_ok=True)
    mesh.save(OUTPUT_ALL_FIELDS_FILE)
    print(f"VTK tout-en-un sauvegarde : {OUTPUT_ALL_FIELDS_FILE}")

    save_pvd_time_series(
        mesh,
        hours,
        surface_temperatures_k,
        fluxes,
        shortwave_w_m2,
        OUTPUT_TIMESERIES_DIR,
        OUTPUT_TIMESERIES_FILE,
    )
    print(f"Serie temporelle sauvegardee : {OUTPUT_TIMESERIES_FILE}")

    if SHOW_FLUX_PLOT:
        scalar_name = f"q_GLO_{PLOT_FLUX_HOUR:02d}h_Wm2"
        print(f"Affichage interactif du champ {scalar_name}")
        plot_cell_scalar(mesh, scalar_name, scalar_name, cmap="coolwarm")

    print_section("Fin du calcul")


if __name__ == "__main__":
    main()
