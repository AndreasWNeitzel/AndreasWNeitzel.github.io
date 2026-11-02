"""The HAYDNsim pipeline as six stations on a dark stage (Blender, Cycles), read left to right and joined by one amber
thread. The stations follow the six stages of the flowchart in figures/haydnsim/build_haydn_figures.py and the caption
on /software/haydnsim/:
  1 the archive data: three thin glass plates, a Gaia cone of stars, the HST image of the core as a dense disc of
    points, and a catalogue as a sparse grid of points
  2 the magnitude window: a glass slab with a bright band through it; points pass through only inside the band
  3 the King profile: a translucent dome of points, denser at the centre, with the shape of the Harris (2010) profile
    of 47 Tucanae (core radius 21.6 arcsec, concentration 2.07), the same shape the line drawing uses
  4 the synthetic population: a cloud of points of varied brightness being laid onto a flat square field
  5 the noise estimator: a brushed-metal cube with a glowing pixel grid on top, a few raised lit pixels for the mask,
    and a cone of light falling on it from a star above
  6 the detection: a short power spectrum as filaments of light, the modes as a comb of taller amber peaks; the curve
    is the same schematic spectrum as the drawing (granulation and envelope from the Mosser et al. 2012 red-giant
    scaling relations at 30 microhertz, the comb at the asymptotic spacing, the isolated-star white level), with the
    peak heights illustrative
Everything in the render is schematic: the point clouds are drawn, not catalogue data, and no number is shown.
Colours: ivory for data drawn as light, blue for the parts of the pipeline Andreas built, amber for the thread.
Usage: uv run --python 3.11 --with bpy==4.2.0 python blender_haydn_pipeline.py OUT [samples] [W] [H] [animN]
  OUT is a PNG path for a still, or a directory for a loop; animN renders N frames of a slow dolly left to right.
"""
import math, random, sys
import bpy, bmesh
import numpy as np
from mathutils import Vector

out = sys.argv[1]
samples = int(sys.argv[2]) if len(sys.argv) > 2 else 48
W, H = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (1600, 900)
ANIM = int(sys.argv[5][4:]) if len(sys.argv) > 5 and sys.argv[5].startswith('anim') else 0
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

# ---------------------------------------------------------------- materials
def principled(name, base, metal=0.0, rough=0.4):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*base, 1); b.inputs['Metallic'].default_value = metal; b.inputs['Roughness'].default_value = rough; return m

def vcol_emission(name, strength):
    """Emission coloured by the per-vertex attribute 'col'; the colour's brightness sets the point's brightness."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    a = nt.nodes.new('ShaderNodeAttribute'); a.attribute_name = 'col'
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Strength'].default_value = strength
    nt.links.new(a.outputs['Color'], e.inputs['Color']); nt.links.new(e.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface']); return m

def glass(name, tint=(0.2, 0.4, 0.9), tint_strength=0.02, gloss=0.07):
    """Hairline glass: almost all transparent, a little glossy reflection, a faint tint so the sheet reads."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); gl = nt.nodes.new('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value = 0.05
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*tint, 1); em.inputs['Strength'].default_value = tint_strength
    m1 = nt.nodes.new('ShaderNodeMixShader'); m1.inputs['Fac'].default_value = gloss; m2 = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(tr.outputs[0], m1.inputs[1]); nt.links.new(gl.outputs[0], m1.inputs[2]); nt.links.new(m1.outputs[0], m2.inputs[0]); nt.links.new(em.outputs[0], m2.inputs[1])
    nt.links.new(m2.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m

def thread_material(name, freq=1.6):
    """Amber emission along the thread, brightened in dashes that move with the view-layer property 'phase'. The
    position along the thread is the vertex attribute 'arc'."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    N = nt.nodes.new; L = nt.links.new
    arc = N('ShaderNodeAttribute'); arc.attribute_name = 'arc'
    sep = N('ShaderNodeSeparateColor'); L(arc.outputs['Color'], sep.inputs['Color'])
    ph = N('ShaderNodeAttribute'); ph.attribute_type = 'VIEW_LAYER'; ph.attribute_name = 'phase'
    mul = N('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = freq; L(sep.outputs['Red'], mul.inputs[0])
    sub = N('ShaderNodeMath'); sub.operation = 'SUBTRACT'; L(mul.outputs[0], sub.inputs[0]); L(ph.outputs['Fac'], sub.inputs[1])
    tau = N('ShaderNodeMath'); tau.operation = 'MULTIPLY'; tau.inputs[1].default_value = 2 * math.pi; L(sub.outputs[0], tau.inputs[0])
    sn = N('ShaderNodeMath'); sn.operation = 'SINE'; L(tau.outputs[0], sn.inputs[0])
    half = N('ShaderNodeMath'); half.operation = 'MULTIPLY_ADD'; half.inputs[1].default_value = 0.5; half.inputs[2].default_value = 0.5; L(sn.outputs[0], half.inputs[0])
    pw = N('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 2.0; L(half.outputs[0], pw.inputs[0])
    st = N('ShaderNodeMath'); st.operation = 'MULTIPLY_ADD'; st.inputs[1].default_value = 3.0; st.inputs[2].default_value = 0.12; L(pw.outputs[0], st.inputs[0])
    e = N('ShaderNodeEmission'); e.inputs['Color'].default_value = (*AMBER, 1); L(st.outputs[0], e.inputs['Strength'])
    L(e.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m

# ---------------------------------------------------------------- one mesh per material
class Mesh:
    """Many small shapes in one mesh, a colour per vertex ('col') and a position along a path ('arc')."""
    def __init__(self): self.bm = bmesh.new(); self.cols = []; self.arcs = []
    def _v(self, p, col, arc=0.0):
        self.cols.append(col); self.arcs.append(arc); return self.bm.verts.new(p)
    def octa(self, p, r, col):
        vs = [self._v((p[0] + dx * r, p[1] + dy * r, p[2] + dz * r), col) for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
        for f in ((0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)): self.bm.faces.new([vs[i] for i in f])
    def box(self, lo, hi, col_bottom, col_top=None):
        col_top = col_top or col_bottom
        (x0, y0, z0), (x1, y1, z1) = lo, hi
        vs = [self._v(v, col_bottom if k < 4 else col_top) for k, v in enumerate(((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)))]
        for f in ((0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)): self.bm.faces.new([vs[i] for i in f])
    def tube(self, pts, r, col, sides=5, arcs=None):
        rings = []
        cols = col if isinstance(col, list) else [col] * len(pts)
        for i, p in enumerate(pts):
            t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
            u = t.cross(Vector((0, 0, 1))); u = u.normalized() if u.length > 1e-6 else Vector((1, 0, 0)); v = t.cross(u)
            a = arcs[i] if arcs else 0.0
            rings.append([self._v(p + r * (math.cos(2 * math.pi * k / sides) * u + math.sin(2 * math.pi * k / sides) * v), cols[i], a) for k in range(sides)])
        for a, b in zip(rings[:-1], rings[1:]):
            for k in range(sides): self.bm.faces.new((a[k], a[(k + 1) % sides], b[(k + 1) % sides], b[k]))
    def obj(self, mat, name='m'):
        me = bpy.data.meshes.new(name); self.bm.verts.ensure_lookup_table(); self.bm.to_mesh(me); self.bm.free()
        at = me.color_attributes.new('col', 'FLOAT_COLOR', 'POINT')
        for i, c in enumerate(self.cols): at.data[i].color = (*c, 1)
        ar = me.color_attributes.new('arc', 'FLOAT_COLOR', 'POINT')   # the arc length rides in the red channel
        for i, a in enumerate(self.arcs): ar.data[i].color = (a, 0.0, 0.0, 1.0)
        ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); ob.data.materials.append(mat); return ob

def plane(loc, sx, sy, rot, mat, name='p'):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc); o = bpy.context.object; o.name = name
    o.scale = (sx, sy, 1); o.rotation_euler = rot; o.data.materials.append(mat); return o

def cube(loc, size, mat, name='c'):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.name = name; o.scale = size; o.data.materials.append(mat); return o

GLASS = glass('glass')
PTS_I = vcol_emission('pts_ivory', 2.2)     # ivory point clouds
PTS_B = vcol_emission('pts_blue', 2.4)      # blue point clouds
LINES = vcol_emission('lines', 1.0)         # hairline edges
PIX = vcol_emission('pix', 1.0)             # the pixel grid and mask
PSD = vcol_emission('psd', 1.8)             # the spectrum filaments
METAL = principled('metal', (0.16, 0.17, 0.19), 0.7, 0.38)
BAND = vcol_emission('band', 0.9)
CONE = glass('cone', tint=IVORY, tint_strength=0.016, gloss=0.0)
DOME = glass('dome', tint=BLUE, tint_strength=0.006, gloss=0.015)

SX = [0.0, 2.4, 4.8, 7.2, 9.6, 12.0]   # the six stations along x
ZT = 0.5                                 # the thread's working height

def edges(M, corners, r=0.004, col=dim(IVORY, 0.5)):
    M.tube([Vector(c) for c in corners + [corners[0]]], r, col, sides=4)

# ---------------------------------------------------------------- 1 the archive data: three glass plates
x0 = SX[0]
P1 = Mesh(); E1 = Mesh()
PW, PH, PZ = 1.3, 0.95, 0.12
for k, (dy, dx) in enumerate(((-0.22, -0.16), (0.0, 0.0), (0.22, 0.16))):
    cx, cy = x0 + dx, dy
    plane((cx, cy, PZ + PH / 2), PW, PH, (math.pi / 2, 0, 0), GLASS, 'plate')
    edges(E1, [(cx - PW / 2, cy, PZ), (cx + PW / 2, cy, PZ), (cx + PW / 2, cy, PZ + PH), (cx - PW / 2, cy, PZ + PH)])
    yf = cy - 0.012
    if k == 0:   # a Gaia cone: stars inside a circle on the sky, more of them toward the cluster
        for _ in range(420):
            r = 0.42 * rng.random() ** 0.7; a = rng.random() * 2 * math.pi
            b = 0.35 + 0.65 * rng.random() ** 2
            P1.octa((cx + r * math.cos(a), yf, PZ + PH / 2 + r * math.sin(a) * 0.95), 0.004 + 0.004 * b, dim(IVORY, 0.4 + 0.6 * b))
    elif k == 1:  # the HST image of the core: a dense disc of points
        for _ in range(900):
            r = 0.2 * math.sqrt(rng.random()) ** 0.8; a = rng.random() * 2 * math.pi
            b = 0.4 + 0.6 * rng.random()
            P1.octa((cx + r * math.cos(a), yf, PZ + PH / 2 + r * math.sin(a)), 0.0035, dim(IVORY, 0.5 + 0.5 * b))
        edges(E1, [(cx - 0.24, yf, PZ + PH / 2 - 0.24), (cx + 0.24, yf, PZ + PH / 2 - 0.24), (cx + 0.24, yf, PZ + PH / 2 + 0.24), (cx - 0.24, yf, PZ + PH / 2 + 0.24)], 0.003, dim(IVORY, 0.35))
    else:        # a catalogue: a sparse grid of entries
        for i in range(9):
            for j in range(7):
                if rng.random() < 0.82:
                    P1.octa((cx - 0.48 + i * 0.12, yf, PZ + 0.12 + j * 0.12), 0.0055, dim(IVORY, 0.55 + 0.45 * rng.random()))
P1.obj(PTS_I, 'archive_points'); E1.obj(LINES, 'archive_edges')

# ---------------------------------------------------------------- 2 the magnitude window: a glass slab with a band
x0 = SX[1]
SW_, SD, SH, SZ = 0.42, 0.72, 1.05, 0.08
cube((x0, 0, SZ + SH / 2), (SW_, SD, SH), GLASS, 'slab')
E2 = Mesh(); P2 = Mesh(); B2 = Mesh()
for z in (SZ, SZ + SH):
    edges(E2, [(x0 - SW_ / 2, -SD / 2, z), (x0 + SW_ / 2, -SD / 2, z), (x0 + SW_ / 2, SD / 2, z), (x0 - SW_ / 2, SD / 2, z)])
BZ0, BZ1 = ZT - 0.1, ZT + 0.1   # the window: the magnitudes where both surveys are complete
B2.box((x0 - SW_ / 2 + 0.01, -SD / 2 + 0.01, BZ0), (x0 + SW_ / 2 - 0.01, SD / 2 - 0.01, BZ1), (0.2, 0.35, 0.9), (0.3, 0.5, 1.0))
B2.obj(BAND, 'band')
for _ in range(700):   # every magnitude arrives from the left; only the window's magnitudes continue to the right
    z = SZ + 0.03 + (SH - 0.06) * rng.random(); y = (rng.random() - 0.5) * (SD - 0.1)
    inside = BZ0 < z < BZ1
    xx = x0 - 1.05 + rng.random() * (2.1 if inside else 0.82)
    b = 0.35 + 0.65 * rng.random() ** 1.5
    P2.octa((xx, y, z), 0.0035 + 0.003 * b, dim(IVORY, (0.45 + 0.55 * b) * (1.0 if inside else 0.75)))
P2.obj(PTS_I, 'window_points'); E2.obj(LINES, 'slab_edges')

# ---------------------------------------------------------------- 3 the King profile: a dome of points
x0 = SX[2]
RC_ARC, CONC = 0.36 * 60.0, 2.07
RT_ARC = RC_ARC * 10 ** CONC
def king(r):
    a = 1.0 / math.sqrt(1.0 + (r / RC_ARC) ** 2); b = 1.0 / math.sqrt(1.0 + (RT_ARC / RC_ARC) ** 2); return (a - b) ** 2
RMAX_ARC, DR = 190.0, 0.78           # the inner 190 arcsec of the cluster, drawn 0.78 wide
DOME_H = 0.95
LK0, LK1 = math.log10(king(RMAX_ARC)), math.log10(king(0.0))
def height(r): return (math.log10(king(r)) - LK0) / (LK1 - LK0)   # the height is log surface density, as on the pictogram's axes
grid = np.linspace(0, RMAX_ARC, 600); dens = np.array([king(r) for r in grid]); cdf = np.cumsum(grid * dens); cdf /= cdf[-1]
P3 = Mesh()
for _ in range(2600):
    r = float(np.interp(rng.random(), cdf, grid)); a = rng.random() * 2 * math.pi
    h = height(r)
    P3.octa((x0 + DR * r / RMAX_ARC * math.cos(a), DR * r / RMAX_ARC * math.sin(a), 0.03 + DOME_H * h), 0.006, mix(dim(BLUE, 0.5), BLUE, h ** 0.5))
P3.obj(PTS_B, 'king_points')
# the dome itself as a faint surface of revolution
bm = bmesh.new(); rings = []
for i in range(0, 40):
    r = RMAX_ARC * (i / 39) ** 1.6; h = height(r)
    rings.append([bm.verts.new((x0 + DR * r / RMAX_ARC * math.cos(a), DR * r / RMAX_ARC * math.sin(a), 0.03 + DOME_H * h)) for a in np.linspace(0, 2 * math.pi, 48, endpoint=False)])
for a, b in zip(rings[:-1], rings[1:]):
    for k in range(48): bm.faces.new((a[k], a[(k + 1) % 48], b[(k + 1) % 48], b[k]))
me = bpy.data.meshes.new('dome'); bm.to_mesh(me); bm.free(); ob = bpy.data.objects.new('dome', me); bpy.context.collection.objects.link(ob); ob.data.materials.append(DOME)
E3 = Mesh(); E3.tube([Vector((x0 + DR * math.cos(a), DR * math.sin(a), 0.03)) for a in np.linspace(0, 2 * math.pi, 64)], 0.003, dim(BLUE, 0.35), sides=4); E3.obj(LINES, 'dome_foot')

# ---------------------------------------------------------------- 4 the synthetic population laid on a field
x0 = SX[3]
FW = 1.4
E4 = Mesh(); P4 = Mesh()
edges(E4, [(x0 - FW / 2, -FW / 2, 0.012), (x0 + FW / 2, -FW / 2, 0.012), (x0 + FW / 2, FW / 2, 0.012), (x0 - FW / 2, FW / 2, 0.012)], 0.004, dim(BLUE, 0.45))
cube((x0, 0, 0.005), (FW, FW, 0.01), principled('field', (0.02, 0.024, 0.034), 0.3, 0.35), 'field')
grid4 = np.linspace(0, 0.68, 400); d4 = np.array([king(r * 300.0) for r in grid4]) * grid4; c4 = np.cumsum(d4); c4 /= c4[-1]
for _ in range(2200):   # landed stars, placed on the sky by inverse-CDF sampling of the profile
    r = float(np.interp(rng.random(), c4, grid4)); a = rng.random() * 2 * math.pi
    lum = min(1.0, (1 - rng.random()) ** (-1 / 1.35) / 12)
    P4.octa((x0 + r * math.cos(a), r * math.sin(a), 0.018), 0.0035 + 0.006 * lum, mix(dim(BLUE, 0.55), mix(BLUE, IVORY, 0.6), lum))
for _ in range(900):    # stars still in the air, on their way down
    r = float(np.interp(rng.random(), c4, grid4)); a = rng.random() * 2 * math.pi
    z = 0.05 + 1.1 * rng.random() ** 0.7
    lum = min(1.0, (1 - rng.random()) ** (-1 / 1.35) / 12)
    P4.octa((x0 + r * math.cos(a), r * math.sin(a), z), 0.003 + 0.006 * lum, mix(dim(BLUE, 0.45), mix(BLUE, IVORY, 0.5), lum))
P4.obj(PTS_B, 'population'); E4.obj(LINES, 'field_edges')

# ---------------------------------------------------------------- 5 the noise estimator: a dark machine
x0 = SX[4]
CS = 0.9
cube((x0, 0, CS / 2), (CS, CS, CS), METAL, 'machine')
M5 = Mesh(); NPX = 12; px = (CS - 0.1) / NPX; gx0, gy0 = x0 - (CS - 0.1) / 2, -(CS - 0.1) / 2
mask = {(5, 5), (6, 5), (5, 6), (6, 6), (4, 5), (7, 6), (5, 4), (6, 7), (4, 6), (7, 5), (5, 7), (6, 4), (4, 4)}   # 13 pixels, a bright star's mask
for i in range(NPX):
    for j in range(NPX):
        on = (i, j) in mask
        lo = (gx0 + i * px + 0.006, gy0 + j * px + 0.006, CS); hi = (gx0 + (i + 1) * px - 0.006, gy0 + (j + 1) * px - 0.006, CS + (0.03 if on else 0.004))
        c = dim(IVORY, 0.9) if on else dim(IVORY, 0.13)
        M5.box(lo, hi, dim(c, 0.4), c)
E5 = Mesh()
for z in (0.0, CS):
    edges(E5, [(x0 - CS / 2, -CS / 2, z), (x0 + CS / 2, -CS / 2, z), (x0 + CS / 2, CS / 2, z), (x0 - CS / 2, CS / 2, z)], 0.003, dim(IVORY, 0.3))
for cx, cy in ((x0 - CS / 2, -CS / 2), (x0 + CS / 2, -CS / 2), (x0 + CS / 2, CS / 2), (x0 - CS / 2, CS / 2)):
    E5.tube([Vector((cx, cy, 0.0)), Vector((cx, cy, CS))], 0.003, dim(IVORY, 0.3), sides=4)
E5.obj(LINES, 'machine_edges')
star = (x0 + 0.02, 0.02, CS + 0.6)
M5.octa(star, 0.018, IVORY)
M5.obj(PIX, 'pixel_grid')
# a thin cone of light from the star onto the mask
bm = bmesh.new(); apex = bm.verts.new(star); base = [bm.verts.new((star[0] + 0.16 * math.cos(a), star[1] + 0.16 * math.sin(a), CS + 0.03)) for a in np.linspace(0, 2 * math.pi, 32, endpoint=False)]
for k in range(32): bm.faces.new((apex, base[k], base[(k + 1) % 32]))
me = bpy.data.meshes.new('cone'); bm.to_mesh(me); bm.free(); ob = bpy.data.objects.new('cone', me); bpy.context.collection.objects.link(ob); ob.data.materials.append(CONE)

# ---------------------------------------------------------------- 6 the detection: a power spectrum in filaments
x0 = SX[5]
NU0, NU1, LP0, LP1 = 8.0, 52.0, 1.7, 5.3
numax, Hh = 30.0, 6200.0
sig = 0.66 * numax ** 0.88 / 2.355; dnu = 0.28 * numax ** 0.75; eps = 0.634 + 0.63 * math.log10(dnu)
modes = [(dnu * (n + eps + shift), vis) for n in range(1, 20) for shift, vis in ((0.0, 1.0), (0.5 - 0.025, 1.5), (-0.121, 0.6)) if NU0 - 2 < dnu * (n + eps + shift) < NU1 + 2]
def psd(nu, white=61.0):
    gran = 52000 / (1 + (nu / 8.6) ** 4) + 3320 / (1 + (nu / 27.7) ** 4)
    comb = sum(4.0 * Hh * v * math.exp(-0.5 * ((m - numax) / sig) ** 2) / (1 + ((nu - m) / 0.12) ** 2) for m, v in modes)
    return gran + comb + white, comb / (gran + white)
P6 = Mesh(); NF = 300; SPW = 1.7
for k in range(NF):
    nu = NU0 + (NU1 - NU0) * k / (NF - 1); p, ratio = psd(nu)
    h = 0.04 + 1.0 * (math.log10(p) - LP0) / (LP1 - LP0)
    t = min(1.0, ratio / 1.5)
    col = mix(dim(IVORY, 0.35), mix(AMBER, (1.0, 0.8, 0.5), t), min(1.0, t * 1.6) ** 0.7)
    x = x0 - SPW / 2 + SPW * k / (NF - 1)
    P6.box((x - 0.0025, -0.0025, 0.0), (x + 0.0025, 0.0025, h), dim(col, 0.15), col)
    if t > 0.25: P6.octa((x, 0, h), 0.012, col)
P6.obj(PSD, 'spectrum')

# ---------------------------------------------------------------- the thread through the six stations
way = [(-1.6, 0.0, ZT), (SX[0], 0.0, ZT), (SX[1], 0.0, ZT), (SX[2] - 0.5, -0.55, 0.14), (SX[2] + 0.5, -0.55, 0.14), (SX[3], 0.0, 0.04),
       (SX[4] - CS / 2 - 0.3, 0.0, 0.3), (SX[4] - CS / 2, 0.0, ZT), (SX[4] + CS / 2, 0.0, ZT), (SX[4] + CS / 2 + 0.3, 0.0, 0.3), (SX[5] - SPW / 2, 0.0, 0.03), (SX[5] + SPW / 2 + 0.4, 0.0, 0.03), (SX[5] + 1.7, 0.0, 0.03)]
def catmull(pts, n=18):
    P = [Vector(pts[0])] + [Vector(p) for p in pts] + [Vector(pts[-1])]; outp = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            outp.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    outp.append(P[-2]); return outp
path = catmull(way); arcs = [0.0]
for a, b in zip(path[:-1], path[1:]): arcs.append(arcs[-1] + (b - a).length)
T = Mesh(); T.tube(path, 0.009, AMBER, sides=6, arcs=arcs); T.obj(thread_material('thread'), 'thread')
N6 = Mesh()   # square hand-off nodes where the thread meets a station
for x in (SX[0] - 0.9, SX[1] - 0.5, SX[2] - 0.5, SX[3] - FW / 2, SX[4] - CS / 2 - 0.3, SX[5] - SPW / 2):
    i = int(np.argmin([abs(p.x - x) for p in path])); p = path[i]
    N6.box((p.x - 0.03, p.y - 0.03, p.z - 0.03), (p.x + 0.03, p.y + 0.03, p.z + 0.03), dim(AMBER, 0.6), AMBER)
N6.obj(vcol_emission('nodes', 1.6), 'nodes')

# ---------------------------------------------------------------- stage, world, light, camera
cube((6.0, 0.0, -0.01), (400, 400, 0.02), principled('floor', (0.006, 0.007, 0.009), 0.5, 0.2), 'floor')
world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True; wn = world.node_tree
wn.nodes['Background'].inputs['Color'].default_value = (0.003, 0.0035, 0.005, 1)
# the haze lives in a box around the stage, not in the world: rays that leave to the black sky stop marching at its wall
import os
HAZE = float(os.environ.get('HAZE', '0'))   # volume haze costs 2.3 times the frame; the glow below does the same job
if HAZE > 0:
    hm = bpy.data.materials.new('haze'); hm.use_nodes = True; hn = hm.node_tree; hn.nodes.remove(hn.nodes['Principled BSDF'])
    vol = hn.nodes.new('ShaderNodeVolumePrincipled'); vol.inputs['Density'].default_value = HAZE; vol.inputs['Color'].default_value = (0.8, 0.85, 1.0, 1)
    hn.links.new(vol.outputs['Volume'], hn.nodes['Material Output'].inputs['Volume'])
    hb = cube((6.0, -3.0, 3.0), (24.0, 14.0, 6.0), hm, 'haze'); hb.display_type = 'WIRE'; hb.visible_shadow = False
sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 12; sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
ld = bpy.data.lights.new('key', 'AREA'); ld.energy = 90; ld.color = (0.7, 0.8, 1.0); ld.size = 8
lo = bpy.data.objects.new('key', ld); bpy.context.collection.objects.link(lo); lo.location = (6.0, -4.0, 7.0)
lo.rotation_euler = (Vector((6.0, 0.5, 0.0)) - lo.location).to_track_quat('-Z', 'Y').to_euler()

cam_d = bpy.data.cameras.new('cam'); cam_d.dof.use_dof = True
cam = bpy.data.objects.new('cam', cam_d); bpy.context.collection.objects.link(cam); sc.camera = cam
def aim(loc, look):
    cam.location = loc; cam.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.dof.focus_distance = (Vector(look) - Vector(loc)).length

sc.use_nodes = True; ct = sc.node_tree; rl = ct.nodes['Render Layers']; comp = ct.nodes['Composite']
gl_ = ct.nodes.new('CompositorNodeGlare'); gl_.glare_type = 'FOG_GLOW'; gl_.quality = 'HIGH'; gl_.size = 8; gl_.threshold = 0.5; gl_.mix = -0.5
ct.links.new(rl.outputs['Image'], gl_.inputs['Image']); ct.links.new(gl_.outputs['Image'], comp.inputs['Image'])
vl = sc.view_layers[0]; vl['phase'] = 0.0

if ANIM:
    cam_d.lens = 45; cam_d.dof.aperture_fstop = 4.0; sc.cycles.adaptive_threshold = 0.02
    sc.frame_start, sc.frame_end = 1, ANIM; sc.render.fps = 30
    XA, XB = 0.6, 11.4   # the dolly, left to right, at a human height
    for fr, x in ((1, XA), (ANIM, XB)):
        aim((x, -5.8, 1.7), (x + 1.2, 0.3, 0.45))
        cam.keyframe_insert('location', frame=fr); cam.keyframe_insert('rotation_euler', frame=fr); cam_d.keyframe_insert('dof.focus_distance', frame=fr)
        vl['phase'] = 0.0 if fr == 1 else 30.0; vl.keyframe_insert   # the dashes outrun the dolly, so the flow reads left to right('["phase"]', frame=fr)
    for ad in (cam.animation_data, cam_d.animation_data, sc.animation_data):
        for fc in ad.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    import os
    if os.environ.get('SUB'): sc.frame_start, sc.frame_end = [int(v) for v in os.environ['SUB'].split(',')]   # a subset of frames, for tests
    sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = out.rstrip('/') + '/f_'
    bpy.ops.render.render(animation=True)
else:
    import os
    cv = [float(v) for v in os.environ.get('CAM', '-2.2,-7.8,2.0,5.9,0.3,0.45,40,5.6').split(',')]   # a framing override for tests
    cam_d.lens = cv[6]; cam_d.dof.aperture_fstop = cv[7]
    aim(tuple(cv[:3]), tuple(cv[3:6]))
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
print('wrote', out)
