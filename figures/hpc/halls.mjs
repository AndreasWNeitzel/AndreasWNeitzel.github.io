// The halls figure of /guide/supercomputers/: the two machines as rows of cabinets at one scale.
// One cabinet stands for 32 nodes, as one square does in the site's HPC figure. Deucalion:
// 1,632 ARM nodes, 500 x86, 33 with A100 GPUs. MareNostrum 5: 6,408 general-purpose nodes and
// 1,120 accelerated with H100s. Cabinets of the partitions the two FCT allocations use are
// lit. Node counts from EuroHPC JU and the
// hosting sites. Usage: node figures/hpc/halls.mjs
import { writeFileSync } from "node:fs";
import * as k from "../kit/iso-kit.mjs";

const W = 1140, H = 560;
const CW = 6, CD = 12, CH = 20, GAP = 1.5, AISLE = 14, PER = 32, ROW = 26;
const f = (v) => (Math.round(v * 10) / 10).toString();
const machines = [
  { name: "DEUCALION", y0: 0, parts: [["ARM", 1632, true, false], ["x86", 500, false, false], ["A100", 33, true, true]] },
  { name: "MARENOSTRUM 5", y0: 118, parts: [["GPP", 6408, true, false], ["ACC", 1120, true, true]] },
];
const cabinets = [];
for (const m of machines) {
  let i = 0;
  for (const [code, n, used, gpu] of m.parts) {
    const count = Math.max(1, Math.round(n / PER));
    for (let j = 0; j < count; j++) {
      const r = Math.floor(i / ROW), col = i % ROW;
      cabinets.push({ x: col * (CW + GAP), y: m.y0 + r * (CD + AISLE), used, gpu, code, machine: m.name, first: j === 0 });
      i++;
    }
  }
  m.rows = Math.ceil(i / ROW);
  m.count = i;
}
const xmax = ROW * (CW + GAP) - GAP;
const ymax = machines[1].y0 + machines[1].rows * (CD + AISLE) - AISLE;
const P = k.fitProjection([[-30, -12, 0], [xmax + 12, -12, 0], [-30, ymax + 26, 0], [xmax + 12, ymax + 26, 0], [xmax + 12, -12, CH + 10], [xmax + 80, ymax, 0]], W, H, { pad: 24, azimuth: 32, elevation: 34 });
const at = (p) => k.iso(p, P);
const parts = [];
const part = (svg, anchor, layer = 0) => parts.push({ svg, depth: k.depthOf(anchor, P), layer });
const S = (paths, style) => k.solidSvg(paths, style);
const L = (d, style) => k.lineSvg(d, style);
const text = (p, s, anchor = "start", dy = 0) => { const [x, y] = at(p); return `<text class="iso-num" x="${f(x)}" y="${f(y + dy)}" text-anchor="${anchor}">${s}</text>`; };

// the floors, one per machine, with the name on the near edge
for (const m of machines) {
  const d = m.rows * (CD + AISLE) - AISLE;
  part(S(k.slabOf({ x: -6, y: m.y0 - 6, w: xmax + 12, d: d + 12, r: 2 }, -3, 3, P, 3, 0.8), { tone: "lo" }), [xmax, m.y0, -3], 0);
  part(text([xmax + 10, m.y0 + d / 2, 0], m.name, "start", 4), [xmax + 10, m.y0 + d / 2, 0], 4);
}
// the cabinets, far to near
for (const c of cabinets.sort((a, b) => k.depthOf([a.x, a.y, 0], P) - k.depthOf([b.x, b.y, 0], P))) {
  part(S(k.slabOf({ x: c.x, y: c.y, w: CW, d: CD, r: 0 }, 0, CH, P, 1, 0), { tone: c.used ? "mid" : "lo", lit: c.gpu, crease: "none" }), [c.x + CW, c.y, 0], 1);
}
// partition labels at the first cabinet of each, above the row
for (const c of cabinets.filter((q) => q.first)) {
  part(text([c.x + CW / 2, c.y - 2, CH + 11], c.code, "middle"), [c.x, c.y - 2, CH + 11], 4);
}
// scale: one cabinet is 32 nodes, as a dimension on the near floor edge
const sy = ymax + 14;
const sx = xmax - CW;
part(L(k.pathOf([at([sx, sy, 0]), at([xmax, sy, 0])]) + k.pathOf([at([sx, sy - 2, 0]), at([sx, sy + 2, 0])]) + k.pathOf([at([xmax, sy - 2, 0]), at([xmax, sy + 2, 0])]), { tone: "mid" }), [sx, sy, 0], 4);
part(text([sx - 4, sy, 0], "one cabinet, 32 nodes", "end", 4), [sx - 4, sy, 0], 4);

const body = parts.sort((p, q) => (p.layer - q.layer) || (p.depth - q.depth)).map((p) => p.svg).join("");
const counts = machines.map((m) => `${m.name} ${m.count} cabinets`).join(", ");
const label = `Two machine halls drawn as rows of cabinets at one scale, each cabinet standing for 32 nodes: ${counts}. The cabinets of the partitions used by the two allocations are drawn in a stronger tone, the GPU cabinets lit.`;
const svg = `<svg class="iso-svg" viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="${label}">${body}</svg>\n`;
writeFileSync(new URL("../../_includes/figures/hpc-halls.svg", import.meta.url), svg);
console.log(`wrote _includes/figures/hpc-halls.svg (${(svg.length / 1024).toFixed(1)} KB)`);
