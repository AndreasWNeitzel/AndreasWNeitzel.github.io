"""Build the site mark: the Milky Way as a barred spiral drawn in stars, with the Sun marked by its symbol.

The Milky Way is a barred spiral. The mark draws it as a bar and two logarithmic arms with a 13 degree
pitch, close to the measured pitch of the Milky Way's arms, each wrapping about 300 degrees. The arm
stars are small at the bar, largest mid-disc and faint at the edge, as in a real spiral. The Sun sits between the arms at
about two thirds of the radius, drawn as the astronomical Sun symbol (a ring with a central dot);
arm stars that would touch it are left out. Galactic archaeology reads the Milky Way star by star,
from where the Sun sits; the mark is drawn the same way. Filled dots and one ring only, so it holds
at 16 px.

Usage: uv run --with pillow python figures/brand/build_mark.py
Writes assets/img/favicon.svg, assets/img/apple-touch-icon.png and favicon.ico, and prints the
32-unit <symbol> for _includes/icons.html.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
PITCH = math.radians(13)
TILT = math.radians(-24)
R0, RMAX = 4.2, 14.4
SUN_R = 9.0


def layout(small=False):
    k = math.tan(PITCH)
    peak, edge, gapf = (1.25, 0.42, 2.3) if not small else (1.6, 0.7, 2.2)
    th_arm = math.log(SUN_R / R0) / k
    sun_a = TILT + th_arm + 0.42 * math.pi  # between the arms, nearer the trailing one
    sun = (16 + SUN_R * math.cos(sun_a), 16 + SUN_R * math.sin(sun_a))
    dots = []
    for phase in (0.0, math.pi):
        th = 0.0
        while True:
            r = R0 * math.exp(k * th)
            if r > RMAX:
                break
            f = (r - R0) / (RMAX - R0)
            # arms are faint at the bar, brightest mid-disc and fade at the edge
            size = edge + (peak - edge) * math.sin(math.pi * min(1.0, f * 1.15)) ** 0.7
            dots.append((16 + r * math.cos(th + phase + TILT), 16 + r * math.sin(th + phase + TILT), size))
            th += (gapf * size + 0.6) / (r * math.sqrt(1 + k * k))
    clear = 3.0 if not small else 3.4
    dots = [d for d in dots if math.hypot(d[0] - sun[0], d[1] - sun[1]) > clear + d[2]]
    return dots, sun


def bar_polygon(scale=1.0, off=0.0):
    pts = []
    for i in range(72):
        a = 2 * math.pi * i / 72
        ex, ey = 3.35 * math.cos(a), 2.2 * math.sin(a)
        pts.append((off + (16 + ex * math.cos(TILT) - ey * math.sin(TILT)) * scale,
                    off + (16 + ex * math.sin(TILT) + ey * math.cos(TILT)) * scale))
    return pts


def svg_body(small=False):
    dots, (sx, sy) = layout(small)
    out = "".join(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}"/>' for x, y, r in dots)
    out += f'<ellipse cx="16" cy="16" rx="3.35" ry="2.2" transform="rotate({math.degrees(TILT):.1f} 16 16)"/>'
    ring, w, dot = (2.25, 1.05, 0.75) if not small else (2.6, 1.35, 0.95)
    out += (f'<circle cx="{sx:.2f}" cy="{sy:.2f}" r="{ring}" fill="none" stroke="currentColor" stroke-width="{w}"/>'
            f'<circle cx="{sx:.2f}" cy="{sy:.2f}" r="{dot}"/>')
    return out


def main():
    print("SYMBOL", f'<symbol id="i-brand" viewBox="0 0 32 32"><g fill="currentColor">{svg_body()}</g></symbol>')
    fav = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><style>g{color:#1b5fd6;fill:#1b5fd6}'
        "@media (prefers-color-scheme:dark){g{color:#7cb8ff;fill:#7cb8ff}}</style>"
        f"<g>{svg_body(small=True)}</g></svg>\n"
    )
    (ROOT / "assets/img/favicon.svg").write_text(fav)
    for size, out, margin, small in ((180, ROOT / "assets/img/apple-touch-icon.png", 0.14, False),
                                     (48, ROOT / "favicon-48.tmp.png", 0.0, True)):
        k = 8
        S = size * k
        img = Image.new("RGB", (S, S), (5, 7, 13))
        dr = ImageDraw.Draw(img)
        sc = S * (1 - 2 * margin) / 32
        off = S * margin
        ink = (124, 184, 255)
        dots, (ux, uy) = layout(small)
        for x, y, r in dots:
            dr.ellipse([off + (x - r) * sc, off + (y - r) * sc, off + (x + r) * sc, off + (y + r) * sc], fill=ink)
        dr.polygon(bar_polygon(sc, off), fill=ink)
        ring, w, dot = (2.25, 1.05, 0.75) if not small else (2.6, 1.35, 0.95)
        dr.ellipse([off + (ux - ring - w / 2) * sc, off + (uy - ring - w / 2) * sc, off + (ux + ring + w / 2) * sc,
                    off + (uy + ring + w / 2) * sc], outline=ink, width=max(1, round(w * sc)))
        dr.ellipse([off + (ux - dot) * sc, off + (uy - dot) * sc, off + (ux + dot) * sc, off + (uy + dot) * sc], fill=ink)
        img.resize((size, size), Image.LANCZOS).save(out)
    Image.open(ROOT / "favicon-48.tmp.png").save(ROOT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    (ROOT / "favicon-48.tmp.png").unlink()


if __name__ == "__main__":
    main()
