// Physics for the Orbits playground: a point-mass Earth, the MWPotential2014 model of the
// Milky Way (Bovy 2015, ApJS 216, 29), three integrators and a few helpers. No DOM here,
// so the same code runs under node for the checks against galpy recorded in orbits.meta.json.
//
// Units. Earth: km, s, km/s. Galaxy: kpc, Myr, km/s. A "system" bundles the force law with
// the factor that turns velocities into position rates (dx/dt = vToX * v) and the energy.

export const KPC_PER_MYR_PER_KMS = 1.0227121650537077e-3; // 1 km/s in kpc/Myr

// ---------------------------------------------------------------- incomplete gamma
// Regularised incomplete gamma functions P(s, x) and Q(s, x) (series for x < s + 1, Lentz
// continued fraction otherwise), as in Numerical Recipes 6.2. The bulge needs s = 0.6 and 0.1.
const GAMMA_06 = 1.489192248812817;
const GAMMA_01 = 9.513507698668732;

function gammaSeries(s, x) {
  let term = 1 / s;
  let sum = term;
  let ap = s;
  for (let n = 0; n < 500; n++) {
    ap += 1;
    term *= x / ap;
    sum += term;
    if (Math.abs(term) < Math.abs(sum) * 1e-16) break;
  }
  return sum * Math.exp(-x + s * Math.log(x)) / gammaOf(s);
}

function gammaFraction(s, x) {
  const tiny = 1e-300;
  let b = x + 1 - s;
  let c = 1 / tiny;
  let d = 1 / b;
  let h = d;
  for (let i = 1; i < 500; i++) {
    const an = -i * (i - s);
    b += 2;
    d = an * d + b;
    if (Math.abs(d) < tiny) d = tiny;
    c = b + an / c;
    if (Math.abs(c) < tiny) c = tiny;
    d = 1 / d;
    const del = d * c;
    h *= del;
    if (Math.abs(del - 1) < 1e-16) break;
  }
  return Math.exp(-x + s * Math.log(x)) * h / gammaOf(s);
}

function gammaOf(s) {
  if (s === 0.6) return GAMMA_06;
  if (s === 0.1) return GAMMA_01;
  throw new Error("gamma(s) is tabulated for s = 0.6 and 0.1 only");
}

export function gammaP(s, x) {
  if (x <= 0) return 0;
  return x < s + 1 ? gammaSeries(s, x) : 1 - gammaFraction(s, x);
}

export function gammaQ(s, x) {
  if (x <= 0) return 1;
  return x < s + 1 ? 1 - gammaSeries(s, x) : gammaFraction(s, x);
}

// ---------------------------------------------------------------- Milky Way
// Each component is scaled so that its radial force at R0 in the plane is the stated
// fraction of v0^2 / R0 (galpy's normalize=). Potentials in km^2/s^2, forces in km^2/s^2/kpc.
export function milkyWay(p) {
  const R0 = p.R0_kpc;
  const v0 = p.v0_km_s;
  const unit = (v0 * v0) / R0; // v0^2 / R0, the radial force scale
  // Miyamoto and Nagai disc
  const a = p.disc.a_kpc;
  const b = p.disc.b_kpc;
  const ab = a + b;
  const GMd = p.disc.force_fraction_at_R0 * unit * Math.pow(R0 * R0 + ab * ab, 1.5) / R0;
  // NFW halo: M(<r) = M0 [ln(1 + r/a) - (r/a) / (1 + r/a)]
  const ah = p.halo.a_kpc;
  const nfwMass = (r) => Math.log(1 + r / ah) - (r / ah) / (1 + r / ah);
  const GM0 = p.halo.force_fraction_at_R0 * unit * R0 * R0 / nfwMass(R0);
  // Power-law bulge with exponential cut-off, rho ~ r^-alpha exp(-(r/rc)^2), alpha = 1.8:
  // G M(<r) = Kb rc^1.2 gamma(0.6, x) and the outer part of the potential is Kb rc^0.2 Gamma(0.1, x),
  // with x = (r/rc)^2 and gamma, Gamma the lower and upper incomplete gamma functions.
  if (p.bulge.alpha !== 1.8) throw new Error("the bulge code assumes alpha = 1.8");
  const rc = p.bulge.rc_kpc;
  const sIn = 0.6; // (3 - alpha) / 2
  const sOut = 0.1; // (2 - alpha) / 2
  const lower = (x) => GAMMA_06 * gammaP(sIn, x);
  const upper = (x) => GAMMA_01 * gammaQ(sOut, x);
  const Kb = p.bulge.force_fraction_at_R0 * unit * R0 * R0 / (Math.pow(rc, 1.2) * lower((R0 / rc) ** 2));
  const bulgeGM = (r) => Kb * Math.pow(rc, 1.2) * lower((r / rc) ** 2);

  function potential(R, z) {
    const r = Math.hypot(R, z);
    const zeta = Math.sqrt(z * z + b * b);
    const disc = -GMd / Math.sqrt(R * R + (a + zeta) ** 2);
    const halo = r > 0 ? -GM0 * Math.log(1 + r / ah) / r : -GM0 / ah;
    const x = (r / rc) ** 2;
    const bulge = (r > 0 ? -bulgeGM(r) / r : 0) - Kb * Math.pow(rc, 0.2) * upper(x);
    return disc + halo + bulge;
  }

  // Radial and vertical force components (cylindrical), filled into out = [FR, Fz].
  function force(R, z, out) {
    const r = Math.hypot(R, z);
    const zeta = Math.sqrt(z * z + b * b);
    const D = Math.sqrt(R * R + (a + zeta) ** 2);
    const D3 = D * D * D;
    let FR = -GMd * R / D3;
    let Fz = -GMd * z * (a + zeta) / (zeta * D3);
    if (r > 0) {
      const spherical = -(GM0 * nfwMass(r) + bulgeGM(r)) / (r * r * r); // F_r / r
      FR += spherical * R;
      Fz += spherical * z;
    }
    out[0] = FR;
    out[1] = Fz;
    return out;
  }

  const massUnit = 1 / 4.30091727e-6; // solar masses per (kpc km^2/s^2) / G
  return {
    potential, force,
    circularSpeed(R) { const f = force(R, 0, [0, 0]); return Math.sqrt(-f[0] * R); },
    masses: {
      disc_total_msun: GMd * massUnit,
      halo_scale_msun: GM0 * massUnit,
      halo_within(r) { return GM0 * nfwMass(r) * massUnit; },
      bulge_within(r) { return bulgeGM(r) * massUnit; },
    },
  };
}

// The Galaxy as a system for the integrators: state vectors in kpc and km/s, time in Myr.
export function galaxySystem(p) {
  const mw = milkyWay(p);
  const k = KPC_PER_MYR_PER_KMS;
  const f = [0, 0];
  return {
    vToX: k,
    accel(x, y, z, out) {
      const R = Math.hypot(x, y);
      mw.force(R, z, f);
      const over = R > 0 ? f[0] / R : 0;
      out[0] = over * x * k;
      out[1] = over * y * k;
      out[2] = f[1] * k;
      return out;
    },
    energy(x, y, z, vx, vy, vz) {
      return 0.5 * (vx * vx + vy * vy + vz * vz) + mw.potential(Math.hypot(x, y), z);
    },
    mw,
  };
}

// A point mass: state in km and km/s, time in s.
export function pointMassSystem(gm) {
  return {
    vToX: 1,
    accel(x, y, z, out) {
      const r2 = x * x + y * y + z * z;
      const s = -gm / (r2 * Math.sqrt(r2));
      out[0] = s * x;
      out[1] = s * y;
      out[2] = s * z;
      return out;
    },
    energy(x, y, z, vx, vy, vz) {
      return 0.5 * (vx * vx + vy * vy + vz * vz) - gm / Math.sqrt(x * x + y * y + z * z);
    },
  };
}

// ---------------------------------------------------------------- integrators
// A body is {s: Float64Array(6) = x, y, z, vx, vy, vz, a: Float64Array(3) cached acceleration}.
// Each stepper advances one body by h and returns the number of force evaluations.

export function leapfrogStep(sys, body, h) {
  const s = body.s;
  const a = body.a;
  const hv = 0.5 * h;
  s[3] += hv * a[0];
  s[4] += hv * a[1];
  s[5] += hv * a[2];
  const d = h * sys.vToX;
  s[0] += d * s[3];
  s[1] += d * s[4];
  s[2] += d * s[5];
  sys.accel(s[0], s[1], s[2], a);
  s[3] += hv * a[0];
  s[4] += hv * a[1];
  s[5] += hv * a[2];
  return 1;
}

// The coursework scheme: position to second order in h, velocity by the explicit Euler step.
export function eulerStep(sys, body, h) {
  const s = body.s;
  const a = body.a;
  const d = h * sys.vToX;
  const dd = 0.5 * h * d;
  s[0] += d * s[3] + dd * a[0];
  s[1] += d * s[4] + dd * a[1];
  s[2] += d * s[5] + dd * a[2];
  s[3] += h * a[0];
  s[4] += h * a[1];
  s[5] += h * a[2];
  sys.accel(s[0], s[1], s[2], a);
  return 1;
}

const K1 = new Float64Array(6);
const K2 = new Float64Array(6);
const K3 = new Float64Array(6);
const K4 = new Float64Array(6);
const TMP = new Float64Array(6);
const ACC = new Float64Array(3);

function derivative(sys, s, out) {
  const k = sys.vToX;
  out[0] = k * s[3];
  out[1] = k * s[4];
  out[2] = k * s[5];
  sys.accel(s[0], s[1], s[2], ACC);
  out[3] = ACC[0];
  out[4] = ACC[1];
  out[5] = ACC[2];
}

// One classical RK4 step from state s into out (may alias s).
export function rk4Step(sys, s, h, out) {
  derivative(sys, s, K1);
  for (let i = 0; i < 6; i++) TMP[i] = s[i] + 0.5 * h * K1[i];
  derivative(sys, TMP, K2);
  for (let i = 0; i < 6; i++) TMP[i] = s[i] + 0.5 * h * K2[i];
  derivative(sys, TMP, K3);
  for (let i = 0; i < 6; i++) TMP[i] = s[i] + h * K3[i];
  derivative(sys, TMP, K4);
  for (let i = 0; i < 6; i++) out[i] = s[i] + (h / 6) * (K1[i] + 2 * K2[i] + 2 * K3[i] + K4[i]);
  return 4;
}

const BIG = new Float64Array(6);
const HALF = new Float64Array(6);

// Adaptive RK4 by step doubling: one step of h against two of h/2, error measured relative
// to the body's distance from the origin and its speed. Advances the body by exactly `span`
// (several accepted steps), keeps the last accepted step size in body.h (never above hMax)
// and returns the number of force evaluations.
export function rk4Adaptive(sys, body, span, hMax, tol) {
  const s = body.s;
  let left = span;
  let h = Math.min(body.h || hMax, hMax, span);
  let evals = 0;
  let guard = 0;
  while (left > 1e-12 * span && guard++ < 100000) {
    h = Math.min(h, left);
    evals += rk4Step(sys, s, h, BIG);
    evals += rk4Step(sys, s, 0.5 * h, HALF);
    evals += rk4Step(sys, HALF, 0.5 * h, HALF);
    const L = Math.max(1e-9, Math.hypot(s[0], s[1], s[2]));
    const V = Math.max(1e-9, Math.hypot(s[3], s[4], s[5]));
    let err = 0;
    for (let i = 0; i < 3; i++) {
      err = Math.max(err, Math.abs(BIG[i] - HALF[i]) / L, Math.abs(BIG[i + 3] - HALF[i + 3]) / V);
    }
    if (err > tol && h > 1e-6 * hMax) {
      h *= Math.max(0.2, 0.9 * Math.pow(tol / err, 0.2));
      continue;
    }
    for (let i = 0; i < 6; i++) s[i] = HALF[i];
    left -= h;
    body.h = Math.min(hMax, h * (err > 0 ? Math.min(4, 0.9 * Math.pow(tol / err, 0.2)) : 4));
    h = body.h;
  }
  sys.accel(s[0], s[1], s[2], body.a);
  return evals + 1;
}

// ---------------------------------------------------------------- Kepler elements
// Inertial position and velocity (km, km/s) from classical elements (km, degrees).
export function stateFromElements(gm, a, e, incDeg, raanDeg, argpDeg, meanAnomalyDeg) {
  const rad = Math.PI / 180;
  const M = ((meanAnomalyDeg * rad) % (2 * Math.PI) + 2 * Math.PI) % (2 * Math.PI);
  let E = e < 0.8 ? M : Math.PI;
  for (let k = 0; k < 60; k++) {
    const dE = (E - e * Math.sin(E) - M) / (1 - e * Math.cos(E));
    E -= dE;
    if (Math.abs(dE) < 1e-14) break;
  }
  const nu = 2 * Math.atan2(Math.sqrt(1 + e) * Math.sin(E / 2), Math.sqrt(1 - e) * Math.cos(E / 2));
  const p = a * (1 - e * e);
  const r = p / (1 + e * Math.cos(nu));
  const xp = r * Math.cos(nu);
  const yp = r * Math.sin(nu);
  const vf = Math.sqrt(gm / p);
  const vxp = -vf * Math.sin(nu);
  const vyp = vf * (e + Math.cos(nu));
  const [cO, sO] = [Math.cos(raanDeg * rad), Math.sin(raanDeg * rad)];
  const [ci, si] = [Math.cos(incDeg * rad), Math.sin(incDeg * rad)];
  const [cw, sw] = [Math.cos(argpDeg * rad), Math.sin(argpDeg * rad)];
  // rows of the perifocal-to-inertial rotation
  const P = [cO * cw - sO * sw * ci, sO * cw + cO * sw * ci, sw * si];
  const Q = [-cO * sw - sO * cw * ci, -sO * sw + cO * cw * ci, cw * si];
  const s = new Float64Array(6);
  for (let i = 0; i < 3; i++) {
    s[i] = P[i] * xp + Q[i] * yp;
    s[i + 3] = P[i] * vxp + Q[i] * vyp;
  }
  return s;
}

// Osculating semi-major axis and eccentricity of a point-mass orbit.
export function osculating(gm, s) {
  const r = Math.hypot(s[0], s[1], s[2]);
  const v2 = s[3] * s[3] + s[4] * s[4] + s[5] * s[5];
  const E = 0.5 * v2 - gm / r;
  const hx = s[1] * s[5] - s[2] * s[4];
  const hy = s[2] * s[3] - s[0] * s[5];
  const hz = s[0] * s[4] - s[1] * s[3];
  const h2 = hx * hx + hy * hy + hz * hz;
  const a = -gm / (2 * E);
  const e = Math.sqrt(Math.max(0, 1 + (2 * E * h2) / (gm * gm)));
  return { a, e, r, v: Math.sqrt(v2), E };
}

// Elevation of a satellite above a station's horizon, in degrees; the station is given by
// its inertial unit vector u and the Earth's radius.
export function elevationDeg(sat, u, radius) {
  const dx = sat[0] - radius * u[0];
  const dy = sat[1] - radius * u[1];
  const dz = sat[2] - radius * u[2];
  const d = Math.hypot(dx, dy, dz);
  return (Math.asin((dx * u[0] + dy * u[1] + dz * u[2]) / d) * 180) / Math.PI;
}
