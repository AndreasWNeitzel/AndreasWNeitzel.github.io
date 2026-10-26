"""Build the HAYDNsim figures for /software/haydnsim/.

haydn-pipeline.svg   The six stages of HAYDNsim as pictograms, after the flowchart on the TASC10/KASC17
                     poster (Neitzel et al. 2026, doi:10.5281/zenodo.23263454) and slide 6 of the DFA
                     Week 2026 talk; the instrument strip is from slide 2 of that talk. Outline means
                     schematic.
haydn-crowding.svg   The share of each cluster's stars whose light is mostly from its neighbours, the
                     seven clusters printed on the poster. Filled bars mean data.

Everything these figures print is on the public poster or in the public talk. The pipeline's own
field, detector and noise results stay out until the paper is submitted.

Usage: python3 figures/haydnsim/build_haydn_figures.py
Needs latex and dvisvgm on the path for the typeset symbols (figures/texsvg.py).
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "figures"))
from texsvg import tex_glyphs  # noqa: E402

OUT = ROOT / "_includes/figures"

GOLDEN = math.pi * (3 - math.sqrt(5))

# 47 Tuc King-profile shape from Harris (2010), used only to draw the profile pictogram
R_CORE_ARCSEC = 0.36 * 60.0
CONCENTRATION = 2.07
R_TIDAL_ARCSEC = R_CORE_ARCSEC * 10 ** CONCENTRATION

# public per-cluster fractions of stars with SPR > 0.5, poster bar chart (per cent)
FRACTIONS = [("47 Tuc", 40), ("NGC 6752", 36), ("M54", 36), ("M22", 12), ("omega Cen", 11), ("NGC 6397", 7), ("M4", 3)]



def f(v: float) -> str:
    return f"{v:.1f}"


def draw(cls: str, d: str, t: float, dur: float = 0.5, style: str = "") -> str:
    return f'<path class="{cls} b-draw" style="--d:{t:.2f}s;--dur:{dur:.2f}s{style}" pathLength="1" d="{d}"/>'


def pop(inner: str, t: float) -> str:
    return f'<g class="b-pop" style="--d:{t:.2f}s">{inner}</g>'


def text(x: float, y: float, s: str, cls: str, t: float, anchor: str = "start", extra: str = "") -> str:
    return f'<text class="{cls} b-pop" style="--d:{t:.2f}s" x="{f(x)}" y="{f(y)}" text-anchor="{anchor}"{extra}>{s}</text>'


def tex(x: float, y: float, snippet: str, size: float, t: float, cls: str = "hy-tex-ink", anchor: str = "start") -> str:
    body, w = tex_glyphs(snippet, size)
    dx = {"start": 0.0, "middle": -w / 2, "end": -w}[anchor]
    return pop(f'<g class="{cls}" transform="translate({f(x + dx)} {f(y)})">{body}</g>', t)


def king(r: float) -> float:
    """King (1962) surface density shape, amplitude one."""
    a = 1.0 / math.sqrt(1.0 + (r / R_CORE_ARCSEC) ** 2)
    b = 1.0 / math.sqrt(1.0 + (R_TIDAL_ARCSEC / R_CORE_ARCSEC) ** 2)
    return (a - b) ** 2


def node(x: float, y: float, t: float, k: float = 6.0) -> str:
    return pop(f'<rect class="hy-node" x="{f(x - k / 2)}" y="{f(y - k / 2)}" width="{f(k)}" height="{f(k)}"/>', t)


def thread(d: str, t: float, cls: str = "ray flowray hy-thread") -> str:
    return pop(f'<path class="{cls}" d="{d}"/>', t)


def pic_archive(x: float, y: float, t: float) -> list[str]:
    """A survey cone, an HST tile and catalogue cards."""
    p = []
    p.append(draw("hy-pic", f"M{x + 10} {y + 70} L{x + 40} {y + 8} L{x + 70} {y + 70} Z", t, 0.3))
    for i, (dx, dy) in enumerate(((40, 34), (30, 50), (52, 52), (44, 62), (34, 62), (56, 40))):
        p.append(pop(f'<circle class="hy-dot" cx="{f(x + dx)}" cy="{f(y + dy)}" r="1.6"/>', t + 0.05 + 0.02 * i))
    p.append(draw("hy-pic", f"M{x + 86} {y + 14} h44 v44 h-44 Z", t + 0.1, 0.3))
    dots = "".join(f'<circle class="hy-dot" cx="{f(x + 90 + 7 * i)}" cy="{f(y + 18 + 7 * j)}" r="1.2"/>'
                   for i in range(6) for j in range(6) if (i * 7 + j * 3) % 5 < 3)
    p.append(pop(dots, t + 0.15))
    for i in range(3):
        p.append(draw("hy-pic", f"M{x + 92 - 6 * i} {y + 74 + 6 * i} h40 v10 h-40 Z", t + 0.2 + 0.04 * i, 0.25))
    return p


def pic_threshold(x: float, y: float, t: float) -> list[str]:
    """A magnitude ruler with the window where both surveys are complete."""
    p = [draw("hy-pic", f"M{x + 8} {y + 50} H{x + 140}", t, 0.3)]
    for i in range(9):
        xx = x + 8 + i * 16.5
        p.append(draw("hy-pic", f"M{f(xx)} {y + 50} v{8 if i % 2 == 0 else 5}", t + 0.02 * i, 0.15))
    p.append(pop(f'<rect class="hy-window" x="{f(x + 41)}" y="{y + 28}" width="{f(66)}" height="22"/>', t + 0.25))
    p.append(draw("hy-pic-strong", f"M{x + 41} {y + 28} v22 M{x + 107} {y + 28} v22", t + 0.3, 0.2))
    p.append(draw("hy-pic", f"M{x + 8} {y + 76} C{x + 40} {y + 76}, {x + 60} {y + 62}, {x + 74} {y + 62}", t + 0.3, 0.3))
    p.append(draw("hy-pic", f"M{x + 74} {y + 62} C{x + 90} {y + 62}, {x + 110} {y + 76}, {x + 140} {y + 76}", t + 0.35, 0.3))
    return p


def pic_king(x: float, y: float, t: float) -> list[str]:
    """A density curve falling with radius, the normalisation annulus shaded."""
    p = [draw("hy-pic", f"M{x + 12} {y + 10} V{y + 78} H{x + 140}", t, 0.3)]
    pts = []
    for i in range(41):
        u = i / 40
        r = 2.0 * (900.0 / 2.0) ** u
        v = king(r) / king(2.0)
        px = x + 16 + 118 * u
        py = y + 14 + 58 * (1 - (math.log10(v) + 3.4) / 3.4)
        pts.append((px, min(py, y + 76)))
    d = "M" + " L".join(f"{f(a)} {f(b)}" for a, b in pts)
    xa = x + 16 + 118 * (math.log10(50 / 2) / math.log10(450))
    xb = x + 16 + 118 * (math.log10(100 / 2) / math.log10(450))
    p.append(pop(f'<rect class="hy-window" x="{f(xa)}" y="{y + 12}" width="{f(xb - xa)}" height="{66}"/>', t + 0.1))
    p.append(draw("hy-pic-strong", d, t + 0.15, 0.5))
    return p


def pic_population(x: float, y: float, t: float) -> list[str]:
    """A luminosity-function histogram feeding a sampled field."""
    p = [draw("hy-pic", f"M{x + 8} {y + 10} V{y + 78} H{x + 70}", t, 0.3)]
    heights = (8, 12, 16, 22, 30, 40, 56)
    for i, h in enumerate(heights):
        p.append(draw("hy-pic", f"M{f(x + 12 + i * 8)} {y + 78} v-{h} h6 v{h}", t + 0.03 * i, 0.2))
    p.append(draw("hy-pic", f"M{x + 78} {y + 44} h18 M{x + 92} {y + 40} l4 4 l-4 4", t + 0.3, 0.2))
    cx, cy = x + 120, y + 44
    p.append(draw("hy-pic", f"M{f(cx + 30)} {f(cy)} A30 30 0 1 1 {f(cx - 30)} {f(cy)} A30 30 0 1 1 {f(cx + 30)} {f(cy)}", t + 0.35, 0.4))
    dots = []
    for i in range(70):
        r = 28 * ((i + 0.5) / 70) ** 1.6
        a = i * GOLDEN
        dots.append(f'<circle class="hy-dot" cx="{f(cx + r * math.cos(a))}" cy="{f(cy + r * math.sin(a))}" r="1.3"/>')
    p.append(pop("".join(dots), t + 0.45))
    return p


def pic_detector(x: float, y: float, t: float) -> list[str]:
    """A pixel grid with a star, its mask and a neighbour."""
    p = []
    g, n = 9, 8
    for i in range(n + 1):
        p.append(draw("hy-grid", f"M{f(x + 20 + i * g)} {y + 6} v{n * g}", t + 0.01 * i, 0.15))
        p.append(draw("hy-grid", f"M{x + 20} {f(y + 6 + i * g)} h{n * g}", t + 0.01 * i, 0.15))
    cx, cy = x + 20 + 4 * g, y + 6 + 4 * g
    for r, o in ((14, 0.12), (9, 0.3), (5, 0.7)):
        p.append(pop(f'<circle class="hy-psf" style="opacity:{o}" cx="{f(cx)}" cy="{f(cy)}" r="{r}"/>', t + 0.2))
    mask = f"M{f(cx - g)} {f(cy - 2 * g)} h{2 * g} v{g} h{g} v{2 * g} h-{g} v{g} h-{2 * g} v-{g} h-{g} v-{2 * g} h{g} Z"
    p.append(draw("hy-mask", mask, t + 0.3, 0.4))
    nx, ny = cx + 2.6 * g, cy - 1.8 * g
    for r, o in ((9, 0.12), (5, 0.4)):
        p.append(pop(f'<circle class="hy-psf" style="opacity:{o}" cx="{f(nx)}" cy="{f(ny)}" r="{r}"/>', t + 0.4))
    p.append(draw("hy-pic", f"M{x + 108} {y + 12} h30 M{x + 108} {y + 24} h30 M{x + 108} {y + 36} h18", t + 0.45, 0.2))
    return p


def pic_seismic(x: float, y: float, t: float) -> list[str]:
    """A power spectrum: a comb of peaks under an envelope."""
    p = [draw("hy-pic", f"M{x + 10} {y + 78} H{x + 140}", t, 0.3)]
    for i in range(11):
        xx = x + 22 + i * 10.6
        env = math.exp(-((i - 5) / 2.6) ** 2)
        h = 10 + 54 * env
        p.append(draw("hy-pic-strong", f"M{f(xx)} {y + 78} v-{f(h)}", t + 0.03 * i, 0.2))
        p.append(draw("hy-pic", f"M{f(xx + 4)} {y + 78} v-{f(h * 0.45)}", t + 0.03 * i, 0.2))
    env = "M" + " L".join(f"{f(x + 22 + i * 10.6)} {f(y + 70 - 54 * math.exp(-((i - 5) / 2.6) ** 2))}" for i in range(11))
    p.append(draw("hy-pic-dash", env, t + 0.35, 0.4))
    return p


# ------------------------------------------------------------------ figure 1: the pipeline
def pipeline() -> str:
    W, H = 1140, 330
    p: list[str] = []
    p.append(text(20, 30, "HAYDN, AS PROPOSED", "hy-head", 0.0))
    facts = [("aperture", "1.2 m"), ("field of view", "1 degree"), ("plate scale", "0.5 arcsec per pixel"),
             ("targets", "to G = 17"), ("candidate clusters", "27")]
    x = 190
    for k, v in facts:
        p.append(text(x, 30, k.upper(), "hy-key", 0.1))
        p.append(text(x, 46, v, "hy-val", 0.15))
        x += 185
    p.append(draw("hy-rule", f"M20 60 H{W - 20}", 0.1, 0.3))
    y0, h, w = 84, 150, 172
    xs = [20 + i * 186 for i in range(6)]
    stages = [
        ("ARCHIVE DATA", "Gaia, HST, four catalogues", pic_archive),
        ("THRESHOLD", "where both are complete", pic_threshold),
        ("KING PROFILE", "normalised in the annulus", pic_king),
        ("TRILEGAL FIELD", "mass-calibrated, then placed", pic_population),
        ("NOISE ESTIMATOR", "HNE, on Deucalion", pic_detector),
        ("SEISMIC MODEL", "Mosser et al. 2019", pic_seismic),
    ]
    for i, (title, line, pic) in enumerate(stages):
        x = xs[i]
        t = 0.2 + 0.12 * i
        p.append(draw("hy-box", f"M{x} {y0} h{w} v{h} h-{w} Z", t, 0.4))
        p.append(text(x + 10, y0 + 20, f"{i + 1}  {title}", "hy-title", t + 0.1))
        p.append(draw("hy-rule", f"M{x + 10} {y0 + 28} h{w - 20}", t + 0.1, 0.2))
        p += pic(x + 12, y0 + 34, t + 0.15)
        p.append(text(x + w / 2, y0 + h - 10, line, "hy-line", t + 0.5, "middle"))
    ym = y0 + h / 2
    for i in range(5):
        xa, xb = xs[i] + w, xs[i + 1]
        t = 0.35 + 0.12 * i
        p.append(thread(f"M{xa} {f(ym)} C{xa + 5} {f(ym - 7)}, {xb - 5} {f(ym + 7)}, {xb} {f(ym)}", t))
        p.append(node(xa, ym, t))
        p.append(node(xb, ym, t + 0.05))
    xe = xs[5] + w
    p.append(thread(f"M{xe} {f(ym)} C{xe + 8} {f(ym)}, {xe + 8} {f(ym)}, {W - 4} {f(ym)}", 1.0))
    p.append(node(xe, ym, 1.0))
    yb = y0 + h + 38
    xa = xs[1] + w / 2
    xb = xs[4] + w / 2
    d = (f"M{f(xa)} {y0 + h} C{f(xa)} {y0 + h + 28}, {f(xa + 20)} {yb}, {f(xa + 40)} {yb} "
         f"H{f(xb - 40)} C{f(xb - 20)} {yb}, {f(xb)} {y0 + h + 28}, {f(xb)} {y0 + h}")
    p.append(thread(d, 1.05, "ray flowray hy-bypass"))
    p.append(node(xa, y0 + h, 1.05))
    p.append(node(xb, y0 + h, 1.1))
    p.append(text((xa + xb) / 2, yb + 18, "open clusters skip these", "hy-line", 1.15, "middle"))
    return (
        f'<svg class="bp-svg hy-svg" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-labelledby="hy-pt hy-pd"><title id="hy-pt">The HAYDNsim pipeline, in six stages</title>'
        "<desc id=\"hy-pd\">Archive data from Gaia DR3, HST and four catalogues; a bright-star threshold and membership "
        "selection; a King profile normalised to HST; a TRILEGAL population placed by inverse-CDF sampling; the HAYDN Noise "
        "Estimator run on Deucalion, which returns a noise-to-signal ratio and a stellar pollution ratio per star; and a "
        "seismic performance model. Open clusters and resolved fields skip the profile and population steps.</desc>"
        + "".join(p) + "</svg>\n"
    )


# ------------------------------------------------------------------ figure 2: how a field is built
def crowding() -> str:
    """The poster's per-cluster fractions, the one result the proposal has made public."""
    W, H = 1140, 318
    p: list[str] = []
    L, T = 40, 30
    p.append(text(L, T, "STARS WHOSE LIGHT IS MOSTLY THEIR NEIGHBOURS'", "hy-head", 0.0))
    p.append(text(L, T + 18, "share with a stellar pollution ratio above 0.5, per cluster", "hy-line", 0.05))
    bx0, bx1 = L + 150, W - 150
    omega, ow = tex_glyphs(r"\omega", 13)
    for i, (name, pc) in enumerate(FRACTIONS):
        y = T + 62 + 28 * i
        t = 0.4 + 0.08 * i
        if name.startswith("omega"):
            p.append(pop(f'<g class="hy-tex-ink" transform="translate({L} {y})">{omega}</g>', t))
            p.append(text(L + ow + 4, y, "Cen", "hy-line", t))
        else:
            p.append(text(L, y, name, "hy-line", t))
        wbar = (bx1 - bx0) * pc / 40.0
        p.append(pop(f'<rect class="hy-bar" x="{bx0}" y="{y - 13}" width="{f(wbar)}" height="17"/>', t))
        p.append(text(bx0 + wbar + 10, y, f"{pc} %", "hy-num", t + 0.05))
    p.append(draw("hy-axis", f"M{bx0} {T + 40} V{T + 62 + 28 * 7 - 10}", 0.3, 0.3))
    p.append(text(L, H - 12, "FILLED BARS ARE DATA, FROM THE TASC10/KASC17 POSTER.", "hy-head", 0.2))
    return (
        f'<svg class="bp-svg hy-svg" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-labelledby="hy-ct hy-cd"><title id="hy-ct">Crowding in seven clusters, from HAYDNsim</title>'
        '<desc id="hy-cd">A bar for each of seven globular clusters giving the share of its stars whose '
        'light is mostly from neighbouring stars: 40 per cent in 47 Tucanae, 36 in NGC 6752 and M54, 12 in '
        'M22, 11 in omega Centauri, 7 in NGC 6397 and 3 in M4.</desc>'
        + "".join(p) + "</svg>\n"
    )


def main() -> None:
    OUT.joinpath("haydn-pipeline.svg").write_text(pipeline())
    OUT.joinpath("haydn-crowding.svg").write_text(crowding())
    for n in ("haydn-pipeline.svg", "haydn-crowding.svg"):
        print(f"wrote {OUT / n} ({OUT.joinpath(n).stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
