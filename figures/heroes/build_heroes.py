"""Hero images for the home page's concept band, rendered in the blueprint style of figures/heroes/blueprint.py.

- gaia: the Gaia spacecraft, schematic. Proportions after ESA's descriptions: a deployable sunshield
  about 10 m across in 12 panels, a hexagonal service module, the payload module under a cylindrical
  thermal tent with the two telescope apertures. Not an engineering model.
- racks: a supercomputer hall, schematic: two rows of standard 42U racks (0.6 by 1.2 by 2.0 m) facing
  a cold aisle, as in the machine rooms of Deucalion and MareNostrum 5. Not a model of either.

Usage: ~/projects/HAYDNsim/.venv/bin/python figures/heroes/build_heroes.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from blueprint import Mesh, render  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "_local/heroes"
OUT.mkdir(parents=True, exist_ok=True)

GREY = [((86, 92, 102), 1.0), ((58, 63, 71), 1.0), ((150, 156, 166), 1.0), ((224, 164, 88), 1.0), ((40, 44, 50), 1.0), ((126, 132, 142), 1.0), ((14, 16, 20), 1.0)]


def gaia() -> Mesh:
    m = Mesh()
    P = lambda r, a, z: (r * math.cos(a), r * math.sin(a), z)
    # sunshield: 12 panels on a shallow cone, each with a raised frame and two cross ribs
    k, r0, r1 = 12, 1.95, 5.1
    for i in range(k):
        a0, a1 = 2 * math.pi * i / k + 0.01, 2 * math.pi * (i + 1) / k - 0.01
        z = lambda r: -0.28 * (r - r0) / (r1 - r0)
        m.quad(P(r0, a0, z(r0)), P(r1, a0, z(r1)), P(r1, a1, z(r1)), P(r0, a1, z(r0)), 0, 10 + i)
        for rr in (2.9, 3.9, 4.6):
            m.quad(P(rr, a0, z(rr) + 0.02), P(rr + 0.06, a0, z(rr) + 0.02), P(rr + 0.06, a1, z(rr) + 0.02), P(rr, a1, z(rr) + 0.02), 4, 10 + i)
        am = (a0 + a1) / 2
        m.quad(P(r0, am - 0.008, z(r0) + 0.025), P(r1, am - 0.008, z(r1) + 0.025), P(r1, am + 0.008, z(r1) + 0.025), P(r0, am + 0.008, z(r0) + 0.025), 4, 10 + i)
        # outer rim strip
        m.quad(P(r1 - 0.08, a0, z(r1) + 0.02), P(r1, a0, z(r1) + 0.02), P(r1, a1, z(r1) + 0.02), P(r1 - 0.08, a1, z(r1) + 0.02), 2, 10 + i)
    # service module: hexagonal prism with panelled sides
    hexo = [(1.9 * math.cos(math.pi / 3 * j + math.pi / 6), 1.9 * math.sin(math.pi / 3 * j + math.pi / 6)) for j in range(6)]
    m.prism(hexo, -0.05, 0.95, 1, 1)
    for j in range(6):
        (x0, y0), (x1, y1) = hexo[j], hexo[(j + 1) % 6]
        for f in (0.33, 0.66):
            xa, ya = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
            nx, ny = xa * 1.004, ya * 1.004
            m.quad((nx - 0.01 * (y1 - y0), ny + 0.01 * (x1 - x0), 0.05), (nx + 0.01 * (y1 - y0), ny - 0.01 * (x1 - x0), 0.05),
                   (nx + 0.01 * (y1 - y0), ny - 0.01 * (x1 - x0), 0.85), (nx - 0.01 * (y1 - y0), ny + 0.01 * (x1 - x0), 0.85), 4, 1)
    # thermal tent: a pleated 24-sided drum with a slightly domed roof, alternating tones
    n, R = 24, 1.72
    for j in range(n):
        a0, a1 = 2 * math.pi * j / n, 2 * math.pi * (j + 1) / n
        rj = R if j % 2 == 0 else R * 0.985
        m.quad(P(rj, a0, 0.95), P(rj, a1, 0.95), P(rj, a1, 2.95), P(rj, a0, 2.95), 2 if j % 2 == 0 else 5, 2)
        m.quad(P(rj, a0, 2.95), P(rj, a1, 2.95), P(R * 0.55, a1, 3.12), P(R * 0.55, a0, 3.12), 2, 2)
        m.tri(P(R * 0.55, a0, 3.12), P(R * 0.55, a1, 3.12), (0, 0, 3.16), 2, 2)
    # the two telescope apertures, 106.5 degrees apart: dark recesses with an amber rim
    for ac in (math.radians(-35), math.radians(-35 + 106.5)):
        w, z0, z1 = 0.62, 1.75, 2.65
        a0, a1 = ac - w / 2, ac + w / 2
        rr = R + 0.012
        m.quad(P(rr, a0, z0), P(rr, a1, z0), P(rr, a1, z1), P(rr, a0, z1), 6, 30)
        for (aa, bb, za, zb) in ((a0, a1, z0 - 0.04, z0), (a0, a1, z1, z1 + 0.04), (a0 - 0.03, a0, z0, z1), (a1, a1 + 0.03, z0, z1)):
            m.quad(P(rr + 0.004, aa, za), P(rr + 0.004, bb, za), P(rr + 0.004, bb, zb), P(rr + 0.004, aa, zb), 3, 31)
    return m


def racks() -> Mesh:
    m = Mesh()
    W, D, Hh, gap = 0.6, 1.2, 2.0, 1.2
    for row, y0 in enumerate((-gap / 2 - D, gap / 2)):
        for i in range(14):
            x0 = i * (W + 0.02)
            obj = row * 100 + i
            m.box(x0, y0, 0.0, x0 + W, y0 + D, Hh, 0, obj)
            # front doors facing the aisle: perforation as horizontal slats, and a status strip
            yf = y0 + D + 0.002 if row == 0 else y0 - 0.002
            for s in range(18):
                z = 0.12 + s * 0.098
                m.quad((x0 + 0.06, yf, z), (x0 + W - 0.06, yf, z), (x0 + W - 0.06, yf, z + 0.05), (x0 + 0.06, yf, z + 0.05), 4, obj)
            lit = (i * 7 + row * 3) % 5 == 0
            m.quad((x0 + 0.06, yf, 1.9), (x0 + 0.16, yf, 1.9), (x0 + 0.16, yf, 1.93), (x0 + 0.06, yf, 1.93), 3 if lit else 4, obj)
    # floor tiles of the raised floor
    for i in range(-2, 16):
        for j in range(-3, 3):
            m.quad((i * 0.6, j * 0.6, 0), ((i + 1) * 0.6, j * 0.6, 0), ((i + 1) * 0.6, (j + 1) * 0.6, 0), (i * 0.6, (j + 1) * 0.6, 0), 1, 999 + i * 10 + j)
    return m


def save(arr, name):
    Image.fromarray(arr, "RGBA").save(OUT / f"{name}.png")
    print("wrote", name, arr.shape)


if __name__ == "__main__":
    save(render(gaia(), cam=(12.5, -9.0, 4.2), look=(0, 0, 0.9), fov_deg=40, W=1200, H=800, materials=GREY), "gaia")
    save(render(racks(), cam=(-3.0, 0.05, 1.6), look=(8.0, 0.0, 1.0), fov_deg=58, W=1200, H=800, materials=GREY, crease_deg=40), "racks")
