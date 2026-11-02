"""Title-card loop for Starfold: a folded sheet of stars unrolls into the flat map on which the groups separate,
then rolls back up (Blender, Cycles).

What is real. Every point is a star of the recorded Starfold run on the APOGEE DR19 example table
(assets/data/starfold, 9,242 stars); a fixed random subsample of 4,000 is drawn. In the flat state each point sits
at its own position on the run's two-dimensional map (the two map axes, scaled by one common factor so the map keeps
its shape), and its colour is its recorded group: blue for the larger group, brass for the smaller one, graphite for
the stars the run left unassigned. The two groups and the unassigned stars are the run's own; nothing is added.

What is schematic. The rolled state is not data. It is the same flat map rolled about its vertical axis into a
loose spiral of about one and a half turns, leaning a little towards the camera. The sheet opens from its outer
edge inwards, like a carpet, and the bending is only ever moved along the sheet, never stretched, so every star
keeps its place on it and the flat end is exactly the map. The real eight-dimensional space the stars come from is
not drawn; the roll stands for the idea that the stars lie on a curved surface inside a larger space. On the rolled
part the points are drawn in one neutral ivory, and each star takes its group colour once its part of the sheet
lies flat, because the groups are read off the flat map. The hairlines are the sheet's straight rulings and level
lines, which become the straight grid of the flat map; the sheet itself is faint glass. Camera, light, floor and
timing are free choices.

Usage:
  python blender_starfold_manifold.py DATA_DIR OUT_DIR --still T [T ...] [--w 640 --h 360 --samples 32]
  python blender_starfold_manifold.py DATA_DIR OUT_DIR --frames 0 360 [--w 1280 --h 720 --samples 32]
DATA_DIR holds apogee_run.json and apogee_run.bin. T is the loop phase in [0, 1): 0 rolled, 0.5 flat.
Frames are numbered from 0; the loop is 360 frames at 30 per second and frame 360 repeats frame 0.
Set CYCLES_DEVICE=GPU to render on the graphics card."""
import argparse, json, math, os
import numpy as np
import bpy, bmesh

ap = argparse.ArgumentParser()
ap.add_argument('data'); ap.add_argument('out')
ap.add_argument('--still', type=float, nargs='*'); ap.add_argument('--frames', type=int, nargs=2)
ap.add_argument('--w', type=int, default=640); ap.add_argument('--h', type=int, default=360)
ap.add_argument('--samples', type=int, default=32); ap.add_argument('--n', type=int, default=4000)
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)
NF = 360

# ---------- the recorded run ----------
meta = json.load(open(os.path.join(args.data, 'apogee_run.json')))
raw = open(os.path.join(args.data, meta['binary']), 'rb').read()
A = {a['name']: a for a in meta['arrays']}
def arr(n):
    a = A[n]; dt = np.dtype(a['dtype']).newbyteorder('<')
    return np.frombuffer(raw, dt, count=int(np.prod(a['shape'])), offset=a['offset']).reshape(a['shape'])
mp, grp = arr('map').astype(float), arr('group').astype(int)
lo, hi = mp.min(0), mp.max(0)
L = 8.6                                            # sheet width: the arc length that is rolled
k = L / (hi[0] - lo[0])                            # one scale for both map axes
HZ = (hi[1] - lo[1]) * k                           # sheet height, along the roll's vertical axis
sel = np.sort(np.random.default_rng(0).choice(len(mp), args.n, replace=False))
S = (mp[sel, 0] - lo[0]) * k                       # arc length from the sheet's left (inner) edge
Z = (mp[sel, 1] - (lo[1] + hi[1]) / 2) * k         # height on the sheet
G = grp[sel]
sizes = {g: int((grp == g).sum()) for g in set(grp.tolist())}
big = max((g for g in sizes if g >= 0), key=sizes.get)

IVORY = np.array((0.96, 0.92, 0.84)); BLUE = np.array((0.45, 0.62, 1.0)); BRASS = np.array((1.0, 0.70, 0.30))
GRAPH = np.array((0.16, 0.17, 0.20))
C1 = np.array([BLUE if g == big else (GRAPH if g < 0 else BRASS) for g in G])
C0 = np.array([IVORY * (0.45 if g < 0 else 0.62) for g in G])

# ---------- the sheet: a loose Archimedean roll about a vertical axis ----------
R0, B = 0.35, 0.124                                # inner radius, and turn spacing over 2 pi (about 1.5 turns)
SS = np.linspace(0, L, 2401)                       # arc length from the inner edge
KAP = 1 / np.sqrt(R0 ** 2 + 2 * B * SS)
WF = 0.45                                          # width of the bend's soft front

def ease(x): x = min(max(x, 0.0), 1.0); return x * x * x * (x * (6 * x - 15) + 10)

def progress(t):
    t = t % 1.0
    if t < 0.08: return 0.0
    if t < 0.44: return ease((t - 0.08) / 0.36)
    if t < 0.58: return 1.0
    if t < 0.94: return 1 - ease((t - 0.58) / 0.36)
    return 0.0

def centreline(p):
    """Plan view (x, y) of the sheet's profile at arc lengths SS, for unroll progress p. The bending is released
    from the outer edge inwards, like a carpet unrolling, so arc length is kept at every stage."""
    front = (L + 3 * WF) * (1 - p) - 3 * WF * p
    bend = 1 / (1 + np.exp(-(front - SS) / WF))  # 1 where the sheet is still rolled, 0 where it lies flat
    BEND[:] = bend
    kap = KAP * bend * (1 - 0.25 * p)
    cum = np.concatenate([[0], np.cumsum((kap[1:] + kap[:-1]) / 2 * np.diff(SS))])
    th = cum - cum[-1]                             # tangent angle, zero at the outer edge
    dz, dy = np.cos(th), np.sin(th); ds = np.diff(SS)
    z = np.concatenate([[0], np.cumsum((dz[1:] + dz[:-1]) / 2 * ds)])
    y = np.concatenate([[0], np.cumsum((dy[1:] + dy[:-1]) / 2 * ds)])
    z -= z.mean(); y -= y.mean()
    return z, y

BEND = np.zeros_like(SS)
TILT = math.radians(float(os.environ.get('SF_TILT', '16')))   # the rolled sheet leans its top towards the camera

def place(s, z, cx, cy, p=1.0):
    x, y = np.interp(s, SS, cx), np.interp(s, SS, cy)
    a = TILT * (1 - p); c, n = math.cos(a), math.sin(a)
    return np.stack([x, y * c - z * n, y * n + z * c], -1)

def place_line(pts, p):
    a = TILT * (1 - p); c, n = math.cos(a), math.sin(a); x, y, z = pts.T
    return np.stack([x, y * c - z * n, y * n + z * c], -1)

# ---------- scene ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = args.samples; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
if os.environ.get('CYCLES_DEVICE') == 'GPU':
    pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'CUDA'; pr.get_devices()
    for dv in pr.devices: dv.use = dv.type == 'CUDA'
    sc.cycles.device = 'GPU'; sc.cycles.denoising_use_gpu = True
sc.cycles.seed = 7; sc.cycles.max_bounces = 4; sc.cycles.glossy_bounces = 2; sc.cycles.transparent_max_bounces = 16
sc.render.use_persistent_data = True; sc.cycles.volume_step_rate = 4.0
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = args.w, args.h, 100
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'

def nodes(m):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); return nt, nt.nodes['Material Output']

def vcol_emission(name, strength):
    m = bpy.data.materials.new(name); nt, out = nodes(m)
    a = nt.nodes.new('ShaderNodeAttribute'); a.attribute_name = 'col'
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Strength'].default_value = strength
    nt.links.new(a.outputs['Color'], e.inputs['Color']); nt.links.new(e.outputs[0], out.inputs['Surface']); return m

def emission(name, col, strength):
    m = bpy.data.materials.new(name); nt, out = nodes(m)
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (*col, 1); e.inputs['Strength'].default_value = strength
    nt.links.new(e.outputs[0], out.inputs['Surface']); return m

def glass(name):
    m = bpy.data.materials.new(name); nt, out = nodes(m); N = nt.nodes.new; Lk = nt.links.new
    tr = N('ShaderNodeBsdfTransparent'); gl = N('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value = 0.12
    fr = N('ShaderNodeLayerWeight'); fr.inputs['Blend'].default_value = 0.25
    mf = N('ShaderNodeMath'); mf.operation = 'MULTIPLY_ADD'; mf.inputs[1].default_value = 0.35; mf.inputs[2].default_value = 0.03
    Lk(fr.outputs['Facing'], mf.inputs[0])
    m1 = N('ShaderNodeMixShader'); Lk(mf.outputs[0], m1.inputs['Fac']); Lk(tr.outputs[0], m1.inputs[1]); Lk(gl.outputs[0], m1.inputs[2])
    em = N('ShaderNodeEmission'); em.inputs['Color'].default_value = (0.30, 0.42, 0.75, 1)
    f2 = N('ShaderNodeMath'); f2.operation = 'POWER'; f2.inputs[1].default_value = 3.0; Lk(fr.outputs['Facing'], f2.inputs[0])
    es = N('ShaderNodeMath'); es.operation = 'MULTIPLY_ADD'; es.inputs[1].default_value = 0.22; es.inputs[2].default_value = 0.02
    Lk(f2.outputs[0], es.inputs[0]); Lk(es.outputs[0], em.inputs['Strength'])
    ad = N('ShaderNodeAddShader'); Lk(m1.outputs[0], ad.inputs[0]); Lk(em.outputs[0], ad.inputs[1])
    Lk(ad.outputs[0], out.inputs['Surface']); return m

def link(ob): bpy.context.collection.objects.link(ob); return ob

# points: one octahedron per star in a single mesh
OCT = np.array([(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)], float)
FACES = ((0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5))
RAD = np.where(G < 0, 0.016, 0.0195)
bm = bmesh.new()
for i in range(len(S)):
    vs = [bm.verts.new((0, 0, 0)) for _ in range(6)]
    for f in FACES: bm.faces.new([vs[j] for j in f])
me = bpy.data.meshes.new('stars'); bm.to_mesh(me); bm.free()
col_attr = me.color_attributes.new('col', 'FLOAT_COLOR', 'POINT')
stars = link(bpy.data.objects.new('stars', me)); me.materials.append(vcol_emission('stars', 2.1))
OFFS = (OCT[None, :, :] * RAD[:, None, None]).reshape(-1, 3)

# sheet: a grid of faint glass
NU, NV = 400, 16
us = np.linspace(0, L, NU); vz = np.linspace(-HZ / 2, HZ / 2, NV)
bm = bmesh.new()
for j in range(NV):
    for i in range(NU): bm.verts.new((0, 0, 0))
bm.verts.ensure_lookup_table()
for j in range(NV - 1):
    for i in range(NU - 1):
        bm.faces.new([bm.verts[j * NU + i], bm.verts[j * NU + i + 1], bm.verts[(j + 1) * NU + i + 1], bm.verts[(j + 1) * NU + i]])
sme = bpy.data.meshes.new('sheet'); bm.to_mesh(sme); bm.free()
for poly in sme.polygons: poly.use_smooth = True
sheet = link(bpy.data.objects.new('sheet', sme)); sme.materials.append(glass('glass'))
GU, GV = np.meshgrid(us, vz)

# hairlines: rulings (vertical) and level lines (horizontal) of the sheet, plus its edge
def curve_obj(name, splines, depth, mat):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = depth; cu.bevel_resolution = 1
    for npts in splines:
        sp = cu.splines.new('POLY'); sp.points.add(npts - 1)
    ob = link(bpy.data.objects.new(name, cu)); cu.materials.append(mat); return ob
RUL = np.linspace(0, L, 10)[1:-1]; LEV = np.linspace(-HZ / 2, HZ / 2, 7)[1:-1]; NL = 400
lines = curve_obj('lines', [2] * len(RUL) + [NL] * len(LEV), 0.004, emission('lines', (0.42, 0.52, 0.70), 0.4))
edge = curve_obj('edge', [2, 2, NL, NL], 0.0065, emission('edge', (0.45, 0.62, 1.0), 0.9))
SL = np.linspace(0, L, NL)

def set_spline(sp, pts):
    pts = place_line(np.asarray(pts, float), PCUR[0])
    sp.points.foreach_set('co', np.concatenate([pts, np.ones((len(pts), 1))], 1).ravel())

# stage
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.003, 0.0035, 0.005, 1)
vol = w.node_tree.nodes.new('ShaderNodeVolumePrincipled'); vol.inputs['Density'].default_value = float(os.environ.get('SF_HAZE', '0.004'))
w.node_tree.links.new(vol.outputs['Volume'], w.node_tree.nodes['World Output'].inputs['Volume'])
fm = bpy.data.materials.new('floor'); fm.use_nodes = True; bs = fm.node_tree.nodes['Principled BSDF']
bs.inputs['Base Color'].default_value = (0.006, 0.007, 0.009, 1); bs.inputs['Roughness'].default_value = 0.2
fme = bpy.data.meshes.new('floor'); fme.from_pydata([(-60, -60, 0), (60, -60, 0), (60, 60, 0), (-60, 60, 0)], [], [(0, 1, 2, 3)])
fl = link(bpy.data.objects.new('floor', fme)); fl.location.z = -HZ / 2 - 0.6; fme.materials.append(fm)
ld = bpy.data.lights.new('area', 'AREA'); ld.energy = 60; ld.size = 6; ld.color = (0.75, 0.85, 1.0)
lt = link(bpy.data.objects.new('area', ld)); lt.location = (-3, -4, 7); lt.rotation_euler = (0.6, -0.3, 0)
sc.use_nodes = True; ct = sc.node_tree
gl_ = ct.nodes.new('CompositorNodeGlare'); gl_.glare_type = 'FOG_GLOW'; gl_.quality = 'HIGH'; gl_.size = 6; gl_.threshold = 0.6; gl_.mix = -0.6
ct.links.new(ct.nodes['Render Layers'].outputs['Image'], gl_.inputs['Image']); ct.links.new(gl_.outputs['Image'], ct.nodes['Composite'].inputs['Image'])

cd = bpy.data.cameras.new('cam'); cd.lens = 40; cd.dof.use_dof = True; cd.dof.aperture_fstop = 2.8
cam = link(bpy.data.objects.new('cam', cd)); sc.camera = cam
from mathutils import Vector
LOOK = Vector((-0.3, 0.0, -0.1))                   # aim a little right and up of the sheet's centre: the lower left stays quiet

CA0, CA1, CD0, CD1, CH0, CH1 = (float(v) for v in os.environ.get('SF_CAM', '0 8 15.0 1.0 3.8 2.6').split())

PCUR = [1.0]

def pose(t):
    p = progress(t); PCUR[0] = p; cx, cy = centreline(p)
    P = place(S, Z, cx, cy, p)
    me.vertices.foreach_set('co', (np.repeat(P, 6, 0) + OFFS).ravel())
    q = np.clip((1 - np.interp(S, SS, BEND) - 0.1) / 0.85, 0, 1)   # a star takes its group colour once its part of the sheet lies flat
    q = q * q * (3 - 2 * q)
    col = C0 + (C1 - C0) * q[:, None]
    col_attr.data.foreach_set('color', np.concatenate([np.repeat(col, 6, 0), np.ones((len(col) * 6, 1))], 1).ravel())
    me.update()
    sme.vertices.foreach_set('co', place(GU.ravel(), GV.ravel(), cx, cy, p).ravel()); sme.update()
    ex, ey = np.interp(SL, SS, cx), np.interp(SL, SS, cy)
    sp = lines.data.splines
    for i, u in enumerate(RUL):
        x, y = np.interp(u, SS, cx), np.interp(u, SS, cy); set_spline(sp[i], np.array([(x, y, -HZ / 2), (x, y, HZ / 2)]))
    for j, z in enumerate(LEV): set_spline(sp[len(RUL) + j], np.stack([ex, ey, np.full(NL, z)], -1))
    se = edge.data.splines
    for j, i in ((0, 0), (1, -1)): set_spline(se[j], np.array([(cx[i], cy[i], -HZ / 2), (cx[i], cy[i], HZ / 2)]))
    set_spline(se[2], np.stack([ex, ey, np.full(NL, -HZ / 2)], -1)); set_spline(se[3], np.stack([ex, ey, np.full(NL, HZ / 2)], -1))
    lines.data.update_tag(); edge.data.update_tag()
    c2 = math.cos(2 * math.pi * t)                                        # 1 rolled, -1 flat; periodic, so the loop is seamless
    a = math.radians(CA0 + CA1 * c2); D = CD0 - CD1 * c2; h = CH0 + CH1 * c2
    cam.location = Vector((LOOK.x + D * math.sin(a), -D * math.cos(a), h))
    cam.rotation_euler = (LOOK - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cd.dof.focus_distance = (Vector((0, 0, 0)) - cam.location).length
    bpy.context.view_layer.update()

if args.still:
    for t in args.still:
        pose(t); sc.render.filepath = os.path.join(args.out, 'still_%03d.png' % round(t * 1000))
        bpy.ops.render.render(write_still=True)
if args.frames:
    for f in range(*args.frames):
        pose(f / NF); sc.render.filepath = os.path.join(args.out, 'f_%04d.png' % f)
        bpy.ops.render.render(write_still=True)
