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
    """One red giant's path through the project. Three lanes leave the star: its TESS light
    curve (task 2, then PARAM in task 4 for mass and age), its Gaia astrometry (task 3, the orbit
    from my kinematics code) and its spectrum (task 3, APOGEE where it exists, else chemistry
    from JANUS). The lanes fill one row of the all-sky catalogue; Starfold (task 5) returns the
    population; the Galactic model (task 6) reads the catalogue and draws the map. Stages the
    team runs are in ink; the ones I built are filled in the accent. Facts from the FCT
    application 2024.15303.PEX and the kickoff of 16 February 2026."""
    global WORDS
    WORDS = []
    DEFS.clear()
    W, H = 1120, 560
    P: list[str] = []
    T = 0.0
    P.append(pop(text(20, 28, "ONE RED GIANT, THROUGH THE PROJECT", "nw-title"), T))
    P.append(pop(text(300, 28, "tasks 1 and 7, data management and outreach, run alongside", "nw-note"), T + 0.05))
    P.append(pop(f'<rect class="nw-key-me" x="846" y="20" width="9" height="9"/>', T + 0.1))
    P.append(pop(text(861, 28, "stages I built", "nw-note"), T + 0.1))
    P.append(pop(f'<rect class="nw-key-team" x="964" y="20" width="9" height="9"/>', T + 0.1))
    P.append(pop(text(979, 28, "the team's stages", "nw-note"), T + 0.1))
    P.append(draw("nw-guide", "M20 36 H1100", T, 0.4))

    L = (150.0, 270.0, 390.0)  # lane centres
    BH = 96.0
    XA, XB, WA = 100.0, 330.0, 190.0
    XC, WC = 560.0, 160.0
    XD, WD = 760.0, 170.0
    XE, WE = 968.0, 132.0

    def stage(x, y, w, title, tag, mine, t):
        cls = "nw-box-me" if mine else "nw-box"
        out = [draw(cls, f"M{f(x)} {f(y - BH / 2)} h{f(w)} v{f(BH)} h{f(-w)} Z", t, 0.4)]
        out.append(pop(text(x + 10, y - BH / 2 + 15, tag, "nw-me" if mine else "nw-note"), t + 0.1))
        out.append(pop(text(x + 10, y + BH / 2 - 10, title, "nw-title"), t + 0.15))
        return out

    # the star, and three rays leaving it
    SX, SY = 48.0, L[1]
    P.append(draw("nw-line", f"M{SX - 13} {SY} a13 13 0 1 0 26 0 a13 13 0 1 0 -26 0", T, 0.4))
    for a in range(0, 360, 45):
        r0, r1 = 17, 22 if a % 90 == 0 else 20
        P.append(draw("nw-line", f"M{f(SX + r0 * math.cos(math.radians(a)))} {f(SY - r0 * math.sin(math.radians(a)))} L{f(SX + r1 * math.cos(math.radians(a)))} {f(SY - r1 * math.sin(math.radians(a)))}", T + 0.05, 0.2))
    P.append(pop(text(SX, SY - 34, "a red giant", "nw-note", "middle"), T + 0.2))
    for y in L:
        P.append(thread(f"M{SX + 24} {SY} C{SX + 50} {SY}, {XA - 40} {f(y)}, {XA} {f(y)}", T + 0.2))
        P.append(node(XA, y, T + 0.3))
    T += 0.4

    # lane 1: the light curve and its oscillations (task 2), then PARAM (task 4)
    y = L[0]
    P += stage(XA, y, WA, "TESS LIGHT CURVE", "TASK 2 · lead Campante", False, T)
    x0, yc = XA + 12, y - 8
    pts = [(x0 + 1.9 * i, yc + 8 * math.sin(i * 0.9) * (0.6 + 0.4 * math.sin(i * 0.17)) + 3 * math.sin(i * 2.7)) for i in range(46)]
    P.append(draw("nw-line", "M" + " L".join(f"{f(a)} {f(b)}" for a, b in pts), T + 0.2, 0.6))
    cx0 = XA + 118
    P.append(draw("nw-guide", f"M{cx0 - 4} {y + 14} H{cx0 + 64}", T + 0.3, 0.2))
    for k in range(9):
        h = 5 + 24 * math.exp(-((k - 4) / 2.2) ** 2)
        P.append(draw("nw-line", f"M{cx0 + 7 * k} {y + 14} v{-h:.1f}", T + 0.3 + 0.02 * k, 0.2))
    P.append(thread(f"M{XA + WA} {f(y)} H{XB}", T + 0.4))
    P.append(node(XA + WA, y, T + 0.4)); P.append(node(XB, y, T + 0.45))
    P += stage(XB, y, WA, "PARAM: MASS AND AGE", "TASK 4 · leads Monteiro, Bossini", False, T + 0.3)
    gx, gy = XB + 14, y - 30
    P.append(draw("nw-line", f"M{gx} {gy} V{gy + 44} H{gx + 52}", T + 0.5, 0.3))
    for k in range(4):
        xx = gx + 46 - 11 * k
        P.append(draw("nw-guide", f"M{xx} {gy + 42 - k} C{xx + 2} {gy + 30}, {xx - 7} {gy + 22}, {xx - 5} {gy + 16} C{xx - 3} {gy + 10}, {xx - 18} {gy + 6}, {xx - 24 - k} {gy + 1}", T + 0.55 + 0.04 * k, 0.4))
    P.append(draw("nw-gate", f"M{gx + 18} {gy + 20} h12 v10 h-12 Z", T + 0.7, 0.3))
    hx, hb = XB + 90, y + 14
    P.append(draw("nw-guide", f"M{hx} {hb} H{hx + 84}", T + 0.6, 0.2))
    P.append(pop(f'<path class="nw-band" d="M{hx + 32} {hb} V{hb - 12} H{hx + 54} V{hb} Z"/>', T + 0.8))
    P.append(draw("nw-line", f"M{hx} {hb} C{hx + 22} {hb}, {hx + 30} {hb - 6}, {hx + 36} {hb - 32} C{hx + 40} {hb - 46}, {hx + 48} {hb - 46}, {hx + 52} {hb - 32} C{hx + 58} {hb - 6}, {hx + 64} {hb}, {hx + 84} {hb}", T + 0.65, 0.6))
    # PARAM also takes the luminosity from the astrometry and the temperature from the spectrum
    for yy in (L[1], L[2]):
        P.append(draw("nw-guide-strong", f"M{XA + WA} {f(yy - 30)} C{XA + WA + 26} {f(yy - 30)}, {XB + 8} {f(y + BH / 2 + 40)}, {XB + 8} {f(y + BH / 2)}", T + 0.5, 0.5))

    # lane 2: Gaia astrometry (task 3), then the orbit from my kinematics code
    y = L[1]
    P += stage(XA, y, WA, "GAIA ASTROMETRY", "TASK 3 · lead Bossini", False, T + 0.2)
    sx, sy = XA + 40, y - 6
    P.append(pop(f'<circle class="nw-dot" cx="{f(sx)}" cy="{f(sy)}" r="3"/>', T + 0.4))
    P.append(draw("nw-line", f"M{sx + 6} {sy - 4} L{sx + 46} {sy - 26} M{sx + 38} {sy - 27} L{sx + 46} {sy - 26} L{sx + 42} {sy - 19}", T + 0.4, 0.4))
    P.append(draw("nw-guide-strong", f"M{sx - 30} {sy + 22} L{sx} {sy} L{sx + 30} {sy + 22} M{sx - 30} {sy + 22} H{sx + 30}", T + 0.45, 0.4))
    P.append(draw("nw-dimline", f"M{sx - 8} {sy + 13} a8 8 0 0 0 16 0", T + 0.5, 0.2))
    P.append(pop(text(XA + 112, y - 20, "proper", "nw-note"), T + 0.5))
    P.append(pop(text(XA + 112, y - 8, "motion,", "nw-note"), T + 0.5))
    P.append(pop(text(XA + 112, y + 4, "parallax", "nw-note"), T + 0.5))
    P.append(thread(f"M{XA + WA} {f(y)} H{XB}", T + 0.6))
    P.append(node(XA + WA, y, T + 0.6)); P.append(node(XB, y, T + 0.65))
    P += stage(XB, y, WA, "ORBIT IN THE GALAXY", "TASK 3 · my kinematics code", True, T + 0.5)
    ox, oy = XB + 58, y - 4
    opts = []
    for k in range(181):
        th = 2 * math.pi * k / 180 * 3
        r = 26 + 10 * math.cos(1.37 * th)
        opts.append((ox + r * math.cos(th), oy + 0.5 * r * math.sin(th)))
    P.append(draw("nw-line-me", "M" + " L".join(f"{f(a)} {f(b)}" for a, b in opts), T + 0.7, 0.8))
    P.append(pop(f'<circle class="nw-obs" cx="{f(ox)}" cy="{f(oy)}" r="2.6"/>', T + 0.9))
    P.append(pop(text(XB + 112, y - 14, "galpy,", "nw-note"), T + 0.8))
    P.append(pop(text(XB + 112, y - 2, "actions,", "nw-note"), T + 0.8))
    P.append(pop(text(XB + 112, y + 10, "provenance", "nw-note"), T + 0.8))

    # lane 3: the spectrum (task 3), APOGEE where it exists, else JANUS
    y = L[2]
    P += stage(XA, y, WA, "SPECTRUM", "TASK 3 · lead Bossini", False, T + 0.4)
    ax, ay = XA + 14, y - 26
    P.append(draw("nw-line", f"M{ax} {ay} H{ax + 70} " + " ".join(f"M{f(ax + 3 + 1.9 * k)} {ay} v{f(3 + 9 * abs(math.sin(k * 1.37) * math.cos(k * 0.41)))}" for k in range(35)), T + 0.6, 0.5))
    P.append(pop(text(ax + 78, ay + 4, "APOGEE", "nw-note"), T + 0.7))
    bx, by = XA + 14, y + 18
    xp = [(bx + 2 * k, by - 14 * math.exp(-((k - 14) / 12) ** 2) * (1 + 0.15 * math.sin(k * 1.3))) for k in range(36)]
    P.append(draw("nw-line", "M" + " L".join(f"{f(a)} {f(b)}" for a, b in xp), T + 0.65, 0.5))
    P.append(draw("nw-guide", f"M{bx} {by} H{bx + 70}", T + 0.65, 0.2))
    P.append(pop(text(bx + 78, by - 2, "Gaia XP", "nw-note"), T + 0.75))
    P.append(thread(f"M{XA + WA} {f(y)} H{XB}", T + 0.8))
    P.append(node(XA + WA, y, T + 0.8)); P.append(node(XB, y, T + 0.85))
    P += stage(XB, y, WA, "CHEMISTRY", "TASK 3 · JANUS, my network", True, T + 0.7)
    nx, ny = XB + 16, y - 30
    cols = (nx, nx + 22, nx + 44)
    rows = (ny + 4, ny + 18, ny + 32, ny + 46)
    edges = " ".join(f"M{cols[a]} {ra} L{cols[a + 1]} {rb}" for a in range(2) for ra in rows for rb in rows)
    P.append(draw("nw-guide", edges, T + 0.9, 0.4))
    P.append(pop("".join(f'<circle class="nw-dot" cx="{c}" cy="{r}" r="2.4"/>' for c in cols for r in rows), T + 1.0))
    lx = XB + 84
    for k, (lab, wv) in enumerate((("[M/H]", 30), ("[α/M]", 18), ("[Fe/H]", 26), ("[Mg/H]", 22))):
        yy = ny + 6 + 13 * k
        P.append(pop(text(lx, yy + 4, lab, "nw-note"), T + 1.0 + 0.05 * k))
        P.append(draw("nw-line-me", f"M{lx + 46} {yy} h{wv} M{lx + 46 + wv - 4} {yy - 3} v6", T + 1.05 + 0.05 * k, 0.3))
    T += 1.2

    # the catalogue: one row per star, filled band by band
    CY0, CY1 = L[0] - BH / 2, L[2] + BH / 2
    P.append(draw("nw-box", f"M{XC} {f(CY0)} h{WC} v{f(CY1 - CY0)} h{-WC} Z", T, 0.5))
    P.append(pop(text(XC + WC / 2, CY0 - 10, "THE ALL-SKY CATALOGUE", "nw-title", "middle"), T + 0.1))
    P.append(pop(text(XC + WC / 2, CY1 + 16, "one row per star", "nw-note", "middle"), T + 0.1))
    bands = (("seismic", "D-Cat-a", False, L[0] - 24), ("mass, age", "D-Cat-c", False, L[0] + 24),
             ("orbit", "D-Cat-b", True, L[1]), ("chemistry", "D-Cat-b", True, L[2]), ("population", "D-Cat-d", True, L[2] + 36))
    for k, (what, dl, mine, by) in enumerate(bands):
        P.append(pop(text(XC + 10, by + 4, what, "nw-me" if mine else "nw-note"), T + 0.15 + 0.06 * k))
        P.append(pop(text(XC + WC - 10, by + 4, dl, "nw-note", "end"), T + 0.15 + 0.06 * k))
        if k:
            P.append(draw("nw-guide", f"M{XC + 6} {f(by - 18)} H{XC + WC - 6}", T + 0.1 + 0.06 * k, 0.25))
    # the lanes land on their bands
    P.append(thread(f"M{XA + WA} {L[0]} C{XA + WA + 20} {L[0]}, {XC - 20} {L[0] - 24}, {XC} {L[0] - 24}", T))
    P.append(thread(f"M{XB + WA} {L[0]} C{XB + WA + 16} {L[0]}, {XC - 16} {L[0] + 24}, {XC} {L[0] + 24}", T + 0.05))
    P.append(thread(f"M{XB + WA} {L[1]} H{XC}", T + 0.1))
    P.append(thread(f"M{XB + WA} {L[2]} H{XC}", T + 0.15))
    for yy in (L[0] - 24, L[0] + 24, L[1], L[2]):
        P.append(node(XC, yy, T + 0.2))
    P.append(node(XB + WA, L[0], T)); P.append(node(XB + WA, L[1], T)); P.append(node(XB + WA, L[2], T))
    T += 0.4

    # Starfold reads the row and returns the population
    y = L[1]
    P += stage(XD, y, WD, "STARFOLD: POPULATION", "TASK 5 · Campante, Miglio", True, T)
    gold = math.pi * (3 - math.sqrt(5))
    for g, (cx, cy, axx, ayy, tilt, n) in enumerate(((XD + 40, y - 20, 22, 12, -14, 7), (XD + 96, y - 22, 20, 11, 12, 6), (XD + 66, y + 6, 28, 12, 4, 8))):
        th = math.radians(tilt)
        hull = []
        for kk in range(36):
            u = 2 * math.pi * kk / 36
            r = 1 + 0.07 * math.sin(2 * u + g) + 0.05 * math.sin(3 * u + 2 * g)
            px, py = axx * r * math.cos(u), ayy * r * math.sin(u)
            hull.append((cx + px * math.cos(th) - py * math.sin(th), cy + px * math.sin(th) + py * math.cos(th)))
        P.append(draw("nw-hull", "M" + " L".join(f"{f(a)} {f(b)}" for a, b in hull) + " Z", T + 0.2 + 0.1 * g, 0.4))
        dots = []
        for kk in range(n):
            rr = 0.7 * math.sqrt((kk + 0.5) / n)
            px, py = axx * rr * math.cos(kk * gold + g), ayy * rr * math.sin(kk * gold + g)
            dots.append(f'<circle class="nw-dot" cx="{f(cx + px * math.cos(th) - py * math.sin(th))}" cy="{f(cy + px * math.sin(th) + py * math.cos(th))}" r="2.2"/>')
        P.append(pop("".join(dots), T + 0.3 + 0.1 * g))
    P.append(pop(text(XD + 112, y + 18, "32 refits", "nw-note"), T + 0.5))
    P.append(thread(f"M{XC + WC} {f(y)} H{XD}", T))
    P.append(node(XC + WC, y, T)); P.append(node(XD, y, T + 0.05))
    # and back into the row, as its last band
    P.append(thread(f"M{XD} {f(y + 30)} C{XD - 30} {f(y + 30)}, {XC + WC + 30} {f(L[2] + 36)}, {XC + WC} {f(L[2] + 36)}", T + 0.4))
    P.append(node(XD, y + 30, T + 0.4)); P.append(node(XC + WC, L[2] + 36, T + 0.5))
    T += 0.5

    # the Galactic model reads the catalogue and draws the map
    P += stage(XE, y, WE, "THE DISC, MAPPED", "TASK 6 · with me", False, T)
    mx, my = XE + WE / 2, y - 6
    for r in (16, 30, 44):
        P.append(draw("nw-line", f"M{f(mx - r)} {f(my)} a{r} {r * 0.4:.1f} 0 1 0 {2 * r} 0 a{r} {r * 0.4:.1f} 0 1 0 {-2 * r} 0", T + 0.1, 0.5))
    P.append(pop(f'<circle class="nw-obs" cx="{f(mx + 24)}" cy="{f(my + 3)}" r="2.6"/>', T + 0.3))
    P.append(thread(f"M{XD + WD} {f(y)} H{XE}", T))
    P.append(node(XD + WD, y, T)); P.append(node(XE, y, T + 0.05))
    T += 0.4

    # the timeline of deliverables, with tasks 1 and 7 at its ends
    RY = 500
    x0, x1 = 40, 1080
    mx_ = lambda m: x0 + (x1 - x0) * m / 18
    P.append(draw("nw-ruler", f"M{x0} {RY - 5} v10 M{x0} {RY} H{x1} M{x1} {RY - 5} v10", T, 0.5))
    P.append(pop(text(x0, RY + 20, "Feb 2026", "nw-note"), T + 0.1))
    P.append(pop(text(x1, RY + 20, "Aug 2027", "nw-note", "end"), T + 0.1))
    marks = ((5, "D-Cat-a", "Jul 2026"), (6, "D-Cat-b · D7.1", "Aug 2026"), (10, "D-Cat-c · D5.1", "Dec 2026"), (12, "D-Cat-d", "Feb 2027"), (18, "D6.1", "Aug 2027"))
    for k, (m, lab, when) in enumerate(marks):
        px = mx_(m)
        above = k % 2 == 0
        P.append(draw("nw-ruler", f"M{f(px)} {RY - 5} v10", T + 0.1 + 0.08 * k, 0.2))
        P.append(pop(text(px, RY - 12 if above else RY + 34, lab, "nw-dim", "end" if m == 18 else "middle"), T + 0.15 + 0.08 * k))
        if m != 18:
            P.append(pop(text(px, RY + 20 if above else RY - 26, when, "nw-note", "middle"), T + 0.15 + 0.08 * k))
    P.append(pop(text((x0 + x1) / 2, RY + 52, "FCT exploratory project 2024.15303.PEX, PI Campante, 18 months", "nw-dim", "middle"), T + 0.5))

    label = ("Schematic of ArqueoGal as one red giant's path: its TESS light curve gives oscillations (task 2) and, with PARAM, "
             "mass and age (task 4); its Gaia astrometry gives an orbit (task 3, from Andreas Neitzel's kinematics code); its "
             "spectrum gives chemistry, from APOGEE for one star in ten and from his network JANUS for the rest (task 3). "
             "The three fill one row of the all-sky catalogue; his package Starfold returns the population (task 5); the "
             "Galactic model reads the catalogue and draws the disc (task 6). Stages he built are filled in the accent colour. "
             "A timeline carries the deliverables from February 2026 to August 2027, with task 1 and task 7 at its ends.")
    out = svg("rs-arqueogal", W, H, label, P)
    print(f"arqueogal.svg: {len(WORDS)} words on the drawing")
    return out


def main() -> None:
    OUT.joinpath("arqueogal.svg").write_text(arqueogal())
    for n in ("arqueogal.svg",):
        print(f"wrote {OUT / n} ({OUT.joinpath(n).stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
