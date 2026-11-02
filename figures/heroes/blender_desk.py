"""Printed pages of the published papers lying on a dark desk, one still (Blender, Cycles).

The sheets are real typeset pages rasterised from the documents themselves, nothing composed by hand: the title
page of Neitzel et al. 2025 (A&A 695, A243) on top, sharp, with the title block in focus; three inner pages of the
same paper (pages 3, 5 and 9, each with a figure inside the two-column text) fanned out beneath it; the first
page of Campante et al. 2024 (the A&A Letter on epsilon Indi, arXiv typesetting) at the left, its near corner
under the top sheet; the title page of the MSc dissertation and its page with the Kippenhahn diagrams (page 44
of the file, printed page 16) lowest in the pile. Every sheet is A4 (0.21 by 0.297) and carries its page at full
size. No text, logos, marks or props are added: paper, desk and light only.

The sheets rest on what is under them. Going up the pile, each sheet takes its height from a height map of the
desk and the sheets already laid, follows it with the small stiffness of paper, and adds back the map for the next
sheet, so a sheet lies on the desk where it overhangs the pile and nowhere is there more than a fraction of a
millimetre of air, the rim of a sheet standing highest, so that its shadow is a thin line. Paper is 0.2 mm thick
here. The top sheet lifts by about a millimetre at one corner.

One warm desk lamp from the far left (a broad area light, about 2700 K), one weak cool fill from the near right, a
faint vignette in the compositor, so the near left of the frame stays dark for the title the page sets there.
The camera (50 mm, f/3.2, focus on the title block) looks down at 55 degrees and does not move.

Usage, from the repository root, with DIR a working directory that holds the three source documents under
DIR/pdf as neitzel2025.pdf, campante2024.pdf and neitzel2022_msc.pdf:
  uv run --python 3.11 --with bpy==4.2.0 --with pillow python figures/heroes/blender_desk.py DIR prep
  uv run --python 3.11 --with bpy==4.2.0 --with pillow python figures/heroes/blender_desk.py DIR still OUT.png [samples] [W] [H]
Prep rasterises the pages with pdftoppm (annotation borders hidden, so the arXiv link boxes do not print). The
still mode runs prep itself when the textures are missing. Set CYCLES_DEVICE=GPU in the environment to render
on the graphics card instead of the processor.
"""
import math
import os
import subprocess
import sys

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

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
SHEET_W, SHEET_H, THICK = 0.21, 0.297, 0.0002
GAP, WAVE, RIM, CURL = 0.00005, 0.00025, 0.00045, 0.0008  # air under a sheet, its slow unevenness, the lift of its rim, of the top corner
NX, NY = 126, 178                        # grid of each sheet, about 1.7 mm
CELL = 0.0005                            # cell of the height map
CAM_DIST, CAM_PITCH, CAM_LENS, CAM_FSTOP = 0.64, 55.0, 50.0, 3.2
SHIFT = (-0.180, -0.065)                 # lens shift, which moves the pile right and up with no change of perspective
FOCUS = (0.03, 0.05)                     # x, y of the focus point, on the title block of the top sheet
PAPER = (0.93, 0.92, 0.89)
DESK = (0.028, 0.025, 0.023)
LAMP = (1.0, 0.78, 0.55)
FILL = (0.62, 0.72, 1.0)
LAMP_POWER, FILL_POWER, LAMP_SIZE = 15.0, 0.7, 0.5


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


def blur(a, n):
    """Three box passes of half width n along both axes of a grid, edges held."""
    ker = np.ones(2 * n + 1) / (2 * n + 1)
    for _ in range(3):
        for ax in (0, 1):
            pad = [(n, n) if i == ax else (0, 0) for i in (0, 1)]
            a = np.apply_along_axis(lambda r: np.convolve(r, ker, 'valid'), ax, np.pad(a, pad, 'edge'))
    return a


def spread(a, n):
    """The highest value within n cells along both axes, so that a following blur of half width n stays above a."""
    for ax in (0, 1):
        pad = [(n, n) if i == ax else (0, 0) for i in (0, 1)]
        a = sliding_window_view(np.pad(a, pad, 'edge'), 2 * n + 1, ax).max(-1)
    return a


def lay_sheets():
    """Height of every sheet's grid, from the bottom of the pile up, each resting on what is already there."""
    x0, y0 = -0.8, -0.7
    mp = np.zeros((int(1.4 / CELL), int(1.6 / CELL)))
    u, w = np.meshgrid(np.linspace(-0.5, 0.5, NX + 1), np.linspace(-0.5, 0.5, NY + 1))
    out = []
    for k, (_doc, _page, x, y, rot) in enumerate(SHEETS):
        c, n = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        lx, ly = u * SHEET_W, w * SHEET_H
        wx, wy = x + c * lx - n * ly, y + n * lx + c * ly
        rest = mp[((wy - y0) / CELL).astype(int), ((wx - x0) / CELL).astype(int)]
        z = blur(spread(rest, 9), 3)             # paper rises over a step in about a centimetre, and never cuts into it
        z += GAP + WAVE * (0.5 + 0.5 * np.sin(2.1 * math.pi * u + k) * np.cos(1.7 * math.pi * w + 2 * k))
        z += RIM * np.maximum(np.abs(2 * u), np.abs(2 * w)) ** 6
        if k == len(SHEETS) - 1:                 # the barely lifted corner, far right of the top sheet
            r = np.hypot(u - 0.5, (w - 0.5) * SHEET_H / SHEET_W)
            z += CURL * np.clip(1 - r / 0.28, 0, None) ** 2
        out.append(z)
        ii, jj = np.nonzero(np.ones_like(mp, bool)[
            int((wy.min() - y0) / CELL):int((wy.max() - y0) / CELL) + 1, int((wx.min() - x0) / CELL):int((wx.max() - x0) / CELL) + 1])
        ii += int((wy.min() - y0) / CELL); jj += int((wx.min() - x0) / CELL)
        dx, dy = x0 + jj * CELL - x, y0 + ii * CELL - y
        cu, cw = (c * dx + n * dy) / SHEET_W, (-n * dx + c * dy) / SHEET_H
        ins = (np.abs(cu) < 0.5) & (np.abs(cw) < 0.5)
        mp[ii[ins], jj[ins]] = z[((cw[ins] + 0.5) * NY).astype(int), ((cu[ins] + 0.5) * NX).astype(int)] + THICK
    return out


def build(d, samples, W, H):
    import bpy, bmesh
    from mathutils import Vector
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
    if os.environ.get('CYCLES_DEVICE') == 'GPU':
        prefs = bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type = 'CUDA'; prefs.get_devices()
        for dev in prefs.devices: dev.use = dev.type == 'CUDA'
        sc.cycles.device = 'GPU'
    sc.render.resolution_x, sc.render.resolution_y = W, H; sc.render.resolution_percentage = 100
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

    # sheets: a grid with UVs at their resting heights, solidified upwards to the paper thickness
    heights = lay_sheets()
    for k, (doc, page, x, y, rot) in enumerate(SHEETS):
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=NX, y_segments=NY, size=0.5)
        uvl = bm.loops.layers.uv.new('UVMap')
        for v in bm.verts:
            i, j = round((v.co.x + 0.5) * NX), round((v.co.y + 0.5) * NY)
            v.co = (v.co.x * SHEET_W, v.co.y * SHEET_H, heights[k][j, i])
        for f in bm.faces:
            for lp in f.loops:
                lp[uvl].uv = (lp.vert.co.x / SHEET_W + 0.5, lp.vert.co.y / SHEET_H + 0.5)
        me = bpy.data.meshes.new('sheet%d' % k); bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new('sheet%d' % k, me); bpy.context.collection.objects.link(ob)
        ob.location = (x, y, 0); ob.rotation_euler = (0, 0, math.radians(rot))
        sol = ob.modifiers.new('solid', 'SOLIDIFY'); sol.thickness = THICK; sol.offset = 1.0; sol.use_even_offset = True
        ob.data.materials.append(paper('paper%d' % k, tex_path(d, doc, page)))
        for p in me.polygons: p.use_smooth = True

    # lights: the warm lamp from the far left, a weak cool fill from the near right
    def area(name, loc, aim, color, power, size):
        ld = bpy.data.lights.new(name, 'AREA'); ld.color = color; ld.energy = power; ld.size = size; ld.shape = 'DISK'
        lo = bpy.data.objects.new(name, ld); bpy.context.collection.objects.link(lo); lo.location = loc
        lo.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return lo
    area('lamp', (-0.72, 0.30, 0.44), (0.10, 0.05, 0.0), LAMP, LAMP_POWER, LAMP_SIZE)
    area('fill', (0.55, -0.30, 0.45), (0.0, 0.0, 0.0), FILL, FILL_POWER, 0.8)
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.004, 0.0045, 0.006, 1)

    # camera: pitched down at the origin, focus on the title block of the top sheet
    focus = bpy.data.objects.new('focus', None); bpy.context.collection.objects.link(focus)
    focus.location = (FOCUS[0], FOCUS[1], 0.001)
    cd = bpy.data.cameras.new('cam'); cd.lens = CAM_LENS; cd.sensor_width = 36; cd.shift_x, cd.shift_y = SHIFT
    cd.dof.use_dof = True; cd.dof.focus_object = focus; cd.dof.aperture_fstop = CAM_FSTOP; cd.dof.aperture_blades = 7
    cam = bpy.data.objects.new('cam', cd); bpy.context.collection.objects.link(cam); sc.camera = cam
    pitch = math.radians(CAM_PITCH)
    cam.location = (0, -CAM_DIST * math.cos(pitch), CAM_DIST * math.sin(pitch))
    cam.rotation_euler = (Vector((0, 0, 0)) - cam.location).to_track_quat('-Z', 'Y').to_euler()

    # a faint vignette
    sc.use_nodes = True; ct = sc.node_tree; rl = ct.nodes['Render Layers']; comp = ct.nodes['Composite']
    em = ct.nodes.new('CompositorNodeEllipseMask'); em.width = 1.3; em.height = 1.3
    bl = ct.nodes.new('CompositorNodeBlur'); bl.filter_type = 'FAST_GAUSS'; bl.use_relative = True; bl.factor_x = 35; bl.factor_y = 35
    mx = ct.nodes.new('CompositorNodeMixRGB'); mx.blend_type = 'MULTIPLY'; mx.inputs['Fac'].default_value = 0.35
    ct.links.new(em.outputs['Mask'], bl.inputs['Image']); ct.links.new(rl.outputs['Image'], mx.inputs[1])
    ct.links.new(bl.outputs['Image'], mx.inputs[2]); ct.links.new(mx.outputs['Image'], comp.inputs['Image'])
    return sc


if __name__ == '__main__':
    d, mode = sys.argv[1], sys.argv[2]
    if mode == 'prep':
        prep(d)
    elif mode == 'still':
        if not all(os.path.exists(tex_path(d, doc, p)) for doc, p, *_ in SHEETS if os.path.exists(os.path.join(d, 'pdf', doc + '.pdf'))):
            prep(d)
        import bpy
        out, rest = sys.argv[3], sys.argv[4:]
        samples = int(rest[0]) if rest else 24
        W, H = (int(rest[1]), int(rest[2])) if len(rest) > 2 else (480, 270)
        sc = build(d, samples, W, H)
        sc.render.filepath = out; bpy.ops.render.render(write_still=True); print('wrote', out)
    else:
        sys.exit('mode must be prep or still')
