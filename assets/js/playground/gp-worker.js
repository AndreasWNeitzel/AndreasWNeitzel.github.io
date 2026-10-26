// Metropolis sampler for the Gaussian-process playground, run in a module Web Worker.
// Model: radial velocities y (mean subtracted) at times t with uncertainties sigma_i,
// a quasi-periodic kernel with parameters eta1 (amplitude, m/s), eta2 (evolution
// timescale, d), eta3 (rotation period, d) and eta4 (smoothing), plus a jitter s (m/s)
// added in quadrature to the diagonal. The log marginal likelihood comes from a Cholesky
// factorisation. The priors are uniform in the sampling coordinate, which is the natural
// logarithm for the log-uniform parameters. Every state of the chain is stored, repeats
// included, as the sampler requires.
//
// In:  init {t, y, var}, run, pause, step {count}, reset {start}, config {stepScale,
//      burn, draws}, grid {x}
// Out: ready {...}, state {...} after every change and about every 60 ms while running,
//      predictive {...} when a marginalised prediction on the grid is finished.
import { cholesky, forwardSolve, logLikelihood, mulberry32, gaussian } from "./gp-math.js";

// The page's priors. Log-uniform parameters are sampled as ln(parameter).
const PRIOR = [
  { name: "eta1", log: true, lo: 0.1, hi: 50, unit: "m/s" },
  { name: "eta2", log: true, lo: 1, hi: 1000, unit: "d" },
  { name: "eta3", log: false, lo: 10, hi: 40, unit: "d" },
  { name: "eta4", log: true, lo: 0.1, hi: 10, unit: "" },
  { name: "s", log: true, lo: 0.1, hi: 20, unit: "m/s" },
];
const D = PRIOR.length;
const COLS = D + 1; // the chain stores the parameters in natural units and the log posterior
// The fixed starting point and the proposal step sizes in the sampling coordinates
// (2.38 / sqrt(5) times the posterior spread of a 60,000-step pilot run of the same model:
// figures/playground/pilot_hd41248_gp.py, recorded in assets/data/playground/hd41248_gp_pilot.json).
const START = [5, 50, 20, 1, 2];
const STEP = [0.1268, 0.2363, 0.5337, 0.1678, 0.1446];
const SEED = 11;
const SLICE_MS = 40;
const MAX_STEPS = 200000;
const PREDICT_EVERY_MS = 1500;
const CURVES_KEPT = 12;

let data = null; // {n, t, y, var, tau}
let K = null; // scratch n by n
let theta = null; // current state, sampling coordinates
let lp = -Infinity;
let chain = new Float64Array(COLS * 4096);
let steps = 0;
let accepted = 0;
let sent = 0;
let status = "idle";
let running = false;
let timer = 0;
let run = 0;
let rand = mulberry32(SEED);
let cfg = { stepScale: 1, burn: 0.25, draws: 32, start: "fixed" };
let grid = null;
let job = null;
let lastPredict = 0;

const lo = PRIOR.map((p) => (p.log ? Math.log(p.lo) : p.lo));
const hi = PRIOR.map((p) => (p.log ? Math.log(p.hi) : p.hi));
const natural = (th) => th.map((v, i) => (PRIOR[i].log ? Math.exp(v) : v));
const coordinate = (p) => p.map((v, i) => (PRIOR[i].log ? Math.log(v) : v));

function prepare(msg) {
  const n = msg.t.length;
  const tau = new Float64Array(n * n);
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) tau[i * n + j] = msg.t[i] - msg.t[j];
  data = { n, t: msg.t, y: msg.y, var: msg.var, tau };
  K = new Float64Array(n * n);
}

// Lower triangle of K for the parameters p (natural units), then its Cholesky factor in place.
function factor(p, out) {
  const { n, tau } = data;
  const e1 = p[0] * p[0];
  const e2 = 2 * p[1] * p[1];
  const e3 = Math.PI / p[2];
  const e4 = 2 / (p[3] * p[3]);
  const s2 = p[4] * p[4];
  for (let i = 0; i < n; i++) {
    const im = i * n;
    for (let j = 0; j < i; j++) {
      const d = tau[im + j];
      const sn = Math.sin(e3 * d);
      out[im + j] = e1 * Math.exp(-(d * d) / e2 - e4 * sn * sn);
    }
    out[im + i] = e1 + data.var[i] + s2;
  }
  return cholesky(out, n);
}

function logPosterior(th) {
  for (let i = 0; i < D; i++) if (!(th[i] >= lo[i] && th[i] <= hi[i])) return -Infinity;
  if (!factor(natural(th), K)) return -Infinity;
  return logLikelihood(K, data.n, data.y).value;
}

function record(th, value) {
  if ((steps + 1) * COLS > chain.length) {
    const bigger = new Float64Array(chain.length * 2);
    bigger.set(chain);
    chain = bigger;
  }
  const p = natural(th);
  const base = steps * COLS;
  for (let i = 0; i < D; i++) chain[base + i] = p[i];
  chain[base + D] = value;
  steps += 1;
}

function metropolisStep() {
  const prop = new Array(D);
  for (let i = 0; i < D; i++) prop[i] = theta[i] + cfg.stepScale * STEP[i] * gaussian(rand);
  const lpProp = logPosterior(prop);
  if (Math.log(1 - rand()) < lpProp - lp) {
    theta = prop;
    lp = lpProp;
    accepted += 1;
  }
  record(theta, lp);
}

// ---------------------------------------------------------------- marginalised prediction
// The prediction on the grid averages the conditional distribution of the latent function
// over posterior samples: the mean of the mixture is the mean of the conditional means and
// its variance is E[var_i + mean_i^2] - mean^2. Samples are taken at even spacing from the
// part of the chain after burn-in; before the first step the starting point alone is used.
function startJob() {
  if (!grid || !data) return;
  const m = grid.length;
  const burn = Math.floor(cfg.burn * steps);
  const avail = steps - burn;
  let rows;
  if (steps === 0) rows = [-1];
  else {
    const count = Math.min(cfg.draws, avail);
    rows = Array.from({ length: count }, (_, k) => burn + Math.floor(((k + 0.5) * avail) / count));
  }
  job = {
    rows, next: 0, m, burn, steps,
    sum: new Float64Array(m), sumSq: new Float64Array(m), curves: [],
    L: new Float64Array(data.n * data.n), row: new Float64Array(data.n), v: new Float64Array(data.n),
  };
}

function jobParams(row) {
  if (row < 0) return natural(theta);
  const p = new Array(D);
  for (let i = 0; i < D; i++) p[i] = chain[row * COLS + i];
  return p;
}

function jobSample() {
  const { n, t, y } = data;
  const p = jobParams(job.rows[job.next]);
  const { L, row, v, m } = job;
  if (!factor(p, L)) { job.next += 1; return; }
  const alpha = logLikelihood(L, n, y).alpha;
  const e1 = p[0] * p[0];
  const e2 = 2 * p[1] * p[1];
  const e3 = Math.PI / p[2];
  const e4 = 2 / (p[3] * p[3]);
  const curve = job.curves.length < CURVES_KEPT ? new Float32Array(m) : null;
  for (let i = 0; i < m; i++) {
    const x = grid[i];
    let mean = 0;
    for (let j = 0; j < n; j++) {
      const d = x - t[j];
      const sn = Math.sin(e3 * d);
      row[j] = e1 * Math.exp(-(d * d) / e2 - e4 * sn * sn);
      mean += row[j] * alpha[j];
    }
    forwardSolve(L, n, row, v);
    let vv = e1;
    for (let j = 0; j < n; j++) vv -= v[j] * v[j];
    job.sum[i] += mean;
    job.sumSq[i] += Math.max(0, vv) + mean * mean;
    if (curve) curve[i] = mean;
  }
  if (curve) job.curves.push(curve);
  job.next += 1;
}

function finishJob() {
  const { m, sum, sumSq, curves } = job;
  const count = job.rows.length;
  const mean = new Float32Array(m);
  const sd = new Float32Array(m);
  for (let i = 0; i < m; i++) {
    const mu = sum[i] / count;
    mean[i] = mu;
    sd[i] = Math.sqrt(Math.max(0, sumSq[i] / count - mu * mu));
  }
  self.postMessage({
    type: "predictive", run, x: grid, mean, sd, curves, samples: count, burn: job.burn, steps: job.steps,
  }, [mean.buffer, sd.buffer, ...curves.map((c) => c.buffer)]);
  job = null;
  lastPredict = performance.now();
}

// Works on the pending job for about `ms` milliseconds.
function advanceJob(ms) {
  if (!job) return;
  const t0 = performance.now();
  while (job.next < job.rows.length && performance.now() - t0 < ms) jobSample();
  if (job.next >= job.rows.length) finishJob();
}

function finishJobNow() {
  while (job) advanceJob(50);
}

// ---------------------------------------------------------------- messages out
function post() {
  const fresh = chain.slice(sent * COLS, steps * COLS);
  sent = steps;
  self.postMessage({
    type: "state", run, status, steps, accepted, rows: fresh, cols: COLS,
    current: natural(theta), lp, maxSteps: MAX_STEPS,
  }, [fresh.buffer]);
}

function stop(reason) {
  running = false;
  clearTimeout(timer);
  status = reason;
}

function loop() {
  if (!running) return;
  const t0 = performance.now();
  while (performance.now() - t0 < SLICE_MS && steps < MAX_STEPS) metropolisStep();
  if (steps >= MAX_STEPS) stop("limit");
  post();
  if (!job && performance.now() - lastPredict > PREDICT_EVERY_MS) startJob();
  advanceJob(SLICE_MS / 2);
  if (running) timer = setTimeout(loop, 0);
}

function restart() {
  stop("idle");
  run += 1;
  rand = mulberry32(SEED);
  steps = 0;
  accepted = 0;
  sent = 0;
  job = null;
  if (cfg.start === "prior") {
    // A fresh draw from the prior on every reset; the proposal stream itself is reseeded.
    const draw = mulberry32(SEED + 1000 * run);
    theta = PRIOR.map((p, i) => lo[i] + (hi[i] - lo[i]) * draw());
  } else theta = coordinate(START);
  lp = logPosterior(theta);
  post();
  startJob();
  finishJobNow();
}

self.onmessage = (event) => {
  const msg = event.data;
  switch (msg.type) {
    case "init":
      prepare(msg);
      cfg = { ...cfg, ...(msg.cfg || {}) };
      if (msg.grid) grid = msg.grid;
      self.postMessage({ type: "ready", n: data.n, prior: PRIOR, start: START, step: STEP, maxSteps: MAX_STEPS });
      restart();
      break;
    case "run":
      if (running || steps >= MAX_STEPS) break;
      running = true;
      status = "running";
      loop();
      break;
    case "pause":
      if (!running) break;
      stop("paused");
      post();
      if (!job) startJob();
      finishJobNow();
      break;
    case "step": {
      if (steps >= MAX_STEPS) break;
      stop("paused");
      const target = Math.min(MAX_STEPS, steps + (msg.count || 100));
      while (steps < target) metropolisStep();
      post();
      startJob();
      finishJobNow();
      break;
    }
    case "reset":
      if (msg.start) cfg.start = msg.start;
      restart();
      break;
    case "config":
      for (const key of ["stepScale", "burn", "draws", "start"]) if (key in msg) cfg[key] = msg[key];
      if (!running) {
        startJob();
        finishJobNow();
      }
      break;
    case "grid":
      grid = msg.x;
      startJob();
      if (!running) finishJobNow();
      break;
    default:
      break;
  }
};
