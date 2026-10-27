"""Cerro Paranal as a blueprint-style rendered site model, for the figure on the field-guide page on
ESO and the VLT (figures/eso/build_eso_figure.py): the real terrain with 10 m and 50 m contours,
the levelled platform, the four Unit Telescope enclosures, UT2 open for the night, the tracks and
station pads, four Auxiliary Telescopes, VST, the VLTI laboratory and the control building. No
shadows; faces are toned by their angle to a fixed light only. Two views: the site from the west,
and a close-up of UT2 with its enclosure removed. Writes both themes as transparent WebP to
assets/img/guide/ and each view's camera, with the plan-derived positions, to
figures/eso/paranal_cameras.json for the drawn overlay.

Sources
- Terrain: Copernicus DEM GLO-30, tile Copernicus_DSM_COG_10_S25_00_W071_00_DEM.tif in _local/dem/
  (not tracked); it reads 2636.6 m at the array centre against ESO's 2635 m.
- Stations and Unit Telescopes: ESO, VLTI station coordinates
  (https://www.eso.org/observing/etc/doc/viscalc/vltistations.html), metres east and north of the
  array centre at latitude -24.62794830, longitude -70.40479659; the platform grid is rotated by
  nu = -18.984 degrees.
- VST, the VLTI laboratory and the control building: ESO, Paranal General Plan, mapped to east and
  north by an affine fit to the four Unit Telescopes (residuals under 1 m).
- Unit Telescope enclosures: a fixed concrete base and a co-rotating upper part with flat front and
  back and the shutter slit, about 29 m across and high. Open (ESO, VLT enclosure,
  https://www.eso.org/sci/facilities/paranal/telescopes/ut/enclosure.html), the shell stays and the
  doors clear a 9.5 m slit down the front and across the roof, its lower part closed by the
  windscreen. The telescope inside is schematic except the 8.2 m primary mirror.
- Auxiliary Telescopes on stations A0, G1, J2 and J3, ESO's "large" configuration.
- VISTA: at latitude -24.6157, longitude -70.3976, on its peak at 2518 m; enclosure about 20 m.

Usage: ~/projects/HAYDNsim/.venv/bin/python figures/eso/paranal_render.py [site|ut2]
  (numpy, scipy, numba, Pillow)
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numba as nb
import numpy as np
from PIL import Image, ImageFilter
from scipy.ndimage import map_coordinates

ROOT = Path(__file__).resolve().parents[2]
DEM = ROOT / "_local/dem"
OUT = ROOT / "assets/img/guide/paranal-render.webp"

Z, X0, Y0 = 14, 4986, 9348
CENTRE = (-24.62794830, -70.40479659)
NU = math.radians(-18.984)
ZPLAT = 2635.0
OPEN_UT = "UT2"  # the enclosure drawn open, with its telescope
BENCH = 9.0  # the control building's bench below the platform, metres
STATIONS = {  # E, N (m), ESO
    "A0": (-14.642, -55.812), "A1": (-9.434, -70.949), "B0": (-7.065, -53.212), "B1": (-1.863, -68.334),
    "B2": (0.739, -75.899), "B3": (3.348, -83.481), "B4": (5.945, -91.030), "B5": (8.547, -98.594),
    "C0": (0.487, -50.607), "C1": (5.691, -65.735), "C2": (8.296, -73.307), "C3": (10.896, -80.864),
    "D0": (15.628, -45.397), "D1": (26.039, -75.660), "D2": (31.243, -90.787), "E0": (30.760, -40.196),
    "G0": (45.896, -34.990), "G1": (66.716, -95.501), "G2": (38.063, -12.289), "H0": (76.150, -24.572),
    "I1": (96.711, -59.789), "J1": (106.648, -39.444), "J2": (114.460, -62.151), "J3": (80.628, 36.193),
    "J4": (75.424, 51.320), "J5": (67.618, 74.009), "J6": (59.810, 96.706), "K0": (106.397, -14.165),
    "L0": (113.977, -11.549), "M0": (121.535, -8.951),
}
UTS = {"UT1": (-9.925, -20.335), "UT2": (14.887, 30.502), "UT3": (44.915, 66.183), "UT4": (103.306, 43.999)}
ATS = ("A0", "G1", "J2", "J3")
VISTA = (-24.6157, -70.3976)
# ESO, Paranal General Plan: pixel positions read from the plan, mapped to east and north by an
# affine fit to the four Unit Telescopes (residuals under 1 m). The plan is to scale only around the
# summit (its roads carry break marks), so it is used for the platform and its buildings alone.
_PLAN_UT = {"UT1": (342, 224), "UT2": (371, 171), "UT3": (403, 131), "UT4": (465, 157)}
PLATFORM_PX = [(290, 85), (318, 52), (355, 35), (400, 28), (450, 30), (500, 42), (535, 62), (553, 95), (560, 140),
               (558, 190), (548, 240), (533, 280), (510, 310), (475, 330), (430, 343), (385, 345), (340, 335),
               (305, 312), (283, 280), (273, 235), (272, 180), (277, 130)]
VST_PX = (462, 75)
LAB_PX = [(399, 214), (428, 214), (428, 229), (399, 229)]
CONTROL_PX = [(292, 265), (305, 298), (336, 320)]
TRACKS = [("A0", "A1"), ("B0", "B5"), ("C0", "C3"), ("D0", "D2"), ("G2", "G1"), ("J2", "J6"), ("A0", "M0")]

W, H, SS = 1200, 800, 3  # output size and supersampling
CAM = np.array([-470.0, 40.0, 2635.0 + 330.0])  # west of the summit, as ESO's aerial photographs
LOOK = np.array([45.0, 10.0, 2626.0])
FOV = math.radians(36.0)
CAM_SITE = CAM.copy()  # the enclosures face this camera in every view
POSE = {"toward": (math.cos(math.atan2(CAM[1], CAM[0])), math.sin(math.atan2(CAM[1], CAM[0]))), "alt": 50.0}  # UT2's telescope
# views: the whole site, and a close-up of the opened Unit Telescope from the same side
VIEWS = {
    "site": dict(cam=CAM, look=LOOK, fov=FOV, size=(W, H)),
    "ut2": dict(cam=np.array([14.887 - 12.0, 30.502 + 52.0, 2635.0 + 44.0]), look=np.array([14.887, 30.502, 2643.0]),
                fov=math.radians(46.0), size=(600, 640)),
}
VIEW = sys.argv[1] if len(sys.argv) > 1 else "site"
CAM, LOOK, FOV, (W, H) = VIEWS[VIEW]["cam"], VIEWS[VIEW]["look"], VIEWS[VIEW]["fov"], VIEWS[VIEW]["size"]
SUN = (math.radians(285.0), math.radians(21.0))  # the fixed light that tones the faces (no shadows): azimuth, altitude


# ------------------------------------------------------------------ geometry helpers
def pq_to_en(p: float, q: float) -> tuple[float, float]:
    """ESO platform coordinates to east and north, by the platform rotation."""
    c, s = math.cos(NU), math.sin(NU)
    return p * c - q * s, p * s + q * c


class Mesh:
    def __init__(self):
        self.v, self.t, self.c = [], [], []

    def tri(self, a, b, c, col):
        n = len(self.v)
        self.v += [a, b, c]
        self.t.append((n, n + 1, n + 2))
        self.c.append(col)

    def quad(self, a, b, c, d, col):
        self.tri(a, b, c, col)
        self.tri(a, c, d, col)

    def prism(self, outline, z0, z1, col_side, col_top, col_bottom=None):
        """A vertical prism over a convex outline (counter-clockwise, E/N), from z0 to z1."""
        k = len(outline)
        if sum(outline[i][0] * outline[(i + 1) % k][1] - outline[(i + 1) % k][0] * outline[i][1] for i in range(k)) < 0:
            outline = outline[::-1]
        for i in range(k):
            (x0, y0), (x1, y1) = outline[i], outline[(i + 1) % k]
            self.quad((x0, y0, z0), (x1, y1, z0), (x1, y1, z1), (x0, y0, z1), col_side)
        cx = sum(p[0] for p in outline) / k
        cy = sum(p[1] for p in outline) / k
        for i in range(k):
            (x0, y0), (x1, y1) = outline[i], outline[(i + 1) % k]
            self.tri((cx, cy, z1), (x0, y0, z1), (x1, y1, z1), col_top)

    def dome(self, cx, cy, z0, r, col, n=24, m=8):
        for j in range(m):
            a0, a1 = (math.pi / 2) * j / m, (math.pi / 2) * (j + 1) / m
            for i in range(n):
                b0, b1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
                p = lambda a, b: (cx + r * math.cos(a) * math.cos(b), cy + r * math.cos(a) * math.sin(b), z0 + r * math.sin(a))
                self.quad(p(a0, b0), p(a0, b1), p(a1, b1), p(a1, b0), col)


def rot(pts, cx, cy, ang):
    c, s = math.cos(ang), math.sin(ang)
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in pts]


ALU = (0.80, 0.80, 0.82)
BEIGE = (0.86, 0.80, 0.72)
PANEL = (0.88, 0.84, 0.78)
ROOF = (0.70, 0.70, 0.72)
CONCRETE = (0.66, 0.64, 0.61)
DARK = (0.08, 0.08, 0.09)
WHITE = (0.92, 0.92, 0.92)
TRACK = (0.78, 0.77, 0.74)
PAD = (0.74, 0.73, 0.70)


def unit_telescope(m: Mesh, cx, cy, z0, facing, opened=False):
    """A Unit Telescope enclosure, after ESO's photographs, from convex parts: a dark plinth on its
    recessed ring of stilts, the concrete drum with its band of windows, and the co-rotating upper
    part, an octagon in plan with flat front and back, the shutter slit running down the front and
    across the roof. 29 m across, about 29 m high."""
    c, s = math.cos(facing), math.sin(facing)
    tr2 = lambda pts: [(cx + x * c - y * s, cy + x * s + y * c) for x, y in pts]
    tr = lambda x, y, z: (cx + x * c - y * s, cy + x * s + y * c, z)
    circ = lambda r, k=40: [(r * math.cos(2 * math.pi * i / k), r * math.sin(2 * math.pi * i / k)) for i in range(k)]
    m.prism(tr2(circ(12.6)), z0, z0 + 2.4, DARK, DARK)
    m.prism(tr2(circ(14.2)), z0 + 2.4, z0 + 3.0, DARK, DARK)
    m.prism(tr2(circ(13.6)), z0 + 3.0, z0 + 10.0, BEIGE, BEIGE)
    m.prism(tr2(circ(13.66)), z0 + 5.6, z0 + 6.8, DARK, DARK)
    # the upper part, closed as in daylight: a 20-sided body with the front and back cut flat, the
    # slit's two door seams down the front and across the roof
    up = []
    for i in range(20):
        a_ = 2 * math.pi * (i + 0.5) / 20
        x, y = 13.6 * math.cos(a_), 13.6 * math.sin(a_)
        up.append((max(-12.0, min(12.0, x)), y))
    up = [q for i, q in enumerate(up) if i == 0 or abs(q[0] - up[i - 1][0]) + abs(q[1] - up[i - 1][1]) > 1e-6]
    if opened == "removed":
        return
    if opened:
        # open for the night (ESO, VLT enclosure): the shell stays, the two doors are drawn back from
        # the 9.5 m slit down the front and across the roof, and the silvered windscreen closes the
        # slit's lower part
        hs, zr, zw = 4.75, z0 + 28.4, z0 + 19.0
        k_ = len(up)
        for i in range(k_):
            (x0, y0), (x1, y1) = up[i], up[(i + 1) % k_]
            if abs(x0 - 12.0) < 1e-6 and abs(x1 - 12.0) < 1e-6:  # the flat front, split at the slit
                ya, yb = sorted((y0, y1))
                for u0, u1 in ((ya, min(yb, -hs)), (max(ya, hs), yb)):
                    if u1 > u0:
                        m.quad(tr(12.0, u0, z0 + 10.0), tr(12.0, u1, z0 + 10.0), tr(12.0, u1, zr), tr(12.0, u0, zr), PANEL)
                u0, u1 = max(ya, -hs), min(yb, hs)
                if u1 > u0:
                    m.quad(tr(12.0, u0, z0 + 10.0), tr(12.0, u1, z0 + 10.0), tr(12.0, u1, zw), tr(12.0, u0, zw), ALU)
                continue
            m.quad(tr(x0, y0, z0 + 10.0), tr(x1, y1, z0 + 10.0), tr(x1, y1, zr), tr(x0, y0, zr), PANEL)
        for piece in (clip_poly(up, 0, 1, hs), clip_poly(up, 0, -1, hs), clip_poly(clip_poly(clip_poly(up, -1, 0, 10.0), 0, 1, -hs - 0.01), 0, -1, -hs - 0.01)):
            if len(piece) >= 3:
                m.prism(tr2(piece), zr, z0 + 29.0, ROOF, ROOF)
        for y in (-hs, hs):  # the slit's edges, where the doors meet when closed
            m.quad(tr(12.0, y, zr), tr(-10.0, y, zr), tr(-10.0, y, z0 + 29.0), tr(12.0, y, z0 + 29.0), DARK)
        return
    m.prism(tr2(up), z0 + 10.0, z0 + 29.0, PANEL, ROOF)
    for y in (-4.5, 4.5):
        m.quad(tr(12.05, y - 0.18, z0 + 12.0), tr(12.05, y + 0.18, z0 + 12.0), tr(12.05, y + 0.18, z0 + 29.0), tr(12.05, y - 0.18, z0 + 29.0), DARK)
        m.quad(tr(-10.0, y - 0.18, z0 + 29.05), tr(12.0, y - 0.18, z0 + 29.05), tr(12.0, y + 0.18, z0 + 29.05), tr(-10.0, y + 0.18, z0 + 29.05), DARK)


def clip_poly(poly, a, b, c):
    """The part of a convex polygon where a*x + b*y >= c (Sutherland-Hodgman, one half-plane)."""
    out = []
    for i in range(len(poly)):
        p, q = poly[i], poly[(i + 1) % len(poly)]
        fp, fq = a * p[0] + b * p[1] - c, a * q[0] + b * q[1] - c
        if fp >= 0:
            out.append(p)
        if (fp >= 0) != (fq >= 0):
            t = fp / (fp - fq)
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def tube(m: Mesh, p0, p1, r, col, k=14, caps=True):
    """A cylinder of radius r from point p0 to point p1, outward faces counter-clockwise."""
    p0, p1 = np.array(p0, float), np.array(p1, float)
    a = p1 - p0
    a /= np.linalg.norm(a)
    u = np.cross(a, [0.0, 0.0, 1.0]) if abs(a[2]) < 0.9 else np.cross(a, [1.0, 0.0, 0.0])
    u /= np.linalg.norm(u)
    v = np.cross(a, u)
    ring = [(math.cos(2 * math.pi * i / k), math.sin(2 * math.pi * i / k)) for i in range(k)]
    P0 = [tuple(p0 + r * (c * u + s_ * v)) for c, s_ in ring]
    P1 = [tuple(p1 + r * (c * u + s_ * v)) for c, s_ in ring]
    for i in range(k):
        j = (i + 1) % k
        m.quad(P0[i], P0[j], P1[j], P1[i], col)
    if caps:
        for i in range(k):
            j = (i + 1) % k
            m.tri(tuple(p1), P1[i], P1[j], col)
            m.tri(tuple(p0), P0[j], P0[i], col)


def obox(m: Mesh, c, axes, half, col):
    """A box centred on c with edges along the three axes, half-extents half, faces outward."""
    c = np.array(c, float)
    ax = [np.array(a, float) / np.linalg.norm(a) * hh for a, hh in zip(axes, half)]
    P = {(i, j, k): tuple(c + i * ax[0] + j * ax[1] + k * ax[2]) for i in (-1, 1) for j in (-1, 1) for k in (-1, 1)}
    faces = [[(1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)], [(-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1)],
             [(-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1)], [(-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)],
             [(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)], [(-1, -1, -1), (-1, 1, -1), (1, 1, -1), (1, -1, -1)]]
    for f in faces:
        q = [np.array(P[v]) for v in f]
        nrm = np.cross(q[1] - q[0], q[2] - q[0])
        if nrm @ (sum(q) / 4 - c) < 0:
            q = q[::-1]
        m.quad(*map(tuple, q), col)


def ut_telescope(m: Mesh, cx, cy, z0, toward, alt):
    """The telescope inside an opened Unit Telescope, schematic except the primary mirror: an
    azimuth floor, the fork, the primary mirror (8.2 m, ESO) in its cell, a Serrurier truss and the
    secondary-mirror ring, pointing at altitude alt toward the horizontal direction toward."""
    h = np.array([toward[0], toward[1], 0.0]); h /= np.linalg.norm(h)
    lat = np.array([-h[1], h[0], 0.0])
    d = h * math.cos(alt) + np.array([0, 0, 1.0]) * math.sin(alt)
    zf, za = z0 + 10.6, z0 + 18.5  # the azimuth floor and the elevation axis
    o = np.array([cx, cy, za])
    zv = np.array([0, 0, 1.0])
    tube(m, (cx, cy, z0 + 9.6), (cx, cy, zf), 7.2, CONCRETE, 40)  # azimuth floor
    obox(m, (cx, cy, zf + 0.9), (h, lat, zv), (2.6, 7.4, 0.9), ROOF)  # the fork's base
    for sg in (1, -1):
        obox(m, np.array([cx, cy, (zf + za) / 2 + 0.6]) + lat * sg * 6.6, (h, lat, zv), (2.6, 0.8, (za - zf) / 2 + 0.6), ROOF)  # yoke
        # the Nasmyth platforms at either end of the elevation axis, an instrument on each
        obox(m, o + lat * sg * 9.0 - zv * 2.6, (h, lat, zv), (3.2, 1.6, 0.25), CONCRETE)
        obox(m, o + lat * sg * 9.0 - zv * 1.3, (h, lat, zv), (1.6, 1.2, 1.05), WHITE)
    tube(m, o - lat * 7.6, o + lat * 7.6, 0.7, ROOF, 12)  # elevation axis
    c1 = o - d * 2.2
    tube(m, c1 - d * 1.2, c1, 4.7, ROOF, 40)  # mirror cell
    tube(m, c1, c1 + d * 0.25, 4.1, WHITE, 40)  # the primary mirror, 8.2 m
    m2 = o + d * 10.8
    tube(m, m2 - d * 0.5, m2 + d * 0.5, 1.7, ROOF, 24)  # secondary ring
    e1 = np.cross(d, lat)
    for i in range(8):  # truss
        a0 = 2 * math.pi * i / 8
        a1 = a0 + (math.pi / 4 if i % 2 == 0 else -math.pi / 4)
        q0 = c1 + 4.3 * (math.cos(a0) * lat + math.sin(a0) * e1)
        q1 = m2 + 1.6 * (math.cos(a1) * lat + math.sin(a1) * e1)
        tube(m, q0, q1, 0.3, ROOF, 6, caps=False)


def aux_telescope(m: Mesh, cx, cy, z0, facing):
    box = rot([(-1.9, -1.9), (1.9, -1.9), (1.9, 1.9), (-1.9, 1.9)], cx, cy, facing)
    m.prism(box, z0, z0 + 2.6, WHITE, WHITE)
    m.dome(cx, cy, z0 + 2.6, 2.1, WHITE, 18, 6)


def build_scene(height, plan):
    m = Mesh()
    zb = ZPLAT
    # the tracks, station pads and apron are painted on the ground in the shading pass
    facing = math.atan2(CAM_SITE[1], CAM_SITE[0])  # the slits toward the viewer, as in ESO's photographs
    for name, (e, n) in UTS.items():
        unit_telescope(m, e, n, zb, facing, opened=(name == OPEN_UT) and ("removed" if VIEW == "ut2" else True))
    e, n = UTS[OPEN_UT]
    # pointed out through the slit, which faces the site view
    ut_telescope(m, e, n, zb, POSE["toward"], math.radians(POSE["alt"]))
    for name in ATS:
        e, n = STATIONS[name]
        aux_telescope(m, e, n, zb, NU)
    # VST on the platform's north end: an octagonal enclosure 13 m across, 12 m high, roof slit
    vx, vy = plan(*VST_PX)
    octo = [(6.5 * math.cos(math.pi / 8 + math.pi / 4 * i), 6.5 * math.sin(math.pi / 8 + math.pi / 4 * i)) for i in range(8)]
    m.prism(rot(octo, vx, vy, 0), zb, zb + 3, BEIGE, BEIGE)
    m.prism(rot(octo, vx, vy, 0.3), zb + 3, zb + 12, PANEL, ROOF)
    # the VLTI laboratory: a low white building over the delay-line tunnel
    m.prism([plan(*q) for q in LAB_PX], zb, zb + 4.5, WHITE, WHITE)
    # the control building: a two-storey block, 14 m deep, bending along the platform's south-west
    # edge on a bench cut 9 m below it, its roof just above the platform; a band of windows
    pts = [plan(*q) for q in CONTROL_PX]
    for (a0, b0), (a1, b1) in zip(pts[:-1], pts[1:]):
        L = math.hypot(a1 - a0, b1 - b0)
        ux, uy = (a1 - a0) / L, (b1 - b0) / L
        a0, b0, a1, b1 = a0 - ux * 7, b0 - uy * 7, a1 + ux * 7, b1 + uy * 7
        nx, ny = -uy * 7, ux * 7
        m.prism([(a0 - nx, b0 - ny), (a1 - nx, b1 - ny), (a1 + nx, b1 + ny), (a0 + nx, b0 + ny)], zb - BENCH, zb + 1.0, WHITE, ROOF)
        k_ = 1.01
        m.prism([(a0 - nx * k_, b0 - ny * k_), (a1 - nx * k_, b1 - ny * k_), (a1 + nx * k_, b1 + ny * k_), (a0 + nx * k_, b0 + ny * k_)], zb - BENCH + 3.2, zb - BENCH + 4.6, DARK, DARK)
    ve, vn = VISTA_EN
    zv = float(height(np.array([ve]), np.array([vn]))[0])
    ring = [(9.8 * math.cos(2 * math.pi * i / 32), 9.8 * math.sin(2 * math.pi * i / 32)) for i in range(32)]
    m.prism(rot(ring, ve, vn, 0), zv - 1, zv + 9, WHITE, WHITE)
    m.dome(ve, vn, zv + 9, 9.8, WHITE, 32, 10)
    return m


def _hull_pts(pts):
    p = sorted(pts)
    cr = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for q in p:
        while len(lo) > 1 and cr(lo[-2], lo[-1], q) <= 0:
            lo.pop()
        lo.append(q)
    for q in reversed(p):
        while len(up) > 1 and cr(up[-2], up[-1], q) <= 0:
            up.pop()
        up.append(q)
    return lo[:-1] + up[:-1]


def pix(lat, lon):
    n = 2 ** Z
    x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return (x - X0) * 256, (y - Y0) * 256


COP = DEM / "Copernicus_DSM_COG_10_S25_00_W071_00_DEM.tif"


def load_dem():
    """The Copernicus DEM GLO-30 tile (TanDEM-X, 2011 to 2015, 1 arcsecond) and its georeference."""
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(COP)
    tp, sc = im.tag_v2[33922], im.tag_v2[33550]
    return np.asarray(im, dtype=float), (tp[3], tp[4], sc[0], sc[1])


# ------------------------------------------------------------------ rasteriser
@nb.njit(cache=True)
def raster(sx, sy, sz, tris, w, h, zbuf, ids, b1, b2):
    for t in range(tris.shape[0]):
        i0, i1, i2 = tris[t, 0], tris[t, 1], tris[t, 2]
        if sz[i0] <= 0 or sz[i1] <= 0 or sz[i2] <= 0:
            continue
        x0, y0, x1, y1, x2, y2 = sx[i0], sy[i0], sx[i1], sy[i1], sx[i2], sy[i2]
        area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
        if abs(area) < 1e-12:
            continue
        minx = max(int(math.floor(min(x0, x1, x2))), 0)
        maxx = min(int(math.ceil(max(x0, x1, x2))), w - 1)
        miny = max(int(math.floor(min(y0, y1, y2))), 0)
        maxy = min(int(math.ceil(max(y0, y1, y2))), h - 1)
        if minx > maxx or miny > maxy:
            continue
        iz0, iz1, iz2 = 1.0 / sz[i0], 1.0 / sz[i1], 1.0 / sz[i2]
        for py in range(miny, maxy + 1):
            for px in range(minx, maxx + 1):
                cx, cy = px + 0.5, py + 0.5
                w0 = ((x1 - cx) * (y2 - cy) - (x2 - cx) * (y1 - cy)) / area
                w1 = ((x2 - cx) * (y0 - cy) - (x0 - cx) * (y2 - cy)) / area
                w2 = 1.0 - w0 - w1
                if w0 < -1e-7 or w1 < -1e-7 or w2 < -1e-7:
                    continue
                iz = w0 * iz0 + w1 * iz1 + w2 * iz2
                if iz > zbuf[py, px]:
                    zbuf[py, px] = iz
                    ids[py, px] = t
                    # perspective-correct barycentrics
                    q0, q1, q2 = w0 * iz0 / iz, w1 * iz1 / iz, w2 * iz2 / iz
                    b1[py, px] = q1
                    b2[py, px] = q2


def main() -> None:
    dem, (lon0, lat0, dlon, dlat) = load_dem()
    phi = math.radians(CENTRE[0])
    mlat = 111132.954 - 559.822 * math.cos(2 * phi) + 1.175 * math.cos(4 * phi)  # metres per degree
    mlon = 111412.84 * math.cos(phi) - 93.5 * math.cos(3 * phi)

    def raw(e, n):
        lat = CENTRE[0] + np.asarray(n) / mlat
        lon = CENTRE[1] + np.asarray(e) / mlon
        return map_coordinates(dem, [(lat0 - lat) / dlat - 0.5, (lon - lon0) / dlon - 0.5], order=3, mode="nearest")

    global VISTA_EN
    VISTA_EN = ((VISTA[1] - CENTRE[1]) * mlon, (VISTA[0] - CENTRE[0]) * mlat)

    # the plan's calibration: an affine map from plan pixels to east and north
    A = np.array([[x, y, 1.0] for x, y in _PLAN_UT.values()])
    cE = np.linalg.lstsq(A, [UTS[k][0] for k in _PLAN_UT], rcond=None)[0]
    cN = np.linalg.lstsq(A, [UTS[k][1] for k in _PLAN_UT], rcond=None)[0]
    plan = lambda x, y: (float(cE @ [x, y, 1.0]), float(cN @ [x, y, 1.0]))
    # the platform: the rounded hull of the facilities, 25 m beyond the Unit Telescopes and VST,
    # 14 m beyond the outermost station pads and 12 m beyond the laboratory, which matches ESO's
    # aerial photographs, where the enclosures stand close to the edge of the cut
    ring_pts = []
    for (e, n), r in [(v, 25.0) for v in UTS.values()] + [(plan(*VST_PX), 25.0)] + [(v, 14.0) for v in STATIONS.values()] + [(plan(*q), 12.0) for q in LAB_PX]:
        ring_pts += [(e + r * math.cos(t), n + r * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 36, endpoint=False)]
    poly = np.array(_hull_pts(ring_pts))
    from matplotlib.path import Path as MPath
    ppath = MPath(poly)
    from scipy.ndimage import distance_transform_edt
    # distance outside the platform on a 2 m grid, for the cut slopes
    gx = np.arange(poly[:, 0].min() - 120, poly[:, 0].max() + 120, 2.0)
    gy = np.arange(poly[:, 1].min() - 120, poly[:, 1].max() + 120, 2.0)
    GX, GY = np.meshgrid(gx, gy)
    ins = ppath.contains_points(np.stack([GX.ravel(), GY.ravel()], 1)).reshape(GX.shape)
    dist_out = distance_transform_edt(~ins) * 2.0

    def outside_dist(e, n):
        return map_coordinates(dist_out, [(np.asarray(n) - gy[0]) / 2.0, (np.asarray(e) - gx[0]) / 2.0], order=1, mode="constant", cval=1.0e4)
    c, s = math.cos(NU), math.sin(NU)
    allpts = list(STATIONS.values()) + list(UTS.values())
    P = [e * c + n * s for e, n in allpts]
    Q = [-e * s + n * c for e, n in allpts]
    p0, p1, q0, q1 = min(P) - 22, max(P) + 22, min(Q) - 22, max(Q) + 22

    cpts = np.array([plan(*q) for q in CONTROL_PX])

    def bench_dist(e, n):
        e, n = np.asarray(e, float), np.asarray(n, float)
        d = np.full(e.shape, 1e9)
        for (a0, b0), (a1, b1) in zip(cpts[:-1], cpts[1:]):
            L = math.hypot(a1 - a0, b1 - b0); ux, uy = (a1 - a0) / L, (b1 - b0) / L
            t = np.clip((e - a0) * ux + (n - b0) * uy, -7.0, L + 7.0)
            d = np.minimum(d, np.hypot(e - (a0 + t * ux), n - (b0 + t * uy)))
        return d

    # The elevation data postdates the levelling but its 30 m cells round the escarpment off. Within
    # 120 m of the platform it is sharpened (an unsharp mask, sigma 15 m, gain 1.6), which steepens
    # the cut the data already holds without inventing a profile.
    from scipy.ndimage import gaussian_filter
    ge = np.arange(poly[:, 0].min() - 160, poly[:, 0].max() + 160, 3.0)
    gn = np.arange(poly[:, 1].min() - 160, poly[:, 1].max() + 160, 3.0)
    GE, GN = np.meshgrid(ge, gn)
    RG = raw(GE, GN)
    SG = RG + 1.6 * (RG - gaussian_filter(RG, 5.0))

    def sharp(e, n):
        return map_coordinates(SG, [(np.asarray(n) - gn[0]) / 3.0, (np.asarray(e) - ge[0]) / 3.0], order=1, mode="nearest")

    def height(e, n):
        e, n = np.asarray(e, float), np.asarray(n, float)
        z = raw(e, n)
        d_ = outside_dist(e, n)
        wgt = np.clip((150.0 - d_) / 40.0, 0, 1)
        z = np.where(wgt > 0, z * (1 - wgt) + sharp(e, n) * wgt, z)
        dout = outside_dist(e, n)
        # the levelled platform, and its cut slope down to the natural ground at about 35 degrees
        zslope = ZPLAT - dout * math.tan(math.radians(35))
        zz = np.where(dout <= 0, ZPLAT, np.where(z < zslope, zslope, z))

        bd = bench_dist(e, n)
        zb_ = ZPLAT - BENCH + np.clip(bd - 11.0, 0, None) * math.tan(math.radians(40))
        return np.where(bd < 11.0, ZPLAT - BENCH, np.minimum(zz, zb_))

    # terrain mesh
    step = 9.0
    E = np.arange(-3200, 3600, step)
    N = np.arange(-2600, 4400, step)
    EE, NN = np.meshgrid(E, N)
    ZZ = height(EE, NN)
    def grid_mesh(EE, NN, ZZ):
        nr, ncol = EE.shape
        v = np.stack([EE.ravel(), NN.ravel(), ZZ.ravel()], 1)
        ix = np.arange(nr * ncol).reshape(nr, ncol)
        a, b, cc, d = ix[:-1, :-1].ravel(), ix[:-1, 1:].ravel(), ix[1:, 1:].ravel(), ix[1:, :-1].ravel()
        return v, np.concatenate([np.stack([a, b, cc], 1), np.stack([a, cc, d], 1)])
    nr, ncol = EE.shape
    tv = np.stack([EE.ravel(), NN.ravel(), ZZ.ravel()], 1)
    idx = np.arange(nr * ncol).reshape(nr, ncol)
    a, b, cc, d = idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()
    tt = np.concatenate([np.stack([a, b, cc], 1), np.stack([a, cc, d], 1)])
    # terrain colour: desert ground, a little lighter on the levelled platform
    zc = tv[:, 2]
    base = np.array([0.62, 0.34, 0.22])
    tcol_v = np.tile(base, (len(tv), 1)) * (0.92 + 0.12 * np.clip((zc - 2200) / 450, 0, 1))[:, None]
    dv = outside_dist(tv[:, 0], tv[:, 1])
    plat = dv <= 0
    tcol_v[plat] = np.array([0.36, 0.25, 0.20])  # the platform's dark gravel
    natural = raw(tv[:, 0], tv[:, 1])
    scree = (dv > 0) & (tv[:, 2] - natural > 1.0)
    tcol_v[scree] = np.array([0.40, 0.38, 0.36])  # the grey scree of the cut slope
    # paved concrete around the telescopes: within 21 m of a UT
    ut = np.array(list(UTS.values()))
    dut = np.min(np.hypot(tv[:, 0, None] - ut[None, :, 0], tv[:, 1, None] - ut[None, :, 1]), axis=1)
    tcol_v[plat & (dut < 21)] = np.array([0.72, 0.71, 0.68])
    # relief detail from the terrain's own curvature: hollows darker, crests lighter
    from scipy.ndimage import laplace
    curv = laplace(ZZ)
    cv = np.clip(1.0 - 0.06 * curv.ravel(), 0.75, 1.15)
    tcol_v *= cv[:, None]
    tcol = tcol_v[tt[:, 0]]


    m = build_scene(height, plan)
    ov = np.array(m.v, float)
    ot = np.array(m.t, np.int64) + len(tv)
    oc = np.array(m.c, float)
    V = np.concatenate([tv, ov])
    T = np.concatenate([tt, ot]).astype(np.int64)
    C = np.concatenate([tcol, oc])
    nterr = len(tt)

    # per-triangle normals, and smooth vertex normals for the terrain
    tn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    tn /= np.linalg.norm(tn, axis=1, keepdims=True) + 1e-12
    tn[tn[:, 2] < 0] *= -1  # terrain normals point up; object faces fixed below
    vn = np.zeros_like(tv)
    for k in range(3):
        np.add.at(vn, tt[:, k], tn[:nterr])
    vn /= np.linalg.norm(vn, axis=1, keepdims=True) + 1e-12
    # object face normals: orient away from each object's local centre column
    on = np.cross(V[ot[:, 1]] - V[ot[:, 0]], V[ot[:, 2]] - V[ot[:, 0]])
    on /= np.linalg.norm(on, axis=1, keepdims=True) + 1e-12
    cen = V[ot].mean(1)
    tn[nterr:] = on

    # camera
    fwd = LOOK - CAM
    fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, [0, 0, 1.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    w, h = W * SS, H * SS
    Fp = (w / 2) / math.tan(FOV / 2)
    q = V - CAM
    zc_ = q @ fwd
    sx = w / 2 + Fp * (q @ right) / np.maximum(zc_, 1e-3)
    sy = h / 2 - Fp * (q @ up) / np.maximum(zc_, 1e-3)
    zbuf = np.zeros((h, w))
    ids = -np.ones((h, w), np.int64)
    bb1 = np.zeros((h, w))
    bb2 = np.zeros((h, w))
    raster(sx, sy, zc_, T, w, h, zbuf, ids, bb1, bb2)

    # shadow map: orthographic from the sun
    saz, sal = SUN
    L = np.array([math.sin(saz) * math.cos(sal), math.cos(saz) * math.cos(sal), math.sin(sal)])
    lr = np.cross(L, [0, 0, 1.0])
    lr /= np.linalg.norm(lr)
    lu = np.cross(lr, -L)
    sm = 8192
    lx, ly = V @ lr, V @ lu
    sel = np.ones(len(V), bool)
    ax0, ax1, ay0, ay1 = lx[sel].min(), lx[sel].max(), ly[sel].min(), ly[sel].max()
    ssx = (lx - ax0) / (ax1 - ax0) * (sm - 1)
    ssy = (ay1 - ly) / (ay1 - ay0) * (sm - 1)
    depth = 1e5 - V @ L  # distance from the sun side; larger is farther
    szb = np.zeros((sm, sm))
    sid = -np.ones((sm, sm), np.int64)
    d1 = np.zeros((sm, sm))
    d2 = np.zeros((sm, sm))
    raster(ssx, ssy, depth, T, sm, sm, szb, sid, d1, d2)

    # shade, in the site's blueprint grammar: grey relief shading in the panel's own tones, contour
    # lines every 10 m, hairline silhouettes and creases; man-made structures in the accent. The
    # sky is transparent so the figure panel shows through. Lines are found on the supersampled
    # buffers and box-filtered to the output, so they stay one crisp pixel wide.
    mask = ids >= 0
    tid = ids[mask]
    q1, q2 = bb1[mask], bb2[mask]
    q0 = 1 - q1 - q2
    P3 = V[T[tid, 0]] * q0[:, None] + V[T[tid, 1]] * q1[:, None] + V[T[tid, 2]] * q2[:, None]
    nrm = tn[tid].copy()
    ter = tid < nterr
    nrm[ter] = (vn[T[tid[ter], 0]] * q0[ter, None] + vn[T[tid[ter], 1]] * q1[ter, None] + vn[T[tid[ter], 2]] * q2[ter, None])
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    lam = np.clip(nrm @ L, 0, 1)
    px_ = np.clip(((P3 @ lr) - ax0) / (ax1 - ax0) * (sm - 1), 0, sm - 1).astype(int)
    py_ = np.clip((ay1 - (P3 @ lu)) / (ay1 - ay0) * (sm - 1), 0, sm - 1).astype(int)
    occ = szb[py_, px_]
    lit = np.where(occ > 0, (1.0 / np.maximum(occ, 1e-12)) >= (1e5 - P3 @ L) - 3.0, True)
    light = np.clip(0.18 + 0.82 * lam, 0, 1)  # form shading only, no cast shadows
    dist = np.linalg.norm(P3 - CAM, axis=1)
    fade = np.clip((dist - 1800) / 2600, 0, 1)

    obj_all = np.where(mask, ids >= nterr, False)
    # ground markings on the platform: the paved apron round the telescopes and the laboratory, the
    # auxiliary-telescope tracks (4.4 m wide) and the station pads (4.8 m squares), as flat paint
    En, Nn = P3[:, 0], P3[:, 1]
    onplat = ter & (np.abs(P3[:, 2] - ZPLAT) < 0.3)
    paved_px = np.zeros(len(P3), bool)
    for a_, b_ in TRACKS:
        (e0, n0), (e1, n1) = STATIONS[a_], STATIONS[b_]
        L_ = math.hypot(e1 - e0, n1 - n0); ux, uy = (e1 - e0) / L_, (n1 - n0) / L_
        tpar = (En - e0) * ux + (Nn - n0) * uy
        tper = -(En - e0) * uy + (Nn - n0) * ux
        paved_px |= (tpar > -5.0) & (tpar < L_ + 5.0) & (np.abs(tper) < 3.6)
    cn, sn = math.cos(NU), math.sin(NU)
    for e0, n0 in STATIONS.values():
        pp_ = (En - e0) * cn + (Nn - n0) * sn
        qq_ = -(En - e0) * sn + (Nn - n0) * cn
        paved_px |= (np.abs(pp_) < 5.0) & (np.abs(qq_) < 4.0)
    apron_poly = MPath(np.array(_hull_pts([(e + 20 * math.cos(a), n + 20 * math.sin(a)) for e, n in list(UTS.values()) + [plan(*VST_PX)] for a in np.linspace(0, 2 * math.pi, 24, endpoint=False)] + [plan(*q) for q in LAB_PX])))
    paved_px |= apron_poly.contains_points(np.stack([En, Nn], 1))
    paved_px &= onplat
    # the cut slope round the platform, where the levelling changed the natural ground
    cut_px = ter & (np.abs(P3[:, 2] - raw(P3[:, 0], P3[:, 1])) > 1.5) & ~onplat
    paved = np.zeros((h, w), bool); paved[mask] = paved_px
    lum_obj = C[tid] @ np.array([0.3, 0.55, 0.15])
    paved = np.zeros(h * w, bool).reshape(h, w)
    Zb = np.full((h, w), np.nan); Zb[mask] = P3[:, 2]
    Db = np.full((h, w), np.inf); Db[mask] = dist
    Nb = np.zeros((h, w, 3)); Nb[mask] = nrm
    ter_px = mask & ~obj_all

    def nb_pairs():
        for dy, dx in ((0, 1), (1, 0)):
            yield (slice(0, h - dy), slice(0, w - dx)), (slice(dy, h), slice(dx, w))

    cont = np.zeros((h, w)); contM = np.zeros((h, w)); edge = np.zeros((h, w)); oedge = np.zeros((h, w))
    zz = np.where(np.isnan(Zb), -1e9, Zb)
    for a_, b_ in nb_pairs():
        both = ter_px[a_] & ter_px[b_]
        c10 = both & (np.floor(zz[a_] / 10) != np.floor(zz[b_] / 10))
        c50 = both & (np.floor(zz[a_] / 50) != np.floor(zz[b_] / 50))
        cont[a_] = np.maximum(cont[a_], c10); contM[a_] = np.maximum(contM[a_], c50)
        Da, Db_ = Db[a_], Db[b_]
        rel = np.abs(Da - Db_) / np.maximum(np.minimum(Da, Db_), 1e-6)
        sil = np.where(np.isfinite(Da) & np.isfinite(Db_), rel > 0.03, np.isfinite(Da) != np.isfinite(Db_))
        objpair = obj_all[a_] | obj_all[b_]
        crease = objpair & ((Nb[a_] * Nb[b_]).sum(-1) < 0.8)
        edge[a_] = np.maximum(edge[a_], (sil & ~objpair) | (paved[a_] != paved[b_]) & ~objpair)
        oedge[a_] = np.maximum(oedge[a_], (sil & objpair) | crease)

    def pool(a):  # supersampled mask to output coverage, box filter
        return a.reshape(H, SS, W, SS).mean((1, 3))

    from scipy.ndimage import maximum_filter

    def line_cov(a):  # a one-supersample line widened to one output pixel, then box-filtered
        return np.clip(pool(maximum_filter(a, size=SS)), 0, 1)

    cov = pool(mask.astype(float))
    fadeb = np.zeros((h, w)); fadeb[mask] = fade
    fadeo = pool(fadeb) / np.maximum(cov, 1e-6)
    near = (fadeo < 0.95)
    lines = {"cont": line_cov(cont) * near * (1 - fadeo), "contM": line_cov(contM) * near * (1 - fadeo),
             "edge": line_cov(edge) * (1 - 0.7 * fadeo), "oedge": line_cov(oedge)}

    themes = {
        "light": dict(lit=(1.00, 1.00, 1.00), shade=(0.80, 0.83, 0.88), objlit=(0.88, 0.92, 0.99), objshade=(0.62, 0.71, 0.88),
                      line=(0.73, 0.78, 0.85), ink2=(0.33, 0.40, 0.52), acc=(0.106, 0.373, 0.839), far=(1.0, 1.0, 1.0),
                      paved=(0.93, 0.95, 0.99), pshade=(0.72, 0.77, 0.86)),
        "dark": dict(lit=(0.20, 0.25, 0.35), shade=(0.06, 0.08, 0.13), objlit=(0.33, 0.48, 0.70), objshade=(0.11, 0.17, 0.29),
                     line=(0.20, 0.26, 0.37), ink2=(0.62, 0.68, 0.78), acc=(0.486, 0.722, 1.0), far=(0.047, 0.067, 0.110),
                     paved=(0.30, 0.37, 0.50), pshade=(0.10, 0.13, 0.20)),
    }
    for theme, t_ in themes.items():
        t_ = {k_: np.array(v_) for k_, v_ in t_.items()}
        rgb = np.zeros((h, w, 3))
        isobj = obj_all[mask]
        ground = t_["shade"] + (t_["lit"] - t_["shade"]) * light[:, None]
        ground = np.where(cut_px[:, None], ground * 0.86 + t_["shade"] * 0.14, ground)
        ground = np.where(paved_px[:, None], ground * 0.9 + t_["paved"] * 0.1 if False else t_["pshade"] + (t_["paved"] - t_["pshade"]) * light[:, None], ground)
        objc = t_["objshade"] + (t_["objlit"] - t_["objshade"]) * light[:, None]
        objc = objc * (0.55 + 0.45 * np.clip(lum_obj / 0.8, 0, 1))[:, None]
        base = np.where(isobj[:, None], objc, ground)
        base = base * (1 - fade[:, None]) + t_["far"] * fade[:, None]
        rgb[mask] = base
        out = np.zeros((H, W, 4))
        out[..., :3] = rgb.reshape(H, SS, W, SS, 3).mean((1, 3)) / np.maximum(cov, 1e-6)[..., None]
        out[..., 3] = cov * (1 - 0.0 * fadeo)

        def paint(cov_, colr, alpha):
            a_ = (cov_ * alpha)[..., None]
            out[..., :3] = out[..., :3] * (1 - a_) + colr * a_
            out[..., 3] = np.maximum(out[..., 3], a_[..., 0])
        paint(lines["cont"], t_["line"], 0.75)
        paint(lines["contM"], t_["ink2"], 0.45)
        paint(lines["edge"], t_["ink2"], 0.7)
        paint(lines["oedge"], t_["acc"], 1.0)
        im = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8), "RGBA")
        stem = "paranal-render" if VIEW == "site" else f"paranal-{VIEW}"
        im.save(ROOT / f"assets/img/guide/{stem}-{theme}.webp", "WEBP", quality=90, method=6)
        im.save(ROOT / f"_local/iso-trials/{stem}-{theme}.png")

    # anchors for the vector overlay: each telescope's top and foot, VST, the laboratory, in output pixels
    def proj(e, n, z):
        qv = np.array([e, n, z]) - CAM
        zc = qv @ fwd
        return [round(float(w / 2 + Fp * (qv @ right) / zc) / SS, 1), round(float(h / 2 - Fp * (qv @ up) / zc) / SS, 1)]
    import json
    anchors = {k_: {"foot": proj(e, n, ZPLAT), "top": proj(e, n, ZPLAT + 30)} for k_, (e, n) in UTS.items()}
    anchors["centre"] = {"foot": proj(0, 0, ZPLAT)}
    camera = {"cam": CAM.tolist(), "fwd": fwd.tolist(), "right": right.tolist(), "up": up.tolist(), "f": Fp / SS, "size": [W, H]}
    cams = ROOT / "figures/eso/paranal_cameras.json"
    allc = json.loads(cams.read_text()) if cams.exists() else {}
    allc[VIEW] = camera
    allc["features"] = {"pose": POSE, "vst": plan(*VST_PX), "lab": [plan(*q) for q in LAB_PX], "control": [plan(*q) for q in CONTROL_PX],
                        "zbench": ZPLAT - BENCH}
    cams.write_text(json.dumps(allc, indent=1))
    print(f"wrote the {VIEW} view in both themes and its camera; {len(T)} triangles")


if __name__ == "__main__":
    main()
