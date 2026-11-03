"""The research header as a closed circuit of stops (Blender, Cycles). Eight stations stand on a ring in the dark, the
Milky Way lies around the ring, and one brass thread joins everything into one closed line. The camera eases to each
station, stands, and goes on; after the eighth it climbs out until the ring is a point in the Galaxy, stands over the
Galaxy, and comes back down to the star it started from. The last frame is the first frame.

The stops, in order:
  1 star     A red giant ringing, with the globular cluster M13 behind it.
  2 sats     Kepler and TESS, which photograph that light.
  3 lc       Six days of the Kepler light curve of KIC 6144777.
  4 psd      The power spectrum of the same star, with three of its modes shown as ringing stars above their peaks.
  5 gaia     Gaia, spinning.
  6 xp       A Gaia XP spectrum.
  7 janus    JANUS: the spectrum enters, four dense layers, five coupling layers of a flow, labels with their spread.
  8 fold     Starfold: the chemistry plane, the rolled sheet, the sheet unrolling, all standing upright.
  9 mw       The Milky Way with its populations apart. The thread enters at its centre and follows an arm home.

What is real.
  The spectrum filaments: the oscillation power spectrum of KIC 6144777 from twelve quarters of Kepler long cadence
    photometry, smoothed and divided by a fitted background, heights compressed by a power of 0.7.
  The mode identification over those peaks: the large separation is 10.9 microhertz from the autocorrelation; 123.65 and
    134.54 are radial modes, 122.25 and 133.16 their degree two neighbours, 140.22 a dipole mode. Read from the spectrum
    with the usual asymptotic pattern; no published peakbagging table was used.
  The light curve: 271 cadences of Kepler PDCSAP flux of the same star, BKJD 616.5 to 622.5, a three day running median
    removed. Nothing else is done to it. Inside its stop the thread runs along this same curve, and along the XP spectrum.
  The XP spectrum: the 343 fluxes of Gaia DR3 5289554869898620416, on a 2 nm grid from 336 to 1020 nm.
  M13: the 31,035 Gaia members in the JANUS cluster table, each at its own position on the sky and brightness and colour
    from its own G and BP-RP. The depth of each star along the line of sight is drawn from a Plummer model: not measured.
  The stars around the ring, and the bright part of the Milky Way near the Sun: the 160,000 Gaia DR3 giants of
    assets/data/mw (Andrae et al. 2023), at their inverse parallax distances, in their true Galactic geometry, with
    brass for [Fe/H] below -0.75 and blue above.
  Starfold: the 9,242 stars of the recorded run on the APOGEE DR19 table, on the plane of [alpha/M] against [Fe/H] and
    on the two-dimensional map. Blue is the low-alpha group, brass the high-alpha group, graphite the unassigned.

What is schematic.
  The ringing: the mode shapes are true spherical harmonics of degree 0 to 2 and the mutual frequency ratios of the three
    shown are true, but amplitude and time are scaled by very large factors. The star's surface is a generic texture
    with solar limb darkening; a raised part of a mode is drawn hotter and a sunken part cooler.
  The spacecraft: Gaia is the hand built model in gaia_model.py, TESS is built on NASA's model; the Kepler holder stays empty until its model is final.
  JANUS: the network's layer counts are true (four dense layers, five coupling layers, eight members); the points are a
    Gaussian draw pushed through hand written coupling layers as in figures/janus/build_janus.py, so the shapes on the
    plates, including the final two-lobed cloud, show the mechanism and are not a JANUS output for this star.
  The rolled sheet of Starfold, as in blender_starfold_manifold.py.
  The Milky Way beyond 5 kpc from the Sun: a model with an exponential thin disc with four arms and a bar in blue, a
    thicker shorter disc in brass, a bulge and a faint halo, with a few model disc stars closing the giants' own gap
    round the Sun. No telescope sees it from outside. The ring is drawn 160 pc in radius, which has no meaning.
  The path of the thread, the camera and the timing.

Usage, with bpy 4.2 (numpy only inside):
  blender_research.py plan
  blender_research.py still OUTDIR --t SECONDS [SECONDS ...] [--w 960 --h 540 --samples 32]
  blender_research.py still OUTDIR --stops [as above]              one still at the settled point of each stop
  blender_research.py frames OUTDIR --fps 30 --from 0 --to 100 [as above]   f_00000.png ...; finished frames are skipped
      --blur 0.5 blurs the camera's motion, --denoise 2 denoises moving frames and the Gaia stop only
--data DIR holds kic6144777_lc.npz and m13.npz. Set CYCLES_DEVICE=GPU to render on the graphics card."""
import argparse, json, math, os, sys
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('mode'); ap.add_argument('out', nargs='?', default='')
ap.add_argument('--t', type=float, nargs='*'); ap.add_argument('--stops', action='store_true'); ap.add_argument('--only', default='')
ap.add_argument('--fps', type=int, default=30); ap.add_argument('--from', dest='a', type=int, default=0); ap.add_argument('--to', dest='b', type=int, default=-1)
ap.add_argument('--w', type=int, default=1280); ap.add_argument('--h', type=int, default=720); ap.add_argument('--samples', type=int, default=32)
ap.add_argument('--blur', type=float, default=0.0); ap.add_argument('--denoise', type=int, default=0)   # --denoise 2: moving frames only
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.normpath(os.path.join(HERE, '..', '..')) + os.sep
ap.add_argument('--data', default=os.path.join(ROOT, '_local', 'renders', 'research', 'data'))
args = ap.parse_args()
if args.out and not os.path.isabs(args.out): args.out = os.path.join(ROOT, '_local', 'renders', 'research', args.out)   # never the repository root

# ---------------------------------------------------------------------------------------------------- the timetable
STOPS = [('star', 3.5, 2.0), ('sats', 3.5, 2.0), ('lc', 3.5, 2.0), ('psd', 4.5, 2.0), ('gaia', 3.0, 2.0), ('xp', 3.5, 2.0),
         ('janus', 4.5, 2.0), ('fold', 5.5, 4.0), ('mw', 4.5, 4.5)]
KEY = [s[0] for s in STOPS]; N_ST = len(STOPS)
T0 = np.cumsum([0] + [s[1] + s[2] for s in STOPS]); LOOP = float(T0[-1])
def stop_of(t):
    t = t % LOOP; k = int(np.searchsorted(T0, t, side='right') - 1); return k, t - T0[k]
def hold_time(name, t):
    """Seconds since the camera settled at this stop, from 0 at the start of its hold; negative before it."""
    return (t % LOOP) - T0[KEY.index(name)]
def smoother(x):
    x = np.clip(x, 0.0, 1.0); return x * x * x * (x * (6 * x - 15) + 10)
if args.mode == 'plan':
    for k, (n, h, tr) in enumerate(STOPS): print(f'{k + 1} {n:6s} settles {T0[k]:5.1f} s, holds {h} s, travels {tr} s')
    print('loop', LOOP, 's'); sys.exit(0)

import bpy, bmesh
from mathutils import Vector, Matrix, Quaternion

IVORY = np.array((0.96, 0.92, 0.84)); BLUE = np.array((0.16, 0.36, 1.0)); BLUE_HI = np.array((0.30, 0.50, 1.0))
BRASS = np.array((1.0, 0.55, 0.14)); GRAPH = np.array((0.24, 0.25, 0.29)); WHITE = np.array((0.86, 0.9, 1.0))
LOOPI = lambda period: 2 * math.pi * max(1, round(LOOP / period)) / LOOP   # an angular speed with a whole number of cycles per loop

# ---------------------------------------------------------------------------------------------------- the ring
R = 16.0; TH0 = math.radians(90.0); DTH = math.radians(45.0); STN = KEY[:8]
def frame_of(k):
    th = TH0 - k * DTH
    Y = np.array((math.cos(th), math.sin(th), 0.0)); X = np.array((math.sin(th), -math.cos(th), 0.0))   # right, away from the ring's centre
    return R * Y, X, Y, np.array((0.0, 0.0, 1.0))
class St:
    """Local coordinates of a station: x to the viewer's right, y away, z up."""
    def __init__(self, name):
        self.k = KEY.index(name); self.o, self.x, self.y, self.z = frame_of(self.k)
    def w(self, p):
        p = np.asarray(p, float); return self.o + p[..., 0, None] * self.x + p[..., 1, None] * self.y + p[..., 2, None] * self.z
    def d(self, v):
        v = np.asarray(v, float); return v[..., 0, None] * self.x + v[..., 1, None] * self.y + v[..., 2, None] * self.z
ST = {n: St(n) for n in STN}

# ---------------------------------------------------------------------------------------------------- the scene
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = args.samples; sc.cycles.device = 'CPU'
if os.environ.get('CYCLES_DEVICE') == 'GPU':
    pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'CUDA'; pr.get_devices()
    for dv in pr.devices: dv.use = dv.type == 'CUDA'
    sc.cycles.device = 'GPU'; sc.cycles.denoising_use_gpu = True
sc.cycles.use_denoising = args.denoise == 1; sc.cycles.use_adaptive_sampling = False
sc.cycles.seed = 7; sc.cycles.use_animated_seed = False
sc.cycles.max_bounces = 3; sc.cycles.diffuse_bounces = 1; sc.cycles.glossy_bounces = 1; sc.cycles.transmission_bounces = 0
sc.cycles.transparent_max_bounces = 10; sc.cycles.volume_bounces = 0; sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
sc.render.use_persistent_data = True
sc.cycles.sample_clamp_direct = 6.0; sc.cycles.sample_clamp_indirect = 2.5; sc.cycles.blur_glossy = 1.0
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = args.w, args.h, 100
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'; sc.render.image_settings.compression = 40
sc.render.fps = args.fps
LIVE = {}

def link(ob): bpy.context.collection.objects.link(ob); return ob
def nodes(m):
    m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); return nt, nt.nodes['Material Output']

def lum(name, strength, sky=False):
    """Emission coloured by the point attribute 'col'; its alpha mixes with transparency. Never sampled as a lamp."""
    m = bpy.data.materials.new(name); nt, out = nodes(m); N = nt.nodes.new; L = nt.links.new; m.cycles.emission_sampling = 'NONE'
    a = N('ShaderNodeAttribute'); a.attribute_name = 'col'
    e = N('ShaderNodeEmission'); L(a.outputs['Color'], e.inputs['Color']); e.inputs['Strength'].default_value = strength
    if sky:
        s = N('ShaderNodeValue'); LIVE['sky'] = s.outputs[0]
        mu = N('ShaderNodeMath'); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = strength; L(s.outputs[0], mu.inputs[0]); L(mu.outputs[0], e.inputs['Strength'])
    tr = N('ShaderNodeBsdfTransparent'); mx = N('ShaderNodeMixShader')
    L(a.outputs['Alpha'], mx.inputs['Fac']); L(tr.outputs[0], mx.inputs[1]); L(e.outputs[0], mx.inputs[2]); L(mx.outputs[0], out.inputs['Surface']); return m

def glass(name):
    m = bpy.data.materials.new(name); nt, out = nodes(m); N = nt.nodes.new; Lk = nt.links.new; m.cycles.emission_sampling = 'NONE'
    fr = N('ShaderNodeLayerWeight'); fr.inputs['Blend'].default_value = 0.25
    tr = N('ShaderNodeBsdfTransparent'); em = N('ShaderNodeEmission'); em.inputs['Color'].default_value = (0.30, 0.42, 0.75, 1)
    f2 = N('ShaderNodeMath'); f2.operation = 'POWER'; f2.inputs[1].default_value = 3.0; Lk(fr.outputs['Facing'], f2.inputs[0])
    es = N('ShaderNodeMath'); es.operation = 'MULTIPLY_ADD'; es.inputs[1].default_value = 0.16; es.inputs[2].default_value = 0.012
    Lk(f2.outputs[0], es.inputs[0]); Lk(es.outputs[0], em.inputs['Strength'])
    ad = N('ShaderNodeAddShader'); Lk(tr.outputs[0], ad.inputs[0]); Lk(em.outputs[0], ad.inputs[1]); Lk(ad.outputs[0], out.inputs['Surface']); return m

def thread_material(period):
    """Brass, brightened in dashes that travel with 'phase'; the coordinate along the line is in the red of 'col'."""
    m = bpy.data.materials.new('thread'); nt, out = nodes(m); N = nt.nodes.new; L = nt.links.new; m.cycles.emission_sampling = 'NONE'
    def M(op, a=None, b=None, c=None):
        n = N('ShaderNodeMath'); n.operation = op
        for k, v in enumerate((a, b, c)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[k].default_value = v
            else: L(v, n.inputs[k])
        return n.outputs[0]
    a = N('ShaderNodeAttribute'); a.attribute_name = 'col'; sp = N('ShaderNodeSeparateColor'); L(a.outputs['Color'], sp.inputs['Color'])
    ph = N('ShaderNodeValue'); LIVE['phase'] = ph.outputs[0]
    s = M('SINE', M('MULTIPLY', M('SUBTRACT', M('DIVIDE', sp.outputs['Red'], period), ph.outputs[0]), 2 * math.pi))
    d = M('POWER', M('MULTIPLY_ADD', s, 0.5, 0.5), 4.0)
    e = N('ShaderNodeEmission'); e.inputs['Color'].default_value = (*BRASS, 1); L(M('MULTIPLY_ADD', d, 5.0, 1.3), e.inputs['Strength'])
    L(e.outputs[0], out.inputs['Surface']); return m

def faded(m, sockets):
    nt = m.node_tree; out = nt.nodes['Material Output']; src = out.inputs['Surface'].links[0].from_socket
    mx = nt.nodes.new('ShaderNodeMixShader'); tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(src, mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface']); sockets.append(mx.inputs['Fac']); return m

def plain(name, col, strength):
    m = bpy.data.materials.new(name); nt, out = nodes(m); m.cycles.emission_sampling = 'NONE'
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (*col, 1); e.inputs['Strength'].default_value = strength
    nt.links.new(e.outputs[0], out.inputs['Surface']); return m

class Obj:
    """One mesh from numpy arrays, positions and RGBA point colours rewritten at will."""
    def __init__(self, name, V, F, mat):
        V = np.asarray(V, np.float32); F = np.asarray(F, np.int32); nf, ns = F.shape
        me = bpy.data.meshes.new(name); me.vertices.add(len(V)); me.vertices.foreach_set('co', V.ravel())
        me.loops.add(nf * ns); me.loops.foreach_set('vertex_index', F.ravel())
        me.polygons.add(nf); me.polygons.foreach_set('loop_start', np.arange(nf, dtype=np.int32) * ns)
        me.update(calc_edges=True); me.color_attributes.new('col', 'FLOAT_COLOR', 'POINT')
        self.me = me; self.n = len(V); self.ob = link(bpy.data.objects.new(name, me)); me.materials.append(mat)
        self.ob.visible_shadow = False; self.ob.cycles.use_motion_blur = False
        self.colour(np.ones((self.n, 4)))
    def move(self, V): self.me.vertices.foreach_set('co', np.ascontiguousarray(V, dtype=np.float32).ravel()); self.me.update()
    def colour(self, C): self.me.color_attributes['col'].data.foreach_set('color', np.ascontiguousarray(C, dtype=np.float32).ravel()); self.me.update()

def rgba(c, a=1.0):
    c = np.atleast_2d(np.asarray(c, float)); a = np.asarray(a, float)
    n = max(len(c), a.size); c = np.broadcast_to(c, (n, 3)); a = np.broadcast_to(a, (n,))
    return np.concatenate([c, a[:, None]], 1)

OCT = np.array([(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)], float)
OCT_F = np.array([(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)])
TET = np.array([(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)], float) / math.sqrt(3) * 1.4
TET_F = np.array([(0, 1, 2), (0, 3, 1), (0, 2, 3), (1, 3, 2)])
def blobs(P, r, shape=OCT, F=OCT_F):
    r = np.broadcast_to(np.asarray(r, float), (len(P),))
    return (P[:, None, :] + r[:, None, None] * shape[None]).reshape(-1, 3), (F[None] + len(shape) * np.arange(len(P))[:, None, None]).reshape(-1, 3)

def tube(pts, r, sides=6):
    """Rings round a polyline with a parallel transported frame; r a number or one per point."""
    pts = np.asarray(pts, float); n = len(pts); rr = np.broadcast_to(np.asarray(r, float), (n,))
    t = np.gradient(pts, axis=0); t /= np.linalg.norm(t, axis=1, keepdims=True) + 1e-12
    u = np.zeros((n, 3)); a = np.cross(t[0], (0.31, 0.42, 0.85)); u[0] = a / np.linalg.norm(a)
    for i in range(1, n):
        a = u[i - 1] - t[i] * np.dot(u[i - 1], t[i]); u[i] = a / (np.linalg.norm(a) + 1e-12)
    v = np.cross(t, u); ang = 2 * np.pi * np.arange(sides) / sides
    V = pts[:, None, :] + rr[:, None, None] * (np.cos(ang)[None, :, None] * u[:, None, :] + np.sin(ang)[None, :, None] * v[:, None, :])
    i = np.arange(n - 1)[:, None]; k = np.arange(sides)[None, :]
    a = i * sides + k; b = i * sides + (k + 1) % sides
    return V.reshape(-1, 3), np.stack([a, b, b + sides, a + sides], -1).reshape(-1, 4)

def bars(x0, x1, z0, z1, y, w):
    """Vertical lines drawn as thin boxes between (x, z0) and (x, z1); returns verts in local coordinates, faces."""
    n = len(x0); xl, xh = x0 - w, x0 + w; yl, yh = np.full(n, y - w), np.full(n, y + w)
    V = np.stack([np.stack(c, 1) for c in ((xl, yl, z0), (xh, yl, z0), (xh, yh, z0), (xl, yh, z0), (xl, yl, z1), (xh, yl, z1), (xh, yh, z1), (xl, yh, z1))], 1)
    BF = np.array([(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
    return V.reshape(-1, 3), (BF[None] + 8 * np.arange(n)[:, None, None]).reshape(-1, 4)

def bez(p0, m0, p1, m1, n):
    """A cubic Hermite from p0 to p1 with end tangents m0, m1."""
    u = np.linspace(0, 1, n)[:, None]
    return (2 * u ** 3 - 3 * u ** 2 + 1) * p0 + (u ** 3 - 2 * u ** 2 + u) * m0 + (-2 * u ** 3 + 3 * u ** 2) * p1 + (u ** 3 - u ** 2) * m1

MAT = {'pt': lum('pt', 1.3), 'line': lum('line', 1.5), 'soft': lum('soft', 0.9), 'hair': lum('hair', 0.55), 'peak': lum('peak', 1.5),
       'sky': lum('sky', 1.0, sky=True), 'star': lum('star', 1.0), 'glass': glass('glass')}

def closed_rect(w, h):
    return np.array([(-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2), (-w / 2, 0, -h / 2)], float)

def hairline(name, P, r=0.004, col=IVORY * 0.5, mat='hair', alpha=1.0):
    V, F = tube(P, r, sides=4); o = Obj(name, V, F, MAT[mat]); o.colour(rgba(col, np.full(len(V), alpha))); return o

def plate(name, st, centre, w, h, normal_x=False):
    """A pane of hairline glass in the plane x-z of the station, or facing along x."""
    c = np.asarray(centre, float)
    if normal_x: P = c + np.array([(0, a, b) for a, b in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))])
    else: P = c + np.array([(a, 0, b) for a, b in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))])
    W = st.w(P); me = bpy.data.meshes.new(name); me.from_pydata(W.tolist(), [], [(0, 1, 2, 3)]); link(bpy.data.objects.new(name, me)); me.materials.append(MAT['glass'])
    hairline(name + '_e', np.concatenate([W, W[:1]]), 0.005, BLUE_HI * 0.55, 'soft')

# ---------------------------------------------------------------------------------------------------- real data
KIC = np.load(os.path.join(ROOT, 'figures/heroes/renders/pipeline/kic6144777_psd.npz'))
XP = np.array(json.load(open(os.path.join(ROOT, 'figures/heroes/renders/pipeline/xp_spec.json'))), float)
LC = np.load(os.path.join(args.data, 'kic6144777_lc.npz')); M13 = np.load(os.path.join(args.data, 'm13.npz'))
meta = json.load(open(ROOT + 'assets/data/starfold/apogee_run.json')); raw = open(ROOT + 'assets/data/starfold/apogee_run.bin', 'rb').read()
AR = {a['name']: a for a in meta['arrays']}
def arr(n):
    a = AR[n]; return np.frombuffer(raw, np.dtype(a['dtype']).newbyteorder('<'), int(np.prod(a['shape'])), a['offset']).reshape(a['shape'])
MAP, GRP, FEAT = arr('map').astype(float), arr('group').astype(int), arr('features').astype(float)
CN = [c['name'] for c in meta['columns']]; FE, AL = FEAT[:, CN.index('fe_h')], FEAT[:, CN.index('alpha_m')]
gi = json.load(open(ROOT + 'assets/data/mw/giants.json')); gb = open(ROOT + 'assets/data/mw/giants.bin', 'rb').read(); gn = gi['n']
GX = np.stack([np.frombuffer(gb, '<f2', gn, o).astype(float) for o in (0, gn * 2, gn * 4)], 1); GFE = np.frombuffer(gb, 'i1', gn, gn * 6) / 50

# ---------------------------------------------------------------------------------------------------- the Milky Way
KPC = 100.0                                         # scene units to the kiloparsec; the Sun at the origin
_gaz = TH0 + DTH / 2; _gel = math.radians(40.0)          # the centre lies out through the gap between stops 8 and 1, high above the ring
GHAT = np.array((math.cos(_gel) * math.cos(_gaz), math.cos(_gel) * math.sin(_gaz), math.sin(_gel)))
POLE = np.array((0.0, 0.0, 1.0)) - GHAT * GHAT[2]; POLE /= np.linalg.norm(POLE)
RGAL = np.stack([GHAT, np.cross(POLE, GHAT), POLE], 1)      # Galactic x (to the centre), y, z in the columns
RSUN = 8.15; GC = GHAT * RSUN * KPC

rg = np.random.default_rng(21)
PITCH = math.tan(math.radians(12.5))
def arm_angle(r):
    """Azimuth of the arm through the Sun at Galactocentric radius r in kpc; the Sun is at azimuth pi."""
    return np.log(np.maximum(r, 1.2) / RSUN) / PITCH + np.pi
def model_galaxy():
    """A thin disc with a bar and four arms, a thick disc, a bulge and a halo, in kpc about the Galactic centre."""
    def expo(n, h, rmax):
        r = rg.gamma(2.0, h, int(n * 1.6)); r = r[r < rmax]; return r[:n]
    n1 = 240000; r = expo(n1, 2.2, 15.0); n1 = len(r); arm = rg.integers(0, 4, n1)
    th = arm_angle(r) + arm * np.pi / 2
    keep = rg.random(n1) < 0.16; th = np.where(keep, rg.uniform(0, 2 * np.pi, n1), th + rg.normal(0, 0.07 + 0.03 * r, n1))
    thin = np.stack([r * np.cos(th), r * np.sin(th), rg.laplace(0, 0.13, n1)], 1)
    n2 = 50000; r = expo(n2, 1.1, 9.0); n2 = len(r); th = rg.uniform(0, 2 * np.pi, n2)
    thick = np.stack([r * np.cos(th), r * np.sin(th), rg.laplace(0, 0.75, n2)], 1)
    n3 = 40000; bar = rg.normal(0, 1, (n3, 3)) * (1.6, 0.55, 0.42); c = math.cos(math.radians(25)); s = math.sin(math.radians(25))
    bar = bar @ np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]])
    n4 = 14000; d = rg.normal(0, 1, (n4, 3)); d /= np.linalg.norm(d, axis=1, keepdims=True); halo = d * (rg.pareto(2.0, n4)[:, None] * 5 + 1.5); halo = halo[np.linalg.norm(halo, axis=1) < 26]
    P = np.concatenate([thin, thick, bar, halo])
    C = np.concatenate([np.repeat(BLUE[None], len(thin), 0) * (rg.uniform(0.5, 1.1, len(thin))[:, None]), np.repeat(BRASS[None], len(thick), 0) * rg.uniform(0.4, 0.9, len(thick))[:, None],
                        np.repeat(IVORY[None] * np.array((1.0, 0.9, 0.72)), len(bar), 0) * rg.uniform(0.35, 0.8, len(bar))[:, None], np.repeat(IVORY[None] * 0.4, len(halo), 0)])
    return P, C
MP, MC = model_galaxy()
MPS = MP.copy(); MPS[:, 0] = RSUN + MP[:, 0]                        # kpc from the Sun, x toward the centre
dsun = np.linalg.norm(MPS, axis=1); keep = rg.random(len(MPS)) < 0.3 + 0.7 * smoother((dsun - 2.5) / 3.5)   # toward the Sun the model gives way to the measured stars
MPS, MC = MPS[keep], MC[keep] * 0.4
n5 = 700; a5 = rg.uniform(0, 2 * np.pi, n5); r5 = 0.62 * np.sqrt(rg.random(n5))                # the giants' own gap round the Sun, closed with model disc stars
MPS = np.concatenate([MPS, np.stack([r5 * np.cos(a5), r5 * np.sin(a5), rg.laplace(0, 0.13, n5)], 1)]); MC = np.concatenate([MC, np.repeat(BLUE[None] * 0.32, n5, 0)])
real_x = GX.copy(); poor = GFE < -0.75
real_c = np.where(poor[:, None], BRASS[None] * 0.8, BLUE[None] * 0.95) * rg.uniform(0.5, 1.0, (len(GX), 1))
GP = np.concatenate([real_x, MPS]) * KPC @ RGAL.T; GC_C = np.concatenate([real_c, MC])
ISREAL = np.arange(len(GP)) < len(real_x)
kp_ = np.linalg.norm(GP, axis=1) > 24.0; GP, GC_C, ISREAL = GP[kp_], GC_C[kp_], ISREAL[kp_]   # nothing inside the ring's own neighbourhood
GALAXY = Obj('galaxy', *blobs(GP, 1.0, TET, TET_F), MAT['sky']); GALAXY.colour(rgba(np.repeat(GC_C, 4, 0)))
def set_star_size(cam_pos):
    """Every point keeps one size on the screen, wherever the camera stands."""
    far = float(smoother((math.log(max(np.linalg.norm(cam_pos), 1.0)) - math.log(400.0)) / math.log(6.0)))     # seen from outside the measured stars must not outshine the model
    r = 0.00062 * (1280 / args.w) * np.linalg.norm(GP - cam_pos, axis=1) * np.where(ISREAL, 1.0 - 0.8 * far, 1.0); GALAXY.move(blobs(GP, r, TET, TET_F)[0])

# ---------------------------------------------------------------------------------------------------- stop 1, the star
def ico(sub):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0); bm.verts.index_update(); bm.faces.index_update()
    V = np.array([v.co[:] for v in bm.verts]); F = np.array([[v.index for v in f.verts] for f in bm.faces]); bm.free(); return V, F

def shape_table(U):
    """Real spherical harmonics, by degree and order, as cosine and sine parts of the azimuth on the unit vectors U, each
    scaled to unit root mean square."""
    x, y, z = U.T; o = {}
    o[(0, 0)] = (np.ones(len(x)), 0 * x)
    o[(1, 0)] = (z, 0 * x); o[(1, 1)] = (x, y)
    o[(2, 0)] = ((3 * z ** 2 - 1) / 2, 0 * x); o[(2, 1)] = (x * z, y * z); o[(2, 2)] = (x ** 2 - y ** 2, 2 * x * y)
    o[(3, 0)] = ((5 * z ** 3 - 3 * z) / 2, 0 * x); o[(3, 2)] = (z * (x ** 2 - y ** 2), 2 * x * y * z); o[(3, 3)] = (x ** 3 - 3 * x * y ** 2, 3 * x ** 2 * y - y ** 3)
    for k, (a, b) in o.items():
        s = math.sqrt(np.mean(a ** 2 + b ** 2)); o[k] = (a / s, b / s)
    return o

BASE_CYCLES = round(LOOP / 2.4)                    # the radial mode's cycles per loop: about 2.4 seconds each
F0, F1, F2 = 123.65, 140.22, 133.16                # the three modes marked on the spectrum, microhertz
W0 = 2 * math.pi * BASE_CYCLES / LOOP; W1 = 2 * math.pi * round(BASE_CYCLES * F1 / F0) / LOOP; W2 = 2 * math.pi * round(BASE_CYCLES * F2 / F0) / LOOP

STAR_BASE = np.array((1.0, 0.68, 0.36)); STAR_HOT = np.array((1.0, 0.86, 0.66)); STAR_COOL = np.array((0.78, 0.36, 0.13))
_ta = math.radians(28.0); MODE_TILT = np.array([[1, 0, 0], [0, math.cos(_ta), -math.sin(_ta)], [0, math.sin(_ta), math.cos(_ta)]])
class Ringing:
    """A star whose surface moves with a sum of modes (degree, order, amplitude, angular speed). A raised part of the
    surface is hotter and brighter, a sunken part cooler and darker, as in the temperature term of a real mode."""
    def __init__(self, name, centre, radius, modes, sub, amp, gain, cells):
        U, F = ico(sub); self.U = U; self.c = np.asarray(centre, float); self.r = radius; self.amp = amp; self.modes = modes; self.gain = gain
        tb = shape_table(U @ MODE_TILT); self.b = [(tb[(l, abs(m))], a, w) for l, m, a, w in modes]
        self.o = Obj(name, self.c + U * radius, F, star_material(name, cells))
        self.o.me.polygons.foreach_set('use_smooth', np.ones(len(F), bool)); self.o.me.color_attributes.new('u3', 'FLOAT_COLOR', 'POINT')
        self.o.me.color_attributes['u3'].data.foreach_set('color', np.concatenate([U, np.ones((len(U), 1))], 1).ravel()); self.o.me.update()
    def __call__(self, t):
        d = 0.0
        for (A, B), a, w in self.b: d = d + a * (A * math.cos(w * t) + B * math.sin(w * t))
        self.o.move(self.c + self.U * (self.r * (1 + self.amp * d))[:, None])
        k = np.clip(d * self.gain, -1, 1)[:, None]; pos = np.clip(k, 0, 1); neg = np.clip(-k, 0, 1)
        self.o.colour(rgba(STAR_BASE[None] * (1 - pos - neg) + STAR_HOT[None] * 1.28 * pos + STAR_COOL[None] * 0.72 * neg))

def star_material(name, cells):
    """Emission from 'col' over a cellular granulation fixed to the surface, with solar limb darkening
    I(mu) = 1 - 0.55 (1 - mu) - 0.25 (1 - mu)^2 and a redder limb."""
    m = bpy.data.materials.new(name); nt, out = nodes(m); N = nt.nodes.new; L = nt.links.new; m.cycles.emission_sampling = 'NONE'
    def M(op, a, b=None, c=None):
        n = N('ShaderNodeMath'); n.operation = op
        for k, v in enumerate((a, b, c)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[k].default_value = v
            else: L(v, n.inputs[k])
        return n.outputs[0]
    a = N('ShaderNodeAttribute'); a.attribute_name = 'col'
    u = N('ShaderNodeAttribute'); u.attribute_name = 'u3'
    wob = N('ShaderNodeTexNoise'); wob.inputs['Scale'].default_value = cells * 0.45; wob.inputs['Detail'].default_value = 3.0; L(u.outputs['Vector'], wob.inputs['Vector'])
    vm = N('ShaderNodeVectorMath'); vm.operation = 'SCALE'; vm.inputs['Scale'].default_value = 0.9 / cells; sb = N('ShaderNodeVectorMath'); sb.operation = 'ADD'
    L(wob.outputs['Color'], vm.inputs[0]); L(u.outputs['Vector'], sb.inputs[0]); L(vm.outputs[0], sb.inputs[1])
    vo = N('ShaderNodeTexVoronoi'); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs['Scale'].default_value = cells; vo.inputs['Randomness'].default_value = 1.0; L(sb.outputs[0], vo.inputs['Vector'])
    gran = M('MULTIPLY_ADD', M('MINIMUM', M('DIVIDE', vo.outputs['Distance'], 0.3), 1.0), 0.13, 0.87)
    sup = N('ShaderNodeTexNoise'); sup.inputs['Scale'].default_value = cells * 0.16; sup.inputs['Detail'].default_value = 2.0; L(u.outputs['Vector'], sup.inputs['Vector'])
    gran = M('MULTIPLY', gran, M('MULTIPLY_ADD', sup.outputs['Fac'], 0.5, 0.75))
    lw = N('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5; f_ = lw.outputs['Facing']
    limb = M('SUBTRACT', M('SUBTRACT', 1.0, M('MULTIPLY', f_, 0.55)), M('MULTIPLY', M('MULTIPLY', f_, f_), 0.25))
    mc = N('ShaderNodeMix'); mc.data_type = 'RGBA'; mc.blend_type = 'MULTIPLY'; L(M('POWER', f_, 1.6), mc.inputs['Factor']); L(a.outputs['Color'], mc.inputs[6]); mc.inputs[7].default_value = (1.0, 0.42, 0.14, 1)
    e = N('ShaderNodeEmission'); L(mc.outputs[2], e.inputs['Color']); L(M('MULTIPLY', gran, M('MULTIPLY', limb, 1.15)), e.inputs['Strength']); L(e.outputs[0], out.inputs['Surface']); return m

s = ST['star']; STAR_P = s.w((0.0, 0.0, 0.0))
STAR = Ringing('star', STAR_P, 1.85, [(2, 2, 1.0, W2), (1, 1, 0.3, W1), (0, 0, 0.25, W0)], 7, 0.012, 0.8, 74.0)

# M13: every member at its place on the sky, depth drawn from a Plummer model about the projected radius
m13 = np.random.default_rng(13); xi, eta = M13['xi'], M13['eta']; Rp = np.hypot(xi, eta); a_ = 0.075
sv = []
while len(sv) < len(xi) * 2:
    u = m13.uniform(-1, 1, len(xi) * 3); sv = np.concatenate([sv, u[m13.random(len(u)) < 1 - u ** 2]])
sv = sv[:len(xi)]; z_los = np.sqrt(a_ ** 2 + Rp ** 2) * sv / np.sqrt(1 - sv ** 2)
z_los = np.clip(z_los, -0.3, 0.3)
M13_K = 9.5; M13_C = np.array((-5.3, 13.0, 2.65))
Pm = np.stack([xi * M13_K, z_los * M13_K, eta * M13_K], 1) + M13_C
fx = 10 ** (-0.4 * (M13['g'] - 16.5)); bprp = np.nan_to_num(M13['bprp'], nan=0.9)
cm = np.clip((bprp - 0.5) / 0.9, 0, 1)[:, None]; cc = BLUE_HI[None] * (1 - cm) + IVORY[None] * cm
cc = cc * np.clip(0.28 + 0.34 * fx ** 0.28, 0.2, 1.3)[:, None]; rr = np.clip(0.0085 + 0.0045 * fx ** 0.3, 0.0085, 0.036)
o = Obj('m13', *blobs(s.w(Pm), rr), MAT['pt']); o.colour(rgba(np.repeat(cc, 6, 0)))

# ---------------------------------------------------------------------------------------------------- stop 2, Kepler and TESS (placeholders)
s = ST['sats']
KEPLER_AP = np.array((-1.9, 0.0, 1.05)); TESS_AP = np.array((1.75, 0.0, 0.55))
TESS_C = np.array((1.75, 0, -0.1)); KEPLER_C = np.array((-1.9, 0, -0.1)); TESS_YAW = math.radians(float(os.environ.get('TESS_YAW', '-28')))
kepler_holder = link(bpy.data.objects.new('kepler_holder', None)); kepler_holder.matrix_world = Matrix.Translation(Vector(s.w(KEPLER_C)))
tess_root = link(bpy.data.objects.new('tess_root', None))
tess_root.matrix_world = Matrix.Translation(Vector(s.w(TESS_C))) @ Matrix(np.stack([s.x, s.y, s.z], 1).tolist()).to_4x4() @ Matrix.Rotation(TESS_YAW, 4, 'Z') @ Matrix.Rotation(math.pi / 2, 4, 'X')
if args.mode in ('still', 'frames') and os.environ.get('MISSIONS_COPY'):      # the accepted TESS, from a local copy of the mission script
    import importlib.util
    spec = importlib.util.spec_from_file_location('missions_copy', os.environ['MISSIONS_COPY']); MC = importlib.util.module_from_spec(spec); spec.loader.exec_module(MC)
    MC.stage = lambda *a_, **k_: None; MC._model(MC.build_tessb, tess_root, float(os.environ.get('TESS_SCALE', '0.62')))

# ---------------------------------------------------------------------------------------------------- stop 3, the light curve
LC_DAYS = 6.0
s = ST['lc']; LC_X0, LC_X1, LC_Z = -3.75, 3.75, 0.3; LC_A = 1.15 / np.abs(LC['flux']).max(); ls_ = LC['t'] <= LC_DAYS
lt = LC['t'][ls_] / LC_DAYS; lx = LC_X0 + (LC_X1 - LC_X0) * lt; lz = LC_Z + LC_A * LC['flux'][ls_]
ldense_x = np.linspace(LC_X0, LC_X1, 1800); ldense_z = np.interp(ldense_x, lx, lz)
LCV, LCF = tube(s.w(np.stack([ldense_x, np.zeros(1800), ldense_z], 1)), 0.0082, 5)
LC_LINE = Obj('lc', LCV, LCF, MAT['line'])
LCP = Obj('lc_pts', *blobs(s.w(np.stack([lx, np.zeros(len(lx)), lz], 1)), 0.0135), MAT['line'])
def set_lc(h):
    head = float(smoother((h + 0.2) / 2.2)) * 1.06; a = np.clip((head - np.linspace(0, 1, 1800)) / 0.015, 0, 1); hot = np.exp(-((np.linspace(0, 1, 1800) - head) / 0.02) ** 2) * (0 < head < 1.02)
    LC_LINE.colour(rgba(np.repeat(BLUE[None] * (1 + 2.0 * hot[:, None]), 5, 0), np.repeat(a, 5)))
    LCP.colour(rgba(np.repeat(BLUE[None] * 1.5, 6 * len(lx), 0), np.repeat(np.clip((head - lt) / 0.015, 0, 1), 6)))

# ---------------------------------------------------------------------------------------------------- stop 4, the power spectrum
s = ST['psd']; f, p = KIC['f'], KIC['p']; kp = (f > 96) & (f < 172); f, p = f[kp], p[kp]
ps = np.convolve(p, np.ones(7) / 7, 'same'); lf, lp = np.log(f), np.log(ps); bg_ = (f < 104) | (f > 160)
b1, b0 = np.polyfit(lf[bg_], lp[bg_], 1); snr = ps / np.exp(b0 + b1 * lf)
NB = 460; edges = np.linspace(f.min(), f.max(), NB + 1); idx = np.digitize(f, edges) - 1
HB = np.array([snr[idx == i].max() if np.any(idx == i) else 0 for i in range(NB)]); HB = np.clip(HB / np.percentile(HB, 99.7), 0, 1.1) ** 0.7
PX0, PX1, PZ, PH = -3.85, 3.85, -1.55, 2.25; FX = np.linspace(PX0, PX1, NB)
def nu_x(nu): return PX0 + (PX1 - PX0) * (nu - edges[0]) / (edges[-1] - edges[0])
PSD_BV, PSD_BF = bars(FX, None, np.full(NB, PZ), PZ + HB * PH + 0.002, 0.0, 0.0065)
PSD = Obj('psd', s.w(PSD_BV), PSD_BF, MAT['peak'])
_t = HB[:, None] ** 0.8; PSD_TOP = BLUE[None] * (0.55 + 0.6 * _t) + (BLUE_HI - BLUE)[None] * _t ** 2
PSD_BOT = BLUE[None] * 0.14
PSD.colour(rgba(np.repeat(np.stack([np.repeat(PSD_BOT, NB, 0), PSD_TOP], 1), 4, 1).reshape(-1, 3)))
PSD_EM = np.abs(FX - nu_x(131.6)) / (PX1 - PX0)
def set_psd(h):
    g = smoother((h + 0.3 - 2.2 * PSD_EM) / 1.1)
    z = np.repeat(np.stack([np.full(NB, PZ), PZ + (HB * PH) * g + 0.002], 1), 4, 1).reshape(-1)
    V = PSD_BV.copy(); V[:, 2] = z; PSD.move(s_psd.w(V))
s_psd = s
RING_Z = 1.55
SM = []
for nu, (l, m), x_ in ((F0, (0, 0), -1.5), (F2, (2, 2), 0.72), (F1, (1, 1), 2.25)):
    x_ = nu_x(nu) + (0.0 if l == 2 else (-0.15 if l == 0 else 0.35))
    w_ = {0: W0, 1: W1, 2: W2}[l]
    SM.append(Ringing(f'mode{l}', s.w((x_, 0, RING_Z)), 0.42, [(l, m, 1.0, w_)], 6, 0.03, 0.9, 30.0))
    top = PZ + np.interp(nu_x(nu), FX, HB) * PH
    hairline(f'lead{l}', s.w(np.array([(nu_x(nu), 0, top + 0.07), (x_, 0, RING_Z - 0.5)])), 0.0035, IVORY * 0.7, 'soft')

# ---------------------------------------------------------------------------------------------------- stop 5, Gaia
sys.path.insert(0, HERE)
from gaia_model import build_gaia
s = ST['gaia']; GAIA_TILT = math.radians(30.0); GAIA_S = 3.9 / 10.2
gaia = link(bpy.data.objects.new('gaia', None)); gaia.rotation_mode = 'XYZ'; build_gaia(gaia, GAIA_S, soft_foil=True)
GAIA_M0 = Matrix.Translation(Vector(s.w((0.0, 0.0, -0.35)))) @ Matrix(np.stack([s.x, s.y, s.z], 1).tolist()).to_4x4() @ Matrix.Rotation(GAIA_TILT, 4, 'X')
GAIA_S_M = Matrix.Diagonal((GAIA_S, GAIA_S, GAIA_S, 1.0))
GAIA_W = 2 * math.pi * 2 / LOOP * 2                 # two and a bit turns are too quick to read; four per loop at this length is slow enough
def set_gaia(t):
    gaia.matrix_world = GAIA_M0 @ Matrix.Rotation(GAIA_W * t, 4, 'Z') @ GAIA_S_M
GAIA_AXIS = np.array(GAIA_M0.to_3x3() @ Vector((0, 0, 1))); GAIA_BASE = np.array(GAIA_M0.translation)

# ---------------------------------------------------------------------------------------------------- stop 6, the XP spectrum
s = ST['xp']; XX0, XX1, XZ0, XH = -3.8, 3.8, -0.75, 2.45
xn = (XP - XP.min()) / (XP.max() - XP.min()); xx = np.linspace(XX0, XX1, len(XP)); xz = XZ0 + 0.12 + XH * xn
xd = np.linspace(XX0, XX1, 1400); xdz = np.interp(xd, xx, xz)
XPV, XPF = tube(s.w(np.stack([xd, np.zeros(1400), xdz], 1)), 0.0095, 5); XP_LINE = Obj('xp', XPV, XPF, MAT['line'])
def set_xp(h):
    q = np.linspace(0, 1, 1400); head = float(smoother((h + 0.2) / 2.0)) * 1.06; a = np.clip((head - q) / 0.012, 0, 1); hot = np.exp(-((q - head) / 0.018) ** 2) * (0 < head < 1.02)
    XP_LINE.colour(rgba(np.repeat(BLUE[None] * 1.35 * (1 + 2.0 * hot[:, None]), 5, 0), np.repeat(a, 5)))

# ---------------------------------------------------------------------------------------------------- stop 7, JANUS
s = ST['janus']
def flow_samples(n):
    """A two-dimensional Gaussian pushed through five coupling layers, as in figures/janus/build_janus.py."""
    z = np.random.default_rng(11).normal(size=(n, 2)); z = z[np.hypot(*z.T) < 2.6]; x, y = z[:, 0].copy(), z[:, 1].copy()
    o = [np.c_[x, y]]; y = y + 0.25 * np.tanh(x); o.append(np.c_[x, y]); x = x + 0.45 * np.sin(1.1 * y); o.append(np.c_[x, y])
    y = 0.42 * y + 1.0 * np.tanh(2.6 * y); o.append(np.c_[x, y]); x = x * (0.5 + 0.12 * np.tanh(y)) - 0.8 * np.tanh(1.5 * y); o.append(np.c_[x, y])
    y = 1.0 * y - 0.16 * x + 0.25; o.append(np.c_[x, y]); return np.stack(o, 1)
JZ = 0.35; XS_J = np.array((-1.5, -0.65, 0.2, 1.05, 1.9)); XO_J = 3.75; JP, JPZ = 2.5, 2.5; JK = 0.5
FS = flow_samples(1500); NS = FS.shape[0]
def layer_xyz(k, ab):
    """Local position on layer k: five panes across the axis, then the output plate facing the viewer."""
    k = np.broadcast_to(k, (len(ab),))
    return np.where((k < 5)[:, None], np.stack([XS_J[np.minimum(k, 4)], JK * ab[:, 0], JZ + JK * ab[:, 1]], 1), np.stack([XO_J + JK * ab[:, 0], 0 * ab[:, 0], JZ + JK * ab[:, 1]], 1))
def flow_at(i, q):
    """World position of samples i at fractional layer q."""
    a = np.clip(np.floor(q).astype(int), 0, 4); u = smoother(q - a)[:, None]
    p0 = layer_xyz(a, FS[i, a]); p1 = layer_xyz(a + 1, FS[i, a + 1]); return s.w(p0 * (1 - u) + p1 * u)
lobe = FS[:, -1, 1] > 0.3
for k in range(6):
    if k < 5: plate(f'jp{k}', s, (XS_J[k], 0, JZ), JP, JPZ, normal_x=True)
    else: plate('jp5', s, (XO_J, 0, JZ), JP, JPZ)
    col = np.where((k > 2) & lobe[:, None], BRASS[None] * 0.95, BLUE[None] * 1.1)
    o = Obj(f'jd{k}', *blobs(s.w(layer_xyz(k, FS[:, k])), 0.0125), MAT['pt']); o.colour(rgba(np.repeat(col, 6, 0)))
tr_i = np.arange(0, NS, NS // 90)
for j, i in enumerate(tr_i):
    q = np.linspace(0, 5, 110); hairline(f'jt{j}', flow_at(np.full(110, i), q), 0.0016, BLUE * 0.8, 'soft')
FLOW_N = 260; FLOW_I = np.random.default_rng(3).integers(0, NS, FLOW_N); FLOW_Q = np.random.default_rng(4).random(FLOW_N)
FLOW = Obj('jflow', *blobs(flow_at(FLOW_I, np.zeros(FLOW_N)), 0.02), MAT['line'])
FLOW_W = max(1, round(LOOP / 2.2))
def set_flow(t):
    q = (FLOW_Q + FLOW_W * t / LOOP) % 1.0; FLOW.move(blobs(flow_at(FLOW_I, q * 5), 0.02)[0])
    FLOW.colour(rgba(np.repeat(WHITE[None] * 1.2, 6 * FLOW_N, 0), np.repeat(np.sin(np.pi * q) ** 0.5, 6)))
# the seven other members of the ensemble, behind the first and last pane
for e in range(1, 8):
    for x_ in XS_J[[0, -1]]:
        hairline(f'je{e}_{x_}', s.w(np.array((x_, 0.0, JZ)) + np.array((0.0, 0.17 * e, 0.11 * e)) + np.array([(0, a, b) for a, b in ((-JP / 2, -JPZ / 2), (JP / 2, -JPZ / 2), (JP / 2, JPZ / 2), (-JP / 2, JPZ / 2), (-JP / 2, -JPZ / 2))])), 0.0025, BLUE * 0.7, 'hair')
# the spectrum as it enters, and the trunk of four dense layers
J_SX0, J_SX1 = -5.0, -3.6; J_SZ0 = JZ - 0.45
Psp = np.stack([np.linspace(J_SX0, J_SX1, 343), np.zeros(343), J_SZ0 + 1.1 * xn], 1); hairline('jspec', s.w(Psp), 0.0085, BLUE * 1.35, 'line')
cols = [-3.2, -2.8, -2.4, -2.0]; NYJ = 7; ys = (np.arange(NYJ) - (NYJ - 1) / 2) * 0.3
for a, b in zip(cols[:-1], cols[1:]):
    for y0 in ys:
        for y1 in ys: hairline(f'jw{a}{y0}{y1}', s.w(np.array([(a, 0, JZ + y0), (b, 0, JZ + y1)])), 0.0014, IVORY * 0.42, 'hair')
for y0 in ys:
    hairline(f'jwa{y0}', s.w(np.array([(J_SX1 + 0.3, 0, JZ), (cols[0], 0, JZ + y0)])), 0.0014, IVORY * 0.42, 'hair')
    hairline(f'jwb{y0}', s.w(np.array([(cols[-1], 0, JZ + y0), (XS_J[0], 0, JZ)])), 0.0014, IVORY * 0.42, 'hair')
nodes_ = np.array([(c, 0, JZ + y) for c in cols for y in ys]); o = Obj('jn', *blobs(s.w(nodes_), 0.03), MAT['pt']); o.colour(rgba(np.repeat(IVORY[None], len(nodes_) * 6, 0)))
# the labels with their spread: the marginals of the final cloud, along the top and side of the output plate
ev = np.linspace(-2.4, 2.4, 90)
def kde(v, w=0.11):
    d_ = np.exp(-0.5 * ((ev[None] - v[:, None]) / w) ** 2).sum(0); return d_ / d_.max()
my = kde(FS[:, -1, 0]); mz = kde(FS[:, -1, 1])
hairline('jm0', s.w(np.stack([XO_J + JK * ev, np.zeros(90), np.full(90, JZ + JPZ / 2 + 0.04) + 0.5 * my], 1)), 0.006, BLUE * 1.35, 'line')
hairline('jm1', s.w(np.stack([np.full(90, XO_J + JP / 2 + 0.04) + 0.5 * mz, np.zeros(90), JZ + JK * ev], 1)), 0.006, BLUE * 1.35, 'line')

# ---------------------------------------------------------------------------------------------------- stop 8, Starfold
s = ST['fold']; FS_Z = 0.15; lo, hi = MAP.min(0), MAP.max(0); MAP_L, MARGIN = 5.6, 0.45; SL_ = MAP_L + 2 * MARGIN; kf = MAP_L / (hi[0] - lo[0]); HZ = (hi[1] - lo[1]) * kf + 0.25
S_ = MARGIN + (MAP[:, 0] - lo[0]) * kf; Z_ = (MAP[:, 1] - (lo[1] + hi[1]) / 2) * kf; NSF = len(S_)
big = 1
FCOL = np.where(GRP[:, None] == 1, BLUE[None], np.where(GRP[:, None] < 0, GRAPH[None] * 0.55, BRASS[None]))
FE0, FE1, AL0, AL1 = -1.2, 0.5, -0.12, 0.40; PW_, PH_, PY_ = 3.2, 3.5, -0.9
P0_ = np.stack([(FE - (FE0 + FE1) / 2) / (FE1 - FE0) * PW_, np.full(NSF, PY_), (AL - (AL0 + AL1) / 2) / (AL1 - AL0) * PH_], 1)
rf = np.random.default_rng(1); rank = np.argsort(np.argsort(-AL)) / (NSF - 1); DELAY = 0.7 * rank + 0.3 * rf.random(NSF); BOW = 0.45 + 0.4 * rf.random(NSF)
R0_, B_ = 0.17, 0.066; SS = np.linspace(0, SL_, 2401); KAP = 1 / np.sqrt(R0_ ** 2 + 2 * B_ * SS); WF = 0.27
def centreline(p):
    front = (SL_ + 3 * WF) * (1 - p) - 6 * WF * p; kap = KAP / (1 + np.exp(-(front - SS) / WF))
    cum = np.concatenate([[0], np.cumsum((kap[1:] + kap[:-1]) / 2 * np.diff(SS))]); th = cum - cum[-1]
    dx, dy = np.cos(th), np.sin(th); ds = np.diff(SS)
    x = np.concatenate([[0], np.cumsum((dx[1:] + dx[:-1]) / 2 * ds)]); y = np.concatenate([[0], np.cumsum((dy[1:] + dy[:-1]) / 2 * ds)])
    return x - x.mean(), y - y.mean()
FOFF = np.array((0.0, 0.0, FS_Z))
FSTARS = Obj('fold', *blobs(s.w(P0_ + FOFF), 0.0125), MAT['pt']); FSTARS.colour(rgba(np.repeat(FCOL, 6, 0)))
FAD = {'plate': [], 'sheet': []}
NU, NV = 220, 10; us = np.linspace(0, SL_, NU); vz = np.linspace(-HZ / 2, HZ / 2, NV); GU, GV = np.meshgrid(us, vz)
bm = bmesh.new()
for _ in range(NU * NV): bm.verts.new((0, 0, 0))
bm.verts.ensure_lookup_table()
for j in range(NV - 1):
    for i in range(NU - 1): bm.faces.new([bm.verts[j * NU + i], bm.verts[j * NU + i + 1], bm.verts[(j + 1) * NU + i + 1], bm.verts[(j + 1) * NU + i]])
sme = bpy.data.meshes.new('sheet'); bm.to_mesh(sme); bm.free()
for poly in sme.polygons: poly.use_smooth = True
SHEET = link(bpy.data.objects.new('sheet', sme)); sme.materials.append(faded(glass('fglass'), FAD['sheet'])); SHEET.visible_shadow = False
def curve_obj(name, splines, depth, m):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = depth; cu.bevel_resolution = 0
    for npts in splines:
        sp = cu.splines.new('POLY'); sp.points.add(npts - 1)
    ob = link(bpy.data.objects.new(name, cu)); cu.materials.append(m); ob.visible_shadow = False; return ob
RUL = np.linspace(0, SL_, 10)[1:-1]; LEV = np.linspace(-HZ / 2, HZ / 2, 7)[1:-1]; NLN = 300; SLN = np.linspace(0, SL_, NLN)
LINES = curve_obj('flines', [2] * len(RUL) + [NLN] * len(LEV), 0.0028, faded(plain('fl', (0.42, 0.52, 0.70), 0.5), FAD['sheet']))
EDGE = curve_obj('fedge', [2, 2, NLN, NLN], 0.0042, faded(plain('fe', (0.45, 0.62, 1.0), 1.1), FAD['sheet']))
def set_spline(sp, pts):
    sp.points.foreach_set('co', np.concatenate([s_fold.w(pts + FOFF), np.ones((len(pts), 1))], 1).ravel())
s_fold = s
wpl = s.w(np.array([(-PW_ / 2, PY_, -PH_ / 2), (PW_ / 2, PY_, -PH_ / 2), (PW_ / 2, PY_, PH_ / 2), (-PW_ / 2, PY_, PH_ / 2)]) + FOFF)
pme = bpy.data.meshes.new('fplate'); pme.from_pydata(wpl.tolist(), [], [(0, 1, 2, 3)]); link(bpy.data.objects.new('fplate', pme)); pme.materials.append(faded(glass('pglass'), FAD['plate']))
RFE, RAL = (-1.0, -0.5, 0.0), (0.0, 0.1, 0.2, 0.3); pmx = lambda v: (v - (FE0 + FE1) / 2) / (FE1 - FE0) * PW_; pmz = lambda v: (v - (AL0 + AL1) / 2) / (AL1 - AL0) * PH_
PR = curve_obj('fprules', [2] * (len(RFE) + len(RAL)), 0.0028, faded(plain('fpr', (0.42, 0.52, 0.70), 0.5), FAD['plate']))
PF = curve_obj('fpframe', [5], 0.0042, faded(plain('fpf', (0.45, 0.62, 1.0), 1.1), FAD['plate']))
for i, v in enumerate(RFE): set_spline(PR.data.splines[i], np.array([(pmx(v), PY_, -PH_ / 2), (pmx(v), PY_, PH_ / 2)]))
for i, v in enumerate(RAL): set_spline(PR.data.splines[len(RFE) + i], np.array([(-PW_ / 2, PY_, pmz(v)), (PW_ / 2, PY_, pmz(v))]))
set_spline(PF.data.splines[0], np.array([(-PW_ / 2, PY_, -PH_ / 2), (PW_ / 2, PY_, -PH_ / 2), (PW_ / 2, PY_, PH_ / 2), (-PW_ / 2, PY_, PH_ / 2), (-PW_ / 2, PY_, -PH_ / 2)]))
F_HOLD, F_TRAVEL, F_STAG, F_U0, F_U1 = 0.3, 1.2, 0.8, 2.3, 4.5
def set_fold(h):
    q = smoother((h - F_HOLD - F_STAG * DELAY) / F_TRAVEL); p = float(smoother((h - F_U0) / (F_U1 - F_U0)))
    cx, cy = centreline(p); P = P0_ + (np.stack([np.interp(S_, SS, cx), np.interp(S_, SS, cy), Z_], 1) - P0_) * q[:, None]; P[:, 1] -= BOW * np.sin(np.pi * q)
    FSTARS.move(blobs(s_fold.w(P + FOFF), 0.0125)[0])
    sme.vertices.foreach_set('co', s_fold.w(np.stack([np.interp(GU.ravel(), SS, cx), np.interp(GU.ravel(), SS, cy), GV.ravel()], 1) + FOFF).ravel()); sme.update()
    ex, ey = np.interp(SLN, SS, cx), np.interp(SLN, SS, cy); sp = LINES.data.splines
    for i, u in enumerate(RUL):
        x, y = np.interp(u, SS, cx), np.interp(u, SS, cy); set_spline(sp[i], np.array([(x, y, -HZ / 2), (x, y, HZ / 2)]))
    for j, z in enumerate(LEV): set_spline(sp[len(RUL) + j], np.stack([ex, ey, np.full(NLN, z)], -1))
    se = EDGE.data.splines
    for j, i in ((0, 0), (1, -1)): set_spline(se[j], np.array([(cx[i], cy[i], -HZ / 2), (cx[i], cy[i], HZ / 2)]))
    set_spline(se[2], np.stack([ex, ey, np.full(NLN, -HZ / 2)], -1)); set_spline(se[3], np.stack([ex, ey, np.full(NLN, HZ / 2)], -1))
    LINES.data.update_tag(); EDGE.data.update_tag()
    fd = float(smoother((h - 0.4) / 1.2))
    for k_ in FAD['plate']: k_.default_value = 1 - fd
    for k_ in FAD['sheet']: k_.default_value = fd

# ---------------------------------------------------------------------------------------------------- the thread
def seg(a, ma, b, mb, n): return bez(np.asarray(a, float), np.asarray(ma, float), np.asarray(b, float), np.asarray(mb, float), n)[:-1]
def hop(sa, pa, sb, pb, n=170):
    """Between two stations, leaving along +x of the first and arriving along +x of the second."""
    A = ST[sa].w(pa); B = ST[sb].w(pb); L = np.linalg.norm(B - A); return seg(A, ST[sa].x * L, B, ST[sb].x * L, n)
def run(st, pa, pb, n=60):
    return seg(ST[st].w(pa), ST[st].d((np.array(pb) - np.array(pa))), ST[st].w(pb), ST[st].d((np.array(pb) - np.array(pa))), n)
PATH = []
a = lambda *x: np.array(x, float)
PATH.append(hop('star', a(0, 0, 0), 'sats', a(-2.9, 0, 1.05)))                            # out of the star, on to Kepler
PATH.append(run('sats', a(-2.9, 0, 1.05), a(2.9, 0, 0.55)))                                # through the two craft
def curve(st, x, z):
    """The thread running as the data curve itself; a thinner tube, which the blue line covers as it is drawn."""
    c = ST[st].w(np.stack([x, np.zeros(len(x)), z], 1))[:-1]; THIN.add(id(c)); PATH.append(c)
THIN = set()
PATH.append(hop('sats', a(2.9, 0, 0.55), 'lc', a(ldense_x[0], 0, ldense_z[0])))
curve('lc', ldense_x, ldense_z)                                                            # the light curve is the thread
PATH.append(hop('lc', a(ldense_x[-1], 0, ldense_z[-1]), 'psd', a(PX0 - 0.6, 0, PZ)))
PATH.append(run('psd', a(PX0 - 0.6, 0, PZ), a(PX1 + 0.6, 0, PZ)))                          # the frequency axis
g0 = GAIA_BASE - GAIA_AXIS * 1.6; g1 = GAIA_BASE + GAIA_AXIS * 2.2; sg = ST['gaia']
PATH.append(seg(ST['psd'].w(a(PX1 + 0.6, 0, PZ)), ST['psd'].x * 12, g0, GAIA_AXIS * 7, 170))    # up the spin axis
PATH.append(seg(g0, GAIA_AXIS * 3.8, g1, GAIA_AXIS * 3.8, 60))
PATH.append(seg(g1, GAIA_AXIS * 3 + ST['gaia'].x * 4, ST['xp'].w(a(xd[0], 0, xdz[0])), ST['xp'].x * 14, 170))
curve('xp', xd, xdz)                                                                       # the spectrum is the thread
PATH.append(hop('xp', a(xd[-1], 0, xdz[-1]), 'janus', a(J_SX0, 0, Psp[0, 2])))
curve('janus', Psp[:, 0], Psp[:, 2])                                                       # and so is its copy entering the network
PATH.append(seg(ST['janus'].w(a(J_SX1, 0, Psp[-1, 2])), ST['janus'].x * 0.7, ST['janus'].w(a(J_SX1 + 0.3, 0, JZ)), ST['janus'].x * 0.7, 30))
PATH.append(run('janus', a(J_SX1 + 0.3, 0, JZ), a(XS_J[0], 0, JZ)))
PATH.append(run('janus', a(XS_J[0], 0, JZ), a(XO_J, 0.02, JZ)))                            # the axis of the flow, to the middle of the output plate
PATH.append(run('janus', a(XO_J, 0.02, JZ), a(XO_J + 1.6, 0.02, JZ), 20))
PATH.append(hop('janus', a(XO_J + 1.6, 0.02, JZ), 'fold', a(-4.2, 0.3, FS_Z)))
PATH.append(run('fold', a(-4.2, 0.3, FS_Z), a(5.6, 0.3, FS_Z)))                            # behind the sheet, along its middle
FOLD_OUT = ST['fold'].w(a(5.6, 0.3, FS_Z))
PATH.append(seg(FOLD_OUT, ST['fold'].x * 14, GC, -POLE * 700, 900))                        # up and over, down into the exact Galactic centre
Rs = np.linspace(0.0, 7.2, 900); th_sp = arm_angle(Rs)                                     # out along the arm that holds the Sun
sp_w = (np.stack([Rs * np.cos(th_sp) + RSUN, Rs * np.sin(th_sp), 0 * Rs], 1) * KPC) @ RGAL.T
PATH.append(sp_w[:-1])
tg = sp_w[-1] - sp_w[-2]; tg = tg / np.linalg.norm(tg) * 500                               # and from the arm straight home to the star
PATH.append(seg(sp_w[-1], tg, STAR_P, -GHAT * 60, 500))
PTS = np.concatenate(PATH + [PATH[0][:1]]); dO = np.linalg.norm(PTS, axis=1)
TR = 0.0105 * np.maximum(1.0, dO / 18.0) ** 1.35 * np.concatenate([np.full(len(c_), 0.52 if id(c_) in THIN else 1.0) for c_ in PATH] + [[1.0]])
ds = np.linalg.norm(np.diff(PTS, axis=0), axis=1); TU = np.concatenate([[0], np.cumsum(ds / (TR[:-1] / TR[0]))])
DASH = TU[-1] / max(1, round(TU[-1] / 0.8))         # a whole number of dashes round the circuit
TV, TF = tube(PTS, TR, 6); THR = Obj('thread', TV, TF, thread_material(DASH))
c_ = np.zeros((len(TV), 4)); c_[:, 0] = np.repeat(TU, 6); c_[:, 3] = 1.0; THR.colour(c_)
DASH_CYCLES = max(1, round(LOOP / 0.7))             # whole dash periods moved per loop

# ---------------------------------------------------------------------------------------------------- stage, lamps
def mirror_sky(base, R_):
    """Only mirrors see this: the all-sky map of the Milky Way, the same reflection the Gaia turntable has."""
    w = bpy.data.worlds.new('sky'); sc.world = w; w.use_nodes = True; nt = w.node_tree; N = nt.nodes.new; L = nt.links.new
    out = nt.nodes['World Output']; bg = nt.nodes['Background']; bg.inputs['Color'].default_value = (*base, 1)
    tc = N('ShaderNodeTexCoord'); mp = N('ShaderNodeMapping'); L(tc.outputs['Generated'], mp.inputs['Vector']); mp.inputs['Rotation'].default_value = tuple(R_.to_euler('XYZ'))
    tx = N('ShaderNodeTexEnvironment'); tx.image = bpy.data.images.load(ROOT + 'assets/img/heroes/research_allsky.webp'); L(mp.outputs[0], tx.inputs['Vector'])
    gain = N('ShaderNodeVectorMath'); gain.operation = 'SCALE'; gain.inputs['Scale'].default_value = 2.6; L(tx.outputs['Color'], gain.inputs[0])
    flo = N('ShaderNodeVectorMath'); flo.operation = 'ADD'; flo.inputs[1].default_value = (0.2, 0.25, 0.34); L(gain.outputs[0], flo.inputs[0])
    b2 = N('ShaderNodeBackground'); L(flo.outputs[0], b2.inputs['Color'])
    lp = N('ShaderNodeLightPath'); mx = N('ShaderNodeMixShader'); L(lp.outputs['Is Glossy Ray'], mx.inputs['Fac']); L(bg.outputs[0], mx.inputs[1]); L(b2.outputs[0], mx.inputs[2]); L(mx.outputs[0], out.inputs['Surface'])
# the turntable's rig carried over: its camera's azimuth about the craft lands on this stop's camera, so the light falls the same way
G_LEAN = Matrix.Rotation(math.radians(-6), 3, 'X'); c_g = G_LEAN.inverted() @ Vector((0.783 * 17.02, -0.621 * 17.02, 6.1))
M0_R = GAIA_M0.to_3x3(); c_r = M0_R.inverted() @ (Vector(ST['gaia'].w((0.0, -8.6, 0.6))) - GAIA_M0.translation)
G_R = M0_R @ Matrix.Rotation(math.atan2(c_r.y, c_r.x) - math.atan2(c_g.y, c_g.x), 3, 'Z') @ G_LEAN.inverted()
mirror_sky((0.0022, 0.0026, 0.0038), Matrix.Rotation(math.radians(38), 3, 'Z') @ Matrix.Rotation(math.radians(-22), 3, 'X') @ G_R.inverted())
ld = bpy.data.lights.new('sun', 'SUN'); ld.energy = 3.2; ld.color = (1.0, 0.96, 0.9); ld.angle = 0.02
lo_ = link(bpy.data.objects.new('sun', ld)); lo_.rotation_euler = (Vector((-0.5, 0.3, -0.7))).to_track_quat('-Z', 'Y').to_euler()
l2 = bpy.data.lights.new('fill', 'SUN'); l2.energy = 0.25; l2.color = (0.6, 0.72, 1.0)
lo2 = link(bpy.data.objects.new('fill', l2)); lo2.rotation_euler = (Vector((0.6, -0.4, 0.3))).to_track_quat('-Z', 'Y').to_euler()
g_set = bpy.data.collections.new('gaia_lit'); not_g = bpy.data.collections.new('not_gaia')
for o_ in gaia.children: g_set.objects.link(o_); not_g.objects.link(o_)
for o_ in (lo_, lo2):                                # the stage's lamps leave Gaia alone; it keeps the turntable's own
    o_.light_linking.receiver_collection = not_g
for co_ in not_g.collection_objects: co_.light_linking.link_state = 'EXCLUDE'
def g_lamp(kind, loc, energy, col, size=1.0):
    ld_ = bpy.data.lights.new('g_' + kind + str(loc), kind); ld_.energy = energy; ld_.color = col
    if kind == 'AREA': ld_.size = size * GAIA_S; ld_.energy = energy * GAIA_S ** 2
    if kind == 'SUN': ld_.angle = math.radians(1.0)
    ob_ = link(bpy.data.objects.new(ld_.name, ld_)); ob_.location = GAIA_M0.translation + G_R @ (Vector(loc) * GAIA_S)
    tg_ = GAIA_M0.translation + G_R @ Vector((0, 0, GAIA_S)); ob_.rotation_euler = (tg_ - ob_.location).to_track_quat('-Z', 'Y').to_euler(); ob_.light_linking.receiver_collection = g_set
g_lamp('SUN', (14, -10, 4), 2.8, (1.0, 0.92, 0.82)); g_lamp('AREA', (-9, 9, 6), 900, (0.62, 0.74, 1.0), 6); g_lamp('AREA', (6, -14, -2), 500, (1.0, 0.85, 0.7), 8)
# the low band of warm metal the near foil mirrors
n_ = 96; V_ = []; F_ = []
for k_ in range(n_):
    a_ = 2 * math.pi * k_ / n_
    for z_ in (0.04, 1.0): V_.append((1.86 * math.cos(a_), 1.86 * math.sin(a_), z_))
for k_ in range(n_): F_.append((2 * k_, 2 * ((k_ + 1) % n_), 2 * ((k_ + 1) % n_) + 1, 2 * k_ + 1))
me_ = bpy.data.meshes.new('band'); me_.from_pydata(V_, [], F_); me_.update(); m_ = bpy.data.materials.new('band'); m_.use_nodes = True; nt_ = m_.node_tree; b_ = nt_.nodes['Principled BSDF']
b_.inputs['Base Color'].default_value = (0.88, 0.8, 0.68, 1); b_.inputs['Metallic'].default_value = 1.0; b_.inputs['Roughness'].default_value = 0.32
tr_ = nt_.nodes.new('ShaderNodeBsdfTransparent'); ge_ = nt_.nodes.new('ShaderNodeNewGeometry'); mx_ = nt_.nodes.new('ShaderNodeMixShader')
nt_.links.new(ge_.outputs['Backfacing'], mx_.inputs[0]); nt_.links.new(b_.outputs[0], mx_.inputs[1]); nt_.links.new(tr_.outputs[0], mx_.inputs[2]); nt_.links.new(mx_.outputs[0], nt_.nodes['Material Output'].inputs['Surface'])
me_.materials.append(m_); band_ = link(bpy.data.objects.new('band', me_)); band_.matrix_world = GAIA_M0 @ GAIA_S_M
band_.visible_camera = band_.visible_shadow = band_.visible_diffuse = band_.visible_transmission = band_.visible_volume_scatter = False
sc.use_nodes = True; ct = sc.node_tree
gg = ct.nodes.new('CompositorNodeGlare'); gg.glare_type = 'FOG_GLOW'; gg.quality = 'MEDIUM'; gg.size = 6; gg.threshold = 0.7; gg.mix = -0.7
ct.links.new(ct.nodes['Render Layers'].outputs['Image'], gg.inputs['Image']); ct.links.new(gg.outputs['Image'], ct.nodes['Composite'].inputs['Image'])

# ---------------------------------------------------------------------------------------------------- the camera
cd = bpy.data.cameras.new('cam'); cd.lens = 40; cd.clip_start = 0.05; cd.clip_end = 40000
cam = link(bpy.data.objects.new('cam', cd)); sc.camera = cam; cam.rotation_mode = 'QUATERNION'
CAM = {  # local position, local target
    'star': ((-1.15, -8.9, 0.1), (-1.15, 0, 0.1)),
    'sats': ((0.0, -8.8, 0.1), (0.0, 0, 0.1)),
    'lc': ((0.0, -8.8, 0.45), (0.0, 0, 0.0)),
    'psd': ((0.0, -8.8, 0.35), (0.0, 0, 0.0)),
    'gaia': ((0.0, -8.6, 0.6), (0.0, 0, 0.2)),
    'xp': ((0.0, -8.8, 0.45), (0.0, 0, 0.1)),
    'janus': ((-1.5, -12.4, 1.2), (0.05, 0, 0.0)),
    'fold': ((-0.2, -9.6, 0.6), (0.0, 0, 0.0)),
}
def cyl(p): return math.atan2(p[1], p[0]), math.hypot(p[0], p[1]), p[2]
POSE = {n: (ST[n].w(CAM[n][0]), ST[n].w(CAM[n][1])) for n in STN}
MW_D = 3700.0; _i = math.radians(47.0); MW_DIR = math.cos(_i) * POLE - math.sin(_i) * GHAT
_r = np.cross(-MW_DIR, (0.0, 0.0, 1.0)); _r /= np.linalg.norm(_r); _u = np.cross(_r, -MW_DIR)
MW_T = GC - _r * 330.0 - _u * 40.0                  # the Galactic centre sits right of the middle, the Sun below it
MW_P = MW_T + MW_DIR * MW_D
Z_UP = np.array((0.0, 0.0, 1.0))

def logpath(a, b, e, dmin=3.0):
    """From a to b, the distance covered growing exponentially with e, so the view opens at a steady rate."""
    k = math.log(max(np.linalg.norm(b - a) / dmin, 1.001)); return a + (b - a) * (math.exp(k * e) - 1) / (math.exp(k) - 1)

def slerp(a, b, u):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b); w = math.acos(np.clip(np.dot(a, b), -1, 1))
    if w < 1e-6: return a
    return (math.sin((1 - u) * w) * a + math.sin(u * w) * b) / math.sin(w)

EPS = 0.012
def camera_at(t):
    """Camera position, target and up vector at time t."""
    k, dt = stop_of(t); name, h, tr = STOPS[k]; D = h + tr; u = float(smoother((dt - h) / tr)); w = (1 - EPS) * u + EPS * dt / D
    if name in STN and name != 'fold':
        nx = KEY[k + 1]; (p0, t0), (p1, t1) = POSE[name], POSE[nx]
        def mix_cyl(a, b):
            ta, ra, za = cyl(a); tb, rb, zb = cyl(b); dth = (tb - ta + math.pi) % (2 * math.pi) - math.pi
            th = ta + dth * w; r_ = ra + (rb - ra) * w; return np.array((r_ * math.cos(th), r_ * math.sin(th), za + (zb - za) * w))
        return mix_cyl(p0, p1), mix_cyl(t0, t1), Z_UP
    if name == 'fold':
        if dt <= h: return POSE['fold'][0], POSE['fold'][1], Z_UP
        p0, t0 = POSE['fold']; return logpath(p0, MW_P, u), logpath(t0, MW_T, u), Z_UP
    if dt <= h: return MW_P, MW_T, Z_UP                 # the Milky Way
    p1, t1 = POSE['star']; return logpath(p1, MW_P, 1 - u), logpath(t1, MW_T, 1 - u), Z_UP

def place_camera(pos, tgt, up):
    f_ = np.asarray(tgt) - pos; f_ /= np.linalg.norm(f_); r_ = np.cross(f_, up); r_ /= np.linalg.norm(r_); u_ = np.cross(r_, f_)
    M = Matrix(np.stack([r_, u_, -f_], 1).tolist()); cam.location = Vector(pos); cam.rotation_quaternion = M.to_quaternion()
    lo_.rotation_mode = 'QUATERNION'; lo_.rotation_quaternion = Vector(0.55 * r_ - 0.6 * u_ + 0.6 * f_).to_track_quat('-Z', 'Y')   # the Sun keeps over the viewer's left shoulder

SKY = {'star': 0.38, 'sats': 0.26, 'lc': 0.05, 'psd': 0.05, 'gaia': 0.26, 'xp': 0.05, 'janus': 0.04, 'fold': 0.04, 'mw': 0.8}
def sky_at(t):
    k, dt = stop_of(t); name, h, tr = STOPS[k]; nx = KEY[(k + 1) % N_ST]; u = float(smoother((dt - h) / tr))
    if name == 'fold': u = u ** 3
    if name == 'mw': u = 1 - (1 - u) ** 3
    return SKY[name] + (SKY[nx] - SKY[name]) * u

# ---------------------------------------------------------------------------------------------------- one frame
ACT = {'star': (('mw', 'star', 'sats'), lambda t: STAR(t)), 'modes': (('lc', 'psd', 'gaia'), lambda t: [m(t) for m in SM]),
       'gaia': (('psd', 'gaia', 'xp'), set_gaia), 'flow': (('xp', 'janus', 'fold'), set_flow),
       'lc': (('sats', 'lc', 'psd'), lambda t: set_lc(hold_time('lc', t))), 'psd': (('lc', 'psd', 'gaia'), lambda t: set_psd(hold_time('psd', t))),
       'xp': (('gaia', 'xp', 'janus'), lambda t: set_xp(hold_time('xp', t))), 'fold': (('janus', 'fold'), lambda t: set_fold(hold_time('fold', t)))}
FIRST = [True]; LAST_D = [None]
def state(t):
    t = t % LOOP; k, _ = stop_of(t); here = KEY[k]
    prev = KEY[(k - 1) % N_ST]
    for nm, (win, fn) in ACT.items():
        if FIRST[0] or here in win:
            fn(t)
    FIRST[0] = False
    pos, tgt, up = camera_at(t); place_camera(pos, tgt, up)
    if t == 0.0 or LAST_D[0] is None or np.linalg.norm(pos - LAST_D[0]) > 0.015 * max(np.linalg.norm(pos), 60.0):
        set_star_size(pos); LAST_D[0] = pos.copy()
    LIVE['sky'].default_value = sky_at(t); LIVE['phase'].default_value = DASH_CYCLES * t / LOOP
    bpy.context.view_layer.update()

def moving(t):
    k, dt = stop_of(t); return bool(dt > STOPS[k][1] + 0.02 or KEY[k] in ('gaia', 'sats'))

def shoot(t, path, frame=None):
    state(t); sc.render.filepath = path
    if args.denoise == 2: sc.cycles.use_denoising = moving(t)          # the denoiser for moving frames and the craft; held hairlines stay untouched
    if frame is not None: sc.frame_set(frame)
    bpy.ops.render.render(write_still=True)

def key_camera(a, b, N):
    """Camera keys around the frames a to b, so that Cycles can blur the camera's motion only."""
    sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = args.blur; sc.cycles.motion_blur_position = 'CENTER'
    prev = None
    for i in range(a - 2, b + 3):
        pos, tgt, up = camera_at((i * LOOP / N) % LOOP); place_camera(pos, tgt, up); q = cam.rotation_quaternion.copy()
        if prev is not None and q.dot(prev) < 0: q.negate()
        cam.rotation_quaternion = q; prev = q
        cam.keyframe_insert('location', frame=1000 + i); cam.keyframe_insert('rotation_quaternion', frame=1000 + i)
    for fc in cam.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

if args.mode == 'still':
    os.makedirs(args.out, exist_ok=True)
    if 'mw' in args.only or not args.only:
        from bpy_extras.object_utils import world_to_camera_view
        state(T0[KEY.index('mw')] + 1.0); bpy.context.view_layer.update()
        i_gc = int(np.argmin(np.linalg.norm(PTS - GC, axis=1)))
        pr_ = lambda p: tuple(round(v, 4) for v in world_to_camera_view(sc, cam, Vector(p))[:2])
        print('CENTRE thread to centre distance', float(np.linalg.norm(PTS[i_gc] - GC)), 'kpc units; frame position of centre', pr_(GC), 'of thread point', pr_(PTS[i_gc]),
              'bulge mean', pr_(((MP[(np.linalg.norm(MP, axis=1) < 3)] + np.array((RSUN, 0, 0))).mean(0) * KPC) @ RGAL.T))
    if args.stops:
        for k, (n, h, tr) in enumerate(STOPS):
            if args.only and n not in args.only.split(','): continue
            for fr_ in ((0.45, 0.95) if n in ('fold',) else (0.92,)):
                shoot(T0[k] + h * fr_, os.path.join(args.out, f'stop{k + 1}_{n}{"" if fr_ > 0.9 else "_a"}.png'))
    for t in args.t or []:
        shoot(t, os.path.join(args.out, f't_{t:06.2f}.png'))
elif args.mode == 'visible':
    # which frames show Gaia at all: its centre and shield radius projected through the camera of each frame
    N = round(LOOP * args.fps); c_ = GAIA_BASE + GAIA_AXIS * 0.4; rad = 2.0
    if os.environ.get('VIS_C'): c_ = np.asarray(ST['sats'].w(TESS_C if os.environ['VIS_C'] == 'tess' else KEPLER_C)); rad = 1.6
    fx = 40 / 36 * 2; shown = []
    for i in range(N + 1):
        pos, tgt, up = camera_at((i * LOOP / N) % LOOP); f_ = np.asarray(tgt) - pos; f_ /= np.linalg.norm(f_); r_ = np.cross(f_, up); r_ /= np.linalg.norm(r_); u_ = np.cross(r_, f_)
        d = c_ - pos; z = float(np.dot(d, f_))
        if z <= 0.1: continue
        x, y = float(np.dot(d, r_)) / z * fx, float(np.dot(d, u_)) / z * fx * 16 / 9; rr = rad / z * fx
        if abs(x) < 1 + rr and abs(y) < 1 + rr * 16 / 9 and rr * 960 > 0.5: shown.append(i)
    runs = []
    for i in shown:
        if runs and i == runs[-1][1] + 1: runs[-1][1] = i
        else: runs.append([i, i])
    print('GAIA_FRAMES', runs)
elif args.mode == 'frames':
    os.makedirs(args.out, exist_ok=True); N = round(LOOP * args.fps); b = N if args.b < 0 else args.b
    for i in range(args.a, min(b, N) + 1):
        pth = os.path.join(args.out, f'f_{i:05d}.png')
        if os.path.exists(pth) and os.path.getsize(pth) > 1000: continue
        if args.blur and not cam.animation_data: key_camera(args.a, min(b, N), N)
        shoot(i * LOOP / N, pth + '.tmp.png', 1000 + i if args.blur else None); os.replace(pth + '.tmp.png', pth)
print('done')
