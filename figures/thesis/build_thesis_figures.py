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
import math
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


TRACK_H5 = Path.home() / "projects/stellar-explorer-data/stellar_data_real.h5"


def real_track():
    """The 1 solar-mass MESA track of the Stellar Explorer file (ZAMS to the lower RGB), thinned,
    and the GYRE mode frequencies of its model at 2.76 Gyr. Both are real; the grid pictogram
    scales the track to other masses by homology, which the caption states."""
    import h5py
    import numpy as np
    with h5py.File(TRACK_H5, "r") as fh:
        h = fh["history"]
        lt, ll, age = h["log_Teff"][:], h["log_L"][:], h["star_age"][:]
        ph = h["phase"][:].astype(str)
        i0 = int(np.where(ph == "ZAMS")[0][0])
        i1 = i0 + int(np.argmax(ll[i0:] > 0.9))
        sel = np.linspace(i0, i1, 90).astype(int)
        track = list(zip(lt[sel].tolist(), ll[sel].tolist(), age[sel].tolist()))
        g = fh["gyre"]["4"]
        modes = list(zip(g["freq_uHz"][:].tolist(), g["l"][:].tolist()))
        numax = float(fh["track"]["nu_max"][4])
        dnu = float(fh["track"]["delta_nu"][4])
    return track, modes, numax, dnu


def poly(pts) -> str:
    return "M" + " L".join(f"{f(a)} {f(b)}" for a, b in pts)


def gauss(x, mu, sig):
    return math.exp(-0.5 * ((x - mu) / sig) ** 2)


def method_figure() -> str:
    """Drawn, not written: framed stages with one pictogram and one short line each, ports on the
    frames, flowing threads between ports. The pictograms follow real shapes: an absorption
    spectrum built from the Mg b triplet and Fe I lines at their wavelengths, the Planck curve at
    the Sun's temperature under the 2MASS Ks band, a power spectrum whose comb is the GYRE
    frequencies of a solar model, the MESA track of that model scaled to a grid of masses, and
    PARAM as the grid of models weighted by likelihood with its marginals."""
    track, modes, numax, dnu = real_track()
    W, H = 1120, 570
    p = []
    T_FRAME, T_PIC, T_THREAD, T_OUT = 0.0, 0.6, 1.5, 2.0

    # ---- frames
    L = [(40, 170, 290, 120, "SPECTROSCOPY"), (40, 300, 290, 120, "LUMINOSITY"), (40, 430, 290, 120, "SEISMIC PARAMETERS")]
    for i, (x, y, w, h, title) in enumerate(L):
        p += frame(x, y, w, h, title, T_FRAME + 0.1 * i)
    p += frame(380, 40, 185, 120, "MESA GRID", T_FRAME + 0.3)
    p += frame(585, 40, 185, 120, "GYRE", T_FRAME + 0.4)
    PX, PY, PW, PH = 380, 170, 390, 380
    p += frame(PX, PY, PW, PH, "PARAM", T_FRAME + 0.5)
    p += frame(810, 170, 280, 180, "MASS, RADIUS, AGE", T_OUT)
    p += frame(810, 370, 280, 180, "CONSTRAINT SETS", T_OUT + 0.1)

    # ---- spectroscopy: a stretch of a high-resolution optical spectrum, 5165 to 5190 angstrom
    x0, x1, yc, dep = 56.0, 314.0, 214.0, 38.0
    lam0, lam1 = 5165.0, 5190.0
    lines = [(5165.41, 0.25), (5166.28, 0.55), (5167.32, 0.88), (5168.90, 0.40), (5169.03, 0.30), (5171.60, 0.62),
             (5172.68, 0.92), (5173.74, 0.45), (5175.11, 0.20), (5176.56, 0.30), (5177.23, 0.18), (5178.80, 0.30),
             (5180.06, 0.15), (5181.10, 0.22), (5183.60, 0.95), (5184.27, 0.25), (5185.90, 0.30), (5187.0, 0.12),
             (5187.92, 0.35), (5188.69, 0.22), (5189.19, 0.26), (5170.37, 0.12), (5174.9, 0.1), (5179.5, 0.12)]
    pts = []
    n = 600
    for i in range(n + 1):
        lam = lam0 + (lam1 - lam0) * i / n
        fl = 1.0
        for lc, d in lines:
            fl -= d * gauss(lam, lc, 0.085 if d < 0.8 else 0.2)
        pts.append((x0 + (x1 - x0) * i / n, yc + dep * (1 - max(fl, 0.02))))
    p.append(draw("th-guide", f"M{x0} {yc} H{x1}", T_PIC, 0.2))
    p.append(draw("th-pic", poly(pts), T_PIC + 0.1, 0.9))
    for lam, lab in ((5170, "5170"), (5180, "5180")):
        xx = x0 + (x1 - x0) * (lam - lam0) / (lam1 - lam0)
        p.append(draw("th-tick", f"M{f(xx)} {yc + dep + 2} v4", T_PIC + 0.3, 0.2))
        p.append(text(xx, yc + dep + 16, lab, "th-note", T_PIC + 0.35, "middle"))
    xm = x0 + (x1 - x0) * (5175.5 - lam0) / (lam1 - lam0)
    p.append(text(xm, yc - 5, "Mg b", "th-note", T_PIC + 0.4, "middle"))
    p.append(text(x1, yc + dep + 16, "Å", "th-note", T_PIC + 0.35, "end"))
    p.append(text(52, 282, "SWEET-Cat", "th-line", T_PIC + 0.2))

    # ---- luminosity: the parallax triangle to scale in angle, and the Sun's Planck curve under the Ks band
    sx, sy = 86.0, 370.0
    p.append(draw("th-pic", f"M{sx - 26} {sy} a26 7 0 1 0 52 0 a26 7 0 1 0 -52 0", T_PIC + 0.2, 0.4))
    p.append(pop(f'<circle class="th-dot" cx="{f(sx)}" cy="{f(sy)}" r="3"/>', T_PIC + 0.25))
    stx, sty = 150.0, 338.0
    p.append(draw("th-dim", f"M{sx - 26} {sy} L{stx} {sty} L{sx + 26} {sy}", T_PIC + 0.3, 0.4))
    p.append(pop(f'<path class="th-pic" d="M{stx - 4} {sty} h8 M{stx} {sty - 4} v8"/>', T_PIC + 0.35))
    p.append(draw("th-dimline", f"M{sx - 26} {sy + 14} H{sx + 26} M{sx - 26} {sy + 11} v6 M{sx + 26} {sy + 11} v6", T_PIC + 0.4, 0.3))
    p.append(text(sx, sy + 27, "1 au", "th-note", T_PIC + 0.45, "middle"))
    p.append(draw("th-dimline", f"M{stx - 9} {sty + 12} a9 9 0 0 0 18 0", T_PIC + 0.4, 0.2))
    p.append(place([("tex", r"\varpi")], stx + 12, sty + 10, "th-note", 10.5, T_PIC + 0.45))
    bx0, bx1, bb, bh = 196.0, 316.0, 386.0, 42.0
    h_, c_, k_ = 6.62607e-34, 2.99792e8, 1.380649e-23
    def planck(um):
        lam = um * 1e-6
        return 1 / (lam ** 5 * (math.exp(h_ * c_ / (lam * k_ * 5772.0)) - 1))
    lmin, lmax = math.log10(0.3), math.log10(3.0)
    xs = [bx0 + (bx1 - bx0) * i / 120 for i in range(121)]
    ums = [10 ** (lmin + (lmax - lmin) * i / 120) for i in range(121)]
    peak = max(planck(u) for u in ums)
    curve = [(xx, bb - bh * planck(u) / peak) for xx, u in zip(xs, ums)]
    kx0 = bx0 + (bx1 - bx0) * (math.log10(1.99) - lmin) / (lmax - lmin)
    kx1 = bx0 + (bx1 - bx0) * (math.log10(2.31) - lmin) / (lmax - lmin)
    p.append(pop(f'<rect class="th-band" x="{f(kx0)}" y="{bb - bh}" width="{f(kx1 - kx0)}" height="{bh}"/>', T_PIC + 0.5))
    p.append(draw("th-guide", f"M{bx0} {bb} H{bx1}", T_PIC + 0.3, 0.2))
    p.append(draw("th-pic", poly(curve), T_PIC + 0.35, 0.6))
    for um, lab in ((0.5, "0.5"), (1.0, "1"), (2.0, "2 μm")):
        xx = bx0 + (bx1 - bx0) * (math.log10(um) - lmin) / (lmax - lmin)
        p.append(draw("th-tick", f"M{f(xx)} {bb + 2} v4", T_PIC + 0.4, 0.2))
        p.append(text(xx, bb + 16, lab, "th-note", T_PIC + 0.45, "middle"))
    p.append(place([("tex", r"K_\mathrm{S}")], (kx0 + kx1) / 2, bb - bh - 4, "th-note", 10.5, T_PIC + 0.5, "middle"))
    p.append(place([("text", "Gaia parallax, 2MASS "), ("tex", r"K_\mathrm{S}")], 52, 412, "th-line", 11, T_PIC + 0.4))

    # ---- seismic parameters: a power spectrum with the GYRE comb under a Gaussian envelope
    fx0, fx1, fb, fh = 56.0, 316.0, 518.0, 50.0
    nu0, nu1 = 2400.0, 4400.0
    sig_env = 0.66 * numax ** 0.88 / 2.355
    vis = {0: 1.0, 1: 1.5, 2: 0.6}
    def psd(nu):
        v = 0.08 / (1 + (nu / 1600.0) ** 4)
        for fr, el in modes:
            if nu0 - 50 < fr < nu1 + 50:
                v += vis[el] * gauss(fr, numax, sig_env) / (1 + ((nu - fr) / 7.0) ** 2)
        return v
    nus = [nu0 + (nu1 - nu0) * i / 500 for i in range(501)]
    vals = [psd(nu) for nu in nus]
    vmax = max(vals)
    pts = [(fx0 + (fx1 - fx0) * i / 500, fb - fh * v / vmax) for i, v in enumerate(vals)]
    xnm = fx0 + (fx1 - fx0) * (numax - nu0) / (nu1 - nu0)
    p.append(draw("th-guide", f"M{fx0} {fb} H{fx1}", T_PIC + 0.4, 0.2))
    env = [(fx0 + (fx1 - fx0) * i / 60, fb - fh * 1.5 * gauss(nu0 + (nu1 - nu0) * i / 60, numax, sig_env) / vmax) for i in range(61)]
    p.append(draw("th-dim", poly(env), T_PIC + 0.5, 0.5))
    p.append(draw("th-pic", poly(pts), T_PIC + 0.45, 0.9))
    p.append(draw("th-dim", f"M{f(xnm)} {fb - fh - 6} V{fb + 3}", T_PIC + 0.6, 0.2))
    p.append(place([("tex", r"\nu_{\max}")], xnm + 5, fb - fh - 2, "th-note", 10.5, T_PIC + 0.65))
    l0 = sorted(fr for fr, el in modes if el == 0 and fr > numax)[:2]
    xa, xb = (fx0 + (fx1 - fx0) * (v - nu0) / (nu1 - nu0) for v in l0)
    p.append(draw("th-dimline", f"M{f(xa)} {fb + 6} V{fb + 10} H{f(xb)} V{fb + 6}", T_PIC + 0.65, 0.2))
    p.append(place([("tex", r"\Delta\nu")], xb + 6, fb + 14, "th-note", 10.5, T_PIC + 0.7))
    p.append(text(52, 542, "from the literature", "th-line", T_PIC + 0.7))

    # ---- MESA grid: the real track, scaled by homology to a family of masses, with three isochrones
    ax, ay, aw, ah = 396, 74, 150, 50
    tx0, tx1, ty0, ty1 = 3.92, 3.56, -1.4, 1.5
    def hr(lt, ll):
        return ax + aw * (tx0 - lt) / (tx0 - tx1), ay + ah * (ty1 - ll) / (ty1 - ty0)
    masses = (0.5, 0.7, 0.9, 1.1, 1.4, 1.8)
    fam = {}
    for m in masses:
        fam[m] = [(lt + 0.55 * math.log10(m), ll + 3.5 * math.log10(m), a / m ** 2.5) for lt, ll, a in track]
    p.append(f'<clipPath id="th-hr"><rect x="{ax}" y="{ay - 2}" width="{aw}" height="{ah + 2}"/></clipPath>')
    p.append(draw("th-axis", f"M{ax} {ay} V{ay + ah} H{ax + aw}", T_PIC + 0.3, 0.3))
    tr = []
    for i, m in enumerate(masses):
        tr.append(draw("th-pic", poly([hr(lt, ll) for lt, ll, _ in fam[m]]), T_PIC + 0.35 + 0.04 * i, 0.5))
    p.append('<g clip-path="url(#th-hr)">' + "".join(tr) + "</g>")
    p.append(place([("tex", r"T_\mathrm{eff}")], ax + aw + 4, ay + ah + 4, "th-note", 10, T_PIC + 0.7))
    p.append(place([("tex", r"L")], ax - 4, ay + 8, "th-note", 10, T_PIC + 0.7, "end"))
    p.append(draw("th-dimline", f"M{ax + 10} {ay + ah + 14} H{ax + aw - 6} M{ax + 10} {ay + ah + 10} v8 M{ax + aw - 6} {ay + ah + 10} v8", T_PIC + 0.6, 0.3))
    p.append(place([("text", "0.5 to 1.8 "), ("tex", r"M_\odot")], ax + 10 + (aw - 16) / 2, ay + ah + 29, "th-note", 10.5, T_PIC + 0.65, "middle"))

    # ---- GYRE: the model's own mode frequencies, by degree
    gx0, gx1, gb = 601.0, 756.0, 132.0
    hts = {0: 40, 1: 26, 2: 14}
    p.append(draw("th-guide", f"M{gx0 - 4} {gb} H{gx1}", T_PIC + 0.4, 0.2))
    comb = []
    for fr, el in sorted(modes):
        if nu0 <= fr <= nu1:
            xx = gx0 + (gx1 - gx0) * (fr - nu0) / (nu1 - nu0)
            comb.append(f"M{f(xx)} {gb} v-{hts[el]}")
    p.append(draw("th-pic", " ".join(comb), T_PIC + 0.45, 0.6))
    lx = gx0
    for el in (0, 1, 2):
        p.append(draw("th-pic", f"M{f(lx)} {gb - 54} v-{hts[el] / 4:.1f}", T_PIC + 0.6, 0.2))
        p.append(place([("tex", rf"\ell={el}")], lx + 5, gb - 52, "th-note", 9.5, T_PIC + 0.65))
        lx += 38
    p.append(text(597, 152, "mode frequencies", "th-line", T_PIC + 0.6))

    # ---- PARAM: the constraints, the grid of models weighted by likelihood, and the marginals
    p.append(place([("tex", r"p(M,\tau\,|\,d)\ \propto\ \sum_{\mathrm{grid}} \mathcal{L}(d\,|\,M,\tau,Z)\ p(M)\,p(\tau)")], PX + 12, PY + 42, "th-body", 11, T_PIC + 0.5))
    p.append(text(PX + 12, PY + 60, "each model on the grid weighted by its likelihood", "th-line", T_PIC + 0.55))
    cx0, cy0 = PX + 14, PY + 92
    cons = ((r"T_\mathrm{eff}", 0.55), (r"\log g", 0.75), (r"[\mathrm{Fe/H}]", 0.6), (r"L", 0.35), (r"\Delta\nu", 0.22), (r"\nu_{\max}", 0.45))
    for i, (lab, wd) in enumerate(cons):
        yy = cy0 + 26 * i
        p.append(place([("tex", lab)], cx0 + 30, yy + 12, "th-note", 9.5, T_PIC + 0.6 + 0.04 * i, "end"))
        bell = [(cx0 + 36 + 44 * k / 40, yy + 16 - 15 * gauss(k / 40, 0.5, 0.17 * wd)) for k in range(41)]
        p.append(draw("th-pic", poly(bell), T_PIC + 0.65 + 0.04 * i, 0.3))
        p.append(draw("th-guide", f"M{cx0 + 36} {yy + 16} h44", T_PIC + 0.6, 0.2))
    p.append(draw("th-join", f"M{cx0 + 84} {cy0 + 70} H{PX + 104}", T_PIC + 0.9, 0.3))
    gx, gy, gw, gh = PX + 104, PY + 86, 190.0, 156.0
    a_lo, a_hi, m_lo, m_hi = 0.0, 14.0, 0.7, 1.5
    mu_a, mu_m, s_a, s_m, rho = 6.4, 1.06, 1.8, 0.1, -0.72
    def like(a, m):
        za, zm = (a - mu_a) / s_a, (m - mu_m) / s_m
        return math.exp(-(za * za - 2 * rho * za * zm + zm * zm) / (2 * (1 - rho * rho)))
    def gxy(a, m):
        return gx + gw * (a - a_lo) / (a_hi - a_lo), gy + gh * (m_hi - m) / (m_hi - m_lo)
    p.append(draw("th-axis", f"M{gx} {gy} V{gy + gh} H{gx + gw}", T_PIC + 0.7, 0.3))
    dots_out, dots_in = [], []
    for i in range(19):
        for j in range(13):
            a = a_lo + (a_hi - a_lo) * (i + 0.5) / 19
            m = m_lo + (m_hi - m_lo) * (j + 0.5) / 13
            w = like(a, m)
            xx, yy = gxy(a, m)
            if w < 0.03:
                dots_out.append(f'<circle cx="{f(xx)}" cy="{f(yy)}" r="0.9"/>')
            else:
                dots_in.append(f'<circle cx="{f(xx)}" cy="{f(yy)}" r="{0.9 + 2.8 * math.sqrt(w):.1f}"/>')
    p.append(pop(f'<g class="th-cell">{"".join(dots_out)}</g>', T_PIC + 0.8))
    p.append(pop(f'<g class="th-mark">{"".join(dots_in)}</g>', T_PIC + 0.9))
    for chi2, cls in ((2.30, "th-pic"), (6.17, "th-dim")):
        ell = []
        for k in range(73):
            th = 2 * math.pi * k / 72
            za, zm = math.cos(th), math.sin(th)
            # a unit circle mapped through the covariance's Cholesky factor
            a = mu_a + math.sqrt(chi2) * s_a * za
            m = mu_m + math.sqrt(chi2) * s_m * (rho * za + math.sqrt(1 - rho * rho) * zm)
            ell.append(gxy(a, m))
        p.append(draw(cls, poly(ell) + " Z", T_PIC + 1.0, 0.5))
    p.append(text(gx + gw / 2, gy + gh + 13, "age", "th-note", T_PIC + 0.8, "middle"))
    p.append(text(gx - 4, gy - 6, "mass", "th-note", T_PIC + 0.8))
    for a in (0, 5, 10):
        xx, _ = gxy(a, m_lo)
        p.append(draw("th-tick", f"M{f(xx)} {gy + gh} v4", T_PIC + 0.8, 0.2))
    # the marginal over age under the grid, with its 68 per cent band
    hb, hh = gy + gh + 86, 60
    hill = [(gx + gw * k / 80, hb - hh * gauss(a_lo + (a_hi - a_lo) * k / 80, mu_a, s_a)) for k in range(81)]
    xl, _ = gxy(mu_a - s_a, m_lo)
    xr, _ = gxy(mu_a + s_a, m_lo)
    p.append(draw("th-guide", f"M{gx} {hb} H{gx + gw}", T_PIC + 0.9, 0.2))
    p.append(pop(f'<path class="th-band" d="M{f(xl)} {hb} V{hb - hh * gauss(mu_a - s_a, mu_a, s_a):.1f} L{f(xr)} {hb - hh * gauss(mu_a + s_a, mu_a, s_a):.1f} V{hb} Z"/>', T_PIC + 1.1))
    p.append(draw("th-pic th-hill", poly(hill), T_PIC + 1.0, 0.7))
    xmu, _ = gxy(mu_a, m_lo)
    p.append(draw("th-dim", f"M{f(xmu)} {hb - hh - 4} V{hb + 3}", T_PIC + 1.1, 0.2))
    p.append(draw("th-dimline", f"M{f(xl)} {hb + 10} V{hb + 14} H{f(xr)} V{hb + 10}", T_PIC + 1.15, 0.3))
    p.append(text((xl + xr) / 2, hb + 27, "68 %", "th-note", T_PIC + 1.2, "middle"))
    # the marginal over mass beside the grid
    vx, vw = gx + gw + 8, 44
    vhill = [(vx + vw * gauss(m_lo + (m_hi - m_lo) * k / 80, mu_m, s_m), gy + gh * (1 - k / 80)) for k in range(81)]
    p.append(draw("th-guide", f"M{vx} {gy} V{gy + gh}", T_PIC + 0.9, 0.2))
    p.append(draw("th-pic", poly(vhill), T_PIC + 1.0, 0.6))

    # ---- ports and threads: every thread runs from a node on one frame to a node on the next
    ports = []
    for i, (x, y, w, h, _) in enumerate(L):
        yc = y + h / 2
        ports += [node(x + w, yc, T_THREAD + 0.05 * i), node(PX, yc, T_THREAD + 0.05 * i)]
        p.append(thread(f"M{x + w} {yc} H{PX}", T_THREAD + 0.05 * i))
    ports += [node(565, 95, T_THREAD), node(585, 95, T_THREAD)]
    p.append(thread("M565 95 H585", T_THREAD))
    ports += [node(677, 160, T_THREAD + 0.1), node(677, PY, T_THREAD + 0.1)]
    p.append(thread(f"M677 160 V{PY}", T_THREAD + 0.1))
    for (yp, yo, t) in ((PY + 110, 260, T_OUT + 0.2), (PY + 270, 460, T_OUT + 0.3)):
        ports += [node(PX + PW, yp, t), node(810, yo, t)]
        p.append(thread(f"M{PX + PW} {yp} C{PX + PW + 24} {yp}, {810 - 24} {yo}, 810 {yo}", t))
    p += ports

    # ---- outputs: three marginal posteriors with their 68 per cent bands, and the constraint sets as a matrix
    ox = 826
    shapes = (("mass", lambda u: gauss(u, 0.5, 0.11)), ("radius", lambda u: gauss(u, 0.5, 0.07)),
              ("age", lambda u: 0.75 * gauss(u, 0.36, 0.11) + 0.55 * gauss(u, 0.68, 0.1)))
    for i, (lab, fn) in enumerate(shapes):
        x0, y0, w, hh = ox + i * 88, 290, 78, 48
        ys = [fn(k / 60) for k in range(61)]
        top = max(ys)
        curve = [(x0 + w * k / 60, y0 - hh * v / top) for k, v in enumerate(ys)]
        tot = sum(ys)
        acc, lo, hi = 0.0, 0, 60
        for k, v in enumerate(ys):
            acc += v
            if acc < 0.16 * tot:
                lo = k
            if acc < 0.84 * tot:
                hi = k
        band = "M" + f"{f(x0 + w * lo / 60)} {y0}" + " " + " L".join(f"{f(x0 + w * k / 60)} {f(y0 - hh * ys[k] / top)}" for k in range(lo, hi + 1)) + f" L{f(x0 + w * hi / 60)} {y0} Z"
        p.append(draw("th-guide", f"M{x0} {y0} H{x0 + w}", T_OUT + 0.2, 0.17))
        p.append(pop(f'<path class="th-band" d="{band}"/>', T_OUT + 0.5 + 0.1 * i))
        p.append(draw("th-pic", poly(curve), T_OUT + 0.25 + 0.1 * i, 0.5))
        p.append(text(x0 + w / 2, y0 + 16, lab, "th-note", T_OUT + 0.4 + 0.1 * i, "middle"))
    p.append(text(822, 336, "per star, the 68 % band shaded", "th-line", T_OUT + 0.6))
    sx0, sy0, cell, gap = 918, 418, 20, 8
    cols = [[("text", "none")], [("tex", r"\Delta\nu")], [("tex", r"\nu_{\max}")], [("text", "both")]]
    rows = [[("text", "spec")], [("text", "no "), ("tex", r"\log g")], [("text", "+ "), ("tex", r"L")], [("text", "+ "), ("tex", r"L"), ("text", ", no "), ("tex", r"\log g")]]
    for j, c in enumerate(cols):
        p.append(place(c, sx0 + j * (cell + gap) + cell / 2, sy0 - 8, "th-note", 10.5, T_OUT + 0.5, "middle"))
    keys = ("spec", "spec+dnu", "spec+numax", "spec+dnu+numax")
    sets = (("published_inputs", "spec"), ("published_inputs_no_logg", "spec"), ("published_inputs", "specphot"), ("published_inputs_no_logg", "specphot"))
    vmax2 = max(DATA[t][k.replace("spec", pre, 1)]["age"] for t, pre in sets for k in keys)
    for i, r in enumerate(rows):
        yy = sy0 + i * (cell + gap)
        tab, pre = sets[i]
        p.append(place(r, sx0 - 10, yy + cell / 2 + 4, "th-note", 10.5, T_OUT + 0.55 + 0.05 * i, "end"))
        for j in range(4):
            v = DATA[tab][keys[j].replace("spec", pre, 1)]["age"]
            side = cell * math.sqrt(v / vmax2)
            x_, y_ = sx0 + j * (cell + gap), yy
            p.append(draw("th-cell", f"M{x_} {y_} h{cell} v{cell} h{-cell} Z", T_OUT + 0.55 + 0.03 * (i * 4 + j), 0.25))
            p.append(pop(f'<rect class="th-mark" x="{f(x_ + (cell - side) / 2)}" y="{f(y_ + (cell - side) / 2)}" width="{f(side)}" height="{f(side)}"/>', T_OUT + 0.7 + 0.03 * (i * 4 + j)))
    right = sx0 + 4 * (cell + gap) - gap
    bottom = sy0 + 4 * (cell + gap) - gap
    p.append(draw("th-dimline", f"M{right + 12} {sy0} H{right + 16} V{bottom} H{right + 12}", T_OUT + 0.9, 0.3))
    p.append(text(right + 22, (sy0 + bottom) / 2 + 4, "16", "th-note", T_OUT + 0.95))
    p.append(text(sx0 - 90, bottom + 22, "filled area: the age uncertainty", "th-line", T_OUT + 1.0))
    return (
        f'<svg class="bp-svg th-svg th-method" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-labelledby="th-m-t"><title id="th-m-t">The method chain of the dissertation as framed stages: a stretch of '
        'optical spectrum, the parallax triangle with the Planck curve under the Ks band, and a power spectrum on the left; '
        'the MESA grid of tracks and the GYRE mode frequencies on top; PARAM in the middle as the six constraints, the grid '
        'of models weighted by likelihood with its 68 and 95 per cent contours and the marginals over age and mass; the '
        'posteriors of mass, radius and age and the sixteen constraint sets on the right.</title>' + "".join(p) + "</svg>\n"
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
    panels = [("age", 0, 40, (0, 10, 20, 30, 40), 196), ("mass", 0, 7, (0, 2, 4, 6), 486)]
    p = []
    top, step = 64, 34
    lab_x = 10
    for i, key in enumerate(order):
        yy = top + i * step
        p.append(place(labels[key], lab_x, yy + 4, "th-row", 13, 0.1 + 0.03 * i))
        p.append(draw("th-guide", f"M{lab_x} {yy + 12} H{W - 16}", 0.05 + 0.02 * i, 0.17))
    for name, lo, hi, ticks, x0 in panels:
        pw = 250
        sx = lambda v, lo=lo, hi=hi, x0=x0, pw=pw: x0 + (v - lo) / (hi - lo) * pw
        ybot = top + 7 * step + 16
        p.append(draw("th-axis", f"M{x0} {top - 24} V{ybot} H{x0 + pw}", 0.0, 0.3))
        for tv in ticks:
            p.append(draw("th-tick", f"M{sx(tv)} {ybot} v4", 0.1, 0.17))
            p.append(text(sx(tv), ybot + 16, str(tv), "th-tickl", 0.15, "middle"))
        p.append(text(x0 + pw, ybot + 32, f"{name}, per cent", "th-note", 0.2, "end"))
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
