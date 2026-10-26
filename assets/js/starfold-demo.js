// Starfold on a recorded run: the APOGEE DR19 example table drawn on three linked canvases (the
// map HDBSCAN cut, the chemistry plane and an orbit plane), with the 32 refits and a star panel.
// Data: assets/data/starfold/apogee_run.json (header) and apogee_run.bin (arrays), written by
// figures/starfold/export_apogee_run.py. The page only draws and counts what the run stored.
// Colours come from the site tokens (window.siteTokens) and are read again on a theme change.

const MINUS = "−";
const TAU = Math.PI * 2;
const motion = matchMedia("(prefers-reduced-motion: reduce)");
const coarse = matchMedia("(hover: none)");
const REFIT_MS = 1100; // time on each refit while replaying
const REFIT_MS_REDUCED = 1800; // slower steps, without cross-fades, under reduced motion
const FADE_MS = 320; // cross-fade between refits, skipped under reduced motion
const PICK_PX = 10; // hover radius for a mouse
const TOUCH_PX = 18; // tap radius
const BRUSH_PX = 4; // drag distance that starts a selection
const CELL = 20; // grid cell for picking
const LEVELS = 8; // opacity steps for support
const RAMP_STEPS = 24;
// matplotlib 3.11 cividis at 17 stops (the site's sequential map, figures/tokens.json).
const CIVIDIS = ["#00224e", "#002e6a", "#1a386f", "#32436d", "#434e6c", "#535a6d", "#61656f", "#6f7073",
  "#7d7c78", "#8c8878", "#9b9476", "#aba072", "#bcae6c", "#cdbb63", "#dec958", "#f0d846", "#fee838"];
// The part of the map used in each theme keeps every step at 2:1 or more against the panel.
const RAMP_RANGE = { light: [0, 0.78], dark: [0.2, 1] };
const LOG_COLUMNS = new Set(["J_R", "J_z"]);

const root = document.getElementById("sf-demo");
if (root) {
  const start = () => boot(root).catch((err) => {
    console.error(err);
    const state = root.querySelector(".sfd-state");
    state.classList.add("is-alert");
    state.textContent = "The recorded run could not be loaded here; the tables below hold its numbers.";
  });
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => {
      if (entries.some((e) => e.isIntersecting)) {
        io.disconnect();
        start();
      }
    }, { rootMargin: "400px 0px" });
    io.observe(root);
  } else start();
}

// ---------------------------------------------------------------- formatting
function signed(v, digits = 2) {
  const r = Number(v.toFixed(digits));
  return (r < 0 ? MINUS : r > 0 ? "+" : "") + Math.abs(r).toFixed(digits);
}
const grouped = (v) => (Math.round(v) < 0 ? MINUS : "") + Math.abs(Math.round(v)).toLocaleString("en-GB");
const sig3 = (v) => (Math.abs(v) >= 1000 ? grouped(v) : (v < 0 ? MINUS : "") + String(Number(Math.abs(v).toPrecision(3))));
const tickText = (v) => (v < 0 ? MINUS : "") + String(Number(Math.abs(v).toPrecision(4)));
const FORMAT = {
  fe_h: (v) => signed(v), alpha_m: (v) => signed(v), mg_fe: (v) => signed(v),
  J_R: sig3, J_z: sig3, L_z: grouped, ecc: (v) => v.toFixed(2), E: grouped,
};
// Axis and field names as runs of text: "" plain, "i" italic symbol, "s" subscript.
const NAME = {
  fe_h: [["[Fe/H]", ""]], alpha_m: [["[α/M]", ""]], mg_fe: [["[Mg/Fe]", ""]],
  J_R: [["J", "i"], ["R", "s"]], J_z: [["J", "i"], ["z", "s"]], L_z: [["L", "i"], ["z", "s"]],
  ecc: [["eccentricity", ""]], E: [["E", "i"]],
};

function partsNode(parts) {
  const span = document.createElement("span");
  for (const [text, style] of parts) {
    const el = style === "i" ? document.createElement("i") : style === "s" ? document.createElement("sub") : document.createTextNode(text);
    if (style) el.textContent = text;
    span.append(el);
  }
  return span;
}

// ---------------------------------------------------------------- colour
function siteTokens() {
  if (window.siteTokens) return window.siteTokens;
  const probe = document.createElement("span");
  probe.style.cssText = "position:absolute;visibility:hidden;pointer-events:none";
  document.body.appendChild(probe);
  return {
    colour(name) {
      probe.style.color = `var(${name})`;
      return getComputedStyle(probe).color;
    },
    onThemeChange(callback) {
      new MutationObserver(callback).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
      matchMedia("(prefers-color-scheme: dark)").addEventListener("change", callback);
    },
  };
}

const pixel = (() => {
  const c = document.createElement("canvas");
  c.width = c.height = 1;
  return c.getContext("2d", { willReadFrequently: true });
})();

function rgbOf(css) {
  pixel.clearRect(0, 0, 1, 1);
  pixel.fillStyle = "#000";
  pixel.fillStyle = css;
  pixel.fillRect(0, 0, 1, 1);
  const [r, g, b] = pixel.getImageData(0, 0, 1, 1).data;
  return [r, g, b];
}

function luminance(css) {
  const lin = (c) => ((c /= 255) <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
  const [r, g, b] = rgbOf(css).map(lin);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

const CIVIDIS_RGB = CIVIDIS.map((h) => [1, 3, 5].map((k) => parseInt(h.slice(k, k + 2), 16)));
function cividis(u) {
  const x = Math.min(1, Math.max(0, u)) * (CIVIDIS_RGB.length - 1);
  const k = Math.min(CIVIDIS_RGB.length - 2, Math.floor(x));
  const f = x - k;
  const [a, b] = [CIVIDIS_RGB[k], CIVIDIS_RGB[k + 1]];
  return `rgb(${a.map((v, i) => Math.round(v + (b[i] - v) * f)).join(" ")})`;
}

// ---------------------------------------------------------------- data
function request(url, type) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("GET", url);
    xhr.responseType = type;
    xhr.onload = () => {
      if (xhr.status === 200 || (xhr.status === 0 && xhr.response)) resolve(xhr.response);
      else reject(new Error(`${url}: HTTP ${xhr.status}`));
    };
    xhr.onerror = () => reject(new Error(`${url}: network error`));
    xhr.send();
  });
}

const VIEWS = { uint64: BigUint64Array, float32: Float32Array, int8: Int8Array, uint8: Uint8Array };

async function loadRun(headerUrl) {
  const header = await request(headerUrl, "json");
  const binUrl = new URL(header.binary, new URL(headerUrl, document.baseURI)).href;
  const buffer = await request(binUrl, "arraybuffer");
  const arrays = {};
  for (const a of header.arrays) {
    const View = VIEWS[a.dtype];
    if (!View) throw new Error(`unknown dtype ${a.dtype}`);
    arrays[a.name] = new View(buffer, a.offset, a.length);
  }
  // Refit labels: two 4-bit values per byte, low nibble first; label = value - 2, so -2 is
  // "not drawn by this refit" and -1 "unassigned in this refit".
  const [W, n] = header.arrays.find((a) => a.name === "refit_labels").shape;
  const packed = arrays.refit_labels;
  const labels = new Int8Array(W * n);
  for (let i = 0; i < W * n; i++) labels[i] = ((i & 1) ? packed[i >> 1] >> 4 : packed[i >> 1] & 15) - 2;
  arrays.refits = labels;
  return { header, arrays };
}

// ---------------------------------------------------------------- canvas
function surface(canvas) {
  const s = { canvas, ctx: canvas.getContext("2d"), w: 0, h: 0, dpr: 1 };
  s.fit = () => {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;
    if (w === s.w && h === s.h && dpr === s.dpr) return false;
    Object.assign(s, { w, h, dpr });
    canvas.width = Math.max(1, Math.round(w * dpr));
    canvas.height = Math.max(1, Math.round(h * dpr));
    return true;
  };
  return s;
}

function line(ctx, x0, y0, x1, y1) {
  ctx.beginPath();
  ctx.moveTo(x0, y0);
  ctx.lineTo(x1, y1);
  ctx.stroke();
}

function ticksFor(lo, hi, count) {
  const span = hi - lo;
  const raw = span / Math.max(1, count);
  const mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => span / s <= count) ?? 10 * mag;
  const out = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi + step * 1e-9; v += step) out.push(Number(v.toFixed(10)));
  return out;
}

// ---------------------------------------------------------------- the demo
async function boot(root) {
  const $ = (sel) => root.querySelector(sel);
  const T = siteTokens();
  const { header: H, arrays: A } = await loadRun(root.dataset.header);
  const n = H.n;
  const d = H.columns.length;
  const G = H.groups.length;
  const W = H.refits.n;
  const names = H.columns.map((c) => c.name);
  const J = Object.fromEntries(names.map((name, j) => [name, j]));
  const X = A.features;
  const value = (i, j) => X[i * d + j];
  const group = A.group;
  const own = new Float32Array(n).fill(NaN);
  for (let i = 0; i < n; i++) if (group[i] >= 0) own[i] = A.support[i * G + group[i]];
  const pct = (j, p) => H.columns[j].percentiles[p];
  const refitOf = (k, i) => A.refits[k * n + i];
  // Outcome of star i in refit k: -3 not drawn, -1 unassigned, G a group with no counterpart,
  // otherwise the group of the fit on all stars that the refit group matched.
  function outcome(k, i) {
    const lab = refitOf(k, i);
    if (lab === -2) return -3;
    if (lab === -1) return -1;
    const g = H.refits.matches[k].match[lab];
    return g < 0 ? G : g;
  }

  const ui = {
    state: $(".sfd-state"),
    colour: $(".sfd-colour"),
    key: $(".sfd-key"),
    sel: $(".sfd-sel"),
    selText: $(".sfd-sel-text"),
    clear: $(".sfd-clear"),
    play: $(".sfd-play"),
    prev: $(".sfd-prev"),
    next: $(".sfd-next"),
    back: $(".sfd-back"),
    strip: $(".sfd-strip"),
    refitNow: $(".sfd-refit-now"),
    refitText: $(".sfd-refit-text"),
    pick: $(".sfd-pick"),
    find: $(".sfd-find"),
    findInput: $(".sfd-find input"),
    findButton: $(".sfd-find button"),
    facts: $(".sfd-facts"),
    cells: $(".sfd-cells"),
    history: $(".sfd-history-text"),
    feats: $(".sfd-feats"),
    calib: $(".sfd-calib-plot"),
    chemY: $(".sfd-chem-y"),
    orbitPlain: $(".sfd-orbit-plain"),
    orbitExact: $(".sfd-orbit-exact"),
  };

  // ------------------------------------------------------------ state
  const S = {
    view: "fit", // "fit", "refit" or "col"
    refit: 0,
    colJ: 0,
    chemY: J.alpha_m,
    orbit: "el",
    hover: -1,
    hoverPanel: null,
    pinned: H.examples[Math.min(2, H.examples.length - 1)].row,
    sel: new Uint8Array(n),
    selCount: 0,
    selKey: null,
    playing: false,
  };
  let C = null;
  let F = null;
  let dark = true;
  let styles = [];
  let order = [];
  const styleOf = new Uint16Array(n);
  let buckets = null;
  let drag = null;
  let timer = 0;
  let raf = 0;
  let fade = null;

  function readTheme() {
    const c = (name) => T.colour(name);
    C = {
      surface: c("--surface"), line: c("--line"), lineStrong: c("--line-strong"), ink: c("--ink"),
      ink2: c("--ink-2"), muted: c("--muted"), accent: c("--accent"), context: c("--context"),
      groups: [c("--cat-0"), c("--cat-6")], extra: c("--cat-4"),
    };
    while (C.groups.length < G) C.groups.push(c(`--cat-${C.groups.length + 1}`));
    const cs = getComputedStyle(document.documentElement);
    F = { mono: cs.getPropertyValue("--mono").trim() || "monospace", sans: cs.getPropertyValue("--sans").trim() || "sans-serif" };
    dark = luminance(C.surface) < 0.4;
  }

  const rampColour = (t) => {
    const [a, b] = RAMP_RANGE[dark ? "dark" : "light"];
    return cividis(a + (b - a) * t);
  };

  function columnScale(j) {
    const log = LOG_COLUMNS.has(names[j]);
    const f = log ? Math.log10 : (v) => v;
    const lo = f(pct(j, "2"));
    const hi = f(pct(j, "98"));
    return { log, lo, hi, t: (v) => Math.min(1, Math.max(0, (f(v) - lo) / (hi - lo))) };
  }

  // Every star gets one style per view; styles are drawn in "order", faint ones first.
  function buildStyles() {
    styles = [];
    order = [];
    const add = (colour, alpha, scale = 1) => styles.push({ colour, alpha, scale }) - 1;
    if (S.view === "fit") {
      const none = add(C.context, 0.9);
      order.push(none);
      const base = [];
      for (let g = 0; g < G; g++) {
        base.push(styles.length);
        for (let l = 0; l < LEVELS; l++) add(C.groups[g], (l + 1) / LEVELS);
      }
      const bySize = [...Array(G).keys()].sort((a, b) => H.groups[b].size - H.groups[a].size);
      for (const g of bySize) for (let l = 0; l < LEVELS; l++) order.push(base[g] + l);
      for (let i = 0; i < n; i++) {
        const g = group[i];
        styleOf[i] = g < 0 ? none : base[g] + Math.min(LEVELS - 1, Math.floor(own[i] * LEVELS));
      }
    } else if (S.view === "refit") {
      const out = add(C.context, 0.32, 0.8);
      const none = add(C.context, 0.95);
      const matched = C.groups.map((c) => add(c, 0.92));
      const extra = add(C.extra, 0.95);
      const bySize = [...Array(G).keys()].sort((a, b) => H.groups[b].size - H.groups[a].size);
      order.push(out, none, ...bySize.map((g) => matched[g]), extra);
      for (let i = 0; i < n; i++) {
        const o = outcome(S.refit, i);
        styleOf[i] = o === -3 ? out : o === -1 ? none : o === G ? extra : matched[o];
      }
    } else {
      const sc = columnScale(S.colJ);
      for (let s = 0; s < RAMP_STEPS; s++) order.push(add(rampColour(s / (RAMP_STEPS - 1)), 0.9));
      for (let i = 0; i < n; i++) styleOf[i] = Math.round(sc.t(value(i, S.colJ)) * (RAMP_STEPS - 1));
    }
    buildBuckets();
  }

  // Star indices per style, split into selected and the rest when a selection exists.
  function buildBuckets() {
    const m = styles.length;
    const make = (want) => {
      const count = new Int32Array(m);
      for (let i = 0; i < n; i++) if (want(i)) count[styleOf[i]]++;
      const lists = Array.from({ length: m }, (_, s) => new Int32Array(count[s]));
      const fill = new Int32Array(m);
      for (let i = 0; i < n; i++) if (want(i)) lists[styleOf[i]][fill[styleOf[i]]++] = i;
      return lists;
    };
    buckets = S.selCount ? { dim: make((i) => !S.sel[i]), main: make((i) => S.sel[i]) } : { dim: null, main: make(() => true) };
  }

  // ------------------------------------------------------------ panels
  function makePanel(name, sel) {
    const fig = $(sel);
    const canvas = fig.querySelector("canvas");
    const base = document.createElement("canvas");
    const prev = document.createElement("canvas");
    return { name, fig, canvas, tip: fig.querySelector(".sfd-tip"), surf: surface(canvas), base, prev,
      xy: new Float32Array(2 * n), grid: new Map(), frame: null, dirty: true, outside: 0 };
  }
  const P = {
    map: makePanel("map", ".sfd-map"),
    chem: makePanel("chem", ".sfd-chem"),
    orbit: makePanel("orbit", ".sfd-orbit"),
  };
  const panels = Object.values(P);

  // Axis of one column: limits from the 0.1th and 99.9th percentiles, padded; log for actions.
  function axisFor(j, log, scale = 1) {
    const f = log ? Math.log10 : (v) => v / scale;
    let lo = f(pct(j, "0.1"));
    let hi = f(pct(j, "99.9"));
    if (log) {
      lo = Math.floor(lo * 2) / 2;
      hi = Math.ceil(hi * 2) / 2;
    } else {
      const pad = (hi - lo) * 0.06;
      lo -= pad;
      hi += pad;
    }
    const ticks = log ? ticksFor(lo, hi, 6).filter((v) => Number.isInteger(v)) : ticksFor(lo, hi, 5);
    return { j, log, scale, lo, hi, ticks, f };
  }

  function panelAxes(p) {
    if (p.name === "chem") return [axisFor(J.fe_h, false), axisFor(S.chemY, false)];
    if (S.orbit === "el") return [axisFor(J.L_z, false), axisFor(J.E, false, 1000)];
    return [axisFor(J.J_R, true), axisFor(J.J_z, true)];
  }

  function layoutPanel(p) {
    const s = p.surf;
    p.grid = new Map();
    p.outside = 0;
    if (p.name === "map") {
      const pad = 10;
      let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
      for (let i = 0; i < n; i++) {
        const x = A.map[2 * i];
        const y = A.map[2 * i + 1];
        if (x < x0) x0 = x;
        if (x > x1) x1 = x;
        if (y < y0) y0 = y;
        if (y > y1) y1 = y;
      }
      const k = Math.min((s.w - 2 * pad) / (x1 - x0), (s.h - 2 * pad - 14) / (y1 - y0));
      const ox = (s.w - k * (x1 - x0)) / 2;
      const oy = (s.h - 14 - k * (y1 - y0)) / 2;
      for (let i = 0; i < n; i++) {
        p.xy[2 * i] = ox + (A.map[2 * i] - x0) * k;
        p.xy[2 * i + 1] = s.h - 14 - oy - (A.map[2 * i + 1] - y0) * k;
      }
      p.frame = { l: 0, t: 0, r: s.w, b: s.h };
      p.radius = Math.min(2.1, Math.max(1.2, s.w / 210));
    } else {
      const [ax, ay] = panelAxes(p);
      const m = { l: 50, r: 10, t: 10, b: 36 };
      const fr = { l: m.l, t: m.t, r: s.w - m.r, b: s.h - m.b };
      p.frame = fr;
      p.axes = [ax, ay];
      const sx = (v) => fr.l + ((v - ax.lo) / (ax.hi - ax.lo)) * (fr.r - fr.l);
      const sy = (v) => fr.b - ((v - ay.lo) / (ay.hi - ay.lo)) * (fr.b - fr.t);
      p.sx = sx;
      p.sy = sy;
      for (let i = 0; i < n; i++) {
        const vx = ax.f(value(i, ax.j));
        const vy = ay.f(value(i, ay.j));
        if (vx < ax.lo || vx > ax.hi || vy < ay.lo || vy > ay.hi || !Number.isFinite(vx) || !Number.isFinite(vy)) {
          p.xy[2 * i] = p.xy[2 * i + 1] = NaN;
          p.outside++;
        } else {
          p.xy[2 * i] = sx(vx);
          p.xy[2 * i + 1] = sy(vy);
        }
      }
      p.radius = Math.min(1.9, Math.max(1.1, (fr.r - fr.l) / 190));
    }
    for (let i = 0; i < n; i++) {
      const x = p.xy[2 * i];
      if (x !== x) continue;
      const key = Math.floor(x / CELL) + 4096 * Math.floor(p.xy[2 * i + 1] / CELL);
      let list = p.grid.get(key);
      if (!list) p.grid.set(key, (list = []));
      list.push(i);
    }
    p.dirty = true;
  }

  function pick(p, x, y, radius) {
    const cx = Math.floor(x / CELL);
    const cy = Math.floor(y / CELL);
    let best = -1;
    let bd = radius * radius;
    for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) {
      const list = p.grid.get(cx + dx + 4096 * (cy + dy));
      if (!list) continue;
      for (const i of list) {
        const dd = (p.xy[2 * i] - x) ** 2 + (p.xy[2 * i + 1] - y) ** 2;
        if (dd < bd) { bd = dd; best = i; }
      }
    }
    return best;
  }

  // ------------------------------------------------------------ drawing
  function drawParts(ctx, parts, x, y, align, size, colour) {
    const font = (st) => (st === "i" ? `italic 500 ${size}px ${F.sans}` : st === "s" ? `500 ${Math.round(size * 0.78)}px ${F.mono}` : `500 ${size}px ${F.mono}`);
    let w = 0;
    for (const [t, st] of parts) { ctx.font = font(st); w += ctx.measureText(t).width + (st === "i" ? 1 : 0); }
    let cx = align === "center" ? x - w / 2 : align === "right" ? x - w : x;
    ctx.textAlign = "left";
    ctx.fillStyle = colour;
    for (const [t, st] of parts) {
      ctx.font = font(st);
      ctx.fillText(t, cx, st === "s" ? y + size * 0.3 : y);
      cx += ctx.measureText(t).width + (st === "i" ? 1 : 0);
    }
    return w;
  }

  function axisTitle(j, scale) {
    const c = H.columns[j];
    const unit = c.unit === "km²/s²" && scale === 1000 ? "10³ km²/s²" : c.unit;
    return unit ? [...NAME[c.name], [` (${unit})`, ""]] : NAME[c.name];
  }

  function drawAxes(ctx, p) {
    const fr = p.frame;
    const [ax, ay] = p.axes;
    ctx.lineWidth = 1;
    ctx.font = `10.5px ${F.mono}`;
    const label = (a, v) => (a.log ? (10 ** v >= 1000 ? grouped(10 ** v) : String(Number((10 ** v).toPrecision(2)))) : a.j === J.L_z ? grouped(v) : tickText(v));
    ctx.textBaseline = "top";
    ctx.textAlign = "center";
    for (const v of ax.ticks) {
      const x = Math.round(p.sx(v)) + 0.5;
      ctx.strokeStyle = C.line;
      line(ctx, x, fr.t, x, fr.b);
      ctx.fillStyle = C.muted;
      const text = label(ax, v);
      const half = ctx.measureText(text).width / 2;
      ctx.fillText(text, Math.min(p.surf.w - half - 1, Math.max(half + 1, x)), fr.b + 5);
    }
    ctx.textBaseline = "middle";
    ctx.textAlign = "right";
    for (const v of ay.ticks) {
      const y = Math.round(p.sy(v)) + 0.5;
      ctx.strokeStyle = C.line;
      line(ctx, fr.l, y, fr.r, y);
      ctx.fillStyle = C.muted;
      ctx.fillText(label(ay, v), fr.l - 5, y);
    }
    ctx.strokeStyle = C.lineStrong;
    line(ctx, fr.l + 0.5, fr.t, fr.l + 0.5, fr.b + 0.5);
    line(ctx, fr.l, fr.b + 0.5, fr.r, fr.b + 0.5);
    ctx.textBaseline = "alphabetic";
    drawParts(ctx, axisTitle(ax.j, ax.scale), (fr.l + fr.r) / 2, p.surf.h - 4, "center", 10.5, C.ink2);
    ctx.save();
    ctx.translate(11, (fr.t + fr.b) / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textBaseline = "middle";
    drawParts(ctx, axisTitle(ay.j, ay.scale), 0, 0, "center", 10.5, C.ink2);
    ctx.restore();
  }

  function dots(ctx, p, list, r) {
    ctx.beginPath();
    for (let k = 0; k < list.length; k++) {
      const i = list[k];
      const x = p.xy[2 * i];
      if (x !== x) continue;
      const y = p.xy[2 * i + 1];
      ctx.moveTo(x + r, y);
      ctx.arc(x, y, r, 0, TAU);
    }
    ctx.fill();
  }

  function haloText(ctx, text, x, y, colour) {
    ctx.lineJoin = "round";
    ctx.lineWidth = 3.5;
    ctx.strokeStyle = C.surface;
    ctx.strokeText(text, x, y);
    ctx.fillStyle = colour;
    ctx.fillText(text, x, y);
  }

  // Direct labels on the map: each group named above its island.
  function mapLabels(ctx, p) {
    if (S.view === "col") return;
    const groups = [];
    for (let g = 0; g <= G; g++) groups.push([]);
    for (let i = 0; i < n; i++) {
      const o = S.view === "fit" ? group[i] : outcome(S.refit, i);
      if (o >= 0) groups[o].push(i);
    }
    ctx.font = `600 11px ${F.sans}`;
    ctx.textBaseline = "alphabetic";
    groups.forEach((list, g) => {
      if (list.length < 20) return;
      const xs = Float32Array.from(list, (i) => p.xy[2 * i]).sort();
      const ys = Float32Array.from(list, (i) => p.xy[2 * i + 1]).sort();
      const x = xs[xs.length >> 1];
      let y = ys[Math.floor(ys.length * 0.03)] - 9;
      const text = g === G ? `no counterpart, ${grouped(list.length)}` : `group ${g}`;
      const w = ctx.measureText(text).width + 12;
      if (y < 14) y = ys[Math.floor(ys.length * 0.97)] + 18;
      const lx = Math.max(4, Math.min(p.surf.w - w - 4, x - w / 2));
      ctx.globalAlpha = 1;
      ctx.fillStyle = C.surface;
      ctx.beginPath();
      ctx.arc(lx + 4, y - 4, 5.5, 0, TAU);
      ctx.fill();
      ctx.fillStyle = g === G ? C.extra : C.groups[g];
      ctx.beginPath();
      ctx.arc(lx + 4, y - 4, 3.5, 0, TAU);
      ctx.fill();
      ctx.textAlign = "left";
      haloText(ctx, text, lx + 12, y, C.ink);
    });
  }

  // Group medians over the refits (from the run), as rings in the physical panels.
  function medianMarks(ctx, p) {
    const [ax, ay] = p.axes;
    H.groups.forEach((g, k) => {
      const x = p.sx(ax.f(g.median[ax.j]));
      const y = p.sy(ay.f(g.median[ay.j]));
      if (!Number.isFinite(x) || !Number.isFinite(y)) return;
      ctx.globalAlpha = 1;
      ctx.fillStyle = C.surface;
      ctx.beginPath();
      ctx.arc(x, y, 7, 0, TAU);
      ctx.fill();
      ctx.fillStyle = C.groups[k];
      ctx.beginPath();
      ctx.arc(x, y, 5, 0, TAU);
      ctx.fill();
      ctx.strokeStyle = C.ink;
      ctx.lineWidth = 1.5;
      ctx.stroke();
    });
  }

  function drawBase(p) {
    const s = p.surf;
    for (const c of [p.base, p.prev]) {
      if (c.width !== s.canvas.width || c.height !== s.canvas.height) {
        c.width = s.canvas.width;
        c.height = s.canvas.height;
      }
    }
    const ctx = p.base.getContext("2d");
    ctx.setTransform(s.dpr, 0, 0, s.dpr, 0, 0);
    ctx.clearRect(0, 0, s.w, s.h);
    ctx.globalAlpha = 1;
    if (p.name !== "map") drawAxes(ctx, p);
    else {
      // Orientation only: the map's axes carry no units, so it gets no ticks.
      const x0 = 6.5;
      const y0 = s.h - 6.5;
      ctx.strokeStyle = C.lineStrong;
      ctx.lineWidth = 1;
      line(ctx, x0, y0, x0 + 22, y0);
      line(ctx, x0, y0, x0, y0 - 22);
      ctx.font = `500 10px ${F.mono}`;
      ctx.fillStyle = C.muted;
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      ctx.fillText("UMAP 1", x0 + 27, y0);
      ctx.save();
      ctx.translate(x0, y0 - 27);
      ctx.rotate(-Math.PI / 2);
      ctx.fillText("UMAP 2", 0, 0);
      ctx.restore();
    }
    ctx.save();
    ctx.beginPath();
    const fr = p.frame;
    ctx.rect(fr.l + 1, fr.t - 2, fr.r - fr.l + 2, fr.b - fr.t + 2);
    ctx.clip();
    const r = p.radius;
    for (const [lists, weight] of [[buckets.dim, 0.14], [buckets.main, 1]]) {
      if (!lists) continue;
      for (const k of order) {
        const st = styles[k];
        if (!lists[k].length) continue;
        ctx.globalAlpha = st.alpha * weight;
        ctx.fillStyle = st.colour;
        dots(ctx, p, lists[k], r * st.scale);
      }
    }
    ctx.restore();
    ctx.globalAlpha = 1;
    if (p.name === "map") mapLabels(ctx, p);
    else medianMarks(ctx, p);
    if (p.outside) {
      // The note goes in whichever top corner of the plot holds fewer stars.
      ctx.font = `10px ${F.mono}`;
      const text = `${grouped(p.outside)} beyond the axes`;
      const w = ctx.measureText(text).width + 6;
      let left = 0;
      let right = 0;
      for (let i = 0; i < n; i++) {
        const y = p.xy[2 * i + 1];
        if (!(y < fr.t + 16)) continue;
        const x = p.xy[2 * i];
        if (x < fr.l + w) left++;
        else if (x > fr.r - w) right++;
      }
      ctx.fillStyle = C.muted;
      ctx.textBaseline = "top";
      ctx.textAlign = left <= right ? "left" : "right";
      haloText(ctx, text, left <= right ? fr.l + 5 : fr.r - 3, fr.t + 3, C.muted);
    }
    p.dirty = false;
  }

  function ring(ctx, p, i, colour, width) {
    const x = p.xy[2 * i];
    if (i < 0 || x !== x) return;
    const y = p.xy[2 * i + 1];
    const r = p.radius + 4;
    ctx.globalAlpha = 1;
    ctx.lineWidth = width + 2.5;
    ctx.strokeStyle = C.surface;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, TAU);
    ctx.stroke();
    ctx.lineWidth = width;
    ctx.strokeStyle = colour;
    ctx.stroke();
  }

  function compose(p, now) {
    const s = p.surf;
    const ctx = s.ctx;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, s.canvas.width, s.canvas.height);
    if (fade) {
      const t = Math.min(1, (now - fade.start) / FADE_MS);
      ctx.globalAlpha = 1 - t;
      ctx.drawImage(p.prev, 0, 0);
      ctx.globalAlpha = t;
      ctx.drawImage(p.base, 0, 0);
    } else {
      ctx.globalAlpha = 1;
      ctx.drawImage(p.base, 0, 0);
    }
    ctx.setTransform(s.dpr, 0, 0, s.dpr, 0, 0);
    ring(ctx, p, S.pinned, C.ink, 2);
    if (S.hover !== S.pinned) ring(ctx, p, S.hover, C.ink2, 1.5);
    if (drag && drag.active && drag.p === p) {
      const x = Math.min(drag.x0, drag.x1);
      const y = Math.min(drag.y0, drag.y1);
      ctx.globalAlpha = 0.12;
      ctx.fillStyle = C.accent;
      ctx.fillRect(x, y, Math.abs(drag.x1 - drag.x0), Math.abs(drag.y1 - drag.y0));
      ctx.globalAlpha = 1;
      ctx.lineWidth = 1;
      ctx.strokeStyle = C.accent;
      ctx.strokeRect(x + 0.5, y + 0.5, Math.abs(drag.x1 - drag.x0), Math.abs(drag.y1 - drag.y0));
    }
  }

  function schedule() {
    if (!raf) raf = requestAnimationFrame(frame);
  }

  function frame(now) {
    raf = 0;
    if (!C) return;
    for (const p of panels) if (p.surf.fit()) layoutPanel(p);
    if (drag && drag.pending) applyBrush();
    for (const p of panels) if (p.dirty) drawBase(p);
    for (const p of panels) compose(p, now);
    if (fade) {
      if (now - fade.start >= FADE_MS) fade = null;
      schedule();
    }
  }

  function redrawAll() {
    for (const p of panels) p.dirty = true;
    schedule();
  }

  // Start a cross-fade: keep what is on screen as the old frame, then draw the new one.
  function beginFade() {
    if (motion.matches) return;
    for (const p of panels) {
      const c = p.prev.getContext("2d");
      p.prev.width = p.base.width;
      p.prev.height = p.base.height;
      c.drawImage(p.base, 0, 0);
    }
    fade = { start: performance.now() };
  }

  // ------------------------------------------------------------ key and selection
  function swatch(colour, cls = "") {
    const i = document.createElement("i");
    if (cls) i.className = cls;
    i.style.background = colour;
    return i;
  }

  function keyRow(tag, colour, cls, text, count, keyId) {
    const el = document.createElement(tag);
    el.className = tag === "div" ? "sfd-key-row" : "";
    if (tag === "button") {
      el.type = "button";
      el.setAttribute("aria-pressed", String(S.selKey === keyId));
      el.addEventListener("click", () => selectKey(keyId));
    }
    const label = document.createElement("span");
    label.textContent = text;
    const num = document.createElement("span");
    num.className = "n";
    num.textContent = count;
    el.append(swatch(colour, cls), label, num);
    return el;
  }

  function renderKey() {
    const rows = [];
    if (S.view === "fit") {
      H.groups.forEach((g, k) => rows.push(keyRow("button", C.groups[k], "", `group ${k}, recurrence ${g.recurrence.toFixed(2)}`, grouped(g.size), `g${k}`)));
      rows.push(keyRow("button", C.context, "", "unassigned", grouped(H.unassigned), "g-1"));
      const note = document.createElement("p");
      note.className = "sfd-key-note";
      note.textContent = "A faint dot has low support for its own group.";
      rows.push(note);
    } else if (S.view === "refit") {
      const counts = new Map();
      for (let i = 0; i < n; i++) {
        const o = outcome(S.refit, i);
        counts.set(o, (counts.get(o) || 0) + 1);
      }
      for (let g = 0; g < G; g++) rows.push(keyRow("button", C.groups[g], "", `matched to group ${g}`, grouped(counts.get(g) || 0), `r${g}`));
      if (counts.get(G)) rows.push(keyRow("button", C.extra, "", "a group with no counterpart", grouped(counts.get(G)), `r${G}`));
      rows.push(keyRow("button", C.context, "", "unassigned in this refit", grouped(counts.get(-1) || 0), "r-1"));
      rows.push(keyRow("div", C.context, "faint", "not drawn by this refit", grouped(counts.get(-3) || 0), null));
    } else {
      const j = S.colJ;
      const sc = columnScale(j);
      const ramp = document.createElement("span");
      ramp.className = "sfd-ramp";
      ramp.style.background = `linear-gradient(90deg, ${Array.from({ length: 9 }, (_, k) => rampColour(k / 8)).join(", ")})`;
      const ends = document.createElement("span");
      ends.className = "sfd-ramp-ends";
      const fmt = FORMAT[names[j]];
      const a = document.createElement("span");
      a.textContent = fmt(pct(j, "2"));
      const b = document.createElement("span");
      b.textContent = `${fmt(pct(j, "98"))} ${H.columns[j].unit}`.trim();
      ends.append(a, b);
      const note = document.createElement("p");
      note.className = "sfd-key-note";
      note.textContent = `Clipped at the 2nd and 98th percentiles${sc.log ? ", on a log scale" : ""}.`;
      rows.push(ramp, ends, note);
    }
    ui.key.replaceChildren(...rows);
  }

  function setSelection(want, keyId) {
    let count = 0;
    for (let i = 0; i < n; i++) count += S.sel[i] = want(i) ? 1 : 0;
    S.selCount = count;
    S.selKey = count ? keyId : null;
    buildBuckets();
    updateSelectionText();
    renderKey();
    redrawAll();
  }

  function clearSelection() {
    if (!S.selCount) return;
    S.sel.fill(0);
    S.selCount = 0;
    S.selKey = null;
    buildBuckets();
    updateSelectionText();
    renderKey();
    redrawAll();
  }

  function selectKey(keyId) {
    if (S.selKey === keyId) return clearSelection();
    const kind = keyId[0];
    const g = Number(keyId.slice(1));
    if (kind === "g") setSelection((i) => group[i] === g || (g === -1 && group[i] < 0), keyId);
    else setSelection((i) => outcome(S.refit, i) === g, keyId);
  }

  // The selection summary takes the place of the instructions, so the panel keeps its height.
  function updateSelectionText() {
    ui.sel.hidden = !S.selCount;
    ui.state.hidden = Boolean(S.selCount);
    if (!S.selCount) return;
    const parts = new Array(G + 1).fill(0);
    for (let i = 0; i < n; i++) if (S.sel[i]) parts[group[i] < 0 ? G : group[i]]++;
    const bits = [];
    parts.slice(0, G).forEach((c, g) => { if (c) bits.push(`${grouped(c)} in group ${g}`); });
    if (parts[G]) bits.push(`${grouped(parts[G])} unassigned`);
    ui.selText.textContent = `${grouped(S.selCount)} selected: ${bits.join(", ")}.`;
  }
  ui.clear.addEventListener("click", clearSelection);

  function applyBrush() {
    const p = drag.p;
    drag.pending = false;
    const x0 = Math.min(drag.x0, drag.x1);
    const x1 = Math.max(drag.x0, drag.x1);
    const y0 = Math.min(drag.y0, drag.y1);
    const y1 = Math.max(drag.y0, drag.y1);
    let count = 0;
    for (let i = 0; i < n; i++) {
      const x = p.xy[2 * i];
      const y = p.xy[2 * i + 1];
      const inside = x >= x0 && x <= x1 && y >= y0 && y <= y1 ? 1 : 0;
      S.sel[i] = inside;
      count += inside;
    }
    S.selCount = count;
    S.selKey = null;
    buildBuckets();
    updateSelectionText();
    for (const q of panels) q.dirty = true;
  }

  // ------------------------------------------------------------ views
  function setView(view, opts = {}) {
    const changed = view !== S.view || (view === "col" && opts.colJ !== undefined && opts.colJ !== S.colJ) || (view === "refit" && opts.refit !== undefined && opts.refit !== S.refit);
    if (opts.fade && changed && S.view === "refit" && view === "refit") beginFade();
    if (view === "refit" && opts.refit !== undefined && opts.refit !== S.refit && S.selKey && S.selKey[0] === "r") S.selKey = null;
    S.view = view;
    if (opts.colJ !== undefined) S.colJ = opts.colJ;
    if (opts.refit !== undefined) S.refit = opts.refit;
    if (view !== "refit") stopReplay();
    if (S.selKey && S.selKey[0] === "r" && view !== "refit") clearSelection();
    ui.colour.value = view === "col" ? `col:${S.colJ}` : view;
    buildStyles();
    renderKey();
    updateRefitUi();
    showStar(S.hover >= 0 ? S.hover : S.pinned);
    redrawAll();
  }

  ui.colour.addEventListener("change", () => {
    const v = ui.colour.value;
    if (v.startsWith("col:")) setView("col", { colJ: Number(v.slice(4)) });
    else setView(v);
  });

  for (const b of $(".sfd-chem .sfd-seg").querySelectorAll("button")) {
    b.addEventListener("click", () => {
      S.chemY = Number(b.dataset.y);
      for (const o of b.parentElement.children) o.setAttribute("aria-pressed", String(o === b));
      ui.chemY.textContent = H.columns[S.chemY].label;
      layoutPanel(P.chem);
      schedule();
    });
  }
  for (const b of $(".sfd-orbit .sfd-seg").querySelectorAll("button")) {
    b.addEventListener("click", () => {
      S.orbit = b.dataset.orbit;
      for (const o of b.parentElement.children) o.setAttribute("aria-pressed", String(o === b));
      if (S.orbit === "el") {
        ui.orbitPlain.textContent = "How bound each orbit is, against how much it turns with the disc.";
        ui.orbitExact.replaceChildren(partsNode(NAME.E), " and ", partsNode(NAME.L_z), " from galpy orbits in the McMillan17 potential; rings mark the group medians.");
      } else {
        ui.orbitPlain.textContent = "How far each orbit swings up and down, against in and out.";
        ui.orbitExact.replaceChildren("The actions ", partsNode(NAME.J_z), " and ", partsNode(NAME.J_R), " from galpy on log axes; rings mark the group medians.");
      }
      P.orbit.canvas.setAttribute("aria-label", S.orbit === "el"
        ? "Orbital energy against angular momentum for every star, coloured as the map"
        : "Vertical action against radial action for every star on log axes, coloured as the map");
      layoutPanel(P.orbit);
      schedule();
    });
  }

  // ------------------------------------------------------------ refits
  const stripButtons = H.refits.agreement.map((a, k) => {
    const b = document.createElement("button");
    b.type = "button";
    b.tabIndex = k === 0 ? 0 : -1;
    const extra = H.refits.matches[k].match.some((m) => m < 0);
    if (extra) b.classList.add("has-extra");
    b.setAttribute("aria-label", `Refit ${k + 1}: ${H.refits.n_groups[k]} groups, agreement ${a.toFixed(2)}`);
    b.setAttribute("aria-pressed", "false");
    const bar = document.createElement("span");
    bar.style.height = `${Math.max(4, a * 100)}%`;
    b.append(bar);
    b.addEventListener("click", () => {
      stopReplay();
      setView("refit", { refit: k, fade: true });
    });
    b.addEventListener("keydown", (e) => {
      const step = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
      if (!step) return;
      e.preventDefault();
      const k2 = Math.min(W - 1, Math.max(0, k + step));
      stopReplay();
      setView("refit", { refit: k2, fade: true });
      stripButtons[k2].focus();
    });
    return b;
  });
  ui.strip.replaceChildren(...stripButtons);

  function updateRefitUi() {
    const on = S.view === "refit";
    stripButtons.forEach((b, k) => {
      b.setAttribute("aria-pressed", String(on && k === S.refit));
      b.tabIndex = k === (on ? S.refit : 0) ? 0 : -1;
    });
    ui.back.disabled = !on;
    if (!on) {
      ui.refitNow.textContent = "showing the fit on all stars";
      ui.refitText.textContent = `Each bar is a refit on a random ${Math.round(H.refits.fraction * 100)} percent of the stars, as tall as its agreement with the fit on all stars.`;
      return;
    }
    const m = H.refits.matches[S.refit];
    const k = H.refits.n_groups[S.refit];
    const extra = m.match.filter((g) => g < 0).length;
    ui.refitNow.textContent = `showing refit ${S.refit + 1} of ${W}`;
    ui.refitText.textContent = `Refit ${S.refit + 1} drew ${grouped(m.drawn)} stars and found ${k} groups${extra ? `, ${extra === 1 ? "one" : extra} with no counterpart` : ""}; agreement with the fit on all stars ${H.refits.agreement[S.refit].toFixed(2)}.`;
  }

  const stepMs = () => (motion.matches ? REFIT_MS_REDUCED : REFIT_MS);

  function stopReplay() {
    if (!S.playing) return;
    S.playing = false;
    clearTimeout(timer);
    ui.play.textContent = "Replay";
  }

  function tick() {
    if (!S.playing) return;
    if (S.refit >= W - 1) return stopReplay();
    setView("refit", { refit: S.refit + 1, fade: true });
    timer = setTimeout(tick, stepMs());
  }

  ui.play.addEventListener("click", () => {
    if (S.playing) return stopReplay();
    const startAt = S.view === "refit" && S.refit < W - 1 ? S.refit : 0;
    setView("refit", { refit: startAt, fade: true });
    S.playing = true;
    ui.play.textContent = "Pause";
    timer = setTimeout(tick, stepMs());
  });
  ui.prev.addEventListener("click", () => {
    stopReplay();
    setView("refit", { refit: S.view === "refit" ? (S.refit + W - 1) % W : W - 1, fade: true });
  });
  ui.next.addEventListener("click", () => {
    stopReplay();
    setView("refit", { refit: S.view === "refit" ? (S.refit + 1) % W : 0, fade: true });
  });
  ui.back.addEventListener("click", () => setView("fit"));
  document.addEventListener("visibilitychange", () => { if (document.hidden) stopReplay(); });
  new IntersectionObserver(([e]) => { if (!e.isIntersecting) stopReplay(); }).observe($(".sfd-dash"));

  // ------------------------------------------------------------ the star panel
  const strongGroup = (i) => (group[i] >= 0 ? `group ${group[i]}` : "unassigned");

  function track(j, i) {
    const t = document.createElement("span");
    t.className = "sfd-track";
    const log = LOG_COLUMNS.has(names[j]);
    const f = log ? Math.log10 : (v) => v;
    const lo = f(pct(j, "1"));
    const hi = f(pct(j, "99"));
    const pos = (v) => ((f(v) - lo) / (hi - lo)) * 100;
    H.groups.forEach((g, k) => {
      const m = document.createElement("i");
      m.style.left = `${Math.min(100, Math.max(0, pos(g.median[j])))}%`;
      m.style.background = C.groups[k];
      t.append(m);
    });
    const v = pos(value(i, j));
    const dot = document.createElement("b");
    if (v < 0 || v > 100) dot.className = "is-clip";
    dot.style.left = `${Math.min(100, Math.max(0, v))}%`;
    t.append(dot);
    t.title = `Line: 1st to 99th percentile of all stars${log ? " on a log scale" : ""}; ticks: the group medians`;
    return t;
  }

  function showStar(i) {
    if (i < 0) return;
    const id = A.source_id[i].toString();
    const head = document.createElement("b");
    head.textContent = `Gaia DR3 ${id}`;
    const link = document.createElement("a");
    link.href = `https://vizier.cds.unistra.fr/viz-bin/VizieR-4?-source=I/355/gaiadr3&Source=${id}`;
    link.textContent = "VizieR";
    link.title = "This star in the Gaia DR3 catalogue at VizieR";
    const sup = [];
    for (let g = 0; g < G; g++) sup.push(A.support[i * G + g]);
    const drawn = A.n_sampled[i];
    const where = group[i] >= 0
      ? `group ${group[i]}, support ${own[i].toFixed(2)}`
      : `unassigned, support ${sup.map((s, g) => `${s.toFixed(2)} for group ${g}`).join(" and ")}`;
    ui.facts.replaceChildren(head, ` · ${where} · unresolved ${A.unresolved[i].toFixed(2)} · `, link);

    const tally = new Map();
    const cells = [];
    for (let k = 0; k < W; k++) {
      const o = outcome(k, i);
      tally.set(o, (tally.get(o) || 0) + 1);
      const c = document.createElement("i");
      if (o === -3) c.className = "is-out";
      else if (o === -1) c.className = "is-none";
      else c.style.setProperty("--c", o === G ? C.extra : C.groups[o]);
      if (S.view === "refit" && k === S.refit) c.classList.add("is-now");
      cells.push(c);
    }
    ui.cells.replaceChildren(...cells);
    const said = [];
    for (let g = 0; g < G; g++) if (tally.get(g)) said.push(`${tally.get(g)} put it with group ${g}`);
    if (tally.get(G)) said.push(`${tally.get(G)} in a group with no counterpart`);
    if (tally.get(-1)) said.push(`${tally.get(-1)} left it unassigned`);
    ui.history.textContent = `Of the ${drawn} refits that drew it, ${said.join(", ")}.`;

    const items = names.map((name, j) => {
      const wrap = document.createElement("div");
      const dt = document.createElement("dt");
      dt.append(partsNode(NAME[name]));
      const dd = document.createElement("dd");
      dd.append(FORMAT[name](value(i, j)));
      const unit = H.columns[j].unit;
      if (unit) {
        const sm = document.createElement("small");
        sm.textContent = ` ${unit}`;
        dd.append(sm);
      }
      wrap.append(dt, dd, track(j, i));
      return wrap;
    });
    ui.feats.replaceChildren(...items);
  }

  // Tooltip: the panel's own values first, then the star.
  function showTip(p, i) {
    if (i < 0 || p.xy[2 * i] !== p.xy[2 * i]) { p.tip.hidden = true; return; }
    const lines = [];
    const reading = (j) => [partsNode(NAME[names[j]]), ` ${FORMAT[names[j]](value(i, j))}`];
    if (p.name === "map") {
      if (S.view === "fit") lines.push([group[i] >= 0 ? `group ${group[i]}, support ${own[i].toFixed(2)}` : "unassigned"]);
      else if (S.view === "refit") {
        const o = outcome(S.refit, i);
        const what = o === -3 ? "not drawn" : o === -1 ? "unassigned" : o === G ? "in a group with no counterpart" : `with group ${o}`;
        lines.push([`refit ${S.refit + 1}: ${what}`]);
      } else lines.push([...reading(S.colJ), ` ${H.columns[S.colJ].unit}`]);
    } else {
      const [ax, ay] = p.axes;
      lines.push([...reading(ax.j), ", ", ...reading(ay.j)]);
    }
    lines.push([`Gaia DR3 ${A.source_id[i].toString()}`]);
    if (p.name !== "map" || S.view !== "fit") lines.push([strongGroup(i)]);
    p.tip.replaceChildren(...lines.map((bits, k) => {
      const el = document.createElement(k === 0 ? "b" : "span");
      el.append(...bits);
      return el;
    }));
    p.tip.hidden = false;
    const x = p.xy[2 * i];
    const y = p.xy[2 * i + 1];
    const w = p.tip.offsetWidth;
    const h = p.tip.offsetHeight;
    p.tip.style.left = `${Math.max(0, Math.min(x + 12, p.surf.w - w - 2))}px`;
    p.tip.style.top = `${y - h - 12 < 0 ? y + 14 : y - h - 12}px`;
  }

  function setHover(p, i) {
    for (const q of panels) if (q !== p || i < 0) q.tip.hidden = true;
    if (p) p.canvas.classList.toggle("is-pick", i >= 0);
    if (i === S.hover && p === S.hoverPanel) return;
    S.hover = i;
    S.hoverPanel = p;
    if (p && i >= 0) showTip(p, i);
    showStar(i >= 0 ? i : S.pinned);
    schedule();
  }

  function option(value, text) {
    const o = document.createElement("option");
    o.value = value;
    o.textContent = text;
    return o;
  }

  function syncPick(i) {
    const k = H.examples.findIndex((e) => e.row === i);
    let picked = ui.pick.querySelector('option[value="picked"]');
    if (k >= 0) {
      picked?.remove();
      ui.pick.value = String(k);
      return;
    }
    if (!picked) {
      picked = option("picked", "");
      ui.pick.insertBefore(picked, ui.pick.querySelector('option[value="random"]'));
    }
    picked.textContent = `Gaia DR3 ${A.source_id[i].toString()}`;
    ui.pick.value = "picked";
  }

  function pin(i) {
    S.pinned = i;
    syncPick(i);
    showStar(S.hover >= 0 ? S.hover : i);
    schedule();
  }

  ui.pick.replaceChildren(...H.examples.map((e, k) => option(String(k), e.label)), option("random", "Another star, at random"));
  ui.pick.addEventListener("change", () => {
    if (ui.pick.value === "picked") return;
    if (ui.pick.value === "random") {
      let r = S.pinned;
      while (r === S.pinned) r = Math.floor(Math.random() * n);
      pin(r);
    } else pin(H.examples[Number(ui.pick.value)].row);
  });
  ui.find.addEventListener("submit", (e) => {
    e.preventDefault();
    const digits = ui.findInput.value.replace(/\D/g, "");
    if (!digits) return;
    const want = BigInt(digits);
    const i = A.source_id.indexOf(want);
    if (i < 0) {
      ui.facts.textContent = `No star with Gaia DR3 source_id ${digits} among the ${grouped(n)}.`;
      return;
    }
    pin(i);
  });

  // ------------------------------------------------------------ pointer input
  const local = (p, e) => {
    const r = p.canvas.getBoundingClientRect();
    return [e.clientX - r.left, e.clientY - r.top];
  };
  for (const p of panels) {
    const c = p.canvas;
    c.addEventListener("pointerdown", (e) => {
      if (e.button !== 0 || e.pointerType === "touch") return;
      const [x, y] = local(p, e);
      drag = { p, x0: x, y0: y, x1: x, y1: y, active: false, pending: false };
      try {
        c.setPointerCapture(e.pointerId);
      } catch {
        // a pointer that is no longer active cannot be captured; the drag still works inside the panel
      }
    });
    c.addEventListener("pointermove", (e) => {
      const [x, y] = local(p, e);
      if (drag && drag.p === p) {
        drag.x1 = Math.max(0, Math.min(p.surf.w, x));
        drag.y1 = Math.max(0, Math.min(p.surf.h, y));
        if (!drag.active && Math.hypot(x - drag.x0, y - drag.y0) > BRUSH_PX) {
          drag.active = true;
          c.classList.add("is-brush");
          setHover(null, -1);
        }
        if (drag.active) {
          drag.pending = true;
          schedule();
          return;
        }
      }
      if (e.pointerType === "touch") return;
      setHover(p, pick(p, x, y, PICK_PX));
    });
    c.addEventListener("pointerup", (e) => {
      const [x, y] = local(p, e);
      if (e.pointerType === "touch") {
        const i = pick(p, x, y, TOUCH_PX);
        if (i >= 0) pin(i);
        setHover(i >= 0 ? p : null, i);
        return;
      }
      if (!drag || drag.p !== p) return;
      const brushed = drag.active;
      if (brushed && drag.pending) applyBrush();
      drag = null;
      c.classList.remove("is-brush");
      if (brushed) {
        if (!S.selCount) clearSelection();
        renderKey();
        redrawAll();
        return;
      }
      const i = pick(p, x, y, PICK_PX);
      if (i >= 0) pin(i);
      else clearSelection();
    });
    c.addEventListener("pointercancel", () => {
      drag = null;
      c.classList.remove("is-brush");
      schedule();
    });
    c.addEventListener("pointerleave", () => {
      if (!drag) setHover(null, -1);
    });
  }
  root.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      clearSelection();
      if (S.playing) stopReplay();
    }
  });

  // ------------------------------------------------------------ the calibration strip
  function drawCalibration() {
    const cal = H.calibration;
    const NS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(NS, "svg");
    const w = 240;
    const h = 34;
    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    svg.setAttribute("preserveAspectRatio", "xMinYMid meet");
    svg.setAttribute("role", "img");
    const top = Math.ceil(Math.max(cal.observed, ...cal.copy_values) * 20) / 20;
    const sx = (v) => 4 + (v / top) * (w - 8);
    const el = (name, attrs) => {
      const e = document.createElementNS(NS, name);
      for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
      svg.append(e);
      return e;
    };
    el("line", { class: "ax", x1: 4, x2: w - 4, y1: 22.5, y2: 22.5 });
    for (let v = 0; v <= top + 1e-9; v += 0.1) {
      const t = el("text", { x: sx(v), y: 33, "text-anchor": "middle" });
      t.textContent = Number(v.toFixed(1)).toString();
    }
    const placed = [];
    [...cal.copy_values].sort((a, b) => a - b).forEach((v) => {
      const x = sx(v);
      let level = 0;
      while (placed.some((q) => q.level === level && Math.abs(q.x - x) < 5.5)) level++;
      placed.push({ x, level });
      el("circle", { class: v >= cal.observed ? "copy is-up" : "copy", cx: x, cy: 19 - level * 5.5, r: 2.5 });
    });
    const ox = sx(cal.observed);
    el("line", { class: "obs", x1: ox, x2: ox, y1: 4, y2: 24 });
    const label = el("text", { class: "obs-t", x: ox - 4, y: 9, "text-anchor": "end" });
    label.textContent = `table ${cal.observed.toFixed(3)}`;
    const above = cal.copy_values.filter((v) => v >= cal.observed);
    svg.setAttribute("aria-label", `Calibration test: the table's statistic, ${cal.observed.toFixed(3)}, against ${cal.copies} structureless copies; ${above.length} scored at or above it.`);
    ui.calib.replaceChildren(svg);
  }

  // ------------------------------------------------------------ start
  readTheme();
  drawCalibration();
  buildStyles();
  renderKey();
  updateRefitUi();
  syncPick(S.pinned);
  showStar(S.pinned);
  for (const el of [ui.colour, ui.pick, ui.findInput, ui.findButton, ui.play, ui.prev, ui.next]) el.disabled = false;
  ui.state.textContent = coarse.matches
    ? "Tap a star to read it in the star panel."
    : "Hover over a star to read it, click to keep it, drag to select stars.";
  root.classList.add("is-ready");
  const resize = new ResizeObserver(() => schedule());
  for (const p of panels) resize.observe(p.canvas);
  motion.addEventListener("change", () => { fade = null; redrawAll(); });
  T.onThemeChange(() => {
    readTheme();
    buildStyles();
    renderKey();
    showStar(S.hover >= 0 ? S.hover : S.pinned);
    redrawAll();
  });
  document.fonts?.ready.then(() => redrawAll());
  schedule();
}
