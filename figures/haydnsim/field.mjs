// The crowding figure of /software/haydnsim/: one line of sight through a globular cluster.
// The telescope looks along y. Far along it sits a cluster of synthetic stars drawn from a King
// profile; at y = 0 stands the detector, a plate of pixels facing the cluster; the column of sky
// the field covers is the tube between them. Seven stars near one line of sight through the
// core are ringed, and their light lands on the same pixels: on the plate their profiles pile
// onto the raised mask of the target. The share of the mask's light that is not the target's is
// what HAYDNsim returns, star by star. Usage: node figures/haydnsim/field.mjs
import { writeFileSync } from "node:fs";
import * as k from "../kit/iso-kit.mjs";
import * as la from "../kit/lathe.mjs";

const TAU = Math.PI * 2;
const W = 1140, H = 420;
const SW = 720; // the 3D scene takes the left part; the mask detail the right
const RC = 70, CY = 360, CZ = 70;
const C = [0, CY, CZ];
const PX = 10, N = 18, SIDE = PX * N, THICK = 6;
const PZ0 = CZ - SIDE / 2;
const MAG = (SIDE / 2) / RC * 0.92;
const onPlate = (x, z) => [(x - C[0]) * MAG, CZ + (z - CZ) * MAG];
const extent = [[0, CY, CZ - RC * 1.75], [-RC * 1.15, CY, CZ - RC * 1.15], [RC * 1.15, CY, CZ + RC * 1.15], [-RC * 1.15, CY, CZ - RC * 1.4], [-SIDE / 2 - 8, 0, PZ0 - 8], [SIDE / 2 + 8, 0, PZ0 + SIDE + 8], [SIDE / 2 + 8, -14, PZ0 - 30], [-SIDE / 2 - 8, -14, PZ0 + SIDE + 8]];
const P = k.fitProjection(extent, SW, H, { pad: 20, azimuth: 28, elevation: 22 });
const at = (p) => k.iso(p, P);
const parts = [];
const part = (svg, anchor, layer = 0) => parts.push({ svg, depth: k.depthOf(anchor, P), layer });
const S = (paths, style) => k.solidSvg(paths, style);
const L = (d, style) => k.lineSvg(d, style);
const f = (v) => (Math.round(v * 10) / 10).toString();

// a seeded random, so the cluster is the same on every build
let seed = 11;
const rnd = () => { seed = (seed * 48271) % 2147483647; return seed / 2147483647; };
// stars from a King-like density, concentrated, truncated at RC
const rc = RC / 25;
const king3 = (r) => Math.pow(1 + (r / rc) ** 2, -1.5) - Math.pow(1 + (RC / rc) ** 2, -1.5);
const cdf = [];
let acc = 0;
for (let i = 0; i <= 400; i++) { const r = (i / 400) * RC; acc += r * r * king3(r); cdf.push(acc); }
const draw3 = () => { const u = rnd() * acc; let lo = 0, hi = 400; while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (cdf[mid] < u) lo = mid; else hi = mid; } return (hi / 400) * RC; };
const stars = [];
for (let i = 0; i < 1600; i++) {
  const r = draw3(), u = rnd() * 2 - 1, ph = rnd() * TAU, s = Math.sqrt(1 - u * u);
  stars.push([C[0] + r * s * Math.cos(ph), C[1] + r * s * Math.sin(ph), C[2] + r * u]);
}
// the line of sight: through the core's edge, where single stars still show
const T = [-14, CZ + 10]; // where to look; re-centred on the target star below
const cand = stars.map((p, i) => ({ i, d: Math.hypot(p[0] - T[0], p[2] - T[1]), y: p[1] })).filter((q) => q.d < 4).sort((a, b) => a.d - b.d).slice(0, 40);
cand.sort((a, b) => a.y - b.y);
const near = [];
for (let j = 0; j < 7; j++) near.push(cand[Math.round((j / 6) * (cand.length - 1))].i);
// the target is the fourth of them by depth; the line of sight passes exactly through it
T[0] = stars[near[3]][0]; T[1] = stars[near[3]][2];
const depth = stars.map((p) => k.depthOf(p, P));
const dmin = Math.min(...depth), dmax = Math.max(...depth);
part(k.dotsSvg(stars.map((p, i) => [...at(p), 0.25 + 0.6 * (depth[i] - dmin) / (dmax - dmin)]).filter((_, i) => !near.includes(i)), { size: 0.9, tone: "hi" }), C, 3);
const ring = (cx, cy, r, steps = 80) => k.pathOf(k.circleRing(0, 0, r, steps).map(([x, y]) => [cx + x * P.scale, cy + y * P.scale]), true);
part(L(ring(...at(C), RC), { tone: "faint" }), [C[0], C[1] - RC, C[2]], 1);

// the column of sky the field covers
const corners = [[-SIDE / 2, PZ0], [SIDE / 2, PZ0], [SIDE / 2, PZ0 + SIDE], [-SIDE / 2, PZ0 + SIDE]];
const tube = [];
for (const [x, z] of corners) tube.push(k.pathOf([at([x, THICK / 2, z]), at([x / MAG, CY, CZ + (z - CZ) / MAG])]));
tube.push(k.pathOf(corners.map(([x, z]) => at([x / MAG, CY, CZ + (z - CZ) / MAG])), true));
part(L(tube.join(""), { tone: "faint" }), [0, CY / 2, CZ], 2);

// the plate, standing in the x-z plane; the frame along +y has its first axis toward -x
const F = la.frameAlong([0, 0, 0], [0, 1, 0]);
const plateSolid = (x, z, w, h, s0, s1, style) => S(la.prismOf(F, [[-x - w, z], [-x, z], [-x, z + h], [-x - w, z + h]], s0, s1, P), style);
part(plateSolid(-SIDE / 2 - 6, PZ0 - 6, SIDE + 12, SIDE + 12, -THICK - 6, -THICK, { tone: "lo" }), [0, -THICK - 6, CZ], 0);
part(plateSolid(-SIDE / 2, PZ0, SIDE, SIDE, -THICK, 0, { tone: "mid" }), [0, -THICK / 2, CZ], 0);
const grid = [];
for (let i = 1; i < N; i++) {
  grid.push(k.pathOf([at([-SIDE / 2 + i * PX, 0.2, PZ0]), at([-SIDE / 2 + i * PX, 0.2, PZ0 + SIDE])]));
  grid.push(k.pathOf([at([-SIDE / 2, 0.2, PZ0 + i * PX]), at([SIDE / 2, 0.2, PZ0 + i * PX])]));
}
part(L(grid.join(""), { tone: "faint" }), [0, 0.2, CZ], 1);
const landed = stars.map((p) => onPlate(p[0], p[2]));
part(k.dotsSvg(landed.filter((_, i) => !near.includes(i)).map(([x, z]) => at([x, 0.4, z])), { size: 0.75, tone: "hi" }), [0, 0.4, CZ], 2);
const TP = onPlate(T[0], T[1]);
const TPX = [Math.floor((TP[0] + SIDE / 2) / PX) * PX - SIDE / 2, Math.floor((TP[1] - PZ0) / PX) * PX + PZ0];
const erf = (x) => { const t = 1 / (1 + 0.3275911 * Math.abs(x)); const y = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-x * x); return x >= 0 ? y : -y; };
const cdf1 = (x, m, sg) => 0.5 * (1 + erf((x - m) / (sg * Math.SQRT2)));
// the noise estimator picks each star's mask from its brightest pixels: here the six pixels that
// collect the most of the target's own light (sigma 0.61 pixel, one PSF for every star)
const SIG = 6.06;
const pixFlux = (a, c, x, z, sg) => (cdf1(TPX[0] + (a + 1) * PX, x, sg) - cdf1(TPX[0] + a * PX, x, sg)) * (cdf1(TPX[1] + (c + 1) * PX, z, sg) - cdf1(TPX[1] + c * PX, z, sg));
const pix = [];
for (let a = -3; a <= 3; a++) for (let c = -3; c <= 3; c++) pix.push({ a, c, v: pixFlux(a, c, TP[0], TP[1], SIG) });
const mask = pix.sort((u, w) => w.v - u.v).slice(0, 6).map((q) => [q.a, q.c]);
for (const [dx, dz] of mask) part(plateSolid(TPX[0] + dx * PX, TPX[1] + dz * PX, PX, PX, 0, 1.6, { tone: "mid", lit: true }), [TPX[0] + dx * PX, 1.6, TPX[1] + dz * PX], 3);

// the seven stars near the line of sight, their paths, and their light on the plate
const lit = near.map((i) => stars[i]);
part(k.dotsSvg(lit.map((p) => at(p)), { size: 2.0, tone: "hi" }), C, 4);
part(L(lit.map((p) => ring(...at(p), 4.2 / P.scale, 24)).join(""), { tone: "hi" }), C, 4);
part(L(lit.map((p) => { const [x, z] = onPlate(p[0], p[2]); return k.pathOf([at(p), at([x, 1.8, z])]); }).join(""), { tone: "lit" }), [0, CY / 2, CZ], 2);
const ray = (y) => { const u = y / CY; return [TP[0] + (T[0] - TP[0]) * u, y, TP[1] + (T[1] - TP[1]) * u]; };
part(L(k.pathOf([at(ray(CY + RC)), at(ray(2))]), { tone: "blue", flow: true }), [0, CY / 2, CZ], 5);
const bump = (x, z, height, sigma) => {
  const g = (r) => 1.8 + height * Math.exp(-(r * r) / (2 * sigma * sigma));
  const mx = [];
  for (let i = 0; i <= 24; i++) { const r = (i / 24 - 0.5) * 6.4 * sigma; mx.push(at([x + r, g(r), z])); }
  const rh = sigma * Math.sqrt(2 * Math.log(2));
  return k.pathOf(mx) + k.pathOf(k.circleRing(0, 0, rh, 36).map(([u, v]) => at([x + u, g(rh), z + v])), true);
};
// one PSF for every star: sigma 0.61 pixel
const bumps = lit.map((p, j) => ({ x: onPlate(p[0], p[2])[0], z: onPlate(p[0], p[2])[1], h: j === 3 ? 34 : 12 + 10 * rnd(), s: SIG, main: j === 3 }));
part(L(bumps.filter((b) => !b.main).map((b) => bump(b.x, b.z, b.h, b.s)).join(""), { tone: "mid" }), [T[0], 10, T[1]], 6);
part(L(bumps.filter((b) => b.main).map((b) => bump(b.x, b.z, b.h, b.s)).join(""), { tone: "hi" }), [T[0], 12, T[1]], 7);

// dimensions: the field of view across the far end of the tube, and pixels along the plate's foot
const text = (x, y, s, anchor = "middle") => `<text class="iso-num" x="${f(x)}" y="${f(y)}" text-anchor="${anchor}">${s}</text>`;
const fz = CZ + (PZ0 - CZ) / MAG - 10;
const fov = [k.pathOf([at([-SIDE / 2 / MAG, CY, fz]), at([SIDE / 2 / MAG, CY, fz])]), k.pathOf([at([-SIDE / 2 / MAG, CY, fz + 3]), at([-SIDE / 2 / MAG, CY, fz - 3])]), k.pathOf([at([SIDE / 2 / MAG, CY, fz + 3]), at([SIDE / 2 / MAG, CY, fz - 3])])];
part(L(fov.join(""), { tone: "mid" }), [0, CY, fz], 7);
const f0 = at([-SIDE / 2 / MAG, CY, fz]), f1 = at([SIDE / 2 / MAG, CY, fz]);
const fang = (Math.atan2(f1[1] - f0[1], f1[0] - f0[0]) * 180) / Math.PI;
const fm = at([0, CY, fz]);
part(`<text class="iso-num" transform="translate(${f(fm[0])} ${f(fm[1])}) rotate(${f(fang)})" x="0" y="14" text-anchor="middle">1 degree</text>`, [0, CY, fz - 6], 8);
const ruler = [k.pathOf([at([-SIDE / 2, 0, PZ0 - 9]), at([SIDE / 2, 0, PZ0 - 9])])];
for (let i = 0; i <= N; i += 6) ruler.push(k.pathOf([at([-SIDE / 2 + i * PX, 0, PZ0 - 6]), at([-SIDE / 2 + i * PX, 0, PZ0 - 12])]));
part(L(ruler.join(""), { tone: "mid" }), [0, 0, PZ0 - 9], 7);
const r0 = at([-SIDE / 2, 0, PZ0 - 9]), r1 = at([SIDE / 2, 0, PZ0 - 9]);
const rang = (Math.atan2(r1[1] - r0[1], r1[0] - r0[0]) * 180) / Math.PI;
const rl = at([-SIDE / 2 + 3 * PX, 0, PZ0 - 9]);
part(`<text class="iso-num" transform="translate(${f(rl[0])} ${f(rl[1])}) rotate(${f(rang)})" x="0" y="14" text-anchor="middle">3 arcsec</text>`, [0, 0, PZ0 - 20], 8);

const body = parts.sort((p, q) => (p.layer - q.layer) || (p.depth - q.depth)).map((p) => p.svg).join("");

// ---- the mask in detail, flat: 7 by 7 pixels about the target, the mask's pixels shaded, each
// star's light as its half-maximum circle, and the light the mask collects split by origin
const DX0 = 780, DY0 = 46, CELL = 30, NP = 7;
const pc = [TPX[0] + PX / 2, TPX[1] + PX / 2]; // centre of the target's pixel, plate units
const toD = (x, z) => [DX0 + (NP / 2) * CELL + ((x - pc[0]) / PX) * CELL, DY0 + (NP / 2) * CELL - ((z - pc[1]) / PX) * CELL];
const dp = [];
const mset = new Set(mask.map(([a, b]) => `${a},${b}`));
for (let i = 0; i < NP; i++) for (let j = 0; j < NP; j++) {
  const a = i - 3, b = 3 - j;
  const cls = mset.has(`${a},${b}`) ? "dp-mask" : "dp-px";
  dp.push(`<rect class="${cls}" x="${f(DX0 + i * CELL)}" y="${f(DY0 + j * CELL)}" width="${CELL}" height="${CELL}"/>`);
}
// light in the mask: integrate each star's Gaussian over the mask pixels
const inMask = (b) => mask.reduce((acc, [a, c]) => {
  const x0 = pc[0] + (a - 0.5) * PX, z0 = pc[1] + (c - 0.5) * PX;
  return acc + (cdf1(x0 + PX, b.x, b.s) - cdf1(x0, b.x, b.s)) * (cdf1(z0 + PX, b.z, b.s) - cdf1(z0, b.z, b.s));
}, 0);
let fT = 0, fN = 0;
for (const b of bumps) { const flux = b.h * b.s * b.s * inMask(b); if (b.main) fT += flux; else fN += flux; }
const spr = fN / (fT + fN);
const clip = `<clipPath id="dp-clip"><rect x="${DX0}" y="${DY0}" width="${NP * CELL}" height="${NP * CELL}"/></clipPath>`;
const circ = [];
for (const b of bumps) {
  const [cx, cy] = toD(b.x, b.z);
  const r = (b.s * Math.sqrt(2 * Math.log(2)) / PX) * CELL;
  circ.push(`<circle class="${b.main ? "dp-target" : "dp-neigh"}" cx="${f(cx)}" cy="${f(cy)}" r="${f(r)}"/>`);
  circ.push(`<circle class="${b.main ? "dp-target-c" : "dp-neigh-c"}" cx="${f(cx)}" cy="${f(cy)}" r="2.2"/>`);
}
dp.push(clip, `<g clip-path="url(#dp-clip)">${circ.join("")}</g>`);
dp.push(`<rect class="dp-frame" x="${DX0}" y="${DY0}" width="${NP * CELL}" height="${NP * CELL}"/>`);
// the split of the mask's light, as one bar under the grid
const BY = DY0 + NP * CELL + 34, BW = NP * CELL;
dp.push(`<rect class="dp-bar-t" x="${DX0}" y="${BY}" width="${f(BW * (1 - spr))}" height="12"/>`);
dp.push(`<rect class="dp-bar-n" x="${f(DX0 + BW * (1 - spr))}" y="${BY}" width="${f(BW * spr)}" height="12"/>`);
dp.push(`<text class="iso-num" x="${DX0}" y="${BY - 8}">target</text>`);
dp.push(`<text class="iso-num" x="${DX0 + BW}" y="${BY - 8}" text-anchor="end">neighbours</text>`);
dp.push(`<text class="dp-spr" x="${DX0 + BW}" y="${BY + 32}" text-anchor="end">SPR = ${spr.toFixed(2)}</text>`);
dp.push(`<text class="iso-num" x="${DX0}" y="${BY + 32}">light in the mask</text>`);
// pixel scale beside the grid
const sx = DX0 + NP * CELL + 14;
dp.push(`<path class="dp-dim" d="M${sx} ${DY0} v${2 * CELL} M${sx - 4} ${DY0} h8 M${sx - 4} ${DY0 + 2 * CELL} h8"/>`);
dp.push(`<text class="iso-num" x="${sx + 8}" y="${DY0 + CELL + 4}">1″</text>`);
// a hairline from the mask on the plate to the detail
const mtop = at([pc[0], 1.6, pc[1] + 2.5 * PX]);
const lead = `<path class="dp-lead" d="M${f(mtop[0])} ${f(mtop[1])} L${DX0} ${DY0}"/>`;

const label = `Left, a globular cluster of synthetic stars far along the telescope's axis, the column of sky the one-degree field covers, and the detector facing it with the cluster landed on its pixels; seven stars near one line of sight through the core are ringed and their light paths meet on the target's raised mask. Right, the mask in detail: seven by seven pixels with the mask shaded, the half-maximum circle of the target and of each neighbour, and a bar splitting the light the mask collects into the target's and the neighbours', a stellar pollution ratio of ${spr.toFixed(2)} for this drawing.`;
const svg = `<svg class="iso-svg" viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="${label}">${body}${lead}${dp.join("")}</svg>\n`;
writeFileSync(new URL("../../_includes/figures/haydn-field.svg", import.meta.url), svg);
console.log(`wrote _includes/figures/haydn-field.svg (${(svg.length / 1024).toFixed(1)} KB), SPR ${spr.toFixed(3)}`);
