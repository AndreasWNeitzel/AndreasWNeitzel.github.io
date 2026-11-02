"""The research pipeline as one dark physical scene for the Research page (Blender, Cycles). Seven stations stand six
units apart on a black reflective floor under faint haze, joined by one amber thread, and the camera dollies past them
from left to right over a twelve second loop.

Stations, left to right:
  1. Gaia, the spacecraft model from blender_gaia.py at 1.2 units across, turning slowly. Schematic proportions.
  2. The XP spectrum: the 343 sampled fluxes of a real Gaia DR3 XP spectrum of a red giant, drawn as a line of ivory
     light standing on the floor with a faint fill beneath it. Real data.
  3. Asteroseismology: the oscillation power spectrum of KIC 6144777 from twelve quarters of Kepler long cadence
     photometry, each filament one bin of the smoothed spectrum divided by its fitted background, the tall peaks in
     amber. Real data.
  4. JANUS: seven glass panels with the activations of a deep network as points, the training pass sweeping through
     them once per loop. The activations are schematic; the first panel carries the real XP spectrum.
  5. Labels: six bars of light from ivory to blue with square nodes, a schematic bar of six values.
  6. Starfold: the 9,242 stars of the recorded Starfold run on the APOGEE table, each at its place on the
     two-dimensional map, lying flat on the floor, cool blue for the metal poor group, warm for the metal rich one,
     grey where the run left the star unassigned. Real data.
  7. The Milky Way: about 60,000 points in a two-arm logarithmic spiral with an exponential density profile and a
     warm bulge, tilted sixty degrees. Schematic.

The loop closes with a one second crossfade: the camera is rendered thirty frames before the start and thirty after
the end, and the post step blends the two moving ends with Pillow, so the dolly never stops.

Usage (the bpy session):
  uv run --python 3.11 --with bpy==4.2.0 python blender_pipeline.py still:I OUT.png [--samples N] [--size WxH]
      [--spec SPEC.json] [--kep PSD.npz]      one frame at loop index I (0 to 359; -30 to 389 allowed)
      The XP fluxes and the Kepler spectrum default to figures/heroes/renders/pipeline/{xp_spec.json,kic6144777_psd.npz}.
  uv run --python 3.11 --with bpy==4.2.0 python blender_pipeline.py anim OUTDIR [...]
      all 420 frames (loop index -30 to 389) as OUTDIR/raw/r_####.png, Blender frame = index + 31
The post step (Pillow, no bpy):
  uv run --python 3.11 --with pillow --with numpy python blender_pipeline.py post OUTDIR
      writes OUTDIR/frames/f_0000.png to f_0389.png (360 dolly frames and 30 crossfade frames) and the poster."""
import json, math, os, random, sys
import numpy as np

mode, out = sys.argv[1], sys.argv[2]
def opt(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default
samples = int(opt('--samples', 24))
W, H = (int(v) for v in opt('--size', '1280x720').split('x'))
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..') + os.sep
DATA = os.path.join(ROOT, 'figures', 'heroes', 'renders', 'pipeline')
SPEC = opt('--spec', os.path.join(DATA, 'xp_spec.json')); KEP = opt('--kep', os.path.join(DATA, 'kic6144777_psd.npz'))

NLOOP, PRE, POST = 360, 30, 30          # loop frames, frames rendered before the start and after the end
def frame_of(i): return i + PRE + 1      # loop index to Blender frame

# ------------------------------------------------------------------------------------------------------ post step
if mode == 'post':
    from PIL import Image
    raw = os.path.join(out, 'raw'); frames = os.path.join(out, 'frames'); os.makedirs(frames, exist_ok=True)
    def load(i): return np.asarray(Image.open(os.path.join(raw, 'r_%04d.png' % frame_of(i))).convert('RGB'), dtype=np.float32)
    for i in range(NLOOP):
        Image.open(os.path.join(raw, 'r_%04d.png' % frame_of(i))).convert('RGB').save(os.path.join(frames, 'f_%04d.png' % i))
    for k in range(POST):
        t = (k + 1) / (POST + 1)
        im = (1 - t) * load(NLOOP + k) + t * load(-PRE + k)
        Image.fromarray(np.clip(im + 0.5, 0, 255).astype(np.uint8)).save(os.path.join(frames, 'f_%04d.png' % (NLOOP + k)))
    Image.open(os.path.join(frames, 'f_0120.png')).convert('RGB').save(os.path.join(out, 'pipeline.poster.webp'), quality=80)
    print('wrote', NLOOP + POST, 'frames to', frames); sys.exit(0)

import bpy, bmesh
from mathutils import Vector

random.seed(5); rng = np.random.default_rng(5)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
sc.cycles.max_bounces = 4; sc.cycles.diffuse_bounces = 1; sc.cycles.glossy_bounces = 2; sc.cycles.transparent_max_bounces = 14
sc.cycles.volume_bounces = 0; sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
sc.render.use_persistent_data = True
sc.cycles.use_denoising = opt('--denoise', '1') == '1'; sc.cycles.volume_step_rate = 2.0; sc.cycles.adaptive_threshold = 0.03; sc.cycles.adaptive_min_samples = 8; sc.cycles.volume_max_steps = 256
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'; sc.render.image_settings.color_depth = '8'
sc.render.fps = 30

def mix(a, b, t): return tuple(x + (y - x) * t for x, y in zip(a, b))
IVORY, BLUE, AMBER = (0.96, 0.92, 0.84), (0.45, 0.62, 1.0), (1.0, 0.55, 0.15)
COLD, WARM = (0.42, 0.62, 1.0), (1.0, 0.66, 0.32)
ICE, DIM, WHITE = (0.55, 0.78, 1.0), (0.10, 0.20, 0.38), (0.9, 0.93, 1.0)
SP = 6.0; SX = [k * SP for k in range(7)]           # station x positions
TZ = 0.85                                            # the thread's height

# ------------------------------------------------------------------------------------------------------ materials
def principled(name, base, metal=0.0, rough=0.4):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*base, 1); b.inputs['Metallic'].default_value = metal; b.inputs['Roughness'].default_value = rough; return m

def mat(name, base, metal=0.0, rough=0.4, noise_bump=0.0, nscale=9.0):
    # the Gaia materials: principled, with a noise bump for crinkled insulation
    m = principled(name, base, metal, rough); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    if noise_bump:
        tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = nscale; nz.inputs['Detail'].default_value = 8
        bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = noise_bump
        nt.links.new(tc.outputs['Object'], nz.inputs['Vector']); nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = rough * 0.5; mr.inputs['To Max'].default_value = rough * 1.6
        nt.links.new(nz.outputs['Fac'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], b.inputs['Roughness'])
    return m

def vcol_emission(name, strength, sample=False):
    # emission from the per-vertex colour attribute 'col'; the clouds of tiny emitters are not sampled as lights
    # (next event estimation over a million small triangles costs more than it gives), only found by bounces
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    if not sample: m.cycles.emission_sampling = 'NONE'
    a = nt.nodes.new('ShaderNodeAttribute'); a.attribute_name = 'col'
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Strength'].default_value = strength
    nt.links.new(a.outputs['Color'], e.inputs['Color']); nt.links.new(e.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface']); return m

def pass_emissive(base, boost, name='pe', width=0.7):
    # Emission from the vertex colour 'col', brightened where the training front passes. The front's x position is the
    # view layer property 'front', keyframed for the animation; the pass runs forward only here.
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); m.cycles.emission_sampling = 'NONE'
    N = nt.nodes.new; L = nt.links.new
    a = N('ShaderNodeAttribute'); a.attribute_name = 'col'
    fr = N('ShaderNodeAttribute'); fr.attribute_type = 'VIEW_LAYER'; fr.attribute_name = 'front'
    geo = N('ShaderNodeNewGeometry'); sep = N('ShaderNodeSeparateXYZ'); L(geo.outputs['Position'], sep.inputs[0])
    sub = N('ShaderNodeMath'); sub.operation = 'SUBTRACT'; L(sep.outputs['X'], sub.inputs[0]); L(fr.outputs['Fac'], sub.inputs[1])
    dv = N('ShaderNodeMath'); dv.operation = 'DIVIDE'; dv.inputs[1].default_value = width; L(sub.outputs[0], dv.inputs[0])
    sq = N('ShaderNodeMath'); sq.operation = 'MULTIPLY'; L(dv.outputs[0], sq.inputs[0]); L(dv.outputs[0], sq.inputs[1])
    ng = N('ShaderNodeMath'); ng.operation = 'MULTIPLY'; ng.inputs[1].default_value = -1.0; L(sq.outputs[0], ng.inputs[0])
    ex = N('ShaderNodeMath'); ex.operation = 'EXPONENT'; L(ng.outputs[0], ex.inputs[0])
    fwdc = N('ShaderNodeRGB'); fwdc.outputs[0].default_value = (*AMBER, 1)
    mc = N('ShaderNodeMix'); mc.data_type = 'RGBA'; L(ex.outputs[0], mc.inputs['Factor']); L(a.outputs['Color'], mc.inputs[6]); L(fwdc.outputs[0], mc.inputs[7])
    st = N('ShaderNodeMath'); st.operation = 'MULTIPLY_ADD'; st.inputs[1].default_value = boost; st.inputs[2].default_value = base; L(ex.outputs[0], st.inputs[0])
    e = N('ShaderNodeEmission'); L(mc.outputs[2], e.inputs['Color']); L(st.outputs[0], e.inputs['Strength'])
    L(e.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m

def pulse_emissive(color, base, boost, period, width, name='thread'):
    # The thread: constant amber emission with a brighter pulse every `period` units of x, all pulses sliding along
    # with the view layer property 'pulse' (floored modulo, so the pattern repeats and the loop closes).
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    N = nt.nodes.new; L = nt.links.new
    def M(op, a=None, b=None, c=None):
        n = N('ShaderNodeMath'); n.operation = op
        for k, v in enumerate((a, b, c)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[k].default_value = v
            else: L(v, n.inputs[k])
        return n.outputs[0]
    pu = N('ShaderNodeAttribute'); pu.attribute_type = 'VIEW_LAYER'; pu.attribute_name = 'pulse'
    geo = N('ShaderNodeNewGeometry'); sep = N('ShaderNodeSeparateXYZ'); L(geo.outputs['Position'], sep.inputs[0])
    d = M('SUBTRACT', sep.outputs['X'], pu.outputs['Fac'])
    d = M('FLOORED_MODULO', M('ADD', d, period / 2), period)
    d = M('DIVIDE', M('SUBTRACT', d, period / 2), width)
    g = M('EXPONENT', M('MULTIPLY', M('MULTIPLY', d, d), -1.0))
    s = M('MULTIPLY_ADD', g, boost, base)
    e = N('ShaderNodeEmission'); e.inputs['Color'].default_value = (*color, 1); L(s, e.inputs['Strength'])
    L(e.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m

# ------------------------------------------------------------------------------------------------------ geometry
class Mesh:
    # many small shapes in one mesh with a colour per vertex (bmesh, for a few thousand shapes)
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

class Cloud:
    """Points and tubes in one mesh, coloured through a loop colour layer 'col' (bmesh)."""
    def __init__(self): self.bm = bmesh.new(); self.cl = self.bm.loops.layers.color.new('col')
    def point(self, p, r, col):
        vs = [self.bm.verts.new(p + d * r) for d in (Vector((1,0,0)),Vector((-1,0,0)),Vector((0,1,0)),Vector((0,-1,0)),Vector((0,0,1)),Vector((0,0,-1)))]
        for f in ((0,2,4),(2,1,4),(1,3,4),(3,0,4),(2,0,5),(1,2,5),(3,1,5),(0,3,5)):
            face = self.bm.faces.new([vs[i] for i in f])
            for lp in face.loops: lp[self.cl] = (*col, 1)
    def tube(self, pts, r, col, sides=5):
        rings = []
        for i, p in enumerate(pts):
            t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
            u = t.cross(Vector((0, 0, 1))); u = u.normalized() if u.length > 1e-6 else Vector((1, 0, 0)); v = t.cross(u)
            rings.append([self.bm.verts.new(p + r * (math.cos(2*math.pi*k/sides) * u + math.sin(2*math.pi*k/sides) * v)) for k in range(sides)])
        cols = col if isinstance(col, list) else [col] * len(pts)
        for ri, (a, b) in enumerate(zip(rings[:-1], rings[1:])):
            for k in range(sides):
                face = self.bm.faces.new((a[k], a[(k+1) % sides], b[(k+1) % sides], b[k]))
                for lp in face.loops:
                    lp[self.cl] = (*cols[ri if lp.vert in a else ri + 1], 1)
    def obj(self, mat, name='cloud'):
        me = bpy.data.meshes.new(name); self.bm.to_mesh(me); self.bm.free()
        ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); ob.data.materials.append(mat); return ob

def points_obj(P, R, C, mat, name):
    """Tens of thousands of points as octahedra in one mesh, built with numpy (P (n,3), R (n,), C (n,3))."""
    n = len(P); D = np.array([[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]], float)
    V = (P[:, None, :] + R[:, None, None] * D[None]).reshape(-1, 3)
    F = np.array([(0,2,4),(2,1,4),(1,3,4),(3,0,4),(2,0,5),(1,2,5),(3,1,5),(0,3,5)])
    faces = (np.arange(n)[:, None, None] * 6 + F[None]).reshape(-1, 3); nf = len(faces)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V)); me.vertices.foreach_set('co', V.ravel())
    me.loops.add(3 * nf); me.loops.foreach_set('vertex_index', faces.ravel())
    me.polygons.add(nf); me.polygons.foreach_set('loop_start', np.arange(nf) * 3); me.polygons.foreach_set('loop_total', np.full(nf, 3))
    me.update(); me.validate()
    at = me.color_attributes.new('col', 'FLOAT_COLOR', 'POINT')
    rgba = np.concatenate([np.repeat(C, 6, axis=0), np.ones((6 * n, 1))], 1); at.data.foreach_set('color', rgba.ravel())
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); ob.data.materials.append(mat); return ob

def curve_pts(a, b, n=24, bow=Vector((0, 0, 0))):
    out = []
    for k in range(n + 1):
        t = k / n; s = t * t * (3 - 2 * t)
        out.append(Vector((a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * s, a.z + (b.z - a.z) * s)) + bow * math.sin(math.pi * t))
    return out

def thread_y(x): return 0.22 * math.sin(2 * math.pi * x / SP)        # the thread's sway, zero at every station

# ------------------------------------------------------------------------------------------------------ stage
def world(color=(0.002, 0.0025, 0.004), haze=0.0, boxed=False):
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (*color, 1)
    if haze and not boxed:
        v = w.node_tree.nodes.new('ShaderNodeVolumePrincipled'); v.inputs['Density'].default_value = haze; v.inputs['Anisotropy'].default_value = 0.3
        w.node_tree.links.new(v.outputs['Volume'], w.node_tree.nodes['World Output'].inputs['Volume'])
    elif haze:
        # the haze lives in a box around the stations rather than in the world, so rays that leave it stop marching
        m = bpy.data.materials.new('haze'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
        v = nt.nodes.new('ShaderNodeVolumePrincipled'); v.inputs['Density'].default_value = haze; v.inputs['Anisotropy'].default_value = 0.3
        nt.links.new(v.outputs['Volume'], nt.nodes['Material Output'].inputs['Volume'])
        bpy.ops.mesh.primitive_cube_add(size=1, location=(18, -1.5, 2.5)); box = bpy.context.object; box.scale = (52, 13, 5.2); box.data.materials.append(m)
        box.visible_shadow = False

def floor(z, size=160, base=(0.006, 0.007, 0.009), rough=0.2):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(18, 0, z)); f = bpy.context.object; f.data.materials.append(principled('floor', base, 0.6, rough)); return f

def bloom(size=7, mix_=-0.6, mist=0.035):
    # faint haze from the mist pass (a dim blue grey added with depth), then a soft glow
    sc.use_nodes = True; ct = sc.node_tree; rl = ct.nodes['Render Layers']; comp = ct.nodes['Composite']
    src = rl.outputs['Image']
    if mist:
        sc.view_layers[0].use_pass_mist = True; ws = sc.world.mist_settings; ws.start = 3.0; ws.depth = 22.0; ws.falloff = 'LINEAR'
        mm = ct.nodes.new('CompositorNodeMath'); mm.operation = 'MULTIPLY'; mm.inputs[1].default_value = mist; ct.links.new(rl.outputs['Mist'], mm.inputs[0])
        mx = ct.nodes.new('CompositorNodeMixRGB'); mx.blend_type = 'ADD'; ct.links.new(mm.outputs[0], mx.inputs[0]); ct.links.new(src, mx.inputs[1])
        mx.inputs[2].default_value = (0.42, 0.5, 0.66, 1); src = mx.outputs[0]
    g = ct.nodes.new('CompositorNodeGlare'); g.glare_type = 'FOG_GLOW'; g.quality = 'HIGH'; g.size = size; g.threshold = 0.6; g.mix = mix_
    ct.links.new(src, g.inputs['Image']); ct.links.new(g.outputs['Image'], comp.inputs['Image'])

HAZE = float(opt('--haze', 0.0))   # volume haze is optional; by default the haze is the cheap mist below
floor(0.0); world(haze=HAZE, boxed=opt('--hazebox', '0') == '1'); bloom(7, -0.6)

# ---- the thread: one tube along x through every station, with pulses sliding along it
thr = Cloud()
xs = np.linspace(-3.0, 40.0, 700)
thr.tube([Vector((x, thread_y(x), TZ + 0.04 * math.sin(2 * math.pi * x / SP + 1.0))) for x in xs], 0.012, AMBER, sides=6)
thr.obj(pulse_emissive(AMBER, 1.6, 7.0, SP, 0.45), 'thread')

# ---- 1. Gaia: the model from blender_gaia.py, 1.2 units across
def build_gaia(root, scale):
    GOLD = mat('gold', (0.92, 0.62, 0.22), metal=1.0, rough=0.24, noise_bump=0.22, nscale=6.0)
    MLI = mat('mli', (0.74, 0.76, 0.8), metal=0.8, rough=0.34, noise_bump=0.06, nscale=3.0)
    TENT = mat('tent', (0.03, 0.032, 0.038), metal=0.05, rough=0.7, noise_bump=0.03, nscale=2.0)
    FRAME = mat('frame', (0.55, 0.57, 0.6), metal=0.9, rough=0.35)
    CELL = mat('cell', (0.03, 0.06, 0.16), metal=0.3, rough=0.12)
    HOLE = mat('hole', (0.0, 0.0, 0.0), rough=1.0)
    RIMG = mat('rim', (0.85, 0.6, 0.25), metal=1.0, rough=0.25)
    def obj_from_bm(bm, name, material):
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); ob.data.materials.append(material)
        for p in ob.data.polygons: p.use_smooth = False
        return ob
    parts = []
    r0, r1, k = 1.95, 5.1, 12
    for i in range(k):
        a0, a1 = 2 * math.pi * i / k + 0.012, 2 * math.pi * (i + 1) / k - 0.012
        z = lambda r: -0.32 * (r - r0) / (r1 - r0)
        bm = bmesh.new()
        vs = [bm.verts.new((r * math.cos(a), r * math.sin(a), z(r) + dz)) for dz in (0.0, -0.04) for (r, a) in ((r0, a0), (r1, a0), (r1, a1), (r0, a1))]
        bm.faces.new(vs[:4]); bm.faces.new(vs[4:][::-1])
        for j in range(4): bm.faces.new((vs[j], vs[(j + 1) % 4], vs[4 + (j + 1) % 4], vs[4 + j])[::-1])
        parts.append(obj_from_bm(bm, f'panel{i}', MLI))
        bm = bmesh.new(); rr = r0 + (r1 - r0) * 0.7
        vs = [bm.verts.new((r * math.cos(a), r * math.sin(a), z(r) - 0.045)) for (r, a) in ((r0, a0), (rr, a0), (rr, a1), (r0, a1))]
        bm.faces.new(vs[::-1]); parts.append(obj_from_bm(bm, f'cells{i}', CELL))
        for (ra, aa, rb, ab, w) in ((r0, a0 - 0.012, r1, a0 - 0.012, 0.045), (r1, a0, r1, a1, 0.05)):
            bm = bmesh.new()
            p0 = Vector((ra * math.cos(aa), ra * math.sin(aa), z(ra) + 0.02)); p1 = Vector((rb * math.cos(ab), rb * math.sin(ab), z(rb) + 0.02))
            d = (p1 - p0).normalized(); n = d.cross(Vector((0, 0, 1))).normalized() * w
            up = Vector((0, 0, w))
            q = [p0 + n, p1 + n, p1 - n, p0 - n]; qs = [bm.verts.new(v) for v in q] + [bm.verts.new(v + up) for v in q]
            bm.faces.new(qs[4:]); bm.faces.new(qs[:4][::-1])
            for j in range(4): bm.faces.new((qs[j], qs[(j + 1) % 4], qs[4 + (j + 1) % 4], qs[4 + j]))
            parts.append(obj_from_bm(bm, 'strut', FRAME))
        rm = r0 + (r1 - r0) * 0.55
        bm = bmesh.new(); pa = Vector((rm * math.cos(a0), rm * math.sin(a0), z(rm) + 0.02)); pb = Vector((rm * math.cos(a1), rm * math.sin(a1), z(rm) + 0.02))
        d = (pb - pa).normalized(); n = Vector((d.y, -d.x, 0)) * 0.03; up = Vector((0, 0, 0.03))
        q = [pa + n, pb + n, pb - n, pa - n]; qs = [bm.verts.new(v) for v in q] + [bm.verts.new(v + up) for v in q]
        bm.faces.new(qs[4:]); [bm.faces.new((qs[j], qs[(j + 1) % 4], qs[4 + (j + 1) % 4], qs[4 + j])) for j in range(4)]
        parts.append(obj_from_bm(bm, 'batten', FRAME))
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=1.95, depth=1.1, location=(0, 0, 0.45)); sm = bpy.context.object; sm.rotation_euler[2] = math.pi / 6; sm.data.materials.append(GOLD); parts.append(sm)
    for zz in (-0.08, 0.98):
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=1.99, depth=0.06, location=(0, 0, zz)); f = bpy.context.object; f.rotation_euler[2] = math.pi / 6; f.data.materials.append(FRAME); parts.append(f)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=1.78, depth=2.15, location=(0, 0, 2.1)); tent = bpy.context.object; tent.data.materials.append(TENT); parts.append(tent)
    bm = bmesh.new(); bm.from_mesh(tent.data)
    for v in bm.verts:
        a = math.atan2(v.co.y, v.co.x); s = 1 + 0.004 * math.cos(24 * a); v.co.x *= s; v.co.y *= s
    bm.to_mesh(tent.data); bm.free()
    for pl in tent.data.polygons: pl.use_smooth = True
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=16, radius=1.78, location=(0, 0, 3.17)); dome = bpy.context.object; dome.scale[2] = 0.12; dome.data.materials.append(TENT); parts.append(dome)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.78, minor_radius=0.035, location=(0, 0, 3.17)); t = bpy.context.object; t.data.materials.append(FRAME); parts.append(t)
    for ac in (math.radians(-70), math.radians(-70 + 106.5)):
        for (w, h, m, off) in ((0.95, 0.75, RIMG, 0.02), (0.82, 0.62, HOLE, 0.035)):
            bpy.ops.mesh.primitive_plane_add(size=1, location=((1.78 + off) * math.cos(ac), (1.78 + off) * math.sin(ac), 2.35))
            p = bpy.context.object; p.scale = (w, h, 1); p.rotation_euler = (math.pi / 2, 0, ac + math.pi / 2); p.data.materials.append(m); parts.append(p)
    for j in range(12):
        a = 2 * math.pi * j / 12
        bpy.ops.mesh.primitive_cube_add(size=1, location=(1.2 * math.cos(a), 1.2 * math.sin(a), -0.3)); c = bpy.context.object; c.scale = (0.35, 0.12, 0.08); c.rotation_euler[2] = a; c.data.materials.append(FRAME); parts.append(c)
    for p in parts: p.parent = root
    root.scale = (scale, scale, scale)

gaia = bpy.data.objects.new('gaia', None); bpy.context.collection.objects.link(gaia)
gaia.location = (SX[0], 0, TZ + 0.12); gaia.rotation_mode = 'ZXY'; gaia.rotation_euler = (math.radians(32), 0, 0)   # spins about its own axis, then tilts toward the camera
build_gaia(gaia, 1.2 / 10.2)
# ---- 2. the XP spectrum: a line of ivory light standing on the floor, a faint fill beneath it (real data)
spec = json.load(open(SPEC)); n = len(spec); mx, mn = max(spec), min(spec); fn = [(v - mn) / (mx - mn) for v in spec]
line = Cloud(); fill = Mesh()
pts = [Vector((SX[1] - 1.0 + 2.0 * k / (n - 1), 0.0, 0.10 + 1.35 * fn[k])) for k in range(n)]
line.tube(pts, 0.013, IVORY, sides=6)
for k in range(0, n, 2): line.point(pts[k], 0.016, IVORY)
line.obj(vcol_emission('xp_line', 4.0, sample=True), 'xp_line')
for k in range(n):
    x = pts[k].x; fill.box((x - 0.0028, -0.004, 0.0), (x + 0.0028, 0.004, pts[k].z - 0.02), (0.012, 0.011, 0.01), mix((0.012, 0.011, 0.01), IVORY, 0.16))
fill.box((SX[1] - 1.05, -0.01, 0.0), (SX[1] + 1.05, 0.01, 0.012), (0.06, 0.057, 0.05), (0.2, 0.19, 0.17))
fill.obj(vcol_emission('xp_fill', 0.6), 'xp_fill')

# ---- 3. asteroseismology: the Kepler power spectrum of KIC 6144777 as filaments, 2 units wide (real data)
d = np.load(KEP); f, p = d['f'], d['p']
keep = (f > 70) & (f < 190); f, p = f[keep], p[keep]
kk = 9; ps = np.convolve(p, np.ones(kk) / kk, 'same')
lf_, lp = np.log(f), np.log(ps); m_ = (f < 95) | (f > 175)
b1, b0 = np.polyfit(lf_[m_], lp[m_], 1); snr = ps / np.exp(b0 + b1 * lf_)
nb = 420; edges = np.linspace(f.min(), f.max(), nb + 1); idx = np.digitize(f, edges) - 1
hb = np.array([snr[idx == i].max() if np.any(idx == i) else 0 for i in range(nb)])
hb = np.clip(hb / np.percentile(hb, 99.5), 0, 1.15)
M = Mesh(); xs = np.linspace(SX[2] - 1.0, SX[2] + 1.0, nb)
for x, v in zip(xs, hb):
    y = 0.08 * math.sin((x - SX[2]) * 1.6); h = 0.03 + 1.25 * v ** 1.3; t = min(1.0, v ** 0.8)
    top = mix((0.16, 0.26, 0.6), mix(AMBER, (1.0, 0.7, 0.35), t), min(1, t * 1.6)); bot = (0.01, 0.012, 0.03)
    M.box((x - 0.0035, y - 0.0035, 0), (x + 0.0035, y + 0.0035, h), bot, top)
    if v > 0.35: M.octa((x, y, h), 0.014, top)
M.obj(vcol_emission('psd', 1.3), 'psd')

# ---- 4. JANUS: seven glass panels of activations, 2.4 units tall, the training pass sweeping through (schematic;
#      the first panel carries the real XP spectrum)
GLASS = bpy.data.materials.new('glass'); GLASS.use_nodes = True; gnt = GLASS.node_tree; gnt.nodes.remove(gnt.nodes['Principled BSDF'])
tr = gnt.nodes.new('ShaderNodeBsdfTransparent'); gl_ = gnt.nodes.new('ShaderNodeBsdfGlossy'); gl_.inputs['Roughness'].default_value = 0.05
tint = gnt.nodes.new('ShaderNodeEmission'); tint.inputs['Color'].default_value = (0.2, 0.4, 0.9, 1); tint.inputs['Strength'].default_value = 0.012
m1 = gnt.nodes.new('ShaderNodeMixShader'); m1.inputs['Fac'].default_value = 0.04; m2 = gnt.nodes.new('ShaderNodeAddShader')
gnt.links.new(tr.outputs[0], m1.inputs[1]); gnt.links.new(gl_.outputs[0], m1.inputs[2]); gnt.links.new(m1.outputs[0], m2.inputs[0]); gnt.links.new(tint.outputs[0], m2.inputs[1])
gnt.links.new(m2.outputs[0], gnt.nodes['Material Output'].inputs['Surface'])
dots = Cloud(); lines = Cloud(); jthr = Cloud()
S = 0.5; XS = 0.25; JX0 = SX[3] - 1.55; JZ = 1.3
sheets = [(0.0, 1.0, 110, 70), (2.4, 1.12, 96, 96), (4.7, 1.04, 84, 84), (6.9, 0.92, 70, 70), (9.0, 0.76, 54, 54), (10.9, 0.55, 36, 36), (12.5, 0.32, 16, 16)]
for si, (xo, scl, nx, ny) in enumerate(sheets):
    x = JX0 + xo * XS; w = h = 4.8 * scl * S
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x + 0.01, 0, JZ)); g = bpy.context.object; g.scale = (h + 0.12, w + 0.12, 1); g.rotation_euler = (0, math.pi / 2, 0); g.data.materials.append(GLASS)
    e = (w + 0.12) / 2; f_ = (h + 0.12) / 2
    corners = [Vector((x, -e, JZ - f_)), Vector((x, e, JZ - f_)), Vector((x, e, JZ + f_)), Vector((x, -e, JZ + f_)), Vector((x, -e, JZ - f_))]
    lines.tube(corners, 0.003, (0.35, 0.6, 1.0), sides=4)
    blobs = [(random.random(), random.random(), 0.03 + 0.05 * random.random(), 0.4 + 0.6 * random.random()) for _ in range(9 + si)]
    for i in range(nx):
        for j in range(ny):
            uu, vv = i / (nx - 1), j / (ny - 1)
            y = (uu - 0.5) * w; z = JZ + (vv - 0.5) * h
            if si == 0:
                k = int(uu * (n - 1)); ln = math.exp(-((vv - (0.12 + 0.76 * fn[k])) ** 2) / 0.0006)
                v = 0.05 + 0.95 * ln
            else:
                v = 0.04 + sum(a_ * math.exp(-((uu - bx) ** 2 + (vv - by) ** 2) / (2 * bs * bs)) for bx, by, bs, a_ in blobs)
                v = min(1.0, v) ** 1.4
            if v < 0.06 and ((i * 73856093) ^ (j * 19349663) ^ (si * 83492791)) % 1000 < 550: continue
            col = mix(DIM, ICE, min(1, v * 1.3))
            if si > 0 and v > 0.82: col = mix(ICE, AMBER, (v - 0.82) / 0.18)
            if si == 0 and v > 0.5: col = mix(ICE, WHITE, 0.6)
            dots.point(Vector((x, y, z)), (0.007 + 0.012 * v) * S, col)
tr_rng = random.Random(77)
def anchor(si):
    xo, scl, nx, ny = sheets[si]; w = 4.8 * scl * S
    return Vector((JX0 + xo * XS, (tr_rng.random() - 0.5) * w * 0.45, JZ + (tr_rng.random() - 0.5) * w * 0.45))
for si in range(len(sheets) - 1):
    for _ in range(8):
        jthr.tube(curve_pts(anchor(si), anchor(si + 1), 20), 0.0009, (0.5, 0.75, 1.0), sides=4)
dots.obj(pass_emissive(2.6, 5.0, 'pe_dots', width=0.3), 'janus_dots'); lines.obj(vcol_emission('edges', 0.9), 'janus_edges'); jthr.obj(pass_emissive(0.5, 9.0, 'pe_thr', width=0.28), 'janus_threads')
JX1 = JX0 + sheets[-1][0] * XS

# ---- 5. labels: six bars of light, ivory to blue, with square nodes (schematic)
L = Mesh(); heights = [1.25, 0.8, 1.55, 1.0, 0.6, 1.35]
for k, hk in enumerate(heights):
    x = SX[4] + (k - 2.5) * 0.34; c = mix(IVORY, (0.32, 0.52, 1.0), (k / 5) ** 0.7)
    L.box((x - 0.016, -0.016, 0.0), (x + 0.016, 0.016, hk), mix((0.02, 0.02, 0.03), c, 0.25), c)
    s = 0.045; L.box((x - s, -s, hk), (x + s, s, hk + 2 * s), c, c)
    L.box((x - 0.09, -0.09, 0.0), (x + 0.09, 0.09, 0.006), (0.01, 0.012, 0.02), mix((0.01, 0.012, 0.02), c, 0.3))
L.box((SX[4] - 1.0, -0.006, 0.0), (SX[4] + 1.0, 0.006, 0.01), (0.04, 0.045, 0.06), (0.12, 0.14, 0.2))
L.obj(vcol_emission('labels', 1.0), 'labels')

# ---- 6. Starfold: the 9,242 stars of the recorded APOGEE run on their map, flat on the floor (real data)
meta = json.load(open(ROOT + 'assets/data/starfold/apogee_run.json')); raw = open(ROOT + 'assets/data/starfold/apogee_run.bin', 'rb').read()
A = {a['name']: a for a in meta['arrays']}
def arr(nm):
    a = A[nm]; dt = np.dtype(a['dtype']).newbyteorder('<'); cnt = int(np.prod(a['shape']))
    return np.frombuffer(raw, dt, count=cnt, offset=a['offset']).reshape(a['shape'])
mp, feat, grp = arr('map').astype(float), arr('features').astype(float), arr('group').astype(int)
lo, hi = np.percentile(mp, 1, axis=0), np.percentile(mp, 99, axis=0)
mp = (mp - (lo + hi) / 2) / (hi - lo).max() * 3.0
fe = feat[:, 0]; gfe = {g: np.median(fe[grp == g]) for g in set(grp) if g >= 0}
order = sorted(gfe, key=gfe.get); rank = {g: k / max(1, len(order) - 1) for k, g in enumerate(order)}
P = np.column_stack([SX[5] + mp[:, 0], mp[:, 1], np.full(len(mp), 0.02)])
C = np.array([mix(COLD, WARM, rank[g]) if g >= 0 else (0.16, 0.17, 0.2) for g in grp])
R = np.where(grp >= 0, 0.008, 0.0055)
points_obj(P, R, C, vcol_emission('stars', 0.85), 'starfold')

# ---- 7. the Milky Way: two-arm logarithmic spiral, exponential disc, warm bulge, tilted 60 degrees (schematic)
NG = 60000; nb_ = int(NG * 0.18); nd = NG - nb_
r = rng.exponential(0.38, nd); r = r[r < 1.5]
while len(r) < nd: r = np.concatenate([r, rng.exponential(0.38, nd)]); r = r[r < 1.5]
r = r[:nd]
arm = rng.integers(0, 2, nd); bpitch = 0.28
th_arm = np.log(np.maximum(r, 0.05) / 0.12) / bpitch + arm * np.pi
smooth = rng.random(nd) < 0.3
th = np.where(smooth, rng.uniform(0, 2 * np.pi, nd), th_arm + rng.normal(0, 0.22 + 0.1 * r, nd))
zz = rng.normal(0, 0.012, nd) * (1 + r)
G = np.column_stack([r * np.cos(th), r * np.sin(th), zz])
rb = np.abs(rng.normal(0, 0.16, nb_)); tb = rng.uniform(0, 2 * np.pi, nb_); ub = rng.uniform(-1, 1, nb_)
B = np.column_stack([rb * np.sqrt(1 - ub ** 2) * np.cos(tb), rb * np.sqrt(1 - ub ** 2) * np.sin(tb), 0.55 * rb * ub])
G = np.concatenate([G, B]); rr = np.hypot(G[:, 0], G[:, 1])
warm = np.exp(-rr / 0.35)[:, None]
C = np.array(IVORY)[None] * (1 - warm) + np.array((1.0, 0.74, 0.45))[None] * warm
C = C * (0.55 + 0.75 * np.exp(-rr / 0.5))[:, None]
onarm = ~np.concatenate([smooth, np.ones(nb_, bool)])
C[onarm] = C[onarm] * 1.15
tilt = math.radians(60); ct_, st_ = math.cos(tilt), math.sin(tilt)
Gt = np.column_stack([G[:, 0], G[:, 1] * ct_ - G[:, 2] * st_, G[:, 1] * st_ + G[:, 2] * ct_])
Gt[:, 0] += SX[6]; Gt[:, 2] += 1.25
Rg = np.full(len(Gt), 0.0045); Rg[-nb_:] = 0.004
points_obj(Gt, Rg, C, vcol_emission('galaxy', 1.8), 'galaxy')

# ------------------------------------------------------------------------------------------------------ rig
X0, X1 = -1.8, 34.2; AHEAD = 1.8
CAM_OFF = Vector((0.0, -7.4, 2.7)); LOOK_OFF = Vector((AHEAD, 0.0, 0.8))
rig = bpy.data.objects.new('rig', None); bpy.context.collection.objects.link(rig)
cd = bpy.data.cameras.new('cam'); cd.lens = 40; cd.dof.use_dof = True; cd.dof.aperture_fstop = 2.8; cd.dof.focus_distance = (LOOK_OFF - CAM_OFF).length
cam = bpy.data.objects.new('cam', cd); bpy.context.collection.objects.link(cam); sc.camera = cam
cam.parent = rig; cam.location = CAM_OFF; cam.rotation_euler = (LOOK_OFF - CAM_OFF).to_track_quat('-Z', 'Y').to_euler()
# one weak cool area light, riding with the camera
ld = bpy.data.lights.new('key', 'AREA'); ld.energy = 420; ld.color = (0.62, 0.74, 1.0); ld.size = 9
key = bpy.data.objects.new('key', ld); bpy.context.collection.objects.link(key); key.parent = rig
key.location = (0.3, 0.8, 7.5); key.rotation_euler = (LOOK_OFF - Vector(key.location)).to_track_quat('-Z', 'Y').to_euler()

def cam_x(i): return X0 + (X1 - X0) * i / NLOOP
def focus_at(i):
    # the focal plane follows the nearest station, weighted so that it never jumps
    c = Vector((cam_x(i), 0, 0)) + CAM_OFF; look_x = cam_x(i) + AHEAD; ws = ds = 0.0
    for x in SX:
        w = math.exp(-((x - look_x) / 2.4) ** 2); ws += w; ds += w * (Vector((x, 0, 0.8)) - c).length
    return ds / ws
vl = sc.view_layers[0]; vl['front'] = 0.0; vl['pulse'] = 0.0

def key_all(i0, i1):
    for i in (i0, i1):
        rig.location = (cam_x(i), 0, 0); rig.keyframe_insert('location', index=0, frame=frame_of(i))
        gaia.rotation_euler[2] = 2 * math.pi * i / NLOOP; gaia.keyframe_insert('rotation_euler', index=2, frame=frame_of(i))
        vl['pulse'] = SP * i / NLOOP; vl.keyframe_insert('["pulse"]', frame=frame_of(i))
    for i in range(i0, i1 + 1):
        cd.dof.focus_distance = focus_at(i); cd.keyframe_insert('dof.focus_distance', frame=frame_of(i))
    # the training front: one sweep per loop from left of the first panel to right of the last, repeating
    F0, F1 = JX0 - 1.2, JX1 + 1.2
    def front(i): return F0 + (F1 - F0) * ((i % NLOOP) / NLOOP)
    for i in sorted({i0, i1, 0, NLOOP} | ({-1} if i0 < 0 else set()) | ({NLOOP - 1} if i1 >= NLOOP else set())):
        if i0 <= i <= i1:
            vl['front'] = front(i); vl.keyframe_insert('["front"]', frame=frame_of(i))
    for ad in (rig.animation_data, gaia.animation_data, cd.animation_data, sc.animation_data):
        for fc in ad.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

if mode.startswith('still:'):
    i = int(mode[6:]); key_all(-PRE, NLOOP + POST - 1)
    sc.frame_set(frame_of(i)); sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
elif mode == 'anim':
    key_all(-PRE, NLOOP + POST - 1)
    sc.frame_start, sc.frame_end = frame_of(-PRE), frame_of(NLOOP + POST - 1)
    os.makedirs(os.path.join(out, 'raw'), exist_ok=True); sc.render.filepath = os.path.join(out, 'raw', 'r_')
    bpy.ops.render.render(animation=True)
print('wrote', out)
