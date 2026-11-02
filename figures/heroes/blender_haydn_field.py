"""What the noise estimator sees: the telescope's line of sight through a cluster to the detector (Blender, Cycles),
after figures/haydnsim/field.mjs. The telescope looks along y. Far along it sits a cluster of about 3,000 synthetic
stars drawn from a King density (tidal to core radius ratio 20) inside a sphere; at y = 0 stands the detector, a glass
plate of 18 by 18 pixels facing the cluster; the faint column between them is the one-degree field. Seven stars near one
line of sight through the core's edge are ringed, and their light runs as thin ivory lines onto the same few pixels of
the plate, where the target's mask, its 13 brightest pixels for a star centred in its pixel, stands raised and lit. The
cluster, the star positions and the brightnesses are schematic, not catalogue data; the depth along the line of sight
is drawn for illustration, since the pipeline works with projected positions. No number is shown.
Usage: uv run --python 3.11 --with bpy==4.2.0 python blender_haydn_field.py OUT.png [samples] [W] [H]
"""
import math, os, random, sys
import bpy, bmesh
import numpy as np
from mathutils import Vector

out = sys.argv[1]
samples = int(sys.argv[2]) if len(sys.argv) > 2 else 48
W, H = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (1600, 900)
random.seed(11); rng = np.random.default_rng(11)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.cycles.volume_step_rate = 4.0

IVORY, BLUE, AMBER = (0.96, 0.92, 0.84), (0.45, 0.62, 1.0), (1.0, 0.55, 0.15)
def mix(a, b, t): return tuple(x + (y - x) * t for x, y in zip(a, b))
def dim(c, k): return tuple(x * k for x in c)

def principled(name, base, metal=0.0, rough=0.4):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*base, 1); b.inputs['Metallic'].default_value = metal; b.inputs['Roughness'].default_value = rough; return m

def vcol_emission(name, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    a = nt.nodes.new('ShaderNodeAttribute'); a.attribute_name = 'col'
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Strength'].default_value = strength
    nt.links.new(a.outputs['Color'], e.inputs['Color']); nt.links.new(e.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface']); return m

def glass(name, tint=(0.2, 0.4, 0.9), tint_strength=0.02, gloss=0.07):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); gl = nt.nodes.new('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value = 0.05
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*tint, 1); em.inputs['Strength'].default_value = tint_strength
    m1 = nt.nodes.new('ShaderNodeMixShader'); m1.inputs['Fac'].default_value = gloss; m2 = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(tr.outputs[0], m1.inputs[1]); nt.links.new(gl.outputs[0], m1.inputs[2]); nt.links.new(m1.outputs[0], m2.inputs[0]); nt.links.new(em.outputs[0], m2.inputs[1])
    nt.links.new(m2.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m

class Mesh:
    """Many small shapes in one mesh with a colour per vertex."""
    def __init__(self): self.bm = bmesh.new(); self.cols = []
    def _v(self, p, col): self.cols.append(col); return self.bm.verts.new(p)
    def octa(self, p, r, col):
        vs = [self._v((p[0] + dx * r, p[1] + dy * r, p[2] + dz * r), col) for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
        for f in ((0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)): self.bm.faces.new([vs[i] for i in f])
    def box(self, lo, hi, col_bottom, col_top=None):
        col_top = col_top or col_bottom
        (x0, y0, z0), (x1, y1, z1) = lo, hi
        vs = [self._v(v, col_bottom if k < 4 else col_top) for k, v in enumerate(((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)))]
        for f in ((0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)): self.bm.faces.new([vs[i] for i in f])
    def tube(self, pts, r, col, sides=5):
        rings = []
        for i, p in enumerate(pts):
            t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
            u = t.cross(Vector((0, 0, 1))); u = u.normalized() if u.length > 1e-6 else Vector((1, 0, 0)); v = t.cross(u)
            rings.append([self._v(p + r * (math.cos(2 * math.pi * k / sides) * u + math.sin(2 * math.pi * k / sides) * v), col) for k in range(sides)])
        for a, b in zip(rings[:-1], rings[1:]):
            for k in range(sides): self.bm.faces.new((a[k], a[(k + 1) % sides], b[(k + 1) % sides], b[k]))
    def obj(self, mat, name='m'):
        me = bpy.data.meshes.new(name); self.bm.verts.ensure_lookup_table(); self.bm.to_mesh(me); self.bm.free()
        at = me.color_attributes.new('col', 'FLOAT_COLOR', 'POINT')
        for i, c in enumerate(self.cols): at.data[i].color = (*c, 1)
        ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); ob.data.materials.append(mat); return ob

def faces_obj(name, verts, faces, mat):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); ob.data.materials.append(mat); return ob

def cube(loc, size, mat, name='c'):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.name = name; o.scale = size; o.data.materials.append(mat); return o

# ---------------------------------------------------------------- the geometry of field.mjs, one unit per 100 of its
RC, CY, CZ = 0.70, 3.6, 1.0                   # cluster radius, its distance along the axis, its height
PX, N = 0.1, 18; SIDE = PX * N; THICK = 0.05   # the plate: 18 by 18 pixels
PZ0 = CZ - SIDE / 2
MAG = (SIDE / 2) / RC * 0.92
def on_plate(x, z): return (x * MAG, CZ + (z - CZ) * MAG)

# the cluster: a King-like density, core radius RC / 20, truncated at RC
rc = RC / 20.0
def king3(r): return (1 + (r / rc) ** 2) ** -1.5 - (1 + (RC / rc) ** 2) ** -1.5
rg = np.linspace(0, RC, 800); cdf = np.cumsum(rg ** 2 * np.array([king3(r) for r in rg])); cdf /= cdf[-1]
NSTAR = 3000
stars = []
for _ in range(NSTAR):
    r = float(np.interp(rng.random(), cdf, rg)); u = rng.random() * 2 - 1; ph = rng.random() * 2 * math.pi; s = math.sqrt(1 - u * u)
    stars.append([r * s * math.cos(ph), CY + r * s * math.sin(ph), CZ + r * u])
stars = np.array(stars)
lum = np.minimum(1.0, (1 - rng.random(NSTAR)) ** (-1 / 1.35) / 10)

# the line of sight through the core's edge, where single stars still show; the target is the fourth by depth
Tx, Tz = -0.14, CZ + 0.10
d = np.hypot(stars[:, 0] - Tx, stars[:, 2] - Tz)
cand = np.argsort(d)[:40]; cand = cand[d[cand] < 0.04]; cand = cand[np.argsort(stars[cand, 1])]
near = [int(cand[round(j / 6 * (len(cand) - 1))]) for j in range(7)]
tgt = near[3]
# nudge the target so it lands on a pixel centre, as the drawing does
tp = on_plate(stars[tgt, 0], stars[tgt, 2])
sx = (math.floor((tp[0] + SIDE / 2) / PX) + 0.5) * PX - SIDE / 2; sz = (math.floor((tp[1] - PZ0) / PX) + 0.5) * PX + PZ0
stars[tgt, 0] = sx / MAG; stars[tgt, 2] = CZ + (sz - CZ) / MAG
Tx, Tz = stars[tgt, 0], stars[tgt, 2]
TP = on_plate(Tx, Tz)
TPX = (math.floor((TP[0] + SIDE / 2) / PX) * PX - SIDE / 2, math.floor((TP[1] - PZ0) / PX) * PX + PZ0)

# ---------------------------------------------------------------- the cluster as points
P = Mesh()
for i in range(NSTAR):
    if i in near: continue
    b = 0.3 + 0.7 * lum[i]
    P.octa(stars[i], 0.0035 + 0.006 * lum[i], dim(IVORY, b))
P.obj(vcol_emission('cluster', 2.0), 'cluster')

# ---------------------------------------------------------------- the one-degree field as a faint column
VEIL = glass('veil', tint=mix(IVORY, BLUE, 0.4), tint_strength=0.012, gloss=0.0)
corners = [(-SIDE / 2, PZ0), (SIDE / 2, PZ0), (SIDE / 2, PZ0 + SIDE), (-SIDE / 2, PZ0 + SIDE)]
nearv = [(x, THICK / 2, z) for x, z in corners]; farv = [(x / MAG, CY, CZ + (z - CZ) / MAG) for x, z in corners]
faces_obj('column', nearv + farv, [(k, (k + 1) % 4, 4 + (k + 1) % 4, 4 + k) for k in range(4)], VEIL)
E = Mesh()
for k in range(4): E.tube([Vector(nearv[k]), Vector(farv[k])], 0.0025, dim(IVORY, 0.28), sides=4)
E.tube([Vector(farv[k % 4]) for k in range(5)], 0.0025, dim(IVORY, 0.28), sides=4)

# ---------------------------------------------------------------- the detector: a glass plate with a pixel grid
GLASS = glass('glass', tint=(0.3, 0.45, 0.9), tint_strength=0.03)
cube((0, -THICK / 2, CZ), (SIDE, THICK, SIDE), GLASS, 'plate')
cube((0, -THICK - 0.03, CZ), (SIDE + 0.12, 0.06, SIDE + 0.12), principled('frame', (0.2, 0.21, 0.23), 0.95, 0.35), 'frame')
cube((0, -THICK - 0.03, PZ0 / 2 - 0.06), (0.5, 0.06, PZ0 - 0.06), principled('foot', (0.16, 0.17, 0.19), 0.95, 0.4), 'foot')
for z in (PZ0, PZ0 + SIDE):
    E.tube([Vector((-SIDE / 2, 0.0, z)), Vector((SIDE / 2, 0.0, z))], 0.003, dim(IVORY, 0.5), sides=4)
for x in (-SIDE / 2, SIDE / 2):
    E.tube([Vector((x, 0.0, PZ0)), Vector((x, 0.0, PZ0 + SIDE))], 0.003, dim(IVORY, 0.5), sides=4)
G = Mesh()
for i in range(1, N):
    G.tube([Vector((-SIDE / 2 + i * PX, 0.002, PZ0)), Vector((-SIDE / 2 + i * PX, 0.002, PZ0 + SIDE))], 0.0015, dim(IVORY, 0.22), sides=4)
    G.tube([Vector((-SIDE / 2, 0.002, PZ0 + i * PX)), Vector((SIDE / 2, 0.002, PZ0 + i * PX))], 0.0015, dim(IVORY, 0.22), sides=4)
G.obj(vcol_emission('grid', 1.0), 'grid')
# the cluster landed on the pixels
L = Mesh()
for i in range(NSTAR):
    if i in near: continue
    x, z = on_plate(stars[i, 0], stars[i, 2])
    if abs(x) < SIDE / 2 and PZ0 < z < PZ0 + SIDE:
        L.octa((x, 0.006, z), 0.002 + 0.003 * lum[i], dim(IVORY, 0.12 + 0.3 * lum[i]))
L.obj(vcol_emission('landed', 1.4), 'landed')

# the mask: the 13 brightest pixels of a Gaussian centred on the target (sigma 0.61 pixel), raised and lit
SIG = 0.0606
def cdf1(x, m, s): return 0.5 * (1 + math.erf((x - m) / (s * math.sqrt(2))))
def pix_flux(a, c): return (cdf1(TPX[0] + (a + 1) * PX, TP[0], SIG) - cdf1(TPX[0] + a * PX, TP[0], SIG)) * (cdf1(TPX[1] + (c + 1) * PX, TP[1], SIG) - cdf1(TPX[1] + c * PX, TP[1], SIG))
pix = sorted(((pix_flux(a, c), a, c) for a in range(-3, 4) for c in range(-3, 4)), reverse=True)
mask = {(a, c) for _, a, c in pix[:13]}
Mk = Mesh()
for dx in range(-3, 4):
    for dz in range(-3, 4):
        on = (dx, dz) in mask
        x0, z0 = TPX[0] + dx * PX + 0.006, TPX[1] + dz * PX + 0.006
        c = dim(IVORY, 0.85) if on else dim(IVORY, 0.07)
        Mk.box((x0, 0.0, z0), (x0 + PX - 0.012, 0.022 if on else 0.004, z0 + PX - 0.012), dim(c, 0.4), c)
Mk.obj(vcol_emission('mask', 1.2), 'mask')

# ---------------------------------------------------------------- the seven stars, their rings and their light
S = Mesh(); R = Mesh(); Ly = Mesh()
for j, i in enumerate(near):
    p = stars[i]
    S.octa(p, 0.012 if j == 3 else 0.009, IVORY)
    R.tube([Vector((p[0] + 0.045 * math.cos(a), p[1], p[2] + 0.045 * math.sin(a))) for a in np.linspace(0, 2 * math.pi, 40)], 0.0025, dim(IVORY, 0.9), sides=4)
    x, z = on_plate(p[0], p[2])
    Ly.tube([Vector(p), Vector((x, 0.024, z))], 0.0012, dim(IVORY, 0.55), sides=4)
# the line of sight itself: a hairline through the target, from beyond the cluster to the plate
def ray(y):
    u = y / CY; return Vector((TP[0] + (Tx - TP[0]) * u, y, TP[1] + (Tz - TP[1]) * u))
Ly.tube([ray(CY + RC + 0.35), ray(0.03)], 0.0012, dim(BLUE, 0.45), sides=4)
S.obj(vcol_emission('seven', 3.0), 'seven'); R.obj(vcol_emission('rings', 1.6), 'rings'); Ly.obj(vcol_emission('light', 0.9), 'light')
E.obj(vcol_emission('edges', 1.0), 'edges')

# ---------------------------------------------------------------- stage, world, light, camera
cube((0, 2.0, -0.01), (400, 400, 0.02), principled('floor', (0.006, 0.007, 0.009), 0.5, 0.2), 'floor')
world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True; wn = world.node_tree
wn.nodes['Background'].inputs['Color'].default_value = (0.003, 0.0035, 0.005, 1)
HAZE = float(os.environ.get('HAZE', '0'))   # optional volume haze in a box around the stage; the compositor glow does the same job at a fraction of the cost
if HAZE > 0:
    hm = bpy.data.materials.new('haze'); hm.use_nodes = True; hn = hm.node_tree; hn.nodes.remove(hn.nodes['Principled BSDF'])
    vol = hn.nodes.new('ShaderNodeVolumePrincipled'); vol.inputs['Density'].default_value = HAZE; vol.inputs['Color'].default_value = (0.8, 0.85, 1.0, 1)
    hn.links.new(vol.outputs['Volume'], hn.nodes['Material Output'].inputs['Volume'])
    hb = cube((0.0, 1.5, 2.0), (12.0, 10.0, 4.0), hm, 'haze'); hb.display_type = 'WIRE'; hb.visible_shadow = False
sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 12; sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
ld = bpy.data.lights.new('key', 'AREA'); ld.energy = 70; ld.color = (0.7, 0.8, 1.0); ld.size = 6
lo = bpy.data.objects.new('key', ld); bpy.context.collection.objects.link(lo); lo.location = (-3.0, 0.5, 6.0)
lo.rotation_euler = (Vector((0.0, 1.8, 0.8)) - lo.location).to_track_quat('-Z', 'Y').to_euler()

cam_d = bpy.data.cameras.new('cam'); cam_d.lens = 40; cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 4.0
cam = bpy.data.objects.new('cam', cam_d); bpy.context.collection.objects.link(cam); sc.camera = cam
cv = [float(v) for v in os.environ.get('CAM', '-6.0,1.0,1.35,0.05,1.85,0.9,38,4').split(',')]   # a framing override for tests
loc, look = Vector(cv[:3]), Vector(cv[3:6]); cam_d.lens = cv[6]; cam_d.dof.aperture_fstop = cv[7]
cam.location = loc; cam.rotation_euler = (look - loc).to_track_quat('-Z', 'Y').to_euler(); cam_d.dof.focus_distance = (Vector((0, 0.3, CZ)) - loc).length

sc.use_nodes = True; ct = sc.node_tree; rl = ct.nodes['Render Layers']; comp = ct.nodes['Composite']
gl_ = ct.nodes.new('CompositorNodeGlare'); gl_.glare_type = 'FOG_GLOW'; gl_.quality = 'HIGH'; gl_.size = 8; gl_.threshold = 0.5; gl_.mix = -0.5
ct.links.new(rl.outputs['Image'], gl_.inputs['Image']); ct.links.new(gl_.outputs['Image'], comp.inputs['Image'])
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print('wrote', out, 'mask', sorted(mask), 'near', near)
