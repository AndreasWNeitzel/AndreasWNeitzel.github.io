"""Build the HAYDNsim figures for /software/haydnsim/.

haydn-pipeline.svg   The six stages of HAYDNsim as pictograms, after the flowchart on the TASC10/KASC17
                     poster (Neitzel et al. 2026, doi:10.5281/zenodo.23263454) and slide 6 of the DFA
                     Week 2026 talk; the instrument strip is from slide 2 of that talk. Outline means
                     schematic.
haydn-crowding.svg   The share of each cluster's stars whose light is mostly from its neighbours, the
                     seven clusters printed on the poster. Filled bars mean data.

Everything these figures print is on the public poster or in the public talk. The pipeline's own
field, detector and noise results stay out until the paper is submitted.

Usage: python3 figures/haydnsim/build_haydn_figures.py
Needs latex and dvisvgm on the path for the typeset symbols (figures/texsvg.py).
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "figures"))
from texsvg import tex_glyphs  # noqa: E402

OUT = ROOT / "_includes/figures"
PICTOS = __import__("json").loads((ROOT / "figures/kit/pictos.json").read_text())

GOLDEN = math.pi * (3 - math.sqrt(5))

# 47 Tuc King-profile shape from Harris (2010), used only to draw the profile pictogram
R_CORE_ARCSEC = 0.36 * 60.0
CONCENTRATION = 2.07
R_TIDAL_ARCSEC = R_CORE_ARCSEC * 10 ** CONCENTRATION

# public per-cluster fractions of stars with SPR > 0.5, poster bar chart (per cent)
FRACTIONS = [("47 Tuc", 40), ("NGC 6752", 36), ("M54", 36), ("M22", 12), ("omega Cen", 11), ("NGC 6397", 7), ("M4", 3)]



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


def king(r: float) -> float:
    """King (1962) surface density shape, amplitude one."""
    a = 1.0 / math.sqrt(1.0 + (r / R_CORE_ARCSEC) ** 2)
    b = 1.0 / math.sqrt(1.0 + (R_TIDAL_ARCSEC / R_CORE_ARCSEC) ** 2)
    return (a - b) ** 2


def node(x: float, y: float, t: float, k: float = 6.0) -> str:
    return pop(f'<rect class="hy-node" x="{f(x - k / 2)}" y="{f(y - k / 2)}" width="{f(k)}" height="{f(k)}"/>', t)


def thread(d: str, t: float, cls: str = "ray flowray hy-thread") -> str:
    return pop(f'<path class="{cls}" d="{d}"/>', t)


def _rng(seed):
    st = [seed]

    def r():
        st[0] = (st[0] * 48271) % 2147483647
        return st[0] / 2147483647
    return r


def pic_archive(x: float, y: float, t: float) -> list[str]:
    """The cluster on the sky: Gaia's stars resolved in the outskirts, HST's square field on the
    crowded core, the catalogue entries beside them."""
    p = []
    cx, cy, R = x + 58, y + 44, 36
    rnd = _rng(5)
    out, core = [], []
    for i in range(260):
        r = R * (rnd() ** 1.9)
        a = rnd() * 2 * math.pi
        px, py = cx + r * math.cos(a), cy + r * math.sin(a)
        (core if abs(px - cx) < 13 and abs(py - cy) < 13 else out).append((px, py))
    p.append(pop("".join(f'<circle class="hy-dot" cx="{f(px)}" cy="{f(py)}" r="0.9"/>' for px, py in out if math.hypot(px - cx, py - cy) > 13), t))
    p.append(pop("".join(f'<circle class="hy-dot-acc" cx="{f(px)}" cy="{f(py)}" r="0.7"/>' for px, py in core), t + 0.1))
    p.append(draw("hy-pic-dash", f"M{f(cx + R)} {f(cy)} A{R} {R} 0 1 1 {f(cx - R)} {f(cy)} A{R} {R} 0 1 1 {f(cx + R)} {f(cy)}", t, 0.4))
    p.append(draw("hy-pic-strong", f"M{f(cx - 14)} {f(cy - 14)} h28 v28 h-28 Z", t + 0.15, 0.3))
    p.append(text(cx - R, y + 4, "Gaia", "hy-mini", t + 0.2))
    p.append(draw("hy-pic", f"M{f(cx - 14)} {f(cy)} H{f(cx - R - 6)}", t + 0.2, 0.2))
    p.append(text(cx - R - 8, cy + 3, "HST", "hy-mini", t + 0.2, "end"))
    # four catalogues as cards
    for i, lab in enumerate(("Harris", "Baumgardt", "Hunt", "Forbes")):
        yy = y + 8 + i * 20
        p.append(draw("hy-pic", f"M{x + 100} {yy} h54 v14 h-54 Z", t + 0.2 + 0.05 * i, 0.25))
        p.append(text(x + 104, yy + 10, lab, "hy-mini", t + 0.3 + 0.05 * i))
    return p


def pic_threshold(x: float, y: float, t: float) -> list[str]:
    """Star counts against magnitude for Gaia in the outskirts and HST in the core; the window
    where both are complete is shaded."""
    x0, x1, yb, yt = x + 6, x + 146, y + 76, y + 6
    p = [draw("hy-axis-thin", f"M{x0} {yt} V{yb} H{x1}", t, 0.3)]
    def lf(m, turn):  # rising counts that roll over past the completeness limit
        return 10 ** (0.32 * m) / (1 + math.exp((m - turn) / 0.35))
    ms = [10 + 12 * i / 120 for i in range(121)]
    for turn, cls in ((18.5, "hy-pic"), (21.0, "hy-pic-strong")):
        vals = [lf(m, turn) for m in ms]
        top = max(lf(m, 21.0) for m in ms)
        pts = [(x0 + (x1 - x0) * i / 120, yb - (yb - yt) * math.log10(1 + 9 * v / top)) for i, v in enumerate(vals)]
        p.append(draw(cls, "M" + " L".join(f"{f(a)} {f(b)}" for a, b in pts), t + 0.1, 0.5))
    wx0 = x0 + (x1 - x0) * (15.0 - 10) / 12
    wx1 = x0 + (x1 - x0) * (18.0 - 10) / 12
    p.append(pop(f'<rect class="hy-window" x="{f(wx0)}" y="{yt}" width="{f(wx1 - wx0)}" height="{yb - yt}"/>', t + 0.3))
    p.append(text(x1, yb + 11, "G", "hy-mini", t + 0.3, "end"))
    p.append(text(wx0 - 3, y + 66, "Gaia", "hy-mini", t + 0.35, "end"))
    p.append(text(x0 + 116, y + 10, "HST", "hy-mini", t + 0.35, "end"))
    return p


def pic_king(x: float, y: float, t: float) -> list[str]:
    """Surface density against radius on log axes: HST counts in the core, Gaia counts outside,
    the King profile through them, the normalisation annulus shaded."""
    x0, x1, yb, yt = x + 6, x + 146, y + 76, y + 6
    p = [draw("hy-axis-thin", f"M{x0} {yt} V{yb} H{x1}", t, 0.3)]
    lr0, lr1 = math.log10(2.0), math.log10(2500.0)
    def X(r):
        return x0 + (x1 - x0) * (math.log10(r) - lr0) / (lr1 - lr0)
    def Y(v):
        return yt + (yb - yt) * (-math.log10(v)) / 5.0
    pts = [(X(10 ** (lr0 + (lr1 - lr0) * i / 80)), Y(king(10 ** (lr0 + (lr1 - lr0) * i / 80)))) for i in range(80)]
    pts = [(a, b) for a, b in pts if b <= yb]
    xa, xb = X(50), X(100)
    p.append(pop(f'<rect class="hy-window" x="{f(xa)}" y="{yt}" width="{f(xb - xa)}" height="{yb - yt}"/>', t + 0.1))
    p.append(draw("hy-pic-strong", "M" + " L".join(f"{f(a)} {f(b)}" for a, b in pts), t + 0.15, 0.5))
    rnd = _rng(9)
    marks = []
    for r in (3, 5, 8, 13, 20, 32, 50, 80):  # HST in the core: triangles
        v = king(r) * (1 + 0.12 * (rnd() - 0.5))
        xx, yy = X(r), Y(v)
        marks.append(f'<path class="hy-mark-h" d="M{f(xx)} {f(yy - 2.6)} L{f(xx + 2.4)} {f(yy + 1.6)} L{f(xx - 2.4)} {f(yy + 1.6)} Z"/>')
    for r in (60, 100, 160, 250, 400, 630, 1000, 1500):  # Gaia outside: circles
        v = king(r) * (1 + 0.2 * (rnd() - 0.5))
        if Y(v) < yb - 2:
            marks.append(f'<circle class="hy-mark-g" cx="{f(X(r))}" cy="{f(Y(v))}" r="2"/>')
    p.append(pop("".join(marks), t + 0.35))
    p.append(text(x1, yb + 11, "r", "hy-mini", t + 0.3, "end"))
    return p


def _isochrone():
    """An old cluster's stars in the HR plane, built from the real one-solar-mass MESA track of the
    Stellar Explorer data: a star of mass m at 12 Gyr sits where the track is at age 12 m^2.5 Gyr,
    shifted by main-sequence homology (log Teff + 0.55 log m, log L + 3.5 log m); helium-burning
    stars from the track's own core-helium-burning models at the turn-off mass."""
    import h5py
    with h5py.File(Path.home() / "projects/stellar-explorer-data/stellar_data_real.h5", "r") as fh:
        h = fh["history"]
        lt, ll, age = h["log_Teff"][:], h["log_L"][:], h["star_age"][:]
        ph = h["phase"][:].astype(str)
    i0 = int((ph == "ZAMS").argmax())
    rgb_end = i0 + int(((ph[i0:] == "HeFlash") | (ph[i0:] == "HeCB")).argmax())
    pts = []
    rnd = _rng(4)
    # masses up to the turn-off, sampled densely near it so the turn-off and subgiant branch show
    for i in range(320):
        u = rnd()
        m = 0.55 + 0.43 * (1 - (1 - u) ** 2.2)
        a = 12.0 * m ** 2.5
        j = i0 + int(abs(age[i0:rgb_end] - a).argmin())
        if ll[j] > 2.2:
            continue
        lgm = math.log10(m)
        pts.append((lt[j] + 0.55 * lgm + 0.003 * (rnd() - 0.5), ll[j] + 3.5 * lgm + 0.02 * (rnd() - 0.5)))
    # the giant branch, climbed quickly by stars of about the turn-off mass
    lgm = math.log10(0.98)
    rows = [j for j in range(i0, rgb_end) if ph[j] in ("SGB", "RGB") and ll[j] < 2.2]
    lo, hi = min(ll[j] for j in rows), max(ll[j] for j in rows)
    for q in range(90):  # evenly in luminosity, so the base of the branch is not empty
        target = lo + (hi - lo) * (q + rnd()) / 90
        j = min(rows, key=lambda r: abs(ll[r] - target))
        pts.append((lt[j] + 0.55 * lgm + 0.003 * (rnd() - 0.5), ll[j] + 3.5 * lgm + 0.02 * (rnd() - 0.5)))
    # the red clump / horizontal branch from the track's own helium-burning models
    hb = [k for k in range(len(ph)) if ph[k] in ("HeCB", "RC") and ll[k] < 2.2]
    for k in hb[:: max(1, len(hb) // 30)]:
        pts.append((lt[k] + 0.006 * (rnd() - 0.5), ll[k] + 0.03 * (rnd() - 0.5)))
    return pts


def pic_population(x: float, y: float, t: float) -> list[str]:
    """A synthetic old population in the HR plane, from a real MESA track (see _isochrone), and its
    stars placed on the sky by the radial profile."""
    p = []
    x0, x1, yb, yt = x + 4, x + 74, y + 80, y + 2
    p.append(draw("hy-axis-thin", f"M{x0} {yt} V{yb} H{x1}", t, 0.3))
    pts = _isochrone()
    lts = [a for a, _ in pts]
    lls = [b for _, b in pts]
    t0, t1 = max(lts) + 0.01, min(lts) - 0.01
    l0, l1 = min(lls) - 0.1, max(lls) + 0.1
    dots = "".join(f'<circle class="hy-dot" cx="{f(x0 + 2 + (x1 - x0 - 4) * (t0 - a) / (t0 - t1))}" cy="{f(yb - 2 - (yb - yt - 4) * (b - l0) / (l1 - l0))}" r="0.8"/>' for a, b in pts)
    p.append(pop(dots, t + 0.15))
    p.append(text(x1, yb + 11, "Teff", "hy-mini", t + 0.3, "end"))
    p.append(text(x0 + 3, yt + 8, "L", "hy-mini", t + 0.3))
    p.append(draw("hy-pic", f"M{x + 80} {y + 44} h12 M{x + 88} {y + 40} l4 4 l-4 4", t + 0.3, 0.2))
    cx, cy = x + 122, y + 44
    p.append(draw("hy-pic-dash", f"M{cx + 26} {cy} A26 26 0 1 1 {cx - 26} {cy} A26 26 0 1 1 {cx + 26} {cy}", t + 0.35, 0.4))
    dd = []
    for i in range(120):
        r = 25 * ((i + 0.5) / 120) ** 1.8
        a = i * GOLDEN
        dd.append(f'<circle class="hy-dot" cx="{f(cx + r * math.cos(a))}" cy="{f(cy + r * math.sin(a))}" r="0.9"/>')
    p.append(pop("".join(dd), t + 0.45))
    return p


def pic_detector(x: float, y: float, t: float) -> list[str]:
    """A patch of the detector in three dimensions: pixels, the target's light as a bump, its
    raised mask, a neighbour's light overlapping it (figures/kit/pictos.mjs)."""
    pic = PICTOS["detector"]
    return [pop(f'<g class="iso-svg" transform="translate({f(x + 75 - pic["w"] / 2)} {f(y + 42 - pic["h"] / 2)})">{pic["body"]}</g>', t)]


def pic_seismic(x: float, y: float, t: float) -> list[str]:
    """The mean power spectrum of a red giant at nu_max = 30 microhertz, in units of its own flux,
    with three white-noise levels. Mode height and granulation at nu_max from the red-giant scaling
    relations of Mosser et al. 2012 (A&A 537, A30): H = 6200 and B = 1750 ppm^2/muHz. White levels
    from the HAYDN noise estimator for the 47 Tuc run at the adopted pointing-jitter level: 61
    isolated (SPR < 0.1), about 500 at SPR 0.2 and 10 000 at SPR 0.5. The envelope and the
    granulation are the same in all three; only the white level rises. Mosser et al. 2019 detect
    the modes from R = H / (B + white): 3.4, 2.7 and 0.5."""
    x0, x1, yb, yt = x + 8, x + 140, y + 74, y + 4
    lnu0, lnu1, lp0, lp1 = 0.0, math.log10(300.0), 1.0, 5.0
    def X(nu):
        return x0 + (x1 - x0) * (math.log10(nu) - lnu0) / (lnu1 - lnu0)
    def Y(pw):
        return yb - (yb - yt) * (math.log10(pw) - lp0) / (lp1 - lp0)
    numax, H = 30.0, 6200.0
    fwhm = 0.66 * numax ** 0.88
    def mean_psd(nu, white):
        gran = 52000 / (1 + (nu / 8.6) ** 4) + 3320 / (1 + (nu / 27.7) ** 4)
        env = H * math.exp(-0.5 * ((nu - numax) / (fwhm / 2.355)) ** 2)
        return gran + env + white
    p = [draw("hy-axis-thin", f"M{x0} {yt} V{yb} H{x1}", t, 0.3)]
    nus = [10 ** (lnu0 + (lnu1 - lnu0) * i / 400) for i in range(401)]
    for white, cls, lab, dt in ((61.0, "hy-pic", "isolated", 0.1), (500.0, "hy-spr2", "SPR 0.2", 0.2), (1.0e4, "hy-floor", "SPR 0.5", 0.3)):
        pts = [(X(nu), Y(mean_psd(nu, white))) for nu in nus]
        p.append(draw(cls, "M" + " L".join(f"{f(a)} {f(b)}" for a, b in pts), t + dt, 0.6))
        p.append(text(x1 + 3, Y(mean_psd(300.0, white)) + 3, lab, "hy-mini", t + 0.4))
    p.append(draw("hy-pic", f"M{f(X(numax))} {yb - 4} V{yb + 3}", t + 0.4, 0.2))
    p.append(tex(X(numax) + 3, yb - 5, r"\nu_{\max}", 9, t + 0.4, "hy-tex"))
    p.append(text(x1, yb + 11, "frequency", "hy-mini", t + 0.3, "end"))
    p.append(text(x0 - 3, yt + 2, "power", "hy-mini", t + 0.3, "end"))
    return p


# ------------------------------------------------------------------ figure 1: the pipeline
def pipeline() -> str:
    """The six stages in two rows of three, each box wide enough for its pictogram and its line;
    the thread snakes from the first row into the second, and the bypass for open clusters drops
    straight from the threshold to the noise estimator."""
    W, H = 1140, 636
    p: list[str] = []
    p.append(text(20, 30, "HAYDN, AS PROPOSED", "hy-head", 0.0))
    facts = [("aperture", "1.2 m"), ("field of view", "1 degree"), ("plate scale", "0.5 arcsec per pixel"),
             ("targets", "to G = 17"), ("target fields", "26")]
    x = 190
    for k, v in facts:
        p.append(text(x, 30, k.upper(), "hy-key", 0.1))
        p.append(text(x, 46, v, "hy-val", 0.15))
        x += 185
    p.append(draw("hy-rule", f"M20 60 H{W - 20}", 0.1, 0.3))
    w, h = 356, 216
    xs = [20, 392, 764]
    ys = [84, 344]
    stages = [
        ("ARCHIVE DATA", "Gaia DR3 to G = 18.5, HST photometry of the core, four catalogues", pic_archive),
        ("THRESHOLD", "the magnitudes where Gaia and HST are both complete; the members", pic_threshold),
        ("KING PROFILE", "fitted to the counts, normalised to HST in the 50 to 100 arcsec annulus", pic_king),
        ("TRILEGAL FIELD", "a synthetic population calibrated to the cluster mass, placed on the sky", pic_population),
        ("NOISE ESTIMATOR", "HNE on Deucalion: point spread function, mask and crowding, per star", pic_detector),
        ("SEISMIC MODEL", "Mosser et al. 2019: which stars show oscillations at that noise", pic_seismic),
    ]
    boxes = []
    for i, (title, line, pic) in enumerate(stages):
        x, y = xs[i % 3], ys[i // 3]
        t = 0.2 + 0.12 * i
        boxes.append((x, y))
        p.append(draw("hy-box", f"M{x} {y} h{w} v{h} h-{w} Z", t, 0.4))
        p.append(text(x + 12, y + 20, f"{i + 1}  {title}", "hy-title", t + 0.1))
        p.append(draw("hy-rule", f"M{x + 12} {y + 28} h{w - 24}", t + 0.1, 0.2))
        # the pictogram, drawn at its native size and scaled up to fill the box
        px, py, sc = x + 12, y + 38, 1.3
        shift = (w - 24 - 150 * sc) / 2
        p.append(f'<g transform="translate({f(px + shift)} {f(py)}) scale({sc}) translate({f(-px)} {f(-py)})">' + "".join(pic(px, py, t + 0.15)) + "</g>")
        # the line, wrapped by hand at the box width
        words, lines, cur = line.split(), [], ""
        for wd in words:
            if len(cur) + len(wd) + 1 > 50:
                lines.append(cur); cur = wd
            else:
                cur = (cur + " " + wd).strip()
        lines.append(cur)
        for k, ln in enumerate(lines):
            p.append(text(x + 12, y + h - 24 + 14 * k - 14 * (len(lines) - 1), ln, "hy-line", t + 0.5))
    ym = [y + 90 for y in ys]
    # row one, then the turn down into row two
    for i in range(2):
        xa, xb = xs[i] + w, xs[i + 1]
        t = 0.35 + 0.12 * i
        p.append(thread(f"M{xa} {ym[0]} C{xa + 5} {ym[0] - 7}, {xb - 5} {ym[0] + 7}, {xb} {ym[0]}", t))
        p.append(node(xa, ym[0], t)); p.append(node(xb, ym[0], t + 0.05))
    xe = xs[2] + w
    turn = f"M{xe} {ym[0]} C{xe + 24} {ym[0]}, {xe + 24} {ys[0] + h + 12}, {xe - 60} {ys[0] + h + 12} H{xs[0] - 4} C{xs[0] - 24} {ys[0] + h + 12}, {xs[0] - 24} {ym[1]}, {xs[0]} {ym[1]}"
    p.append(thread(turn, 0.65))
    p.append(node(xe, ym[0], 0.65)); p.append(node(xs[0], ym[1], 0.8))
    for i in range(2):
        xa, xb = xs[i] + w, xs[i + 1]
        t = 0.85 + 0.12 * i
        p.append(thread(f"M{xa} {ym[1]} C{xa + 5} {ym[1] - 7}, {xb - 5} {ym[1] + 7}, {xb} {ym[1]}", t))
        p.append(node(xa, ym[1], t)); p.append(node(xb, ym[1], t + 0.05))
    xo = xs[2] + w
    p.append(thread(f"M{xo} {ym[1]} H{W - 6}", 1.1)); p.append(node(xo, ym[1], 1.1))
    # open clusters skip the profile and the population: straight down from 2 to 5
    xm = xs[1] + w / 2
    p.append(thread(f"M{f(xm)} {ys[0] + h} V{ys[1]}", 1.15, "ray flowray hy-bypass"))
    p.append(node(xm, ys[0] + h, 1.15)); p.append(node(xm, ys[1], 1.2))
    p.append(text(xm + 10, ys[0] + h + 34, "open clusters skip 3 and 4", "hy-line", 1.25))
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
# Harris (2010) structure for the seven clusters: core radius (arcmin), concentration
# c = log10(r_t / r_c), distance (kpc); the copy in the HAYDNsim repository (data/catalogs/harris_2010.csv)
HARRIS = {
    "47 Tuc": ("NGC 104", 0.36, 2.07, 4.5), "NGC 6752": ("NGC 6752", 0.17, 2.50, 4.0), "M54": ("NGC 6715", 0.09, 2.04, 26.5),
    "M22": ("NGC 6656", 1.33, 1.38, 3.2), "omega Cen": ("NGC 5139", 2.37, 1.31, 5.2), "NGC 6397": ("NGC 6397", 0.05, 2.50, 2.3),
    "M4": ("NGC 6121", 1.16, 1.65, 2.2),
}


def cluster_disc(cx: float, cy: float, R: float, rc: float, c: float, seed: int, n: int = 900) -> str:
    """Stars at radii drawn from the King (1962) surface density of the cluster, at a common angular
    scale: R pixels for the 30 arcmin radius of the one-degree field."""
    rt = rc * 10 ** c
    def sigma(r):
        if r >= rt:
            return 0.0
        return (1 / math.sqrt(1 + (r / rc) ** 2) - 1 / math.sqrt(1 + (rt / rc) ** 2)) ** 2
    rmax = min(rt, 30.0)
    grid = [rmax * (i / 2000) ** 2 for i in range(2001)]
    cdf, acc = [0.0], 0.0
    for i in range(1, len(grid)):
        rm = 0.5 * (grid[i] + grid[i - 1])
        acc += rm * sigma(rm) * (grid[i] - grid[i - 1])
        cdf.append(acc)
    rnd = _rng(seed)
    dots = []
    for _ in range(n):
        u = rnd() * acc
        lo, hi = 0, len(cdf) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if cdf[mid] < u:
                lo = mid
            else:
                hi = mid
        r = grid[hi] * R / 30.0
        a = rnd() * 2 * math.pi
        dots.append(f'<circle cx="{f(cx + r * math.cos(a))}" cy="{f(cy + r * math.sin(a))}" r="0.75"/>')
    return "".join(dots)


def crowding() -> str:
    """The poster's per-cluster fractions, each under a drawing of its cluster in the one-degree field."""
    W, H = 1140, 330
    p: list[str] = []
    L, T = 24, 30
    p.append(text(L, T, "STARS WHOSE LIGHT IS MOSTLY THEIR NEIGHBOURS'", "hy-head", 0.0))
    p.append(text(L, T + 18, "share with a stellar pollution ratio above 0.5, under each cluster as it fills the one-degree field", "hy-line", 0.05))
    cw = (W - 2 * L) / 7
    R = 62
    cy = T + 54 + R
    by = cy + R + 54
    bmax = cw - 34
    omega, ow = tex_glyphs(r"\omega", 13)
    for i, (name, pc) in enumerate(FRACTIONS):
        x0 = L + i * cw
        cx = x0 + cw / 2
        t = 0.2 + 0.08 * i
        ngc, rc, c, dist = HARRIS[name]
        p.append(f'<circle class="hy-field-edge" cx="{f(cx)}" cy="{f(cy)}" r="{R}"/>')
        p.append(pop(f'<g class="hy-cluster">{cluster_disc(cx, cy, R, rc, c, 11 + i)}</g>', t))
        # the tidal radius, where it falls inside the field
        rt = rc * 10 ** c
        if rt < 30:
            p.append(f'<circle class="hy-tidal" cx="{f(cx)}" cy="{f(cy)}" r="{f(R * rt / 30)}"/>')
        ny = cy + R + 20
        if name.startswith("omega"):
            p.append(pop(f'<g class="hy-tex-ink" transform="translate({f(cx - (ow + 4 + 3 * 7.2) / 2)} {f(ny)})">{omega}</g>', t))
            p.append(text(cx - (ow + 4 + 3 * 7.2) / 2 + ow + 4, ny, "Cen", "hy-title", t))
        else:
            p.append(text(cx, ny, name, "hy-title", t, "middle"))
        p.append(text(cx, ny + 15, f"{ngc} · {dist:g} kpc", "hy-num", t, "middle"))
        bx = cx - bmax / 2
        p.append(f'<rect class="hy-bar-track" x="{f(bx)}" y="{by}" width="{f(bmax)}" height="10"/>')
        p.append(pop(f'<rect class="hy-bar" x="{f(bx)}" y="{by}" width="{f(bmax * pc / 40.0)}" height="10"/>', t + 0.2))
        p.append(text(cx, by + 30, f"{pc} %", "hy-val", t + 0.25, "middle"))
    return (
        f'<svg class="bp-svg hy-svg" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-labelledby="hy-ct hy-cd"><title id="hy-ct">Crowding in seven clusters</title>'
        '<desc id="hy-cd">Seven globular clusters drawn as they fill the one-degree field, at a common angular '
        'scale, each from its King profile in the Harris 2010 catalogue, with a bar beneath for the share of its '
        'stars whose light is mostly from neighbouring stars: 40 per cent in 47 Tucanae, 36 in NGC 6752 and M54, '
        '12 in M22, 11 in omega Centauri, 7 in NGC 6397 and 3 in M4.</desc>'
        + "".join(p) + "</svg>\n"
    )


def main() -> None:
    OUT.joinpath("haydn-pipeline.svg").write_text(pipeline())
    OUT.joinpath("haydn-crowding.svg").write_text(crowding())
    for n in ("haydn-pipeline.svg", "haydn-crowding.svg"):
        print(f"wrote {OUT / n} ({OUT.joinpath(n).stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
