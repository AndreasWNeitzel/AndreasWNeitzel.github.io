"""The title card for HAYDNsim on the Software page (Blender, Cycles): a synthetic population, one star's light curve
buried in instrument noise, and the oscillation spectrum that has to be dug out of it, read left to right on the dark
stage over a twelve second loop.

The three parts:
  1 The population: a glass plate standing upright on the left, carrying a Kiel diagram drawn as points of light
    (effective temperature falling to the right, surface gravity falling upwards: main sequence, turn off, subgiants,
    the red giant branch and the red clump). Real data: the effective temperatures and surface gravities of the 4,000
    Gaia DR3 stars with a best quality GSP-Spec solution in assets/data/playground/gaia_xp_mh.bin, each point's
    brightness set by its Gaia G magnitude. These are catalogue stars standing in for a synthetic population; the
    points are redrawn from the bottom of the diagram upwards at the start of every loop.
  2 The light curve: one red giant (the catalogue star nearest an effective temperature of 4,750 K and a surface
    gravity of 3.0) lifts out of the plate and its light curve unrolls to the right as a line of light over a faint
    curtain. The curve is schematic: a sum of sinusoids at the frequencies of the eight strongest peaks in the real
    spectrum of part 3, with illustrative amplitudes. Three noise layers then arrive from behind in brass and merge
    into it one after the other: white photon noise, red granulation noise and a slow drift. The noise draws are
    illustrative random series with a fixed seed; no simulation output is shown.
  3 The spectrum: filaments standing on the floor, each one bin of the oscillation power spectrum of the red giant
    KIC 6144777 from twelve quarters of Kepler long cadence photometry (figures/heroes/renders/pipeline/
    kic6144777_psd.npz), smoothed and divided by a power law fitted to the background, so the heights are real.
    The filaments first rise to a common noise floor, then the peaks grow out of it as a comb under a Gaussian
    envelope; the envelope's centre and width are the power weighted mean and spread of the same filaments.
A brass thread with moving dashes joins the star in the plate, the light curve and the spectrum. The camera sways
slowly on a closed path, so the loop is seamless: frame 360 is frame 0. No text, numbers or labels appear.
Colours: blue for the real data, brass for the noise and the flow, graphite neutrals on a near black stage.

Usage:
  uv run --python 3.11 --with bpy==4.2.0 python blender_haydn_card.py still OUTDIR T1,T2,...  [options]
      one PNG per loop phase T (0 to 1) as OUTDIR/still_TTT.png
  uv run --python 3.11 --with bpy==4.2.0 python blender_haydn_card.py anim OUTDIR [options]
      frames 0 to 360 as OUTDIR/f_0000.png ... OUTDIR/f_0360.png (frame 360 only for checking the seam)
Options: --samples N, --size WxH, --frames A,B (a subset of the loop), --kiel PATH.json, --psd PATH.npz.
The data paths default to the repository's copies, found relative to this file. Set CYCLES_DEVICE=GPU to render on
the graphics card.
"""
import json, math, os, sys
import numpy as np
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
mode, OUT = sys.argv[1], sys.argv[2]
args = sys.argv[3:]
def opt(name, default):
    return args[args.index(name) + 1] if name in args else default
SAMPLES = int(opt('--samples', '32'))
W, H = (int(v) for v in opt('--size', '1280x720').split('x'))
KIEL = opt('--kiel', os.path.join(REPO, 'assets', 'data', 'playground', 'gaia_xp_mh.json'))
PSD = opt('--psd', os.path.join(HERE, 'renders', 'pipeline', 'kic6144777_psd.npz'))
NFR = 360
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)

BLUE = np.array((0.30, 0.50, 1.0)); BLUE_HI = np.array((0.55, 0.72, 1.0)); IVORY = np.array((0.96, 0.92, 0.84))
BRASS = np.array((1.0, 0.68, 0.30)); GRAPH = np.array((0.30, 0.32, 0.36))
def sstep(x): x = np.clip(x, 0.0, 1.0); return x * x * (3 - 2 * x)
def ramp(t, a, b): return float(sstep((t - a) / (b - a)))

# ---------------------------------------------------------------- data
meta = json.load(open(KIEL)); raw = open(os.path.join(os.path.dirname(KIEL), meta['binary']), 'rb').read()
def col_(n):
    a = [x for x in meta['arrays'] if x['name'] == n][0]
    return np.frombuffer(raw, dtype=a['dtype'], count=a['length'], offset=a['offset']).astype(float)
TEFF, LOGG, GMAG = col_('teff_gspspec'), col_('logg_gspspec'), col_('phot_g_mean_mag')

d = np.load(PSD); f, p = d['f'], d['p']
keep = (f > 88) & (f < 172); f, p = f[keep], p[keep]
ps = np.convolve(p, np.ones(9) / 9, 'same')
lf, lp = np.log(f), np.log(ps); bg = (f < 100) | (f > 160)
b1, b0 = np.polyfit(lf[bg], lp[bg], 1); snr = ps / np.exp(b0 + b1 * lf)
NB = 210; edges = np.linspace(f.min(), f.max(), NB + 1); idx = np.digitize(f, edges) - 1
HB = np.array([snr[idx == i].max() if np.any(idx == i) else 0 for i in range(NB)])
HB = np.clip(HB / np.percentile(HB, 99.5), 0, 1.15) ** 0.7   # a gentle compression so the smaller modes read
FB = 0.5 * (edges[:-1] + edges[1:])
# the eight strongest peaks of the same spectrum give the light curve its frequencies
ps25 = np.convolve(p, np.ones(25) / 25, 'same'); order = np.argsort(ps25)[::-1]; PEAKS = []
for j in order:
    if all(abs(f[j] - s) > 1.5 for s in PEAKS): PEAKS.append(f[j])
    if len(PEAKS) == 8: break

# ---------------------------------------------------------------- scene
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
if os.environ.get('CYCLES_DEVICE') == 'GPU':
    pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'CUDA'; pr.get_devices()
    for dv in pr.devices: dv.use = dv.type == 'CUDA'
    sc.cycles.device = 'GPU'; sc.cycles.denoising_use_gpu = True
sc.render.resolution_x, sc.render.resolution_y = W, H; sc.render.resolution_percentage = 100
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
sc.cycles.max_bounces = 4; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 2; sc.cycles.transparent_max_bounces = 16
sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False; sc.cycles.seed = 3

def lum_material(name, strength):
    """Emission coloured by the vertex attribute 'col'; its alpha mixes the surface with full transparency."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    a = nt.nodes.new('ShaderNodeAttribute'); a.attribute_name = 'col'
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Strength'].default_value = strength
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(a.outputs['Color'], e.inputs['Color']); nt.links.new(a.outputs['Alpha'], mx.inputs['Fac'])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(e.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m

def glass(name, tint=(0.2, 0.4, 0.9), tint_strength=0.012, gloss=0.06):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); gl = nt.nodes.new('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value = 0.05
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*tint, 1); em.inputs['Strength'].default_value = tint_strength
    m1 = nt.nodes.new('ShaderNodeMixShader'); m1.inputs['Fac'].default_value = gloss; m2 = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(tr.outputs[0], m1.inputs[1]); nt.links.new(gl.outputs[0], m1.inputs[2]); nt.links.new(m1.outputs[0], m2.inputs[0]); nt.links.new(em.outputs[0], m2.inputs[1])
    nt.links.new(m2.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m

def thread_material(name, freq=2.2):
    """Brass emission brightened in dashes that move with the view-layer property 'phase'; the arc length is in the
    red channel of 'col', the alpha channel mixes with transparency."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    N = nt.nodes.new; L = nt.links.new
    arc = N('ShaderNodeAttribute'); arc.attribute_name = 'col'
    sep = N('ShaderNodeSeparateColor'); L(arc.outputs['Color'], sep.inputs['Color'])
    ph = N('ShaderNodeAttribute'); ph.attribute_type = 'VIEW_LAYER'; ph.attribute_name = 'phase'
    mul = N('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = freq; L(sep.outputs['Red'], mul.inputs[0])
    sub = N('ShaderNodeMath'); sub.operation = 'SUBTRACT'; L(mul.outputs[0], sub.inputs[0]); L(ph.outputs['Fac'], sub.inputs[1])
    tau = N('ShaderNodeMath'); tau.operation = 'MULTIPLY'; tau.inputs[1].default_value = 2 * math.pi; L(sub.outputs[0], tau.inputs[0])
    sn = N('ShaderNodeMath'); sn.operation = 'SINE'; L(tau.outputs[0], sn.inputs[0])
    half = N('ShaderNodeMath'); half.operation = 'MULTIPLY_ADD'; half.inputs[1].default_value = 0.5; half.inputs[2].default_value = 0.5; L(sn.outputs[0], half.inputs[0])
    pw = N('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 3.0; L(half.outputs[0], pw.inputs[0])
    st = N('ShaderNodeMath'); st.operation = 'MULTIPLY_ADD'; st.inputs[1].default_value = 1.6; st.inputs[2].default_value = 0.10; L(pw.outputs[0], st.inputs[0])
    e = N('ShaderNodeEmission'); e.inputs['Color'].default_value = (*BRASS, 1); L(st.outputs[0], e.inputs['Strength'])
    tr = N('ShaderNodeBsdfTransparent'); mx = N('ShaderNodeMixShader'); L(arc.outputs['Alpha'], mx.inputs['Fac'])
    L(tr.outputs[0], mx.inputs[1]); L(e.outputs[0], mx.inputs[2])
    L(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m

class Obj:
    """A mesh built from numpy arrays whose vertex positions and RGBA colours are rewritten every frame."""
    def __init__(self, name, verts, faces, mat):
        me = bpy.data.meshes.new(name); me.from_pydata(verts.tolist(), [], faces.tolist()); me.update()
        me.color_attributes.new('col', 'FLOAT_COLOR', 'POINT')
        self.me = me; self.n = len(verts)
        self.ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(self.ob); me.materials.append(mat)
        self.ob.visible_shadow = False
    def set(self, verts=None, rgba=None):
        if verts is not None: self.me.vertices.foreach_set('co', np.ascontiguousarray(verts, dtype=np.float32).ravel())
        if rgba is not None: self.me.color_attributes['col'].data.foreach_set('color', np.ascontiguousarray(rgba, dtype=np.float32).ravel())
        self.me.update()

OCT = np.array([(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)], float)
OCT_F = np.array([(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)])
def octa(centres, r):
    v = (centres[:, None, :] + r[:, None, None] * OCT[None]).reshape(-1, 3)
    fc = (OCT_F[None] + 6 * np.arange(len(centres))[:, None, None]).reshape(-1, 3); return v, fc

SIDES = 6
def tube_faces(n, sides=SIDES):
    i = np.arange(n - 1)[:, None]; k = np.arange(sides)[None, :]
    a = i * sides + k; b = i * sides + (k + 1) % sides
    return np.stack([a, b, b + sides, a + sides], -1).reshape(-1, 4)
def tube_verts(pts, r, normal_hint=(0, 1, 0)):
    """Rings around a polyline; pts (n,3). The ring frame uses the given hint as one axis."""
    t = np.gradient(pts, axis=0); t /= np.linalg.norm(t, axis=1, keepdims=True) + 1e-9
    u = np.cross(t, np.array(normal_hint, float)); un = np.linalg.norm(u, axis=1, keepdims=True)
    u = np.where(un > 1e-6, u / np.maximum(un, 1e-9), np.array((1.0, 0, 0)))
    v = np.cross(t, u); ang = 2 * math.pi * np.arange(SIDES) / SIDES
    rr = np.asarray(r, float).reshape(-1, 1, 1) if np.ndim(r) else r
    return (pts[:, None, :] + rr * (np.cos(ang)[None, :, None] * u[:, None, :] + np.sin(ang)[None, :, None] * v[:, None, :])).reshape(-1, 3)
def rgba(colours, alpha):
    c = np.broadcast_to(np.asarray(colours, float), (len(alpha), 3)) if np.ndim(colours) == 1 else np.asarray(colours, float)
    return np.concatenate([c, np.asarray(alpha, float)[:, None]], 1)

PTS = lum_material('points', 1.5); LINE = lum_material('line', 1.3); SOFT = lum_material('soft', 0.8)
SPEC = lum_material('spectrum', 1.5); BRASSM = lum_material('brass', 2.4); GLASS = glass('glass', gloss=0.025)

# ---------------------------------------------------------------- 1 the population plate
PC = np.array((-3.0, 0.45, 2.08)); PW, PH = 2.15, 2.4; YAW = math.radians(28)
U = np.array((math.cos(YAW), math.sin(YAW), 0.0)); Z = np.array((0.0, 0.0, 1.0)); NRM = np.array((math.sin(YAW), -math.cos(YAW), 0.0))
def on_plate(u, v, lift=0.0):   # u, v in plate units from the centre
    return PC + np.outer(u, U) + np.outer(v, Z) + lift * NRM
T0, T1, G0, G1 = 7300.0, 3750.0, 4.85, 0.95
ku = (TEFF - T0) / (T1 - T0) - 0.5; kv = (G0 - LOGG) / (G0 - G1) - 0.5
ku, kv = np.clip(ku, -0.5, 0.5) * (PW - 0.28), np.clip(kv, -0.5, 0.5) * (PH - 0.24)
STAR_POS = on_plate(ku, kv, 0.012)
gl = np.clip((14.5 - GMAG) / 6.0, 0, 1)                      # brighter catalogue stars as brighter points
P_BRIGHT = 0.35 + 0.65 * gl ** 0.8
P_ORDER = np.argsort(np.argsort(-LOGG + rng.normal(0, 0.12, len(LOGG)))) / len(LOGG)   # drawn from the bottom up
P_COL = (BLUE[None] * (0.75 + 0.25 * gl[:, None]) + (BLUE_HI - BLUE)[None] * gl[:, None] ** 2)
pv, pf = octa(STAR_POS, np.full(len(STAR_POS), 0.0105))
POP = Obj('population', pv, pf, PTS)
SEL = int(np.argmin(((TEFF - 4750) / 400) ** 2 + ((LOGG - 3.0) / 0.25) ** 2))
SEL_POS = STAR_POS[SEL]

bpy.ops.mesh.primitive_plane_add(size=1, location=tuple(PC)); plate = bpy.context.object
plate.scale = (PW, PH, 1); plate.rotation_euler = (math.pi / 2, 0, YAW); plate.data.materials.append(GLASS)
corners = np.array([on_plate(np.array([a]), np.array([b]))[0] for a, b in ((-PW / 2, -PH / 2), (PW / 2, -PH / 2), (PW / 2, PH / 2), (-PW / 2, PH / 2), (-PW / 2, -PH / 2))])
fr = np.concatenate([np.linspace(corners[i], corners[i + 1], 30) for i in range(4)])
FRAME = Obj('plate_edges', tube_verts(fr, 0.0035), tube_faces(len(fr)), SOFT)
FRAME.set(rgba=rgba(GRAPH * 1.4, np.full(FRAME.n, 1.0)))

# ---------------------------------------------------------------- 2 the light curve and its noise
X0, X1, ZC, YR = -1.55, 1.45, 2.0, -0.05
NS = 700; XS = np.linspace(X0, X1, NS); S = (XS - X0) / (X1 - X0)
tday = S * 2.2                                                # the span in days, for the oscillation only
CLEAN = sum(math.cos(1.7 * k) * np.cos(2 * math.pi * fq * 1e-6 * tday * 86400 + 2.1 * k) * (0.55 + 0.45 * math.exp(-((fq - 127) / 12) ** 2))
            for k, fq in enumerate(PEAKS))
CLEAN = 0.30 * CLEAN / np.abs(CLEAN).max()
PHOT = rng.normal(0, 0.065, NS)
g = np.zeros(NS); e = rng.normal(0, 1, NS)
for i in range(1, NS): g[i] = 0.93 * g[i - 1] + e[i]
GRAN = 0.12 * g / g.std()
DRIFT = 0.24 * (np.sin(2 * math.pi * (0.55 * S + 0.1)) - 0.4 * S)
DRIFT -= DRIFT.mean()
LAYERS = [PHOT, GRAN, DRIFT]
def curve(w):
    zz = ZC + CLEAN + sum(wk * Lk for wk, Lk in zip(w, LAYERS)); return np.stack([XS, np.full(NS, YR), zz], 1)
RIB = Obj('light_curve', tube_verts(curve((0, 0, 0)), 0.009), tube_faces(NS), LINE)
# the curtain under the curve, down to a hairline baseline
ZB = ZC - 0.78
def curtain_verts(c): return np.concatenate([c, np.stack([XS, np.full(NS, YR + 0.002), np.full(NS, ZB)], 1)])
cf = np.array([(i, i + 1, NS + i + 1, NS + i) for i in range(NS - 1)])
CUR = Obj('curtain', curtain_verts(curve((0, 0, 0))), cf, SOFT)
LAY = [Obj(f'noise_{k}', tube_verts(np.stack([XS, np.full(NS, 0.0), ZC + Lk], 1), 0.0045), tube_faces(NS), BRASSM) for k, Lk in enumerate(LAYERS)]
BASE = np.stack([XS, np.full(NS, YR), np.full(NS, ZB)], 1)
BASEL = Obj('baseline', tube_verts(BASE, 0.0025), tube_faces(NS), SOFT)
STAR = Obj('star', *octa(SEL_POS[None], np.array([0.03])), PTS)

# ---------------------------------------------------------------- 3 the spectrum
SX0, SX1, SY = 1.9, 4.05, 0.0
FX = np.linspace(SX0, SX1, NB); FWD = 0.0055
def boxes(x, h):
    xl, xh = x - FWD, x + FWD; yl, yh = np.full(NB, SY - FWD), np.full(NB, SY + FWD); z0 = np.zeros(NB)
    v = np.stack([np.stack(c, 1) for c in ((xl, yl, z0), (xh, yl, z0), (xh, yh, z0), (xl, yh, z0),
                                           (xl, yl, h), (xh, yl, h), (xh, yh, h), (xl, yh, h))], 1)
    return v.reshape(-1, 3)
BF = np.array([(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
bf = (BF[None] + 8 * np.arange(NB)[:, None, None]).reshape(-1, 4)
HSCALE = 2.3
FLOOR = np.minimum(HB, np.percentile(HB, 55))
SP = Obj('spectrum', boxes(FX, np.full(NB, 0.002)), bf, SPEC)
tpk = np.clip((HB - FLOOR) / (HB.max() - FLOOR.max() + 1e-9), 0, 1) ** 0.6
TOP = BRASS[None] * 0.32 * (1 - tpk[:, None]) + (BLUE[None] * 0.9 + 0.25 * (BLUE_HI - BLUE)[None] * tpk[:, None]) * tpk[:, None]
TOP = np.where(tpk[:, None] < 0.03, BRASS[None] * 0.3, TOP)
w8 = np.clip(HB - FLOOR, 0, None); MU = float((FX * w8).sum() / w8.sum()); SIG = float(np.sqrt((w8 * (FX - MU) ** 2).sum() / w8.sum()))
ENV_X = np.linspace(SX0, SX1, 260)
ENV_H = 0.05 + HSCALE * 0.78 * np.exp(-0.5 * ((ENV_X - MU) / SIG) ** 2) + HSCALE * float(np.median(FLOOR))
ENV = Obj('envelope', tube_verts(np.stack([ENV_X, np.full(260, SY), ENV_H], 1), 0.0028), tube_faces(260), SOFT)
# the frequency order in which peaks emerge: from the envelope's centre outwards
EMERGE = np.abs(FX - MU) / (SX1 - SX0)

# ---------------------------------------------------------------- the thread
def bez(p0, p1, p2, p3, n):
    t = np.linspace(0, 1, n)[:, None]; return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3
A = SEL_POS; B = np.array((X0, YR, ZB)); C = np.array((X1, YR, ZB)); D = np.array((SX0 - 0.05, SY, 0.012))
path = np.concatenate([bez(A, A + 0.5 * NRM + np.array((0.2, 0, 0)), B + np.array((-0.45, -0.1, 0.0)), B, 40)[:-1],
                       np.linspace(B, C, 60)[:-1], bez(C, C + np.array((0.35, 0, 0)), D + np.array((-0.35, -0.0, 0.25)), D, 40)[:-1],
                       np.linspace(D, np.array((SX1 + 0.3, SY, 0.012)), 40)])
arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))])
THR = Obj('thread', tube_verts(path, 0.0045), tube_faces(len(path)), thread_material('thread'))
THR.set(rgba=np.concatenate([np.repeat(arc, SIDES)[:, None], np.zeros((len(path) * SIDES, 2)), np.full((len(path) * SIDES, 1), 0.85)], 1))
HEAD = np.argmin(np.linalg.norm(path - B, axis=1))   # the thread's index at the light curve's start

# ---------------------------------------------------------------- stage, light, camera, glow
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.01)); fl = bpy.context.object; fl.scale = (400, 400, 0.02)
fm = bpy.data.materials.new('floor'); fm.use_nodes = True; bs = fm.node_tree.nodes['Principled BSDF']
bs.inputs['Base Color'].default_value = (0.006, 0.007, 0.009, 1); bs.inputs['Metallic'].default_value = 0.5; bs.inputs['Roughness'].default_value = 0.26
fl.data.materials.append(fm)
world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.003, 0.0035, 0.005, 1)
ld = bpy.data.lights.new('key', 'AREA'); ld.energy = 60; ld.color = (0.7, 0.8, 1.0); ld.size = 8
lo = bpy.data.objects.new('key', ld); bpy.context.collection.objects.link(lo); lo.location = (0.5, -4.0, 7.0)
lo.rotation_euler = (Vector((0.5, 0.5, 0.0)) - lo.location).to_track_quat('-Z', 'Y').to_euler()
cam_d = bpy.data.cameras.new('cam'); cam_d.lens = 30; cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 5.6
cam = bpy.data.objects.new('cam', cam_d); bpy.context.collection.objects.link(cam); sc.camera = cam
LOOK = Vector((0.05, 0.2, 1.55))
def camera(t):
    a = 2 * math.pi * t
    loc = Vector((0.05 + 0.25 * math.sin(a), -7.35 + 0.12 * math.cos(a), 2.05 + 0.05 * math.sin(2 * a)))
    cam.location = loc; cam.rotation_euler = (LOOK - loc).to_track_quat('-Z', 'Y').to_euler()
    cam_d.dof.focus_distance = (Vector((0.0, YR, ZC)) - loc).length
sc.use_nodes = True; ct = sc.node_tree; rl = ct.nodes['Render Layers']; comp = ct.nodes['Composite']
gg = ct.nodes.new('CompositorNodeGlare'); gg.glare_type = 'FOG_GLOW'; gg.quality = 'HIGH'; gg.size = 7; gg.threshold = 0.55; gg.mix = -0.55
ct.links.new(rl.outputs['Image'], gg.inputs['Image']); ct.links.new(gg.outputs['Image'], comp.inputs['Image'])
VL = sc.view_layers[0]; VL['phase'] = 0.0

# ---------------------------------------------------------------- the twelve second story, t from 0 to 1
def state(t):
    out_ = 1.0 - ramp(t, 0.885, 0.985)                       # everything downstream fades before the reset
    # 1 the population is redrawn from a dim floor, bottom up, and dims again at the end
    grow = np.clip((t / 0.17 - P_ORDER) / 0.12, 0, 1) if t < 0.5 else np.ones_like(P_ORDER)
    lvl = np.where(t < 0.5, 0.15 + 0.85 * sstep(grow), 0.15 + 0.85 * out_)
    pc = P_COL * (P_BRIGHT * lvl)[:, None]
    sel_on = ramp(t, 0.16, 0.20) * out_
    POP.set(rgba=rgba(np.repeat(pc, 6, 0), np.repeat(np.where(np.arange(len(pc)) == SEL, 1 - sel_on, 1.0), 6)))
    # 2 the chosen star lifts out and travels along the thread to the start of the curve
    lift = ramp(t, 0.18, 0.29)
    k = int(round(lift * HEAD)); sp = path[k] if lift < 1 else B
    rr = 0.016 + 0.014 * sel_on + 0.006 * math.sin(2 * math.pi * 6 * t) * sel_on
    sv, _ = octa(sp[None], np.array([rr])); STAR.set(sv, rgba(IVORY * 1.15, np.full(6, sel_on)))
    # the curve unrolls, then takes on the three noise layers one by one
    unroll = ramp(t, 0.27, 0.43)
    w = [ramp(t, a + 0.055, a + 0.085) for a in (0.44, 0.53, 0.62)]
    c = curve(w)
    a_ = np.clip((unroll * 1.04 - S) / 0.04, 0, 1) * out_
    head = np.exp(-((S - unroll) / 0.025) ** 2) * (unroll < 1) * (unroll > 0)
    noise = sum(w) / 3.0
    colr = (BLUE * (1 - 0.35 * noise) + BRASS * 0.35 * noise)[None] * (1 + 0.8 * head[:, None])
    RIB.set(tube_verts(c, 0.009), rgba(np.repeat(colr, SIDES, 0), np.repeat(a_, SIDES)))
    CUR.set(curtain_verts(c), rgba(BLUE, np.concatenate([0.07 * a_, 0.0 * a_])))
    BASEL.set(rgba=rgba(GRAPH * 1.5, np.repeat(a_ * 0.8, SIDES)))
    for kk, (Lo, a0) in enumerate(zip(LAY, (0.44, 0.53, 0.62))):
        come = ramp(t, a0, a0 + 0.06)                          # arrives from behind
        y = YR + 0.95 * (1 - come) + 0.02
        alpha = ramp(t, a0 - 0.01, a0 + 0.02) * (1 - ramp(t, a0 + 0.06, a0 + 0.09)) * out_
        pts = np.stack([XS, np.full(NS, y), ZC + 0.0 + LAYERS[kk]], 1)
        Lo.set(tube_verts(pts, 0.006), rgba(BRASS, np.full(NS * SIDES, alpha)))
    # 3 the spectrum: a noise floor first, then the comb grows from the centre of the envelope outwards
    fl_ = ramp(t, 0.70, 0.76)
    pk = np.clip((t - 0.75 - 0.07 * EMERGE / EMERGE.max()) / 0.07, 0, 1); pk = sstep(pk)
    h = HSCALE * (FLOOR * fl_ + (HB - FLOOR) * pk) * out_ + 0.002
    sc_ = np.repeat(np.stack([TOP * 0.05, TOP], 1), 4, 1).reshape(-1, 3)
    SP.set(boxes(FX, h), rgba(sc_, np.full(NB * 8, min(1.0, fl_ * 3) * float(out_ > 0))))
    ENV.set(rgba=rgba(IVORY * 0.4, np.full(ENV.n, 0.9 * ramp(t, 0.82, 0.88) * out_)))
    VL['phase'] = 6.0 * t                                     # whole cycles per loop, so the dashes close too
    camera(t)

def render(t, path_):
    state(t); sc.render.filepath = path_; bpy.ops.render.render(write_still=True)

if mode == 'still':
    for tt in (float(v) for v in args[0].split(',')):
        render(tt, os.path.join(OUT, f'still_{int(round(tt * 1000)):03d}.png'))
else:
    a_, b_ = (int(v) for v in opt('--frames', f'0,{NFR}').split(','))
    for fr_ in range(a_, b_ + 1):
        render(fr_ / NFR, os.path.join(OUT, f'f_{fr_:04d}.png'))
print('done')
