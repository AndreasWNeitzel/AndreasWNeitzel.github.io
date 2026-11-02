"""A small blueprint-style renderer for the site's hero images: triangle meshes rasterised with a z-buffer
(the rasteriser of figures/eso/paranal_render.py), toned by their angle to a fixed light with no cast
shadows, and drawn with silhouette, crease and material edges. Output is RGBA on a transparent ground,
supersampled and pooled, so pages can place it on either theme."""

from __future__ import annotations

import math

import numba as nb
import numpy as np
from scipy.ndimage import maximum_filter


class Mesh:
    def __init__(self):
        self.v: list = []
        self.t: list = []
        self.m: list = []  # material index per triangle
        self.o: list = []  # object index per triangle, for silhouette edges

    def tri(self, a, b, c, mat=0, obj=0):
        n = len(self.v)
        self.v += [a, b, c]
        self.t.append((n, n + 1, n + 2))
        self.m.append(mat)
        self.o.append(obj)

    def quad(self, a, b, c, d, mat=0, obj=0):
        self.tri(a, b, c, mat, obj)
        self.tri(a, c, d, mat, obj)

    def prism(self, outline, z0, z1, mat=0, obj=0, cap=True):
        k = len(outline)
        for i in range(k):
            (x0, y0), (x1, y1) = outline[i], outline[(i + 1) % k]
            self.quad((x0, y0, z0), (x1, y1, z0), (x1, y1, z1), (x0, y0, z1), mat, obj)
        if cap:
            cx = sum(p[0] for p in outline) / k
            cy = sum(p[1] for p in outline) / k
            for z in (z0, z1):
                for i in range(k):
                    (x0, y0), (x1, y1) = outline[i], outline[(i + 1) % k]
                    self.tri((cx, cy, z), (x0, y0, z), (x1, y1, z), mat, obj)

    def box(self, x0, y0, z0, x1, y1, z1, mat=0, obj=0):
        self.prism([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1, mat, obj)


@nb.njit(cache=True)
def raster(sx, sy, sz, tris, w, h, zbuf, ids):
    for t in range(tris.shape[0]):
        i0, i1, i2 = tris[t, 0], tris[t, 1], tris[t, 2]
        if sz[i0] <= 0 or sz[i1] <= 0 or sz[i2] <= 0:
            continue
        x0, y0, x1, y1, x2, y2 = sx[i0], sy[i0], sx[i1], sy[i1], sx[i2], sy[i2]
        area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
        if abs(area) < 1e-12:
            continue
        minx = max(int(math.floor(min(x0, x1, x2))), 0)
        maxx = min(int(math.ceil(max(x0, x1, x2))), w - 1)
        miny = max(int(math.floor(min(y0, y1, y2))), 0)
        maxy = min(int(math.ceil(max(y0, y1, y2))), h - 1)
        if minx > maxx or miny > maxy:
            continue
        iz0, iz1, iz2 = 1.0 / sz[i0], 1.0 / sz[i1], 1.0 / sz[i2]
        for py in range(miny, maxy + 1):
            for px in range(minx, maxx + 1):
                cx, cy = px + 0.5, py + 0.5
                w0 = ((x1 - cx) * (y2 - cy) - (x2 - cx) * (y1 - cy)) / area
                w1 = ((x2 - cx) * (y0 - cy) - (x0 - cx) * (y2 - cy)) / area
                w2 = 1.0 - w0 - w1
                if w0 < -1e-7 or w1 < -1e-7 or w2 < -1e-7:
                    continue
                iz = w0 * iz0 + w1 * iz1 + w2 * iz2
                if iz > zbuf[py, px]:
                    zbuf[py, px] = iz
                    ids[py, px] = t


def render(mesh: Mesh, cam, look, fov_deg, W, H, materials, light=(0.4, -0.6, 0.7), line=(222, 226, 232),
           line_alpha=0.85, ss=3, crease_deg=28.0):
    """materials: list of (rgb tuple 0-255, alpha). Returns an RGBA uint8 array of shape (H, W, 4)."""
    V = np.array(mesh.v, float)
    T = np.array(mesh.t, np.int64)
    M = np.array(mesh.m, np.int64)
    O = np.array(mesh.o, np.int64)
    cam, look = np.array(cam, float), np.array(look, float)
    fwd = look - cam
    fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, [0, 0, 1.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    w, h = W * ss, H * ss
    F = (w / 2) / math.tan(math.radians(fov_deg) / 2)
    q = V - cam
    zc = q @ fwd
    sx = w / 2 + F * (q @ right) / np.maximum(zc, 1e-3)
    sy = h / 2 - F * (q @ up) / np.maximum(zc, 1e-3)
    zbuf = np.zeros((h, w))
    ids = -np.ones((h, w), np.int64)
    raster(sx, sy, zc, T, w, h, zbuf, ids)
    # face normals, oriented towards the camera
    n = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    cen = V[T].mean(1)
    flip = ((cen - cam) * n).sum(1) > 0
    n[flip] *= -1
    L = np.array(light, float)
    L /= np.linalg.norm(L)
    lam = np.clip(n @ L, 0, 1)
    tone = 0.42 + 0.58 * lam
    cols = np.array([m[0] for m in materials], float)
    alph = np.array([m[1] for m in materials], float)
    hit = ids >= 0
    tid = np.where(hit, ids, 0)
    rgb = cols[M[tid]] * tone[tid][..., None]
    a = np.where(hit, alph[M[tid]], 0.0)
    # edges: object or material change, normal crease, depth jump
    def diff(arr):
        d = np.zeros(arr.shape[:2], bool)
        d[:, 1:] |= arr[:, 1:] != arr[:, :-1]
        d[1:, :] |= arr[1:, :] != arr[:-1, :]
        return d
    objmap = np.where(hit, O[tid], -1)
    matmap = np.where(hit, M[tid], -1)
    nm = np.where(hit[..., None], n[tid], 0.0)
    crease = np.zeros(hit.shape, bool)
    cth = math.cos(math.radians(crease_deg))
    dx = (nm[:, 1:] * nm[:, :-1]).sum(-1)
    dy = (nm[1:, :] * nm[:-1, :]).sum(-1)
    crease[:, 1:] |= (dx < cth) & hit[:, 1:] & hit[:, :-1]
    crease[1:, :] |= (dy < cth) & hit[1:, :] & hit[:-1, :]
    edges = diff(objmap) | diff(matmap) | crease
    edges = maximum_filter(edges.astype(float), size=max(1, ss - 1)) > 0
    out = np.zeros((h, w, 4))
    out[..., :3] = rgb
    out[..., 3] = a
    lc = np.array(line, float)
    e = edges.astype(float) * line_alpha
    out[..., :3] = out[..., :3] * (1 - e[..., None]) + lc * e[..., None]
    out[..., 3] = np.maximum(out[..., 3], e)
    # pool the supersampled image, premultiplied
    pre = out[..., :3] * out[..., 3:4]
    pre = pre.reshape(H, ss, W, ss, 3).mean((1, 3))
    al = out[..., 3].reshape(H, ss, W, ss).mean((1, 3))
    rgbp = pre / np.maximum(al, 1e-6)[..., None]
    res = np.dstack([rgbp, al * 255])
    return np.clip(res, 0, 255).astype(np.uint8)
