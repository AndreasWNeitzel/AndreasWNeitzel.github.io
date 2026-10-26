"""Build the figure for the field-guide page on ESO and the VLT: where ESO's sites are in Chile, and
the four Unit Telescopes on the Paranal platform.

Usage: uv run --with pyshp --with shapely --with numpy python figures/eso/build_eso_figure.py \
    <ne_10m_admin_0_countries.shp> _includes/figures/eso-vlt.svg

Sources
- Unit Telescope stations (east and north of the array centre, metres), the array centre
  (longitude -70.40479659, latitude -24.62794830) and the platform rotation (-18.984 degrees):
  ESO, VLTI Station Position Technical Data, https://www.eso.org/observing/etc/doc/viscalc/vltistations.html
  The UT1 to UT4 baseline they give, 130.2 m (113.2 m east, 64.3 m north), matches the VLTI User
  Manual (VLT-MAN-ESO-15000-4552).
- La Silla (29 15 40.2 S, 70 43 52.8 W) and Cerro Armazones, site of the ELT (24 36 S, 70 11 30 W):
  ESO, Travel and Contacts, https://www.eso.org/public/about-eso/travel/
- Coastline and borders: Natural Earth 1:10m admin-0 countries (public domain).
"""

from __future__ import annotations

import math
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import shapefile
from shapely.geometry import Polygon, box, shape
from shapely.ops import unary_union

UT = {  # station: (east m, north m, name)
    "UT1": (-9.925, -20.335, "Antu"),
    "UT2": (14.887, 30.502, "Kueyen"),
    "UT3": (44.915, 66.183, "Melipal"),
    "UT4": (103.306, 43.999, "Yepun"),
}
NU = math.radians(-18.984)  # platform rotation from north
PARANAL = (-70.40479659, -24.62794830)
SITES = [  # (lon, lat, label, sub, dx, dy, anchor)
    (PARANAL[0], PARANAL[1], "Paranal", "Very Large Telescope", -10, 4, "end"),
    (-(70 + 11 / 60 + 30 / 3600), -(24 + 36 / 60), "Cerro Armazones", "ELT, under construction", 10, 4, "start"),
    (-(70 + 43 / 60 + 52.8 / 3600), -(29 + 15 / 60 + 40.2 / 3600), "La Silla", "", -10, 4, "end"),
]
LON0, LON1, LAT0, LAT1 = -75.2, -66.0, -33.9, -21.2

W, H = 1120, 460
MAP = (20, 40, 300, 396)  # x, y, w, h of the map panel
PLAN = (380, 30, 724, 416)  # x, y, w, h of the framed platform inset


def f(v):
    return f"{v:.1f}"


def draw(cls, d, t, dur=0.5, extra=""):
    return f'<path class="{cls} b-draw" style="--d:{t:.2f}s;--dur:{dur:.2f}s" pathLength="1" d="{d}"{extra}/>'


def pop(inner, t):
    return f'<g class="b-pop" style="--d:{t:.2f}s">{inner}</g>'


def text(x, y, s, cls, t, anchor="start", extra=""):
    return f'<text class="{cls} b-pop" style="--d:{t:.2f}s" x="{f(x)}" y="{f(y)}" text-anchor="{anchor}"{extra}>{s}</text>'


def map_panel(shp_path):
    mx, my, mw, mh = MAP
    c = math.cos(math.radians(27.5))
    k = min(mw / ((LON1 - LON0) * c), mh / (LAT1 - LAT0))
    ox = mx + (mw - (LON1 - LON0) * c * k) / 2

    def px(lon, lat):
        return ox + (lon - LON0) * c * k, my + (LAT1 - lat) * k

    clip = box(LON0, LAT0, LON1, LAT1)
    r = shapefile.Reader(shp_path)
    fields = [fl[0] for fl in r.fields[1:]]
    iso = fields.index("ADM0_A3")
    chile = None
    for sr in r.iterShapeRecords():
        if sr.record[iso] == "CHL":
            chile = shape(sr.shape.__geo_interface__).intersection(clip).simplify(0.012)
    polys = [chile] if chile.geom_type == "Polygon" else list(chile.geoms)
    d = " ".join(
        "M" + " L".join(f"{f(a)} {f(b)}" for a, b in (px(x, y) for x, y in poly.exterior.coords)) + " Z"
        for poly in polys if poly.area > 0.002
    )
    parts = [text(mx, my - 14, "ESO SITES IN CHILE", "eso-head", 0.0)]
    parts.append(draw("eso-chile", d, 0.05, 0.9))
    for lat in (-24, -27, -30, -33):
        x0, y0 = px(LON0, lat)
        parts.append(draw("bp-thin", f"M{f(x0)} {f(y0)} h12", 0.1, 0.17))
        parts.append(text(x0 + 16, y0 + 4, f"{-lat}° S", "bp-tick", 0.2))
    xt0, yt = px(LON0, -23.4365)
    xt1, _ = px(LON1, -23.4365)
    parts.append(draw("eso-tropic", f"M{f(xt0)} {f(yt)} H{f(xt1)}", 0.15, 0.3))
    parts.append(text(xt0 + 2, yt - 5, "Tropic of Capricorn", "bp-tick", 0.3, "start"))
    for lon, lat, lab, anchor in ((-74.2, -26.0, "Pacific Ocean", "middle"), (-67.6, -31.0, "Argentina", "middle"),
                                  (-66.9, -21.8, "Bolivia", "middle"), (-69.0, -28.6, "Chile", "middle")):
        x, y = px(lon, lat)
        parts.append(text(x, y, lab, "eso-country", 0.2, anchor))
    sites = [(PARANAL[0], PARANAL[1], "Paranal", "VLT", "end", -9),
             (-(70 + 11 / 60 + 30 / 3600), -(24 + 36 / 60), "Cerro Armazones", "site of the ELT", "start", 9),
             (-(70 + 43 / 60 + 52.8 / 3600), -(29 + 15 / 60 + 40.2 / 3600), "La Silla", "", "end", -9)]
    for i, (lon, lat, lab, sub, anchor, dx) in enumerate(sites):
        x, y = px(lon, lat)
        t = 0.5 + 0.12 * i
        dy = 4
        parts.append(pop(f'<rect class="eso-site" x="{f(x - 3.5)}" y="{f(y - 3.5)}" width="7" height="7"/>', t))
        if lab == "Cerro Armazones":
            lx, ly = px(-67.9, -25.3)
            parts.append(draw("bp-thin", f"M{f(x + 3)} {f(y + 3)} L{f(lx - 4)} {f(ly - 4)}", t, 0.17))
            parts.append(text(lx, ly, lab, "bp-label2", t, "start"))
            parts.append(text(lx, ly + 14, sub, "bp-tick", t, "start"))
            continue
        parts.append(text(x + dx, y + dy, lab, "bp-label2", t, anchor))
        if sub:
            parts.append(text(x + dx, y + dy + 14, sub, "bp-tick", t, anchor))
    x0, y0 = px(-75.0, -33.5)
    km = k * (100 / 111.32)
    parts.append(draw("bp", f"M{f(x0)} {f(y0)} h{f(km)} M{f(x0)} {f(y0 - 4)} v8 M{f(x0 + km)} {f(y0 - 4)} v8", 0.3, 0.2))
    parts.append(text(x0, y0 + 16, "100 km", "bp-tick", 0.3))
    return parts, px(*PARANAL)


def plan_panel():
    fx, fy, fw, fh = PLAN
    gx, gy, gw, gh = fx + 24, fy + 44, 400, fh - 70  # drawing area
    es = [v[0] for v in UT.values()]
    ns = [v[1] for v in UT.values()]
    pad = 18.0
    span_e = max(es) - min(es) + 2 * pad
    span_n = max(ns) - min(ns) + 2 * pad
    sc = min(gw / span_e, gh / span_n)
    cx = gx + (gw - span_e * sc) / 2 - (min(es) - pad) * sc
    cy = gy + (gh - span_n * sc) / 2 + (max(ns) + pad) * sc

    def p(e, n):
        return cx + e * sc, cy - n * sc

    parts = [pop(f'<rect class="eso-frame" x="{f(fx)}" y="{f(fy)}" width="{f(fw)}" height="{f(fh)}" rx="4"/>', 0.0),
             text(fx + 16, fy + 24, "THE PARANAL PLATFORM, SEEN FROM ABOVE", "eso-head", 0.0)]
    c0 = p(0, 0)
    parts.append(pop(f'<path class="bp" d="M{f(c0[0] - 5)} {f(c0[1])} h10 M{f(c0[0])} {f(c0[1] - 5)} v10"/>', 0.2))
    parts.append(text(c0[0] + 8, c0[1] + 15, "array centre", "bp-tick", 0.25))
    t = 0.45
    for (a, va), (b, vb) in combinations(UT.items(), 2):
        pa, pb = p(va[0], va[1]), p(vb[0], vb[1])
        parts.append(draw("eso-base", f"M{f(pa[0])} {f(pa[1])} L{f(pb[0])} {f(pb[1])}", t, 0.3))
        t += 0.06
    # the longest baseline as a dimension line, offset from the telescopes
    (e1, n1, _), (e4, n4, _) = UT["UT1"], UT["UT4"]
    L = math.hypot(e4 - e1, n4 - n1)
    ux, uy = (e4 - e1) / L, (n4 - n1) / L
    off = 14.0  # metres, perpendicular, to the south-east side
    q1 = p(e1 + off * (uy), n1 + off * (-ux))
    q4 = p(e4 + off * (uy), n4 + off * (-ux))
    parts.append(draw("eso-dim", f"M{f(q1[0])} {f(q1[1])} L{f(q4[0])} {f(q4[1])}", 0.9, 0.3))
    for (e, n), q in (((e1, n1), q1), ((e4, n4), q4)):
        a = p(e + 3 * uy, n - 3 * ux)
        parts.append(draw("bp-thin", f"M{f(a[0])} {f(a[1])} L{f(q[0])} {f(q[1])}", 0.85, 0.17))
    mxp, myp = (q1[0] + q4[0]) / 2, (q1[1] + q4[1]) / 2
    ang = math.degrees(math.atan2(q4[1] - q1[1], q4[0] - q1[0]))
    parts.append(f'<text class="eso-len b-pop" style="--d:1.1s" transform="translate({f(mxp)} {f(myp)}) rotate({ang:.1f})" y="15" text-anchor="middle">{L:.1f} m, the longest baseline</text>'.replace('y="15"', 'y="16"'))
    for i, (st, (e, n, name)) in enumerate(UT.items()):
        x, y = p(e, n)
        tt = 0.2 + 0.08 * i
        parts.append(pop(f'<circle class="eso-mirror" cx="{f(x)}" cy="{f(y)}" r="{f(4.1 * sc)}"/>', tt))
        if st == "UT4":
            parts.append(text(x, y + 4.1 * sc + 18, f"{st} {name}", "bp-label2", tt, "middle"))
        else:
            parts.append(text(x + 4.1 * sc + 8, y + 4, f"{st} {name}", "bp-label2", tt, "start"))
    nx, ny = gx + gw - 6, gy + 18
    parts.append(pop(f'<path class="bp" d="M{f(nx)} {f(ny + 26)} V{f(ny)} M{f(nx - 5)} {f(ny + 8)} L{f(nx)} {f(ny)} L{f(nx + 5)} {f(ny + 8)}"/>', 0.3))
    parts.append(text(nx, ny - 6, "N", "bp-label2", 0.3, "middle"))
    sx, sy = gx + 4, gy + gh - 4
    parts.append(draw("bp", f"M{f(sx)} {f(sy)} h{f(20 * sc)} M{f(sx)} {f(sy - 4)} v8 M{f(sx + 20 * sc)} {f(sy - 4)} v8", 0.3, 0.2))
    parts.append(text(sx + 10 * sc, sy - 8, "20 m", "bp-tick", 0.3, "middle"))
    # station table and baselines, set as a drafting table
    tx, ty = gx + gw + 30, fy + 66
    parts.append(draw("bp-thin", f"M{f(tx - 16)} {f(fy + 44)} V{f(fy + fh - 20)}", 0.2, 0.17))
    parts.append(text(tx, ty, "STATION", "eso-th", 0.3))
    parts.append(text(tx + 180, ty, "EAST", "eso-th", 0.3, "end"))
    parts.append(text(tx + 256, ty, "NORTH", "eso-th", 0.3, "end"))
    for i, (st, (e, n, name)) in enumerate(UT.items()):
        y = ty + 22 + 19 * i
        parts.append(text(tx, y, f"{st} {name}", "eso-td", 0.4 + 0.05 * i))
        parts.append(text(tx + 180, y, f"{e:.1f} m".replace("-", "\u2212"), "eso-td", 0.4 + 0.05 * i, "end"))
        parts.append(text(tx + 256, y, f"{n:.1f} m".replace("-", "\u2212"), "eso-td", 0.4 + 0.05 * i, "end"))
    by = ty + 22 + 19 * 4 + 22
    parts.append(text(tx, by, "BASELINE", "eso-th", 0.6))
    parts.append(text(tx + 256, by, "LENGTH", "eso-th", 0.6, "end"))
    for i, ((a, va), (b, vb)) in enumerate(combinations(UT.items(), 2)):
        y = by + 22 + 19 * i
        parts.append(text(tx, y, f"{a} to {b}", "eso-td", 0.65 + 0.05 * i))
        parts.append(text(tx + 256, y, f"{math.hypot(va[0] - vb[0], va[1] - vb[1]):.1f} m", "eso-td", 0.65 + 0.05 * i, "end"))
    parts.append(text(tx, by + 22 + 19 * 6 + 10, "Metres from the array centre.", "bp-tick", 0.9))
    return parts


def main(shp_path, out):
    m, (pxx, pyy) = map_panel(shp_path)
    pl = plan_panel()
    # the thread from Paranal on the map to the platform panel: flowing, curved
    fx, fy, fw, fh = PLAN
    ty = fy + fh / 2
    thread = (
        f'<g class="b-pop" style="--d:1.0s"><path class="ray flowray eso-thread" d="M{f(pxx)} {f(pyy + 6)} C{f(pxx + 10)} {f(pyy + 120)}, '
        f'{f(fx - 70)} {f(ty)}, {f(fx - 4)} {f(ty)}"/>'
        f'<rect class="eso-site" x="{f(fx - 4)}" y="{f(ty - 3)}" width="6" height="6"/></g>'
    )
    svg = (
        f'<svg class="bp-svg eso-svg" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-labelledby="eso-ft eso-fd"><title id="eso-ft">ESO\'s sites in Chile and the four Unit Telescopes on Paranal</title>'
        '<desc id="eso-fd">Left: northern Chile with ESO\'s sites at Paranal, Cerro Armazones, where the ELT is being built, and '
        'La Silla. Right: the Paranal platform seen from above, with the four 8.2 m Unit Telescopes at their stations and the '
        'six baselines between them, from 46.6 m (UT2 to UT3) to 130.2 m (UT1 to UT4).</desc>'
        + "".join(m) + thread + "".join(pl) + "</svg>\n"
    )
    Path(out).write_text(svg)
    print(f"wrote {out} ({len(svg) / 1024:.1f} KB)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])
