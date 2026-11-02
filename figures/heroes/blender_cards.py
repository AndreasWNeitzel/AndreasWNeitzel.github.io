"""Title cards for the browser playgrounds and demos on the Software page (Blender 4.2 as a module, Cycles).
One visual family with the JANUS and Starfold renders: a dark stage, hairline glass, objects drawn as light.

Variants and what in each is real:
  orbits    : the Earth as a dark sphere with a faint blue limb, three Molniya orbits and one geostationary orbit as
              thin curves of light, one satellite on each. The elements are those of the Orbits playground
              (assets/data/playground/orbits.json): semimajor axis 26,562 km, eccentricity 0.74, inclination 63.4
              degrees, perigee at the southernmost point, the three planes 120 degrees apart; geostationary radius
              42,164 km. The Earth radius 6,378.137 km is one unit. The positions of the satellites along their
              orbits are arbitrary instants.
  gp        : five draws from a Gaussian process with a squared exponential kernel (length scale 1, 240 points on 0
              to 10) conditioned on four observations, with the band of two standard deviations around the posterior
              mean drawn as a translucent envelope open at the front. This is the method the playground shows; the
              observation values here are illustrative, not a measurement.
  polytrope : a Sun-like star with an octant cut away so the inside shows. The script solves the Lane-Emden equation
              for n = 3 numerically (fourth order Runge-Kutta from the series start; first zero 6.8969) and scales it to
              the Sun (1 solar mass, 1 solar radius, ideal gas of mean molecular weight 0.62, which gives a central
              temperature near 12 million kelvin). The cut faces glow with the computed temperature profile T = T_c
              theta: a fixed ramp from deep red to white yellow is indexed by theta, so where each colour falls is
              computed, while the ramp itself is schematic (the true Planck colour of millions of kelvin is blue
              white). Hairlines mark the shells at a quarter, a half and three quarters of the radius. The photosphere
              has the Planck colour of 5,772 K (CIE 1931 matching functions, D65 white), a linear limb darkening law
              with u = 0.62, a reddening towards the Planck colour of 3,600 K at the limb and a soft cellular
              granulation; the reddening and the granulation are schematic.
  explorer  : a star's life on a glass plate: the real MESA track of the Stellar Explorer (1 solar mass, solar
              metallicity, stellar-explorer-data stellar_data_real.h5, history group, 13,024 rows, exported to
              cards/track.json) drawn as a thin ivory line in the plane of log Teff against log L, with six spheres at
              real rows of the track (zero age main sequence, end of the main sequence, the red giant branch twice,
              the red clump and the white dwarf). The sphere sizes follow the real log R but are compressed, and
              their colours follow the real Teff through a short blackbody table; both are schematic.
  tellurion : a black hole, schematic in the manner of the familiar edge on view: a dark disc, a thin photon ring,
              a warm accretion disc seen nearly edge on, brighter on the approaching side, with the far side folded
              over the top and a thinner image below. Nothing here is computed from a metric.
  nn        : the playground's network (48 inputs, two hidden layers of 16 tanh units, one output for [M/H]) standing
              in depth. The input layer is the real star the playground follows by default, the example giant in row
              97 of assets/data/playground/gaia_xp_mh.bin (Gaia DR3 5289554869898620416, GSP-Spec [M/H] of -0.09):
              its 24 BP and 24 RP coefficients over the star's flux scale, standardised with the training rows as the
              network sees them, drawn as signed bars, with coefficients beyond the relevant bases dimmed as in the
              playground. The weights come from one training run in this script with the playground's settings (Adam,
              rate 0.003, batches of 64) for 60 passes with a fixed seed (validation error in the log); the edges are
              the largest weights of each layer within the playground's budget of 400 lines; edge brightness follows
              the weight and falls off with distance from the camera, node glow follows the activation for this star.
              Positions in space are schematic.

Usage: uv run --python 3.11 --with bpy==4.2.0 python blender_cards.py VARIANT OUT.png [samples] [W] [H]
The nn variant reads the playground data from assets/data/playground. The explorer variant reads track.json from
the directory of OUT.png (built from the history group of the Stellar Explorer data file).
"""
import json, math, os, random, sys
import bpy, bmesh
import numpy as np
from mathutils import Matrix, Vector

variant, out = sys.argv[1], sys.argv[2]
samples = int(sys.argv[3]) if len(sys.argv) > 3 else 48
W, H = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (1600, 900)
random.seed(5); rng = np.random.default_rng(5)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'

def mix(a, b, t): return tuple(x + (y - x) * t for x, y in zip(a, b))
IVORY, BLUE, AMBER, ICE = (0.96, 0.92, 0.84), (0.45, 0.62, 1.0), (1.0, 0.55, 0.15), (0.55, 0.78, 1.0)

# ------------------------------------------------------------------------------------------------- materials
def vcol_emission(name, strength):
    # emission from the per-vertex colour attribute 'col'
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    a = nt.nodes.new('ShaderNodeAttribute'); a.attribute_name = 'col'
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Strength'].default_value = strength
    nt.links.new(a.outputs['Color'], e.inputs['Color']); nt.links.new(e.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface']); return m

def vcol_translucent(name, strength, fac):
    # a see-through sheet that glows a little: transparent mixed with vertex-coloured emission, fac the glowing share
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    a = nt.nodes.new('ShaderNodeAttribute'); a.attribute_name = 'col'
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Strength'].default_value = strength
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); mx.inputs['Fac'].default_value = fac
    nt.links.new(a.outputs['Color'], e.inputs['Color']); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(e.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m

def principled(name, base, metal=0.0, rough=0.4):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*base, 1); b.inputs['Metallic'].default_value = metal; b.inputs['Roughness'].default_value = rough; return m

def glass_material():
    # hairline glass of the JANUS and Starfold plates: mostly transparent, a touch of gloss and a faint blue tint
    m = bpy.data.materials.new('glass'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); gl = nt.nodes.new('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value = 0.05
    tint = nt.nodes.new('ShaderNodeEmission'); tint.inputs['Color'].default_value = (0.2, 0.4, 0.9, 1); tint.inputs['Strength'].default_value = 0.02
    m1 = nt.nodes.new('ShaderNodeMixShader'); m1.inputs['Fac'].default_value = 0.06; m2 = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(tr.outputs[0], m1.inputs[1]); nt.links.new(gl.outputs[0], m1.inputs[2]); nt.links.new(m1.outputs[0], m2.inputs[0]); nt.links.new(tint.outputs[0], m2.inputs[1])
    nt.links.new(m2.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m

def limb_material(name, base, glow, strength, power=3.0):
    # a dark body whose rim glows: Principled base plus emission scaled by the facing weight raised to a power
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes.new; L = nt.links.new
    b = nt.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (*base, 1); b.inputs['Roughness'].default_value = 0.9; b.inputs['Specular IOR Level'].default_value = 0.05
    lw = N('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    pw = N('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = power; L(lw.outputs['Facing'], pw.inputs[0])
    st = N('ShaderNodeMath'); st.operation = 'MULTIPLY'; st.inputs[1].default_value = strength; L(pw.outputs[0], st.inputs[0])
    e = N('ShaderNodeEmission'); e.inputs['Color'].default_value = (*glow, 1); L(st.outputs[0], e.inputs['Strength'])
    ad = N('ShaderNodeAddShader'); L(b.outputs[0], ad.inputs[0]); L(e.outputs[0], ad.inputs[1]); L(ad.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m

# ------------------------------------------------------------------------------------------------- geometry
class Mesh:
    # many small shapes in one mesh with a colour per vertex
    def __init__(self): self.bm = bmesh.new(); self.cols = []
    def v(self, p, col): self.cols.append(col); return self.bm.verts.new(p)
    def octa(self, p, r, col):
        vs = [self.v((p[0] + dx * r, p[1] + dy * r, p[2] + dz * r), col) for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
        for f in ((0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)): self.bm.faces.new([vs[i] for i in f])
    def box(self, lo, hi, col_bottom, col_top):
        (x0, y0, z0), (x1, y1, z1) = lo, hi
        vs = [self.v(p, c) for p, c in (((x0, y0, z0), col_bottom), ((x1, y0, z0), col_bottom), ((x1, y1, z0), col_bottom), ((x0, y1, z0), col_bottom),
                                         ((x0, y0, z1), col_top), ((x1, y0, z1), col_top), ((x1, y1, z1), col_top), ((x0, y1, z1), col_top))]
        for f in ((0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)): self.bm.faces.new([vs[i] for i in f])
    def tube(self, pts, r, col, sides=6):
        # a polyline as a thin tube; col one colour or one per point
        cols = col if isinstance(col, list) else [col] * len(pts); rings = []
        for i, p in enumerate(pts):
            t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
            u = t.cross(Vector((0, 0, 1))); u = u.normalized() if u.length > 1e-6 else Vector((1, 0, 0)); w = t.cross(u)
            rings.append([self.v(p + r * (math.cos(2 * math.pi * k / sides) * u + math.sin(2 * math.pi * k / sides) * w), cols[i]) for k in range(sides)])
        for a, b in zip(rings[:-1], rings[1:]):
            for k in range(sides): self.bm.faces.new((a[k], a[(k + 1) % sides], b[(k + 1) % sides], b[k]))
    def grid(self, rows, cols=None):
        # rows: list of lists of (point, colour); quads between consecutive rows
        vr = [[self.v(p, c) for p, c in row] for row in rows]
        for a, b in zip(vr[:-1], vr[1:]):
            for k in range(len(a) - 1):
                try: self.bm.faces.new((a[k], a[k + 1], b[k + 1], b[k]))
                except ValueError: pass
    def sphere(self, c, r, colf, seg=48, rings=24, keep=None):
        # a lat-long sphere; colf(point on the unit sphere) gives the colour; keep(point) False drops a face
        vs = []
        for i in range(rings + 1):
            th = math.pi * i / rings; row = []
            for j in range(seg):
                ph = 2 * math.pi * j / seg; n = Vector((math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)))
                row.append(self.v(Vector(c) + r * n, colf(n)))
            vs.append(row)
        for i in range(rings):
            for j in range(seg):
                quad = (vs[i][j], vs[i][(j + 1) % seg], vs[i + 1][(j + 1) % seg], vs[i + 1][j])
                if keep is not None:
                    mid = sum((q.co for q in quad), Vector()) / 4
                    if not keep((mid - Vector(c)) / r): continue
                try: self.bm.faces.new(quad if 0 < i < rings - 1 else (quad[0], quad[2], quad[3]) if i == 0 else (quad[0], quad[1], quad[2]))
                except ValueError: pass
    def obj(self, mat, name='m'):
        me = bpy.data.meshes.new(name); self.bm.verts.ensure_lookup_table(); self.bm.to_mesh(me); self.bm.free()
        at = me.color_attributes.new('col', 'FLOAT_COLOR', 'POINT')
        for i, c in enumerate(self.cols): at.data[i].color = (*c, 1)
        ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); ob.data.materials.append(mat)
        for p in ob.data.polygons: p.use_smooth = True
        return ob

def sphere_obj(name, loc, r, mat, seg=64, rings=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, radius=r, location=loc); ob = bpy.context.object
    ob.name = name; ob.data.materials.append(mat); bpy.ops.object.shade_smooth(); return ob

# ------------------------------------------------------------------------------------------------- stage
def world(color=(0.003, 0.0035, 0.005), haze=0.0):
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (*color, 1)
    if haze:
        v = w.node_tree.nodes.new('ShaderNodeVolumePrincipled'); v.inputs['Density'].default_value = haze
        w.node_tree.links.new(v.outputs['Volume'], w.node_tree.nodes['World Output'].inputs['Volume'])

def floor(z, size=80, base=(0.006, 0.007, 0.009), rough=0.2):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z)); f = bpy.context.object; f.data.materials.append(principled('floor', base, 0.6, rough)); return f

def camera(loc, look, lens, focus=None, fstop=4.0):
    cd = bpy.data.cameras.new('cam'); cd.lens = lens
    if focus: cd.dof.use_dof = True; cd.dof.focus_distance = focus; cd.dof.aperture_fstop = fstop
    cam = bpy.data.objects.new('cam', cd); bpy.context.collection.objects.link(cam); sc.camera = cam
    cam.location = loc; cam.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()

def key_light(loc, energy=220, size=8):
    ld = bpy.data.lights.new('key', 'AREA'); ld.energy = energy; ld.color = (0.62, 0.74, 1.0); ld.size = size
    k = bpy.data.objects.new('key', ld); bpy.context.collection.objects.link(k); k.location = loc
    k.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()

def bloom(size=7, mix_=-0.6):
    sc.use_nodes = True; ct = sc.node_tree; rl = ct.nodes['Render Layers']; comp = ct.nodes['Composite']
    g = ct.nodes.new('CompositorNodeGlare'); g.glare_type = 'FOG_GLOW'; g.quality = 'HIGH'; g.size = size; g.threshold = 0.5; g.mix = mix_
    ct.links.new(rl.outputs['Image'], g.inputs['Image']); ct.links.new(g.outputs['Image'], comp.inputs['Image'])

def glass_plate(w=6.4, h=4.4, z=0.0):
    # the Starfold plate: a hairline glass sheet with blue edge lights
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, z)); g = bpy.context.object; g.scale = (w, h, 1); g.data.materials.append(glass_material())
    E = Mesh(); e, f_ = w / 2, h / 2; c = (0.35, 0.6, 1.0)
    for (x0, y0), (x1, y1) in (((-e, -f_), (e, -f_)), ((e, -f_), (e, f_)), ((e, f_), (-e, f_)), ((-e, f_), (-e, -f_))):
        E.box((min(x0, x1) - 0.006, min(y0, y1) - 0.006, z - 0.004), (max(x0, x1) + 0.006, max(y0, y1) + 0.006, z + 0.004), c, c)
    E.obj(vcol_emission('edge', 0.9), 'edge')

def star_colour(teff):
    # a short blackbody table, interpolated in log T; schematic tints for spheres of light
    tab = [(3200, (1.0, 0.50, 0.22)), (4000, (1.0, 0.66, 0.38)), (5000, (1.0, 0.84, 0.62)), (5800, (1.0, 0.93, 0.82)),
           (7000, (0.94, 0.95, 1.0)), (10000, (0.80, 0.87, 1.0)), (30000, (0.66, 0.78, 1.0))]
    lt = math.log10(teff)
    for (t0, c0), (t1, c1) in zip(tab[:-1], tab[1:]):
        if lt <= math.log10(t1): return mix(c0, c1, max(0.0, (lt - math.log10(t0)) / (math.log10(t1) - math.log10(t0))))
    return tab[-1][1]

def planck_rgb(kelvin):
    # Planck spectrum weighted by the CIE 1931 colour matching functions (the multi-lobe Gaussian fit of Wyman, Sloan
    # and Shirley 2013), XYZ to linear Rec. 709 with the D65 white, scaled so the largest channel is 1
    lam = np.arange(360.0, 831.0, 1.0)
    def g(x, m, s1, s2): return np.exp(-0.5 * ((x - m) / np.where(x < m, s1, s2)) ** 2)
    xb = 1.056 * g(lam, 599.8, 37.9, 31.0) + 0.362 * g(lam, 442.0, 16.0, 26.7) - 0.065 * g(lam, 501.1, 20.4, 26.2)
    yb = 0.821 * g(lam, 568.8, 46.9, 40.5) + 0.286 * g(lam, 530.9, 16.3, 31.1)
    zb = 1.217 * g(lam, 437.0, 11.8, 36.0) + 0.681 * g(lam, 459.0, 26.0, 13.8)
    lm = lam * 1e-9; B = 1.0 / lm ** 5 / np.expm1(1.438777e-2 / (lm * kelvin))
    XYZ = np.array([(B * xb).sum(), (B * yb).sum(), (B * zb).sum()])
    M = np.array([[3.2404542, -1.5371385, -0.4985314], [-0.9692660, 1.8760108, 0.0415560], [0.0556434, -0.2040259, 1.0572252]])
    rgb = np.clip(M @ XYZ, 0, None); return tuple(float(v) for v in rgb / rgb.max())

def sun_material(name, col, limb_col, strength, u=0.6):
    # a photosphere: emission with linear limb darkening I = 1 - u (1 - mu), the colour cooling towards the limb,
    # and a soft cellular granulation (dark lanes between bright cells) with a slow mottle
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF']); N = nt.nodes.new; L = nt.links.new
    lw = N('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    ld = N('ShaderNodeMath'); ld.operation = 'MULTIPLY_ADD'; ld.inputs[1].default_value = -u; ld.inputs[2].default_value = 1.0; L(lw.outputs['Facing'], ld.inputs[0])
    tc = N('ShaderNodeTexCoord')
    vo = N('ShaderNodeTexVoronoi'); vo.feature = 'SMOOTH_F1'; vo.inputs['Scale'].default_value = 13.0; vo.inputs['Smoothness'].default_value = 1.0; L(tc.outputs['Object'], vo.inputs['Vector'])
    ln = N('ShaderNodeMapRange'); ln.inputs['From Min'].default_value = 0.0; ln.inputs['From Max'].default_value = 0.7
    ln.inputs['To Min'].default_value = 1.0; ln.inputs['To Max'].default_value = 0.80; L(vo.outputs['Distance'], ln.inputs['Value'])
    nz = N('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 5.0; nz.inputs['Detail'].default_value = 3.0; L(tc.outputs['Object'], nz.inputs['Vector'])
    mo = N('ShaderNodeMapRange'); mo.inputs['To Min'].default_value = 0.86; mo.inputs['To Max'].default_value = 1.08; L(nz.outputs['Fac'], mo.inputs['Value'])
    a1 = N('ShaderNodeMath'); a1.operation = 'MULTIPLY'; L(ld.outputs[0], a1.inputs[0]); L(ln.outputs[0], a1.inputs[1])
    a2 = N('ShaderNodeMath'); a2.operation = 'MULTIPLY'; L(a1.outputs[0], a2.inputs[0]); L(mo.outputs[0], a2.inputs[1])
    st = N('ShaderNodeMath'); st.operation = 'MULTIPLY'; st.inputs[1].default_value = strength; L(a2.outputs[0], st.inputs[0])
    pw = N('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 0.9; L(lw.outputs['Facing'], pw.inputs[0])
    cm = N('ShaderNodeMix'); cm.data_type = 'RGBA'; cm.inputs[6].default_value = (*col, 1); cm.inputs[7].default_value = (*limb_col, 1); L(pw.outputs[0], cm.inputs['Factor'])
    e = N('ShaderNodeEmission'); L(cm.outputs[2], e.inputs['Color']); L(st.outputs[0], e.inputs['Strength'])
    L(e.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m

# ================================================================================================== variants
if variant == 'orbits':
    RE = 6378.137; a_m, e_m, inc = 26562.0 / RE, 0.74, math.radians(63.4); r_geo = 42164.0 / RE
    def orbit_pts(a, e, i, raan, argp, nus):
        # classical elements to inertial coordinates: perifocal ellipse, then argument of perigee, inclination, node
        M = Matrix.Rotation(raan, 3, 'Z') @ Matrix.Rotation(i, 3, 'X') @ Matrix.Rotation(argp, 3, 'Z'); pts = []
        for nu in nus:
            r = a * (1 - e * e) / (1 + e * math.cos(nu)); pts.append(M @ Vector((r * math.cos(nu), r * math.sin(nu), 0)))
        return pts
    nus = [2 * math.pi * k / 400 for k in range(401)]
    L = Mesh(); S = Mesh()
    for k, (raan, nu_sat) in enumerate(((math.radians(20), math.radians(180)), (math.radians(140), math.radians(75)), (math.radians(260), math.radians(300)))):
        pts = orbit_pts(a_m, e_m, inc, raan, math.radians(270), nus)
        L.tube(pts, 0.012, IVORY)
        s = orbit_pts(a_m, e_m, inc, raan, math.radians(270), [nu_sat])[0]
        S.octa(s, 0.055, (1.0, 0.97, 0.9)); S.octa(s, 0.11, mix(IVORY, (0, 0, 0), 0.0))
    geo = [Vector((r_geo * math.cos(t), r_geo * math.sin(t), 0)) for t in nus]
    L.tube(geo, 0.012, ICE)
    S.octa(Vector((r_geo, 0, 0)), 0.055, (0.9, 0.95, 1.0)); S.octa(Vector((r_geo, 0, 0)), 0.11, ICE)
    L.obj(vcol_emission('orbits', 2.4), 'orbits'); S.obj(vcol_emission('sats', 3.0), 'sats')
    sphere_obj('earth', (0, 0, 0), 1.0, limb_material('earth', (0.006, 0.009, 0.016), BLUE, 0.45, 4.0))
    floor(-1.45, base=(0.005, 0.006, 0.008), rough=0.2)
    world(haze=0.004); bloom(7, -0.55); key_light((-10, -14, 12), 40, 10)
    camera((-12.5, -19.0, 5.6), (0.6, 0.0, 2.6), 46, 23.0, 5.0)

elif variant == 'gp':
    X = np.linspace(0, 10, 240); xo = np.array([1.5, 3.8, 6.2, 8.6]); yo = np.array([0.6, -0.5, 0.9, 0.1])   # illustrative
    def K(a, b, l=1.0): return np.exp(-0.5 * (a[:, None] - b[None, :]) ** 2 / l ** 2)
    Koo = K(xo, xo) + 1e-6 * np.eye(4); Ko = K(X, xo); Kxx = K(X, X)
    sol = np.linalg.solve(Koo, Ko.T)
    mu = sol.T @ yo; cov = Kxx - Ko @ sol; sd = np.sqrt(np.clip(np.diag(cov), 0, None))
    Lc = np.linalg.cholesky(cov + 1e-7 * np.eye(len(X))); draws = mu[None, :] + (Lc @ rng.standard_normal((len(X), 5))).T
    def px(x): return -2.95 + 5.9 * x / 10
    def pz(y): return 0.62 + 0.42 * y
    R = Mesh(); offs = [-0.16, -0.08, 0.0, 0.08, 0.16]
    for k in range(5):
        col = mix(IVORY, BLUE, k / 4); y = offs[k]; wdt = 0.05
        rows = [[(Vector((px(x), y - wdt / 2, pz(f))), col), (Vector((px(x), y + wdt / 2, pz(f))), col)] for x, f in zip(X, draws[k])]
        R.grid(rows)
    R.obj(vcol_emission('ribbons', 1.15), 'ribbons')
    B = Mesh(); hw = 0.22; bc = ICE
    top = [[(Vector((px(x), -hw, pz(m + 2 * s))), bc), (Vector((px(x), hw, pz(m + 2 * s))), bc)] for x, m, s in zip(X, mu, sd)]
    bot = [[(Vector((px(x), -hw, pz(m - 2 * s))), bc), (Vector((px(x), hw, pz(m - 2 * s))), bc)] for x, m, s in zip(X, mu, sd)]
    back = [[(Vector((px(x), hw, pz(m - 2 * s))), bc), (Vector((px(x), hw, pz(m + 2 * s))), bc)] for x, m, s in zip(X, mu, sd)]
    for rows in (top, bot, back): B.grid(rows)   # no front wall, so the ribbons stay in view
    B.obj(vcol_translucent('band', 0.22, 0.10), 'band')
    P = Mesh()
    for x, y in zip(xo, yo):
        P.sphere((px(x), 0, pz(y)), 0.075, lambda n: (1.0, 0.98, 0.94), 24, 12)
    P.obj(vcol_emission('obs', 4.5), 'obs')
    glass_plate()
    floor(-0.02, base=(0.004, 0.005, 0.007), rough=0.12)
    world(haze=0.005); bloom(7, -0.5); key_light((-6, -8, 7), 180, 8)
    camera((-3.4, -6.3, 3.4), (0.1, 0.2, 0.5), 42, 7.6, 3.4)

elif variant == 'polytrope':
    # Lane-Emden equation for n = 3, solved here with a fourth order Runge-Kutta step from the series start
    n_pt = 3.0
    def le_rhs(x, s): return np.array([s[1], -max(s[0], 0.0) ** n_pt - 2.0 * s[1] / x])
    h = 1e-3; x = 1e-4; s = np.array([1.0 - x * x / 6.0, -x / 3.0]); xi, th = [0.0, x], [1.0, s[0]]
    while s[0] > 0:
        k1 = le_rhs(x, s); k2 = le_rhs(x + h / 2, s + h / 2 * k1); k3 = le_rhs(x + h / 2, s + h / 2 * k2); k4 = le_rhs(x + h, s + h * k3)
        s_new = s + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        if s_new[0] <= 0: x1 = x + h * s[0] / (s[0] - s_new[0]); dth1 = s[1]; xi.append(x1); th.append(0.0); break
        x += h; s = s_new; xi.append(x); th.append(s[0])
    xi, th = np.array(xi), np.array(th)
    # central temperature of the Sun as an n = 3 polytrope of ideal gas, mean molecular weight 0.62
    T_c = 6.674e-11 * 1.989e30 * 0.62 * 1.66054e-27 / (1.380649e-23 * 6.957e8 * (n_pt + 1) * x1 * abs(dth1))
    print('Lane-Emden n=3: xi_1 = %.5f, -xi_1^2 theta\'(xi_1) = %.5f, T_c = %.3e K' % (x1, -x1 * x1 * dth1, T_c))
    def theta(fr): return float(np.interp(fr * x1, xi, th))       # T / T_c at a fraction of the radius
    # the interior ramp: deep red envelope to a white yellow core, indexed by theta (T / T_c)
    ramp = [(0.0, (0.42, 0.05, 0.015)), (0.12, (0.80, 0.16, 0.03)), (0.32, (1.0, 0.36, 0.06)), (0.55, (1.0, 0.60, 0.16)),
            (0.80, (1.0, 0.82, 0.42)), (1.0, (1.0, 0.95, 0.80))]
    def interior(fr):
        t = theta(fr)
        for (t0, c0), (t1, c1) in zip(ramp[:-1], ramp[1:]):
            if t <= t1: c = mix(c0, c1, (t - t0) / (t1 - t0)); break
        return tuple(v * (0.30 + 0.70 * t ** 0.8) for v in c)
    sun = planck_rgb(5772.0); limb = planck_rgb(3600.0)
    print('photosphere colour', tuple(round(v, 3) for v in sun))
    C = Vector((0, 0, 1.78)); R0 = 1.5
    a0, a1 = math.radians(-165), math.radians(-75)     # the wedge: this range of azimuth, upper half (on grid lines)
    def in_wedge(n):
        az = math.atan2(n.y, n.x); return n.z > 0 and a0 < az < a1
    S = Mesh(); S.sphere(C, R0, lambda n: (1, 1, 1), 192, 96, keep=lambda n: not in_wedge(n))
    S.obj(sun_material('photo', sun, limb, 0.95, 0.62), 'photosphere')
    # the three cut faces, emissive in the interior colour; a small factor per face so the cut reads in depth
    F = Mesh(); nr = 140
    ua, ub = Vector((math.cos(a0), math.sin(a0), 0)), Vector((math.cos(a1), math.sin(a1), 0)); up = Vector((0, 0, 1))
    def face(du, dv, shade, na=48):
        rows = []
        for i in range(nr + 1):
            fr = i / nr; col = tuple(c * shade for c in interior(fr)); row = []
            for j in range(na + 1):
                t = j / na * math.pi / 2; p = C + R0 * fr * (du * math.cos(t) + dv * math.sin(t)); row.append((p, col))
            rows.append(row)
        F.grid(rows)
    face(ua, up, 0.80); face(ub, up, 0.92)
    # the equatorial face spans the azimuths a0 to a1
    rows = []
    for i in range(nr + 1):
        fr = i / nr; col = interior(fr); rows.append([(C + R0 * fr * Vector((math.cos(a), math.sin(a), 0)), col) for a in np.linspace(a0, a1, 49)])
    F.grid(rows)
    F.obj(vcol_emission('cuts', 2.1), 'cuts')
    # hairline shells at fractions of the radius, drawn where the cut crosses them
    Hl = Mesh(); hc = (1.0, 0.93, 0.80)
    for fr in (0.25, 0.5, 0.75):
        r = R0 * fr + 0.002
        for du in (ua, ub):
            Hl.tube([C + r * (du * math.cos(t) + up * math.sin(t)) for t in np.linspace(0, math.pi / 2, 60)], 0.0035, hc, 5)
        Hl.tube([C + r * Vector((math.cos(a), math.sin(a), 0.0005)) for a in np.linspace(a0, a1, 60)], 0.0035, hc, 5)
    Hl.obj(vcol_emission('shells', 0.9), 'shells')
    glass_plate(4.6, 4.6)
    floor(-0.02, base=(0.004, 0.005, 0.007), rough=0.14)
    world(haze=0.004); bloom(7, -0.55); key_light((-6, -8, 8), 60, 8)
    camera((-3.0, -9.8, 4.9), (0.05, 0.0, 1.5), 48, 10.4, 4.0)

elif variant == 'explorer':
    tr = json.load(open(os.path.join(os.path.dirname(os.path.abspath(out)), 'track.json')))
    lt, ll, lr, ph = (np.array(tr[k]) for k in ('log_Teff', 'log_L', 'log_R', 'phase'))
    def px(t): return -2.85 + 5.7 * (5.0 - t) / 1.6        # hot on the left
    def py(l): return -1.9 + 3.8 * (l + 1.2) / 4.9           # luminous at the back
    xs, ys = px(lt), py(ll)
    # thin the 13,024 rows by distance along the drawn path so the tube has about 700 points
    pts = [Vector((xs[0], ys[0], 0.03))]
    for x, y in zip(xs[1:], ys[1:]):
        if (Vector((x, y, 0.03)) - pts[-1]).length > 0.012: pts.append(Vector((x, y, 0.03)))
    pts.append(Vector((xs[-1], ys[-1], 0.03)))
    T = Mesh(); T.tube(pts, 0.007, IVORY, 6); T.obj(vcol_emission('track', 2.6), 'track')
    def first(cond):
        i = np.where(cond)[0]; return int(i[0])
    rows = [first(ph == 'ZAMS'), first(ph == 'SGB') - 1, first((ph == 'RGB') & (ll > 1.9)), first(ph == 'HeFlash') - 1,
            first(ph == 'RC') + 300, len(lt) - 1]
    P = Mesh(); H = Mesh()
    for i in rows:
        r = float(np.clip(0.05 * 10 ** (0.36 * lr[i]), 0.04, 0.34)); col = star_colour(10 ** lt[i]); c = (xs[i], ys[i], 0.03 + r)
        P.sphere(c, r, lambda n, col=col: col, 32, 16)
        H.sphere(c, r * 1.22, lambda n, col=col: col, 24, 12)
    P.obj(vcol_emission('stars', 2.6), 'stars'); H.obj(vcol_translucent('halo', 0.35, 0.14), 'halo')
    glass_plate()
    floor(-0.02, base=(0.004, 0.005, 0.007), rough=0.12)
    world(haze=0.005); bloom(7, -0.5); key_light((-6, -8, 7), 180, 8)
    camera((-3.6, -6.2, 4.3), (0.2, 0.2, 0.25), 40, 7.9, 3.6)

elif variant == 'tellurion':
    r_in, r_out, r_ph = 1.5, 3.6, 1.3
    def disc_col(r, x):
        t = (r - r_in) / (r_out - r_in); col = mix((1.0, 0.95, 0.85), AMBER, min(1.0, t * 1.3))
        b = (r_in / r) ** 1.8 * (1 - t) ** 0.8 * (1 + 0.65 * (-x / r))    # hotter inside, fading out, left side boosted
        return tuple(c * b for c in col)
    D = Mesh(); nr, nphi = 40, 120
    # the near half, flat
    rows = []
    for i in range(nr + 1):
        r = r_in + (r_out - r_in) * i / nr; row = []
        for j in range(nphi + 1):
            ph = math.pi + math.pi * j / nphi; x, y = r * math.cos(ph), r * math.sin(ph)
            row.append((Vector((x, y, 0)), disc_col(r, x)))
        rows.append(row)
    D.grid(rows)
    # the far half, folded over the top in the plane facing the camera
    rows = []
    for i in range(nr + 1):
        r = r_in + (r_out - r_in) * i / nr; row = []
        for j in range(nphi + 1):
            ph = math.pi * j / nphi; x = r * math.cos(ph); z = (r_ph + (r - r_in) * 0.42) * math.sin(ph)
            row.append((Vector((x, 0.0, z)), tuple(c * (1 - (r - r_in) / (r_out - r_in)) ** 0.8 for c in disc_col(r, x))))
        rows.append(row)
    D.grid(rows)
    # the thinner image below the shadow
    rows = []
    for i in range(nr + 1):
        r = r_in + (r_out - r_in) * i / nr; row = []
        for j in range(nphi + 1):
            ph = math.pi * j / nphi; x = r * math.cos(ph); z = -(r_ph * 0.94 + (r - r_in) * 0.06) * math.sin(ph)
            row.append((Vector((x, 0.0, z)), tuple(c * 0.22 for c in disc_col(r, x))))
        rows.append(row)
    D.grid(rows)
    D.obj(vcol_emission('disc', 1.75), 'disc')
    # the bright inner edge of the near half
    edge = [Vector((r_in * math.cos(t), r_in * math.sin(t), 0)) for t in np.linspace(math.pi, 2 * math.pi, 121)]
    Eg = Mesh(); Eg.tube(edge, 0.02, [tuple(min(1, c * 1.2) for c in disc_col(r_in, p.x)) for p in edge], 6); Eg.obj(vcol_emission('edge', 3.0), 'discedge')
    # the shadow and the photon ring in the plane facing the camera
    sphere_obj('shadow', (0, 0, 0), 1.0, principled('black', (0, 0, 0), 0.0, 1.0))
    ring = [Vector((r_ph * math.cos(t), 0, r_ph * math.sin(t))) for t in np.linspace(0, 2 * math.pi, 241)]
    Rg = Mesh(); Rg.tube(ring, 0.012, (1.0, 0.98, 0.93), 8); Rg.obj(vcol_emission('ring', 7.0), 'ring')
    Hz = Mesh(); Hz.tube(ring, 0.06, (1.0, 0.9, 0.7), 8); Hz.obj(vcol_translucent('ringhalo', 0.9, 0.3), 'ringhalo')
    floor(-3.4, base=(0.005, 0.006, 0.008), rough=0.3)
    world(haze=0.003); bloom(6, -0.5)   # a tighter glow, so the arch above and the thin disc below keep their shapes
    camera((0.0, -14.5, 0.8), (0.0, 0.0, 0.3), 55, 14.5, 5.6)

elif variant == 'nn':
    # the playground's data: 4,000 stars, 48 features (BP then RP coefficients over the star's flux scale), GSP-Spec [M/H]
    pg = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets', 'data', 'playground')
    hd = json.load(open(os.path.join(pg, 'gaia_xp_mh.json'))); raw = open(os.path.join(pg, hd['binary']), 'rb').read()
    arr = {a['name']: np.frombuffer(raw, np.dtype(a['dtype']).newbyteorder('<'), a['length'], a['offset']) for a in hd['arrays']}
    nS, d = hd['n'], 2 * hd['k']
    Xf = np.array(hd['feature_offset']) + arr['features'].reshape(nS, d).astype(float) * np.array(hd['feature_step'])
    y = arr['mh_gspspec'].astype(float); split = arr['split']; tr_ = split == 0; va_ = split == 1
    mu_x, sd_x = Xf[tr_].mean(0), Xf[tr_].std(0); sd_x[sd_x == 0] = 1; Z = (Xf - mu_x) / sd_x
    mu_y, sd_y = y[tr_].mean(), y[tr_].std()
    star = hd['examples'][1]['row']           # the example giant the playground follows by default
    print('star row', star, 'source_id', arr['source_id'][star], '[M/H]', arr['mh_gspspec'][star])
    # one training run of the playground's default network (48, 16, 16, 1; tanh; Adam, rate 0.003, batches of 64)
    sizes = [d, 16, 16, 1]; nr_ = np.random.default_rng(7)
    Wt = [nr_.normal(0, math.sqrt(2 / (a + b)) if i < 2 else math.sqrt(1 / a), (b, a)) for i, (a, b) in enumerate(zip(sizes[:-1], sizes[1:]))]
    bt = [np.zeros(b) for b in sizes[1:]]
    mW = [np.zeros_like(w) for w in Wt]; vW = [np.zeros_like(w) for w in Wt]; mb = [np.zeros_like(b) for b in bt]; vb = [np.zeros_like(b) for b in bt]
    def forward(x):
        acts = [x]
        for i, (w, b) in enumerate(zip(Wt, bt)):
            z_ = acts[-1] @ w.T + b; acts.append(np.tanh(z_) if i < 2 else z_)
        return acts
    Ztr, ytr = Z[tr_], (y[tr_] - mu_y) / sd_y; t_ = 0
    for ep in range(60):
        perm = nr_.permutation(len(ytr))
        for s0 in range(0, len(perm), 64):
            idx = perm[s0:s0 + 64]; acts = forward(Ztr[idx]); g = (acts[-1][:, 0] - ytr[idx])[:, None] * 2 / len(idx); t_ += 1
            for i in (2, 1, 0):
                gW, gb = g.T @ acts[i], g.sum(0)
                if i: g = (g @ Wt[i]) * (1 - acts[i] ** 2)
                for P, G, m_, v_ in ((Wt[i], gW, mW[i], vW[i]), (bt[i], gb, mb[i], vb[i])):
                    m_ *= 0.9; m_ += 0.1 * G; v_ *= 0.999; v_ += 0.001 * G * G
                    P -= 0.003 * (m_ / (1 - 0.9 ** t_)) / (np.sqrt(v_ / (1 - 0.999 ** t_)) + 1e-8)
    pred = forward(Z[va_])[-1][:, 0] * sd_y + mu_y
    print('validation RMSE [M/H] %.3f dex over %d stars' % (np.sqrt(np.mean((pred - y[va_]) ** 2)), va_.sum()))
    acts = forward(Z[star:star + 1]); zin = Z[star]
    print('estimate for the star %.2f' % (acts[-1][0, 0] * sd_y + mu_y))
    # layout: the network stands in depth along x; inputs as two columns (BP, RP), hidden layers as 4 by 4 grids
    zc = 1.95; cam_loc = Vector((-5.4, -8.6, 2.9))
    def in_pos(k):
        band, j = divmod(k, 24); return Vector((-3.0, 0.0, zc + 1.70 - (k * 0.068 + band * 0.14)))
    def hid_pos(layer, j):
        r, c = divmod(j, 4); return Vector((-0.9 + 2.0 * layer, -0.66 + 0.44 * c, zc + 0.66 - 0.44 * r))
    pos = [[in_pos(k) for k in range(d)], [hid_pos(0, j) for j in range(16)], [hid_pos(1, j) for j in range(16)], [Vector((3.0, 0.0, zc))]]
    dists = [(p - cam_loc).length for layer in pos for p in layer]; dmin, dmax = min(dists), max(dists)
    def depth(p): return math.exp(-2.0 * ((p - cam_loc).length - dmin) / (dmax - dmin))   # brightness falls off with depth
    # the input bars: the star's 48 standardised coefficients, as the network sees them; signed about a zero line
    lim = min(8, max(2, math.ceil(np.abs(zin).max()))); nrel = [int(arr['bp_n_relevant_bases'][star]), int(arr['rp_n_relevant_bases'][star])]
    Bm = Mesh(); x0 = -3.72
    for k in range(d):
        p = in_pos(k); v = float(zin[k]); ln = 0.62 * max(-1, min(1, v / lim)); dim = 1.0 if k % 24 < nrel[k // 24] else 0.3
        col = tuple(c * dim for c in (IVORY if v >= 0 else ICE)); xa, xb = sorted((x0, x0 - ln)); xb = max(xb, xa + 0.004)
        Bm.box((xa, p.y - 0.024, p.z - 0.022), (xb, p.y + 0.024, p.z + 0.022), col, col)
    for band in (0, 1):   # the zero lines of the BP and RP bands
        za, zb = in_pos(24 * band + 23).z - 0.03, in_pos(24 * band).z + 0.03; Bm.box((x0 - 0.003, -0.003, za), (x0 + 0.003, 0.003, zb), mix(ICE, (0, 0, 0), 0.6), mix(ICE, (0, 0, 0), 0.6))
    Bm.obj(vcol_emission('bars', 1.8), 'bars')
    # edges: the largest weights of each layer within the playground's budget of 400 lines (192, 192, 16)
    Em = Mesh(); budgets = [192, 192, 16]; ne = 0
    for l, w in enumerate(Wt):
        flat = np.argsort(-np.abs(w).ravel())[:budgets[l]]; wmax = np.abs(w).max()
        for f_ in flat:
            j, k = divmod(int(f_), w.shape[1]); s_ = float(abs(w[j, k]) / wmax); a, b = pos[l][k], pos[l + 1][j]
            base = mix(BLUE, IVORY, 0.6) if w[j, k] > 0 else mix(BLUE, (0, 0, 0), 0.1); amp = 0.06 + 0.94 * s_ ** 1.3
            Em.tube([a, b], 0.0026 + 0.003 * s_, [tuple(c * amp * depth(a) for c in base), tuple(c * amp * depth(b) for c in base)], 4); ne += 1
    print('edges', ne)
    Em.obj(vcol_emission('edges', 1.2), 'edges')
    # nodes: small spheres, glowing with the magnitude of their activation for this star
    Nd = Mesh()
    for l, layer in enumerate(pos):
        for j, p in enumerate(layer):
            if l == 0: r_, col = 0.021, mix(BLUE, IVORY, 0.4)
            elif l < 3: a_ = abs(float(acts[l][0, j])); r_, col = 0.058, tuple(c * (0.35 + 0.65 * a_) for c in mix(BLUE, IVORY, 0.25 + 0.5 * a_))
            else: r_, col = 0.12, (1.0, 0.95, 0.86)
            Nd.sphere(p, r_, lambda n, col=col, p=p: tuple(c * max(depth(p), 0.45) for c in col), 20, 10)
    Nd.obj(vcol_emission('nodes', 2.6), 'nodes')
    Ho = Mesh(); Ho.sphere(pos[3][0], 0.2, lambda n: (1.0, 0.9, 0.75), 24, 12); Ho.obj(vcol_translucent('outhalo', 0.5, 0.18), 'outhalo')
    glass_plate(9.0, 3.4)
    floor(-0.02, base=(0.004, 0.005, 0.007), rough=0.14)
    world(haze=0.005); bloom(7, -0.5); key_light((-6, -8, 7), 120, 8)
    camera(tuple(cam_loc), (-0.45, 0.0, 1.75), 40, 9.6, 4.5)

else:
    raise SystemExit('unknown variant ' + variant)

sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print('wrote', out)
