"""Gaia in Blender (Cycles). Proportions after ESA's descriptions: deployable sunshield about 10 m across in 12 panels,
solar cells on its sun-facing side, a hexagonal service module in gold multi-layer insulation, the payload under a
cylindrical dark thermal tent with the two telescope apertures 106.5 degrees apart, and the phased-array antenna.
Schematic, not an engineering model. Usage: uv run --python 3.11 --with bpy==4.2.0 python blender_gaia.py OUT.png [angle_deg] [samples]"""
import math, sys
import bpy, bmesh
from mathutils import Vector

out = sys.argv[1]; ANIM = len(sys.argv) > 2 and sys.argv[2].startswith('anim')
NFR = int(sys.argv[2][4:]) if ANIM else 0
ang = 0.0 if ANIM else math.radians(float(sys.argv[2]) if len(sys.argv) > 2 else 0.0)
samples = int(sys.argv[3]) if len(sys.argv) > 3 else 128
W, H = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (1500, 1000)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = W, H; sc.render.film_transparent = True
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.cycles.device = 'CPU'

def mat(name, base, metal=0.0, rough=0.4, emit=None, estr=0.0, noise_bump=0.0, spec=0.5, nscale=9.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*base, 1); b.inputs['Metallic'].default_value = metal; b.inputs['Roughness'].default_value = rough
    if emit is not None:
        b.inputs['Emission Color'].default_value = (*emit, 1); b.inputs['Emission Strength'].default_value = estr
    if noise_bump:
        tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = nscale; nz.inputs['Detail'].default_value = 8
        bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = noise_bump
        nt.links.new(tc.outputs['Object'], nz.inputs['Vector']); nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
        # crinkle also varies roughness
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = rough * 0.5; mr.inputs['To Max'].default_value = rough * 1.6
        nt.links.new(nz.outputs['Fac'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], b.inputs['Roughness'])
    return m

GOLD = mat('gold', (0.92, 0.62, 0.22), metal=1.0, rough=0.24, noise_bump=0.22, nscale=6.0)
MLI = mat('mli', (0.74, 0.76, 0.8), metal=0.8, rough=0.34, noise_bump=0.06, nscale=3.0)
TENT = mat('tent', (0.03, 0.032, 0.038), metal=0.05, rough=0.7, noise_bump=0.03, nscale=2.0)
FRAME = mat('frame', (0.55, 0.57, 0.6), metal=0.9, rough=0.35)
CELL = mat('cell', (0.03, 0.06, 0.16), metal=0.3, rough=0.12)
HOLE = mat('hole', (0.0, 0.0, 0.0), rough=1.0)
RIMG = mat('rim', (0.85, 0.6, 0.25), metal=1.0, rough=0.25)

def obj_from_bm(bm, name, material):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); ob.data.materials.append(material)
    for p in ob.data.polygons: p.use_smooth = False
    return ob

root = bpy.data.objects.new('gaia', None); bpy.context.collection.objects.link(root)
parts = []
# ---- sunshield: 12 panels on a shallow cone, a gap between panels, frames along the edges
r0, r1, k = 1.95, 5.1, 12
for i in range(k):
    a0, a1 = 2 * math.pi * i / k + 0.012, 2 * math.pi * (i + 1) / k - 0.012
    z = lambda r: -0.32 * (r - r0) / (r1 - r0)
    bm = bmesh.new()
    vs = [bm.verts.new((r * math.cos(a), r * math.sin(a), z(r) + dz)) for dz in (0.0, -0.04) for (r, a) in ((r0, a0), (r1, a0), (r1, a1), (r0, a1))]
    bm.faces.new(vs[:4]); bm.faces.new(vs[4:][::-1])
    for j in range(4): bm.faces.new((vs[j], vs[(j + 1) % 4], vs[4 + (j + 1) % 4], vs[4 + j])[::-1])
    parts.append(obj_from_bm(bm, f'panel{i}', MLI))
    # underside solar cells: a slightly lower copy of the inner two thirds
    bm = bmesh.new(); rr = r0 + (r1 - r0) * 0.7
    vs = [bm.verts.new((r * math.cos(a), r * math.sin(a), z(r) - 0.045)) for (r, a) in ((r0, a0), (rr, a0), (rr, a1), (r0, a1))]
    bm.faces.new(vs[::-1]); parts.append(obj_from_bm(bm, f'cells{i}', CELL))
    # frame: radial strut at the panel edge and a rim segment
    for (ra, aa, rb, ab, w) in ((r0, a0 - 0.012, r1, a0 - 0.012, 0.045), (r1, a0, r1, a1, 0.05)):
        bm = bmesh.new()
        p0 = Vector((ra * math.cos(aa), ra * math.sin(aa), z(ra) + 0.02)); p1 = Vector((rb * math.cos(ab), rb * math.sin(ab), z(rb) + 0.02))
        d = (p1 - p0).normalized(); n = d.cross(Vector((0, 0, 1))).normalized() * w
        up = Vector((0, 0, w))
        q = [p0 + n, p1 + n, p1 - n, p0 - n]; qs = [bm.verts.new(v) for v in q] + [bm.verts.new(v + up) for v in q]
        bm.faces.new(qs[4:]); bm.faces.new(qs[:4][::-1])
        for j in range(4): bm.faces.new((qs[j], qs[(j + 1) % 4], qs[4 + (j + 1) % 4], qs[4 + j]))
        parts.append(obj_from_bm(bm, 'strut', FRAME))
    # one cross batten per panel
    rm = r0 + (r1 - r0) * 0.55
    bm = bmesh.new(); pa = Vector((rm * math.cos(a0), rm * math.sin(a0), z(rm) + 0.02)); pb = Vector((rm * math.cos(a1), rm * math.sin(a1), z(rm) + 0.02))
    d = (pb - pa).normalized(); n = Vector((d.y, -d.x, 0)) * 0.03; up = Vector((0, 0, 0.03))
    q = [pa + n, pb + n, pb - n, pa - n]; qs = [bm.verts.new(v) for v in q] + [bm.verts.new(v + up) for v in q]
    bm.faces.new(qs[4:]); [bm.faces.new((qs[j], qs[(j + 1) % 4], qs[4 + (j + 1) % 4], qs[4 + j])) for j in range(4)]
    parts.append(obj_from_bm(bm, 'batten', FRAME))
# ---- service module: hexagonal prism in gold MLI, with a frame at top and bottom
bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=1.95, depth=1.1, location=(0, 0, 0.45)); sm = bpy.context.object; sm.rotation_euler[2] = math.pi / 6; sm.data.materials.append(GOLD); parts.append(sm)
for zz in (-0.08, 0.98):
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=1.99, depth=0.06, location=(0, 0, zz)); f = bpy.context.object; f.rotation_euler[2] = math.pi / 6; f.data.materials.append(FRAME); parts.append(f)
# ---- payload thermal tent: dark pleated drum with a domed roof
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=1.78, depth=2.15, location=(0, 0, 2.1)); tent = bpy.context.object; tent.data.materials.append(TENT); parts.append(tent)
bm = bmesh.new(); bm.from_mesh(tent.data)
for v in bm.verts:
    a = math.atan2(v.co.y, v.co.x); s = 1 + 0.004 * math.cos(24 * a); v.co.x *= s; v.co.y *= s
bm.to_mesh(tent.data); bm.free()
for pl in tent.data.polygons: pl.use_smooth = True
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=16, radius=1.78, location=(0, 0, 3.17)); dome = bpy.context.object; dome.scale[2] = 0.12; dome.data.materials.append(TENT); parts.append(dome)
bpy.ops.mesh.primitive_torus_add(major_radius=1.78, minor_radius=0.035, location=(0, 0, 3.17)); t = bpy.context.object; t.data.materials.append(FRAME); parts.append(t)
# apertures: dark recess with a gold rim, facing outward
for ac in (math.radians(-70), math.radians(-70 + 106.5)):
    for (w, h, m, off) in ((0.95, 0.75, RIMG, 0.02), (0.82, 0.62, HOLE, 0.035)):
        bpy.ops.mesh.primitive_plane_add(size=1, location=((1.78 + off) * math.cos(ac), (1.78 + off) * math.sin(ac), 2.35))
        p = bpy.context.object; p.scale = (w, h, 1); p.rotation_euler = (math.pi / 2, 0, ac + math.pi / 2); p.data.materials.append(m); parts.append(p)
# phased-array antenna under the service module: a ring of small plates
for j in range(12):
    a = 2 * math.pi * j / 12
    bpy.ops.mesh.primitive_cube_add(size=1, location=(1.2 * math.cos(a), 1.2 * math.sin(a), -0.3)); c = bpy.context.object; c.scale = (0.35, 0.12, 0.08); c.rotation_euler[2] = a; c.data.materials.append(FRAME); parts.append(c)
for p in parts: p.parent = root
root.rotation_euler = (math.radians(-6), 0, ang)

# ---- lights: a warm key from the lower left (the sun's side), a cool rim from behind, a soft fill
def light(kind, loc, energy, color, size=1.0, rot=None):
    ld = bpy.data.lights.new(kind + str(loc), kind); ld.energy = energy; ld.color = color
    if kind == 'AREA': ld.size = size
    if kind == 'SUN': ld.angle = math.radians(1.0)
    ob = bpy.data.objects.new(ld.name, ld); bpy.context.collection.objects.link(ob); ob.location = loc
    tgt = Vector((0, 0, 1.0)); ob.rotation_euler = (tgt - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return ob
light('SUN', (14, -10, 4), 4.5, (1.0, 0.92, 0.82))
light('AREA', (-9, 9, 6), 1600, (0.62, 0.74, 1.0), size=6)
light('AREA', (6, -14, -2), 500, (1.0, 0.85, 0.7), size=8)
world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.012, 0.013, 0.018, 1); world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.6

cam_d = bpy.data.cameras.new('cam'); cam_d.lens = 55
cam = bpy.data.objects.new('cam', cam_d); bpy.context.collection.objects.link(cam); sc.camera = cam
cam.location = (14.5, -11.5, 8.2); cam.rotation_euler = (Vector((0, 0, 0.9)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
if ANIM:
    sc.frame_start, sc.frame_end = 1, NFR; sc.render.fps = 30
    root.rotation_euler[2] = 0.0; root.keyframe_insert('rotation_euler', index=2, frame=1)
    root.rotation_euler[2] = 2 * math.pi; root.keyframe_insert('rotation_euler', index=2, frame=NFR + 1)
    for fc in root.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = out + '/f_'
    bpy.ops.render.render(animation=True)
else:
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
print('wrote', out)
