# -*- coding: utf-8 -*-
"""
Discretization sensitivity example for pyViewFactor.

A sphere is approximated by planar facets.
We compute the total view factor from a wall to the spherical surface
for increasing mesh resolutions, and visualize the geometry.
"""

import numpy as np
import pyvista as pv
import pyviewfactor as pvf
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------
# Geometry builders
# ---------------------------------------------------------------------

def build_wall(width=3.0, height=3.0):
    wall = pv.Rectangle([
        [-2.5, -width / 2.0, 0.0],
        [-2.5,  width / 2.0, 0.0],
        [-2.5, -width / 2.0, height]
    ])
    return wall


def build_sphere(radius=0.8, center=(1.0, 0.0, 1.5),
                 theta_resolution=16, phi_resolution=16):
    sphere = pv.Sphere(
        radius=radius,
        center=center,
        theta_resolution=theta_resolution,
        phi_resolution=phi_resolution
    )
    sphere.triangulate(inplace=True)
    return sphere


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def face_centroid_and_normal(face, rounding_decimal=8):
    pts = pvf.face_to_array(face, rounding_decimal)
    c = pvf.polygon_centroid(pts)
    n = pvf.face_normal_numpy(pts)
    return c, n


def ensure_wall_faces_plus_x(wall, rounding_decimal=8):
    _, n = face_centroid_and_normal(wall, rounding_decimal)
    if n[0] < 0:
        wall.flip_faces(inplace=True)
    return wall


def count_visible_facets(surface, wall, strict=False, rounding_decimal=8):
    visible_ids = []
    hidden_ids = []

    for i in range(surface.n_cells):
        facet = pvf.fc_unstruc2poly(surface.extract_cells(i))
        vis = pvf.get_visibility(
            facet, wall,
            strict=strict,
            rounding_decimal=rounding_decimal
        )[0]
        if vis:
            visible_ids.append(i)
        else:
            hidden_ids.append(i)

    return visible_ids, hidden_ids


def compute_wall_to_surface_vf(surface, wall, strict_visibility=False, rounding_decimal=8):
    F_total = 0.0
    visible_ids = []

    for i in range(surface.n_cells):
        facet = pvf.fc_unstruc2poly(surface.extract_cells(i))

        vis = pvf.get_visibility(
            facet, wall,
            strict=strict_visibility,
            rounding_decimal=rounding_decimal
        )[0]

        if vis:
            visible_ids.append(i)
            # compute_viewfactor(receiver, emitter) = F_emitter->receiver
            # We want F_wall->facet, so wall is emitter and facet is receiver.
            F_total += pvf.compute_viewfactor(
                facet,
                wall,
                rounding_decimal=rounding_decimal
            )

    return F_total, visible_ids


# ---------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------

def plot_geometry_and_visibility(wall, surface, visible_ids=None, hidden_ids=None,
                                 title="Geometry"):
    p = pv.Plotter(window_size=[1000, 800])
    p.add_title(title, font_size=10)

    p.add_mesh(wall, color="limegreen", opacity=1.0, show_edges=True, label="wall")

    if visible_ids is None or hidden_ids is None:
        p.add_mesh(surface, color="lightblue", opacity=0.8, show_edges=True, label="surface")
    else:
        if len(hidden_ids) > 0:
            p.add_mesh(
                surface.extract_cells(hidden_ids),
                color="tomato",
                opacity=0.45,
                show_edges=True,
                label="hidden facets"
            )
        if len(visible_ids) > 0:
            p.add_mesh(
                surface.extract_cells(visible_ids),
                color="deepskyblue",
                opacity=0.9,
                show_edges=True,
                label="visible facets"
            )

    # Wall normal
    cw, nw = face_centroid_and_normal(wall)
    p.add_mesh(pv.Arrow(start=cw, direction=nw, scale=0.4), color="green")

    # A few facet normals
    sample_ids = np.linspace(0, surface.n_cells - 1, min(12, surface.n_cells), dtype=int)
    for idx in sample_ids:
        facet = pvf.fc_unstruc2poly(surface.extract_cells(int(idx)))
        c, n = face_centroid_and_normal(facet)
        p.add_mesh(pv.Arrow(start=c, direction=n, scale=0.15), color="navy")

    p.add_legend()
    p.add_axes()
    p.show()

def plot_convergence(resolutions, values):
    values = np.array(values, dtype=float)
    ref = values[-1]
    abs_err = np.abs(values - ref)

    if abs(ref) > 1e-12:
        err = abs_err / abs(ref)
        err_ylabel = "Relative deviation from finest mesh"
    else:
        err = abs_err
        err_ylabel = "Absolute deviation from finest mesh"

    # ---- raw values ----
    plt.figure(figsize=(7, 5))
    plt.plot(resolutions, values, marker="o", label="pyViewFactor")
    plt.axhline(ref, linestyle="--", linewidth=1, label="finest mesh reference")
    plt.xlabel("Sphere resolution")
    plt.ylabel("F(wall → sphere)")
    plt.title("Discretization sensitivity")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # ---- optional log-scale version of raw values ----
    if np.all(values > 0):
        plt.figure(figsize=(7, 5))
        plt.semilogy(resolutions, values, marker="o", label="pyViewFactor")
        plt.axhline(ref, linestyle="--", linewidth=1, label="finest mesh reference")
        plt.xlabel("Sphere resolution")
        plt.ylabel("F(wall → sphere)")
        plt.title("Discretization sensitivity (log scale)")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()

    # ---- error plot ----
    plt.figure(figsize=(7, 5))
    if np.any(err > 0):
        plt.semilogy(resolutions, err, marker="o")
    else:
        plt.plot(resolutions, err, marker="o")
    plt.xlabel("Sphere resolution")
    plt.ylabel(err_ylabel)
    plt.title("Convergence with discretization")
    plt.grid(True)
    plt.tight_layout()
    plt.show()


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    rounding_decimal = 8
    strict_visibility = False

    # --- one reference case for geometry debug ---
    wall = build_wall(width=3.0, height=3.0)
    wall = ensure_wall_faces_plus_x(wall, rounding_decimal=rounding_decimal)

    sphere_ref = build_sphere(
        radius=0.8,
        center=(1.0, 0.0, 1.5),
        theta_resolution=24,
        phi_resolution=24
    )

    visible_ids, hidden_ids = count_visible_facets(
        sphere_ref, wall,
        strict=strict_visibility,
        rounding_decimal=rounding_decimal
    )

    print("Reference geometry")
    print("Wall cells:", wall.n_cells)
    print("Sphere cells:", sphere_ref.n_cells)
    print("Visible facets:", len(visible_ids), "/", sphere_ref.n_cells)

    plot_geometry_and_visibility(
        wall, sphere_ref,
        visible_ids=visible_ids,
        hidden_ids=hidden_ids,
        title="Wall / sphere geometry and visible facets"
    )

    # --- convergence study ---
    resolutions = [2, 4, 8, 10, 12, 14, 16, 20, 24, 28, 32, 40, 48, 64]
    values = []

    for res in resolutions:
        wall = build_wall(width=3.0, height=3.0)
        wall = ensure_wall_faces_plus_x(wall, rounding_decimal=rounding_decimal)

        sphere = build_sphere(
            radius=0.8,
            center=(1.0, 0.0, 1.5),
            theta_resolution=res,
            phi_resolution=res
        )

        F, visible_ids = compute_wall_to_surface_vf(
            sphere, wall,
            strict_visibility=strict_visibility,
            rounding_decimal=rounding_decimal
        )

        values.append(F)
        print(
            f"resolution={res:>3d} | "
            f"visible facets={len(visible_ids):>4d}/{sphere.n_cells:<4d} | "
            f"F(wall -> sphere) = {F:.8f}"
        )

    plot_convergence(resolutions, values)


if __name__ == "__main__":
    main()