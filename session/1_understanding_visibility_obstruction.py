# -*- coding: utf-8 -*-
"""
Visual debug script for pyViewFactor visibility / obstruction semantics.
"""

import sys
import numpy as np
import pyvista as pv
import pyviewfactor as pvf


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def print_face_info(name, face, rounding_decimal=8):
    pts = pvf.face_to_array(face, rounding_decimal)
    c = pvf.polygon_centroid(pts)
    n = pvf.face_normal_numpy(pts)
    print(f"\n{name}")
    print("points:\n", pts)
    print("centroid:", c)
    print("normal:  ", n)


def add_normals(plotter, face, rounding_decimal=8, scale=0.2, color="black"):
    pts = pvf.face_to_array(face, rounding_decimal)
    c = pvf.polygon_centroid(pts)
    n = pvf.face_normal_numpy(pts)
    arr = pv.Arrow(start=c, direction=n, scale=scale)
    plotter.add_mesh(arr, color=color)


def add_point_to_point_rays(plotter, face1, face2, rounding_decimal=8,
                            color="gray", opacity=0.15, skip_coincident=True):
    pts1 = pvf.face_to_array(face1, rounding_decimal)
    pts2 = pvf.face_to_array(face2, rounding_decimal)
    for p1 in pts1:
        tp1 = tuple(np.round(p1, rounding_decimal))
        for p2 in pts2:
            tp2 = tuple(np.round(p2, rounding_decimal))
            if skip_coincident and tp1 == tp2:
                continue
            if np.linalg.norm(p2 - p1) < 1e-12:
                continue
            plotter.add_mesh(pv.Line(p1, p2), color=color, opacity=opacity)


def add_centroid_ray(plotter, face1, face2, rounding_decimal=8,
                     color="black", line_width=4):
    c1 = pvf.polygon_centroid(pvf.face_to_array(face1, rounding_decimal))
    c2 = pvf.polygon_centroid(pvf.face_to_array(face2, rounding_decimal))
    plotter.add_mesh(pv.Line(c1, c2), color=color, line_width=line_width)


# ---------------------------------------------------------------------
# Core test runners
# ---------------------------------------------------------------------

def run_visibility(face1, face2, rounding_decimal=8):
    combos = [
        (False, False),
        (False, True),
        (True, False),
        (True, True),
    ]
    out = []
    for strict, verbose in combos:
        vis, warn = pvf.get_visibility(
            face1, face2,
            strict=strict,
            verbose=verbose,
            rounding_decimal=rounding_decimal
        )
        out.append((strict, verbose, vis, warn))
    return out


def run_obstruction(face1, face2, obstacle, rounding_decimal=8, eps=1e-6):
    combos = [
        (False, False),
        (False, True),
        (True, False),
        (True, True),
    ]
    out = []
    for strict, verbose in combos:
        vis, warn = pvf.get_obstruction(
            face1, face2, obstacle,
            strict=strict,
            verbose=verbose,
            rounding_decimal=rounding_decimal,
            eps=eps
        )
        out.append((strict, verbose, vis, warn))
    return out


# ---------------------------------------------------------------------
# Overlay logic
# ---------------------------------------------------------------------

def check_results(vis_results, obs_results, expected_dict):
    if expected_dict is None:
        return True

    ok = True

    if vis_results is not None and "visibility" in expected_dict:
        for strict, verbose, vis, _ in vis_results:
            exp = expected_dict["visibility"].get((strict, verbose), None)
            if exp is not None and vis != exp:
                ok = False

    if obs_results is not None and "obstruction" in expected_dict:
        for strict, verbose, vis, _ in obs_results:
            exp = expected_dict["obstruction"].get((strict, verbose), None)
            if exp is not None and vis != exp:
                ok = False

    return ok


def build_overlay_text(expected, vis_results, obs_results=None, expected_dict=None):
    lines = []

    if expected:
        lines.append("EXPECTED:")
        lines.append(expected)
        lines.append("")

    if vis_results is not None:
        lines.append("VISIBILITY:")
        for strict, verbose, vis, _ in vis_results:
            exp = None
            if expected_dict and "visibility" in expected_dict:
                exp = expected_dict["visibility"].get((strict, verbose))

            if exp is None:
                line = f"S={int(strict)} V={int(verbose)} -> {vis}"
            else:
                mark = "✓" if vis == exp else "✗"
                line = f"S={int(strict)} V={int(verbose)} -> {vis} (exp {exp}) {mark}"

            lines.append(line)

        lines.append("")

    if obs_results is not None:
        lines.append("OBSTRUCTION:")
        for strict, verbose, vis, _ in obs_results:
            exp = None
            if expected_dict and "obstruction" in expected_dict:
                exp = expected_dict["obstruction"].get((strict, verbose))

            if exp is None:
                line = f"S={int(strict)} V={int(verbose)} -> {vis}"
            else:
                mark = "✓" if vis == exp else "✗"
                line = f"S={int(strict)} V={int(verbose)} -> {vis} (exp {exp}) {mark}"

            lines.append(line)

    return "\n".join(lines)


# ---------------------------------------------------------------------
# Visualization wrapper
# ---------------------------------------------------------------------

def show_case(face1, face2, obstacle=None, title="",
              expected="", expected_dict=None,
              rounding_decimal=8, eps=1e-6, show_rays=True):

    print("\n" + "#" * 80)
    print(title)
    if expected:
        print("EXPECTED:", expected)

    print_face_info("Face 1", face1, rounding_decimal)
    print_face_info("Face 2", face2, rounding_decimal)

    vis_results = run_visibility(face1, face2, rounding_decimal)
    obs_results = None

    if obstacle is not None:
        obs_results = run_obstruction(
            face1, face2, obstacle,
            rounding_decimal=rounding_decimal,
            eps=eps
        )

    overlay_text = build_overlay_text(
        expected,
        vis_results,
        obs_results,
        expected_dict=expected_dict
    )

    is_ok = check_results(vis_results, obs_results, expected_dict)
    overlay_color = "green" if is_ok else "red"

    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)

    print("\nVisibility:")
    for strict, verbose, vis, warn in vis_results:
        mode = f"strict={strict}, verbose={verbose}"
        print(f"  [{mode:<22}] -> {vis} | {warn}")

    if obs_results is not None:
        print("\nObstruction:")
        for strict, verbose, vis, warn in obs_results:
            mode = f"strict={strict}, verbose={verbose}"
            print(f"  [{mode:<22}] -> {vis} | {warn}")

    sys.stdout.flush()

    pl = pv.Plotter(window_size=[1000, 800])
    pl.add_title(title, font_size=10)

    pl.add_mesh(face1, color="orange", opacity=0.8, show_edges=True)
    pl.add_mesh(face2, color="deepskyblue", opacity=0.8, show_edges=True)

    add_normals(pl, face1, rounding_decimal, 0.25, "red")
    add_normals(pl, face2, rounding_decimal, 0.25, "navy")

    add_centroid_ray(pl, face1, face2, rounding_decimal)

    if show_rays:
        add_point_to_point_rays(pl, face1, face2, rounding_decimal)

    if obstacle is not None:
        pl.add_mesh(obstacle, color="green", opacity=0.35, show_edges=True)

    pl.add_text(
        overlay_text,
        position="lower_left",
        font_size=10,
        color=overlay_color,
        shadow=True
    )

    pl.show()


# ---------------------------------------------------------------------
# Geometry factory
# ---------------------------------------------------------------------

def case_parallel_facing():
    f1 = pv.Triangle([[0.0, 0.0, 0.0],
                      [1.0, 0.0, 0.0],
                      [0.0, 1.0, 0.0]])
    f2 = pv.Triangle([[0.0, 0.0, 1.0],
                      [0.0, 1.0, 1.0],
                      [1.0, 0.0, 1.0]])
    return f1, f2


def case_parallel_backfacing():
    f1, f2 = case_parallel_facing()
    f2.flip_faces(inplace=True)
    return f1, f2


def case_partial_visibility():
    f1 = pv.Triangle([[0.0, 0.0, 0.0],
                      [1.0, 0.0, 0.0],
                      [0.0, 1.0, 0.0]])
    f2 = pv.Triangle([[0.0, 0.0, 0.0],
                      [0.0, 0.0, 1.0],
                      [1.0, 0.0, 0.0]])
    f2.translate([0.0, 0.0, -0.25], inplace=True)
    return f1, f2


def case_shared_edge_perpendicular():
    f1 = pv.Triangle([[0.0, 0.0, 0.0],
                      [1.0, 0.0, 0.0],
                      [0.0, 1.0, 0.0]])
    f2 = pv.Triangle([[0.0, 0.0, 0.0],
                      [0.0, 1.0, 0.0],
                      [0.0, 0.0, 1.0]])
    return f1, f2


def case_shared_vertex_only():
    f1 = pv.Triangle([[0.0, 0.0, 0.0],
                      [1.0, 0.0, 0.0],
                      [0.0, 1.0, 0.0]])
    f2 = pv.Triangle([[0.0, 0.0, 0.0],
                      [0.0, 0.0, 1.0],
                      [1.0, 0.0, 1.0]])
    return f1, f2


def case_shared_vertex_only_almost_perpendicular():
    f1 = pv.Triangle([[0.0, 0.0, 0.0],
                      [1.0, 0.0, 0.0],
                      [0.0, 1.0, 0.0]])
    f2 = pv.Triangle([[0.0, 0.0, 0.0],
                      [0.0, 0.0, 1.0],
                      [1.0, 0.0, 1.0]])
    f2.points[1] += np.array([0.0, 0.0, 1e-8])
    return f1, f2


def case_import_like_noise_shared_edge(noise=1e-6):
    f1 = pv.Triangle([[ -5.0, -35.0,  0.0],
                      [ -5.0,  35.0,  0.0],
                      [ -5.0,  35.0, 10.0]])
    f2 = pv.Triangle([[-5.0 - noise,  35.0,      -noise],
                      [-5.0 - noise, -35.0,      -noise],
                      [ 5.0 - 2*noise, -35.0,      noise]])
    return f1, f2


def case_obstruction_full():
    f1, f2 = case_parallel_facing()
    obs = pv.Plane(i_size=2, j_size=2, i_resolution=1, j_resolution=1)
    obs.translate([0.0, 0.0, 0.5], inplace=True)
    return f1, f2, obs


def case_obstruction_partial():
    f1, f2 = case_parallel_facing()
    obs = pv.Plane(i_size=2, j_size=2, i_resolution=1, j_resolution=1)
    obs.translate([1.7, 0.0, 0.5], inplace=True)
    return f1, f2, obs


def case_obstruction_beyond_target():
    f1, f2 = case_parallel_facing()
    obs = pv.Rectangle([[0.0, 0.0, 2.0],
                        [0.0, 1.0, 2.0],
                        [1.0, 1.0, 2.0]])
    obs.triangulate(inplace=True)
    return f1, f2, obs


# ---------------------------------------------------------------------
# Run selected cases
# ---------------------------------------------------------------------

if __name__ == "__main__":

    rounding_list = [8, 6, 5, 4, 3]

    f1, f2 = case_parallel_facing()
    show_case(
        f1, f2,
        title="CASE 1 - Parallel facing triangles",
        expected="Visible in all visibility modes.",
        expected_dict={
            "visibility": {
                (False, False): True,
                (False, True):  True,
                (True,  False): True,
                (True,  True):  True,
            }
        },
        rounding_decimal=8
    )

    f1, f2 = case_parallel_backfacing()
    show_case(
        f1, f2,
        title="CASE 2 - Parallel backfacing triangles",
        expected="Not visible in all visibility modes.",
        expected_dict={
            "visibility": {
                (False, False): False,
                (False, True):  False,
                (True,  False): False,
                (True,  True):  False,
            }
        },
        rounding_decimal=8
    )

    f1, f2 = case_partial_visibility()
    show_case(
        f1, f2,
        title="CASE 3 - Partial visibility",
        expected="strict=False verbose=False => visible; strict=False verbose=True => visible + warning; strict=True => not visible.",
        expected_dict={
            "visibility": {
                (False, False): True,
                (False, True):  True,
                (True,  False): False,
                (True,  True):  False,
            }
        },
        rounding_decimal=8
    )

    f1, f2 = case_shared_edge_perpendicular()
    show_case(
        f1, f2,
        title="CASE 4 - Shared edge, perpendicular triangles",
        expected="Diagnostic case: decide intended strict behavior for valid edge-sharing visibility.",
        rounding_decimal=8
    )

    f1, f2 = case_shared_vertex_only()
    show_case(
        f1, f2,
        title="CASE 5 - Shared vertex only",
        expected="Diagnostic case: coincident pair ignored, remaining pairs decide visibility.",
        rounding_decimal=8
    )

    f1, f2 = case_shared_vertex_only_almost_perpendicular()
    show_case(
        f1, f2,
        title="CASE 6 - Shared vertex only, almost perpendicular",
        expected="Diagnostic case: tolerance-sensitive strict behavior.",
        rounding_decimal=8
    )

    for rd in rounding_list:
        f1, f2 = case_import_like_noise_shared_edge(noise=1e-6)
        show_case(
            f1, f2,
            title=f"CASE 7 - Import-like noisy shared edge | rounding_decimal={rd}",
            expected="Diagnostic case: find rounding threshold where touching behavior becomes stable.",
            rounding_decimal=rd
        )

    f1, f2, obs = case_obstruction_full()
    show_case(
        f1, f2, obstacle=obs,
        title="CASE 8 - Full obstruction between parallel faces",
        expected="Visibility True in all modes; obstruction False in all modes because the path is blocked.",
        expected_dict={
            "visibility": {
                (False, False): True,
                (False, True):  True,
                (True,  False): True,
                (True,  True):  True,
            },
            "obstruction": {
                (False, False): False,
                (False, True):  False,
                (True,  False): False,
                (True,  True):  False,
            }
        },
        rounding_decimal=8
    )

    f1, f2, obs = case_obstruction_partial()
    show_case(
        f1, f2, obstacle=obs,
        title="CASE 9 - Partial obstruction",
        expected="Diagnostic case: target behavior still to define for non-strict verbose / strict.",
        rounding_decimal=8
    )

    f1, f2, obs = case_obstruction_beyond_target()
    show_case(
        f1, f2, obstacle=obs,
        title="CASE 10 - Obstacle beyond target",
        expected="Visibility True in all modes; obstruction True in all modes because the segment is clear.",
        expected_dict={
            "visibility": {
                (False, False): True,
                (False, True):  True,
                (True,  False): True,
                (True,  True):  True,
            },
            "obstruction": {
                (False, False): True,
                (False, True):  True,
                (True,  False): True,
                (True,  True):  True,
            }
        },
        rounding_decimal=8
    )