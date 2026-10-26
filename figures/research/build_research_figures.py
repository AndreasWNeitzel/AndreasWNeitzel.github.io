"""Draw the wide figure of /research/arqueogal/. The JANUS page reuses FIG 1 (figures/fig1/build_fig1.py).

A schematic is drawn, not written: each stage is a pictogram with a title and at most one short
line, and the only numbers on a drawing are dimension lines. Every fact is from a public record:

arqueogal.svg  the FCT record of project 2024.15303.PEX and the public ArqueoGal repository: TESS
               seismic ages, Gaia astrometry and APOGEE abundances; the integration repository
               with provenance; JANUS for the labels and Starfold for the populations; a
               chrono-chemo-kinematic map of the disc; 2026 to 2027.

Usage: python3 figures/research/build_research_figures.py
Symbols are set in LaTeX through figures/texsvg.py (latex and dvisvgm must be installed).
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from texsvg import tex_glyphs  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "_includes/figures"
FS = 10.5
TY = 36
Y0 = 176

WORDS: list[str] = []
DEFS: dict = {}


def f(v: float) -> str:
    return f"{v:.1f}"


def draw(cls: str, d: str, t: float, dur: float = 0.35) -> str:
    return f'<path class="{cls} b-draw" style="--d:{t:.2f}s;--dur:{dur:.2f}s" pathLength="1" d="{d}"/>'


def pop(inner: str, t: float) -> str:
    return f'<g class="b-pop" style="--d:{t:.2f}s">{inner}</g>'


def text(x: float, y: float, s: str, cls: str, anchor: str = "start") -> str:
    WORDS.extend(s.split())
    return f'<text class="{cls}" x="{f(x)}" y="{f(y)}" text-anchor="{anchor}">{s}</text>'


def glyph(snippet: str, size: float) -> tuple[str, float]:
    key = (snippet, round(size, 2))
    if key not in DEFS:
        body, w = tex_glyphs(snippet, size)
        DEFS[key] = (f"rsg{len(DEFS)}", w, body)
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
    b = (x1 - x0) * 0.45
    return thread(f"M{f(x0)} {f(y0)} C{f(x0 + b)} {f(y0)} {f(x1 - b)} {f(y1)} {f(x1)} {f(y1)}", t)


def dim(x0: float, x1: float, y: float, label: str, t: float, above: bool = True) -> str:
    tick = 4
    s = draw("nw-ruler", f"M{f(x0)} {f(y - tick)} v{tick * 2} M{f(x0)} {f(y)} H{f(x1)} M{f(x1)} {f(y - tick)} v{tick * 2}", t, 0.25)
    ly = y - 7 if above else y + 14
    return s + pop(text((x0 + x1) / 2, ly, label, "nw-dim", "middle"), t + 0.1)


def box(x: float, y: float, w: float, h: float, t: float) -> str:
    return draw("nw-box", f"M{f(x)} {f(y)} h{f(w)} v{f(h)} h{f(-w)} Z", t, 0.4)


def svg(cls: str, w: int, h: int, label: str, body: list[str]) -> str:
    defs = "".join(f'<g id="{gid}">{b}</g>' for gid, _, b in DEFS.values())
    return (f'<svg class="bp-svg nw-svg {cls}" data-build viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" '
            f'role="img" aria-label="{label}"><defs>{defs}</defs>' + "".join(body) + "</svg>\n")


# ---------------------------------------------------------------- ArqueoGal
def arqueogal() -> str:
    global WORDS
    WORDS = []
    DEFS.clear()
    W, H = 1120, 392
    CX = {"data": 120, "repo": 360, "tools": 620, "map": 920}
    P: list[str] = []
    P.append(draw("nw-guide", f"M16 {f(Y0)} H1104", 0.0, 0.3))
    for cx in CX.values():
        P.append(draw("nw-guide", f"M{f(cx)} 46 V338", 0.05, 0.2))
    T = 0.25

    # 1 three sources
    cx = CX["data"]
    P.append(pop(text(cx, TY, "THREE SURVEYS", "nw-title", "middle"), T))
    rows = (("TESS", "seismic ages", Y0 - 70), ("Gaia DR3", "astrometry and orbits", Y0), ("APOGEE DR19", "abundances", Y0 + 70))
    for i, (nm, what, y) in enumerate(rows):
        P.append(box(cx - 70, y - 20, 140, 40, T + 0.1 * i))
        P.append(pop(text(cx - 60, y - 4, nm, "nw-body"), T + 0.15 + 0.1 * i))
        P.append(pop(text(cx - 60, y + 11, what, "nw-note"), T + 0.2 + 0.1 * i))
        P.append(node(cx + 76, y, T + 0.25 + 0.1 * i))
    T += 0.5

    # 2 the integration repository
    cx = CX["repo"]
    P.append(pop(text(cx, TY, "ARQUEOGAL REPOSITORY", "nw-title", "middle"), T))
    P.append(box(cx - 80, Y0 - 78, 160, 156, T))
    steps = ("selection", "corrections", "kinematics", "provenance")
    for i, s in enumerate(steps):
        y = Y0 - 54 + 34 * i
        P.append(draw("nw-line", f"M{f(cx - 60)} {f(y)} H{f(cx + 60)}", T + 0.1 + 0.08 * i, 0.3))
        P.append(pop(text(cx - 60, y - 5, s, "nw-note"), T + 0.15 + 0.08 * i))
    for _, _, y in rows:
        P.append(link(CX["data"] + 76, y, cx - 84, Y0, T + 0.05))
    P.append(pop(text(cx, Y0 + 100, "the catalogues, prepared once", "nw-body", "middle"), T + 0.4))
    P.append(node(cx + 84, Y0, T + 0.45))
    T += 0.5

    # 3 the two tools
    cx = CX["tools"]
    P.append(pop(text(cx, TY, "TWO TOOLS", "nw-title", "middle"), T))
    for i, (nm, what, y) in enumerate((("JANUS", "stellar labels, with reliability", Y0 - 46), ("Starfold", "populations, with recurrence", Y0 + 46))):
        P.append(box(cx - 90, y - 24, 180, 48, T + 0.1 * i))
        P.append(pop(text(cx - 78, y - 4, nm, "nw-body"), T + 0.15 + 0.1 * i))
        P.append(pop(text(cx - 78, y + 12, what, "nw-note"), T + 0.2 + 0.1 * i))
        P.append(link(CX["repo"] + 84, Y0, cx - 94, y, T + 0.05))
        P.append(node(cx + 96, y, T + 0.3 + 0.1 * i))
    P.append(pop(text(cx, Y0 + 100, "separate repositories, called by contract", "nw-body", "middle"), T + 0.4))
    T += 0.5

    # 4 the map of the disc: a face-on galaxy with a colour ramp of age, as construction
    cx = CX["map"]
    P.append(pop(text(cx, TY, "THE DISC, MAPPED", "nw-title", "middle"), T))
    for r in (24, 44, 64):
        P.append(draw("nw-line", f"M{f(cx - r)} {f(Y0)} a{r} {r * 0.42:.1f} 0 1 0 {2 * r} 0 a{r} {r * 0.42:.1f} 0 1 0 {-2 * r} 0", T + 0.1, 0.5))
    P.append(pop(f'<circle class="nw-obs" cx="{f(cx + 34)}" cy="{f(Y0 + 4)}" r="2.6"/>', T + 0.3))
    P.append(pop(text(cx + 34, Y0 + 20, "Sun", "nw-note", "middle"), T + 0.35))
    for i, lab in enumerate(("age", "chemistry", "motion")):
        P.append(pop(text(cx, Y0 + 100 + 14 * i, lab, "nw-note", "middle"), T + 0.4 + 0.05 * i))
    P.append(pop(text(cx, Y0 + 100 - 14, "star by star:", "nw-body", "middle"), T + 0.4))
    for y in (Y0 - 46, Y0 + 46):
        P.append(link(CX["tools"] + 96, y, cx - 68, Y0, T))
    P.append(dim(CX["data"] - 70, CX["map"] + 64, 352, "FCT exploratory project 2024.15303.PEX, February 2026 to August 2027", T + 0.5, above=False))

    label = ("Schematic of ArqueoGal: TESS seismic ages, Gaia astrometry and APOGEE abundances are prepared once in the "
             "integration repository, with selection, corrections, kinematics and provenance; JANUS supplies stellar labels "
             "and Starfold the populations; the result is a map of the Milky Way's disc by age, chemistry and motion, "
             "under the FCT exploratory project 2024.15303.PEX, February 2026 to August 2027.")
    out = svg("rs-arqueogal", W, H, label, P)
    print(f"arqueogal.svg: {len(WORDS)} words on the drawing")
    return out


def main() -> None:
    OUT.joinpath("arqueogal.svg").write_text(arqueogal())
    for n in ("arqueogal.svg",):
        print(f"wrote {OUT / n} ({OUT.joinpath(n).stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
