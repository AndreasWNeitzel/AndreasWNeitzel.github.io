// The kinematic spiral of the Orbits playground: test stars on epicyclic orbits in the plane of
// MWPotential2014, set up as nested two-armed ovals whose orientation turns with radius
// (Kalnajs 1973, PASA 2, 174). There is no self-gravity: each oval keeps turning at its own
// Omega - kappa/2, which the potential fixes, so the pattern is not rigid and winds up, more
// slowly than a material arm would. No DOM here, so the code also runs under node.
//
// Units: kpc and Myr for positions and times, km/s/kpc for the rates a reader sees.
//
// With theta = kappa t + theta0, a star on an orbit of guiding radius Rg and relative amplitude
// epsilon sits at (Binney and Tremaine 2008, section 3.2.3, first order in epsilon)
//   R   = Rg (1 + epsilon cos theta)
//   phi = psi(Rg) + (Omega - kappa/2) t + theta / 2 - (2 Omega / kappa) epsilon sin theta,
// which at any instant is a closed oval with its long axis along psi(Rg) + (Omega - kappa/2) t.
import { KPC_PER_MYR_PER_KMS } from "./orbits-physics.js";

// The set-up, chosen for this figure: the count, radii, amplitude and opening pitch of the
// pattern at t = 0 are not measurements of the Milky Way.
export const SPIRAL = { count: 5000, Rmin: 3, Rmax: 15, epsilon: 0.12, pitchDeg: 15, R0: 8, seed: 1973 };

// Circular frequency and epicyclic frequency in km/s/kpc at radius R in the plane.
export function rates(mw, R) {
  const f = [0, 0];
  const omega2 = (r) => -mw.force(r, 0, f)[0] / r;
  const h = 1e-4 * R;
  const slope = (omega2(R + h) - omega2(R - h)) / (2 * h);
  const o2 = omega2(R);
  return { omega: Math.sqrt(o2), kappa: Math.sqrt(R * slope + 4 * o2) };
}

// Mulberry32, so that every visitor sees the same stars.
function random(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let z = a;
    z = Math.imul(z ^ (z >>> 15), z | 1);
    z ^= z + Math.imul(z ^ (z >>> 7), z | 61);
    return ((z ^ (z >>> 14)) >>> 0) / 4294967296;
  };
}

export function makeDisc(mw, cfg = SPIRAL) {
  const { count, Rmin, Rmax, epsilon, pitchDeg, R0, seed } = cfg;
  const k = KPC_PER_MYR_PER_KMS;
  const cot = 1 / Math.tan((pitchDeg * Math.PI) / 180);
  const rand = random(seed);
  const disc = {
    cfg, count, epsilon, cot,
    Rg: new Float64Array(count), kappa: new Float64Array(count), pattern: new Float64Array(count),
    gamma: new Float64Array(count), psi: new Float64Array(count), theta0: new Float64Array(count),
  };
  for (let i = 0; i < count; i++) {
    const Rg = Rmin + (Rmax - Rmin) * rand();
    const r = rates(mw, Rg);
    disc.Rg[i] = Rg;
    disc.kappa[i] = r.kappa * k;
    disc.pattern[i] = (r.omega - r.kappa / 2) * k;
    disc.gamma[i] = (2 * r.omega) / r.kappa;
    disc.psi[i] = -cot * Math.log(Rg / R0); // trailing: the outer ovals lag
    disc.theta0[i] = 4 * Math.PI * rand();
  }
  return disc;
}

// Positions at time t (Myr) in a frame turning at `frame` rad/Myr, written to x and y.
export function place(disc, t, frame, x, y) {
  const { count, epsilon, Rg, kappa, pattern, gamma, psi, theta0 } = disc;
  for (let i = 0; i < count; i++) {
    const th = kappa[i] * t + theta0[i];
    const R = Rg[i] * (1 + epsilon * Math.cos(th));
    const phi = psi[i] + (pattern[i] - frame) * t + 0.5 * th - gamma[i] * epsilon * Math.sin(th);
    x[i] = R * Math.cos(phi);
    y[i] = R * Math.sin(phi);
  }
}

// One star at time t, for the short trails of the marked stars; out = [x, y].
export function placeOne(disc, i, t, frame, out) {
  const th = disc.kappa[i] * t + disc.theta0[i];
  const R = disc.Rg[i] * (1 + disc.epsilon * Math.cos(th));
  const phi = disc.psi[i] + (disc.pattern[i] - frame) * t + 0.5 * th - disc.gamma[i] * disc.epsilon * Math.sin(th);
  out[0] = R * Math.cos(phi);
  out[1] = R * Math.sin(phi);
  return out;
}

// The oval through every star of guiding radius Rg at time t, as flat [x0, y0, x1, y1, ...].
export function oval(mw, disc, Rg, t, frame, points = 96) {
  const r = rates(mw, Rg);
  const gamma = (2 * r.omega) / r.kappa;
  const turned = -disc.cot * Math.log(Rg / disc.cfg.R0) + ((r.omega - r.kappa / 2) * KPC_PER_MYR_PER_KMS - frame) * t;
  const out = new Float32Array(2 * points);
  for (let i = 0; i < points; i++) {
    const th = (4 * Math.PI * i) / points;
    const R = Rg * (1 + disc.epsilon * Math.cos(th));
    const phi = turned + 0.5 * th - gamma * disc.epsilon * Math.sin(th);
    out[2 * i] = R * Math.cos(phi);
    out[2 * i + 1] = R * Math.sin(phi);
  }
  return out;
}

// Pitch angle (degrees) of the pattern at radius R after t Myr: the ovals started on a
// logarithmic spiral and the shear of Omega - kappa/2 adds to its cotangent.
export function pitchAt(mw, disc, R, t) {
  const h = 1e-3 * R;
  const p = (r) => { const q = rates(mw, r); return q.omega - q.kappa / 2; };
  const slope = ((p(R + h) - p(R - h)) / (2 * h)) * KPC_PER_MYR_PER_KMS; // rad/Myr/kpc
  return (Math.atan2(1, disc.cot - R * slope * t) * 180) / Math.PI;
}
