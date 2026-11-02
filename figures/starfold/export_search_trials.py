"""Export the settings search of the recorded Starfold run for the schematic on the demo page.

Reads notebooks/runs/apogee/result.json from a Starfold checkout (the run behind
assets/data/starfold/apogee_run.json) and writes assets/data/starfold/apogee_trials.json: for each
trial its number, phase, state, score on the table, score on the structureless copy, the gap
between them and the settings tried.

Usage: python3 figures/starfold/export_search_trials.py --starfold /path/to/starfold
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--starfold", type=Path, required=True)
    args = ap.parse_args()
    run = args.starfold / "notebooks/runs/apogee"
    search = json.loads((run / "result.json").read_text())["search"]
    trials = [
        {"number": t["number"], "phase": t["phase"], "state": t["state"], "score": t["raw_score"], "copy_score": t["null_score"], "gap": t["score"], "params": t["params"]}
        for t in search["trials"]
    ]
    out = {
        "format": "starfold_apogee_trials 1",
        "source": "notebooks/runs/apogee/result.json of the Starfold repository, the run of apogee_run.json",
        "score": "the score of the setting on the table; copy_score is the same setting on a structureless copy; gap is the first minus the second",
        "selected_trial": search["candidates"][0]["trial_number"],
        "trials": trials,
    }
    (ROOT / "assets/data/starfold/apogee_trials.json").write_text(json.dumps(out, separators=(",", ":")) + "\n")
    print(len(trials), "trials")


if __name__ == "__main__":
    main()
