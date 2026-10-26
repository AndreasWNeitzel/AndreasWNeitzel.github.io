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
def frame(x: float, y: float, w: float, h: float, title: str, t: float) -> list[str]:
    """A framed stage in the HAYDNsim pipeline's grammar: outline box, title and a rule under it."""
    return [
        draw("th-frame", f"M{f(x)} {f(y)} h{f(w)} v{f(h)} h{f(-w)} Z", t, 0.4),
        text(x + 12, y + 20, title, "th-title", t + 0.1),
        draw("th-rule", f"M{f(x + 12)} {f(y + 28)} h{f(w - 24)}", t + 0.1, 0.2),
    ]


def method_figure() -> str:
    """Drawn, not written: framed stages with one pictogram and one short line each, ports on the
    frames, flowing threads between ports. Build order: frames, pictograms, threads, outputs."""
    import math
    W, H = 1120, 570
    p = []
    T_FRAME, T_PIC, T_THREAD, T_OUT = 0.0, 0.6, 1.5, 2.0

    # ---- frames
    L = [(40, 170, 290, 120, "SPECTROSCOPY"), (40, 300, 290, 120, "LUMINOSITY"), (40, 430, 290, 120, "SEISMIC PARAMETERS")]
    for i, (x, y, w, h, title) in enumerate(L):
        p += frame(x, y, w, h, title, T_FRAME + 0.1 * i)
    p += frame(380, 40, 185, 110, "MESA GRID", T_FRAME + 0.3)
    p += frame(585, 40, 185, 110, "GYRE", T_FRAME + 0.4)
    PX, PY, PW, PH = 380, 170, 390, 380
    p += frame(PX, PY, PW, PH, "PARAM", T_FRAME + 0.5)
    p += frame(810, 170, 280, 180, "MASS, RADIUS, AGE", T_OUT)
    p += frame(810, 370, 280, 180, "CONSTRAINT SETS", T_OUT + 0.1)

    # ---- pictograms, left column
    # spectroscopy: a star and its spectrum with absorption dips
    x, y = 60, 240
    p.append(draw("th-pic", f"M{x + 16} {y} m-11 0 a11 11 0 1 0 22 0 a11 11 0 1 0 -22 0", T_PIC, 0.3))
    for a in range(0, 360, 45):
        r0, r1 = 15, (20 if a % 90 == 0 else 18)
        p.append(draw("th-pic", f"M{x + 16 + r0 * math.cos(math.radians(a)):.1f} {y - r0 * math.sin(math.radians(a)):.1f} L{x + 16 + r1 * math.cos(math.radians(a)):.1f} {y - r1 * math.sin(math.radians(a)):.1f}", T_PIC + 0.05, 0.17))
    cur = x + 50
    d = f"M{cur} {y}"
    for depth in (9, 4, 12, 5, 7, 11, 4, 8, 6):
        cur += 20
        d += f" L{cur - 7} {y} L{cur - 2} {y + depth} L{cur + 2} {y + depth} L{cur + 7} {y}"
    d += f" L{cur + 16} {y}"
    p.append(draw("th-pic", d, T_PIC + 0.1, 0.6))
    p.append(text(52, 282, "SWEET-Cat", "th-line", T_PIC + 0.2))
    # luminosity: a parallax triangle and a filter curve
    x, y = 60, 320
    bx0, bx1, by = x + 10, x + 70, y + 54
    tx, ty = x + 40, y + 8
    p.append(draw("th-pic", f"M{bx0} {by} H{bx1}", T_PIC + 0.2, 0.2))
    p.append(draw("th-pic", f"M{bx0} {by} L{tx} {ty} L{bx1} {by}", T_PIC + 0.25, 0.4))
    p.append(pop(f'<circle class="th-pic" cx="{bx0}" cy="{by}" r="3"/><circle class="th-pic" cx="{bx1}" cy="{by}" r="3"/>', T_PIC + 0.25))
    p.append(pop(f'<path class="th-pic" d="M{tx - 4} {ty - 4} l8 8 M{tx - 4} {ty + 4} l8 -8"/>', T_PIC + 0.3))
    p.append(draw("th-dim", f"M{tx - 9} {ty + 14} a9 9 0 0 0 18 0", T_PIC + 0.3, 0.2))
    fx = x + 130
    p.append(draw("th-guide", f"M{fx} {by} H{fx + 120}", T_PIC + 0.25, 0.17))
    p.append(draw("th-pic", f"M{fx} {by} L{fx + 20} {by} C{fx + 32} {by - 42}, {fx + 88} {by - 42}, {fx + 100} {by} L{fx + 120} {by}", T_PIC + 0.3, 0.5))
    p.append(place([("text", "Gaia parallax, 2MASS "), ("tex", r"K_\mathrm{S}")], 52, 412, "th-line", 11, T_PIC + 0.4))
    # seismic parameters: a comb of peaks under a Gaussian envelope
    x, y = 60, 450
    base = y + 56
    xs = [x + 14 + i * 24 for i in range(9)]
    heights = (6, 10, 16, 24, 30, 24, 16, 10, 6)
    for i, (xx, h) in enumerate(zip(xs, heights)):
        p.append(draw("th-pic", f"M{xx} {base} v{-h}", T_PIC + 0.4 + 0.02 * i, 0.2))
    p.append(draw("th-dim", f"M{xs[0] - 10} {base - 2} C{xs[2]} {base - 22}, {xs[3]} {base - 36}, {xs[4]} {base - 36} C{xs[5]} {base - 36}, {xs[6]} {base - 22}, {xs[8] + 10} {base - 2}", T_PIC + 0.55, 0.5))
    p.append(draw("th-dim", f"M{xs[4]} {base - 44} V{base + 4}", T_PIC + 0.6, 0.2))
    p.append(draw("th-dimline", f"M{xs[3]} {base + 8} V{base + 12} H{xs[4]} V{base + 8}", T_PIC + 0.6, 0.2))
    p.append(place([("tex", r"\Delta\nu")], (xs[3] + xs[4]) / 2 + 12, base + 14, "th-note", 10.5, T_PIC + 0.65, "start"))
    p.append(place([("tex", r"\nu_{\max}")], xs[4] + 8, base - 40, "th-note", 10.5, T_PIC + 0.65))
    p.append(text(52, 542, "from the literature", "th-line", T_PIC + 0.7))

    # ---- pictograms, model panels
    # MESA grid: HR axes, tracks clipped inside them, a mass dimension line
    ax, ay, aw, ah = 396, 76, 140, 40
    p.append(f'<clipPath id="th-hr"><rect x="{ax}" y="{ay - 2}" width="{aw}" height="{ah + 2}"/></clipPath>')
    p.append(draw("th-axis", f"M{ax} {ay} V{ay + ah} H{ax + aw}", T_PIC + 0.3, 0.3))
    tracks = []
    for i in range(5):
        x0 = ax + aw - 14 - i * 24
        y0 = ay + ah - 4 - i * 2
        tracks.append(draw("th-pic", f"M{x0} {y0} C{x0 + 3} {y0 - 14 - i}, {x0 - 8} {y0 - 22 - i * 2}, {x0 - 6} {y0 - 28 - i * 2} C{x0 - 4} {y0 - 34 - i * 2}, {x0 - 30} {y0 - 44}, {x0 - 48 - i} {ay - 2}", T_PIC + 0.35 + 0.05 * i, 0.5))
    p.append('<g clip-path="url(#th-hr)">' + "".join(tracks) + "</g>")
    p.append(draw("th-dimline", f"M{ax + 10} {ay + ah + 10} H{ax + aw - 6} M{ax + 10} {ay + ah + 6} v8 M{ax + aw - 6} {ay + ah + 6} v8", T_PIC + 0.6, 0.3))
    p.append(place([("text", "0.5 to 1.8 "), ("tex", r"M_\odot")], ax + aw / 2 + 2, ay + ah + 26, "th-note", 10.5, T_PIC + 0.65, "middle"))
    # GYRE: a mode spectrum
    mx0, mbase = 603, 126
    pattern = (26, 8, 18, 28, 9, 20, 30, 10, 20, 28, 8, 17, 24)
    p.append(draw("th-guide", f"M{mx0 - 6} {mbase} H{mx0 + 12 * len(pattern)}", T_PIC + 0.4, 0.17))
    for i, h in enumerate(pattern):
        p.append(draw("th-pic", f"M{mx0 + i * 12} {mbase} v{-h}", T_PIC + 0.45 + 0.02 * i, 0.2))
    p.append(text(597, 142, "mode frequencies", "th-line", T_PIC + 0.6))

    # ---- PARAM: the posterior hill with its 68 per cent band
    p.append(text(PX + 12, PY + 46, "Bayesian isochrone fitting", "th-line", T_PIC + 0.5))
    hx, hb, hw = PX + 50, PY + 300, PW - 100
    peak = hx + 150
    hill = (f"M{hx} {hb} C{hx + 60} {hb}, {hx + 100} {hb - 10}, {hx + 120} {hb - 70} "
            f"C{hx + 136} {hb - 120}, {hx + 160} {hb - 140}, {hx + 172} {hb - 100} C{hx + 184} {hb - 64}, {hx + 200} {hb - 8}, {hx + hw} {hb}")
    p.append(draw("th-guide", f"M{hx} {hb} H{hx + hw}", T_PIC + 0.5, 0.17))
    p.append(pop(f'<path class="th-band" d="M{hx + 112} {hb} V{hb - 36} H{hx + 196} V{hb} Z"/>', T_PIC + 0.8))
    p.append(draw("th-pic th-hill", hill, T_PIC + 0.55, 0.8))
    p.append(draw("th-dim", f"M{hx + 160} {hb - 140} V{hb + 4}", T_PIC + 0.8, 0.2))
    p.append(draw("th-dimline", f"M{hx + 112} {hb + 12} V{hb + 16} H{hx + 196} V{hb + 12}", T_PIC + 0.85, 0.3))
    p.append(text(hx + 154, hb + 30, "68 %", "th-note", T_PIC + 0.9, "middle"))

    # ---- ports and threads: every thread runs from a node on one frame to a node on the next
    ports = []
    for i, (x, y, w, h, _) in enumerate(L):
        yc = y + h / 2
        ports += [node(x + w, yc, T_THREAD + 0.05 * i), node(PX, yc, T_THREAD + 0.05 * i)]
        p.append(thread(f"M{x + w} {yc} H{PX}", T_THREAD + 0.05 * i))
    ports += [node(565, 95, T_THREAD), node(585, 95, T_THREAD)]
    p.append(thread("M565 95 H585", T_THREAD))
    ports += [node(677, 150, T_THREAD + 0.1), node(677, PY, T_THREAD + 0.1)]
    p.append(thread(f"M677 150 V{PY}", T_THREAD + 0.1))
    for (yp, yo, t) in ((PY + 110, 260, T_OUT + 0.2), (PY + 270, 460, T_OUT + 0.3)):
        ports += [node(PX + PW, yp, t), node(810, yo, t)]
        p.append(thread(f"M{PX + PW} {yp} C{PX + PW + 24} {yp}, {810 - 24} {yo}, 810 {yo}", t))
    p += ports

    # ---- outputs: three marginal hills, and the constraint sets as a 4 x 4 grid
    ox = 826
    for i, lab in enumerate(("mass", "radius", "age")):
        x0, y0, w = ox + i * 88, 290, 78
        if lab == "age":
            d = (f"M{x0} {y0} C{x0 + 12} {y0}, {x0 + 16} {y0 - 40}, {x0 + 26} {y0 - 40} C{x0 + 36} {y0 - 40}, {x0 + 38} {y0 - 8}, {x0 + 47} {y0 - 8} "
                 f"C{x0 + 54} {y0 - 8}, {x0 + 56} {y0 - 24}, {x0 + 62} {y0 - 24} C{x0 + 71} {y0 - 24}, {x0 + 74} {y0}, {x0 + w} {y0}")
            pk = x0 + 26
        else:
            d = f"M{x0} {y0} C{x0 + 26} {y0}, {x0 + 30} {y0 - 46}, {x0 + 40} {y0 - 46} C{x0 + 50} {y0 - 46}, {x0 + 54} {y0}, {x0 + w} {y0}"
            pk = x0 + 40
        p.append(draw("th-guide", f"M{x0} {y0} H{x0 + w}", T_OUT + 0.2, 0.17))
        p.append(draw("th-pic", d, T_OUT + 0.25 + 0.1 * i, 0.5))
        p.append(draw("th-dim", f"M{pk} {y0 - 46} V{y0 + 4}", T_OUT + 0.4 + 0.1 * i, 0.2))
        p.append(text(x0 + w / 2, y0 + 16, lab, "th-note", T_OUT + 0.4 + 0.1 * i, "middle"))
    p.append(text(822, 336, "per star", "th-line", T_OUT + 0.6))
    sx0, sy0, cell, gap = 918, 418, 20, 8
    cols = [[("text", "none")], [("tex", r"\Delta\nu")], [("tex", r"\nu_{\max}")], [("text", "both")]]
    rows = [[("text", "spec")], [("text", "no "), ("tex", r"\log g")], [("text", "+ "), ("tex", r"L")], [("text", "+ "), ("tex", r"L"), ("text", ", no "), ("tex", r"\log g")]]
    for j, c in enumerate(cols):
        p.append(place(c, sx0 + j * (cell + gap) + cell / 2, sy0 - 8, "th-note", 10.5, T_OUT + 0.5, "middle"))
    for i, r in enumerate(rows):
        yy = sy0 + i * (cell + gap)
        p.append(place(r, sx0 - 10, yy + cell / 2 + 4, "th-note", 10.5, T_OUT + 0.55 + 0.05 * i, "end"))
        for j in range(4):
            p.append(draw("th-cell", f"M{sx0 + j * (cell + gap)} {yy} h{cell} v{cell} h{-cell} Z", T_OUT + 0.55 + 0.03 * (i * 4 + j), 0.25))
    right = sx0 + 4 * (cell + gap) - gap
    bottom = sy0 + 4 * (cell + gap) - gap
    p.append(draw("th-dimline", f"M{right + 12} {sy0} H{right + 16} V{bottom} H{right + 12}", T_OUT + 0.9, 0.3))
    p.append(text(right + 22, (sy0 + bottom) / 2 + 4, "16", "th-note", T_OUT + 0.95))
    return (
        f'<svg class="bp-svg th-svg th-method" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-labelledby="th-m-t"><title id="th-m-t">The method chain of the dissertation as framed stages: spectroscopy, '
        'luminosity and seismic parameters on the left; the MESA grid and GYRE on top; PARAM in the middle, with its posterior '
        'hill; the marginal distributions of mass, radius and age and the sixteen constraint sets on the right.</title>' + "".join(p) + "</svg>\n"
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
