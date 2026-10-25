"""Build the output panel of FIG 2 on /observing/paranal/ from the public GJ 570 A velocities.

Usage:
    uv run --with numpy python -I figures/observing/build_espresso_output.py <ts_HD_131977> <repo root>

Input: the file ts_HD_131977 of the Zenodo record doi:10.5281/zenodo.17236515 (version
10.5281/zenodo.17236516, CC BY 4.0), the ESPRESSO radial velocities of GJ 570 A (HD 131977) from
programme 0113.D-0255(B), May 2024, published with Campante et al. 2026 (arXiv:2610.20985).

Method, after Sect. 2 and 4.1 of the paper:
- keep the rows whose FLUX_CORR_CHECK flag is 1, as the file header instructs (2,250 of 2,369);
- split into nights at gaps longer than 6 h;
- high-pass filter each night by subtracting a weighted triangular smoothing with a 1.2 h cutoff
  (implemented as a triangle of half-width 1.2 h; this only affects frequencies far below the
  oscillations);
- amplitude spectrum by weighted least-squares sine fits (weighted Lomb-Scargle) with weights
  1/sigma^2 from the file's RV_ERR, on a 1 microhertz grid; power = amplitude squared.
  The paper further optimises the weights; it is not repeated here, so the noise level differs a
  little (1.55 here against 1.51 cm/s in the paper, mean amplitude between 6 and 8 mHz);
- the smooth curve is the power convolved with a Gaussian of FWHM 4 times the paper's large
  separation (197.29 microhertz), the kernel the paper uses to locate nu_max.
Display: the raw power is drawn at the panel's resolution, each column showing the highest power
among the frequencies it covers, which is how the full curve renders at this size. The smooth
curve and the noise level are multiplied by three, as in Fig. 3 of the paper.

The links between stages use the figure's moving dashed light style.

Outputs: assets/data/observing/gj570a_output.json (the arrays drawn),
assets/data/observing/gj570a_provenance.json, _includes/figures/espresso-output.svg.
"""

from __future__ import annotations

import hashlib
import json
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
    "paper": "Campante et al. 2026, accepted in A&A, arXiv:2610.20985",
    "programme": "ESO 0113.D-0255(B)",
}
PAPER = {"numax_uHz": 4705, "numax_err_uHz": 105, "dnu_uHz": 197.29, "sigma_rv_cms": 46,
         "white_cms": 1.51, "period_min": "3 to 4"}
NIGHT_SHOWN = 2  # 1-based: the longest night of the run
F0, F1 = 2.0, 8.2  # mHz shown
W, H = 430, 436


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
    num = np.convolve(p, k, mode="same")
    den = np.convolve(np.ones_like(p), k, mode="same")  # edge-corrected
    return num / den


def main(src: Path, root: Path) -> int:
    raw = src.read_bytes()
    md5 = hashlib.md5(raw).hexdigest()
    if md5 != SOURCE["md5"]:
        raise SystemExit(f"checksum {md5} does not match the Zenodo record")
    d = np.loadtxt(src, comments="#")
    keep = d[:, 9] == 1
    t, v, e = d[keep, 0], d[keep, 1] * 1e5, d[keep, 2] * 1e5  # cm/s
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
    white_p = float(p[hi].mean())
    white_amp = float(amp[hi].mean())
    smooth = gauss_smooth(p, step, 4 * PAPER["dnu_uHz"] * 1e-6)
    sel = (nu >= 2e-3) & (nu <= 7.5e-3)
    peak_uHz = float(nu[sel][np.argmax(smooth[sel])] * 1e6)

    # --- display arrays -------------------------------------------------------------
    a, b = nights[NIGHT_SHOWN - 1]
    hours = (t[a:b] - t[a]) * 24
    start, end = jd_to_utc(t[a]), jd_to_utc(t[b - 1])
    xs0, xs1 = 46.0, 414.0
    ncol = int(xs1 - xs0)
    cols_max, cols_smooth = [], []
    for c in range(ncol):
        lo = F0 + (F1 - F0) * c / ncol
        up = F0 + (F1 - F0) * (c + 1) / ncol
        m = (nu * 1e3 >= lo) & (nu * 1e3 < up)
        cols_max.append(float(p[m].max()))
        cols_smooth.append(float(smooth[m].mean()))
    ymax_p = 60.0
    if max(cols_max) > ymax_p:
        raise SystemExit(f"raise ymax_p: highest column {max(cols_max):.1f}")
    data = {
        "night": {"index": NIGHT_SHOWN, "n": int(b - a), "start_utc": start.isoformat(timespec="minutes"),
                  "end_utc": end.isoformat(timespec="minutes"),
                  "hours": [round(float(h), 4) for h in hours], "rv_cms": [round(float(r), 1) for r in res[a:b]]},
        "spectrum": {"f_mHz": [F0, F1], "columns": ncol, "power_col_max_cms2": [round(x, 2) for x in cols_max],
                     "smooth_col_mean_cms2": [round(x, 3) for x in cols_smooth], "white_power_cms2": round(white_p, 3)},
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

    # --- SVG ----------------------------------------------------------------------------
    S = []
    add = S.append
    # spine: the data thread from the detector, down the left edge, with square nodes
    # curved, flowing dashed links (the same moving dash as the light path), shown in their turn
    add('<g class="b-pop eo-thread-out" style="--d:1.95s"><path class="ray flowray eo-link" d="M0 60 C 6 60, 10 60, 14 60"/></g>')
    add('<g class="b-pop" style="--d:2.30s"><path class="ray flowray eo-link" d="M14 63 C 2 90, 2 122, 14 147"/></g>')
    add('<g class="b-pop" style="--d:2.65s"><path class="ray flowray eo-link" d="M14 153 C 0 196, 0 248, 14 289"/></g>')
    for y, dly in ((60, 2.0), (150, 2.45), (292, 2.8)):
        add(f'<rect class="eo-node b-pop" style="--d:{dly}s" x="11" y="{y - 3}" width="6" height="6"/>')
    # row A: one exposure becomes one velocity (schematic: outline)
    add('<text class="bp-label2 b-pop" style="--d:2.0s" x="28" y="34">each exposure, 25 s</text>')
    spec = "M28 60 H44 l3 9 l3 -9 H62 l2 5 l2 -5 H80 l3 12 l3 -12 H96 l2 4 l2 -4 H110 l3 8 l3 -8 H128 l2 6 l2 -6 H142"
    add(f'<path class="bp b-draw" style="--d:2.0s;--dur:.25s" pathLength="1" d="{spec}"/>')
    add('<text class="bp-tick b-pop" style="--d:2.1s" x="28" y="90">extracted spectrum</text>')
    add('<path class="eo-arrow b-pop" style="--d:2.15s" d="M150 66 h16 m-5 -4 l5 4 l-5 4"/>')
    add('<path class="bp-thin b-draw" style="--d:2.15s;--dur:.17s" pathLength="1" d="M178 82 V52 M178 82 H272"/>')
    add('<path class="bp b-draw" style="--d:2.2s;--dur:.2s" pathLength="1" d="M180 56 C206 56 212 80 225 80 C238 80 244 56 270 56"/>')
    add('<path class="eo-mark b-pop" style="--d:2.35s" d="M225 48 V86"/>')
    add('<text class="bp-tick b-pop" style="--d:2.15s" x="178" y="98">cross-correlation dip</text>')
    add('<path class="eo-arrow b-pop" style="--d:2.35s" d="M280 66 h16 m-5 -4 l5 4 l-5 4"/>')
    add('<text class="bp-label2 b-pop" style="--d:2.35s" x="304" y="64">one velocity</text>')
    add(f'<text class="bp-tick b-pop" style="--d:2.35s" x="304" y="78">typical error {PAPER["sigma_rv_cms"]} cm/s</text>')

    # row B: one night of velocities (real data: filled dots)
    yb, sc_b = 200.0, 0.15  # centre, px per cm/s
    xb0, xb1, hmax = 46.0, 414.0, 10.0
    add(f'<text class="bp-label2 b-pop" style="--d:2.45s" x="28" y="128">one night, {b - a} velocities</text>')
    night_label = f"{start.astimezone(timezone(timedelta(hours=-4))).day} to {end.astimezone(timezone(timedelta(hours=-4))).strftime('%-d %B %Y')}, slow drifts removed"
    add(f'<text class="bp-tick b-pop" style="--d:2.45s" x="28" y="142">night of {night_label}</text>')
    add(f'<path class="bp-thin b-draw" style="--d:2.45s;--dur:.17s" pathLength="1" d="M{xb0} {yb - 300 * sc_b:.1f} V{yb + 300 * sc_b:.1f} M{xb0} {yb:.1f} H{xb1}"/>')
    ticks = []
    for cms in (-200, 200):
        yy = yb - cms * sc_b
        ticks.append(f'<path class="bp-thin" d="M{xb0 - 3} {yy:.1f} h3"/><text class="eo-num" x="{xb0 - 5}" y="{yy + 3:.1f}" text-anchor="end">{cms:+d}</text>')
    ticks.append(f'<text class="eo-num" x="{xb0 - 5}" y="{yb + 3:.1f}" text-anchor="end">0</text>')
    for hh in range(0, 11, 2):
        xx = xb0 + (xb1 - xb0) * hh / hmax
        ticks.append(f'<path class="bp-thin" d="M{xx:.1f} {yb + 300 * sc_b:.1f} v3"/><text class="eo-num" x="{xx:.1f}" y="{yb + 300 * sc_b + 12:.1f}" text-anchor="middle">{hh}</text>')
    add(f'<g class="b-pop" style="--d:2.55s">{"".join(ticks)}<text class="eo-num" x="{xb1}" y="{yb + 300 * sc_b + 24:.1f}" text-anchor="end">hours</text><text class="eo-num" x="{xb0 + 4}" y="{yb - 300 * sc_b + 2:.1f}">cm/s</text></g>')
    dots = "".join(f"M{xb0 + (xb1 - xb0) * h / hmax:.1f} {yb - r * sc_b:.1f}h0" for h, r in zip(hours, res[a:b]))
    add(f'<path class="eo-dots b-pop" style="--d:2.6s" d="{dots}"/>')
    # dimension: the typical error of one velocity, at true scale
    ex = 422.0
    half = PAPER["sigma_rv_cms"] * sc_b
    add(f'<g class="b-pop" style="--d:2.62s"><path class="eo-dim" d="M{ex} {yb - half:.1f} V{yb + half:.1f} M{ex - 3} {yb - half:.1f} h6 M{ex - 3} {yb + half:.1f} h6"/></g>')

    # row C: power spectrum of all nights (real data: filled)
    yc0, yc1 = 410.0, 312.0  # baseline, top (ymax_p)
    xc0, xc1 = xs0, xs1
    def yp(pw):
        return yc0 - (yc0 - yc1) * min(pw, ymax_p) / ymax_p
    add(f'<text class="bp-label2 b-pop" style="--d:2.8s" x="28" y="276">all five nights, power spectrum</text>')
    add(f'<text class="bp-tick b-pop" style="--d:2.8s" x="28" y="290">{int(keep.sum()):,} velocities, weighted</text>')
    add(f'<path class="bp-thin b-draw" style="--d:2.8s;--dur:.17s" pathLength="1" d="M{xc0} {yc1} V{yc0} H{xc1}"/>')
    t2 = []
    for fm in range(2, 9):
        xx = xc0 + (xc1 - xc0) * (fm - F0) / (F1 - F0)
        t2.append(f'<path class="bp-thin" d="M{xx:.1f} {yc0} v3"/><text class="eo-num" x="{xx:.1f}" y="{yc0 + 12}" text-anchor="middle">{fm}</text>')
    for pw in (20, 40, 60):
        t2.append(f'<path class="bp-thin" d="M{xc0 - 3} {yp(pw):.1f} h3"/><text class="eo-num" x="{xc0 - 5}" y="{yp(pw) + 3:.1f}" text-anchor="end">{pw}</text>')
    t2.append(f'<text class="eo-num" x="{xc1}" y="{yc0 + 24}" text-anchor="end">frequency, mHz</text>')
    t2.append(f'<text class="eo-num" x="{xc0}" y="{yc1 - 7}">power, (cm/s)²</text>')
    add(f'<g class="b-pop" style="--d:2.9s">{"".join(t2)}</g>')
    area = f"M{xc0} {yc0} " + " ".join(f"L{xc0 + c:.0f} {yp(v_):.1f} L{xc0 + c + 1:.0f} {yp(v_):.1f}" for c, v_ in enumerate(cols_max)) + f" L{xc1} {yc0} Z"
    add(f'<path class="eo-power b-pop" style="--d:2.95s" d="{area}"/>')
    sm = "M" + " L".join(f"{xc0 + c + 0.5:.1f} {yp(3 * v_):.1f}" for c, v_ in enumerate(cols_smooth))
    add(f'<path class="eo-smooth b-draw" style="--d:3.0s;--dur:.53s" pathLength="1" d="{sm}"/>')
    add(f'<path class="eo-noise b-pop" style="--d:3.35s" d="M{xc0} {yp(3 * white_p):.1f} H{xc1}"/>')
    xn = xc0 + (xc1 - xc0) * (PAPER["numax_uHz"] / 1e3 - F0) / (F1 - F0)
    add(f'<g class="b-pop" style="--d:3.45s"><path class="eo-numax" d="M{xn:.1f} {yc1 - 4} V{yc0}"/>'
        f'<text class="bp-label2" x="{xn + 6:.1f}" y="{yc1 + 2}">oscillations</text>'
        f'<text class="bp-tick" x="{xn + 6:.1f}" y="{yc1 + 14}">periods of {PAPER["period_min"]} minutes</text>'
        f'<text class="bp-tick" x="{xn + 6:.1f}" y="{yc1 + 26}">most power near {PAPER["numax_uHz"] / 1e3:.1f} mHz</text></g>')
    add(f'<text class="eo-num b-pop" style="--d:3.35s" x="{xc1}" y="{yp(3 * white_p) - 4:.1f}" text-anchor="end">noise ×3</text>')
    add(f'<text class="eo-num b-pop" style="--d:3.45s" x="{xc0 + 6}" y="{yp(3 * white_p) - 22:.1f}">smoothed ×3</text>')

    desc = (f"Output of the spectrograph. Each 25 s exposure gives an extracted spectrum, whose cross-correlation dip gives one radial velocity. "
            f"One night of {b - a} velocities of GJ 570 A scatters by tens of centimetres per second around zero. "
            f"The power spectrum of all {int(keep.sum()):,} velocities shows excess power from oscillations near {PAPER['numax_uHz'] / 1e3:.2f} mHz, periods of three to four minutes.")
    svg = (f'<svg class="bp-svg eo-svg" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="eo-t eo-d">'
           f'<title id="eo-t">From the detector to velocities and their power spectrum, GJ 570 A, May 2024</title><desc id="eo-d">{desc}</desc>'
           + "".join(S) + "</svg>\n")
    (root / "_includes/figures/espresso-output.svg").write_text(svg)
    print(json.dumps({k: prov[k] for k in ("n_rows", "n_used", "median_cadence_s", "mean_rv_err_cms", "rms_detrended_cms", "white_noise", "smooth_peak_uHz")}))
    top = int(np.argmax(cols_max))
    print("highest column at", round(F0 + (F1 - F0) * (top + 0.5) / ncol, 3), "mHz:", round(max(cols_max), 1))
    print("night shown:", NIGHT_SHOWN, b - a, start.isoformat(timespec="minutes"), end.isoformat(timespec="minutes"), "| svg KB", round(len(svg) / 1024, 1))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(Path(sys.argv[1]), Path(sys.argv[2])))
