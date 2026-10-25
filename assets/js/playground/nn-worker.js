// Multilayer perceptron for the playground, trained in a Web Worker.
// Plain Float32Array maths: mini-batch Adam on a mean-squared-error loss with an
// optional L2 penalty on the weights (not the biases). Inputs and the label are
// standardised with the mean and spread of the training rows.
//
// In:  init {features, y, split, d, hp, sample}, train, pause, step, reset,
//      config {lr, batch, l2}, arch {layers, units, activation}, sample {row}
// Out: ready {mean, std, yMean, yStd, valRows}, state {...} after every change and
//      about every 50 ms while training.
"use strict";

const BETA1 = 0.9;
const BETA2 = 0.999;
const EPS = 1e-8;
const SLICE_MS = 45;
const MAX_EPOCHS = 2000;
const SEED = 7;
const MAX_BATCH = 256;
const GELU_C = Math.sqrt(2 / Math.PI);

let data = null;
let net = null;
let hp = { layers: 2, units: 16, activation: "tanh", lr: 0.003, batch: 64, l2: 0 };
let buf = null;
let order = null;
let shuffleRand = null;
let epoch = 0;
let cursor = 0;
let history = [];
let last = { train: NaN, val: NaN };
let running = false;
let timer = 0;
let status = "idle";
let sampleRow = 0;
let run = 0;

function mulberry32(a) {
  return function () {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function gaussian(rand) {
  let u = 0;
  while (u === 0) u = rand();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * rand());
}

function shuffle(arr, rand) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    const t = arr[i];
    arr[i] = arr[j];
    arr[j] = t;
  }
}

// Standardise every column with the training rows only; validation rows never inform the scaling.
function prepare(msg) {
  const { features, y, split, d } = msg;
  const n = y.length;
  const trainRows = [];
  const valRows = [];
  for (let i = 0; i < n; i++) (split[i] === 0 ? trainRows : valRows).push(i);
  const mean = new Float64Array(d);
  const sq = new Float64Array(d);
  let yMean = 0;
  for (const r of trainRows) {
    for (let k = 0; k < d; k++) mean[k] += features[r * d + k];
    yMean += y[r];
  }
  for (let k = 0; k < d; k++) mean[k] /= trainRows.length;
  yMean /= trainRows.length;
  let ySq = 0;
  for (const r of trainRows) {
    for (let k = 0; k < d; k++) {
      const e = features[r * d + k] - mean[k];
      sq[k] += e * e;
    }
    ySq += (y[r] - yMean) ** 2;
  }
  const std = new Float64Array(d);
  for (let k = 0; k < d; k++) std[k] = Math.sqrt(sq[k] / trainRows.length) || 1;
  const yStd = Math.sqrt(ySq / trainRows.length) || 1;
  const pack = (rows) => {
    const x = new Float32Array(rows.length * d);
    const t = new Float32Array(rows.length);
    rows.forEach((r, i) => {
      for (let k = 0; k < d; k++) x[i * d + k] = (features[r * d + k] - mean[k]) / std[k];
      t[i] = (y[r] - yMean) / yStd;
    });
    return [x, t];
  };
  const [xTr, yTr] = pack(trainRows);
  const [xVa, yVa] = pack(valRows);
  data = {
    d, xTr, yTr, xVa, yVa, nTr: trainRows.length, nVa: valRows.length,
    features, mean, std, yMean, yStd, valRows: Int32Array.from(valRows),
  };
}

function initNetwork() {
  const sizes = [data.d];
  for (let l = 0; l < hp.layers; l++) sizes.push(hp.units);
  sizes.push(1);
  const rand = mulberry32(SEED);
  const W = [];
  const b = [];
  for (let l = 1; l < sizes.length; l++) {
    const nIn = sizes[l - 1];
    const nOut = sizes[l];
    const output = l === sizes.length - 1;
    // Glorot for tanh, He for ReLU and GELU, LeCun for the linear output.
    const scale = output ? Math.sqrt(1 / nIn)
      : hp.activation === "tanh" ? Math.sqrt(2 / (nIn + nOut)) : Math.sqrt(2 / nIn);
    const w = new Float32Array(nIn * nOut);
    for (let i = 0; i < w.length; i++) w[i] = gaussian(rand) * scale;
    W.push(w);
    b.push(new Float32Array(nOut));
  }
  const zeros = (list) => list.map((a) => new Float32Array(a.length));
  net = { sizes, W, b, mW: zeros(W), vW: zeros(W), mb: zeros(b), vb: zeros(b), t: 0 };
  buf = {
    Z: sizes.map((s) => new Float32Array(MAX_BATCH * s)),
    A: sizes.map((s) => new Float32Array(MAX_BATCH * s)),
    dZ: sizes.map((s) => new Float32Array(MAX_BATCH * s)),
    dA: sizes.map((s) => new Float32Array(MAX_BATCH * s)),
    gW: zeros(W),
    gb: zeros(b),
  };
  order = new Uint32Array(data.nTr);
  for (let i = 0; i < order.length; i++) order[i] = i;
  shuffleRand = mulberry32(SEED + 1);
  shuffle(order, shuffleRand);
  epoch = 0;
  cursor = 0;
  history = [];
  status = "idle";
}

function activate(Z, A, len) {
  switch (hp.activation) {
    case "relu":
      for (let i = 0; i < len; i++) A[i] = Z[i] > 0 ? Z[i] : 0;
      break;
    case "gelu":
      for (let i = 0; i < len; i++) {
        const z = Z[i];
        A[i] = 0.5 * z * (1 + Math.tanh(GELU_C * (z + 0.044715 * z * z * z)));
      }
      break;
    default:
      for (let i = 0; i < len; i++) A[i] = Math.tanh(Z[i]);
  }
}

// dZ = dA * f'(Z), with f' written out for each activation.
function activationGrad(Z, A, dA, dZ, len) {
  switch (hp.activation) {
    case "relu":
      for (let i = 0; i < len; i++) dZ[i] = Z[i] > 0 ? dA[i] : 0;
      break;
    case "gelu":
      for (let i = 0; i < len; i++) {
        const z = Z[i];
        const th = Math.tanh(GELU_C * (z + 0.044715 * z * z * z));
        const grad = 0.5 * (1 + th) + 0.5 * z * (1 - th * th) * GELU_C * (1 + 3 * 0.044715 * z * z);
        dZ[i] = dA[i] * grad;
      }
      break;
    default:
      for (let i = 0; i < len; i++) dZ[i] = dA[i] * (1 - A[i] * A[i]);
  }
}

// Forward pass for `count` rows of x (row indices in `rows`, or consecutive from `start`).
function forward(x, rows, start, count) {
  const { sizes, W, b } = net;
  const d = sizes[0];
  // Gathered rows (a mini-batch) are copied into A[0], which backward() needs;
  // consecutive rows (an evaluation pass) are read from x in place.
  if (rows) {
    const A0 = buf.A[0];
    for (let i = 0; i < count; i++) {
      const src = rows[i] * d;
      const dst = i * d;
      for (let k = 0; k < d; k++) A0[dst + k] = x[src + k];
    }
  }
  const last = sizes.length - 1;
  for (let l = 1; l <= last; l++) {
    const nIn = sizes[l - 1];
    const nOut = sizes[l];
    const Ain = l === 1 && !rows ? x : buf.A[l - 1];
    const base = l === 1 && !rows ? start * d : 0;
    const Z = buf.Z[l];
    const w = W[l - 1];
    const bias = b[l - 1];
    for (let i = 0; i < count; i++) {
      const ai = base + i * nIn;
      const zi = i * nOut;
      for (let j = 0; j < nOut; j++) {
        const wj = j * nIn;
        let s = bias[j];
        for (let k = 0; k < nIn; k++) s += Ain[ai + k] * w[wj + k];
        Z[zi + j] = s;
      }
    }
    if (l < last) activate(Z, buf.A[l], count * nOut);
    else buf.A[l].set(Z.subarray(0, count * nOut));
  }
  return buf.A[last];
}

// Backward pass after forward(); fills buf.gW and buf.gb and returns the batch MSE.
function backward(y, rows, count) {
  const { sizes, W } = net;
  const last = sizes.length - 1;
  const out = buf.A[last];
  let dZ = buf.dZ[last];
  let loss = 0;
  for (let i = 0; i < count; i++) {
    const e = out[i] - y[rows[i]];
    loss += e * e;
    dZ[i] = (2 * e) / count;
  }
  for (let l = last; l >= 1; l--) {
    const nIn = sizes[l - 1];
    const nOut = sizes[l];
    const Ain = buf.A[l - 1];
    const w = W[l - 1];
    const gW = buf.gW[l - 1];
    const gb = buf.gb[l - 1];
    gW.fill(0);
    gb.fill(0);
    const dA = l > 1 ? buf.dA[l - 1] : null;
    if (dA) dA.fill(0, 0, count * nIn);
    for (let i = 0; i < count; i++) {
      const ai = i * nIn;
      const zi = i * nOut;
      for (let j = 0; j < nOut; j++) {
        const g = dZ[zi + j];
        if (g === 0) continue;
        gb[j] += g;
        const wj = j * nIn;
        for (let k = 0; k < nIn; k++) gW[wj + k] += g * Ain[ai + k];
        if (dA) for (let k = 0; k < nIn; k++) dA[ai + k] += g * w[wj + k];
      }
    }
    if (dA) {
      activationGrad(buf.Z[l - 1], buf.A[l - 1], dA, buf.dZ[l - 1], count * nIn);
      dZ = buf.dZ[l - 1];
    }
  }
  return loss / count;
}

function adamStep() {
  net.t += 1;
  const c1 = 1 - Math.pow(BETA1, net.t);
  const c2 = 1 - Math.pow(BETA2, net.t);
  const lr = hp.lr;
  const l2 = hp.l2;
  const update = (p, g, m, v, decay) => {
    for (let i = 0; i < p.length; i++) {
      const gi = g[i] + decay * p[i];
      m[i] = BETA1 * m[i] + (1 - BETA1) * gi;
      v[i] = BETA2 * v[i] + (1 - BETA2) * gi * gi;
      p[i] -= (lr * (m[i] / c1)) / (Math.sqrt(v[i] / c2) + EPS);
    }
  };
  for (let l = 0; l < net.W.length; l++) {
    update(net.W[l], buf.gW[l], net.mW[l], net.vW[l], l2);
    update(net.b[l], buf.gb[l], net.mb[l], net.vb[l], 0);
  }
}

// Mean squared error over a whole set, in standardised units; optionally keeps predictions.
function evaluate(x, y, n, keep) {
  let sum = 0;
  for (let start = 0; start < n; start += MAX_BATCH) {
    const count = Math.min(MAX_BATCH, n - start);
    const out = forward(x, null, start, count);
    for (let i = 0; i < count; i++) {
      const e = out[i] - y[start + i];
      sum += e * e;
      if (keep) keep[start + i] = out[i] * data.yStd + data.yMean;
    }
  }
  return sum / n;
}

function measure() {
  const s2 = data.yStd * data.yStd;
  last = {
    train: evaluate(data.xTr, data.yTr, data.nTr, null) * s2,
    val: evaluate(data.xVa, data.yVa, data.nVa, null) * s2,
  };
}

// One mini-batch; returns false if the loss has diverged.
function trainBatch() {
  const count = Math.min(hp.batch, MAX_BATCH, data.nTr - cursor);
  const rows = order.subarray(cursor, cursor + count);
  forward(data.xTr, rows, 0, count);
  const loss = backward(data.yTr, rows, count);
  if (!Number.isFinite(loss) || loss > 1e6) return false;
  adamStep();
  cursor += count;
  if (cursor >= data.nTr) {
    cursor = 0;
    epoch += 1;
    shuffle(order, shuffleRand);
    measure();
    history.push([epoch, last.train, last.val]);
    if (!Number.isFinite(last.train) || !Number.isFinite(last.val)) return false;
  }
  return true;
}

function sampleActivations() {
  const { sizes, W, b } = net;
  const d = sizes[0];
  const r = sampleRow;
  const input = new Float32Array(d);
  for (let k = 0; k < d; k++) input[k] = (data.features[r * d + k] - data.mean[k]) / data.std[k];
  const layers = [input];
  let a = input;
  for (let l = 1; l < sizes.length; l++) {
    const nIn = sizes[l - 1];
    const nOut = sizes[l];
    const z = new Float32Array(nOut);
    for (let j = 0; j < nOut; j++) {
      let s = b[l - 1][j];
      for (let k = 0; k < nIn; k++) s += a[k] * W[l - 1][j * nIn + k];
      z[j] = s;
    }
    if (l < sizes.length - 1) activate(z, z, nOut);
    layers.push(z);
    a = z;
  }
  return { row: r, layers, prediction: a[0] * data.yStd + data.yMean };
}

let sent = 0;
function post() {
  const preds = new Float32Array(data.nVa);
  evaluate(data.xVa, data.yVa, data.nVa, preds);
  const weights = net.W.map((w) => w.slice());
  const biases = net.b.map((v) => v.slice());
  const sample = sampleActivations();
  const fresh = history.slice(sent);
  sent = history.length;
  const transfer = [preds.buffer, ...weights.map((w) => w.buffer), ...biases.map((v) => v.buffer),
    ...sample.layers.map((v) => v.buffer)];
  self.postMessage({
    type: "state", run, status, epoch, cursor, nTr: data.nTr, sizes: net.sizes, hp: { ...hp },
    history: fresh, train: last.train, val: last.val, preds, weights, biases, sample,
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
  let ok = true;
  do {
    ok = trainBatch();
  } while (ok && performance.now() - t0 < SLICE_MS);
  if (!ok) stop("diverged");
  else if (epoch >= MAX_EPOCHS) stop("limit");
  post();
  if (running) timer = setTimeout(loop, 0);
}

function restart() {
  stop("idle");
  run += 1;
  initNetwork();
  measure();
  sent = 0;
  post();
}

self.onmessage = (event) => {
  const msg = event.data;
  switch (msg.type) {
    case "init":
      hp = { ...hp, ...msg.hp };
      prepare(msg);
      sampleRow = msg.sample ?? data.valRows[0];
      self.postMessage({
        type: "ready", mean: Float32Array.from(data.mean), std: Float32Array.from(data.std),
        yMean: data.yMean, yStd: data.yStd, valRows: data.valRows, nTr: data.nTr,
        maxEpochs: MAX_EPOCHS,
      });
      restart();
      break;
    case "train":
      if (running || status === "diverged" || epoch >= MAX_EPOCHS) break;
      running = true;
      status = "training";
      loop();
      break;
    case "pause":
      if (!running) break;
      stop("paused");
      post();
      break;
    case "step": {
      if (status === "diverged" || epoch >= MAX_EPOCHS) break;
      stop("paused");
      const target = epoch + 1;
      let ok = true;
      while (ok && epoch < target) ok = trainBatch();
      if (!ok) status = "diverged";
      post();
      break;
    }
    case "reset":
      restart();
      break;
    case "config":
      for (const key of ["lr", "batch", "l2"]) if (key in msg) hp[key] = msg[key];
      if (!running) post();
      break;
    case "arch": {
      const wasRunning = running;
      for (const key of ["layers", "units", "activation"]) if (key in msg) hp[key] = msg[key];
      restart();
      if (wasRunning) {
        running = true;
        status = "training";
        loop();
      }
      break;
    }
    case "sample":
      sampleRow = msg.row;
      if (!running) post();
      break;
    default:
      break;
  }
};
