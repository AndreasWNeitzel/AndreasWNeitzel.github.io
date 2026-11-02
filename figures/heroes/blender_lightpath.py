"""The light path from a Unit Telescope to ESPRESSO as a rendered cross-section (Blender 4.2 as a module, Cycles).
UT2 is cut open along a vertical plane through the telescope's optical axis; the half nearer the viewer is
removed. Inside: the 8.2 m primary mirror as a thin concave meniscus of glass with a reflective face, the
secondary at the top of the structure, the tertiary at the crossing of the axes, the Nasmyth platform, and the
Coude train as a chain of small mirrors folding the light down through the fork and the hollow pier to the Coude
room under the telescope, then along a duct in the rock to the Combined-Coude Laboratory, where ESPRESSO's vacuum
vessel (a horizontal cylinder of brushed steel) receives it. The light is one amber beam from the sky to the
vessel. No text.

Real, with sources
- The primary mirror: 8.2 m across, 177 mm thick, focal ratio f/1.75 (ESO, VLT Unit Telescope pages), so the
  curvature radius is 28.7 m and the dish's sag 0.29 m; the secondary 1.12 m across; the enclosure about 29 m
  across and high (ESO, VLT enclosure page), with the 9.5 m slit down the front and across the roof.
- The route: from the Nasmyth B focus down to a Coude room under the telescope and through a duct in the rock
  to the Combined-Coude Laboratory, 48 m from UT2 (Pepe et al. 2014, arXiv:1401.5918); the laboratory about
  10.7 by 20 m and the Coude room 8.5 m across (Grupp et al. 2020, arXiv:2004.12499).
Schematic: the mirror to secondary distance (12.4 m), the fork, pier and azimuth floor, the number and places
of the Coude train mirrors, the duct's diameter and depth, the laboratory's height and orientation, the vacuum
vessel's size (about 2 m across and 3.6 m long here) and every material.

Usage, from the repository root, with DIR the working directory:
  uv run --python 3.11 --with bpy==4.2.0 --with pillow python figures/heroes/blender_lightpath.py DIR test [samples] [W] [H]
  uv run --python 3.11 --with bpy==4.2.0 --with pillow python figures/heroes/blender_lightpath.py DIR still [samples] [W] [H]
Set CYCLES_DEVICE=GPU to render on the graphics card (the same tracer; the CPU path of this wheel is slow).
"""
import math
import os
import sys

import numpy as np

AMBER = (1.0, 0.55, 0.15)
TILT = math.radians(12.0)  # the telescope leans toward the slit, so the starlight comes from the upper left
ZAX, ZFLOOR = 18.5, 10.6  # the elevation axis and the azimuth floor above the platform
Z_ROOM = -6.5  # the Coude room's beam level; the room spans -9 to -4
LAB_X0, LAB_LEN, LAB_W = 48.0, 20.0, 10.7
CAM_POS, CAM_LOOK = (-2.0, -98.0, 54.0), (21.0, 0.0, 6.0)  # above and a little to the left, 25 degrees down


def build(samples, W, H):
    import bpy
    import bmesh
    from mathutils import Matrix, Vector
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
    if os.environ.get('CYCLES_DEVICE') == 'GPU':
        pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'CUDA'; pr.get_devices()
        for dv in pr.devices:
            dv.use = dv.type == 'CUDA'
        sc.cycles.device = 'GPU'; sc.cycles.denoising_use_gpu = True
    sc.render.resolution_x, sc.render.resolution_y = W, H; sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
    sc.cycles.volume_step_rate = 2.0; sc.cycles.volume_bounces = 1

    def principled(name, base, metal=0.0, rough=0.5, spec=0.5, aniso=0.0):
        mt = bpy.data.materials.new(name); mt.use_nodes = True; b = mt.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = (*base, 1); b.inputs['Metallic'].default_value = metal
        b.inputs['Roughness'].default_value = rough; b.inputs['Specular IOR Level'].default_value = spec
        b.inputs['Anisotropic'].default_value = aniso
        return mt

    def emissive(name, color, strength, volume=False):
        mt = bpy.data.materials.new(name); mt.use_nodes = True; nt = mt.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
        e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (*color, 1); e.inputs['Strength'].default_value = strength
        out = nt.nodes['Material Output']
        nt.links.new(e.outputs['Emission'], out.inputs['Volume'] if volume else out.inputs['Surface'])
        return mt

    CONCRETE = principled('concrete', (0.40, 0.385, 0.36), 0.0, 0.9, 0.15)
    PAVING = principled('paving', (0.15, 0.147, 0.14), 0.0, 0.9, 0.1)
    ROCK = principled('rock', (0.025, 0.023, 0.021), 0.0, 0.95, 0.04)
    ALU = principled('alu', (0.80, 0.80, 0.82), 1.0, 0.35)
    STRUCT = principled('struct', (0.42, 0.43, 0.45), 1.0, 0.55)
    STEEL = principled('steel', (0.80, 0.80, 0.82), 0.6, 0.5, 0.5, 0.7)
    DARK = principled('dark', (0.03, 0.03, 0.034), 0.0, 0.85, 0.1)
    WHITE = principled('white', (0.72, 0.72, 0.70), 0.0, 0.7, 0.2)
    MIRROR = principled('mirror', (0.96, 0.96, 0.98), 1.0, 0.03)
    GLASS = bpy.data.materials.new('glass'); GLASS.use_nodes = True; g = GLASS.node_tree.nodes['Principled BSDF']
    g.inputs['Base Color'].default_value = (0.85, 0.93, 0.95, 1); g.inputs['Transmission Weight'].default_value = 1.0
    g.inputs['Roughness'].default_value = 0.06; g.inputs['IOR'].default_value = 1.5
    BEAM = emissive('beam', AMBER, 1.7)
    BEAMV = emissive('beamv', AMBER, 0.03, volume=True)
    FLOOR = principled('floor', (0.006, 0.007, 0.009), 0.6, 0.22)

    # the cutter: everything at y < 0 is removed from the solids it is applied to
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -250.0 + 0.0137, 0)); cutter = bpy.context.object
    cutter.scale = (900, 500, 900); cutter.hide_render = True; cutter.display_type = 'WIRE'; cutter.name = 'cutter'

    def make(name, bm, mat, cut=True, holes=()):
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); ob.data.materials.append(mat)
        for i, h in enumerate(holes):
            md = ob.modifiers.new('hole%d' % i, 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.solver = 'EXACT'; md.object = h
        if cut:
            md = ob.modifiers.new('cut', 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.solver = 'EXACT'; md.object = cutter
        return ob

    def hole(name, bm):
        ob = make(name, bm, DARK, cut=False); ob.hide_render = True; ob.display_type = 'WIRE'; return ob

    def cyl(bm, p0, p1, r, seg=48, phase=0.0):
        """A closed cylinder from p0 to p1."""
        p0, p1 = Vector(p0), Vector(p1); a = p1 - p0; L = a.length
        q = a.to_track_quat('Z', 'Y'); M = Matrix.Translation((p0 + p1) / 2) @ q.to_matrix().to_4x4() @ Matrix.Rotation(phase, 4, 'Z')
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r, radius2=r, depth=L, matrix=M)
        return bm

    def cone(bm, p0, p1, r0, r1, seg=48):
        p0, p1 = Vector(p0), Vector(p1); a = p1 - p0; L = a.length
        q = a.to_track_quat('Z', 'Y'); M = Matrix.Translation((p0 + p1) / 2) @ q.to_matrix().to_4x4()
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r0, radius2=max(r1, 0.004), depth=L, matrix=M)
        return bm

    def box(bm, c, axes, half):
        """A closed box centred on c with edges along the (unit) axes and the given half-extents."""
        c = Vector(c); ax = [Vector(a).normalized() * h for a, h in zip(axes, half)]
        P = {}
        for i in (-1, 1):
            for j in (-1, 1):
                for k in (-1, 1):
                    P[(i, j, k)] = bm.verts.new(c + i * ax[0] + j * ax[1] + k * ax[2])
        faces = [[(1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)], [(-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1)],
                 [(-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1)], [(-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)],
                 [(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)], [(-1, -1, -1), (-1, 1, -1), (1, 1, -1), (1, -1, -1)]]
        for f in faces:
            bm.faces.new([P[v] for v in f])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        return bm

    def abox(bm, lo, hi):
        lo, hi = Vector(lo), Vector(hi)
        return box(bm, (lo + hi) / 2, ((1, 0, 0), (0, 1, 0), (0, 0, 1)), ((hi - lo) / 2)[:])

    def prism(bm, outline, z0, z1):
        """A closed prism over a counter-clockwise outline."""
        k = len(outline)
        if sum(outline[i][0] * outline[(i + 1) % k][1] - outline[(i + 1) % k][0] * outline[i][1] for i in range(k)) < 0:
            outline = outline[::-1]
        lo = [bm.verts.new((x, y, z0)) for x, y in outline]; hi = [bm.verts.new((x, y, z1)) for x, y in outline]
        bm.faces.new(lo[::-1]); bm.faces.new(hi)
        for i in range(k):
            j = (i + 1) % k; bm.faces.new([lo[i], lo[j], hi[j], hi[i]])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        return bm

    def ring(r, k=48, phase=0.0):
        return [(r * math.cos(2 * math.pi * i / k + phase), r * math.sin(2 * math.pi * i / k + phase)) for i in range(k)]

    # ------------------------------------------------------------------ telescope frame
    d = Vector((-math.sin(TILT), 0.0, math.cos(TILT)))  # the optical axis, toward the sky
    lat = Vector((0.0, 1.0, 0.0))  # the elevation axis
    e1 = d.cross(lat)
    o = Vector((0.0, 0.0, ZAX))  # the crossing of the axes, where the tertiary sits
    m1 = o - d * 2.0  # the primary's vertex
    m2 = o + d * 10.4  # the secondary, 12.4 m from the primary
    R1 = 28.7  # the primary's curvature radius, from its f/1.75 focal length of 14.35 m
    nas = o + lat * 5.0  # the Nasmyth B fold, inside the fork arm's reach
    zc = ZFLOOR + 2.3  # the Coude train's crossing just above the fork base
    m5 = Vector((0.0, 5.0, zc)); m6 = Vector((0.0, 0.0, zc)); m7 = Vector((0.0, 0.0, Z_ROOM))
    vessel_c = Vector((LAB_X0 + 8.0, 0.0, -7.0)); vessel_r, vessel_l = 1.0, 3.6
    beam_end = Vector((vessel_c.x - vessel_l / 2, 0.0, Z_ROOM))

    # ------------------------------------------------------------------ ground: paving, rock, cavities
    make('floor', abox(bmesh.new(), (-400, -400, -13.8), (400, 400, -13.5)), FLOOR, cut=False)
    cav = [hole('room', cyl(bmesh.new(), (0, 0, -9.0), (0, 0, -4.0), 4.25)),
           hole('passage', cyl(bmesh.new(), (0, 0, -4.5), (0, 0, 0.6), 1.2, phase=0.05)),
           hole('duct', cyl(bmesh.new(), (3.0, 0, Z_ROOM), (LAB_X0 + 0.5, 0, Z_ROOM), 1.1, phase=0.05)),
           hole('lab', abox(bmesh.new(), (LAB_X0, -LAB_W / 2, -9.5), (LAB_X0 + LAB_LEN, LAB_W / 2, -4.5)))]
    make('rock', abox(bmesh.new(), (-45, -30, -13.48), (95, 60, 0.0)), ROCK, holes=cav)
    make('paving', abox(bmesh.new(), (-45, -30, 0.0), (95, 60, 0.3)), PAVING, holes=cav[1:2])
    # the rooms are lined: the Coude room in concrete, the laboratory in white, with a floor
    make('room_wall', cyl(bmesh.new(), (0, 0, -9.0), (0, 0, -4.0), 4.25, phase=0.03), CONCRETE,
         holes=[hole('room_in', cyl(bmesh.new(), (0, 0, -8.7), (0, 0, -4.3), 3.95, phase=0.03)), cav[1], cav[2]])
    make('lab_wall', abox(bmesh.new(), (LAB_X0, -LAB_W / 2, -9.5), (LAB_X0 + LAB_LEN, LAB_W / 2, -4.5)), WHITE,
         holes=[hole('lab_in', abox(bmesh.new(), (LAB_X0 + 0.3, -LAB_W / 2 + 0.3, -9.2), (LAB_X0 + LAB_LEN - 0.3, LAB_W / 2 - 0.3, -4.8))), cav[2]])
    make('lab_light', abox(bmesh.new(), (LAB_X0 + 2.0, -0.5, -4.86), (LAB_X0 + LAB_LEN - 2.0, 0.5, -4.80)), emissive('lablight', (0.80, 0.88, 1.0), 1.6), cut=False)
    make('lab_floor', abox(bmesh.new(), (LAB_X0 + 0.3, -LAB_W / 2 + 0.3, -9.2), (LAB_X0 + LAB_LEN - 0.3, LAB_W / 2 - 0.3, -9.1)), PAVING)

    # ------------------------------------------------------------------ the enclosure, open for the night
    facing = math.pi  # the flat front and the slit toward -x, where the telescope leans
    rotz = lambda pts: [(x * math.cos(facing) - y * math.sin(facing), x * math.sin(facing) + y * math.cos(facing)) for x, y in pts]
    make('plinth', prism(bmesh.new(), ring(12.6, 48, 0.03), 0.3, 2.4), DARK, holes=[hole('plinth_in', prism(bmesh.new(), ring(11.6, 48, 0.03), -1, 3))])
    make('stilts', prism(bmesh.new(), ring(14.2, 48, 0.03), 2.4, 3.0), DARK, holes=[hole('stilts_in', prism(bmesh.new(), ring(11.6, 48, 0.03), 2, 4))])
    make('drum', prism(bmesh.new(), ring(13.6, 48, 0.03), 3.0, 10.0), CONCRETE, holes=[hole('drum_in', prism(bmesh.new(), ring(13.0, 48, 0.03), 2, 11))])
    make('band', prism(bmesh.new(), ring(13.68, 48, 0.03), 5.6, 6.8), DARK, holes=[hole('band_in', prism(bmesh.new(), ring(13.6, 48, 0.03), 5, 7))])
    up = []
    for i in range(20):
        a_ = 2 * math.pi * (i + 0.5) / 20
        x, y = 13.6 * math.cos(a_), 13.6 * math.sin(a_)
        up.append((max(-12.0, min(12.0, x)), y))
    up = [q for i, q in enumerate(up) if i == 0 or abs(q[0] - up[i - 1][0]) + abs(q[1] - up[i - 1][1]) > 1e-6]
    inner = [(max(-11.6, min(11.6, x * 13.2 / 13.6)), y * 13.2 / 13.6) for x, y in up]
    hs = 4.75
    slit_cuts = [hole('shell_in', prism(bmesh.new(), rotz(inner), 9.9, 28.6)),
                 hole('slit_front', abox(bmesh.new(), (-13.0, -hs, 19.0), (-10.5, hs, 30.0))),
                 hole('slit_roof', abox(bmesh.new(), (-13.0, -hs, 28.0), (10.0, hs, 30.0)))]
    make('shell', prism(bmesh.new(), rotz(up), 10.0, 29.0), ALU, holes=slit_cuts)

    # ------------------------------------------------------------------ pier, azimuth floor, fork
    make('pier', cyl(bmesh.new(), (0, 0, 0.3), (0, 0, ZFLOOR), 7.2, phase=0.03), CONCRETE,
         holes=[hole('pier_in', cyl(bmesh.new(), (0, 0, -1), (0, 0, ZFLOOR - 0.6), 6.4, phase=0.03))])
    make('azfloor', cyl(bmesh.new(), (0, 0, ZFLOOR - 0.6), (0, 0, ZFLOOR), 7.2, phase=0.03), STRUCT,
         holes=[hole('az_hole', cyl(bmesh.new(), (0, 0, ZFLOOR - 2), (0, 0, ZFLOOR + 2), 1.0, phase=0.05))])
    for sg in (1, -1):  # the fork base as two blocks, the Coude passage between them
        make('forkbase', box(bmesh.new(), Vector((0, sg * 4.2, ZFLOOR + 0.8)), (e1, lat, d), (2.6, 3.2, 0.8)), STRUCT)
        make('yoke', box(bmesh.new(), Vector((0, sg * 6.6, (ZFLOOR + ZAX) / 2 + 0.6)), ((1, 0, 0), lat, (0, 0, 1)), (2.6, 0.8, (ZAX - ZFLOOR) / 2 + 0.6)), STRUCT)
        make('nasplat', box(bmesh.new(), o + lat * sg * 9.0 - Vector((0, 0, 2.6)), ((1, 0, 0), lat, (0, 0, 1)), (3.2, 1.6, 0.25)), CONCRETE)
        make('nasinst', box(bmesh.new(), o + lat * sg * 9.0 - Vector((0, 0, 1.3)), ((1, 0, 0), lat, (0, 0, 1)), (1.6, 1.2, 1.05)), WHITE)
    make('elaxis', cyl(bmesh.new(), o - lat * 7.6, o + lat * 7.6, 0.7, 24), STRUCT)

    # ------------------------------------------------------------------ the optics
    def meniscus(half=True):
        """The primary: a concave meniscus of radius 4.1 m with a 0.5 m central hole, thickness 0.177 m, top
        surface a sphere of radius R1, in the telescope frame; only the y >= 0 half when half is set."""
        bm = bmesh.new()
        nr, nt = 14, 48
        rs = np.linspace(0.5, 4.1, nr + 1)
        ths = np.linspace(0, math.pi, nt // 2 + 1) if half else np.linspace(0, 2 * math.pi, nt, endpoint=False)
        sag = lambda r: r * r / (2 * R1)
        M = Matrix((e1, lat, d)).transposed().to_4x4(); M.translation = m1
        top, bot = [], []
        for r in rs:
            top.append([bm.verts.new(M @ Vector((r * math.cos(t), r * math.sin(t), sag(r)))) for t in ths])
            bot.append([bm.verts.new(M @ Vector((r * math.cos(t), r * math.sin(t), sag(r) - 0.177))) for t in ths])
        nth = len(ths)
        for i in range(nr):
            for j in range(nth if not half else nth - 1):
                jn = (j + 1) % nth
                bm.faces.new([top[i][j], top[i][jn], top[i + 1][jn], top[i + 1][j]])
                bm.faces.new([bot[i][j], bot[i + 1][j], bot[i + 1][jn], bot[i][jn]])
        for j in range(nth if not half else nth - 1):
            jn = (j + 1) % nth
            bm.faces.new([top[-1][j], bot[-1][j], bot[-1][jn], top[-1][jn]])  # the rim
            bm.faces.new([top[0][j], top[0][jn], bot[0][jn], bot[0][j]])  # the hole's wall
        if half:
            for j in (0, nth - 1):  # the cut faces
                bm.faces.new([top[i][j] for i in range(nr + 1)] + [bot[i][j] for i in range(nr, -1, -1)])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        return bm

    def coat():
        bm = bmesh.new(); nr, nt = 14, 48
        rs = np.linspace(0.5, 4.1, nr + 1); ths = np.linspace(0, math.pi, nt // 2 + 1)
        M = Matrix((e1, lat, d)).transposed().to_4x4(); M.translation = m1
        top = [[bm.verts.new(M @ Vector((r * math.cos(t), r * math.sin(t), r * r / (2 * R1) + 0.004))) for t in ths] for r in rs]
        for i in range(nr):
            for j in range(len(ths) - 1):
                bm.faces.new([top[i][j], top[i][j + 1], top[i + 1][j + 1], top[i + 1][j]])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        return bm
    make('m1_glass', meniscus(), GLASS, cut=False)
    make('m1_face', coat(), MIRROR, cut=False)
    make('cell', cyl(bmesh.new(), m1 - d * 1.5, m1 - d * 0.1, 4.7, phase=0.03), STRUCT, holes=[hole('cell_in', cyl(bmesh.new(), m1 - d * 1.2, m1 + d * 0.5, 4.2, phase=0.03))])
    make('m2_ring', cyl(bmesh.new(), m2 - d * 0.5, m2 + d * 0.5, 1.7, 24, phase=0.03), STRUCT, holes=[hole('m2_in', cyl(bmesh.new(), m2 - d, m2 + d, 1.5, 24, phase=0.03))])
    make('m2', cyl(bmesh.new(), m2, m2 + d * 0.12, 0.56, 32, phase=0.03), MIRROR)  # the secondary, 1.12 m, faces the primary
    make('m2_back', cyl(bmesh.new(), m2 + d * 0.12, m2 + d * 0.6, 0.62, 32, phase=0.03), DARK)
    for i in range(4):  # the spider
        a_ = math.pi / 4 + i * math.pi / 2
        make('vane', cyl(bmesh.new(), m2 + d * 0.3, m2 + d * 0.3 + 1.6 * (math.cos(a_) * lat + math.sin(a_) * e1), 0.05, 8), STRUCT)
    for i in range(8):  # the Serrurier truss
        a0 = 2 * math.pi * i / 8; a1 = a0 + (math.pi / 4 if i % 2 == 0 else -math.pi / 4)
        q0 = m1 - d * 0.8 + 4.5 * (math.cos(a0) * lat + math.sin(a0) * e1); q1 = m2 + 1.6 * (math.cos(a1) * lat + math.sin(a1) * e1)
        make('truss', cyl(bmesh.new(), q0, q1, 0.22, 10), STRUCT)

    def flat(name, c, n, r, thick=0.06):
        n = Vector(n).normalized()
        return make(name, cyl(bmesh.new(), c - n * thick, c + n * thick, r, 32, phase=0.05), MIRROR)
    flat('m3', o, d + lat, 0.6)  # the tertiary: down the tube to the elevation axis
    flat('m4', nas, lat + Vector((0, 0, 1)), 0.3)  # Nasmyth B: down the fork arm
    flat('m5', m5, Vector((0, 0, 1)) + lat, 0.3)  # to the azimuth axis
    flat('m6', m6, -lat + Vector((0, 0, 1)), 0.3)  # down the pier
    flat('m7', m7, Vector((0, 0, 1)) + Vector((-1, 0, 0)), 0.3)  # along the duct
    for p in (nas, m5, m6):  # the mirrors' mounts
        make('mount', box(bmesh.new(), p - Vector((0, 0, 0.5)), ((1, 0, 0), (0, 1, 0), (0, 0, 1)), (0.2, 0.2, 0.5)), DARK)

    # ------------------------------------------------------------------ ESPRESSO
    ax = Vector((1, 0, 0))
    make('vessel', cyl(bmesh.new(), vessel_c - ax * vessel_l / 2, vessel_c + ax * vessel_l / 2, vessel_r, 64, phase=0.03), STEEL)
    for sx in (-1, 1):
        make('vessel_leg', abox(bmesh.new(), (vessel_c.x + sx * 1.2 - 0.25, -0.8, -9.5), (vessel_c.x + sx * 1.2 + 0.25, 0.8, vessel_c.z - 0.6)), DARK)
    make('frontend', abox(bmesh.new(), (beam_end.x - 1.4, -0.5, Z_ROOM - 0.5), (beam_end.x - 0.2, 0.5, Z_ROOM + 0.5)), DARK)
    make('bench', abox(bmesh.new(), (beam_end.x - 1.6, -0.7, -9.5), (beam_end.x, 0.7, Z_ROOM - 0.5)), DARK)

    # ------------------------------------------------------------------ the beam
    sky = m1 + d * 22.0
    make('beam_sky', cyl(bmesh.new(), m1 + d * 0.05, sky, 4.1, 48, phase=0.03), BEAMV)
    make('beam_12', cone(bmesh.new(), m1 + d * 0.05, m2, 4.1, 0.56), BEAMV)
    make('beam_23', cone(bmesh.new(), m2, o, 0.56, 0.2), BEAM, cut=False)
    make('beam_34', cone(bmesh.new(), o, nas, 0.2, 0.05), BEAM, cut=False)
    for a, b in ((nas, m5), (m5, m6), (m6, m7), (m7, beam_end)):
        make('beam_c', cyl(bmesh.new(), a, b, 0.11, 16), BEAM, cut=False)
    for p in (o, nas, m5, m6, m7):  # a small glow at each fold
        make('fold', cyl(bmesh.new(), p - Vector((0, 0, 0.14)), p + Vector((0, 0, 0.14)), 0.14, 12), BEAM, cut=False)

    # ------------------------------------------------------------------ light, world, camera
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.0035, 0.004, 0.006, 1)
    ld = bpy.data.lights.new('key', 'AREA'); ld.shape = 'RECTANGLE'; ld.size = 40.0; ld.size_y = 40.0; ld.energy = 2.2e5; ld.color = (0.78, 0.85, 1.0)
    lo = bpy.data.objects.new('key', ld); bpy.context.collection.objects.link(lo); lo.location = (-30.0, -90.0, 80.0)
    lo.rotation_euler = (Vector((20.0, 0.0, 8.0)) - Vector(lo.location)).to_track_quat('-Z', 'Y').to_euler()
    cd = bpy.data.cameras.new('cam'); cd.lens = 42.0; cd.sensor_width = 36
    cd.dof.use_dof = True; cd.dof.focus_distance = (Vector(CAM_LOOK) - Vector(CAM_POS)).length; cd.dof.aperture_fstop = 4.0
    cam = bpy.data.objects.new('cam', cd); bpy.context.collection.objects.link(cam); sc.camera = cam
    cam.location = CAM_POS
    cam.rotation_euler = (Vector(CAM_LOOK) - Vector(cam.location)).to_track_quat('-Z', 'Y').to_euler()
    sc.use_nodes = True; ct = sc.node_tree; rl = ct.nodes['Render Layers']; comp = ct.nodes['Composite']
    g = ct.nodes.new('CompositorNodeGlare'); g.glare_type = 'FOG_GLOW'; g.quality = 'HIGH'; g.size = 7; g.threshold = 0.8; g.mix = -0.75
    ct.links.new(rl.outputs['Image'], g.inputs['Image']); ct.links.new(g.outputs['Image'], comp.inputs['Image'])
    return sc


if __name__ == '__main__':
    d, mode = sys.argv[1], sys.argv[2]
    os.makedirs(d, exist_ok=True)
    import bpy
    rest = sys.argv[3:]
    if mode == 'test':
        samples = int(rest[0]) if rest else 24
        W, H = (int(rest[1]), int(rest[2])) if len(rest) > 2 else (480, 320)
        sc = build(samples, W, H); out = os.path.join(d, 'lp_test_%dx%d.png' % (W, H))
    elif mode == 'still':
        samples = int(rest[0]) if rest else 48
        W, H = (int(rest[1]), int(rest[2])) if len(rest) > 2 else (1600, 900)
        sc = build(samples, W, H); out = os.path.join(d, 'lightpath_still.png')
    else:
        sys.exit('mode must be test or still')
    sc.render.filepath = out; bpy.ops.render.render(write_still=True); print('wrote', out)
    if mode == 'still':
        from PIL import Image
        Image.open(out).convert('RGB').save(os.path.join(d, 'lightpath_still.webp'), quality=82)
