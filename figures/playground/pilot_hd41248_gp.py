#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "numpy>=1.26",
#     "scipy>=1.11",
# ]
# ///
"""Pilot run of the quasi-periodic Gaussian-process model behind the Gaussian-process playground.

The browser page at /playground/gaussian-processes/ runs a random-walk Metropolis sampler
over the five parameters of a quasi-periodic Gaussian process (eta1 to eta4 and the jitter s)
fitted to the HARPS radial velocities of HD 41248 (assets/data/playground/hd41248_harps.json).
This script runs the same model offline, with the same priors, to record

    the posterior mode (from several Nelder-Mead starts),
    a long pilot chain: medians, 16th and 84th percentiles, acceptance rate,
    the proposal step sizes the page uses (2.38 / sqrt(5) times the pilot's posterior spread
    in the sampling coordinates, the Roberts, Gelman and Gilks 1997 scaling),

and writes them to assets/data/playground/hd41248_gp_pilot.json. The page prints nothing from
this file; it fixes the numbers quoted in its text and the step sizes in gp-worker.js.

Model (times in days, velocities in m/s, y = rv minus its mean):
    k(t, t') = eta1^2 exp(-(t - t')^2 / (2 eta2^2) - 2 sin^2(pi (t - t') / eta3) / eta4^2)
    K = k + diag(sigma_i^2 + s^2)
    log L = -1/2 y^T K^-1 y - 1/2 log|K| - n/2 log(2 pi), by Cholesky factorisation
Priors (uniform in the sampling coordinate, which is ln for the log-uniform ones):
    eta1 ~ log-uniform(0.1, 50) m/s      eta2 ~ log-uniform(1, 1000) d
    eta3 ~ uniform(10, 40) d             eta4 ~ log-uniform(0.1, 10)
    s    ~ log-uniform(0.1, 20) m/s

Usage
    uv run figures/playground/pilot_hd41248_gp.py [--steps 60000] [--seed 1]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "assets" / "data" / "playground" / "hd41248_harps.json"
OUT = ROOT / "assets" / "data" / "playground" / "hd41248_gp_pilot.json"

NAMES = ["eta1", "eta2", "eta3", "eta4", "s"]
LOG = [True, True, False, True, True]  # sampled as ln(parameter)?
BOUNDS = [(0.1, 50.0), (1.0, 1000.0), (10.0, 40.0), (0.1, 10.0), (0.1, 20.0)]
START = [5.0, 50.0, 20.0, 1.0, 2.0]  # the page's fixed starting point


def to_theta(p):
    return np.array([np.log(v) if lg else v for v, lg in zip(p, LOG)])


def from_theta(th):
    return np.array([np.exp(v) if lg else v for v, lg in zip(th, LOG)])


class Model:
    def __init__(self, t, y, sigma):
        self.t = t
        self.y = y
        self.var = sigma**2
        self.tau = np.abs(t[:, None] - t[None, :])
        self.n = len(t)
        self.lo = to_theta([b[0] for b in BOUNDS])
        self.hi = to_theta([b[1] for b in BOUNDS])

    def kernel(self, tau, p):
        e1, e2, e3, e4, _ = p
        return e1**2 * np.exp(-(tau**2) / (2 * e2**2) - 2 * np.sin(np.pi * tau / e3) ** 2 / e4**2)

    def log_like(self, p):
        K = self.kernel(self.tau, p)
        K[np.diag_indices(self.n)] += self.var + p[4] ** 2
        try:
            c, low = cho_factor(K, lower=True, check_finite=False)
        except np.linalg.LinAlgError:
            return -np.inf
        alpha = cho_solve((c, low), self.y, check_finite=False)
        return -0.5 * self.y @ alpha - np.sum(np.log(np.diag(c))) - 0.5 * self.n * np.log(2 * np.pi)

    def log_post(self, th):
        if np.any(th < self.lo) or np.any(th > self.hi):
            return -np.inf
        return self.log_like(from_theta(th))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=60000)
    ap.add_argument("--adapt", type=int, default=8000)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    d = json.loads(DATA.read_text())
    bjd = np.array(d["bjd"])
    t = bjd - bjd[0]
    y = np.array(d["rv"]) - np.mean(d["rv"])
    sigma = np.array(d["e_rv"])
    m = Model(t, y, sigma)
    rng = np.random.default_rng(a.seed)

    # Posterior mode: Nelder-Mead from a few rotation periods and the page's start.
    best = None
    starts = [START] + [[3.0, 30.0, p, 0.7, 1.5] for p in (12, 15, 18, 22, 25, 28, 32, 36)]
    for s0 in starts:
        res = minimize(lambda th: -m.log_post(th), to_theta(s0), method="Nelder-Mead",
                       options={"xatol": 1e-4, "fatol": 1e-4, "maxiter": 4000})
        if best is None or res.fun < best.fun:
            best = res
    mode = from_theta(best.x)
    print("mode:", dict(zip(NAMES, np.round(mode, 4))), "log post", -best.fun)

    # Pilot chain: random-walk Metropolis with a diagonal proposal, adapted during the first
    # `adapt` steps towards about 25 percent acceptance, then fixed.
    th = to_theta(START)
    lp = m.log_post(th)
    step = np.array([0.1, 0.3, 1.0, 0.2, 0.1])
    chain = np.empty((a.steps, 5))
    lps = np.empty(a.steps)
    acc = 0
    acc_window = 0
    for i in range(a.steps):
        prop = th + step * rng.standard_normal(5)
        lp_prop = m.log_post(prop)
        if np.log(rng.random()) < lp_prop - lp:
            th, lp = prop, lp_prop
            acc += 1
            acc_window += 1
        chain[i] = th
        lps[i] = lp
        if i < a.adapt and (i + 1) % 200 == 0:
            rate = acc_window / 200
            step *= np.exp(0.6 * (rate - 0.25))
            acc_window = 0
            if (i + 1) % 2000 == 0:
                print(f"adapt {i + 1}: rate {rate:.2f} step {np.round(step, 3)}")
    post = chain[a.adapt:]
    rate = (acc - 0) / a.steps
    sd = post.std(axis=0)
    suggested = 2.38 / np.sqrt(5) * sd
    params = from_theta(post.T).T if False else np.column_stack([np.exp(post[:, j]) if LOG[j] else post[:, j] for j in range(5)])
    q = np.percentile(params, [16, 50, 84], axis=0)
    summary = {}
    for j, name in enumerate(NAMES):
        summary[name] = {
            "mode": float(f"{mode[j]:.4g}"),
            "p16": float(f"{q[0, j]:.4g}"),
            "median": float(f"{q[1, j]:.4g}"),
            "p84": float(f"{q[2, j]:.4g}"),
            "coordinate": "ln" if LOG[j] else "linear",
            "posterior_sd_in_coordinate": float(f"{sd[j]:.4g}"),
            "step_size": float(f"{suggested[j]:.4g}"),
        }
        print(f"{name:5s} mode {mode[j]:9.4f}  median {q[1, j]:9.4f}  16-84 {q[0, j]:9.4f} {q[2, j]:9.4f}  "
              f"sd({'ln' if LOG[j] else 'lin'}) {sd[j]:.4f}  step {suggested[j]:.4f}")
    print(f"acceptance {rate:.3f} over {a.steps} steps; final adapted step {np.round(step, 4)}")
    lp_post = lps[a.adapt:]
    out = {
        "description": "Pilot run of the playground's quasi-periodic Gaussian-process model on the HD 41248 HARPS velocities.",
        "built_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "script": "figures/playground/pilot_hd41248_gp.py",
        "data": "assets/data/playground/hd41248_harps.json",
        "n": int(m.n),
        "rv_mean_subtracted_m_s": float(f"{np.mean(d['rv']):.4f}"),
        "priors": {n: {"type": "log-uniform" if lg else "uniform", "low": b[0], "high": b[1]} for n, lg, b in zip(NAMES, LOG, BOUNDS)},
        "start": dict(zip(NAMES, START)),
        "sampler": {
            "kind": "random-walk Metropolis, Gaussian proposal, diagonal covariance",
            "steps": a.steps,
            "adapted_during_first_steps": a.adapt,
            "discarded_as_burn_in": a.adapt,
            "seed": a.seed,
            "acceptance_rate": float(f"{rate:.4f}"),
            "final_adapted_step": [float(f"{v:.4g}") for v in step],
            "page_step_sizes_rule": "2.38 / sqrt(5) times the posterior standard deviation in the sampling coordinate (Roberts, Gelman and Gilks 1997)",
            "page_step_sizes": [float(f"{v:.4g}") for v in suggested],
        },
        "log_posterior": {"mode": float(f"{-best.fun:.3f}"), "median": float(f"{np.median(lp_post):.3f}"),
                          "p16": float(f"{np.percentile(lp_post, 16):.3f}"), "p84": float(f"{np.percentile(lp_post, 84):.3f}")},
        "posterior": summary,
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
