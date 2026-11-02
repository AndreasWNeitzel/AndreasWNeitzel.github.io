"""Printed pages of the published papers in a loose pile on a dark desk, a camera breathing over them (Blender, Cycles).

The sheets are real typeset pages rasterised from the documents themselves, nothing composed by hand: the title
page of Neitzel et al. 2025 (A&A 695, A243) on top, sharp, with the title block in focus; three inner pages of the
same paper (pages 3, 5 and 9, each with a figure inside the two-column text) fanned out beneath it; the first
page of Campante et al. 2024 (the A&A Letter on epsilon Indi, arXiv typesetting) at the left, its near corner
under the top sheet; the title page of the MSc dissertation and its page with the Kippenhahn diagrams (page 44
of the file, printed page 16) lowest in the pile. Every sheet is A4 (0.21 by 0.297, 1.5 mm thick, with a 2 mm
sine arch so it reads as paper) and carries its page at full size. No text, logos, marks or props are added:
paper, desk and light only.

One warm desk lamp from the far left (an area light, about 2700 K), one weak cool fill from the near right, a
faint vignette in the compositor, so the near left of the frame stays dark for the title the page sets there.
The camera (50 mm, f/3.2, focus on the title block) looks down at 55 degrees and moves on a small ellipse
around its rest position while tracking a fixed point on the desk, over 300 frames at 30 fps. The path is
periodic, so frame 300 equals frame 0 and the loop closes without a crossfade.

Usage, from the repository root, with DIR a working directory that holds the three source documents under
DIR/pdf as neitzel2025.pdf, campante2024.pdf and neitzel2022_msc.pdf:
  uv run --python 3.11 --with bpy==4.2.0 --with pillow python figures/heroes/blender_desk.py DIR prep
  uv run --python 3.11 --with bpy==4.2.0 --with pillow python figures/heroes/blender_desk.py DIR still FRAME [samples] [W] [H]
  uv run --python 3.11 --with bpy==4.2.0 --with pillow python figures/heroes/blender_desk.py DIR anim [samples] [W] [H] [first] [last]
  uv run --python 3.11 --with pillow python figures/heroes/blender_desk.py DIR post
Prep rasterises the pages with pdftoppm (annotation borders hidden, so the arXiv link boxes do not print). The
still and anim modes run prep themselves when the textures are missing. Set DESK_GPU=1 in the environment
to render on the graphics card instead of the processor. The post mode writes the poster
(frame 0 as desk.poster.webp) and prints the seam check, the mean difference between frames 299 and 0 against
that between frames 0 and 1. Encoding to video is done with ffmpeg afterwards:
  ffmpeg -y -framerate 30 -i DIR/frames/f_%04d.png -vf "scale=1280:-2,format=yuv420p" -c:v libsvtav1 -crf 42 \\
    -preset 5 -g 120 -movflags +faststart DIR/desk.av1.mp4
  ffmpeg -y -framerate 30 -i DIR/frames/f_%04d.png -vf "scale=1280:-2,format=yuv420p" -c:v libx264 -crf 28 \\
    -preset slow -g 120 -movflags +faststart DIR/desk.h264.mp4
"""
import math
import os
import subprocess
import sys

# bottom of the pile first; (document, page, centre x, centre y, rotation in degrees about the vertical)
# x runs to the right of the camera, y away from it; the desk is z = 0 and the camera aims at the origin
SHEETS = [
    ('neitzel2022_msc', 44, 0.24, -0.03, -8.0),
    ('neitzel2022_msc', 1, 0.02, 0.22, 6.0),
    ('neitzel2025', 5, -0.30, 0.16, 24.0),
    ('neitzel2025', 9, -0.40, 0.03, 32.0),
    ('neitzel2025', 3, 0.26, 0.14, -8.0),
    ('campante2024', 1, -0.17, 0.11, 20.0),
    ('neitzel2025', 1, 0.03, -0.05, -5.0),
]
DPI, TOP_DPI = 150, 220                  # raster resolution of the pages; the top sheet gets more
SHEET_W, SHEET_H, THICK, ARCH = 0.21, 0.297, 0.0015, 0.002
LAYER = THICK + ARCH + 0.0002            # sheets never cut into each other
FRAMES, FPS = 300, 30
CAM_DIST, CAM_PITCH, CAM_LENS, CAM_FSTOP = 0.64, 55.0, 50.0, 3.2
SWAY_X, SWAY_D = 0.010, 0.012            # half amplitude of the lateral sway and of the dolly in and out
SHIFT = (-0.180, -0.065)                 # lens shift, which moves the pile right and up with no change of perspective
FOCUS = (0.03, 0.05)                     # x, y of the focus point, on the title block of the top sheet
PAPER = (0.93, 0.92, 0.89)
DESK = (0.05, 0.045, 0.04)
LAMP = (1.0, 0.78, 0.55)
FILL = (0.62, 0.72, 1.0)
LAMP_POWER, FILL_POWER = 8.5, 0.8


def tex_path(d, doc, page):
    return os.path.join(d, 'tex', '%s_p%02d.png' % (doc, page))


def prep(d):
    """Rasterise each page used on the desk from its document, at DPI (TOP_DPI for the top sheet)."""
    os.makedirs(os.path.join(d, 'tex'), exist_ok=True)
    for k, (doc, page, *_) in enumerate(SHEETS):
        src = os.path.join(d, 'pdf', doc + '.pdf')
        if not os.path.exists(src):
            print('missing document, sheet left blank:', src)
            continue
        dpi = TOP_DPI if k == len(SHEETS) - 1 else DPI
        stem = os.path.join(d, 'tex', 'tmp_%s_%02d' % (doc, page))
        subprocess.run(['pdftoppm', '-r', str(dpi), '-png', '-hide-annotations', '-singlefile',
                        '-f', str(page), '-l', str(page), src, stem], check=True)
        os.replace(stem + '.png', tex_path(d, doc, page))
        print('texture', tex_path(d, doc, page))


def build(d, samples, W, H):
    import bpy, bmesh
    from mathutils import Vector
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
    if os.environ.get('DESK_GPU') == '1':
        # the graphics card, when there is one: about twice as fast as the processor for these frames
        prefs = bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type = 'CUDA'; prefs.get_devices()
        for dev in prefs.devices: dev.use = dev.type == 'CUDA'
        sc.cycles.device = 'GPU'
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
        m = principled(name, PAPER, 0.7); nt = m.node_tree; b = nt.nodes['Principled BSDF']
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
    desk.data.materials.append(principled('desk', DESK, 0.65))
    desk.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.3

    # sheets: a grid with UVs, arched by a sine, solidified upwards to the paper thickness
    for k, (doc, page, x, y, rot) in enumerate(SHEETS):
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
        ob.data.materials.append(paper('paper%d' % k, tex_path(d, doc, page)))
        for p in me.polygons: p.use_smooth = True

    # lights: the warm lamp from the far left, a weak cool fill from the near right
    def area(name, loc, aim, color, power, size):
        ld = bpy.data.lights.new(name, 'AREA'); ld.color = color; ld.energy = power; ld.size = size; ld.shape = 'DISK'
        lo = bpy.data.objects.new(name, ld); bpy.context.collection.objects.link(lo); lo.location = loc
        lo.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return lo
    area('lamp', (-0.40, 0.02, 0.55), (0.08, 0.03, 0.0), LAMP, LAMP_POWER, 0.22)
    area('fill', (0.55, -0.30, 0.45), (0.0, 0.0, 0.0), FILL, FILL_POWER, 0.8)
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.004, 0.0045, 0.006, 1)

    # camera: pitched down at the origin, breathing on a closed path, focus on the title block of the top sheet
    aim = bpy.data.objects.new('aim', None); bpy.context.collection.objects.link(aim); aim.location = (0, 0, 0)
    focus = bpy.data.objects.new('focus', None); bpy.context.collection.objects.link(focus)
    focus.location = (FOCUS[0], FOCUS[1], len(SHEETS) * LAYER)
    cd = bpy.data.cameras.new('cam'); cd.lens = CAM_LENS; cd.sensor_width = 36; cd.shift_x, cd.shift_y = SHIFT
    cd.dof.use_dof = True; cd.dof.focus_object = focus; cd.dof.aperture_fstop = CAM_FSTOP; cd.dof.aperture_blades = 7
    cam = bpy.data.objects.new('cam', cd); bpy.context.collection.objects.link(cam); sc.camera = cam
    tr = cam.constraints.new('TRACK_TO'); tr.target = aim; tr.track_axis = 'TRACK_NEGATIVE_Z'; tr.up_axis = 'UP_Y'
    pitch = math.radians(CAM_PITCH)
    for f in range(FRAMES + 1):
        t = 2 * math.pi * f / FRAMES
        dist = CAM_DIST + SWAY_D * (1 - math.cos(t)) / 2
        cam.location = (SWAY_X * math.sin(t), -dist * math.cos(pitch), dist * math.sin(pitch))
        cam.keyframe_insert('location', frame=f)
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
    """The poster from frame 0, and the seam check: frames 299 to 0 should differ no more than frames 0 to 1."""
    from PIL import Image, ImageChops, ImageStat
    fr = os.path.join(d, 'frames')
    load = lambda i: Image.open(os.path.join(fr, 'f_%04d.png' % i)).convert('RGB')
    f0, f1, fl = load(0), load(1), load(FRAMES - 1)
    seam = sum(ImageStat.Stat(ImageChops.difference(fl, f0)).mean) / 3
    step = sum(ImageStat.Stat(ImageChops.difference(f0, f1)).mean) / 3
    print('seam check: mean difference 299 to 0 = %.3f, 0 to 1 = %.3f (8 bit levels)' % (seam, step))
    f0.save(os.path.join(d, 'desk.poster.webp'), quality=82)
    print('wrote', os.path.join(d, 'desk.poster.webp'))


if __name__ == '__main__':
    d, mode = sys.argv[1], sys.argv[2]
    os.makedirs(os.path.join(d, 'frames'), exist_ok=True)
    if mode == 'prep':
        prep(d)
    elif mode == 'post':
        post(d)
    else:
        if not all(os.path.exists(tex_path(d, doc, p)) for doc, p, *_ in SHEETS if os.path.exists(os.path.join(d, 'pdf', doc + '.pdf'))):
            prep(d)
        import bpy
        if mode == 'still':
            frame = int(sys.argv[3]); rest = sys.argv[4:]
            samples = int(rest[0]) if rest else 24
            W, H = (int(rest[1]), int(rest[2])) if len(rest) > 2 else (480, 270)
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
