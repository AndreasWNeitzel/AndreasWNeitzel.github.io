"""The Gaia spacecraft as one hand built model, shared by the renders (Blender, bmesh). No openly licensed mesh of the
flight craft was found, so this is built by hand and is schematic, not an engineering model.

Followed from flight model photographs (ESA, Astrium) and the ESA animation: a sunshield of about 10 m across, twelve
frame arms with foil billowing between them, a flat disc with a thin black stepped rim, slack foil only between the arms, and solar panels underneath; two stacked
drums in dark insulation with seams and tabs, 3 m across, the upper drum a little wider; a shallow white conical roof with
a small mast; a tall silver radiator panel edged in gold on the upper drum; two telescope windows 106.5 degrees apart.
The wrinkles of the foil are random, and the instrument seen through each window is suggested only.

One model unit is a metre. The spin axis is z; the sun-facing side of the shield is down."""
import math
import numpy as np
import bpy, bmesh
from mathutils import Vector


def _principled(name, base, metal=0.0, rough=0.4, bump=0.0, scale=9.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*base, 1); b.inputs['Metallic'].default_value = metal; b.inputs['Roughness'].default_value = rough
    if bump:
        tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 6
        bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump
        nt.links.new(tc.outputs['Object'], nz.inputs['Vector']); nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


def _glowing(name, base, metal, rough, glow):
    """A dim emission, so the instrument inside an aperture still reads when the Sun is not on it."""
    m = _principled(name, base, metal, rough); b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Emission Color'].default_value = (*base, 1); b.inputs['Emission Strength'].default_value = glow; return m


class _Parts:
    """Everything of one material in one mesh."""
    def __init__(self, root, materials): self.root, self.mats, self.b = root, materials, {k: bmesh.new() for k in materials}
    def face(self, key, pts):
        bm = self.b[key]; bm.faces.new([bm.verts.new(p) for p in pts])
    def box(self, key, centre, u, v, w):
        """A box from its centre and three half axes."""
        c, u, v, w = Vector(centre), Vector(u), Vector(v), Vector(w); bm = self.b[key]
        q = [bm.verts.new(c + a * u + b * v + d * w) for d in (-1, 1) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        for f in ((3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)): bm.faces.new([q[i] for i in f])
    def rod(self, key, a, b, r):
        a, b = Vector(a), Vector(b); d = (b - a) / 2; u = d.orthogonal().normalized() * r; v = d.cross(u).normalized() * r
        self.box(key, (a + b) / 2, u, v, d)
    def revolve(self, key, rings, sides, rot=0.0):
        """A surface of revolution through the (radius, z) rings."""
        bm = self.b[key]; R = []
        for r, z in rings: R.append([bm.verts.new((r * math.cos(rot + 2 * math.pi * i / sides), r * math.sin(rot + 2 * math.pi * i / sides), z)) for i in range(sides)])
        for A, B in zip(R[:-1], R[1:]):
            for i in range(sides): bm.faces.new((A[i], A[(i + 1) % sides], B[(i + 1) % sides], B[i]))
    def finish(self, smooth=()):
        out = []
        for k, bm in self.b.items():
            if not bm.verts: bm.free(); continue
            me = bpy.data.meshes.new(k); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
            for p in me.polygons: p.use_smooth = k in smooth
            ob = bpy.data.objects.new(k, me); bpy.context.collection.objects.link(ob); me.materials.append(self.mats[k]); ob.parent = self.root; out.append(ob)
            if k == 'mast': ob.visible_shadow = False           # its shadow on the roof reads as a stray mark
            if k in ('trim', 'patch', 'hoop'): ob.visible_glossy = False   # the foil's folds would scatter them into bright specks
        return out


R_IN, R_OUT, K = 1.62, 5.1, 12         # shield radii and sectors
DISH = 0.0                             # the rim and arms lie in the plane of the collar's base: the shield opens flat
PATCH_R = 4.72
MAXD = 0.02                            # the largest crease height


def _rim(a):
    """Radius of the twelve sided outline at azimuth a; the corners lie on the frame arms."""
    d = (np.asarray(a, float) + math.pi / K) % (2 * math.pi / K) - math.pi / K
    return R_OUT * math.cos(math.pi / K) / np.cos(np.abs(d) - math.pi / K)


class _Shield:
    """The upper face of the shield as a height over azimuth and radius. The arms stand as ridges, each sector billows
    down between them, long soft wrinkles run diagonally across each sector, and thin tension lines fan in from the rim."""
    def __init__(self):
        rng = np.random.default_rng(31); W = []
        for k in range(K):
            for _ in range(rng.integers(3, 6)):                                  # long soft diagonals, a few big ones per sector
                W.append(((k + rng.uniform(0.1, 0.9)) * 2 * math.pi / K, rng.uniform(0.2, 0.8), rng.choice((-1, 1)) * rng.uniform(0.45, 1.05), rng.uniform(0.9, 2.2), rng.uniform(0.14, 0.3), rng.uniform(0.006, 0.02) * rng.choice((-1, 1), p=(0.3, 0.7))))
        self.W = np.array(W)
        nw = 150; self.fa = rng.uniform(0, 2 * math.pi, nw); self.fs = rng.uniform(0.006, 0.02, nw); self.fh = rng.uniform(0.003, 0.012, nw); self.fl = rng.uniform(0.25, 0.7, nw)
        self.ca = rng.uniform(0, 2 * math.pi, 110); self.cs = rng.uniform(0.008, 0.022, 110); self.ch = rng.uniform(0.006, 0.02, 110); self.cl = rng.uniform(0.25, 0.65, 110)   # tension lines fanning out of the collar
    def _xy(self, a, f):
        """Flat coordinates on the sheet: x along the arc, y along the radius, in metres."""
        return a * 3.4, f * (R_OUT - R_IN)
    def gold(self, a, r):
        d = (a + math.pi / K) % (2 * math.pi / K) - math.pi / K
        return np.clip((0.56 - np.abs(d) * r) / 0.14, 0, 1) ** 2 * np.clip((0.28 - np.abs(r - PATCH_R)) / 0.11, 0, 1) ** 2
    def z(self, a, r):
        a = np.asarray(a, float); f = np.clip((r - R_IN) / (_rim(a) - R_IN), 0, 1); u = (a % (2 * math.pi / K)) / (2 * math.pi / K)
        x, y = self._xy(a, f); h = 0.0
        for a0, f0, tn, ln, wd, ht in self.W:
            X0, Y0 = self._xy(a0, f0); d0 = (x - X0 + math.pi * 3.4) % (2 * math.pi * 3.4) - math.pi * 3.4; dy = y - Y0
            c, s_ = math.cos(math.atan(tn)), math.sin(math.atan(tn)); t = d0 * s_ + dy * c; n = d0 * c - dy * s_
            h = h + ht * np.exp(-(n / wd) ** 2) * np.exp(-(t / ln) ** 4)
        fan = 0.0
        for fa, fs, fh, fl in zip(self.fa, self.fs, self.fh, self.fl):
            d = (a - fa + np.pi) % (2 * np.pi) - np.pi; fan = fan + fh * np.exp(-(d / fs) ** 2) * np.clip((f - fl) / 0.25, 0, 1) ** 2
        for ca, cs, ch, cl in zip(self.ca, self.cs, self.ch, self.cl):
            d = (a - ca + np.pi) % (2 * np.pi) - np.pi; fan = fan + ch * np.exp(-(d / (cs * (0.6 + 2.2 * f))) ** 2) * np.clip((cl - f) / cl, 0, 1) ** 1.5
        calm = np.clip(np.minimum(u, 1 - u) / 0.05, 0, 1)                        # the foil is tight along the arms
        arm = 0.012 * np.exp(-(np.minimum(u, 1 - u) * 2 * math.pi / K * r / 0.035) ** 2)   # a shallow ridge along each frame arm
        d = (1 - self.gold(a, r)) * (h * calm + fan) * np.clip((1 - f) / 0.03, 0, 1) + arm
        return MAXD * np.tanh(d / MAXD)                                           # a flat sheet: form comes only from creases, never over 2 cm


def _under_z(r):
    """Height of the solar panel side: level with the rim at its edge, then a little below the deepest slack of the foil."""
    return -0.06 - 0.36 * np.clip((5.1 - np.asarray(r, float)) / 1.5, 0, 1)


def _grid_mesh(P, key, V):
    bm = P.b[key]; na, nr = V.shape[:2]; v = [[bm.verts.new(V[i, j]) for j in range(nr)] for i in range(na)]
    return bm, v


def _foil(P):
    """The shield: foil on a dense smooth mesh, the black stepped rim, the gold underside, patches on the frame tips."""
    S = _Shield(); na, nr = 1080, 130
    a = np.linspace(0, 2 * math.pi, na, endpoint=False)[:, None]; fr = (np.linspace(0, 1, nr) ** 0.9)[None, :]
    A = np.repeat(a, nr, 1); F = np.repeat(fr, na, 0); Rr = R_IN + (_rim(A) - R_IN) * F; Z = S.z(A, Rr); Z = Z - Z.mean(0, keepdims=True)   # each ring averages to the plane
    bm, v = _grid_mesh(P, 'foil', np.stack([Rr * np.cos(A), Rr * np.sin(A), Z], 2))
    uv = bm.loops.layers.uv.new('UVMap')
    for i in range(na):
        for j in range(nr - 1):
            f_ = bm.faces.new((v[i][j], v[(i + 1) % na][j], v[(i + 1) % na][j + 1], v[i][j + 1]))
            for lp, (a_, b_) in zip(f_.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))): lp[uv].uv = (a_ / na, b_ / (nr - 1))
    # the rim: a thin black band with a finely stepped outer edge, foil wrapped over it
    ns = 24 * K; z0 = float(S.z(np.array(0.0), np.array(R_OUT)))
    for i in range(ns):
        a0, a1 = i * 2 * math.pi / ns, (i + 1) * 2 * math.pi / ns; r0, r1 = float(_rim(a0)), float(_rim(a1)); step = 0.05 if i % 2 else 0.03
        at = lambda r, t, z: (r * math.cos(t), r * math.sin(t), z)
        P.face('hoop', [at(r0 - 0.03, a0, z0 + 0.004), at(r1 - 0.03, a1, z0 + 0.004), at(r1 + 0.012, a1, z0 - 0.002), at(r0 + 0.012, a0, z0 - 0.002)])
        P.face('skirt', [at(r0 + 0.012, a0, z0 - 0.002), at(r1 + 0.012, a1, z0 - 0.002), at(r1 + step, a1, z0 - 0.012), at(r0 + step, a0, z0 - 0.012)])
        P.face('skirt', [at(r0 + step, a0, z0 - 0.012), at(r1 + step, a1, z0 - 0.012), at(r1 + step, a1, z0 - 0.05), at(r0 + step, a0, z0 - 0.05)])
    # the underside: frames and solar panels behind the slack foil, kept inside the rim so nothing shows from above
    na2 = 240; A2 = np.linspace(0, 2 * math.pi, na2, endpoint=False)[:, None]; F2 = np.linspace(1, 0, 16)[None, :]
    R2 = (_rim(A2) - 0.02) * F2 + 0.5 * (1 - F2); Z2 = _under_z(R2)
    bm, v = _grid_mesh(P, 'cell', np.stack([R2 * np.cos(A2), R2 * np.sin(A2), Z2], 2))
    for i in range(na2):
        for j in range(15): bm.faces.new((v[i][j], v[(i + 1) % na2][j], v[(i + 1) % na2][j + 1], v[i][j + 1]))
    # gold patches: small sheets wrapped over each frame tip, each with a faint crease; dark and gold brackets down the arms
    rng = np.random.default_rng(4)
    for k in range(K):
        am_ = k * 2 * math.pi / K; aa = np.linspace(-1, 1, 25)[:, None]; bb = np.linspace(-1, 1, 15)[None, :]
        w = aa * 0.42 / PATCH_R + am_; r_ = PATCH_R + bb * 0.17
        A_ = np.broadcast_to(w, (25, 15)); R_ = np.broadcast_to(r_, (25, 15)); z_ = S.z(A_, R_) + 0.014
        for _ in range(int(rng.integers(1, 3))):                                  # one or two soft folds across the sheet
            th, off, dr = rng.uniform(0, math.pi), rng.uniform(-0.5, 0.5), rng.uniform(0.004, 0.009)
            z_ = z_ + dr * np.exp(-(((aa * np.cos(th) + bb * np.sin(th)) - off) / 0.13) ** 2) * (1 - aa ** 2) * (1 - bb ** 2)   # dies away at the sheet's edges
        bm, v = _grid_mesh(P, 'patch', np.stack([R_ * np.cos(A_), R_ * np.sin(A_), z_], 2))
        for i in range(24):
            for j in range(14): bm.faces.new((v[i][j], v[i + 1][j], v[i + 1][j + 1], v[i][j + 1]))
        rt = float(_rim(np.array(am_))) - 0.03; ca_, sa_ = math.cos(am_), math.sin(am_)   # the frame arm, a thin bright edge under the foil's ridge
        P.rod('edge', (R_IN * ca_, R_IN * sa_, 0.022), (rt * ca_, rt * sa_, 0.022), 0.02)
        for rb in (2.75, 3.75):
            zc = float(S.z(np.array(am_), np.array(rb))); c = Vector((rb * math.cos(am_), rb * math.sin(am_), zc + 0.025))
            P.box('trim' if rb < 3 else 'tab', c, Vector((0.038, 0, 0)), Vector((0, 0.038, 0)), Vector((0, 0, 0.024)))


RU, RL = 1.62, 1.52                   # the upper drum and the lower one


def _tent(P, apertures):
    """The dark drum, with its windows left open."""
    z = (1.3, 2.08, 2.84, 3.0); n = 120; R = RU; half = math.radians(24.0); bm = P.b['tent']
    rings = [[bm.verts.new((R * math.cos(2 * math.pi * i / n), R * math.sin(2 * math.pi * i / n), zz)) for i in range(n)] for zz in z]
    def inside(i):
        m = (i + 0.5) * 2 * math.pi / n
        return any(abs((m - a + math.pi) % (2 * math.pi) - math.pi) < half for a in apertures)
    for b_ in range(3):
        for i in range(n):
            if b_ == 1 and inside(i): continue
            bm.faces.new((rings[b_][i], rings[b_][(i + 1) % n], rings[b_ + 1][(i + 1) % n], rings[b_ + 1][i]))
    for a in apertures:
        rad = Vector((math.cos(a), math.sin(a), 0)); t = Vector((-math.sin(a), math.cos(a), 0)); zc = (z[1] + z[2]) / 2; hz = (z[2] - z[1]) / 2; hw = R * math.sin(half)
        d = 0.8; o = rad * (R * math.cos(half)); back = o - rad * d; up = Vector((0, 0, 1))
        c = lambda r_, a_, b_: r_ + t * a_ + up * (zc + b_)
        # the recess: four walls and a back
        for (p, q) in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
            P.face('deep', [c(o, p[0] * hw, p[1] * hz), c(o, q[0] * hw, q[1] * hz), c(back, q[0] * hw, q[1] * hz), c(back, p[0] * hw, p[1] * hz)])
        P.face('deep', [c(back, -hw, -hz), c(back, hw, -hz), c(back, hw, hz), c(back, -hw, hz)])
        # the instrument: a long mirror on the back wall, a bench with pipes across, two uprights
        P.box('mirror', c(back + rad * 0.05, 0, 0), t * hw * 0.72, up * hz * 0.5, rad * 0.015)
        P.box('bench', c(back + rad * 0.2, 0, -hz * 0.62), t * hw * 0.9, up * hz * 0.14, rad * 0.16)
        rng = np.random.default_rng(int(abs(a) * 100))
        for _ in range(9):                                                                    # pipes, baffles and supports, unevenly placed
            u0, v0 = rng.uniform(-0.9, 0.5), rng.uniform(-0.8, 0.8); ln, tilt, d_ = rng.uniform(0.25, 0.9), rng.uniform(-0.25, 0.25), rng.uniform(0.15, 0.62)
            P.rod('pipe', c(o - rad * d_, u0 * hw, v0 * hz), c(o - rad * d_, (u0 + ln) * hw, (v0 + tilt) * hz), rng.uniform(0.012, 0.03))
        for u_ in (-0.55, 0.05, 0.6):
            P.box('bench', c(o - rad * 0.45, u_ * hw, 0), t * 0.05, up * hz * 0.85, rad * 0.05)
        # a gold frame round the opening
        e = o + rad * 0.015
        for s_ in (-1, 1):
            P.box('trim', c(e, 0, s_ * hz), t * (hw + 0.03), up * 0.024, rad * 0.018)
            P.box('trim', c(e, s_ * hw, 0), t * 0.024, up * (hz + 0.03), rad * 0.018)


def studio_world(scene, base=(0.003, 0.0035, 0.005)):
    """A dark world that only mirrors can see: to reflections it shows large soft bright panels and dark sweeps, as the hall
    does in the flight photographs. Cameras see the plain dark base."""
    w = bpy.data.worlds.new('studio'); scene.world = w; w.use_nodes = True; nt = w.node_tree; N = nt.nodes.new; L = nt.links.new
    out = nt.nodes['World Output']; bg = nt.nodes['Background']; bg.inputs['Color'].default_value = (*base, 1)
    tc = N('ShaderNodeTexCoord'); nz = N('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.7; nz.inputs['Detail'].default_value = 1.0; L(tc.outputs['Generated'], nz.inputs['Vector'])
    mr = N('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.44; mr.inputs['From Max'].default_value = 0.58; mr.inputs['To Min'].default_value = 0.17; mr.inputs['To Max'].default_value = 1.05; L(nz.outputs['Fac'], mr.inputs['Value'])
    b2 = N('ShaderNodeBackground'); b2.inputs['Color'].default_value = (0.97, 0.98, 1.0, 1); L(mr.outputs[0], b2.inputs['Strength'])
    lp = N('ShaderNodeLightPath'); mx = N('ShaderNodeMixShader'); L(lp.outputs['Is Glossy Ray'], mx.inputs['Fac']); L(bg.outputs[0], mx.inputs[1]); L(b2.outputs[0], mx.inputs[2]); L(mx.outputs[0], out.inputs['Surface'])
    return w


def _crease_image():
    """A height map over the sheet, azimuth across and radius up: thousands of small creases that follow the tension,
    fanning towards the frame tips near the rim and running out from the collar. Random, drawn once."""
    W, H = 4096, 512; A = np.zeros((H, W), np.float32); rng = np.random.default_rng(77)
    for _ in range(16000):
        u0, f0 = rng.random(), rng.random() ** 0.8; us = (u0 * K) % 1.0
        th = (1 - 2 * us) * 0.95 * f0 + rng.normal(0, 0.24) + (rng.choice((-1, 1)) * 0.75 if rng.random() < 0.18 else 0.0)
        n = int(rng.uniform(14, 120)); t = np.arange(n); h = rng.uniform(0.25, 1.0) * rng.choice((-1, 1), p=(0.4, 0.6)) * np.sin(np.pi * (t + 0.5) / n)
        y = np.clip((f0 * (H - 1) + t * math.cos(th) * 1.0).astype(int), 0, H - 1); x = ((u0 * W + t * math.sin(th) * 1.3).astype(int)) % W
        np.add.at(A, (y, x), h); np.add.at(A, (y, (x + 1) % W), 0.55 * h); np.add.at(A, (y, (x - 1) % W), 0.55 * h)
    A = (A + 0.5 * (np.roll(A, 1, 0) + np.roll(A, -1, 0))) / 2
    A = np.clip(0.5 + 0.5 * A / np.percentile(np.abs(A), 99.7), 0, 1)
    img = bpy.data.images.new('foil_creases', W, H, alpha=False); img.colorspace_settings.name = 'Non-Color'
    px = np.stack([A, A, A, np.ones_like(A)], 2).ravel(); img.pixels.foreach_set(px); img.update(); img.pack(); return img


def _foil_material():
    """Near mirror silver, its fine creases in a bump map, with a faint iridescence that wanders over the sheet."""
    m = _principled('g_foil', (0.8, 0.8, 0.8), 1.0, 0.075); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.8; nz.inputs['Detail'].default_value = 2.0
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['Factor'].default_value = 0.2; nt.links.new(nz.outputs['Color'], mx.inputs[7]); mx.inputs[6].default_value = (0.86, 0.86, 0.86, 1)
    nt.links.new(mx.outputs[2], b.inputs['Base Color'])
    im = nt.nodes.new('ShaderNodeTexImage'); im.image = _crease_image(); im.extension = 'REPEAT'; nt.links.new(tc.outputs['UV'], im.inputs['Vector'])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.3; bp.inputs['Distance'].default_value = 0.006
    nt.links.new(im.outputs['Color'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal']); return m


def _crinkled(name, base, rough, scale, amount, glow=0.0):
    """Thin metal film: each small facet tilts its own way, so the reflection breaks into crisp shards."""
    m = _principled(name, base, 1.0, rough); nt = m.node_tree; b = nt.nodes['Principled BSDF']; N = nt.nodes.new; L = nt.links.new
    tc = N('ShaderNodeTexCoord'); vo = N('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = scale; L(tc.outputs['Object'], vo.inputs['Vector'])
    sb = N('ShaderNodeVectorMath'); sb.operation = 'SUBTRACT'; sb.inputs[1].default_value = (0.5, 0.5, 0.5); L(vo.outputs['Color'], sb.inputs[0])
    sc = N('ShaderNodeVectorMath'); sc.operation = 'SCALE'; sc.inputs['Scale'].default_value = amount; L(sb.outputs[0], sc.inputs[0])
    ge = N('ShaderNodeNewGeometry'); ad = N('ShaderNodeVectorMath'); ad.operation = 'ADD'; L(ge.outputs['Normal'], ad.inputs[0]); L(sc.outputs[0], ad.inputs[1])
    no = N('ShaderNodeVectorMath'); no.operation = 'NORMALIZE'; L(ad.outputs[0], no.inputs[0]); L(no.outputs[0], b.inputs['Normal'])
    if glow: b.inputs['Emission Color'].default_value = (*base, 1); b.inputs['Emission Strength'].default_value = glow
    return m


def _soft_foil_material():
    """The card's foil: bright metal, a little rough so reflections spread softly, with only a slow wander in its surface."""
    m = _principled('g_foil', (0.9, 0.91, 0.93), 1.0, 0.22); nt = m.node_tree; b = nt.nodes['Principled BSDF']; N = nt.nodes.new; L = nt.links.new
    tc = N('ShaderNodeTexCoord'); nz = N('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.6; nz.inputs['Detail'].default_value = 3; L(tc.outputs['Object'], nz.inputs['Vector'])
    bp = N('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.025; L(nz.outputs['Fac'], bp.inputs['Height'])
    mr = N('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.18; mr.inputs['To Max'].default_value = 0.26; L(nz.outputs['Fac'], mr.inputs['Value']); L(mr.outputs['Result'], b.inputs['Roughness'])
    L(bp.outputs['Normal'], b.inputs['Normal']); return m


def _mli(name, base, scale):
    """Dark insulation film, satin: soft wrinkles running along the panels, a sheen that wanders slowly from panel to panel."""
    m = _principled(name, base, 0.62, 0.34); nt = m.node_tree; b = nt.nodes['Principled BSDF']; N = nt.nodes.new; L = nt.links.new
    tc = N('ShaderNodeTexCoord'); mp = N('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1.0, 1.0, 0.34); L(tc.outputs['Object'], mp.inputs['Vector'])
    n1 = N('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = scale * 2.4; n1.inputs['Detail'].default_value = 1.5; L(mp.outputs[0], n1.inputs['Vector'])
    n2 = N('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = scale * 6.5; n2.inputs['Detail'].default_value = 1.0; L(mp.outputs[0], n2.inputs['Vector'])
    ad = N('ShaderNodeMath'); ad.operation = 'MULTIPLY_ADD'; ad.inputs[1].default_value = 0.25; L(n2.outputs['Fac'], ad.inputs[0]); L(n1.outputs['Fac'], ad.inputs[2])
    bp = N('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.85; bp.inputs['Distance'].default_value = 0.09; L(ad.outputs[0], bp.inputs['Height']); L(bp.outputs['Normal'], b.inputs['Normal'])
    n3 = N('ShaderNodeTexNoise'); n3.inputs['Scale'].default_value = 1.1; n3.inputs['Detail'].default_value = 1.0; L(tc.outputs['Object'], n3.inputs['Vector'])
    mr = N('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.35; mr.inputs['From Max'].default_value = 0.65; mr.inputs['To Min'].default_value = 0.26; mr.inputs['To Max'].default_value = 0.46; L(n3.outputs['Fac'], mr.inputs['Value']); L(mr.outputs['Result'], b.inputs['Roughness'])
    return m


def build_gaia(root, scale=1.0, soft_foil=False):
    """Builds the craft as children of the object root, one model unit times scale."""
    M = {'foil': _soft_foil_material() if soft_foil else _foil_material(), 'skirt': _principled('g_skirt', (0.01, 0.01, 0.012), 0.2, 0.45), 'edge': _principled('g_edge', (0.86, 0.86, 0.87), 1.0, 0.16), 'cell': _principled('g_cell', (0.03, 0.06, 0.16), 0.3, 0.12),
         'patch': _crinkled('g_patch', (1.0, 0.62, 0.1), 0.2, 9.0, 0.34, 0.0), 'svmfoil': _crinkled('g_svmfoil', (0.72, 0.72, 0.74), 0.24, 40.0, 0.035, 0.05), 'trim': _principled('g_trim', (0.9, 0.6, 0.16), 1.0, 0.26),
         'tab': _principled('g_tab', (0.05, 0.045, 0.04), 0.4, 0.4), 'tent': _mli('g_tent', (0.075, 0.076, 0.082), 0.7), 'svm': _mli('g_svm', (0.068, 0.069, 0.074), 0.8),
         'white': _principled('g_white', (0.82, 0.82, 0.8), 0.0, 0.38), 'silver': _principled('g_silver', (0.93, 0.93, 0.93), 0.62, 0.24, 0.06, 85.0),
         'hoop': _principled('g_hoop', (0.32, 0.33, 0.35), 0.8, 0.3), 'mast': _principled('g_mast', (0.62, 0.62, 0.64), 0.8, 0.35), 'seam': _principled('g_seam', (0.2, 0.2, 0.21), 0.7, 0.3), 'deep': _principled('g_deep', (0.006, 0.006, 0.008), 0.0, 0.8),
         'mirror': _glowing('g_mirror', (0.6, 0.62, 0.66), 1.0, 0.1, 0.05), 'pipe': _glowing('g_pipe', (0.34, 0.34, 0.36), 0.9, 0.35, 0.035), 'bench': _glowing('g_bench', (0.2, 0.19, 0.17), 0.7, 0.4, 0.02)}
    if soft_foil:                                                                # the card keeps the foil the brightest thing in frame
        M['white'].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.46, 0.47, 0.49, 1)
        M['silver'].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.6, 0.6, 0.62, 1)
    P = _Parts(root, M); ap = [math.radians(-70.0), math.radians(-70.0 + 106.5)]
    _foil(P)
    # the collar, gold trimmed, on the shield; the lower drum
    P.revolve('tent', [(1.8, -0.02), (1.7, 0.1), (1.56, 0.2), (RL, 0.24)], 48); P.revolve('trim', [(1.76, 0.02), (1.72, 0.08)], 48)
    P.revolve('svm', [(0.3, 0.2), (RL, 0.2), (RL, 1.26), (RU, 1.3), (0.3, 1.3)], 24, math.pi / 24)
    P.revolve('seam', [(RU + 0.012, 1.32), (RU + 0.012, 1.35)], 96); P.revolve('hoop', [(RU + 0.012, 2.0), (RU + 0.012, 2.016)], 96)
    # the bracket on the lower drum, as in the animation: a stout gold brace rising to a short top bar, a dark panel beside it, gold along the panel's far edge
    a1 = math.radians(-120.0); n1 = Vector((math.cos(a1), math.sin(a1), 0)); t1 = Vector((-math.sin(a1), math.cos(a1), 0)); c1 = n1 * (RL + 0.03); up = Vector((0, 0, 1))
    P.rod('trim', c1 - t1 * 0.72 + up * 0.32, c1 - t1 * 0.46 + up * 0.32, 0.05); P.rod('trim', c1 - t1 * 0.46 + up * 0.32, c1 - t1 * 0.12 + up * 1.08, 0.05); P.rod('trim', c1 - t1 * 0.12 + up * 1.08, c1 + t1 * 0.12 + up * 1.14, 0.05)
    P.box('tab', c1 + t1 * 0.42 + up * 0.72, t1 * 0.34, up * 0.4, n1 * 0.016); P.rod('trim', c1 + t1 * 0.8 + up * 0.32, c1 + t1 * 0.8 + up * 1.12, 0.024)
    # crinkled silver panels on the lower drum, the first beside the bracket's foot, black panels between them
    for ac in (-171.0, -51.0, 69.0):
        ac = math.radians(ac); hw_ = math.radians(21.0); aa = np.linspace(-1, 1, 33)[:, None]; zz = np.linspace(0, 1, 17)[None, :]
        A_ = np.broadcast_to(ac + aa * hw_, (33, 17)); Z_ = np.broadcast_to(0.3 + zz * 0.88, (33, 17)); R_ = RL + 0.016 + 0.012 * (1 - aa ** 2) * np.sin(math.pi * zz)
        bm, v = _grid_mesh(P, 'svmfoil', np.stack([R_ * np.cos(A_), R_ * np.sin(A_), Z_], 2))
        for i in range(32):
            for j in range(16): bm.faces.new((v[i][j], v[i + 1][j], v[i + 1][j + 1], v[i][j + 1]))
        for sg, kk in ((-1, 'trim'), (1, 'tab')):                                # small tabs at the panel's corners
            ct = ac + sg * (hw_ + math.radians(3)); nc = Vector((math.cos(ct), math.sin(ct), 0)); P.box(kk, nc * (RL + 0.02) + Vector((0, 0, 1.06)), Vector((-math.sin(ct), math.cos(ct), 0)) * 0.05, Vector((0, 0, 0.05)), nc * 0.01)
    # the upper drum with its windows
    _tent(P, ap)
    # the seams of the insulation: irregular blankets, each band cut at uneven azimuths, with cross seams at uneven heights
    win = lambda a_: any(abs((a_ - w + math.pi) % (2 * math.pi) - math.pi) < math.radians(27) for w in ap); rad_az = math.radians(-20.0); rng = np.random.default_rng(8)
    near_rad = lambda a_: abs((a_ - rad_az + math.pi) % (2 * math.pi) - math.pi) < math.radians(17)
    for z_a, z_b, r_, nn, top in ((0.26, 1.24, RL, 8, False), (1.36, 1.99, RU, 7, False), (2.03, 2.97, RU, 6, True)):
        az = np.sort(rng.uniform(0, 2 * math.pi, nn))
        for i in range(nn):
            a0, a1_ = az[i], az[(i + 1) % nn] + (2 * math.pi if i == nn - 1 else 0.0); n = Vector((math.cos(a0), math.sin(a0), 0)); t = Vector((-math.sin(a0), math.cos(a0), 0))
            if not (near_rad(a0) or (top and win(a0))): P.box('seam', n * (r_ + 0.006) + Vector((0, 0, (z_a + z_b) / 2)), t * 0.012, Vector((0, 0, (z_b - z_a) / 2)), n * 0.004)
            if rng.random() < 0.65:
                zz = rng.uniform(z_a + 0.2, z_b - 0.2); m_ = max(2, int((a1_ - a0) / math.radians(7)))
                for j in range(m_):
                    b0, b1 = a0 + (a1_ - a0) * j / m_, a0 + (a1_ - a0) * (j + 1) / m_
                    if near_rad(b0) or (top and win(b0)): continue
                    r2 = r_ + 0.007; P.face('seam', [(r2 * math.cos(b0), r2 * math.sin(b0), zz - 0.012), (r2 * math.cos(b1), r2 * math.sin(b1), zz - 0.012), (r2 * math.cos(b1), r2 * math.sin(b1), zz + 0.012), (r2 * math.cos(b0), r2 * math.sin(b0), zz + 0.012)])
            ac = rng.uniform(a0, a1_)
            if not (near_rad(ac) or win(ac)):
                nc = Vector((math.cos(ac), math.sin(ac), 0)); tc_ = Vector((-math.sin(ac), math.cos(ac), 0))
                P.box('trim' if rng.random() < 0.6 else 'tab', nc * (r_ + 0.012) + Vector((0, 0, rng.uniform(z_a + 0.1, z_b - 0.1))), tc_ * 0.045, Vector((0, 0, 0.045)), nc * 0.01)
    # the tall silver radiator with its gold edge, curved with the drum
    hw = math.radians(13.0); z0, z1 = 1.38, 2.72; ns = 14
    for i in range(ns):
        b0, b1 = rad_az - hw + 2 * hw * i / ns, rad_az - hw + 2 * hw * (i + 1) / ns; r_ = RU + 0.014
        P.face('silver', [(r_ * math.cos(b0), r_ * math.sin(b0), z0), (r_ * math.cos(b1), r_ * math.sin(b1), z0), (r_ * math.cos(b1), r_ * math.sin(b1), z1), (r_ * math.cos(b0), r_ * math.sin(b0), z1)])
        for zz in (z0, z1): P.box('trim', Vector(((r_ + 0.004) * math.cos((b0 + b1) / 2), (r_ + 0.004) * math.sin((b0 + b1) / 2), zz)), Vector((-math.sin(b0), math.cos(b0), 0)) * (r_ * hw / ns), Vector((0, 0, 0.022)), Vector((math.cos(b0), math.sin(b0), 0)) * 0.006)
    for b_ in (rad_az - hw, rad_az + hw):
        n = Vector((math.cos(b_), math.sin(b_), 0)); P.box('trim', n * (RU + 0.018) + Vector((0, 0, (z0 + z1) / 2)), Vector((-math.sin(b_), math.cos(b_), 0)) * 0.022, Vector((0, 0, (z1 - z0) / 2 + 0.02)), n * 0.006)
    # small gold and dark fittings along the hoops, a bolted ring of them under the roof
    for zz, cnt, hs in ((1.33, 18, 0.04), (2.92, 24, 0.03), (0.34, 14, 0.05)):
        rr_ = RL if zz < 1 else RU
        for j in range(cnt):
            ac = 2 * math.pi * (j + 0.3) / cnt
            if zz > 2 and (win(ac) or near_rad(ac)): continue
            nc = Vector((math.cos(ac), math.sin(ac), 0)); tc_ = Vector((-math.sin(ac), math.cos(ac), 0))
            P.box('trim' if j % 3 == 0 else 'tab', nc * (rr_ + 0.016) + Vector((0, 0, zz)), tc_ * hs, Vector((0, 0, hs)), nc * 0.012)
    # the shallow conical roof, flush with the drum, with a small mast
    P.revolve('white', [(RU + 0.012, 3.0), (RU + 0.012, 3.015), (1.22, 3.11), (0.81, 3.205), (0.41, 3.3), (0.0005, 3.40)], 96); P.revolve('trim', [(RU + 0.016, 2.985), (RU + 0.016, 3.01)], 96)
    mx, my = 1.4 * math.cos(math.radians(120)), 1.4 * math.sin(math.radians(120))
    P.rod('mast', (mx, my, 3.07), (mx, my, 3.26), 0.011); P.box('mast', (mx, my, 3.275), (0.026, 0, 0), (0, 0.026, 0), (0, 0, 0.024))
    # the phased array antenna under the shield
    for j in range(12):
        a = 2 * math.pi * j / 12; c = Vector((1.2 * math.cos(a), 1.2 * math.sin(a), -0.3)); P.box('hoop', c, Vector((math.cos(a), math.sin(a), 0)) * 0.18, Vector((-math.sin(a), math.cos(a), 0)) * 0.06, Vector((0, 0, 0.04)))
    P.finish(smooth=('white', 'tent', 'foil', 'patch', 'svm', 'svmfoil'))
    root.scale = (scale, scale, scale)
