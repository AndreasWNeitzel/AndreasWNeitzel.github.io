#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "astroquery>=0.4.10",
#     "astropy>=6.0",
#     "numpy>=1.26",
# ]
# ///
"""Export the published HARPS radial velocities of HD 41248 for the Gaussian-process playground.

The playground at /playground/gaussian-processes/ fits a quasi-periodic Gaussian
process to a real radial-velocity series in the browser. This script reads the
HARPS time series of HD 41248 that accompanies Jenkins and Tuomi (2014, ApJ 794,
110) from VizieR (catalogue J/ApJ/794/110, table1) and writes two files to
assets/data/playground/:

    hd41248_harps.json       the table: BJD, radial velocity and its uncertainty
                             (m/s), plus the S-index, bisector span and FWHM
    hd41248_harps.meta.json  provenance: service, query time, row count, column
                             meanings, summary numbers, licence and credits

Nothing is altered: the values are the catalogue values at the catalogue's
printed precision. The page subtracts the mean radial velocity itself.

Usage
    uv run figures/playground/build_hd41248_rv.py
"""

from __future__ import annotations

import json
import sys
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

CATALOGUE = "J/ApJ/794/110"
TABLE = "J/ApJ/794/110/table1"
README_URL = "https://cdsarc.cds.unistra.fr/ftp/J/ApJ/794/110/ReadMe"
OUT_DIR = Path(__file__).resolve().parents[2] / "assets" / "data" / "playground"
STEM = "hd41248_harps"
# Printed precision of the catalogue columns (decimal places); see the ReadMe.
DECIMALS = {"BJD": 7, "RVel": 2, "e_RVel": 2, "S-index": 3, "BIS": 2, "FWHM": 2}


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_readme() -> dict:
    """Fetch the CDS ReadMe (optional; recorded when the service answers)."""
    req = urllib.request.Request(README_URL, headers={"User-Agent": "Mozilla/5.0 (site data export)"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            text = r.read().decode("latin-1")
        return {"url": README_URL, "fetched_utc": now(), "text": text}
    except Exception as e:  # noqa: BLE001
        return {"url": README_URL, "fetched_utc": now(), "error": f"{type(e).__name__}: {e}"}


def main() -> int:
    from astroquery.vizier import Vizier

    queried = now()
    v = Vizier(columns=["**"], row_limit=-1)
    tables = v.get_catalogs(CATALOGUE)
    table = next(t for t in tables if t.meta.get("name") == TABLE)
    n = len(table)
    cols = {}
    for name, dec in DECIMALS.items():
        col = table[name]
        if getattr(col, "mask", None) is not None and np.any(col.mask):
            print(f"column {name} has masked values; refusing to export", file=sys.stderr)
            return 1
        raw = np.asarray(col, dtype=np.float64)
        rounded = np.round(raw, dec)
        # The VOTable stores single precision for the m/s columns; rounding to the printed
        # precision recovers the catalogue text. Refuse if that is not true for every row.
        if np.max(np.abs(rounded - raw)) > 0.6 * 10.0 ** (-dec):
            print(f"column {name}: rounding changes a value by more than half a unit", file=sys.stderr)
            return 1
        cols[name] = rounded
    order = np.argsort(cols["BJD"])
    if not np.all(order == np.arange(n)):
        print("table is not in time order; sorting", file=sys.stderr)
    cols = {k: v[order] for k, v in cols.items()}
    if len(np.unique(cols["BJD"])) != n:
        print("duplicate epochs", file=sys.stderr)
        return 1

    def num(values, dec):
        return [float(f"{x:.{dec}f}") for x in values]

    rv = cols["RVel"]
    e_rv = cols["e_RVel"]
    bjd = cols["BJD"]
    data = {
        "star": "HD 41248",
        "source": {
            "service": "VizieR, Centre de Données astronomiques de Strasbourg",
            "catalogue": CATALOGUE,
            "table": TABLE,
            "reference": "Jenkins, J. S. and Tuomi, M. 2014, ApJ 794, 110",
            "doi": "10.1088/0004-637X/794/2/110",
            "instrument": "HARPS, ESO 3.6 m telescope, La Silla",
            "queried_utc": queried,
        },
        "n": n,
        "columns": {
            "bjd": "Barycentric Julian Date of observation (d), catalogue column BJD",
            "rv": "radial velocity (m/s), catalogue column RVel",
            "e_rv": "uncertainty in rv (m/s), catalogue column e_RVel",
            "s_index": "chromospheric activity S-index, catalogue column S-index",
            "bis": "bisector inverse slope (m/s), catalogue column BIS",
            "fwhm": "full width at half maximum of the cross-correlation function (m/s), catalogue column FWHM",
        },
        "bjd": num(bjd, 7),
        "rv": num(rv, 2),
        "e_rv": num(e_rv, 2),
        "s_index": num(cols["S-index"], 3),
        "bis": num(cols["BIS"], 2),
        "fwhm": num(cols["FWHM"], 2),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{STEM}.json").write_text(json.dumps(data, separators=(",", ":")) + "\n")

    readme = fetch_readme()
    meta = {
        "description": (
            "HARPS radial velocities of the G dwarf HD 41248 as published with Jenkins and Tuomi "
            "(2014), read from VizieR unchanged, for a teaching page that fits a quasi-periodic "
            "Gaussian process to them in the browser."
        ),
        "built_utc": now(),
        "script": "figures/playground/build_hd41248_rv.py",
        "query": {
            "library": "astroquery.vizier.Vizier(columns=['**'], row_limit=-1).get_catalogs('J/ApJ/794/110')",
            "table": TABLE,
            "queried_utc": queried,
            "rows_received": n,
            "rows_kept": n,
            "dropped": 0,
            "processing": [
                "values rounded to the catalogue's printed precision (the VOTable carries the m/s columns in single precision)",
                "rows sorted by BJD (the catalogue order was already chronological)",
                "no other change; the page subtracts the mean radial velocity when it loads",
            ],
        },
        "summary": {
            "first_bjd": float(f"{bjd[0]:.7f}"),
            "last_bjd": float(f"{bjd[-1]:.7f}"),
            "span_days": float(f"{bjd[-1] - bjd[0]:.4f}"),
            "rv_mean_m_s": float(f"{rv.mean():.4f}"),
            "rv_std_m_s": float(f"{rv.std(ddof=1):.4f}"),
            "rv_min_m_s": float(f"{rv.min():.2f}"),
            "rv_max_m_s": float(f"{rv.max():.2f}"),
            "e_rv_median_m_s": float(f"{np.median(e_rv):.4f}"),
            "e_rv_min_m_s": float(f"{e_rv.min():.2f}"),
            "e_rv_max_m_s": float(f"{e_rv.max():.2f}"),
        },
        "columns": data["columns"],
        "readme": readme,
        "licence": (
            "The table is the electronic supplement of Jenkins and Tuomi (2014, ApJ 794, 110), served "
            "by the CDS through VizieR. The authors and the journal hold the rights to the published "
            "table; it is reproduced here unchanged, with its reference, for teaching. The CDS asks "
            "that use of VizieR be acknowledged (Ochsenbein, Bauer and Marcout 2000, A&AS 143, 23; "
            "doi:10.26093/cds/vizier)."
        ),
        "credits": [
            "Jenkins, J. S. and Tuomi, M. 2014, ApJ 794, 110, doi:10.1088/0004-637X/794/2/110",
            "VizieR catalogue access tool, CDS, Strasbourg, France, doi:10.26093/cds/vizier",
            "Ochsenbein, F., Bauer, P. and Marcout, J. 2000, A&AS 143, 23, doi:10.1051/aas:2000169",
            "Observations made with the HARPS spectrograph on the ESO 3.6 m telescope at La Silla",
        ],
    }
    (OUT_DIR / f"{STEM}.meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"{n} rows, BJD {bjd[0]:.3f} to {bjd[-1]:.3f} ({bjd[-1] - bjd[0]:.1f} d), "
          f"RV mean {rv.mean():.3f} m/s, std {rv.std(ddof=1):.3f} m/s, median error {np.median(e_rv):.3f} m/s")
    print("readme:", "ok" if "text" in readme else readme.get("error"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
