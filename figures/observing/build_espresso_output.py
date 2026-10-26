"""Build the output side of FIG 2 on /observing/paranal/ from the public GJ 570 A velocities.

Usage:
    uv run --with numpy python -I figures/observing/build_espresso_output.py <ts_HD_131977> <repo root>

Input: the file ts_HD_131977 of the Zenodo record doi:10.5281/zenodo.17236515 (version
10.5281/zenodo.17236516, CC BY 4.0), the ESPRESSO radial velocities of GJ 570 A (HD 131977) from
programme 0113.D-0255(B), May 2024, published with Campante et al. 2026, A&A,
doi:10.1051/0004-6361/202660350 (arXiv:2610.20985).

Method, after Sect. 2 and 4.1 of the paper:
- keep the rows whose FLUX_CORR_CHECK flag is 1, as the file header instructs (2,250 of 2,369);
- split into nights at gaps longer than 6 h;
- high-pass filter each night by subtracting a weighted triangular smoothing with a 1.2 h cutoff
  (a triangle of half-width 1.2 h; this only affects frequencies far below the oscillations);
- amplitude spectrum by weighted least-squares sine fits (weighted Lomb-Scargle) with weights
  1/sigma^2 from the file's RV_ERR, on a 1 microhertz grid; power = amplitude squared.
  The paper further optimises the weights; that step is not repeated, so the noise level differs a
  little (1.55 here against 1.51 cm/s in the paper, mean amplitude between 6 and 8 mHz);
- the smooth curve is the power convolved with a Gaussian of FWHM 4 times the paper's large
  frequency separation (197.29 microhertz), the kernel the paper uses to locate nu_max.
Display: the raw power is drawn at the panel's resolution, each column showing the highest power
among the frequencies it covers, which is how the full curve renders at this size. The smooth
curve and the noise level are multiplied by three, as in Fig. 3 of the paper.

Layout of the figure (one coordinate space, 1220 units wide, split into SVGs at the seams):
top tier 436 high = light path (x 0 to 800, hand-drawn in _includes/figures/vlt-lightpath.svg)
plus the exposure column (x 800 to 1220); bottom tier 322 high = the night (x 0 to 610) and the
power spectrum (x 610 to 1220). The data thread is one chain of curves cut at the seams; each piece
carries the dash phase of the length before it, so the moving dash runs on across seams.

Outputs: assets/data/observing/gj570a_output.json (the arrays drawn),
assets/data/observing/gj570a_provenance.json, _includes/figures/espresso-exposure.svg,
_includes/figures/espresso-night.svg, _includes/figures/espresso-spectrum.svg, and the data-thread
block between the "generated" markers of _includes/figures/vlt-lightpath.svg.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

SOURCE = {
    "record": "https://doi.org/10.5281/zenodo.17236515",
    "version_doi": "10.5281/zenodo.17236516",
    "file": "ts_HD_131977",
    "md5": "4675c3bf88dad84930a654a4422b6199",
    "licence": "CC BY 4.0",
    "creator": "Campante, Tiago L.",
    "paper": "Campante et al. 2026, A&A, doi:10.1051/0004-6361/202660350",
    "programme": "ESO 0113.D-0255(B)",
}
PAPER = {"numax_uHz": 4705, "numax_err_uHz": 105, "numax_where": "Sect. 4.1",
         "dnu_uHz": 197.29, "dnu_where": "Table 1",
         "sigma_rv_cms": 46, "sigma_rv_where": "Sect. 2",
         "exposure_s": 25, "exposure_where": "Sect. 2",
         "amp_cms": 2.57, "amp_where": "Table 1", "white_cms": 1.51}
CITE = "Campante et al. 2026"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from texsvg import tex_glyphs  # noqa: E402  (LaTeX glyphs for the symbols)

NIGHT_SHOWN = 2  # 1-based: the longest night of the run
F0, F1 = 2.0, 8.2  # mHz shown
CHILE = timezone(timedelta(hours=-4))  # local time at Paranal in May 2024
# figure geometry
TOP_H, BOT_H = 436, 322
X_SEAM_TOP, X_SEAM_BOT = 800, 610
DASH = 11.0  # dash period of the flowing light (6 on, 5 off)
FLOW_S = 1.1  # seconds per dash period


# --------------------------------------------------------------------------- data
def jd_to_utc(jd):
    return datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(days=jd - 2440587.5)


def detrend(t, v, w, nights, half_width_d):
    out = np.empty_like(v)
    for a, b in nights:
        tt, vv, ww = t[a:b], v[a:b], w[a:b]
        for i in range(b - a):
            k = np.clip(1 - np.abs(tt - tt[i]) / half_width_d, 0, None) * ww
            out[a + i] = vv[i] - np.sum(k * vv) / np.sum(k)
    return out


def amplitude_spectrum(ts, y, w, nu):
    y = y - np.sum(w * y) / np.sum(w)
    amp = np.empty(len(nu))
    for i0 in range(0, len(nu), 400):
        ph = 2 * np.pi * nu[i0:i0 + 400, None] * ts[None, :]
        c, s = np.cos(ph), np.sin(ph)
        cc, ss, cs = (w * c * c).sum(1), (w * s * s).sum(1), (w * c * s).sum(1)
        yc, ys = (w * y * c).sum(1), (w * y * s).sum(1)
        det = cc * ss - cs * cs
        amp[i0:i0 + 400] = np.hypot((yc * ss - ys * cs) / det, (ys * cc - yc * cs) / det)
    return amp


def gauss_smooth(p, step, fwhm):
    sig = fwhm / 2.3548
    x = np.arange(-4 * sig, 4 * sig + step, step)
    k = np.exp(-0.5 * (x / sig) ** 2)
    return np.convolve(p, k, mode="same") / np.convolve(np.ones_like(p), k, mode="same")


# --------------------------------------------------------------------------- curves
def bez(p, t):
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = p
    u = 1 - t
    return (u**3 * x0 + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t**3 * x3,
            u**3 * y0 + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t**3 * y3)


def bez_len(p, n=400):
    pts = [bez(p, i / n) for i in range(n + 1)]
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(n))


def bez_split(p, t):
    (p0, p1, p2, p3) = p
    lerp = lambda a, b: (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    a, b, c = lerp(p0, p1), lerp(p1, p2), lerp(p2, p3)
    d, e = lerp(a, b), lerp(b, c)
    f = lerp(d, e)
    return (p0, a, d, f), (f, e, c, p3)


def split_at_x(p, x):
    lo, hi = 0.0, 1.0
    f = lambda t: bez(p, t)[0] - x
    if f(lo) * f(hi) > 0:
        raise ValueError("curve does not cross the seam")
    for _ in range(60):
        mid = (lo + hi) / 2
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return bez_split(p, (lo + hi) / 2)


def d_of(curves, dx=0.0, dy=0.0):
    (x0, y0) = curves[0][0]
    s = f"M{x0 - dx:.1f} {y0 - dy:.1f}"
    for c in curves:
        s += " C" + ", ".join(f"{x - dx:.1f} {y - dy:.1f}" for x, y in c[1:])
    return s


def link(curves, phase, delay_s, dx=0.0, dy=0.0, seam=False):
    """One flowing dashed piece; phase = path length drawn before it, for a seamless dash."""
    shift = (phase % DASH) / DASH
    anim = (shift - 1) * FLOW_S
    cls = "ray flowray eo-link" + (" eo-seam" if seam else "")
    return (f'<g class="b-pop{" eo-seam" if seam else ""}" style="--d:{delay_s:.2f}s">'
            f'<path class="{cls}" style="animation-delay:{anim:.3f}s" d="{d_of(curves, dx, dy)}"/></g>')


def node(x, y, delay_s, seam=False):
    return f'<rect class="eo-node b-pop{" eo-seam" if seam else ""}" style="--d:{delay_s:.2f}s" x="{x - 3:.1f}" y="{y - 3:.1f}" width="6" height="6"/>'


def text(x, y, s, cls, delay_s, anchor="start"):
    a = "" if anchor == "start" else f' text-anchor="{anchor}"'
    return f'<text class="{cls} b-pop" style="--d:{delay_s:.2f}s" x="{x:.1f}" y="{y:.1f}"{a}>{s}</text>'


def svg(cls, w, h, title, desc, body, tid):
    return (f'<svg class="bp-svg {cls}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img" '
            f'aria-labelledby="{tid}-t {tid}-d"><title id="{tid}-t">{title}</title><desc id="{tid}-d">{desc}</desc>'
            + "".join(body) + "</svg>\n")


# --------------------------------------------------------------------------- main
def main(src: Path, root: Path) -> int:
    raw = src.read_bytes()
    md5 = hashlib.md5(raw).hexdigest()
    if md5 != SOURCE["md5"]:
        raise SystemExit(f"checksum {md5} does not match the Zenodo record")
    d = np.loadtxt(src, comments="#")
    keep = d[:, 9] == 1
    t, v, e = d[keep, 0], d[keep, 1] * 1e5, d[keep, 2] * 1e5  # cm/s
    rv_kms = d[keep, 1]
    gaps = np.where(np.diff(t) > 0.25)[0]
    edges = np.concatenate([[0], gaps + 1, [len(t)]])
    nights = [(int(edges[i]), int(edges[i + 1])) for i in range(len(edges) - 1)]
    w = 1 / e**2
    res = detrend(t, v, w, nights, 1.2 / 24)
    ts = (t - t[0]) * 86400.0
    step = 1e-6
    nu = np.arange(0.5e-3, 8.25e-3, step)
    amp = amplitude_spectrum(ts, res, w, nu)
    p = amp**2
    hi = (nu >= 6e-3) & (nu <= 8e-3)
    white_p, white_amp = float(p[hi].mean()), float(amp[hi].mean())
    smooth = gauss_smooth(p, step, 4 * PAPER["dnu_uHz"] * 1e-6)
    sel = (nu >= 2e-3) & (nu <= 7.5e-3)
    peak_uHz = float(nu[sel][np.argmax(smooth[sel])] * 1e6)
    a, b = nights[NIGHT_SHOWN - 1]
    hours = (t[a:b] - t[a]) * 24
    start, end = jd_to_utc(t[a]), jd_to_utc(t[b - 1])
    first_rv, first_err = float(rv_kms[a]), float(e[a])
    median_rv = float(np.median(rv_kms))
    night_date = f"{start.astimezone(CHILE).day} to {end.astimezone(CHILE).strftime('%-d %B %Y')}"

    # ------------------------------------------------------------- data thread geometry
    entry = ((766, 268), (792, 268), (800, 107), (816, 107))  # detector to the first stage
    a1, a2 = split_at_x(entry, X_SEAM_TOP)
    c_a = ((816, 306), (816, 372), (812, 418), (800, 418))  # last stage down to the corridor
    c_b = ((800, 418), (600, 430), (240, 410), (40, 422))  # along the foot of the light path
    c_c = ((40, 422), (24, 423), (18, 428), (18, TOP_H))  # turning down into the night panel
    c_d = ((18, TOP_H), (18, TOP_H + 34), (10, TOP_H + 104), (18, TOP_H + 139))
    d_arc = ((596, TOP_H + 145), (626, TOP_H + 95), (646, TOP_H + 145), (680 - 3, TOP_H + 145))
    d1, d2 = split_at_x(d_arc, X_SEAM_BOT)
    L = bez_len
    T_ENTRY, T_DESC, T_ARC = 1.80, 2.65, 3.05

    # ------------------------------------------------------------- exposure column (x 800 to 1220)
    E = []
    dx = X_SEAM_TOP
    E.append(link([a2], L(a1), T_ENTRY, dx=dx, seam=True))
    for (yy, dl) in ((107, 1.92), (210, 2.2), (300, 2.5)):
        E.append(node(16, yy, dl))
    E.append(link([((16, 113), (4, 140), (4, 180), (16, 204))], 0, 2.2))
    E.append(link([((16, 216), (4, 244), (4, 272), (16, 294))], 0, 2.5))
    E.append(link([c_a], 0, T_DESC, dx=dx, seam=True))
    E.append(text(36, 28, f"From one {PAPER['exposure_s']}-second exposure to one velocity", "eo-title", 1.86))
    # stage 1: extracted spectrum (schematic outline)
    E.append(text(36, 80, "extracted spectrum", "eo-label", 1.92))
    spec = ("M36 98 H64 l4 12 l4 -12 H96 l3 6 l3 -6 H128 l4 18 l4 -18 H160 l3 5 l3 -5 H190 l4 10 l4 -10 "
            "H222 l3 7 l3 -7 H252 l4 16 l4 -16 H284 l3 6 l3 -6 H316 l4 11 l4 -11 H348 l3 5 l3 -5 H400")
    E.append(f'<path class="bp b-draw" style="--d:1.95s;--dur:.25s" pathLength="1" d="{spec}"/>')
    # stage 2: cross-correlation dip (schematic outline) and the shift it measures
    E.append(text(36, 176, "cross-correlation", "eo-label", 2.2))
    E.append('<path class="bp-thin b-draw" style="--d:2.22s;--dur:.17s" pathLength="1" d="M36 232 H400 M188 186 V236"/>')
    E.append('<path class="bp b-draw" style="--d:2.25s;--dur:.2s" pathLength="1" d="M36 192 C 200 192, 214 228, 246 228 C 278 228, 292 192, 400 192"/>')
    E.append('<path class="eo-mark b-pop" style="--d:2.4s" d="M246 184 V236"/>')
    E.append('<path class="eo-dim b-pop" style="--d:2.42s" d="M192 208 H242 M192 204 v8 M242 204 v8"/>')
    E.append(text(217, 202, "shift", "eo-num", 2.42, "middle"))
    E.append(text(36, 254, f"{median_rv:.1f} km/s", "eo-value", 2.42))
    # stage 3: one velocity, with its uncertainty and the signal it has to reveal
    E.append(text(36, 304, "one velocity", "eo-label", 2.52))
    E.append(text(36, 324, f"{first_rv:.4f} km/s ± {first_err:.0f} cm/s", "eo-value", 2.55))
    E.append(text(36, 346, f"uncertainty {PAPER['sigma_rv_cms']} cm/s", "eo-note", 2.58))
    E.append(text(36, 362, f"oscillation {PAPER['amp_cms']} cm/s", "eo-note", 2.6))
    exp_svg = svg("eo-svg eo-exposure", 420, TOP_H, "From one exposure to one radial velocity",
                  f"Each {PAPER['exposure_s']}-second exposure gives an extracted spectrum; cross-correlating it gives a dip whose shift is the "
                  f"radial velocity, {median_rv:.1f} km/s for GJ 570 A. One velocity has an average uncertainty of {PAPER['sigma_rv_cms']} cm/s, while "
                  f"the oscillations reach about {PAPER['amp_cms']} cm/s.", E, "eo-x")

    # ------------------------------------------------------------- light path pieces (between markers)
    thread = [
        "  <!-- generated: data thread (figures/observing/build_espresso_output.py) -->",
        "  " + node(766, 268, T_ENTRY, seam=True),
        "  " + link([a1], 0, T_ENTRY, seam=True),
        "  " + link([c_b, c_c], L(c_a), T_DESC, seam=True),
        "  <!-- /generated -->",
    ]
    lp = root / "_includes/figures/vlt-lightpath.svg"
    lp_text = lp.read_text()
    lp_text, n = re.subn(r"  <!-- generated: data thread.*?<!-- /generated -->", "\n".join(thread), lp_text, flags=re.S)
    if n != 1:
        raise SystemExit("generated markers not found in vlt-lightpath.svg")
    lp.write_text(lp_text)

    # ------------------------------------------------------------- night panel (x 0 to 610)
    N = []
    xp0, xp1, hmax = 70.0, 596.0, 10.0
    yc, sc = 145.0, 85.0 / 300.0  # zero line; units per cm/s
    N.append(link([c_d], L(c_a) + L(c_b) + L(c_c), T_DESC, dy=TOP_H, seam=True))
    N.append(node(18, 145, 2.75, seam=True))
    N.append(text(xp0, 22, f"Radial velocity during the night of {night_date}", "eo-title", 2.75))
    N.append(text(xp0, 40, f"{b - a} exposures", "eo-note", 2.75))
    N.append(text(xp0, 56, "radial velocity, cm/s", "eo-num", 2.85))
    N.append(f'<path class="bp-thin b-draw" style="--d:2.75s;--dur:.17s" pathLength="1" d="M{xp0} {yc - 85} V{yc + 85} M{xp0} {yc} H{xp1}"/>')
    ticks = []
    for cms in (-200, 0, 200):
        yy = yc - cms * sc
        lab = f"{cms:+d}".replace("-", "−") if cms else "0"
        ticks.append(f'<path class="bp-thin" d="M{xp0 - 4} {yy:.1f} h4"/><text class="eo-num" x="{xp0 - 7}" y="{yy + 4:.1f}" text-anchor="end">{lab}</text>')
    for hh in range(0, 11, 2):
        xx = xp0 + (xp1 - xp0) * hh / hmax
        ticks.append(f'<path class="bp-thin" d="M{xx:.1f} {yc + 85} v4"/><text class="eo-num" x="{xx:.1f}" y="{yc + 102:.1f}" text-anchor="middle">{hh}</text>')
    ticks.append(f'<text class="eo-num" x="{xp1}" y="{yc + 118:.1f}" text-anchor="end">hours since the start of the night</text>')
    N.append(f'<g class="b-pop" style="--d:2.85s">{"".join(ticks)}</g>')
    dots = "".join(f"M{xp0 + (xp1 - xp0) * h / hmax:.1f} {yc - r * sc:.1f}h0" for h, r in zip(hours, res[a:b]))
    N.append(f'<path class="eo-dots b-pop" style="--d:2.95s" d="{dots}"/>')
    N.append(link([d1], 0, T_ARC, seam=True))
    doi = "https://doi.org/10.5281/zenodo.17236515"
    N.append(f'<a href="{doi}">' + text(xp0, 296, f"Data: {CITE}, Zenodo, CC BY 4.0", "eo-note eo-data", 2.95) + "</a>")
    night_svg = svg("eo-svg eo-night", 610, BOT_H, f"Radial velocity of GJ 570 A during the night of {night_date}",
                    f"{b - a} radial velocities from one night, with slow drifts removed, scatter by tens of centimetres per second around zero; "
                    "the oscillations are far smaller than the uncertainty of a single point.", N, "eo-n")

    # ------------------------------------------------------------- power spectrum (x 610 to 1220)
    S = []
    xc0, xc1 = 70.0, 596.0
    yb, ytop, pmax = 230.0, 60.0, 60.0
    ncol = int(xc1 - xc0)
    cols_max, cols_smooth = [], []
    for c in range(ncol):
        lo = F0 + (F1 - F0) * c / ncol
        up = F0 + (F1 - F0) * (c + 1) / ncol
        m = (nu * 1e3 >= lo) & (nu * 1e3 < up)
        cols_max.append(float(p[m].max()))
        cols_smooth.append(float(smooth[m].mean()))
    if max(cols_max) > pmax:
        raise SystemExit(f"raise pmax: highest column {max(cols_max):.1f}")

    def yp(pw):
        return yb - (yb - ytop) * min(pw, pmax) / pmax

    S.append(link([d2], L(d1), T_ARC, dx=X_SEAM_BOT, dy=TOP_H, seam=True))
    S.append(node(70, 145, 3.1, seam=True))
    S.append(text(xc0, 22, "Power spectrum of the five nights", "eo-title", 3.1))
    S.append(text(xc0, 40, f"{int(keep.sum()):,} velocities", "eo-note", 3.1))
    S.append(text(xc0, 56, "power, (cm/s)²", "eo-num", 3.2))
    S.append(f'<path class="bp-thin b-draw" style="--d:3.1s;--dur:.17s" pathLength="1" d="M{xc0} {ytop} V{yb} H{xc1}"/>')
    t2 = []
    for fm in range(2, 9):
        xx = xc0 + (xc1 - xc0) * (fm - F0) / (F1 - F0)
        t2.append(f'<path class="bp-thin" d="M{xx:.1f} {yb} v4"/><text class="eo-num" x="{xx:.1f}" y="{yb + 17}" text-anchor="middle">{fm}</text>')
    for pw in (20, 40, 60):
        t2.append(f'<path class="bp-thin" d="M{xc0 - 4} {yp(pw):.1f} h4"/><text class="eo-num" x="{xc0 - 7}" y="{yp(pw) + 4:.1f}" text-anchor="end">{pw}</text>')
    t2.append(f'<text class="eo-num" x="{xc1}" y="{yb + 32}" text-anchor="end">frequency, mHz</text>')
    S.append(f'<g class="b-pop" style="--d:3.2s">{"".join(t2)}</g>')
    area = (f"M{xc0} {yb} " + " ".join(f"L{xc0 + c:.0f} {yp(v_):.1f} L{xc0 + c + 1:.0f} {yp(v_):.1f}" for c, v_ in enumerate(cols_max))
            + f" L{xc1} {yb} Z")
    S.append(f'<path class="eo-power b-pop" style="--d:3.25s" d="{area}"/>')
    sm = "M" + " L".join(f"{xc0 + c + 0.5:.1f} {yp(3 * v_):.1f}" for c, v_ in enumerate(cols_smooth))
    S.append(f'<path class="eo-smooth b-draw" style="--d:3.3s;--dur:.53s" pathLength="1" d="{sm}"/>')
    S.append(f'<path class="eo-noise b-pop" style="--d:3.6s" d="M{xc0} {yp(3 * white_p):.1f} H{xc1}"/>')
    xn = xc0 + (xc1 - xc0) * (PAPER["numax_uHz"] / 1e3 - F0) / (F1 - F0)
    numax_glyphs = tex_glyphs(r"\nu_{\max}", 14)[0]
    S.append(f'<g class="b-pop" style="--d:3.7s"><path class="eo-numax" d="M{xn:.1f} {ytop} V{yb}"/>'
             f'<g class="eo-tex" transform="translate({xn + 6:.1f} {ytop + 13})">{numax_glyphs}</g></g>')
    # legend: every mark on the panel, with its source
    lg = []
    def swatch(x, y, kind):
        if kind == "fill":
            return f'<rect class="eo-power" x="{x}" y="{y - 8}" width="16" height="9"/>'
        cls = {"line": "eo-smooth", "dash": "eo-noise", "dot": "eo-numax"}[kind]
        return f'<path class="{cls}" d="M{x} {y - 4} h16"/>'
    rows = [
        (xc0, 284, "fill", "power"),
        (300, 284, "dash", "white noise ×3"),
        (xc0, 300, "line", [("text", "smoothed, "), ("tex", r"4\Delta\nu"), ("text", " ≈ 790 μHz")]),
        (xc0, 316, "dot", [("tex", r"\nu_{\max}"), ("text", f' {PAPER["numax_uHz"]} μHz')]),
    ]
    adv = 0.6 * 11  # Geist Mono advance at the 11 px legend size
    for x, y, kind, label in rows:
        parts = [("text", label)] if isinstance(label, str) else label
        cur, out = x + 22, []
        for kind_, seg in parts:
            if kind_ == "text":
                out.append(f'<text class="eo-note" x="{cur:.1f}" y="{y}" style="white-space:pre">{seg}</text>')
                cur += len(seg) * adv
            else:
                body, w = tex_glyphs(seg, 12)
                out.append(f'<g class="eo-tex-note" transform="translate({cur + 1:.1f} {y})">{body}</g>')
                cur += w + 2
        lg.append(swatch(x, y, kind) + "".join(out))
    S.append(f'<g class="b-pop" style="--d:3.75s">{"".join(lg)}</g>')
    spec_svg = svg("eo-svg eo-spectrum", 610, BOT_H, "Power spectrum of the radial velocities of GJ 570 A, five nights",
                   f"The power spectrum of {int(keep.sum()):,} velocities from five nights. Peaks crowd together near "
                   f"{PAPER['numax_uHz'] / 1e3:.1f} mHz, where the smoothed power rises above the white-noise level: the star's oscillations, "
                   "with periods of three to four minutes.", S, "eo-s")

    figs = root / "_includes/figures"
    (figs / "espresso-exposure.svg").write_text(exp_svg)
    (figs / "espresso-night.svg").write_text(night_svg)
    (figs / "espresso-spectrum.svg").write_text(spec_svg)

    # ------------------------------------------------------------- data files
    data = {
        "night": {"index": NIGHT_SHOWN, "n": int(b - a), "start_utc": start.isoformat(timespec="minutes"),
                  "end_utc": end.isoformat(timespec="minutes"), "first_rv_kms": round(first_rv, 5),
                  "first_rv_err_cms": round(first_err, 1),
                  "hours": [round(float(h), 4) for h in hours], "rv_cms": [round(float(r), 1) for r in res[a:b]]},
        "spectrum": {"f_mHz": [F0, F1], "columns": ncol, "power_col_max_cms2": [round(x, 2) for x in cols_max],
                     "smooth_col_mean_cms2": [round(x, 3) for x in cols_smooth], "white_power_cms2": round(white_p, 3)},
        "median_rv_kms": round(median_rv, 4),
    }
    out_dir = root / "assets/data/observing"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "gj570a_output.json").write_text(json.dumps(data, separators=(",", ":")) + "\n")
    prov = {
        "source": SOURCE, "paper_values_used": PAPER,
        "selection": "FLUX_CORR_CHECK == 1", "n_rows": int(len(d)), "n_used": int(keep.sum()),
        "nights": [{"n": int(b_ - a_), "start_utc": jd_to_utc(t[a_]).isoformat(timespec="minutes")} for a_, b_ in nights],
        "median_cadence_s": round(float(np.median(np.diff(t)) * 86400), 1),
        "mean_rv_err_cms": round(float(e.mean()), 1),
        "median_rv_kms": round(median_rv, 4),
        "rms_detrended_cms": round(float(res.std()), 1),
        "detrend": "per night, minus a weighted triangular smoothing of half-width 1.2 h",
        "spectrum": "weighted least-squares sine fits, weights 1/RV_ERR^2, 1 microhertz grid, power = amplitude^2",
        "white_noise": {"mean_amplitude_6_8_mHz_cms": round(white_amp, 3), "mean_power_6_8_mHz_cms2": round(white_p, 3)},
        "smooth": "Gaussian, FWHM = 4 x 197.29 microhertz, edge-corrected",
        "smooth_peak_uHz": round(peak_uHz, 0),
        "display": "raw power: highest value per display column; smooth curve and noise level x3, as in the paper's Fig. 3",
        "script": "figures/observing/build_espresso_output.py",
    }
    (out_dir / "gj570a_provenance.json").write_text(json.dumps(prov, indent=1) + "\n")
    print(json.dumps({k: prov[k] for k in ("n_used", "median_rv_kms", "rms_detrended_cms", "white_noise", "smooth_peak_uHz")}))
    print("night", night_date, b - a, "| first", round(first_rv, 4), round(first_err, 1), "| highest column", round(max(cols_max), 1))
    print("KB:", {n_: round(len(s_) / 1024, 1) for n_, s_ in (("exposure", exp_svg), ("night", night_svg), ("spectrum", spec_svg))})
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(Path(sys.argv[1]), Path(sys.argv[2])))
