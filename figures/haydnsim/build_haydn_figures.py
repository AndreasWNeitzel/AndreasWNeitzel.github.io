"""Build the three HAYDNsim figures for /software/haydnsim/.

haydn-pipeline.svg   The six stages of HAYDNsim as pictograms, after the flowchart on the TASC10/KASC17
                     poster (Neitzel et al. 2026, doi:10.5281/zenodo.23263454) and slide 6 of the DFA
                     Week 2026 talk; the instrument strip is from slide 2 of that talk. Outline means
                     schematic.
haydn-field.svg      How a field is built: the 47 Tucanae sky plane with the binned radial profile of the
                     placed stars (assets/data/haydnsim/47tuc_radial_profile.csv) and a King (1962) model
                     with the Harris 2010 shape parameters, the luminosity function of the delivered field
                     (assets/data/haydnsim/47tuc_luminosity_function.csv), the detector with the point
                     spread function and a photometric mask, the two noise formulas, and the median noise
                     terms of one magnitude bin from the binned noise table.
haydn-noise.svg      Real data: the 47 Tucanae noise budget, binned medians from the HAYDN Noise Estimator
                     output (assets/data/haydnsim/47tuc_noise_budget_binned.csv), against the PLATO P band,
                     and the public per-cluster fractions of stars whose light is mostly from neighbours.
                     Filled marks mean data.

Usage: python3 figures/haydnsim/build_haydn_figures.py
Needs latex and dvisvgm on the path for the typeset symbols (figures/texsvg.py).
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "figures"))
from texsvg import tex_glyphs  # noqa: E402

OUT = ROOT / "_includes/figures"
DATA = ROOT / "assets/data/haydnsim"
NOISE = DATA / "47tuc_noise_budget_binned.csv"
LUMFN = DATA / "47tuc_luminosity_function.csv"
RADIAL = DATA / "47tuc_radial_profile.csv"

# public per-cluster fractions of stars with SPR > 0.5, poster bar chart (per cent)
FRACTIONS = [("47 Tuc", 40), ("NGC 6752", 36), ("M54", 36), ("M22", 12), ("omega Cen", 11), ("NGC 6397", 7), ("M4", 3)]

# 47 Tuc King-profile shape, Harris 2010 (public): core radius and concentration
R_CORE_ARCSEC = 0.36 * 60.0
CONCENTRATION = 2.07
R_TIDAL_ARCSEC = R_CORE_ARCSEC * 10 ** CONCENTRATION  # 42.3 arcmin
FIELD_RADIUS_ARCSEC = 1800.0  # the 1 degree field (public)
PIXEL_ARCSEC = 0.5  # public
PSF_90_ARCSEC = 1.3  # 90 per cent energy diameter (clearable)
MASK_PX = (6, 3, 13)  # median mask size and its 5 to 95 per cent range (clearable)
EXAMPLE = {"bin": "15.7 to 16.0", "n": 1038, "total": 430, "photon": 182, "detector": 168, "jitter": 71,
           "crowding": 347, "spr": 0.16}  # medians of one P bin (clearable)
GOLDEN = math.pi * (3 - math.sqrt(5))


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


def node(x: float, y: float, t: float, k: float = 6.0) -> str:
    return pop(f'<rect class="hy-node" x="{f(x - k / 2)}" y="{f(y - k / 2)}" width="{f(k)}" height="{f(k)}"/>', t)


def thread(d: str, t: float, cls: str = "ray flowray hy-thread") -> str:
    return pop(f'<path class="{cls}" d="{d}"/>', t)


def read_csv(path: Path) -> list[dict[str, float]]:
    with path.open() as fh:
        return [{k: float(v) for k, v in r.items()}
                for r in csv.DictReader(line for line in fh if not line.startswith("#"))]


def king(r: float) -> float:
    """King (1962) surface density shape, amplitude one."""
    a = 1.0 / math.sqrt(1.0 + (r / R_CORE_ARCSEC) ** 2)
    b = 1.0 / math.sqrt(1.0 + (R_TIDAL_ARCSEC / R_CORE_ARCSEC) ** 2)
    return (a - b) ** 2


def sampled_marks(profile: list[dict[str, float]], n: int) -> list[tuple[float, float]]:
    """Positions (r in arcsec, theta) whose density follows the binned profile: stratified quantiles of
    the star-count CDF, uniform in area inside each bin, azimuths on the golden angle. Schematic."""
    counts = [row["n_stars"] for row in profile]
    total = sum(counts)
    cum = []
    acc = 0.0
    for c in counts:
        acc += c
        cum.append(acc / total)
    out = []
    for i in range(n):
        u = (i + 0.5) / n
        j = next(k for k, c in enumerate(cum) if u <= c)
        lo = cum[j - 1] if j else 0.0
        frac = (u - lo) / (cum[j] - lo)
        r0, r1 = profile[j]["r_lo_arcsec"], profile[j]["r_hi_arcsec"]
        r = math.sqrt(r0 * r0 + frac * (r1 * r1 - r0 * r0))
        out.append((r, i * GOLDEN))
    return out


# ------------------------------------------------------------------ pictograms for the pipeline
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
def field() -> str:
    profile = read_csv(RADIAL)
    lumfn = read_csv(LUMFN)
    W, H = 1140, 580
    p: list[str] = []

    # ---- sky plane: the field circle with schematic marks
    cx, cy, R = 150, 196, 124
    p.append(text(20, 30, "SKY PLANE, 47 TUCANAE", "hy-head", 0.0))
    p.append(draw("hy-axis", f"M{f(cx + R)} {f(cy)} A{R} {R} 0 1 1 {f(cx - R)} {f(cy)} A{R} {R} 0 1 1 {f(cx + R)} {f(cy)}", 0.1, 0.6))
    p.append(draw("hy-grid", f"M{f(cx - R - 6)} {f(cy)} H{f(cx + R + 6)} M{f(cx)} {f(cy - R - 6)} V{f(cy + R + 6)}", 0.1, 0.3))
    marks = []
    for r, a in sampled_marks(profile, 900):
        s = r / FIELD_RADIUS_ARCSEC * R
        marks.append(f'<circle cx="{f(cx + s * math.cos(a))}" cy="{f(cy + s * math.sin(a))}" r="1.1"/>')
    p.append(pop(f'<g class="hy-sample">{"".join(marks)}</g>', 0.5))
    ra, rb = 50 / FIELD_RADIUS_ARCSEC * R, 100 / FIELD_RADIUS_ARCSEC * R
    p.append(pop(f'<circle class="hy-ring" cx="{f(cx)}" cy="{f(cy)}" r="{f(ra)}"/><circle class="hy-ring" cx="{f(cx)}" cy="{f(cy)}" r="{f(rb)}"/>', 0.7))
    p.append(draw("hy-leader", f"M{f(cx + rb)} {f(cy + rb)} L{f(cx + 46)} {f(cy + 66)} H{f(cx + 56)}", 0.8, 0.3))
    p.append(text(cx + 60, cy + 62, "HST annulus", "hy-line", 0.9))
    p.append(text(cx + 60, cy + 76, "50 to 100 arcsec", "hy-line", 0.9))
    p.append(text(cx, cy + R + 20, "1 degree field", "hy-lab", 0.3, "middle"))

    # ---- radial profile: data as filled marks, King shape as outline
    L1, R1, T1, B1 = 386, 544, 70, 300
    lr0, lr1 = math.log10(2.0), math.log10(1800.0)
    ld0, ld1 = -0.3, 4.75

    def px1(r: float) -> float:
        return L1 + (math.log10(r) - lr0) / (lr1 - lr0) * (R1 - L1)

    def py1(dens: float) -> float:
        return B1 - (math.log10(dens) - ld0) / (ld1 - ld0) * (B1 - T1)

    p.append(draw("hy-axis", f"M{L1} {T1} V{B1} H{R1}", 0.1, 0.4))
    for dens in (1, 10, 100, 1000, 10000):
        y = py1(dens)
        p.append(draw("hy-grid", f"M{L1} {f(y)} H{R1}", 0.15, 0.17))
        p.append(text(L1 - 6, y + 4, f"{dens:,}".replace(",", " "), "hy-num", 0.25, "end"))
    for r, lab in ((10, "10"), (100, "100"), (1000, "1000")):
        x = px1(r)
        p.append(draw("hy-tick", f"M{f(x)} {B1} v5", 0.15, 0.17))
        p.append(text(x, B1 + 17, lab, "hy-num", 0.25, "middle"))
    p.append(text(R1, B1 + 32, "radius (arcsec), log", "hy-lab", 0.3, "end"))
    p.append(pop(f'<g transform="translate({L1 - 54} {f((T1 + B1) / 2)}) rotate(-90)"><text class="hy-lab" text-anchor="middle">stars per square arcmin</text></g>', 0.3))
    xa, xb = px1(50), px1(100)
    p.append(pop(f'<rect class="hy-window" x="{f(xa)}" y="{T1}" width="{f(xb - xa)}" height="{B1 - T1}"/>', 0.4))
    xc = px1(R_CORE_ARCSEC)
    p.append(draw("hy-limit", f"M{f(xc)} {T1} V{B1}", 0.45, 0.3))
    p.append(tex(xc + 4, T1 + 14, r"r_c", 12, 0.5, "hy-tex-muted"))
    # King shape scaled to the data in log space (least squares on the bins inside 1000 arcsec)
    xs_mid = [math.sqrt(r["r_lo_arcsec"] * r["r_hi_arcsec"]) for r in profile]
    resid = [math.log10(r["density_per_arcmin2"]) - math.log10(king(m)) for r, m in zip(profile, xs_mid) if m < 1000]
    offset = sum(resid) / len(resid)
    pts = []
    for i in range(61):
        r = 2.0 * (1800.0 / 2.0) ** (i / 60)
        pts.append((px1(r), py1(10 ** (math.log10(king(r)) + offset))))
    p.append(draw("hy-model", "M" + " L".join(f"{f(a)} {f(b)}" for a, b in pts), 0.6, 0.9))
    marks = "".join(f'<circle cx="{f(px1(m))}" cy="{f(py1(r["density_per_arcmin2"]))}" r="2.6"/>' for r, m in zip(profile, xs_mid))
    p.append(pop(f'<g class="hy-data">{marks}</g>', 1.0))
    p.append(pop(f'<path class="hy-model" d="M{L1 + 14} {B1 - 40} h18"/>', 1.1))
    p.append(text(L1 + 38, B1 - 36, "King shape", "hy-line", 1.1))
    p.append(pop(f'<circle class="hy-data-key" cx="{L1 + 23}" cy="{B1 - 22}" r="2.6"/>', 1.1))
    p.append(text(L1 + 38, B1 - 18, "placed stars", "hy-line", 1.1))

    # ---- population: the luminosity function
    L2, R2, T2, B2 = 650, 814, 100, 300
    p.append(text(598, 30, "POPULATION", "hy-head", 0.0))
    ln0, ln1 = math.log10(20.0), math.log10(60000.0)

    def px2(g: float) -> float:
        return L2 + (g - 10.5) / 8.0 * (R2 - L2)

    def py2(n: float) -> float:
        return B2 - (math.log10(n) - ln0) / (ln1 - ln0) * (B2 - T2)

    p.append(draw("hy-axis", f"M{L2} {T2} V{B2} H{R2}", 0.1, 0.4))
    for n, lab in ((100, "100"), (1000, "1k"), (10000, "10k")):
        y = py2(n)
        p.append(draw("hy-grid", f"M{L2} {f(y)} H{R2}", 0.15, 0.17))
        p.append(text(L2 - 6, y + 4, lab, "hy-num", 0.25, "end"))
    for g in (12, 14, 16, 18):
        x = px2(g)
        p.append(draw("hy-tick", f"M{f(x)} {B2} v5", 0.15, 0.17))
        p.append(text(x, B2 + 17, f"{g}", "hy-num", 0.25, "middle"))
    p.append(text(R2, B2 + 32, "G magnitude (Gaia)", "hy-lab", 0.3, "end"))
    p.append(pop(f'<g transform="translate({L2 - 44} {f((T2 + B2) / 2)}) rotate(-90)"><text class="hy-lab" text-anchor="middle">stars per 0.5 mag</text></g>', 0.3))
    for i, row in enumerate(lumfn):
        x0, x1 = px2(row["g_lo"]), px2(row["g_hi"])
        y = py2(row["n_stars"])
        p.append(pop(f'<rect class="hy-bar" x="{f(x0 + 1)}" y="{f(y)}" width="{f(x1 - x0 - 2)}" height="{f(B2 - y)}"/>', 0.6 + 0.04 * i))
    total = int(sum(r["n_stars"] for r in lumfn))
    p.append(text(598, 50, f"{total:,} stars", "hy-line", 1.2))
    p.append(text(598, 66, "TRILEGAL at 853,000", "hy-line", 1.25))
    p.append(tex(598 + 20 * 6.6 + 2, 66, r"M_\odot", 12, 1.25, "hy-tex-ink"))
    p.append(text(598, 82, "12.8 Gyr, [Fe/H] −0.63", "hy-line", 1.3))

    # threads: population to sky (sampling), sky to detector (the field feeds the noise model)
    yt = B1 - 12
    p.append(thread(f"M{L2} {yt} C{L2 - 40} {yt}, {R1 + 40} {yt}, {R1} {yt}", 0.8))
    p.append(node(L2, yt, 0.8))
    p.append(node(R1, yt, 0.85))
    p.append(thread(f"M{f(cx + R)} {f(cy)} C{f(cx + R + 36)} {f(cy)}, {L1 - 36} {yt}, {L1} {yt}", 0.9))
    p.append(node(cx + R, cy, 0.9))
    p.append(node(L1, yt, 0.95))

    # ---- the detector: pixel grid, point spread function, mask, neighbours
    L3, T3 = 836, 62
    g, n = 20, 10
    p.append(text(L3, 30, "DETECTOR", "hy-head", 0.0))
    for i in range(n + 1):
        p.append(draw("hy-grid", f"M{f(L3 + i * g)} {T3} v{n * g}", 0.2 + 0.01 * i, 0.15))
        p.append(draw("hy-grid", f"M{L3} {f(T3 + i * g)} h{n * g}", 0.2 + 0.01 * i, 0.15))
    p.append(draw("hy-axis", f"M{L3} {T3} h{n * g} v{n * g} h-{n * g} Z", 0.2, 0.4))
    sx, sy = L3 + 5.5 * g, T3 + 5.5 * g  # the target sits mid-pixel
    sigma = PSF_90_ARCSEC / 2 / PIXEL_ARCSEC / math.sqrt(2 * math.log(10)) * g  # 90 per cent of a Gaussian within 2.146 sigma
    for k, o in ((2.146, 0.10), (1.6, 0.22), (1.0, 0.45), (0.5, 0.85)):
        p.append(pop(f'<circle class="hy-psf" style="opacity:{o}" cx="{f(sx)}" cy="{f(sy)}" r="{f(k * sigma)}"/>', 0.6))
    r90 = 2.146 * sigma
    p.append(pop(f'<circle class="hy-ring-strong" cx="{f(sx)}" cy="{f(sy)}" r="{f(r90)}"/>', 0.7))
    # a six-pixel mask around the target (median mask size): the centre pixel, four neighbours and one more
    mx, my = L3 + 5 * g, T3 + 5 * g
    mask = (f"M{f(mx)} {f(my - g)} h{g} v{g} h{g} v{g} h-{g} v{g} h-{g} v-{g} h-{g} v-{g} h{g} Z")
    p.append(draw("hy-mask", mask, 0.8, 0.5))
    p.append(draw("hy-mask", f"M{f(mx + g)} {f(my + g)} h{g} v{g} h-{g} Z", 0.85, 0.3))
    for (dx, dy, sc, o) in ((2.4, -1.9, 0.8, 0.6), (-2.9, 2.3, 0.6, 0.5), (3.6, 2.8, 0.5, 0.4)):
        nx, ny = sx + dx * g, sy + dy * g
        for k, oo in ((2.146, 0.08 * o), (1.0, 0.35 * o), (0.5, 0.7 * o)):
            p.append(pop(f'<circle class="hy-psf-n" style="opacity:{oo}" cx="{f(nx)}" cy="{f(ny)}" r="{f(k * sigma * sc)}"/>', 0.9))
    p.append(draw("hy-leader", f"M{f(sx + r90 + 2)} {f(sy - r90 + 6)} L{f(L3 + n * g + 4)} {f(T3 + 36)} H{f(L3 + n * g + 10)}", 1.0, 0.3))
    p.append(text(L3 + n * g + 14, T3 + 32, "90 % energy", "hy-line", 1.05))
    p.append(text(L3 + n * g + 14, T3 + 46, "1.3 arcsec", "hy-line", 1.05))
    p.append(draw("hy-leader", f"M{f(mx + 2 * g)} {f(my + 1.5 * g)} L{f(L3 + n * g + 4)} {f(T3 + 110)} H{f(L3 + n * g + 10)}", 1.0, 0.3))
    p.append(text(L3 + n * g + 14, T3 + 106, "mask: 6 px", "hy-line", 1.05))
    p.append(text(L3 + n * g + 14, T3 + 120, "(3 to 13)", "hy-line", 1.05))
    p.append(text(L3 + n * g + 14, T3 + 160, "neighbours", "hy-line", 1.05))
    p.append(draw("hy-leader", f"M{f(sx + 2.4 * g + 0.8 * sigma)} {f(sy - 1.9 * g)} L{f(L3 + n * g + 4)} {f(T3 + 164)} H{f(L3 + n * g + 10)}", 1.0, 0.3))
    p.append(text(L3, T3 + n * g + 18, "0.5 arcsec per pixel", "hy-lab", 0.3))
    # scale bar of one arcsecond (two pixels)
    bx = L3 + n * g - 2 * g
    p.append(draw("hy-pic-strong", f"M{bx} {T3 + n * g + 10} h{2 * g} M{bx} {T3 + n * g + 6} v8 M{bx + 2 * g} {T3 + n * g + 6} v8", 0.4, 0.3))
    p.append(text(bx + g, T3 + n * g + 28, "1 arcsec", "hy-num", 0.4, "middle"))

    # ---- the two formulas and the term legend
    FY = 376
    p.append(draw("hy-rule", f"M20 {FY - 22} H{W - 20}", 0.2, 0.3))
    p.append(tex(20, FY + 8, r"\mathrm{NSR}_{\mathrm{tot}} = \sqrt{\textstyle\sum_{i=1}^{9} \sigma_i^{2}}", 14, 1.2))
    terms = ["shot", "contaminant shot", "readout", "background", "jitter", "contaminant jitter", "PRNU",
             "contaminant PRNU", "quantisation"]
    p.append(tex(20, FY + 40, r"\sigma_i:", 12, 1.3, "hy-tex-muted"))
    p.append(text(48, FY + 40, ", ".join(terms[:4]) + ",", "hy-line", 1.3))
    p.append(text(48, FY + 56, ", ".join(terms[4:]), "hy-line", 1.3))
    p.append(tex(20, FY + 96, r"\mathrm{SPR} = \dfrac{C}{S + C}", 14, 1.35))
    p.append(tex(150, FY + 96, r"S", 12, 1.4, "hy-tex-muted"))
    p.append(text(162, FY + 96, "target,", "hy-line", 1.4))
    p.append(tex(226, FY + 96, r"C", 12, 1.4, "hy-tex-muted"))
    p.append(text(239, FY + 96, "neighbours, inside the mask", "hy-line", 1.4))

    # ---- the worked example: medians of one magnitude bin as five bars
    EX, EY = 650, FY - 4
    p.append(text(EX, EY, "MEDIAN STAR, P 15.7 TO 16.0", "hy-head", 0.2))
    p.append(text(EX, EY + 16, f"{EXAMPLE['n']:,} stars", "hy-line", 0.25))
    bars = [("total", EXAMPLE["total"], "hy-ebar-total"), ("photon", EXAMPLE["photon"], ""), ("detector", EXAMPLE["detector"], ""),
            ("jitter", EXAMPLE["jitter"], ""), ("crowding", EXAMPLE["crowding"], "")]
    bx0, bx1 = EX + 80, 1040
    for i, (lab, v, cls) in enumerate(bars):
        y = EY + 42 + 24 * i
        wbar = (bx1 - bx0) * v / 430.0
        p.append(text(EX, y + 4, lab, "hy-line", 1.0 + 0.06 * i))
        p.append(pop(f'<rect class="hy-ebar {cls}" x="{bx0}" y="{y - 7}" width="{f(wbar)}" height="14"/>', 1.0 + 0.06 * i))
        p.append(text(bx0 + wbar + 8, y + 4, f"{v}", "hy-num", 1.05 + 0.06 * i))
    p.append(draw("hy-axis", f"M{bx0} {EY + 28} V{EY + 42 + 24 * 5 - 4}", 0.3, 0.3))
    p.append(text(bx1, EY + 42 + 24 * 5 + 10, "ppm per square root of an hour", "hy-lab", 0.4, "end"))
    sx2, sy2 = 1085, EY + 70
    p.append(pop(f'<circle class="hy-ring-strong" cx="{sx2}" cy="{sy2}" r="22"/><path class="hy-spr-wedge" d="M{sx2} {sy2} L{sx2} {sy2 - 22} A22 22 0 0 1 {f(sx2 + 22 * math.sin(2 * math.pi * EXAMPLE["spr"]))} {f(sy2 - 22 * math.cos(2 * math.pi * EXAMPLE["spr"]))} Z"/>', 1.3))
    p.append(text(sx2, sy2 + 40, f"SPR {EXAMPLE['spr']}", "hy-line", 1.35, "middle"))
    p.append(text(EX, EY + 42 + 24 * 5 + 30, "medians, not a quadrature sum", "hy-key", 1.4))
    return (
        f'<svg class="bp-svg hy-svg" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-labelledby="hy-ft hy-fd"><title id="hy-ft">How HAYDNsim builds a field: 47 Tucanae</title>'
        "<desc id=\"hy-fd\">Left: the one degree field as a circle with schematic star marks whose density follows the "
        "binned radial profile of the placed stars, the HST normalisation annulus at 50 to 100 arcsec, and the profile "
        "itself with a King model of the Harris 2010 shape. Middle: the luminosity function of the delivered TRILEGAL "
        "field, 91,629 stars in half-magnitude bins, with the mass, age and metallicity it was built at. Right: a pixel "
        "grid at 0.5 arcsec per pixel with one star's point spread function, its six-pixel mask and three neighbours "
        "whose light spills into the mask. Below: the noise-to-signal ratio as the quadrature sum of nine terms, the "
        "stellar pollution ratio, and the median noise terms of the stars between P 15.7 and 16.0.</desc>"
        + "".join(p) + "</svg>\n"
    )


# ------------------------------------------------------------------ figure 3: the 47 Tuc noise budget
def noise() -> str:
    rows = read_csv(NOISE)
    W, H = 1140, 440
    p: list[str] = []
    L, R, T, B = 66, 610, 50, 362
    g0, g1 = 9.9, 18.5
    n0, n1 = math.log10(0.3), math.log10(4000.0)

    def px(g: float) -> float:
        return L + (g - g0) / (g1 - g0) * (R - L)

    def py(v: float) -> float:
        return B - (math.log10(v) - n0) / (n1 - n0) * (B - T)

    p.append(text(L, 24, "47 TUCANAE, NOISE BUDGET PER STAR", "hy-head", 0.0))
    p.append(text(L, 40, "median per 0.3 mag bin in P, from 91,350 stars; four terms and their total", "hy-line", 0.05))
    for v in (1, 3, 10, 30, 100, 300, 1000, 3000):
        y = py(v)
        p.append(draw("hy-grid", f"M{L} {f(y)} H{R}", 0.1, 0.17))
        p.append(text(L - 8, y + 4, f"{v:,}".replace(",", " "), "hy-num", 0.2, "end"))
    for g in (10, 12, 14, 16, 18):
        x = px(g)
        p.append(draw("hy-tick", f"M{f(x)} {B} v5", 0.15, 0.17))
        p.append(text(x, B + 18, f"{g}", "hy-num", 0.2, "middle"))
    p.append(draw("hy-axis", f"M{L} {T} V{B} H{R}", 0.05, 0.3))
    p.append(text(R, B + 34, "P magnitude (PLATO band)", "hy-lab", 0.3, "end"))
    unit, uw = tex_glyphs(r"\mathrm{ppm}\;\mathrm{hr}^{-1/2}", 12)
    p.append(pop(f'<g transform="translate(22 {f((T + B) / 2)}) rotate(-90)"><text class="hy-lab" x="-6" y="0" text-anchor="end">'
                 f'median noise-to-signal ratio,</text><g class="hy-tex" transform="translate(0 0)">{unit}</g></g>', 0.3))
    terms = [("median_crowding", "crowding", "--cat-2"), ("median_photon", "photon", "--cat-1"),
             ("median_detector", "detector", "--cat-4"), ("median_target_jitter", "target jitter", "--cat-9")]
    t = 0.5
    for key, label, var in terms:
        pts = [(px(r["p_bin_centre_mag"]), py(r[key])) for r in rows]
        d = "M" + " L".join(f"{f(a)} {f(b)}" for a, b in pts)
        p.append(f'<path class="hy-curve b-draw" style="--d:{t:.2f}s;--dur:.8s;stroke:var({var})" pathLength="1" d="{d}"/>')
        marks = "".join(f'<circle cx="{f(a)}" cy="{f(b)}" r="2.4"/>' for a, b in pts)
        p.append(pop(f'<g class="hy-marks" style="fill:var({var})">{marks}</g>', t + 0.6))
        t += 0.15
    pts = [(px(r["p_bin_centre_mag"]), py(r["median_total_nsr_ppm_sqrt_hr"])) for r in rows]
    d = "M" + " L".join(f"{f(a)} {f(b)}" for a, b in pts)
    p.append(draw("hy-total", d, t, 0.9))
    p.append(pop('<g class="hy-marks hy-marks-total">' + "".join(f'<circle cx="{f(a)}" cy="{f(b)}" r="2.8"/>' for a, b in pts) + "</g>", t + 0.7))
    lx, ly = L + 22, T + 26
    items = [("total", "hy-total", None)] + [(lab, "hy-curve", var) for _, lab, var in terms]
    for i, (lab, cls, var) in enumerate(items):
        y = ly + 18 * i
        style = f' style="stroke:var({var})"' if var else ""
        p.append(pop(f'<path class="{cls}"{style} d="M{lx} {y - 4} h22"/>', 1.4))
        p.append(text(lx + 30, y, lab, "hy-line", 1.4))
    L2, R2, T2, B2 = 690, 1100, 50, 180

    def px2(g: float) -> float:
        return L2 + (g - g0) / (g1 - g0) * (R2 - L2)

    def py2(v: float) -> float:
        return B2 - v / 0.5 * (B2 - T2)

    p.append(text(L2, 24, "STELLAR POLLUTION RATIO, 47 TUCANAE", "hy-head", 0.0))
    p.append(text(L2, 40, "median share of each star's light that comes from its neighbours", "hy-line", 0.05))
    for v in (0.0, 0.25, 0.5):
        y = py2(v)
        p.append(draw("hy-grid", f"M{L2} {f(y)} H{R2}", 0.1, 0.17))
        p.append(text(L2 - 8, y + 4, f"{v:g}", "hy-num", 0.2, "end"))
    p.append(draw("hy-axis", f"M{L2} {T2} V{B2} H{R2}", 0.05, 0.3))
    for g in (10, 12, 14, 16, 18):
        x = px2(g)
        p.append(draw("hy-tick", f"M{f(x)} {B2} v5", 0.15, 0.17))
        p.append(text(x, B2 + 18, f"{g}", "hy-num", 0.2, "middle"))
    p.append(text(R2, B2 + 34, "P magnitude (PLATO band)", "hy-lab", 0.3, "end"))
    p.append(pop(f'<path class="hy-limit" d="M{L2} {f(py2(0.5))} H{R2}"/>', 0.4))
    p.append(text(R2 - 6, py2(0.5) + 15, "SPR = 0.5: HALF THE LIGHT IS NOT THE STAR'S", "hy-key", 0.45, "end"))
    pts = [(px2(r["p_bin_centre_mag"]), py2(r["median_spr"])) for r in rows]
    d = "M" + " L".join(f"{f(a)} {f(b)}" for a, b in pts)
    p.append(f'<path class="hy-curve b-draw" style="--d:1.2s;--dur:.8s;stroke:var(--cat-6)" pathLength="1" d="{d}"/>')
    p.append(pop('<g class="hy-marks" style="fill:var(--cat-6)">' + "".join(f'<circle cx="{f(a)}" cy="{f(b)}" r="2.6"/>' for a, b in pts) + "</g>", 1.9))
    T3 = 236
    p.append(text(L2, T3, "STARS WITH SPR ABOVE 0.5, PER CLUSTER", "hy-head", 0.0))
    p.append(text(L2, T3 + 16, "share of each cluster's stars whose light is mostly from neighbours (poster)", "hy-line", 0.05))
    bx0, bx1 = L2 + 92, R2 - 44
    omega, ow = tex_glyphs(r"\omega", 12)
    for i, (name, pc) in enumerate(FRACTIONS):
        y = T3 + 44 + 22 * i
        t = 1.0 + 0.08 * i
        if name.startswith("omega"):
            p.append(pop(f'<g class="hy-tex-ink" transform="translate({L2} {y})">{omega}</g>', t))
            p.append(text(L2 + ow + 3, y, "Cen", "hy-line", t))
        else:
            p.append(text(L2, y, name, "hy-line", t))
        wbar = (bx1 - bx0) * pc / 40.0
        p.append(pop(f'<rect class="hy-bar" x="{bx0}" y="{y - 11}" width="{f(wbar)}" height="14"/>', t))
        p.append(text(bx0 + wbar + 8, y, f"{pc} %", "hy-num", t + 0.05))
    p.append(draw("hy-axis", f"M{bx0} {T3 + 28} V{T3 + 44 + 22 * 7 - 4}", 0.3, 0.3))
    p.append(text(L, H - 10, "FILLED MARKS AND BARS ARE DATA. NOISE IN PPM PER SQUARE ROOT OF AN HOUR, LOG AXIS.", "hy-head", 0.2))
    return (
        f'<svg class="bp-svg hy-svg" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-labelledby="hy-nt hy-nd"><title id="hy-nt">The 47 Tucanae noise budget from HAYDNsim</title>'
        "<desc id=\"hy-nd\">Left: the median photometric noise per star against PLATO P magnitude in 47 Tucanae, split into "
        "photon, detector, target-jitter and crowding terms, with their total; crowding is the largest term for stars "
        "fainter than about 14th magnitude. Top right: the median stellar pollution ratio against magnitude, rising "
        "towards 0.37 at 18th magnitude. Bottom right: the share of stars whose light is mostly from neighbours, for "
        "seven clusters, from 40 per cent in 47 Tucanae to 3 per cent in M4.</desc>"
        + "".join(p) + "</svg>\n"
    )


def main() -> None:
    OUT.joinpath("haydn-pipeline.svg").write_text(pipeline())
    OUT.joinpath("haydn-field.svg").write_text(field())
    OUT.joinpath("haydn-noise.svg").write_text(noise())
    for n in ("haydn-pipeline.svg", "haydn-field.svg", "haydn-noise.svg"):
        print(f"wrote {OUT / n} ({OUT.joinpath(n).stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
