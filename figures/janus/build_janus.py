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
JANUS ensemble of conditional normalising flows, the labels with their spread and P(H), the
catalogue of TESS red giants, and the two machines it runs on.

Real data (filled, in the mark colour):
- the spectrum: Gaia DR3 5289554869898620416, the median-[M/H] red giant of the playground set
  (assets/data/playground/gaia_xp_mh.json, row 97; GaiaXPy calibrated flux on a 2 nm grid).
  The part blueward of 660 nm comes from BP, the part redward from RP (they overlap from 640 to
  680 nm). H alpha (656.28 nm) and the Ca II triplet (849.80, 854.21, 866.21 nm) are ticked at
  their air wavelengths.
- the alpha plane: [alpha/M] against [Fe/H] for the 9,242 APOGEE DR19 giants of the recorded
  Starfold run (assets/data/starfold/apogee_run.*), as a smoothed density in four levels.
- the machines: node counts of Deucalion and MareNostrum 5 to scale, one square for 64 nodes
  (sources in figures/hpc/build_hpc_figure.py).
Schematic (outline): the spacecraft render (proportions after ESA, not an engineering model),
the flow densities, the label posteriors, P(H) and the table cells.

Every connector starts and ends on the outer edge of a square port; the script checks this.
"""

from __future__ import annotations

import argparse
import json
import math
import random
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


CHAR = {"jn-title": 0.50 * 17, "jn-lab": 0.60 * 12.5, "jn-tick": 0.60 * 12}


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


def gaia_stage(img_w: int, img_h: int) -> Stage:
    s = Stage("gaia", "Gaia", 190, 170, 0.2, italic=True)
    W = 178.0
    H = W * img_h / img_w
    ix, iy = 6.0, 50.0
    s.body.append(
        pop(
            f'<image class="jn-render" href="{{{{ \'/assets/img/figures/janus-gaia.webp\' | relative_url }}}}" '
            f'x="{f(ix)}" y="{f(iy)}" width="{f(W)}" height="{f(H)}" preserveAspectRatio="xMidYMid meet"/>',
            0.2,
        )
    )
    # the starlight: from a star into the first telescope aperture (located in the render)
    ax, ay = ix + APERTURE[0] * W, iy + APERTURE[1] * H
    sx, sy = 168.0, 40.0
    s.body.append(pop(f'<circle class="jn-star" cx="{f(sx)}" cy="{f(sy)}" r="2.6"/>', 0.25))
    s.body.append(pop(f'<path class="jn-spike" d="M{f(sx - 8)} {f(sy)} H{f(sx + 8)} M{f(sx)} {f(sy - 8)} V{f(sy + 8)}"/>', 0.25))
    s.body.append(draw("jn-light", f"M{f(sx - 4)} {f(sy + 3)} L{f(ax + 3)} {f(ay - 2)}", 0.4, 0.35))
    s.port("r", 190, iy + H * 0.62, "r")
    s.port("b", 95, iy + H + 6, "b")
    s.h = iy + H + 10
    return s


def xp_stage(lam, flux) -> Stage:
    s = Stage("xp", "XP spectrum", 230, 176, 0.6)
    X0, X1, YT, YB = 14.0, 222.0, 54.0, 138.0

    def x_of(nm):
        return X0 + (nm - 360) / (990 - 360) * (X1 - X0)

    def y_of(v):
        return YB - v * (YB - YT)

    pts = [(x_of(l), y_of(v)) for l, v in zip(lam, flux)]
    s.body.append(draw("jn-g", f"M{f(X0)} {f(YT - 4)} V{f(YB)} H{f(X1)} V{f(YT - 4)}", 0.45, 0.3))
    split = int(np.searchsorted(lam, 660))
    bp, rp = pts[: split + 1], pts[split:]
    for part, cls in ((bp, "jn-fill-bp"), (rp, "jn-fill-rp")):
        thin = part[::3] + [part[-1]]
        area = poly(thin) + f" L{f(part[-1][0])} {f(YB)} L{f(part[0][0])} {f(YB)} Z"
        s.body.append(pop(f'<path class="{cls}" d="{area}"/>', 0.75))
    s.body.append(draw("jn-spec", smooth(pts), 0.6, 0.7))
    s.body.append(pop(f'<path class="jn-gd" d="M{f(x_of(660))} {f(YT - 4)} V{f(YB)}"/>', 0.8))
    # the two photometers: brackets under the axis
    for (a, b, y, lab) in ((360, 680, 147, "BP"), (640, 990, 155, "RP")):
        s.body.append(draw("jn-g2", f"M{f(x_of(a))} {f(y - 3)} V{f(y)} H{f(x_of(b))} V{f(y - 3)}", 0.85, 0.3))
    s.text(x_of(500), 166, "BP", "jn-tick", "middle", t=0.9)
    s.text(x_of(830), 166, "RP", "jn-tick", "middle", t=0.9)
    # real lines at their wavelengths
    li = np.interp

    def tick(nm, top):
        yv = y_of(float(li(nm, lam, flux)))
        return f"M{f(x_of(nm))} {f(yv - 5)} V{f(top)}"

    s.body.append(draw("jn-line", tick(656.28, 40), 1.0, 0.2))
    s.body.append(draw("jn-line", " ".join(tick(nm, 40) for nm in (849.80, 854.21, 866.21)), 1.0, 0.2))
    s.text(x_of(656.28), 36, "Hα", "jn-tick", "middle", t=1.0)
    s.text(x_of(856.0), 36, "Ca II", "jn-tick", "middle", t=1.0)
    s.port("l", X0, 96, "l")
    s.port("r", X1, 96, "r")
    s.port("t", 142, 26, "t")
    s.port("b", x_of(660), 172, "b")
    s.leads["b"] = pop(f'<path class="jn-gd" d="M{f(x_of(660))} {f(YB)} V{f(172 - HALF)}"/>', 0.9)
    return s


def apogee_stage(fe, am) -> Stage:
    from matplotlib import pyplot as plt
    from scipy.ndimage import gaussian_filter

    s = Stage("apogee", "APOGEE DR19", 150, 132, 1.0)
    X0, X1, YT, YB = 6.0, 146.0, 38.0, 112.0
    FE, AM = (-1.0, 0.5), (-0.08, 0.36)
    H, xe, ye = np.histogram2d(fe, am, bins=[60, 44], range=[FE, AM])
    D = gaussian_filter(H.T, 1.0)
    D = D / D.max()
    xc = 0.5 * (xe[1:] + xe[:-1])
    yc = 0.5 * (ye[1:] + ye[:-1])
    levels = [0.025, 0.09, 0.25, 0.55, 1.01]
    fig = plt.figure()
    cs = plt.contourf(xc, yc, D, levels=levels)
    paths = cs.get_paths()
    plt.close(fig)

    def to_xy(px, py):
        return X0 + (px - FE[0]) / (FE[1] - FE[0]) * (X1 - X0), YB - (py - AM[0]) / (AM[1] - AM[0]) * (YB - YT)

    s.body.append(draw("jn-g", f"M{f(X0)} {f(YT - 6)} V{f(YB)} H{f(X1 + 2)}", 1.05, 0.3))
    for i, p in enumerate(paths):
        d = []
        for (vx, vy), code in zip(p.vertices, p.codes):
            x, y = to_xy(vx, vy)
            if code == 1:
                d.append(f"M{f(x)} {f(y)}")
            elif code == 79:
                d.append("Z")
            else:
                d.append(f"L{f(x)} {f(y)}")
        s.body.append(pop(f'<path class="jn-dens jn-dens-{i}" fill-rule="evenodd" d="{"".join(d)}"/>', 1.1 + 0.08 * i))
    s.text(X1, 50, "[α/M]", "jn-tick", "end", t=1.1)
    s.text(X1, 128, "[Fe/H]", "jn-tick", "end", t=1.1)
    s.port("t", 128, 26, "t")
    s.port("r", 150, 75, "r")
    return s


def gauss(y, m, w):
    return np.exp(-0.5 * ((y - m) / w) ** 2)


def janus_stage() -> Stage:
    s = Stage("janus", "JANUS", 290, 176, 1.2)
    PW, PY0, PY1 = 262.0, 58.0, 170.0  # the front plate
    # eight networks: seven plates behind the front one
    back = []
    for k in range(7, 0, -1):
        dx, dy = 4 * k, -4 * k
        back.append(f'<rect class="jn-plate jn-plate-back" x="{f(dx)}" y="{f(PY0 + dy)}" width="{f(PW)}" height="{f(PY1 - PY0)}" rx="3"/>')
    s.body.append(pop("".join(back), 1.2))
    s.body.append(pop(f'<rect class="jn-plate" x="0" y="{f(PY0)}" width="{f(PW)}" height="{f(PY1 - PY0)}" rx="3"/>', 1.25))
    cy, A = 114.0, 38.0
    ys = np.linspace(-1, 1, 41)
    dens = [
        gauss(ys, 0, 0.32),
        0.75 * gauss(ys, -0.15, 0.30) + 0.35 * gauss(ys, 0.35, 0.22),
        0.6 * gauss(ys, -0.32, 0.2) + 0.55 * gauss(ys, 0.3, 0.22),
        0.65 * gauss(ys, -0.45, 0.13) + 0.8 * gauss(ys, 0.28, 0.18),
    ]
    axes = [18.0, 86.0, 154.0, 222.0]  # density axes; transforms between them
    blocks = [52.0, 120.0, 188.0]
    for i, (ax, p) in enumerate(zip(axes, dens)):
        p = p / p.max()
        pts = [(ax + 26 * v, cy + A * y) for y, v in zip(ys, p)]
        s.body.append(draw("jn-g", f"M{f(ax)} {f(cy - A - 4)} V{f(cy + A + 4)}", 1.3 + 0.12 * i, 0.2))
        cls = "jn-dens-o" if i < 3 else "jn-dens-out"
        s.body.append(draw(cls, smooth(pts), 1.35 + 0.15 * i, 0.35))
    for i, bx in enumerate(blocks):
        s.body.append(pop(f'<rect class="jn-block" x="{f(bx)}" y="{f(cy - 34)}" width="14" height="68" rx="2"/>', 1.4 + 0.15 * i))
        # invertible: a forward and a backward chevron on each transform
        s.body.append(pop(f'<path class="jn-chev" d="M{f(bx + 4)} {f(cy - 4)} l3 3 l3 -3 M{f(bx + 4)} {f(cy + 4)} l3 -3 l3 3" transform="rotate(-90 {f(bx + 7)} {f(cy)})"/>', 1.45 + 0.15 * i))
    # the spectrum conditions every transform: a bus along the top of the front plate
    BY = 70.0
    bus = f"M{f(blocks[0] + 7)} {f(BY)} H{f(blocks[-1] + 7)} " + " ".join(f"M{f(bx + 7)} {f(BY)} V{f(cy - 34)}" for bx in blocks)
    s.body.append(draw("jn-bus", bus, 1.3, 0.4))
    s.text(axes[0] + 2, PY1 - 6, "z", "jn-tick", extra=' style="font-style:italic"', t=1.5)
    s.text(axes[-1] + 2, PY1 - 6, "θ", "jn-tick", extra=' style="font-style:italic"', t=1.9)
    # ports: the spectrum enters the bus from the left (wide) or from the rule above (phone)
    s.port("l", 0, BY, "l")
    s.port("t", 150, 26, "t")
    s.leads = {
        "l": draw("jn-bus", f"M{f(HALF)} {f(BY)} H{f(blocks[0] + 7)}", 1.25, 0.15),
        "t": draw("jn-bus", f"M150 {f(26 + HALF)} V{f(BY)} M{f(blocks[0] + 7)} {f(BY)} H150", 1.25, 0.2),
    }
    s.port("r", PW + 28, cy, "r")
    s.leads["r"] = draw("jn-bus", f"M{f(PW - 8)} {f(cy)} H{f(PW + 28 - HALF)}", 2.0, 0.15)
    s.port("b1", 60, PY1, "b")
    s.port("b", 127, PY1, "b")
    s.port("b3", 210, PY1, "b")
    return s


def labels_stage() -> Stage:
    s = Stage("labels", "Labels", 170, 172, 2.0)
    s.body.append(draw("jn-g", "M0 34 V166 H170 V34", 2.0, 0.3))
    rows = [
        ("T<tspan class=\"jn-sub\" dy=\"3\">eff</tspan>", 0.0, 0.16, 0.8, "Teff"),
        ("log <tspan style=\"font-style:italic\">g</tspan>", 0.05, 0.22, -2.0, "log g"),
        ("[M/H]", -0.04, 0.18, 1.6, "[M/H]"),
        ("[α/M]", 0.02, 0.13, -1.2, "[α/M]"),
    ]
    xs = np.linspace(-1, 1, 33)
    for i, (lab, m, w, skew, plain) in enumerate(rows):
        y = 58 + 26 * i
        s.texts.append((12, y, plain, "jn-lab", "start"))
        s.body.append(pop(f'<text class="jn-lab" x="12" y="{f(y)}">{lab}</text>', 2.1 + 0.08 * i))
        # a skew-normal bump: a posterior with its spread (schematic)
        z = (xs - m) / w
        p = np.exp(-0.5 * z**2) * (1 + np.vectorize(math.erf)(skew * z / math.sqrt(2)))
        p = p / p.max()
        pts = [(116 + 44 * x, y + 2 - 15 * v) for x, v in zip(xs, p)]
        s.body.append(draw("jn-g", f"M72 {f(y + 2)} H160", 2.1, 0.2))
        s.body.append(draw("jn-post", smooth(pts), 2.15 + 0.08 * i, 0.3))
    # P(H): the probability that the four parameters are jointly off, on a 0 to 1 track
    y = 160.0
    s.text(12, y - 2, "P(H)", "jn-lab", t=2.5)
    s.body.append(draw("jn-g2", f"M72 {f(y - 6)} H160 M72 {f(y - 9)} v6 M160 {f(y - 9)} v6", 2.5, 0.2))
    s.body.append(pop(f'<rect class="jn-ph" x="72" y="{f(y - 8.5)}" width="11" height="5"/>', 2.6))
    s.port("l", 0, 104, "l")
    s.port("r", 170, 104, "r")
    s.port("t", 67, 26, "t")
    s.port("b", 67, 166, "b")
    return s


def catalogue_stage() -> Stage:
    s = Stage("catalogue", "Catalogue", 200, 166, 2.5)
    X0, X1, Y0, Y1 = 0.0, 200.0, 34.0, 162.0
    cols = [("T<tspan class=\"jn-sub\" dy=\"3\">eff</tspan>", "Teff", 40), ("[M/H]", "[M/H]", 44), ("[α/M]", "[α/M]", 44), (None, "nu", 30), ("P(H)", "P(H)", 42)]
    s.body.append(draw("jn-g", f"M{f(X0)} {f(Y0)} V{f(Y1)} H{f(X1)} V{f(Y0)} M{f(X0)} 58 H{f(X1)}", 2.5, 0.35))
    x = 0.0
    starts = []
    for lab, plain, w in cols:
        starts.append((x, w))
        if lab is None:
            # oscillation power excess: a comb under a Gaussian envelope (the seismic column)
            cx = x + w / 2
            comb = " ".join(f"M{f(cx - 11 + 2.75 * k)} 50 v-{f(1.5 + 9 * math.exp(-(((k - 4) / 1.9) ** 2)))}" for k in range(9))
            s.body.append(draw("jn-g2", comb, 2.6, 0.2))
        else:
            s.texts.append((x + 6, 50, plain, "jn-lab", "start"))
            s.body.append(pop(f'<text class="jn-lab" x="{f(x + 6)}" y="50">{lab}</text>', 2.6))
        x += w
    rng = random.Random(4)
    cells, flagged = [], []
    for r in range(8):
        y = 72 + 12.5 * r
        bad = r == 5
        row = []
        for j, (cx, w) in enumerate(starts[:-1]):
            L = (0.45 + 0.4 * rng.random()) * (w - 12)
            row.append(f"M{f(cx + 6)} {f(y)} h{f(L)}")
        sq_x = starts[-1][0] + 6
        ph = f'<rect class="{"jn-ph" if bad else "jn-ph-o"}" x="{f(sq_x)}" y="{f(y - 3)}" width="6" height="6"/>'
        (flagged if bad else cells).append((" ".join(row), ph))
    s.body.append(draw("jn-cell", " ".join(c for c, _ in cells), 2.7, 0.5))
    s.body.append(pop("".join(p for _, p in cells), 2.8))
    for c, p in flagged:
        s.body.append(pop(f'<g class="jn-flag"><path class="jn-cell" d="{c}"/>{p}</g>', 2.85))
    s.port("l", 0, 104, "l")
    s.port("t", 100, 26, "t")
    return s


def hpc_stage(wide: bool) -> Stage:
    s = Stage("hpc", "Supercomputers", 262 if wide else 180, 104 if wide else 152, 2.2)
    SQ, P = 4.2, 5.5
    machines = [
        ("Deucalion", "DR3", [(1632, True), (500, False), (33, True)], 6, 36.0),
        ("MareNostrum 5", "DR4", [(6408, True), (1120, True)], 10, 82.0),
    ]
    if wide:  # side by side, same square size, so the areas keep their ratio
        machines = [(m[0], m[1], m[2], 6, 36.0) for m in machines[:1]] + [(m[0], m[1], m[2], 16, 36.0) for m in machines[1:]]
    for k, (name, rel, parts, ncol, y0) in enumerate(machines):
        i, sq = 0, []
        x0 = 112.0 if wide and k else 0.0
        for nodes, used in parts:
            for _ in range(max(1, round(nodes / 64))):
                r, c = divmod(i, ncol)
                sq.append(f'<rect class="{"jn-node" if used else "jn-node-o"}" x="{f(x0 + c * P)}" y="{f(y0 + r * P)}" width="{SQ}" height="{SQ}"/>')
                i += 1
        s.body.append(pop("".join(sq), 2.3 + 0.15 * k))
        if wide:
            yb = y0 + 8 * P
            s.text(x0, yb + 14, name, "jn-lab", t=2.35 + 0.15 * k)
            s.text(x0 + text_w(name, "jn-lab") + 8, yb + 14, rel, "jn-tick", t=2.35 + 0.15 * k)
        else:
            tx = ncol * P + 8
            s.text(tx, y0 + 12, name, "jn-lab", t=2.35 + 0.15 * k)
            s.text(tx, y0 + 28, rel, "jn-tick", t=2.35 + 0.15 * k)
    s.port("t", 160, 26, "t")
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
        W, H = 1248, 352
        pos = {
            "gaia": (12, 8), "xp": (240, 8), "janus": (512, 8), "labels": (842, 8), "catalogue": (1040, 8),
            "apogee": (300, 216), "hpc": (640, 216),
        }
        links = [
            ("gaia", "r", "xp", "l", "flow"), ("xp", "r", "janus", "l", "flow"), ("apogee", "r", "janus", "b1", "flow"),
            ("janus", "r", "labels", "l", "flow"), ("labels", "r", "catalogue", "l", "flow"), ("hpc", "t", "janus", "b3", "wire"),
        ]
    else:
        W = 360
        pos = {
            "gaia": (85, 8), "xp": (65, 206), "janus": (35, 404),
            "apogee": (0, 610), "hpc": (176, 610), "labels": (95, 800), "catalogue": (80, 1004),
        }
        H = pos["catalogue"][1] + stages["catalogue"].h + 8
        links = [
            ("gaia", "b", "xp", "t", "flow"), ("xp", "b", "janus", "t", "flow"), ("apogee", "t", "janus", "b1", "flow"),
            ("janus", "b", "labels", "t", "flow"), ("labels", "b", "catalogue", "t", "flow"), ("hpc", "t", "janus", "b3", "wire"),
        ]
    for k, (x, y) in pos.items():
        st = stages[k]
        assert x >= 0 and x + st.w <= W and y + st.h <= H, f"{layout}: {k} outside the frame"
    used: dict[str, set[str]] = {k: set() for k in stages}
    for a, pa, b, pb, _ in links:
        used[a].add(pa)
        used[b].add(pb)
    prefix = "jw" if layout == "wide" else "jp"
    masks, wires, checks = [], [], []
    for a, pa, b, pb, kind in links:
        t = stages[a].t + 0.35
        connector(edge_point(pos[a], stages[a], pa), edge_point(pos[b], stages[b], pb), kind, t, 0.35, prefix, masks, wires, checks)
    for pa, ca, pb, cb in checks:
        assert on_square_edge(pa, ca) and on_square_edge(pb, cb), f"{layout}: connector end off its port {pa} {ca} {pb} {cb}"
    body = [st.render(*pos[k], used[k]) for k, st in stages.items()]
    return (
        f'<svg class="jn-svg jn-{layout}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="group" '
        f'aria-label="{aria}">'
        + "<defs>" + "".join(masks) + "</defs>"
        + '<g class="jn-thread" aria-hidden="true">' + "".join(wires) + "</g>"
        + "".join(body)
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
    stages = {
        "gaia": gaia_stage(*img.size),
        "xp": xp_stage(lam, flux),
        "apogee": apogee_stage(fe, am),
        "janus": janus_stage(),
        "labels": labels_stage(),
        "catalogue": catalogue_stage(),
        "hpc": hpc_stage(wide=True),
    }
    aria = "{{ site.data.copy.research.janus_fig.aria | strip_html | escape }}"
    svg = (
        "{%- comment -%} Generated by figures/janus/build_janus.py; do not edit. {%- endcomment -%}\n"
        + build("wide", stages, aria)
        + "\n"
        + build("phone", {**stages, "hpc": hpc_stage(wide=False)}, aria)
        + "\n"
    )
    OUT.write_text(svg)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(svg) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
