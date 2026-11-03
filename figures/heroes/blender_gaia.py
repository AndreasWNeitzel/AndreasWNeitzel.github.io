"""Gaia in Blender (Cycles): the turntable of the shared model in gaia_model.py, schematic, not an engineering model.
Usage: uv run --python 3.11 --with bpy==4.2.0 python blender_gaia.py OUT.png [angle_deg] [samples] [W H]
GAIA_CHECK=1 renders nothing and prints the craft's margins in the frame at 72 angles."""
import math, sys, os
import bpy
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
if os.environ.get('CYCLES_DEVICE') == 'GPU':  # the CPU path in this wheel uses two or three cores; the GPU is the same tracer
    pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'CUDA'; pr.get_devices()
    for dv in pr.devices: dv.use = dv.type == 'CUDA'
    sc.cycles.device = 'GPU'; sc.cycles.denoising_use_gpu = True

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gaia_model import build_gaia
root = bpy.data.objects.new('gaia', None); bpy.context.collection.objects.link(root); build_gaia(root, soft_foil=True)
root.rotation_mode = 'ZXY'; root.rotation_euler = (math.radians(-6), 0, ang)   # spin about its own axis, then the fixed lean

# ---- lights: a warm key from the lower left, a cool rim from behind, a soft fill
def light(kind, loc, energy, color, size=1.0):
    ld = bpy.data.lights.new(kind + str(loc), kind); ld.energy = energy; ld.color = color
    if kind == 'AREA': ld.size = size
    if kind == 'SUN': ld.angle = math.radians(1.0)
    ob = bpy.data.objects.new(ld.name, ld); bpy.context.collection.objects.link(ob); ob.location = loc
    tgt = Vector((0, 0, 1.0)); ob.rotation_euler = (tgt - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return ob
light('SUN', (14, -10, 4), 2.8, (1.0, 0.92, 0.82))
light('AREA', (-9, 9, 6), 900, (0.62, 0.74, 1.0), size=6)
light('AREA', (6, -14, -2), 500, (1.0, 0.85, 0.7), size=8)

def sky_world():
    """Only mirrors see this world: the all-sky map of the Milky Way, tilted so the band lies where the far foil looks."""
    w = bpy.data.worlds.new('sky'); sc.world = w; w.use_nodes = True; nt = w.node_tree; N = nt.nodes.new; L = nt.links.new
    out = nt.nodes['World Output']; bg = nt.nodes['Background']; bg.inputs['Color'].default_value = (0.012, 0.013, 0.018, 1); bg.inputs['Strength'].default_value = 0.6
    tc = N('ShaderNodeTexCoord'); mp = N('ShaderNodeMapping'); L(tc.outputs['Generated'], mp.inputs['Vector'])
    mp.inputs['Rotation'].default_value = (math.radians(-22), 0, math.radians(38))
    tx = N('ShaderNodeTexEnvironment'); tx.image = bpy.data.images.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets', 'img', 'heroes', 'research_allsky.webp')); L(mp.outputs[0], tx.inputs['Vector'])
    gain = N('ShaderNodeVectorMath'); gain.operation = 'SCALE'; gain.inputs['Scale'].default_value = 2.6; L(tx.outputs['Color'], gain.inputs[0])
    flo = N('ShaderNodeVectorMath'); flo.operation = 'ADD'; flo.inputs[1].default_value = (0.2, 0.25, 0.34); L(gain.outputs[0], flo.inputs[0])
    b2 = N('ShaderNodeBackground'); L(flo.outputs[0], b2.inputs['Color'])
    lp = N('ShaderNodeLightPath'); mx = N('ShaderNodeMixShader'); L(lp.outputs['Is Glossy Ray'], mx.inputs['Fac']); L(bg.outputs[0], mx.inputs[1]); L(b2.outputs[0], mx.inputs[2]); L(mx.outputs[0], out.inputs['Surface'])
sky_world()

def warm_band():
    """A low band of warm metal round the collar, seen only in reflection: the near foil mirrors it as a soft pool of light."""
    n = 96; V = []; F = []
    for k in range(n):
        a = 2 * math.pi * k / n
        for z in (0.04, 1.0): V.append((1.86 * math.cos(a), 1.86 * math.sin(a), z))
    for k in range(n): F.append((2 * k, 2 * ((k + 1) % n), 2 * ((k + 1) % n) + 1, 2 * k + 1))
    me = bpy.data.meshes.new('band'); me.from_pydata(V, [], F); me.update(); m = bpy.data.materials.new('band'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.88, 0.8, 0.68, 1); b.inputs['Metallic'].default_value = 1.0; b.inputs['Roughness'].default_value = 0.32
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); ge = nt.nodes.new('ShaderNodeNewGeometry'); mx = nt.nodes.new('ShaderNodeMixShader'); ou = nt.nodes['Material Output']
    nt.links.new(ge.outputs['Backfacing'], mx.inputs[0]); nt.links.new(b.outputs[0], mx.inputs[1]); nt.links.new(tr.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], ou.inputs['Surface'])   # the drum looks straight through it
    me.materials.append(m); ob = bpy.data.objects.new('band', me); bpy.context.collection.objects.link(ob)
    ob.visible_camera = ob.visible_shadow = ob.visible_diffuse = ob.visible_transmission = ob.visible_volume_scatter = False
warm_band()

cam_d = bpy.data.cameras.new('cam'); cam_d.lens = float(os.environ.get('GAIA_LENS', '50')); cam_d.shift_y = float(os.environ.get('GAIA_SHIFT_Y', '0'))
cam = bpy.data.objects.new('cam', cam_d); bpy.context.collection.objects.link(cam); sc.camera = cam
el = math.radians(float(os.environ.get('GAIA_EL', '17'))); dist = float(os.environ.get('GAIA_DIST', '17.8'))   # low, so the band stands behind the body
cam.location = (0.783 * dist * math.cos(el), -0.621 * dist * math.cos(el), 0.9 + dist * math.sin(el))
if os.environ.get('GAIA_OLDCAM'): cam.location = (14.5, -11.5, 8.2); cam_d.lens = 55
cam.rotation_euler = (Vector((0, 0, 0.9)) - cam.location).to_track_quat('-Z', 'Y').to_euler()

if os.environ.get('GAIA_CHECK'):
    from bpy_extras.object_utils import world_to_camera_view
    V = [(o, [v.co.copy() for v in o.data.vertices]) for o in root.children]; worst = [9, 9, 9, 9]; cut = 0
    for k in range(72):
        root.rotation_euler[2] = 2 * math.pi * k / 72; bpy.context.view_layer.update()
        x0 = y0 = 9; x1 = y1 = -9
        for o, vs in V:
            M = o.matrix_world
            for v in vs:
                q = world_to_camera_view(sc, cam, M @ v); x0, x1, y0, y1 = min(x0, q.x), max(x1, q.x), min(y0, q.y), max(y1, q.y)
        m = (x0, 1 - x1, y0, 1 - y1); worst = [min(a, b) for a, b in zip(worst, m)]; cut += min(m) < 0
    print('MARGINS left, right, bottom, top, worst of 72 angles', [round(w, 4) for w in worst], 'angles clipped', cut); sys.exit(0)
if ANIM:
    sc.frame_start, sc.frame_end = 1, NFR; sc.render.fps = 30
    root.rotation_euler[2] = 0.0; root.keyframe_insert('rotation_euler', index=2, frame=1)
    root.rotation_euler[2] = 2 * math.pi; root.keyframe_insert('rotation_euler', index=2, frame=NFR + 1)
    for fc in root.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = out + '/f_'
    bpy.ops.render.render(animation=True)
elif os.environ.get('GAIA_STILLS'):   # several angles in one process: OUT is a prefix
    for a in os.environ['GAIA_STILLS'].split(','):
        root.rotation_euler[2] = math.radians(float(a)); sc.render.filepath = f'{out}_{a}.png'
        bpy.ops.render.render(write_still=True)
else:
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
print('wrote', out)
