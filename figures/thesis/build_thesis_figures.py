"""Figures for the MSc dissertation explainer (/papers/neitzel-2022-msc-thesis/).

1. thesis-method.svg: the method chain of the dissertation as a blueprint schematic: observed
   inputs on the left, the model side on top, PARAM in the middle, outputs on the right, joined by
   one flowing thread. Everything in it is schematic (outline).
2. thesis-results.svg: the dissertation's own numbers (filled marks): median relative uncertainty of
   age and mass for the ten Ariel input catalogue stars under each constraint set, with the
   as-published input uncertainties (Table 6.8) and the inflated ones (Table 6.18), read from
   assets/data/papers/thesis2022/constraint_sets.json.

Usage: python3 figures/thesis/build_thesis_figures.py
Symbols are set in LaTeX through figures/texsvg.py.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "figures"))
from texsvg import tex_glyphs  # noqa: E402

DATA = json.loads((ROOT / "assets/data/papers/thesis2022/constraint_sets.json").read_text())


def f(v: float) -> str:
    return f"{v:.1f}"


def draw(cls: str, d: str, t: float, dur: float = 0.5) -> str:
    return f'<path class="{cls} b-draw" style="--d:{t:.2f}s;--dur:{dur:.2f}s" pathLength="1" d="{d}"/>'


def pop(inner: str, t: float) -> str:
    return f'<g class="b-pop" style="--d:{t:.2f}s">{inner}</g>'


def text(x: float, y: float, s: str, cls: str, t: float, anchor: str = "start") -> str:
    return f'<text class="{cls} b-pop" style="--d:{t:.2f}s" x="{f(x)}" y="{f(y)}" text-anchor="{anchor}">{s}</text>'


def run(parts, cls: str, size: float, anchor: str = "start") -> tuple[str, float]:
    """A label made of mono text and LaTeX glyphs, set from its left end; returns (svg, width)."""
    adv = 0.6 * size  # Geist Mono advance
    cur, out = 0.0, []
    for kind, seg in parts:
        if kind == "text":
            out.append(f'<text class="{cls}" x="{cur:.1f}" y="0" style="white-space:pre">{seg}</text>')
            cur += len(seg) * adv
        else:
            body, w = tex_glyphs(seg, size * 1.12)
            out.append(f'<g class="{cls}-tex" transform="translate({cur + 0.5:.1f} 0)">{body}</g>')
            cur += w + 1.5
    shift = {"start": 0.0, "middle": -cur / 2, "end": -cur}[anchor]
    return f'<g transform="translate({shift:.1f} 0)">{"".join(out)}</g>', cur


def place(parts, x: float, y: float, cls: str, size: float, t: float, anchor: str = "start") -> str:
    g, _ = run(parts, cls, size, anchor)
    return f'<g class="b-pop" style="--d:{t:.2f}s" transform="translate({f(x)} {f(y)})">{g}</g>'


def box(x: float, y: float, w: float, h: float, t: float, cls: str = "th-box") -> str:
    return draw(cls, f"M{f(x)} {f(y)} h{f(w)} v{f(h)} h{f(-w)} Z", t, 0.3)


def node(x: float, y: float, t: float, size: float = 6.0) -> str:
    return pop(f'<rect class="th-node" x="{f(x - size / 2)}" y="{f(y - size / 2)}" width="{f(size)}" height="{f(size)}"/>', t)


def thread(d: str, t: float) -> str:
    """A flowing dashed connector, revealed once (the dashes keep moving afterwards)."""
    return pop(f'<path class="ray flowray th-thread" d="{d}"/>', t)


# ---------------------------------------------------------------- figure 1: the method chain
def method_figure() -> str:
    """Drawn, not written: a pictogram per stage, one title, at most one short line, numbers only on
    dimension lines. Everything else lives in the caption."""
    W, H = 1120, 470
    p = []
    for x in (300, 770):
        p.append(draw("th-guide", f"M{x} 24 V{H - 24}", 0.05, 0.17))
    p.append(text(24, 30, "OBSERVED INPUTS", "th-head", 0.0))
    p.append(text(330, 30, "STELLAR MODELS", "th-head", 0.0))
    p.append(text(796, 30, "OUTPUTS", "th-head", 0.0))

    # ---- input 1: spectroscopy. a star and its spectrum with absorption dips
    x, y = 40, 96
    p.append(draw("th-pic", f"M{x + 22} {y} m-11 0 a11 11 0 1 0 22 0 a11 11 0 1 0 -22 0", 0.2, 0.3))
    for a in (0, 90, 180, 270, 45, 135, 225, 315):
        import math
        r0, r1 = 15, 20 if a % 90 == 0 else 18
        p.append(draw("th-pic", f"M{x + 22 + r0 * math.cos(math.radians(a)):.1f} {y - r0 * math.sin(math.radians(a)):.1f} L{x + 22 + r1 * math.cos(math.radians(a)):.1f} {y - r1 * math.sin(math.radians(a)):.1f}", 0.25, 0.17))
    sx = x + 60
    d = f"M{sx} {y}"
    cur = sx
    for i, depth in enumerate((9, 4, 12, 5, 7, 11, 4, 8)):
        cur += 22
        d += f" L{cur - 7} {y} L{cur - 2} {y + depth} L{cur + 2} {y + depth} L{cur + 7} {y}"
    d += f" L{cur + 18} {y}"
    p.append(draw("th-pic", d, 0.3, 0.6))
    p.append(text(x, y + 44, "Spectroscopy", "th-title", 0.35))
    p.append(text(x, y + 60, "SWEET-Cat", "th-note", 0.35))

    # ---- input 2: luminosity. a parallax triangle and a filter curve
    x, y = 40, 212
    bx0, bx1, by = x + 10, x + 70, y + 44
    tx, ty = x + 40, y - 6
    p.append(draw("th-pic", f"M{bx0} {by} H{bx1}", 0.45, 0.2))
    p.append(draw("th-pic", f"M{bx0} {by} L{tx} {ty} L{bx1} {by}", 0.5, 0.4))
    p.append(pop(f'<circle class="th-pic" cx="{bx0}" cy="{by}" r="3"/><circle class="th-pic" cx="{bx1}" cy="{by}" r="3"/>', 0.5))
    p.append(pop(f'<path class="th-pic" d="M{tx - 4} {ty - 4} l8 8 M{tx - 4} {ty + 4} l8 -8"/>', 0.55))
    p.append(draw("th-dim", f"M{tx - 9} {ty + 14} a9 9 0 0 0 18 0", 0.55, 0.2))
    fx = x + 120
    p.append(draw("th-guide", f"M{fx} {by} H{fx + 110}", 0.5, 0.17))
    p.append(draw("th-pic", f"M{fx} {by} L{fx + 18} {by} C{fx + 30} {by - 42}, {fx + 80} {by - 42}, {fx + 92} {by} L{fx + 110} {by}", 0.55, 0.5))
    p.append(place([("text", "Luminosity")], x, y + 74, "th-title", 12, 0.6))
    p.append(place([("text", "Gaia parallax, 2MASS "), ("tex", r"K_\mathrm{S}")], x, y + 90, "th-note", 10.5, 0.6))

    # ---- input 3: seismology. a comb of peaks under a Gaussian envelope, with the two global parameters
    x, y = 40, 346
    cx0, base = x + 10, y + 40
    heights = (6, 10, 16, 24, 30, 24, 16, 10, 6)
    xs = [cx0 + i * 24 for i in range(9)]
    for i, (xx, h) in enumerate(zip(xs, heights)):
        p.append(draw("th-pic", f"M{xx} {base} v{-h}", 0.65 + 0.03 * i, 0.2))
    p.append(draw("th-dim", f"M{xs[0] - 10} {base - 2} C{xs[2]} {base - 22}, {xs[3]} {base - 36}, {xs[4]} {base - 36} C{xs[5]} {base - 36}, {xs[6]} {base - 22}, {xs[8] + 10} {base - 2}", 0.9, 0.5))
    p.append(draw("th-dim", f"M{xs[4]} {base - 40} V{base + 6}", 0.95, 0.2))
    p.append(draw("th-dimline", f"M{xs[3]} {base + 10} V{base + 14} H{xs[4]} V{base + 10}", 0.95, 0.2))
    p.append(place([("tex", r"\Delta\nu")], (xs[3] + xs[4]) / 2, base + 26, "th-note", 10.5, 1.0, "middle"))
    p.append(place([("tex", r"\nu_{\max}")], xs[4] + 8, base - 42, "th-note", 10.5, 1.0))
    p.append(text(x, y + 86, "Seismic parameters", "th-title", 1.0))
    p.append(text(x, y + 102, "from the literature", "th-note", 1.0))

    # ---- models 1: MESA grid. an HR box with schematic tracks and a mass dimension line
    gx, gy, gw, gh = 340, 58, 150, 100
    p.append(draw("th-axis", f"M{gx} {gy} V{gy + gh} H{gx + gw}", 1.05, 0.3))
    for i in range(5):
        x0 = gx + gw - 18 - i * 26
        y0 = gy + gh - 10 - i * 4
        d = (f"M{x0} {y0} C{x0 + 4} {y0 - 22 - i * 4}, {x0 - 12} {y0 - 34 - i * 6}, {x0 - 8} {y0 - 44 - i * 7} "
             f"C{x0 - 4} {y0 - 52 - i * 7}, {x0 - 40} {y0 - 70 - i * 3}, {x0 - 58 - i * 2} {gy + 6}")
        p.append(draw("th-pic", d, 1.1 + 0.05 * i, 0.5))
    p.append(draw("th-dimline", f"M{gx + 16} {gy + gh + 14} H{gx + gw - 8} M{gx + 16} {gy + gh + 10} v8 M{gx + gw - 8} {gy + gh + 10} v8", 1.35, 0.3))
    p.append(place([("text", "0.5 to 1.8 "), ("tex", r"M_\odot")], gx + (gw + 8) / 2, gy + gh + 30, "th-note", 10.5, 1.4, "middle"))
    p.append(text(gx, gy + gh + 50, "MESA grid", "th-title", 1.35))

    # ---- models 2: GYRE. a mode spectrum
    mx0, mbase = 540, 150
    pattern = (26, 8, 18, 28, 9, 20, 30, 10, 20, 28, 8, 17, 24)
    for i, h in enumerate(pattern):
        p.append(draw("th-pic", f"M{mx0 + i * 12} {mbase} v{-h}", 1.45 + 0.02 * i, 0.2))
    p.append(draw("th-guide", f"M{mx0 - 6} {mbase} H{mx0 + 12 * len(pattern)}", 1.4, 0.17))
    p.append(text(mx0, gy + gh + 50, "GYRE", "th-title", 1.6))
    p.append(text(mx0, gy + gh + 66, "mode frequencies", "th-note", 1.6))
    p.append(draw("th-line", f"M{gx + gw + 10} {gy + gh / 2} H{mx0 - 16}", 1.4, 0.2))
    p.append(pop(f'<path class="th-arrow" d="M{mx0 - 20} {gy + gh / 2 - 4} L{mx0 - 14} {gy + gh / 2} L{mx0 - 20} {gy + gh / 2 + 4}"/>', 1.45))

    # ---- centre: PARAM. a posterior hill with its 68 per cent band and the mode
    px, py, pw = 420, 258, 300
    hb = py + 110
    peak = px + 150
    hill = (f"M{px} {hb} C{px + 60} {hb}, {px + 100} {hb - 10}, {px + 120} {hb - 48} "
            f"C{px + 136} {hb - 82}, {px + 160} {hb - 96}, {px + 172} {hb - 70} C{px + 184} {hb - 44}, {px + 200} {hb - 8}, {px + 300} {hb}")
    p.append(draw("th-guide", f"M{px} {hb} H{px + pw}", 1.7, 0.17))
    p.append(pop(f'<path class="th-band" d="M{px + 112} {hb} V{hb - 30} H{px + 196} V{hb} Z"/>', 1.95))
    p.append(draw("th-pic th-hill", hill, 1.75, 0.8))
    p.append(draw("th-dim", f"M{px + 160} {hb - 96} V{hb + 4}", 2.0, 0.2))
    p.append(draw("th-dimline", f"M{px + 112} {hb + 12} V{hb + 16} H{px + 196} V{hb + 12}", 2.0, 0.3))
    p.append(text(px + 154, hb + 30, "68 %", "th-note", 2.05, "middle"))
    p.append(text(px, py - 2, "PARAM", "th-big", 1.7))
    p.append(text(px, py + 16, "Bayesian isochrone fitting", "th-note", 1.7))

    # thread: inputs and models into PARAM, PARAM to outputs
    xin = 280
    for k, yy in enumerate((96, 256, 386)):
        p.append(thread(f"M{xin} {yy} C{xin + 60} {yy}, {px - 60} {hb - 72 + 26 * k}, {px} {hb - 72 + 26 * k}", 1.6 + 0.05 * k))
        p.append(node(px, hb - 72 + 26 * k, 1.65 + 0.05 * k))
    p.append(thread(f"M{mx0 + 150} {mbase + 8} C{mx0 + 150} {mbase + 60}, {px + 236} {hb - 110}, {px + 236} {hb - 62}", 1.7))
    p.append(node(px + 236, hb - 62, 1.75))
    p.append(thread(f"M{px + pw} {hb - 40} C{px + pw + 30} {hb - 40}, 760 110, 792 110", 2.1))
    p.append(thread(f"M{px + pw} {hb - 10} C{px + pw + 30} {hb - 10}, 760 330, 792 330", 2.4))
    p.append(node(px + pw, hb - 40, 2.1))
    p.append(node(px + pw, hb - 10, 2.4))

    # ---- outputs 1: marginal distributions of mass, radius and age
    ox = 800
    for i, lab in enumerate(("mass", "radius", "age")):
        x0, y0, w = ox + i * 104, 150, 90
        if lab == "age":
            d = (f"M{x0} {y0} C{x0 + 14} {y0}, {x0 + 18} {y0 - 44}, {x0 + 30} {y0 - 44} C{x0 + 42} {y0 - 44}, {x0 + 44} {y0 - 8}, {x0 + 54} {y0 - 8} "
                 f"C{x0 + 62} {y0 - 8}, {x0 + 64} {y0 - 26}, {x0 + 72} {y0 - 26} C{x0 + 82} {y0 - 26}, {x0 + 86} {y0}, {x0 + w} {y0}")
            pk = x0 + 30
        else:
            d = f"M{x0} {y0} C{x0 + 30} {y0}, {x0 + 34} {y0 - 50}, {x0 + 46} {y0 - 50} C{x0 + 58} {y0 - 50}, {x0 + 62} {y0}, {x0 + w} {y0}"
            pk = x0 + 46
        p.append(draw("th-guide", f"M{x0} {y0} H{x0 + w}", 2.1, 0.17))
        p.append(draw("th-pic", d, 2.15 + 0.1 * i, 0.5))
        p.append(draw("th-dim", f"M{pk} {y0 - 50} V{y0 + 4}", 2.4 + 0.1 * i, 0.2))
        p.append(text(x0 + w / 2, y0 + 18, lab, "th-body", 2.4 + 0.1 * i, "middle"))
    p.append(text(ox, 58, "Marginal distributions", "th-title", 2.1))
    p.append(text(ox, 196, "per star", "th-note", 2.5))

    # ---- outputs 2: the constraint sets as a 4 x 4 grid of squares, counted by a dimension line
    sx0, sy0, cell, gap = ox + 100, 262, 22, 8
    cols = [[("text", "none")], [("tex", r"\Delta\nu")], [("tex", r"\nu_{\max}")], [("text", "both")]]
    rows = [[("text", "spec")], [("text", "no "), ("tex", r"\log g")], [("text", "+ "), ("tex", r"L")], [("text", "+ "), ("tex", r"L"), ("text", ", no "), ("tex", r"\log g")]]
    for j, c in enumerate(cols):
        p.append(place(c, sx0 + j * (cell + gap) + cell / 2, sy0 - 8, "th-note", 10.5, 2.5, "middle"))
    for i, r in enumerate(rows):
        yy = sy0 + i * (cell + gap)
        p.append(place(r, sx0 - 10, yy + cell / 2 + 4, "th-note", 10.5, 2.55 + 0.05 * i, "end"))
        for j in range(4):
            p.append(draw("th-cell", f"M{sx0 + j * (cell + gap)} {yy} h{cell} v{cell} h{-cell} Z", 2.55 + 0.03 * (i * 4 + j), 0.25))
    right = sx0 + 4 * (cell + gap) - gap
    bottom = sy0 + 4 * (cell + gap) - gap
    p.append(draw("th-dimline", f"M{right + 14} {sy0} H{right + 18} V{bottom} H{right + 14}", 2.9, 0.3))
    p.append(text(right + 24, (sy0 + bottom) / 2 + 4, "16", "th-note", 2.95))
    p.append(text(ox, bottom + 30, "Constraint sets", "th-title", 2.95))
    return (
        f'<svg class="bp-svg th-svg th-method" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-labelledby="th-m-t"><title id="th-m-t">The method chain of the dissertation, drawn as pictograms: a star and its '
        'spectrum, a parallax triangle and a filter curve, and a comb of oscillation peaks on the left; a grid of stellar tracks '
        'and a mode spectrum on top; a posterior hill for PARAM in the middle; marginal distributions of mass, radius and age and '
        'the sixteen constraint sets on the right.</title>' + "".join(p) + "</svg>\n"
    )


# ---------------------------------------------------------------- figure 2: the results
def results_figure() -> str:
    W, H = 760, 400
    pub = DATA["published_inputs"]
    inf = DATA["inflated_inputs"]
    order = ["spec", "spec+dnu", "spec+numax", "spec+dnu+numax", "specphot", "specphot+dnu", "specphot+numax", "specphot+dnu+numax"]
    labels = {
        "spec": [("text", "spec")],
        "spec+dnu": [("text", "spec + "), ("tex", r"\Delta\nu")],
        "spec+numax": [("text", "spec + "), ("tex", r"\nu_{\max}")],
        "spec+dnu+numax": [("text", "spec + "), ("tex", r"\Delta\nu"), ("text", " + "), ("tex", r"\nu_{\max}")],
        "specphot": [("text", "spec + L")],
        "specphot+dnu": [("text", "spec + L + "), ("tex", r"\Delta\nu")],
        "specphot+numax": [("text", "spec + L + "), ("tex", r"\nu_{\max}")],
        "specphot+dnu+numax": [("text", "spec + L + "), ("tex", r"\Delta\nu"), ("text", " + "), ("tex", r"\nu_{\max}")],
    }
    panels = [("age", 0, 40, (0, 10, 20, 30, 40), 150), ("mass", 0, 7, (0, 2, 4, 6), 470)]
    p = []
    top, step = 64, 34
    lab_x = 10
    for i, key in enumerate(order):
        yy = top + i * step
        p.append(place(labels[key], lab_x, yy + 4, "th-row", 10.5, 0.1 + 0.03 * i))
        p.append(draw("th-guide", f"M{lab_x} {yy + 12} H{W - 16}", 0.05 + 0.02 * i, 0.17))
    for name, lo, hi, ticks, x0 in panels:
        pw = 270
        sx = lambda v, lo=lo, hi=hi, x0=x0, pw=pw: x0 + (v - lo) / (hi - lo) * pw
        ybot = top + 7 * step + 16
        p.append(draw("th-axis", f"M{x0} {top - 24} V{ybot} H{x0 + pw}", 0.0, 0.3))
        for tv in ticks:
            p.append(draw("th-tick", f"M{sx(tv)} {ybot} v4", 0.1, 0.17))
            p.append(text(sx(tv), ybot + 16, str(tv), "th-tickl", 0.15, "middle"))
        p.append(text(x0 + pw, ybot + 32, f"median relative uncertainty of {name}, per cent", "th-note", 0.2, "end"))
        p.append(text(x0, top - 32, name.upper(), "th-head", 0.0))
        for i, key in enumerate(order):
            yy = top + i * step
            v = pub[key][name]
            t = 0.4 + 0.06 * i
            if key in inf:
                v2 = inf[key][name]
                p.append(draw("th-join", f"M{sx(v)} {yy} H{sx(v2)}", t, 0.3))
                p.append(pop(f'<rect class="th-sq" x="{f(sx(v2) - 4.5)}" y="{f(yy - 4.5)}" width="9" height="9"/>', t + 0.2))
                p.append(text(sx(v2) + (10 if v2 >= v else -10), yy + 4, f"{v2:.1f}", "th-val2", t + 0.25, "start" if v2 >= v else "end"))
            p.append(pop(f'<circle class="th-dot" cx="{f(sx(v))}" cy="{f(yy)}" r="5"/>', t + 0.1))
            below = key in inf and inf[key][name] >= v
            p.append(text(sx(v) + (-10 if below else 10), yy + 4, f"{v:.1f}", "th-val", t + 0.15, "end" if below else "start"))
    # legend
    ly = H - 14
    p.append(pop(f'<circle class="th-dot" cx="20" cy="{ly - 4}" r="5"/>', 1.2))
    p.append(text(32, ly, "input uncertainties as published (Table 6.8)", "th-note", 1.2))
    p.append(pop(f'<rect class="th-sq" x="{f(380 - 4.5)}" y="{f(ly - 8.5)}" width="9" height="9"/>', 1.2))
    p.append(text(392, ly, "inflated to 75 K and 0.1 dex (Table 6.18)", "th-note", 1.2))
    return (
        f'<svg class="bp-svg th-svg th-results" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-labelledby="th-r-t"><title id="th-r-t">Median relative uncertainty of age and of mass for the ten Ariel input '
        'catalogue stars under eight constraint sets, with the input uncertainties as published and, for four sets, inflated '
        'to literature-typical values.</title>' + "".join(p) + "</svg>\n"
    )


def main() -> None:
    out = ROOT / "_includes/figures"
    m = method_figure()
    r = results_figure()
    (out / "thesis-method.svg").write_text(m)
    (out / "thesis-results.svg").write_text(r)
    print(f"thesis-method.svg {len(m) / 1024:.1f} KB; thesis-results.svg {len(r) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
