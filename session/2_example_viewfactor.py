# -*- coding: utf-8 -*-

import pyvista as pv
from pyviewfactor import get_visibility, compute_viewfactor

# Basic example

# ###########
# 0. Geometry
# ###########

# Create a rectangle and a triangle facing each other
pointa1 = [0.0, 0.0, 0.0]
pointb1 = [1.0, 0.0, 0.0]
pointc1 = [0.0, 1.0, 0.0]
rectangle = pv.Rectangle([pointa1, pointb1, pointc1])

pointa2 = [0.0, 0.0, 1.0]
pointb2 = [0.0, 1.0, 1.0]
pointc2 = [1.0, 1.0, 1.0]
triangle = pv.Triangle([pointa2, pointb2, pointc2])

# #################################
# 1. Vizualitions with face normals
# #################################

pl = pv.Plotter()
pl.add_mesh(rectangle, color="lightblue", opacity=0.7)
pl.add_mesh(triangle, color="salmon", opacity=0.7)

# compute and glyph normals for mesh1
n1 = rectangle.compute_normals(cell_normals=True, point_normals=False)
arrows1 = n1.glyph(orient="Normals", factor=0.5)
pl.add_mesh(arrows1, color="blue")
# similarly for mesh2
n2 = triangle.compute_normals(cell_normals=True, point_normals=False)
arrows2 = n2.glyph(orient="Normals", factor=0.5)
pl.add_mesh(arrows2, color="darkred")

pl.show()

# ##########################################################
# 2. View factor computation for one cell against all others
# ##########################################################
if get_visibility(rectangle, triangle)[0]:
    F = compute_viewfactor(triangle, rectangle)
    print("VF from rectangle to triangle :", F)
else:
    print("Not facing each other")
