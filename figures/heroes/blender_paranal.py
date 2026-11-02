"""Cerro Paranal at night as a rendered scene (Blender 4.2 as a module, Cycles on the CPU): the real terrain
under a low moon, the levelled platform with the four Unit Telescope enclosures, UT2 open for the night with a
faint cool light inside, the Auxiliary Telescopes on their rails, VST, the VLTI laboratory and the control
building, and VISTA on its own peak to the north east. The sky is black and carries no stars (the page shows
real sky elsewhere). A still and a slow orbit of 20 degrees about the platform.

Real data and sources (the geometry is the one figures/eso/paranal_render.py builds, copied here)
- Terrain: Copernicus DEM GLO-30, tile Copernicus_DSM_COG_10_S25_00_W071_00_DEM.tif in _local/dem/ (not
  tracked). The levelled platform (2,635 m), its cut slope and the control building's bench are modelled on top
  of the data as in paranal_render.py; within 120 m of the platform the 30 m cells are sharpened so the cut
  keeps its edge.
- Unit Telescopes, stations and the Auxiliary Telescope tracks: ESO, VLTI station coordinates, metres east and
  north of the array centre (latitude -24.62794830, longitude -70.40479659), platform grid rotated by
  -18.984 degrees. The Auxiliary Telescopes stand on A0, G1, J2 and J3.
- VST, the VLTI laboratory and the control building: ESO, Paranal General Plan, fitted to the Unit Telescopes.
- Unit Telescope enclosures: concrete base, co-rotating upper part with flat front and back, about 29 m across
  and high; open, the doors clear a 9.5 m slit down the front and across the roof (ESO, VLT enclosure page).
- VISTA at latitude -24.6157, longitude -70.3976, enclosure about 20 m.
Schematic: the telescope inside UT2 except its 8.2 m primary mirror, the rails and station pads (their
gauge is not from a source), the buildings' heights, the moon's position and the materials.

Usage, from the repository root, with DIR the working directory for frames and outputs:
  uv run --python 3.11 --with bpy==4.2.0 --with scipy --with pillow python figures/heroes/blender_paranal.py DIR test [samples] [W] [H]
  uv run --python 3.11 --with bpy==4.2.0 --with scipy --with pillow python figures/heroes/blender_paranal.py DIR still [samples] [W] [H]
  uv run --python 3.11 --with bpy==4.2.0 --with scipy --with pillow python figures/heroes/blender_paranal.py DIR anim [samples] [W] [H]
  uv run --python 3.11 --with pillow python figures/heroes/blender_paranal.py DIR post
still writes paranal_still.png and paranal_still.webp; anim writes frames/f_0000.png to f_0359.png, the orbit;
post appends the 30 crossfade frames f_0360 to f_0389 (last into first, Pillow) and writes paranal.poster.webp.
Encoding, after post:
  ffmpeg -y -framerate 30 -i DIR/frames/f_%04d.png -vf "scale=1280:-2,format=yuv420p" -c:v libsvtav1 -crf 42 \\
    -preset 5 -g 120 -movflags +faststart DIR/paranal.av1.mp4
  ffmpeg -y -framerate 30 -i DIR/frames/f_%04d.png -vf "scale=1280:-2,format=yuv420p" -c:v libx264 -crf 28 \\
    -preset slow -g 120 -movflags +faststart DIR/paranal.h264.mp4
"""
import math
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEM = os.path.join(ROOT, '_local', 'dem', 'Copernicus_DSM_COG_10_S25_00_W071_00_DEM.tif')
FRAMES, FADE, ORBIT_DEG = 360, 30, 20.0

CENTRE = (-24.62794830, -70.40479659)
NU = math.radians(-18.984)
ZPLAT = 2635.0
OPEN_UT = 'UT2'
BENCH = 9.0
STATIONS = {  # E, N (m), ESO
    'A0': (-14.642, -55.812), 'A1': (-9.434, -70.949), 'B0': (-7.065, -53.212), 'B1': (-1.863, -68.334),
    'B2': (0.739, -75.899), 'B3': (3.348, -83.481), 'B4': (5.945, -91.030), 'B5': (8.547, -98.594),
    'C0': (0.487, -50.607), 'C1': (5.691, -65.735), 'C2': (8.296, -73.307), 'C3': (10.896, -80.864),
    'D0': (15.628, -45.397), 'D1': (26.039, -75.660), 'D2': (31.243, -90.787), 'E0': (30.760, -40.196),
    'G0': (45.896, -34.990), 'G1': (66.716, -95.501), 'G2': (38.063, -12.289), 'H0': (76.150, -24.572),
    'I1': (96.711, -59.789), 'J1': (106.648, -39.444), 'J2': (114.460, -62.151), 'J3': (80.628, 36.193),
    'J4': (75.424, 51.320), 'J5': (67.618, 74.009), 'J6': (59.810, 96.706), 'K0': (106.397, -14.165),
    'L0': (113.977, -11.549), 'M0': (121.535, -8.951),
}
UTS = {'UT1': (-9.925, -20.335), 'UT2': (14.887, 30.502), 'UT3': (44.915, 66.183), 'UT4': (103.306, 43.999)}
ATS = ('A0', 'G1', 'J2', 'J3')
VISTA = (-24.6157, -70.3976)
_PLAN_UT = {'UT1': (342, 224), 'UT2': (371, 171), 'UT3': (403, 131), 'UT4': (465, 157)}
VST_PX = (462, 75)
LAB_PX = [(399, 214), (428, 214), (428, 229), (399, 229)]
CONTROL_PX = [(292, 265), (305, 298), (336, 320)]
TRACKS = [('A0', 'A1'), ('B0', 'B5'), ('C0', 'C3'), ('D0', 'D2'), ('G2', 'G1'), ('J2', 'J6'), ('A0', 'M0')]

# the platform's centre, the camera's orbit and the moon
PC = np.array([48.0, 12.0, ZPLAT])
CAM_DIST, CAM_AZ, CAM_EL, CAM_LENS = 320.0, 180.0, 18.0, 35.0  # azimuth from east, counter-clockwise; from the west
LOOK = np.array([52.0, 2.0, ZPLAT - 2.0])
MOON_AZ, MOON_EL = 196.0, 20.0  # low in the south south west, so the enclosures' flanks and the relief catch it
POSE_ALT = 50.0  # UT2's telescope altitude, pointed out through the slit

# material keys, mapped to Cycles materials in build()
ALU, PANEL, ROOF, CONCRETE, BEIGE, DARK, WHITE, PAD, RAIL = 'alu', 'panel', 'roof', 'concrete', 'beige', 'dark', 'white', 'pad', 'rail'


def pq_to_en(p, q):
    c, s = math.cos(NU), math.sin(NU)
    return p * c - q * s, p * s + q * c


class Mesh:
    """Triangle soup keyed by material; every shape is a convex solid or a strip, as in paranal_render.py."""
    def __init__(self):
        self.v, self.t, self.c = [], [], []

    def tri(self, a, b, c, col):
        n = len(self.v); self.v += [a, b, c]; self.t.append((n, n + 1, n + 2)); self.c.append(col)

    def quad(self, a, b, c, d, col):
        self.tri(a, b, c, col); self.tri(a, c, d, col)

    def prism(self, outline, z0, z1, col_side, col_top, bottom=False):
        k = len(outline)
        if sum(outline[i][0] * outline[(i + 1) % k][1] - outline[(i + 1) % k][0] * outline[i][1] for i in range(k)) < 0:
            outline = outline[::-1]
        for i in range(k):
            (x0, y0), (x1, y1) = outline[i], outline[(i + 1) % k]
            self.quad((x0, y0, z0), (x1, y1, z0), (x1, y1, z1), (x0, y0, z1), col_side)
        cx = sum(p[0] for p in outline) / k; cy = sum(p[1] for p in outline) / k
        for i in range(k):
            (x0, y0), (x1, y1) = outline[i], outline[(i + 1) % k]
            self.tri((cx, cy, z1), (x0, y0, z1), (x1, y1, z1), col_top)
            if bottom:
                self.tri((cx, cy, z0), (x1, y1, z0), (x0, y0, z0), col_top)

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


def clip_poly(poly, a, b, c):
    out = []
    for i in range(len(poly)):
        p, q = poly[i], poly[(i + 1) % len(poly)]
        fp, fq = a * p[0] + b * p[1] - c, a * q[0] + b * q[1] - c
        if fp >= 0:
            out.append(p)
        if (fp >= 0) != (fq >= 0):
            t = fp / (fp - fq); out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def tube(m, p0, p1, r, col, k=14, caps=True):
    p0, p1 = np.array(p0, float), np.array(p1, float)
    a = p1 - p0; a /= np.linalg.norm(a)
    u = np.cross(a, [0.0, 0.0, 1.0]) if abs(a[2]) < 0.9 else np.cross(a, [1.0, 0.0, 0.0]); u /= np.linalg.norm(u)
    v = np.cross(a, u)
    ring = [(math.cos(2 * math.pi * i / k), math.sin(2 * math.pi * i / k)) for i in range(k)]
    P0 = [tuple(p0 + r * (c * u + s_ * v)) for c, s_ in ring]; P1 = [tuple(p1 + r * (c * u + s_ * v)) for c, s_ in ring]
    for i in range(k):
        j = (i + 1) % k; m.quad(P0[i], P0[j], P1[j], P1[i], col)
    if caps:
        for i in range(k):
            j = (i + 1) % k; m.tri(tuple(p1), P1[i], P1[j], col); m.tri(tuple(p0), P0[j], P0[i], col)


def obox(m, c, axes, half, col):
    c = np.array(c, float)
    ax = [np.array(a, float) / np.linalg.norm(a) * hh for a, hh in zip(axes, half)]
    P = {(i, j, k): tuple(c + i * ax[0] + j * ax[1] + k * ax[2]) for i in (-1, 1) for j in (-1, 1) for k in (-1, 1)}
    faces = [[(1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)], [(-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1)],
             [(-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1)], [(-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)],
             [(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)], [(-1, -1, -1), (-1, 1, -1), (1, 1, -1), (1, -1, -1)]]
    for f in faces:
        q = [np.array(P[v]) for v in f]
        if np.cross(q[1] - q[0], q[2] - q[0]) @ (sum(q) / 4 - c) < 0:
            q = q[::-1]
        m.quad(*map(tuple, q), col)


def unit_telescope(m, cx, cy, z0, facing, opened=False):
    """A Unit Telescope enclosure after ESO's photographs: the dark plinth on its ring of stilts, the concrete
    drum with its band of windows, the co-rotating upper part (an octagon in plan with flat front and back) with
    the shutter slit down the front and across the roof. 29 m across, about 29 m high."""
    c, s = math.cos(facing), math.sin(facing)
    tr2 = lambda pts: [(cx + x * c - y * s, cy + x * s + y * c) for x, y in pts]
    tr = lambda x, y, z: (cx + x * c - y * s, cy + x * s + y * c, z)
    circ = lambda r, k=40: [(r * math.cos(2 * math.pi * i / k), r * math.sin(2 * math.pi * i / k)) for i in range(k)]
    m.prism(tr2(circ(12.6)), z0, z0 + 2.4, DARK, DARK)
    m.prism(tr2(circ(14.2)), z0 + 2.4, z0 + 3.0, DARK, DARK)
    m.prism(tr2(circ(13.6)), z0 + 3.0, z0 + 10.0, BEIGE, BEIGE)
    m.prism(tr2(circ(13.66)), z0 + 5.6, z0 + 6.8, DARK, DARK)
    up = []
    for i in range(20):
        a_ = 2 * math.pi * (i + 0.5) / 20
        x, y = 13.6 * math.cos(a_), 13.6 * math.sin(a_)
        up.append((max(-12.0, min(12.0, x)), y))
    up = [q for i, q in enumerate(up) if i == 0 or abs(q[0] - up[i - 1][0]) + abs(q[1] - up[i - 1][1]) > 1e-6]
    if opened:
        hs, zr, zw = 4.75, z0 + 28.4, z0 + 19.0
        k_ = len(up)
        for i in range(k_):
            (x0, y0), (x1, y1) = up[i], up[(i + 1) % k_]
            if abs(x0 - 12.0) < 1e-6 and abs(x1 - 12.0) < 1e-6:
                ya, yb = sorted((y0, y1))
                for u0, u1 in ((ya, min(yb, -hs)), (max(ya, hs), yb)):
                    if u1 > u0:
                        m.quad(tr(12.0, u0, z0 + 10.0), tr(12.0, u1, z0 + 10.0), tr(12.0, u1, zr), tr(12.0, u0, zr), PANEL)
                u0, u1 = max(ya, -hs), min(yb, hs)
                if u1 > u0:  # the windscreen closing the slit's lower part
                    m.quad(tr(12.0, u0, z0 + 10.0), tr(12.0, u1, z0 + 10.0), tr(12.0, u1, zw), tr(12.0, u0, zw), ALU)
                continue
            m.quad(tr(x0, y0, z0 + 10.0), tr(x1, y1, z0 + 10.0), tr(x1, y1, zr), tr(x0, y0, zr), PANEL)
        for piece in (clip_poly(up, 0, 1, hs), clip_poly(up, 0, -1, hs),
                      clip_poly(clip_poly(clip_poly(up, -1, 0, 10.0), 0, 1, -hs - 0.01), 0, -1, -hs - 0.01)):
            if len(piece) >= 3:
                m.prism(tr2(piece), zr, z0 + 29.0, ROOF, ROOF, bottom=True)
        for y in (-hs, hs):
            m.quad(tr(12.0, y, zr), tr(-10.0, y, zr), tr(-10.0, y, z0 + 29.0), tr(12.0, y, z0 + 29.0), DARK)
        return
    m.prism(tr2(up), z0 + 10.0, z0 + 29.0, PANEL, ROOF)
    for y in (-4.5, 4.5):  # the slit's door seams, closed
        m.quad(tr(12.05, y - 0.18, z0 + 12.0), tr(12.05, y + 0.18, z0 + 12.0), tr(12.05, y + 0.18, z0 + 29.0), tr(12.05, y - 0.18, z0 + 29.0), DARK)
        m.quad(tr(-10.0, y - 0.18, z0 + 29.05), tr(12.0, y - 0.18, z0 + 29.05), tr(12.0, y + 0.18, z0 + 29.05), tr(-10.0, y + 0.18, z0 + 29.05), DARK)


def ut_telescope(m, cx, cy, z0, toward, alt):
    """The telescope inside the opened enclosure, schematic except the 8.2 m primary mirror."""
    h = np.array([toward[0], toward[1], 0.0]); h /= np.linalg.norm(h)
    lat = np.array([-h[1], h[0], 0.0])
    d = h * math.cos(alt) + np.array([0, 0, 1.0]) * math.sin(alt)
    zf, za = z0 + 10.6, z0 + 18.5
    o = np.array([cx, cy, za]); zv = np.array([0, 0, 1.0])
    tube(m, (cx, cy, z0 + 9.6), (cx, cy, zf), 7.2, CONCRETE, 40)
    obox(m, (cx, cy, zf + 0.9), (h, lat, zv), (2.6, 7.4, 0.9), ROOF)
    for sg in (1, -1):
        obox(m, np.array([cx, cy, (zf + za) / 2 + 0.6]) + lat * sg * 6.6, (h, lat, zv), (2.6, 0.8, (za - zf) / 2 + 0.6), ROOF)
        obox(m, o + lat * sg * 9.0 - zv * 2.6, (h, lat, zv), (3.2, 1.6, 0.25), CONCRETE)
        obox(m, o + lat * sg * 9.0 - zv * 1.3, (h, lat, zv), (1.6, 1.2, 1.05), WHITE)
    tube(m, o - lat * 7.6, o + lat * 7.6, 0.7, ROOF, 12)
    c1 = o - d * 2.2
    tube(m, c1 - d * 1.2, c1, 4.7, ROOF, 40)
    tube(m, c1, c1 + d * 0.25, 4.1, WHITE, 40)
    m2 = o + d * 10.8
    tube(m, m2 - d * 0.5, m2 + d * 0.5, 1.7, ROOF, 24)
    e1 = np.cross(d, lat)
    for i in range(8):
        a0 = 2 * math.pi * i / 8; a1 = a0 + (math.pi / 4 if i % 2 == 0 else -math.pi / 4)
        q0 = c1 + 4.3 * (math.cos(a0) * lat + math.sin(a0) * e1); q1 = m2 + 1.6 * (math.cos(a1) * lat + math.sin(a1) * e1)
        tube(m, q0, q1, 0.3, ROOF, 6, caps=False)


def aux_telescope(m, cx, cy, z0, facing):
    box = rot([(-1.9, -1.9), (1.9, -1.9), (1.9, 1.9), (-1.9, 1.9)], cx, cy, facing)
    m.prism(box, z0, z0 + 2.6, WHITE, WHITE)
    m.dome(cx, cy, z0 + 2.6, 2.1, WHITE, 18, 6)


def strip(m, p0, p1, w, z, h, col, extend=0.0):
    (e0, n0), (e1, n1) = p0, p1
    L = math.hypot(e1 - e0, n1 - n0); ux, uy = (e1 - e0) / L, (n1 - n0) / L
    e0, n0, e1, n1 = e0 - ux * extend, n0 - uy * extend, e1 + ux * extend, n1 + uy * extend
    nx, ny = -uy * w / 2, ux * w / 2
    m.prism([(e0 - nx, n0 - ny), (e1 - nx, n1 - ny), (e1 + nx, n1 + ny), (e0 + nx, n0 + ny)], z, z + h, col, col)


def build_site(height, plan, vista_en, cam_dir):
    m = Mesh()
    zb = ZPLAT
    facing = math.atan2(cam_dir[1], cam_dir[0])  # the slits toward the viewer, as in ESO's photographs
    for name, (e, n) in UTS.items():
        unit_telescope(m, e, n, zb, facing, opened=(name == OPEN_UT))
    e, n = UTS[OPEN_UT]
    ut_telescope(m, e, n, zb, (math.cos(facing), math.sin(facing)), math.radians(POSE_ALT))
    for name in ATS:
        e, n = STATIONS[name]; aux_telescope(m, e, n, zb, NU)
    # the tracks (4.4 m paved strips with two rails) and the station pads (4.8 m squares)
    for a_, b_ in TRACKS:
        strip(m, STATIONS[a_], STATIONS[b_], 4.4, zb, 0.06, PAD, extend=5.0)
        (e0, n0), (e1, n1) = STATIONS[a_], STATIONS[b_]
        L = math.hypot(e1 - e0, n1 - n0); ux, uy = (e1 - e0) / L, (n1 - n0) / L
        for sg in (-1, 1):
            off = (-uy * sg * 1.4, ux * sg * 1.4)
            strip(m, (e0 + off[0], n0 + off[1]), (e1 + off[0], n1 + off[1]), 0.14, zb + 0.06, 0.12, RAIL, extend=4.0)
    cn, sn = math.cos(NU), math.sin(NU)
    for e0, n0 in STATIONS.values():
        sq = [(e0 + x * cn - y * sn, n0 + x * sn + y * cn) for x, y in ((-2.4, -2.4), (2.4, -2.4), (2.4, 2.4), (-2.4, 2.4))]
        m.prism(sq, zb, zb + 0.08, PAD, PAD)
    # VST: an octagonal enclosure 13 m across, 12 m high
    vx, vy = plan(*VST_PX)
    octo = [(6.5 * math.cos(math.pi / 8 + math.pi / 4 * i), 6.5 * math.sin(math.pi / 8 + math.pi / 4 * i)) for i in range(8)]
    m.prism(rot(octo, vx, vy, 0), zb, zb + 3, BEIGE, BEIGE)
    m.prism(rot(octo, vx, vy, 0.3), zb + 3, zb + 12, PANEL, ROOF)
    # the VLTI laboratory: a low white building over the delay-line tunnel
    m.prism([plan(*q) for q in LAB_PX], zb, zb + 4.5, WHITE, WHITE)
    # the control building on its bench, a band of windows
    pts = [plan(*q) for q in CONTROL_PX]
    for (a0, b0), (a1, b1) in zip(pts[:-1], pts[1:]):
        L = math.hypot(a1 - a0, b1 - b0); ux, uy = (a1 - a0) / L, (b1 - b0) / L
        a0, b0, a1, b1 = a0 - ux * 7, b0 - uy * 7, a1 + ux * 7, b1 + uy * 7
        nx, ny = -uy * 7, ux * 7
        m.prism([(a0 - nx, b0 - ny), (a1 - nx, b1 - ny), (a1 + nx, b1 + ny), (a0 + nx, b0 + ny)], zb - BENCH, zb + 1.0, CONCRETE, DARK)
        k_ = 1.01
        m.prism([(a0 - nx * k_, b0 - ny * k_), (a1 - nx * k_, b1 - ny * k_), (a1 + nx * k_, b1 + ny * k_), (a0 + nx * k_, b0 + ny * k_)],
                zb - BENCH + 3.2, zb - BENCH + 4.6, DARK, DARK)
    ve, vn = vista_en
    zv = float(height(np.array([ve]), np.array([vn]))[0])
    ring = [(9.8 * math.cos(2 * math.pi * i / 32), 9.8 * math.sin(2 * math.pi * i / 32)) for i in range(32)]
    m.prism(rot(ring, ve, vn, 0), zv - 1, zv + 9, WHITE, WHITE)
    m.dome(ve, vn, zv + 9, 9.8, WHITE, 32, 10)
    return m


def hull(pts):
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


def terrain_model():
    """The height function over east and north (metres), the plan mapping and VISTA's position, after
    paranal_render.py: the DEM, the levelled platform, its cut slope and the control building's bench."""
    from PIL import Image
    from scipy.ndimage import distance_transform_edt, gaussian_filter, map_coordinates
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(DEM)
    tp, scl = im.tag_v2[33922], im.tag_v2[33550]
    dem = np.asarray(im, dtype=float); lon0, lat0, dlon, dlat = tp[3], tp[4], scl[0], scl[1]
    phi = math.radians(CENTRE[0])
    mlat = 111132.954 - 559.822 * math.cos(2 * phi) + 1.175 * math.cos(4 * phi)
    mlon = 111412.84 * math.cos(phi) - 93.5 * math.cos(3 * phi)

    def raw(e, n):
        lat = CENTRE[0] + np.asarray(n) / mlat; lon = CENTRE[1] + np.asarray(e) / mlon
        return map_coordinates(dem, [(lat0 - lat) / dlat - 0.5, (lon - lon0) / dlon - 0.5], order=3, mode='nearest')

    vista_en = ((VISTA[1] - CENTRE[1]) * mlon, (VISTA[0] - CENTRE[0]) * mlat)
    A = np.array([[x, y, 1.0] for x, y in _PLAN_UT.values()])
    cE = np.linalg.lstsq(A, [UTS[k][0] for k in _PLAN_UT], rcond=None)[0]
    cN = np.linalg.lstsq(A, [UTS[k][1] for k in _PLAN_UT], rcond=None)[0]
    plan = lambda x, y: (float(cE @ [x, y, 1.0]), float(cN @ [x, y, 1.0]))
    ring_pts = []
    for (e, n), r in [(v, 25.0) for v in UTS.values()] + [(plan(*VST_PX), 25.0)] + [(v, 14.0) for v in STATIONS.values()] + [(plan(*q), 12.0) for q in LAB_PX]:
        ring_pts += [(e + r * math.cos(t), n + r * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 36, endpoint=False)]
    poly = np.array(hull(ring_pts))  # convex, counter-clockwise

    def inside(e, n):
        e, n = np.asarray(e, float), np.asarray(n, float)
        ok = np.ones(e.shape, bool)
        for i in range(len(poly)):
            (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % len(poly)]
            ok &= (x1 - x0) * (n - y0) - (y1 - y0) * (e - x0) >= 0
        return ok

    gx = np.arange(poly[:, 0].min() - 120, poly[:, 0].max() + 120, 2.0)
    gy = np.arange(poly[:, 1].min() - 120, poly[:, 1].max() + 120, 2.0)
    GX, GY = np.meshgrid(gx, gy)
    dist_out = distance_transform_edt(~inside(GX, GY)) * 2.0

    def outside_dist(e, n):
        return map_coordinates(dist_out, [(np.asarray(n) - gy[0]) / 2.0, (np.asarray(e) - gx[0]) / 2.0], order=1, mode='constant', cval=1.0e4)

    cpts = np.array([plan(*q) for q in CONTROL_PX])

    def bench_dist(e, n):
        e, n = np.asarray(e, float), np.asarray(n, float)
        d = np.full(e.shape, 1e9)
        for (a0, b0), (a1, b1) in zip(cpts[:-1], cpts[1:]):
            L = math.hypot(a1 - a0, b1 - b0); ux, uy = (a1 - a0) / L, (b1 - b0) / L
            t = np.clip((e - a0) * ux + (n - b0) * uy, -7.0, L + 7.0)
            d = np.minimum(d, np.hypot(e - (a0 + t * ux), n - (b0 + t * uy)))
        return d

    ge = np.arange(poly[:, 0].min() - 160, poly[:, 0].max() + 160, 3.0)
    gn = np.arange(poly[:, 1].min() - 160, poly[:, 1].max() + 160, 3.0)
    GE, GN = np.meshgrid(ge, gn)
    RG = raw(GE, GN); SG = RG + 1.6 * (RG - gaussian_filter(RG, 5.0))

    def sharp(e, n):
        return map_coordinates(SG, [(np.asarray(n) - gn[0]) / 3.0, (np.asarray(e) - ge[0]) / 3.0], order=1, mode='nearest')

    def height(e, n):
        e, n = np.asarray(e, float), np.asarray(n, float)
        z = raw(e, n); dout = outside_dist(e, n)
        wgt = np.clip((150.0 - dout) / 40.0, 0, 1)
        z = np.where(wgt > 0, z * (1 - wgt) + sharp(e, n) * wgt, z)
        zslope = ZPLAT - dout * math.tan(math.radians(35))
        zz = np.where(dout <= 0, ZPLAT, np.where(z < zslope, zslope, z))
        bd = bench_dist(e, n)
        zb_ = ZPLAT - BENCH + np.clip(bd - 11.0, 0, None) * math.tan(math.radians(40))
        return np.where(bd < 11.0, ZPLAT - BENCH, np.minimum(zz, zb_))

    return height, raw, outside_dist, plan, vista_en


def graded(lo, hi, fine_lo, fine_hi, step, ratio=1.09, step_max=36.0):
    """Grid coordinates: step within [fine_lo, fine_hi], growing geometrically outside to step_max."""
    mid = list(np.arange(fine_lo, fine_hi + 1e-6, step))
    left, x, s = [], fine_lo, step
    while x > lo:
        s = min(s * ratio, step_max); x -= s; left.append(x)
    right, x, s = [], fine_hi, step
    while x < hi:
        s = min(s * ratio, step_max); x += s; right.append(x)
    return np.array(left[::-1] + mid + right)


def build(samples, W, H):
    import bpy
    from mathutils import Vector
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
    if os.environ.get('CYCLES_DEVICE') == 'GPU':  # the CPU path in this wheel uses two or three cores; the GPU is the same tracer
        pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'CUDA'; pr.get_devices()
        for dv in pr.devices: dv.use = dv.type == 'CUDA'
        sc.cycles.device = 'GPU'; sc.cycles.denoising_use_gpu = True
    sc.render.resolution_x, sc.render.resolution_y = W, H; sc.render.resolution_percentage = 100
    sc.render.fps = 30; sc.frame_start, sc.frame_end = 0, FRAMES - 1
    sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
    sc.cycles.max_bounces = 4; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 2

    def principled(name, base, metal=0.0, rough=0.5, spec=0.5):
        mt = bpy.data.materials.new(name); mt.use_nodes = True; b = mt.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = (*base, 1); b.inputs['Metallic'].default_value = metal
        b.inputs['Roughness'].default_value = rough; b.inputs['Specular IOR Level'].default_value = spec
        return mt
    MAT = {
        ALU: principled('alu', (0.80, 0.80, 0.82), 1.0, 0.35), PANEL: principled('panel', (0.80, 0.80, 0.82), 1.0, 0.35),
        ROOF: principled('roof', (0.72, 0.72, 0.74), 1.0, 0.45), CONCRETE: principled('concrete', (0.22, 0.21, 0.20), 0.0, 0.9, 0.15),
        BEIGE: principled('beige', (0.24, 0.22, 0.19), 0.0, 0.9, 0.15), DARK: principled('dark', (0.035, 0.035, 0.04), 0.0, 0.9, 0.1),
        WHITE: principled('white', (0.30, 0.30, 0.29), 0.0, 0.8, 0.15), PAD: principled('pad', (0.30, 0.295, 0.28), 0.0, 0.95, 0.1),
        RAIL: principled('rail', (0.32, 0.32, 0.34), 1.0, 0.5),
    }

    height, raw, outside_dist, plan, vista_en = terrain_model()
    cam_az = math.radians(CAM_AZ)
    cam_dir = (math.cos(cam_az), math.sin(cam_az))
    m = build_site(height, plan, vista_en, cam_dir)
    V = np.array(m.v, float); T = np.array(m.t); C = np.array(m.c)
    for key, mat in MAT.items():
        sel = np.where(C == key)[0]
        if len(sel) == 0:
            continue
        tris = T[sel]; used = np.unique(tris); remap = {int(u): i for i, u in enumerate(used)}
        verts = [tuple(V[u]) for u in used]; faces = [tuple(remap[int(i)] for i in t) for t in tris]
        me = bpy.data.meshes.new('site_' + key); me.from_pydata(verts, [], faces); me.update()
        ob = bpy.data.objects.new('site_' + key, me); bpy.context.collection.objects.link(ob); ob.data.materials.append(mat)

    # the terrain: a graded grid, 4 m on the platform, 36 m far out
    E = graded(-2600, 3200, -140, 240, 4.0); N = graded(-2400, 2800, -180, 220, 4.0)
    EE, NN = np.meshgrid(E, N); ZZ = height(EE, NN)
    nr, nc = EE.shape
    verts = np.stack([EE.ravel(), NN.ravel(), ZZ.ravel()], 1)
    idx = np.arange(nr * nc).reshape(nr, nc)
    a, b, c, d = idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()
    faces = np.stack([a, b, c, d], 1)
    me = bpy.data.meshes.new('terrain'); me.from_pydata([tuple(v) for v in verts], [], [tuple(int(i) for i in f) for f in faces]); me.update()
    for p in me.polygons:
        p.use_smooth = True
    # ground tones: desert ground, the platform's dark gravel, the grey scree of the cut, the paved apron
    dv = outside_dist(verts[:, 0], verts[:, 1])
    plat = dv <= 0
    col = np.tile(np.array([0.22, 0.175, 0.14]), (len(verts), 1))
    col[plat] = np.array([0.12, 0.105, 0.09])
    natural = raw(verts[:, 0], verts[:, 1])
    col[(dv > 0) & (verts[:, 2] - natural > 1.0)] = np.array([0.17, 0.165, 0.16])
    ut = np.array(list(UTS.values()) + [plan(*VST_PX)])
    dut = np.min(np.hypot(verts[:, 0, None] - ut[None, :, 0], verts[:, 1, None] - ut[None, :, 1]), axis=1)
    col[plat & (dut < 21)] = np.array([0.20, 0.195, 0.185])
    at = me.color_attributes.new('col', 'FLOAT_COLOR', 'POINT')
    at.data.foreach_set('color', np.column_stack([col, np.ones(len(col))]).ravel())
    tm = bpy.data.materials.new('terrain'); tm.use_nodes = True; nt = tm.node_tree; bs = nt.nodes['Principled BSDF']
    bs.inputs['Roughness'].default_value = 0.97; bs.inputs['Specular IOR Level'].default_value = 0.08
    att = nt.nodes.new('ShaderNodeAttribute'); att.attribute_name = 'col'
    cd = nt.nodes.new('ShaderNodeCameraData'); mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 700.0; mr.inputs['From Max'].default_value = 2600.0
    mr.inputs['To Min'].default_value = 0.0; mr.inputs['To Max'].default_value = 1.0
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs[7].default_value = (0, 0, 0, 1)
    nt.links.new(cd.outputs['View Distance'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], mx.inputs['Factor'])
    nt.links.new(att.outputs['Color'], mx.inputs[6]); nt.links.new(mx.outputs[2], bs.inputs['Base Color'])
    ob = bpy.data.objects.new('terrain', me); bpy.context.collection.objects.link(ob); ob.data.materials.append(tm)

    # the moon: one cool area light, low, from the side; the sky black
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.0025, 0.003, 0.0045, 1)
    ld = bpy.data.lights.new('moon', 'AREA'); ld.shape = 'DISK'; ld.size = 260.0; ld.energy = 6.0e7; ld.color = (0.72, 0.80, 1.0)
    ld.cycles.cast_shadow = True
    lo = bpy.data.objects.new('moon', ld); bpy.context.collection.objects.link(lo)
    ma, me_ = math.radians(MOON_AZ), math.radians(MOON_EL)
    lo.location = tuple(PC + 2600.0 * np.array([math.cos(ma) * math.cos(me_), math.sin(ma) * math.cos(me_), math.sin(me_)]))
    lo.rotation_euler = (Vector(PC) - Vector(lo.location)).to_track_quat('-Z', 'Y').to_euler()
    # the faint cool light inside UT2, seen through the slit
    e, n = UTS[OPEN_UT]
    pd = bpy.data.lights.new('ut2', 'POINT'); pd.energy = 1200.0; pd.color = (0.62, 0.76, 1.0); pd.shadow_soft_size = 2.0
    po = bpy.data.objects.new('ut2', pd); bpy.context.collection.objects.link(po); po.location = (e, n, ZPLAT + 24.0)

    # the camera on an orbit about the platform's centre: a pivot turned over the frames
    piv = bpy.data.objects.new('pivot', None); bpy.context.collection.objects.link(piv); piv.location = tuple(LOOK)
    cd_ = bpy.data.cameras.new('cam'); cd_.lens = CAM_LENS; cd_.sensor_width = 36
    cd_.dof.use_dof = True; cd_.dof.focus_distance = CAM_DIST; cd_.dof.aperture_fstop = 4.0
    cam = bpy.data.objects.new('cam', cd_); bpy.context.collection.objects.link(cam); sc.camera = cam
    el = math.radians(CAM_EL)
    rel = np.array([math.cos(cam_az) * math.cos(el), math.sin(cam_az) * math.cos(el), math.sin(el)]) * CAM_DIST
    cam.parent = piv; cam.location = tuple(rel)
    cam.rotation_euler = (Vector((0, 0, 0)) - Vector(rel)).to_track_quat('-Z', 'Y').to_euler()
    piv.rotation_euler = (0, 0, math.radians(-ORBIT_DEG / 2)); piv.keyframe_insert('rotation_euler', index=2, frame=0)
    piv.rotation_euler = (0, 0, math.radians(ORBIT_DEG / 2)); piv.keyframe_insert('rotation_euler', index=2, frame=FRAMES - 1)
    for fc in piv.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
    # a faint vignette and a touch of glow on the lit slit
    sc.use_nodes = True; ct = sc.node_tree; rl = ct.nodes['Render Layers']; comp = ct.nodes['Composite']
    g = ct.nodes.new('CompositorNodeGlare'); g.glare_type = 'FOG_GLOW'; g.quality = 'HIGH'; g.size = 7; g.threshold = 0.6; g.mix = -0.7
    ct.links.new(rl.outputs['Image'], g.inputs['Image']); ct.links.new(g.outputs['Image'], comp.inputs['Image'])
    return sc


def post(d):
    from PIL import Image
    fr = os.path.join(d, 'frames')
    a = Image.open(os.path.join(fr, 'f_%04d.png' % (FRAMES - 1))).convert('RGB')
    b = Image.open(os.path.join(fr, 'f_%04d.png' % 0)).convert('RGB')
    for i in range(FADE):
        t = (i + 1) / (FADE + 1)
        Image.blend(a, b, t).save(os.path.join(fr, 'f_%04d.png' % (FRAMES + i)), compress_level=6)
    Image.open(os.path.join(fr, 'f_0180.png')).convert('RGB').save(os.path.join(d, 'paranal.poster.webp'), quality=80)
    print('wrote', FADE, 'crossfade frames and', os.path.join(d, 'paranal.poster.webp'))


if __name__ == '__main__':
    d, mode = sys.argv[1], sys.argv[2]
    os.makedirs(os.path.join(d, 'frames'), exist_ok=True)
    if mode == 'post':
        post(d)
    else:
        import bpy
        rest = sys.argv[3:]
        if mode == 'test':
            samples = int(rest[0]) if rest else 24
            W, H = (int(rest[1]), int(rest[2])) if len(rest) > 2 else (480, 320)
            sc = build(samples, W, H); sc.frame_set(FRAMES // 2)
            out = os.path.join(d, 'test_%dx%d.png' % (W, H)); sc.render.filepath = out; bpy.ops.render.render(write_still=True); print('wrote', out)
        elif mode == 'still':
            samples = int(rest[0]) if rest else 48
            W, H = (int(rest[1]), int(rest[2])) if len(rest) > 2 else (1600, 900)
            sc = build(samples, W, H); sc.frame_set(FRAMES // 2)
            out = os.path.join(d, 'paranal_still.png'); sc.render.filepath = out; bpy.ops.render.render(write_still=True)
            from PIL import Image
            Image.open(out).convert('RGB').save(os.path.join(d, 'paranal_still.webp'), quality=82); print('wrote', out)
        elif mode == 'anim':
            samples = int(rest[0]) if rest else 24
            W, H = (int(rest[1]), int(rest[2])) if len(rest) > 2 else (1280, 720)
            sc = build(samples, W, H); sc.render.filepath = os.path.join(d, 'frames', 'f_')
            bpy.ops.render.render(animation=True); print('wrote frames to', sc.render.filepath)
        else:
            sys.exit('mode must be test, still, anim or post')
