"""Shared pieces of the site's schematics (styles in assets/css/schematics.css).

The grammar: construction hairlines (sx-guide), outline for schematic parts (sx-line, sx-box),
filled marks in the mark colour for real data (sx-data), square hand-off nodes (sx-node), one
accent thread of flowing dashes (sx-thread), and a one-time build on first view: elements with
b-draw (pathLength 1, delay --d, duration --dur) draw on, elements with b-pop appear, both only
when the root carries data-build (site.js arms it).
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORDS: list[str] = []
MONO_ADV = 0.6  # Geist Mono advance per character, in em


def reset() -> None:
    WORDS.clear()


def f(v: float) -> str:
    return f"{v:.1f}"


def fits(label: str, size: float, width: float) -> str:
    """Refuse a label wider than the room it has; the check runs at build time."""
    need = len(label) * MONO_ADV * size
    if need > width:
        raise ValueError(f"label too wide for {width:.0f}px: {label!r} needs {need:.0f}px")
    return label


def draw(cls: str, d: str, t: float, dur: float = 0.4, extra: str = "") -> str:
    return f'<path class="{cls} b-draw" style="--d:{t:.2f}s;--dur:{dur:.2f}s" pathLength="1" d="{d}"{extra}/>'


def pop(inner: str, t: float, cls: str = "") -> str:
    return f'<g class="b-pop{" " + cls if cls else ""}" style="--d:{t:.2f}s">{inner}</g>'


def text(x: float, y: float, s: str, cls: str, anchor: str = "start", room: float | None = None, size: float = 11.0) -> str:
    if room is not None:
        fits(s, size, room)
    WORDS.extend(s.split())
    s = s.replace("Gaia", '<tspan class="sx-i">Gaia</tspan>')  # mission names in italics
    return f'<text class="{cls}" x="{f(x)}" y="{f(y)}" text-anchor="{anchor}">{s}</text>'


def node(x: float, y: float, t: float, size: float = 5.0) -> str:
    return pop(f'<rect class="sx-node" x="{f(x - size / 2)}" y="{f(y - size / 2)}" width="{f(size)}" height="{f(size)}"/>', t)


def thread(d: str, t: float, cls: str = "") -> str:
    return pop(f'<path class="sx-thread{" " + cls if cls else ""}" d="{d}"/>', t)


def link(x0: float, y0: float, x1: float, y1: float, t: float) -> str:
    """A flowing connector between two hand-off nodes, curved when the ends differ in height."""
    if abs(y1 - y0) < 0.5:
        d = f"M{f(x0)} {f(y0)} H{f(x1)}"
    elif abs(x1 - x0) < 0.5:
        d = f"M{f(x0)} {f(y0)} V{f(y1)}"
    else:
        b = (x1 - x0) * 0.5
        d = f"M{f(x0)} {f(y0)} C{f(x0 + b)} {f(y0)} {f(x1 - b)} {f(y1)} {f(x1)} {f(y1)}"
    return thread(d, t) + node(x0, y0, t) + node(x1, y1, t + 0.05)


def poly(pts, close: bool = False) -> str:
    s = "M" + " L".join(f"{f(a)} {f(b)}" for a, b in pts)
    return s + (" Z" if close else "")


def dots_path(pts) -> str:
    """Many dots as one path of zero-length segments, drawn with round caps (compact)."""
    return "".join(f"M{a:.1f} {b:.1f}h0" for a, b in pts)


def svg(cls: str, w: float, h: float, label: str, body: list[str], defs: str = "", role: str = "img") -> str:
    return (f'<svg class="sx-svg {cls}" data-build viewBox="0 0 {f(w)} {f(h)}" xmlns="http://www.w3.org/2000/svg" '
            f'role="{role}" aria-label="{label}">' + (f"<defs>{defs}</defs>" if defs else "") + "".join(body) + "</svg>\n")


def starfold_run() -> dict:
    """The recorded Starfold run of assets/data/starfold, as arrays keyed by name."""
    import numpy as np

    base = ROOT / "assets/data/starfold"
    meta = json.loads((base / "apogee_run.json").read_text())
    raw = (base / meta["binary"]).read_bytes()
    out = {}
    for a in meta["arrays"]:
        if a["name"] in ("features", "map", "group", "support", "unresolved"):
            dt = np.dtype(a["dtype"]).newbyteorder("<")
            out[a["name"]] = np.frombuffer(raw, dtype=dt, count=a["length"], offset=a["offset"]).reshape(a["shape"])
    return out
