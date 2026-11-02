"""Build the point cloud behind the Milky Way map on the Galactic archaeology guide page.

Usage: uv run --with numpy python figures/map/build_mw_points.py <giants3d_snr.npz>

Input: an npz of Gaia DR3 red giants from the Andrae et al. (2023) XP catalogue with
heliocentric Galactic x, y, z in kpc (x toward the Galactic centre, z toward the north
Galactic pole), the catalogue metallicity ``feh`` and the parallax signal to noise ``snr``.
The npz itself comes from the catalogue parquet with parallax over error above 5 and a
parallax above 0.2 mas, so the cube spans 5 kpc from the Sun.

Output, under assets/data/mw/:
    giants.bin   little-endian, planar: x, y, z as float16 (kpc), then [Fe/H] as int8
                 (value times 50, clipped to the range -2.5 to 0.5)
    giants.json  the count, the layout, the selection and the provenance

The script fetches nothing and invents nothing: every row is a catalogue star, chosen by a
uniform random draw with a fixed seed from the stars whose parallax over error is above 10.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

N_KEEP = 160_000
SEED = 20261102
SNR_MIN = 10.0
FEH_SCALE = 50
FEH_RANGE = (-2.5, 0.5)
OUT_DIR = Path(__file__).resolve().parents[2] / "assets" / "data" / "mw"
SOURCE_PARQUET = "~/data/janus_store/gaia/xp_parameters_andrae2023/andrae2023_rgb.parquet"
REFERENCES = [
    {
        "label": "Andrae, Rix and Chandra 2023, ApJS 267, 8: robust data-driven metallicities "
        "for 175 million stars from Gaia XP spectra",
        "doi": "10.3847/1538-4365/acd53e",
        "arxiv": "2302.02611",
    },
    {
        "label": "Gaia Collaboration, Vallenari et al. 2023, A&A 674, A1: Gaia Data Release 3",
        "doi": "10.1051/0004-6361/202243940",
        "arxiv": "2208.00211",
    },
]


def main(npz_path: str) -> None:
    d = np.load(npz_path)
    n_in = int(d["snr"].shape[0])
    good = d["snr"] > SNR_MIN
    n_good = int(good.sum())
    idx = np.flatnonzero(good)
    rng = np.random.default_rng(SEED)
    pick = np.sort(rng.choice(idx, size=N_KEEP, replace=False))

    x = d["x"][pick].astype("<f2")
    y = d["y"][pick].astype("<f2")
    z = d["z"][pick].astype("<f2")
    feh = d["feh"][pick].astype("f8")
    if not np.isfinite(feh).all():
        raise SystemExit("non-finite [Fe/H] in the selection; the catalogue should have none")
    feh_i8 = np.clip(np.rint(np.clip(feh, *FEH_RANGE) * FEH_SCALE), -128, 127).astype("i1")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    blob = b"".join(a.tobytes() for a in (x, y, z, feh_i8))
    (OUT_DIR / "giants.bin").write_bytes(blob)

    r = np.sqrt(x.astype("f8") ** 2 + y.astype("f8") ** 2 + z.astype("f8") ** 2)
    pct = [1, 5, 25, 50, 75, 95, 99]
    header = {
        "format": "mw_giants 1",
        "binary": "giants.bin",
        "bytes": len(blob),
        "byte_order": "little",
        "n": N_KEEP,
        "layout": [
            {"field": "x", "dtype": "float16", "unit": "kpc", "offset": 0},
            {"field": "y", "dtype": "float16", "unit": "kpc", "offset": 2 * N_KEEP},
            {"field": "z", "dtype": "float16", "unit": "kpc", "offset": 4 * N_KEEP},
            {"field": "feh", "dtype": "int8", "unit": "dex times 50", "offset": 6 * N_KEEP},
        ],
        "frame": "heliocentric Galactic Cartesian: x toward the Galactic centre, y toward "
        "l = 90 degrees (the direction of rotation), z toward the north Galactic pole; "
        "distance is the inverse parallax",
        "feh_decode": "[Fe/H] = feh / 50, after clipping to [-2.5, 0.5]",
        "selection": {
            "catalogue": "Andrae et al. 2023 red giants with XP metallicities (Gaia DR3)",
            "cuts": "parallax > 0.2 mas and parallax/error > 5 in the intermediate file; "
            f"parallax/error > {SNR_MIN:g} here",
            "n_catalogue_file": n_in,
            "n_after_snr_cut": n_good,
            "n_kept": N_KEEP,
            "draw": f"uniform random subsample without replacement, numpy default_rng seed {SEED}",
            "summary": f"{N_KEEP:,} of {n_good:,} stars with parallax/error > {SNR_MIN:g}",
        },
        "distance_kpc_percentiles": {str(p): round(float(v), 3) for p, v in zip(pct, np.percentile(r, pct))},
        "feh_percentiles": {str(p): round(float(v), 3) for p, v in zip(pct, np.percentile(feh, pct))},
        "provenance": {
            "source_file": SOURCE_PARQUET,
            "intermediate": Path(npz_path).name,
            "script": "figures/map/build_mw_points.py",
            "built_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "references": REFERENCES,
    }
    (OUT_DIR / "giants.json").write_text(json.dumps(header, indent=2) + "\n")
    print(f"{N_KEEP:,} of {n_good:,} (snr > {SNR_MIN:g}) of {n_in:,}; {len(blob):,} bytes")
    print("distance percentiles", header["distance_kpc_percentiles"])
    print("[Fe/H] percentiles", header["feh_percentiles"])


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
