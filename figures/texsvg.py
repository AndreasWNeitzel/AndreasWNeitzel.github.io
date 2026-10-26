"""Typeset short LaTeX snippets as SVG glyph outlines for the site's inline figures.

latex writes a DVI, dvisvgm turns it into outlines (no fonts needed in the browser), and the glyphs
are returned as one SVG fragment with its origin on the left end of the baseline, scaled so that the
TeX em equals `size` user units. The fragment has no fill, so the caller's class sets the colour.

    from texsvg import tex_glyphs
    body, width = tex_glyphs(r"\\nu_{\\max}", 13)
    svg_text = f'<g class="eo-tex" transform="translate({x} {y})">{body}</g>'
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

DOC = (
    "\\documentclass[12pt]{article}\\usepackage{amsmath,amssymb}\\pagestyle{empty}"
    "\\begin{document}$%s\\mathrm{I}$\\end{document}\n"
)
# The trailing upright I is a sentinel: its glyph sits on the baseline at the right end of the
# snippet, which gives the baseline (also for snippets that start with a radical, whose glyph
# origin lies below the baseline) and the snippet's width. It is removed from the output.


@lru_cache(maxsize=None)
def tex_glyphs(snippet: str, size: float) -> tuple[str, float]:
    with tempfile.TemporaryDirectory() as d:
        Path(d, "t.tex").write_text(DOC % snippet)
        subprocess.run(["latex", "-interaction=nonstopmode", "-halt-on-error", "t.tex"], cwd=d, check=True, capture_output=True)
        subprocess.run(["dvisvgm", "--no-fonts", "--exact-bbox", "--precision=4", "-o", "t.svg", "t.dvi"],
                       cwd=d, check=True, capture_output=True)
        svg = Path(d, "t.svg").read_text()
    q = "['\"]"
    defs = dict(re.findall(rf"<path id={q}([^'\"]+){q} d={q}([^'\"]+){q}\s*/>", svg))
    uses = [(float(x), float(y), ref) for x, y, ref in
            re.findall(rf"<use x={q}([-\d.]+){q} y={q}([-\d.]+){q} (?:xlink:)?href={q}#([^'\"]+){q}\s*/>", svg)]
    rects = [tuple(map(float, r)) for r in
             re.findall(rf"<rect x={q}([-\d.]+){q} y={q}([-\d.]+){q} height={q}([-\d.]+){q} width={q}([-\d.]+){q}\s*/>", svg)]
    vb = [float(v) for v in re.search(rf"viewBox={q}([^'\"]+){q}", svg).group(1).split()]
    if not uses:
        raise ValueError(f"no glyphs for {snippet!r}")
    sentinel = uses[-1]
    uses = uses[:-1]
    if not uses:
        raise ValueError(f"no glyphs for {snippet!r}")
    x0, y0 = min(x for x, _, _ in uses), sentinel[1]
    k = size / 12.0
    out = [f'<path transform="translate({(x - x0) * k:.3f} {(y - y0) * k:.3f}) scale({k:.4f})" d="{defs[ref]}"/>'
           for x, y, ref in uses]
    out += [f'<rect x="{(x - x0) * k:.3f}" y="{(y - y0) * k:.3f}" width="{w * k:.3f}" height="{h * k:.3f}"/>'
            for x, y, h, w in rects]
    return "".join(out), (sentinel[0] - x0) * k
