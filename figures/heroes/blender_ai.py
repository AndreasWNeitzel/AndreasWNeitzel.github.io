"""Three designs for the deep-learning card (Blender, Cycles). The input is always a real Gaia DR3 XP spectrum of a
red giant (its 343 sampled fluxes) or its 48 coefficients.
  points   : layers as dense sheets of tiny emissive points (activation fields), thin light filaments between them
  fibres   : thousands of light filaments leave the spectrum, converge through a bottleneck (the latent space) and
             fan out to six outputs, like a bundle of optical fibres
  manifold : a learned latent surface, a fine glowing mesh that the spectrum's light falls onto and bends
Usage: uv run --python 3.11 --with bpy==4.2.0 python blender_ai.py VARIANT SPEC.json OUT.png [samples] [W] [H]"""
import json, math, random, sys, os
import bpy, bmesh
from mathutils import Vector

variant, spec, out = sys.argv[1], json.load(open(sys.argv[2])), sys.argv[3]
samples = int(sys.argv[4]) if len(sys.argv) > 4 else 96
W, H = (int(sys.argv[5]), int(sys.argv[6])) if len(sys.argv) > 6 else (1200, 800)
PHASE = float(sys.argv[7]) if len(sys.argv) > 7 else 0.0
random.seed(5)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y = W, H
if os.environ.get('CYCLES_DEVICE') == 'GPU':  # the CPU path in this wheel uses two or three cores; the GPU is the same tracer
    pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'CUDA'; pr.get_devices()
    for dv in pr.devices: dv.use = dv.type == 'CUDA'
    sc.cycles.device = 'GPU'; sc.cycles.denoising_use_gpu = True
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'

def emissive(color, strength, name='e'):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (*color, 1); e.inputs['Strength'].default_value = strength
    nt.links.new(e.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface']); return m

def attr_emissive(strength, name='ae'):
    """Emission coloured per vertex from a colour attribute 'col'."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    a = nt.nodes.new('ShaderNodeAttribute'); a.attribute_name = 'col'
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Strength'].default_value = strength
    nt.links.new(a.outputs['Color'], e.inputs['Color']); nt.links.new(e.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface']); return m

def pass_emissive(base, boost, name='pe', width=0.7):
    # Emission from the vertex colour 'col', brightened where the training front passes. The front's x position and
    # direction are scene properties 'front' and 'back' (0 forward, 1 backward), keyframed for the animation.
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    N = nt.nodes.new; L = nt.links.new
    a = N('ShaderNodeAttribute'); a.attribute_name = 'col'
    fr = N('ShaderNodeAttribute'); fr.attribute_type = 'VIEW_LAYER'; fr.attribute_name = 'front'
    bk = N('ShaderNodeAttribute'); bk.attribute_type = 'VIEW_LAYER'; bk.attribute_name = 'back'
    geo = N('ShaderNodeNewGeometry'); sep = N('ShaderNodeSeparateXYZ'); L(geo.outputs['Position'], sep.inputs[0])
    sub = N('ShaderNodeMath'); sub.operation = 'SUBTRACT'; L(sep.outputs['X'], sub.inputs[0]); L(fr.outputs['Fac'], sub.inputs[1])
    dv = N('ShaderNodeMath'); dv.operation = 'DIVIDE'; dv.inputs[1].default_value = width; L(sub.outputs[0], dv.inputs[0])
    sq = N('ShaderNodeMath'); sq.operation = 'MULTIPLY'; L(dv.outputs[0], sq.inputs[0]); L(dv.outputs[0], sq.inputs[1])
    ng = N('ShaderNodeMath'); ng.operation = 'MULTIPLY'; ng.inputs[1].default_value = -1.0; L(sq.outputs[0], ng.inputs[0])
    ex = N('ShaderNodeMath'); ex.operation = 'EXPONENT'; L(ng.outputs[0], ex.inputs[0])
    fwdc = N('ShaderNodeRGB'); fwdc.outputs[0].default_value = (1.0, 0.5, 0.12, 1)
    bwdc = N('ShaderNodeRGB'); bwdc.outputs[0].default_value = (0.35, 0.7, 1.0, 1)
    pc = N('ShaderNodeMix'); pc.data_type = 'RGBA'; L(bk.outputs['Fac'], pc.inputs['Factor']); L(fwdc.outputs[0], pc.inputs[6]); L(bwdc.outputs[0], pc.inputs[7])
    mc = N('ShaderNodeMix'); mc.data_type = 'RGBA'; L(ex.outputs[0], mc.inputs['Factor']); L(a.outputs['Color'], mc.inputs[6]); L(pc.outputs[2], mc.inputs[7])
    st = N('ShaderNodeMath'); st.operation = 'MULTIPLY_ADD'; st.inputs[1].default_value = boost; st.inputs[2].default_value = base; L(ex.outputs[0], st.inputs[0])
    e = N('ShaderNodeEmission'); L(mc.outputs[2], e.inputs['Color']); L(st.outputs[0], e.inputs['Strength'])
    L(e.outputs[0], nt.nodes['Material Output'].inputs['Surface']); return m

def wl(l):
    r = g = b = 0.0
    if l < 440: r, b = -(l - 440) / 60, 1
    elif l < 490: g, b = (l - 440) / 50, 1
    elif l < 510: g, b = 1, -(l - 510) / 20
    elif l < 580: r, g = (l - 510) / 70, 1
    elif l < 645: r, g = 1, -(l - 645) / 65
    else: r = 1
    s = max(0.4, 1 - (l - 700) / 400) if l > 700 else 1
    return (max(r, 0) * s, max(g, 0) * s, max(b, 0) * s)

CYAN, AMBER, WHITE = (0.12, 0.5, 1.0), (1.0, 0.45, 0.08), (0.9, 0.93, 1.0)
def mix(a, b, t): return tuple(x + (y - x) * t for x, y in zip(a, b))

class Cloud:
    """Many tiny points in one mesh: each point is a small octahedron, coloured through a vertex attribute."""
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
    def obj(self, mat):
        me = bpy.data.meshes.new('cloud'); self.bm.to_mesh(me); self.bm.free()
        ob = bpy.data.objects.new('cloud', me); bpy.context.collection.objects.link(ob); ob.data.materials.append(mat); return ob

def curve_pts(a, b, n=24, bow=Vector((0, 0, 0))):
    out = []
    for k in range(n + 1):
        t = k / n; s = t * t * (3 - 2 * t)
        p = Vector((a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * s, a.z + (b.z - a.z) * s)) + bow * math.sin(math.pi * t)
        out.append(p)
    return out

f = spec; n = len(f); mx, mn = max(f), min(f); fn = [(v - mn) / (mx - mn) for v in f]

if variant == 'points':
    cl = Cloud(); thr = Cloud()
    sheets = [(0.0, 1.0, 96, 56), (2.6, 1.15, 80, 80), (5.0, 1.05, 72, 72), (7.3, 0.9, 60, 60), (9.4, 0.7, 44, 44), (11.2, 0.45, 24, 24)]
    blobs = [[(random.random(), random.random(), 0.035 + 0.06 * random.random()) for _ in range(14)] for _ in sheets]
    hot = []
    for si, (x, sc_, nx, ny) in enumerate(sheets):
        w, h = 4.6 * sc_, 4.6 * sc_; pts = []
        for i in range(nx):
            for j in range(ny):
                y = (i / (nx - 1) - 0.5) * w; z = (j / (ny - 1) - 0.5) * h
                if si == 0:
                    v = 1.0 if fn[int(i / (nx - 1) * (n - 1))] >= j / (ny - 1) else 0.08   # the spectrum drawn as a lit area
                    col = mix(wl(336 + 2 * int(i / (nx - 1) * (n - 1))), WHITE, 0.35) if v > 0.5 else mix(CYAN, WHITE, 0.2); v = v * 0.6
                else:
                    uu, vv = i / (nx - 1), j / (ny - 1)
                    v = 0.06 + sum(math.exp(-((uu - bx) ** 2 + (vv - by) ** 2) / (2 * bs * bs)) for bx, by, bs in blobs[si])
                    v = max(0.03, min(1.0, v)) ** 1.6
                    col = mix(CYAN, AMBER, v)
                p = Vector((x, y, z)); cl.point(p, 0.011 + 0.022 * v, mix((0.02, 0.05, 0.12), col, 0.2 + 0.8 * v))
                if v > 0.7: pts.append(p)
        random.shuffle(pts); hot.append(pts[:40])
    for a_set, b_set in zip(hot[:-1], hot[1:]):
        for a in a_set[:30]:
            b = random.choice(b_set); thr.tube(curve_pts(a, b, 18), 0.0028, mix(CYAN, AMBER, random.random() * 0.6))
    cl.obj(attr_emissive(2.4)); thr.obj(attr_emissive(1.2))
    cam_loc, look, lens = Vector((-5.0, -8.8, 2.6)), Vector((5.4, 0.2, -0.1)), 36

elif variant == 'panels':
    GLASS = bpy.data.materials.new('glass'); GLASS.use_nodes = True; gnt = GLASS.node_tree; gnt.nodes.remove(gnt.nodes['Principled BSDF'])
    tr = gnt.nodes.new('ShaderNodeBsdfTransparent'); gl_ = gnt.nodes.new('ShaderNodeBsdfGlossy'); gl_.inputs['Roughness'].default_value = 0.05
    tint = gnt.nodes.new('ShaderNodeEmission'); tint.inputs['Color'].default_value = (0.2, 0.4, 0.9, 1); tint.inputs['Strength'].default_value = 0.025
    m1 = gnt.nodes.new('ShaderNodeMixShader'); m1.inputs['Fac'].default_value = 0.06; m2 = gnt.nodes.new('ShaderNodeAddShader')
    gnt.links.new(tr.outputs[0], m1.inputs[1]); gnt.links.new(gl_.outputs[0], m1.inputs[2]); gnt.links.new(m1.outputs[0], m2.inputs[0]); gnt.links.new(tint.outputs[0], m2.inputs[1])
    gnt.links.new(m2.outputs[0], gnt.nodes['Material Output'].inputs['Surface'])
    dots = Cloud(); lines = Cloud(); thr = Cloud()
    ICE, DIM = (0.55, 0.78, 1.0), (0.10, 0.20, 0.38)
    sheets = [(0.0, 1.0, 110, 70), (2.4, 1.12, 96, 96), (4.7, 1.04, 84, 84), (6.9, 0.92, 70, 70), (9.0, 0.76, 54, 54), (10.9, 0.55, 36, 36), (12.5, 0.32, 16, 16)]
    hot = []
    for si, (x, scl, nx, ny) in enumerate(sheets):
        w = h = 4.8 * scl
        # thin glass plane with hairline edges
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x + 0.02, 0, 0)); g = bpy.context.object; g.scale = (h + 0.25, w + 0.25, 1); g.rotation_euler = (0, math.pi / 2, 0); g.data.materials.append(GLASS)
        e = (w + 0.25) / 2; f_ = (h + 0.25) / 2
        corners = [Vector((x, -e, -f_)), Vector((x, e, -f_)), Vector((x, e, f_)), Vector((x, -e, f_)), Vector((x, -e, -f_))]
        lines.tube(corners, 0.006, (0.35, 0.6, 1.0), sides=4)
        blobs = [(random.random(), random.random(), 0.03 + 0.05 * random.random(), 0.4 + 0.6 * random.random()) for _ in range(9 + si)]
        pts = []
        for i in range(nx):
            for j in range(ny):
                uu, vv = i / (nx - 1), j / (ny - 1)
                y = (uu - 0.5) * w; z = (vv - 0.5) * h
                if si == 0:
                    k = int(uu * (n - 1)); line = math.exp(-((vv - (0.12 + 0.76 * fn[k])) ** 2) / 0.0006)
                    v = 0.05 + 0.95 * line
                else:
                    v = 0.04 + sum(a_ * (0.75 + 0.25 * math.sin(2 * math.pi * PHASE + 7 * bx)) * math.exp(-((uu - bx - 0.03 * math.sin(2 * math.pi * PHASE + 5 * by)) ** 2 + (vv - by - 0.03 * math.cos(2 * math.pi * PHASE + 3 * bx)) ** 2) / (2 * bs * bs)) for bx, by, bs, a_ in blobs)
                    v = min(1.0, v) ** 1.4
                if v < 0.06 and ((i * 73856093) ^ (j * 19349663) ^ (si * 83492791)) % 1000 < 550: continue   # fixed per point, so frames do not flicker
                col = mix(DIM, ICE, min(1, v * 1.3))
                if si > 0 and v > 0.82: col = mix(ICE, AMBER, (v - 0.82) / 0.18)
                if si == 0 and v > 0.5: col = mix(ICE, WHITE, 0.6)
                pp = Vector((x, y, z)); dots.point(pp, 0.007 + 0.012 * v, col)
                if v > 0.7: pts.append(pp)
        random.Random(si).shuffle(pts); hot.append(pts[:24])
    # threads between fixed anchor points (the same in every frame of a loop)
    tr_rng = random.Random(77)
    def anchor(si):
        x, scl, nx, ny = sheets[si]; w = 4.8 * scl
        return Vector((x, (tr_rng.random() - 0.5) * w * 0.45, (tr_rng.random() - 0.5) * w * 0.45))
    for si in range(len(sheets) - 1):
        for _ in range(8):
            thr.tube(curve_pts(anchor(si), anchor(si + 1), 20), 0.0016, (0.5, 0.75, 1.0), sides=4)
    dots.obj(pass_emissive(2.6, 5.0, width=1.1)); lines.obj(attr_emissive(0.9)); thr.obj(pass_emissive(0.5, 9.0, width=1.0))
    cam_loc, look, lens = Vector((-7.5, -11.0, 3.4)), Vector((6.2, 0.2, -0.2)), 38
    fstop = 5.6

elif variant == 'fibres':
    cl = Cloud(); N = 900
    outs = [Vector((11.0, (k - 2.5) * 0.9, 0.0)) for k in range(6)]
    N = 900
    for q in range(N):
        i = random.randrange(n)
        a = Vector((0.0, (i / (n - 1) - 0.5) * 6.0, (fn[i] - 0.5) * 2.6 + random.gauss(0, 0.05)))
        mid = Vector((5.5, random.gauss(0, 0.12), random.gauss(0, 0.12)))   # the bottleneck
        b = outs[q % 6] + Vector((0, random.gauss(0, 0.05), random.gauss(0, 0.05)))
        col = wl(336 + 2 * i); t = (q % 6) / 5
        path = curve_pts(a, mid, 26)[:-1] + curve_pts(mid, b, 22)
        # colour fades from the wavelength colour to amber as information is compressed
        pts = curve_pts(a, mid, 26)[:-1] + curve_pts(mid, b, 22); m_ = len(pts); end = mix(CYAN, AMBER, (q % 6) / 5 * 0.85)
        start = mix(col, WHITE, 0.15)
        cs = []
        for ii in range(m_):
            t = ii / (m_ - 1)
            cs.append(mix(start, CYAN, (t / 0.5) ** 1.5) if t < 0.5 else mix(CYAN, end, ((t - 0.5) / 0.5) ** 1.2))
        cl.tube(pts, 0.0026, cs, sides=4)
    for k, o in enumerate(outs): cl.point(o, 0.09, AMBER)
    for i in range(0, n, 2): cl.point(Vector((0.0, (i / (n - 1) - 0.5) * 6.0, (fn[i] - 0.5) * 2.6)), 0.035, wl(336 + 2 * i))
    cl.obj(attr_emissive(1.5))
    cam_loc, look, lens = Vector((5.2, -10.5, 5.5)), Vector((5.4, 0.0, -0.2)), 30

else:  # manifold
    cl = Cloud(); nu, nv = 160, 96
    def surf(u, v):
        return Vector((u * 10.0, (v - 0.5) * 6.0, 0.9 * math.sin(2.2 * u * math.pi) * math.cos(1.3 * v * math.pi) + 0.6 * math.sin(3.1 * v + 4 * u)))
    for i in range(nu):
        cl.tube([surf(i / (nu - 1), j / (nv - 1)) for j in range(nv)], 0.004, mix(CYAN, WHITE, 0.15))
    for j in range(0, nv, 2):
        cl.tube([surf(i / (nu - 1), j / (nv - 1)) for i in range(nu)], 0.003, mix(CYAN, WHITE, 0.1))
    # stars of the spectrum fall onto the surface and settle at their place in the latent space
    for q in range(3000):
        i = random.randrange(n); u = random.random(); v = random.random()
        p = surf(u, v) + Vector((0, 0, 0.03)); hot = math.exp(-((u - 0.62) ** 2 + (v - 0.45) ** 2) / 0.02)
        cl.point(p, 0.022 + 0.04 * hot, mix(wl(336 + 2 * i), AMBER, hot))
    cl.obj(attr_emissive(2.4))
    cam_loc, look, lens = Vector((0.5, -7.2, 4.4)), Vector((5.6, 0.4, -0.2)), 30

world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.003, 0.004, 0.007, 1)
cam_d = bpy.data.cameras.new('cam'); cam_d.lens = lens; cam_d.dof.use_dof = True; cam_d.dof.focus_distance = (look - cam_loc).length; cam_d.dof.aperture_fstop = globals().get('fstop', 1.8)
cam = bpy.data.objects.new('cam', cam_d); bpy.context.collection.objects.link(cam); sc.camera = cam
cam.location = cam_loc; cam.rotation_euler = (look - cam_loc).to_track_quat('-Z', 'Y').to_euler()
# bloom-like glow in the compositor
sc.use_nodes = True; ct = sc.node_tree; rl = ct.nodes['Render Layers']; comp = ct.nodes['Composite']
gl = ct.nodes.new('CompositorNodeGlare'); gl.glare_type = 'FOG_GLOW'; gl.quality = 'HIGH'; gl.size = 8; gl.threshold = 0.6; gl.mix = -0.55
ct.links.new(rl.outputs['Image'], gl.inputs['Image']); ct.links.new(gl.outputs['Image'], comp.inputs['Image'])
vl = sc.view_layers[0]
if len(sys.argv) > 8 and sys.argv[8].startswith('anim'):
    F = int(sys.argv[8][4:]); sc.frame_start, sc.frame_end = 1, F; sc.render.fps = 30
    # one beat per layer gap, in both directions, at a constant rate (linear keys); the direction flips while the
    # front is outside the stack, so the loop has no pause and no easing
    xs = [-3.0] + [sh[0] for sh in sheets] + [15.0]
    path = [(x, 0) for x in xs] + [(x, 1) for x in reversed(xs[:-1])]
    step = F / (len(path) - 1)
    vl['front'] = 0.0; vl['back'] = 0.0
    for k_, (x, bk) in enumerate(path):
        fr_ = 1 + k_ * step
        vl['front'] = x; vl.keyframe_insert('["front"]', frame=fr_)
        vl['back'] = float(bk); vl.keyframe_insert('["back"]', frame=fr_)
    vl['back'] = 1.0; vl.keyframe_insert('["back"]', frame=1 + (len(xs) - 1) * step)
    ad = sc.animation_data
    for fc in ad.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT' if '"back"' in fc.data_path else 'LINEAR'
    sc.frame_end = F
    sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = out + '/f_'
    bpy.ops.render.render(animation=True)
elif len(sys.argv) > 8 and sys.argv[8].startswith('at'):
    # one frame of the combined loop: the weights at PHASE, the training front at x with direction b
    fx, fb = sys.argv[8][2:].split(','); vl['front'] = float(fx); vl['back'] = float(fb)
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
else:
    vl['front'] = 6.0; vl['back'] = 0.0
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
print('wrote', out)
