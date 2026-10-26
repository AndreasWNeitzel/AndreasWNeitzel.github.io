#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "h5py>=3.10",
#     "numpy>=1.26",
# ]
# ///
"""Export one interior profile of the 1 M_sun MESA track for the polytrope playground.

The playground at /playground/polytropes/ overlays a real stellar model on the
polytrope, so the reader sees where the polytrope departs from it. The model comes
from the HDF5 file behind Stellar Explorer (github.com/AndreasWNeitzel/stellar-explorer-data,
MESA r24.08.1 + GYRE, 1 M_sun, [Fe/H] = 0), which stores 176 models of the track with a
256-zone interior profile each. This script writes the profile arrays of one model, as
stored, to assets/data/playground/mesa_1msun_profile.json together with their provenance.
No value is changed, rounded or interpolated: float32 values are written with nine
significant digits, which round-trips float32 exactly.

Which model
    The track row nearest the Sun's age is row 27 (4.615 Gyr). The file's builder
    (archive/preprocess_mesa_v2.py in the data repository) attaches to each track row the
    nearest native MESA profile when the run saved none for that model, and rows 23 to 28
    all carry the same arrays. The arrays belong to track row 25 (model 200, 2.758 Gyr),
    whose central hydrogen fraction in the track table equals the profile's innermost
    value; the solar-age row's central hydrogen (0.344) does not. This script therefore
    exports the profile under row 25 with that row's scalars, records the solar-age row
    for comparison, and asserts that the arrays under rows 25 and 27 are identical.

Usage
    uv run figures/playground/build_mesa_profile.py --h5 PATH [--out assets/data/playground/mesa_1msun_profile.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import h5py
import numpy as np

SOLAR_AGE_GYR = 4.57  # Bahcall et al. 1995 style value; used only to pick the nearest row
PROFILE_KEYS = ("x", "logRho", "logT", "logP", "eps_nuc", "h1", "he4", "mixing_type")
UNITS = {
    "x": "fractional radius r/R, dimensionless; the storage grid is 0 followed by 255 points log-spaced from 1e-3 to 1",
    "logRho": "log10 of the density in g cm^-3",
    "logT": "log10 of the temperature in K",
    "logP": "log10 of the total pressure in dyn cm^-2",
    "eps_nuc": "nuclear energy generation rate in erg g^-1 s^-1",
    "h1": "hydrogen mass fraction",
    "he4": "helium-4 mass fraction",
    "mixing_type": "MESA mixing_type code, nearest-zone resampled: 0 no mixing, 1 convective",
}
TRACK_KEYS = ("star_age", "star_mass", "log_R", "log_L", "log_Teff", "log_g", "center_h1", "surface_h1", "surface_he4", "phase", "model_number_orig")


def fmt(v: np.floating | np.integer) -> float | int:
    """A JSON number that reproduces the stored float32 (or int32) exactly."""
    if isinstance(v, (np.integer, int)):
        return int(v)
    return float(f"{float(v):.9g}")


def git_head(path: Path) -> str | None:
    try:
        return subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def row_scalars(track: h5py.Group, i: int) -> dict:
    out = {}
    for k in TRACK_KEYS:
        v = track[k][i]
        out[k] = v.decode() if isinstance(v, bytes) else fmt(v)
    out["R_Rsun"] = fmt(np.float32(10.0 ** float(track["log_R"][i])))
    out["L_Lsun"] = fmt(np.float32(10.0 ** float(track["log_L"][i])))
    out["Teff_K"] = fmt(np.float32(10.0 ** float(track["log_Teff"][i])))
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--h5", required=True, type=Path, help="stellar_data_real.h5 from the stellar-explorer-data repository")
    ap.add_argument("--out", type=Path, default=Path("assets/data/playground/mesa_1msun_profile.json"))
    args = ap.parse_args(argv)

    with h5py.File(args.h5, "r") as f:
        track = f["track"]
        ages = track["star_age"][:]
        solar_row = int(np.argmin(np.abs(ages - SOLAR_AGE_GYR)))
        prof_solar = f["profiles"][str(solar_row)]
        # Find the row whose track scalars match the arrays stored under the solar-age row.
        h1_centre = float(prof_solar["h1"][0])
        matches = [i for i in range(len(ages)) if abs(float(track["center_h1"][i]) - h1_centre) < 1e-6]
        if len(matches) != 1:
            sys.exit(f"expected one track row with center_h1 = {h1_centre}, found {matches}")
        row = matches[0]
        prof = f["profiles"][str(row)]
        for k in PROFILE_KEYS:
            if not np.array_equal(prof[k][:], prof_solar[k][:]):
                sys.exit(f"profile arrays under rows {row} and {solar_row} differ in {k}")
        same_rows = [i for i in range(len(ages)) if all(np.array_equal(f["profiles"][str(i)][k][:], prof[k][:]) for k in PROFILE_KEYS)]
        arrays = {k: [fmt(v) for v in prof[k][:]] for k in PROFILE_KEYS}
        dtypes = {k: str(prof[k].dtype) for k in PROFILE_KEYS}
        x = prof["x"][:]
        conv = np.where(prof["mixing_type"][:] == 1)[0]
        file_attrs = {k: (v.item() if hasattr(v, "item") else v) for k, v in f.attrs.items()}
        model = row_scalars(track, row)
        solar = row_scalars(track, solar_row)

    sha = hashlib.sha256(args.h5.read_bytes()).hexdigest()
    out = {
        "description": "One interior profile of a 1 M_sun, [Fe/H] = 0 MESA model, exported unchanged from the Stellar Explorer data file for the polytrope playground.",
        "built_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "script": "figures/playground/build_mesa_profile.py",
        "source": {
            "repository": "https://github.com/AndreasWNeitzel/stellar-explorer-data",
            "file": args.h5.name,
            "sha256": sha,
            "size_bytes": args.h5.stat().st_size,
            "repository_commit": git_head(args.h5.parent),
            "file_attrs": file_attrs,
            "codes": "MESA r24.08.1 (Paxton et al. 2011, ApJS 192, 3, doi:10.1088/0067-0049/192/1/3) with GYRE post-processing (Townsend and Teitler 2013, MNRAS 435, 3406)",
            "sampling": "the data file resamples each native MESA profile onto 256 fractional radii, linear in each quantity, nearest zone for mixing_type (archive/preprocess_mesa_v2.py in the repository); values below the innermost native zone repeat it",
        },
        "model": {
            "track_row": row,
            "why_this_row": (
                f"the track row nearest the solar age ({SOLAR_AGE_GYR} Gyr) is row {solar_row} ({solar['star_age']} Gyr), but the arrays stored "
                f"under rows {same_rows[0]} to {same_rows[-1]} are one and the same native profile, the one of model {model['model_number_orig']} "
                f"(row {row}): the file's builder attaches the nearest saved profile to rows without one. The track's central hydrogen fraction "
                f"equals the profile's innermost value only for row {row}, so this is the model the arrays describe."
            ),
            "rows_sharing_these_arrays": same_rows,
            **model,
            "convective_envelope_base_x": fmt(x[conv[0]]) if len(conv) else None,
            "n_convective_zones": int(len(conv)),
        },
        "solar_age_row_for_comparison": {"track_row": solar_row, **solar},
        "units": UNITS,
        "dtypes": dtypes,
        "n_zones": int(len(x)),
        "arrays": arrays,
        "licence": "MESA and GYRE outputs are redistributed under the terms of those codes; cite the MESA and GYRE papers for scientific use.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, separators=(",", ":")) + "\n")
    print(f"wrote {args.out} ({args.out.stat().st_size} bytes): row {row}, age {model['star_age']} Gyr, R {model['R_Rsun']} Rsun, L {model['L_Lsun']} Lsun")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
