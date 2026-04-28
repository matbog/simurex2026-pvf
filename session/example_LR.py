# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 17:26:13 2026

@author: bogdanm
"""

import time
import numpy as np
import pyvista as pv
import pyviewfactor as pvf
from tqdm import tqdm


# ============================================================
# User parameters
# ============================================================
file = "./src_data/scene_LR_oriented_normals.vtk"
output_file = "./scene_LR_oriented_normals_results.vtk"

strict_visibility = True
strict_obstruction = True
rounding_decimal = 4
epsilon = 1e-3

# Cell to export in the mesh, e.g. mesh["FF_248"] = FFmat[:, 248]
target_cell_id = 248

# For time estimation of the naive method:
# use only a sample of columns to estimate the full runtime first
estimate_naive_time = True
sample_columns_for_estimate = 5


# ============================================================
# Helpers
# ============================================================
def compute_ff_column_naive(mesh, pre, j,
                            strict_visibility=True,
                            strict_obstruction=True,
                            rounding_decimal=4,
                            epsilon=1e-3):
    """
    Compute one column j of the view-factor matrix with the naive nested approach.
    Returns FF[:, j].
    """
    n_cells = mesh.n_cells
    ff_col = np.zeros(n_cells)

    chosen_face = mesh.extract_cells(j)
    chosen_face = pvf.fc_unstruc2poly(chosen_face)

    for i in range(n_cells):
        if i == j:
            continue

        face = mesh.extract_cells(i)
        face = pvf.fc_unstruc2poly(face)

        visible = pvf.get_visibility(
            face,
            chosen_face,
            strict=strict_visibility,
            verbose=False,
            rounding_decimal=rounding_decimal
        )[0]

        if not visible:
            continue

        unobstructed = pvf.get_obstruction(
            face,
            chosen_face,
            pre,
            strict=strict_obstruction,
            verbose=False
        )[0]

        if not unobstructed:
            continue

        vf = pvf.compute_viewfactor(
            face,
            chosen_face,
            epsilon=epsilon,
            rounding_decimal=rounding_decimal
        )

        ff_col[i] = vf

    return ff_col


def format_duration(seconds):
    """Pretty print a duration in s / min / h."""
    if seconds < 60:
        return f"{seconds:.2f} s"
    if seconds < 3600:
        return f"{seconds/60:.2f} min"
    return f"{seconds/3600:.2f} h"


# ============================================================
# Load mesh
# ============================================================
mesh = pv.read(file)
pre = pvf.FaceMeshPreprocessor(mesh, rounding_decimal=rounding_decimal)

n_cells = mesh.n_cells
print("\n>>> Start of test PVF matrix vs naive <<<\n")
print(f"Mesh file          : {file}")
print(f"Number of cells    : {n_cells}")
print(f"Target cell id     : {target_cell_id}")
print(f"strict_visibility  : {strict_visibility}")
print(f"strict_obstruction : {strict_obstruction}")
print("")


if not (0 <= target_cell_id < n_cells):
    raise ValueError(
        f"target_cell_id={target_cell_id} is out of bounds for a mesh with {n_cells} cells."
    )


# ============================================================
# 1) Estimate naive total runtime
# ============================================================
estimated_naive_total = None

if estimate_naive_time:
    n_sample = min(sample_columns_for_estimate, n_cells)
    sample_ids = np.linspace(0, n_cells - 1, n_sample, dtype=int)

    print("1. Estimating naive nested-loop runtime")
    print(f"   Sampling {n_sample} column(s): {sample_ids.tolist()}")

    t0 = time.time()
    for j in tqdm(sample_ids, desc="Naive runtime estimate"):
        _ = compute_ff_column_naive(
            mesh,
            pre,
            j,
            strict_visibility=strict_visibility,
            strict_obstruction=strict_obstruction,
            rounding_decimal=rounding_decimal,
            epsilon=epsilon
        )
    t_est = time.time() - t0

    avg_time_per_column = t_est / n_sample
    estimated_naive_total = avg_time_per_column * n_cells

    print(f"   Sample elapsed time         : {format_duration(t_est)}")
    print(f"   Average time per column     : {format_duration(avg_time_per_column)}")
    print(f"   Estimated full naive runtime: {format_duration(estimated_naive_total)}\n")


# ============================================================
# 2) Compute one naive reference column for comparison
# ============================================================
print("2. Naive computation for one target column")
t0 = time.time()

ff_seq_target = compute_ff_column_naive(
    mesh,
    pre,
    target_cell_id,
    strict_visibility=strict_visibility,
    strict_obstruction=strict_obstruction,
    rounding_decimal=rounding_decimal,
    epsilon=epsilon
)

naive_single_col_time = time.time() - t0
mesh[f"FFseq_{target_cell_id}"] = ff_seq_target

print(f"   Naive time for column {target_cell_id}: {format_duration(naive_single_col_time)}\n")


# ============================================================
# 3) Full matrix computation
# ============================================================
print("3. Full matrix computation")
t0 = time.time()

FFmat = pvf.compute_viewfactor_matrix(
    mesh,
    obstacles=mesh,
    skip_visibility=False,
    skip_obstruction=False,
    strict_visibility=strict_visibility,
    strict_obstruction=strict_obstruction,
    rounding_decimal=rounding_decimal,
    epsilon=epsilon,
    verbose=True
)

matrix_time = time.time() - t0
mesh[f"FF_{target_cell_id}"] = FFmat[:, target_cell_id]

print(f"\n   Full matrix computation time: {format_duration(matrix_time)}")


# ============================================================
# 4) Compare naive target column vs matrix target column
# ============================================================
ff_mat_target = FFmat[:, target_cell_id]

abs_diff = np.abs(ff_seq_target - ff_mat_target)
max_abs_diff = np.max(abs_diff)
mean_abs_diff = np.mean(abs_diff)

print("\n4. Comparison on target column")
print(f"   max(|FFseq - FFmat|)  = {max_abs_diff:.6e}")
print(f"   mean(|FFseq - FFmat|) = {mean_abs_diff:.6e}")

if estimated_naive_total is not None:
    if matrix_time > 0:
        speedup = estimated_naive_total / matrix_time
        print("\n5. Runtime comparison")
        print(f"   Estimated naive full runtime : {format_duration(estimated_naive_total)}")
        print(f"   Matrix full runtime          : {format_duration(matrix_time)}")
        print(f"   Estimated speed-up (matrix)  : x{speedup:.2f}")


# ============================================================
# 5) Save output
# ============================================================
mesh.save(output_file)

print(f"\nSaved result file: {output_file}")
print("\n>>> End of tests <<<\n")