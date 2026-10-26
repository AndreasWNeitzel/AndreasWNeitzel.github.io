#!/usr/bin/env python3
"""Export the recorded Starfold run on the APOGEE DR19 example table for the demo page.

The page /software/starfold-demo/ shows the run that the Starfold tutorials load with
``starfold.load("notebooks/runs/apogee")`` and ``bench.datasets.example_table()``
(docs/tutorial/apogee.md and docs/tutorial/apogee-checks.md in the Starfold
repository). This script reads that run, the table and the recorded calibration test
from a Starfold checkout, recomputes the two-dimensional map that HDBSCAN cut (the
call in notebooks/02_apogee.ipynb: the selected setting refitted on all stars with
the seed that recover used), checks that the refit gives back the recorded groups
exactly, and writes three files to assets/data/starfold/:

    apogee_run.bin        little-endian arrays (layout in the header)
    apogee_run.json       header: layout, columns, groups, refits, flags and checks
    apogee_run.meta.json  provenance: checksums, versions, seed, sources and credits

Every value comes from the run, the table or the calibration record, or is counted
from them (the refit matches and the example stars, each with its rule). Nothing is
filled in: the script stops when a recorded quantity is missing or does not match.

The map needs the engine the run used. The recorded run used RAPIDS cuML on an NVIDIA
GPU, so run the script in a Starfold environment that has cuML, from the root of the
website repository:

    UV_PROJECT_ENVIRONMENT=/path/to/starfold/.venv-rapids \\
        uv run --project /path/to/starfold --no-sync \\
        python figures/starfold/export_apogee_run.py --starfold /path/to/starfold

``--no-sync`` keeps uv from changing that environment. The Starfold checkout is only
read, and Python is told not to write bytecode into it.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

sys.dont_write_bytecode = True  # the Starfold checkout is read, never written

import numpy as np  # noqa: E402

SITE = Path(__file__).resolve().parents[2]
OUT_DIR = SITE / "assets" / "data" / "starfold"
STEM = "apogee_run"
RUN = Path("notebooks/runs/apogee")
TABLE = Path("bench/data/stellar_chemokinematics_apogee_dr19.npz")
TABLE_NOTE = Path("bench/data/stellar_chemokinematics_apogee_dr19.md")
NULL_RECORD = Path("bench/results/apogee_null.json")
NOTEBOOK = Path("notebooks/runs/exec_02_apogee.py")
TUTORIALS = ("docs/tutorial/apogee.md", "docs/tutorial/apogee-checks.md")
REFERENCE_SEED_ID = (
    4  # recover() fits the selected setting on all rows with derive_seed(seed, 4)
)
UNSAMPLED = -2  # refit label of a star the refit did not draw
NOISE = -1  # label of an unassigned star

# Label, unit and source column of each feature, after the table's provenance note.
COLUMNS = {
    "fe_h": ("[Fe/H]", "dex", "ASPCAP FE_H_ATM: iron abundance relative to the Sun"),
    "alpha_m": (
        "[α/M]",
        "dex",
        "ASPCAP ALPHA_M_ATM: alpha elements relative to all metals",
    ),
    "mg_fe": ("[Mg/Fe]", "dex", "ASPCAP MG_H_ATM minus FE_H_ATM"),
    "J_R": ("J_R", "kpc km/s", "radial action from galpy in the McMillan17 potential"),
    "J_z": (
        "J_z",
        "kpc km/s",
        "vertical action from galpy in the McMillan17 potential",
    ),
    "L_z": ("L_z", "kpc km/s", "angular momentum about the Galactic axis, from galpy"),
    "ecc": ("eccentricity", "", "orbital eccentricity from galpy"),
    "E": ("E", "km²/s²", "orbital energy from galpy in the McMillan17 potential"),
}
PERCENTILES = (0.1, 1, 2, 5, 50, 95, 98, 99, 99.9)
MAP_LIBRARIES = (
    "cuml-cu13",
    "cuml-cu12",
    "umap-learn",
    "hdbscan",
    "numpy",
    "scikit-learn",
)


def sha256(path: Path) -> str:
    """SHA-256 of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def installed(package: str) -> bool:
    """Whether a distribution is installed in the running environment."""
    try:
        version(package)
    except PackageNotFoundError:
        return False
    return True


def git(root: Path, *args: str) -> str:
    """Output of a read-only git command in the Starfold checkout."""
    done = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return done.stdout.strip()


def fail(message: str) -> None:
    """Stop the export with a message."""
    sys.exit(f"export_apogee_run: {message}")


def recorded_table_sha256(note: Path) -> str:
    """The SHA-256 of the npz as written in the table's provenance note."""
    found = re.search(
        r"SHA-256 of the npz:\s*`([0-9a-f]{64})`", note.read_text(encoding="utf-8")
    )
    if found is None:
        fail(f"no npz SHA-256 found in {note}")
    return found.group(1)


def flag_meanings(notebook: Path) -> dict[str, str]:
    """The MEANING dictionary of the APOGEE notebook, read from its source."""
    tree = ast.parse(notebook.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "MEANING" for t in node.targets
        ):
            return ast.literal_eval(node.value)
    fail(f"no MEANING dictionary in {notebook}")
    return {}


def refit_matches(
    world_labels: np.ndarray, labels: np.ndarray, n_groups: int
) -> list[dict]:
    """Match each refit's groups to the groups of the fit on all stars.

    For every group, the refit group with the largest Jaccard index is its match, ties
    going to the lowest id, as in starfold.worlds. A refit group that is the match of
    no group (or of a group whose stronger match took it) keeps no counterpart.
    """
    out = []
    for k, row in enumerate(world_labels):
        rows = np.flatnonzero(row != UNSAMPLED)
        lw = row[rows].astype(np.int64)
        assigned = lw >= 0
        ids, cluster = np.unique(lw[assigned], return_inverse=True)
        if not np.array_equal(ids, np.arange(ids.size)):
            fail(f"refit {k} labels are not 0..K-1: {ids.tolist()}")
        ref = np.where(labels[rows] >= 0, labels[rows], n_groups)
        table = np.zeros((ids.size, n_groups + 1))
        np.add.at(table, (cluster, ref[assigned]), 1.0)
        members = np.bincount(ref, minlength=n_groups + 1)[:n_groups].astype(np.float64)
        shared = table[:, :n_groups]
        size = table.sum(axis=1)
        union = members[None, :] + size[:, None] - shared
        jaccard = np.divide(shared, union, out=np.zeros_like(shared), where=union > 0)
        best = jaccard.argmax(axis=0)
        strength = jaccard[best, np.arange(n_groups)]
        match = [-1] * ids.size
        for g in np.argsort(-strength, kind="stable"):
            c = int(best[g])
            if match[c] == -1 and strength[g] > 0:
                match[c] = int(g)
        out.append(
            {
                "drawn": int(rows.size),
                "unassigned": int((~assigned).sum()),
                "sizes": [int(v) for v in size],
                "match": match,
                "jaccard": [float(v) for v in strength],
                "overlap": [[int(v) for v in r] for r in table],
            }
        )
    return out


def examples(
    x: np.ndarray,
    labels: np.ndarray,
    support: np.ndarray,
    unresolved: np.ndarray,
    median: np.ndarray,
) -> list[dict]:
    """Example stars for the inspector, each chosen by a stated rule."""
    centre, spread = x.mean(axis=0), x.std(axis=0)
    z = (x - centre) / spread
    picks = []
    for g in range(median.shape[0]):
        members = np.flatnonzero(labels == g)
        target = (median[g] - centre) / spread
        row = int(members[np.argmin(np.linalg.norm(z[members] - target, axis=1))])
        picks.append(
            {
                "row": row,
                "label": f"A typical group {g} star",
                "rule": f"the member of group {g} nearest, in the eight standardised columns, "
                "to the group's median over the refits",
            }
        )
    second = np.sort(support, axis=1)[:, -2]
    row = int(np.argmax(second))
    picks.append(
        {
            "row": row,
            "label": "A star split between groups",
            "rule": "the star whose second-largest support for a group is the largest of all stars",
        }
    )
    noise = np.flatnonzero(labels < 0)
    order = noise[np.argsort(unresolved[noise], kind="stable")]
    row = int(order[(order.size - 1) // 2])
    picks.append(
        {
            "row": row,
            "label": "A typical unassigned star",
            "rule": "the unassigned star with the median unresolved share among unassigned stars",
        }
    )
    return picks


def pack_nibbles(values: np.ndarray) -> np.ndarray:
    """Two 4-bit values per byte, the first in the low nibble."""
    flat = values.reshape(-1).astype(np.uint8)
    if flat.size % 2:
        flat = np.append(flat, np.uint8(0))
    return (flat[0::2] | (flat[1::2] << 4)).astype(np.uint8)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--starfold",
        type=Path,
        default=SITE.parent / "starfold",
        help="Starfold checkout holding the recorded run (default: next to this repository)",
    )
    args = parser.parse_args()
    root = args.starfold.resolve()
    sys.path.insert(0, str(root))

    import starfold
    from bench.datasets import EXAMPLE_SHA256, example_table
    from starfold._engine import derive_seed
    from starfold.backend import fit_pipeline
    from starfold.result import matrix_fingerprint
    from starfold.worlds import summarize_worlds

    # ---------------------------------------------------------------- inputs
    table_path, note_path = root / TABLE, root / TABLE_NOTE
    table_sha = sha256(table_path)
    if not (table_sha == recorded_table_sha256(note_path) == EXAMPLE_SHA256):
        fail("the table's SHA-256 differs from its provenance note")
    x, names = example_table()  # also verifies the digest, the row count and the names
    with np.load(table_path, allow_pickle=False) as bundle:
        x32 = np.asarray(bundle["X"])
        source_id = np.asarray(bundle["source_id"])
    if x32.dtype != np.float32 or not np.array_equal(x32.astype(np.float64), x):
        fail("the table's float32 values do not match example_table()")
    if (
        tuple(names) != tuple(COLUMNS)
        or source_id.dtype != np.int64
        or (source_id <= 0).any()
    ):
        fail("unexpected columns or source_id values in the table")
    if np.unique(source_id).size != source_id.size:
        fail("duplicate source_id values in the table")

    result = starfold.load(
        root / RUN
    )  # verifies the manifest checksums and re-derives the flags
    prov = result.provenance
    n = x.shape[0]
    if not np.array_equal(result.kept_rows, np.arange(n)) or prov["n_input_rows"] != n:
        fail("the run did not keep every row of the table in order")
    if prov["input_fingerprint"] != matrix_fingerprint(x):
        fail("the run's input fingerprint does not match the table")

    # ---------------------------------------------------------------- the map HDBSCAN cut
    if result.deployed_params.n_components != 2:
        fail("the selected setting does not embed in two dimensions")
    engine = prov["engine_resolved"]
    seed = derive_seed(prov["random_state"], REFERENCE_SEED_ID)
    fit = fit_pipeline(
        x,
        result.deployed_params,
        seed=seed,
        engine=engine,
        scaling=prov["config"]["scaling"],
    )
    if not np.array_equal(fit.labels, result.labels):
        fail(f"the {engine} refit did not reproduce the recorded groups")
    embedding = np.asarray(fit.embedding, dtype=np.float32)

    # ---------------------------------------------------------------- refits
    labels = result.labels.astype(np.int64)
    worlds = result.worlds
    group_ids = np.unique(labels[labels >= 0])
    n_groups = int(group_ids.size)
    if not np.array_equal(group_ids, np.arange(n_groups)):
        fail("the groups are not numbered 0..G-1")
    again = summarize_worlds(worlds.world_labels, result.labels, x, propagated=False)
    for name in ("support", "unresolved", "group_recurrence"):
        if not np.allclose(getattr(again, name), getattr(worlds, name), equal_nan=True):
            fail(f"recomputed {name} differs from the stored values")
    support = np.asarray(worlds.support, dtype=np.float32)
    unresolved = np.asarray(worlds.unresolved, dtype=np.float32)
    if np.isnan(support).any() or np.isnan(unresolved).any():
        fail("a star was never drawn by a refit")
    if np.abs(support.sum(axis=1) + unresolved - 1.0).max() > 1e-4:
        fail("support and unresolved do not sum to one")
    refits = refit_matches(worlds.world_labels, labels, n_groups)
    jaccard = np.array([r["jaccard"] for r in refits])
    if not np.allclose(jaccard.mean(axis=0), worlds.group_recurrence, atol=1e-6):
        fail("matched Jaccard indices do not average to the stored recurrence")
    counts = [int(v) for v in worlds.count_values]
    if counts != [len(r["sizes"]) for r in refits]:
        fail("refit group counts differ from the stored count_values")
    n_sampled = np.asarray(worlds.n_sampled)
    if not np.array_equal(n_sampled, (worlds.world_labels != UNSAMPLED).sum(axis=0)):
        fail("n_sampled differs from the refit labels")
    if worlds.world_labels.min() < UNSAMPLED or worlds.world_labels.max() > 13:
        fail("refit labels do not fit in four bits")

    # ---------------------------------------------------------------- calibration record
    null_record = json.loads((root / NULL_RECORD).read_text(encoding="utf-8"))
    if (
        null_record["observed"] != result.null.observed
        or null_record["observed"] != result.search.exploration_max
    ):
        fail("the calibration record's observed statistic differs from the run's")
    record_input = root / null_record["result"]
    record_arrays = record_input / "arrays.npz"
    run_manifest = json.loads(
        (root / RUN / "manifest.json").read_text(encoding="utf-8")
    )
    same_arrays = (
        record_arrays.exists() and sha256(record_arrays) == run_manifest["arrays.npz"]
    )

    # ---------------------------------------------------------------- binary
    seeds = [int(s) for s in worlds.world_seeds]
    arrays = [
        ("source_id", source_id.astype("<u8"), [n]),
        ("features", x32.astype("<f4"), [n, x32.shape[1]]),
        ("map", embedding.astype("<f4"), [n, 2]),
        ("group", labels.astype(np.int8), [n]),
        ("support", support.astype("<f4"), [n, n_groups]),
        ("unresolved", unresolved.astype("<f4"), [n]),
        ("n_sampled", n_sampled.astype(np.uint8), [n]),
        (
            "refit_labels",
            pack_nibbles(worlds.world_labels.astype(np.int64) - UNSAMPLED),
            [len(seeds), n],
        ),
    ]
    blob, layout = bytearray(), []
    for name, arr, shape in arrays:
        entry = {
            "name": name,
            "dtype": arr.dtype.name,
            "offset": len(blob),
            "length": int(arr.size),
            "shape": shape,
        }
        if name == "refit_labels":
            entry["decode"] = (
                "two 4-bit values per byte, low nibble first; label = value - 2"
            )
        layout.append(entry)
        blob += arr.tobytes()
        blob += b"\0" * (-len(blob) % 8)

    # ---------------------------------------------------------------- header
    meaning = flag_meanings(root / NOTEBOOK)
    centre, spread = x.mean(axis=0), x.std(axis=0)
    pct = np.percentile(x, PERCENTILES, axis=0)
    columns = [
        {
            "name": name,
            "label": COLUMNS[name][0],
            "unit": COLUMNS[name][1],
            "source": COLUMNS[name][2],
            "mean": float(centre[j]),
            "std": float(spread[j]),
            "percentiles": {
                f"{p:g}": float(pct[i, j]) for i, p in enumerate(PERCENTILES)
            },
        }
        for j, name in enumerate(names)
    ]
    groups = [
        {
            "id": g,
            "size": int((labels == g).sum()),
            "recurrence": float(worlds.group_recurrence[g]),
            "recurrence_band": [float(v) for v in worlds.group_recurrence_band[g]],
            "median": [float(v) for v in worlds.property_median[g]],
            "band": [[float(a), float(b)] for a, b in worlds.property_band[g]],
        }
        for g in range(n_groups)
    ]
    search = result.search
    selected_trial = search.candidates[0].trial_number
    consensus = result.consensus
    default_labels = result.default_labels
    header = {
        "format": "starfold_apogee_run 1",
        "binary": f"{STEM}.bin",
        "byte_order": "little",
        "n": n,
        "arrays": layout,
        "columns": columns,
        "map": {
            "axes": "UMAP 1 and UMAP 2 of the map HDBSCAN cut; they have no units",
            "how": "the selected setting refitted on all stars with the seed recover used for that fit "
            f"(derive_seed({prov['random_state']}, {REFERENCE_SEED_ID})) on {engine}; it gives back "
            "the recorded groups exactly",
        },
        "groups": groups,
        "unassigned": int((labels < 0).sum()),
        "unresolved_mass": float(worlds.unresolved_mass),
        "count_interval": [int(v) for v in worlds.count_interval],
        "refits": {
            "n": len(seeds),
            "fraction": prov["config"]["world_fraction"],
            "n_groups": counts,
            "agreement": [float(v) for v in worlds.world_agreement],
            "seeds": seeds,
            "matches": refits,
            "match_rule": "each group's match is the refit group with the largest Jaccard index, ties to "
            "the lowest id (as for recurrence); a refit group matched to no group has no counterpart",
            "agreement_rule": "adjusted Rand index, floored at 0, times joint coverage between the refit "
            "and the fit on all stars, on the refit's stars",
        },
        "consensus": {
            "rows": consensus.n_rows,
            "subsampled": consensus.subsampled,
            "within": consensus.within_association,
            "between": consensus.between_association,
            "contrast": consensus.contrast,
            "agreement": consensus.agreement,
            "cut_assigned": int((consensus.labels >= 0).sum()),
        },
        "flags": [{"name": f, "meaning": meaning[f]} for f in result.flags],
        "calibration": {
            "attached_to_run": False,
            "flag_if_attached": {
                "name": "no_structure_supported",
                "meaning": meaning["no_structure_supported"],
            },
            "statistic": null_record["statistic_name"],
            "observed": null_record["observed"],
            "family": null_record["families"][0],
            "copies": null_record["n_realisations"][0],
            "at_or_above": null_record["exceedances"][0],
            "copy_values": null_record["null_values"][0],
            "p_value": null_record["p_value"],
            "p_interval": null_record["p_intervals"][0],
            "alpha": null_record["alpha"],
            "structure_supported": null_record["structure_supported"],
            "fits": null_record["n_fits"],
            "seconds": null_record["seconds"],
        },
        "search": {
            "trials": len(search.trials),
            "trial_budget": prov["config"]["n_trials"],
            "complete": search.n_completed,
            "pruned": search.n_pruned,
            "stop_reason": search.stop_reason,
            "selected_trial": selected_trial,
            "score_selected": search.score_selected,
            "score_default": search.score_default,
            "gap_selected": search.gap_selected,
            "gap_default": search.gap_default,
            "exploration_max": search.exploration_max,
        },
        "settings": {
            "on_subsets": result.params.to_dict(),
            "all_stars": result.deployed_params.to_dict(),
            "defaults": result.default_params.to_dict(),
        },
        "defaults_fit": {
            "groups": int(np.unique(default_labels[default_labels >= 0]).size),
            "unassigned": int((default_labels < 0).sum()),
        },
        "run": {
            "starfold_version": prov["starfold_version"],
            "random_state": prov["random_state"],
            "engine": engine,
            "fits": prov["total_fits"],
            "stage_fits": prov["stage_fits"],
            "seconds": prov["stage_seconds"],
            "peak_rss_mb": prov["peak_rss_mb"],
        },
        "examples": examples(x, labels, support, unresolved, worlds.property_median),
        "provenance": f"{STEM}.meta.json",
    }

    # ---------------------------------------------------------------- provenance
    head = git(root, "rev-parse", "HEAD")
    meta = {
        "description": (
            "The recorded Starfold run on the APOGEE DR19 example table (9,242 stars, eight "
            "chemo-dynamical columns), with the two-dimensional map HDBSCAN cut, for the "
            "interactive demo at /software/starfold-demo/."
        ),
        "exported_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "script": "figures/starfold/export_apogee_run.py",
        "starfold": {
            "repository": "https://github.com/AndreasWNeitzel/starfold",
            "version_in_run": prov["starfold_version"],
            "checkout_commit": head,
            "checkout_describe": git(root, "describe", "--tags", "--always", "--dirty"),
            "checkout_clean": git(root, "status", "--porcelain", "--untracked-files=no")
            == "",
            "run_last_changed_in": git(
                root, "log", "-1", "--format=%H", "--", str(RUN)
            ),
            "release_tag": "v0.2.0",
            "release_commit": git(root, "rev-list", "-n", "1", "v0.2.0"),
            "tutorials": list(TUTORIALS),
            "notebook": "notebooks/02_apogee.ipynb",
        },
        "run": {
            "path": str(RUN),
            "loaded_with": 'starfold.load("notebooks/runs/apogee")',
            "manifest": run_manifest,
            "random_state": prov["random_state"],
            "engine_requested": prov["engine_requested"],
            "engine_resolved": engine,
            "libraries": prov["libraries"],
            "python": prov["python"],
            "config": prov["config"],
            "hardware_in_tutorial": "laptop NVIDIA RTX 3060 with RAPIDS cuML (docs/tutorial/apogee.md)",
        },
        "table": {
            "path": str(TABLE),
            "loaded_with": "bench.datasets.example_table()",
            "sha256": table_sha,
            "sha256_in_note": recorded_table_sha256(note_path),
            "note": str(TABLE_NOTE),
            "rows": n,
            "columns": list(names),
            "values": "float32 as stored in the table, unchanged",
            "use": "The provenance note calls the bundled table a convenience and says not to use it "
            "for scientific work; anything citable must be rebuilt from APOGEE and Gaia.",
        },
        "map": {
            "call": "starfold.backend.fit_pipeline(x, result.deployed_params, "
            f"seed=derive_seed({prov['random_state']}, {REFERENCE_SEED_ID}), engine='{engine}', "
            f"scaling='{prov['config']['scaling']}')",
            "check": "the refit's labels equal the recorded labels for every star",
            "seed": seed,
            "libraries": {lib: version(lib) for lib in MAP_LIBRARIES if installed(lib)},
        },
        "calibration": {
            "path": str(NULL_RECORD),
            "sha256": sha256(root / NULL_RECORD),
            "run_by": "python -m bench.null_stage (docs/tutorial/apogee-checks.md, step 10)",
            "record_input": null_record["result"],
            "record_input_arrays_identical_to_run": same_arrays,
            "check": "the record's observed statistic equals the run's exploration_max exactly",
            "attached_to_run": "no; attaching it with --update-result would add the flag no_structure_supported",
        },
        "derived": {
            "refit matches": header["refits"]["match_rule"],
            "examples": [e["rule"] for e in header["examples"]],
            "column statistics": "mean, standard deviation (ddof 0) and linear percentiles over all stars",
        },
        "credits": [
            "APOGEE DR19, SDSS-V: SDSS Collaboration 2025, arXiv:2507.07093",
            "ASPCAP abundances in DR19: Meszaros et al. 2025, AJ 170, 96, doi:10.3847/1538-3881/ade4b9",
            "ASPCAP method: Abdurro'uf et al. 2022, ApJS 259, 35, doi:10.3847/1538-4365/ac4414",
            "Gaia DR3: Gaia Collaboration, Vallenari et al. 2023, A&A 674, A1, doi:10.1051/0004-6361/202243940",
            "galpy: Bovy 2015, ApJS 216, 29, doi:10.1088/0067-0049/216/2/29",
            "McMillan17 potential: McMillan 2017, MNRAS 465, 76, doi:10.1093/mnras/stw2759",
            "UMAP: McInnes, Healy and Melville 2018, arXiv:1802.03426",
            "HDBSCAN: Campello, Moulavi and Sander 2013, doi:10.1007/978-3-642-37456-2_14",
            "Optuna: Akiba et al. 2019, arXiv:1907.10902",
        ],
        "licence": (
            "Starfold and its outputs: MIT. Gaia data: ESA/Gaia/DPAC, CC BY-SA 3.0 IGO; the files "
            "derived from them are shared under the same licence. APOGEE data: public SDSS data, "
            "credited as above."
        ),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{STEM}.bin").write_bytes(bytes(blob))
    (OUT_DIR / f"{STEM}.json").write_text(
        json.dumps(header, separators=(",", ":"), ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    meta["files"] = {
        f"{STEM}.bin": sha256(OUT_DIR / f"{STEM}.bin"),
        f"{STEM}.json": sha256(OUT_DIR / f"{STEM}.json"),
    }
    (OUT_DIR / f"{STEM}.meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    sizes = {g["id"]: g["size"] for g in groups}
    total = sum((OUT_DIR / f).stat().st_size for f in (f"{STEM}.bin", f"{STEM}.json"))
    print(
        f"{n:,} stars, groups {sizes}, unassigned {header['unassigned']:,}, flags {list(result.flags)}; "
        f"wrote {total / 1e6:.2f} MB to {OUT_DIR}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
