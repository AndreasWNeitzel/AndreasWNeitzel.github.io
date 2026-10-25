#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "astroquery>=0.4.10",
#     "gaiaxpy==2.1.5",
#     "numpy>=1.26",
#     "pyvo>=1.5",
# ]
# ///
"""Build the Gaia XP to [M/H] teaching set for the neural-network playground.

The playground at /playground/neural-network/ trains a small network in the browser
to predict the GSP-Spec metallicity [M/H] of a star from the first K Hermite
coefficients of its Gaia DR3 BP and RP mean spectra. This script selects the stars,
fetches their coefficients, normalises them and writes three files to
assets/data/playground/:

    gaia_xp_mh.bin        little-endian arrays (layout in the header)
    gaia_xp_mh.json       header: array layout, split, three example spectra
    gaia_xp_mh.meta.json  provenance: queries, dates, cuts, columns, credits

Sources
    Selection and labels come from the Gaia archive TAP service at ESA
    (gaiadr3.gaia_source, gaiadr3.astrophysical_parameters, gaiadr3.xp_summary).
    The archive stops anonymous queries after 60 s, so the selection runs over
    consecutive random_index ranges and keeps the first N_STARS rows in
    random_index order: the same rows as the single ORDER BY random_index query
    recorded in the provenance file.
    The coefficients come from gaiadr3.xp_continuous_mean_spectrum. The ESA TAP
    service does not expose that table (ESA serves it through DataLink, at most
    50 sources per anonymous request), so they are read from the same Gaia DR3
    table at the Gaia@AIP partner data centre. Up to 50 rows are compared with
    ESA DataLink whenever that service answers; the outcome is recorded.

Usage
    uv run figures/playground/build_gaia_xp_mh.py --raw-dir DIR [--refresh]

Downloads are cached in DIR and reused; --refresh queries the services again.
Keep DIR outside the repository.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

ESA_TAP = "https://gea.esac.esa.int/tap-server/tap"
AIP_TAP = "https://gaia.aip.de/tap"
N_STARS = 4000
K = 24  # coefficients kept per band; see K_REASON
N_BASES = 55  # Hermite bases per band in Gaia DR3
SEED = 20261025
VAL_FRACTION = 0.2
CHUNK = 250_000  # random_index values per ESA query (wider ranges can time out)
BATCH = 500  # source_ids per Gaia@AIP query
CHECK_N = 50  # anonymous DataLink limit per request
SAMPLING_NM = np.arange(336.0, 1021.0, 2.0)  # GaiaXPy default grid
EXAMPLE_BOX = {"teff": (4500.0, 5000.0), "logg": (2.0, 3.0)}
EXAMPLE_PERCENTILES = (3, 50, 97)
EXAMPLE_BP_SHARE_TOL = 0.02
OUT_DIR = Path(__file__).resolve().parents[2] / "assets" / "data" / "playground"
STEM = "gaia_xp_mh"
K_REASON = (
    "validation RMSE of a ridge fit and of a 32-32 tanh network on these stars stops "
    "improving near K = 24 (ridge 0.113 dex, network 0.114 dex, against 0.217 dex for "
    "predicting the training mean); more coefficients make the file larger and the "
    "small network overfit"
)

SELECT_COLUMNS = """gs.source_id, gs.random_index, gs.phot_g_mean_mag,
  ap.mh_gspspec, ap.teff_gspspec, ap.logg_gspspec, ap.flags_gspspec,
  xs.bp_n_relevant_bases, xs.rp_n_relevant_bases"""
FROM_WHERE = """FROM gaiadr3.gaia_source AS gs
JOIN gaiadr3.astrophysical_parameters AS ap ON ap.source_id = gs.source_id
JOIN gaiadr3.xp_summary AS xs ON xs.source_id = gs.source_id
WHERE ap.mh_gspspec IS NOT NULL
  AND ap.flags_gspspec LIKE '0000000000000%'"""
SELECTION_EQUIVALENT = (
    f"SELECT TOP {N_STARS} {SELECT_COLUMNS}\n{FROM_WHERE}\nORDER BY gs.random_index"
)
SELECTION_CHUNK = (
    f"SELECT {SELECT_COLUMNS}\n{FROM_WHERE}\n"
    "  AND gs.random_index >= {lo} AND gs.random_index < {hi}\n"
    "ORDER BY gs.random_index"
)
COEFF_COLUMNS = (
    "source_id",
    "bp_n_parameters",
    "rp_n_parameters",
    "bp_coefficients",
    "rp_coefficients",
    "bp_coefficient_errors",
    "rp_coefficient_errors",
)
COEFF_QUERY = (
    "SELECT " + ", ".join(COEFF_COLUMNS) + "\n"
    "FROM gaiadr3.xp_continuous_mean_spectrum\n"
    "WHERE source_id IN ({ids})"
)
FULL_XP_QUERY = (
    "SELECT * FROM gaiadr3.xp_continuous_mean_spectrum WHERE source_id IN ({ids})"
)


def ordinal(n: int) -> str:
    suffix = (
        "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    )
    return f"{n}{suffix}"


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def tap(url: str, adql: str):
    """Run a synchronous ADQL query and return an astropy Table."""
    import pyvo

    return pyvo.dal.TAPService(url).run_sync(adql).to_table()


def id_list(ids) -> str:
    return ", ".join(str(int(i)) for i in ids)


def as_matrix(column, width: int) -> np.ndarray:
    """Variable-length array column to a float64 matrix; short rows stay NaN."""
    out = np.full((len(column), width), np.nan)
    for i, value in enumerate(column):
        arr = np.ma.filled(np.ma.asarray(value, dtype=float), np.nan)
        out[i, : min(width, arr.size)] = arr[:width]
    return out


def select_stars(raw: Path, refresh: bool):
    """First N_STARS stars in random_index order that pass the cuts (ESA TAP)."""
    from astropy.table import Table, vstack

    path = raw / "selection_esa.ecsv"
    if path.exists() and not refresh:
        return Table.read(path)

    def query_range(lo: int, hi: int):
        try:
            return [tap(ESA_TAP, SELECTION_CHUNK.format(lo=lo, hi=hi))]
        except Exception:  # noqa: BLE001 (a timed-out range is split in two)
            if hi - lo <= CHUNK // 16:
                raise
            mid = (lo + hi) // 2
            return query_range(lo, mid) + query_range(mid, hi)

    started, parts, total, lo = now(), [], 0, 0
    while total < N_STARS:
        for part in query_range(lo, lo + CHUNK):
            parts.append(part)
            total += len(part)
        lo += CHUNK
        print(f"  random_index < {lo:,}: {total} stars", file=sys.stderr)
    sel = vstack(parts)
    sel.sort("random_index")
    sel = sel[:N_STARS]
    sel.meta.update(
        {
            "service": ESA_TAP,
            "queried_utc": started,
            "random_index_scanned_below": lo,
            "chunk_template": SELECTION_CHUNK,
        }
    )
    sel.write(path, overwrite=True)
    return sel


def fetch_coefficients(ids: np.ndarray, raw: Path, refresh: bool) -> dict:
    """BP and RP coefficients and their errors for each source_id (Gaia@AIP TAP)."""
    path = raw / "xp_continuous_aip.npz"
    if path.exists() and not refresh:
        with np.load(path) as f:
            cached = {key: f[key] for key in f.files}
        if np.isin(ids, cached["source_id"]).all():
            return cached
    started, chunks = now(), []
    for start in range(0, len(ids), BATCH):
        chunks.append(
            tap(AIP_TAP, COEFF_QUERY.format(ids=id_list(ids[start : start + BATCH])))
        )
        print(
            f"  coefficients: {min(start + BATCH, len(ids))} of {len(ids)}",
            file=sys.stderr,
        )
    out = {
        "source_id": np.concatenate(
            [np.asarray(c["source_id"], dtype=np.int64) for c in chunks]
        ),
        "queried_utc": np.array(started),
    }
    for band in ("bp", "rp"):
        out[f"{band}_n_parameters"] = np.concatenate(
            [np.asarray(c[f"{band}_n_parameters"], dtype=np.int64) for c in chunks]
        )
        for kind in ("coefficients", "coefficient_errors"):
            name = f"{band}_{kind}"
            out[name] = np.concatenate([as_matrix(c[name], N_BASES) for c in chunks])
    np.savez(path, **out)
    return out


def check_against_esa(ids: np.ndarray, bp: np.ndarray, rp: np.ndarray) -> dict:
    """Compare up to CHECK_N rows with ESA DataLink; record failure if it does not answer."""
    record = {
        "service": "https://gea.esac.esa.int/data-server/data",
        "attempted_utc": now(),
    }
    try:
        from astroquery.gaia import Gaia

        result = Gaia.load_data(
            ids=[int(i) for i in ids[:CHECK_N]],
            data_release="Gaia DR3",
            retrieval_type="XP_CONTINUOUS",
            data_structure="COMBINED",
            format="votable",
            verbose=False,
        )
        tables = [
            item.to_table() if hasattr(item, "to_table") else item
            for items in result.values()
            for item in items
        ]
        esa = tables[0]
        rows = {int(s): i for i, s in enumerate(esa["source_id"])}
        worst = 0.0
        for j, sid in enumerate(ids[:CHECK_N]):
            i = rows[int(sid)]
            for mine, col in ((bp[j], "bp_coefficients"), (rp[j], "rp_coefficients")):
                theirs = np.asarray(esa[col][i], dtype=float)
                worst = max(
                    worst, float(np.max(np.abs(theirs - mine) / np.abs(mine[0])))
                )
        record.update(
            status="compared",
            n_compared=len(rows),
            max_abs_difference_over_first_coefficient=worst,
        )
    except Exception as exc:  # noqa: BLE001 (any failure is recorded, not fatal)
        first = str(exc).strip().splitlines()[0][:120] if str(exc).strip() else ""
        record.update(status="not compared", reason=f"{type(exc).__name__}: {first}")
    return record


def choose_examples(teff, logg, mh, split, bp_share) -> list[int]:
    """Three validation giants of similar Teff, log g and observed colour, spread in [M/H].

    The colour cut (the BP share of the flux, within EXAMPLE_BP_SHARE_TOL of the median
    in the box) keeps strongly reddened stars out, so dust does not dominate the
    differences between the three spectra.
    """
    (t0, t1), (g0, g1) = EXAMPLE_BOX["teff"], EXAMPLE_BOX["logg"]
    box = np.flatnonzero(
        (split == 1) & (teff >= t0) & (teff <= t1) & (logg >= g0) & (logg <= g1)
    )
    share = np.median(bp_share[box])
    box = box[np.abs(bp_share[box] - share) <= EXAMPLE_BP_SHARE_TOL]
    picks: list[int] = []
    for target in np.percentile(mh[box], EXAMPLE_PERCENTILES):
        order = box[np.argsort(np.abs(mh[box] - target), kind="stable")]
        picks.append(int(next(r for r in order if r not in picks)))
    return picks


def sample_spectra(source_ids: list[int], raw: Path, refresh: bool) -> np.ndarray:
    """GaiaXPy calibrated flux (W m^-2 nm^-1) on SAMPLING_NM for the example stars."""
    path = raw / "xp_sampled_examples.npz"
    if path.exists() and not refresh:
        with np.load(path) as f:
            if list(f["source_id"]) == source_ids:
                return f["flux"]
    import pandas as pd
    from gaiaxpy import calibrate

    table = tap(AIP_TAP, FULL_XP_QUERY.format(ids=id_list(source_ids)))
    frame = table.to_pandas()
    for col in frame.columns:
        if frame[col].dtype == object:
            frame[col] = [
                np.ma.filled(np.ma.asarray(v, dtype=float), np.nan) for v in frame[col]
            ]
    spectra, _ = calibrate(pd.DataFrame(frame), sampling=SAMPLING_NM, save_file=False)
    by_id = {
        int(s): np.asarray(f, dtype=float)
        for s, f in zip(spectra["source_id"], spectra["flux"])
    }
    flux = np.stack([by_id[s] for s in source_ids])
    np.savez(path, source_id=np.array(source_ids, dtype=np.int64), flux=flux)
    return flux


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--raw-dir", type=Path, required=True, help="download cache")
    parser.add_argument(
        "--refresh", action="store_true", help="query the services again"
    )
    args = parser.parse_args()
    raw = args.raw_dir.expanduser().resolve()
    raw.mkdir(parents=True, exist_ok=True)

    print("Selecting stars (ESA TAP)", file=sys.stderr)
    sel = select_stars(raw, args.refresh)
    ids = np.asarray(sel["source_id"], dtype=np.int64)
    print("Fetching XP coefficients (Gaia@AIP TAP)", file=sys.stderr)
    xp = fetch_coefficients(ids, raw, args.refresh)
    row_of = {int(s): i for i, s in enumerate(xp["source_id"])}

    def labels(name: str) -> np.ndarray:
        return np.ma.filled(np.ma.asarray(sel[name], dtype=float), np.nan)

    mh, teff, logg = (
        labels("mh_gspspec"),
        labels("teff_gspspec"),
        labels("logg_gspspec"),
    )
    gmag = labels("phot_g_mean_mag")
    take = np.array([row_of.get(int(s), -1) for s in ids])
    have = take >= 0
    bp = np.full((len(ids), N_BASES), np.nan)
    rp, bp_err, rp_err = bp.copy(), bp.copy(), bp.copy()
    bp[have] = xp["bp_coefficients"][take[have]]
    rp[have] = xp["rp_coefficients"][take[have]]
    bp_err[have] = xp["bp_coefficient_errors"][take[have]]
    rp_err[have] = xp["rp_coefficient_errors"][take[have]]
    scale = bp[:, 0] + rp[:, 0]

    # Drop, never fill: a star stays only if every value it contributes was measured.
    reasons = {
        "no XP continuous spectrum returned": ~have,
        "fewer than 55 coefficients in a band": have
        & ~(np.isfinite(bp).all(1) & np.isfinite(rp).all(1)),
        "missing Teff, log g or G": ~(
            np.isfinite(teff) & np.isfinite(logg) & np.isfinite(gmag)
        ),
        "non-positive flux scale": ~(scale > 0),
    }
    keep = ~np.logical_or.reduce(list(reasons.values()))
    dropped = {k: int(v.sum()) for k, v in reasons.items() if v.any()}
    print(f"Kept {keep.sum()} of {len(keep)} stars; dropped {dropped}", file=sys.stderr)

    ids, mh, teff, logg, gmag, scale = (
        a[keep] for a in (ids, mh, teff, logg, gmag, scale)
    )
    bp, rp, bp_err, rp_err = (a[keep] for a in (bp, rp, bp_err, rp_err))
    nrel_bp = np.asarray(sel["bp_n_relevant_bases"], dtype=np.int64)[keep]
    nrel_rp = np.asarray(sel["rp_n_relevant_bases"], dtype=np.int64)[keep]
    n = len(ids)

    features = np.concatenate([bp[:, :K], rp[:, :K]], axis=1) / scale[:, None]
    # 16-bit linear quantisation per feature; the rounding stays far below the catalogue errors.
    offset = features.min(axis=0)
    step = (features.max(axis=0) - offset) / 65535
    quantised = np.round((features - offset) / step).astype("<u2")
    errors = np.concatenate([bp_err[:, :K], rp_err[:, :K]], axis=1)
    restored = offset + quantised * step
    rounding = np.abs(restored - features) * scale[:, None] / errors

    rng = np.random.default_rng(SEED)
    split = np.zeros(n, dtype=np.uint8)
    split[rng.permutation(n)[: round(n * VAL_FRACTION)]] = 1

    examples = choose_examples(teff, logg, mh, split, features[:, 0])
    print("Sampling example spectra (GaiaXPy)", file=sys.stderr)
    flux = sample_spectra([int(ids[r]) for r in examples], raw, args.refresh)
    print("Comparing with ESA DataLink", file=sys.stderr)
    check = check_against_esa(ids, bp, rp)
    print(f"  {check['status']}", file=sys.stderr)
    # Row-level consistency of the two services: the XP flux scale (Gaia@AIP) must track
    # the G magnitude (ESA) star by star; a mismatched row would stand out.
    mag = -2.5 * np.log10(scale)
    slope, icept = np.polyfit(gmag, mag, 1)
    resid = mag - (slope * gmag + icept)
    consistency = {
        "test": "-2.5 log10(flux_scale) against phot_g_mean_mag, straight-line fit",
        "slope": round(float(slope), 4),
        "robust_scatter_mag": round(
            float(1.4826 * np.median(np.abs(resid - np.median(resid)))), 4
        ),
        "max_abs_residual_mag": round(float(np.abs(resid).max()), 3),
    }

    arrays = [
        ("source_id", ids.astype("<u8")),
        ("mh_gspspec", mh.astype("<f4")),
        ("teff_gspspec", teff.astype("<f4")),
        ("logg_gspspec", logg.astype("<f4")),
        ("phot_g_mean_mag", gmag.astype("<f4")),
        ("flux_scale", scale.astype("<f4")),
        ("split", split),
        ("bp_n_relevant_bases", nrel_bp.astype(np.uint8)),
        ("rp_n_relevant_bases", nrel_rp.astype(np.uint8)),
        ("features", quantised.reshape(-1)),
    ]
    blob, layout = bytearray(), []
    for name, arr in arrays:
        layout.append(
            {
                "name": name,
                "dtype": arr.dtype.name,
                "offset": len(blob),
                "length": int(arr.size),
            }
        )
        blob += arr.tobytes()
        blob += b"\0" * (-len(blob) % 8)
    layout[-1]["shape"] = [n, 2 * K]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{STEM}.bin").write_bytes(bytes(blob))
    header = {
        "format": "gaia_xp_mh 1",
        "binary": f"{STEM}.bin",
        "byte_order": "little",
        "n": n,
        "k": K,
        "features": f"bp_0..bp_{K - 1} then rp_0..rp_{K - 1}, each divided by flux_scale",
        "feature_decode": "value = feature_offset[j] + features[i, j] * feature_step[j]",
        "feature_offset": [float(v) for v in offset],
        "feature_step": [float(v) for v in step],
        "split": {"0": "train", "1": "validation"},
        "arrays": layout,
        "examples": [
            {
                "row": int(r),
                "source_id": str(int(ids[r])),
                "flux": [float(f"{v:.4g}") for v in flux[j]],
            }
            for j, r in enumerate(examples)
        ],
        "wavelength_nm": {
            "start": float(SAMPLING_NM[0]),
            "step": 2.0,
            "count": int(SAMPLING_NM.size),
        },
        "provenance": f"{STEM}.meta.json",
    }
    (OUT_DIR / f"{STEM}.json").write_text(
        json.dumps(header, separators=(",", ":")) + "\n"
    )

    import gaiaxpy

    meta = {
        "description": (
            "Gaia DR3 stars with a best-quality GSP-Spec metallicity, with the first "
            f"{K} BP and {K} RP Hermite coefficients of their XP mean spectra, for a "
            "teaching demo that trains a small network in the browser."
        ),
        "built_utc": now(),
        "script": "figures/playground/build_gaia_xp_mh.py",
        "n_stars": n,
        "n_train": int((split == 0).sum()),
        "n_validation": int((split == 1).sum()),
        "dropped": dropped,
        "selection": {
            "service": ESA_TAP,
            "queried_utc": sel.meta.get("queried_utc"),
            "adql": SELECTION_EQUIVALENT,
            "run_as": (
                "the same query restricted to consecutive random_index ranges of "
                f"{CHUNK:,} (the archive stops anonymous queries after 60 s), "
                f"scanned below random_index {sel.meta.get('random_index_scanned_below'):,}; "
                f"the first {N_STARS} rows in random_index order were kept"
            ),
            "adql_per_range": SELECTION_CHUNK,
            "cuts": [
                "mh_gspspec IS NOT NULL",
                "flags_gspspec characters 1 to 13 all '0' (best GSP-Spec quality, "
                "Recio-Blanco et al. 2023)",
                "an XP continuous mean spectrum exists (join with gaiadr3.xp_summary)",
            ],
            "order": "gaia_source.random_index, ascending",
        },
        "coefficients": {
            "service": AIP_TAP,
            "table": "gaiadr3.xp_continuous_mean_spectrum",
            "queried_utc": str(xp["queried_utc"]),
            "adql": COEFF_QUERY.format(ids="<500 source_ids per query>"),
            "why_not_esa": (
                "the ESA TAP service does not expose this table; ESA serves it through "
                "DataLink, limited to 50 sources per anonymous request"
            ),
            "esa_datalink_check": check,
            "consistency_with_esa_g_magnitude": consistency,
        },
        "features": {
            "k_per_band": K,
            "order": f"bp_0..bp_{K - 1} then rp_0..rp_{K - 1}",
            "normalisation": (
                "each coefficient divided by flux_scale = bp_coefficients[0] + "
                "rp_coefficients[0] of the same star, so the network sees spectral "
                "shape and not brightness"
            ),
            "why_k": K_REASON,
            "storage": (
                "uint16 per feature: value = feature_offset + stored * feature_step "
                "(offsets and steps in the header)"
            ),
            "rounding_over_catalogue_error": {
                "median": float(np.median(rounding)),
                "p99": float(np.percentile(rounding, 99)),
                "max": float(rounding.max()),
            },
            "browser_scaling": (
                "the page standardises each feature and the label with the mean and "
                "standard deviation of the training stars"
            ),
        },
        "split": {
            "seed": SEED,
            "rule": (
                f"numpy.random.default_rng({SEED}).permutation(n); the first "
                f"{round(VAL_FRACTION * 100)} percent of that permutation is validation"
            ),
        },
        "columns": {
            "source_id": "Gaia DR3 source_id",
            "mh_gspspec": "GSP-Spec [M/H] in dex, catalogue value (no calibration applied)",
            "teff_gspspec": "GSP-Spec effective temperature in K",
            "logg_gspspec": "GSP-Spec log g in dex (cgs)",
            "phot_g_mean_mag": "Gaia G magnitude",
            "flux_scale": "bp_coefficients[0] + rp_coefficients[0], archive flux units",
            "split": "0 train, 1 validation",
            "bp_n_relevant_bases": "from gaiadr3.xp_summary",
            "rp_n_relevant_bases": "from gaiadr3.xp_summary",
            "features": "normalised coefficients, row-major [n, 2k]",
        },
        "examples": {
            "rule": (
                "validation stars with Teff {0} to {1} K, log g {2} to {3} and a BP share "
                "of the flux, bp_coefficients[0] / flux_scale, within {4} of the median "
                "of that box (to keep strongly reddened stars out); the stars closest "
                "to the {5}, {6} and {7} percentiles of [M/H] among them"
            ).format(
                *(f"{v:g}" for v in EXAMPLE_BOX["teff"] + EXAMPLE_BOX["logg"]),
                EXAMPLE_BP_SHARE_TOL,
                *(ordinal(p) for p in EXAMPLE_PERCENTILES),
            ),
            "rows": examples,
            "spectra": (
                f"GaiaXPy {gaiaxpy.__version__} calibrate() on all {N_BASES} BP and "
                f"{N_BASES} RP coefficients, 336 to 1020 nm in 2 nm steps, "
                "flux in W m^-2 nm^-1, four significant figures"
            ),
        },
        "licence": (
            "Gaia data: CC BY-SA 3.0 IGO, ESA/Gaia/DPAC. This file and the binary "
            "derived from them are shared under the same licence."
        ),
        "credits": [
            "Gaia Collaboration, Vallenari et al. 2023, A&A 674, A1 (Gaia DR3)",
            "De Angeli et al. 2023, A&A 674, A2 (XP spectra processing)",
            "Montegriffo et al. 2023, A&A 674, A3 (XP external calibration)",
            "Recio-Blanco et al. 2023, A&A 674, A29 (GSP-Spec)",
            "GaiaXPy, developed by Gaia DPAC CU5 and DPCI",
            "Gaia@AIP partner data centre, https://gaia.aip.de",
        ],
    }
    (OUT_DIR / f"{STEM}.meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    size = len(blob) + (OUT_DIR / f"{STEM}.json").stat().st_size
    print(f"Wrote {n} stars, {size / 1024:.0f} KiB to {OUT_DIR}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
