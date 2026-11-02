"""Build the figure for the field-guide page on ESO and the VLT: where ESO's sites are in Chile, and
Paranal itself as a rendered site model (figures/eso/paranal_render.py) with a drawn overlay: the
four Unit Telescopes and the light ducts under the platform; UT2, open for the night, is boxed and
shown in an inset with its enclosure removed and the path of the light down to the Coude room.

Usage: uv run --with numpy python figures/eso/build_eso_figure.py _includes/figures/eso-vlt.svg

Sources
- Unit Telescopes (east and north of the array centre, metres), the array centre
  (longitude -70.40479659, latitude -24.62794830) and the platform rotation (-18.984 degrees):
  ESO, VLTI Station Position Technical Data, https://www.eso.org/observing/etc/doc/viscalc/vltistations.html
  The UT1 to UT4 baseline they give, 130.2 m (113.2 m east, 64.3 m north), matches the VLTI User
  Manual (VLT-MAN-ESO-15000-4552).
- La Silla (29 15 40.2 S, 70 43 52.8 W) and Cerro Armazones, site of the ELT (24 36 S, 70 11 30 W):
  ESO, Travel and Contacts, https://www.eso.org/public/about-eso/travel/
- Chile: Natural Earth 1:10m admin-0 countries (public domain), clipped, simplified and projected into
  this figure's map panel; figures/eso/chile_outline.txt holds the resulting path.
- The light ducts: Pepe et al. 2014 (arXiv:1401.5918) describe the light of each Unit Telescope
  taken from the Nasmyth B focus down to a Coude room under the telescope and on through ducts in
  the rock to the Combined-Coude Laboratory, 48 m (UT2) to 69 m (UT1) long. Grupp et al. 2020
  (arXiv:2004.12499) give the laboratory as about 10.7 m by 20 m and each Coude room 8.5 m across.
  The laboratory is placed where circles of 48 m round UT2 and 69 m round UT1 meet, (54.7, 3.7) m;
  the other intersection would put UT4 134 m away, beyond the published range. Its orientation is
  not published; it is drawn square to the platform. Ducts are drawn straight.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

UT = {  # station: (east m, north m, name)
    "UT1": (-9.925, -20.335, "Antu"),
    "UT2": (14.887, 30.502, "Kueyen"),
    "UT3": (44.915, 66.183, "Melipal"),
    "UT4": (103.306, 43.999, "Yepun"),
}
NU = math.radians(-18.984)  # platform rotation from north
PARANAL = (-70.40479659, -24.62794830)
LON0, LON1, LAT0, LAT1 = -76.0, -66.0, -57.0, -17.2

W, H = 1200, 650
MAP = (20, 40, 290, 600)  # x, y, w, h of the map panel: the whole of Chile
ROOT = Path(__file__).resolve().parents[2]
CAMS = json.loads((ROOT / "figures/eso/paranal_cameras.json").read_text())
ZP = 2635.0
CROP = (160.0, 150.0, 1110.0, 800.0)  # the part of the site render shown, render pixels
PANEL = (330.0, 20.0, 854.0)  # x, y, width of the render panel
INSET = (342.0, 330.0, 0.61, (120.0, 60.0, 580.0, 500.0))  # in the render panel's open lower left  # x, y, scale and source crop of the UT2 close-up
CCL = (54.7, 3.7)  # Combined-Coude Laboratory, metres east and north (see the sources)
ZDUCT = ZP - 6.0  # the ducts, drawn below the platform


def f(v):
    return f"{v:.1f}"


def draw(cls, d, t, dur=0.5, extra=""):
    return f'<path class="{cls} b-draw" style="--d:{t:.2f}s;--dur:{dur:.2f}s" pathLength="1" d="{d}"{extra}/>'


def pop(inner, t):
    return f'<g class="b-pop" style="--d:{t:.2f}s">{inner}</g>'


def text(x, y, s, cls, t, anchor="start", extra=""):
    return f'<text class="{cls} b-pop" style="--d:{t:.2f}s" x="{f(x)}" y="{f(y)}" text-anchor="{anchor}"{extra}>{s}</text>'


def map_panel():
    mx, my, mw, mh = MAP
    c = math.cos(math.radians(37.0))
    k = min(mw / ((LON1 - LON0) * c), mh / (LAT1 - LAT0))
    ox = mx + 50

    def px(lon, lat):
        return ox + (lon - LON0) * c * k, my + (LAT1 - lat) * k

    parts = [text(mx, my - 14, "ESO SITES IN CHILE", "eso-head", 0.0)]
    parts.append(draw("eso-chile", (ROOT / "figures/eso/chile_outline.txt").read_text().strip(), 0.05, 0.9))
    sites = [(PARANAL[0], PARANAL[1], "Paranal", "VLT", "end", -9),
             (-(70 + 11 / 60 + 30 / 3600), -(24 + 36 / 60), "Cerro Armazones", "ELT", "start", 9),
             (-(70 + 43 / 60 + 52.8 / 3600), -(29 + 15 / 60 + 40.2 / 3600), "La Silla", "", "end", -9)]
    for i, (lon, lat, lab, sub, anchor, dx) in enumerate(sites):
        x, y = px(lon, lat)
        t = 0.5 + 0.12 * i
        parts.append(pop(f'<rect class="eso-site" x="{f(x - 3.5)}" y="{f(y - 3.5)}" width="7" height="7"/>', t))
        if lab == "Cerro Armazones":
            lx, ly = px(-67.4, -26.4)
            parts.append(draw("bp-thin", f"M{f(x + 3)} {f(y + 3)} L{f(lx - 4)} {f(ly - 4)}", t, 0.17))
            parts.append(text(lx, ly, lab, "bp-label2", t, "start"))
            parts.append(text(lx, ly + 14, sub, "bp-tick", t, "start"))
            continue
        parts.append(text(x + dx, y + 4, lab, "bp-label2", t, anchor))
        if sub:
            parts.append(text(x + dx, y + 18, sub, "bp-tick", t, anchor))
    return parts, px(*PARANAL)


def camera(view):
    c = CAMS[view]
    cam, fwd, right, up = (np.array(c[k]) for k in ("cam", "fwd", "right", "up"))
    w, h = c["size"]

    def P(e, n, z):
        q = np.array([e, n, z], float) - cam
        zc = q @ fwd
        return w / 2 + c["f"] * (q @ right) / zc, h / 2 - c["f"] * (q @ up) / zc
    return P, cam


def occluded(cam, pt, solids):
    """Whether the sight line from the camera to pt passes through one of the vertical cylinders
    (e, n, radius, z0, z1) before reaching it."""
    d = np.array(pt, float) - cam
    for e, n, r, z0, z1 in solids:
        ox, oy = cam[0] - e, cam[1] - n
        a = d[0] ** 2 + d[1] ** 2
        b = 2 * (ox * d[0] + oy * d[1])
        cc = ox * ox + oy * oy - r * r
        disc = b * b - 4 * a * cc
        if disc > 0:
            for t in ((-b - math.sqrt(disc)) / (2 * a), (-b + math.sqrt(disc)) / (2 * a)):
                if 0 < t < 0.999 and z0 <= cam[2] + t * d[2] <= z1:
                    return True
        if d[2] != 0:
            t = (z1 - cam[2]) / d[2]
            if 0 < t < 0.999 and (ox + t * d[0]) ** 2 + (oy + t * d[1]) ** 2 < r * r:
                return True
    return False


def runs(pts3, P, cam, solids, to2):
    """The visible parts of a 3D polyline as SVG path data, in figure coordinates."""
    out, cur = [], []
    for a, b in zip(pts3[:-1], pts3[1:]):
        k = max(2, int(math.dist(a, b) / 1.0))
        for i in range(k + (1 if b is pts3[-1] else 0)):
            q = tuple(a[j] + (b[j] - a[j]) * i / k for j in range(3))
            if occluded(cam, q, solids):
                if len(cur) > 1:
                    out.append(cur)
                cur = []
            else:
                cur.append(to2(*P(*q)))
    if len(cur) > 1:
        out.append(cur)
    return " ".join("M" + " L".join(f"{f(x)} {f(y)}" for x, y in r) for r in out)


def label(x, y, s, t, anchor="start", cls="bp-label2 eso-halo"):
    return text(x, y, s, cls, t, anchor)


def leader(x0, y0, x1, y1, t):
    return draw("bp-thin eso-lead", f"M{f(x0)} {f(y0)} L{f(x1)} {f(y1)}", t, 0.2)


def site_panel():
    P, cam = camera("site")
    cx0, cy0, cx1, cy1 = CROP
    px, py, pw = PANEL
    k = pw / (cx1 - cx0)
    ph = (cy1 - cy0) * k

    def to2(x, y):
        return px + (x - cx0) * k, py + (y - cy0) * k

    def at(e, n, z):
        return to2(*P(e, n, z))

    feats = CAMS["features"]
    solids = [(e, n, 14.2, ZP, ZP + (10.0 if s == "UT2" else 29.0)) for s, (e, n, _) in UT.items()]
    solids.append((*feats["vst"], 6.6, ZP, ZP + 12.0))
    w, h = CAMS["site"]["size"]
    parts = [
        '<clipPath id="eso-site-clip"><rect x="{}" y="{}" width="{}" height="{}" rx="4"/></clipPath>'.format(f(px), f(py), f(pw), f(ph)),
        '<g clip-path="url(#eso-site-clip)" class="b-pop" style="--d:0.1s">',
    ]
    for th in ("light", "dark"):
        parts.append(f'<image class="eso-img-{th}" x="{f(px - cx0 * k)}" y="{f(py - cy0 * k)}" width="{f(w * k)}" height="{f(h * k)}" '
                     f'href="/assets/img/guide/paranal-render-{th}.webp"/>')
    # the light ducts under the platform, from each Coude room to the Combined-Coude Laboratory
    ccl_c, ccl_s = math.cos(NU), math.sin(NU)
    rect = [(CCL[0] + a * ccl_c - b * ccl_s, CCL[1] + a * ccl_s + b * ccl_c) for a, b in ((-5.35, -10), (5.35, -10), (5.35, 10), (-5.35, 10), (-5.35, -10))]
    duct = []
    for i, (st, (e, n, _)) in enumerate(UT.items()):
        L = math.hypot(CCL[0] - e, CCL[1] - n)
        ux, uy = (CCL[0] - e) / L, (CCL[1] - n) / L
        a = (e + ux * 4.25, n + uy * 4.25, ZDUCT)
        b = (CCL[0] - ux * 6.0, CCL[1] - uy * 6.0, ZDUCT)
        d = runs([a, b], P, cam, solids, to2)
        if d:
            duct.append(f'<path class="ray flowray eso-duct" d="{d}"/>')
        room = [(e + 4.25 * math.cos(t_), n + 4.25 * math.sin(t_), ZDUCT) for t_ in np.linspace(0, 2 * math.pi, 33)]
        d = runs(room, P, cam, solids, to2)
        if d:
            duct.append(f'<path class="eso-hidden" d="{d}"/>')
    d = runs([(x, y, ZDUCT) for x, y in rect], P, cam, solids, to2)
    duct.append(f'<path class="eso-hidden eso-ccl" d="{d}"/>')
    parts.append(f'<g class="b-pop" style="--d:1.2s">{"".join(duct)}</g>')
    parts.append("</g>")
    parts.append(f'<rect class="eso-panel" x="{f(px)}" y="{f(py)}" width="{f(pw)}" height="{f(ph)}" rx="4"/>')
    parts.append(text(px + 14, py + 22, "PARANAL", "eso-head eso-halo", 0.0))

    # names, with leaders; offsets in figure pixels, chosen to fall in free space
    t = 0.5

    def callout(p3, dx, dy, txt, tt, anchor="start", cls="bp-label2 eso-halo", sub=None):
        x, y = at(*p3)
        parts.append(leader(x, y, x + dx, y + dy, tt))
        ty_ = y + dy + (-5 if dy < 0 else 13)
        tx_ = x + dx + (4 if anchor == "start" else -4 if anchor == "end" else 0)
        parts.append(label(tx_, ty_, txt, tt, anchor, cls))
        if sub:
            parts.append(label(tx_, ty_ + 14, sub, tt, anchor, "bp-tick eso-halo"))

    callout((*UT["UT4"][:2], ZP + 29.5), 0, -20, "UT4", t, "middle")
    callout((*UT["UT3"][:2], ZP + 29.5), -24, -18, "UT3", t + 0.08, "end")
    callout((*UT["UT1"][:2], ZP + 29.5), 16, -18, "UT1", t + 0.16)
    callout((CCL[0], CCL[1], ZDUCT), 40, 138, "Combined-Coudé Laboratory", 1.3, "middle", "bp-label2 eso-halo eso-acc")
    # UT2, open, boxed as the detail shown in the inset
    bx = [at(*UT["UT2"][:2], z) for z in (ZP, ZP + 30)]
    x0_, x1_ = bx[0][0] - 34, bx[0][0] + 34
    y0_, y1_ = bx[1][1] - 8, bx[0][1] + 14
    parts.append(pop(f'<rect class="eso-detail" x="{f(x0_)}" y="{f(y0_)}" width="{f(x1_ - x0_)}" height="{f(y1_ - y0_)}" rx="3"/>', 1.2))
    parts.append(label(x0_ - 4, y0_ + 12, "UT2", 1.2, "end"))
    # north
    # north, as it runs on the platform, drawn in the panel's top right corner
    p0, p1 = at(0, 0, ZP), at(0, 20, ZP)
    L = math.dist(p0, p1)
    ux, uy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L
    a = (px + pw - 40 - ux * 13, py + 40 - uy * 13)
    tip = (a[0] + ux * 26, a[1] + uy * 26)
    parts.append(pop(f'<path class="bp" d="M{f(a[0])} {f(a[1])} L{f(tip[0])} {f(tip[1])} M{f(tip[0] - 6 * ux - 4 * uy)} {f(tip[1] - 6 * uy + 4 * ux)} '
                     f'L{f(tip[0])} {f(tip[1])} L{f(tip[0] - 6 * ux + 4 * uy)} {f(tip[1] - 6 * uy - 4 * ux)}"/>', 0.3))
    parts.append(label(tip[0] + ux * 10, tip[1] + uy * 10 + 4, "N", 0.3, "middle"))
    return parts, (px, py, pw, ph), (x0_, y1_)


def ut2_panel(ut2_main):
    P, cam = camera("ut2")
    w, h = CAMS["ut2"]["size"]
    ix, iy, k, (sx0, sy0, sx1, sy1) = INSET
    iw, ih = (sx1 - sx0) * k, (sy1 - sy0) * k

    def to2(x, y):
        return ix + (x - sx0) * k, iy + (y - sy0) * k

    def at(p):
        return to2(*P(*p))

    e0, n0, _ = UT["UT2"]
    # the telescope's pose, as built in figures/eso/paranal_render.py
    pose = CAMS["features"]["pose"]
    hv = np.array([pose["toward"][0], pose["toward"][1], 0.0])
    hv /= np.linalg.norm(hv)
    lat = np.array([-hv[1], hv[0], 0.0])
    alt = math.radians(pose["alt"])
    dv = hv * math.cos(alt) + np.array([0, 0, 1.0]) * math.sin(alt)
    o = np.array([e0, n0, ZP + 18.5])
    m1 = o - dv * 1.95
    m2 = o + dv * 10.3
    e1 = np.cross(dv, lat)
    # Nasmyth B: the end of the elevation axis on the side facing the viewer
    sg = 1 if (o + lat * 9 - cam) @ (o + lat * 9 - cam) < (o - lat * 9 - cam) @ (o - lat * 9 - cam) else -1
    nas = o + lat * sg * 6.6
    room_z = ZP - 6.0
    parts = [
        f'<rect class="eso-frame" x="{f(ix)}" y="{f(iy)}" width="{f(iw)}" height="{f(ih)}" rx="3"/>',
        f'<clipPath id="eso-ut2-clip"><rect x="{f(ix)}" y="{f(iy)}" width="{f(iw)}" height="{f(ih)}" rx="4"/></clipPath>',
        '<g clip-path="url(#eso-ut2-clip)" class="b-pop" style="--d:1.4s">',
    ]
    for t_ in ("light", "dark"):
        parts.append(f'<image class="eso-img-{t_}" x="{f(ix - sx0 * k)}" y="{f(iy - sy0 * k)}" width="{f(w * k)}" height="{f(h * k)}" '
                     f'href="/assets/img/guide/paranal-ut2-{t_}.webp"/>')
    parts.append("</g>")
    parts.append(f'<rect class="eso-detail" x="{f(ix)}" y="{f(iy)}" width="{f(iw)}" height="{f(ih)}" rx="3"/>')
    # the Coude room under the telescope, 8.5 m across (Grupp et al. 2020), hidden in the rock
    room = [at((e0 + 4.25 * math.cos(a_), n0 + 4.25 * math.sin(a_), z)) for z in (room_z - 3.0, room_z + 2.0) for a_ in np.linspace(0, 2 * math.pi, 41)]
    lo, hi = room[:41], room[41:]
    rh = _hull(lo + hi)
    parts.append(pop('<path class="eso-hidden" d="M' + " L".join(f"{f(x)} {f(y)}" for x, y in rh) + ' Z"/>', 1.9))
    # the light: in from the sky to the primary mirror, to the secondary, to the tertiary at the
    # crossing of the axes, out to the Nasmyth B focus, then down the fork to the Coude room
    beam = []
    for sgn in (1, -1):
        rim = m1 + e1 * sgn * 3.9
        beam.append([rim + dv * 4.0, rim, m2 + e1 * sgn * 0.6])
    beam.append([m2, o, nas, np.array([nas[0], nas[1], room_z + 2.0]), np.array([e0, n0, room_z + 2.0])])
    hl = []
    for pts in beam:
        q = [at(tuple(p)) for p in pts]
        hl.append("M" + " L".join(f"{f(x)} {f(y)}" for x, y in q))
    parts.append(f'<g class="b-pop" style="--d:2.0s"><path class="ray flowray eso-light" d="{" ".join(hl)}"/></g>')
    # labels, in the inset's free corners
    t = 2.0

    def note(p3, lx, ly, txt, anchor):
        x, y = at(tuple(p3))
        ex = ix + lx + (6 if anchor == "start" else -6 if anchor == "end" else 0)
        parts.append(leader(x, y, ex, iy + ly - 4, t))
        parts.append(label(ix + lx + (8 if anchor == "start" else -8 if anchor == "end" else 0), iy + ly, txt, t, anchor, "bp-tick eso-halo"))

    note(m2, 274, 62, "secondary mirror", "end")
    note(m1 + e1 * 3.0, 274, 170, "primary mirror", "end")
    x, y = at((e0, n0, room_z - 1.0))
    parts.append(label(x - 26, y + 4, "Coudé room", t + 0.2, "end", "bp-tick eso-halo"))
    parts.append(text(ix + 10, iy + 20, "UT2, ENCLOSURE REMOVED", "eso-head eso-halo", 1.5))
    # the call-out from the site view
    parts.insert(0, draw("eso-callout", f"M{f(ut2_main[0])} {f(ut2_main[1])} L{f(ix + iw)} {f(iy)}", 1.3, 0.4))
    return parts


def _hull(pts):
    p = sorted(set((round(x, 2), round(y, 2)) for x, y in pts))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for q in p:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], q) <= 0:
            lower.pop()
        lower.append(q)
    for q in reversed(p):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], q) <= 0:
            upper.pop()
        upper.append(q)
    return lower[:-1] + upper[:-1]


def main(out):
    m, (pxx, pyy) = map_panel()
    site, (px, py, pw, ph), ut2 = site_panel()
    inset = ut2_panel(ut2)
    # the thread from Paranal on the map to the site panel
    ty = py + 36
    thread = (
        f'<g class="b-pop" style="--d:1.0s"><path class="ray flowray eso-thread" d="M{f(pxx + 4)} {f(pyy - 4)} C{f(pxx + 30)} {f(pyy - 50)}, '
        f'{f(px - 50)} {f(ty)}, {f(px - 4)} {f(ty)}"/>'
        f'<rect class="eso-site" x="{f(px - 4)}" y="{f(ty - 3)}" width="6" height="6"/></g>'
    )
    svg = (
        f'<svg class="bp-svg eso-svg" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-labelledby="eso-ft eso-fd"><title id="eso-ft">ESO\'s sites in Chile, and Paranal with the four Unit Telescopes</title>'
        '<desc id="eso-fd">Left: Chile with ESO\'s sites at Paranal, Cerro Armazones, where the ELT is being built, and '
        'La Silla. Right: a rendered model of the Paranal summit seen from the west, with the four Unit Telescopes, '
        'UT2 open for the night, and the light ducts under the platform from each Unit Telescope to the '
        'Combined-Coudé Laboratory. Inset: UT2 with its enclosure removed, showing the telescope on its fork and the path of the '
        'light from the primary mirror to the secondary, to the Nasmyth B focus and down to the Coudé room.</desc>'
        + "".join(m) + "".join(site) + thread + "".join(inset) + "</svg>\n"
    )
    Path(out).write_text(svg)
    print(f"wrote {out} ({len(svg) / 1024:.1f} KB)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1])
