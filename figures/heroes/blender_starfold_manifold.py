"""Title-card loop for Starfold: stars leave the plane of [alpha/M] against [Fe/H], settle on a rolled sheet, the sheet
unrolls into the flat map on which the groups stand apart, and everything returns (Blender, Cycles).

What is real. Every point is a star of the recorded Starfold run on the APOGEE DR19 example table
(assets/data/starfold, 9,242 stars); a fixed random subsample of 4,000 is drawn, and the same stars are drawn in every
frame. On the upright plate each star sits at its own recorded [Fe/H] (across) and [alpha/M] (up), so the two ridges
are the high-alpha and low-alpha sequences as measured; the plate's rules fall on round values of the two
abundances, and a few very metal-poor stars lie past its left edge. On the flat map each star sits at its own position
on the run's two-dimensional map, the two axes scaled by one common factor, with the smaller group to the right and
the sheet that carries the map a little longer than the map at either end, so that it spans most of the frame. The
colour of a star is its recorded group throughout: blue for the larger group, brass for the smaller one, graphite for
the stars the run left unassigned. Nothing is added.

What is schematic. The paths between the plate and the sheet are not data: each star moves alone along an eased
arc towards the camera, starting a little after its neighbours higher on the plate. The rolled state is not data
either. It is the same flat map rolled about its vertical axis into a loose spiral of about one and a half turns. The
sheet opens from its outer edge inwards, like a carpet, and the bending is only ever moved along the sheet, never
stretched, so every star keeps its place on it and the flat end is exactly the map. The real eight-dimensional space
is not drawn, and the map was not made from the two plate columns alone; the roll stands for the idea that the stars
lie on a curved surface inside a larger space. The hairlines of the sheet are its straight rulings and level lines,
which become the straight grid of the flat map; plate and sheet are faint glass. Camera, light, floor and timing are
free choices.

Usage:
  python blender_starfold_manifold.py DATA_DIR OUT_DIR --still T [T ...] [--w 640 --h 360 --samples 32]
  python blender_starfold_manifold.py DATA_DIR OUT_DIR --frames 0 199 [--w 1280 --h 720 --samples 32]
DATA_DIR holds apogee_run.json and apogee_run.bin. T is the loop phase in [0, 1]: 0 the plate, 0.23 the roll, 0.5 the
flat map. The loop is 397 frames at 30 per second, numbered from 0. The second half plays the first backwards, so
frame 396 - f is frame f and only frames 0 to 198 need rendering; frame 396 equals frame 0.
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
NF = 397
FPS = 30

# ---------- the recorded run ----------
meta = json.load(open(os.path.join(args.data, 'apogee_run.json')))
raw = open(os.path.join(args.data, meta['binary']), 'rb').read()
A = {a['name']: a for a in meta['arrays']}
def arr(n):
    a = A[n]; dt = np.dtype(a['dtype']).newbyteorder('<')
    return np.frombuffer(raw, dt, count=int(np.prod(a['shape'])), offset=a['offset']).reshape(a['shape'])
mp, grp, feat = arr('map').astype(float), arr('group').astype(int), arr('features').astype(float)
names = [c['name'] for c in meta['columns']]
FE, AL = feat[:, names.index('fe_h')], feat[:, names.index('alpha_m')]
lo, hi = mp.min(0), mp.max(0)
MAP_L, MARGIN = 12.6, 1.5                          # width of the map, and the blank sheet beyond it at either end
L = MAP_L + 2 * MARGIN                             # sheet width: the arc length that is rolled
k = MAP_L / (hi[0] - lo[0])                        # one scale for both map axes
HZ = (hi[1] - lo[1]) * k + 0.25                    # sheet height, along the roll's vertical axis
sel = np.sort(np.random.default_rng(0).choice(len(mp), args.n, replace=False))
S = MARGIN + (mp[sel, 0] - lo[0]) * k              # arc length from the sheet's left (inner) edge
Z = (mp[sel, 1] - (lo[1] + hi[1]) / 2) * k         # height on the sheet
G = grp[sel]
sizes = {g: int((grp == g).sum()) for g in set(grp.tolist())}
big = max((g for g in sizes if g >= 0), key=sizes.get)

BLUE = np.array((0.16, 0.36, 1.0)); BRASS = np.array((1.0, 0.55, 0.14)); GRAPH = np.array((0.24, 0.25, 0.29))   # as light, before the view transform
COL = np.array([BLUE if g == big else (GRAPH if g < 0 else BRASS) for g in G])

# ---------- the plate: [Fe/H] across, [alpha/M] up ----------
FE0, FE1, AL0, AL1 = -1.2, 0.5, -0.12, 0.40        # the plate's edges in dex
PW, PH, PY = 5.6, 7.7, -2.9                        # its size, and its place in front of the roll
def plate_x(v): return (np.asarray(v) - (FE0 + FE1) / 2) / (FE1 - FE0) * PW
def plate_z(v): return (np.asarray(v) - (AL0 + AL1) / 2) / (AL1 - AL0) * PH
P0 = np.stack([plate_x(FE[sel]), np.full(len(sel), PY), plate_z(AL[sel])], -1)
rng = np.random.default_rng(1)
rank = np.argsort(np.argsort(-AL[sel])) / (len(sel) - 1)   # 0 for the highest star on the plate
DELAY = 0.7 * rank + 0.3 * rng.random(len(sel))    # the stagger, in [0, 1]
BOW = 1.2 + 1.0 * rng.random(len(sel))             # how far towards the camera a star's path swings

# ---------- the timetable, in seconds of the first half; the second half is its mirror ----------
HOLD, TRAVEL, STAGGER = 0.7, 1.4, 1.0              # plate held; one star's journey; spread of the departures
UNROLL0, UNROLL1 = 2.9, 5.4                        # the sheet opens; the flat map then holds to the middle of the loop
FADE = (0.9, 2.1)                                  # plate gives way to sheet
T_MID = (NF - 1) / FPS / 2

def smooth(x):
    x = np.clip(x, 0.0, 1.0); return x * x * x * (x * (6 * x - 15) + 10)

def clock(t):
    return (0.5 - abs((t % 1.0 if t < 1 else 0.0) - 0.5)) * 2 * T_MID   # seconds, folded at the middle of the loop

# ---------- the sheet: a loose Archimedean roll about a vertical axis ----------
R0, B = 0.40, 0.15                                 # inner radius, and turn spacing over 2 pi (about 1.5 turns)
SS = np.linspace(0, L, 2401)                       # arc length from the inner edge
KAP = 1 / np.sqrt(R0 ** 2 + 2 * B * SS)
WF = 0.60                                          # width of the bend's soft front

def centreline(p):
    """Plan view (x, y) of the sheet's profile at arc lengths SS, for unroll progress p. The bending is released
    from the outer edge inwards, like a carpet unrolling, so arc length is kept at every stage."""
    front = (L + 3 * WF) * (1 - p) - 6 * WF * p
    bend = 1 / (1 + np.exp(-(front - SS) / WF))  # 1 where the sheet is still rolled, 0 where it lies flat
    kap = KAP * bend
    cum = np.concatenate([[0], np.cumsum((kap[1:] + kap[:-1]) / 2 * np.diff(SS))])
    th = cum - cum[-1]                             # tangent angle, zero at the outer edge
    dz, dy = np.cos(th), np.sin(th); ds = np.diff(SS)
    z = np.concatenate([[0], np.cumsum((dz[1:] + dz[:-1]) / 2 * ds)])
    y = np.concatenate([[0], np.cumsum((dy[1:] + dy[:-1]) / 2 * ds)])
    z -= z.mean(); y -= y.mean()
    return z, y

TILT = math.radians(float(os.environ.get('SF_TILT', '3')))    # the roll leans its top towards the camera
LEAN = [0.0]                                       # the sheet's current lean, in radians

def tilt(pts):
    c, n = math.cos(LEAN[0]), math.sin(LEAN[0]); x, y, z = pts.T
    return np.stack([x, y * c - z * n, y * n + z * c], -1)

def place(s, z, cx, cy):
    return tilt(np.stack([np.interp(s, SS, cx), np.interp(s, SS, cy), z], -1))

# ---------- scene ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = args.samples; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
if os.environ.get('CYCLES_DEVICE') == 'GPU':
    pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'CUDA'; pr.get_devices()
    for dv in pr.devices: dv.use = dv.type == 'CUDA'
    sc.cycles.device = 'GPU'; sc.cycles.denoising_use_gpu = True
sc.cycles.seed = 7; sc.cycles.use_animated_seed = False; sc.cycles.max_bounces = 4; sc.cycles.glossy_bounces = 2; sc.cycles.transparent_max_bounces = 16
sc.render.use_persistent_data = True
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

FADERS = {'plate': [], 'sheet': []}
def fades(m, who):
    """Put a mix with transparency before the output of a material, so that it can be faded."""
    nt = m.node_tree; out = nt.nodes['Material Output']; src = out.inputs['Surface'].links[0].from_socket
    mx = nt.nodes.new('ShaderNodeMixShader'); tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(src, mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
    FADERS[who].append(mx.inputs['Fac']); return m

def link(ob): bpy.context.collection.objects.link(ob); return ob

# points: one octahedron per star in a single mesh
OCT = np.array([(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)], float)
FACES = ((0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5))
RAD = np.where(G < 0, 0.026, 0.032)
bm = bmesh.new()
for i in range(len(S)):
    vs = [bm.verts.new((0, 0, 0)) for _ in range(6)]
    for f in FACES: bm.faces.new([vs[j] for j in f])
me = bpy.data.meshes.new('stars'); bm.to_mesh(me); bm.free()
col_attr = me.color_attributes.new('col', 'FLOAT_COLOR', 'POINT')
stars = link(bpy.data.objects.new('stars', me)); me.materials.append(vcol_emission('stars', 1.5))
col_attr.data.foreach_set('color', np.concatenate([np.repeat(COL, 6, 0), np.ones((len(COL) * 6, 1))], 1).ravel())
OFFS = (OCT[None, :, :] * RAD[:, None, None]).reshape(-1, 3)
ON_PLATE = 0.75                                    # a star is drawn smaller on the plate, so that the two ridges keep their density

# sheet: a grid of faint glass
NU, NV = 300, 16
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
sheet = link(bpy.data.objects.new('sheet', sme)); sme.materials.append(fades(glass('glass'), 'sheet'))
GU, GV = np.meshgrid(us, vz)

# hairlines: rulings (vertical) and level lines (horizontal) of the sheet, plus its edge
def curve_obj(name, splines, depth, mat):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = depth; cu.bevel_resolution = 1
    for npts in splines:
        sp = cu.splines.new('POLY'); sp.points.add(npts - 1)
    ob = link(bpy.data.objects.new(name, cu)); cu.materials.append(mat); return ob
RUL = np.linspace(0, L, 10)[1:-1]; LEV = np.linspace(-HZ / 2, HZ / 2, 7)[1:-1]; NL = 400
lines = curve_obj('lines', [2] * len(RUL) + [NL] * len(LEV), 0.006, fades(emission('lines', (0.42, 0.52, 0.70), 0.4), 'sheet'))
edge = curve_obj('edge', [2, 2, NL, NL], 0.009, fades(emission('edge', (0.45, 0.62, 1.0), 0.9), 'sheet'))
SL = np.linspace(0, L, NL)

def set_spline(sp, pts):
    pts = tilt(np.asarray(pts, float))
    sp.points.foreach_set('co', np.concatenate([pts, np.ones((len(pts), 1))], 1).ravel())

# the plate: faint glass, a frame, and rules at round values of the two abundances
pme = bpy.data.meshes.new('plate')
pme.from_pydata([(-PW / 2, PY, -PH / 2), (PW / 2, PY, -PH / 2), (PW / 2, PY, PH / 2), (-PW / 2, PY, PH / 2)], [], [(0, 1, 2, 3)])
link(bpy.data.objects.new('plate', pme)); pme.materials.append(fades(glass('pglass'), 'plate'))
RFE, RAL = (-1.0, -0.5, 0.0), (0.0, 0.1, 0.2, 0.3)
prules = curve_obj('prules', [2] * (len(RFE) + len(RAL)), 0.006, fades(emission('prules', (0.42, 0.52, 0.70), 0.4), 'plate'))
pframe = curve_obj('pframe', [5], 0.009, fades(emission('pframe', (0.45, 0.62, 1.0), 0.9), 'plate'))
def flat_spline(sp, pts): sp.points.foreach_set('co', np.concatenate([np.array(pts, float), np.ones((len(pts), 1))], 1).ravel())
for i, v in enumerate(RFE): x = float(plate_x(v)); flat_spline(prules.data.splines[i], [(x, PY, -PH / 2), (x, PY, PH / 2)])
for i, v in enumerate(RAL):
    z = float(plate_z(v)); flat_spline(prules.data.splines[len(RFE) + i], [(-PW / 2, PY, z), (PW / 2, PY, z)])
flat_spline(pframe.data.splines[0], [(-PW / 2, PY, -PH / 2), (PW / 2, PY, -PH / 2), (PW / 2, PY, PH / 2), (-PW / 2, PY, PH / 2), (-PW / 2, PY, -PH / 2)])

# stage
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.003, 0.0035, 0.005, 1)
fm = bpy.data.materials.new('floor'); fm.use_nodes = True; bs = fm.node_tree.nodes['Principled BSDF']
bs.inputs['Base Color'].default_value = (0.006, 0.007, 0.009, 1); bs.inputs['Roughness'].default_value = 0.2
fme = bpy.data.meshes.new('floor'); fme.from_pydata([(-60, -60, 0), (60, -60, 0), (60, 60, 0), (-60, 60, 0)], [], [(0, 1, 2, 3)])
fl = link(bpy.data.objects.new('floor', fme)); fl.location.z = -HZ / 2 - 0.6; fme.materials.append(fm)
ld = bpy.data.lights.new('area', 'AREA'); ld.energy = 60; ld.size = 6; ld.color = (0.75, 0.85, 1.0)
lt = link(bpy.data.objects.new('area', ld)); lt.location = (-3, -4, 7); lt.rotation_euler = (0.6, -0.3, 0)
sc.use_nodes = True; ct = sc.node_tree
gl_ = ct.nodes.new('CompositorNodeGlare'); gl_.glare_type = 'FOG_GLOW'; gl_.quality = 'HIGH'; gl_.size = 6; gl_.threshold = 0.6; gl_.mix = -0.6
ct.links.new(ct.nodes['Render Layers'].outputs['Image'], gl_.inputs['Image']); ct.links.new(gl_.outputs['Image'], ct.nodes['Composite'].inputs['Image'])

cd = bpy.data.cameras.new('cam'); cd.lens = 40; cd.dof.use_dof = True; cd.dof.aperture_fstop = 8.0
cam = link(bpy.data.objects.new('cam', cd)); sc.camera = cam
from mathutils import Vector
LOOK = Vector((0.0, 0.0, 0.12))
CAM_D, CAM_H, CAM_AZ, CAM_BACK = (float(v) for v in os.environ.get('SF_CAM', '19.5 2.2 14 3.5').split())

def pose(t):
    now = clock(t)
    q = smooth((now - HOLD - STAGGER * DELAY) / TRAVEL)   # each star's own progress from plate to sheet
    p = float(smooth((now - UNROLL0) / (UNROLL1 - UNROLL0)))
    mid = float(smooth((now - HOLD) / (HOLD + TRAVEL)))
    arc = mid * (1 - p)                                   # 0 at the plate and at the map, 1 at the roll
    LEAN[0] = TILT * arc
    cx, cy = centreline(p)
    P = P0 + (place(S, Z, cx, cy) - P0) * q[:, None]
    P[:, 1] -= BOW * np.sin(np.pi * q)
    me.vertices.foreach_set('co', (np.repeat(P, 6, 0) + OFFS * np.repeat(ON_PLATE + (1 - ON_PLATE) * q, 6)[:, None]).ravel()); me.update()
    sme.vertices.foreach_set('co', place(GU.ravel(), GV.ravel(), cx, cy).ravel()); sme.update()
    ex, ey = np.interp(SL, SS, cx), np.interp(SL, SS, cy)
    sp = lines.data.splines
    for i, u in enumerate(RUL):
        x, y = np.interp(u, SS, cx), np.interp(u, SS, cy); set_spline(sp[i], np.array([(x, y, -HZ / 2), (x, y, HZ / 2)]))
    for j, z in enumerate(LEV): set_spline(sp[len(RUL) + j], np.stack([ex, ey, np.full(NL, z)], -1))
    se = edge.data.splines
    for j, i in ((0, 0), (1, -1)): set_spline(se[j], np.array([(cx[i], cy[i], -HZ / 2), (cx[i], cy[i], HZ / 2)]))
    set_spline(se[2], np.stack([ex, ey, np.full(NL, -HZ / 2)], -1)); set_spline(se[3], np.stack([ex, ey, np.full(NL, HZ / 2)], -1))
    lines.data.update_tag(); edge.data.update_tag()
    f = float(smooth((now - FADE[0]) / (FADE[1] - FADE[0])))
    for s_ in FADERS['plate']: s_.default_value = 1 - f
    for s_ in FADERS['sheet']: s_.default_value = f
    a = math.radians(CAM_AZ * math.sin(math.pi / 2 * arc) ** 2)   # the camera swings round the roll and back
    D = CAM_D + CAM_BACK * arc                            # and stands back while the sheet is rolled, which stands nearer
    cam.location = Vector((LOOK.x + D * math.sin(a), -D * math.cos(a), CAM_H))
    cam.rotation_euler = (LOOK - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cd.dof.focus_distance = (Vector((0, 0, 0)) - cam.location).length
    bpy.context.view_layer.update()

if args.still:
    for t in args.still:
        pose(t); sc.render.filepath = os.path.join(args.out, 'still_%03d.png' % round(t * 1000))
        bpy.ops.render.render(write_still=True)
if args.frames:
    for f in range(*args.frames):
        pose(f / (NF - 1)); sc.render.filepath = os.path.join(args.out, 'f_%04d.png' % f)
        bpy.ops.render.render(write_still=True)
