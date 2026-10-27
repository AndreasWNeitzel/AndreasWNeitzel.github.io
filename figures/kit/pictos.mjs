// Small three-dimensional pictograms for the site's 2D schematics, drawn with the isometric kit
// and written to figures/kit/pictos.json as {name: {w, h, body}}. The Python figure scripts
// place each one inside its box with a <g class="iso-svg" transform="..."> wrapper, so the
// kit's tones follow the site's tokens (site.css). Usage: node figures/kit/pictos.mjs
import { writeFileSync } from "node:fs";
import * as k from "./iso-kit.mjs";
import * as la from "./lathe.mjs";

const AZ = 38, EL = 30;
const out = {};

function pictogram(name, w, h, extent, draw) {
  const P = k.fitProjection(extent, w, h, { pad: 4, azimuth: AZ, elevation: EL });
  const parts = [];
  const ctx = {
    P,
    at: (p) => k.iso(p, P),
    part: (svg, anchor, layer = 0) => parts.push({ svg, depth: k.depthOf(anchor, P), layer }),
    slab: (x, y, z, wd, d, ht, style, r = 0.6) => k.solidSvg(k.slabOf({ x, y, w: wd, d, r }, z, ht, P, 2, 0.2), style),
    line: (pts, style) => k.lineSvg(k.pathOf(pts.map((p) => k.iso(p, P))), style),
  };
  const anchors = draw(ctx) || {};
  out[name] = { w, h, anchors, body: parts.sort((a, b) => (a.layer - b.layer) || (a.depth - b.depth)).map((q) => q.svg).join("") };
}

// a storage cabinet: a tall rack with shelves of drive bays across its front
pictogram("storage", 96, 120, [[0, 0, 0], [24, 30, 0], [0, 30, 60], [24, 0, 60]], ({ part, slab, line }) => {
  part(slab(0, 0, 0, 24, 30, 60, { tone: "mid" }, 1), [24, 0, 0], 0);
  const bays = [];
  for (let s = 0; s < 8; s++) {
    const z = 5 + s * 6.6;
    bays.push(line([[24.2, 3, z], [24.2, 27, z]], { tone: "lo" }));
    for (let b = 0; b < 6; b++) bays.push(line([[24.2, 4 + b * 4, z + 1], [24.2, 4 + b * 4, z + 5]], { tone: "faint" }));
  }
  part(bays.join(""), [30, 15, 30], 1);
});

// CPU nodes: five 1U servers stacked, fronts lit by a row of status marks
pictogram("cpu", 96, 120, [[0, 0, 0], [30, 34, 0], [0, 34, 50], [30, 0, 50]], ({ part, slab, line }) => {
  for (let i = 0; i < 5; i++) {
    const z = i * 10;
    part(slab(0, 0, z, 30, 34, 8, { tone: "mid", lit: i === 4 }, 0.6), [30, 0, z], i);
    part(line([[30.2, 4, z + 4], [30.2, 30, z + 4]], { tone: "faint" }), [31, 17, z + 4], i);
  }
});

// a GPU node: an open tray with four accelerator cards standing in it
pictogram("gpu", 96, 120, [[0, 0, 0], [40, 36, 0], [0, 36, 30], [40, 0, 30]], ({ part, slab }) => {
  part(slab(0, 0, 0, 40, 36, 4, { tone: "mid" }, 0.8), [40, 0, 0], 0);
  for (let i = 0; i < 4; i++) {
    const x = 5 + i * 9;
    part(slab(x, 4, 4, 4, 28, 22, { tone: "mid", lit: true }, 0.4), [x + 4, 4, 4], 1 + i);
  }
});

// the catalogue: three sheets standing upright, the front one ruled into rows with two cells lit
pictogram("catalogue", 96, 120, [[0, 0, 0], [12, 36, 0], [0, 36, 50], [12, 0, 50]], ({ part, slab, line }) => {
  for (let i = 0; i < 3; i++) part(slab(i * 4, i * 2.5, i * 2, 1.2, 30, 44, { tone: i === 2 ? "mid" : "lo" }, 0.3), [i * 4 + 1.2, i * 2.5, i * 2], i);
  const xf = 2 * 4 + 1.25, y0 = 2 * 2.5, z0 = 2 * 2;
  const rows = [];
  for (let r = 1; r < 8; r++) rows.push(line([[xf, y0 + 3, z0 + 44 - r * 5.2], [xf, y0 + 22, z0 + 44 - r * 5.2]], { tone: "lo" }));
  part(rows.join(""), [xf + 1, y0 + 15, z0 + 22], 4);
  for (const r of [2, 5]) part(slab(xf, y0 + 23.5, z0 + 44 - r * 5.2 - 1.8, 0.6, 4, 3.6, { tone: "mid", lit: true }, 0.2), [xf + 1, y0 + 23, z0 + 30], 5);
});

// Gaia: the deployed sunshield (12 panels, about 10 m across), the service module (a short
// hexagonal prism) and the payload module under its thermal tent, in proportion. The anchor is
// the top of the tent, where the starlight enters in FIG 1.
pictogram("gaia", 170, 104, [[-50, -50, 0], [50, 50, 0], [-50, 50, 0], [50, -50, 0], [0, 0, 36]], ({ P, part, line }) => {
  part(k.solidSvg(k.cylinder(0, 0, 50, 0, 1.2, P, 12, 0), { tone: "mid" }), [0, 0, 0], 0);
  const ribs = [];
  for (let i = 0; i < 12; i++) { const a = (i + 0.5) * Math.PI / 6; ribs.push(line([[17 * Math.cos(a), 17 * Math.sin(a), 1.3], [49 * Math.cos(a), 49 * Math.sin(a), 1.3]], { tone: "lo" })); }
  part(ribs.join(""), [0, 0, 1.3], 1);
  part(k.solidSvg(k.cylinder(0, 0, 17, 1.2, 9, P, 6, 0), { tone: "mid" }), [0, 0, 1.2], 2);
  part(k.solidSvg(k.cylinder(0, 0, 14, 10.2, 22, P, 40, 0), { tone: "mid", lit: true }), [0, 0, 10.2], 3);
  // the two telescope apertures on the tent, 106.5 degrees apart
  const ap = [];
  for (const a0 of [-0.93, 0.93]) { const a = Math.PI / 4 + a0; ap.push(line([[14.2 * Math.cos(a), 14.2 * Math.sin(a), 22], [14.2 * Math.cos(a), 14.2 * Math.sin(a), 28]], { tone: "hi" })); }
  part(ap.join(""), [0, 0, 32], 4);
  return { top: k.iso([0, 0, 32.2], P) };
});

// a patch of detector: 9 by 9 pixels, the target's mask raised and lit, the target's light as a
// tall bump and one neighbour's as a lower bump overlapping the mask's edge
pictogram("detector", 150, 90, [[0, 0, -4], [90, 90, -4], [0, 90, 0], [90, 0, 0], [45, 45, 30]], ({ P, part, at }) => {
  const PXL = 10, N = 9;
  part(k.solidSvg(k.slabOf({ x: 0, y: 0, w: N * PXL, d: N * PXL, r: 0.6 }, -4, 4, P, 2, 0.3), { tone: "mid" }), [N * PXL, 0, -4], 0);
  const grid = [];
  for (let i = 1; i < N; i++) { grid.push(k.lineOnTop([i * PXL, 0], [i * PXL, N * PXL], 0, P)); grid.push(k.lineOnTop([0, i * PXL], [N * PXL, i * PXL], 0, P)); }
  part(k.lineSvg(grid.join(""), { tone: "faint" }), [45, 45, 0], 1);
  const c = 4 * PXL;
  // a compact mask of six pixels on the target's brightest pixels; the noise estimator chooses it per star
  for (const [dx, dy] of [[0, 0], [1, 0], [-1, 0], [0, 1], [0, -1], [1, 1]])
    part(k.solidSvg(k.slabOf({ x: c + dx * PXL, y: c + dy * PXL, w: PXL, d: PXL, r: 0.2 }, 0, 1.4, P, 1, 0), { tone: "mid", lit: true }), [c + dx * PXL + PXL, c + dy * PXL, 1.4], 2);
  // each star's light as a wire profile: two meridians and the half-maximum ring, so the
  // pixels and the mask stay visible under it
  const bump = (cx, cy, h, sg, tone) => {
    const g = (r) => 1.6 + h * Math.exp(-(r * r) / (2 * sg * sg));
    const mx = [], my = [];
    for (let i = 0; i <= 24; i++) { const r = (i / 24 - 0.5) * 6.4 * sg; mx.push(at([cx + r, cy, g(r)])); my.push(at([cx, cy + r, g(r)])); }
    const rh = sg * Math.sqrt(2 * Math.log(2));
    const ring = k.circleRing(0, 0, rh, 36).map(([u, v]) => at([cx + u, cy + v, g(rh)]));
    return k.lineSvg(k.pathOf(mx) + k.pathOf(my) + k.pathOf(ring, true), { tone });
  };
  // one PSF for every star: sigma 0.61 pixel (a Gaussian with 90 per cent of its energy in 1.3 arcsec)
  part(bump(c + 23, c + 13, 14, 6.1, "mid"), [c + 23, c + 13, 20], 3);
  part(bump(c + 5, c + 5, 26, 6.1, "lit"), [c + 5, c + 5, 30], 4);
});

writeFileSync(new URL("./pictos.json", import.meta.url), JSON.stringify(out));
console.log("wrote figures/kit/pictos.json:", Object.entries(out).map(([n, v]) => `${n} ${(v.body.length / 1024).toFixed(1)} KB`).join(", "));
