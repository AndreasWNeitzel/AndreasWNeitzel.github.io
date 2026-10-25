"""Build the travel-map basemap: Natural Earth countries in an azimuthal equidistant
projection centred on Porto, written as an inline SVG with coordinates in kilometres.

Usage: uv run --with pyshp --with shapely --with numpy python figures/map/build_basemap.py \
    <ne_50m_admin_0_countries.shp> <ne_10m_admin_0_countries.shp> assets/img/map/world_map.svg

Three levels of detail: 1:50M for the world view, 1:50M at finer tolerance for the Europe zoom,
and 1:10M for the Portugal zoom. The script fetches nothing; download Natural Earth 5.1.1 yourself.

Natural Earth is in the public domain (https://www.naturalearthdata.com/about/terms-of-use/).
Markers, arcs and cards are drawn by assets/js/travel-map.js with the same projection.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import shapefile
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from shapely.validation import make_valid

R_EARTH = 6371.0
LAT0, LON0 = 41.1496, -8.6110  # Porto
VISITED = {"PRT", "ESP", "ITA", "DNK", "CHL"}
# Frame in projected km (x east, y north), wide enough for Chile and Denmark.
FRAME = (-13200.0, -11200.0, 6800.0, 4600.0)  # xmin, ymin, xmax, ymax
DETAIL = (-3400.0, -2600.0, 4600.0, 3600.0)  # wider than the Europe zoom view
PORTUGAL = (-650.0, -750.0, 650.0, 450.0)  # wider than the Portugal zoom view
RINGS = (100, 250, 500, 1000, 2500, 5000, 10000)
MAX_ANGLE = np.radians(140.0)


def project(
    lon: np.ndarray, lat: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    phi0, lam0 = np.radians(LAT0), np.radians(LON0)
    phi, lam = np.radians(lat), np.radians(lon)
    cosc = np.sin(phi0) * np.sin(phi) + np.cos(phi0) * np.cos(phi) * np.cos(lam - lam0)
    c = np.arccos(np.clip(cosc, -1.0, 1.0))
    k = np.where(c < 1e-9, 1.0, c / np.sin(np.where(c < 1e-9, 1.0, c)))
    x = R_EARTH * k * np.cos(phi) * np.sin(lam - lam0)
    y = (
        R_EARTH
        * k
        * (np.cos(phi0) * np.sin(phi) - np.sin(phi0) * np.cos(phi) * np.cos(lam - lam0))
    )
    return x, y, c


def rings_of(shape) -> list[np.ndarray]:
    pts = np.asarray(shape.points, dtype=float)
    parts = list(shape.parts) + [len(pts)]
    return [pts[parts[i] : parts[i + 1]] for i in range(len(parts) - 1)]


def to_path(geom, ndigits: int) -> str:
    polys = [geom] if isinstance(geom, Polygon) else list(getattr(geom, "geoms", []))
    out = []
    for poly in polys:
        if not isinstance(poly, Polygon) or poly.is_empty:
            continue
        for ring in [poly.exterior, *poly.interiors]:
            xy = np.asarray(ring.coords)[:-1]
            if len(xy) < 3:
                continue
            fmt = f"{{:.{ndigits}f}}"
            pts = " ".join(f"{fmt.format(x)} {fmt.format(-y)}" for x, y in xy)
            out.append(f"M{pts}Z")
    return "".join(out).replace(".0 ", " ").replace("-0 ", "0 ")


def country_geoms(shp: Path, region) -> dict[str, tuple[str, object]]:
    """Project every country and clip it to `region`; returns {code: (name, geometry)}."""
    reader = shapefile.Reader(str(shp))
    fields = [f[0] for f in reader.fields[1:]]
    a3, name_i = fields.index("ADM0_A3"), fields.index("NAME")
    out = {}
    for sr in reader.iterShapeRecords():
        code, name = sr.record[a3], sr.record[name_i]
        if code == "ATA":
            continue
        polys = []
        for ring in rings_of(sr.shape):
            x, y, c = project(ring[:, 0], ring[:, 1])
            if np.any(c > MAX_ANGLE) or len(x) < 4:
                continue
            poly = make_valid(Polygon(np.column_stack([x, y])))
            if not poly.is_empty:
                polys.append(poly)
        if not polys:
            continue
        geom = unary_union(polys).intersection(region)
        if not geom.is_empty:
            out[code] = (name, geom)
    return out


def line_path(geom, ndigits: int) -> str:
    lines = [geom] if isinstance(geom, LineString) else list(getattr(geom, "geoms", []))
    fmt = f"{{:.{ndigits}f}}"
    parts = []
    for ln in lines:
        if not isinstance(ln, LineString):
            continue
        xy = np.asarray(ln.coords)
        if len(xy) > 1:
            parts.append(
                "M" + " ".join(f"{fmt.format(x)} {fmt.format(-y)}" for x, y in xy)
            )
    return "".join(parts)


def layer(geoms: dict, tol: float, ndigits: int, lod: str) -> str:
    """Stroked fills. Each level's clip region is larger than the view that shows it, so the
    artificial clip edge never appears on screen."""
    paths = []
    for code, (name, geom) in geoms.items():
        g = geom.simplify(tol, preserve_topology=True)
        if g.is_empty:
            continue
        cls = "visited" if code in VISITED else "land"
        d = to_path(g, ndigits)
        if d:
            paths.append(
                f'<path class="{cls}" data-c="{code}" d="{d}"><title>{name}</title></path>'
            )
    return f'<g class="lod lod-{lod}">{"".join(paths)}</g>'


def main(shp50: Path, shp10: Path, out: Path) -> int:
    frame = box(*FRAME)
    europe = box(*DETAIL)
    portugal = box(*PORTUGAL)
    world_g = country_geoms(shp50, frame)
    europe_g = country_geoms(shp50, europe)
    portugal_g = country_geoms(shp10, portugal)
    layers = [
        layer(world_g, 12.0, 0, "world"),
        layer(europe_g, 2.0, 0, "europe"),
        layer(portugal_g, 0.35, 1, "portugal"),
    ]
    rings = "".join(
        f'<circle class="ring" cx="0" cy="0" r="{r}" data-r="{r}"/>' for r in RINGS
    )
    grat = []
    for lon in range(-180, 181, 15):
        lat = np.linspace(-80, 80, 161)
        x, y, c = project(np.full_like(lat, lon), lat)
        keep = c < MAX_ANGLE
        if keep.sum() > 2:
            grat.append(
                LineString(np.column_stack([x[keep], y[keep]])).intersection(frame)
            )
    for lat0 in range(-75, 76, 15):
        lon = np.linspace(-180, 180, 361)
        x, y, c = project(lon, np.full_like(lon, lat0))
        keep = c < MAX_ANGLE
        if keep.sum() > 2:
            grat.append(
                LineString(np.column_stack([x[keep], y[keep]])).intersection(frame)
            )
    gpath = "".join(line_path(g.simplify(5.0), 0) for g in grat if not g.is_empty)
    xmin, ymin, xmax, ymax = FRAME
    vb = f"{xmin:.0f} {-ymax:.0f} {xmax - xmin:.0f} {ymax - ymin:.0f}"
    svg = [
        (
            f'<svg class="tmap-svg" viewBox="{vb}" data-frame="{vb}" preserveAspectRatio="xMidYMid slice" '
            'xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="tmap-title" data-lod="world">'
        ),
        '<title id="tmap-title">Map centred on Porto with the places I have worked and presented</title>',
        f'<g class="grat"><path d="{gpath}"/></g>',
        *layers,
        f'<g class="rings">{rings}</g>',
        '<g class="tmap-routes"></g><g class="tmap-places"></g>',
        "</svg>",
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(svg))
    print(f"wrote {out} ({out.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])))
