"""Header renders for the field guide pages on PLATO and Ariel.

Both spacecraft are schematic models after the public ESA descriptions (the PLATO mission page and definition study
report, the Ariel factsheet), not engineering models; no ESA image, drawing or model was used. Proportions are
approximate, and small parts (thrusters, antennas, harness, star trackers) are left out or reduced to blocks.

Variants:
  plato : 26 cameras on the optical bench. The 24 normal cameras sit in four groups of six, each group on its own
          mounting face tilted 9.2 degrees away from the common axis towards its quadrant, so the four fields
          overlap in the middle; the two fast cameras sit between the groups and point along the common axis. Each
          camera is a short cylindrical telescope with a flared sunshade lip and a dark entrance lens. The bench sits
          on bipods above the hexagonal service module in gold insulation, and a large flat sunshield carrying the
          solar cells stands on one side, with two side wings. The grouping and the tilt follow ESA; where each
          camera sits on the bench is schematic.
  ariel : an off axis telescope with an elliptical primary mirror of 1.1 by 0.7 metres, set behind a baffle that is
          longer on its lower side, the secondary mirror on a tripod above the opening, the instrument bay behind the
          primary on the payload bench, three stacked V groove shields that open towards their outer edges and keep
          the payload cold, the struts that carry the payload, and the service module with the solar panel facing
          down towards the Sun.

The look: a black sky with a sparse field of point stars, a hard key from one side standing in for sunlight and a
faint cool fill; matte white and gold multilayer insulation with a crinkle in the normals, dark solar cells with a
faint grid, aluminium. No text, logos or flags.

Usage: uv run --python 3.11 --with bpy==4.2.0 python blender_missions.py VARIANT OUT.png [samples] [W] [H]
Set CYCLES_DEVICE=GPU to render on the graphics card, and BORDER=x0,x1,y0,y1 to render one part of the frame.
"""
import math, os, random, sys
import bpy, bmesh
from mathutils import Matrix, Vector

variant, out = sys.argv[1], sys.argv[2]
samples = int(sys.argv[3]) if len(sys.argv) > 3 else 128
W, H = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (2400, 1350)
random.seed(11)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
if os.environ.get('CYCLES_DEVICE') == 'GPU':
    pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'CUDA'; pr.get_devices()
    for dv in pr.devices: dv.use = dv.type == 'CUDA'
    sc.cycles.device = 'GPU'; sc.cycles.denoising_use_gpu = True
sc.render.resolution_x, sc.render.resolution_y = W, H; sc.render.resolution_percentage = 100
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
sc.cycles.max_bounces = 6; sc.cycles.glossy_bounces = 4; sc.cycles.diffuse_bounces = 2

# ------------------------------------------------------------------------------------------------- materials
def material(name, base, metal=0.0, rough=0.4, crinkle=0.0, scale=14.0, coat=0.0):
    # Principled surface; crinkle > 0 adds the creased foil look of multilayer insulation in the normals and roughness
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes.new; L = nt.links.new
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*base, 1); b.inputs['Metallic'].default_value = metal; b.inputs['Roughness'].default_value = rough
    b.inputs['Coat Weight'].default_value = coat
    if crinkle:
        tc = N('ShaderNodeTexCoord')
        nz = N('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 10; nz.inputs['Roughness'].default_value = 0.62
        nz.inputs['Distortion'].default_value = 0.6
        vo = N('ShaderNodeTexVoronoi'); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs['Scale'].default_value = scale * 0.35
        mx = N('ShaderNodeMath'); mx.operation = 'MULTIPLY_ADD'; mx.inputs[1].default_value = 0.5
        L(tc.outputs['Object'], nz.inputs['Vector']); L(nz.outputs['Color'], vo.inputs['Vector'])
        L(vo.outputs['Distance'], mx.inputs[0]); L(nz.outputs['Fac'], mx.inputs[2])
        bp = N('ShaderNodeBump'); bp.inputs['Strength'].default_value = crinkle; bp.inputs['Distance'].default_value = 0.02
        L(mx.outputs[0], bp.inputs['Height']); L(bp.outputs['Normal'], b.inputs['Normal'])
        mr = N('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = rough * 0.55; mr.inputs['To Max'].default_value = rough * 1.5
        L(nz.outputs['Fac'], mr.inputs['Value']); L(mr.outputs['Result'], b.inputs['Roughness'])
    return m

def cell_material(name, cell=(0.155, 0.075)):
    # dark solar cells in a faint silver grid; the grid is a brick texture in the panel's own plane
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes.new; L = nt.links.new
    b = nt.nodes['Principled BSDF']; b.inputs['Metallic'].default_value = 0.35; b.inputs['Roughness'].default_value = 0.16
    b.inputs['Coat Weight'].default_value = 0.6; b.inputs['Coat Roughness'].default_value = 0.05
    tc = N('ShaderNodeTexCoord'); mp = N('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1 / cell[0], 1 / cell[0], 1)
    br = N('ShaderNodeTexBrick'); br.offset = 0.0; br.inputs['Scale'].default_value = 1.0
    br.inputs['Brick Width'].default_value = 1.0; br.inputs['Row Height'].default_value = cell[1] / cell[0]
    br.inputs['Mortar Size'].default_value = 0.035; br.inputs['Mortar Smooth'].default_value = 0.2
    br.inputs['Color1'].default_value = (0.018, 0.026, 0.06, 1); br.inputs['Color2'].default_value = (0.022, 0.03, 0.068, 1)
    br.inputs['Mortar'].default_value = (0.2, 0.21, 0.23, 1)
    L(tc.outputs['Object'], mp.inputs['Vector']); L(mp.outputs['Vector'], br.inputs['Vector']); L(br.outputs['Color'], b.inputs['Base Color'])
    return m

WHITE = material('mli_white', (0.80, 0.80, 0.78), 0.0, 0.55, crinkle=0.35, scale=9.0)
GOLD = material('mli_gold', (0.90, 0.60, 0.22), 1.0, 0.26, crinkle=0.45, scale=7.0)
BLACKMLI = material('mli_black', (0.03, 0.03, 0.035), 0.1, 0.5, crinkle=0.4, scale=9.0)
ALU = material('alu', (0.62, 0.64, 0.67), 1.0, 0.32)
POLISH = material('polished', (0.86, 0.87, 0.89), 1.0, 0.12)
DARK = material('dark', (0.025, 0.026, 0.03), 0.3, 0.45)
CFRP = material('cfrp', (0.09, 0.093, 0.1), 0.3, 0.36)
LENS = material('lens', (0.0, 0.0, 0.0), 0.0, 0.03, coat=1.0)
MIRROR = material('mirror', (0.93, 0.94, 0.96), 1.0, 0.04)
CELLS = cell_material('cells')
BAFFLE = material('baffle', (0.32, 0.33, 0.35), 0.7, 0.45, crinkle=0.08, scale=5.0)

# ------------------------------------------------------------------------------------------------- geometry
def frame(loc, zdir, up=(0, 0, 1)):
    # a matrix with its z axis along zdir, placed at loc
    q = Vector(zdir).normalized().to_track_quat('Z', 'Y' if abs(Vector(zdir).normalized().z) < 0.99 else 'X')
    return Matrix.Translation(Vector(loc)) @ q.to_matrix().to_4x4()

class Batch:
    # many parts in one mesh per material; quads of cylinders are smooth, caps and boxes flat
    def __init__(self): self.d = {}
    def bm(self, mat): return self.d.setdefault(mat.name, (bmesh.new(), mat))[0]
    def cyl(self, mat, M, r1, r2, h, segs=40, caps=True):
        bmesh.ops.create_cone(self.bm(mat), cap_ends=caps, cap_tris=False, segments=segs, radius1=r1, radius2=r2, depth=h,
                              matrix=M @ Matrix.Translation((0, 0, h / 2)))
    def box(self, mat, M, sx, sy, sz):
        bmesh.ops.create_cube(self.bm(mat), size=1.0, matrix=M @ Matrix.Diagonal((sx, sy, sz, 1)))
    def strut(self, mat, a, b, r, segs=10):
        a, b = Vector(a), Vector(b); self.cyl(mat, frame(a, b - a), r, r, (b - a).length, segs)
    def prism(self, mat, pts, z0, z1, M=Matrix()):
        # a flat polygon pts (x, y) extruded from z0 to z1
        bm = self.bm(mat)
        lo = [bm.verts.new(M @ Vector((x, y, z0))) for x, y in pts]; hi = [bm.verts.new(M @ Vector((x, y, z1))) for x, y in pts]
        bm.faces.new(lo[::-1]); bm.faces.new(hi)
        for i in range(len(pts)): bm.faces.new((lo[i], lo[(i + 1) % len(pts)], hi[(i + 1) % len(pts)], hi[i]))
    def solid(self, mat, bottom, top):
        # two matching vertex loops (lists of 3D points) joined into a closed solid
        bm = self.bm(mat); lo = [bm.verts.new(p) for p in bottom]; hi = [bm.verts.new(p) for p in top]; n = len(lo)
        bm.faces.new(lo[::-1]); bm.faces.new(hi)
        for i in range(n): bm.faces.new((lo[i], lo[(i + 1) % n], hi[(i + 1) % n], hi[i]))
    def build(self, parent):
        for name, (bm, mat) in self.d.items():
            for f in bm.faces: f.smooth = len(f.verts) == 4 and mat.name not in ('cfrp',)
            me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
            ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); ob.data.materials.append(mat); ob.parent = parent
        self.d = {}

def ngon(r, n, rot=0.0): return [(r * math.cos(rot + 2 * math.pi * i / n), r * math.sin(rot + 2 * math.pi * i / n)) for i in range(n)]

def cell_panel(parent, M, w, h, name='cells'):
    # a flat plane of cells in its own frame so the grid follows the panel
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    vs = [bm.verts.new((x, y, 0)) for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]; bm.faces.new(vs); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); ob.data.materials.append(CELLS)
    ob.matrix_world = M; ob.parent = parent; return ob

def poly_cell_panel(parent, M, pts, name='cells'):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); vs = [bm.verts.new((x, y, 0)) for x, y in pts]; bm.faces.new(vs); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); ob.data.materials.append(CELLS)
    ob.matrix_world = M; ob.parent = parent; return ob

root = bpy.data.objects.new('craft', None); bpy.context.collection.objects.link(root)
B = Batch()

# ------------------------------------------------------------------------------------------------- stage
def stars(cam_loc, look, n=320, R=400.0, px=None):
    # point stars on a far sphere, seen by the camera only; brightness from a steep power law, a few warmer or bluer
    bm = bmesh.new(); cols = []
    fwd = (Vector(look) - Vector(cam_loc)).normalized()
    for _ in range(n):
        while True:
            d = Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1))).normalized()
            if d.dot(fwd) > 0.72: break
        p = Vector(cam_loc) + R * d
        b = min(1.0, 0.05 / (random.random() ** 1.6 + 0.05)); r = px * (0.7 + 1.1 * b)
        t = random.random(); c = (1.0, 0.86, 0.7) if t < 0.18 else (0.75, 0.85, 1.0) if t < 0.4 else (1.0, 0.97, 0.93)
        u = d.orthogonal().normalized(); v = d.cross(u)
        vs = [bm.verts.new(p + r * (math.cos(2 * math.pi * k / 6) * u + math.sin(2 * math.pi * k / 6) * v)) for k in range(6)]
        bm.faces.new(vs); cols += [tuple(x * (0.06 + 1.8 * b) for x in c)] * 6
    me = bpy.data.meshes.new('stars'); bm.to_mesh(me); bm.free()
    at = me.color_attributes.new('col', 'FLOAT_COLOR', 'POINT')
    for i, c in enumerate(cols): at.data[i].color = (*c, 1)
    m = bpy.data.materials.new('stars'); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    a = nt.nodes.new('ShaderNodeAttribute'); a.attribute_name = 'col'; e = nt.nodes.new('ShaderNodeEmission')
    nt.links.new(a.outputs['Color'], e.inputs['Color']); nt.links.new(e.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
    ob = bpy.data.objects.new('stars', me); bpy.context.collection.objects.link(ob); ob.data.materials.append(m)
    for attr in ('visible_diffuse', 'visible_glossy', 'visible_transmission', 'visible_volume_scatter', 'visible_shadow'): setattr(ob, attr, False)

def sun(direction, strength, color=(1.0, 0.95, 0.88)):
    ld = bpy.data.lights.new('sun', 'SUN'); ld.energy = strength; ld.color = color; ld.angle = math.radians(0.53)
    ob = bpy.data.objects.new('sun', ld); bpy.context.collection.objects.link(ob)
    ob.rotation_euler = (-Vector(direction)).to_track_quat('-Z', 'Y').to_euler()

def area(loc, target, energy, size, color=(0.6, 0.72, 1.0)):
    ld = bpy.data.lights.new('fill', 'AREA'); ld.energy = energy; ld.color = color; ld.size = size
    ob = bpy.data.objects.new('fill', ld); bpy.context.collection.objects.link(ob); ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    ob.visible_camera = False

def camera(loc, look, lens, shift_x=0.0, shift_y=0.0):
    cd = bpy.data.cameras.new('cam'); cd.lens = lens; cd.shift_x = shift_x; cd.shift_y = shift_y; cd.clip_end = 1000
    cam = bpy.data.objects.new('cam', cd); bpy.context.collection.objects.link(cam); sc.camera = cam
    cam.location = loc; cam.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    # star size: about one pixel and a half at this lens and width
    return 2 * math.tan(math.atan(18.0 / lens)) / W

w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.0015, 0.0017, 0.0022, 1)

# ================================================================================================== PLATO
if variant == 'plato':
    TILT = math.radians(9.2)
    # service module: hexagonal prism in gold insulation, aluminium rims
    B.prism(GOLD, ngon(1.72, 6, math.pi / 6), 0.0, 1.1)
    for z in (-0.03, 1.08):
        B.prism(ALU, ngon(1.75, 6, math.pi / 6), z, z + 0.05)
    # three bipods to the bench
    for k in range(3):
        a = math.radians(90 + 120 * k)
        for s in (-1, 1):
            foot = Vector((1.35 * math.cos(a + s * 0.28), 1.35 * math.sin(a + s * 0.28), 1.12)); head = Vector((1.5 * math.cos(a), 1.5 * math.sin(a), 1.46))
            B.strut(WHITE, foot, head, 0.035)
    # optical bench: a hexagonal plate, insulated sides, a dark top
    B.prism(WHITE, ngon(2.1, 6), 1.44, 1.58); B.prism(CFRP, ngon(2.12, 6), 1.58, 1.62)
    B.prism(ALU, ngon(2.14, 6), 1.43, 1.46)
    cam_axes = []
    def camera_unit(M):
        # a PLATO camera: mount ring, insulated barrel with a band, flared sunshade lip, dark entrance lens
        B.cyl(ALU, M, 0.16, 0.16, 0.07)
        for k in range(3):
            a = 2 * math.pi * k / 3 + 0.4
            B.box(ALU, M @ Matrix.Translation((0.17 * math.cos(a), 0.17 * math.sin(a), 0.05)) @ Matrix.Rotation(a, 4, 'Z'), 0.06, 0.04, 0.1)
        B.cyl(WHITE, M @ Matrix.Translation((0, 0, 0.07)), 0.17, 0.17, 0.4, 48)
        B.cyl(ALU, M @ Matrix.Translation((0, 0, 0.26)), 0.176, 0.176, 0.03, 48)
        B.cyl(ALU, M @ Matrix.Translation((0, 0, 0.47)), 0.172, 0.186, 0.05, 48)
        B.cyl(WHITE, M @ Matrix.Translation((0, 0, 0.52)), 0.186, 0.21, 0.12, 48, caps=False)
        B.cyl(DARK, M @ Matrix.Translation((0, 0, 0.52)), 0.18, 0.205, 0.115, 48, caps=False)
        B.cyl(LENS, M @ Matrix.Translation((0, 0, 0.53)), 0.13, 0.13, 0.01, 40)
        B.cyl(ALU, M @ Matrix.Translation((0, 0, 0.528)), 0.15, 0.15, 0.008, 40)
    for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
        u = Vector((sx, sy, 0)).normalized(); n = Vector((math.sin(TILT) * u.x, math.sin(TILT) * u.y, math.cos(TILT)))
        c = Vector((sx * 0.76, sy * 0.85, 0))
        def ztop(p): return 1.72 - math.tan(TILT) * ((p - c).dot(u))
        # the group's mounting face: a wedge whose top is tilted 9.2 degrees towards its quadrant
        fw, fh = 0.5, 0.73
        foot = [c + Vector((x, y, 0)) for x, y in ((-fw, -fh), (fw, -fh), (fw, fh), (-fw, fh))]
        B.solid(ALU, [Vector((p.x, p.y, 1.62)) for p in foot], [Vector((p.x, p.y, ztop(p))) for p in foot])
        for dx in (-0.235, 0.235):
            for dy in (-0.47, 0.0, 0.47):
                p = c + Vector((dx, dy, 0)); p.z = ztop(p); camera_unit(frame(p, n)); cam_axes.append(n)
    for sy in (-0.37, 0.37):   # the two fast cameras, along the common axis
        B.cyl(ALU, frame((0, sy, 1.62), (0, 0, 1)), 0.2, 0.2, 0.08, 6)
        camera_unit(frame((0, sy, 1.70), (0, 0, 1)))
    assert len(cam_axes) == 24
    # sunshield: a tall flat panel on the sunward side, insulated on the inside, cells outside, two side wings
    X0, Y0, Z0, Z1 = 2.12, 2.15, -0.25, 2.95
    B.box(WHITE, Matrix.Translation((X0, 0, (Z0 + Z1) / 2)), 0.06, 2 * Y0, Z1 - Z0)
    B.box(ALU, Matrix.Translation((X0 + 0.01, 0, Z1)), 0.09, 2 * Y0 + 0.04, 0.05)
    B.box(ALU, Matrix.Translation((X0 + 0.01, 0, Z0)), 0.09, 2 * Y0 + 0.04, 0.05)
    rot = Matrix.Rotation(math.pi / 2, 4, 'Y')
    cell_panel(root, Matrix.Translation((X0 + 0.032, 0, (Z0 + Z1) / 2)) @ rot, Z1 - Z0 - 0.12, 2 * Y0 - 0.12)
    WING = math.radians(15); ww, wz0, wz1 = 1.05, 0.15, 2.55
    for s in (-1, 1):
        d = Vector((-math.sin(WING), s * math.cos(WING), 0))           # along the wing, bending back towards the payload
        hinge = Vector((X0, s * (Y0 + 0.04), 0)); mid = hinge + d * (ww / 2 + 0.03)
        Mw = Matrix.Translation((mid.x, mid.y, (wz0 + wz1) / 2)) @ Matrix.Rotation(s * -WING, 4, 'Z')
        B.box(WHITE, Mw, 0.05, ww, wz1 - wz0)
        cell_panel(root, Mw @ Matrix.Translation((0.027, 0, 0)) @ rot, wz1 - wz0 - 0.1, ww - 0.1)
        for z in (0.6, 2.1): B.strut(ALU, hinge + Vector((0, 0, z)), mid + d * 0.4 + Vector((0, 0, z)), 0.02)
    # a few blocks on the service module: thrusters and a star tracker head, schematic
    for k in range(6):
        a = math.radians(60 * k)
        B.box(ALU, Matrix.Translation((1.5 * math.cos(a), 1.5 * math.sin(a), -0.08)), 0.16, 0.16, 0.12)
    B.cyl(DARK, frame((-1.2, -0.9, 1.1), (-0.5, -0.4, 0.8)), 0.09, 0.12, 0.22, 24)
    B.build(root)
    root.rotation_euler = (math.radians(32), 0, math.radians(-8))
    cam_loc, look = Vector((5.4, -23.0, 2.0)), Vector((0.3, -0.4, 1.4))
    px = camera(cam_loc, look, 60, shift_x=-0.16, shift_y=-0.05)
    sun((-0.45, 0.8, -0.45), 8.0)                        # sunlight from the right, in front of the sunshield's plane
    area((-10, -6, 6), (0, 0, 1.5), 1500, 10)             # faint cool fill from the left
    area((-3, 12, 5), (0, 0, 1.5), 1200, 8, (0.7, 0.8, 1.0))   # cool rim from behind
    stars(cam_loc, look, px=px * 400.0)

# ================================================================================================== Ariel
elif variant == 'ariel':
    # solar panel facing down (the Sun is below), service module above it
    B.prism(ALU, ngon(1.32, 8, math.pi / 8), -0.06, 0.0)
    poly_cell_panel(root, Matrix.Translation((0, 0, -0.062)) @ Matrix.Rotation(math.pi, 4, 'X'), ngon(1.28, 8, math.pi / 8))
    B.prism(GOLD, ngon(1.02, 8, math.pi / 8), 0.0, 0.86)
    B.prism(ALU, ngon(1.05, 8, math.pi / 8), 0.84, 0.89)
    # a white radiator face on the service module
    B.box(WHITE, Matrix.Translation((0, -0.955, 0.43)), 0.62, 0.02, 0.62)
    # struts from the service module through the shields to the payload bench
    for k in range(6):
        a = math.radians(30 + 60 * k)
        foot = Vector((0.82 * math.cos(a), 0.82 * math.sin(a), 0.89)); head = Vector((0.55 * math.cos(a + 0.5), 0.55 * math.sin(a + 0.5), 1.92))
        B.strut(WHITE, foot, head, 0.022)
    # three V groove shields: two flat halves each, opening more steeply towards the outer edge from bottom to top
    hx, hy = 1.65, 1.3
    for i, (z, ang) in enumerate(((1.08, 2.0), (1.30, 6.0), (1.52, 10.0))):
        t = math.tan(math.radians(ang)); mat = POLISH if i < 2 else ALU
        for s in (-1, 1):
            bot = [Vector((0, -hy, z)), Vector((s * hx, -hy, z + t * hx)), Vector((s * hx, hy, z + t * hx)), Vector((0, hy, z))]
            if s < 0: bot = bot[::-1]
            B.solid(mat, bot, [p + Vector((0, 0, 0.022)) for p in bot])
            B.strut(ALU, Vector((s * hx, -hy, z + t * hx + 0.011)), Vector((s * hx, hy, z + t * hx + 0.011)), 0.016, 8)
        B.strut(ALU, Vector((-hx, -hy, z + t * hx + 0.011)), Vector((0, -hy, z + 0.011)), 0.014, 8)
        B.strut(ALU, Vector((0, -hy, z + 0.011)), Vector((hx, -hy, z + t * hx + 0.011)), 0.014, 8)
        B.strut(ALU, Vector((-hx, hy, z + t * hx + 0.011)), Vector((0, hy, z + 0.011)), 0.014, 8)
        B.strut(ALU, Vector((0, hy, z + 0.011)), Vector((hx, hy, z + t * hx + 0.011)), 0.014, 8)
    # payload bench and the instrument bay behind the primary
    B.box(CFRP, Matrix.Translation((0, -0.05, 1.98)), 1.9, 1.7, 0.1)
    B.box(ALU, Matrix.Translation((0, -0.05, 1.925)), 1.94, 1.74, 0.02)
    B.box(BLACKMLI, Matrix.Translation((0, -0.62, 2.28)), 1.05, 0.5, 0.5)
    B.box(GOLD, Matrix.Translation((0.32, -0.62, 2.56)), 0.32, 0.4, 0.06)
    B.box(ALU, Matrix.Translation((-0.3, -0.62, 2.555)), 0.36, 0.42, 0.05)
    # telescope: line of sight along +y; the primary is tilted to send light up to the secondary
    C1 = Vector((0, -0.18, 2.62)); C2 = Vector((0, 0.62, 3.38))
    to2 = (C2 - C1).normalized(); n1 = (Vector((0, 1, 0)) + to2).normalized()
    M1 = frame(C1, n1)
    # elliptical dish, 1.1 by 0.7 m, with a shallow sag, mirror face and a ribbed back
    bm = B.bm(MIRROR); rings, seg = 10, 72; grid = []
    for i in range(rings + 1):
        rr = i / rings; row = []
        for j in range(seg):
            ph = 2 * math.pi * j / seg; x, y = 0.55 * rr * math.cos(ph), 0.35 * rr * math.sin(ph)
            row.append(bm.verts.new(M1 @ Vector((x, y, 0.06 * rr * rr))))
        grid.append(row)
    for i in range(1, rings):
        for j in range(seg):
            bm.faces.new((grid[i][j], grid[i][(j + 1) % seg], grid[i + 1][(j + 1) % seg], grid[i + 1][j]))
    ctr = bm.verts.new(M1 @ Vector((0, 0, 0)))
    for j in range(seg): bm.faces.new((ctr, grid[1][j], grid[1][(j + 1) % seg]))
    B.solid(ALU, [M1 @ Vector((0.57 * math.cos(2 * math.pi * j / seg), 0.37 * math.sin(2 * math.pi * j / seg), -0.12)) for j in range(seg)],
            [M1 @ Vector((0.57 * math.cos(2 * math.pi * j / seg), 0.37 * math.sin(2 * math.pi * j / seg), 0.055)) for j in range(seg)])
    # mirror mounts to the bench
    for x in (-0.4, 0.0, 0.4):
        B.strut(ALU, Vector((x, -0.35, 2.03)), M1 @ Vector((x * 0.9, -0.2, -0.12)), 0.03)
    # baffle: an elliptical shroud around the beam in front of the primary, longer on the lower (sunward) side, open at the top front
    seg = 96; ax, az = 0.68, 0.6; Cb = Vector((0, 0, 2.66))
    inner, outer = [], []
    for j in range(seg):
        ph = 2 * math.pi * j / seg; x, z = ax * math.cos(ph), az * math.sin(ph)
        y0 = -0.42 + 0.22 * (z / az)                         # rear edge follows the mirror tilt
        y1 = 0.95 - 0.5 * (0.5 + 0.5 * z / az) ** 1.4        # front edge: long below, shorter above
        outer.append((x, z, y0, y1))
    bo = B.bm(BAFFLE); bi = B.bm(DARK)
    A = [bo.verts.new((x, y0, Cb.z + z)) for x, z, y0, y1 in outer]; Bv = [bo.verts.new((x, y1, Cb.z + z)) for x, z, y0, y1 in outer]
    Ai = [bi.verts.new((x * 0.97, y0, Cb.z + z * 0.97)) for x, z, y0, y1 in outer]; Bi = [bi.verts.new((x * 0.97, y1, Cb.z + z * 0.97)) for x, z, y0, y1 in outer]
    for j in range(seg):
        k = (j + 1) % seg
        bo.faces.new((A[j], A[k], Bv[k], Bv[j])); bi.faces.new((Ai[k], Ai[j], Bi[j], Bi[k]))
    # rim of the opening in aluminium, a thin tube along the front edge
    for j in range(seg):
        k = (j + 1) % seg; x0, z0, _, y0 = outer[j]; x1, z1, _, y1 = outer[k]
        B.strut(ALU, (x0 * 1.005, y0, Cb.z + z0 * 1.005), (x1 * 1.005, y1, Cb.z + z1 * 1.005), 0.012, 6)
    # secondary mirror on a tripod from the bench, above the opening
    M2 = frame(C2, (C1 - C2).normalized())
    B.cyl(ALU, M2 @ Matrix.Translation((0, 0, -0.06)), 0.12, 0.12, 0.06, 32); B.cyl(MIRROR, M2, 0.1, 0.1, 0.012, 32)
    for a in ((-0.45, -0.32, 3.18), (0.45, -0.32, 3.18), (0.0, -0.6, 2.53)):
        B.strut(ALU, a, C2 + Vector((0, -0.04, 0.04)), 0.018)
    B.build(root)
    root.rotation_euler = (0, 0, math.radians(-20))
    cam_loc, look = Vector((10.2, 9.6, 2.15)), Vector((0.0, 0.1, 1.75))
    px = camera(cam_loc, look, 55, shift_x=-0.16, shift_y=0.0)
    sun((0.29, -0.82, 0.3), 7.0)                        # light from the right and a little from below, where the Sun is
    area((-6, 9, 8), (0, 0, 1.8), 700, 10)
    area((-7, -9, 6), (0, 0, 1.8), 1100, 8, (0.7, 0.8, 1.0))
    stars(cam_loc, look, px=px * 400.0)
else:
    raise SystemExit('variant: plato or ariel')

if os.environ.get('BORDER'):   # render one part of the frame, as x0,x1,y0,y1 in fractions, when memory is short
    x0, x1, y0, y1 = (float(v) for v in os.environ['BORDER'].split(','))
    sc.render.use_border = True; sc.render.use_crop_to_border = True
    sc.render.border_min_x, sc.render.border_max_x, sc.render.border_min_y, sc.render.border_max_y = x0, x1, y0, y1
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print('wrote', out)
