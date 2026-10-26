"""Draw the workflow of Neitzel et al. 2025 (A&A 695, A243) as the wide figure of its explainer page.

A schematic is drawn, not written: each stage is a pictogram with a title and at most one short
line. The only numbers on the drawing are dimension lines: 75,000 stars and 76,168 giants
(Sect. 2.2), five features (Sect. 2.1), two dimensions and 10,000 epochs (Sect. 3.1), the
trustworthiness gate T > 0.90 (Sect. 3.2), informedness 0.97 to 0.99 (Table 2) and 97.6 to
98.7 per cent of accreted stars in MC2 (Sect. 4.1). Every other fact lives in the page's caption
and prose. The accepted paper is arXiv:2501.16294.

Usage: python3 figures/papers/build_neitzel2025_figure.py _includes/figures/neitzel-2025-workflow.svg
Symbols are set in LaTeX through figures/texsvg.py (latex and dvisvgm must be installed).
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from texsvg import tex_glyphs  # noqa: E402

W, H = 1120, 392
TY = 36  # title baseline
Y0 = 176  # the thread's height
FS = 10.5  # mono size in user units (about 11.3 px at a 1440 px viewport)
CX = {"survey": 92, "samples": 262, "features": 428, "umap": 592, "hdbscan": 752, "runs": 912, "check": 1052}

WORDS: list[str] = []  # every word printed on the drawing, for the count


def f(v: float) -> str:
    return f"{v:.1f}"


def draw(cls: str, d: str, t: float, dur: float = 0.35) -> str:
    return f'<path class="{cls} b-draw" style="--d:{t:.2f}s;--dur:{dur:.2f}s" pathLength="1" d="{d}"/>'


def pop(inner: str, t: float) -> str:
    return f'<g class="b-pop" style="--d:{t:.2f}s">{inner}</g>'


def text(x: float, y: float, s: str, cls: str, anchor: str = "start") -> str:
    WORDS.extend(s.split())
    return f'<text class="{cls}" x="{f(x)}" y="{f(y)}" text-anchor="{anchor}">{s}</text>'


DEFS: dict = {}


def glyph(snippet: str, size: float) -> tuple[str, float]:
    key = (snippet, round(size, 2))
    if key not in DEFS:
        body, w = tex_glyphs(snippet, size)
        DEFS[key] = (f"nwg{len(DEFS)}", w, body)
    gid, w, _ = DEFS[key]
    return gid, w


def run(x: float, y: float, parts, cls: str = "nw-body", size: float = FS, anchor: str = "start") -> str:
    adv = 0.6 * size
    cur, out = 0.0, []
    for kind, seg in parts:
        if kind == "text":
            WORDS.extend(seg.split())
            out.append(f'<text class="{cls}" x="{f(cur)}" y="0" style="white-space:pre">{seg}</text>')
            cur += len(seg) * adv
        else:
            WORDS.append(seg)
            gid, w = glyph(seg, size * 1.08)
            out.append(f'<use class="{cls}-tex" href="#{gid}" transform="translate({f(cur + 0.5)} 0)"/>')
            cur += w + 1.2
    shift = {"start": 0.0, "middle": -cur / 2, "end": -cur}[anchor]
    return f'<g transform="translate({f(x + shift)} {f(y)})">{"".join(out)}</g>'


def node(x: float, y: float, t: float, size: float = 5.0) -> str:
    return pop(f'<rect class="nw-node" x="{f(x - size / 2)}" y="{f(y - size / 2)}" width="{f(size)}" height="{f(size)}"/>', t)


def thread(d: str, t: float) -> str:
    return pop(f'<path class="ray flowray nw-thread" d="{d}"/>', t)


def link(x0: float, y0: float, x1: float, y1: float, t: float) -> str:
    cx = (x0 + x1) / 2
    return thread(f"M{f(x0)} {f(y0)} C{f(cx)} {f(y0)} {f(cx)} {f(y1)} {f(x1)} {f(y1)}", t)


def dim(x0: float, x1: float, y: float, label: str, t: float, above: bool = True) -> str:
    """A horizontal dimension line with end ticks and its value."""
    s = draw("nw-dimline", f"M{f(x0)} {f(y - 3)} v6 M{f(x0)} {f(y)} H{f(x1)} M{f(x1)} {f(y - 3)} v6", t, 0.25)
    ly = y - 5 if above else y + 13
    return s + pop(text((x0 + x1) / 2, ly, label, "nw-dim", "middle"), t + 0.1)


def dim_v(x: float, y0: float, y1: float, label: str, t: float) -> str:
    s = draw("nw-dimline", f"M{f(x - 3)} {f(y0)} h6 M{f(x)} {f(y0)} V{f(y1)} M{f(x - 3)} {f(y1)} h6", t, 0.25)
    return s + pop(text(x + 6, (y0 + y1) / 2 + 4, label, "nw-dim"), t + 0.1)


def lcg(seed: int):
    s = seed & 0xFFFFFFFF
    while True:
        s = (1664525 * s + 1013904223) & 0xFFFFFFFF
        yield s / 0x100000000


def cloud(cx: float, cy: float, rx: float, ry: float, n: int, seed: int, r: float, cls: str, t: float, stagger: float = 0.012) -> str:
    g = lcg(seed)
    out = []
    for i in range(n):
        u, v = next(g), next(g)
        rad, ang = math.sqrt(u), 2 * math.pi * v
        x, y = cx + rx * rad * math.cos(ang), cy + ry * rad * math.sin(ang)
        out.append(pop(f'<circle class="{cls}" cx="{f(x)}" cy="{f(y)}" r="{f(r)}"/>', t + stagger * i))
    return "".join(out)


def two_blob_points(cx: float, cy: float, seed: int, scale: float = 1.0):
    """The embedding's shape: a large blob (MC1) and a small one (MC2), the same points every time."""
    g = lcg(seed)
    pts = []
    for i in range(60):
        u, v = next(g), next(g)
        rad, ang = math.sqrt(u), 2 * math.pi * v
        pts.append((cx - 14 * scale + 26 * scale * rad * math.cos(ang), cy + 6 * scale + 17 * scale * rad * math.sin(ang), 0))
    for i in range(16):
        u, v = next(g), next(g)
        rad, ang = math.sqrt(u), 2 * math.pi * v
        pts.append((cx + 30 * scale + 11 * scale * rad * math.cos(ang), cy - 22 * scale + 8 * scale * rad * math.sin(ang), 1))
    return pts


def main(out: Path) -> int:
    P: list[str] = []
    # construction hairlines: the thread's level and the stage centres
    P.append(draw("nw-guide", f"M16 {f(Y0)} H1104", 0.0, 0.3))
    for k, cx in CX.items():
        P.append(draw("nw-guide", f"M{f(cx)} 46 V338", 0.05, 0.2))
    T = 0.25

    # ------------------------------------------------------------------ 1 the survey
    cx = CX["survey"]
    P.append(pop(text(cx, TY, "THE SURVEY", "nw-title", "middle"), T))
    fy = 128  # face-on view
    P.append(draw("nw-line", f"M{f(cx - 46)} {f(fy)} a46 46 0 1 0 92 0 a46 46 0 1 0 -92 0", T, 0.6))
    P.append(draw("nw-line", f"M{f(cx - 10)} {f(fy)} a10 10 0 1 0 20 0 a10 10 0 1 0 -20 0", T + 0.1, 0.3))
    # two spiral arms as construction
    for sgn in (0.0, math.pi):
        pts = []
        for i in range(28):
            th = i / 27 * 2.1
            r = 11 * math.exp(0.42 * th)
            if r > 45:
                break
            pts.append((cx + r * math.cos(th + sgn), fy + r * math.sin(th + sgn)))
        P.append(draw("nw-guide", "M" + " L".join(f"{f(a)} {f(b)}" for a, b in pts), T + 0.15, 0.4))
    sx, sy = cx + 31, fy + 2
    P.append(pop(f'<circle class="nw-sphere" cx="{f(sx)}" cy="{f(sy)}" r="11"/>', T + 0.3))
    P.append(pop(f'<circle class="nw-obs" cx="{f(sx)}" cy="{f(sy)}" r="2.4"/>', T + 0.3))
    ey = 248  # edge-on view
    P.append(draw("nw-line", f"M{f(cx - 46)} {f(ey)} a46 7 0 1 0 92 0 a46 7 0 1 0 -92 0", T + 0.2, 0.5))
    P.append(draw("nw-line", f"M{f(cx - 10)} {f(ey)} a10 5 0 1 0 20 0 a10 5 0 1 0 -20 0", T + 0.25, 0.3))
    P.append(pop(f'<circle class="nw-obs" cx="{f(sx)}" cy="{f(ey)}" r="2.4"/>', T + 0.35))
    P.append(draw("nw-guide", f"M{f(sx)} {f(sy + 11)} V{f(ey - 4)}", T + 0.3, 0.3))
    P.append(pop(text(sx, sy + 24, "Sun", "nw-dim", "middle"), T + 0.4))
    P.append(node(sx + 11, sy, T + 0.4))
    T += 0.45

    # ------------------------------------------------------------------ 2 four samples
    cx = CX["samples"]
    P.append(pop(text(cx, TY, "FOUR SAMPLES", "nw-title", "middle"), T))
    ys = [92, 148, 204, 260]
    x_in = CX["survey"] + 31 + 11
    specs = [  # (letter, n, radius, class, outline)
        ("A", 46, 1.5, "nw-dot", False),
        ("B", 22, 1.9, "nw-dot", False),
        ("C", 22, 2.7, "nw-dot-o", True),
        ("D", 22, 2.3, "nw-dot-o", True),
    ]
    for i, ((letter, n, r, cls, outline), y) in enumerate(zip(specs, ys)):
        tt = T + 0.1 * i
        P.append(link(x_in, sy if i == 0 else sy, cx - 44, y, tt))
        P.append(node(cx - 44, y, tt + 0.05))
        if outline:
            P.append(draw("nw-hull", f"M{f(cx - 38)} {f(y)} a38 19 0 1 0 76 0 a38 19 0 1 0 -76 0", tt + 0.05, 0.4))
        P.append(cloud(cx, y, 30, 14, n, 11 + i, r, cls, tt + 0.1))
        P.append(pop(text(cx - 52, y + 4, letter, "nw-letter", "end"), tt + 0.1))
        P.append(link(cx + 44, y, CX["features"] - 80, Y0, tt + 0.4))
        P.append(node(cx + 44, y, tt + 0.35))
    P.append(dim(cx - 30, cx + 30, ys[0] + 21, "75,000 stars", T + 0.5, above=False))
    P.append(dim(cx - 30, cx + 30, ys[1] + 21, "76,168 giants", T + 0.55, above=False))
    P.append(pop(text(cx, ys[3] + 33, "with errors", "nw-dim", "middle"), T + 0.6))
    T += 0.75

    # ------------------------------------------------------------------ 3 five features
    cx = CX["features"]
    P.append(pop(text(cx, TY, "FIVE FEATURES", "nw-title", "middle"), T))
    P.append(node(cx - 80, Y0, T))
    rows = [(r"V", 104), (r"\sqrt{U^2+W^2}", 140), (r"[\mathrm{Fe}/\mathrm{H}]", 176), (r"[\alpha/\mathrm{Fe}]", 212), (r"\tau", 248)]
    bx = cx + 56  # the bundle point
    for i, (sym, y) in enumerate(rows):
        tt = T + 0.08 * i
        P.append(link(cx - 80, Y0, cx - 40, y, tt))
        P.append(draw("nw-ruler", f"M{f(cx - 40)} {f(y)} H{f(cx + 8)} M{f(cx - 40)} {f(y - 3)} v6 M{f(cx - 16)} {f(y - 2)} v4 M{f(cx + 8)} {f(y - 3)} v6", tt + 0.1, 0.3))
        P.append(pop(run(cx - 16, y - 7, [("tex", sym)], "nw-body", FS, "middle"), tt + 0.15))
        P.append(thread(f"M{f(cx + 8)} {f(y)} C{f(cx + 30)} {f(y)} {f(cx + 34)} {f(Y0)} {f(bx)} {f(Y0)}", tt + 0.3))
    P.append(node(bx, Y0, T + 0.55))
    T += 0.65

    # ------------------------------------------------------------------ 4 UMAP and the gate
    cx = CX["umap"]
    P.append(pop(text(cx, TY, "UMAP", "nw-title", "middle"), T))
    P.append(link(bx, Y0, cx - 52, Y0, T))
    P.append(node(cx - 52, Y0, T + 0.05))
    # five strands collapsing into the 2-D cloud
    ax, ay = cx - 44, 240  # axis corner
    P.append(draw("nw-line", f"M{f(ax)} {f(ay - 120)} V{f(ay)} H{f(ax + 96)}", T + 0.05, 0.4))
    pts = two_blob_points(cx + 4, ay - 60, 5)
    for i, (x, y, _) in enumerate(pts):
        P.append(pop(f'<circle class="nw-dot" cx="{f(x)}" cy="{f(y)}" r="1.5"/>', T + 0.2 + 0.006 * i))
    P.append(dim(ax, ax + 96, ay + 12, "2-D", T + 0.4, above=False))
    P.append(dim(ax, ax + 96, ay + 36, "10,000 epochs", T + 0.45, above=False))
    # the gate: a diamond on the thread between the plot and the clustering
    gx, gy = cx + 84, Y0
    P.append(link(ax + 96, ay - 60, gx - 20, gy, T + 0.5))
    P.append(draw("nw-box", f"M{f(gx)} {f(gy - 20)} L{f(gx + 20)} {f(gy)} L{f(gx)} {f(gy + 20)} L{f(gx - 20)} {f(gy)} Z", T + 0.55, 0.35))
    P.append(pop(text(gx, gy + 34, "T > 0.90", "nw-dim", "middle"), T + 0.65))
    P.append(node(gx + 20, gy, T + 0.65))
    T += 0.8

    # ------------------------------------------------------------------ 5 HDBSCAN
    cx = CX["hdbscan"]
    P.append(pop(text(cx, TY, "HDBSCAN", "nw-title", "middle"), T))
    P.append(link(gx + 20, gy, cx - 60, ay - 60, T))
    P.append(node(cx - 60, ay - 60, T + 0.05))
    pts = two_blob_points(cx + 4, ay - 60, 5)
    for i, (x, y, _) in enumerate(pts):
        P.append(pop(f'<circle class="nw-dot" cx="{f(x)}" cy="{f(y)}" r="1.5"/>', T + 0.05 + 0.004 * i))
    hx, hy = cx + 4 - 14, ay - 60 + 6
    P.append(draw("nw-hull", f"M{f(hx - 32)} {f(hy)} a32 23 0 1 0 64 0 a32 23 0 1 0 -64 0", T + 0.3, 0.5))
    P.append(pop(text(hx - 8, hy + 38, "MC1", "nw-dim", "middle"), T + 0.45))
    kx, ky = cx + 4 + 30, ay - 60 - 22
    P.append(draw("nw-hull", f"M{f(kx - 16)} {f(ky)} a16 13 0 1 0 32 0 a16 13 0 1 0 -32 0", T + 0.4, 0.4))
    P.append(pop(text(kx + 2, ky - 18, "MC2", "nw-dim", "middle"), T + 0.5))
    # persistence bars against the noise baseline
    px0, pyb = cx - 36, 312
    P.append(draw("nw-line", f"M{f(px0)} {f(pyb)} H{f(px0 + 72)}", T + 0.5, 0.3))
    P.append(pop(f'<rect class="nw-bar" x="{f(px0 + 10)}" y="{f(pyb - 44)}" width="16" height="44"/>', T + 0.6))
    P.append(pop(f'<rect class="nw-bar" x="{f(px0 + 36)}" y="{f(pyb - 30)}" width="16" height="30"/>', T + 0.65))
    P.append(draw("nw-gate", f"M{f(px0)} {f(pyb - 14)} H{f(px0 + 72)}", T + 0.6, 0.3))
    P.append(pop(text(px0 + 76, pyb - 11, "baseline", "nw-dim"), T + 0.7))
    P.append(pop(text(px0 + 36, pyb - 54, "persistence", "nw-dim", "middle"), T + 0.7))
    P.append(node(cx + 60, ay - 60, T + 0.55))
    T += 0.8

    # ------------------------------------------------------------------ 6 the second run
    cx = CX["runs"]
    P.append(pop(text(cx, TY, "SECOND RUN", "nw-title", "middle"), T))
    x_from = CX["hdbscan"] + 60
    y1, y2 = Y0 + 34, Y0 - 50  # MC1 and MC2 branch points
    P.append(link(x_from, ay - 60, cx - 40, y1, T))
    P.append(link(x_from, ay - 60, cx - 40, y2, T + 0.05))
    P.append(node(cx - 40, y1, T + 0.1))
    P.append(node(cx - 40, y2, T + 0.1))
    leaves1 = [y1 - 22, y1 + 22]
    leaves2 = [y2 - 30, y2, y2 + 30]
    for i, ly in enumerate(leaves1):
        P.append(link(cx - 40, y1, cx + 8, ly, T + 0.2 + 0.08 * i))
        P.append(draw("nw-hull", f"M{f(cx + 8)} {f(ly)} a14 9 0 1 0 28 0 a14 9 0 1 0 -28 0", T + 0.4 + 0.08 * i, 0.35))
    for i, ly in enumerate(leaves2):
        P.append(link(cx - 40, y2, cx + 8, ly, T + 0.25 + 0.08 * i))
        P.append(draw("nw-hull", f"M{f(cx + 8)} {f(ly)} a10 7 0 1 0 20 0 a10 7 0 1 0 -20 0", T + 0.45 + 0.08 * i, 0.35))
    T += 0.85

    # ------------------------------------------------------------------ 7 the check
    cx = CX["check"]
    P.append(pop(text(cx, TY, "THE CHECK", "nw-title", "middle"), T))
    # all leaves feed the grid
    gx0, gy0, cell = cx - 33, Y0 - 54, 22
    for ly in leaves1 + leaves2:
        P.append(link(CX["runs"] + 8 + (28 if ly in leaves1 else 20), ly, gx0 - 10, gy0 + 33, T + 0.05))
    P.append(node(gx0 - 10, gy0 + 33, T + 0.1))
    for i in range(3):
        P.append(pop(f'<rect class="nw-diag" x="{f(gx0 + i * cell)}" y="{f(gy0 + i * cell)}" width="{cell}" height="{cell}"/>', T + 0.3 + 0.08 * i))
    gridd = "".join(f"M{f(gx0)} {f(gy0 + k * cell)} h{3 * cell} M{f(gx0 + k * cell)} {f(gy0)} v{3 * cell} " for k in range(4))
    P.append(draw("nw-line", gridd, T + 0.15, 0.5))
    gm = gx0 + 1.5 * cell
    P.append(draw("nw-dimline", f"M{f(gx0)} {f(gy0 + 3 * cell + 11)} v6 M{f(gx0)} {f(gy0 + 3 * cell + 14)} H{f(gx0 + 3 * cell)} M{f(gx0 + 3 * cell)} {f(gy0 + 3 * cell + 11)} v6", T + 0.5, 0.25))
    P.append(pop(text(gm, gy0 + 3 * cell + 29, "informedness", "nw-dim", "middle"), T + 0.6))
    P.append(pop(text(gm, gy0 + 3 * cell + 42, "0.97 to 0.99", "nw-dim", "middle"), T + 0.6))
    P.append(draw("nw-dimline", f"M{f(gx0)} {f(gy0 - 15)} v6 M{f(gx0)} {f(gy0 - 12)} H{f(gx0 + 3 * cell)} M{f(gx0 + 3 * cell)} {f(gy0 - 15)} v6", T + 0.55, 0.25))
    P.append(pop(text(gm, gy0 - 30, "97.6 to 98.7 %", "nw-dim", "middle"), T + 0.65))
    P.append(pop(text(gm, gy0 - 17, "accreted in MC2", "nw-dim", "middle"), T + 0.65))
    # the simulation's own record returns as a faint dashed line along the foot
    ret_y = 346
    P.append(draw("nw-truth", f"M{f(CX['survey'])} {f(ey + 7)} V{f(ret_y)} H{f(gx0 + 33)} V{f(gy0 + 3 * cell + 24)}", T + 0.2, 0.9))
    P.append(pop(text(CX["survey"] + 10, ret_y - 4, "the galaxy's own record", "nw-note"), T + 0.5))
    T += 0.7

    svg = (
        f'<svg class="bp-svg nw-svg" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-labelledby="nw-t nw-d"><title id="nw-t">Workflow of Neitzel et al. 2025</title>'
        "<desc id=\"nw-d\">A pipeline of shapes, left to right: a simulated galaxy seen face-on and edge-on with the Sun's "
        "viewpoint; four sample clouds, two sharp and two blurred by errors; five feature rulers feeding one bundle; "
        "UMAP collapsing the bundle into a two-dimensional cloud, then a trustworthiness gate; HDBSCAN drawing two hulls, "
        "MC1 and MC2, with persistence bars above a baseline; a second run splitting MC1 into two and MC2 into three; "
        "and a three-by-three confusion grid with its diagonal filled, where the galaxy's own record arrives along a dashed "
        "return line.</desc>"
        + "<defs>" + "".join(f'<g id="{gid}">{body}</g>' for gid, _, body in DEFS.values()) + "</defs>"
        + "".join(P) + "</svg>\n"
    )
    out.write_text(svg)
    print(f"wrote {out} ({len(svg) / 1024:.1f} KB); {len(WORDS)} words on the drawing")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(Path(sys.argv[1])))
