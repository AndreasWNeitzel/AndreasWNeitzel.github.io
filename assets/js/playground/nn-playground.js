// Neural-network playground on Gaia XP spectra: controls, canvas drawing and the bridge
// to nn-worker.js, which does all of the maths. Canvas colours come from the site tokens
// (window.siteTokens) and are read again whenever the theme changes. The data load when
// the playground nears the viewport; nothing trains until the visitor presses Train.
import { loadDataset } from "./xp-data.js";

const MINUS = "−";
const EDGE_BUDGET = 400;
const DOTS_PER_LAYER = 14;
const PULSE_MS = 2600;
const FRAME_MS = 33;
const motion = matchMedia("(prefers-reduced-motion: reduce)");

const root = document.getElementById("nn-playground");
if (root) {
  const start = () => boot(root).catch((err) => {
    console.error(err);
    const status = root.querySelector(".pg-status");
    status.hidden = false;
    status.textContent = "The star data could not be loaded, so the playground cannot run here.";
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
const grouped = (v) => Math.round(v).toLocaleString("en-GB");
const axisNumber = (v) => (v < 0 ? MINUS : "") + String(Number(Math.abs(v).toPrecision(3)));

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

const toLinear = (c) => ((c /= 255) <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
const toByte = (c) => Math.round(255 * Math.min(1, Math.max(0, c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055)));

function oklab([r, g, b]) {
  const [lr, lg, lb] = [toLinear(r), toLinear(g), toLinear(b)];
  const l = Math.cbrt(0.4122214708 * lr + 0.5363325363 * lg + 0.0514459929 * lb);
  const m = Math.cbrt(0.2119034982 * lr + 0.6806995451 * lg + 0.1073969566 * lb);
  const s = Math.cbrt(0.0883024619 * lr + 0.2817188376 * lg + 0.6299787005 * lb);
  return [
    0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s,
    1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s,
    0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s,
  ];
}

function fromOklab([L, a, b]) {
  const l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3;
  const m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3;
  const s = (L - 0.0894841775 * a - 1.291485548 * b) ** 3;
  return [
    toByte(4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s),
    toByte(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s),
    toByte(-0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s),
  ];
}

// Interpolate between two token colours in OKLab, as the CSS legend gradient does.
function ramp(from, to) {
  const a = oklab(rgbOf(from));
  const b = oklab(rgbOf(to));
  return (t) => {
    const [r, g, bl] = fromOklab(a.map((v, i) => v + (b[i] - v) * t));
    return `rgb(${r} ${g} ${bl})`;
  };
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
  s.begin = () => {
    s.ctx.setTransform(s.dpr, 0, 0, s.dpr, 0, 0);
    s.ctx.clearRect(0, 0, s.w, s.h);
    s.ctx.globalAlpha = 1;
    return s.ctx;
  };
  return s;
}

function line(ctx, x0, y0, x1, y1) {
  ctx.beginPath();
  ctx.moveTo(x0, y0);
  ctx.lineTo(x1, y1);
  ctx.stroke();
}

function dot(ctx, x, y, r) {
  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.fill();
}

function logTicks(l0, l1) {
  const out = [];
  for (const steps of [[1], [1, 2, 5], [1, 2, 3, 4, 5, 6, 7, 8, 9]]) {
    out.length = 0;
    for (let e = Math.floor(l0); e <= Math.ceil(l1); e++) {
      for (const s of steps) {
        const v = s * 10 ** e;
        const lv = Math.log10(v);
        if (lv >= l0 && lv <= l1) out.push(v);
      }
    }
    if (out.length >= 3) break;
  }
  return out;
}

const niceEpochs = (e) => [10, 20, 50, 100, 200, 500, 1000, 2000].find((v) => v >= e) ?? e;

// Lines per weight layer: every weight into the output, then the rest of EDGE_BUDGET shared
// out from the smallest layer up, so a layer smaller than its share is drawn in full.
function edgeBudgets(counts) {
  const L = counts.length;
  const out = new Array(L).fill(0);
  out[L - 1] = counts[L - 1];
  let left = Math.max(0, EDGE_BUDGET - out[L - 1]);
  const order = [...Array(L - 1).keys()].sort((a, b) => counts[a] - counts[b]);
  order.forEach((l, i) => {
    out[l] = Math.min(counts[l], Math.floor(left / (order.length - i)));
    left -= out[l];
  });
  return out;
}

// ---------------------------------------------------------------- the playground
async function boot(root) {
  const $ = (sel) => root.querySelector(sel);
  const T = siteTokens();
  // ?autotrain=1 starts training on load; it exists for automated screenshots only.
  const autotrain = new URLSearchParams(location.search).get("autotrain") === "1";

  const ui = {
    status: $(".pg-status"),
    train: $(".pg-train"),
    step: $(".pg-step"),
    reset: $(".pg-reset"),
    readout: $(".pg-readout"),
    epoch: $(".pg-epoch"),
    rmse: $(".pg-rmse"),
    note: $(".pg-note"),
    form: $(".pg-settings"),
    stars: $(".pg-stars"),
    facts: $(".pg-facts"),
    estimate: $(".pg-estimate"),
    modes: [...root.querySelectorAll(".pg-mode")],
    rampTicks: $(".pg-ramp-ticks"),
    lossTip: $(".pg-loss .pg-tip"),
    parityTip: $(".pg-parity .pg-tip"),
    netCanvas: $(".pg-net canvas"),
    barsNote: $(".pg-bars-note"),
    specNote: $(".pg-spec-note"),
  };
  const cv = {
    net: surface(ui.netCanvas),
    loss: surface($(".pg-loss canvas")),
    parity: surface($(".pg-parity canvas")),
    bars: surface($(".pg-bars canvas")),
    spectrum: surface($(".pg-spectrum canvas")),
  };

  const { header, arrays: A } = await loadDataset(root.dataset.header);
  const K = header.k;
  const d = 2 * K;
  const n = header.n;
  const examples = header.examples.map((e) => e.row);
  const wave = Array.from({ length: header.wavelength_nm.count }, (_, i) => header.wavelength_nm.start + i * header.wavelength_nm.step);
  const exampleFlux = header.examples.map((e) => {
    const mean = e.flux.reduce((a, b) => a + b, 0) / e.flux.length;
    return e.flux.map((v) => v / mean);
  });

  // ------------------------------------------------------------ state
  let stats = null;
  let S = null;
  let history = [];
  let run = -1;
  let selected = examples[1];
  let barMode = "network";
  let edges = null;
  let layout = null;
  let C = null;
  let F = null;
  let teffColour = [];
  let hoverLoss = -1;
  let hoverParity = -1;
  let parityXY = null;
  let netVisible = true;
  let resumeOnShow = false;
  let autoStarted = false;
  let pulseStart = performance.now();
  let lastNetDraw = 0;
  let raf = 0;
  const dirty = { net: true, loss: true, parity: true, bars: true, spectrum: true };
  let valRows = null;
  let valIndex = null;
  let parityDomain = [-1, 1];
  let teffDomain = [4000, 6500];

  function readTheme() {
    const c = (name) => T.colour(name);
    C = {
      surface: c("--surface"), surface2: c("--surface-2"), line: c("--line"), lineStrong: c("--line-strong"),
      ink: c("--ink"), ink2: c("--ink-2"), muted: c("--muted"), accent: c("--accent"), accent2: c("--accent-2"),
    };
    const cs = getComputedStyle(document.documentElement);
    F = { mono: cs.getPropertyValue("--mono").trim() || "monospace", sans: cs.getPropertyValue("--sans").trim() || "sans-serif" };
    const mix = ramp(C.accent2, C.accent);
    if (valRows) {
      const [t0, t1] = teffDomain;
      teffColour = Array.from(valRows, (r) => mix(Math.min(1, Math.max(0, (A.teff_gspspec[r] - t0) / (t1 - t0)))));
    }
  }

  function markAll() {
    for (const key in dirty) dirty[key] = true;
    schedule();
  }

  // ------------------------------------------------------------ worker
  const worker = new Worker(root.dataset.worker);
  const send = (msg) => worker.postMessage(msg);
  worker.onerror = (e) => {
    e.preventDefault?.();
    ui.status.hidden = false;
    ui.status.textContent = "The training worker could not start in this browser.";
  };
  worker.onmessage = (event) => {
    const m = event.data;
    if (m.type === "ready") onReady(m);
    else if (m.type === "state") onState(m);
  };

  function settings() {
    const f = ui.form.elements;
    return {
      layers: Number(f.layers.value), units: Number(f.units.value), activation: f.activation.value,
      lr: Number(f.lr.value), batch: Number(f.batch.value), l2: Number(f.l2.value),
    };
  }

  send({ type: "init", features: A.features, y: A.mh_gspspec.slice(), split: A.split.slice(), d, hp: settings(), sample: selected });

  function onReady(m) {
    stats = m;
    valRows = m.valRows;
    valIndex = new Int32Array(n).fill(-1);
    valRows.forEach((r, i) => { valIndex[r] = i; });
    const mh = Array.from(valRows, (r) => A.mh_gspspec[r]);
    parityDomain = [Math.floor(Math.min(...mh) * 4) / 4, Math.ceil(Math.max(...mh) * 4) / 4];
    const teff = Array.from(valRows, (r) => A.teff_gspspec[r]).sort((a, b) => a - b);
    teffDomain = [Math.floor(teff[Math.floor(teff.length * 0.01)] / 250) * 250, Math.ceil(teff[Math.floor(teff.length * 0.99)] / 250) * 250];
    const ticks = [teffDomain[0], (teffDomain[0] + teffDomain[1]) / 2, teffDomain[1]];
    ui.rampTicks.replaceChildren(...ticks.map((t, i) => {
      const s = document.createElement("span");
      s.textContent = `${i === 0 ? "\u2264" : i === 2 ? "\u2265" : ""}${grouped(t)} K`;
      return s;
    }));
    readTheme();
    for (const b of [ui.train, ui.step, ui.reset]) b.disabled = false;
    ui.status.hidden = true;
    root.classList.add("is-ready");
    buildStars();
    markAll();
  }

  function onState(m) {
    if (m.run !== run) {
      run = m.run;
      history = [[0, m.train, m.val]];
      hoverLoss = -1;
    }
    for (const h of m.history) history.push(h);
    S = m;
    edges = null;
    updateReadout();
    updateEstimate();
    dirty.net = dirty.loss = dirty.parity = true;
    schedule();
    if (autotrain && !autoStarted && m.status === "idle") {
      autoStarted = true;
      send({ type: "train" });
    }
  }

  // ------------------------------------------------------------ controls
  function updateReadout() {
    const training = S.status === "training";
    ui.epoch.textContent = `Epoch ${grouped(S.epoch)}`;
    ui.rmse.textContent = Number.isFinite(S.val) ? `Validation RMSE ${Math.sqrt(S.val).toFixed(3)} dex` : "Validation RMSE not available";
    ui.readout.setAttribute("aria-busy", training ? "true" : "false");
    ui.train.textContent = training ? "Pause" : "Train";
    const stuck = S.status === "diverged" || S.status === "limit";
    ui.train.disabled = stuck;
    ui.step.disabled = stuck;
    ui.note.hidden = !stuck;
    if (S.status === "diverged") ui.note.textContent = "The error grew without bound, so training stopped. Lower the learning rate and press Reset.";
    else if (S.status === "limit") ui.note.textContent = `Training stops after ${grouped(stats.maxEpochs)} epochs. Press Reset to start again.`;
    const counts = S.weights.map((w) => w.length);
    const total = counts.reduce((a, b) => a + b, 0);
    const shown = edgeBudgets(counts).reduce((a, b) => a + b, 0);
    const hidden = S.sizes.slice(1, -1);
    const lines = shown === total ? `Lines show all ${grouped(total)} weights.` : `Lines show ${grouped(shown)} of its ${grouped(total)} weights, chosen by size.`;
    ui.netCanvas.setAttribute("aria-label", `Diagram of the network: ${d} inputs, ${hidden.length} hidden ${hidden.length === 1 ? "layer" : "layers"} of ${hidden[0]} units and one output. ${lines}`);
  }

  ui.train.addEventListener("click", () => send({ type: S && S.status === "training" ? "pause" : "train" }));
  ui.step.addEventListener("click", () => send({ type: "step" }));
  ui.reset.addEventListener("click", () => send({ type: "reset" }));
  ui.form.addEventListener("submit", (e) => e.preventDefault());
  ui.form.addEventListener("change", (e) => {
    const hp = settings();
    if (["layers", "units", "activation"].includes(e.target.name)) send({ type: "arch", layers: hp.layers, units: hp.units, activation: hp.activation });
    else send({ type: "config", lr: hp.lr, batch: hp.batch, l2: hp.l2 });
  });

  document.addEventListener("visibilitychange", () => {
    if (document.hidden && S && S.status === "training") {
      resumeOnShow = true;
      send({ type: "pause" });
    } else if (!document.hidden && resumeOnShow) {
      resumeOnShow = false;
      send({ type: "train" });
    }
  });

  // ------------------------------------------------------------ star selection
  function buildStars() {
    const buttons = examples.map((row) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "pg-chip";
      b.dataset.row = String(row);
      b.textContent = `Giant, [M/H] ${signed(A.mh_gspspec[row])}`;
      return b;
    });
    const other = document.createElement("button");
    other.type = "button";
    other.className = "pg-chip";
    other.dataset.row = "other";
    other.textContent = "Another validation star";
    ui.stars.replaceChildren(...buttons, other);
    ui.stars.addEventListener("click", (e) => {
      const b = e.target.closest("button");
      if (!b) return;
      if (b.dataset.row === "other") {
        let r = selected;
        while (r === selected || examples.includes(r)) r = valRows[Math.floor(Math.random() * valRows.length)];
        select(r);
      } else select(Number(b.dataset.row));
    });
    select(selected);
  }

  function select(row) {
    selected = row;
    send({ type: "sample", row });
    for (const b of ui.stars.querySelectorAll("button")) {
      const on = b.dataset.row === String(row) || (b.dataset.row === "other" && !examples.includes(row));
      b.setAttribute("aria-pressed", on ? "true" : "false");
    }
    const sid = A.source_id[row].toString();
    ui.facts.textContent = `Gaia DR3 ${sid} · Teff ${grouped(A.teff_gspspec[row])} K · log g ${A.logg_gspspec[row].toFixed(2)} · G ${A.phot_g_mean_mag[row].toFixed(1)} mag`;
    ui.specNote.hidden = examples.includes(row);
    updateEstimate();
    dirty.bars = dirty.spectrum = dirty.parity = dirty.net = true;
    schedule();
  }

  function updateEstimate() {
    const label = `GSP-Spec [M/H] ${signed(A.mh_gspspec[selected])} dex`;
    const est = S && S.sample.row === selected ? `network ${signed(S.sample.prediction)} dex` : "network estimate pending";
    ui.estimate.textContent = `${label} · ${est}`;
  }

  for (const b of ui.modes) {
    b.addEventListener("click", () => {
      barMode = b.dataset.mode;
      for (const o of ui.modes) o.setAttribute("aria-pressed", o === b ? "true" : "false");
      ui.barsNote.textContent = barMode === "network"
        ? "Each coefficient divided by the star's brightness, then rescaled so that 0 is the training average and 1 its spread."
        : "Each coefficient divided by the star's brightness, on a scale that expands small values.";
      dirty.bars = true;
      schedule();
    });
  }

  // ------------------------------------------------------------ network drawing
  function netLayout() {
    const s = cv.net;
    const sizes = S.sizes;
    const key = `${s.w}x${s.h}:${sizes.join(",")}`;
    if (layout && layout.key === key) return layout;
    const small = s.w < 520;
    const top = 18;
    const bottom = s.h - 30;
    const span = bottom - top;
    const x0 = small ? 30 : 46;
    const ctx = s.ctx;
    ctx.font = `500 ${small ? 10 : 11}px ${F.mono}`;
    const labelW = Math.max(ctx.measureText("[M/H] estimate").width, ctx.measureText(`GSP-Spec ${MINUS}0.00`).width);
    const x1 = s.w - labelW - 9 - 12 - 8;
    const cols = sizes.length;
    const xs = Array.from({ length: cols }, (_, i) => x0 + ((x1 - x0) * i) / (cols - 1));
    const gap = 16;
    const bandH = (span - gap) / 2;
    const ys = [new Float32Array(d)];
    for (let k = 0; k < K; k++) {
      ys[0][k] = top + (bandH * (k + 0.5)) / K;
      ys[0][K + k] = top + bandH + gap + (bandH * (k + 0.5)) / K;
    }
    const radius = [0];
    for (let c = 1; c < cols; c++) {
      const m = sizes[c];
      const step = m > 1 ? Math.min(30, span / (m - 1)) : 0;
      const y0 = top + (span - step * (m - 1)) / 2;
      ys.push(Float32Array.from({ length: m }, (_, j) => y0 + j * step));
      radius.push(c === cols - 1 ? 9 : Math.max(2.2, Math.min(8, step * 0.34)));
    }
    layout = { key, xs, ys, radius, top, bottom, bandH, gap, small };
    return layout;
  }

  // The largest weights of each layer, at most EDGE_BUDGET lines in all.
  function netEdges() {
    if (edges && edges.layout === layout) return edges;
    const { sizes, weights } = S;
    const L = weights.length;
    const budgets = edgeBudgets(weights.map((w) => w.length));
    const act = S.sample.layers;
    const layers = [];
    for (let l = 0; l < L; l++) {
      const w = weights[l];
      const nIn = sizes[l];
      const budget = budgets[l];
      let idx = Uint32Array.from({ length: w.length }, (_, i) => i);
      if (w.length > budget) idx = idx.sort((a, b) => Math.abs(w[b]) - Math.abs(w[a])).slice(0, budget);
      let max = 1e-12;
      for (const i of idx) max = Math.max(max, Math.abs(w[i]));
      const list = Array.from(idx, (i) => {
        const j = Math.floor(i / nIn);
        const k = i % nIn;
        const strength = Math.abs(w[i]) / max;
        return {
          x0: layout.xs[l], y0: layout.ys[l][k], x1: layout.xs[l + 1], y1: layout.ys[l + 1][j],
          positive: w[i] > 0, width: 0.45 + 2.1 * strength ** 0.85, alpha: 0.1 + 0.55 * strength,
          flow: w[i] * act[l][k],
        };
      }).sort((a, b) => a.alpha - b.alpha);
      let flowMax = 1e-12;
      for (const e of list) flowMax = Math.max(flowMax, Math.abs(e.flow));
      const dots = [...list].sort((a, b) => Math.abs(b.flow) - Math.abs(a.flow)).slice(0, DOTS_PER_LAYER)
        .map((e) => ({ ...e, strength: Math.abs(e.flow) / flowMax }));
      layers.push({ list, dots });
    }
    edges = { layout, layers };
    return edges;
  }

  function nodeIntensity(values, tanhLike) {
    let max = 1e-9;
    if (!tanhLike) for (const v of values) max = Math.max(max, Math.abs(v));
    return Array.from(values, (v) => Math.min(1, Math.abs(v) / (tanhLike ? 1 : max)));
  }

  function drawNet(now) {
    const s = cv.net;
    const ctx = s.begin();
    if (!S || s.w < 40) return;
    const L = netLayout();
    const E = netEdges();
    const act = S.sample.layers;
    const cols = L.xs.length;
    const animate = !motion.matches && netVisible;
    const phase = animate ? ((now - pulseStart) % PULSE_MS) / PULSE_MS : 1;
    const front = phase * (cols - 0.2);
    const glow = (c) => {
      if (!animate) return 1;
      const x = front - c;
      return x < 0 ? 0 : Math.exp(-x * 1.4);
    };
    ctx.lineCap = "round";
    for (const layer of E.layers) {
      for (const e of layer.list) {
        ctx.globalAlpha = e.alpha;
        ctx.lineWidth = e.width;
        ctx.strokeStyle = e.positive ? C.accent : C.accent2;
        line(ctx, e.x0, e.y0, e.x1, e.y1);
      }
    }
    // Activation flow for the selected star, one layer at a time.
    if (animate && S.sample.row === selected) {
      E.layers.forEach((layer, l) => {
        const u = front - l;
        if (u < 0 || u > 1) return;
        const ease = u * u * (3 - 2 * u);
        for (const e of layer.dots) {
          ctx.globalAlpha = (0.25 + 0.75 * e.strength) * Math.sin(Math.PI * u);
          ctx.fillStyle = e.flow > 0 ? C.accent : C.accent2;
          dot(ctx, e.x0 + (e.x1 - e.x0) * ease, e.y0 + (e.y1 - e.y0) * ease, 1.6 + 1.6 * e.strength);
        }
      });
    }
    // Input bands: one tick per coefficient, coloured by the star's standardised value.
    const bandX = L.xs[0];
    const bandW = L.small ? 8 : 10;
    const tickH = Math.max(1, Math.min(8, (L.bandH / K) * 0.6));
    for (let b = 0; b < 2; b++) {
      const y = L.top + b * (L.bandH + L.gap);
      ctx.globalAlpha = 1;
      ctx.fillStyle = C.surface2;
      ctx.strokeStyle = C.lineStrong;
      ctx.lineWidth = 1;
      ctx.beginPath();
      if (ctx.roundRect) ctx.roundRect(bandX - bandW / 2 - 2, y - 2, bandW + 4, L.bandH + 4, 4);
      else ctx.rect(bandX - bandW / 2 - 2, y - 2, bandW + 4, L.bandH + 4);
      ctx.fill();
      ctx.stroke();
    }
    const g0 = glow(0);
    for (let k = 0; k < d; k++) {
      const v = act[0][k];
      const i = Math.min(1, Math.abs(v) / 2.5);
      ctx.globalAlpha = 0.1 + 0.9 * i * (0.4 + 0.6 * g0);
      ctx.fillStyle = v >= 0 ? C.accent : C.accent2;
      ctx.fillRect(bandX - bandW / 2, L.ys[0][k] - tickH / 2, bandW, tickH);
    }
    // Hidden and output nodes.
    const tanhLike = S.hp.activation === "tanh";
    for (let c = 1; c < cols; c++) {
      const out = c === cols - 1;
      const vals = act[c];
      const inten = out ? [1] : nodeIntensity(vals, tanhLike);
      const g = glow(c);
      const r = L.radius[c];
      for (let j = 0; j < vals.length; j++) {
        const x = L.xs[c];
        const y = L.ys[c][j];
        ctx.globalAlpha = 1;
        ctx.fillStyle = C.surface;
        dot(ctx, x, y, r + 1.5);
        ctx.strokeStyle = out ? C.ink : C.lineStrong;
        ctx.lineWidth = out ? 1.5 : 1;
        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.stroke();
        ctx.globalAlpha = out ? 0.25 + 0.6 * g : 0.12 + 0.8 * inten[j] * (0.35 + 0.65 * g);
        ctx.fillStyle = out ? C.ink : vals[j] >= 0 ? C.accent : C.accent2;
        dot(ctx, x, y, out ? r - 3 : r - 0.5);
      }
    }
    // Labels.
    ctx.globalAlpha = 1;
    ctx.fillStyle = C.muted;
    ctx.font = `500 ${L.small ? 10 : 11}px ${F.mono}`;
    ctx.textBaseline = "middle";
    ctx.textAlign = "right";
    ctx.fillText("BP", bandX - bandW / 2 - 8, L.top + L.bandH / 2);
    ctx.fillText("RP", bandX - bandW / 2 - 8, L.top + L.bandH + L.gap + L.bandH / 2);
    ctx.textBaseline = "alphabetic";
    const y = cv.net.h - 10;
    const full = (c) => (c === 0 ? `${d} inputs` : c === cols - 1 ? "output" : `${S.sizes[c]} units`);
    const compact = (c) => (c === 0 ? `${d} in` : c === cols - 1 ? "out" : String(S.sizes[c]));
    const fits = (label) => {
      for (let c = 1; c < cols; c++) {
        const left = c === 1 ? bandX - bandW / 2 - 2 + ctx.measureText(label(0)).width : L.xs[c - 1] + ctx.measureText(label(c - 1)).width / 2;
        if (left + 8 > L.xs[c] - ctx.measureText(label(c)).width / 2) return false;
      }
      return true;
    };
    const label = fits(full) ? full : compact;
    for (let c = 0; c < cols; c++) {
      ctx.textAlign = c === 0 ? "left" : "center";
      ctx.fillText(label(c), c === 0 ? bandX - bandW / 2 - 2 : L.xs[c], y);
    }
    const ox = L.xs[cols - 1] + L.radius[cols - 1] + 12;
    const oy = L.ys[cols - 1][0];
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    ctx.fillStyle = C.muted;
    ctx.font = `500 ${L.small ? 10 : 11}px ${F.mono}`;
    ctx.fillText("[M/H] estimate", ox, oy - (L.small ? 15 : 18));
    ctx.fillStyle = C.ink;
    ctx.font = `600 ${L.small ? 14 : 17}px ${F.mono}`;
    ctx.fillText(S.sample.row === selected ? signed(S.sample.prediction) : "…", ox, oy);
    ctx.fillStyle = C.muted;
    ctx.font = `500 ${L.small ? 10 : 11}px ${F.mono}`;
    ctx.fillText(`GSP-Spec ${signed(A.mh_gspspec[selected])}`, ox, oy + (L.small ? 15 : 18));
  }

  // ------------------------------------------------------------ loss chart
  function lossFrame() {
    const s = cv.loss;
    const m = { l: 44, r: 14, t: 10, b: 24 };
    let lo = Infinity;
    let hi = 0;
    for (const p of history) for (const v of [p[1], p[2]]) if (v > 0 && Number.isFinite(v)) { lo = Math.min(lo, v); hi = Math.max(hi, v); }
    if (!Number.isFinite(lo)) { lo = 0.01; hi = 0.1; }
    let l0 = Math.log10(lo);
    let l1 = Math.log10(hi);
    if (l1 - l0 < 1) l0 = l1 - 1;
    const pad = (l1 - l0) * 0.06;
    l0 -= pad;
    l1 += pad;
    const xMax = niceEpochs(Math.max(10, history.length ? history[history.length - 1][0] : 0));
    const W = s.w - m.l - m.r;
    const H = s.h - m.t - m.b;
    return {
      m, W, H, l0, l1, xMax,
      X: (e) => m.l + (e / xMax) * W,
      Y: (v) => m.t + (1 - (Math.log10(v) - l0) / (l1 - l0)) * H,
    };
  }

  function drawLoss() {
    const s = cv.loss;
    const ctx = s.begin();
    if (s.w < 60 || !history.length) return;
    const f = lossFrame();
    ctx.font = `11px ${F.mono}`;
    ctx.lineWidth = 1;
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (const t of logTicks(f.l0, f.l1)) {
      const y = Math.round(f.Y(t)) + 0.5;
      ctx.strokeStyle = C.line;
      line(ctx, f.m.l, y, f.m.l + f.W, y);
      ctx.fillStyle = C.muted;
      ctx.fillText(axisNumber(t), f.m.l - 6, y);
    }
    ctx.strokeStyle = C.lineStrong;
    const base = f.m.t + f.H + 0.5;
    line(ctx, f.m.l, base, f.m.l + f.W, base);
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.fillStyle = C.muted;
    const xStep = f.xMax / (f.xMax % 4 === 0 ? 4 : 5);
    for (let e = 0; e <= f.xMax; e += xStep) {
      ctx.fillText(grouped(e), Math.min(f.X(e), f.m.l + f.W - 12), base + 6);
    }
    const series = [[1, C.ink2, 1.5], [2, C.accent, 2]];
    ctx.lineJoin = "round";
    ctx.lineCap = "round";
    for (const [col, colour, width] of series) {
      ctx.strokeStyle = colour;
      ctx.lineWidth = width;
      ctx.beginPath();
      let started = false;
      for (const p of history) {
        if (!(p[col] > 0) || !Number.isFinite(p[col])) continue;
        const x = f.X(p[0]);
        const y = f.Y(p[col]);
        if (started) ctx.lineTo(x, y);
        else { ctx.moveTo(x, y); started = true; }
      }
      ctx.stroke();
    }
    if (history.length === 1) {
      ctx.fillStyle = C.muted;
      ctx.font = `500 12px ${F.sans}`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("Press Train to start", f.m.l + f.W / 2, f.m.t + f.H / 2);
    }
    const lastP = history[history.length - 1];
    const marks = hoverLoss >= 0 ? history[hoverLoss] : lastP;
    if (hoverLoss >= 0) {
      ctx.strokeStyle = C.lineStrong;
      ctx.lineWidth = 1;
      const x = Math.round(f.X(marks[0])) + 0.5;
      line(ctx, x, f.m.t, x, f.m.t + f.H);
    }
    for (const [col, colour] of series) {
      if (!(marks[col] > 0)) continue;
      ctx.fillStyle = C.surface;
      dot(ctx, f.X(marks[0]), f.Y(marks[col]), 5);
      ctx.fillStyle = colour;
      dot(ctx, f.X(marks[0]), f.Y(marks[col]), 3.2);
    }
  }

  function lossHover(e) {
    if (!history.length) return;
    const rect = cv.loss.canvas.getBoundingClientRect();
    const f = lossFrame();
    const epoch = ((e.clientX - rect.left - f.m.l) / f.W) * f.xMax;
    let best = 0;
    let bd = Infinity;
    for (let i = 0; i < history.length; i++) {
      const dd = Math.abs(history[i][0] - epoch);
      if (dd < bd) { bd = dd; best = i; }
    }
    hoverLoss = best;
    const p = history[best];
    ui.lossTip.replaceChildren();
    const head = document.createElement("b");
    head.textContent = `Epoch ${grouped(p[0])}`;
    const a = document.createElement("span");
    a.textContent = `training ${p[1].toPrecision(3)} dex²`;
    const b = document.createElement("span");
    b.textContent = `validation ${p[2].toPrecision(3)} dex²`;
    ui.lossTip.append(head, a, b);
    ui.lossTip.hidden = false;
    const x = f.X(p[0]);
    const tipW = ui.lossTip.offsetWidth;
    ui.lossTip.style.left = `${Math.max(0, Math.min(x + 12, cv.loss.w - tipW - 4))}px`;
    ui.lossTip.style.top = `${f.m.t + 4}px`;
    dirty.loss = true;
    schedule();
  }

  cv.loss.canvas.addEventListener("pointermove", lossHover);
  cv.loss.canvas.addEventListener("pointerleave", () => {
    hoverLoss = -1;
    ui.lossTip.hidden = true;
    dirty.loss = true;
    schedule();
  });

  // ------------------------------------------------------------ parity plot
  function parityFrame() {
    const s = cv.parity;
    s.ctx.font = `11px ${F.mono}`;
    const [lo0, hi0] = parityDomain;
    const tick = (v) => s.ctx.measureText(axisNumber(v)).width;
    const m = { l: Math.ceil(Math.max(tick(lo0), tick(hi0))) + 28, r: Math.ceil(tick(hi0) / 2) + 6, t: 10, b: 40 };
    const size = Math.max(20, Math.min(s.w - m.l - m.r, s.h - m.t - m.b));
    const x0 = m.l + Math.max(0, (s.w - m.l - m.r - size) / 2);
    const y0 = m.t;
    const [lo, hi] = parityDomain;
    return {
      m, size, x0, y0, lo, hi,
      sx: (v) => x0 + ((v - lo) / (hi - lo)) * size,
      sy: (v) => y0 + size - ((Math.min(hi, Math.max(lo, v)) - lo) / (hi - lo)) * size,
    };
  }

  function drawParity() {
    const s = cv.parity;
    const ctx = s.begin();
    if (!S || !valRows || s.w < 60) return;
    const f = parityFrame();
    const step = f.size > 420 ? 0.25 : 0.5;
    ctx.font = `11px ${F.mono}`;
    ctx.lineWidth = 1;
    for (let v = Math.ceil(f.lo / step) * step; v <= f.hi + 1e-9; v += step) {
      const x = Math.round(f.sx(v)) + 0.5;
      const y = Math.round(f.sy(v)) + 0.5;
      ctx.strokeStyle = C.line;
      line(ctx, x, f.y0, x, f.y0 + f.size);
      line(ctx, f.x0, y, f.x0 + f.size, y);
      ctx.fillStyle = C.muted;
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      ctx.fillText(axisNumber(v), x, f.y0 + f.size + 6);
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";
      ctx.fillText(axisNumber(v), f.x0 - 6, y);
    }
    ctx.strokeStyle = C.lineStrong;
    line(ctx, f.x0 + 0.5, f.y0, f.x0 + 0.5, f.y0 + f.size + 0.5);
    line(ctx, f.x0, f.y0 + f.size + 0.5, f.x0 + f.size, f.y0 + f.size + 0.5);
    ctx.save();
    ctx.globalAlpha = 0.7;
    ctx.strokeStyle = C.ink2;
    line(ctx, f.sx(f.lo), f.sy(f.lo), f.sx(f.hi), f.sy(f.hi));
    ctx.restore();
    const preds = S.preds;
    const r = f.size > 320 ? 3 : 2.5;
    parityXY = new Float32Array(preds.length * 2);
    for (let i = 0; i < preds.length; i++) {
      const x = f.sx(A.mh_gspspec[valRows[i]]);
      const y = f.sy(preds[i]);
      parityXY[2 * i] = x;
      parityXY[2 * i + 1] = y;
      ctx.fillStyle = C.surface;
      dot(ctx, x, y, r + 1);
      ctx.fillStyle = teffColour[i];
      dot(ctx, x, y, r);
    }
    for (const [i, colour, width] of [[valIndex[selected], C.ink, 2], [hoverParity, C.ink2, 1.5]]) {
      if (i < 0) continue;
      ctx.strokeStyle = colour;
      ctx.lineWidth = width;
      ctx.beginPath();
      ctx.arc(parityXY[2 * i], parityXY[2 * i + 1], r + 4, 0, Math.PI * 2);
      ctx.stroke();
    }
    ctx.fillStyle = C.ink2;
    ctx.font = `500 11px ${F.mono}`;
    ctx.textAlign = "center";
    ctx.textBaseline = "alphabetic";
    ctx.fillText("GSP-Spec [M/H] (dex)", f.x0 + f.size / 2, s.h - 4);
    ctx.save();
    ctx.translate(11, f.y0 + f.size / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textBaseline = "middle";
    ctx.fillText("network [M/H] (dex)", 0, 0);
    ctx.restore();
  }

  function parityPick(e) {
    if (!parityXY) return -1;
    const rect = cv.parity.canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    let best = -1;
    let bd = 14 * 14;
    for (let i = 0; i < parityXY.length / 2; i++) {
      const dd = (parityXY[2 * i] - x) ** 2 + (parityXY[2 * i + 1] - y) ** 2;
      if (dd < bd) { bd = dd; best = i; }
    }
    return best;
  }

  cv.parity.canvas.addEventListener("pointermove", (e) => {
    const i = parityPick(e);
    if (i === hoverParity) return;
    hoverParity = i;
    cv.parity.canvas.style.cursor = i >= 0 ? "pointer" : "";
    if (i < 0) ui.parityTip.hidden = true;
    else {
      const r = valRows[i];
      ui.parityTip.replaceChildren();
      const head = document.createElement("b");
      head.textContent = `network ${signed(S.preds[i])}, GSP-Spec ${signed(A.mh_gspspec[r])}`;
      const a = document.createElement("span");
      a.textContent = `Teff ${grouped(A.teff_gspspec[r])} K, log g ${A.logg_gspspec[r].toFixed(2)}`;
      const b = document.createElement("span");
      b.textContent = `Gaia DR3 ${A.source_id[r].toString()}`;
      ui.parityTip.append(head, a, b);
      ui.parityTip.hidden = false;
      const x = parityXY[2 * i];
      const y = parityXY[2 * i + 1];
      const w = ui.parityTip.offsetWidth;
      const h = ui.parityTip.offsetHeight;
      ui.parityTip.style.left = `${Math.max(0, Math.min(x + 12, cv.parity.w - w - 2))}px`;
      ui.parityTip.style.top = `${y - h - 12 < 0 ? y + 14 : y - h - 12}px`;
    }
    dirty.parity = true;
    schedule();
  });
  cv.parity.canvas.addEventListener("pointerleave", () => {
    hoverParity = -1;
    ui.parityTip.hidden = true;
    dirty.parity = true;
    schedule();
  });
  cv.parity.canvas.addEventListener("click", (e) => {
    const i = parityPick(e);
    if (i >= 0) select(valRows[i]);
  });

  // ------------------------------------------------------------ input bars
  function drawBars() {
    const s = cv.bars;
    const ctx = s.begin();
    if (!stats || s.w < 60) return;
    const m = { l: 44, r: 6, t: 10, b: 24 };
    const W = s.w - m.l - m.r;
    const H = s.h - m.t - m.b;
    const row = selected;
    const vals = new Float32Array(d);
    for (let k = 0; k < d; k++) {
      const x = A.features[row * d + k];
      vals[k] = barMode === "network" ? (x - stats.mean[k]) / stats.std[k] : x;
    }
    let lim;
    let fy;
    let ticks;
    if (barMode === "network") {
      let big = 0;
      for (const v of vals) big = Math.max(big, Math.abs(v));
      lim = Math.min(8, Math.max(2, Math.ceil(big)));
      fy = (v) => Math.max(-1, Math.min(1, v / lim));
      ticks = [-lim, -lim / 2, 0, lim / 2, lim];
    } else {
      const c = 3e-4;
      const top = Math.asinh(0.7 / c);
      fy = (v) => Math.asinh(v / c) / top;
      ticks = [-0.01, -0.001, 0, 0.001, 0.01, 0.1];
    }
    const zero = m.t + H / 2;
    const Y = (v) => zero - fy(v) * (H / 2);
    ctx.font = `11px ${F.mono}`;
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    ctx.lineWidth = 1;
    for (const t of ticks) {
      const y = Math.round(Y(t)) + 0.5;
      ctx.strokeStyle = t === 0 ? C.lineStrong : C.line;
      line(ctx, m.l, y, m.l + W, y);
      ctx.fillStyle = C.muted;
      ctx.fillText(axisNumber(t), m.l - 6, y);
    }
    const groupGap = 14;
    const slot = (W - groupGap) / d;
    const bw = Math.max(1.5, Math.min(14, slot * 0.68));
    const nrel = [A.bp_n_relevant_bases[row], A.rp_n_relevant_bases[row]];
    for (let k = 0; k < d; k++) {
      const band = k < K ? 0 : 1;
      const idx = k % K;
      const x = m.l + k * slot + band * groupGap + (slot - bw) / 2;
      const v = vals[k];
      const y = Y(v);
      ctx.globalAlpha = idx < nrel[band] ? 1 : 0.3;
      ctx.fillStyle = barMode === "network" ? (v >= 0 ? C.accent : C.accent2) : C.ink2;
      ctx.fillRect(x, Math.min(y, zero), bw, Math.max(1, Math.abs(y - zero)));
    }
    ctx.globalAlpha = 1;
    ctx.fillStyle = C.ink2;
    ctx.textBaseline = "alphabetic";
    ctx.textAlign = "center";
    ctx.font = `500 11px ${F.mono}`;
    const long = ctx.measureText(`BP coefficients 0 to ${K - 1}`).width < K * slot - 12;
    const names = long ? ["BP coefficients", "RP coefficients"] : ["BP", "RP"];
    ctx.fillText(`${names[0]} 0 to ${K - 1}`, m.l + (K * slot) / 2, s.h - 6);
    ctx.fillText(`${names[1]} 0 to ${K - 1}`, m.l + K * slot + groupGap + (K * slot) / 2, s.h - 6);
  }

  // ------------------------------------------------------------ spectra
  function drawSpectrum() {
    const s = cv.spectrum;
    const ctx = s.begin();
    if (s.w < 60) return;
    ctx.font = `500 11px ${F.mono}`;
    const endLabel = (i) => `[M/H] ${signed(A.mh_gspspec[examples[i]])}`;
    const labelW = Math.max(...[0, 1, 2].map((i) => ctx.measureText(endLabel(i)).width));
    const m = { l: 36, r: labelW + 14, t: 10, b: 24 };
    const W = s.w - m.l - m.r;
    const H = s.h - m.t - m.b;
    const w0 = wave[0];
    const w1 = wave[wave.length - 1];
    let top = 0;
    for (const f of exampleFlux) for (const v of f) top = Math.max(top, v);
    top = Math.ceil(top * 4) / 4;
    const X = (w) => m.l + ((w - w0) / (w1 - w0)) * W;
    const Y = (v) => m.t + H - (v / top) * H;
    ctx.font = `11px ${F.mono}`;
    ctx.lineWidth = 1;
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (let v = 0; v <= top + 1e-9; v += 0.5) {
      const y = Math.round(Y(v)) + 0.5;
      ctx.strokeStyle = v === 0 ? C.lineStrong : C.line;
      line(ctx, m.l, y, m.l + W, y);
      ctx.fillStyle = C.muted;
      ctx.fillText(axisNumber(v), m.l - 6, y);
    }
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    for (const w of [400, 500, 600, 700, 800, 900, 1000]) {
      if (s.w < 420 && w % 200 !== 0) continue;
      ctx.fillText(String(w), X(w), m.t + H + 6);
    }
    const order = [0, 1, 2].sort((a, b) => (examples[a] === selected) - (examples[b] === selected));
    ctx.lineJoin = "round";
    const ends = [];
    for (const i of order) {
      const on = examples[i] === selected;
      ctx.strokeStyle = on ? C.ink : C.muted;
      ctx.globalAlpha = on ? 1 : 0.55;
      ctx.lineWidth = on ? 2 : 1.25;
      ctx.beginPath();
      exampleFlux[i].forEach((v, j) => (j ? ctx.lineTo(X(wave[j]), Y(v)) : ctx.moveTo(X(wave[j]), Y(v))));
      ctx.stroke();
      ends.push({ i, y: Y(exampleFlux[i][exampleFlux[i].length - 1]), on });
    }
    // End labels, spread apart so they never overlap; a short leader joins each to its curve.
    ends.sort((a, b) => a.y - b.y);
    const gapY = 13;
    const placed = ends.map((e) => e.y);
    for (let k = 1; k < placed.length; k++) placed[k] = Math.max(placed[k], placed[k - 1] + gapY);
    const overflow = placed[placed.length - 1] - (m.t + H);
    if (overflow > 0) for (let k = 0; k < placed.length; k++) placed[k] -= overflow;
    ctx.font = `500 11px ${F.mono}`;
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    ends.forEach((e, k) => {
      ctx.globalAlpha = e.on ? 1 : 0.8;
      ctx.strokeStyle = C.line;
      ctx.lineWidth = 1;
      line(ctx, m.l + W + 2, e.y, m.l + W + 8, placed[k]);
      ctx.fillStyle = e.on ? C.ink : C.muted;
      ctx.fillText(endLabel(e.i), m.l + W + 10, placed[k]);
    });
    ctx.globalAlpha = 1;
    ctx.fillStyle = C.muted;
    ctx.textAlign = "left";
    ctx.textBaseline = "top";
    ctx.fillText("nm", m.l + W + 10, m.t + H + 6);
  }

  // ------------------------------------------------------------ frame loop
  function schedule() {
    if (!raf) raf = requestAnimationFrame(frame);
  }

  function frame(now) {
    raf = 0;
    for (const s of Object.values(cv)) if (s.fit()) markAllSilently();
    if (!C) return;
    if (dirty.loss) { drawLoss(); dirty.loss = false; }
    if (dirty.parity) { drawParity(); dirty.parity = false; }
    if (dirty.bars) { drawBars(); dirty.bars = false; }
    if (dirty.spectrum) { drawSpectrum(); dirty.spectrum = false; }
    const animate = S && netVisible && !motion.matches && !document.hidden;
    if (dirty.net || (animate && now - lastNetDraw >= FRAME_MS)) {
      drawNet(now);
      lastNetDraw = now;
      dirty.net = false;
    }
    if (animate) schedule();
  }

  function markAllSilently() {
    for (const key in dirty) dirty[key] = true;
    layout = null;
  }

  const resize = new ResizeObserver(() => schedule());
  for (const s of Object.values(cv)) resize.observe(s.canvas);
  new IntersectionObserver(([e]) => {
    netVisible = e.isIntersecting;
    schedule();
  }).observe(cv.net.canvas);
  motion.addEventListener("change", () => markAll());
  T.onThemeChange(() => {
    readTheme();
    markAll();
  });
  document.fonts?.ready.then(() => markAll());
  pulseStart = performance.now();
}
