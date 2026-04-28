# -*- coding: utf-8 -*-
"""
Example for pyViewFactor on an urban scene.

This script combines:
1. Geometry loading and identification of wall / sky / building cells
2. Visual debug plots for what the wall sees in strict and non-strict modes
3. Aggregated wall->sky / wall->building1 / wall->building2 / wall->ground view factors
4. Sequential computation of all wall->cell_i view factors for one target wall cell
5. Full matrix computation and VTK export for comparison

Notes
-----
- get_visibility(...) returns True if faces are geometrically visible
- get_obstruction(...) returns True if the path is NOT obstructed
- For imported geometries, rounding_decimal=5 is often a better compromise than 4
"""

import numpy as np
import pyvista as pv
import pyviewfactor as pvf

from pyviewfactor.pvf_geometry_preprocess import (
    ProcessedGeometry,
    FaceMeshPreprocessor,
)
from pyviewfactor.pvf_integrators import (
    compute_viewfactor_dblquad,
    compute_viewfactor_gauss_legendre,
)


# -----------------------------------------------------------------------------
# Small plotting helpers
# -----------------------------------------------------------------------------

def add_face_normal(plotter, face, color="black", scale=1.0, rounding_decimal=6):
    pts = pvf.face_to_array(face, rounding_decimal=rounding_decimal)
    c = pvf.polygon_centroid(pts)
    n = pvf.face_normal_numpy(pts)
    arr = pv.Arrow(start=c, direction=n, scale=scale)
    plotter.add_mesh(arr, color=color)


def add_visibility_rays(plotter, face1, face2, rounding_decimal=6,
                        show_centroid_ray=True, show_point_rays=True):
    pts1 = pvf.face_to_array(face1, rounding_decimal=rounding_decimal)
    pts2 = pvf.face_to_array(face2, rounding_decimal=rounding_decimal)

    if show_centroid_ray:
        c1 = pvf.polygon_centroid(pts1)
        c2 = pvf.polygon_centroid(pts2)
        plotter.add_mesh(pv.Line(c1, c2), color="black", line_width=4)

    if show_point_rays:
        for p1 in pts1:
            for p2 in pts2:
                if np.linalg.norm(p2 - p1) < 1e-12:
                    continue
                plotter.add_mesh(pv.Line(p1, p2), color="gray", opacity=0.2)


def plot_scene(wall, sky, building1, building2):
    p = pv.Plotter()
    p.add_mesh(sky.extract_surface(), color="lightblue", opacity=0.25,
               show_edges=True, label="sky")
    p.add_mesh(building1.extract_surface(), color="tomato", opacity=0.8,
               show_edges=True, label="building1")
    p.add_mesh(building2.extract_surface(), color="orange", opacity=0.8,
               show_edges=True, label="building2")
    p.add_mesh(wall, color="limegreen", opacity=1.0,
               show_edges=True, label="wall")
    p.add_legend()
    p.add_axes()
    p.add_title("Urban scene")
    p.show()


def plot_one_patch_debug(mesh, wall, patch_id, color="blue", rounding_decimal=5,
                         title="Patch debug"):
    patch = mesh.extract_cells(patch_id).extract_surface()

    p = pv.Plotter()
    p.add_mesh(wall, color="limegreen", opacity=1.0, show_edges=True)
    p.add_mesh(patch, color=color, opacity=0.9, show_edges=True)
    add_face_normal(p, wall, color="green", scale=2.0,
                    rounding_decimal=rounding_decimal)
    add_face_normal(p, patch, color=color, scale=2.0,
                    rounding_decimal=rounding_decimal)
    add_visibility_rays(p, patch, wall, rounding_decimal=rounding_decimal)
    p.add_axes()
    p.add_title(title)
    p.show()


def classify_visible_patches(mesh, meshpoly, wall, patch_ids,
                             strict_visibility, strict_obstruction,
                             rounding_decimal):
    accepted = []
    rejected_visibility = []
    rejected_obstruction = []

    for patch in patch_ids:
        patch_face = mesh.extract_cells(patch).extract_surface()

        vis = pvf.get_visibility(
            patch_face, wall,
            strict=strict_visibility,
            rounding_decimal=rounding_decimal
        )[0]
        if not vis:
            rejected_visibility.append(patch)
            continue

        unob = pvf.get_obstruction(
            patch_face, wall, meshpoly,
            strict=strict_obstruction,
            rounding_decimal=rounding_decimal
        )[0]
        if not unob:
            rejected_obstruction.append(patch)
            continue

        accepted.append(patch)

    return accepted, rejected_visibility, rejected_obstruction


def plot_patch_classification(mesh, wall,
                              accepted_sky, rejected_sky_visibility, rejected_sky_obstruction,
                              accepted_build1, rejected_build1_visibility, rejected_build1_obstruction,
                              accepted_build2, rejected_build2_visibility, rejected_build2_obstruction,
                              title="Wall visibility / obstruction classification"):
    p = pv.Plotter()
    p.add_mesh(wall, color="limegreen", opacity=1.0, show_edges=True, label="wall")

    if accepted_sky:
        p.add_mesh(mesh.extract_cells(accepted_sky).extract_surface(),
                   color="blue", opacity=1.0, show_edges=True, label="accepted sky")
    if rejected_sky_visibility:
        p.add_mesh(mesh.extract_cells(rejected_sky_visibility).extract_surface(),
                   color="red", opacity=1.0, show_edges=True, label="sky rejected by visibility")
    if rejected_sky_obstruction:
        p.add_mesh(mesh.extract_cells(rejected_sky_obstruction).extract_surface(),
                   color="orange", opacity=1.0, show_edges=True, label="sky rejected by obstruction")

    if accepted_build1:
        p.add_mesh(mesh.extract_cells(accepted_build1).extract_surface(),
                   color="cyan", opacity=1.0, show_edges=True, label="accepted build1")
    if rejected_build1_visibility:
        p.add_mesh(mesh.extract_cells(rejected_build1_visibility).extract_surface(),
                   color="darkred", opacity=1.0, show_edges=True, label="build1 rejected by visibility")
    if rejected_build1_obstruction:
        p.add_mesh(mesh.extract_cells(rejected_build1_obstruction).extract_surface(),
                   color="gold", opacity=1.0, show_edges=True, label="build1 rejected by obstruction")

    if accepted_build2:
        p.add_mesh(mesh.extract_cells(accepted_build2).extract_surface(),
                   color="magenta", opacity=1.0, show_edges=True, label="accepted build2")
    if rejected_build2_visibility:
        p.add_mesh(mesh.extract_cells(rejected_build2_visibility).extract_surface(),
                   color="firebrick", opacity=1.0, show_edges=True, label="build2 rejected by visibility")
    if rejected_build2_obstruction:
        p.add_mesh(mesh.extract_cells(rejected_build2_obstruction).extract_surface(),
                   color="yellow", opacity=1.0, show_edges=True, label="build2 rejected by obstruction")

    p.add_legend()
    p.add_axes()
    p.add_title(title)
    p.show()


# -----------------------------------------------------------------------------
# Aggregated wall -> sky/buildings/ground
# -----------------------------------------------------------------------------

def compute_aggregated_wall_viewfactors(mesh, meshpoly, wall,
                                        i_sky, i_building1, i_building2,
                                        strict_visibility=True,
                                        strict_obstruction=True,
                                        rounding_decimal=5,
                                        epsilon=1e-3):
    Fsky = 0.0
    Fbuilding1 = 0.0
    Fbuilding2 = 0.0

    print("> Computation F_wall>sky")
    for patch in i_sky:
        sky_patch = mesh.extract_cells(patch).extract_surface()
        if pvf.get_visibility(
            sky_patch, wall,
            strict=strict_visibility,
            rounding_decimal=rounding_decimal
        )[0]:
            if pvf.get_obstruction(
                sky_patch, wall, meshpoly,
                strict=strict_obstruction,
                rounding_decimal=rounding_decimal
            )[0]:
                Fsky += pvf.compute_viewfactor(
                    sky_patch, wall,
                    epsilon=epsilon,
                    rounding_decimal=rounding_decimal
                )

    print("> Computation F_wall>building1")
    for patch in i_building1:
        b1_patch = mesh.extract_cells(patch).extract_surface()
        if pvf.get_visibility(
            b1_patch, wall,
            strict=strict_visibility,
            rounding_decimal=rounding_decimal
        )[0]:
            if pvf.get_obstruction(
                b1_patch, wall, meshpoly,
                strict=strict_obstruction,
                rounding_decimal=rounding_decimal
            )[0]:
                Fbuilding1 += pvf.compute_viewfactor(
                    b1_patch, wall,
                    epsilon=epsilon,
                    rounding_decimal=rounding_decimal
                )

    print("> Computation F_wall>building2")
    for patch in i_building2:
        b2_patch = mesh.extract_cells(patch).extract_surface()
        if pvf.get_visibility(
            b2_patch, wall,
            strict=strict_visibility,
            rounding_decimal=rounding_decimal
        )[0]:
            if pvf.get_obstruction(
                b2_patch, wall, meshpoly,
                strict=strict_obstruction,
                rounding_decimal=rounding_decimal
            )[0]:
                Fbuilding2 += pvf.compute_viewfactor(
                    b2_patch, wall,
                    epsilon=epsilon,
                    rounding_decimal=rounding_decimal
                )

    Fground = 1.0 - Fsky - Fbuilding1 - Fbuilding2

    print("\n-----------------------------")
    print("\tSky       ", round(Fsky, 6))
    print("\tGround    ", round(Fground, 6))
    print("\tBuilding 1", round(Fbuilding1, 6))
    print("\tBuilding 2", round(Fbuilding2, 6))

    return Fsky, Fbuilding1, Fbuilding2, Fground


# -----------------------------------------------------------------------------
# Sequential wall -> all cells for one target cell, mirroring matrix logic
# -----------------------------------------------------------------------------

def compute_sequential_column_like_matrix(meshpoly, target_id,
                                          strict_visibility=True,
                                          strict_obstruction=True,
                                          rounding_decimal=5,
                                          epsilon=1e-3,
                                          area_tol=1e-14):
    pg = ProcessedGeometry(meshpoly, rounding_decimal=rounding_decimal)
    obs_pre = FaceMeshPreprocessor(meshpoly, rounding_decimal=rounding_decimal)

    N = meshpoly.n_cells
    FFseq = np.zeros((N, N), dtype=np.float64)
    areas = pg.areas

    vertex_sets = [
        frozenset(tuple(np.round(v, rounding_decimal)) for v in pg.get_face(i))
        for i in range(N)
    ]

    Sj = vertex_sets[target_id]

    accepted = []
    rejected_visibility = []
    rejected_obstruction = []
    touching_pairs = []
    disconnected_pairs = []

    for i in range(N):
        if i == target_id:
            continue
        if vertex_sets[i] & Sj:
            touching_pairs.append(i)
        else:
            disconnected_pairs.append(i)

    print(f"Target cell: {target_id}")
    print(f"Touching pairs: {len(touching_pairs)}")
    print(f"Disconnected pairs: {len(disconnected_pairs)}")

    for i in range(N):
        if i == target_id:
            continue

        if areas[i] <= area_tol or areas[target_id] <= area_tol:
            continue

        vis, _ = pvf.get_visibility_from_cache(
            i, target_id, pg,
            strict=strict_visibility,
            verbose=False,
            rounding_decimal=rounding_decimal
        )
        if not vis:
            rejected_visibility.append(i)
            continue

        unob, _ = pvf.get_obstruction_from_cache(
            i, target_id, pg, obs_pre,
            strict=strict_obstruction,
            verbose=False,
            eps=1e-6,
            rounding_decimal=rounding_decimal
        )
        if not unob:
            rejected_obstruction.append(i)
            continue

        pts_i = pg.get_face(i)
        pts_j = pg.get_face(target_id)
        constante = 4.0 * np.pi * areas[target_id]

        if vertex_sets[i] & Sj:
            pts_j_adj = pts_j.copy()
            c_i = pg.get_centroid(i)
            c_j = pg.get_centroid(target_id)
            direction = c_j - c_i
            norm = np.linalg.norm(direction)
            if norm > 0.0:
                direction /= norm
                pts_j_adj = pts_j_adj + epsilon * direction
            fij = compute_viewfactor_dblquad(pts_i, pts_j_adj, constante)
        else:
            fij = compute_viewfactor_gauss_legendre(pts_i, pts_j, constante)

        FFseq[i, target_id] = fij
        accepted.append(i)

    print("\nSequential column summary")
    print("Accepted:", len(accepted))
    print("Rejected by visibility:", len(rejected_visibility))
    print("Rejected by obstruction:", len(rejected_obstruction))

    return FFseq, accepted, rejected_visibility, rejected_obstruction


# -----------------------------------------------------------------------------
# Main script
# -----------------------------------------------------------------------------

def main():
    # Parameters
    strict_visibility = False
    strict_obstruction = False
    rounding_decimal = 5
    epsilon = 1e-3
    target_id = 182

    # -----------------------------------------------------------------
    # 0. Geometry
    # -----------------------------------------------------------------
    mesh = pv.read("./src_data/built_envmt.vtk")
    meshpoly = pvf.fc_unstruc2poly(mesh)

    i_wall = np.where(mesh["wall_names"] == "wall")[0]
    i_sky = np.where(mesh["wall_names"] == "sky")[0]
    i_building1 = np.where(mesh["wall_names"] == "building1")[0]
    i_building2 = np.where(mesh["wall_names"] == "building2")[0]

    wall = mesh.extract_cells(i_wall).extract_surface()
    sky = mesh.extract_cells(i_sky)
    building1 = mesh.extract_cells(i_building1)
    building2 = mesh.extract_cells(i_building2)

    # -----------------------------------------------------------------
    # 1. Visual debug of scene and wall visibility / obstruction
    # -----------------------------------------------------------------
    plot_scene(wall, sky, building1, building2)

    # one sky patch and one building patch for local visual debug
    if len(i_sky) > 0:
        plot_one_patch_debug(
            mesh, wall, int(i_sky[0]),
            color="blue",
            rounding_decimal=rounding_decimal,
            title="One sky patch vs wall"
        )

    if len(i_building1) > 0:
        plot_one_patch_debug(
            mesh, wall, int(i_building1[0]),
            color="red",
            rounding_decimal=rounding_decimal,
            title="One building1 patch vs wall"
        )

    # strict classification
    accepted_sky_s, rejected_sky_vis_s, rejected_sky_obs_s = classify_visible_patches(
        mesh, meshpoly, wall, i_sky,
        strict_visibility=True,
        strict_obstruction=True,
        rounding_decimal=rounding_decimal
    )
    accepted_b1_s, rejected_b1_vis_s, rejected_b1_obs_s = classify_visible_patches(
        mesh, meshpoly, wall, i_building1,
        strict_visibility=True,
        strict_obstruction=True,
        rounding_decimal=rounding_decimal
    )
    accepted_b2_s, rejected_b2_vis_s, rejected_b2_obs_s = classify_visible_patches(
        mesh, meshpoly, wall, i_building2,
        strict_visibility=True,
        strict_obstruction=True,
        rounding_decimal=rounding_decimal
    )

    plot_patch_classification(
        mesh, wall,
        accepted_sky_s, rejected_sky_vis_s, rejected_sky_obs_s,
        accepted_b1_s, rejected_b1_vis_s, rejected_b1_obs_s,
        accepted_b2_s, rejected_b2_vis_s, rejected_b2_obs_s,
        title="STRICT mode: wall visibility / obstruction classification"
    )

    # non-strict classification
    accepted_sky_ns, rejected_sky_vis_ns, rejected_sky_obs_ns = classify_visible_patches(
        mesh, meshpoly, wall, i_sky,
        strict_visibility=False,
        strict_obstruction=False,
        rounding_decimal=rounding_decimal
    )
    accepted_b1_ns, rejected_b1_vis_ns, rejected_b1_obs_ns = classify_visible_patches(
        mesh, meshpoly, wall, i_building1,
        strict_visibility=False,
        strict_obstruction=False,
        rounding_decimal=rounding_decimal
    )
    accepted_b2_ns, rejected_b2_vis_ns, rejected_b2_obs_ns = classify_visible_patches(
        mesh, meshpoly, wall, i_building2,
        strict_visibility=False,
        strict_obstruction=False,
        rounding_decimal=rounding_decimal
    )

    plot_patch_classification(
        mesh, wall,
        accepted_sky_ns, rejected_sky_vis_ns, rejected_sky_obs_ns,
        accepted_b1_ns, rejected_b1_vis_ns, rejected_b1_obs_ns,
        accepted_b2_ns, rejected_b2_vis_ns, rejected_b2_obs_ns,
        title="NON-STRICT mode: wall visibility / obstruction classification"
    )

    # -----------------------------------------------------------------
    # 2. Aggregated wall -> sky/buildings/ground view factors
    # -----------------------------------------------------------------
    compute_aggregated_wall_viewfactors(
        mesh, meshpoly, wall,
        i_sky, i_building1, i_building2,
        strict_visibility=strict_visibility,
        strict_obstruction=strict_obstruction,
        rounding_decimal=rounding_decimal,
        epsilon=epsilon
    )

    # -----------------------------------------------------------------
    # 3. Sequential column, mirroring matrix logic
    # -----------------------------------------------------------------
    FFseq, accepted, rejected_visibility, rejected_obstruction = compute_sequential_column_like_matrix(
        meshpoly,
        target_id=target_id,
        strict_visibility=strict_visibility,
        strict_obstruction=strict_obstruction,
        rounding_decimal=rounding_decimal,
        epsilon=epsilon
    )

    meshpoly_seq = meshpoly.copy()
    meshpoly_seq[f"FFseq_col{target_id}"] = FFseq[:, target_id]
    meshpoly_seq.save("results_seq.vtk")
    print(f"Saved sequential result to results_seq.vtk (column {target_id})")

    # -----------------------------------------------------------------
    # 4. Full matrix computation
    # -----------------------------------------------------------------
    FFmat = pvf.compute_viewfactor_matrix(
        meshpoly,
        obstacles=meshpoly,
        skip_visibility=False,
        skip_obstruction=False,
        strict_visibility=strict_visibility,
        strict_obstruction=strict_obstruction,
        rounding_decimal=rounding_decimal,
        epsilon=epsilon,
        verbose=True
    )

    meshpoly_mat = meshpoly.copy()
    meshpoly_mat[f"FFmat_col{target_id}"] = FFmat[:, target_id]
    meshpoly_mat.save("results_matrix.vtk")
    print(f"Saved matrix result to results_matrix.vtk (column {target_id})")

    # Optional comparison export
    meshpoly_cmp = meshpoly.copy()
    meshpoly_cmp[f"FFseq_col{target_id}"] = FFseq[:, target_id]
    meshpoly_cmp[f"FFmat_col{target_id}"] = FFmat[:, target_id]
    meshpoly_cmp[f"FFdiff_col{target_id}"] = FFseq[:, target_id] - FFmat[:, target_id]
    meshpoly_cmp.save("results_compare.vtk")
    print(f"Saved comparison result to results_compare.vtk (column {target_id})")


if __name__ == "__main__":
    main()
