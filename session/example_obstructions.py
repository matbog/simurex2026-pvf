# -*- coding: utf-8 -*-
"""
Created on Tue May 27 17:28:19 2025

@author: bogdanm
"""

import pyvista as pv
import pyviewfactor as pvf

# Example on how the obstruction function works


# let us first create two rectangles

pointa = [0.0, 0.0, 0.0]
pointb = [1.0, 0.0, 0.0]
pointc = [0.0, 1.0, 0.0]
rectangle_down = pv.Rectangle([pointa, pointb, pointc])

pointa = [0.0, 0.0, 1.0]
pointb = [0.0, 1.0, 1.0]
pointc = [1.0, 0.0, 1.0]
rectangle_up = pv.Rectangle([pointa, pointb, pointc])

# a circle will be the obstruction
z_translation, r = 0.5, 2
obstacle = pv.Circle(radius=r, resolution=10)
obstacle.triangulate(inplace=True)
# we translate the obstruction right between both rectangles
obstacle.translate([0, 0, z_translation], inplace=True)
# Define line segment
start = rectangle_down.cell_centers().points[0]
stop = rectangle_up.cell_centers().points[0]
# Perform ray trace
# points, ind = obstacle.ray_trace(start, stop)

# Create geometry to represent ray trace
ray = pv.Line(start, stop)

# Render the result
p = pv.Plotter()
p.add_mesh(obstacle, show_edges=True, opacity=0.5,
           color="red", lighting=False, label="obstacle")
p.add_mesh(rectangle_up, color="blue", line_width=5,
           opacity=0.9, label="rect up")
p.add_mesh(rectangle_down, color="yellow", line_width=5,
           opacity=0.9, label="rect down")
p.add_mesh(ray, color="green", line_width=5, label="ray trace")
p.show()


# Now we can use the get_obtruction function, to check for the obstruction,
# and see each cell of the obstruction mesh is in the way.
obstruction_cell = []
for idx in range(obstacle.n_cells):
    obs = obstacle.get_cell(idx).cast_to_polydata()
    visible = pvf.get_obstruction(rectangle_down, rectangle_up, obs,
                                  strict=False)
    if not visible[0]:
        print("Cell {} of the obstactle is in the way of the ".format(idx)
              + "centroids of rectangle_up and rectangle_down")
        obstruction_cell.append(idx)

obs = obstacle.extract_cells(obstruction_cell)

# if any intersection
if obs.n_cells > 0:
    p = pv.Plotter()
    p.add_mesh(obstacle, show_edges=True, opacity=0.4, color="red",
               lighting=False, label="obstacle")
    p.add_mesh(rectangle_up, color="blue", line_width=5, opacity=0.9,
               label="rect up")
    p.add_mesh(rectangle_down, color="orange", line_width=5, opacity=0.9,
               label="rect down")
    p.add_mesh(ray, color="black", line_width=5, label="ray trace")
    p.add_mesh(obs, show_edges=True, opacity=0.9, color="green", lighting=False,
               label="cell_obstrucion")
    p.add_legend()
    p.show()
