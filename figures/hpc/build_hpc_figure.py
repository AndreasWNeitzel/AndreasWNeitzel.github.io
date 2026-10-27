"""Build the figure for the field-guide page on supercomputers: the two national machines Andreas
computes on, drawn to scale, and how one JANUS run moves through them.

Usage: python3 figures/hpc/build_hpc_figure.py _includes/figures/hpc.svg

Sources (every number printed on the figure)
- Node counts, peak performance and storage of both machines: EuroHPC Joint Undertaking, Our
  supercomputers, https://eurohpc-ju.europa.eu/supercomputers/our-supercomputers_en
  (Deucalion: ARM 1,632 nodes, x86 500 nodes, accelerated 33 nodes with 4 x A100 each,
  9.76 petaflops peak, 10.6 PB parallel file system and 430 TB NVMe; MareNostrum 5: 314 petaflops
  peak, 248 PB storage, Sapphire Rapids and Hopper partitions).
- Deucalion cores per node and interconnect: the hosting site, https://deucalion.acnca.pt/about/
  (A64FX 48 cores, EPYC 7742 128 cores, 4 x A100 per node, 100 Gb/s InfiniBand).
- MareNostrum 5 node counts and node hardware: Barcelona Supercomputing Center, MareNostrum 5
  overview, https://www.bsc.es/supportkc/docs/MareNostrum5/overview/ (general purpose partition
  6,408 nodes of 2 x Intel Xeon Platinum 8480+, 112 cores; accelerated partition 1,120 nodes with
  4 x NVIDIA H100 64 GB).
- The allocations: _data/ledger.yml, entries fund-2026-10-cpca-a1-deucalion,
  fund-2026-10-cpca-a2-marenostrum and fund-2025-hpcvlab-deucalion-team-member.
- Node-days are arithmetic: core-hours divided by the cores of one node and by 24; GPU-hours divided
  by the four GPUs of one node and by 24.
"""

from __future__ import annotations

import sys
from pathlib import Path

W, H = 1120, 492
PICTOS = __import__("json").loads((Path(__file__).resolve().parents[1] / "kit/pictos.json").read_text())

SQ, PITCH, COLS = 7.4, 10.0, 20  # node squares: side, pitch, squares per row
PER_SQ = 32  # nodes per square

MACHINES = [
    {
        "name": "DEUCALION",
        "where": "Guimarães, Portugal; hosted by FCT, run with CNCA, INESC TEC and U. Minho",
        "when": "inaugurated 6 September 2023",
        "peak": 9.76,
        "store": "10.6 PB parallel file system, 430 TB NVMe",
        "parts": [
            ("ARM", 1632, "cpu-on", "1,632 nodes", "Fujitsu A64FX, 48 cores a node"),
            ("x86", 500, "cpu-off", "500 nodes", "2 x AMD EPYC 7742, 128 cores a node"),
            ("A100", 33, "gpu-on", "33 nodes", "4 x NVIDIA A100 a node"),
        ],
    },
    {
        "name": "MARENOSTRUM 5",
        "where": "Barcelona Supercomputing Center, Spain",
        "when": "inaugurated 21 December 2023",
        "peak": 314.0,
        "store": "248 PB storage",
        "parts": [
            ("GPP", 6408, "cpu-on", "6,408 nodes", "2 x Intel Xeon Platinum 8480+, 112 cores"),
            ("ACC", 1120, "gpu-on", "1,120 nodes", "4 x NVIDIA H100 64 GB a node"),
        ],
    },
]

# allocations, from the ledger; node-days are arithmetic from the counts above
ALLOC = [
    {
        "machine": "Deucalion", "ref": "2026.08382.CPCA.A1", "data": "Gaia DR3, about 220 million stars",
        "cpu": "299,520 core-hours, ARM", "gpu": "1,500 A100 GPU-hours", "store": "10 TB", "months": "12 months",
        "cpu_days": 99840 / 48 / 24, "gpu_days": 1500 / 4 / 24, "cores": 48,
    },
    {
        "machine": "MareNostrum 5", "ref": "2026.08362.CPCA.A2", "data": "Gaia DR4, about 1.8 billion stars",
        "cpu": "1,002,400 core-hours, GPP", "gpu": "1,000 H100 GPU-hours", "store": "25 TB", "months": "12 months",
        "cpu_days": 1002400 / 112 / 24, "gpu_days": 1000 / 4 / 24, "cores": 112,
    },
]


def f(v):
    return f"{v:.1f}"


def draw(cls, d, t, dur=0.5):
    return f'<path class="{cls} b-draw" style="--d:{t:.2f}s;--dur:{dur:.2f}s" pathLength="1" d="{d}"/>'


def pop(inner, t):
    return f'<g class="b-pop" style="--d:{t:.2f}s">{inner}</g>'


def text(x, y, s, cls, t, anchor="start"):
    return f'<text class="{cls} b-pop" style="--d:{t:.2f}s" x="{f(x)}" y="{f(y)}" text-anchor="{anchor}">{s}</text>'


def node(x, y, t, size=5.0):
    return pop(f'<rect class="hpc-node" x="{f(x - size / 2)}" y="{f(y - size / 2)}" width="{f(size)}" height="{f(size)}"/>', t)


def machines_panel():
    x0, x1 = 20, 520
    parts = [text(x0, 24, "THE TWO MACHINES, TO SCALE: ONE SQUARE IS 32 NODES", "hpc-head", 0.0)]
    ky = 46
    for k, (cls, lab) in enumerate((("cpu-on", "CPU partitions I use"), ("gpu-on", "GPU partitions I use"), ("cpu-off", "other"))):
        kx = x0 + (0, 168, 336)[k]
        parts.append(pop(f'<rect class="hpc-sq {cls}" x="{kx}" y="{ky - 7}" width="{SQ}" height="{SQ}"/>', 0.1))
        parts.append(text(kx + 12, ky, lab, "bp-tick", 0.1))
    y = 72
    t = 0.2
    for m in MACHINES:
        parts.append(text(x0, y, m["name"], "bp-label2", t))
        parts.append(text(x1, y, m["when"], "bp-tick", t, "end"))
        parts.append(text(x0, y + 14, m["where"], "bp-tick", t))
        gy = y + 24
        i, sq = 0, []
        for _, n, cls, _, _ in m["parts"]:
            for _k in range(round(n / PER_SQ)):
                r, c = divmod(i, COLS)
                sq.append((cls, x0 + c * PITCH, gy + r * PITCH))
                i += 1
        rows = (i + COLS - 1) // COLS
        by_row = {}
        for cls, x, yy in sq:
            by_row.setdefault(yy, []).append(f'<rect class="hpc-sq {cls}" x="{f(x)}" y="{f(yy)}" width="{SQ}" height="{SQ}"/>')
        for k, (yy, rects) in enumerate(sorted(by_row.items())):
            parts.append(pop("".join(rects), t + 0.05 + 0.04 * k))
        # the partition legend beside the block, in the free width to its right
        lx = x0 + COLS * PITCH + 16
        for k, (code, n, cls, count, hw) in enumerate(m["parts"]):
            ly = gy + 8 + 27 * k
            parts.append(pop(f'<rect class="hpc-sq {cls}" x="{f(lx)}" y="{f(ly - 7)}" width="{SQ}" height="{SQ}"/>', t + 0.3 + 0.05 * k))
            parts.append(text(lx + 12, ly, f"{code}: {count}", "hpc-td", t + 0.3 + 0.05 * k))
            parts.append(text(lx + 12, ly + 13, hw, "bp-tick", t + 0.3 + 0.05 * k))
        parts.append(text(lx, gy + 8 + 27 * len(m["parts"]) + 2, m["store"], "bp-tick", t + 0.45))
        y = gy + max(rows * PITCH, 27 * len(m["parts"]) + 14) + 26
        t += 0.5
    ry = y
    parts.append(text(x0, ry, "PEAK PERFORMANCE", "hpc-head", t))
    bar_w = 290.0
    for k, m in enumerate(MACHINES):
        yy = ry + 22 + 22 * k
        w = bar_w * m["peak"] / MACHINES[1]["peak"]
        parts.append(text(x0, yy + 4, ("Deucalion", "MareNostrum 5")[k], "bp-tick", t + 0.1))
        parts.append(draw("hpc-bar", f"M{x0 + 110} {yy} h{f(w)}", t + 0.15 + 0.1 * k, 0.4))
        parts.append(text(x0 + 116 + w, yy + 4, f"{m['peak']:g} petaflops", "hpc-val", t + 0.3 + 0.1 * k))
    parts.append(text(x0, ry + 22 + 22 * 2 + 4, "one petaflop is a million billion calculations a second", "bp-tick", t + 0.4))
    return parts, ry + 22 + 22 * 2 + 10


def run_panel():
    x0, x1 = 560, 1100
    parts = [text(x0, 24, "ONE JANUS RUN ON THE MACHINES", "hpc-head", 1.4)]
    bw, gap, by, bh = 116, 22, 48, 160
    stages = [  # title, one short line, pictogram
        ("file system", "spectra, 10 to 25 TB", "pfs"),
        ("CPU nodes", "Slurm job array", "cpu"),
        ("GPU nodes", "JANUS on CUDA", "gpu"),
        ("catalogue", "labels, reliability", "cat"),
    ]
    xs = [x0 + 4 + k * (bw + gap) for k in range(4)]
    tb = 1.5
    mid = by + bh / 2
    parts.append(pop(f'<path class="ray flowray hpc-thread" d="M{x0 - 12} {f(mid + 14)} C{x0 - 2} {f(mid + 14)} {x0 - 4} {f(mid)} {xs[0]} {f(mid)}"/>', tb))
    for k in range(3):
        xa, xb = xs[k] + bw, xs[k + 1]
        xm = (xa + xb) / 2
        d = (f"M{xa} {f(mid)} C{f(xm)} {f(mid)} {f(xm)} {f(mid - 10)} {xb} {f(mid - 10)}" if k % 2 == 0
             else f"M{xa} {f(mid - 10)} C{f(xm)} {f(mid - 10)} {f(xm)} {f(mid)} {xb} {f(mid)}")
        parts.append(pop(f'<path class="ray flowray hpc-thread" d="{d}"/>', tb + 0.35 + 0.35 * k))
    for k, (title, line, kind) in enumerate(stages):
        x = xs[k]
        t = tb + 0.1 + 0.35 * k
        parts.append(draw("bp", f"M{x} {by} h{bw} v{bh} h-{bw} Z", t, 0.3))
        parts.append(node(x, mid - 10 if k % 2 == 1 else mid, t + 0.05))
        if k < 3:
            parts.append(node(x + bw, mid - 10 if k % 2 == 0 else mid, t + 0.3))
        cx, cy = x + bw / 2, by + bh / 2
        # the object itself, drawn in three dimensions by figures/kit/pictos.mjs
        pic = PICTOS[{"pfs": "storage", "cpu": "cpu", "gpu": "gpu", "cat": "catalogue"}[kind]]
        parts.append(pop(f'<g class="iso-svg" transform="translate({f(cx - pic["w"] / 2)} {f(cy - pic["h"] / 2)})">{pic["body"]}</g>', t + 0.15))
        parts.append(text(cx, by + bh + 18, title, "bp-label2", t + 0.2, "middle"))
        parts.append(text(cx, by + bh + 33, line, "bp-tick", t + 0.25, "middle"))
    # CPU time to scale, including the development access that came first
    ry = by + bh + 76
    parts.append(text(x0, ry, "CPU TIME, TO SCALE", "hpc-head", tb + 1.4))
    bars = (("HPCvLAB development access, used", 94001, "94,001 core-hours, about 250 jobs"),
            ("Deucalion allocation 2026.08382.CPCA.A1", 299520, "299,520 core-hours"),
            ("MareNostrum 5 allocation 2026.08362.CPCA.A2", 1002400, "1,002,400 core-hours"))
    for k, (lab, n, val) in enumerate(bars):
        by_ = ry + 24 + 46 * k
        w = (x1 - x0) * n / bars[-1][1]
        parts.append(text(x0, by_, lab, "bp-tick", tb + 1.45 + 0.1 * k))
        parts.append(text(x1, by_, val, "hpc-val", tb + 1.6 + 0.1 * k, "end"))
        parts.append(draw("hpc-bar", f"M{x0} {by_ + 10} h{f(w)}", tb + 1.5 + 0.1 * k, 0.4))
    return parts, ry + 24 + 46 * 2 + 14


def main(out: Path) -> None:
    left, lbot = machines_panel()
    right, rbot = run_panel()
    parts = left + [draw("bp-thin", "M540 20 V478", 1.3, 0.3)] + right
    svg = (
        f'<svg class="bp-svg hpc-svg" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-labelledby="hpc-ft hpc-fd"><title id="hpc-ft">The two supercomputers, to scale, and one JANUS run</title>'
        '<desc id="hpc-fd">Left: Deucalion and MareNostrum 5 as blocks of node squares, one square for 32 nodes, with the '
        'partitions used by the allocations filled in, and bars comparing their peak performance of 9.76 and 314 '
        'petaflops. Right: a run as four stages, parallel file system, CPU nodes under a Slurm job array, GPU nodes '
        'running the JANUS ensemble, and the catalogue written back, with the two FCT allocations tabulated below.</desc>'
        + "".join(parts) + "</svg>\n"
    )
    out.write_text(svg)
    print(f"wrote {out} ({len(svg) / 1024:.1f} KB); left panel ends at y={lbot:.0f}, right at y={rbot:.0f}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("_includes/figures/hpc.svg"))
