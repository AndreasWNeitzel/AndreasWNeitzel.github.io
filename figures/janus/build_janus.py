#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy>=1.26", "scipy>=1.11", "matplotlib>=3.8", "pillow>=10"]
# ///
"""Build the JANUS figure on /research/janus/ as inline SVG, in two layouts (wide and phone).

Usage (from the repository root):
    uv run figures/janus/build_janus.py [--gaia-render PNG]

--gaia-render takes a transparent still of the spacecraft from figures/heroes/blender_gaia.py
(rendered with `blender_gaia.py OUT.png 20 96 1200 800`), crops it to its alpha box and writes
assets/img/figures/janus-gaia.webp at twice the drawn size. Without it the existing WebP is used.

The story, one stage each: Gaia, its XP spectrum, the APOGEE DR19 labels it learns from, the
JANUS ensemble (trunk and coupling layers), the labels with their spread and P(H), the catalogue of
TESS red giants, and the two machines it runs on. The figure is a dark plate in both themes.
White is linework and data, brass is the one accent: the thread, and the alpha-rich mode.

Real data:
- the spectrum: Gaia DR3 5289554869898620416, the median-[M/H] red giant of the playground set
  (assets/data/playground/gaia_xp_mh.json, row 97; GaiaXPy calibrated flux on a 2 nm grid).
  The part blueward of 660 nm comes from BP, the part redward from RP (they overlap from 640 to
  680 nm). H alpha (656.28 nm) and the Ca II triplet (849.80, 854.21, 866.21 nm) are ticked at
  their air wavelengths.
- the alpha plane: [alpha/M] against [Fe/H] for the 9,242 APOGEE DR19 giants of the recorded
  Starfold run (assets/data/starfold/apogee_run.*), as isodensity hairlines.
- the machines: node counts of Deucalion and MareNostrum 5 to scale, one square for 64 nodes
  (sources in figures/hpc/build_hpc_figure.py).
Schematic: the spacecraft render (proportions after ESA, not an engineering model), the network
(flow_samples below pushes a real Gaussian draw through five hand-written coupling layers), the
label shapes, P(H) and the table cells.

Every connector starts and ends on the outer edge of a square port; the script checks this.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from itertools import pairwise
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "assets/data/playground/gaia_xp_mh.json"
APOGEE = ROOT / "assets/data/starfold/apogee_run.json"
GAIA_WEBP = ROOT / "assets/img/figures/janus-gaia.webp"
OUT = ROOT / "_includes/figures/janus.svg"
EXAMPLE_ROW = 97
PORT = 7.0  # port square side
HALF = PORT / 2

# ------------------------------------------------------------------ helpers


def f(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".")


def timing(d: float, dur: float | None = None) -> str:
    return f'style="--d:{d:.2f}s{"" if dur is None else f";--dur:{dur:.2f}s"}"'


def draw(cls: str, d: str, t: float, dur: float = 0.4) -> str:
    return f'<path class="{cls} b-draw" pathLength="1" {timing(t, dur)} d="{d}"/>'


def pop(inner: str, t: float) -> str:
    return f'<g class="b-pop" {timing(t)}>{inner}</g>'


CHAR = {"jn-title": 0.50 * 19, "jn-lab": 0.60 * 12.5, "jn-tick": 0.60 * 12}


def text_w(s: str, cls: str) -> float:
    import re

    plain = re.sub(r"<[^>]+>", "", s).replace("&amp;", "&")
    return len(plain) * CHAR[cls.split()[0]]


def poly(pts) -> str:
    return "M" + " L".join(f"{f(x)} {f(y)}" for x, y in pts)


def smooth(pts, closed: bool = False) -> str:
    """Catmull-Rom spline through the points, as cubic Beziers."""
    n = len(pts)
    d = f"M{f(pts[0][0])} {f(pts[0][1])}"
    for i in range(n - 1):
        p0 = pts[max(i - 1, 0)]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[min(i + 2, n - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{f(c1[0])} {f(c1[1])} {f(c2[0])} {f(c2[1])} {f(p2[0])} {f(p2[1])}"
    return d + (" Z" if closed else "")


NORMAL = {"l": (-1, 0), "r": (1, 0), "t": (0, -1), "b": (0, 1)}


class Stage:
    """One stage in local coordinates: a title over a hairline rule, the object below, ports."""

    def __init__(self, key: str, title: str, w: float, h: float, t: float, italic: bool = False):
        self.key, self.title, self.w, self.h, self.t = key, title, w, h, t
        self.body: list[str] = []
        self.ports: dict[str, tuple[float, float, str]] = {}
        self.texts: list[tuple[float, float, str, str, str]] = []
        self.leads: dict[str, str] = {}
        it = ' style="font-style:italic"' if italic else ""
        self.text(0, 17, title, "jn-title", extra=it)
        self.body.append(draw("jn-g", f"M0 26 H{f(w)}", t - 0.15, 0.3))

    def text(self, x, y, s, cls, anchor="start", extra="", t=None):
        self.texts.append((x, y, s, cls, anchor))
        self.body.append(
            pop(f'<text class="{cls}" x="{f(x)}" y="{f(y)}" text-anchor="{anchor}"{extra}>{s}</text>', self.t if t is None else t)
        )

    def port(self, name: str, x: float, y: float, side: str):
        self.ports[name] = (x, y, side)

    def check(self):
        for x, y, s, cls, anchor in self.texts:
            w = text_w(s, cls)
            x0 = {"start": x, "middle": x - w / 2, "end": x - w}[anchor]
            assert x0 >= -0.5 and x0 + w <= self.w + 0.5, f"{self.key}: label {s!r} overflows ({x0:.1f}..{x0 + w:.1f} of {self.w})"

    def render(self, ox: float, oy: float, used: set[str]) -> str:
        self.check()
        sq = []
        for name in sorted(used):
            x, y, _ = self.ports[name]
            sq.append(f'<rect class="jn-port" x="{f(x - HALF)}" y="{f(y - HALF)}" width="{f(PORT)}" height="{f(PORT)}"/>')
        return (
            f'<g class="jn-stage" data-stage="{self.key}" tabindex="0" role="button" aria-label="{self.title}" '
            f'transform="translate({f(ox)} {f(oy)})">'
            f'<rect class="jn-hit" x="-8" y="-6" width="{f(self.w + 16)}" height="{f(self.h + 10)}" rx="6"/>'
            + "".join(self.body)
            + "".join(self.leads[n] for n in sorted(used) if n in self.leads)
            + pop("".join(sq), self.t + 0.2)
            + "</g>"
        )


# ------------------------------------------------------------------ data


def load_spectrum():
    spec = json.loads(SPEC.read_text())
    ex = next(e for e in spec["examples"] if e["row"] == EXAMPLE_ROW)
    w0, dw = spec["wavelength_nm"]["start"], spec["wavelength_nm"]["step"]
    lam = np.array([w0 + dw * i for i in range(len(ex["flux"]))])
    flux = np.array(ex["flux"], dtype=float)
    keep = (lam >= 360) & (lam <= 990)
    return lam[keep], flux[keep] / flux[keep].max(), ex["source_id"]


def load_apogee():
    meta = json.loads(APOGEE.read_text())
    raw = (APOGEE.parent / meta["binary"]).read_bytes()
    a = {x["name"]: x for x in meta["arrays"]}["features"]
    n, k = a["shape"]
    feat = np.frombuffer(raw, "<f4", count=n * k, offset=a["offset"]).reshape(n, k).astype(float)
    names = [c["name"] for c in meta["columns"]]
    return feat[:, names.index("fe_h")], feat[:, names.index("alpha_m")]


# ------------------------------------------------------------------ stages


def gaia_stage(img_w: int, img_h: int, w: float) -> Stage:
    s = Stage("gaia", "Gaia", w, 140, 0.2, italic=True)
    W = 178.0
    H = W * img_h / img_w
    ix, iy = w - W - 22, 32.0
    s.body.append(
        pop(
            f'<image class="jn-render" href="{{{{ \'/assets/img/figures/janus-gaia.webp\' | relative_url }}}}" '
            f'x="{f(ix)}" y="{f(iy)}" width="{f(W)}" height="{f(H)}" preserveAspectRatio="xMidYMid meet"/>',
            0.2,
        )
    )
    # the starlight: from a star into the near telescope aperture, located in the render
    ax, ay = ix + APERTURE[0] * W, iy + APERTURE[1] * H
    sx, sy = ix - 60, 52.0
    s.body.append(pop(f'<circle class="jn-star" cx="{f(sx)}" cy="{f(sy)}" r="2.2"/>', 0.25))
    s.body.append(pop(f'<path class="jn-spike" d="M{f(sx - 9)} {f(sy)} H{f(sx + 9)} M{f(sx)} {f(sy - 9)} V{f(sy + 9)}"/>', 0.25))
    s.body.append(draw("jn-light", f"M{f(sx + 4)} {f(sy + 1)} L{f(ax - 3)} {f(ay - 1)}", 0.4, 0.35))
    s.port("b", ix + W / 2, iy + H + 7, "b")
    s.h = iy + H + 11
    return s


def xp_stage(lam, flux, w: float, ph: float, pid: str) -> Stage:
    s = Stage("xp", "XP spectrum", w, ph + 92, 0.6)
    X0, X1, YT, YB = 0.0, w, 56.0, 56.0 + ph

    def x_of(nm):
        return X0 + (nm - 360) / (990 - 360) * (X1 - X0)

    def y_of(v):
        return YB - v * (YB - YT)

    pts = [(x_of(l), y_of(v)) for l, v in zip(lam, flux)]
    grad = (
        f'<linearGradient id="{pid}fade" gradientUnits="userSpaceOnUse" x1="0" y1="{f(YT)}" x2="0" y2="{f(YB)}">'
        '<stop offset="0" stop-color="#f4f1ea" stop-opacity=".5"/><stop offset="1" stop-color="#f4f1ea" stop-opacity=".03"/></linearGradient>'
    )
    s.body.append(f"<defs>{grad}</defs>")
    # an engraved fall of hairlines under the curve, one per sampled wavelength
    for lo, hi, cls in ((360, 660, "jn-comb"), (660, 990, "jn-comb jn-comb-rp")):
        d = "".join(
            f"M{f(x_of(l))} {f(y_of(v) + 3)}V{f(YB)}" for l, v in zip(lam, flux) if lo <= l < hi and int(l) % 4 == 0
        )
        s.body.append(pop(f'<path class="{cls}" stroke="url(#{pid}fade)" d="{d}"/>', 0.7))
    s.body.append(draw("jn-g", f"M{f(X0)} {f(YB)} H{f(X1)}", 0.5, 0.3))
    line = smooth(pts)
    s.body.append(pop(f'<path class="jn-halo2" d="{line}"/><path class="jn-halo1" d="{line}"/>', 1.0))
    s.body.append(draw("jn-spec", line, 0.6, 0.8))

    def tick(nm, top):
        return f"M{f(x_of(nm))} {f(y_of(float(np.interp(nm, lam, flux))) - 7)} V{f(top)}"

    s.body.append(draw("jn-line", tick(656.28, 46), 1.1, 0.2))
    s.body.append(draw("jn-line", " ".join(tick(nm, 46) for nm in (849.80, 854.21, 866.21)), 1.1, 0.2))
    s.text(x_of(656.28), 42, "Hα", "jn-tick", "middle", t=1.1)
    s.text(x_of(856.0), 42, "Ca II", "jn-tick", "middle", t=1.1)
    # the two photometers overlap: brackets under the axis
    for a, b, y in ((360, 680, YB + 10), (640, 990, YB + 17)):
        s.body.append(draw("jn-g2", f"M{f(x_of(a))} {f(y - 3)} V{f(y)} H{f(x_of(b))} V{f(y - 3)}", 0.9, 0.3))
    s.text(x_of(500), YB + 30, "BP", "jn-tick", "middle", t=0.95)
    s.text(x_of(830), YB + 34, "RP", "jn-tick", "middle", t=0.95)
    s.port("t", x_of(740), 26, "t")
    s.port("r", X1, YT + ph * 0.5, "r")
    s.port("b", x_of(660), YB + 40, "b")
    s.h = YB + 44
    return s


def apogee_stage(fe, am, w: float, ph: float) -> Stage:
    from matplotlib import pyplot as plt
    from scipy.ndimage import gaussian_filter

    s = Stage("apogee", "APOGEE DR19", w, ph + 58, 1.0)
    X0, X1, YT, YB = 0.0, w, 40.0, 40.0 + ph
    FE, AM = (-1.0, 0.5), (-0.08, 0.36)
    H, xe, ye = np.histogram2d(fe, am, bins=[64, 46], range=[FE, AM])
    D = gaussian_filter(H.T, 1.15)
    D = D / D.max()
    xc, yc = 0.5 * (xe[1:] + xe[:-1]), 0.5 * (ye[1:] + ye[:-1])
    levels = [0.02, 0.05, 0.1, 0.17, 0.26, 0.37, 0.5, 0.65, 0.82]
    fig = plt.figure()
    cs = plt.contour(xc, yc, D, levels=levels)
    paths = cs.get_paths()
    plt.close(fig)

    def to_xy(px, py):
        return X0 + (px - FE[0]) / (FE[1] - FE[0]) * (X1 - X0), YB - (py - AM[0]) / (AM[1] - AM[0]) * (YB - YT)

    # topographic hairlines; the alpha-rich ridge is the upper one, in the accent
    SPLIT = lambda px: 0.145 - 0.115 * (px + 0.3)  # the valley between the two sequences
    for i, p in enumerate(paths):
        hi, lo = [], []
        for seg in p.to_polygons(closed_only=False):
            if len(seg) < 3:
                continue
            xy = [to_xy(*v) for v in seg[:: 2 if len(seg) > 30 else 1]]
            cx, cy = seg[:, 0].mean(), seg[:, 1].mean()
            (hi if cy > SPLIT(cx) else lo).append(poly(xy))
        o = 0.32 + 0.68 * i / (len(paths) - 1)
        if lo:
            s.body.append(pop(f'<path class="jn-iso" style="--o:{o:.2f}" d="{"".join(lo)}"/>', 1.1 + 0.05 * i))
        if hi:
            s.body.append(pop(f'<path class="jn-iso jn-iso-hi" style="--o:{max(o + 0.35, 0.75):.2f}" d="{"".join(hi)}"/>', 1.1 + 0.05 * i))
    s.body.append(draw("jn-g", f"M{f(X0)} {f(YT)} V{f(YB)} H{f(X1)}", 1.05, 0.3))
    s.text(X1, YT + 12, "[α/M]", "jn-tick", "end", t=1.1)
    s.text(X1, YB + 16, "[Fe/H]", "jn-tick", "end", t=1.1)
    s.port("t", w - 20, 26, "t")
    s.port("r", X1, YT + ph * 0.45, "r")
    s.h = YB + 22
    return s


def flow_samples(n: int) -> np.ndarray:
    """Draws from a two-dimensional Gaussian pushed through five coupling layers.

    Each layer changes one coordinate by an invertible function of itself, conditioned on the
    other, as a spline coupling layer does. The target (a correlated, two-lobed density) is
    written by hand: this draws the mechanism of the network, not its output."""
    z = np.random.default_rng(11).normal(size=(n, 2))
    z = z[np.hypot(*z.T) < 2.6]
    x, y = z[:, 0].copy(), z[:, 1].copy()
    out = [np.c_[x, y]]
    y = y + 0.25 * np.tanh(x)
    out.append(np.c_[x, y])
    x = x + 0.45 * np.sin(1.1 * y)
    out.append(np.c_[x, y])
    y = 0.42 * y + 1.0 * np.tanh(2.6 * y)
    out.append(np.c_[x, y])
    x = x * (0.5 + 0.12 * np.tanh(y)) - 0.8 * np.tanh(1.5 * y)
    out.append(np.c_[x, y])
    y = 1.0 * y - 0.16 * x + 0.25
    out.append(np.c_[x, y])
    return np.stack(out, 1)


def janus_stage(scale: float, top: bool, n: int, ny: int, bx: float, b1: float, b3: float) -> Stage:
    W0, H0 = 514.0, 404.0
    s = Stage("janus", "JANUS", W0 * scale, H0 * scale, 1.2)
    k = scale
    FX1, FY0, FY1 = 486.0, 54.0, 404.0  # the front plate; seven more behind it
    g: list[str] = []
    back = "".join(
        f'<rect class="jn-plate-back" x="{f(4 * i)}" y="{f(FY0 - 3 * i)}" width="{f(FX1)}" height="{f(FY1 - FY0)}" rx="3"/>'
        for i in range(7, 0, -1)
    )
    g.append(pop(back, 1.2))
    g.append(pop(f'<rect class="jn-plate" x="0" y="{f(FY0)}" width="{f(FX1)}" height="{f(FY1 - FY0)}" rx="3"/>', 1.25))
    cy = (FY0 + FY1) / 2 + 8
    # the trunk: four dense layers, all to all, between the inputs and the flows
    cols = [26.0, 54.0, 82.0, 110.0]
    ys = [cy + (i - (ny - 1) / 2) * 250 / (ny - 1) for i in range(ny)]
    edges = "".join(f"M{f(a)} {f(y0)}L{f(b)} {f(y1)}" for a, b in pairwise(cols) for y0 in ys for y1 in ys)
    fan = "".join(f"M{f(HALF)} {f(cy)}L{f(cols[0])} {f(y)}" for y in ys)
    g.append(pop(f'<path class="jn-mesh" d="{edges}{fan}"/>', 1.3))
    dots = "".join(f'<circle cx="{f(x)}" cy="{f(y)}" r="1.5"/>' for x in cols for y in ys)
    g.append(pop(f'<g class="jn-dots">{dots}</g>', 1.35))
    # the flow: six planes in oblique view, base Gaussian first, each pair a coupling layer
    P = flow_samples(n)
    n, m, _ = P.shape
    PX0, PW, PG, PH, SK = 160.0, 56.0, 52.0, 262.0, 34.0
    upper = P[:, 2, 1] > 0  # the draws that end in the upper mode

    def plane_xy(j: int, u, v):
        return PX0 + PG * j + u * PW, cy + 10 + (0.5 - v) * PH - u * SK

    # one scale for every plane, so the eye sees the density change shape
    uv = np.stack((0.5 + P[..., 0] / 5.6, 0.5 + P[..., 1] / 5.8), -1)
    # the conditioning: every plane hears the trunk through one bus along the top
    BY = FY0 + 16
    drops = "".join(f"M{f(plane_xy(j, 0.5, 1)[0])} {f(BY)} V{f(plane_xy(j, 0.5, 1)[1])}" for j in range(1, m))
    bus = f'M{f(cols[-1])} {f(ys[0])} V{f(BY)} H{f(plane_xy(m - 1, 0.5, 1)[0])} {drops}'
    g.append(draw("jn-bus", bus, 1.4, 0.5))
    for j in range(m):
        a = [plane_xy(j, u, v) for u, v in ((0, 0), (1, 0), (1, 1), (0, 1))]
        g.append(pop(f'<path class="jn-pane{" jn-pane-end" if j in (0, m - 1) else ""}" d="{poly(a)} Z"/>', 1.4 + 0.08 * j))
    KNEE = m - 3  # the accent takes over where the upper mode has separated
    idx = np.arange(len(P))
    white = "".join(poly([plane_xy(j, *uv[i, j]) for j in range(m if not upper[i] else KNEE + 1)]) for i in idx)
    brass = "".join(poly([plane_xy(j, *uv[i, j]) for j in range(KNEE, m)]) for i in idx[upper])
    g.append(pop(f'<path class="jn-fib" d="{white}"/>', 1.6))
    g.append(pop(f'<path class="jn-fib jn-fib-hi" d="{brass}"/>', 1.8))
    for j in range(m):
        hi = upper & (j > KNEE)
        for mask, cls in ((~hi, "jn-pt"), (hi, "jn-pt jn-pt-hi")):
            d = "".join(f"M{f(plane_xy(j, *uv[i, j])[0])} {f(plane_xy(j, *uv[i, j])[1])}h.01" for i in idx[mask])
            if d:
                g.append(pop(f'<path class="{cls}" d="{d}"/>', 1.5 + 0.1 * j))
    zx, zy = plane_xy(0, 0.5, 0)
    tx, ty = plane_xy(m - 1, 0.5, 0)
    g.append(pop(f'<text class="jn-tick" x="{f(zx)}" y="{f(zy + 20)}" text-anchor="middle" style="font-style:italic">z</text>', 1.5))
    g.append(pop(f'<text class="jn-tick" x="{f(tx)}" y="{f(ty + 20)}" text-anchor="middle" style="font-style:italic">θ</text>', 2.0))
    ox = plane_xy(m - 1, 1, 0.5)
    g.append(draw("jn-g2", f"M{f(ox[0] + 4)} {f(cy)} H{f(FX1 + 28 - HALF)}", 2.0, 0.15))
    s.body.append(f'<g transform="scale({k:.3f})">' + "".join(g) + "</g>")
    s.port("l", 0, cy * k, "l")
    s.port("r", (FX1 + 28) * k, cy * k, "r")
    s.port("t", cols[-1] * k + 60, 26, "t")
    if top:
        s.leads["t"] = pop(f'<path class="jn-g2" d="M{f(cols[-1] * k + 60)} {f(26 + HALF)} V{f(FY0 * k)}"/>', 1.25)
    s.port("l2", 0, (FY1 - 34) * k, "l")
    s.port("b", bx * k, FY1 * k, "b")
    s.port("b1", b1 * k, FY1 * k, "b")
    s.port("b3", b3 * k, FY1 * k, "b")
    return s


def bump(xs, m, w, skew=0.0):
    z = (xs - m) / w
    return np.exp(-0.5 * z**2) * (1 + np.vectorize(math.erf)(skew * z / math.sqrt(2)))


def labels_stage(w: float, px: float) -> Stage:
    s = Stage("labels", "Labels", w, 232, 2.0)
    L0, L1 = 86.0, w - 8
    rows = [
        ('T<tspan class="jn-sub" dy="3">eff</tspan>', "Teff", bump),
        ('log <tspan style="font-style:italic">g</tspan>', "log g", bump),
        ("[M/H]", "[M/H]", bump),
        ("[α/M]", "[α/M]", bump),
    ]
    xs = np.linspace(-1, 1, 49)
    shapes = [
        bump(xs, 0.0, 0.17, 0.8),
        bump(xs, 0.08, 0.22, -2.0),
        0.8 * bump(xs, -0.2, 0.18) + 0.45 * bump(xs, 0.26, 0.14),
        0.55 * bump(xs, -0.42, 0.13) + 0.9 * bump(xs, 0.28, 0.17),
    ]
    for i, ((lab, plain, _), p) in enumerate(zip(rows, shapes)):
        y = 70 + 40 * i
        s.texts.append((0, y, plain, "jn-lab", "start"))
        s.body.append(pop(f'<text class="jn-lab" x="0" y="{f(y)}">{lab}</text>', 2.1 + 0.08 * i))
        p = p / p.max()
        pts = [(L0 + (L1 - L0) * (x + 1) / 2, y + 4 - 30 * v) for x, v in zip(xs, p)]
        hatch = "".join(f"M{f(a)} {f(b + 2)}V{f(y + 4)}" for a, b in pts)
        s.body.append(pop(f'<path class="jn-hatch" d="{hatch}"/>', 2.2 + 0.08 * i))
        s.body.append(draw("jn-g", f"M{f(L0)} {f(y + 4)} H{f(L1)}", 2.1, 0.2))
        s.body.append(draw("jn-post", smooth(pts), 2.15 + 0.08 * i, 0.3))
    # P(H), the probability that the four atmospheric parameters are jointly off
    y = 226.0
    s.text(0, y, "P(H)", "jn-lab", t=2.5)
    s.body.append(draw("jn-g2", f"M{f(L0)} {f(y - 4)} H{f(L1)} M{f(L0)} {f(y - 8)} v8 M{f(L1)} {f(y - 8)} v8", 2.5, 0.2))
    s.body.append(pop(f'<rect class="jn-ph" x="{f(L0)}" y="{f(y - 7)}" width="{f((L1 - L0) * 0.09)}" height="6"/>', 2.6))
    s.port("l", 0, 26, "l")
    s.port("t", px, 26, "t")
    s.body.append(draw("jn-g", f"M0 240 H{f(w)}", 2.5, 0.3))
    s.port("b", px, 240, "b")
    s.h = 244
    return s


def catalogue_stage(w: float, rows: int, px: float) -> Stage:
    H = 58 + rows * 13.0 + 8
    s = Stage("catalogue", "Catalogue", w, H + 4, 2.5)
    heads = [('T<tspan class="jn-sub" dy="3">eff</tspan>', "Teff"), ("[M/H]", "[M/H]"), ("[α/M]", "[α/M]"), (None, "nu"), ("P(H)", "P(H)")]
    cw = w / len(heads)
    s.body.append(draw("jn-g", f"M0 58 H{f(w)} M0 {f(H)} H{f(w)}", 2.5, 0.35))
    for j, (lab, plain) in enumerate(heads):
        x = cw * j
        if lab is None:
            comb = " ".join(f"M{f(x + 2 + 2.75 * q)} 50 v-{f(1.5 + 9 * math.exp(-(((q - 4) / 1.9) ** 2)))}" for q in range(9))
            s.body.append(draw("jn-g2", comb, 2.6, 0.2))
        else:
            s.texts.append((x, 50, plain, "jn-lab", "start"))
            s.body.append(pop(f'<text class="jn-lab" x="{f(x)}" y="50">{lab}</text>', 2.6))
    rng = random.Random(4)
    flagged = {4, 11, 16}
    cells, marks = [], []
    for r in range(rows):
        y = 70 + 13.0 * r
        row = "".join(f"M{f(cw * j)} {f(y)}h{f((0.45 + 0.4 * rng.random()) * (cw - 12))}" for j in range(4))
        if r in flagged:
            marks.append(f'<path class="jn-cell jn-cell-off" d="{row}"/><rect class="jn-ph" x="{f(cw * 4)}" y="{f(y - 3)}" width="6" height="6"/>')
        else:
            cells.append(row)
            marks.append(f'<rect class="jn-ph-o" x="{f(cw * 4)}" y="{f(y - 3)}" width="6" height="6"/>')
    s.body.append(draw("jn-cell", "".join(cells), 2.7, 0.5))
    s.body.append(pop("".join(marks), 2.8))
    s.port("t", px, 26, "t")
    return s


def hpc_stage(w: float, wide: bool, px: float) -> Stage:
    s = Stage("hpc", "Supercomputers", w, 170, 2.2)
    P = 15.0 if wide else 6.0
    Q = P * 0.72
    machines = [
        ("Deucalion", "DR3", [(1632, True), (500, False), (33, True)], 9),
        ("MareNostrum 5", "DR4", [(6408, True), (1120, True)], 23),
    ]
    base = 40 + 6 * P
    x0 = 0.0
    for k, (name, rel, parts, ncol) in enumerate(machines):
        n = sum(max(1, round(a / 64)) for a, _ in parts)
        nrow = math.ceil(n / ncol)
        y0 = (base - nrow * P) if wide else (36.0 if k == 0 else 36 + 4 * P + 34)
        i, sq = 0, []
        for nodes, used in parts:
            for _ in range(max(1, round(nodes / 64))):
                r, c = divmod(i, ncol)
                sq.append(f'<rect class="{"jn-node" if used else "jn-node-o"}" x="{f(x0 + c * P)}" y="{f(y0 + r * P)}" width="{f(Q)}" height="{f(Q)}"/>')
                i += 1
        s.body.append(pop("".join(sq), 2.3 + 0.15 * k))
        yt = (base + 14) if wide else y0 + nrow * P + 14
        s.text(x0, yt, name, "jn-lab", t=2.35 + 0.15 * k)
        s.text(x0 + text_w(name, "jn-lab") + 8, yt, rel, "jn-tick", t=2.35 + 0.15 * k)
        s.h = max(s.h, yt + 6) if not wide else yt + 6
        if wide:
            x0 += ncol * P + 18
    s.port("t", px, 26, "t")
    return s


# ------------------------------------------------------------------ layout and connectors


def edge_point(st_xy, stage: Stage, name: str):
    ox, oy = st_xy
    x, y, side = stage.ports[name]
    nx, ny = NORMAL[side]
    return (ox + x + nx * HALF, oy + y + ny * HALF), (nx, ny), (ox + x, oy + y)


def connector(a, b, kind: str, t: float, dur: float, prefix: str, masks: list, out: list, checks: list):
    (pa, na, ca), (pb, nb, cb) = a, b
    dist = math.hypot(pb[0] - pa[0], pb[1] - pa[1])
    k = max(14.0, min(70.0, 0.42 * dist))
    c1 = (pa[0] + na[0] * k, pa[1] + na[1] * k)
    c2 = (pb[0] + nb[0] * k, pb[1] + nb[1] * k)
    d = f"M{f(pa[0])} {f(pa[1])} C{f(c1[0])} {f(c1[1])} {f(c2[0])} {f(c2[1])} {f(pb[0])} {f(pb[1])}"
    checks.append((pa, ca, pb, cb))
    if kind == "flow":
        m = f"{prefix}m{len(masks) + 1}"
        masks.append(f'<mask id="{m}" maskUnits="userSpaceOnUse"><path class="jn-mask b-draw" pathLength="1" {timing(t, dur)} d="{d}"/></mask>')
        out.append(f'<path class="jn-link" mask="url(#{m})" d="{d}"/>')
    else:
        out.append(draw("jn-wire", d, t, dur))


def on_square_edge(p, c) -> bool:
    dx, dy = abs(p[0] - c[0]), abs(p[1] - c[1])
    tol = 0.06
    return (abs(dx - HALF) < tol and dy <= HALF + tol) or (abs(dy - HALF) < tol and dx <= HALF + tol)


def build(layout: str, stages: dict[str, Stage], aria: str) -> str:
    if layout == "wide":
        W, H = 1280, 646
        pos = {
            "gaia": (28, 12), "xp": (28, 160), "apogee": (28, 462),
            "janus": (430, 12), "hpc": (430, 462),
            "labels": (982, 12), "catalogue": (982, 306),
        }
        links = [
            ("gaia", "b", "xp", "t", "flow"), ("xp", "r", "janus", "l", "flow"), ("apogee", "r", "janus", "l2", "flow"),
            ("janus", "r", "labels", "l", "flow"), ("labels", "b", "catalogue", "t", "flow"), ("hpc", "t", "janus", "b3", "wire"),
        ]
    else:
        W = 360
        pos = {
            "gaia": (8, 8), "xp": (8, 156), "janus": (8, 420),
            "apogee": (8, 706), "hpc": (187, 706), "labels": (8, 900), "catalogue": (8, 1168),
        }
        H = pos["catalogue"][1] + stages["catalogue"].h + 8
        links = [
            ("gaia", "b", "xp", "t", "flow"), ("xp", "b", "janus", "t", "flow"), ("apogee", "t", "janus", "b1", "flow"),
            ("janus", "b", "labels", "t", "flow"), ("labels", "b", "catalogue", "t", "flow"), ("hpc", "t", "janus", "b3", "wire"),
        ]
    for k, (x, y) in pos.items():
        st = stages[k]
        assert x >= 0 and x + st.w <= W and y + st.h <= H, f"{layout}: {k} outside the frame ({x + st.w}, {y + st.h})"
    used: dict[str, set[str]] = {k: set() for k in stages}
    for a, pa, b, pb, _ in links:
        used[a].add(pa)
        used[b].add(pb)
    prefix = "jw" if layout == "wide" else "jp"
    masks, wires, checks = [], [], []
    for a, pa, b, pb, kind in links:
        connector(edge_point(pos[a], stages[a], pa), edge_point(pos[b], stages[b], pb), kind, stages[a].t + 0.35, 0.35, prefix, masks, wires, checks)
    for pa, ca, pb, cb in checks:
        assert on_square_edge(pa, ca) and on_square_edge(pb, cb), f"{layout}: connector end off its port {pa} {ca} {pb} {cb}"
    body = [st.render(*pos[k], used[k]) for k, st in stages.items()]
    return (
        f'<svg class="jn-svg jn-{layout}" viewBox="0 0 {W} {f(H)}" xmlns="http://www.w3.org/2000/svg" role="group" '
        f'aria-label="{aria}">'
        + "<defs>" + "".join(masks) + "</defs>"
        + "".join(body)
        + '<g class="jn-thread" aria-hidden="true">' + "".join(wires) + "</g>"
        + "</svg>"
    )


# ------------------------------------------------------------------ main

APERTURE = (0.0, 0.0)


def make_webp(png: Path) -> None:
    from PIL import Image

    im = Image.open(png).convert("RGBA")
    box = im.split()[3].getbbox()
    im = im.crop(box)
    w = 400
    im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    GAIA_WEBP.parent.mkdir(parents=True, exist_ok=True)
    im.save(GAIA_WEBP, "WEBP", quality=88, method=6)
    # the aperture: the darkest pixels inside the gold rim on the tent wall, upper middle
    print(f"wrote {GAIA_WEBP.relative_to(ROOT)} {im.size}")


def main() -> None:
    global APERTURE
    ap = argparse.ArgumentParser()
    ap.add_argument("--gaia-render", type=Path)
    args = ap.parse_args()
    if args.gaia_render:
        make_webp(args.gaia_render)
    from PIL import Image

    img = Image.open(GAIA_WEBP)
    # the near telescope aperture in the cropped still (render at 20 degrees, 1200 x 800, see the docstring)
    APERTURE = (0.478, 0.262)
    lam, flux, _sid = load_spectrum()
    fe, am = load_apogee()
    wide = {
        "gaia": gaia_stage(*img.size, 364),
        "xp": xp_stage(lam, flux, 364, 196, "jw"),
        "apogee": apogee_stage(fe, am, 364, 112),
        "janus": janus_stage(1.0, False, 330, 15, 220, 60, 340),
        "labels": labels_stage(270, 108),
        "catalogue": catalogue_stage(270, 19, 108),
        "hpc": hpc_stage(514, True, 486),
    }
    phone = {
        "gaia": gaia_stage(*img.size, 344),
        "xp": xp_stage(lam, flux, 344, 150, "jp"),
        "apogee": apogee_stage(fe, am, 165, 100),
        "janus": janus_stage(0.669, True, 200, 11, 257, 217, 477),
        "labels": labels_stage(344, 172),
        "catalogue": catalogue_stage(344, 8, 172),
        "hpc": hpc_stage(165, False, 158),
    }
    aria = "{{ site.data.copy.research.janus_fig.aria | strip_html | escape }}"
    svg = (
        "{%- comment -%} Generated by figures/janus/build_janus.py; do not edit. {%- endcomment -%}\n"
        + build("wide", wide, aria)
        + "\n"
        + build("phone", phone, aria)
        + "\n"
    )
    OUT.write_text(svg)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(svg) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
