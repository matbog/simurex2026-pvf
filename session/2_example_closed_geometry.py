# -*- coding: utf-8 -*-

# Imports
import pyvista as pv
import numpy as np
import pyviewfactor as pvf

# Examples with a closed geometry

# ###########
# 0. Geometry
# ###########

# create a raw sphere with pyvista
sphere = pv.Sphere(radius=3, center=(0, 0, 0), direction=(0, 0, 1),
                    theta_resolution=8, phi_resolution=8,
                    start_theta=0, end_theta=360,
                    start_phi=0, end_phi=180)

# and put the normals inwards please
sphere.flip_faces(inplace=True)


# let us chose a cell to compute view factors to
cell_extracted_id = 2
# let us chose a cell to compute view factors to
chosen_face = sphere.extract_cells(cell_extracted_id)
# convert to PolyData
chosen_face = pvf.fc_unstruc2poly(chosen_face)


# ##########################################################
# 1. View factor computation for one cell against all others
# ##########################################################


# "one array to contain them all"
F = np.zeros(sphere.n_cells)
# now let us compute the view factor to all other faces
for i in range(sphere.n_cells):
    if i != cell_extracted_id:
        face = sphere.extract_cells(i)  # other facet
        face = pvf.fc_unstruc2poly(face)  # convert to PolyData
        if pvf.get_visibility(face, chosen_face):
            # compute VF
            F[i] = pvf.compute_viewfactor(face,
                                          chosen_face,
                                          epsilon=1e-5,
                                          rounding_decimal=7)
        else:
            print("Problem, all cells should see each other.")

print("Sum check: \n (is Sum_i^n F_i =? 1)", np.sum(F))


# Plot the results
# put the scalar values in the geometry
sphere.cell_data["VF1"] = F

# Here you can save the results to a *.VTK file
sphere.save("./src_data/sphere.vtk")  # ... and save.

pl = pv.Plotter()  # instantiate 3D window
pl.add_mesh(sphere, scalars="VF1", cmap="jet")  # add mesh with a nice color scheme
outline = chosen_face.outline()  # gives you just the wireframe of that cell
pl.add_mesh(
    outline,
    color="red",  # pick a contrasting color
    line_width=3.0,  # thicker line so it stands out
    pickable=False
)
pl.show()

# ##########################################################
# 2. View factor computation for all cells against all others
# ##########################################################

# We keep the same geomtry

# Computation of the fonclete Fij matrix in parallel
F1 = pvf.compute_viewfactor_matrix(
    sphere,
    skip_visibility=True,
    skip_obstruction=True,
    strict_visibility=False,
    strict_obstruction=False,
    rounding_decimal=7,
    epsilon=1e-5,
    verbose=True)

print("Sum check: \n (is Sum_i^n F_i =? 1)", cell_extracted_id,
      "=", F1[:, cell_extracted_id].sum())
# Plot the results
# put the scalar values in the geometry
sphere.cell_data["VF2"] = F1[:, cell_extracted_id]
pl = pv.Plotter()
chosen = sphere.extract_cells(cell_extracted_id)
outline = chosen.outline()  # gives you just the wireframe of that cell
pl.add_mesh(
    outline,
    color="red",  # pick a contrasting color
    line_width=3.0,  # thicker line so it stands out
    pickable=False
)
pl.add_mesh(
    sphere,
    scalars="VF2",
    cmap="jet",
    opacity=1.0,
    show_edges=False,
    scalar_bar_args={"title": f"VF from cell {cell_extracted_id}"}
)
pl.add_title("View factors from cell {}".format(cell_extracted_id))
pl.show()

