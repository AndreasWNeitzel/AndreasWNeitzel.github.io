"""The Milky Way drawn on /research/arqueogal/: its components as projected density envelopes,
the real Gaia red giants around the Sun, and the orbit of one red giant, Arcturus.

Frame: heliocentric Galactic Cartesian as in assets/data/mw/giants.json (x toward the Galactic
centre, y toward l = 90 degrees, z toward the north Galactic pole), shifted to the centre:
X = x - R0. The view is from the north side, INC degrees from the disc's axis, turned by AZ degrees
about it, a proper rotation, so the bar and the sense of rotation keep their handedness.

Structural parameters (all real, from the literature):
  R0 = 8.21 kpc, the Sun's distance from the centre, as in the potential below (McMillan 2017,
      MNRAS 465, 76, arXiv:1608.00971; Bland-Hawthorn and Gerhard 2016 give 8.2 +- 0.1 kpc).
  Thin disc: scale length 2.6 kpc, scale height 0.30 kpc; thick disc: scale length 2.0 kpc,
      scale height 0.90 kpc (Bland-Hawthorn and Gerhard 2016, ARA&A 54, 529,
      doi:10.1146/annurev-astro-081915-023441, arXiv:1602.07702, their recommended values).
  Bar: half-length 5.0 kpc (Wegg, Gerhard and Portail 2015, MNRAS 450, 4050,
      arXiv:1504.01401) at 27 degrees to the Sun-centre line with its near end at positive
      longitude, and the box/peanut bulge with axis ratios 1 : 0.63 : 0.26 (Wegg and Gerhard 2013,
      MNRAS 435, 1874, arXiv:1308.0593). The bulge's half-length (2.0 kpc) and the long bar's
      width and thickness (1.0 and 0.3 kpc) are chosen for legibility, not measured.
  Stellar halo: density falling as r^-2.77 with flattening q = 0.64 (Juric et al. 2008, ApJ 673,
      864, arXiv:astro-ph/0510520), softened inside 1 kpc so the centre stays finite.
The discs are softened the same way (radius sqrt(R^2 + 1 kpc^2)), since the bulge replaces their
central cusp. Each envelope is a set of nested contours of that component's projected density, at
the levels where its major axis reaches the radii in REACH; the shapes follow from the parameters,
the levels are chosen for legibility.

The orbit: Arcturus (alpha Bootis, a K1.5 III red giant 11 pc from the Sun). Position and
parallax 88.83 mas from van Leeuwen 2007 (A&A 474, 653, arXiv:0708.1752), proper motion
(-1093.45, -1999.40) mas/yr from the Hipparcos catalogue (Perryman et al. 1997, A&A 323, L49),
radial velocity -5.19 km/s (Massarotti et al. 2008, AJ 135, 209). Integrated for ORBIT_GYR in the
McMillan 2017 potential with galpy (Bovy 2015, ApJS 216, 29, arXiv:1412.3451), solar motion of
Schoenrich, Binney and Dehnen 2010.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
R0 = 8.21
THIN = (2.6, 0.30)
THICK = (2.0, 0.90)
BAR_ANGLE = 27.0
HALO_N, HALO_Q = 2.77, 0.64
REACH = {"halo": (19.0, 15.5, 12.0), "thick": (11.5, 9.0, 6.5), "thin": (15.0, 12.0, 9.0, 6.0, 3.5)}
INC, AZ = 72.0, 52.0
ORBIT_GYR = 0.8


def to_view(X, Y, Z, inc=INC, az=AZ):
    """Galactocentric (X, Y, Z) in kpc to the image plane (u right, v up) and depth (toward the
    viewer), seen from the north side, by a proper rotation so the Galaxy keeps its handedness."""
    X, Y, Z = np.asarray(X, float), np.asarray(Y, float), np.asarray(Z, float)
    c, s_ = math.cos(math.radians(az)), math.sin(math.radians(az))
    Xp = X * c - Y * s_
    Yp = X * s_ + Y * c
    i = math.radians(inc)
    return Xp, Yp * math.cos(i) + Z * math.sin(i), -Yp * math.sin(i) + Z * math.cos(i)


def from_view(u, v, depth, inc=INC, az=AZ):
    i = math.radians(inc)
    Yp = v * math.cos(i) - depth * math.sin(i)
    Z = v * math.sin(i) + depth * math.cos(i)
    c, s_ = math.cos(math.radians(az)), math.sin(math.radians(az))
    return u * c + Yp * s_, -u * s_ + Yp * c, Z


def rho_disc(X, Y, Z, hR, hz):
    return np.exp(-np.sqrt(X**2 + Y**2 + 1.0) / hR - np.abs(Z) / hz)


def rho_halo(X, Y, Z):
    return (X**2 + Y**2 + (Z / HALO_Q) ** 2 + 1.0) ** (-HALO_N / 2)


def bar_axes(X, Y):
    """Distance along and across the bar, whose near end points to (-cos 27, sin 27) in the
    centre-shifted frame (X toward the Galactic centre's far side, Y toward l = 90 degrees)."""
    a = math.radians(BAR_ANGLE)
    ex, ey = -math.cos(a), math.sin(a)
    return X * ex + Y * ey, -X * ey + Y * ex


def bar_field(X, Y, Z):
    """Below 1 inside the union of the box/peanut bulge and the long bar."""
    xb, yb = bar_axes(X, Y)
    bulge = (xb / 2.0) ** 2 + (yb / (2.0 * 0.63)) ** 2 + (Z / (2.0 * 0.26)) ** 2
    long_bar = (np.abs(xb) / 5.0) ** 4 + (yb / 1.0) ** 2 + (Z / 0.3) ** 2
    return np.minimum(bulge, long_bar)


def project(fn, extent=(24.0, 16.0), step=0.2, depth=32.0, dstep=0.25, mode="sum"):
    """Integrate fn along the line of sight, or take its minimum for mode="min"."""
    u = np.arange(-extent[0], extent[0] + step, step)
    v = np.arange(-extent[1], extent[1] + step, step)
    U, V = np.meshgrid(u, v)
    acc = np.zeros_like(U) if mode == "sum" else np.full_like(U, np.inf)
    for d in np.arange(-depth, depth + dstep, dstep):
        val = fn(*from_view(U, V, np.full_like(U, d)))
        acc = acc + val if mode == "sum" else np.minimum(acc, val)
    return u, v, acc


def envelopes():
    """Nested contours of each component's projected density, as lists of (u, v) arrays in kpc
    per level, outermost first. The bar is its single outline."""
    from contourpy import contour_generator

    out = {}
    comps = {
        "halo": rho_halo,
        "thick": lambda X, Y, Z: rho_disc(X, Y, Z, *THICK),
        "thin": lambda X, Y, Z: rho_disc(X, Y, Z, *THIN),
    }
    for name, fn in comps.items():
        u, v, S = project(fn)
        gen = contour_generator(u, v, S)
        major = S[int(np.argmin(np.abs(v)))]
        levels = []
        for reach in REACH[name]:
            lines = gen.lines(float(np.interp(reach, u, major)))
            levels.append([np.asarray(ln) for ln in lines if len(ln) > 8])
        out[name] = levels
    u, v, M = project(bar_field, extent=(7.0, 4.0), step=0.05, depth=8.0, dstep=0.05, mode="min")
    out["bar"] = [[np.asarray(ln) for ln in contour_generator(u, v, M).lines(1.0)]]
    return out


def rings(radii=(5.0, 10.0, 15.0), n=180):
    t = np.linspace(0, 2 * np.pi, n + 1)
    res = {}
    for r in radii:
        u, v, d = to_view(r * np.cos(t), r * np.sin(t), 0 * t)
        res[r] = (u, v, d)
    return res


def giants(n_keep: int, seed=20261102):
    meta = json.loads((ROOT / "assets/data/mw/giants.json").read_text())
    raw = (ROOT / "assets/data/mw" / meta["binary"]).read_bytes()
    n = meta["n"]
    col = {c["field"]: c for c in meta["layout"]}
    def arr(f):
        return np.frombuffer(raw, dtype="<f2", count=n, offset=col[f]["offset"]).astype(float)
    x, y, z = arr("x"), arr("y"), arr("z")
    idx = np.random.default_rng(seed).choice(n, size=n_keep, replace=False)
    return to_view(x[idx] - R0, y[idx], z[idx])


def arcturus_orbit():
    from galpy.orbit import Orbit
    from galpy.potential.mwpotentials import McMillan17
    from astropy import units as un

    o = Orbit([213.91530, 19.18241, 1 / 88.83, -1093.45, -1999.40, -5.19], radec=True,
              ro=8.21, vo=233.1, zo=0.0208, solarmotion="schoenrich")
    ts = np.linspace(0, ORBIT_GYR, 1600) * un.Gyr
    o.integrate(ts, McMillan17, method="dop853_c")
    hx, hy, hz = o.helioX(ts), o.helioY(ts), o.helioZ(ts)
    X, Y, Z = np.asarray(hx) - R0, np.asarray(hy), np.asarray(hz)
    return X, Y, Z
