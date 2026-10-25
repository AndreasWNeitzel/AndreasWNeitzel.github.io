"""Members grid of the recorded Starfold digits run: one row per group, example digits,
group size and recurrence. Real recorded data only (assets/data/starfold_digits_demo.json).
Usage: uv run --with matplotlib --with numpy --with pillow python figures/digits_grid.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, to_rgb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import figstyle as fs

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
D = json.loads((ROOT / "assets/data/starfold_digits_demo.json").read_text())
lab = np.asarray(D["starfold_labels"])
truth = np.asarray(D["truth"])
pix = np.asarray(D["pixels"], dtype=float).reshape(-1, 8, 8) / 16.0
rec = D["group_recurrence"]

fs.use_site_style()
pal = fs.categorical(10)
rows = [(g, np.flatnonzero(lab == g)) for g in range(10)] + [(-1, np.flatnonzero(lab < 0))]
n_show = 11
rng = np.random.default_rng(0)
width_px, row_px = 680, 40
fig = plt.figure(figsize=(width_px / 96, (row_px * len(rows) + 8) / 96))
fig.set_constrained_layout(False)
left, thumb_w, gap = 0.125, 0.042, 0.006
for r, (g, idx) in enumerate(rows):
    yc = 1 - (r + 0.5) * row_px / (row_px * len(rows) + 8)
    colour = pal[g] if g >= 0 else fs.context()
    fig.text(0.0, yc, f"group {g}" if g >= 0 else "unassigned", va="center", ha="left", fontsize=9.75, color=colour)
    pick = rng.choice(idx, size=min(n_show, len(idx)), replace=False)
    cmap = LinearSegmentedColormap.from_list("g", [(*to_rgb(colour), 0.0), (*to_rgb(colour), 1.0)])
    for k, i in enumerate(sorted(pick, key=lambda i: truth[i])):
        ax = fig.add_axes([left + k * (thumb_w + gap), yc - 0.42 * row_px / (row_px * len(rows) + 8), thumb_w, 0.84 * row_px / (row_px * len(rows) + 8)])
        ax.imshow(pix[i], cmap=cmap, vmin=0, vmax=1, interpolation="nearest")
        ax.set_axis_off()
    n = len(idx)
    note = f"{n} digits, {round(rec[g] * 100)}% of refits" if g >= 0 else f"{n} digits, no group"
    fig.text(left + n_show * (thumb_w + gap) + 0.01, yc, note, va="center", ha="left", fontsize=9.75, color=fs.MUTED, family="monospace")
out = fs.save(fig, "digits_grid", kind="vector", outdir=ROOT / "_includes" / "figures")
print(out, (ROOT / "_includes/figures/digits_grid.svg").stat().st_size, "bytes")
