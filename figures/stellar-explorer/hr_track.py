"""Draw the real MESA track behind Stellar Explorer as a theme-aware SVG HR diagram.

Usage: uv run --with h5py --with numpy python figures/stellar-explorer/hr_track.py \
    <stellar_data_real.h5> _includes/figures/art-hr.svg

Input: the public file of github.com/AndreasWNeitzel/stellar-explorer-data (MESA r24.08.1 with
GYRE, one solar mass, solar metallicity). The curve is every row of the run's history; the points
are the models that carry a stored interior profile.

Construction lines are lines of constant radius from L = 4 pi R^2 sigma Teff^4, so they are exact.
Colours are CSS custom properties. The page plays a one-time draw-on when the figure first enters
the view; the file itself is the finished figure, which is what no-JS, print and reduced motion show.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from texsvg import tex_glyphs  # noqa: E402  (LaTeX glyphs for the solar symbols)

W, H = 520, 330
L_, R_, T_, B_ = 50, 16, 14, 40
TX0, TX1 = 4.98, 3.42  # log Teff, hot on the left
LY0, LY1 = -1.35, 3.75  # log L
LOG_TSUN = math.log10(5772.0)  # IAU 2015 nominal solar effective temperature

PHASE = {  # name in the file -> (label, colour token)
    "PMS": ("pre-main sequence", "--cat-3"),
    "ZAMS": ("zero-age main sequence", "--cat-0"),
    "MS": ("main sequence", "--cat-0"),
    "SGB": ("subgiant branch", "--cat-9"),
    "RGB": ("red-giant branch", "--cat-2"),
    "HeFlash": ("helium flash", "--cat-6"),
    "HeCB": ("core helium burning", "--cat-6"),
    "RC": ("red clump", "--cat-1"),
    "AGB": ("asymptotic giant branch", "--cat-4"),
    "postAGB": ("post-AGB", "--cat-7"),
    "WD": ("white-dwarf cooling", "--cat-8"),
}

DRAW_START = 0.55  # s, after the construction lines
DRAW_DUR = 1.6  # s, the pen along the whole track


def px(logt):
    return L_ + (TX0 - logt) / (TX0 - TX1) * (W - L_ - R_)


def py(logl):
    return T_ + (LY1 - logl) / (LY1 - LY0) * (H - T_ - B_)


def out_expo_inverse(f):
    """Time fraction at which an outExpo ease (1 - 2^-10t) reaches progress f."""
    if f >= 0.999:
        return 1.0
    return min(1.0, -math.log2(1.0 - f) / 10.0)


def clip_line(x0, y0, x1, y1):
    """Liang-Barsky clip of a segment to the plot box."""
    xmin, xmax, ymin, ymax = L_, W - R_, T_, H - B_
    dx, dy = x1 - x0, y1 - y0
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x0 - xmin), (dx, xmax - x0), (-dy, y0 - ymin), (dy, ymax - y0)):
        if p == 0:
            if q < 0:
                return None
            continue
        r = q / p
        if p < 0:
            t0 = max(t0, r)
        else:
            t1 = min(t1, r)
        if t0 > t1:
            return None
    return x0 + t0 * dx, y0 + t0 * dy, x0 + t1 * dx, y0 + t1 * dy



def run(parts, cls, size, anchor="start"):
    """Set a label made of mono text and LaTeX glyphs from its left end; returns (svg, width)."""
    adv = 0.6 * size  # Geist Mono advance
    cur, out = 0.0, []
    for kind, seg in parts:
        if kind == "text":
            out.append(f'<text class="{cls}" x="{cur:.1f}" y="0" style="white-space:pre">{seg}</text>')
            cur += len(seg) * adv
        else:
            body, w = tex_glyphs(seg, size * 1.1)
            out.append(f'<g class="{cls}-tex" transform="translate({cur + 0.5:.1f} 0)">{body}</g>')
            cur += w + 1.5
    shift = {"start": 0.0, "middle": -cur / 2, "end": -cur}[anchor]
    return f'<g transform="translate({shift:.1f} 0)">{"".join(out)}</g>', cur

def main(h5: Path, out: Path) -> int:
    with h5py.File(h5, "r") as f:
        t = f["track"]
        m_phase = [p.decode().strip() for p in t["phase"][:]]
        m_model = t["model_number_orig"][:].astype(int)
        h = f["history"]
        logt = h["log_Teff"][:].astype(float)
        logl = h["log_L"][:].astype(float)
        logr = h["log_R"][:].astype(float)
        age = h["star_age"][:].astype(float)  # Gyr
        phase = [p.decode().strip() for p in h["phase"][:]]
        model = h["model_number"][:].astype(int)
    unknown = sorted(set(phase) | set(m_phase)) and sorted((set(phase) | set(m_phase)) - set(PHASE))
    if unknown:
        raise SystemExit(f"unmapped phases: {unknown}")
    # Every row of the run is the curve; the models that carry a stored
    # interior are the points on it.
    row_of = {int(mn): i for i, mn in enumerate(model)}
    mrow = [row_of[int(mn)] for mn in m_model]

    x, y = px(logt), py(logl)
    seg = np.hypot(np.diff(x), np.diff(y))
    cum = np.concatenate([[0.0], np.cumsum(seg)]) / seg.sum()
    when = [DRAW_START + DRAW_DUR * out_expo_inverse(c) for c in cum]

    p = []
    # construction: lines of constant radius, drawn first and kept faint
    for k, r in enumerate((0.01, 0.1, 1, 10, 100)):
        labelled = r < 100  # the 100 R line meets the red-giant tip, where its label would collide
        a = 2 * math.log10(r)
        c = clip_line(px(TX0), py(a + 4 * (TX0 - LOG_TSUN)), px(TX1), py(a + 4 * (TX1 - LOG_TSUN)))
        if not c:
            continue
        x0, y0, x1, y1 = c
        p.append(f'<path class="hr-guide b-draw" style="--d:{0.06 * k:.2f}s;--dur:.17s" pathLength="1" d="M{x0:.1f} {y0:.1f} L{x1:.1f} {y1:.1f}"/>')
        lab = f"{r:g}" if labelled else ""
        # label at the upper (left) end, nudged inside the box
        lx, ly = (x0, y0) if y0 < y1 else (x1, y1)
        ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
        if lab:
            g, _ = run([("text", lab + " "), ("tex", r"R_\odot")], "hr-dim", 9.5)
            p.append(f'<g class="b-pop" style="--d:{0.06 * k + 0.17:.2f}s" transform="translate({lx + 4:.1f} {ly + 10:.1f}) rotate({ang:.1f})">{g}</g>')
    # axes: object weight
    p.append(f'<path class="hr-axis b-draw" style="--d:0s;--dur:.17s" pathLength="1" d="M{L_} {T_} V{H - B_} H{W - R_}"/>')
    for teff in (50000, 20000, 10000, 5000, 3000):
        xx = px(math.log10(teff))
        p.append(f'<path class="hr-tick" d="M{xx:.1f} {H - B_} v4"/><text class="hr-num" x="{xx:.1f}" y="{H - B_ + 15}" text-anchor="middle">{teff:,}</text>'.replace(",", " "))
    for lg in (-1, 0, 1, 2, 3):
        yy = py(lg)
        lab = {-1: "0.1", 0: "1", 1: "10", 2: "100", 3: "1000"}[lg]
        p.append(f'<path class="hr-tick" d="M{L_ - 4} {yy:.1f} h4"/><text class="hr-num" x="{L_ - 7}" y="{yy + 3.5:.1f}" text-anchor="end">{lab}</text>')
    p.append(f'<text class="hr-lab" x="{W - R_}" y="{H - 6}" text-anchor="end">surface temperature (K), hotter to the left</text>')
    g, _ = run([("text", "luminosity ("), ("tex", r"L_\odot"), ("text", ")")], "hr-lab", 9.5, "end")
    p.append(f'<g transform="translate(13 {T_}) rotate(-90)">{g}</g>')
    # the pen: one ink path along the track, thinned to the points the curve needs
    keep = [0]
    for i in range(1, len(x) - 1):
        if math.hypot(x[i] - x[keep[-1]], y[i] - y[keep[-1]]) > 0.9:
            keep.append(i)
    keep.append(len(x) - 1)
    d = "M" + " L".join(f"{x[i]:.1f} {y[i]:.1f}" for i in keep)
    p.append(f'<path class="hr-track b-draw" style="--d:{DRAW_START}s;--dur:{DRAW_DUR}s" pathLength="1" d="{d}"/>')
    # real data: every model with a stored interior, appearing as the pen passes it
    for k, i in enumerate(mrow):
        var = PHASE[m_phase[k]][1]
        p.append(f'<circle class="hr-pt b-pop" style="--d:{when[i]:.2f}s;fill:var({var})" cx="{x[i]:.1f}" cy="{y[i]:.1f}" r="2.1"><title>model {m_model[k]}, {age[i]:.3g} Gyr</title></circle>')
    # square nodes where each phase begins, in the order the star meets them
    seen = set()
    for i, ph in enumerate(phase):
        if ph in seen:
            continue
        seen.add(ph)
        if i == 0:
            continue
        p.append(f'<rect class="hr-node b-pop" style="--d:{when[i]:.2f}s" x="{x[i] - 2.5:.1f}" y="{y[i] - 2.5:.1f}" width="5" height="5"><title>{PHASE[ph][0]} begins</title></rect>')
    # the model at the Sun's age
    k_sun = int(np.argmin(np.abs(np.where(np.array(phase) == "MS", age, 1e9) - 4.57)))
    p.append(f'<circle class="hr-sun b-pop" style="--d:{when[k_sun] + 0.05:.2f}s" cx="{x[k_sun]:.1f}" cy="{y[k_sun]:.1f}" r="6"/>')

    def rows(name):
        return [i for i in range(len(phase)) if phase[i] == name]

    def first(name):
        return rows(name)[0]

    def last(name):
        return rows(name)[-1]

    def nearest(name, target_logl):
        return min(rows(name), key=lambda i: abs(logl[i] - target_logl))

    sun_label = f"{age[k_sun]:.1f} Gyr, {10 ** logr[k_sun]:.2f} R_sun: the Sun today"
    sun_parts = [("text", f"{age[k_sun]:.1f} Gyr, {10 ** logr[k_sun]:.2f} "), ("tex", r"R_\odot"), ("text", ": the Sun today")]

    # labels: (x, y, anchor, text, appear-at history row), placed by hand against the data
    def at(k, dx, dy):
        return x[k] + dx, y[k] + dy

    rgb_mid = nearest("RGB", 1.0)
    pms_low = min(rows("PMS"), key=lambda i: logl[i])
    agb_mid = nearest("AGB", 2.45)
    rc_rows = rows("RC")
    rc_mid = rc_rows[len(rc_rows) // 2]
    labels = [
        (*at(k_sun, -10, 4), "end", sun_parts, k_sun),
        (*at(pms_low, -8, 16), "end", "pre-main sequence", first("PMS")),
        (*at(rgb_mid, -9, 4), "end", "red-giant branch", rgb_mid),
        (*at(first("HeFlash"), -4, -9), "end", "helium flash", first("HeFlash")),
        (*at(rc_mid, -9, 4), "end", "red clump", rc_mid),
        (*at(agb_mid, -9, 4), "end", "asymptotic giant branch", agb_mid),
        (px(4.27), py(2.97) - 8, "middle", "post-AGB", first("postAGB")),
        (*at(last("WD"), 8, 4), "start", "white dwarf", last("WD")),
    ]
    for lx, ly, anchor, txt, k in labels:
        if isinstance(txt, list):
            g, _ = run(txt, "hr-note", 10, anchor)
            p.append(f'<g class="b-pop" style="--d:{when[k] + 0.1:.2f}s" transform="translate({lx:.1f} {ly:.1f})">{g}</g>')
            continue
        p.append(f'<text class="hr-note b-pop" style="--d:{when[k] + 0.1:.2f}s" x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}">{txt}</text>')

    svg = (
        f'<svg class="hr-svg" data-build viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-label="Hertzsprung-Russell diagram of the MESA track that Stellar Explorer shows: a one-solar-mass, '
        'solar-metallicity star from the pre-main sequence through the main sequence, the red-giant branch, the '
        'helium flash, the red clump and the asymptotic giant branch to the white-dwarf cooling track. Faint '
        'diagonal lines mark constant radius.">' + "".join(p) + "</svg>\n"
    )
    out.write_text(svg)
    print(f"wrote {out} ({len(svg) / 1024:.1f} KB, {len(phase)} history rows, {len(mrow)} models with a profile; "
          f"Sun-age row {k_sun}: {sun_label})")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(Path(sys.argv[1]), Path(sys.argv[2])))
