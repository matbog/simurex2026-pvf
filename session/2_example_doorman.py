# -*- coding: utf-8 -*-
from tqdm import tqdm
import numpy as np
import pyvista as pv
import pyviewfactor as pvf

# #######################################################################
# Second example : forma factor from the ground to the facets of a person
# #######################################################################

# The provided geomtry ais a persona standing in the corner of a
# patch of "ground"


def fc_Fwall(nom_vtk):
    # This function is bit more generic than this specific use case,
    # so it can be reused for other applications
    mesh = pv.read(nom_vtk)

    # find all types of walls : in this example only a ground
    wall_types = list(np.unique(mesh["geom_id"]))
    # remove the individual from the list (still named "cylinder"...)
    wall_types.remove("doorman")
    # where is the doorman in the list?
    index_doorman = np.where(mesh["geom_id"] == "doorman")[0]
    # prepare storage for the different walls in a dict
    dict_F = {}
    # loop over wall types
    for type_wall in wall_types:
        # prepare for storing doorman to wall view factor
        F = np.zeros(mesh.n_cells)
        # get the indices of this type of wall
        indices = np.where(mesh["geom_id"] == type_wall)[0]
        # loop over
        for i in indices:
            wall = mesh.extract_cells(i)
            wall = pvf.fc_unstruc2poly(wall)  # convert for normals
            # ... for each facet of the individual
            for idx in tqdm(index_doorman):
                face = mesh.extract_cells(idx)
                face = pvf.fc_unstruc2poly(face)  # convert for normals
                # check if faces can "see" each other
                if pvf.get_visibility(wall, face):
                    # compute face2wall view factor
                    Ffp = pvf.compute_viewfactor(wall, face)
                else:
                    Ffp = 0
                F[idx] = Ffp
        # store array F in e.g. dict_F["F_ceiling"]
        dict_F["F_" + type_wall.replace("\r", "")] = F
    return dict_F


# ##########################
# 0. Geometry of the doorman
# ##########################

# You can get the  doorman geomtry it directly from here:
# https://gitlab.com/arep-dev/pyViewFactor/-/blob/main/examples/example_doorman_clean.vtk
# ... or get it from this repository's examples
file = "./src_data/example_doorman_clean.vtk"

# compute the VFs for the doorman to the different wall types in the scene
dict_F = fc_Fwall(file)

# re-read and store
mesh = pv.read(file)
# loop over what is in the dictionary of view factors
for elt in dict_F.keys():
    mesh[elt.replace("\r", "")] = dict_F[elt]  # name the field
mesh.save("./src_data/example_doorman_VFground.vtk")  # store in the intial VTK

# have a look without paraview with fancy colors
mesh.plot(cmap="magma_r", lighting=False)
