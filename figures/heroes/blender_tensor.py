"""Deep learning as a stack of tensor layers (Blender, Cycles): thin glass slabs receding in depth, each carrying a
grid of activation columns whose height and glow encode their value; the first layer holds the 48 real Gaia XP
coefficients of a red giant (24 BP, 24 RP), later layers are schematic and narrow towards the output. Light threads
join strongly active units of successive layers. Schematic.
Usage: uv run --python 3.11 --with bpy==4.2.0 python blender_tensor.py COEFFS.json OUT.png [samples] [W] [H] [phase]"""
import json, math, random, sys
import bpy
from mathutils import Vector

coef = json.load(open(sys.argv[1])); out = sys.argv[2]
samples = int(sys.argv[3]) if len(sys.argv) > 3 else 128
W, H = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (1500, 1000)
phase = float(sys.argv[6]) if len(sys.argv) > 6 else 0.0
random.seed(11)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'

def principled(name, base, metal=0.0, rough=0.4, trans=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*base, 1); b.inputs['Metallic'].default_value = metal; b.inputs['Roughness'].default_value = rough
    b.inputs['Transmission Weight'].default_value = trans; return m

_em = {}
def emissive(color, strength):
    key = (tuple(round(c, 2) for c in color), round(strength, 1))
    if key in _em: return _em[key]
    m = bpy.data.materials.new('e'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (*color, 1); e.inputs['Strength'].default_value = strength
    nt.links.new(e.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface']); _em[key] = m; return m

GLASS = principled('glass', (0.8, 0.9, 1.0), 0.0, 0.08, trans=1.0)
DARK = principled('dark', (0.03, 0.035, 0.045), 0.6, 0.35)
EDGE = emissive((0.3, 0.6, 1.0), 0.9)
CYAN = (0.08, 0.45, 1.0); AMBER = (1.0, 0.42, 0.05)

def lerp(a, b, t): return tuple(x + (y - x) * t for x, y in zip(a, b))

def box(loc, size, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.scale = size; o.data.materials.append(mat); return o

# layer shapes (rows x cols): input 6 x 8 from the 48 coefficients, then wider hidden layers, then a narrow head
shapes = [(6, 8), (12, 12), (12, 12), (10, 10), (6, 6), (2, 3)]
X = [0.0, 3.0, 5.6, 8.0, 10.2, 12.0]
pitch = 0.32
# normalised input values
c = [abs(v) for v in coef]; cm = max(c); vin = [v / cm for v in c]
active = []
for li, (rws, cls) in enumerate(shapes):
    w, h = cls * pitch, rws * pitch
    x = X[li]
    box((x, 0, 0), (0.06, w + 0.3, h + 0.3), GLASS)                     # the glass slab
    for (dy, dz, sy, sz) in ((0, h / 2 + 0.15, w + 0.3, 0.012), (0, -h / 2 - 0.15, w + 0.3, 0.012), (w / 2 + 0.15, 0, 0.012, h + 0.3), (-w / 2 - 0.15, 0, 0.012, h + 0.3)):
        box((x, dy, dz), (0.07, sy, sz), EDGE)                            # lit slab edges
    cells = []
    for r in range(rws):
        for k in range(cls):
            if li == 0: v = vin[r * cls + k]
            else:
                # a smooth field with a few hot spots, shifting with the phase for animation
                v = 0.5 + 0.5 * math.sin(1.7 * r + 2.3 * k + li * 1.3 + phase * 2 * math.pi) * math.cos(0.9 * k - 1.1 * r + li)
                v = max(0.0, min(1.0, v * (0.6 + 0.8 * random.random())))
            y = (k - (cls - 1) / 2) * pitch; z = (r - (rws - 1) / 2) * pitch
            d = 0.06 + 0.5 * v                                              # column depth along -x (towards the viewer side)
            box((x - 0.03 - d / 2, y, z), (d, pitch * 0.62, pitch * 0.62), DARK)
            col = lerp(CYAN, AMBER, v ** 2) if li < len(shapes) - 1 else AMBER
            box((x - 0.04 - d, y, z), (0.012, pitch * 0.62, pitch * 0.62), emissive(col, 0.35 + 2.6 * v ** 1.8))
            cells.append((Vector((x - 0.05 - d, y, z)), Vector((x + 0.04, y, z)), v))
    active.append(cells)
# light threads between strongly active units of neighbouring layers
def thread(a, b, col, strength, r=0.006):
    d = b - a; L = d.length
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=r, depth=L, location=(a + b) / 2)
    o = bpy.context.object; o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler(); o.data.materials.append(emissive(col, strength))
for li in range(len(active) - 1):
    src = sorted(active[li], key=lambda t: -t[2])[:14]; dst = sorted(active[li + 1], key=lambda t: -t[2])[:10]
    for s_ in src:
        for d_ in random.sample(dst, 3):
            thread(s_[1], d_[0], lerp(CYAN, AMBER, (s_[2] + d_[2]) / 2), 0.8 + 1.6 * s_[2] * d_[2])
# floor reflection plane
bpy.ops.mesh.primitive_plane_add(size=60, location=(6, 0, -2.6)); f = bpy.context.object
f.data.materials.append(principled('floor', (0.01, 0.012, 0.016), 0.6, 0.18))
world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.004, 0.005, 0.008, 1)
vol = world.node_tree.nodes.new('ShaderNodeVolumePrincipled'); vol.inputs['Density'].default_value = 0.01
world.node_tree.links.new(vol.outputs['Volume'], world.node_tree.nodes['World Output'].inputs['Volume'])
ld = bpy.data.lights.new('rim', 'AREA'); ld.energy = 600; ld.size = 6; ld.color = (0.6, 0.75, 1.0)
lo = bpy.data.objects.new('rim', ld); bpy.context.collection.objects.link(lo); lo.location = (14, 6, 6); lo.rotation_euler = (Vector((6, 0, 0)) - lo.location).to_track_quat('-Z', 'Y').to_euler()
cam_d = bpy.data.cameras.new('cam'); cam_d.lens = 38; cam_d.dof.use_dof = True; cam_d.dof.focus_distance = 11.0; cam_d.dof.aperture_fstop = 2.0
cam = bpy.data.objects.new('cam', cam_d); bpy.context.collection.objects.link(cam); sc.camera = cam
cam.location = (-5.5, -8.5, 2.6); cam.rotation_euler = (Vector((6.0, 0.4, -0.3)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print('wrote', out)
