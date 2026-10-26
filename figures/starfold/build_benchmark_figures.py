"""Export the recorded Starfold benchmark results and draw the benchmark figures as SVG.

Two steps, both standard library only (plus figures/texsvg.py for the LaTeX glyphs):

    python3 figures/starfold/build_benchmark_figures.py export <starfold repo> <site root>
    python3 figures/starfold/build_benchmark_figures.py draw <site root>

`export` reads bench/results/summary.json from the Starfold checkout, keeps the per-table and
injection records the figures need, and writes them with a provenance file under
assets/data/starfold/benchmark/. `draw` reads those files and writes
_includes/figures/starfold-resolution.svg and _includes/figures/starfold-injection.svg.

The x axes follow bench/figures.py in the Starfold repository: a group size is divided by
sqrt(15 m) with m = 0.8 n, the edge bound of a 15-neighbour graph on a resample of n rows
(Fortunato and Barthelemy 2007, doi:10.1073/pnas.0605965104). Nothing is recomputed from data:
every plotted value is read from the recorded summary.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from texsvg import tex_glyphs  # noqa: E402

RESAMPLE_FRACTION = 0.8
NEIGHBORS = 15
PRETTY = {
    "digits": "Digits", "rice": "Rice", "landsat": "Landsat", "pendigits": "PenDigits",
    "dry_bean": "Dry Bean", "waveform": "Waveform", "coil20": "COIL-20", "isolet": "Isolet",
    "gas_drift": "Gas drift", "letter": "Letter",
}
DATA = Path("assets/data/starfold/benchmark")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scale(rows: float) -> float:
    """sqrt(15 m) with m = 0.8 n."""
    return math.sqrt(NEIGHBORS * RESAMPLE_FRACTION * rows)


# ------------------------------------------------------------------ export
def export(repo: Path, site: Path) -> None:
    src = repo / "bench/results/summary.json"
    summary = json.loads(src.read_text())
    tables = []
    for r in summary["datasets"]:
        n, c = r["n_rows"], r["n_classes"]
        tables.append({
            "key": r["dataset"], "table": PRETTY[r["dataset"]],
            "set": "held-out" if r["split"] == "sealed" else "development",
            "n_rows": n, "n_classes": c, "n_features": r["n_features"],
            "starfold_recovery": r["coverage_ari"], "defaults_recovery": r["default_coverage_ari"],
            "gain": r["gain"], "spearman_score_recovery": r["spearman_score_ari"],
            "class_size_over_scale": RESAMPLE_FRACTION * n / c / scale(n),
        })
    injection = []
    for r in summary["injection"]:
        total = r["n_rows"] + r["n_injected_rows"]
        injection.append({
            "rows_per_group": r["rows_per_group"], "n_real_rows": r["n_rows"],
            "n_injected_rows": r["n_injected_rows"], "contrast": r["contrast"],
            "retrieval_rate": r["retrieval_rate"],
            "group_size_over_scale": RESAMPLE_FRACTION * r["rows_per_group"] / scale(total),
            "by_threshold": [{"threshold": b["threshold"],
                              "purity": b["mean_purity_of_matched_group"],
                              "completeness": b["mean_completeness_of_injected"],
                              "groups_with_a_match": b["groups_with_a_match"]} for b in r["by_threshold"]],
        })
    out = site / DATA
    out.mkdir(parents=True, exist_ok=True)
    (out / "resolution.json").write_text(json.dumps(tables, indent=1))
    (out / "injection.json").write_text(json.dumps(injection, indent=1))
    prov = {
        "source": {"repository": "https://github.com/AndreasWNeitzel/starfold",
                   "file": "bench/results/summary.json", "sha256": sha256(src),
                   "file_last_commit": "bc89297ba02d697928e8af3914d21bdde01d2b58 (2026-09-28)",
                   "benchmark_tag": "v0.2.0", "benchmark_commit": "f93dea03aa0f29a2e538b7221970a35898ea3c90",
                   "injection_records_file": "bench/results/injection_recovery.json",
                   "injection_records_sha256": sha256(repo / "bench/results/injection_recovery.json")},
        "exported": dt.date.today().isoformat(),
        "definitions": {
            "starfold_recovery": "adjusted Rand index (floored at 0) against the true classes on the assigned rows, times the share of rows assigned, for the selected setting",
            "defaults_recovery": "median of the same quantity for the UMAP and HDBSCAN library defaults over 8 seeds",
            "gain": "starfold_recovery minus defaults_recovery",
            "spearman_score_recovery": "Spearman correlation of the label-free trial score with the recovery of each trial, over the search trials of that table",
            "class_size_over_scale": "0.8 n / classes divided by sqrt(15 x 0.8 n): the mean class size in an 80 percent resample over the modularity resolution scale, as in bench/figures.py",
            "injection": "synthetic groups of declared size were injected into the real APOGEE DR19 example table (2,000 rows) as a check of the method; a group counts as retrieved when an emitted group reaches Jaccard 0.5 with it; purity and completeness are averaged over the three injected groups at each support threshold; purity is null where no group matched; the injected rows are never kept (bench/injection_recovery.py)",
        },
        "licence": "Results: MIT, as the Starfold repository. Only derived scores are exported.",
    }
    (out / "provenance.json").write_text(json.dumps(prov, indent=1))
    print(f"exported {len(tables)} tables and {len(injection)} injection records to {out}")


# ------------------------------------------------------------------ drawing helpers
def f(v: float) -> str:
    return f"{v:.1f}"


def draw(cls: str, d: str, t: float, dur: float = 0.4) -> str:
    return f'<path class="{cls} b-draw" style="--d:{t:.2f}s;--dur:{dur:.2f}s" pathLength="1" d="{d}"/>'


def pop(inner: str, t: float) -> str:
    return f'<g class="b-pop" style="--d:{t:.2f}s">{inner}</g>'


def text(x: float, y: float, s: str, cls: str, anchor: str = "start", extra: str = "") -> str:
    return f'<text class="{cls}" x="{f(x)}" y="{f(y)}" text-anchor="{anchor}"{extra}>{s}</text>'


def run(parts, cls: str, size: float, anchor: str = "start") -> tuple[str, float]:
    """A label of mono text and LaTeX glyphs set from its left end; returns (svg, width)."""
    adv = 0.6 * size
    cur, out = 0.0, []
    for kind, seg in parts:
        if kind == "text":
            out.append(f'<text class="{cls}" x="{cur:.1f}" y="0" style="white-space:pre">{seg}</text>')
            cur += len(seg) * adv
        else:
            body, w = tex_glyphs(seg, size * 1.3)
            out.append(f'<g class="{cls}-tex" transform="translate({cur + 1:.1f} 0)">{body}</g>')
            cur += w + 2
    shift = {"start": 0.0, "middle": -cur / 2, "end": -cur}[anchor]
    return f'<g transform="translate({shift:.1f} 0)">{"".join(out)}</g>', cur


class Panel:
    """A log-x, linear-y plot panel in SVG user units."""

    def __init__(self, x0, y0, w, h, xlim, ylim, logx=True):
        self.x0, self.y0, self.w, self.h = x0, y0, w, h
        self.xlim, self.ylim, self.logx = xlim, ylim, logx

    def px(self, v):
        a, b = self.xlim
        t = (math.log10(v) - math.log10(a)) / (math.log10(b) - math.log10(a)) if self.logx else (v - a) / (b - a)
        return self.x0 + t * self.w

    def py(self, v):
        a, b = self.ylim
        return self.y0 + self.h - (v - a) / (b - a) * self.h

    def frame(self, xticks, yticks, xlabel_parts, ylabel, t0=0.0, ytick_fmt=lambda v: f"{v:g}"):
        p = [draw("sfb-axis", f"M{f(self.x0)} {f(self.y0)} V{f(self.y0 + self.h)} H{f(self.x0 + self.w)}", t0, 0.3)]
        for v in xticks:
            x = self.px(v)
            p.append(f'<path class="sfb-tick" d="M{f(x)} {f(self.y0 + self.h)} v5"/>')
            p.append(text(x, self.y0 + self.h + 17, f"{v:g}", "sfb-num", "middle"))
        for v in yticks:
            y = self.py(v)
            p.append(f'<path class="sfb-tick" d="M{f(self.x0 - 5)} {f(y)} h5"/>')
            p.append(text(self.x0 - 8, y + 4, ytick_fmt(v), "sfb-num", "end"))
        g, _ = run(xlabel_parts, "sfb-lab", 11, "end")
        p.append(f'<g transform="translate({f(self.x0 + self.w)} {f(self.y0 + self.h + 36)})">{g}</g>')
        p.append(f'<text class="sfb-lab" transform="translate({f(self.x0 - 44)} {f(self.y0)}) rotate(-90)" text-anchor="end">{ylabel}</text>')
        return "".join(p)


SCALE_LABEL = [("text", "mean class size in a resample, over "), ("tex", r"\sqrt{15\,m}")]
INJ_LABEL = [("text", "injected group in a resample, over "), ("tex", r"\sqrt{15\,m}")]


def guide_lines(panel: Panel, t: float, zero=True):
    p = [draw("sfb-guide", f"M{f(panel.px(1.0))} {f(panel.y0)} V{f(panel.y0 + panel.h)}", t, 0.17)]
    if zero:
        p.append(draw("sfb-zero", f"M{f(panel.x0)} {f(panel.py(0))} H{f(panel.x0 + panel.w)}", t + 0.05, 0.17))
    return "".join(p)


def scale_note(panel: Panel, t: float):
    g, _ = run([("text", "group of "), ("tex", r"\sqrt{15\,m}"), ("text", " rows")], "sfb-note", 10.5, "start")
    return pop(f'<g transform="translate({f(panel.px(1.0) + 6)} {f(panel.y0 + panel.h - 8)})">{g}</g>', t)


# ------------------------------------------------------------------ figure 1: resolution
def figure_resolution(site: Path) -> None:
    rows = json.loads((site / DATA / "resolution.json").read_text())
    W, H = 1120, 392
    left = Panel(70, 20, 440, 300, (0.3, 12), (-0.3, 0.36))
    right = Panel(650, 20, 440, 300, (0.3, 12), (-0.5, 0.7))
    # label offsets per table and panel, chosen by hand so that no label covers a mark
    off_gain = {"landsat": (8, -8, "start"), "rice": (8, -8, "start"), "waveform": (8, 4, "start"),
                "digits": (8, -8, "start"), "letter": (8, 12, "start"), "pendigits": (8, 18, "start"),
                "dry_bean": (-8, -8, "end"), "gas_drift": (8, 4, "start"), "coil20": (8, 12, "start"),
                "isolet": (8, 4, "start")}
    off_rho = {"landsat": (-8, 14, "end"), "dry_bean": (8, 12, "start"), "rice": (8, 4, "start"),
               "waveform": (8, 4, "start"), "pendigits": (8, 14, "start"), "letter": (8, -8, "start"),
               "digits": (8, 4, "start"), "coil20": (8, -8, "start"), "isolet": (8, 10, "start"),
               "gas_drift": (8, 4, "start")}
    p = []
    p.append(left.frame((0.5, 1, 2, 5, 10), (-0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3), SCALE_LABEL, "recovery minus default recovery", 0.0,
                        lambda v: f"{v:+.1f}" if v else "0"))
    p.append(right.frame((0.5, 1, 2, 5, 10), (-0.4, -0.2, 0, 0.2, 0.4, 0.6), SCALE_LABEL, "Spearman of trial score against recovery", 0.1,
                         lambda v: f"{v:+.1f}" if v else "0"))
    p.append(guide_lines(left, 0.3)); p.append(guide_lines(right, 0.35))
    p.append(scale_note(left, 0.5)); p.append(scale_note(right, 0.55))
    t = 0.6
    for panel, key, offs in ((left, "gain", off_gain), (right, "spearman_score_recovery", off_rho)):
        for r in rows:
            v = r[key]
            if v is None:
                continue
            x, y = panel.px(r["class_size_over_scale"]), panel.py(v)
            held = r["set"] == "held-out"
            mark = (f'<rect class="sfb-held" x="{f(x - 5)}" y="{f(y - 5)}" width="10" height="10"/>' if held
                    else f'<circle class="sfb-dev" cx="{f(x)}" cy="{f(y)}" r="5.2"/>')
            dx, dy, anchor = offs[r["key"]]
            p.append(pop(mark + f'<title>{r["table"]}: {v:.3f}</title>', t))
            p.append(pop(text(x + dx, y + dy, r["table"], "sfb-name", anchor), t + 0.05))
            t += 0.05
    # legend
    lx, ly = left.x0 + 12, left.y0 + 16
    p.append(pop(f'<circle class="sfb-dev" cx="{f(lx)}" cy="{f(ly)}" r="5.2"/>' + text(lx + 12, ly + 4, "development table", "sfb-note")
                 + f'<rect class="sfb-held" x="{f(lx + 148)}" y="{f(ly - 5)}" width="10" height="10"/>' + text(lx + 165, ly + 4, "held-out table", "sfb-note"), 0.9))
    svg = (f'<svg class="sfb-svg" data-build viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
           'aria-label="Two scatter plots over the ten benchmark tables. Left: Starfold recovery minus the default recovery against '
           'the mean class size over the resolution scale; right: the Spearman correlation of the trial score with recovery. '
           'Development tables as circles, held-out tables as squares; a dashed line marks a group of the resolution scale.">'
           + "".join(p) + "</svg>\n")
    (site / "_includes/figures/starfold-resolution.svg").write_text(svg)


# ------------------------------------------------------------------ figure 2: injection
def figure_injection(site: Path) -> None:
    recs = json.loads((site / DATA / "injection.json").read_text())
    W, H = 1120, 392
    left = Panel(70, 20, 440, 300, (0.12, 2.5), (-0.05, 1.15))
    right = Panel(650, 20, 440, 300, (-0.04, 0.96), (-0.05, 1.05), logx=False)
    p = [left.frame((0.2, 0.5, 1, 2), (0, 0.2, 0.4, 0.6, 0.8, 1.0), INJ_LABEL, "fraction of injected groups retrieved", 0.0),
         right.frame((0, 0.2, 0.4, 0.6, 0.8), (0, 0.2, 0.4, 0.6, 0.8, 1.0), [("text", "recurrence support threshold")], "purity (solid) and completeness (dashed)", 0.1),
         guide_lines(left, 0.3, zero=False), scale_note(left, 0.5)]
    pts = [(left.px(r["group_size_over_scale"]), left.py(r["retrieval_rate"]), r) for r in recs]
    p.append(draw("sfb-line", "M" + " L".join(f"{f(x)} {f(y)}" for x, y, _ in pts), 0.6, 0.8))
    for i, (x, y, r) in enumerate(pts):
        p.append(pop(f'<circle class="sfb-dev" cx="{f(x)}" cy="{f(y)}" r="5.2"/><title>{r["rows_per_group"]} rows: {r["retrieval_rate"]:.0%} retrieved</title>', 0.7 + 0.08 * i))
        dy = -10 if r["retrieval_rate"] else -10
        p.append(pop(text(x + (6 if i < 2 else 0), y + dy, f'{r["rows_per_group"]} rows', "sfb-name", "start" if i < 2 else "middle"), 0.75 + 0.08 * i))
    colours = ["--cat-0", "--cat-4", "--cat-6"]
    shown = [r for r in recs if r["retrieval_rate"]]
    t = 1.2
    for r, col in zip(shown, colours):
        pur = [(b["threshold"], b["purity"]) for b in r["by_threshold"] if b["purity"] is not None]
        com = [(b["threshold"], b["completeness"]) for b in r["by_threshold"]]
        if len(pur) > 1:
            p.append(draw("sfb-series", "M" + " L".join(f"{f(right.px(a))} {f(right.py(b))}" for a, b in pur), t, 0.6).replace('class="sfb-series', f'style="stroke:var({col})" class="sfb-series'))
        p.append(draw("sfb-series-dash", "M" + " L".join(f"{f(right.px(a))} {f(right.py(b))}" for a, b in com), t + 0.1, 0.6).replace('class="sfb-series-dash', f'style="stroke:var({col})" class="sfb-series-dash'))
        for a, b in pur:
            p.append(pop(f'<circle class="sfb-pt" style="fill:var({col})" cx="{f(right.px(a))}" cy="{f(right.py(b))}" r="4.6"/>', t + 0.2))
        for a, b in com:
            p.append(pop(f'<rect class="sfb-pt-open" style="stroke:var({col})" x="{f(right.px(a) - 4)}" y="{f(right.py(b) - 4)}" width="8" height="8"/>', t + 0.3))
        t += 0.25
    # legend for the right panel
    lx, ly = right.x0 + 12, right.y0 + right.h - 60
    leg = []
    for i, (r, col) in enumerate(zip(shown, colours)):
        y = ly + 16 * i
        leg.append(f'<path style="stroke:var({col})" class="sfb-series" d="M{f(lx)} {f(y - 4)} h18"/>'
                   + text(lx + 26, y, f'{r["rows_per_group"]} rows per group', "sfb-note"))
    y = ly + 16 * len(shown)
    leg.append(f'<path class="sfb-series-dash sfb-legend-dash" d="M{f(lx)} {f(y - 4)} h18"/>' + text(lx + 26, y, "dashed: completeness of the injected rows", "sfb-note"))
    p.append(pop("".join(leg), 1.9))
    svg = (f'<svg class="sfb-svg" data-build viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
           'aria-label="Left: the fraction of injected groups retrieved against the injected group size over the resolution scale, '
           'zero for 30 and 60 rows and one for 120, 240 and 480 rows. Right: purity and completeness of the retrieved groups '
           'against the recurrence support threshold for the three retrieved sizes.">' + "".join(p) + "</svg>\n")
    (site / "_includes/figures/starfold-injection.svg").write_text(svg)


def main(argv: list[str]) -> int:
    if len(argv) == 4 and argv[1] == "export":
        export(Path(argv[2]), Path(argv[3]))
    elif len(argv) == 3 and argv[1] == "draw":
        figure_resolution(Path(argv[2]))
        figure_injection(Path(argv[2]))
        print("wrote _includes/figures/starfold-resolution.svg and starfold-injection.svg")
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
