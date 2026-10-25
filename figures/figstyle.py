"""Site figure style: fonts, palettes and theme-aware export.

Usage::

    import figstyle as fs
    fs.use_site_style()
    fig, ax = plt.subplots(figsize=fs.slot("column"))
    ax.scatter(x, y, c=fs.categorical(10)[labels], s=fs.dot(5))
    fs.save(fig, "digits_map")                 # SVG, theme-aware
    fs.save(fig, "digits_map", kind="raster")  # PNG + WebP at 2x, light and dark
"""

from __future__ import annotations

import json
import re
import warnings
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import ListedColormap, to_hex

HERE = Path(__file__).resolve().parent
TOKENS = json.loads((HERE / "tokens.json").read_text())
STYLE = HERE / "site.mplstyle"
FONT_DIR = HERE.parent / "_local" / "fonts"  # static OTF/TTF files, untracked; matplotlib cannot read WOFF2
OUT_DIR = HERE.parent / "assets" / "figures"

PX_PER_IN = TOKENS["layout"]["css_px_per_inch"]
SCALE = TOKENS["layout"]["raster_scale"]
# Use these instead of "k", "0.4" or "grey" so export can map them to the theme.
INK, MUTED, RULE = "#010101", "#020202", "#030303"
SENTINELS = {INK: "ink", MUTED: "muted", RULE: "rule"}


def use_site_style() -> None:
    """Register the site fonts (if present) and apply site.mplstyle."""
    for path in sorted(FONT_DIR.glob("*.[ot]tf")):
        font_manager.fontManager.addfont(str(path))
    names = {f.name for f in font_manager.fontManager.ttflist}
    for family in (TOKENS["type"]["serif"], TOKENS["type"]["mono"]):
        if family not in names:
            warnings.warn(
                f"{family} not registered; put its OTF/TTF files in {FONT_DIR}",
                stacklevel=2,
            )
    plt.style.use(STYLE)


def slot(name: str = "column", height_px: int | None = None) -> tuple[float, float]:
    """Figure size in inches for a layout slot; height defaults to a ratio snapped to 8 px."""
    width = {
        "column": TOKENS["layout"]["column_px"],
        "wide": TOKENS["layout"]["wide_px"],
    }[name]
    if height_px is None:
        height_px = round(width / 1.6 / 8) * 8
    return width / PX_PER_IN, height_px / PX_PER_IN


def dot(diameter_px: float) -> float:
    """Scatter size (pt^2) for a marker of the given CSS-pixel diameter."""
    return (diameter_px * 72 / PX_PER_IN) ** 2


def categorical(n: int = 10, theme: str = "light") -> list[str]:
    """First n colours of the site categorical palette (petroff10)."""
    colours = TOKENS["data"]["categorical"][theme]
    if n > len(colours):
        raise ValueError(
            f"{n} classes exceed the {len(colours)}-colour palette; group or facet instead"
        )
    return colours[:n]


def context(theme: str = "light") -> str:
    """Grey for de-emphasised marks (unassigned, background population)."""
    return TOKENS["data"]["context"][theme]


def sequential(name: str | None = None) -> mpl.colors.Colormap:
    """Perceptually uniform sequential map; cividis unless viridis is asked for."""
    return mpl.colormaps[name or TOKENS["data"]["sequential"]]


def mono_ticks(ax) -> None:
    """Set tick labels in the mono face, as numbers are elsewhere on the site."""
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontfamily("monospace")


def _svg_theme(svg: str) -> str:
    """Make a matplotlib SVG follow the page theme when inlined."""
    for hex_, token in SENTINELS.items():
        target = "currentColor" if token == "ink" else f"var(--{token})"
        svg = re.sub(hex_, target, svg, flags=re.IGNORECASE)
    light = TOKENS["data"]["categorical"]["light"]
    for i, hex_ in enumerate(light):
        svg = re.sub(
            rf"{hex_}(?![0-9a-f])", f"var(--cat-{i}, {hex_})", svg, flags=re.IGNORECASE
        )
    svg = re.sub(r"<\?xml[^>]*\?>\s*", "", svg)
    svg = re.sub(r"<!DOCTYPE[^>]*>\s*", "", svg)
    svg = re.sub(r"<metadata>.*?</metadata>\s*", "", svg, flags=re.DOTALL)
    # Drop fixed width/height so CSS sizes the figure; viewBox keeps the ratio.
    svg = re.sub(r'(<svg[^>]*?)\s(width|height)="[^"]*"', r"\1", svg, count=1)
    svg = re.sub(r'(<svg[^>]*?)\s(width|height)="[^"]*"', r"\1", svg, count=1)
    # Round geometry (not opacities) to 0.1 pt: invisible at 2x, halves gzip size.
    num = re.compile(r"-?\d+\.\d+")
    svg = re.sub(
        r'\b(x|y)="(-?\d+\.\d+)"', lambda m: f'{m[1]}="{float(m[2]):.1f}"', svg
    )
    svg = re.sub(
        r'\bd="([^"]*)"',
        lambda m: 'd="' + num.sub(lambda n: f"{float(n[0]):.1f}", m[1]) + '"',
        svg,
    )
    return svg.replace("<svg ", '<svg class="fig" role="img" ', 1)


def save(
    fig, name: str, kind: str = "vector", outdir: Path | None = None
) -> list[Path]:
    """Write a figure for the site.

    kind="vector": one theme-aware SVG (sentinels to currentColor/var(), palette to
    var(--cat-i, hex)). Artists with rasterized=True are embedded as 2x PNG inside it,
    with text and axes still vector.
    kind="raster": PNG and WebP at 2x, once per theme, with sentinels replaced by the
    theme's hex values, for pages that swap sources by data-theme.
    """
    outdir = Path(outdir or OUT_DIR)
    outdir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    if kind == "vector":
        path = outdir / f"{name}.svg"
        # Salt ids with the figure name: reproducible diffs, no clashes between inline SVGs.
        with mpl.rc_context({"svg.hashsalt": name}):
            fig.savefig(
                path, format="svg", dpi=PX_PER_IN * SCALE, metadata={"Date": None}
            )
        path.write_text(_svg_theme(path.read_text()))
        written.append(path)
        return written
    if kind != "raster":
        raise ValueError("kind must be 'vector' or 'raster'")
    from PIL import Image

    for theme in ("light", "dark"):
        swaps = {
            hex_: TOKENS["colour"][token][theme] for hex_, token in SENTINELS.items()
        }
        light, dark = (
            TOKENS["data"]["categorical"]["light"],
            TOKENS["data"]["categorical"]["dark"],
        )
        if theme == "dark":
            swaps.update({a: b for a, b in zip(light, dark) if a != b})
        undo = _recolour(fig, swaps)
        png = outdir / f"{name}-{theme}.png"
        fig.savefig(
            png, format="png", dpi=PX_PER_IN * SCALE, metadata={"Software": None}
        )
        _recolour(fig, undo)
        webp = png.with_suffix(".webp")
        Image.open(png).save(webp, "WEBP", lossless=True, method=6)
        written += [png, webp]
    return written


def _recolour(fig, swaps: dict[str, str]) -> dict[str, str]:
    """Swap exact colours on every artist; return the inverse mapping."""
    swaps = {k.lower(): v for k, v in swaps.items()}
    getters = ("color", "facecolor", "edgecolor", "markerfacecolor", "markeredgecolor")
    for artist in fig.findobj():
        for prop in getters:
            get, setp = (
                getattr(artist, f"get_{prop}", None),
                getattr(artist, f"set_{prop}", None),
            )
            if get is None or setp is None:
                continue
            try:
                value = get()
                if hasattr(value, "ndim") and value.ndim == 2:
                    new = [swaps.get(to_hex(c), c) for c in value]
                    alphas = value[:, 3]
                    rgba = mpl.colors.to_rgba_array(new)
                    rgba[:, 3] = alphas
                    setp(rgba)
                else:
                    hx = to_hex(value)
                    if hx in swaps:
                        setp(swaps[hx])
            except (ValueError, TypeError):
                continue
    return {v.lower(): k for k, v in swaps.items()}


def palette_cmap(n: int = 10, theme: str = "light") -> ListedColormap:
    return ListedColormap(categorical(n, theme), name=f"site{n}")
