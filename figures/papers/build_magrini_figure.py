"""Draw the Kiel diagram of the 187 Ariel host stars of Magrini et al. 2022 from the paper's own table.

Usage: python3 figures/papers/build_magrini_figure.py
Reads assets/data/papers/magrini2022/tables.json (table A.1 and A.2 of the paper, from the CDS
catalogue J/A+A/663/A161; see provenance.json beside it) and writes _includes/figures/magrini-2022.svg.

Every mark is one star at its measured effective temperature and surface gravity, with the table's
error bars, sized by the table's mass and shaded by [Fe/H]. The thin-disc against thick-disc styling
applies the paper's own first-approximation rule (Sect. 6.2) to table A.2: the peculiar velocity
v_pec = sqrt(U^2 + V_LSR^2 + W^2), with V_LSR = V - 220 km/s because the table's V is the rotational
component and the paper sets the local standard of rest at 220 km/s; v_pec < 50 km/s thin disc,
70 to 200 km/s thick disc, 50 to 70 km/s either. Qatar-8 has no orbit row and is drawn unclassed.
The Sun is drawn at its nominal values (IAU 2015 Resolution B3: 5772 K, log g 4.438) for reference.
Colours are CSS custom properties (assets/css/kiel.css); the figure builds once on first view.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "figures"))
from texsvg import tex_glyphs  # noqa: E402  (LaTeX glyphs for the symbols)

W, H = 760, 450
L_, R_, T_, B_ = 62, 22, 24, 54
TX0, TX1 = 7400.0, 4000.0  # Teff, hotter to the left
GY0, GY1 = 3.72, 4.78  # log g, low gravity at the top
V_LSR = 220.0  # km/s, the paper's local standard of rest (Sect. 6.2)
SUN = (5772.0, 4.438)  # IAU 2015 nominal solar values
MASS_LO, MASS_HI = 0.62, 1.74  # the table's range (checked below)
FE_EDGES = [-0.6, -0.4, -0.2, 0.0, 0.2, 0.4, 0.6]


def px(teff: float) -> float:
    return L_ + (TX0 - teff) / (TX0 - TX1) * (W - L_ - R_)


def py(logg: float) -> float:
    return T_ + (logg - GY0) / (GY1 - GY0) * (H - T_ - B_)


def f(v: float) -> str:
    return f"{v:.1f}"


def run(parts, cls, size, anchor="start"):
    """Set a label made of mono text and LaTeX glyphs from its left end; returns (svg, width)."""
    adv = 0.6 * size  # Geist Mono advance
    cur, out = 0.0, []
    for kind, seg in parts:
        if kind == "text":
            out.append(f'<text class="{cls}" x="{cur:.1f}" y="0" style="white-space:pre">{seg}</text>')
            cur += len(seg) * adv
        else:
            body, w = tex_glyphs(seg, size * 1.1)
            out.append(f'<g class="{cls}-tex" transform="translate({cur + 0.5:.1f} 0)">{body}</g>')
            cur += w + 1.5
    shift = {"start": 0.0, "middle": -cur / 2, "end": -cur}[anchor]
    return f'<g transform="translate({shift:.1f} 0)">{"".join(out)}</g>', cur


def radius(mass: float) -> float:
    return 2.3 + (mass - MASS_LO) / (MASS_HI - MASS_LO) * 3.2


def fe_bin(fe: float) -> int:
    for i in range(len(FE_EDGES) - 1):
        if fe < FE_EDGES[i + 1]:
            return i
    return len(FE_EDGES) - 2


def main() -> int:
    data = json.loads((ROOT / "assets/data/papers/magrini2022/tables.json").read_text())
    a1 = data["tablea1"]["rows"]
    a2 = {r["ID"]: r for r in data["tablea2"]["rows"]}
    masses = [r["Mass"] for r in a1]
    assert min(masses) >= MASS_LO and max(masses) <= MASS_HI, (min(masses), max(masses))
    fes = [r["[Fe/H]"] for r in a1]
    assert min(fes) >= FE_EDGES[0] and max(fes) < FE_EDGES[-1], (min(fes), max(fes))

    def vclass(r):
        o = a2.get(r["ID"])
        if o is None:
            return "none", None
        v = math.sqrt(o["U"] ** 2 + (o["V"] - V_LSR) ** 2 + o["W"] ** 2)
        if v < 50:
            return "thin", v
        if 70 <= v <= 200:
            return "thick", v
        if 50 <= v < 70:
            return "mid", v
        return "beyond", v

    counts = {"thin": 0, "thick": 0, "mid": 0, "none": 0, "beyond": 0}
    p: list[str] = []
    # axes and ticks (outline = schematic)
    p.append(f'<path class="k-axis b-draw" style="--d:0s;--dur:.3s" pathLength="1" d="M{L_} {T_} V{H - B_} H{W - R_}"/>')
    for teff in (7000, 6500, 6000, 5500, 5000, 4500):
        x = px(teff)
        p.append(f'<path class="k-tick" d="M{f(x)} {H - B_} v4"/>'
                 f'<text class="k-num" x="{f(x)}" y="{H - B_ + 16}" text-anchor="middle">{teff}</text>')
    for g in (3.8, 4.0, 4.2, 4.4, 4.6):
        y = py(g)
        p.append(f'<path class="k-tick" d="M{L_ - 4} {f(y)} h4"/>'
                 f'<text class="k-num" x="{L_ - 7}" y="{f(y + 4)}" text-anchor="end">{g:.1f}</text>')
    gx, _ = run([("tex", r"T_\mathrm{eff}"), ("text", " (K), hotter to the left")], "k-lab", 11, "end")
    p.append(f'<g transform="translate({W - R_} {H - 8})">{gx}</g>')
    gy, _ = run([("tex", r"\log g"), ("text", " (cgs), low gravity at the top")], "k-lab", 11, "end")
    p.append(f'<g transform="translate(16 {T_}) rotate(-90)">{gy}</g>')
    # construction: the Sun's nominal values as hairlines to both axes, and the Sun symbol
    sx, sy = px(SUN[0]), py(SUN[1])
    p.append(f'<path class="k-guide b-draw" style="--d:.2s;--dur:.17s" pathLength="1" d="M{f(sx)} {H - B_} V{f(sy)} H{L_}"/>')
    p.append(f'<g class="b-pop" style="--d:.4s"><circle class="k-sun" cx="{f(sx)}" cy="{f(sy)}" r="5.5"/>'
             f'<circle class="k-sun-dot" cx="{f(sx)}" cy="{f(sy)}" r="1.4"/></g>')
    p.append(f'<text class="k-note b-pop" style="--d:.45s" x="{L_ + 8}" y="{f(sy - 5)}">Sun, nominal values</text>')
    # the stars: error bars faint, marks filled (thin disc) or outline (thick disc), by Teff order
    order = sorted(a1, key=lambda r: -r["Teff"])
    for r in order:
        cls, v = vclass(r)
        counts[cls] += 1
        x, y = px(r["Teff"]), py(r["logg"])
        t = 0.55 + 1.3 * (TX0 - r["Teff"]) / (TX0 - TX1)
        ex = (px(r["Teff"] - r["e_Teff"]), px(r["Teff"] + r["e_Teff"]))
        ey = (py(r["logg"] - r["e_logg"]), py(r["logg"] + r["e_logg"]))
        rad = radius(r["Mass"])
        bin_ = fe_bin(r["[Fe/H]"])
        title = (f'{r["ID"]}: {r["Teff"]} ± {r["e_Teff"]} K, log g {r["logg"]:.2f} ± {r["e_logg"]:.2f}, '
                 f'[Fe/H] {r["[Fe/H]"]:+.2f}, {r["Mass"]:.2f} solar masses'
                 + (f', v_pec {v:.0f} km/s' if v is not None else ', no orbit in table A.2'))
        p.append(f'<g class="k-star b-pop" style="--d:{t:.2f}s">'
                 f'<path class="k-err" d="M{f(ex[0])} {f(y)} H{f(ex[1])} M{f(x)} {f(ey[0])} V{f(ey[1])}"/>')
        if cls == "none":
            p.append(f'<path class="k-none fe-{bin_}" d="M{f(x - rad)} {f(y - rad)} L{f(x + rad)} {f(y + rad)} '
                     f'M{f(x - rad)} {f(y + rad)} L{f(x + rad)} {f(y - rad)}"/>')
        else:
            p.append(f'<circle class="k-pt k-{cls} fe-{bin_}" cx="{f(x)}" cy="{f(y)}" r="{f(rad)}"/>')
            if cls == "mid":
                p.append(f'<circle class="k-pt-dot fe-{bin_}" cx="{f(x)}" cy="{f(y)}" r="1.1"/>')
        p.append(f"<title>{title}</title></g>")
    assert counts["beyond"] == 0, counts
    # keys, stacked in the empty cool, low-gravity corner of a dwarf Kiel diagram
    kx, ky = W - R_ - 252, T_ + 14
    k: list[str] = [f'<text class="k-key-h" x="{kx}" y="{ky}">[Fe/H], dex</text>']
    for i in range(6):
        k.append(f'<rect class="k-swatch fe-{i}" x="{kx + i * 30}" y="{ky + 8}" width="26" height="9"/>')
    for i, e in enumerate(FE_EDGES):
        if i % 2 == 0:
            k.append(f'<text class="k-num" x="{kx + i * 30}" y="{ky + 30}" text-anchor="middle">{e:+.1f}</text>')
    k.append(f'<text class="k-key-h" x="{kx}" y="{ky + 54}">mass</text>')
    cx = kx + 6
    for m in (0.7, 1.0, 1.5):
        rad = radius(m)
        k.append(f'<circle class="k-key-pt" cx="{f(cx + rad)}" cy="{f(ky + 68)}" r="{f(rad)}"/>')
        g, w = run([("text", f"{m:.1f} "), ("tex", r"M_\odot")], "k-num", 11)
        k.append(f'<g transform="translate({f(cx + 2 * rad + 5)} {f(ky + 72)})">{g}</g>')
        cx += 2 * rad + 5 + w + 12
    p.append(f'<g class="b-pop" style="--d:1.95s">{"".join(k)}</g>')
    sx0, sy0 = kx, ky + 100
    s: list[str] = [f'<text class="k-key-h" x="{sx0}" y="{sy0}">disc, by the paper\'s rule</text>']
    rows = (
        ("thin", f'thin: v below 50 km/s ({counts["thin"]})'),
        ("mid", f'either: 50 to 70 km/s ({counts["mid"]})'),
        ("thick", f'thick: 70 to 200 km/s ({counts["thick"]})'),
        ("none", f'no orbit in table A.2 ({counts["none"]})'),
    )
    for i, (cls, lab) in enumerate(rows):
        y = sy0 + 16 + i * 17
        if cls == "none":
            s.append(f'<path class="k-none fe-3" d="M{sx0 + 2} {y - 7} L{sx0 + 10} {y + 1} M{sx0 + 2} {y + 1} L{sx0 + 10} {y - 7}"/>')
        else:
            s.append(f'<circle class="k-pt k-{cls} fe-3" cx="{sx0 + 6}" cy="{y - 3}" r="4"/>')
            if cls == "mid":
                s.append(f'<circle class="k-pt-dot fe-3" cx="{sx0 + 6}" cy="{y - 3}" r="1.1"/>')
        s.append(f'<text class="k-num" x="{sx0 + 18}" y="{y}">{lab}</text>')
    p.append(f'<g class="b-pop" style="--d:2.05s">{"".join(s)}</g>')
    p.append(f'<text class="k-note b-pop" style="--d:.1s" x="{L_ + 10}" y="{T_ + 16}">{len(a1)} planet hosts, table A.1</text>')

    svg = (
        f'<svg class="kiel-svg" data-build viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-labelledby="kiel-t kiel-d"><title id="kiel-t">Kiel diagram of the 187 Ariel host stars of Magrini et al. 2022</title>'
        '<desc id="kiel-d">Surface gravity against effective temperature for the 187 F, G and K planet hosts of table A.1, '
        'each with its error bars, sized by mass and shaded by iron abundance. Filled marks are thin-disc stars and open marks '
        f'thick-disc stars by the paper\'s peculiar-velocity rule: {counts["thin"]} thin disc, {counts["thick"]} thick disc, '
        f'{counts["mid"]} in between and one without an orbit. The main sequence runs from the hot, low-gravity corner at the '
        'upper left to the cool, high-gravity corner at the lower right, with the Sun marked for reference.</desc>'
        + "".join(p) + "</svg>\n"
    )
    out = ROOT / "_includes/figures/magrini-2022.svg"
    out.write_text(svg)
    print(f"wrote {out} ({len(svg) / 1024:.1f} KB); stars {len(a1)}; classes {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
