"""A neural network in Blender (Cycles): layers of glass-and-metal nodes in depth, thin connections, and a few lit
signal paths carrying light from a real Gaia DR3 XP spectrum of a red giant (drawn as a glowing ribbon in its own
wavelength colours) towards six outputs. Schematic.
Usage: uv run --python 3.11 --with bpy==4.2.0 python blender_network.py SPEC.json OUT.png [samples] [W] [H]"""
import json, math, random, sys
import bpy
from mathutils import Vector

spec = json.load(open(sys.argv[1])); out = sys.argv[2]
samples = int(sys.argv[3]) if len(sys.argv) > 3 else 128
W, H = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (1500, 1000)
random.seed(4)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'

def principled(name, base, metal=0.0, rough=0.4, trans=0.0, ior=1.45):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*base, 1); b.inputs['Metallic'].default_value = metal; b.inputs['Roughness'].default_value = rough
    b.inputs['Transmission Weight'].default_value = trans; b.inputs['IOR'].default_value = ior
    return m

def emissive(name, color, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (*color, 1); e.inputs['Strength'].default_value = strength
    nt.links.new(e.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface']); return m

GLASS = principled('glass', (0.85, 0.88, 0.95), 0.0, 0.05, trans=1.0)
CORE = emissive('core', (0.55, 0.65, 0.85), 1.2)
HOTCORE = emissive('hot', (1.0, 0.55, 0.15), 2.4)
WIRE = principled('wire', (0.35, 0.38, 0.45), 0.9, 0.4)
HOT = emissive('path', (1.0, 0.5, 0.12), 1.3)

def smooth(a, b, n=14):
    # an S-curve from a to b, flat at both ends in x
    out = []
    for k in range(n + 1):
        t = k / n; s_ = t * t * (3 - 2 * t)
        out.append(Vector((a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * s_, a.z + (b.z - a.z) * s_)))
    return out

def curve(points, mat, bevel):
    cd = bpy.data.curves.new('c', 'CURVE'); cd.dimensions = '3D'; cd.bevel_depth = bevel; cd.bevel_resolution = 2
    sp = cd.splines.new('POLY'); sp.points.add(len(points) - 1)
    for pt, p in zip(sp.points, points): pt.co = (*p, 1)
    ob = bpy.data.objects.new('c', cd); bpy.context.collection.objects.link(ob); ob.data.materials.append(mat); return ob

# layers along x, nodes on a curved sheet in y-z
L = [10, 14, 14, 10, 6]; xs = [0, 2.2, 4.4, 6.6, 8.8]; nodes = []
for li, n in enumerate(L):
    col = []
    for j in range(n):
        u = j / (n - 1) - 0.5
        z = u * (5.0 if n > 8 else 2.8); y = -0.9 * math.cos(u * math.pi)
        p = Vector((xs[li], y, z)); col.append(p)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.17, location=p); s = bpy.context.object
        s.data.materials.append(GLASS); [setattr(f, 'use_smooth', True) for f in s.data.polygons]
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.07, location=p); c = bpy.context.object; c.data.materials.append(CORE)
    nodes.append(col)
# connections: every pair, thin metal
for li in range(len(L) - 1):
    for a in nodes[li]:
        for b in nodes[li + 1]:
            if random.random() < 0.45:
                curve(smooth(a, b), WIRE, 0.005)
# lit routes: one per output
for k in range(6):
    j = random.randrange(L[0]); pts = [nodes[0][j]]
    for li in range(1, len(L)):
        jj = k if li == len(L) - 1 else random.randrange(L[li]); pts.append(nodes[li][jj])
    path = []
    for a, b in zip(pts[:-1], pts[1:]): path += smooth(a, b)[:-1]
    path.append(pts[-1]); curve(path, HOT, 0.014)
    for p in pts:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.085, location=p); c = bpy.context.object; c.data.materials.append(HOTCORE)
# the input: a real XP spectrum as a ribbon of light, in its own wavelength colours, feeding the first layer
def wl(l):
    r = g = b = 0.0
    if l < 440: r, b = -(l - 440) / 60, 1
    elif l < 490: g, b = (l - 440) / 50, 1
    elif l < 510: g, b = 1, -(l - 510) / 20
    elif l < 580: r, g = (l - 510) / 70, 1
    elif l < 645: r, g = 1, -(l - 645) / 65
    else: r = 1
    s = max(0.45, 1 - (l - 700) / 400) if l > 700 else 1
    return (max(r, 0) * s, max(g, 0) * s, max(b, 0) * s)
f = spec; n = len(f); mx, mn = max(f), min(f); step = 6
for i in range(0, n - step, step):
    a = Vector((-3.4 + 1.4 * (f[i] - mn) / (mx - mn), 0.0, -2.5 + 5.0 * i / n))
    b = Vector((-3.4 + 1.4 * (f[i + step] - mn) / (mx - mn), 0.0, -2.5 + 5.0 * (i + step) / n))
    curve([a, b], emissive(f'w{i}', wl(336 + 2 * i), 4), 0.028)
# fan from the spectrum into the first layer
for j, p in enumerate(nodes[0]):
    i = int((j + 0.5) / len(nodes[0]) * n); a = Vector((-3.4 + 1.4 * (f[i] - mn) / (mx - mn), 0.0, -2.5 + 5.0 * i / n))
    curve(smooth(a, p), emissive(f'fan{j}', wl(336 + 2 * i), 1.2), 0.004)

world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.008, 0.009, 0.013, 1)
ld = bpy.data.lights.new('key', 'AREA'); ld.energy = 900; ld.size = 8; ld.color = (0.75, 0.82, 1.0)
lo = bpy.data.objects.new('key', ld); bpy.context.collection.objects.link(lo); lo.location = (3, -6, 7); lo.rotation_euler = (Vector((4, 0, 0)) - lo.location).to_track_quat('-Z', 'Y').to_euler()
cam_d = bpy.data.cameras.new('cam'); cam_d.lens = 33; cam_d.dof.use_dof = True; cam_d.dof.focus_distance = 12.0; cam_d.dof.aperture_fstop = 2.2
cam = bpy.data.objects.new('cam', cam_d); bpy.context.collection.objects.link(cam); sc.camera = cam
cam.location = (-6.5, -10.0, 3.0); cam.rotation_euler = (Vector((3.6, 0.0, -0.2)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print('wrote', out)
