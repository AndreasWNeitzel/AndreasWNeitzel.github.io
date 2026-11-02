"""Draw the record's pictograms into one SVG sprite, assets/img/kind-marks.svg.

The marks are drawn with a brush, as an engraver or sign painter would: a solid silhouette for the body of the object
and curved strokes whose width swells and tapers to a hairline. Every stroke is a filled outline, so nothing has a
uniform line width. Objects sit in three-quarter view. Each mark takes one colour, currentColor.

Usage: python3 scripts/kind_marks.py
"""

import math
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "img" / "kind-marks.svg"


def spline(pts, n=14):
    """Catmull-Rom through pts, with widths or any other trailing values interpolated along."""
    pts = [pts[0], *pts, pts[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for k in range(n):
            t = k / n
            out.append(tuple(
                0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t ** 2 + (3 * b - a - 3 * c + d) * t ** 3)
                for a, b, c, d in zip(p0, p1, p2, p3)))
    out.append(pts[-1])
    return out


def path(points, close=True):
    d = "M" + "L".join(f"{x:.1f} {y:.1f}".replace(".0 ", " ").removesuffix(".0") for x, y in points)
    return d + ("Z" if close else "")


def brush(pts, n=6):
    """A stroke through (x, y, half-width) points, returned as a closed outline."""
    s = spline(pts, n)
    left, right = [], []
    for i, (x, y, w) in enumerate(s):
        x0, y0, _ = s[max(i - 1, 0)]
        x1, y1, _ = s[min(i + 1, len(s) - 1)]
        dx, dy = x1 - x0, y1 - y0
        m = math.hypot(dx, dy) or 1
        w = max(w, 0.04)
        left.append((x - dy / m * w, y + dx / m * w))
        right.append((x + dy / m * w, y - dx / m * w))
    return path(left + right[::-1])


def line(x0, y0, x1, y1, w=0.5, bow=0.0):
    """A straight hand stroke that swells in the middle and tapers at both ends."""
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = x1 - x0, y1 - y0
    return brush([(x0, y0, 0.05), (mx - dy * bow, my + dx * bow, w), (x1, y1, 0.05)])


def ring(cx, cy, rx, ry, rot=0, thick=0.9, thin=0.12, phase=0.0, turn=1.0, start=0.0, n=30):
    """An ellipse drawn with a broad nib: thick on one side, hairline on the other."""
    pts = []
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    for i in range(n + 1):
        a = 2 * math.pi * (start + turn * i / n)
        x, y = rx * math.cos(a), ry * math.sin(a)
        w = thin + (thick - thin) * (0.5 + 0.5 * math.cos(a - phase)) ** 2
        pts.append((cx + c * x - s * y, cy + s * x + c * y, w))
    return brush(pts, 2)


def poly(*pts):
    return path(pts)


def sparkle(cx, cy, r, waist=0.1):
    pts = []
    for i in range(8):
        a = math.pi * i / 4 - math.pi / 2
        q = r if i % 2 == 0 else r * waist * 1.4
        pts.append((cx + q * math.cos(a), cy + q * math.sin(a)))
    return path(pts)


def rot3(v, ax, ay):
    x, y, z = v
    y, z = y * math.cos(ax) - z * math.sin(ax), y * math.sin(ax) + z * math.cos(ax)
    x, z = x * math.cos(ay) + z * math.sin(ay), -x * math.sin(ay) + z * math.cos(ay)
    return x, y, z


def globe_mesh(cx, cy, r, ax, ay, roll, w=1.5):
    """Front-facing meridians and parallels of a sphere, each stroke thick on the near side, hairline at the rim."""
    out = []
    c, s = math.cos(roll), math.sin(roll)

    def place(v):
        x, y, z = rot3(v, ax, ay)
        return cx + r * (c * x - s * y), cy + r * (s * x + c * y), z

    def stroke(seq):
        run = []
        for v in seq:
            x, y, z = place(v)
            if z > 0.02:
                run.append((x, y, max(0.06, w * z ** 1.3)))
            elif run:
                if len(run) > 3:
                    out.append(brush(run, 2))
                run = []
        if len(run) > 3:
            out.append(brush(run, 2))

    for lon in range(0, 180, 36):
        a = math.radians(lon)
        stroke([(math.cos(t) * math.cos(a), math.sin(t), math.cos(t) * math.sin(a))
                for t in [i * math.pi / 14 for i in range(29)]])
    for lat in (-52, -18, 18, 52):
        b = math.radians(lat)
        stroke([(math.cos(b) * math.cos(t), math.sin(b), math.cos(b) * math.sin(t))
                for t in [i * math.pi / 14 for i in range(29)]])
    return out


# ---------------------------------------------------------------------------------------------- the marks
def mic():
    p = []
    cx, cy, r = 68, 29, 21
    # the handle, tapering from the collar to the butt, with a slit of highlight cut out of it
    p.append(path([(52.5, 36.5), (63.5, 47.5), (35.5, 74.5), (31, 75.6), (24.6, 69.4), (25.6, 64.6)])
             + path([(50.6, 44.2), (51.8, 45.4), (35.6, 61.4), (34.4, 60.2)]))
    p.append(ring(cx - 10.4, cy + 10.4, 9.6, 2.8, rot=45, thick=1.1, thin=0.22, phase=1.6))
    p += globe_mesh(cx, cy, r, math.radians(-25), math.radians(28), math.radians(-42), w=1.9)
    p.append(ring(cx, cy, r, r, thick=0.75, thin=0.05, phase=0.9))
    # the cable leaves the butt and thins to a hairline
    p.append(brush([(29, 75, 1.05), (24.5, 80, 1.0), (17.5, 90, 0.85), (10, 91, 0.7), (7.5, 80, 0.6), (13, 64, 0.5),
                    (16, 54, 0.4), (10, 47, 0.28), (2, 53, 0.04)]))
    return p


def talk():
    return mic()


def invited():
    return mic() + [sparkle(89, 66, 13), sparkle(74, 84, 5.5)]


def seminar():
    p = []
    # the screen, in hairlines, a curve on it
    for a in ((6, 12, 62, 7), (62, 7, 62, 45), (6, 12, 6, 49)):
        p.append(line(*a, w=0.4))
    p.append(line(5, 49, 63, 45, w=0.55))
    p.append(brush([(12, 40, 0.05), (20, 37, 0.5), (29, 25, 0.75), (37, 31, 0.6), (46, 19, 0.7), (56, 15, 0.05)]))
    # the lectern, solid, in three-quarter view, with a slanted top
    p.append(path([(52, 55), (88, 49), (92, 55), (86, 58), (82, 90), (60, 94), (56, 61), (51, 60)])
             + path([(62, 66), (63.5, 87), (64.5, 86.8), (63, 65.8)]))
    p.append(line(52, 96.5, 86, 92, w=0.8))
    # the gooseneck microphone
    p.append(brush([(76, 52, 0.75), (75, 42, 0.6), (70, 34, 0.45), (63, 30, 0.1)]))
    p.append(ring(61, 29, 2.6, 1.7, rot=25, thick=1.5, thin=1.0))
    return p


def poster():
    p = []
    # a sheet hanging from two pins, its lower corner curling up
    p.append(line(14, 8, 84, 13, w=0.75))
    p.append(line(14, 8, 12, 88, w=0.45))
    p.append(line(84, 13, 86, 70, w=0.5))
    p.append(line(12, 88, 62, 91, w=0.6))
    p.append(path([(86, 70), (62, 91), (66, 80), (74, 73)]))
    p.append(brush([(86, 70, 0.3), (74, 72, 0.5), (66, 79, 0.5), (62, 91, 0.2)]))
    # title, a solid figure, its curve and the column of text as hand strokes
    p.append(line(23, 19, 72, 22, w=0.95))
    p.append(line(32, 25, 62, 27, w=0.4))
    p.append(poly((22, 34), (48, 35.5), (47, 62), (21, 61)))
    p.append(line(55, 37, 76, 38, w=0.4))
    p.append(line(55, 43, 76, 44, w=0.4))
    p.append(line(55, 49, 76, 50, w=0.4))
    p.append(line(55, 55, 70, 56, w=0.4))
    p.append(line(21, 69, 50, 70.5, w=0.4))
    p.append(line(21, 75, 44, 76, w=0.4))
    p.append(ring(14, 8, 1.9, 1.9, thick=1.6, thin=1.2))
    p.append(ring(84, 13, 1.9, 1.9, thick=1.6, thin=1.2))
    return p


def pitch():
    p = []
    cx, cy, r = 50, 56, 34
    p.append(ring(cx, cy, r, r, thick=1.7, thin=0.12, phase=2.4))
    p.append(ring(cx, cy, r - 5, r - 5, thick=0.3, thin=0.05, phase=2.4))
    for i in range(12):
        a = 2 * math.pi * i / 12
        q = 0.8 if i % 3 == 0 else 0.32
        p.append(line(cx + (r - 6.5) * math.cos(a), cy + (r - 6.5) * math.sin(a),
                      cx + (r - 11) * math.cos(a), cy + (r - 11) * math.sin(a), w=q))
    p.append(poly((cx - 1.2, cy + 5), (cx + 1.2, cy + 5), (cx + 10.4, cy - 21), (cx + 9.4, cy - 21.4)))
    p.append(ring(cx, cy, 1.8, 1.8, thick=1.6, thin=1.2))
    p.append(poly((43, 10), (57, 10), (55, 21), (45, 21)))
    p.append(ring(50, 8, 5.2, 2.5, thick=1.1, thin=0.5))
    p.append(poly((80, 19), (84, 15), (90, 22), (86, 26)))
    return p


def sheet(curl=True):
    p = []
    p.append(line(20, 7, 66, 4, w=0.55))
    p.append(line(20, 7, 16, 94, w=0.75))
    p.append(line(16, 94, 80, 91, w=0.5))
    p.append(line(82, 22, 80, 91, w=0.45))
    if curl:
        p.append(path([(66, 4), (82, 22), (72, 21), (66, 15)]))
        p.append(brush([(66, 4, 0.2), (64.6, 13, 0.4), (70, 20.5, 0.4), (82, 22, 0.1)]))
    return p


def article():
    p = sheet()
    p.append(line(27, 15, 55, 14, w=1.0))
    p.append(line(32, 21, 50, 20, w=0.35))
    for i in range(9):
        y = 32 + 5.6 * i
        p.append(line(26, y, 45, y - 0.7, w=0.34))
    for i in range(3):
        y = 69 + 5.6 * i
        p.append(line(51, y, 71, y - 0.7, w=0.34))
    p.append(poly((51, 31), (72, 30), (71.4, 61), (50.6, 62)))
    return p


def lead():
    """First author: the page with the pen that wrote it."""
    p = sheet()
    p.append(line(27, 15, 55, 14, w=1.0))
    for i in range(4):
        y = 26 + 6 * i
        p.append(line(26, y, 66, y - 1, w=0.36))
    p.append(line(26, 50, 48, 49.6, w=0.36))
    p.append(path([(40, 86), (46, 62), (68, 40), (79, 51), (57, 73)])
             + path([(55.2, 63.5), (58, 66.3), (54.6, 69.2), (52.6, 66.6)]))
    p.append(poly((40, 86), (41, 85), (53, 70), (52, 69)))
    p.append(brush([(40, 86, .5), (31, 90, .55), (24, 84, .4), (18, 90, .04)]))
    return p


def letter():
    p = []
    # an envelope in three-quarter view, sealed
    a, b, c, d = (8, 30), (90, 22), (94, 74), (12, 84)
    p.append(line(*a, *b, w=0.5))
    p.append(line(*b, *c, w=0.65))
    p.append(line(*c, *d, w=0.8))
    p.append(line(*d, *a, w=0.5))
    p.append(line(8, 30, 51, 58, w=0.7, bow=0.02))
    p.append(line(90, 22, 51, 58, w=0.7, bow=-0.02))
    p.append(line(12, 84, 40, 51, w=0.3))
    p.append(line(94, 74, 63, 48, w=0.3))
    p.append(ring(51, 56, 3.4, 3.4, thick=3.4, thin=3.0))
    return p


def thesis():
    p = []
    # a bound volume lying in three-quarter view: solid cover, fine page edges, a ribbon
    p.append(path([(10, 34), (64, 12), (92, 34), (38, 60)]) + path([(46, 30), (62, 23.5), (72, 31), (56, 38)]))
    p.append(path([(10, 34), (38, 60), (38, 67), (10, 41)]))
    for i in range(5):
        y = 62.5 + 3.6 * i
        p.append(line(38.5, y, 92, y - 25.5 + i * 0.1, w=0.26))
    p.append(line(38, 83, 92, 56, w=0.5))
    p.append(line(92, 34, 92, 57, w=0.35))
    p.append(path([(10, 41), (38, 67), (38, 83.5), (10, 58)]))
    p.append(brush([(62, 45, 0.9), (63, 56, 1.1), (61, 66, 1.0), (66, 78, 0.8), (73, 88, 0.45), (80, 92, 0.05)]))
    return p


def data():
    p = []
    cx, rx, ry = 50, 36, 11
    for y, solid in ((18, True), (38, False), (58, False)):
        if solid:
            p.append(path([(cx + rx * math.cos(i * math.pi / 30), y + ry * math.sin(i * math.pi / 30)) for i in range(60)])
                     + path([(cx + rx * .62 * math.cos(-i * math.pi / 30) - 2, y - 1 + ry * .62 * math.sin(-i * math.pi / 30)) for i in range(60)]))
        else:
            p.append(ring(cx, y, rx, ry, thick=1.0, thin=0.05, phase=1.57, turn=.5))
    p.append(ring(cx, 80, rx, ry, thick=1.25, thin=0.1, phase=1.57, turn=.5, start=0))
    p.append(line(14, 18, 14, 80, w=0.5))
    p.append(line(86, 18, 86, 80, w=0.8))
    return p


def hpc():
    p = []
    # a tower of nodes in three-quarter view: solid front cut by hairline bays, a fine side, a cable
    f = []
    x0, x1 = 22, 62
    for i in range(7):
        y0 = 11 + 11.1 * i
        f.append(path([(x0, y0 + 2.2 - i * .34), (x1, y0 - i * .1), (x1, y0 + 9.4 - i * .1), (x0, y0 + 11.1 - i * .34)]))
    p += f
    p.append(line(62, 9, 84, 19, w=0.55))
    p.append(line(62, 88, 84, 80, w=0.55))
    p.append(line(84, 19, 84, 80, w=0.7))
    for i in range(1, 7):
        y = 10 + 11.1 * i
        p.append(line(64, y, 82.4, 19 + 10.1 * i, w=0.26))
    p.append(line(62, 9, 44, 4, w=0.45))
    p.append(line(44, 4, 22, 12, w=0.45))
    p.append(line(44, 4, 84, 19, w=0.25))
    p.append(brush([(84, 74, 0.7), (92, 80, 0.6), (93, 90, 0.45), (84, 95, 0.3), (72, 94, 0.05)]))
    return p


def leaf(x, y, a, s):
    c, d = math.cos(a), math.sin(a)
    return brush([(x, y, 0.05), (x + c * s * .5, y + d * s * .5, s * .17), (x + c * s, y + d * s, 0.05)], 8)


def wreath(cx, cy, r):
    p = []
    for side in (-1, 1):
        pts = []
        for i in range(9):
            t = -1.25 + i * 0.31
            a = math.pi / 2 + side * (t + 1.35) * 1.15
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            pts.append((x, y, 0.5 - i * .05))
            out = a + side * -0.55
            inner = a + side * (math.pi + .55) 
            s = 15 - i * .75
            p.append(leaf(x, y, a - side * 1.05, s))
            p.append(leaf(x, y, a + side * 2.1, s * .7))
        p.append(brush(pts, 4))
    return p


def grant():
    p = []
    cx, cy, r = 50, 38, 28
    p.append(ring(cx, cy, r, r, thick=1.6, thin=0.1, phase=2.3))
    p.append(ring(cx, cy, r - 5, r - 5, thick=.28, thin=.05, phase=2.3))
    for i in range(16):
        a = 2 * math.pi * i / 16
        p.append(line(cx + (r - 8) * math.cos(a), cy + (r - 8) * math.sin(a), cx + (r - 13) * math.cos(a), cy + (r - 13) * math.sin(a), w=.5))
    p.append(sparkle(cx, cy, 12, .22))
    p.append(brush([(36, 63, 3.4), (32, 75, 3.2), (26, 90, 2.8), (24, 97, .1)], 8))
    p.append(brush([(64, 63, 3.4), (68, 75, 3.2), (74, 90, 2.8), (76, 97, .1)], 8))
    return p


def proposal():
    p = []
    # a fountain-pen nib seen from above, signing
    p.append(path([(52, 62), (58, 30), (76, 8), (88, 18), (72, 44)])
             + path([(62.6, 41.5), (65, 45.6), (61, 48), (60, 44.5)]))
    p.append(poly((52, 62), (53, 60.8), (63, 47.3), (62.6, 46.6)))
    p.append(brush([(52, 62, .5), (44, 71, .7), (34, 66, .9), (25, 74, .6), (32, 80, .5), (23, 87, .75), (14, 84, .4), (5, 89, .04)]))
    p.append(line(6, 95, 92, 91, w=.42))
    return p


def observing():
    p = []
    # a refractor on a tripod, tilted at the sky, with a star
    p.append(path([(16, 62), (61, 26), (66, 32.5), (22, 71)]))
    p.append(path([(61, 20), (73, 11), (80, 20.5), (67, 34.5)]))
    p.append(ring(76.5, 15.5, 3, 6.6, rot=-38, thick=.8, thin=.12))
    p.append(path([(10, 62), (17.5, 57), (23, 66), (15.5, 71)]))
    p.append(ring(44, 53, 3.2, 3.2, thick=1.7, thin=1.2))
    p.append(line(44, 55, 27, 94, w=.8))
    p.append(line(44, 55, 61, 94, w=.8))
    p.append(line(44, 55, 45, 88, w=.5))
    p.append(line(33.5, 80, 55, 80, w=.28))
    p.append(sparkle(92, 8, 7))
    p.append(sparkle(82, 44, 3))
    return p


def software():
    p = []
    p.append(brush([(38, 18, .05), (28, 30, .9), (9, 50, 2.9), (11, 52.5, 2.5), (28, 71, 1.0), (39, 82, .05)], 8))
    p.append(brush([(62, 18, .05), (72, 30, 1.0), (91, 48, 2.5), (89, 51, 2.9), (72, 70, .9), (61, 82, .05)], 8))
    p.append(brush([(61, 8, .05), (55, 30, 1.5), (47, 62, 2.2), (39, 92, .05)], 8))
    return p


def position():
    p = []
    # a portico in three-quarter view: pediment, entablature, fluted columns as tapered shafts
    p.append(line(6, 34, 50, 7, w=.95))
    p.append(line(50, 7, 94, 28, w=.7))
    p.append(path([(6, 34), (94, 28), (94, 33), (6, 39.5)]))
    for x, dy in ((14, 0), (34, -1.4), (54, -2.8), (74, -4.2)):
        p.append(poly((x, 44 + dy), (x + 8, 43.4 + dy), (x + 7, 85 + dy * .4), (x + 1, 85.4 + dy * .4)))
    p.append(line(6, 90, 92, 85, w=.8))
    p.append(line(2, 96, 96, 90.5, w=.5))
    return p


def degree():
    p = []
    p.append(path([(50, 16), (96, 36), (50, 58), (4, 36)]))
    p.append(brush([(22, 49, .4), (23, 64, .55), (36, 76, .7), (54, 77, .7), (72, 66, .5), (76, 50, .3)]))
    p.append(brush([(50, 37, .4), (68, 40, .5), (86, 44, .5), (89, 58, .45), (86, 72, .3), (84, 80, .1)]))
    p.append(poly((81, 80), (87, 80), (90, 96), (79, 96)))
    return p


def service():
    p = []
    # a leaf of a calendar, its lower corner turning over; one day inked in
    p.append(path([(12, 16), (86, 10), (87, 28), (12, 34)]))
    p.append(line(12, 34, 13, 92, w=.55))
    p.append(line(87, 28, 87, 70, w=.5))
    p.append(line(13, 92, 62, 89, w=.65))
    p.append(path([(87, 70), (62, 89), (67, 78), (76, 72)]))
    for x in (30, 68):
        p.append(ring(x, 13, 2.4, 6.5, thick=.9, thin=.2))
    for r in range(3):
        for c in range(5):
            if (r, c) == (2, 3) or (r, c) == (2, 4):
                continue
            x, y = 21 + 12.5 * c, 42 + 13 * r - c * .5
            if (r, c) == (1, 2):
                p.append(poly((x - 3.4, y - 3.8), (x + 4.6, y - 4.2), (x + 4.8, y + 3.8), (x - 3.2, y + 4.2)))
            else:
                p.append(line(x - 2.8, y, x + 3.8, y - .3, w=.42))
    return p


def award():
    return wreath(50, 46, 34) + [sparkle(50, 42, 15, .2)]


MARKS = dict(talk=talk, invited=invited, seminar=seminar, poster=poster, pitch=pitch, article=article, lead=lead,
             thesis=thesis, data=data, hpc=hpc, grant=grant, proposal=proposal, observing=observing, software=software,
             position=position, degree=degree, service=service, award=award)

parts = ['<svg xmlns="http://www.w3.org/2000/svg">']
for name, fn in MARKS.items():
    body = "".join(f'<path d="{d}"/>' for d in fn())
    parts.append(f'<symbol id="mk-{name}" viewBox="0 0 100 100"><g fill="currentColor" fill-rule="evenodd">{body}</g></symbol>')
parts.append("</svg>")
OUT.write_text("\n".join(parts) + "\n")
print(OUT, f"{OUT.stat().st_size / 1024:.0f} KB")
