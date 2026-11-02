"""Title-card art for the Software card, one panel per code (Blender, Cycles).
- starfold: the recorded Starfold run on the APOGEE DR19 table (assets/data/starfold, 9,242 stars). Each star sits at
  its place on the two-dimensional map and is lifted by its [alpha/M]; colour is its group's median [Fe/H] (cool
  metal-poor, warm metal-rich), unassigned stars are dim. Real data.
- janus: the lower-triangular covariance a block-Cholesky head predicts for 15 labels, drawn as a field of bars, the
  diagonal brightest; behind it the Gaia XP spectrum of a red giant (bl/spec.json). The bar heights are schematic.
- haydn: a crowded cluster core as counts on a pixel grid: stars drawn from a King profile and a power-law luminosity
  function, each spread by a Moffat PSF, the image lifted into a height field. Schematic.
Usage: uv run --python 3.11 --with bpy==4.2.0 python blender_software.py VARIANT OUT.png [samples] [W] [H]"""
import json, math, random, sys
import bpy, bmesh
import numpy as np
from mathutils import Vector

variant, out = sys.argv[1], sys.argv[2]
samples = int(sys.argv[3]) if len(sys.argv) > 3 else 96
W, H = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (1100, 950)
ROOT = '/home/aneitzel/projects/AndreasWNeitzel.github.io/'
random.seed(5); rng = np.random.default_rng(5)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'

def mix(a, b, t): return tuple(x + (y - x) * t for x, y in zip(a, b))
COLD, WARM, AMBER = (0.42, 0.62, 1.0), (1.0, 0.66, 0.32), (1.0, 0.55, 0.15)

def vcol_emission(name, strength):
    # emission from the per-vertex colour attribute 'col'
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    a = nt.nodes.new('ShaderNodeAttribute'); a.attribute_name = 'col'
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Strength'].default_value = strength
    nt.links.new(a.outputs['Color'], e.inputs['Color']); nt.links.new(e.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface']); return m

def principled(name, base, metal=0.0, rough=0.4):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*base, 1); b.inputs['Metallic'].default_value = metal; b.inputs['Roughness'].default_value = rough; return m

class Mesh:
    # many small shapes in one mesh with a colour per vertex
    def __init__(self): self.bm = bmesh.new(); self.cols = []
    def octa(self, p, r, col):
        vs = [self.bm.verts.new((p[0] + dx * r, p[1] + dy * r, p[2] + dz * r)) for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
        for f in ((0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)): self.bm.faces.new([vs[i] for i in f])
        self.cols += [col] * 6
    def box(self, lo, hi, col_bottom, col_top):
        (x0, y0, z0), (x1, y1, z1) = lo, hi
        vs = [self.bm.verts.new(v) for v in ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))]
        for f in ((0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)): self.bm.faces.new([vs[i] for i in f])
        self.cols += [col_bottom] * 4 + [col_top] * 4
    def obj(self, mat, name='m'):
        me = bpy.data.meshes.new(name); self.bm.verts.ensure_lookup_table(); self.bm.to_mesh(me); self.bm.free()
        at = me.color_attributes.new('col', 'FLOAT_COLOR', 'POINT')
        for i, c in enumerate(self.cols): at.data[i].color = (*c, 1)
        ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); ob.data.materials.append(mat); return ob

def world(color=(0.003, 0.0035, 0.005), haze=0.0):
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (*color, 1)
    if haze:
        v = w.node_tree.nodes.new('ShaderNodeVolumePrincipled'); v.inputs['Density'].default_value = haze
        w.node_tree.links.new(v.outputs['Volume'], w.node_tree.nodes['World Output'].inputs['Volume'])

def floor(z, size=80, base=(0.008, 0.009, 0.011), rough=0.22):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z)); f = bpy.context.object; f.data.materials.append(principled('floor', base, 0.6, rough)); return f

def camera(loc, look, lens, focus=None, fstop=4.0):
    cd = bpy.data.cameras.new('cam'); cd.lens = lens
    if focus: cd.dof.use_dof = True; cd.dof.focus_distance = focus; cd.dof.aperture_fstop = fstop
    cam = bpy.data.objects.new('cam', cd); bpy.context.collection.objects.link(cam); sc.camera = cam
    cam.location = loc; cam.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()

def bloom(size=7, mix_=-0.6):
    sc.use_nodes = True; ct = sc.node_tree; rl = ct.nodes['Render Layers']; comp = ct.nodes['Composite']
    g = ct.nodes.new('CompositorNodeGlare'); g.glare_type = 'FOG_GLOW'; g.quality = 'HIGH'; g.size = size; g.threshold = 0.5; g.mix = mix_
    ct.links.new(rl.outputs['Image'], g.inputs['Image']); ct.links.new(g.outputs['Image'], comp.inputs['Image'])

if variant == 'starfold':
    meta = json.load(open(ROOT + 'assets/data/starfold/apogee_run.json')); raw = open(ROOT + 'assets/data/starfold/apogee_run.bin', 'rb').read()
    A = {a['name']: a for a in meta['arrays']}
    def arr(n):
        a = A[n]; dt = np.dtype(a['dtype']).newbyteorder('<'); cnt = int(np.prod(a['shape']))
        return np.frombuffer(raw, dt, count=cnt, offset=a['offset']).reshape(a['shape'])
    mp, feat, grp = arr('map').astype(float), arr('features').astype(float), arr('group').astype(int)
    mp = (mp - mp.mean(0)) / mp.std(0) * 2.2
    am = feat[:, 1]; z = (am - np.percentile(am, 2)) / (np.percentile(am, 98) - np.percentile(am, 2)); z = np.clip(z, 0, 1) * 2.4
    fe = feat[:, 0]; gfe = {g: np.median(fe[grp == g]) for g in set(grp) if g >= 0}
    order = sorted(gfe, key=gfe.get); rank = {g: k / max(1, len(order) - 1) for k, g in enumerate(order)}
    M = Mesh()
    for i in range(len(mp)):
        g = grp[i]
        if g >= 0:
            t = rank[g]; col = mix(COLD, WARM, t); r = 0.010
        else:
            col = (0.05, 0.055, 0.07); r = 0.007
        M.octa((mp[i, 0], mp[i, 1], z[i] + rng.normal(0, 0.01)), r, col)
    M.obj(vcol_emission('stars', 1.1), 'stars')
    floor(-0.05, base=(0.006, 0.007, 0.009), rough=0.18)
    world(haze=0.004); bloom(6, -0.55)
    camera((-4.2, -5.6, 6.4), (0.1, 0.2, 0.7), 40, 9.0, 3.5)

elif variant == 'janus':
    n = 15; M = Mesh(); pitch = 0.34; blocks = [(0, 3), (3, 15)]
    def corr(i, j):
        same = any(a <= i < b and a <= j < b for a, b in blocks)
        return (0.75 if same else 0.25) * math.exp(-abs(i - j) / (5 if same else 9)) * (0.7 + 0.6 * random.random())
    for i in range(n):
        for j in range(i + 1):
            x = (j - n / 2) * pitch; y = (n / 2 - i) * pitch
            if i == j: h = 1.5 + 0.4 * random.random(); top = AMBER; bot = (0.06, 0.02, 0.0); w_ = 0.022
            else: c = corr(i, j); h = 0.05 + 1.1 * c; top = mix((0.25, 0.42, 0.85), (0.8, 0.9, 1.0), c); bot = (0.0, 0.01, 0.03); w_ = 0.012
            M.box((x - w_, y - w_, 0), (x + w_, y + w_, h), bot, top)
            M.octa((x, y, h), w_ * 2.4, top)
            M.box((x - pitch * 0.45, y - pitch * 0.45, 0), (x + pitch * 0.45, y + pitch * 0.45, 0.002), (0.004, 0.006, 0.012), (0.006, 0.009, 0.018))
    M.obj(vcol_emission('bars', 1.6), 'bars')
    # glass sleeves over the bars would cost too much; a thin dark frame along the triangle's edges instead
    spec = json.load(open(sys.argv[6])) if len(sys.argv) > 6 else None
    if spec:
        f = np.array(spec); f = (f - f.min()) / (f.max() - f.min()); L = Mesh(); xs = np.linspace(-3.4, 3.4, len(f))
        for k in range(0, len(f), 1): L.octa((xs[k], 3.2, 0.25 + 1.4 * f[k]), 0.012, (0.85, 0.9, 1.0))
        L.obj(vcol_emission('spec', 2.0), 'spec')
    floor(0, base=(0.005, 0.006, 0.008), rough=0.12)
    world(haze=0.006); bloom(7, -0.5)
    camera((-5.6, -6.6, 3.4), (-0.3, 0.6, 0.5), 38, 8.6, 2.8)

elif variant == 'haydn':
    N = 220; img = np.zeros((N, N))
    rc, rt = 6.0, 120.0; nstar = 5000
    # King-like radial profile by rejection, luminosity from a power law
    rs = []
    while len(rs) < nstar:
        r = rng.uniform(0, 110)
        if rng.random() < (1 / math.sqrt(1 + (r / rc) ** 2) - 1 / math.sqrt(1 + (rt / rc) ** 2)) ** 2 * (r / 110 + 0.02): rs.append(r)
    th = rng.uniform(0, 2 * np.pi, nstar); xs = N / 2 + np.array(rs) * np.cos(th); ys = N / 2 + np.array(rs) * np.sin(th)
    fl = (1 - rng.random(nstar)) ** (-1 / 1.35)
    yy, xx = np.mgrid[0:N, 0:N]
    for x0, y0, f0 in zip(xs, ys, fl):
        if not (2 < x0 < N - 2 and 2 < y0 < N - 2): continue
        i0, i1, j0, j1 = int(max(0, y0 - 9)), int(min(N, y0 + 10)), int(max(0, x0 - 9)), int(min(N, x0 + 10))
        r2 = (xx[i0:i1, j0:j1] - x0) ** 2 + (yy[i0:i1, j0:j1] - y0) ** 2
        img[i0:i1, j0:j1] += f0 * (1 + r2 / 2.2 ** 2) ** -2.5
    h = np.arcsinh(img / 0.8); h = h / h.max() * 1.1
    M = Mesh(); s = 6.0 / N
    for i in range(N):
        for j in range(N):
            v = h[i, j]; t = min(1.0, v / 1.4)
            top = mix((0.012, 0.02, 0.05), mix((0.3, 0.45, 0.9), (1.0, 0.8, 0.5), min(1, t * 1.2) ** 1.5), min(1, t ** 1.5 * 1.3)); bot = (0.003, 0.005, 0.012)
            x = (j - N / 2) * s; y = (i - N / 2) * s
            M.box((x, y, 0), (x + s * 0.9, y + s * 0.9, 0.004 + v), bot, top)
    M.obj(vcol_emission('px', 0.9), 'pixels')
    floor(0, base=(0.004, 0.005, 0.007), rough=0.3)
    world(haze=0.004); bloom(6, -0.55)
    camera((-3.9, -4.6, 2.2), (0.1, 0.3, 0.2), 44, 6.0, 2.4)

if variant == 'seismo':
    # the oscillation power spectrum of KIC 6144777, a red giant, from 12 quarters of Kepler long-cadence photometry
    # (lightkurve, PDCSAP); each filament is one bin of the smoothed spectrum, its height the power. Real data.
    d = np.load(sys.argv[6]); f, p = d['f'], d['p']
    keep = (f > 70) & (f < 190); f, p = f[keep], p[keep]
    k = 9; ps = np.convolve(p, np.ones(k) / k, 'same')
    lf, lp = np.log(f), np.log(ps); m = (f < 95) | (f > 175)   # background: a power law fitted away from the modes
    b1, b0 = np.polyfit(lf[m], lp[m], 1); snr = ps / np.exp(b0 + b1 * lf)
    nb = 520; edges = np.linspace(f.min(), f.max(), nb + 1); idx = np.digitize(f, edges) - 1
    hb = np.array([snr[idx == i].max() if np.any(idx == i) else 0 for i in range(nb)])
    hb = np.clip(hb / np.percentile(hb, 99.5), 0, 1.15)
    M = Mesh(); xs = np.linspace(-3.6, 3.6, nb)
    for x, v in zip(xs, hb):
        y = 0.25 * math.sin(x * 0.55); h = 0.04 + 2.2 * v ** 1.3; t = min(1.0, v ** 0.8)
        top = mix((0.16, 0.26, 0.6), mix(AMBER, (1.0, 0.8, 0.5), t), min(1, t * 1.6)); bot = (0.01, 0.012, 0.03)
        M.box((x - 0.004, y - 0.004, 0), (x + 0.004, y + 0.004, h), bot, top)
        if v > 0.35: M.octa((x, y, h), 0.018, top)
    M.obj(vcol_emission('psd', 1.6), 'psd')
    floor(0, base=(0.005, 0.006, 0.008), rough=0.1)
    world(haze=0.006); bloom(7, -0.5)
    camera((-3.2, -5.9, 1.5), (0.4, 0.2, 0.85), 44, 6.6, 2.6)

sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print('wrote', out)
