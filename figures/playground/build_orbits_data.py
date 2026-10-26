#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "astroquery>=0.4.10",
#     "astropy>=6.0",
#     "galpy>=1.10",
#     "numpy>=1.26",
#     "scipy>=1.11",
# ]
# ///
"""Build the data file for the Orbits playground (/playground/orbits/).

The playground integrates two problems in the browser with the same code: satellites
around a point-mass Earth (a Molniya constellation and a geostationary satellite, with
ground-station visibility) and real stars in the MWPotential2014 model of the Milky Way.
This script collects every number the page prints, with its source, and writes two files
to assets/data/playground/:

    orbits.json       what the page loads: Earth constants, orbital elements, stations,
                      potential parameters, solar parameters, the stars with Gaia DR3
                      values and Galactocentric coordinates, and reference orbit
                      quantities from galpy for a cross-check
    orbits.meta.json  provenance: services, dates, the ADQL query, the identifier
                      resolution, dropped candidates with reasons, references, versions

Sources
    Gaia DR3 astrometry and radial velocities come from the Gaia archive TAP service at
    ESA (gaiadr3.gaia_source), selected by source_id. The source_ids are resolved from
    the stars' common names through SIMBAD and recorded. Galactocentric coordinates use
    astropy with the solar parameters listed in SOLAR. Reference orbit quantities come
    from galpy's own MWPotential2014, integrated for 10 Gyr.

Usage
    uv run figures/playground/build_orbits_data.py [--refresh]

The Gaia and SIMBAD answers are cached next to this script's output in the directory
given by --raw-dir (default: a sibling of the repository) and reused; --refresh queries
the services again.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "assets" / "data" / "playground"

ESA_TAP = "https://gea.esac.esa.int/tap-server/tap"
MC_SAMPLES = 20_000
SEED = 20261026

# ----------------------------------------------------------------------------- Earth
# Constants of the Earth problem, each with its source.
EARTH = {
    "gm_km3_s2": 398600.4418,
    "gm_source": "IERS Conventions (2010), Petit and Luzum (eds.), IERS Technical Note 36, Table 1.1: GM_E = 3.986004418 x 10^14 m^3 s^-2; the NSSDC Earth fact sheet gives 0.39860 x 10^6 km^3 s^-2",
    "radius_km": 6378.137,
    "radius_source": "NSSDC Earth fact sheet, equatorial radius 6378.137 km (also the WGS 84 semi-major axis); the Earth is treated as a sphere of this radius",
    "rotation_rate_rad_s": 7.292115e-5,
    "rotation_source": "IERS Conventions (2010), Table 1.1, nominal mean angular velocity of the Earth 7.292115 x 10^-5 rad s^-1; the NSSDC fact sheet gives the sidereal rotation period as 23.9345 h",
}
EARTH["sidereal_day_s"] = 2 * math.pi / EARTH["rotation_rate_rad_s"]

MOLNIYA = {
    "period_s": EARTH["sidereal_day_s"] / 2,
    "period_note": "half a sidereal day (semi-synchronous), so the ground track repeats daily; Kolyuka et al. (2009) give 718 min, the NASA catalogue 12 h",
    "eccentricity": 0.74,
    "eccentricity_source": "Kidder and Vonder Haar (1990), J. Atmos. Oceanic Technol. 7, 517, as relayed by the Molniya orbit article of Wikipedia (0.74, 'approximately 0.737'); the NASA Earth Observatory catalogue gives 0.722 for the orbit type. Operational Molniya satellites varied between these values",
    "inclination_deg": 63.4,
    "inclination_source": "NASA Earth Observatory, Catalog of Earth Satellite Orbits (63.4 degrees); Kidder and Vonder Haar (1990). At this critical inclination the Earth's oblateness does not rotate the line of apsides, which keeps the apogee over the northern hemisphere",
    "argument_of_perigee_deg": 270.0,
    "argument_of_perigee_source": "the perigee at the southernmost point of the orbit puts the apogee over the northern hemisphere (Kidder and Vonder Haar 1990); 270 degrees is the value listed for the orbit type",
    "constellation": {
        "count": 3,
        "raan_spacing_deg": 120.0,
        "mean_anomaly_spacing_deg": -240.0,
        "apogee_longitude_deg": 37.62,
        "note": "three planes spaced by 120 degrees in the longitude of the ascending node, with mean anomalies spaced by -240 degrees, so one satellite passes apogee every two thirds of a period above the same longitude; the apogee longitude is set to Moscow's, as in the coursework test. The Greenwich meridian lies along the inertial x axis at t = 0",
    },
}
mu = EARTH["gm_km3_s2"]
MOLNIYA["semi_major_axis_km"] = (mu * MOLNIYA["period_s"] ** 2 / (4 * math.pi**2)) ** (1 / 3)
MOLNIYA["perigee_radius_km"] = MOLNIYA["semi_major_axis_km"] * (1 - MOLNIYA["eccentricity"])
MOLNIYA["apogee_radius_km"] = MOLNIYA["semi_major_axis_km"] * (1 + MOLNIYA["eccentricity"])
MOLNIYA["perigee_altitude_km"] = MOLNIYA["perigee_radius_km"] - EARTH["radius_km"]
MOLNIYA["apogee_altitude_km"] = MOLNIYA["apogee_radius_km"] - EARTH["radius_km"]
MOLNIYA["perigee_speed_km_s"] = math.sqrt(mu * (2 / MOLNIYA["perigee_radius_km"] - 1 / MOLNIYA["semi_major_axis_km"]))
MOLNIYA["apogee_speed_km_s"] = math.sqrt(mu * (2 / MOLNIYA["apogee_radius_km"] - 1 / MOLNIYA["semi_major_axis_km"]))
MOLNIYA["derived_note"] = "semi-major axis from Kepler's third law with the period and GM above; radii, altitudes and speeds (vis-viva) follow from it and the eccentricity. Kidder and Vonder Haar (1990) give about 26,600 km, a perigee altitude of about 600 km and an apogee altitude of 39,700 km"

GEO = {
    "period_s": EARTH["sidereal_day_s"],
    "longitude_deg": 0.0,
    "source": "NASA Earth Observatory, Catalog of Earth Satellite Orbits: 42,164 km from the centre of the Earth, about 36,000 km above the surface, one orbit per day; ESA, Types of orbits: altitude 35,786 km, period 23 h 56 min 4 s",
}
GEO["radius_km"] = (mu * GEO["period_s"] ** 2 / (4 * math.pi**2)) ** (1 / 3)
GEO["altitude_km"] = GEO["radius_km"] - EARTH["radius_km"]
GEO["speed_km_s"] = math.sqrt(mu / GEO["radius_km"])

STATIONS = [
    {"id": "porto", "name": "Porto", "short_name": "Porto", "lat_deg": 41.15, "lon_deg": -8.61},
    {"id": "moscow", "name": "Moscow", "short_name": "Moscow", "lat_deg": 55.75, "lon_deg": 37.62},
    {"id": "north", "name": "Polar station", "short_name": "Polar", "lat_deg": 85.0, "lon_deg": 0.0, "adjustable_latitude": [60.0, 90.0],
     "note": "a movable station on the geostationary satellite's own meridian, where the satellite's elevation is highest for that latitude; it starts at 85 degrees north, above the limit of acos(R_E / r_geo) = 81.3 degrees beyond which the geostationary satellite never rises. The coursework placed it at 80 degrees north"},
]

# ----------------------------------------------------------------------------- Galaxy
# MWPotential2014 (Bovy 2015, ApJS 216, 29, Table 1), as implemented in galpy. Each
# component is normalised so that its radial force at R0 in the plane is the stated
# fraction of v0^2 / R0; the fractions sum to 1, so the circular speed at R0 is v0.
POTENTIAL = {
    "name": "MWPotential2014",
    "source": "Bovy (2015), ApJS 216, 29, doi:10.1088/0067-0049/216/2/29, Table 1 and Section 3.5; parameters checked against galpy's definition (galpy.potential.MWPotential2014)",
    "R0_kpc": 8.0,
    "v0_km_s": 220.0,
    "bulge": {"form": "power-law density with exponential cut-off, rho(r) proportional to r^-alpha exp(-(r/rc)^2)", "alpha": 1.8, "rc_kpc": 1.9, "force_fraction_at_R0": 0.05},
    "disc": {"form": "Miyamoto and Nagai (1975) potential", "a_kpc": 3.0, "b_kpc": 0.28, "force_fraction_at_R0": 0.60},
    "halo": {"form": "Navarro, Frenk and White (1997) profile", "a_kpc": 16.0, "force_fraction_at_R0": 0.35},
}

SOLAR = {
    "galcen_distance_kpc": 8.0,
    "z_sun_pc": 20.8,
    "v_sun_km_s": [11.1, 232.24, 7.25],
    "note": "distance from the Sun to the Galactic centre 8.0 kpc and circular speed 220 km/s, the normalisation of MWPotential2014 (Bovy 2015); height of the Sun above the plane 20.8 pc (Bennett and Bovy 2019, MNRAS 482, 1417); solar peculiar motion (U, V, W) = (11.10, 12.24, 7.25) km/s (Schoenrich, Binney and Dehnen 2010, MNRAS 403, 1829), so the Sun's Galactocentric velocity is (11.10, 232.24, 7.25) km/s. Frame: astropy Galactocentric, right-handed, x from the Sun towards the centre, y along Galactic rotation, z towards the north Galactic pole; the Sun sits at x = -8 kpc",
    "distance_note": "distances are 1 / parallax; every selected star has parallax / error above 600. No parallax zero-point correction is applied: the Lindegren et al. (2021) offsets are of order -0.02 mas, 0.1 percent of the smallest parallax here",
}

# Common name, SIMBAD query name, other designation; the Gaia DR3 source_id is resolved
# at run time through SIMBAD and recorded. Order is the order on the page.
STARS = [
    {"name": "61 Virginis", "simbad": "61 Vir", "other": "HD 115617"},
    {"name": "Proxima Centauri", "simbad": "Proxima Cen", "other": "GJ 551"},
    {"name": "Barnard's star", "simbad": "Barnard's star", "other": "GJ 699"},
    {"name": "Lalande 21185", "simbad": "HD 95735", "other": "HD 95735, GJ 411"},
    {"name": "Kapteyn's star", "simbad": "Kapteyn's star", "other": "GJ 191"},
    {"name": "HD 140283", "simbad": "HD 140283", "other": "the metal-poor subgiant"},
]
# Candidates considered and not used, with the reason, so the selection is on record.
DROPPED = [
    {"name": "Arcturus", "reason": "no Gaia DR3 source: brighter than the catalogue's bright limit"},
    {"name": "Alpha Centauri A", "reason": "no Gaia DR3 source: brighter than the catalogue's bright limit"},
    {"name": "Alpha Centauri B", "reason": "no Gaia DR3 source: brighter than the catalogue's bright limit"},
    {"name": "tau Ceti", "reason": "in Gaia DR3 (G = 3.30) but without a radial velocity"},
    {"name": "epsilon Eridani", "reason": "in Gaia DR3 (G = 3.47) but without a radial velocity"},
    {"name": "mu Cassiopeiae", "reason": "RUWE 6.97: the single-star astrometric solution does not fit this binary"},
    {"name": "70 Ophiuchi A", "reason": "RUWE 3.27: the single-star astrometric solution does not fit this binary"},
    {"name": "Groombridge 1830 (HD 103095)", "reason": "not selected; six stars were kept so that the plots stay legible"},
    {"name": "HD 122563", "reason": "not selected; six stars were kept so that the plots stay legible"},
    {"name": "HD 19445", "reason": "not selected; six stars were kept so that the plots stay legible"},
    {"name": "HD 84937", "reason": "not selected; six stars were kept so that the plots stay legible"},
]

GAIA_COLUMNS = [
    "source_id", "ref_epoch", "ra", "dec", "parallax", "parallax_error", "pmra", "pmra_error", "pmdec", "pmdec_error",
    "radial_velocity", "radial_velocity_error", "rv_nb_transits", "rv_template_teff", "grvs_mag",
    "ruwe", "phot_g_mean_mag", "bp_rp",
    "parallax_pmra_corr", "parallax_pmdec_corr", "pmra_pmdec_corr",
]

REFERENCES = {
    "gaia_mission": "Gaia Collaboration, Prusti et al. (2016), A&A 595, A1, doi:10.1051/0004-6361/201629272",
    "gaia_dr3": "Gaia Collaboration, Vallenari et al. (2023), A&A 674, A1, doi:10.1051/0004-6361/202243940",
    "gaia_dr3_astrometry": "Lindegren et al. (2021), A&A 649, A2, doi:10.1051/0004-6361/202039709",
    "gaia_dr3_radial_velocities": "Katz et al. (2023), A&A 674, A5, doi:10.1051/0004-6361/202244220",
    "gaia_credit": "This work has made use of data from the European Space Agency (ESA) mission Gaia (https://www.cosmos.esa.int/gaia), processed by the Gaia Data Processing and Analysis Consortium (DPAC, https://www.cosmos.esa.int/web/gaia/dpac/consortium). Funding for the DPAC has been provided by national institutions, in particular the institutions participating in the Gaia Multilateral Agreement.",
    "gaia_licence": "ESA/Gaia/DPAC, CC BY-SA 3.0 IGO, https://creativecommons.org/licenses/by-sa/3.0/igo/",
    "simbad": "Wenger et al. (2000), A&AS 143, 9, doi:10.1051/aas:2000332 (SIMBAD, CDS Strasbourg), used to resolve common names to Gaia DR3 source_ids",
    "potential": "Bovy (2015), ApJS 216, 29, doi:10.1088/0067-0049/216/2/29, arXiv:1412.3451",
    "miyamoto_nagai": "Miyamoto and Nagai (1975), PASJ 27, 533",
    "nfw": "Navarro, Frenk and White (1997), ApJ 490, 493, doi:10.1086/304888",
    "solar_motion": "Schoenrich, Binney and Dehnen (2010), MNRAS 403, 1829, doi:10.1111/j.1365-2966.2010.16253.x",
    "z_sun": "Bennett and Bovy (2019), MNRAS 482, 1417, doi:10.1093/mnras/sty2813",
    "astropy": "Astropy Collaboration (2022), ApJ 935, 167, doi:10.3847/1538-4357/ac7c74",
    "molniya": "Kidder and Vonder Haar (1990), J. Atmos. Oceanic Technol. 7, 517, doi:10.1175/1520-0426(1990)007<0517:OTUOSI>2.0.CO;2",
    "molniya_period": "Kolyuka et al. (2009), 21st International Symposium on Space Flight Dynamics, Toulouse",
    "nasa_orbits": "NASA Earth Observatory, Catalog of Earth Satellite Orbits, https://science.nasa.gov/earth/earth-observatory/catalog-of-earth-satellite-orbits",
    "esa_orbits": "ESA, Types of orbits, https://www.esa.int/Enabling_Support/Space_Transportation/Types_of_orbits",
    "iers": "Petit and Luzum (eds.) (2010), IERS Conventions (2010), IERS Technical Note 36, Table 1.1",
    "nssdc": "NASA NSSDCA, Earth Fact Sheet, https://nssdc.gsfc.nasa.gov/planetary/factsheet/earthfact.html",
    "coursework": "Computational Astronomy, University of Porto, 2018/19, project 3 (N-body code applied to a Molniya constellation and a geostationary satellite with ground-station visibility)",
}


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve_ids(stars, cache: Path, refresh: bool) -> dict:
    """Gaia DR3 source_id for each star through SIMBAD, cached."""
    if cache.exists() and not refresh:
        return json.loads(cache.read_text())
    from astroquery.simbad import Simbad

    out = {"queried_utc": now(), "ids": {}}
    for s in stars:
        t = Simbad.query_objectids(s["simbad"])
        col = "ID" if t is not None and "ID" in t.colnames else "id"
        ids = [str(x).strip() for x in t[col]] if t is not None else []
        gaia = [i for i in ids if i.startswith("Gaia DR3 ")]
        if len(gaia) != 1:
            sys.exit(f"{s['name']}: SIMBAD lists {len(gaia)} Gaia DR3 identifiers")
        out["ids"][s["name"]] = int(gaia[0].split()[-1])
        print(f"{s['name']}: {gaia[0]}")
    cache.write_text(json.dumps(out, indent=1))
    return out


def fetch_gaia(source_ids, cache: Path, refresh: bool) -> dict:
    """The Gaia DR3 rows, cached as JSON (floats; NaN for nulls)."""
    adql = (
        "SELECT " + ", ".join(GAIA_COLUMNS) + "\nFROM gaiadr3.gaia_source\nWHERE source_id IN (" + ", ".join(str(s) for s in source_ids) + ")"
    )
    if cache.exists() and not refresh:
        data = json.loads(cache.read_text())
        if data["adql"] == adql:
            return data
    from astroquery.gaia import Gaia

    job = Gaia.launch_job(adql)
    table = job.get_results()
    rows = {}
    for r in table:
        row = {}
        for c in GAIA_COLUMNS:
            v = r[c]
            if c == "source_id":
                row[c] = int(v)
            elif hasattr(v, "mask") and bool(np.ma.getmask(v)):
                row[c] = None
            else:
                fv = float(v)
                row[c] = None if not math.isfinite(fv) else fv
        rows[str(row["source_id"])] = row
    data = {"service": ESA_TAP, "queried_utc": now(), "adql": adql, "rows": rows}
    cache.write_text(json.dumps(data, indent=1))
    return data


def galactocentric(row: dict, rng: np.random.Generator) -> dict:
    """Galactocentric position and velocity with Monte Carlo uncertainties."""
    import astropy.units as u
    from astropy.coordinates import CartesianDifferential, Galactocentric, SkyCoord
    from astropy.time import Time

    frame = Galactocentric(
        galcen_distance=SOLAR["galcen_distance_kpc"] * u.kpc,
        z_sun=SOLAR["z_sun_pc"] * u.pc,
        galcen_v_sun=CartesianDifferential(SOLAR["v_sun_km_s"] * u.km / u.s),
    )
    mean = np.array([row["parallax"], row["pmra"], row["pmdec"], row["radial_velocity"]])
    sig = np.array([row["parallax_error"], row["pmra_error"], row["pmdec_error"], row["radial_velocity_error"]])
    corr = np.eye(4)
    corr[0, 1] = corr[1, 0] = row["parallax_pmra_corr"]
    corr[0, 2] = corr[2, 0] = row["parallax_pmdec_corr"]
    corr[1, 2] = corr[2, 1] = row["pmra_pmdec_corr"]
    cov = corr * np.outer(sig, sig)
    samples = rng.multivariate_normal(mean, cov, size=MC_SAMPLES)
    samples = np.vstack([mean, samples])  # row 0 is the catalogue value
    obstime = Time(row["ref_epoch"], format="jyear")
    c = SkyCoord(
        ra=np.full(len(samples), row["ra"]) * u.deg,
        dec=np.full(len(samples), row["dec"]) * u.deg,
        distance=(1000.0 / samples[:, 0]) * u.pc,
        pm_ra_cosdec=samples[:, 1] * u.mas / u.yr,
        pm_dec=samples[:, 2] * u.mas / u.yr,
        radial_velocity=samples[:, 3] * u.km / u.s,
        frame="icrs",
        obstime=obstime,
    )
    g = c.transform_to(frame)
    pos = np.vstack([g.x.to_value(u.kpc), g.y.to_value(u.kpc), g.z.to_value(u.kpc)]).T
    vel = np.vstack([g.v_x.to_value(u.km / u.s), g.v_y.to_value(u.km / u.s), g.v_z.to_value(u.km / u.s)]).T
    dist = 1000.0 / samples[:, 0]
    return {
        "distance_pc": round(float(dist[0]), 4),
        "distance_error_pc": round(float(dist[1:].std()), 4),
        "xyz_kpc": [round(float(v), 6) for v in pos[0]],
        "xyz_error_kpc": [round(float(v), 6) for v in pos[1:].std(axis=0)],
        "vxyz_km_s": [round(float(v), 4) for v in vel[0]],
        "vxyz_error_km_s": [round(float(v), 4) for v in vel[1:].std(axis=0)],
    }


def galpy_reference(star: dict, row: dict) -> dict:
    """Orbit quantities from galpy's MWPotential2014 for the catalogue values."""
    import astropy.units as u
    from astropy.coordinates import SkyCoord
    from astropy.time import Time
    from galpy.orbit import Orbit
    from galpy.potential import MWPotential2014

    c = SkyCoord(
        ra=row["ra"] * u.deg, dec=row["dec"] * u.deg, distance=(1000.0 / row["parallax"]) * u.pc,
        pm_ra_cosdec=row["pmra"] * u.mas / u.yr, pm_dec=row["pmdec"] * u.mas / u.yr,
        radial_velocity=row["radial_velocity"] * u.km / u.s, frame="icrs", obstime=Time(row["ref_epoch"], format="jyear"),
    )
    u_sun, v_sun, w_sun = SOLAR["v_sun_km_s"][0], SOLAR["v_sun_km_s"][1] - POTENTIAL["v0_km_s"], SOLAR["v_sun_km_s"][2]
    o = Orbit(c, ro=POTENTIAL["R0_kpc"], vo=POTENTIAL["v0_km_s"], zo=SOLAR["z_sun_pc"] / 1000.0, solarmotion=[-u_sun, v_sun, w_sun])
    ts = np.linspace(0.0, 10.0, 200_001) * u.Gyr
    o.integrate(ts, MWPotential2014, method="dop853_c")
    return {
        "eccentricity": round(float(o.e()), 4),
        "zmax_kpc": round(float(o.zmax()), 4),
        "rperi_kpc": round(float(o.rperi()), 4),
        "rapo_kpc": round(float(o.rap()), 4),
        "energy_km2_s2": round(float(o.E()) - potential_zero_point(), 1),
        "energy_galpy_km2_s2": round(float(o.E()), 1),
        "Lz_kpc_km_s": round(float(o.Lz()), 2),
        "galpy_xyz0_kpc": [round(float(o.x()), 6), round(float(o.y()), 6), round(float(o.z()), 6)],
        "galpy_vxyz0_km_s": [round(float(o.vx()), 4), round(float(o.vy()), 4), round(float(o.vz()), 4)],
    }


def potential_zero_point() -> float:
    """galpy's MWPotential2014 does not vanish at infinity: its bulge potential carries a
    constant, while the disc and halo terms fall off as 1/r. The page sets the potential to
    zero at infinity, so galpy energies are shifted by that constant, the bulge potential
    evaluated far out (r = 10^12 R0, where the remaining 1/r term is below 10^-12)."""
    from galpy.potential import MWPotential2014, evaluatePotentials

    vo = POTENTIAL["v0_km_s"]
    return float(evaluatePotentials(MWPotential2014[0], 1e12, 0.0) * vo**2)


def potential_checks() -> dict:
    """galpy's potential, forces and masses at test points, for checking the page's code."""
    from galpy.potential import MWPotential2014, evaluatePotentials, evaluateRforces, evaluatezforces, vcirc
    from galpy.util import conversion

    ro, vo = POTENTIAL["R0_kpc"], POTENTIAL["v0_km_s"]
    pts = [(8, 0), (2, 0.5), (15, 3), (0.5, 0.1), (30, -5), (1.0, 0.0), (8, 2), (4, -1.5), (60, 10), (0.05, 0.02)]
    checks = []
    for R, z in pts:
        checks.append({
            "R_kpc": R, "z_kpc": z,
            "Phi_km2_s2": float(evaluatePotentials(MWPotential2014, R / ro, z / ro) * vo**2),
            "FR_km2_s2_kpc": float(evaluateRforces(MWPotential2014, R / ro, z / ro) * vo**2 / ro),
            "Fz_km2_s2_kpc": float(evaluatezforces(MWPotential2014, R / ro, z / ro) * vo**2 / ro),
        })
    msun = conversion.mass_in_msol(vo, ro)
    names = ["bulge", "disc", "halo"]
    masses = {n: {"within_8_kpc_msun": float(p.mass(1.0) * msun), "within_245_kpc_msun": float(p.mass(245 / ro) * msun)} for n, p in zip(names, MWPotential2014)}
    total = float(evaluateRforces(MWPotential2014, 1.0, 0.0))
    fractions = {n: float(p.Rforce(1.0, 0.0) / total) for n, p in zip(names, MWPotential2014)}
    return {
        "vcirc_R0_km_s": float(vcirc(MWPotential2014, 1.0) * vo),
        "Phi_sun_km2_s2": float(evaluatePotentials(MWPotential2014, 1.0, 0.0) * vo**2),
        "Phi_zero_point_km2_s2": potential_zero_point(),
        "zero_point_note": "galpy's values of Phi below include this constant; the page's potential is zero at infinity, so page values equal galpy values minus the constant. Forces are unaffected",
        "radius_note": "galpy's eccentricity, rperi and rap use the spherical radius sqrt(R^2 + z^2); the page computes its live values the same way",
        "force_fractions_at_R0": fractions,
        "masses": masses,
        "points": checks,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", type=Path, default=ROOT.parent / "orbits_raw")
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    a.raw_dir.mkdir(parents=True, exist_ok=True)
    import astropy
    import galpy

    ids = resolve_ids(STARS, a.raw_dir / "simbad_ids.json", a.refresh)
    gaia = fetch_gaia([ids["ids"][s["name"]] for s in STARS], a.raw_dir / "gaia_rows.json", a.refresh)
    rng = np.random.default_rng(SEED)
    stars = []
    for s in STARS:
        sid = ids["ids"][s["name"]]
        row = gaia["rows"][str(sid)]
        if row["radial_velocity"] is None:
            sys.exit(f"{s['name']} has no Gaia DR3 radial velocity")
        if row["ruwe"] > 1.4:
            sys.exit(f"{s['name']} has RUWE {row['ruwe']}")
        gc = galactocentric(row, rng)
        ref = galpy_reference(s, row)
        stars.append({
            "name": s["name"], "other": s["other"], "source_id": sid,
            "gaia": row, "galactocentric": gc, "reference": ref,
        })
        print(f"{s['name']:18s} d={gc['distance_pc']:.2f} pc  xyz={gc['xyz_kpc']}  v={gc['vxyz_km_s']}  e={ref['eccentricity']} zmax={ref['zmax_kpc']} Lz={ref['Lz_kpc_km_s']}")
    checks = potential_checks()
    print(f"vcirc(R0) = {checks['vcirc_R0_km_s']:.6f} km/s, Phi(sun) = {checks['Phi_sun_km2_s2']:.3f} km2/s2")

    data = {
        "description": "Numbers used by the Orbits playground: a point-mass Earth with a Molniya constellation and a geostationary satellite, and six Gaia DR3 stars in the MWPotential2014 model of the Milky Way.",
        "built_utc": now(),
        "earth": EARTH,
        "molniya": MOLNIYA,
        "geo": GEO,
        "stations": STATIONS,
        "potential": POTENTIAL,
        "solar": SOLAR,
        "stars": stars,
        "credit": "Gaia data: ESA/Gaia/DPAC, CC BY-SA 3.0 IGO",
    }
    meta = {
        "description": "Provenance of orbits.json for the Orbits playground.",
        "built_utc": data["built_utc"],
        "script": "figures/playground/build_orbits_data.py",
        "identifier_resolution": {"service": "SIMBAD (CDS), astroquery.simbad.Simbad.query_objectids", "queried_utc": ids["queried_utc"], "ids": ids["ids"]},
        "gaia_query": {"service": gaia["service"], "queried_utc": gaia["queried_utc"], "adql": gaia["adql"], "columns": GAIA_COLUMNS,
                       "note": "Gaia DR3 reference epoch J2016.0; the archive reported release 3.15 at query time"},
        "coordinates": {"method": "astropy SkyCoord (ICRS, J2016.0) to Galactocentric", "solar": SOLAR,
                        "uncertainties": f"standard deviation over {MC_SAMPLES} draws of (parallax, pmra, pmdec, radial velocity) from a multivariate normal with the Gaia errors and the three published correlation coefficients; seed {SEED}",
                        "versions": {"astropy": astropy.__version__, "galpy": galpy.__version__, "numpy": np.__version__, "python": sys.version.split()[0]}},
        "reference_orbits": {"method": "galpy Orbit from the same SkyCoord with ro = 8 kpc, vo = 220 km/s, zo = 0.0208 kpc, solarmotion = [-11.1, 12.24, 7.25]; integrated for 10 Gyr in MWPotential2014 with dop853_c on 200,001 output times",
                             "sign_convention": "galpy's L_z is positive for rotation with the disc; in the astropy frame of orbits.json that is -(x v_y - y v_x). The page uses galpy's sign",
                             "energy_convention": "energy_km2_s2 is galpy's orbit energy shifted so that the potential is zero at infinity (galpy's value is kept as energy_galpy_km2_s2); see potential_checks.Phi_zero_point_km2_s2",
                             "potential_checks": checks},
        "dropped_candidates": DROPPED,
        "references": REFERENCES,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "orbits.json").write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    (OUT_DIR / "orbits.meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False) + "\n")
    print("wrote", OUT_DIR / "orbits.json", (OUT_DIR / "orbits.json").stat().st_size, "bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
