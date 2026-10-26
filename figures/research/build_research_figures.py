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
MONO_ADV = 0.6  # Geist Mono advance per character, in em


def fits(label: str, size: float, width: float) -> str:
    """Refuse a label wider than the room it has; the check runs at build time."""
    need = len(label) * MONO_ADV * size
    if need > width:
        raise ValueError(f"label too wide for {width:.0f}px: {label!r} needs {need:.0f}px")
    return label


def arqueogal() -> str:
    """One red giant's path through the project. Three lanes leave the star: its TESS light
    curve (task 2, then PARAM in task 4 for mass and age), its Gaia astrometry (task 3, the
    orbit) and its spectrum (task 3, APOGEE where it exists, else chemistry from JANUS). The
    lanes fill one row of the all-sky catalogue; Starfold (task 5) returns the population; the
    Galactic model (task 6) reads the catalogue and draws the map. Fill tells who built what:
    solid accent for the stages Andreas built, hatched where he takes part, outline for the
    team's. Facts from the FCT application 2024.15303.PEX and the kickoff of 16 February 2026."""
    global WORDS
    WORDS = []
    DEFS.clear()
    W, H = 1120, 560
    P: list[str] = []
    P.append('<pattern id="nw-hatch" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)">'
             '<path class="nw-hatch-line" d="M0 0 V6"/></pattern>')
    T = 0.0
    P.append(pop(text(20, 28, "ONE RED GIANT, THROUGH THE PROJECT", "nw-title"), T))
    P.append(draw("nw-guide", "M20 36 H1100", T, 0.4))

    L = (150.0, 270.0, 390.0)  # lane centres
    BH = 96.0
    XA, XB, WA = 100.0, 330.0, 190.0
    XC, WC = 560.0, 160.0
    XD, WD = 756.0, 184.0
    XE, WE = 968.0, 132.0
    FS_NOTE, FS_TITLE = 10.5, 11.0

    def stage(x, y, w, title, tag, kind, t):
        cls = {"me": "nw-box-me", "part": "nw-box-part", "team": "nw-box"}[kind]
        lines = tag if isinstance(tag, tuple) else (tag,)
        for ln in lines:
            fits(ln, FS_NOTE, w - 20)
        fits(title, FS_TITLE, w - 20)
        out = [draw(cls, f"M{f(x)} {f(y - BH / 2)} h{f(w)} v{f(BH)} h{f(-w)} Z", t, 0.4)]
        for k, ln in enumerate(lines):
            out.append(pop(text(x + 10, y - BH / 2 + 15 + 12 * k, ln, "nw-note"), t + 0.1))
        out.append(pop(text(x + 10, y + BH / 2 - 10, title, "nw-title"), t + 0.15))
        return out

    def note(x, y, label, room, t, anchor="start"):
        fits(label, FS_NOTE, room)
        return pop(text(x, y, label, "nw-note", anchor), t)

    # the star, and three rays leaving it
    SX, SY = 48.0, L[1]
    P.append(draw("nw-line", f"M{SX - 13} {SY} a13 13 0 1 0 26 0 a13 13 0 1 0 -26 0", T, 0.4))
    for a in range(0, 360, 45):
        r0, r1 = 17, 22 if a % 90 == 0 else 20
        P.append(draw("nw-line", f"M{f(SX + r0 * math.cos(math.radians(a)))} {f(SY - r0 * math.sin(math.radians(a)))} L{f(SX + r1 * math.cos(math.radians(a)))} {f(SY - r1 * math.sin(math.radians(a)))}", T + 0.05, 0.2))
    P.append(note(SX, SY - 36, "a red giant", 90, T + 0.2, "middle"))
    for y in L:
        P.append(thread(f"M{SX + 26} {SY} C{SX + 52} {SY}, {XA - 40} {f(y)}, {XA} {f(y)}", T + 0.2))
        P.append(node(XA, y, T + 0.3))
    T += 0.4

    # lane 1: the light curve and its oscillations (task 2), then PARAM (task 4)
    y = L[0]
    P += stage(XA, y, WA, "TESS LIGHT CURVE", "TASK 2", "team", T)
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
    P += stage(XB, y, WA, "PARAM: MASS AND AGE", "TASK 4", "team", T + 0.3)
    gx, gy = XB + 14, y - 30
    P.append(draw("nw-line", f"M{gx} {gy} V{gy + 44} H{gx + 52}", T + 0.5, 0.3))
    for k in range(4):
        xx = gx + 46 - 11 * k
        P.append(draw("nw-guide", f"M{xx} {gy + 42 - k} C{xx + 2} {gy + 30}, {xx - 7} {gy + 22}, {xx - 5} {gy + 16} C{xx - 3} {gy + 10}, {xx - 18} {gy + 6}, {xx - 24 - k} {gy + 1}", T + 0.55 + 0.04 * k, 0.4))
    P.append(draw("nw-gate", f"M{gx + 18} {gy + 20} h12 v10 h-12 Z", T + 0.7, 0.3))
    hx, hb = XB + 90, y + 18
    P.append(draw("nw-guide", f"M{hx} {hb} H{hx + 84}", T + 0.6, 0.2))
    P.append(pop(f'<path class="nw-band" d="M{hx + 32} {hb} V{hb - 12} H{hx + 54} V{hb} Z"/>', T + 0.8))
    P.append(draw("nw-line", f"M{hx} {hb} C{hx + 22} {hb}, {hx + 30} {hb - 6}, {hx + 36} {hb - 28} C{hx + 40} {hb - 40}, {hx + 48} {hb - 40}, {hx + 52} {hb - 28} C{hx + 58} {hb - 6}, {hx + 64} {hb}, {hx + 84} {hb}", T + 0.65, 0.6))

    # lane 2: Gaia astrometry (task 3), then the orbit
    y = L[1]
    P += stage(XA, y, WA, "GAIA ASTROMETRY", "TASK 3", "team", T + 0.2)
    sx, sy = XA + 40, y - 6
    P.append(pop(f'<circle class="nw-dot" cx="{f(sx)}" cy="{f(sy)}" r="3"/>', T + 0.4))
    P.append(draw("nw-line", f"M{sx + 6} {sy - 4} L{sx + 46} {sy - 26} M{sx + 38} {sy - 27} L{sx + 46} {sy - 26} L{sx + 42} {sy - 19}", T + 0.4, 0.4))
    P.append(draw("nw-guide-strong", f"M{sx - 30} {sy + 22} L{sx} {sy} L{sx + 30} {sy + 22} M{sx - 30} {sy + 22} H{sx + 30}", T + 0.45, 0.4))
    P.append(draw("nw-dimline", f"M{sx - 8} {sy + 13} a8 8 0 0 0 16 0", T + 0.5, 0.2))
    P.append(note(XA + 112, y - 14, "motion,", 70, T + 0.5))
    P.append(note(XA + 112, y - 2, "parallax", 70, T + 0.5))
    P.append(thread(f"M{XA + WA} {f(y)} H{XB}", T + 0.6))
    P.append(node(XA + WA, y, T + 0.6)); P.append(node(XB, y, T + 0.65))
    P += stage(XB, y, WA, "ORBIT IN THE GALAXY", "TASK 3", "me", T + 0.5)
    ox, oy = XB + 58, y - 4
    opts = []
    for k in range(181):
        th = 2 * math.pi * k / 180 * 3
        r = 26 + 10 * math.cos(1.37 * th)
        opts.append((ox + r * math.cos(th), oy + 0.5 * r * math.sin(th)))
    P.append(draw("nw-line-me", "M" + " L".join(f"{f(a)} {f(b)}" for a, b in opts), T + 0.7, 0.8))
    P.append(pop(f'<circle class="nw-obs" cx="{f(ox)}" cy="{f(oy)}" r="2.6"/>', T + 0.9))
    P.append(note(XB + 112, y - 14, "galpy,", 70, T + 0.8))
    P.append(note(XB + 112, y - 2, "actions", 70, T + 0.8))

    # lane 3: the spectrum (task 3), APOGEE where it exists, else JANUS
    y = L[2]
    P += stage(XA, y, WA, "SPECTRUM", "TASK 3", "team", T + 0.4)
    ax, ay = XA + 14, y - 26
    P.append(draw("nw-line", f"M{ax} {ay} H{ax + 70} " + " ".join(f"M{f(ax + 3 + 1.9 * k)} {ay} v{f(3 + 9 * abs(math.sin(k * 1.37) * math.cos(k * 0.41)))}" for k in range(35)), T + 0.6, 0.5))
    P.append(note(ax + 80, ay + 4, "APOGEE", 90, T + 0.7))
    bx, by = XA + 14, y + 18
    xp = [(bx + 2 * k, by - 14 * math.exp(-((k - 14) / 12) ** 2) * (1 + 0.15 * math.sin(k * 1.3))) for k in range(36)]
    P.append(draw("nw-line", "M" + " L".join(f"{f(a)} {f(b)}" for a, b in xp), T + 0.65, 0.5))
    P.append(draw("nw-guide", f"M{bx} {by} H{bx + 70}", T + 0.65, 0.2))
    P.append(note(bx + 80, by - 2, "Gaia XP", 90, T + 0.75))
    P.append(thread(f"M{XA + WA} {f(y)} H{XB}", T + 0.8))
    P.append(node(XA + WA, y, T + 0.8)); P.append(node(XB, y, T + 0.85))
    P += stage(XB, y, WA, "CHEMISTRY: JANUS", "TASK 3", "me", T + 0.7)
    nx, ny = XB + 16, y - 30
    cols = (nx, nx + 22, nx + 44)
    rows = (ny + 4, ny + 18, ny + 32, ny + 46)
    edges = " ".join(f"M{cols[a]} {ra} L{cols[a + 1]} {rb}" for a in range(2) for ra in rows for rb in rows)
    P.append(draw("nw-guide", edges, T + 0.9, 0.4))
    P.append(pop("".join(f'<circle class="nw-dot" cx="{c}" cy="{r}" r="2.4"/>' for c in cols for r in rows), T + 1.0))
    lx = XB + 84
    for k, (lab, wv) in enumerate((("[M/H]", 30), ("[α/M]", 18), ("[Fe/H]", 26), ("[Mg/H]", 22))):
        yy = ny + 6 + 13 * k
        P.append(note(lx, yy + 4, lab, 44, T + 1.0 + 0.05 * k))
        P.append(draw("nw-line-me", f"M{lx + 46} {yy} h{wv} M{lx + 46 + wv - 4} {yy - 3} v6", T + 1.05 + 0.05 * k, 0.3))
    T += 1.2

    # the catalogue: one row per star, filled band by band
    CY0, CY1 = L[0] - BH / 2, L[2] + BH / 2
    P.append(draw("nw-box", f"M{XC} {f(CY0)} h{WC} v{f(CY1 - CY0)} h{-WC} Z", T, 0.5))
    P.append(pop(text(XC + WC / 2, CY0 - 10, fits("THE ALL-SKY CATALOGUE", FS_TITLE, 200), "nw-title", "middle"), T + 0.1))
    P.append(note(XC + WC / 2, CY1 + 16, "one row per star", 160, T + 0.1, "middle"))
    bands = (("seismic", "D-Cat-a", "team", L[0] - 24), ("mass, age", "D-Cat-c", "team", L[0] + 24),
             ("orbit", "D-Cat-b", "me", L[1]), ("chemistry", "D-Cat-b", "me", L[2]), ("population", "D-Cat-d", "me", L[2] + 36))
    for k, (what, dl, kind, by) in enumerate(bands):
        if kind == "me":
            P.append(pop(f'<rect class="nw-band-me" x="{XC + 4}" y="{f(by - 8)}" width="{WC - 8}" height="16" rx="2"/>', T + 0.1 + 0.06 * k))
        P.append(note(XC + 10, by + 4, what, 90, T + 0.15 + 0.06 * k))
        P.append(note(XC + WC - 10, by + 4, dl, 60, T + 0.15 + 0.06 * k, "end"))
        if k:
            P.append(draw("nw-guide", f"M{XC + 6} {f(by - 18)} H{XC + WC - 6}", T + 0.1 + 0.06 * k, 0.25))
    ytop = L[0] - BH / 2 - 16
    P.append(thread(f"M{XA + WA} {L[0] - 30} C{XA + WA + 22} {L[0] - 30}, {XB - 30} {ytop}, {XB} {ytop} H{XC - 24} C{XC - 10} {ytop}, {XC - 10} {L[0] - 24}, {XC} {L[0] - 24}", T))
    P.append(node(XA + WA, L[0] - 30, T))
    P.append(thread(f"M{XB + WA} {L[0]} C{XB + WA + 16} {L[0]}, {XC - 16} {L[0] + 24}, {XC} {L[0] + 24}", T + 0.05))
    P.append(thread(f"M{XB + WA} {L[1]} H{XC}", T + 0.1))
    P.append(thread(f"M{XB + WA} {L[2]} H{XC}", T + 0.15))
    for yy in (L[0] - 24, L[0] + 24, L[1], L[2]):
        P.append(node(XC, yy, T + 0.2))
    P.append(node(XB + WA, L[0], T)); P.append(node(XB + WA, L[1], T)); P.append(node(XB + WA, L[2], T))
    T += 0.4

    # Starfold reads the row and returns the population
    y = L[1]
    P += stage(XD, y, WD, "STARFOLD: POPULATION", "TASK 5", "me", T)
    gold = math.pi * (3 - math.sqrt(5))
    for g, (cx, cy, axx, ayy, tilt, n) in enumerate(((XD + 40, y - 12, 22, 11, -14, 7), (XD + 96, y - 13, 20, 10, 12, 6), (XD + 66, y + 12, 28, 11, 4, 8))):
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
    P.append(note(XD + 112, y + 18, "32 refits", 62, T + 0.5))
    P.append(thread(f"M{XC + WC} {f(y)} H{XD}", T))
    P.append(node(XC + WC, y, T)); P.append(node(XD, y, T + 0.05))
    P.append(thread(f"M{XD} {f(y + 30)} C{XD - 30} {f(y + 30)}, {XC + WC + 30} {f(L[2] + 36)}, {XC + WC} {f(L[2] + 36)}", T + 0.4))
    P.append(node(XD, y + 30, T + 0.4)); P.append(node(XC + WC, L[2] + 36, T + 0.5))
    T += 0.5

    # the Galactic model reads the catalogue and draws the map
    P += stage(XE, y, WE, "THE DISC, MAPPED", "TASK 6", "part", T)
    mx, my = XE + WE / 2, y - 4
    for r in (16, 30, 44):
        P.append(draw("nw-line", f"M{f(mx - r)} {f(my)} a{r} {r * 0.4:.1f} 0 1 0 {2 * r} 0 a{r} {r * 0.4:.1f} 0 1 0 {-2 * r} 0", T + 0.1, 0.5))
    P.append(pop(f'<circle class="nw-obs" cx="{f(mx + 24)}" cy="{f(my + 3)}" r="2.6"/>', T + 0.3))
    P.append(thread(f"M{XD + WD} {f(y)} H{XE}", T))
    P.append(node(XD + WD, y, T)); P.append(node(XE, y, T + 0.05))
    T += 0.4

    # the timeline of deliverables
    RY = 500
    x0, x1 = 40, 1080
    mx_ = lambda m: x0 + (x1 - x0) * m / 18
    P.append(draw("nw-ruler", f"M{x0} {RY - 5} v10 M{x0} {RY} H{x1} M{x1} {RY - 5} v10", T, 0.5))
    P.append(note(x0, RY + 20, "Feb 2026", 60, T + 0.1))
    P.append(note(x1, RY + 20, "Aug 2027", 60, T + 0.1, "end"))
    marks = ((5, "D-Cat-a", "Jul 2026"), (6, "D-Cat-b · D7.1", "Aug 2026"), (10, "D-Cat-c · D5.1", "Dec 2026"), (12, "D-Cat-d", "Feb 2027"), (18, "D6.1", "Aug 2027"))
    for k, (m, lab, when) in enumerate(marks):
        px = mx_(m)
        above = k % 2 == 0
        P.append(draw("nw-ruler", f"M{f(px)} {RY - 5} v10", T + 0.1 + 0.08 * k, 0.2))
        P.append(pop(text(px, RY - 12 if above else RY + 34, lab, "nw-dim", "end" if m == 18 else "middle"), T + 0.15 + 0.08 * k))
        if m != 18:
            P.append(note(px, RY + 20 if above else RY - 26, when, 70, T + 0.15 + 0.08 * k, "middle"))
    P.append(pop(text((x0 + x1) / 2, RY + 52, "FCT exploratory project 2024.15303.PEX, 18 months · task 1 data management and task 7 outreach alongside", "nw-dim", "middle"), T + 0.5))

    label = ("Schematic of ArqueoGal as one red giant's path: its TESS light curve gives oscillations (task 2) and, with PARAM, "
             "mass and age (task 4); its Gaia astrometry gives an orbit (task 3); its spectrum gives chemistry, from APOGEE where "
             "it exists and from the network JANUS otherwise (task 3). The three fill one row of the all-sky catalogue; Starfold "
             "returns the population (task 5); the Galactic model reads the catalogue and draws the disc (task 6). Stages filled "
             "in the accent are the ones Andreas Neitzel built, the hatched stage is one he takes part in, outlined stages are the "
             "team's. A timeline carries the deliverables from February 2026 to August 2027.")
    out = svg("rs-arqueogal", W, H, label, P)
    print(f"arqueogal.svg: {len(WORDS)} words on the drawing")
    return out


def main() -> None:
    OUT.joinpath("arqueogal.svg").write_text(arqueogal())
    for n in ("arqueogal.svg",):
        print(f"wrote {OUT / n} ({OUT.joinpath(n).stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
