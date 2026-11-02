"""Draw how Starfold works for /software/starfold-demo/: _includes/figures/starfold-how.svg (wide)
and starfold-how-narrow.svg (phones).

Four stages, after the package's README (github.com/AndreasWNeitzel/starfold): a table of
measurements; UMAP draws it as a map that keeps close rows close; HDBSCAN cuts the dense clumps and
leaves sparse rows unassigned; refits on random subsets show how far the groups can be trusted. The
loop from the groups back to the map is the search over settings, scored without labels.

All marks are real, from the recorded run in assets/data/starfold: the cells are the eight
measured columns of randomly drawn rows, as each value's rank within its column; the dots are a
random subsample of the stars at their map positions, in their recorded groups, faded by their
recorded support. Only the frames, the stack of cards and the arrows are schematic.

Usage: uv run --python 3.11 --with numpy python figures/starfold/build_starfold_schematic.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import schematic_kit as k  # noqa: E402
from schematic_kit import dots_path, draw, f, fits, link, pop, text, thread  # noqa: E402

OUT = HERE.parents[1] / "_includes/figures"
SEED = 20261102
N_DOTS, N_ROWS = 900, 11

STAGES = (
    ("THE TABLE", "one row per star"),
    ("THE MAP", "UMAP keeps neighbours close"),
    ("THE GROUPS", "HDBSCAN cuts the dense clumps"),
    ("WHAT COMES BACK", "refits on random subsets"),
)
LOOP = "settings scored without labels"
LABEL = ("How Starfold works. A table of measurements, one row per star, is drawn as a map by UMAP. HDBSCAN "
         "cuts the dense clumps of the map into groups and leaves sparse stars unassigned; settings for both are "
         "searched and scored without labels. Refits on random subsets show which stars and groups come back: "
         "stars fade where the refits disagree. The marks are from a recorded run on APOGEE stars.")


def load() -> dict:
    run = k.starfold_run()
    rng = np.random.default_rng(SEED)
    feats = np.asarray(run["features"], float)
    n = len(feats)
    rank = feats.argsort(axis=0).argsort(axis=0) / (n - 1)
    idx = rng.choice(n, size=N_DOTS, replace=False)
    group = np.asarray(run["group"]).astype(int)
    support = np.asarray(run["support"], float)
    keep = np.where(group >= 0, support[np.arange(n), np.clip(group, 0, None)], 0.0)
    return {"cells": rank[rng.choice(n, size=N_ROWS, replace=False)], "map": np.asarray(run["map"], float)[idx],
            "group": group[idx], "keep": keep[idx]}


def to_box(m, x, y, w, h):
    lo, hi = m.min(axis=0), m.max(axis=0)
    pad = 6
    return np.column_stack([x + pad + (m[:, 0] - lo[0]) / (hi[0] - lo[0]) * (w - 2 * pad),
                            y + h - pad - (m[:, 1] - lo[1]) / (hi[1] - lo[1]) * (h - 2 * pad)])


def frame(x, y, w, h, t):
    return draw("sx-line sf-frame", f"M{f(x)} {f(y)} h{f(w)} v{f(h)} h{f(-w)} Z", t, 0.35)


def panel(i, x, y, w, h, D, t):
    if i == 0:
        cw, ch = w / D["cells"].shape[1], h / D["cells"].shape[0]
        cells = "".join(f'<rect class="sf-cell" x="{f(x + c * cw + 1)}" y="{f(y + r * ch + 1)}" width="{f(cw - 2)}" height="{f(ch - 2)}" opacity="{0.1 + 0.8 * v:.2f}"/>'
                        for (r, c), v in np.ndenumerate(D["cells"]))
        return pop(cells, t)
    q = to_box(D["map"], x, y, w, h)
    g = D["group"]
    if i == 1:
        return frame(x, y, w, h, t) + pop(f'<path class="sx-ink sf-dot" d="{dots_path(q)}"/>', t + 0.1)
    if i == 2:
        s = "".join(f'<path class="{c} sf-dot" d="{dots_path(q[g == v])}"/>' for v, c in ((-1, "sx-faint"), (1, "sx-ink"), (0, "sx-data")))
        return frame(x, y, w, h, t) + pop(s, t + 0.1)
    bins = ((0.85, 1.01, "sf-k3"), (0.6, 0.85, "sf-k2"), (0.0, 0.6, "sf-k1"))
    s = "".join(f'<path class="sf-dot {c} {b}" d="{dots_path(q[(g == v) & (D["keep"] >= lo) & (D["keep"] < hi)])}"/>'
                for lo, hi, b in bins for v, c in ((1, "sx-ink"), (0, "sx-data")))
    cards = "".join(draw("sx-line sf-frame", f"M{f(x + o)} {f(y - o)} h{f(w)} v{f(h)}", t + 0.05 * o, 0.3) for o in (10, 5))
    return cards + frame(x, y, w, h, t) + pop(s, t + 0.2)


def wide(D) -> str:
    k.reset()
    W, H, Y, PW, PH = 1120.0, 296.0, 66.0, 200.0, 150.0
    xs = (30.0, 310.0, 590.0, 870.0)
    P = []
    for i, (title, line) in enumerate(STAGES):
        t = 0.1 + 0.3 * i
        P.append(panel(i, xs[i], Y, PW, PH, D, t))
        P.append(pop(text(xs[i], Y + PH + 28, fits(title, 12.5, PW), "sx-title") + text(xs[i], Y + PH + 46, fits(line, 11.5, PW + 1), "sx-note"), t + 0.1))
        if i:
            P.append(link(xs[i - 1] + PW, Y + PH / 2, xs[i], Y + PH / 2, t))
    a, b = xs[2] + PW / 2, xs[1] + PW / 2
    P.append(thread(f"M{f(a)} {f(Y)} C{f(a)} 18 {f(b)} 18 {f(b)} {f(Y)}", 1.1) + k.node(a, Y, 1.1) + k.node(b, Y, 1.15))
    P.append(pop(text((a + b) / 2, 22, fits(LOOP, 11.5, 260), "sx-note sf-onbg", "middle"), 1.2))
    print(f"starfold-how.svg: {len(k.WORDS)} words")
    return k.svg("sf-fig sx-wide", W, H, LABEL, P)


def narrow(D) -> str:
    k.reset()
    W, PW, PH, X, GAP = 380.0, 122.0, 98.0, 24.0, 34.0
    P = []
    ys = [14 + i * (PH + GAP) for i in range(4)]
    tx = X + PW + 18
    for i, (title, line) in enumerate(STAGES):
        y = ys[i]
        t = 0.1 + 0.3 * i
        P.append(panel(i, X, y, PW, PH, D, t))
        P.append(pop(text(tx, y + 38, fits(title, 13, W - tx), "sx-title") + text(tx, y + 58, fits(line, 12, W - tx), "sx-note"), t + 0.1))
        if i:
            P.append(link(X + PW / 2, ys[i - 1] + PH, X + PW / 2, y, t))
    y0, y1 = ys[2] + PH / 2, ys[1] + PH / 2
    R = X + PW
    P.append(thread(f"M{f(R)} {f(y0)} C{f(R + 18)} {f(y0)} {f(R + 18)} {f(y1)} {f(R)} {f(y1)}", 1.1) + k.node(R, y0, 1.1) + k.node(R, y1, 1.15))
    P.append(pop(text(tx, ys[1] + PH + 21, fits(LOOP, 12, 220), "sx-note"), 1.2))
    print(f"starfold-how-narrow.svg: {len(k.WORDS)} words")
    return k.svg("sf-fig sx-narrow", W, ys[3] + PH + 14, LABEL, P)


def main() -> None:
    D = load()
    for name, out in (("starfold-how.svg", wide(D)), ("starfold-how-narrow.svg", narrow(D))):
        (OUT / name).write_text(out)
        print(f"wrote {OUT / name} ({len(out) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
