"""The published figures as printed sheets on a dark desk, a slow camera dolly across them (Blender, Cycles).

The sheets carry the figures exactly as they appear on the site, under assets/img/papers: Neitzel et al. 2025
(the four samples of the manifold learning paper, the first author paper, on top and nearest the camera),
Campante et al. 2026 (oscillation amplitude against luminosity over mass for GJ 570 A and the other K dwarfs),
Campante et al. 2024 (the epsilon Indi sample in radius against effective temperature) and the MSc dissertation
(the Kippenhahn diagrams). Each image is placed at its own aspect ratio, centred with white margins on a sheet of
A4 proportion (0.21 by 0.297, 1.5 mm thick, with a 2 mm sine arch so it reads as paper). Nothing is added to
the sheets: no text, no logos, no marks. The Magrini et al. 2022 figure has no published image in the repository
(the paper page draws a Kiel diagram from the CDS tables), so it is not on the desk.

One warm desk lamp from the upper left (an area light, 2700 K), one weak cool fill, a faint vignette in the
compositor. The camera (50 mm, f/2.8, focus on the top sheet) sits about half a unit above the desk, pitched
55 degrees down, and dollies from right to left over 300 frames at 30 fps. The loop closes with a 30 frame
crossfade of the last frame into the first, blended with Pillow and appended as frames 300 to 329.

Usage, from the repository root, with DIR the working directory for the textures and frames:
  uv run --python 3.11 --with bpy==4.2.0 --with pillow python figures/heroes/blender_desk.py DIR prep
  uv run --python 3.11 --with bpy==4.2.0 --with pillow python figures/heroes/blender_desk.py DIR still FRAME [samples] [W] [H]
  uv run --python 3.11 --with bpy==4.2.0 --with pillow python figures/heroes/blender_desk.py DIR anim [samples] [W] [H] [first] [last]
  uv run --python 3.11 --with pillow python figures/heroes/blender_desk.py DIR post
The still and anim modes run prep themselves when the textures are missing. The post mode writes the crossfade
frames and the poster (frame 100 as desk.poster.webp). Encoding to video is done with ffmpeg afterwards:
  ffmpeg -y -framerate 30 -i DIR/frames/f_%04d.png -vf "scale=1280:-2,format=yuv420p" -c:v libsvtav1 -crf 42 \\
    -preset 5 -g 120 -movflags +faststart DIR/desk.av1.mp4
  ffmpeg -y -framerate 30 -i DIR/frames/f_%04d.png -vf "scale=1280:-2,format=yuv420p" -c:v libx264 -crf 28 \\
    -preset slow -g 120 -movflags +faststart DIR/desk.h264.mp4
"""
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PAPERS = os.path.join(ROOT, 'assets', 'img', 'papers')

# bottom of the pile first; (file, centre x, centre y, rotation in degrees about the vertical)
# x runs to the right of the camera, y away from it; the desk is z = 0
SHEETS = [
    ('neitzel-2022-kippenhahn.webp', 0.03, 0.27, -3.0),
    ('campante-2024-eps-indi.webp', 0.175, 0.13, 8.0),
    ('campante-2026-gj570a.webp', -0.165, 0.11, -7.0),
    ('neitzel-2025-manifold-learning.webp', 0.0, -0.02, 3.5),
]
SHEET_W, SHEET_H, THICK, ARCH = 0.21, 0.297, 0.0015, 0.002
LAYER = THICK + ARCH + 0.0002        # sheets never cut into each other
CANVAS_W = 1240                      # texture pixels across a sheet; A4 at about 150 dpi
MARGIN = 0.075                       # white margin as a fraction of the sheet width
FRAMES, FPS, FADE = 300, 30, 30
DOLLY = 0.12                         # camera x from +DOLLY to -DOLLY
CAM_H, CAM_PITCH, CAM_LENS, CAM_FSTOP = 0.5, 55.0, 50.0, 2.8
PAPER = (0.93, 0.92, 0.89)
DESK = (0.05, 0.045, 0.04)
LAMP = (1.0, 0.78, 0.55)
FILL = (0.62, 0.72, 1.0)


def tex_path(d, name):
    return os.path.join(d, 'tex', os.path.splitext(name)[0] + '.png')


def prep(d):
    """Convert each figure to a PNG sheet canvas: white A4 page, figure fitted to the width, centred."""
    from PIL import Image
    os.makedirs(os.path.join(d, 'tex'), exist_ok=True)
    cw, ch = CANVAS_W, round(CANVAS_W * SHEET_H / SHEET_W)
    for name, *_ in SHEETS:
        src = os.path.join(PAPERS, name)
        if not os.path.exists(src):
            print('missing figure, sheet left blank:', src)
            continue
        im = Image.open(src).convert('RGB')
        fw = round(cw * (1 - 2 * MARGIN)); fh = round(fw * im.height / im.width)
        if fh > ch * (1 - 2 * MARGIN * SHEET_W / SHEET_H):
            fh = round(ch * (1 - 2 * MARGIN * SHEET_W / SHEET_H)); fw = round(fh * im.width / im.height)
        im = im.resize((fw, fh), Image.LANCZOS)
        page = Image.new('RGB', (cw, ch), (255, 255, 255))
        page.paste(im, ((cw - fw) // 2, (ch - fh) // 2))
        page.save(tex_path(d, name), compress_level=6)
        print('texture', tex_path(d, name), page.size)


def build(d, samples, W, H):
    import bpy, bmesh
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
    sc.render.resolution_x, sc.render.resolution_y = W, H; sc.render.resolution_percentage = 100
    sc.render.fps = FPS; sc.frame_start = 0; sc.frame_end = FRAMES - 1
    sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
    sc.render.film_transparent = False

    def principled(name, base, rough, metal=0.0):
        m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = (*base, 1); b.inputs['Roughness'].default_value = rough
        b.inputs['Metallic'].default_value = metal; return m

    def paper(name, png):
        # the printed sheet: the page image multiplied by the paper tint, so margins are paper and ink is ink
        m = principled(name, PAPER, 0.65); nt = m.node_tree; b = nt.nodes['Principled BSDF']
        if png and os.path.exists(png):
            img = bpy.data.images.load(png); img.colorspace_settings.name = 'sRGB'
            t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; t.interpolation = 'Cubic'; t.extension = 'EXTEND'
            uv = nt.nodes.new('ShaderNodeUVMap'); nt.links.new(uv.outputs['UV'], t.inputs['Vector'])
            mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
            mx.inputs[6].default_value = (*PAPER, 1)
            nt.links.new(t.outputs['Color'], mx.inputs[7]); nt.links.new(mx.outputs[2], b.inputs['Base Color'])
        return m

    # desk
    bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, 0)); desk = bpy.context.object; desk.name = 'desk'
    desk.data.materials.append(principled('desk', DESK, 0.5))

    # sheets: a grid with UVs, arched by a sine, solidified upwards to the paper thickness
    top = None
    for k, (name, x, y, rot) in enumerate(SHEETS):
        nx, ny = 32, 44
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=nx, y_segments=ny, size=0.5)
        uvl = bm.loops.layers.uv.new('UVMap')
        for v in bm.verts:
            u, w = v.co.x + 0.5, v.co.y + 0.5
            z = ARCH * math.sin(math.pi * u) * math.sin(math.pi * w) * (0.85 + 0.15 * math.cos(3 * math.pi * u + k))
            v.co = (v.co.x * SHEET_W, v.co.y * SHEET_H, z)
        for f in bm.faces:
            for lp in f.loops:
                lp[uvl].uv = (lp.vert.co.x / SHEET_W + 0.5, lp.vert.co.y / SHEET_H + 0.5)
        me = bpy.data.meshes.new('sheet%d' % k); bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new('sheet%d' % k, me); bpy.context.collection.objects.link(ob)
        ob.location = (x, y, k * LAYER); ob.rotation_euler = (0, 0, math.radians(rot))
        sol = ob.modifiers.new('solid', 'SOLIDIFY'); sol.thickness = THICK; sol.offset = 1.0; sol.use_even_offset = True
        ob.data.materials.append(paper('paper%d' % k, tex_path(d, name)))
        for p in me.polygons: p.use_smooth = True
        top = ob

    # lights: the warm lamp from the upper left, a weak cool fill from the right
    def area(name, loc, aim, color, power, size):
        ld = bpy.data.lights.new(name, 'AREA'); ld.color = color; ld.energy = power; ld.size = size; ld.shape = 'DISK'
        lo = bpy.data.objects.new(name, ld); bpy.context.collection.objects.link(lo); lo.location = loc
        from mathutils import Vector
        lo.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return lo
    area('lamp', (-0.5, -0.15, 0.55), (0.0, 0.04, 0.0), LAMP, 10.0, 0.32)
    area('fill', (0.55, -0.35, 0.45), (0.0, 0.1, 0.0), FILL, 1.5, 0.7)
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.004, 0.0045, 0.006, 1)

    # camera: pitched down, dollying along x, focus on the top sheet
    cd = bpy.data.cameras.new('cam'); cd.lens = CAM_LENS; cd.sensor_width = 36
    cd.dof.use_dof = True; cd.dof.focus_object = top; cd.dof.aperture_fstop = CAM_FSTOP; cd.dof.aperture_blades = 7
    cam = bpy.data.objects.new('cam', cd); bpy.context.collection.objects.link(cam); sc.camera = cam
    cam.rotation_euler = (math.radians(90 - CAM_PITCH), 0, 0)
    cy = top.location.y + 0.04 - CAM_H / math.tan(math.radians(CAM_PITCH))   # aim a little past the sheet centre
    cam.location = (DOLLY, cy, CAM_H); cam.keyframe_insert('location', frame=0)
    cam.location = (-DOLLY, cy, CAM_H); cam.keyframe_insert('location', frame=FRAMES - 1)
    for fc in cam.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

    # a faint vignette
    sc.use_nodes = True; ct = sc.node_tree; rl = ct.nodes['Render Layers']; comp = ct.nodes['Composite']
    em = ct.nodes.new('CompositorNodeEllipseMask'); em.width = 1.3; em.height = 1.3
    bl = ct.nodes.new('CompositorNodeBlur'); bl.filter_type = 'FAST_GAUSS'; bl.use_relative = True; bl.factor_x = 35; bl.factor_y = 35
    mx = ct.nodes.new('CompositorNodeMixRGB'); mx.blend_type = 'MULTIPLY'; mx.inputs['Fac'].default_value = 0.35
    ct.links.new(em.outputs['Mask'], bl.inputs['Image']); ct.links.new(rl.outputs['Image'], mx.inputs[1])
    ct.links.new(bl.outputs['Image'], mx.inputs[2]); ct.links.new(mx.outputs['Image'], comp.inputs['Image'])
    return sc


def post(d):
    """Crossfade frames FRAMES to FRAMES + FADE - 1 from the last rendered frame into the first, and the poster."""
    from PIL import Image
    fr = os.path.join(d, 'frames')
    a = Image.open(os.path.join(fr, 'f_%04d.png' % (FRAMES - 1))).convert('RGB')
    b = Image.open(os.path.join(fr, 'f_%04d.png' % 0)).convert('RGB')
    for i in range(FADE):
        t = (i + 1) / (FADE + 1)
        Image.blend(a, b, t).save(os.path.join(fr, 'f_%04d.png' % (FRAMES + i)), compress_level=6)
    Image.open(os.path.join(fr, 'f_0100.png')).convert('RGB').save(os.path.join(d, 'desk.poster.webp'), quality=80)
    print('wrote', FADE, 'crossfade frames and', os.path.join(d, 'desk.poster.webp'))


if __name__ == '__main__':
    d, mode = sys.argv[1], sys.argv[2]
    os.makedirs(os.path.join(d, 'frames'), exist_ok=True)
    if mode == 'prep':
        prep(d)
    elif mode == 'post':
        post(d)
    else:
        if not all(os.path.exists(tex_path(d, n)) for n, *_ in SHEETS if os.path.exists(os.path.join(PAPERS, n))):
            prep(d)
        import bpy
        if mode == 'still':
            frame = int(sys.argv[3]); rest = sys.argv[4:]
            samples = int(rest[0]) if rest else 24
            W, H = (int(rest[1]), int(rest[2])) if len(rest) > 2 else (480, 320)
            sc = build(d, samples, W, H); sc.frame_set(frame)
            out = os.path.join(d, 'still_%04d_%dx%d.png' % (frame, W, H))
            sc.render.filepath = out; bpy.ops.render.render(write_still=True); print('wrote', out)
        elif mode == 'anim':
            rest = sys.argv[3:]
            samples = int(rest[0]) if rest else 32
            W, H = (int(rest[1]), int(rest[2])) if len(rest) > 2 else (1280, 720)
            sc = build(d, samples, W, H)
            if len(rest) > 4: sc.frame_start, sc.frame_end = int(rest[3]), int(rest[4])   # a partial range, to resume
            sc.render.filepath = os.path.join(d, 'frames', 'f_')
            bpy.ops.render.render(animation=True); print('wrote frames to', sc.render.filepath)
        else:
            sys.exit('mode must be prep, still, anim or post')
