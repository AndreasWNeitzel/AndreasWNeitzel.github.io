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
// Out: ready {...}, state {...} after every change and about every 60 ms while running
//      (with the conditional mean of the current state on the grid whenever the state has
//      moved), predictive {...} with the marginalised prediction: after every loop while
//      running, one of its posterior states refreshed each time, and in full otherwise.
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
let slots = null; // the marginalised prediction, one slot per posterior state
let lastAlpha = null; // K^-1 y of the last factorised state
let alphaNow = null; // K^-1 y of the current state
let nowDirty = true; // the current state moved since its curve was last sent

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
  const ll = logLikelihood(K, data.n, data.y);
  lastAlpha = ll.alpha;
  return ll.value;
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
    alphaNow = lastAlpha;
    nowDirty = true;
    accepted += 1;
  }
  record(theta, lp);
}

// ---------------------------------------------------------------- marginalised prediction
// The prediction on the grid averages the conditional distribution of the latent function
// over posterior samples: the mean of the mixture is the mean of the conditional means and
// its variance is E[var_i + mean_i^2] - mean^2. Slot k holds state burn + (k + 1/2) avail / count
// of the part of the chain after burn-in, so the slots sit at even spacing; before the first
// step the starting point alone is used. While the chain runs, one slot is recomputed per loop
// (in turn), so the band follows the chain without a pause; when it stops, every slot is
// recomputed at once for the chain as it stands.
function makeSlots() {
  if (!grid || !data) return null;
  const m = grid.length;
  const count = cfg.draws;
  return {
    m, count, next: 0,
    filled: new Uint8Array(count),
    mean: new Float64Array(count * m), sq: new Float64Array(count * m),
    curves: Array.from({ length: Math.min(CURVES_KEPT, count) }, () => new Float32Array(m)),
    L: new Float64Array(data.n * data.n), row: new Float64Array(data.n), v: new Float64Array(data.n),
  };
}

function slotParams(k) {
  if (steps === 0) return natural(theta);
  const burn = Math.floor(cfg.burn * steps);
  const avail = steps - burn;
  const row = burn + Math.min(avail - 1, Math.floor(((k + 0.5) * avail) / slots.count));
  const p = new Array(D);
  for (let i = 0; i < D; i++) p[i] = chain[row * COLS + i];
  return p;
}

function fillSlot(k) {
  const { n, t, y } = data;
  const p = slotParams(k);
  const { L, row, v, m } = slots;
  slots.filled[k] = 0;
  if (!factor(p, L)) return;
  const alpha = logLikelihood(L, n, y).alpha;
  const e1 = p[0] * p[0];
  const e2 = 2 * p[1] * p[1];
  const e3 = Math.PI / p[2];
  const e4 = 2 / (p[3] * p[3]);
  const curve = k < slots.curves.length ? slots.curves[k] : null;
  const base = k * m;
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
    slots.mean[base + i] = mean;
    slots.sq[base + i] = Math.max(0, vv) + mean * mean;
    if (curve) curve[i] = mean;
  }
  slots.filled[k] = 1;
}

// Sends the mixture over the filled slots.
function publish() {
  const { m, count, filled } = slots;
  const mean = new Float32Array(m);
  const sd = new Float32Array(m);
  let used = 0;
  for (let k = 0; k < count; k++) used += filled[k];
  if (!used) return;
  for (let i = 0; i < m; i++) {
    let s1 = 0;
    let s2 = 0;
    for (let k = 0; k < count; k++) {
      if (!filled[k]) continue;
      s1 += slots.mean[k * m + i];
      s2 += slots.sq[k * m + i];
    }
    const mu = s1 / used;
    mean[i] = mu;
    sd[i] = Math.sqrt(Math.max(0, s2 / used - mu * mu));
  }
  const curves = slots.curves.filter((_, k) => filled[k]).map((c) => c.slice());
  self.postMessage({
    type: "predictive", run, x: grid, mean, sd, curves, samples: used, burn: Math.floor(cfg.burn * steps), steps,
  }, [mean.buffer, sd.buffer, ...curves.map((c) => c.buffer)]);
}

// Every slot at once, for a chain that is not running.
function refreshAll() {
  slots = makeSlots();
  if (!slots) return;
  const count = steps === 0 ? 1 : slots.count;
  for (let k = 0; k < count; k++) fillSlot(k);
  publish();
}

// One slot, in turn, while the chain runs.
function refreshOne() {
  if (!slots) slots = makeSlots();
  if (!slots) return;
  fillSlot(slots.next);
  slots.next = (slots.next + 1) % slots.count;
  publish();
}

// The conditional mean of the latent function on the grid at the current state, which needs
// only K^-1 y of that state and one row of the cross-covariance per grid point.
function currentCurve() {
  if (!grid || !alphaNow) return null;
  const { n, t } = data;
  const p = natural(theta);
  const e1 = p[0] * p[0];
  const e2 = 2 * p[1] * p[1];
  const e3 = Math.PI / p[2];
  const e4 = 2 / (p[3] * p[3]);
  const out = new Float32Array(grid.length);
  for (let i = 0; i < grid.length; i++) {
    const x = grid[i];
    let mean = 0;
    for (let j = 0; j < n; j++) {
      const d = x - t[j];
      const sn = Math.sin(e3 * d);
      mean += e1 * Math.exp(-(d * d) / e2 - e4 * sn * sn) * alphaNow[j];
    }
    out[i] = mean;
  }
  return out;
}

// ---------------------------------------------------------------- messages out
function post() {
  const fresh = chain.slice(sent * COLS, steps * COLS);
  sent = steps;
  const now = nowDirty ? currentCurve() : null;
  if (now) nowDirty = false;
  const transfer = [fresh.buffer];
  if (now) transfer.push(now.buffer);
  self.postMessage({
    type: "state", run, status, steps, accepted, rows: fresh, cols: COLS,
    current: natural(theta), lp, maxSteps: MAX_STEPS, now, nowX: now ? grid : null,
  }, transfer);
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
  if (running) refreshOne();
  else refreshAll();
  if (running) timer = setTimeout(loop, 0);
}

function restart() {
  stop("idle");
  run += 1;
  rand = mulberry32(SEED);
  steps = 0;
  accepted = 0;
  sent = 0;
  slots = null;
  if (cfg.start === "prior") {
    // A fresh draw from the prior on every reset; the proposal stream itself is reseeded.
    const draw = mulberry32(SEED + 1000 * run);
    theta = PRIOR.map((p, i) => lo[i] + (hi[i] - lo[i]) * draw());
  } else theta = coordinate(START);
  lp = logPosterior(theta);
  alphaNow = lastAlpha;
  nowDirty = true;
  post();
  refreshAll();
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
      refreshAll();
      break;
    case "step": {
      if (steps >= MAX_STEPS) break;
      stop("paused");
      const target = Math.min(MAX_STEPS, steps + (msg.count || 100));
      while (steps < target) metropolisStep();
      post();
      refreshAll();
      break;
    }
    case "reset":
      if (msg.start) cfg.start = msg.start;
      restart();
      break;
    case "config":
      for (const key of ["stepScale", "burn", "draws", "start"]) if (key in msg) cfg[key] = msg[key];
      if (!running || (slots && slots.count !== cfg.draws)) refreshAll();
      break;
    case "grid":
      grid = msg.x;
      nowDirty = true;
      refreshAll();
      if (!running) post();
      break;
    default:
      break;
  }
};
