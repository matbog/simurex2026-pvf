# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 13:47:51 2026

@author: bogdanm
"""

# -*- coding: utf-8 -*-
"""
Analytical validation example for pyViewFactor.

Configuration:
- one square plate of size L
- one adjacent rectangle at 90 degrees
- common edge of length L
- rectangle height H

The analytical formula used here is:

    h  = H / L
    h1 = sqrt(1 + h^2)
    h2 = h1^4 / (h^2 * (2 + h^2))

    F_12 = 1/4 + 1/pi * (
        h * atan(1/h)
        - h1 * atan(1/h1)
        - h^2/4 * ln(h2)
    )

where F_12 is the view factor from the square to the adjacent rectangle.
"""

import numpy as np
import pyvista as pv
import pyviewfactor as pvf
import matplotlib.pyplot as plt


def analytical_f12_square_to_adjacent_rectangle(h):
    h1 = np.sqrt(1.0 + h**2)
    h2 = h1**4 / (h**2 * (2.0 + h**2))
    return (
        0.25
        + 1.0 / np.pi
        * (
            h * np.arctan(1.0 / h)
            - h1 * np.arctan(1.0 / h1)
            - (h**2 / 4.0) * np.log(h2)
        )
    )


def build_geometry(L=1.0, H=1.0):
    """
    Square in the plane z=0.
    Adjacent rectangle in the plane y=0, sharing the edge y=z=0, x in [0, L].
    """
    square = pv.Rectangle([
        [0.0, 0.0, 0.0],
        [L,   0.0, 0.0],
        [0.0, L,   0.0]
    ])

    rectangle = pv.Rectangle([
        [0.0, 0.0, 0.0],
        [L,   0.0, 0.0],
        [0.0, 0.0, H]
    ])

    # Make sure normals are oriented so that both faces "see" each other
    vis = pvf.get_visibility(rectangle, square, strict=False)[0]
    if not vis:
        rectangle.flip_faces(inplace=True)

    vis = pvf.get_visibility(rectangle, square, strict=False)[0]
    if not vis:
        square.flip_faces(inplace=True)

    return square, rectangle


def numerical_f12_square_to_adjacent_rectangle(L=1.0, H=1.0, rounding_decimal=8):
    """
    compute_viewfactor(receiver, emitter) returns F_emitter->receiver,
    so to get F_square->rectangle we call:
        compute_viewfactor(rectangle, square)
    """
    square, rectangle = build_geometry(L=L, H=H)

    if not pvf.get_visibility(rectangle, square, strict=False,
                              rounding_decimal=rounding_decimal)[0]:
        raise RuntimeError("Faces are not visible with current orientation.")

    return pvf.compute_viewfactor(
        rectangle,   # receiver
        square,      # emitter
        rounding_decimal=rounding_decimal
    )


def main():
    L = 1.0
    h_values = np.array([0.25, 0.5, 1.0, 2.0, 4.0])

    ana = []
    num = []
    err = []

    for h in h_values:
        H = h * L
        f_ana = analytical_f12_square_to_adjacent_rectangle(h)
        f_num = numerical_f12_square_to_adjacent_rectangle(L=L, H=H)

        ana.append(f_ana)
        num.append(f_num)
        err.append(abs(f_num - f_ana) / abs(f_ana))

        print(
            f"h={h:>5.2f} | "
            f"analytical={f_ana:.8f} | "
            f"numerical={f_num:.8f} | "
            f"rel_error={err[-1]:.3e}"
        )

    ana = np.array(ana)
    num = np.array(num)
    err = np.array(err)

    plt.figure(figsize=(7, 5))
    plt.plot(h_values, ana, label="Analytical")
    plt.plot(h_values, num, "o", label="pyViewFactor")
    plt.xlabel("h = H / L")
    plt.ylabel("F(square → adjacent rectangle)")
    plt.title("Analytical validation")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    plt.figure(figsize=(7, 5))
    plt.semilogy(h_values, err, "o-")
    plt.xlabel("h = H / L")
    plt.ylabel("Relative error")
    plt.title("Relative error vs analytical solution")
    plt.grid(True)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()