"""Build FIG 2 on /observing/paranal/: the light path from a Unit Telescope through the Coude train
to ESPRESSO, and the power spectrum of the public GJ 570 A velocities that came out of it.

Usage:
    uv run --with numpy python -I figures/observing/build_espresso_output.py <repo root> [<ts_HD_131977>]

With the data file, the arrays are recomputed and written to assets/data/observing/ first; without
it, the figure is drawn from the recorded assets/data/observing/gj570a_output.json.

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
Display: the raw power at 526 columns over 2 to 8.2 mHz, each column the highest power among the
frequencies it covers; the smooth curve multiplied by three, as in Fig. 3 of the paper; no power
ticks, so only the shape is read. nu_max is the paper's value (Sect. 4.1).

The light path is a schematic, not to scale, after ESO's descriptions of the Unit Telescopes and
ESPRESSO (Pepe et al. 2014, arXiv:1401.5918): starlight to the primary mirror, the secondary, the
tertiary, down the Coude train under the platform, into the spectrograph (collimator, echelle
grating, cross-disperser, detector). Both SVGs share one scale (800 + 480 units wide, 416 high);
the flowing dash of the light runs on across the seam into the spectrum.

Outputs: _includes/figures/vlt-lightpath.svg, _includes/figures/espresso-spectrum.svg and, with the
data file, assets/data/observing/gj570a_output.json and gj570a_provenance.json.
"""

from __future__ import annotations

import hashlib
import json
import math
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
NCOL = 526  # display columns of the recorded spectrum
# figure geometry: two SVGs on one scale, side by side
W_PATH, W_SPEC, H = 800, 480, 416
X0_SPEC = 44.0  # left axis of the spectrum
DASH = 11.0  # dash period of the flowing light (6 on, 5 off)
FLOW_S = 1.1  # seconds per dash period


# --------------------------------------------------------------------------- helpers
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


# --------------------------------------------------------------------------- data
def compute(src: Path, root: Path) -> None:
    """Recompute the recorded arrays from the Zenodo file and write them with their provenance."""
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
    median_rv = float(np.median(rv_kms))
    cols_max, cols_smooth = [], []
    for c in range(NCOL):
        lo = F0 + (F1 - F0) * c / NCOL
        up = F0 + (F1 - F0) * (c + 1) / NCOL
        m = (nu * 1e3 >= lo) & (nu * 1e3 < up)
        cols_max.append(float(p[m].max()))
        cols_smooth.append(float(smooth[m].mean()))
    data = {
        "night": {"index": NIGHT_SHOWN, "n": int(b - a), "start_utc": start.isoformat(timespec="minutes"),
                  "end_utc": end.isoformat(timespec="minutes"), "first_rv_kms": round(float(rv_kms[a]), 5),
                  "first_rv_err_cms": round(float(e[a]), 1),
                  "hours": [round(float(h), 4) for h in hours], "rv_cms": [round(float(r), 1) for r in res[a:b]]},
        "spectrum": {"f_mHz": [F0, F1], "columns": NCOL, "power_col_max_cms2": [round(x, 2) for x in cols_max],
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
        "display": "raw power: highest value per display column; smooth curve x3, as in the paper's Fig. 3",
        "script": "figures/observing/build_espresso_output.py",
    }
    (out_dir / "gj570a_provenance.json").write_text(json.dumps(prov, indent=1) + "\n")
    print(json.dumps({k: prov[k] for k in ("n_used", "median_rv_kms", "rms_detrended_cms", "white_noise", "smooth_peak_uHz")}))


# --------------------------------------------------------------------------- light path
# Hand-placed schematic in the 800 x 416 space: structure first, then the light, then the instrument.
LIGHT_PATH = [
    # ground, pier, fork, truss, top ring
    '<path class="bp-thin b-draw" style="--d:0s;--dur:.17s" pathLength="1" d="M20 372 L780 372"/>',
    '<path class="bp b-draw" style="--d:.03s;--dur:.17s" pathLength="1" d="M112 372 L112 330 L308 330 L308 372"/>',
    '<path class="bp-thin b-pop" style="--d:.17s" d="' + " ".join(f"M{x} 372 l8 -8" for x in range(120, 300, 16)) + '"/>',
    '<path class="bp b-draw" style="--d:.06s;--dur:.17s" pathLength="1" d="M138 330 L138 236 L205 236 M282 330 L282 236"/>',
    '<circle class="bp b-pop" style="--d:.2s" cx="210" cy="236" r="5"/>',
    '<path class="bp-thin b-draw" style="--d:.09s;--dur:.17s" pathLength="1" d="M132 288 L190 60 M288 288 L230 60 M132 288 L230 60 M288 288 L190 60"/>',
    '<path class="bp b-draw" style="--d:.12s;--dur:.17s" pathLength="1" d="M184 60 L236 60"/>',
    # mirrors: primary, secondary, tertiary, the Coude train
    '<path class="bp mirror b-pop" style="--d:.2s" d="M128 292 Q210 314 292 292"/>',
    '<path class="bp mirror b-pop" style="--d:.22s" d="M196 66 Q210 60 224 66"/>',
    '<path class="bp mirror b-pop" style="--d:.24s" d="M202 228 L218 244"/>',
    '<path class="bp mirror b-pop" style="--d:.26s" d="M276 230 L288 242 M276 346 L288 358 M364 346 L376 358 M364 294 L376 306"/>',
    # the light: down to the primary, up to the secondary, down to the tertiary, along the Coude train
    '<path class="ray b-draw" style="--d:.3s;--dur:.32s" pathLength="1" d="M150 20 L150 296 M270 20 L270 296"/>',
    '<path class="eo-head b-pop" style="--d:.6s" d="M146.4 287 L150 293 L153.6 287 M266.4 287 L270 293 L273.6 287"/>',
    '<path class="ray b-draw" style="--d:.62s;--dur:.18s" pathLength="1" d="M150 296 L204 66 M270 296 L216 66"/>',
    '<path class="ray b-draw" style="--d:.8s;--dur:.15s" pathLength="1" d="M204 66 L210 230 M216 66 L210 230"/>',
    '<g class="b-pop" style="--d:.95s"><path class="ray flowray" d="M212 236 L282 236 L282 352 L370 352 L370 300 L460 300"/></g>',
    '<path class="eo-head b-pop" style="--d:1.33s" d="M452 296.4 L458 300 L452 303.6"/>',
    # ESPRESSO: fibre in, collimator, echelle grating, cross-disperser, detector with its orders
    '<rect class="bp lab b-pop" style="--d:1s" x="460" y="120" width="320" height="236" rx="4" stroke-dasharray="5 4"/>',
    '<path class="bp b-draw" style="--d:1.35s;--dur:.1s" pathLength="1" d="M460 300 C490 300 496 260 510 252"/>',
    '<circle class="bp-fill b-pop" style="--d:1.44s" cx="512" cy="251" r="2.5"/>',
    '<path class="bp mirror b-pop" style="--d:1.1s" d="M560 214 Q568 251 560 288"/>',
    '<path class="ray b-draw" style="--d:1.45s;--dur:.1s" pathLength="1" d="M512 251 L560 220 M512 251 L560 282"/>',
    '<g class="b-pop" style="--d:1.15s"><rect class="bp" x="636" y="182" width="16" height="72" transform="rotate(-12 644 218)"/>'
    '<path class="bp-thin" d="M638 190 l12 -4 M638 202 l12 -4 M638 214 l12 -4 M638 226 l12 -4 M638 238 l12 -4" transform="rotate(-12 644 218)"/></g>',
    '<path class="ray b-draw" style="--d:1.55s;--dur:.1s" pathLength="1" d="M564 230 L636 196 M564 272 L636 238"/>',
    '<path class="bp b-pop" style="--d:1.2s" d="M690 244 L702 296 L678 296 Z"/>',
    '<path class="ray warmray b-draw" style="--d:1.65s;--dur:.1s" pathLength="1" d="M640 220 L690 252 M642 232 L690 268 M644 244 L690 284"/>',
    '<rect class="bp b-pop" style="--d:1.25s" x="722" y="232" width="44" height="72" rx="2"/>',
    '<path class="ray warmray b-draw" style="--d:1.75s;--dur:.05s" pathLength="1" d="M700 270 L720 268"/>',
    '<path class="order b-pop" style="--d:1.8s" d="' + " ".join(f"M726 {y} q18 -4 36 2" for y in range(240, 291, 10)) + '"/>',
    # one title per stage
    text(300, 44, "Unit Telescope, 8.2 m", "eo-title", 0.2),
    text(300, 398, "Coudé train", "eo-title", 0.26),
    text(474, 146, "ESPRESSO", "eo-title", 1.0),
]


# --------------------------------------------------------------------------- figure
def draw(root: Path) -> None:
    data = json.loads((root / "assets/data/observing/gj570a_output.json").read_text())
    spec = data["spectrum"]
    cols_max, cols_smooth = spec["power_col_max_cms2"], spec["smooth_col_mean_cms2"]
    if spec["columns"] != NCOL or spec["f_mHz"] != [F0, F1]:
        raise SystemExit("recorded spectrum does not match the display grid; rerun with the data file")

    # the data thread: out of the detector, across the seam, into the spectrum's axis
    out1 = ((766, 268), (778, 268), (788, 268), (W_PATH, 268))
    out2 = ((W_PATH, 268), (W_PATH + 12, 268), (W_PATH + 24, 268), (W_PATH + X0_SPEC, 268))
    T_OUT = 1.85
    path_body = LIGHT_PATH + [
        node(766, 268, T_OUT, seam=True),
        link([out1], 0, T_OUT, seam=True),
    ]
    lp_svg = svg("vlt-svg", W_PATH, H, "Light path from a VLT Unit Telescope to ESPRESSO, schematic",
                 "Starlight reflects off the 8.2 m primary mirror to the secondary and the tertiary, runs down the Coudé train "
                 "under the platform into ESPRESSO, and is spread by an échelle grating and a cross-disperser into a spectrum "
                 "on the detector.", path_body, "lp")

    S = [link([out2], bez_len(out1), T_OUT, dx=W_PATH, seam=True)]
    x0, x1, yb, ytop = X0_SPEC, 460.0, 340.0, 72.0
    pmax = max(cols_max) * 1.04
    S.append(node(x0, 268, 2.0, seam=True))
    S.append(text(x0, 44, "Oscillations of GJ 570 A", "eo-title", 2.0))

    def yp(pw):
        return yb - (yb - ytop) * min(pw, pmax) / pmax

    def xf(fm):
        return x0 + (x1 - x0) * (fm - F0) / (F1 - F0)

    S.append(f'<path class="bp-thin b-draw" style="--d:2.0s;--dur:.17s" pathLength="1" d="M{x0} {ytop} V{yb} H{x1}"/>')
    ax = [f'<path class="bp-thin" d="M{xf(fm):.1f} {yb} v4"/><text class="eo-num" x="{xf(fm):.1f}" y="{yb + 17}" text-anchor="middle">{fm}</text>'
          for fm in (2, 4, 6, 8)]
    ax.append(f'<text class="eo-num" x="{x1}" y="{yb + 34}" text-anchor="end">frequency, mHz</text>')
    ax.append(f'<text class="eo-num" x="{x0 + 6}" y="{ytop + 4}">power</text>')
    S.append(f'<g class="b-pop" style="--d:2.1s">{"".join(ax)}</g>')
    cw = (x1 - x0) / NCOL
    area = (f"M{x0} {yb} " + " ".join(f"L{x0 + c * cw:.2f} {yp(v_):.1f} L{x0 + (c + 1) * cw:.2f} {yp(v_):.1f}" for c, v_ in enumerate(cols_max))
            + f" L{x1} {yb} Z")
    S.append(f'<path class="eo-power b-pop" style="--d:2.15s" d="{area}"/>')
    sm = "M" + " L".join(f"{x0 + (c + 0.5) * cw:.1f} {yp(3 * v_):.1f}" for c, v_ in enumerate(cols_smooth))
    S.append(f'<path class="eo-smooth b-draw" style="--d:2.2s;--dur:.53s" pathLength="1" d="{sm}"/>')
    xn = xf(PAPER["numax_uHz"] / 1e3)
    numax_glyphs = tex_glyphs(r"\nu_{\max}", 15)[0]
    S.append(f'<g class="b-pop" style="--d:2.6s"><path class="eo-numax" d="M{xn:.1f} {ytop - 6} V{yb}"/>'
             f'<g class="eo-tex" transform="translate({xn + 7:.1f} {ytop + 8})">{numax_glyphs}</g></g>')
    doi = "https://doi.org/10.5281/zenodo.17236515"
    S.append(f'<a href="{doi}">' + text(x0, 404, f"Data: {CITE}, CC BY 4.0", "eo-note eo-data", 2.6) + "</a>")
    sp_svg = svg("eo-svg eo-spectrum", W_SPEC, H, "Power spectrum of the radial velocities of GJ 570 A",
                 "The power spectrum of the ESPRESSO velocities of GJ 570 A from five nights in May 2024. Power gathers in a hump "
                 "around nu max, near 4.7 millihertz: the star's oscillations, with periods of three to four minutes.", S, "eo-s")

    figs = root / "_includes/figures"
    (figs / "vlt-lightpath.svg").write_text(lp_svg)
    (figs / "espresso-spectrum.svg").write_text(sp_svg)
    print("KB:", {n_: round(len(s_) / 1024, 1) for n_, s_ in (("lightpath", lp_svg), ("spectrum", sp_svg))})


def main(argv: list[str]) -> int:
    if len(argv) not in (2, 3):
        print(__doc__)
        return 2
    root = Path(argv[1])
    if len(argv) == 3:
        compute(Path(argv[2]), root)
    draw(root)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
