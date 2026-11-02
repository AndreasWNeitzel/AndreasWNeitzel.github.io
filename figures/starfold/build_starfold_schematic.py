"""Draw how Starfold works for /software/starfold-demo/: _includes/figures/starfold-how.svg (wide)
and starfold-how-narrow.svg (phones).

More than a UMAP map cut by HDBSCAN, after the package's README and concept pages
(github.com/AndreasWNeitzel/starfold): the settings of both are searched without labels, each
scored against the same setting on a structureless copy of the table; the chosen setting is fitted
on all rows; refits on random subsets, each with a new seed, measure what holds. That is read
without matching groups, from how often pairs of rows stay together, and per group as recurrence
with its range; what the evidence does not support comes back as flags.

All marks are real, from the recorded run in assets/data/starfold. The table: the eight columns of
randomly drawn rows, as each value's rank in its column. The search: every completed trial,
sorted by gap, joining its score on the table (filled) to its score on the copy (open).
The groups: a random subsample of the stars at their map positions, in their recorded groups. The
dashed circle holds sqrt(12 n) of the stars around the middle of a group: the package's rule of
thumb for the size below which groups tend to merge, measured, not derived. The refits: the first
refits, the stars they drew at their map positions, each refit's groups matched to the fit on all
stars by largest Jaccard index. The matrix: for 16, 26 and 6 random stars of the two groups and the
unassigned, the share of refits that put each pair in one group among those that drew and assigned
both (the unequal shares are chosen so that the small group shows). The rings: the recorded
recurrence of each group, with ticks at its 5 and 95 percent range.
Only the frames and the thread are schematic.

Usage: uv run --python 3.11 --with numpy python figures/starfold/build_starfold_schematic.py
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import schematic_kit as k  # noqa: E402
from schematic_kit import dots_path, draw, f, fits, link, pop, text  # noqa: E402

OUT = HERE.parents[1] / "_includes/figures"
SEED = 20261102
N_DOTS, N_ROWS = 900, 12

STAGES = (
    ("THE TABLE", "no labels"),
    ("THE SEARCH", "score against a structureless copy"),
    ("THE GROUPS", "UMAP map, HDBSCAN cut"),
    ("THE REFITS", "random subsets, new seeds"),
    ("WHAT HOLDS", "pairs, recurrence, flags"),
)
LABEL = ("How Starfold works. A table of measurements with no labels enters a search over the settings of UMAP and "
         "HDBSCAN, where each setting is scored against the same setting on a structureless copy of the table, and "
         "the setting with the largest gap is chosen. It gives a map and its groups, with a limit below which groups "
         "tend to merge. Refits on random subsets with new seeds then show what holds: how often pairs of stars stay "
         "together, how far each group recurs, and flags for what the evidence does not support. The marks are from "
         "a recorded run on APOGEE stars.")
BLUE, INK = "sx-data", "sx-ink"


def load() -> dict:
    run = k.starfold_run()
    rng = np.random.default_rng(SEED)
    feats = np.asarray(run["features"], float)
    n = len(feats)
    rank = feats.argsort(axis=0).argsort(axis=0) / (n - 1)
    group = np.asarray(run["group"]).astype(int)
    m = np.asarray(run["map"], float)
    span = m.max(axis=0) - m.min(axis=0)
    scaled = (m - m.min(axis=0)) / span
    packed = np.asarray(run["refit_labels"])  # two 4-bit values per byte, low nibble first
    refits = np.zeros((packed.shape[0], n), dtype=int)
    refits[:, 0::2] = packed[:, : (n + 1) // 2] & 15
    refits[:, 1::2] = packed[:, : n // 2] >> 4
    refits -= 2  # -2 not drawn in this refit, -1 unassigned
    idx = rng.choice(n, size=N_DOTS, replace=False)

    # each refit's groups take the colour of the group of the fit on all stars they overlap most
    aligned = np.full_like(refits, -1)
    for r in range(refits.shape[0]):
        for lab in np.unique(refits[r][refits[r] >= 0]):
            mem = refits[r] == lab
            jac = [(mem & (group == g)).sum() / (mem | (group == g)).sum() for g in (0, 1)]
            aligned[r][mem] = int(np.argmax(jac))
    aligned[refits == -2] = -2

    # the co-association matrix
    pick = [rng.choice(np.flatnonzero(group == g), size=c, replace=False) for g, c in ((0, 16), (1, 26), (-1, 6))]
    rows = np.concatenate(pick)
    lab = refits[:, rows]
    both = (lab[:, :, None] >= 0) & (lab[:, None, :] >= 0)
    same = both & (lab[:, :, None] == lab[:, None, :])
    with np.errstate(invalid="ignore", divide="ignore"):
        share = same.sum(axis=0) / both.sum(axis=0)

    # the disc of the resolution limit, around the middle of the smaller group
    limit = int(round(math.sqrt(12 * n)))
    mem = scaled[group == 0]
    mid = np.median(mem, axis=0)
    radius = float(np.sort(np.hypot(*(scaled - mid).T))[limit])

    meta = json.loads((k.ROOT / "assets/data/starfold/apogee_run.json").read_text())
    tr = json.loads((k.ROOT / "assets/data/starfold/apogee_trials.json").read_text())
    done = sorted((t for t in tr["trials"] if t["state"] == "complete"), key=lambda t: t["gap"])
    return {"cells": rank[rng.choice(n, size=N_ROWS, replace=False)], "map": scaled[idx], "group": group[idx],
            "aligned": aligned[:, idx], "share": share, "limit": (mid, radius),
            "trials": [(t["score"], t["copy_score"], t["number"] == tr["selected_trial"]) for t in done],
            "rings": [(g["recurrence"], *g["recurrence_band"]) for g in meta["groups"]]}


def to_box(m, x, y, w, h, pad=6.0):
    return np.column_stack([x + pad + m[:, 0] * (w - 2 * pad), y + h - pad - m[:, 1] * (h - 2 * pad)])


def frame(x, y, w, h, t):
    return draw("sx-line sf-frame", f"M{f(x)} {f(y)} h{f(w)} v{f(h)} h{f(-w)} Z", t, 0.35)


def table(x, y, w, h, D, t):
    cw, ch = w / D["cells"].shape[1], h / D["cells"].shape[0]
    return pop("".join(f'<rect class="sf-cell" x="{f(x + c * cw + 0.5)}" y="{f(y + r * ch + 0.5)}" width="{f(cw - 1)}" height="{f(ch - 1)}" opacity="{0.1 + 0.8 * v:.2f}"/>'
                       for (r, c), v in np.ndenumerate(D["cells"])), t)


def search(x, y, w, h, D, t):
    T = D["trials"]
    top = 0.82
    px = lambda i: x + 6 + i * (w - 12) / (len(T) - 1)  # noqa: E731
    py = lambda v: y + h - 4 - v / top * (h - 8)  # noqa: E731
    stems = "".join(f"M{f(px(i))} {f(py(a))} V{f(py(b))}" for i, (a, b, _) in enumerate(T))
    on = dots_path([(px(i), py(a)) for i, (a, _, _) in enumerate(T)])
    off = "".join(f'<circle class="sf-copy" cx="{f(px(i))}" cy="{f(py(b))}" r="1.7"/>' for i, (_, b, _) in enumerate(T))
    s = next(i for i, c in enumerate(T) if c[2])
    a, b, _ = T[s]
    mark = (f'<path class="sf-chosen" d="M{f(px(s))} {f(py(a))} V{f(py(b))}"/><circle class="sf-ring" cx="{f(px(s))}" cy="{f(py(a))}" r="5.5"/>')
    return (draw("sx-guide", f"M{f(x)} {f(y + h - 4)} H{f(x + w)}", t, 0.3) + pop(f'<path class="sf-stem" d="{stems}"/>', t + 0.1)
            + pop(f'<path class="sx-data sf-on" d="{on}"/>' + off, t + 0.2)
            + pop(mark + text(px(s) + 6, py(a) - 11, "chosen", "sx-note", "end"), t + 0.5))


def groups(x, y, w, h, D, t):
    q = to_box(D["map"], x, y, w, h)
    g = D["group"]
    s = "".join(f'<path class="{c} sf-dot" d="{dots_path(q[g == v])}"/>' for v, c in ((-1, "sx-faint"), (1, INK), (0, BLUE)))
    mid, r = D["limit"]
    c = to_box(mid[None, :], x, y, w, h)[0]
    rx, ry = r * (w - 12), r * (h - 12)
    lim = f'<ellipse class="sf-limit" cx="{f(c[0])}" cy="{f(c[1])}" rx="{f(rx)}" ry="{f(ry)}"/>'
    lab = text(x + w - 5, y + h - 20, "resolution", "sx-note sf-small", "end") + text(x + w - 5, y + h - 7, "limit", "sx-note sf-small", "end")
    lead = f'<path class="sx-guide-strong" d="M{f(c[0])} {f(c[1] + ry)} V{f(y + h - 32)}"/>'
    return frame(x, y, w, h, t) + pop(s, t + 0.1) + pop(lim + lead + lab, t + 0.4)


def refits(x, y, w, h, D, t, cols=4, rows=3):
    gap = 4.0
    tw, th = (w - gap * (cols - 1)) / cols, (h - gap * (rows - 1)) / rows
    out = []
    A = D["aligned"]
    for i in range(rows * cols):
        c, r = i % cols, i // cols
        tx, ty = x + c * (tw + gap), y + r * (th + gap)
        q = to_box(D["map"], tx, ty, tw, th, 3.0)
        lab = A[i]
        keep = np.arange(len(lab)) % 3 == 0  # a third of the dots, for weight
        cell = frame(tx, ty, tw, th, t + 0.02 * i)
        paths = "".join(f'<path class="{cl} sf-tiny" d="{dots_path(q[keep & (lab == v)])}"/>' for v, cl in ((1, INK), (0, BLUE)))
        out.append(cell + pop(paths, t + 0.1 + 0.03 * i))
    return "".join(out)


def ring(cx, cy, r, value, lo, hi, cls, t):
    def at(frac):
        a = 2 * math.pi * frac - math.pi / 2
        return cx + r * math.cos(a), cy + r * math.sin(a)

    ax, ay = at(value)
    arc = f"M{f(cx)} {f(cy - r)} A{f(r)} {f(r)} 0 {1 if value > 0.5 else 0} 1 {f(ax)} {f(ay)}"
    ticks = "".join(f"M{f(cx + (r - 3) * math.cos(2 * math.pi * v - math.pi / 2))} {f(cy + (r - 3) * math.sin(2 * math.pi * v - math.pi / 2))} L{f(cx + (r + 3) * math.cos(2 * math.pi * v - math.pi / 2))} {f(cy + (r + 3) * math.sin(2 * math.pi * v - math.pi / 2))}" for v in (lo, hi))
    return (pop(f'<circle class="sf-track" cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}"/>', t) + draw(f"sf-arc {cls}", arc, t, 0.6)
            + pop(f'<path class="sf-tick" d="{ticks}"/>' + text(cx, cy + 4, f"{value:.2f}", "sx-note sf-small", "middle"), t + 0.3))


def holds(x, y, w, h, D, t):
    S = D["share"]
    n = S.shape[0]
    side = min(h, w * 0.62)
    c = side / n
    my = y + (h - side) / 2
    bins = [(0.02, 0.25, 0.15), (0.25, 0.75, 0.4), (0.75, 1.01, 0.72)]
    cells = ""
    for lo, hi, op in bins:
        d = ""
        for r in range(n):
            j = 0
            while j < n:
                if lo <= S[r, j] < hi:
                    e = j
                    while e + 1 < n and lo <= S[r, e + 1] < hi:
                        e += 1
                    d += f"M{f(x + j * c)} {f(my + r * c)}h{f((e - j + 1) * c)}v{f(c)}h{f(-(e - j + 1) * c)}z"
                    j = e + 1
                else:
                    j += 1
        cells += f'<path class="sf-share" fill-opacity="{op}" d="{d}"/>'
    rr = min(0.5 * h / 2 - 7, (w - side - 20) / 2)
    rx = x + side + 12 + rr
    (v0, l0, h0), (v1, l1, h1) = D["rings"]
    return (frame(x, my, side, side, t) + pop(cells, t + 0.1) + ring(rx, y + h * 0.27, rr, v0, l0, h0, BLUE, t + 0.3)
            + ring(rx, y + h * 0.73, rr, v1, l1, h1, INK, t + 0.4))


def wide(D) -> str:
    k.reset()
    W, H, Y, PH = 1120.0, 262.0, 26.0, 158.0
    cols = ((24.0, 100.0), (168.0, 250.0), (462.0, 170.0), (676.0, 200.0), (920.0, 176.0))
    P = []
    panels = (lambda *a: table(*a), lambda *a: search(*a), lambda *a: groups(*a), lambda *a: refits(*a), lambda *a: holds(*a))
    for i, ((title, line), (x, w)) in enumerate(zip(STAGES, cols)):
        t = 0.1 + 0.3 * i
        P.append(panels[i](x, Y, w, PH, D, t))
        P.append(pop(text(x, Y + PH + 28, fits(title, 12.5, w), "sx-title") + text(x, Y + PH + 46, fits(line, 11.5, w + 1), "sx-note"), t + 0.1))
        if i:
            xp, wp = cols[i - 1]
            P.append(link(xp + wp, Y + PH / 2, x, Y + PH / 2, t))
    print(f"starfold-how.svg: {len(k.WORDS)} words")
    return k.svg("sf-fig sx-wide", W, H, LABEL, P)


def narrow(D) -> str:
    k.reset()
    W, PW, PH, X, GAP = 380.0, 150.0, 96.0, 14.0, 22.0
    ys = [12 + i * (PH + GAP) for i in range(5)]
    tx = X + PW + 16
    P = []
    panels = (lambda *a: table(a[0] + 25, *a[1:2], 100, *a[3:]), lambda *a: search(*a), lambda *a: groups(*a), lambda *a: refits(*a), lambda *a: holds(*a))
    lines = (("no labels",), ("score against a", "structureless copy"), ("UMAP map,", "HDBSCAN cut"), ("random subsets,", "new seeds"), ("pairs, recurrence,", "flags"))
    for i, ((title, _), ln) in enumerate(zip(STAGES, lines)):
        y, t = ys[i], 0.1 + 0.3 * i
        P.append(panels[i](X, y, PW, PH, D, t))
        body = text(tx, y + 34, fits(title, 13, W - tx), "sx-title")
        for j, s in enumerate(ln):
            body += text(tx, y + 54 + 17 * j, fits(s, 12, W - tx), "sx-note")
        P.append(pop(body, t + 0.1))
        if i:
            P.append(link(X + PW / 2, ys[i - 1] + PH, X + PW / 2, y, t))
    print(f"starfold-how-narrow.svg: {len(k.WORDS)} words")
    return k.svg("sf-fig sx-narrow", W, ys[4] + PH + 12, LABEL, P)


def main() -> None:
    D = load()
    for name, out in (("starfold-how.svg", wide(D)), ("starfold-how-narrow.svg", narrow(D))):
        (OUT / name).write_text(out)
        print(f"wrote {OUT / name} ({len(out) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
