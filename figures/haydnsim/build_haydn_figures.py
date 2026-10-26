"""Build the two HAYDNsim figures for the field-guide page on HAYDN.

haydn-pipeline.svg  The HAYDNsim stages, after the flowchart on the TASC10/KASC17 poster
                    (Neitzel et al. 2026, doi:10.5281/zenodo.23263454) and slide 6 of the DFA Week
                    2026 talk; instrument figures from slide 2 of that talk. Outline means schematic.
haydn-noise.svg     Real data: the 47 Tucanae noise budget, binned medians from the HAYDN Noise
                    Estimator output (assets/data/haydnsim/47tuc_noise_budget_binned.csv, with its
                    provenance file), and the public per-cluster fractions of stars whose light is
                    mostly from neighbours (SPR > 0.5), read from the poster. Filled marks mean data.

Usage: python3 figures/haydnsim/build_haydn_figures.py
Needs latex and dvisvgm on the path for the few typeset symbols (figures/texsvg.py).
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
DATA = ROOT / "assets/data/haydnsim/47tuc_noise_budget_binned.csv"

# public per-cluster fractions of stars with SPR > 0.5, poster bar chart (per cent)
FRACTIONS = [("47 Tuc", 40), ("NGC 6752", 36), ("M54", 36), ("M22", 12), ("omega Cen", 11), ("NGC 6397", 7), ("M4", 3)]


def f(v: float) -> str:
    return f"{v:.1f}"


def draw(cls: str, d: str, t: float, dur: float = 0.5) -> str:
    return f'<path class="{cls} b-draw" style="--d:{t:.2f}s;--dur:{dur:.2f}s" pathLength="1" d="{d}"/>'


def pop(inner: str, t: float) -> str:
    return f'<g class="b-pop" style="--d:{t:.2f}s">{inner}</g>'


def text(x: float, y: float, s: str, cls: str, t: float, anchor: str = "start", extra: str = "") -> str:
    return f'<text class="{cls} b-pop" style="--d:{t:.2f}s" x="{f(x)}" y="{f(y)}" text-anchor="{anchor}"{extra}>{s}</text>'


def node(x: float, y: float, t: float, k: float = 6.0) -> str:
    return pop(f'<rect class="hy-node" x="{f(x - k / 2)}" y="{f(y - k / 2)}" width="{f(k)}" height="{f(k)}"/>', t)


def thread(d: str, t: float, cls: str = "ray flowray hy-thread") -> str:
    return pop(f'<path class="{cls}" d="{d}"/>', t)


# ------------------------------------------------------------------ figure 1: the pipeline
def pipeline() -> str:
    W, H = 1140, 378
    p: list[str] = []
    # instrument strip (public: DFA Week 2026 talk, slide 2)
    p.append(text(20, 30, "HAYDN, AS PROPOSED", "hy-head", 0.0))
    facts = [("aperture", "1.2 m"), ("field of view", "1 degree"), ("plate scale", "0.5 arcsec per pixel"),
             ("targets", "to G = 17"), ("candidate clusters", "27")]
    x = 190
    for k, v in facts:
        p.append(text(x, 30, k.upper(), "hy-key", 0.1))
        p.append(text(x, 46, v, "hy-val", 0.15))
        x += 185
    p.append(draw("hy-rule", f"M20 60 H{W - 20}", 0.1, 0.3))
    # stages
    y0, h, w = 92, 170, 172
    xs = [20 + i * 186 for i in range(6)]
    stages = [
        ("1  ARCHIVE DATA", ["Gaia DR3 cone, G to 18.5", "HST ACS, cluster core", "Harris 2010", "Baumgardt+Hilker 2018",
                             "Hunt+Reffert 2024", "Forbes+Bridges 2010"]),
        ("2  THRESHOLD, MEMBERS", ["bright-star limit where", "Gaia (outskirts) and", "HST (core) are both", "complete;",
                                    "members selected"]),
        ("3  KING PROFILE", ["normalised to HST in", "the 50 to 100 arcsec", "annulus; checked", "against Gaia counts"]),
        ("4  TRILEGAL FIELD", ["mass-calibrated to the", "present-day mass and", "bright-star counts;", "placed on the sky by",
                                     "inverse-CDF sampling"]),
        ("5  HNE ON DEUCALION", ["HAYDN Noise Estimator", "(R. Samadi): per-star", "NSR, with the light of", "every neighbour,",
                                  "and the SPR"]),
        ("6  SEISMIC MODEL", ["model of Mosser et al.", "2019: per-star noise", "becomes detectability", "(no numbers here)"]),
    ]
    for i, (title, lines) in enumerate(stages):
        x = xs[i]
        t = 0.2 + 0.12 * i
        p.append(draw("hy-box", f"M{x} {y0} h{w} v{h} h-{w} Z", t, 0.4))
        p.append(text(x + 10, y0 + 22, title, "hy-title", t + 0.1))
        p.append(draw("hy-rule", f"M{x + 10} {y0 + 32} h{w - 20}", t + 0.1, 0.2))
        for j, line in enumerate(lines):
            p.append(text(x + 10, y0 + 52 + 16 * j, line, "hy-line", t + 0.15 + 0.03 * j))
    # the HNE box owns the PSF, aperture and crowding treatment: an inner outlined box
    x5 = xs[4]
    p.append(draw("hy-inner", f"M{x5 + 10} {y0 + 126} h{w - 20} v36 h-{w - 20} Z", 0.9, 0.3))
    p.append(text(x5 + 16, y0 + 141, "INSIDE HNE: PSF,", "hy-key", 1.0))
    p.append(text(x5 + 16, y0 + 155, "aperture, crowding", "hy-line", 1.0))
    # the thread: box to box, gently curved, with a square node at each hand-off
    ym = y0 + h / 2
    for i in range(5):
        xa, xb = xs[i] + w, xs[i + 1]
        t = 0.35 + 0.12 * i
        p.append(thread(f"M{xa} {f(ym)} C{xa + 5} {f(ym - 7)}, {xb - 5} {f(ym + 7)}, {xb} {f(ym)}", t))
        p.append(node(xa, ym, t))
        p.append(node(xb, ym, t + 0.05))
    # output after stage 6
    xe = xs[5] + w
    p.append(thread(f"M{xe} {f(ym)} C{xe + 8} {f(ym)}, {xe + 8} {f(ym)}, {W - 4} {f(ym)}", 1.0))
    p.append(node(xe, ym, 1.0))
    # the bypass: open clusters and resolved fields skip stages 3 and 4
    yb = y0 + h + 40
    xa = xs[1] + w / 2
    xb = xs[4] + w / 2
    d = (f"M{f(xa)} {y0 + h} C{f(xa)} {y0 + h + 30}, {f(xa + 20)} {yb}, {f(xa + 40)} {yb} "
         f"H{f(xb - 40)} C{f(xb - 20)} {yb}, {f(xb)} {y0 + h + 30}, {f(xb)} {y0 + h}")
    p.append(thread(d, 1.05, "ray flowray hy-bypass"))
    p.append(node(xa, y0 + h, 1.05))
    p.append(node(xb, y0 + h, 1.1))
    p.append(text((xa + xb) / 2, yb + 18, "open clusters and resolved fields skip the profile and the population steps",
                  "hy-line", 1.15, "middle"))
    p.append(text(20, H - 10, "SCHEMATIC, AFTER THE POSTER FLOWCHART AND THE DFA WEEK 2026 TALK. OUTLINE MEANS SCHEMATIC.",
                  "hy-head", 0.2))
    return (
        f'<svg class="bp-svg hy-svg" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-labelledby="hy-pt hy-pd"><title id="hy-pt">The HAYDNsim pipeline, in six stages</title>'
        "<desc id=\"hy-pd\">Archive data from Gaia DR3, HST and four catalogues; a bright-star threshold and membership "
        "selection; a King profile normalised to HST; a TRILEGAL population placed by inverse-CDF sampling; the HAYDN Noise "
        "Estimator run on Deucalion, which returns a noise-to-signal ratio and a stellar pollution ratio per star; and a "
        "seismic performance model. Open clusters and resolved fields skip the profile and population steps.</desc>"
        + "".join(p) + "</svg>\n"
    )


# ------------------------------------------------------------------ figure 2: the 47 Tuc noise budget
def read_rows() -> list[dict[str, float]]:
    rows = []
    with DATA.open() as fh:
        for r in csv.DictReader(line for line in fh if not line.startswith("#")):
            rows.append({k: float(v) for k, v in r.items()})
    return rows


def noise() -> str:
    rows = read_rows()
    W, H = 1140, 440
    p: list[str] = []
    # left panel: the noise budget on a log axis
    L, R, T, B = 66, 610, 50, 362
    g0, g1 = 9.9, 18.5
    n0, n1 = math.log10(0.3), math.log10(4000.0)

    def px(g: float) -> float:
        return L + (g - g0) / (g1 - g0) * (R - L)

    def py(v: float) -> float:
        return B - (math.log10(v) - n0) / (n1 - n0) * (B - T)

    p.append(text(L, 24, "47 TUCANAE, NOISE BUDGET PER STAR", "hy-head", 0.0))
    p.append(text(L, 40, "median per 0.3 mag bin in G, from 91,350 stars; four terms and their total", "hy-line", 0.05))
    for v in (1, 3, 10, 30, 100, 300, 1000, 3000):
        y = py(v)
        p.append(draw("hy-grid", f"M{L} {f(y)} H{R}", 0.1, 0.17))
        p.append(text(L - 8, y + 4, f"{v:,}".replace(",", " "), "hy-num", 0.2, "end"))
    for g in (10, 12, 14, 16, 18):
        x = px(g)
        p.append(draw("hy-tick", f"M{f(x)} {B} v5", 0.15, 0.17))
        p.append(text(x, B + 18, f"{g}", "hy-num", 0.2, "middle"))
    p.append(draw("hy-axis", f"M{L} {T} V{B} H{R}", 0.05, 0.3))
    p.append(text(R, B + 34, "G magnitude (Gaia)", "hy-lab", 0.3, "end"))
    unit, uw = tex_glyphs(r"\mathrm{ppm}\;\mathrm{hr}^{-1/2}", 12)
    p.append(pop(f'<g transform="translate(22 {f((T + B) / 2)}) rotate(-90)"><text class="hy-lab" x="-6" y="0" text-anchor="end">'
                 f'median noise-to-signal ratio,</text><g class="hy-tex" transform="translate(0 0)">{unit}</g></g>', 0.3))
    terms = [("median_crowding", "crowding", "--cat-2"), ("median_photon", "photon", "--cat-1"),
             ("median_detector", "detector", "--cat-4"), ("median_target_jitter", "target jitter", "--cat-9")]
    t = 0.5
    for key, label, var in terms:
        pts = [(px(r["g_bin_centre_mag"]), py(r[key])) for r in rows]
        d = "M" + " L".join(f"{f(a)} {f(b)}" for a, b in pts)
        p.append(f'<path class="hy-curve b-draw" style="--d:{t:.2f}s;--dur:.8s;stroke:var({var})" pathLength="1" d="{d}"/>')
        marks = "".join(f'<circle cx="{f(a)}" cy="{f(b)}" r="2.4"/>' for a, b in pts)
        p.append(pop(f'<g class="hy-marks" style="fill:var({var})">{marks}</g>', t + 0.6))
        t += 0.15
    pts = [(px(r["g_bin_centre_mag"]), py(r["median_total_nsr_ppm_sqrt_hr"])) for r in rows]
    d = "M" + " L".join(f"{f(a)} {f(b)}" for a, b in pts)
    p.append(draw("hy-total", d, t, 0.9))
    p.append(pop('<g class="hy-marks hy-marks-total">' + "".join(f'<circle cx="{f(a)}" cy="{f(b)}" r="2.8"/>' for a, b in pts) + "</g>", t + 0.7))
    # legend in the empty upper-left corner
    lx, ly = L + 22, T + 26
    items = [("total", "hy-total", None)] + [(lab, "hy-curve", var) for _, lab, var in terms]
    for i, (lab, cls, var) in enumerate(items):
        y = ly + 18 * i
        style = f' style="stroke:var({var})"' if var else ""
        p.append(pop(f'<path class="{cls}"{style} d="M{lx} {y - 4} h22"/>', 1.4))
        p.append(text(lx + 30, y, lab, "hy-line", 1.4))
    # top right: the stellar pollution ratio
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
    p.append(text(R2, B2 + 34, "G magnitude (Gaia)", "hy-lab", 0.3, "end"))
    p.append(pop(f'<path class="hy-limit" d="M{L2} {f(py2(0.5))} H{R2}"/>', 0.4))
    p.append(text(R2 - 6, py2(0.5) + 15, "SPR = 0.5: HALF THE LIGHT IS NOT THE STAR'S", "hy-key", 0.45, "end"))
    pts = [(px2(r["g_bin_centre_mag"]), py2(r["median_spr"])) for r in rows]
    d = "M" + " L".join(f"{f(a)} {f(b)}" for a, b in pts)
    p.append(f'<path class="hy-curve b-draw" style="--d:1.2s;--dur:.8s;stroke:var(--cat-6)" pathLength="1" d="{d}"/>')
    p.append(pop('<g class="hy-marks" style="fill:var(--cat-6)">' + "".join(f'<circle cx="{f(a)}" cy="{f(b)}" r="2.6"/>' for a, b in pts) + "</g>", 1.9))
    # bottom right: the public per-cluster fractions
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
        "<desc id=\"hy-nd\">Left: the median photometric noise per star against Gaia G magnitude in 47 Tucanae, split into "
        "photon, detector, target-jitter and crowding terms, with their total; crowding dominates for stars fainter than "
        "about 14th magnitude. Top right: the median stellar pollution ratio against magnitude, rising towards 0.37 at "
        "18th magnitude. Bottom right: the share of stars whose light is mostly from neighbours, for seven clusters, from "
        "40 per cent in 47 Tucanae to 3 per cent in M4.</desc>"
        + "".join(p) + "</svg>\n"
    )


def main() -> None:
    OUT.joinpath("haydn-pipeline.svg").write_text(pipeline())
    OUT.joinpath("haydn-noise.svg").write_text(noise())
    for n in ("haydn-pipeline.svg", "haydn-noise.svg"):
        print(f"wrote {OUT / n} ({OUT.joinpath(n).stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
