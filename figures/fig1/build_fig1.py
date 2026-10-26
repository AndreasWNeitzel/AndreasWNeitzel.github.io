"""Build FIG 1, the research-pipeline figure on the home page, as an inline SVG.

Usage: python3 figures/fig1/build_fig1.py   (stdlib only; run from the repository root)

Drafting grammar: construction lines are hairlines and draw first; objects are drawn in the
working weight; one accent line carries the reading from Gaia to the Milky Way and changes role
on the way (starlight, the XP spectrum, a fan into and out of the ensemble, the posterior, the
label vector, the thin disc). Between stages the data travels along curved, dashed connectors
whose dashes keep flowing in the direction of the data. Outline means schematic; fill means
real data.

Real data: assets/data/playground/gaia_xp_mh.json, the median-[M/H] red-giant example
spectrum (Gaia DR3 5289554869898620416, sampled from its XP coefficients, 2 nm grid). Every
other stage is schematic and drawn in outline, the Starfold groups included.

The page plays a one-time build when the figure first enters the view (site.js arms
[data-build]); the markup is the finished figure, which is what no-JS, print and reduced
motion show. Connectors are revealed by masks that draw on, so their dashes can flow.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "assets/data/playground/gaia_xp_mh.json"
OUT = ROOT / "_includes/figures/pipeline.svg"
EXAMPLE_ROW = 97  # the 50th-percentile [M/H] star of the three examples
W, H = 680, 524
TY1, TY2 = 238.0, 456.0  # title baselines, rows 1 and 2


def f(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".")


def timing(d: float, dur: float | None = None) -> str:
    return f'style="--d:{d:.2f}s{"" if dur is None else f";--dur:{dur:.2f}s"}"'


def draw(cls: str, d: str, t: float, dur: float) -> str:
    """A path that draws on like a pen stroke."""
    return f'<path class="{cls} b-draw" pathLength="1" {timing(t, dur)} d="{d}"/>'


def pop(el: str, t: float) -> str:
    """One-step reveal at time t for an element written as '<tag class="..." ...'."""
    assert el.startswith("<") and 'class="' in el, el
    tag, rest = el[1:].split(" ", 1)
    return f"<{tag} {timing(t)} " + rest.replace('class="', 'class="b-pop ', 1)


def text(
    x: float,
    y: float,
    s: str,
    cls: str,
    t: float,
    anchor: str = "start",
    italic: bool = False,
) -> str:
    it = ' font-style="italic"' if italic else ""
    return pop(
        f'<text class="{cls}" x="{f(x)}" y="{f(y)}" text-anchor="{anchor}"{it}>{s}</text>',
        t,
    )


def node(x: float, y: float, t: float, size: float = 5.0) -> str:
    return pop(
        f'<rect class="f1-node" x="{f(x - size / 2)}" y="{f(y - size / 2)}" width="{f(size)}" height="{f(size)}"/>',
        t,
    )


def poly(pts) -> str:
    return "M" + " L".join(f"{f(x)} {f(y)}" for x, y in pts)


def smooth(pts) -> str:
    """Catmull-Rom spline through the points, as cubic Beziers."""
    d = f"M{f(pts[0][0])} {f(pts[0][1])}"
    for i in range(len(pts) - 1):
        p0 = pts[max(i - 1, 0)]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[min(i + 2, len(pts) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{f(c1[0])} {f(c1[1])} {f(c2[0])} {f(c2[1])} {f(p2[0])} {f(p2[1])}"
    return d


def stage(key: str, label: str, box, body: list[str]) -> str:
    x, y, w, h = box
    return (
        f'<g class="f1-stage" data-stage="{key}" tabindex="0" role="button" aria-label="{label}">'
        f'<rect class="f1-hit" x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" rx="6"/>'
        + "".join(body)
        + "</g>"
    )


masks: list[str] = []
links: list[str] = []


def link(d: str, t: float, dur: float) -> None:
    """A curved connector: dashed, flowing with the data, revealed once by a mask that draws on."""
    k = len(masks) + 1
    masks.append(
        f'<mask id="f1m-{k}" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
        f'<path class="f1-mask b-draw" pathLength="1" {timing(t, dur)} d="{d}"/></mask>'
    )
    links.append(f'<path class="f1-link" mask="url(#f1m-{k})" d="{d}"/>')


# ------------------------------------------------------------------ data
spec = json.loads(SPEC.read_text())
ex = next(e for e in spec["examples"] if e["row"] == EXAMPLE_ROW)
w0, dw = spec["wavelength_nm"]["start"], spec["wavelength_nm"]["step"]
flux = ex["flux"]
lam = [w0 + dw * i for i in range(len(flux))]
keep = [i for i, l in enumerate(lam) if 360 <= l <= 990]
fmax = max(flux[i] for i in keep)


# ------------------------------------------------------------------ timeline (s)
T = {
    "gaia": 0.25,
    "light": 0.45,
    "l1": 0.7,
    "xp": 0.9,
    "l2": 1.35,
    "janus": 1.45,
    "post": 2.0,
    "l3": 2.2,
    "labels": 2.5,
    "l4": 2.8,
    "starfold": 3.0,
    "l5": 3.3,
    "galaxy": 3.3,
    "done": 3.6,
}

roles: list[str] = []  # the accent line inside stages, solid

# ------------------------------------------------------------------ construction
cons = [draw("f1-g", "M16 494 H664", 0.0, 0.17)]

# ------------------------------------------------------------------ stage A1: Gaia
t = T["gaia"]
gaia = [
    draw("f1-g", "M100 100 V206 M16 182 H184", 0.06, 0.17),
    draw("f1-g", "M100 122 L36 70 M100 122 L176 66", 0.1, 0.17),
    draw(
        "f1-o",
        "M80 122 L82 152 M120 122 L118 152 M80 122 A20 5.5 0 0 1 120 122 A20 5.5 0 0 1 80 122",
        t,
        0.32,
    ),
    draw("f1-o", "M82 152 L76 172 H124 L118 152 Z", t + 0.05, 0.28),
    draw("f1-o", "M28 182 A72 14 0 0 1 172 182 A72 14 0 0 1 28 182", t + 0.08, 0.35),
    draw(
        "f1-o",
        "M47 173 L63 176 M153 173 L137 176 M47 191 L63 188 M153 191 L137 188",
        t + 0.14,
        0.2,
    ),
    draw("f1-o", "M88 132 h8 v8 h-8 z M104 132 h8 v8 h-8 z", t + 0.16, 0.17),
]
for sx, sy in ((36, 70), (176, 66)):
    gaia.append(
        pop(f'<path class="f1-star" d="M{sx - 4} {sy} h8 M{sx} {sy - 4} v8"/>', t)
    )
gaia += [
    text(20, TY1, "GAIA", "f1-title", t, italic=True),
    text(20, TY1 + 15, "ESA astrometry satellite", "f1-sub", t),
]
# starlight along the line of sight into the payload, and out of its far wall
roles.append(
    draw("f1-t", "M176 66 L108 116.1 C112 124 116 131 122 137", T["light"], 0.25)
)

# ------------------------------------------------------------------ stage B1: the real XP spectrum
SPX0, SPX1, SPY0, SPY1 = 248.0, 412.0, 196.0, 92.0


def x_of(nm: float) -> float:
    return SPX0 + (nm - 360) / (990 - 360) * (SPX1 - SPX0)


curve = [(x_of(lam[i]), SPY0 - (flux[i] / fmax) * (SPY0 - SPY1) * 0.96) for i in keep]
spec_d = poly(curve)
tx = T["xp"]
xp = [
    draw("f1-g", f"M{f(SPX0)} {f(SPY1 - 8)} V{f(SPY0)} H{f(SPX1 + 4)}", 0.05, 0.17),
    pop(f'<path class="f1-gd" d="M{f(x_of(660))} {f(SPY1 - 4)} V{f(SPY0)}"/>', 0.1),
    text(x_of(660) - 6, SPY0 - 7, "BP", "f1-tick f1-onfill", 0.1, "end"),
    text(x_of(660) + 6, SPY0 - 7, "RP", "f1-tick f1-onfill", 0.1),
]
for nm in (360, 990):
    xp.append(draw("f1-g", f"M{f(x_of(nm))} {f(SPY0)} v4", 0.1, 0.17))
xp += [
    text(x_of(360), SPY0 + 15, "360", "f1-tick", 0.15, "middle"),
    text(x_of(990), SPY0 + 15, "990 nm", "f1-tick", 0.15, "middle"),
]
t_land = tx + 0.45
xp.append(
    pop(
        f'<path class="f1-fill" d="{spec_d} L{f(SPX1)} {f(SPY0)} L{f(SPX0)} {f(SPY0)} Z"/>',
        t_land,
    )
)
for nm, lab in ((656.3, "Hα"), (854.2, "Ca II")):
    xx = x_of(nm)
    yy = min(y for x, y in curve if abs(x - xx) < 1.5)
    xp.append(
        pop(f'<path class="f1-gm" d="M{f(xx)} {f(yy - 4)} V{f(yy - 12)}"/>', t_land)
    )
    xp.append(text(xx, yy - 15, lab, "f1-ann", t_land, "middle"))
xp += [
    text(238, TY1, "XP SPECTRUM", "f1-title", tx),
    text(238, TY1 + 15, "a red giant, 360 to 990 nm", "f1-sub", tx),
]
roles.append(draw("f1-t", spec_d, tx, 0.45))
x0s, y0s = curve[0]
x1s, y1s = curve[-1]
link(f"M126 137 C170 137 204 {f(y0s)} {f(x0s - 2)} {f(y0s)}", T["l1"], 0.2)

# ------------------------------------------------------------------ stage C1: JANUS
tj = T["janus"]
Y1 = 137.0
cols = (504.0, 540.0, 576.0)
rows5 = (86.0, 111.0, 136.0, 161.0, 186.0)
outs = [92.0 + i * 18.0 for i in range(6)]
edges = [
    f"M{f(cols[a])} {f(ya)} L{f(cols[b])} {f(yb)}"
    for a, b in ((0, 1), (1, 2))
    for ya in rows5
    for yb in rows5
]
edges += [f"M{f(cols[2])} {f(ya)} L604 {f(yb)}" for ya in rows5 for yb in outs]
jn = [draw("f1-g f1-edges", " ".join(edges), 0.12, 0.3)]
for k in range(3, 0, -1):
    jn.append(
        draw(
            "f1-g",
            f"M{f(472 + 3 * k)} {f(64 - 3 * k)} h148 v142 h-148 Z",
            0.18 + 0.03 * k,
            0.17,
        )
    )
jn.append(draw("f1-o", "M472 64 h148 v142 h-148 Z", tj, 0.3))
# the thread fans into the first layer and gathers again from the output layer: straight lines
# that end on the nodes, so the network reads as a network; the stack behind it carries the x8
for i, y in enumerate(rows5):
    jn.append(draw("f1-strand", f"M452 {f(Y1)} L{f(cols[0] - 4.2)} {f(y)}", tj + 0.04 * i, 0.3))
for i, y in enumerate(outs):
    jn.append(draw("f1-strand", f"M{f(604 + 4.2)} {f(y)} L634 {f(Y1)}", tj + 0.25 + 0.04 * i, 0.3))
nodes = [(x, y) for x in cols for y in rows5] + [(604, y) for y in outs]
jn.append(
    pop(
        '<g class="f1-nodes">'
        + "".join(f'<circle cx="{f(x)}" cy="{f(y)}" r="4.2"/>' for x, y in nodes)
        + "</g>",
        tj,
    )
)
jn.append(draw("f1-o", "M634 108 h28 v58 h-28 Z", tj + 0.2, 0.25))
jn.append(
    pop(
        '<path class="f1-gd" d="M637 160 C642 160 643 128 648 128 C653 128 654 160 659 160"/>',
        tj + 0.3,
    )
)
jn += [
    text(634, 62, "×8", "f1-dim", T["post"]),
    text(472, 220, "110 in", "f1-tick", T["post"]),
    text(620, 220, "6 out", "f1-tick", T["post"], "end"),
    text(472, TY1, "JANUS", "f1-title", tj),
    text(472, TY1 + 15, "8 normalising-flow networks", "f1-sub", tj),
]
roles.append(
    draw(
        "f1-t",
        "M634 137 C638 122 643 114 648 114 C654 114 657 126 662 140",
        T["post"],
        0.2,
    )
)
link(f"M{f(x1s)} {f(y1s)} C428 {f(y1s)} 436 {f(Y1)} 452 {f(Y1)}", T["l2"], 0.1)

# ------------------------------------------------------------------ seismic input above JANUS
sm = [
    draw("f1-g", "M470 42 H560", 0.2, 0.17),
    pop(
        '<path class="f1-gd" d="M474 40 C494 40 496 14 515 12 C534 14 536 40 556 40"/>',
        0.25,
    ),
]
comb = " ".join(
    f"M{f(480 + 6 * k)} 42 v-{f(4 + 22 * math.exp(-(((480 + 6 * k - 515) / 16) ** 2)))}"
    for k in range(13)
)
sm += [
    draw("f1-o", comb, tj, 0.3),
    text(466, 24, "TESS · KEPLER", "f1-title f1-small", tj, "end", italic=True),
    text(466, 38, "seismic red giants", "f1-sub", tj, "end"),
]
link("M515 46 C515 52 515 57 515 63", tj + 0.2, 0.15)

# ------------------------------------------------------------------ stage C2: labels and reliability
tlab = T["labels"]
names = ("Teff", "log g", "[M/H]", "[α/M]", "[Fe/H]", "[Mg/H]")
ry = [314.0 + 18.0 * i for i in range(6)]
med = [552.0] * 6  # schematic: one star's six labels, centred on the spine
half = [11.0, 13.0, 8.0, 16.0, 8.0, 12.0]  # schematic spreads
lb = []
for i, (nm, y) in enumerate(zip(names, ry)):
    lb.append(draw("f1-g", f"M510 {f(y - 3)} H596", 0.2 + 0.03 * i, 0.17))
    lb.append(text(462, y, nm, "f1-tick", tlab))
    lb.append(
        draw(
            "f1-o",
            f"M{f(med[i] - half[i])} {f(y - 3)} H{f(med[i] + half[i])}",
            tlab + 0.04 * i,
            0.17,
        )
    )
lb += [
    draw("f1-g", "M610 410 H660", 0.25, 0.17),
    draw("f1-o", "M612 410 A23 23 0 0 1 658 410", tlab, 0.3),
    pop('<path class="f1-needle" d="M635 410 L648 392"/>', tlab + 0.3),
    pop('<circle class="f1-dot" cx="635" cy="410" r="2.4"/>', tlab + 0.3),
    text(635, 380, "P(miss)", "f1-tick", tlab + 0.3, "middle"),
    text(612, 423, "0", "f1-tick", tlab + 0.3, "middle"),
    text(658, 423, "1", "f1-tick", tlab + 0.3, "middle"),
    text(462, TY2, "LABELS + RELIABILITY", "f1-title", tlab),
    text(462, TY2 + 15, "spread and miss probability", "f1-sub", tlab),
]
roles.append(draw("f1-t", f"M{f(med[0])} {f(ry[0] - 3)} V{f(ry[-1] - 3)}", tlab, 0.3))
link(
    f"M662 140 C678 162 680 236 667 268 C654 298 566 290 {f(med[0])} {f(ry[0] - 3)}",
    T["l3"],
    0.3,
)

# ------------------------------------------------------------------ stage B2: Starfold, schematic
# Three groups drawn in outline. Each group is three faint contours, one per refit shown, that
# nearly agree (the recurrence Starfold measures over 32 refits), with hollow marks inside;
# three hollow marks outside belong to no group.
tsf = T["starfold"]
GOLDEN = math.pi * (3 - math.sqrt(5))
GROUPS = (  # centre x, centre y, radius x, radius y, tilt (deg), marks
    (290.0, 336.0, 30.0, 19.0, -12.0, 8),
    (372.0, 334.0, 28.0, 17.0, 16.0, 7),
    (330.0, 396.0, 38.0, 19.0, 4.0, 9),
)


def blob(cx, cy, rx, ry, tilt, phase, scale):
    th = math.radians(tilt)
    pts = []
    for k in range(48):
        u = 2 * math.pi * k / 48
        r = scale * (
            1 + 0.07 * math.sin(2 * u + phase) + 0.05 * math.sin(3 * u + 2 * phase)
        )
        x, y = rx * r * math.cos(u), ry * r * math.sin(u)
        pts.append(
            (
                cx + x * math.cos(th) - y * math.sin(th),
                cy + x * math.sin(th) + y * math.cos(th),
            )
        )
    return poly(pts) + " Z"


sf = []
for g, (cx, cy, ax, ay, tilt, n) in enumerate(GROUPS):
    for j, (phase, scale) in enumerate(((0.0, 1.0), (0.9, 1.06), (2.1, 0.95))):
        sf.append(
            draw(
                "f1-g f1-hull",
                blob(cx, cy, ax, ay, tilt, phase + g, scale),
                0.2 + 0.03 * (3 * g + j),
                0.17,
            )
        )
    th = math.radians(tilt)
    marks = []
    for k in range(n):
        rr = 0.72 * math.sqrt((k + 0.5) / n)
        x, y = ax * rr * math.cos(k * GOLDEN + g), ay * rr * math.sin(k * GOLDEN + g)
        marks.append(
            f'<circle cx="{f(cx + x * math.cos(th) - y * math.sin(th))}" '
            f'cy="{f(cy + x * math.sin(th) + y * math.cos(th))}" r="2.6"/>'
        )
    sf.append(
        pop(
            '<g class="f1-marks">' + "".join(marks) + "</g>",
            tsf + 0.06 * (len(GROUPS) - 1 - g),
        )
    )
loose = "".join(
    f'<circle cx="{f(x)}" cy="{f(y)}" r="2.6"/>'
    for x, y in ((256.0, 374.0), (404.0, 372.0), (262.0, 420.0))
)
sf.append(pop(f'<g class="f1-marks f1-loose">{loose}</g>', tsf + 0.2))
sf += [
    text(414, 440, "32 refits", "f1-tick", tsf + 0.3, "end"),
    text(238, TY2, "STARFOLD", "f1-title", tsf),
    text(238, TY2 + 15, "UMAP + HDBSCAN, recurrence", "f1-sub", tsf),
]
link(f"M{f(med[-1])} {f(ry[-1] - 3)} C{f(med[-1])} 434 470 436 418 408", T["l4"], 0.2)

# ------------------------------------------------------------------ stage A2: the Milky Way
tg = T["galaxy"]
CX, CY = 104.0, 372.0
# accreted debris: an inclined stream wrapped around the Galaxy (schematic, outline)
_th = math.radians(-34)
_ring = [
    (
        CX + 60 * math.cos(u) * math.cos(_th) - 18 * math.sin(u) * math.sin(_th),
        CY + 60 * math.cos(u) * math.sin(_th) + 18 * math.sin(u) * math.cos(_th),
    )
    for u in (math.pi * (0.62 + 1.5 * k / 40) for k in range(41))
]
stream_d = smooth(_ring)
mw = [
    draw("f1-g", f"M{f(CX - 86)} {f(CY)} H{f(CX + 86)}", 0.25, 0.17),
    pop(f'<circle class="f1-gd" cx="{f(CX)}" cy="{f(CY)}" r="62"/>', 0.3),
    draw(
        "f1-o",
        f"M{f(CX - 74)} {f(CY)} A74 15 0 0 1 {f(CX + 74)} {f(CY)} A74 15 0 0 1 {f(CX - 74)} {f(CY)}",
        tg,
        0.35,
    ),
    draw(
        "f1-o",
        f"M{f(CX - 13)} {f(CY)} A13 9 0 0 1 {f(CX + 13)} {f(CY)} A13 9 0 0 1 {f(CX - 13)} {f(CY)}",
        tg + 0.1,
        0.25,
    ),
    draw("f1-o f1-stream", stream_d, tg + 0.2, 0.35),
    text(CX + 4, CY - 66, "halo", "f1-tick", tg + 0.3),
    text(CX + 50, CY - 40, "accreted", "f1-tick", tg + 0.3),
    text(CX - 82, CY + 28, "thick disc", "f1-tick", tg + 0.3),
    text(CX + 18, CY + 28, "thin disc", "f1-tick", tg + 0.3),
    text(20, TY2, "MILKY WAY", "f1-title", tg),
    text(20, TY2 + 15, "its populations and history", "f1-sub", tg),
]
link(f"M246 372 C228 350 200 350 {f(CX + 74)} {f(CY)}", T["l5"], 0.15)
roles.append(
    draw(
        "f1-t",
        f"M{f(CX + 72)} {f(CY)} A72 5 0 0 1 {f(CX - 72)} {f(CY)} A72 5 0 0 1 {f(CX + 72)} {f(CY)}",
        tg + 0.15,
        0.45,
    )
)

# ------------------------------------------------------------------ compute rail
rl = [
    node(104, 494, T["gaia"]),
    node(330, 494, T["xp"]),
    node(560, 494, T["janus"]),
    text(20, 513, "RUNS ON", "f1-title f1-small", T["done"]),
    text(
        84,
        513,
        "Deucalion · MareNostrum 5 · Slurm · CUDA · RAPIDS · 1.3 M core-h approved",
        "f1-sub",
        T["done"],
    ),
]

# ------------------------------------------------------------------ assemble, back to front
svg = (
    f'<svg class="f1-svg" data-build="" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="group" '
    'aria-label="Schematic of the research pipeline: Gaia spectra, the JANUS neural networks, labels with reliability, '
    "Starfold groups and Milky Way populations, on two supercomputers. The spectrum is a real Gaia XP spectrum of a red "
    'giant; the other stages are schematic.">'
    + "<defs>"
    + "".join(masks)
    + "</defs>"
    + "".join(cons)
    + stage("gaia", "Stage 1, Gaia", (12, 56, 192, 196), gaia)
    + stage("xp", "Stage 2, XP spectra", (226, 56, 210, 196), xp)
    + stage("seismo", "Asteroseismology input", (340, 2, 230, 50), sm)
    + stage("janus", "Stage 3, JANUS neural networks", (456, 62, 212, 196), jn)
    + stage(
        "labels", "Stage 4, stellar labels with reliability", (456, 292, 212, 186), lb
    )
    + stage("starfold", "Stage 5, Starfold", (226, 292, 210, 186), sf)
    + stage("galaxy", "Stage 6, Milky Way populations", (12, 292, 192, 186), mw)
    + stage("hpc", "Compute: Deucalion and MareNostrum 5", (12, 484, 656, 38), rl)
    + '<g class="f1-thread" aria-hidden="true">'
    + "".join(links)
    + "".join(roles)
    + "</g>"
    + "</svg>\n"
)
OUT.write_text(svg)


# ------------------------------------------------------------------ the JANUS figure for /research/janus/
# The same Gaia, XP and JANUS stages at the same scale, with what the JANUS page needs around
# them: APOGEE DR19 as the teacher above the networks, the labels beside them, the withheld-star
# test and the two alpha sequences under them, the inputs under the spectrum, the catalogue of
# TESS giants at the right with the seismic sample entering it, and the compute rail along the
# bottom. Numbers from the IMAS13 abstract (October 2026) and the FCT allocations in the ledger.
JW, JH = 1180, 524
jmasks: list[str] = []
jlinks: list[str] = []


def jlink(d: str, t: float, dur: float) -> None:
    k = len(jmasks) + 1
    jmasks.append(
        f'<mask id="f1jm-{k}" maskUnits="userSpaceOnUse" x="0" y="0" width="{JW}" height="{JH}">'
        f'<path class="f1-mask b-draw" pathLength="1" {timing(t, dur)} d="{d}"/></mask>'
    )
    jlinks.append(f'<path class="f1-link" mask="url(#f1jm-{k})" d="{d}"/>')


LX, LY = 234.0, -230.0  # the labels stage, from row two of FIG 1 up beside the networks

# APOGEE DR19 above the networks: a high-resolution spectrum, a continuum with narrow lines
ap = [draw("f1-g", "M470 44 H560", 0.2, 0.17)]
lines_d = " ".join(
    f"M{f(476 + 2.1 * k)} 24 v{f(3 + 13 * abs(math.sin(k * 1.37) * math.cos(k * 0.41)))}" for k in range(39)
)
ap += [
    draw("f1-o", "M474 24 H558 " + lines_d, tj, 0.35),
    text(466, 24, "APOGEE DR19", "f1-title f1-small", tj, "end"),
    text(466, 38, "the training labels", "f1-sub", tj, "end"),
]
jlink("M515 46 C515 52 515 57 515 63", tj + 0.2, 0.15)

# the inputs under the spectrum: one star as a row of numbers
ti = T["xp"] + 0.5
IX, IY = 248.0, 318.0
inp = [draw("f1-g", f"M{f(IX)} {f(IY + 46)} H412", 0.2, 0.17)]
cells = " ".join(f"M{f(IX + 7 * k)} {f(IY)} h5 v5 h-5 Z" for k in range(24))
aux = " ".join(f"M{f(IX + 7 * k)} {f(IY + 30)} h5 v5 h-5 Z" for k in range(7))
inp += [
    draw("f1-o", cells, ti, 0.3),
    text(IX + 7 * 24 + 4, IY + 5, "…", "f1-tick", ti + 0.2),
    draw("f1-g", f"M{f(IX)} {f(IY + 12)} H{f(IX + 7 * 24 - 2)} M{f(IX)} {f(IY + 9)} v6 M{f(IX + 7 * 24 - 2)} {f(IY + 9)} v6", ti + 0.2, 0.2),
    text(IX + 7 * 12, IY + 24, "110 coefficients", "f1-dim", ti + 0.3, "middle"),
    draw("f1-o", aux, ti + 0.2, 0.2),
    text(IX, IY + 52, "parallax, photometry, extinction", "f1-tick", ti + 0.3),
    text(238, TY2, "THE INPUTS", "f1-title", ti),
    text(238, TY2 + 15, "one star as a row of numbers", "f1-sub", ti),
]
jlink("M232 252 C232 268 232 278 232 292", T["xp"] + 0.4, 0.15)

# the two alpha sequences under the networks: resolved with the spectrum, merged without it
ta = T["post"] + 0.2
al = []
for k, (x0, title) in enumerate(((472.0, "with the spectrum"), (584.0, "without it"))):
    al.append(draw("f1-g", f"M{f(x0)} 318 V398 H{f(x0 + 84)}", 0.2 + 0.05 * k, 0.17))
    al.append(text(x0 + 42, 312, title, "f1-tick", ta + 0.1 * k, "middle"))
    al.append(text(x0 + 84, 410, "[M/H]", "f1-tick", ta + 0.1 * k, "end"))
    al.append(text(x0 + 3, 326, "[α/M]", "f1-tick", ta + 0.1 * k))
if True:
    hi = smooth([(480, 336), (500, 334), (522, 339), (542, 347), (552, 356), (540, 360), (518, 354), (496, 348), (478, 344), (476, 339), (480, 336)])
    lo = smooth([(488, 378), (506, 374), (526, 374), (546, 378), (554, 386), (542, 392), (520, 392), (498, 390), (484, 386), (482, 381), (488, 378)])
    al.append(draw("f1-o", hi + " Z", ta, 0.3))
    al.append(draw("f1-o", lo + " Z", ta + 0.1, 0.3))
    one = smooth([(590, 342), (612, 338), (636, 346), (658, 362), (664, 380), (652, 390), (628, 388), (606, 376), (590, 360), (586, 350), (590, 342)])
    al.append(draw("f1-o", one + " Z", ta + 0.2, 0.35))
al += [
    text(472, TY2, "TWO α SEQUENCES", "f1-title", ta),
    text(472, TY2 + 15, "the same network, with and without the spectrum", "f1-sub", ta),
]
jlink("M464 258 C464 268 464 278 464 292", T["post"] + 0.1, 0.15)

# the labels stage beside the networks, the test on withheld stars under it
jlink(f"M662 140 C684 140 690 68 722 68 H{f(med[0] + LX - 16)} C{f(med[0] + LX - 6)} 68 {f(med[0] + LX)} 72 {f(med[0] + LX)} {f(ry[0] - 3 + LY)}", T["l3"], 0.35)
tt = T["labels"] + 0.3
TX, TY = 696.0, 300.0
test = [
    draw("f1-g", f"M{f(TX)} {f(TY - 20)} H908", 0.2, 0.17),
    text(TX, TY, "WITHHELD STARS", "f1-title f1-small", tt),
    text(TX, TY + 15, "robust scatter about APOGEE", "f1-sub", tt),
]
for i, (nm, val) in enumerate((("Teff", "32 K"), ("log g", "0.072 dex"), ("[M/H]", "0.051 dex"), ("[α/M]", "0.021 dex"))):
    cx, cy = TX + (i % 2) * 108, TY + 38 + (i // 2) * 44
    test += [
        draw("f1-g", f"M{f(cx)} {f(cy + 16)} h96 M{f(cx)} {f(cy + 12)} v8 M{f(cx + 96)} {f(cy + 12)} v8", tt + 0.1 + 0.05 * i, 0.2),
        text(cx, cy, nm, "f1-tick", tt + 0.15 + 0.05 * i),
        text(cx + 96, cy + 8, val, "f1-dim", tt + 0.15 + 0.05 * i, "end"),
    ]
jlink(f"M{f(658 + LX)} {f(410 + LY)} C{f(672 + LX)} {f(410 + LY)} 906 {f(TY - 70)} 906 {f(TY - 24)}", T["labels"] + 0.3, 0.2)

# the seismic sample above the catalogue: TESS red giants with measured oscillations
sm2 = [draw("f1-g", "M936 42 H1026", 0.2, 0.17), pop('<path class="f1-gd" d="M940 40 C960 40 962 14 981 12 C1000 14 1002 40 1022 40"/>', 0.25)]
comb2 = " ".join(
    f"M{f(946 + 6 * k)} 42 v-{f(4 + 22 * math.exp(-(((946 + 6 * k - 981) / 16) ** 2)))}" for k in range(13)
)
tc = T["starfold"]
sm2 += [
    draw("f1-o", comb2, tc, 0.3),
    text(1034, 24, "TESS GIANTS", "f1-title f1-small", tc),
    text(1034, 38, "with oscillations", "f1-sub", tc),
]
jlink("M981 46 C981 54 981 62 981 72", tc + 0.2, 0.15)

# the catalogue: a table, one row per giant, one row in ten with APOGEE values too
CX0, CY0, CW = 936.0, 72.0, 222.0
cols = ("Teff", "log g", "[M/H]", "[α/M]", "[X/H]", "P(miss)")
cat = [draw("f1-g", f"M{f(CX0)} {f(CY0)} H{f(CX0 + CW)} V380 H{f(CX0)} Z M{f(CX0)} 96 H{f(CX0 + CW)}", 0.25, 0.3)]
for i, nm in enumerate(cols):
    cat.append(text(CX0 + 6 + 37 * i, 88, nm, "f1-tick", tc + 0.3))
rows_d, fills = [], []
for r in range(27):
    y = 106 + 10.2 * r
    rows_d.append(" ".join(f"M{f(CX0 + 8 + 37 * i)} {f(y)} h18" for i in range(6)))
    if r % 10 == 4:
        fills.append(f'<rect class="f1-fill" x="{f(CX0 + 2)}" y="{f(y - 4)}" width="{f(CW - 4)}" height="8" rx="1"/>')
cat += [
    pop("".join(fills), tc + 0.4),
    draw("f1-g", " ".join(rows_d), tc + 0.3, 0.6),
    draw("f1-g", f"M{f(CX0)} 396 H{f(CX0 + CW)} M{f(CX0)} 392 v8 M{f(CX0 + CW)} 392 v8", tc + 0.5, 0.3),
    text(CX0 + CW / 2, 412, "144,304 giants", "f1-dim", tc + 0.6, "middle"),
    text(CX0, TY2, "THE CATALOGUE", "f1-title", tc + 0.5),
    text(CX0, TY2 + 15, "one row in ten has APOGEE values too", "f1-sub", tc + 0.55),
]
jlink(f"M{f(med[-1] + LX)} {f(ry[-1] - 3 + LY)} C{f(med[-1] + LX)} 206 820 206 860 206 H{f(CX0 - 2)}", T["l4"], 0.3)

# the compute rail, under the first three stages
rl2 = [
    node(104, 494, T["gaia"]),
    node(330, 494, T["xp"]),
    node(560, 494, T["janus"]),
    text(20, 513, "RUNS ON", "f1-title f1-small", T["done"]),
    text(84, 513, "Deucalion, Gaia DR3, about 220 million spectra · MareNostrum 5, Gaia DR4, about 1.8 billion", "f1-sub", T["done"]),
]

janus_svg = (
    f'<svg class="f1-svg f1-janus" data-build="" viewBox="0 0 {JW} {JH}" xmlns="http://www.w3.org/2000/svg" role="group" '
    'aria-label="Schematic of JANUS: Gaia observes a red giant; its XP spectrum becomes 110 coefficients with parallax, '
    "photometry and extinction; eight normalising-flow networks trained on APOGEE DR19 return six labels with a spread and a "
    "miss probability; the test on withheld stars gives the scatter about APOGEE; the same network without the spectrum merges "
    'the two alpha sequences; the catalogue covers 144,304 TESS red giants; the networks run on Deucalion and MareNostrum 5.">'
    + "<defs>" + masks[0] + masks[1] + "".join(jmasks) + "</defs>"
    + draw("f1-g", "M16 494 H900", 0.0, 0.17)
    + stage("gaia", "Gaia", (12, 56, 192, 196), gaia)
    + stage("xp", "XP spectra", (226, 56, 210, 196), xp)
    + stage("inputs", "The inputs", (226, 292, 210, 180), inp)
    + stage("apogee", "APOGEE DR19, the training labels", (340, 2, 230, 50), ap)
    + stage("janus", "JANUS neural networks", (456, 62, 212, 196), jn)
    + stage("alpha", "The two alpha sequences", (456, 292, 212, 180), al)
    + f'<g transform="translate({f(LX)} {f(LY)})">' + stage("labels", "Stellar labels with reliability", (456, 292, 212, 186), lb) + "</g>"
    + stage("test", "The test on withheld stars", (690, 272, 222, 150), test)
    + stage("sample", "TESS red giants with oscillations", (924, 2, 246, 54), sm2)
    + stage("catalogue", "The catalogue", (924, 62, 246, 420), cat)
    + stage("hpc", "Compute: Deucalion and MareNostrum 5", (12, 484, 890, 38), rl2)
    + '<g class="f1-thread" aria-hidden="true">'
    + links[0] + links[1] + roles[0] + roles[1] + roles[2]
    + f'<g transform="translate({f(LX)} {f(LY)})">' + roles[3] + "</g>"
    + "".join(jlinks)
    + "</g></svg>\n"
)
(ROOT / "_includes/figures/janus.svg").write_text(janus_svg)
print(f"wrote _includes/figures/janus.svg: {len(janus_svg) / 1024:.1f} KB")
