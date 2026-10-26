// Numerics for the polytrope playground: the Lane-Emden equation solved by RK4, the scaling
// of a solution to a star's mass and radius, hydrogen-burning rates and the luminosity
// integral. Pure functions and cgs units throughout, so the file also runs under Node.

// Constants. The solar values are the IAU 2015 nominal conversion constants (Prsa et al.
// 2016, AJ 152, 41); G and the atomic mass constant are CODATA 2022; k is exact in the SI.
export const CGS = {
  G: 6.6743e-8, // cm^3 g^-1 s^-2
  k: 1.380649e-16, // erg K^-1
  m_u: 1.66053906892e-24, // g
  GM_sun: 1.3271244e26, // cm^3 s^-2
  R_sun: 6.957e10, // cm
  L_sun: 3.828e33, // erg s^-1
};
CGS.M_sun = CGS.GM_sun / CGS.G; // 1.98841e33 g

export const N_MAX = 4.9; // the slider's upper limit; n = 5 has no surface
export const NODES = 400; // samples of each solution, uniform in xi / xi_1

// C, N and O are 66 percent of the metals by mass in the solar mixture of Asplund et al.
// (2009): with log eps = 8.43, 7.83 and 8.69 and X = 0.7381, their mass fractions sum to
// 8.80e-3 against Z = 0.0134.
export const CNO_SHARE_OF_Z = 0.66;

// ---------------------------------------------------------------- Lane-Emden
// theta'' + (2/xi) theta' + theta^n = 0, theta(0) = 1, theta'(0) = 0. The series
// theta = 1 - xi^2/6 + n xi^4/120 starts the integration away from the singular origin.
// Steps are 0.01 up to xi = 5 and then grow with xi, which keeps the cost of the large,
// slowly decaying solutions near n = 5 small. The surface is the first zero of theta.
function derivs(n, xi, th, ph, out) {
  out[0] = ph;
  out[1] = -(th > 0 ? th ** n : th < 0 ? -((-th) ** n) : 0) - (2 * ph) / xi;
}

export function solveLaneEmden(n) {
  const k1 = [0, 0];
  const k2 = [0, 0];
  const k3 = [0, 0];
  const k4 = [0, 0];
  let xi = 1e-3;
  let th = 1 - xi ** 2 / 6 + (n * xi ** 4) / 120;
  let ph = -xi / 3 + (n * xi ** 3) / 30;
  const XI = [xi];
  const TH = [th];
  const PH = [ph];
  let xi1 = NaN;
  let dth1 = NaN;
  let h = 0.01;
  for (let guard = 0; guard < 400000; guard++) {
    h = xi < 5 ? 0.01 : 0.002 * xi;
    let accepted = false;
    for (let halving = 0; halving < 60; halving++) {
      derivs(n, xi, th, ph, k1);
      derivs(n, xi + h / 2, th + (h / 2) * k1[0], ph + (h / 2) * k1[1], k2);
      derivs(n, xi + h / 2, th + (h / 2) * k2[0], ph + (h / 2) * k2[1], k3);
      derivs(n, xi + h, th + h * k3[0], ph + h * k3[1], k4);
      const thNew = th + (h / 6) * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0]);
      const phNew = ph + (h / 6) * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1]);
      if (thNew > 0) {
        xi += h;
        th = thNew;
        ph = phNew;
        XI.push(xi);
        TH.push(th);
        PH.push(ph);
        accepted = true;
        break;
      }
      if (h < 1e-9) {
        // The remaining distance to the zero is below the step: interpolate linearly.
        const f = th / (th - thNew);
        xi1 = xi + h * f;
        dth1 = ph + (phNew - ph) * f;
        break;
      }
      h /= 2;
    }
    if (!accepted) break;
  }
  if (!Number.isFinite(xi1)) throw new Error(`no surface found for n = ${n}`);
  XI.push(xi1);
  TH.push(0);
  PH.push(dth1);
  // Resample onto NODES + 1 points, uniform in u = xi / xi1, by cubic Hermite interpolation.
  const theta = new Float64Array(NODES + 1);
  const dtheta = new Float64Array(NODES + 1);
  let j = 0;
  for (let i = 0; i <= NODES; i++) {
    const x = (i / NODES) * xi1;
    while (j < XI.length - 2 && XI[j + 1] < x) j++;
    const x0 = XI[j];
    const x1 = XI[j + 1];
    const d = x1 - x0;
    const t = d > 0 ? Math.min(1, Math.max(0, (x - x0) / d)) : 0;
    const t2 = t * t;
    const t3 = t2 * t;
    const h00 = 2 * t3 - 3 * t2 + 1;
    const h10 = t3 - 2 * t2 + t;
    const h01 = -2 * t3 + 3 * t2;
    const h11 = t3 - t2;
    theta[i] = h00 * TH[j] + h10 * d * PH[j] + h01 * TH[j + 1] + h11 * d * PH[j + 1];
    const g00 = 6 * t2 - 6 * t;
    const g10 = 3 * t2 - 4 * t + 1;
    const g01 = -6 * t2 + 6 * t;
    const g11 = 3 * t2 - 2 * t;
    dtheta[i] = d > 0 ? (g00 * TH[j] + g01 * TH[j + 1]) / d + g10 * PH[j] + g11 * PH[j + 1] : PH[j];
  }
  theta[0] = 1;
  dtheta[0] = 0;
  theta[NODES] = 0;
  dtheta[NODES] = dth1;
  if (i0Neg(theta)) throw new Error(`negative theta for n = ${n}`);
  // theta^n and the Simpson weights times u^2 theta^n, so that the luminosity integral
  // of any star costs one rate evaluation per node.
  const thn = new Float64Array(NODES + 1);
  const wu2thn = new Float64Array(NODES + 1);
  for (let i = 0; i <= NODES; i++) {
    thn[i] = n === 0 ? 1 : theta[i] ** n;
    const w = i === 0 || i === NODES ? 1 : i % 2 ? 4 : 2;
    wu2thn[i] = (w * (i / NODES) ** 2 * thn[i]) / (3 * NODES);
  }
  return { n, xi1, dtheta1: dth1, mr: -(xi1 ** 2) * dth1, theta, dtheta, thn, wu2thn, steps: XI.length };
}

function i0Neg(theta) {
  for (let i = 0; i < theta.length - 1; i++) if (!(theta[i] > 0)) return true;
  return false;
}

// Analytic solutions used as checks: n = 0, 1 and 5.
export const ANALYTIC = {
  0: { theta: (xi) => 1 - (xi * xi) / 6, xi1: Math.sqrt(6), mr: 2 * Math.sqrt(6) },
  1: { theta: (xi) => (xi === 0 ? 1 : Math.sin(xi) / xi), xi1: Math.PI, mr: Math.PI },
  5: { theta: (xi) => 1 / Math.sqrt(1 + (xi * xi) / 3), xi1: Infinity, mr: Math.sqrt(3) },
};

// ---------------------------------------------------------------- scaling
// Mean molecular weight of a fully ionised gas, 1/mu = 2X + 3Y/4 + Z/2 with Y = 1 - X - Z.
export const meanMolecularWeight = (X, Z) => 4 / (3 + 5 * X - Z);

// Central values from M, R and the Lane-Emden constants (Chandrasekhar 1939; Kippenhahn,
// Weigert and Weiss 2012, Chap. 19): rho_c = rho_mean xi1 / (3 |theta'_1|),
// P_c = G M^2 / (4 pi R^4 (n + 1) theta'_1^2), and the ideal gas gives T_c = mu m_u P_c / (k rho_c).
export function scaleStar(sol, star) {
  const { G, k, m_u } = CGS;
  const M = star.M * CGS.M_sun;
  const R = star.R * CGS.R_sun;
  const n = sol.n;
  const rhoMean = (3 * M) / (4 * Math.PI * R ** 3);
  const rhoC = (rhoMean * sol.xi1) / (3 * Math.abs(sol.dtheta1));
  const PC = (G * M * M) / (4 * Math.PI * R ** 4 * (n + 1) * sol.dtheta1 ** 2);
  const mu = meanMolecularWeight(star.X, star.Z);
  const TC = (mu * m_u * PC) / (k * rhoC);
  return { M, R, n, mu, rhoMean, rhoC, PC, TC, K: n > 0 ? PC / rhoC ** (1 + 1 / n) : NaN };
}

// ---------------------------------------------------------------- energy generation
// Kippenhahn, Weigert and Weiss (2012), Sect. 18.5.1 and 18.5.2, in erg g^-1 s^-1 with
// rho in g cm^-3 and T9 = T / 10^9 K. The pp chain is taken with psi = 1 (the pp I
// branch only) and the screening factor f_11 = 1; X_CNO is the C, N and O mass fraction.
export function ratePP(rho, T, X) {
  if (!(T > 1e5)) return 0;
  const T9 = T / 1e9;
  const c = Math.cbrt(1 / T9); // T9^(-1/3)
  const g11 = 1 + 3.82 * T9 + 1.51 * T9 ** 2 + 0.144 * T9 ** 3 - 0.0114 * T9 ** 4;
  return 2.57e4 * g11 * rho * X * X * c * c * Math.exp(-3.381 * c);
}

export function rateCNO(rho, T, X, Z) {
  if (!(T > 1e5)) return 0;
  const T9 = T / 1e9;
  const c = Math.cbrt(1 / T9);
  const g14 = 1 - 2.0 * T9 + 3.41 * T9 ** 2 - 2.43 * T9 ** 3;
  const XCNO = CNO_SHARE_OF_Z * Z;
  return 8.24e25 * g14 * XCNO * X * rho * c * c * Math.exp(-15.231 * c - (T9 / 0.8) ** 2);
}

// The total luminosity alone, in erg s^-1, with no allocation: the Monte Carlo's inner loop.
export function luminosityOnly(sol, scaled, X, Z) {
  const { thn, wu2thn, theta } = sol;
  const { rhoC, TC, R } = scaled;
  let sum = 0;
  for (let i = 0; i <= NODES; i++) {
    const rho = rhoC * thn[i];
    const T = TC * theta[i];
    if (!(T > 1e5)) break; // the rates vanish outward from here
    sum += wu2thn[i] * (ratePP(rho, T, X) + rateCNO(rho, T, X, Z));
  }
  return 4 * Math.PI * R ** 3 * rhoC * sum;
}

// ---------------------------------------------------------------- luminosity
// L = 4 pi R^3 rho_c int_0^1 u^2 theta^n eps(rho(u), T(u)) du by Simpson's rule on the
// NODES + 1 samples. Returns the pp and CNO parts and the cumulative L(<u) for drawing.
export function luminosity(sol, scaled, star) {
  const { theta } = sol;
  const { rhoC, TC, R } = scaled;
  const N = NODES;
  const pp = new Float64Array(N + 1);
  const cno = new Float64Array(N + 1);
  const cum = new Float64Array(N + 1);
  const factor = 4 * Math.PI * R ** 3 * rhoC;
  const h = 1 / N;
  let spp = 0;
  let scno = 0;
  for (let i = 0; i <= N; i++) {
    const th = theta[i];
    const rho = rhoC * sol.thn[i];
    const T = TC * th;
    pp[i] = ratePP(rho, T, star.X);
    cno[i] = rateCNO(rho, T, star.X, star.Z);
    const u2thn = (i * h) ** 2 * sol.thn[i];
    const w = i === 0 || i === N ? 1 : i % 2 ? 4 : 2;
    spp += w * u2thn * pp[i];
    scno += w * u2thn * cno[i];
    // cumulative by the trapezoid rule, for the picture only
    if (i > 0) {
      const prev = ((i - 1) * h) ** 2 * sol.thn[i - 1] * (pp[i - 1] + cno[i - 1]);
      cum[i] = cum[i - 1] + (h / 2) * (prev + u2thn * (pp[i] + cno[i]));
    }
  }
  const Lpp = (factor * h * spp) / 3;
  const Lcno = (factor * h * scno) / 3;
  return { L: Lpp + Lcno, Lpp, Lcno, pp, cno, cum };
}

// Everything the picture needs for one n and one star.
export function model(sol, star) {
  const scaled = scaleStar(sol, star);
  const lum = luminosity(sol, scaled, star);
  return { sol, scaled, lum, LsunModel: lum.L / CGS.L_sun };
}

// ---------------------------------------------------------------- the index at L_obs
// A cache of solutions on the grid n = 0, 0.01, ..., N_MAX (491 entries) serves the slider,
// the L(n) curve and the Monte Carlo. log L is interpolated linearly between grid nodes.
export class Grid {
  constructor(step = 0.01) {
    this.step = step;
    this.count = Math.round(N_MAX / step) + 1;
    this.sols = new Array(this.count).fill(null);
  }
  at(i) {
    if (!this.sols[i]) this.sols[i] = solveLaneEmden(i * this.step);
    return this.sols[i];
  }
  solution(n) {
    return this.at(Math.min(this.count - 1, Math.max(0, Math.round(n / this.step))));
  }
  get complete() {
    return this.sols.every(Boolean);
  }
  // Model luminosity in L_sun at grid node i for a star.
  lumAt(i, star) {
    const sol = this.at(i);
    return luminosityOnly(sol, scaleStar(sol, star), star.X, star.Z) / CGS.L_sun;
  }
  // The index at which L_model equals L (in L_sun): L(n) rises with n, so the crossing is
  // bracketed on a coarse grid (or around a guess, for the Monte Carlo) and then bisected on
  // the fine one. null if the curve never reaches L.
  indexAt(L, star, guess = NaN, coarse = 5) {
    const target = Math.log(L);
    const last = this.count - 1;
    let lo;
    let hi;
    let flo;
    let fhi;
    if (Number.isFinite(guess)) {
      lo = Math.min(last, Math.max(0, Math.round(guess / this.step) - coarse));
      hi = Math.min(last, lo + 2 * coarse);
      flo = Math.log(this.lumAt(lo, star));
      fhi = Math.log(this.lumAt(hi, star));
      while (flo >= target && lo > 0) {
        hi = lo;
        fhi = flo;
        lo = Math.max(0, lo - 2 * coarse);
        flo = Math.log(this.lumAt(lo, star));
      }
      while (fhi < target && hi < last) {
        lo = hi;
        flo = fhi;
        hi = Math.min(last, hi + 2 * coarse);
        fhi = Math.log(this.lumAt(hi, star));
      }
      if (flo >= target) return 0;
      if (fhi < target) return null;
    } else {
      lo = 0;
      flo = Math.log(this.lumAt(0, star));
      if (flo >= target) return 0;
      hi = -1;
      fhi = 0;
      for (let i = coarse; i <= last; i += coarse) {
        const i2 = Math.min(i, last);
        const f = Math.log(this.lumAt(i2, star));
        if (f >= target) {
          hi = i2;
          fhi = f;
          break;
        }
        lo = i2;
        flo = f;
        if (i2 === last) break;
      }
      if (hi < 0) return null;
    }
    while (hi - lo > 1) {
      const mid = (lo + hi) >> 1;
      const f = Math.log(this.lumAt(mid, star));
      if (f >= target) {
        hi = mid;
        fhi = f;
      } else {
        lo = mid;
        flo = f;
      }
    }
    const t = fhi === flo ? 0.5 : (target - flo) / (fhi - flo);
    return (lo + t) * this.step;
  }
}

// ---------------------------------------------------------------- random draws
// Normal deviates by Box-Muller; a split normal takes different widths on either side.
export function normal(rng = Math.random) {
  let u = 0;
  while (u === 0) u = rng();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * rng());
}

export function drawValue(q, rng = Math.random) {
  // q: { value, sigma } or { value, plus, minus } (split normal) or { log10, sigma_dex }.
  if (q.log10 !== undefined) return 10 ** (q.log10 + q.sigma_dex * normal(rng));
  const z = normal(rng);
  if (q.plus !== undefined) return q.value + z * (z >= 0 ? q.plus : q.minus);
  return q.value + z * (q.sigma ?? 0);
}

export function quantile(sorted, p) {
  if (!sorted.length) return NaN;
  const pos = (sorted.length - 1) * p;
  const lo = Math.floor(pos);
  const hi = Math.min(sorted.length - 1, lo + 1);
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo);
}
