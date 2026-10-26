// Numerics shared by the Gaussian-process playground: kernels, Cholesky factorisation,
// the log marginal likelihood and the conditional distribution on a grid. Plain Float64Array
// maths, row-major matrices; used by gp-playground.js (kernel mode, main thread) and by
// gp-worker.js (the sampler). Nothing here touches the DOM.

// Kernels as functions of the separation tau and a parameter object
// {sf: amplitude, l: length scale, P: period, lam: smoothing within a period}.
const SQRT3 = Math.sqrt(3);
export const KERNELS = {
  se: {
    label: "Squared exponential",
    uses: ["l"],
    k: (tau, p) => p.sf * p.sf * Math.exp(-(tau * tau) / (2 * p.l * p.l)),
  },
  m32: {
    label: "Matérn 3/2",
    uses: ["l"],
    k: (tau, p) => {
      const r = (SQRT3 * Math.abs(tau)) / p.l;
      return p.sf * p.sf * (1 + r) * Math.exp(-r);
    },
  },
  per: {
    label: "Periodic",
    uses: ["l", "P"],
    k: (tau, p) => {
      const s = Math.sin((Math.PI * tau) / p.P);
      return p.sf * p.sf * Math.exp((-2 * s * s) / (p.l * p.l));
    },
  },
  qp: {
    label: "Quasi-periodic",
    uses: ["l", "P", "lam"],
    k: (tau, p) => {
      const s = Math.sin((Math.PI * tau) / p.P);
      return p.sf * p.sf * Math.exp(-(tau * tau) / (2 * p.l * p.l) - (2 * s * s) / (p.lam * p.lam));
    },
  },
};

// Covariance matrix between two sets of inputs, as a row-major Float64Array (n1 rows, n2 columns).
export function covariance(x1, x2, k, p) {
  const n1 = x1.length;
  const n2 = x2.length;
  const out = new Float64Array(n1 * n2);
  for (let i = 0; i < n1; i++) for (let j = 0; j < n2; j++) out[i * n2 + j] = k(x1[i] - x2[j], p);
  return out;
}

// Cholesky factorisation in place: the lower triangle of A (n by n, symmetric positive definite)
// is overwritten with L such that L L^T = A. Returns false if A is not positive definite.
export function cholesky(A, n) {
  for (let j = 0; j < n; j++) {
    const jn = j * n;
    let d = A[jn + j];
    for (let k = 0; k < j; k++) d -= A[jn + k] * A[jn + k];
    if (!(d > 0)) return false;
    d = Math.sqrt(d);
    A[jn + j] = d;
    const inv = 1 / d;
    for (let i = j + 1; i < n; i++) {
      const im = i * n;
      let s = A[im + j];
      for (let k = 0; k < j; k++) s -= A[im + k] * A[jn + k];
      A[im + j] = s * inv;
    }
  }
  return true;
}

// Solves L z = b (forward substitution) into out.
export function forwardSolve(L, n, b, out) {
  const z = out || new Float64Array(n);
  for (let i = 0; i < n; i++) {
    const im = i * n;
    let s = b[i];
    for (let k = 0; k < i; k++) s -= L[im + k] * z[k];
    z[i] = s / L[im + i];
  }
  return z;
}

// Solves L L^T x = b.
export function choleskySolve(L, n, b) {
  const x = forwardSolve(L, n, b);
  for (let i = n - 1; i >= 0; i--) {
    let s = x[i];
    for (let k = i + 1; k < n; k++) s -= L[k * n + i] * x[k];
    x[i] = s / L[i * n + i];
  }
  return x;
}

// log p(y | x, theta) = -1/2 y^T K^-1 y - 1/2 log|K| - n/2 log(2 pi), from the factor L of K.
export function logLikelihood(L, n, y) {
  const alpha = choleskySolve(L, n, y);
  let quad = 0;
  let logdet = 0;
  for (let i = 0; i < n; i++) {
    quad += y[i] * alpha[i];
    logdet += Math.log(L[i * n + i]);
  }
  return { value: -0.5 * quad - logdet - 0.5 * n * Math.log(2 * Math.PI), alpha };
}

// Distribution of the function on the grid xs: the prior when there are no observations,
// otherwise the conditional on observations (x, y) with noise variance `noise` (one value for
// all points). Returns the mean, the standard deviation, the full covariance (for draws) and
// the log marginal likelihood of the observations, or null if the factorisation fails.
export function conditional(xs, x, y, k, p, noise) {
  const m = xs.length;
  const n = x.length;
  const cov = covariance(xs, xs, k, p);
  const mean = new Float64Array(m);
  let lml = NaN;
  if (n > 0) {
    const K = covariance(x, x, k, p);
    for (let i = 0; i < n; i++) K[i * n + i] += noise;
    if (!cholesky(K, n)) return null;
    const ll = logLikelihood(K, n, y);
    lml = ll.value;
    const Ks = covariance(xs, x, k, p);
    const V = new Float64Array(n * m);
    const row = new Float64Array(n);
    const v = new Float64Array(n);
    for (let i = 0; i < m; i++) {
      let s = 0;
      for (let j = 0; j < n; j++) {
        row[j] = Ks[i * n + j];
        s += row[j] * ll.alpha[j];
      }
      mean[i] = s;
      forwardSolve(K, n, row, v);
      for (let j = 0; j < n; j++) V[j * m + i] = v[j];
    }
    for (let i = 0; i < m; i++) {
      for (let j = 0; j <= i; j++) {
        let s = 0;
        for (let q = 0; q < n; q++) s += V[q * m + i] * V[q * m + j];
        cov[i * m + j] -= s;
        cov[j * m + i] = cov[i * m + j];
      }
    }
  }
  const sd = new Float64Array(m);
  for (let i = 0; i < m; i++) sd[i] = Math.sqrt(Math.max(0, cov[i * m + i]));
  return { mean, sd, cov, lml };
}

// Draws from N(mean, cov) with a seeded generator; a small ridge keeps the factorisation stable.
export function sampleFunctions(mean, cov, count, rand) {
  const m = mean.length;
  const L = Float64Array.from(cov);
  for (let i = 0; i < m; i++) L[i * m + i] += 1e-8;
  if (!cholesky(L, m)) return [];
  const out = [];
  const z = new Float64Array(m);
  for (let c = 0; c < count; c++) {
    for (let i = 0; i < m; i++) z[i] = gaussian(rand);
    const f = new Float64Array(m);
    for (let i = 0; i < m; i++) {
      let s = mean[i];
      for (let k = 0; k <= i; k++) s += L[i * m + k] * z[k];
      f[i] = s;
    }
    out.push(f);
  }
  return out;
}

export function mulberry32(a) {
  return function () {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function gaussian(rand) {
  let u = 0;
  while (u === 0) u = rand();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * rand());
}
