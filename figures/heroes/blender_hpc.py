"""A supercomputer cold aisle in Blender (Cycles): two rows of 42U racks (0.6 by 1.2 by 2.2 m) with perforated doors,
server faces and status lights behind them, a raised floor of tiles, light strips and cable trays overhead, light haze.
A schematic of the kind of hall that houses Deucalion and MareNostrum 5, not a model of either.
Usage: uv run --python 3.11 --with bpy==4.2.0 python blender_hpc.py OUT.png [samples] [W] [H] [phase]"""
import math, random, sys
import bpy, bmesh
from mathutils import Vector

out = sys.argv[1]; samples = int(sys.argv[2]) if len(sys.argv) > 2 else 128
W, H = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (1500, 1000)
phase = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.cycles.volume_step_rate = 4.0

def principled(name, base, metal=0.0, rough=0.4):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*base, 1); b.inputs['Metallic'].default_value = metal; b.inputs['Roughness'].default_value = rough
    return m

def emissive(name, color, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (*color, 1); e.inputs['Strength'].default_value = strength
    nt.links.new(e.outputs['Emission'], nt.nodes['Material Output'].inputs['Surface']); return m

BODY = principled('body', (0.018, 0.019, 0.022), 0.6, 0.38)
FACE = principled('face', (0.05, 0.052, 0.058), 0.7, 0.32)
TRIM = principled('trim', (0.5, 0.52, 0.56), 0.9, 0.25)
TRAY = principled('tray', (0.55, 0.42, 0.12), 0.8, 0.4)
LED = {'b': emissive('ledb', (0.12, 0.42, 1.0), 16), 'g': emissive('ledg', (0.15, 1.0, 0.45), 12), 'a': emissive('leda', (1.0, 0.55, 0.12), 14)}
DISP = {'b': LED['b'], 'g': LED['g']}
import os
if os.environ.get('NOLED'):
    LED = {k: emissive('off' + k, (0.02, 0.03, 0.05), 0.0) for k in 'bga'}
STRIP = emissive('strip', (0.92, 0.95, 1.0), 22)

# perforated door: holes from a Voronoi dot grid, transparent through the holes
DOOR = bpy.data.materials.new('door'); DOOR.use_nodes = True; nt = DOOR.node_tree; b = nt.nodes['Principled BSDF']
b.inputs['Base Color'].default_value = (0.03, 0.032, 0.036, 1); b.inputs['Metallic'].default_value = 0.8; b.inputs['Roughness'].default_value = 0.3
tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (0.56 * 60, 2.14 * 60, 1)
vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.voronoi_dimensions = '2D'; vo.feature = 'F1'; vo.inputs['Randomness'].default_value = 0.0
mt = nt.nodes.new('ShaderNodeMath'); mt.operation = 'GREATER_THAN'; mt.inputs[1].default_value = 0.36
tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
nt.links.new(tc.outputs['UV'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], vo.inputs['Vector'])
nt.links.new(vo.outputs['Distance'], mt.inputs[0]); nt.links.new(mt.outputs['Value'], mx.inputs['Fac'])
nt.links.new(tr.outputs['BSDF'], mx.inputs[1]); nt.links.new(b.outputs['BSDF'], mx.inputs[2])
nt.links.new(mx.outputs['Shader'], nt.nodes['Material Output'].inputs['Surface'])

# floor: tiles with seams, glossy
FLOOR = bpy.data.materials.new('floor'); FLOOR.use_nodes = True; nt = FLOOR.node_tree; b = nt.nodes['Principled BSDF']
br = nt.nodes.new('ShaderNodeTexBrick'); br.offset = 0.0; br.inputs['Scale'].default_value = 1.0 / 0.6
br.inputs['Color1'].default_value = (0.14, 0.145, 0.155, 1); br.inputs['Color2'].default_value = (0.12, 0.125, 0.135, 1); br.inputs['Mortar'].default_value = (0.02, 0.02, 0.022, 1)
br.inputs['Mortar Size'].default_value = 0.006; br.inputs['Brick Width'].default_value = 1.0; br.inputs['Row Height'].default_value = 1.0
tc2 = nt.nodes.new('ShaderNodeTexCoord'); nt.links.new(tc2.outputs['Object'], br.inputs['Vector']); nt.links.new(br.outputs['Color'], b.inputs['Base Color'])
b.inputs['Roughness'].default_value = 0.16; b.inputs['Metallic'].default_value = 0.2

class Batch:
    # many boxes in one mesh per material: fast to build, fast to render
    def __init__(self): self.bm = {}
    def add(self, loc, size, mat):
        bm = self.bm.setdefault(mat.name, (bmesh.new(), mat))[0]
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v in r['verts']:
            v.co = Vector((loc[0] + v.co.x * size[0], loc[1] + v.co.y * size[1], loc[2] + v.co.z * size[2]))
    def build(self):
        for name, (bm, mat) in self.bm.items():
            me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
            ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); ob.data.materials.append(mat)
B = Batch()

def box(name, loc, size, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.name = name; o.scale = size; o.data.materials.append(mat); return o

RW, RD, RH, AISLE, N = 0.6, 1.2, 2.2, 1.2, 22
for side in (-1, 1):
    yface = side * AISLE / 2                       # the door plane faces the aisle
    yc = yface + side * RD / 2
    for i in range(N):
        x = i * (RW + 0.01)
        box('rack', (x, yc + side * 0.05, RH / 2), (RW, RD - 0.1, RH), BODY)
        for sx in (-1, 1): box('side', (x + sx * (RW / 2 - 0.01), yface + side * 0.05, RH / 2), (0.02, 0.1, RH), BODY)
        box('top', (x, yface + side * 0.05, RH - 0.01), (RW, 0.1, 0.02), BODY)
        box('trimL', (x - RW / 2 + 0.015, yface + side * 0.01, RH / 2), (0.03, 0.03, RH), TRIM)
        # server faces 6 cm behind the door, with status lights
        yb = yface + side * 0.06
        box('face', (x, yb + side * 0.005, RH / 2), (RW - 0.06, 0.01, RH - 0.2), FACE)
        for u in range(40):
            z = 0.12 + u * 0.0445
            if random.random() < 0.85:
                col = random.choices('bga', weights=(5, 3, 1))[0]
                if (u + i + int(phase * 7)) % 11 == 0: col = 'a'
                B.add((x - RW / 2 + 0.07 + random.random() * 0.06, yb - side * 0.002, z), (0.012, 0.004, 0.006), LED[col])
                for q in range(random.randint(1, 4)): B.add((x + 0.02 + q * 0.025, yb - side * 0.002, z), (0.007, 0.004, 0.005), LED[random.choice('bbg')])
        box('display', (x + 0.12, yface + side * 0.012, RH - 0.12), (0.14, 0.005, 0.05), DISP['b'] if i % 3 else DISP['g'])
        # perforated door
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x, yface, RH / 2)); d = bpy.context.object
        d.scale = (RW - 0.04, RH - 0.06, 1); d.rotation_euler = (math.pi / 2, 0, 0); d.data.materials.append(DOOR)
for side in (-1, 1):
    box('kick', (N * 0.3, side * AISLE / 2, 0.02), (N * 0.62, 0.01, 0.006), emissive('kick', (0.35, 0.55, 1.0), 6))
B.build()
# floor and ceiling
bpy.ops.mesh.primitive_plane_add(size=1, location=(N * 0.3, 0, 0)); f = bpy.context.object; f.scale = (N * 0.7 + 8, 12, 1); f.data.materials.append(FLOOR)
bpy.ops.mesh.primitive_plane_add(size=1, location=(N * 0.3, 0, 3.2)); c = bpy.context.object; c.scale = (N * 0.7 + 8, 12, 1); c.rotation_euler[0] = math.pi; c.data.materials.append(principled('ceil', (0.02, 0.02, 0.024), 0, 0.8))
# light strips over the aisle and cable trays over the racks
for x0 in range(0, N, 3):
    box('strip', (x0 * 0.61 + 0.6, 0, 3.05), (1.2, 0.06, 0.02), STRIP)
for side in (-1, 1):
    box('tray', (N * 0.3, side * (AISLE / 2 + 0.6), 2.55), (N * 0.62, 0.3, 0.06), TRAY)
    box('trayside', (N * 0.3, side * (AISLE / 2 + 0.45), 2.6), (N * 0.62, 0.01, 0.12), TRAY)
# end-of-aisle wall glow
bpy.ops.mesh.primitive_plane_add(size=1, location=(N * 0.61 + 1.5, 0, 1.4)); g = bpy.context.object; g.scale = (2.8, 2.6, 1); g.rotation_euler = (math.pi / 2, 0, math.pi / 2); g.data.materials.append(emissive('glow', (0.45, 0.6, 1.0), 0.5))

world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True; wn = world.node_tree
wn.nodes['Background'].inputs['Color'].default_value = (0.004, 0.005, 0.007, 1)
vol = wn.nodes.new('ShaderNodeVolumePrincipled'); vol.inputs['Density'].default_value = 0.05; vol.inputs['Color'].default_value = (0.8, 0.85, 1.0, 1)
wn.links.new(vol.outputs['Volume'], wn.nodes['World Output'].inputs['Volume'])

cam_d = bpy.data.cameras.new('cam'); cam_d.lens = 22; cam_d.dof.use_dof = True; cam_d.dof.focus_distance = 3.2; cam_d.dof.aperture_fstop = 2.8
cam = bpy.data.objects.new('cam', cam_d); bpy.context.collection.objects.link(cam); sc.camera = cam
cam.location = (-1.4, 0.18, 1.45); cam.rotation_euler = (Vector((12.0, -0.05, 1.15)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print('wrote', out)
