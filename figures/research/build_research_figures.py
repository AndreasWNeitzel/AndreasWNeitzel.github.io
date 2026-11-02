"""Draw the schematic of /research/arqueogal/: _includes/figures/arqueogal.svg (wide) and
arqueogal-narrow.svg (phones). The JANUS page has its own figure under figures/janus/.

The Milky Way at an angle with its components as projected density envelopes, one red giant's
orbit as the accent, the real Gaia red giants around the Sun as marks, and below it the project's
stages: the star's oscillations give an age (tasks 2 and 4), its astrometry an orbit (task 3), its
spectrum a chemistry (task 3); Starfold returns its population (task 5); the Galactic model reads
the catalogue and draws the Galaxy (task 6). Fill tells who built what: tinted for the stages built
by the developer of the pipelines, hatched for taking part, outline for the team's. Facts from the
FCT record of 2024.15303.PEX, the kickoff of 16 February 2026 and _data/ledger.yml.

Real: the giants (assets/data/mw), the orbit (Arcturus, see galaxy_model.py), the chemistry plane
and the map in two pictograms (assets/data/starfold). Schematic: the oscillation comb and the
small disc of the last stage. Model: the envelopes, whose parameters and sources are in
galaxy_model.py.

Usage: uv run --python 3.11 --with numpy --with scipy --with contourpy --with astropy --with galpy \
           python figures/research/build_research_figures.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]
import galaxy_model as gm  # noqa: E402
import schematic_kit as k  # noqa: E402
from schematic_kit import draw, dots_path, f, fits, link, node, pop, poly, text, thread  # noqa: E402,F401

OUT = HERE.parents[1] / "_includes/figures"

STAGES = (  # key, kind, title, tag, line
    ("age", "team", "AGE", "TASKS 2, 4", "TESS oscillations, PARAM"),
    ("orbit", "me", "ORBIT", "TASK 3", "Gaia astrometry, galpy"),
    ("chem", "me", "CHEMISTRY", "TASK 3", "APOGEE, JANUS"),
    ("pops", "me", "POPULATION", "TASK 5", "Starfold"),
    ("model", "part", "THE GALAXY", "TASK 6", "TRILEGAL, chemo-kinematic"),
)
LABEL = ("Schematic of the ArqueoGal project. The Milky Way seen at an angle, with its halo, thick disc, "
         "thin disc and bar drawn as density envelopes, real Gaia red giants around the Sun, and the orbit "
         "of one red giant. That star gives an age from TESS oscillations (tasks 2 and 4), an orbit from Gaia "
         "astrometry and a chemistry from APOGEE or JANUS (task 3). Starfold returns its population (task 5) "
         "and the Galactic model reads the result (task 6). The orbit, chemistry and population stages are "
         "tinted, the Galactic model is hatched and the age stage is in outline.")


def scaled(pts, x, y, w, h, xr=None, yr=None, flip=True):
    """Map (a, b) rows into a box, keeping the data ranges given or found."""
    a, b = pts[:, 0], pts[:, 1]
    x0, x1 = xr or (a.min(), a.max())
    y0, y1 = yr or (b.min(), b.max())
    px = x + (a - x0) / (x1 - x0) * w
    py = y + h - (b - y0) / (y1 - y0) * h if flip else y + (b - y0) / (y1 - y0) * h
    return np.column_stack([px, py])


def pictogram(key: str, x: float, y: float, w: float, h: float, t: float, data: dict) -> str:
    if key == "age":
        # the comb of a red giant's modes under its Gaussian envelope (shape only)
        base = y + h
        xs = np.linspace(x, x + w, 17)
        env = np.exp(-(((xs - (x + w / 2)) / (w * 0.24)) ** 2))
        teeth = " ".join(f"M{f(a)} {f(base)} V{f(base - (h - 4) * e * (1 if i % 2 == 0 else 0.62) - 2)}" for i, (a, e) in enumerate(zip(xs, env)))
        curve = [(a, base - (h - 4) * np.exp(-(((a - (x + w / 2)) / (w * 0.24)) ** 2)) - 2) for a in np.linspace(x, x + w, 40)]
        return draw("sx-guide", f"M{f(x)} {f(base)} H{f(x + w)}", t, 0.25) + draw("sx-line", teeth, t + 0.1, 0.4) + draw("sx-guide", poly(curve), t + 0.2, 0.4)
    if key == "orbit":
        # the same star's orbit seen from above, to the same data as the Galaxy above
        X, Y = data["orbit_face"]
        ext = 8.6
        side = min(w, h)
        cx, cy = x + w / 2, y + h / 2
        pts = [(cx + a / ext * side / 2, cy - b / ext * side / 2) for a, b in zip(X[::4], Y[::4])]
        return draw("sx-line-me", poly(pts), t, 0.6) + pop(f'<rect class="sx-node-q" x="{f(cx - 1.5)}" y="{f(cy - 1.5)}" width="3" height="3"/>', t + 0.2)
    if key == "chem":
        p = data["chem"]
        q = scaled(p, x, y, w, h, (-1.0, 0.5), (-0.08, 0.34))
        q = q[(q[:, 0] >= x) & (q[:, 0] <= x + w) & (q[:, 1] >= y) & (q[:, 1] <= y + h)]
        return pop(f'<path class="sx-data" d="{dots_path(q)}"/>', t)
    if key == "pops":
        m, g = data["map"], data["group"]
        xr, yr = (m[:, 0].min(), m[:, 0].max()), (m[:, 1].min(), m[:, 1].max())
        q = scaled(m, x, y, w, h, xr, yr)
        s = "".join(f'<path class="{cls}" d="{dots_path(q[g == v])}"/>' for v, cls in ((-1, "sx-faint"), (1, "sx-ink"), (0, "sx-data")))
        return pop(s, t)
    cx, cy = x + w / 2, y + h / 2
    return "".join(draw("sx-line", f"M{f(cx - r)} {f(cy)} a{f(r)} {f(r * 0.34)} 0 1 0 {f(2 * r)} 0 a{f(r)} {f(r * 0.34)} 0 1 0 {f(-2 * r)} 0", t + 0.05 * i, 0.4)
                   for i, r in enumerate((min(w / 2, h * 1.3), min(w / 2, h * 1.3) * 0.62, min(w / 2, h * 1.3) * 0.28)))


def stage_shell(key, kind, x, y, w, h, t, inner, hatch):
    cls = {"team": "sx-box", "me": "sx-box-me", "part": "sx-box-part"}[kind]
    style = f' fill="url(#{hatch})"' if kind == "part" else ""
    d = f"M{f(x)} {f(y)} h{f(w)} v{f(h)} h{f(-w)} Z"
    title = next(s[2] for s in STAGES if s[0] == key)
    tag = next(s[3] for s in STAGES if s[0] == key)
    line = next(s[4] for s in STAGES if s[0] == key)
    return (f'<g class="sx-stage sx-part ag-s-{key}" tabindex="0" role="group" aria-label="{title.title()}, {tag.lower()}: {line}">'
            f'<rect class="sx-hit" x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}"/>'
            + draw(cls, d, t, 0.4, style) + inner + "</g>")


def galaxy(cx, cy, s, n_giants, env, t):
    """Layers of the Galaxy at centre (cx, cy), s pixels per kpc."""
    def path(ln, keep=2):
        ln = np.vstack([ln[::keep], ln[:1]])
        return poly(np.column_stack([cx + s * ln[:, 0], cy - s * ln[:, 1]]), close=True)

    comps = []
    for name in ("halo", "thick", "thin"):
        for i, level in enumerate(env[name]):
            d = "".join(path(ln) for ln in level)
            comps.append(pop(f'<path class="ag-tone ag-{name}" d="{d}"/>', t + 0.1 * i))
            if i == 0:
                comps.append(draw(f"ag-edge ag-edge-{name}", d, t, 0.8))
    bar = "".join(path(ln, 3) for ln in env["bar"][0])
    comps.append(pop(f'<path class="ag-bar" d="{bar}"/>', t + 0.5))
    hair = "".join(draw("sx-guide", poly(np.column_stack([cx + s * u, cy - s * v]), close=True), t + 0.2 * i, 0.6)
                   for i, (u, v, _) in enumerate(gm.rings().values()))
    u, v, _ = gm.giants(n_giants)
    dots = pop(f'<path class="sx-data ag-giant" d="{dots_path(np.column_stack([cx + s * u, cy - s * v]))}"/>', t + 0.7)
    return comps, hair, dots


def anchor(level, u, upper=True):
    """The envelope's point at horizontal position u, on its upper side."""
    ln = max(level, key=len)
    side = ln[ln[:, 1] > 0] if upper else ln[ln[:, 1] < 0]
    return side[np.argmin(np.abs(side[:, 0] - u))]


def leader(x0, y0, x1, y1, label, t, anchor_side="start", room=120):
    """A hairline from a point on the drawing to its label; the elbow keeps the text level."""
    gap = 6 if anchor_side == "start" else -6
    ex = x0 + abs(y1 - y0) * (1 if x1 > x0 else -1)
    return (draw("sx-guide-strong", f"M{f(x0)} {f(y0)} L{f(ex)} {f(y1)} H{f(x1)}", t, 0.3)
            + pop(text(x1 + gap, y1 + 4, label, "sx-note", anchor_side, room, 11.5), t + 0.1))


def wide(env, orbit, data) -> str:
    k.reset()
    W, H, cx, cy, s = 1120.0, 558.0, 560.0, 196.0, 14.4
    BY, BH, BW = 402.0, 116.0, 204.0
    xs = {"age": 20.0, "orbit": 236.0, "chem": 452.0, "pops": 668.0, "model": 896.0}
    comps, hair, dots = galaxy(cx, cy, s, 2400, env, 0.0)
    P = ['<g class="sx-part ag-comps">' + "".join(comps) + hair + "</g>", '<g class="sx-part ag-giants">' + dots + "</g>"]
    u, v, _ = orbit
    ox, oy = cx + s * u, cy - s * v
    P.append('<g class="sx-part ag-orbit">' + thread(poly(np.column_stack([ox, oy])[::3]), 0.9, "ag-orbit-line")
             + pop(f'<circle class="ag-star" cx="{f(ox[0])}" cy="{f(oy[0])}" r="4"/>', 0.9) + "</g>")

    # labels on the margins
    def at(name, uu, up=True):
        a = anchor(env[name][0], uu, up)
        return cx + s * a[0], cy - s * a[1]

    L = []
    L.append(leader(*at("halo", 9.5), 870, 40, "halo", 1.2))
    L.append(leader(*at("thick", 7.0), 870, 74, "thick disc", 1.25))
    L.append(leader(*at("thin", 13.0), 870, 142, "thin disc", 1.3))
    b = max(env["bar"][0], key=len)
    e = b[np.argmax(b[:, 0])]
    L.append(leader(cx + s * e[0], cy - s * e[1], 870, 108, "bar", 1.35))
    L.append(leader(ox[0], oy[0] - 4, 250, oy[0] - 40, "one red giant", 1.4, "end"))
    gu, gv, _ = gm.giants(2400)
    L.append(leader(cx + s * np.median(gu) - 40, cy - s * np.median(gv) + 22, 250, cy - s * np.median(gv) + 62, "Gaia red giants", 1.45, "end"))
    P.append('<g class="sx-part ag-labels">' + "".join(L) + "</g>")

    # stages
    T = 1.4
    for i, (key, kind, title, tag, line) in enumerate(STAGES):
        x = xs[key]
        inner = pictogram(key, x + 14, BY + 12, BW - 28, 52, T + 0.15 * i + 0.1, data)
        inner += pop(text(x + 12, BY + 84, fits(title, 12.5, 120), "sx-title") + text(x + BW - 12, BY + 84, fits(tag, 11.5, 76), "sx-note", "end")
                     + text(x + 12, BY + 102, fits(line, 11.5, BW - 24), "sx-note"), T + 0.15 * i + 0.2)
        P.append(stage_shell(key, kind, x, BY, BW, BH, T + 0.15 * i, inner, "ag-hatch-w"))

    # the thread: the star fans out to its three measurements, they meet on the rail under the
    # stages, Starfold passes to the model and the model returns to the Galaxy
    th = []
    for key in ("age", "orbit", "chem"):
        c = xs[key] + BW / 2
        th.append(thread(f"M{f(ox[0])} {f(oy[0])} C{f(ox[0])} 350 {f(c)} 330 {f(c)} {f(BY)}", 1.0) + node(c, BY, 1.1))
    R = BY + BH + 20
    sx = xs["pops"] + BW / 2
    a0, a1, a2 = (xs[n] + BW / 2 for n in ("age", "orbit", "chem"))
    th.append(thread(f"M{f(a0)} {f(BY + BH)} V{f(R - 8)} Q{f(a0)} {f(R)} {f(a0 + 8)} {f(R)} H{f(sx - 8)} Q{f(sx)} {f(R)} {f(sx)} {f(R - 8)} V{f(BY + BH)}", 2.0))
    th.append(thread(f"M{f(a1)} {f(BY + BH)} V{f(R)} M{f(a2)} {f(BY + BH)} V{f(R)}", 2.0))
    for c in (a0, a1, a2, sx):
        th.append(node(c, BY + BH, 2.05))
    th.append(link(xs["pops"] + BW, BY + 58, xs["model"], BY + 58, 2.2))
    mx = xs["model"] + BW / 2
    tipx, tipy = cx + s * gm.REACH["thin"][0], cy
    th.append(thread(f"M{f(mx)} {f(BY)} C{f(mx)} 300 {f(tipx + 110)} {f(tipy)} {f(tipx)} {f(tipy)}", 2.4) + node(mx, BY, 2.4) + node(tipx, tipy, 2.5))
    P.insert(3, '<g class="sx-part ag-thread">' + "".join(th) + "</g>")

    defs = hatch("ag-hatch-w")
    print(f"arqueogal.svg: {len(k.WORDS)} words")
    return k.svg("ag-fig sx-wide", W, H, LABEL, P, defs, "group")


def hatch(pid: str) -> str:
    return (f'<pattern id="{pid}" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)">'
            '<path class="sx-hatch-line" d="M0 0 V6"/></pattern>')


def narrow(env, orbit, data) -> str:
    k.reset()
    W, cx, cy, s = 380.0, 190.0, 134.0, 9.6
    BX, BW, BH, GAP = 18.0, 354.0, 76.0, 10.0
    comps, hair, dots = galaxy(cx, cy, s, 1300, env, 0.0)
    P = ['<g class="sx-part ag-comps">' + "".join(comps) + hair + "</g>", '<g class="sx-part ag-giants">' + dots + "</g>"]
    u, v, _ = orbit
    ox, oy = cx + s * u, cy - s * v
    P.append('<g class="sx-part ag-orbit">' + thread(poly(np.column_stack([ox, oy])[::3]), 0.9, "ag-orbit-line")
             + pop(f'<circle class="ag-star" cx="{f(ox[0])}" cy="{f(oy[0])}" r="3.5"/>', 0.9) + "</g>")

    # a key in place of the margin labels
    ky = 274.0
    key = (("ag-k-halo", "halo", 18), ("ag-k-thick", "thick disc", 86), ("ag-k-thin", "thin disc", 196), ("ag-k-bar", "bar", 300),
           ("ag-k-star", "one red giant", 18), ("ag-k-giant", "Gaia red giants", 196))
    K = []
    for i, (cls, lab, x) in enumerate(key):
        y = ky + (20 if i > 3 else 0)
        K.append(f'<rect class="{cls}" x="{f(x)}" y="{f(y - 8)}" width="10" height="10"/>')
        K.append(text(x + 16, y + 1, lab, "sx-note", "start", W - x - 16, 12))
    P.append('<g class="sx-part ag-labels">' + pop("".join(K), 1.2) + "</g>")

    y0 = ky + 40
    for i, (key_, kind, title, tag, line) in enumerate(STAGES):
        y = y0 + i * (BH + GAP)
        inner = pictogram(key_, BX + 12, y + 12, 76, BH - 24, 1.4 + 0.1 * i, data)
        inner += pop(text(BX + 104, y + 30, fits(title, 13, 130), "sx-title") + text(BX + BW - 10, y + 30, fits(tag, 12, 90), "sx-note", "end")
                     + text(BX + 104, y + 52, fits(line, 12, BW - 114), "sx-note"), 1.5 + 0.1 * i)
        P.append(stage_shell(key_, kind, BX, y, BW, BH, 1.3 + 0.1 * i, inner, "ag-hatch-n"))
    yl = y0 + 4 * (BH + GAP) + BH / 2
    th = [thread(f"M{f(ox[0])} {f(oy[0])} C{f(ox[0])} {f(ky - 50)} 8 {f(ky - 80)} 8 {f(ky - 24)} V{f(yl)}", 1.0)]
    for i in range(5):
        y = y0 + i * (BH + GAP) + BH / 2
        th.append(thread(f"M8 {f(y)} H{f(BX)}", 1.2) + node(BX, y, 1.25))
    P.insert(3, '<g class="sx-part ag-thread">' + "".join(th) + "</g>")
    H = yl + BH / 2 + 8
    print(f"arqueogal-narrow.svg: {len(k.WORDS)} words")
    return k.svg("ag-fig sx-narrow", W, H, LABEL, P, hatch("ag-hatch-n"), "group")


def main() -> None:
    env = gm.envelopes()
    X, Y, Z = gm.arcturus_orbit()
    orbit = gm.to_view(X, Y, Z)
    run = k.starfold_run()
    rng = np.random.default_rng(20261102)
    idx = rng.choice(len(run["group"]), size=500, replace=False)
    data = {
        "orbit_face": (X, Y),
        "chem": np.asarray(run["features"], float)[idx][:, :2],
        "map": np.asarray(run["map"], float)[idx],
        "group": np.asarray(run["group"])[idx],
    }
    for name, out in (("arqueogal.svg", wide(env, orbit, data)), ("arqueogal-narrow.svg", narrow(env, orbit, data))):
        (OUT / name).write_text(out)
        print(f"wrote {OUT / name} ({len(out) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
