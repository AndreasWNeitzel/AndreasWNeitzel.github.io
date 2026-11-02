"""Regional detail maps for the globe on the home page (assets/js/globe.js): Natural Earth 1:10m countries (world-atlas 2.0.2) for Europe with North
Africa, and for central South America, simplified to 0.006 degrees (half a pixel at the closest zoom), islets under
2 km2 dropped, coordinates rounded to 3 decimals. Writes assets/data/map/globe-mid.json (Europe with North Africa, and South America, at 0.025 degrees) and
globe-near.json (Iberia and the western Mediterranean at 0.005 degrees), both GeoJSON. Natural Earth data are public domain.
Usage: uv run --with shapely python figures/map/build_globe_regions.py"""
import json, urllib.request
from shapely.geometry import shape, mapping, box, Polygon, MultiPolygon
from shapely.ops import unary_union
T = json.loads(urllib.request.urlopen('https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-10m.json', timeout=60).read())
sx, sy = T['transform']['scale']; tx, ty = T['transform']['translate']
arcs = []
for a in T['arcs']:
    x = y = 0; pts = []
    for dx, dy in a: x += dx; y += dy; pts.append((x * sx + tx, y * sy + ty))
    arcs.append(pts)
def ring(ix):
    out = []
    for i in ix:
        pts = arcs[i] if i >= 0 else arcs[~i][::-1]
        out += pts if not out else pts[1:]
    return out
def poly(p):
    sh = ring(p[0]); holes = [h for h in (ring(r) for r in p[1:]) if len(h) >= 4]
    return Polygon(sh, holes) if len(sh) >= 4 else None
def geom(g):
    ps = [poly(g['arcs'])] if g['type'] == 'Polygon' else [poly(p) for p in g['arcs']]
    return MultiPolygon([p for p in ps if p is not None])
def build(REG, tol, area_min, name):
    feats = []
    for g in T['objects']['countries']['geometries']:
        if g['type'] not in ('Polygon', 'MultiPolygon') or 'id' not in g: continue
        s_ = geom(g).buffer(0)
        if not s_.intersects(REG): continue
        s_ = s_.intersection(REG).simplify(tol, preserve_topology=True)
        polys = [p for p in (s_.geoms if hasattr(s_, 'geoms') else [s_]) if isinstance(p, Polygon) and p.area > area_min]
        if not polys: continue
        m = mapping(MultiPolygon(polys)); rnd = lambda c: [[round(x, 3), round(y, 3)] for x, y in c]
        feats.append({'type': 'Feature', 'id': g['id'], 'properties': {}, 'geometry': {'type': 'MultiPolygon', 'coordinates': [[rnd(r) for r in p] for p in m['coordinates']]}})
    out = json.dumps({'type': 'FeatureCollection', 'features': feats}, separators=(',', ':')); open(name, 'w').write(out)
    print(name, len(feats), len(out), sum(len(r) for f in feats for p in f['geometry']['coordinates'] for r in p), 'points')
# Europe with North Africa, and central South America, for the Europe and world zooms
build(unary_union([box(-32, 24, 46, 72), box(-85, -50, -50, -5)]), 0.025, 1.5e-3, 'assets/data/map/globe-mid.json')
# Iberia and the western Mediterranean, for the Portugal zoom
build(box(-26, 24, 20, 53), 0.005, 2e-4, 'assets/data/map/globe-near.json')
