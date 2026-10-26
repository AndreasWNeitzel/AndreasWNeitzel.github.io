// Gaussian-process playground: a kernel gallery with live conditioning (on the main thread,
// the problems are small) and a Metropolis fit of a quasi-periodic Gaussian process to the
// HARPS radial velocities of HD 41248 (gp-worker.js does the sampling). Canvas colours come
// from the site tokens (window.siteTokens) and are read again whenever the theme changes.
// Nothing starts until the playground nears the viewport.
import { KERNELS, conditional, covariance, cholesky, logLikelihood, sampleFunctions, mulberry32 } from "./gp-math.js";

const MINUS = "−";
const X_MAX = 10;
const GRID_M = 240;
const DRAWS = 5;
const MAX_POINTS = 40;
const LML_CELLS = 28;
const LML_L = [Math.log10(0.1), Math.log10(10)];
const LML_SN = [Math.log10(0.01), Math.log10(2)];
const WINDOW_DAYS = 150;
const PREDICT_M = 300;
const RV_RANGE = 16;
const PAIR_POINTS = 3000;
const SUMMARY_POINTS = 4000;
const SYMBOL = { eta1: "η1", eta2: "η2", eta3: "η3", eta4: "η4", s: "s" };
const MEANING = { eta1: "amplitude", eta2: "evolution timescale", eta3: "rotation period", eta4: "smoothing", s: "jitter" };
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const motion = matchMedia("(prefers-reduced-motion: reduce)");

const root = document.getElementById("gp-playground");
if (root) {
  const start = () => boot(root).catch((err) => {
    console.error(err);
    for (const el of root.querySelectorAll(".pg-state")) {
      el.classList.add("is-alert");
      el.textContent = "The playground could not start here.";
    }
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
const grouped = (v) => Math.round(v).toLocaleString("en-GB");
const axisNumber = (v) => (v < 0 ? MINUS : "") + String(Number(Math.abs(v).toPrecision(3)));
function signed(v, digits = 2) {
  const r = Number(v.toFixed(digits));
  return (r < 0 ? MINUS : r > 0 ? "+" : "") + Math.abs(r).toFixed(digits);
}
function fixed(v, digits) {
  return (v < 0 ? MINUS : "") + Math.abs(v).toFixed(digits);
}
// Three significant figures, written plainly (no exponent) for the parameter table.
function sig3(v) {
  if (!Number.isFinite(v)) return "n/a";
  const a = Math.abs(v);
  const d = a >= 100 ? 0 : a >= 10 ? 1 : a >= 1 ? 2 : 3;
  return (v < 0 ? MINUS : "") + a.toFixed(d);
}

// Calendar date of a Julian Date (Meeus, Astronomical Algorithms, chapter 7).
function civil(jd) {
  const Z = Math.floor(jd + 0.5);
  let A = Z;
  if (Z >= 2299161) {
    const alpha = Math.floor((Z - 1867216.25) / 36524.25);
    A = Z + 1 + alpha - Math.floor(alpha / 4);
  }
  const B = A + 1524;
  const C = Math.floor((B - 122.1) / 365.25);
  const D = Math.floor(365.25 * C);
  const E = Math.floor((B - D) / 30.6001);
  const day = B - D - Math.floor(30.6001 * E);
  const month = E < 14 ? E - 1 : E - 13;
  const year = month > 2 ? C - 4716 : C - 4715;
  return { year, month, day };
}
function julianDay(year, month, day) {
  let Y = year;
  let M = month;
  if (M <= 2) { Y -= 1; M += 12; }
  const A = Math.floor(Y / 100);
  const B = 2 - A + Math.floor(A / 4);
  return Math.floor(365.25 * (Y + 4716)) + Math.floor(30.6001 * (M + 1)) + day + B - 1524.5;
}
const monthYear = (jd) => { const c = civil(jd); return `${MONTHS[c.month - 1]} ${c.year}`; };
const isoDate = (jd) => { const c = civil(jd); return `${c.year}-${String(c.month).padStart(2, "0")}-${String(c.day).padStart(2, "0")}`; };

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
    categorical() { return Array.from({ length: 10 }, (_, i) => this.colour(`--cat-${i}`)); },
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

// Interpolate between two token colours in OKLab; returns [r, g, b] bytes.
function ramp(from, to) {
  const a = oklab(rgbOf(from));
  const b = oklab(rgbOf(to));
  return (t) => fromOklab(a.map((v, i) => v + (b[i] - v) * t));
}
const alphaOf = (css, alpha) => { const [r, g, b] = rgbOf(css); return `rgb(${r} ${g} ${b} / ${alpha})`; };

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

function ring(ctx, x, y, r) {
  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.stroke();
}

function polyline(ctx, xs, ys, X, Y) {
  ctx.beginPath();
  for (let i = 0; i < xs.length; i++) {
    const x = X(xs[i]);
    const y = Y(ys[i]);
    if (i) ctx.lineTo(x, y);
    else ctx.moveTo(x, y);
  }
  ctx.stroke();
}

function bandPath(ctx, xs, mean, sd, k, X, Y) {
  ctx.beginPath();
  for (let i = 0; i < xs.length; i++) {
    const y = Y(mean[i] + k * sd[i]);
    if (i) ctx.lineTo(X(xs[i]), y);
    else ctx.moveTo(X(xs[i]), y);
  }
  for (let i = xs.length - 1; i >= 0; i--) ctx.lineTo(X(xs[i]), Y(mean[i] - k * sd[i]));
  ctx.closePath();
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
        if (lv >= l0 - 1e-9 && lv <= l1 + 1e-9) out.push(v);
      }
    }
    if (out.length >= 3) break;
  }
  return out;
}

function niceStep(range, target) {
  const raw = range / target;
  const mag = 10 ** Math.floor(Math.log10(raw));
  for (const m of [1, 2, 2.5, 5, 10]) if (m * mag >= raw) return m * mag;
  return 10 * mag;
}

function linTicks(lo, hi, target = 5) {
  const step = niceStep(hi - lo, target);
  const out = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) out.push(Number(v.toFixed(10)));
  return out;
}

const niceCount = (n) => [100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000].find((v) => v >= n) ?? n;

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

function tooltip(tip, lines, x, y, w, h) {
  tip.replaceChildren(...lines.map((text, i) => {
    const el = document.createElement(i ? "span" : "b");
    el.textContent = text;
    return el;
  }));
  tip.hidden = false;
  const tw = tip.offsetWidth;
  const th = tip.offsetHeight;
  tip.style.left = `${Math.max(0, Math.min(x + 12, w - tw - 2))}px`;
  tip.style.top = `${y - th - 12 < 0 ? y + 14 : y - th - 12}px`;
}

// ---------------------------------------------------------------- the playground
async function boot(root) {
  const $ = (sel) => root.querySelector(sel);
  const $$ = (sel) => Array.from(root.querySelectorAll(sel));
  const T = siteTokens();
  const query = new URLSearchParams(location.search);
  // ?mode=star opens the star mode and ?autorun=1 starts the sampler; for screenshots.
  const autorun = query.get("autorun") === "1";

  let C = null;
  let F = null;
  let CAT = [];
  function readTheme() {
    const c = (name) => T.colour(name);
    C = {
      surface: c("--surface"), surface2: c("--surface-2"), line: c("--line"), lineStrong: c("--line-strong"),
      ink: c("--ink"), ink2: c("--ink-2"), muted: c("--muted"), accent: c("--accent"), accent2: c("--accent-2"),
    };
    const cs = getComputedStyle(document.documentElement);
    F = { mono: cs.getPropertyValue("--mono").trim() || "monospace", sans: cs.getPropertyValue("--sans").trim() || "sans-serif" };
    CAT = T.categorical();
  }

  // ------------------------------------------------------------ mode switch
  const tabs = $$(".gp-switch [role=tab]");
  const panels = { kernels: $("#gp-kernels"), star: $("#gp-star") };
  let mode = query.get("mode") === "star" ? "star" : "kernels";
  function setMode(next) {
    mode = next;
    for (const tab of tabs) tab.setAttribute("aria-selected", tab.dataset.mode === mode ? "true" : "false");
    for (const [name, panel] of Object.entries(panels)) panel.hidden = name !== mode;
    for (const el of $$("[data-for]")) el.hidden = el.dataset.for !== mode;
    schedule();
  }
  for (const tab of tabs) tab.addEventListener("click", () => setMode(tab.dataset.mode));
  $(".gp-switch").addEventListener("keydown", (e) => {
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
    const i = tabs.findIndex((t) => t.dataset.mode === mode);
    const next = tabs[(i + (e.key === "ArrowRight" ? 1 : tabs.length - 1)) % tabs.length];
    next.focus();
    setMode(next.dataset.mode);
  });

  // ============================================================ kernel mode
  const K = {
    form: $(".gp-k-settings"),
    draw: $(".gp-k-draw"),
    clear: $(".gp-k-clear"),
    count: $(".gp-k-count"),
    lml: $(".gp-k-lml"),
    state: $(".gp-k-state"),
    title: $(".gp-k-title"),
    formula: $(".gp-k-formula"),
    tipMain: $(".gp-k-main .pg-tip"),
    tipLml: $(".gp-k-lml .pg-tip"),
  };
  const kcv = {
    main: surface($(".gp-k-main canvas")),
    kernel: surface($(".gp-k-kernel canvas")),
    lml: surface($(".gp-k-lml canvas")),
  };
  const xs = Float64Array.from({ length: GRID_M }, (_, i) => (X_MAX * i) / (GRID_M - 1));
  const ks = { kernel: "se", l: 1, P: 2, lam: 1, sf: 1, sn: 0.1 };
  let points = [];
  let drawSeed = 1;
  let post = null;
  let draws = [];
  let lmlMap = null;
  let hoverLml = null;

  const FORMULA = {
    se: "k(x, x') = \\sigma_f^2 \\exp\\!\\left(-\\frac{(x - x')^2}{2\\ell^2}\\right)",
    m32: "k(x, x') = \\sigma_f^2 \\left(1 + \\frac{\\sqrt{3}\\,|x - x'|}{\\ell}\\right) \\exp\\!\\left(-\\frac{\\sqrt{3}\\,|x - x'|}{\\ell}\\right)",
    per: "k(x, x') = \\sigma_f^2 \\exp\\!\\left(-\\frac{2 \\sin^2\\!\\big(\\pi (x - x') / P\\big)}{\\ell^2}\\right)",
    qp: "k(x, x') = \\sigma_f^2 \\exp\\!\\left(-\\frac{(x - x')^2}{2\\ell^2} - \\frac{2 \\sin^2\\!\\big(\\pi (x - x') / P\\big)}{\\lambda^2}\\right)",
  };
  const FALLBACK = {
    se: "k(x, x') = σf² exp(−(x − x')² / 2ℓ²)",
    m32: "k(x, x') = σf² (1 + √3 |x − x'| / ℓ) exp(−√3 |x − x'| / ℓ)",
    per: "k(x, x') = σf² exp(−2 sin²(π (x − x') / P) / ℓ²)",
    qp: "k(x, x') = σf² exp(−(x − x')² / 2ℓ² − 2 sin²(π (x − x') / P) / λ²)",
  };

  function readKernelForm() {
    const f = K.form.elements;
    ks.kernel = f.kernel.value;
    ks.l = 10 ** Number(f.l.value);
    ks.P = Number(f.P.value);
    ks.lam = 10 ** Number(f.lam.value);
    ks.sf = 10 ** Number(f.sf.value);
    ks.sn = 10 ** Number(f.sn.value);
    const uses = KERNELS[ks.kernel].uses;
    for (const el of K.form.querySelectorAll(".gp-range")) {
      const p = el.dataset.param;
      const shown = p === "sf" || p === "sn" || uses.includes(p);
      el.hidden = !shown;
    }
    f["l-out"].value = ks.l.toFixed(2);
    f["P-out"].value = ks.P.toFixed(1);
    f["lam-out"].value = ks.lam.toFixed(2);
    f["sf-out"].value = ks.sf.toFixed(2);
    f["sn-out"].value = ks.sn.toFixed(2);
    if (K.formula.dataset.tex !== FORMULA[ks.kernel]) {
      K.formula.dataset.tex = FORMULA[ks.kernel];
      K.formula.textContent = FALLBACK[ks.kernel];
      delete K.formula.dataset.done;
      window.renderTex?.(K.formula.parentElement);
    }
  }

  function kernelParams() {
    return { sf: ks.sf, l: ks.l, P: ks.P, lam: ks.lam };
  }

  // The prior or posterior on the grid, the five draws and the readouts.
  function computeKernelMode() {
    const k = KERNELS[ks.kernel].k;
    const p = kernelParams();
    const x = Float64Array.from(points, (q) => q.x);
    const y = Float64Array.from(points, (q) => q.y);
    post = conditional(xs, x, y, k, p, ks.sn * ks.sn);
    if (post) draws = sampleFunctions(post.mean, post.cov, DRAWS, mulberry32(drawSeed));
    else draws = [];
    lmlMap = null;
    K.count.textContent = String(points.length);
    K.lml.textContent = post && Number.isFinite(post.lml) ? fixed(post.lml, 1) : "n/a";
    K.title.textContent = points.length
      ? `Five functions drawn from the posterior, given ${points.length} ${points.length === 1 ? "observation" : "observations"}`
      : "Five functions drawn from the prior";
    K.state.textContent = points.length >= MAX_POINTS
      ? `At most ${MAX_POINTS} observations here. Click a point to remove it.`
      : post ? "Click in the figure to add an observation, and on a point to remove it."
        : "The covariance matrix could not be factorised; raise the noise.";
    K.state.classList.toggle("is-alert", !post);
    kcv.main.canvas.setAttribute("aria-label", `${KERNELS[ks.kernel].label} kernel: ${points.length ? "posterior" : "prior"} mean, 2 sigma band and five random functions on 0 to ${X_MAX}, with ${points.length} observations`);
    kdirty.main = kdirty.kernel = kdirty.lml = true;
    schedule();
  }

  // Log marginal likelihood over a grid of length scale and noise, cached until the points,
  // the kernel or another hyperparameter changes.
  function lmlGrid() {
    if (lmlMap || !points.length) return lmlMap;
    const k = KERNELS[ks.kernel].k;
    const n = points.length;
    const x = Float64Array.from(points, (q) => q.x);
    const y = Float64Array.from(points, (q) => q.y);
    const cells = new Float64Array(LML_CELLS * LML_CELLS);
    let max = -Infinity;
    for (let j = 0; j < LML_CELLS; j++) {
      const sn = 10 ** (LML_SN[0] + ((LML_SN[1] - LML_SN[0]) * (j + 0.5)) / LML_CELLS);
      for (let i = 0; i < LML_CELLS; i++) {
        const l = 10 ** (LML_L[0] + ((LML_L[1] - LML_L[0]) * (i + 0.5)) / LML_CELLS);
        const p = { ...kernelParams(), l };
        const A = covariance(x, x, k, p);
        for (let q = 0; q < n; q++) A[q * n + q] += sn * sn;
        let v = -Infinity;
        if (cholesky(A, n)) v = logLikelihood(A, n, y).value;
        cells[j * LML_CELLS + i] = v;
        if (v > max) max = v;
      }
    }
    const finite = Array.from(cells).filter(Number.isFinite).sort((a, b) => a - b);
    const floor = finite.length ? finite[Math.floor(finite.length * 0.1)] : max - 1;
    lmlMap = { cells, max, floor: Math.min(floor, max - 1e-6), best: cells.indexOf(max) };
    return lmlMap;
  }

  K.form.addEventListener("submit", (e) => e.preventDefault());
  K.form.addEventListener("input", () => {
    readKernelForm();
    computeKernelMode();
  });
  K.draw.addEventListener("click", () => {
    drawSeed += 1;
    computeKernelMode();
  });
  K.clear.addEventListener("click", () => {
    points = [];
    computeKernelMode();
  });

  function kMainFrame() {
    const s = kcv.main;
    const m = { l: 38, r: 22, t: 18, b: 24 };
    let R = 3;
    for (const q of points) R = Math.max(R, Math.abs(q.y) + 0.6);
    if (post) for (let i = 0; i < GRID_M; i++) R = Math.max(R, Math.abs(post.mean[i]) + 2 * post.sd[i]);
    R = Math.min(12, Math.ceil(R));
    const W = s.w - m.l - m.r;
    const H = s.h - m.t - m.b;
    return { m, W, H, R, X: (x) => m.l + (x / X_MAX) * W, Y: (y) => m.t + H / 2 - (y / R) * (H / 2) };
  }

  function drawKMain() {
    const s = kcv.main;
    const ctx = s.begin();
    if (s.w < 60) return;
    const f = kMainFrame();
    ctx.font = `11px ${F.mono}`;
    ctx.lineWidth = 1;
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (const v of linTicks(-f.R, f.R, 6)) {
      const y = Math.round(f.Y(v)) + 0.5;
      ctx.strokeStyle = v === 0 ? C.lineStrong : C.line;
      line(ctx, f.m.l, y, f.m.l + f.W, y);
      ctx.fillStyle = C.muted;
      ctx.fillText(axisNumber(v), f.m.l - 6, y);
    }
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    for (let v = 0; v <= X_MAX; v += 2) {
      const x = Math.round(f.X(v)) + 0.5;
      ctx.strokeStyle = C.line;
      line(ctx, x, f.m.t, x, f.m.t + f.H);
      ctx.fillStyle = C.muted;
      ctx.fillText(String(v), x, f.m.t + f.H + 6);
    }
    ctx.fillStyle = C.ink2;
    ctx.font = `500 11px ${F.mono}`;
    ctx.textAlign = "left";
    ctx.textBaseline = "top";
    ctx.fillText("x", f.m.l + f.W + 10, f.m.t + f.H + 6);
    ctx.textAlign = "right";
    ctx.fillText("f(x)", f.m.l - 6, 1);
    if (!post) return;
    ctx.save();
    ctx.beginPath();
    ctx.rect(f.m.l, f.m.t, f.W, f.H);
    ctx.clip();
    ctx.fillStyle = alphaOf(C.accent, 0.14);
    bandPath(ctx, xs, post.mean, post.sd, 2, f.X, f.Y);
    ctx.lineJoin = "round";
    ctx.lineWidth = 1.3;
    draws.forEach((d, i) => {
      ctx.strokeStyle = CAT[i % CAT.length];
      ctx.globalAlpha = 0.85;
      polyline(ctx, xs, d, f.X, f.Y);
    });
    ctx.globalAlpha = 1;
    ctx.strokeStyle = C.accent;
    ctx.lineWidth = 2;
    polyline(ctx, xs, post.mean, f.X, f.Y);
    ctx.restore();
    ctx.lineWidth = 1;
    for (const q of points) {
      const x = f.X(q.x);
      const y = f.Y(q.y);
      ctx.strokeStyle = C.ink2;
      line(ctx, x, f.Y(q.y - ks.sn), x, f.Y(q.y + ks.sn));
      ctx.fillStyle = C.surface;
      dot(ctx, x, y, 5.5);
      ctx.fillStyle = C.ink;
      dot(ctx, x, y, 4);
    }
  }

  function kMainPick(e) {
    const rect = kcv.main.canvas.getBoundingClientRect();
    const f = kMainFrame();
    const px = e.clientX - rect.left;
    const py = e.clientY - rect.top;
    let best = -1;
    let bd = 10 * 10;
    points.forEach((q, i) => {
      const dd = (f.X(q.x) - px) ** 2 + (f.Y(q.y) - py) ** 2;
      if (dd < bd) { bd = dd; best = i; }
    });
    const inside = px >= f.m.l && px <= f.m.l + f.W && py >= f.m.t && py <= f.m.t + f.H;
    return { best, inside, x: ((px - f.m.l) / f.W) * X_MAX, y: ((f.m.t + f.H / 2 - py) / (f.H / 2)) * f.R, px, py };
  }

  kcv.main.canvas.addEventListener("click", (e) => {
    const p = kMainPick(e);
    if (p.best >= 0) points.splice(p.best, 1);
    else if (p.inside && points.length < MAX_POINTS) points.push({ x: Math.round(p.x * 100) / 100, y: Math.round(p.y * 100) / 100 });
    else return;
    K.tipMain.hidden = true;
    computeKernelMode();
  });
  kcv.main.canvas.addEventListener("pointermove", (e) => {
    const p = kMainPick(e);
    kcv.main.canvas.style.cursor = p.best >= 0 ? "pointer" : p.inside ? "crosshair" : "";
    if (!post || !p.inside) { K.tipMain.hidden = true; return; }
    const i = Math.max(0, Math.min(GRID_M - 1, Math.round((p.x / X_MAX) * (GRID_M - 1))));
    const lines = p.best >= 0
      ? [`observation at x ${points[p.best].x.toFixed(2)}`, `y ${signed(points[p.best].y)} ± ${ks.sn.toFixed(2)}`, "click to remove"]
      : [`x ${xs[i].toFixed(2)}`, `mean ${signed(post.mean[i])}, sd ${post.sd[i].toFixed(2)}`, points.length < MAX_POINTS ? "click to add an observation" : "no more observations"];
    tooltip(K.tipMain, lines, p.px, p.py, kcv.main.w, kcv.main.h);
  });
  kcv.main.canvas.addEventListener("pointerleave", () => { K.tipMain.hidden = true; });

  function drawKKernel() {
    const s = kcv.kernel;
    const ctx = s.begin();
    if (s.w < 60) return;
    const m = { l: 38, r: 22, t: 14, b: 22 };
    const W = s.w - m.l - m.r;
    const H = s.h - m.t - m.b;
    const top = ks.sf * ks.sf;
    const X = (t) => m.l + (t / X_MAX) * W;
    const Y = (v) => m.t + H - (v / top) * H * 0.92;
    ctx.font = `11px ${F.mono}`;
    ctx.lineWidth = 1;
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (const v of [0, top / 2, top]) {
      const y = Math.round(Y(v)) + 0.5;
      ctx.strokeStyle = v === 0 ? C.lineStrong : C.line;
      line(ctx, m.l, y, m.l + W, y);
      ctx.fillStyle = C.muted;
      ctx.fillText(axisNumber(v), m.l - 6, y);
    }
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    for (let v = 0; v <= X_MAX; v += 2) {
      ctx.fillStyle = C.muted;
      ctx.fillText(String(v), X(v), m.t + H + 6);
    }
    ctx.fillStyle = C.ink2;
    ctx.font = `500 11px ${F.mono}`;
    ctx.textAlign = "left";
    ctx.fillText("τ", m.l + W + 10, m.t + H + 6);
    ctx.textAlign = "right";
    ctx.fillText("k(τ)", m.l - 6, 0);
    const k = KERNELS[ks.kernel].k;
    const p = kernelParams();
    const n = 400;
    const taus = Float64Array.from({ length: n }, (_, i) => (X_MAX * i) / (n - 1));
    const vals = Float64Array.from(taus, (t) => k(t, p));
    ctx.save();
    ctx.beginPath();
    ctx.rect(m.l, m.t, W, H);
    ctx.clip();
    ctx.strokeStyle = C.accent;
    ctx.lineWidth = 1.8;
    ctx.lineJoin = "round";
    polyline(ctx, taus, vals, X, Y);
    ctx.restore();
  }

  function lmlFrame() {
    const s = kcv.lml;
    const m = { l: 40, r: 22, t: 12, b: 26 };
    const W = s.w - m.l - m.r;
    const H = s.h - m.t - m.b;
    return {
      m, W, H,
      X: (l) => m.l + ((Math.log10(l) - LML_L[0]) / (LML_L[1] - LML_L[0])) * W,
      Y: (sn) => m.t + H - ((Math.log10(sn) - LML_SN[0]) / (LML_SN[1] - LML_SN[0])) * H,
      cell: (px, py) => {
        const i = Math.floor(((px - m.l) / W) * LML_CELLS);
        const j = Math.floor(((m.t + H - py) / H) * LML_CELLS);
        if (i < 0 || j < 0 || i >= LML_CELLS || j >= LML_CELLS) return null;
        return {
          i, j,
          l: 10 ** (LML_L[0] + ((LML_L[1] - LML_L[0]) * (i + 0.5)) / LML_CELLS),
          sn: 10 ** (LML_SN[0] + ((LML_SN[1] - LML_SN[0]) * (j + 0.5)) / LML_CELLS),
        };
      },
    };
  }

  function drawKLml() {
    const s = kcv.lml;
    const ctx = s.begin();
    if (s.w < 60) return;
    const f = lmlFrame();
    const map = lmlGrid();
    ctx.font = `11px ${F.mono}`;
    ctx.lineWidth = 1;
    if (map) {
      const mix = ramp(C.surface2, C.accent);
      const cw = f.W / LML_CELLS;
      const ch = f.H / LML_CELLS;
      for (let j = 0; j < LML_CELLS; j++) {
        for (let i = 0; i < LML_CELLS; i++) {
          const v = map.cells[j * LML_CELLS + i];
          const t = Number.isFinite(v) ? Math.max(0, Math.min(1, (v - map.floor) / (map.max - map.floor))) : 0;
          const [r, g, b] = mix(t);
          ctx.fillStyle = `rgb(${r} ${g} ${b})`;
          ctx.fillRect(f.m.l + i * cw, f.m.t + f.H - (j + 1) * ch, cw + 0.5, ch + 0.5);
        }
      }
    }
    ctx.strokeStyle = C.lineStrong;
    ctx.strokeRect(f.m.l + 0.5, f.m.t + 0.5, f.W, f.H);
    ctx.fillStyle = C.muted;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    for (const v of [0.1, 1, 10]) ctx.fillText(axisNumber(v), f.X(v), f.m.t + f.H + 6);
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (const v of [0.01, 0.1, 1]) ctx.fillText(axisNumber(v), f.m.l - 6, f.Y(v));
    ctx.fillStyle = C.ink2;
    ctx.font = `500 11px ${F.mono}`;
    ctx.textAlign = "left";
    ctx.textBaseline = "top";
    ctx.fillText("ℓ", f.m.l + f.W + 10, f.m.t + f.H + 6);
    ctx.textAlign = "right";
    ctx.fillText("σn", f.m.l - 6, 0);
    if (!map) {
      ctx.fillStyle = C.muted;
      ctx.font = `500 12px ${F.sans}`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("Add observations to map it", f.m.l + f.W / 2, f.m.t + f.H / 2);
      return;
    }
    // The best cell, the current hyperparameters, and the cell under the pointer.
    const bi = map.best % LML_CELLS;
    const bj = Math.floor(map.best / LML_CELLS);
    const bx = f.m.l + ((bi + 0.5) * f.W) / LML_CELLS;
    const by = f.m.t + f.H - ((bj + 0.5) * f.H) / LML_CELLS;
    ctx.strokeStyle = C.surface;
    ctx.lineWidth = 1.5;
    line(ctx, bx - 4, by, bx + 4, by);
    line(ctx, bx, by - 4, bx, by + 4);
    if (hoverLml) {
      ctx.strokeStyle = C.ink2;
      ring(ctx, f.X(hoverLml.l), f.Y(hoverLml.sn), 5);
    }
    ctx.strokeStyle = C.ink;
    ctx.lineWidth = 2;
    const x = Math.max(f.m.l, Math.min(f.m.l + f.W, f.X(ks.l)));
    const y = Math.max(f.m.t, Math.min(f.m.t + f.H, f.Y(ks.sn)));
    ring(ctx, x, y, 5.5);
    ctx.fillStyle = C.surface;
    dot(ctx, x, y, 2);
    ctx.fillStyle = C.ink;
    dot(ctx, x, y, 1.5);
    ctx.font = `11px ${F.mono}`;
    ctx.fillStyle = C.muted;
    ctx.textAlign = "right";
    ctx.textBaseline = "bottom";
    ctx.fillText(`max ${fixed(map.max, 1)}`, f.m.l + f.W - 4, f.m.t + f.H - 3);
  }

  kcv.lml.canvas.addEventListener("pointermove", (e) => {
    const rect = kcv.lml.canvas.getBoundingClientRect();
    const f = lmlFrame();
    const map = lmlGrid();
    const cell = map ? f.cell(e.clientX - rect.left, e.clientY - rect.top) : null;
    hoverLml = cell;
    kcv.lml.canvas.style.cursor = cell ? "pointer" : "";
    if (!cell) K.tipLml.hidden = true;
    else {
      const v = map.cells[cell.j * LML_CELLS + cell.i];
      tooltip(K.tipLml, [`log marginal likelihood ${Number.isFinite(v) ? fixed(v, 1) : "n/a"}`, `ℓ ${cell.l.toFixed(2)}, σn ${cell.sn.toFixed(3)}`, "click to set"], e.clientX - rect.left, e.clientY - rect.top, kcv.lml.w, kcv.lml.h);
    }
    kdirty.lml = true;
    schedule();
  });
  kcv.lml.canvas.addEventListener("pointerleave", () => {
    hoverLml = null;
    K.tipLml.hidden = true;
    kdirty.lml = true;
    schedule();
  });
  kcv.lml.canvas.addEventListener("click", (e) => {
    const rect = kcv.lml.canvas.getBoundingClientRect();
    const cell = lmlGrid() ? lmlFrame().cell(e.clientX - rect.left, e.clientY - rect.top) : null;
    if (!cell) return;
    K.form.elements.l.value = String(Math.log10(cell.l));
    K.form.elements.sn.value = String(Math.log10(cell.sn));
    readKernelForm();
    computeKernelMode();
  });

  // ============================================================ star mode
  const S = {
    run: $(".gp-s-run"),
    step: $(".gp-s-step"),
    reset: $(".gp-s-reset"),
    live: $("#gp-star .pg-live"),
    steps: $(".gp-s-steps"),
    acc: $(".gp-s-acc"),
    state: $(".gp-s-state"),
    form: $(".gp-s-settings"),
    table: $(".gp-s-params tbody"),
    tableNote: $(".gp-s-note"),
    mainTitle: $(".gp-s-title"),
    pairTitle: $(".gp-s-pair-title"),
    traceTitle: $(".gp-s-trace-title"),
    tipMain: $(".gp-s-main .pg-tip"),
    tipPair: $(".gp-s-pair .pg-tip"),
    windowSelect: $(".gp-s-window"),
    px: $(".gp-s-px"),
    py: $(".gp-s-py"),
  };
  const scv = {
    main: surface($(".gp-s-main canvas")),
    trace: surface($(".gp-s-trace canvas")),
    pair: surface($(".gp-s-pair canvas")),
  };
  const STRIP = 54;

  const rv = await request(root.dataset.rv, "json");
  const n = rv.n;
  const bjd0 = rv.bjd[0];
  const t = Float64Array.from(rv.bjd, (b) => b - bjd0);
  const rvMean = rv.rv.reduce((a, b) => a + b, 0) / n;
  const y = Float64Array.from(rv.rv, (v) => v - rvMean);
  const sig = Float64Array.from(rv.e_rv);
  const span = t[n - 1];
  for (const el of $$(".gp-rv-mean")) el.textContent = rvMean.toFixed(2);
  for (const el of $$(".gp-rv-n")) el.textContent = String(n);

  // Observing groups (gaps over 60 days) for the window select; the window is 150 days wide.
  const groups = [];
  let g0 = 0;
  for (let i = 1; i <= n; i++) {
    if (i === n || t[i] - t[i - 1] > 60) {
      if (i - g0 >= 4) groups.push({ from: g0, to: i - 1 });
      g0 = i;
    }
  }
  let win = { x0: 0 };
  function windowFor(group) {
    const centre = (t[group.from] + t[group.to]) / 2;
    const width = t[group.to] - t[group.from];
    return Math.max(0, Math.min(span - WINDOW_DAYS, width <= WINDOW_DAYS ? centre - WINDOW_DAYS / 2 : t[group.to] - WINDOW_DAYS + 6));
  }
  S.windowSelect.replaceChildren(...groups.map((g, i) => {
    const o = document.createElement("option");
    o.value = String(i);
    o.textContent = `${monthYear(rv.bjd[g.from])}, ${g.to - g.from + 1} points`;
    return o;
  }));
  S.windowSelect.value = String(groups.length - 1);
  win.x0 = windowFor(groups[groups.length - 1]);

  let prior = null;
  let chain = new Float64Array(6 * 4096);
  let cols = 6;
  let steps = 0;
  let accepted = 0;
  let status = "idle";
  let current = null;
  let lpNow = NaN;
  let runId = -1;
  let maxSteps = Infinity;
  let predictive = null;
  let summary = null;
  let pairCache = null;
  let hoverMain = -1;
  let resumeOnShow = false;
  let autoStarted = false;
  const scfg = { stepScale: 1, burn: 0.25, draws: 32, start: "fixed", px: "eta3", py: "eta1" };

  function readStarForm() {
    const f = S.form.elements;
    scfg.stepScale = Number(f.scale.value);
    scfg.burn = Number(f.burn.value);
    scfg.start = f.start.value;
    if (!prior || prior.some((p) => p.name === S.px.value)) scfg.px = S.px.value;
    if (!prior || prior.some((p) => p.name === S.py.value)) scfg.py = S.py.value;
  }

  function gridFor(x0) {
    return Float64Array.from({ length: PREDICT_M }, (_, i) => x0 + (WINDOW_DAYS * i) / (PREDICT_M - 1));
  }

  const worker = new Worker(root.dataset.worker, { type: "module" });
  const send = (msg, transfer) => worker.postMessage(msg, transfer);
  worker.onerror = (e) => {
    e.preventDefault?.();
    S.state.classList.add("is-alert");
    S.state.textContent = "The sampler could not start in this browser.";
  };
  worker.onmessage = (event) => {
    const m = event.data;
    if (m.type === "ready") onReady(m);
    else if (m.type === "state") onState(m);
    else if (m.type === "predictive") onPredictive(m);
  };
  readStarForm();
  send({
    type: "init", t: t.slice(), y: y.slice(), var: Float64Array.from(sig, (s) => s * s),
    cfg: { stepScale: scfg.stepScale, burn: scfg.burn, draws: scfg.draws, start: scfg.start }, grid: gridFor(win.x0),
  });

  function onReady(m) {
    prior = m.prior;
    maxSteps = m.maxSteps;
    readTheme();
    for (const b of [S.run, S.step, S.reset]) b.disabled = false;
    root.classList.add("is-ready");
    buildTable();
    markAll();
  }

  function onState(m) {
    if (m.run !== runId) {
      runId = m.run;
      steps = 0;
      accepted = 0;
      predictive = null;
      summary = null;
      pairCache = null;
    }
    cols = m.cols;
    const need = (steps + m.rows.length / cols) * cols;
    if (need > chain.length) {
      const bigger = new Float64Array(Math.max(need, chain.length * 2));
      bigger.set(chain);
      chain = bigger;
    }
    chain.set(m.rows, steps * cols);
    steps = m.steps;
    accepted = m.accepted;
    status = m.status;
    current = m.current;
    lpNow = m.lp;
    pairCache = null;
    updateReadout();
    sdirty.trace = sdirty.pair = true;
    schedule();
    if (autorun && !autoStarted && status === "idle") {
      autoStarted = true;
      send({ type: "run" });
    }
  }

  function onPredictive(m) {
    if (m.run !== runId) return;
    predictive = m;
    sdirty.main = true;
    schedule();
  }

  const STATES = {
    idle: "Not started. Run draws proposals until you pause; 100 steps takes that many.",
    running: "Sampling.",
    paused: "Paused.",
    limit: "The chain stops at its length limit. Press Reset to start again.",
  };

  function updateReadout() {
    const running = status === "running";
    S.steps.textContent = grouped(steps);
    S.acc.textContent = steps ? `${(100 * accepted / steps).toFixed(1)}%` : "n/a";
    S.live.setAttribute("aria-busy", running ? "true" : "false");
    S.run.textContent = running ? "Pause" : "Run";
    const stuck = status === "limit";
    S.run.disabled = stuck;
    S.step.disabled = stuck;
    S.state.classList.toggle("is-alert", stuck);
    S.state.textContent = STATES[status] ?? "";
    updateSummary();
  }

  const burnSteps = () => Math.floor(scfg.burn * steps);

  // Posterior medians and 16 to 84 percent intervals after burn-in, from at most
  // SUMMARY_POINTS evenly spaced states.
  function updateSummary() {
    const burn = burnSteps();
    const avail = steps - burn;
    if (avail < 20) { summary = null; }
    else {
      const stride = Math.max(1, Math.floor(avail / SUMMARY_POINTS));
      const count = Math.floor(avail / stride);
      summary = [...prior.keys(), cols - 1].map((d) => {
        const v = new Float64Array(count);
        for (let k = 0; k < count; k++) v[k] = chain[(burn + k * stride) * cols + d];
        v.sort();
        const q = (f) => v[Math.min(count - 1, Math.floor(f * count))];
        return { p16: q(0.16), median: q(0.5), p84: q(0.84) };
      });
    }
    fillTable();
  }

  function buildTable() {
    const rows = prior.map((p) => {
      const tr = document.createElement("tr");
      const cells = ["", "", ""].map(() => document.createElement("td"));
      cells[0].innerHTML = `<b>${SYMBOL[p.name]}</b>${p.unit ? ` <small>${p.unit}</small>` : ""}`;
      cells[0].title = `${MEANING[p.name]}, prior ${p.log ? "log-uniform" : "uniform"} ${p.lo} to ${p.hi}${p.unit ? ` ${p.unit}` : ""}`;
      tr.append(...cells);
      return tr;
    });
    const last = document.createElement("tr");
    const cells = ["", "", ""].map(() => document.createElement("td"));
    cells[0].innerHTML = "<b>ln p</b>";
    cells[0].title = "log posterior of the state, up to a constant";
    last.append(...cells);
    S.table.replaceChildren(...rows, last);
    for (const sel of [S.px, S.py]) {
      sel.replaceChildren(...prior.map((p) => {
        const o = document.createElement("option");
        o.value = p.name;
        o.textContent = SYMBOL[p.name];
        o.title = MEANING[p.name];
        return o;
      }));
    }
    S.px.value = "eta3";
    S.py.value = "eta1";
    readStarForm();
  }

  function fillTable() {
    if (!prior) return;
    const rows = S.table.rows;
    const show = (d, now, digits) => {
      const r = rows[d];
      r.cells[1].textContent = Number.isFinite(now) ? (digits === undefined ? sig3(now) : fixed(now, digits)) : "";
      const q = summary && summary[d];
      const f = (v) => (digits === undefined ? sig3(v) : fixed(v, digits));
      r.cells[2].textContent = q ? `${f(q.median)} (${f(q.p16)} to ${f(q.p84)})` : "";
    };
    prior.forEach((p, d) => show(d, current ? current[d] : NaN));
    show(prior.length, lpNow, 0);
    const burn = burnSteps();
    S.tableNote.textContent = summary
      ? `Median and 16 to 84% interval of ${grouped(steps - burn)} states after a burn-in of ${grouped(burn)}; priors below.`
      : "Median and 16 to 84% interval after burn-in; priors below.";
  }

  S.run.addEventListener("click", () => send({ type: status === "running" ? "pause" : "run" }));
  S.step.addEventListener("click", () => send({ type: "step", count: 100 }));
  S.reset.addEventListener("click", () => send({ type: "reset", start: scfg.start }));
  S.form.addEventListener("submit", (e) => e.preventDefault());
  S.form.addEventListener("change", (e) => {
    readStarForm();
    pairCache = null;
    send({ type: "config", stepScale: scfg.stepScale, burn: scfg.burn, start: scfg.start });
    if (e.target.name === "burn") updateSummary();
    sdirty.trace = sdirty.pair = true;
    schedule();
  });
  S.windowSelect.addEventListener("change", () => {
    win.x0 = windowFor(groups[Number(S.windowSelect.value)]);
    send({ type: "grid", x: gridFor(win.x0) });
    sdirty.main = true;
    schedule();
  });
  for (const sel of [S.px, S.py]) {
    sel.addEventListener("change", () => {
      readStarForm();
      pairCache = null;
      sdirty.trace = sdirty.pair = true;
      schedule();
    });
  }

  document.addEventListener("visibilitychange", () => {
    if (document.hidden && status === "running") {
      resumeOnShow = true;
      send({ type: "pause" });
    } else if (!document.hidden && resumeOnShow) {
      resumeOnShow = false;
      send({ type: "run" });
    }
  });

  // ------------------------------------------------------------ main figure: window and overview
  function sMainFrame() {
    const s = scv.main;
    const m = { l: 44, r: 12, t: 16, b: 24 };
    const W = s.w - m.l - m.r;
    const H = s.h - STRIP - 14 - m.t - m.b;
    const strip = { t: s.h - STRIP, h: STRIP - 18 };
    return {
      m, W, H, strip,
      X: (x) => m.l + ((x - win.x0) / WINDOW_DAYS) * W,
      Y: (v) => m.t + H / 2 - (v / RV_RANGE) * (H / 2),
      SX: (x) => m.l + (x / span) * W,
      SY: (v) => strip.t + strip.h / 2 - (v / RV_RANGE) * (strip.h / 2),
    };
  }

  function drawSMain() {
    const s = scv.main;
    const ctx = s.begin();
    if (s.w < 60) return;
    const f = sMainFrame();
    ctx.font = `11px ${F.mono}`;
    ctx.lineWidth = 1;
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (const v of linTicks(-RV_RANGE, RV_RANGE, 8)) {
      const yy = Math.round(f.Y(v)) + 0.5;
      ctx.strokeStyle = v === 0 ? C.lineStrong : C.line;
      line(ctx, f.m.l, yy, f.m.l + f.W, yy);
      ctx.fillStyle = C.muted;
      ctx.fillText(axisNumber(v), f.m.l - 6, yy);
    }
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    const x1 = win.x0 + WINDOW_DAYS;
    for (const v of linTicks(win.x0, x1, 6)) {
      const xx = Math.round(f.X(v)) + 0.5;
      ctx.strokeStyle = C.line;
      line(ctx, xx, f.m.t, xx, f.m.t + f.H);
      ctx.fillStyle = C.muted;
      ctx.fillText(grouped(v), xx, f.m.t + f.H + 6);
    }
    ctx.fillStyle = C.ink2;
    ctx.font = `500 11px ${F.mono}`;
    ctx.textAlign = "right";
    ctx.textBaseline = "top";
    ctx.fillText("m/s", f.m.l - 6, 0);
    ctx.save();
    ctx.beginPath();
    ctx.rect(f.m.l, f.m.t, f.W, f.H);
    ctx.clip();
    if (predictive) {
      const px = predictive.x;
      ctx.fillStyle = alphaOf(C.accent, 0.14);
      bandPath(ctx, px, predictive.mean, predictive.sd, 2, f.X, f.Y);
      ctx.lineJoin = "round";
      ctx.lineWidth = 1;
      ctx.strokeStyle = C.accent2;
      ctx.globalAlpha = 0.4;
      for (const curve of predictive.curves) polyline(ctx, px, curve, f.X, f.Y);
      ctx.globalAlpha = 1;
      ctx.strokeStyle = C.accent;
      ctx.lineWidth = 2;
      polyline(ctx, px, predictive.mean, f.X, f.Y);
    }
    ctx.lineWidth = 1;
    for (let i = 0; i < n; i++) {
      if (t[i] < win.x0 - 1 || t[i] > x1 + 1) continue;
      const xx = f.X(t[i]);
      const yy = f.Y(y[i]);
      ctx.strokeStyle = C.ink2;
      line(ctx, xx, f.Y(y[i] - sig[i]), xx, f.Y(y[i] + sig[i]));
      ctx.fillStyle = C.surface;
      dot(ctx, xx, yy, 4.5);
      ctx.fillStyle = i === hoverMain ? C.accent2 : C.ink;
      dot(ctx, xx, yy, 3.2);
    }
    ctx.restore();
    // Overview strip: the whole series, the window, and year ticks.
    const st = f.strip;
    ctx.fillStyle = C.surface2;
    ctx.fillRect(f.m.l, st.t, f.W, st.h);
    ctx.fillStyle = alphaOf(C.accent, 0.18);
    ctx.fillRect(f.SX(win.x0), st.t, f.SX(x1) - f.SX(win.x0), st.h);
    ctx.strokeStyle = C.accent;
    ctx.strokeRect(Math.round(f.SX(win.x0)) + 0.5, st.t + 0.5, Math.round(f.SX(x1) - f.SX(win.x0)), st.h - 1);
    ctx.fillStyle = C.ink2;
    for (let i = 0; i < n; i++) ctx.fillRect(f.SX(t[i]) - 0.75, f.SY(y[i]) - 0.75, 1.5, 1.5);
    ctx.font = `10px ${F.mono}`;
    ctx.fillStyle = C.muted;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    const y0 = civil(bjd0).year;
    const y1 = civil(bjd0 + span).year;
    for (let yr = y0 + 1; yr <= y1; yr++) {
      const xx = f.SX(julianDay(yr, 1, 1) - bjd0);
      ctx.strokeStyle = C.lineStrong;
      line(ctx, Math.round(xx) + 0.5, st.t + st.h - 4, Math.round(xx) + 0.5, st.t + st.h);
      if ((yr - y0) % 2 === 0) ctx.fillText(String(yr), xx, st.t + st.h + 3);
    }
    const nShown = Array.from(t).filter((v) => v >= win.x0 && v <= x1).length;
    S.mainTitle.textContent = `${nShown} of ${n} velocities, ${isoDate(bjd0 + win.x0)} to ${isoDate(bjd0 + x1)}`;
    scv.main.canvas.setAttribute("aria-label", `Radial velocities of HD 41248 from ${isoDate(bjd0 + win.x0)} to ${isoDate(bjd0 + x1)} with the marginalised Gaussian-process mean and 2 sigma band${predictive ? ` from ${predictive.samples} posterior samples` : ""}, and an overview of all ${n} points below`);
  }

  scv.main.canvas.addEventListener("click", (e) => {
    const rect = scv.main.canvas.getBoundingClientRect();
    const f = sMainFrame();
    const px = e.clientX - rect.left;
    const py = e.clientY - rect.top;
    if (py < f.strip.t - 4) return;
    const centre = ((px - f.m.l) / f.W) * span;
    win.x0 = Math.max(0, Math.min(span - WINDOW_DAYS, centre - WINDOW_DAYS / 2));
    send({ type: "grid", x: gridFor(win.x0) });
    sdirty.main = true;
    schedule();
  });
  scv.main.canvas.addEventListener("pointermove", (e) => {
    const rect = scv.main.canvas.getBoundingClientRect();
    const f = sMainFrame();
    const px = e.clientX - rect.left;
    const py = e.clientY - rect.top;
    if (py >= f.strip.t - 4) {
      scv.main.canvas.style.cursor = "pointer";
      if (hoverMain >= 0) { hoverMain = -1; sdirty.main = true; schedule(); }
      S.tipMain.hidden = true;
      return;
    }
    scv.main.canvas.style.cursor = "";
    let best = -1;
    let bd = 10 * 10;
    for (let i = 0; i < n; i++) {
      if (t[i] < win.x0 || t[i] > win.x0 + WINDOW_DAYS) continue;
      const dd = (f.X(t[i]) - px) ** 2 + (f.Y(y[i]) - py) ** 2;
      if (dd < bd) { bd = dd; best = i; }
    }
    if (best !== hoverMain) {
      hoverMain = best;
      sdirty.main = true;
      schedule();
    }
    if (best < 0) { S.tipMain.hidden = true; return; }
    tooltip(S.tipMain, [`BJD ${rv.bjd[best].toFixed(4)}, ${isoDate(rv.bjd[best])}`, `RV ${signed(y[best])} ± ${sig[best].toFixed(2)} m/s about the mean`, `S-index ${rv.s_index[best].toFixed(3)}`], f.X(t[best]), f.Y(y[best]), scv.main.w, scv.main.h);
  });
  scv.main.canvas.addEventListener("pointerleave", () => {
    S.tipMain.hidden = true;
    if (hoverMain >= 0) { hoverMain = -1; sdirty.main = true; schedule(); }
  });

  // ------------------------------------------------------------ traces
  const paramIndex = (name) => prior.findIndex((p) => p.name === name);
  const coord = (d, v) => (prior[d].log ? Math.log10(v) : v);

  function traceRange(d) {
    let lo = Infinity;
    let hi = -Infinity;
    const stride = Math.max(1, Math.floor(steps / 20000));
    for (let k = 0; k < steps; k += stride) {
      const v = coord(d, chain[k * cols + d]);
      if (v < lo) lo = v;
      if (v > hi) hi = v;
    }
    if (!Number.isFinite(lo)) { lo = coord(d, prior[d].lo); hi = coord(d, prior[d].hi); }
    const pad = Math.max((hi - lo) * 0.1, prior[d].log ? 0.02 : 0.2);
    return [lo - pad, hi + pad];
  }

  function drawTrace() {
    const s = scv.trace;
    const ctx = s.begin();
    if (!prior || s.w < 60) return;
    const which = [paramIndex(scfg.px), paramIndex(scfg.py)];
    const m = { l: 50, r: 10, t: 6, b: 18 };
    const gap = 8;
    const W = s.w - m.l - m.r;
    const H = (s.h - m.t - m.b - gap) / 2;
    const xMax = niceCount(Math.max(100, steps));
    const X = (k) => m.l + (k / xMax) * W;
    const burn = burnSteps();
    ctx.font = `11px ${F.mono}`;
    ctx.lineWidth = 1;
    which.forEach((d, row) => {
      const top = m.t + row * (H + gap);
      const [lo, hi] = traceRange(d);
      const Y = (v) => top + H - ((v - lo) / (hi - lo)) * H;
      ctx.fillStyle = C.surface2;
      ctx.fillRect(m.l, top, W, H);
      if (burn > 0) {
        ctx.fillStyle = alphaOf(C.muted, 0.16);
        ctx.fillRect(m.l, top, X(burn) - m.l, H);
      }
      ctx.strokeStyle = C.line;
      ctx.strokeRect(m.l + 0.5, top + 0.5, W, H);
      ctx.fillStyle = C.ink2;
      ctx.font = `500 11px ${F.mono}`;
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";
      ctx.fillText(SYMBOL[prior[d].name], m.l - 6, top + H / 2);
      ctx.font = `10px ${F.mono}`;
      ctx.fillStyle = C.muted;
      ctx.textBaseline = "top";
      ctx.fillText(sig3(prior[d].log ? 10 ** hi : hi), m.l - 6, top);
      ctx.textBaseline = "bottom";
      ctx.fillText(sig3(prior[d].log ? 10 ** lo : lo), m.l - 6, top + H);
      if (!steps) return;
      // Per pixel column: the lowest and highest value, so long chains stay honest.
      ctx.strokeStyle = C.accent;
      ctx.beginPath();
      const perPx = steps / W;
      if (perPx <= 1) {
        for (let k = 0; k < steps; k++) {
          const v = Y(coord(d, chain[k * cols + d]));
          if (k) ctx.lineTo(X(k), v);
          else ctx.moveTo(X(k), v);
        }
      } else {
        for (let px = 0; px < W; px++) {
          const k0 = Math.floor(px * perPx);
          const k1 = Math.min(steps, Math.floor((px + 1) * perPx) + 1);
          if (k0 >= steps) break;
          let lo2 = Infinity;
          let hi2 = -Infinity;
          for (let k = k0; k < k1; k++) {
            const v = coord(d, chain[k * cols + d]);
            if (v < lo2) lo2 = v;
            if (v > hi2) hi2 = v;
          }
          ctx.moveTo(m.l + px + 0.5, Y(hi2) - 0.5);
          ctx.lineTo(m.l + px + 0.5, Y(lo2) + 0.5);
        }
      }
      ctx.stroke();
    });
    ctx.fillStyle = C.muted;
    ctx.font = `11px ${F.mono}`;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    const base = m.t + 2 * H + gap;
    const xStep = xMax / (xMax % 4 === 0 ? 4 : 5);
    for (let k = 0; k <= xMax; k += xStep) ctx.fillText(grouped(k), Math.min(X(k), m.l + W - 14), base + 4);
    S.traceTitle.textContent = `Trace of ${SYMBOL[scfg.px]} and ${SYMBOL[scfg.py]} over ${grouped(steps)} steps`;
    scv.trace.canvas.setAttribute("aria-label", `Trace plots of ${SYMBOL[scfg.px]} and ${SYMBOL[scfg.py]} over ${steps} Metropolis steps; the first ${burn} are shaded as burn-in`);
  }

  // ------------------------------------------------------------ pair plot
  function pairSamples() {
    if (pairCache) return pairCache;
    const burn = burnSteps();
    const avail = steps - burn;
    const dx = paramIndex(scfg.px);
    const dy = paramIndex(scfg.py);
    const stride = Math.max(1, Math.floor(avail / PAIR_POINTS));
    const count = avail > 0 ? Math.floor(avail / stride) : 0;
    const xv = new Float64Array(count);
    const yv = new Float64Array(count);
    for (let k = 0; k < count; k++) {
      const row = (burn + k * stride) * cols;
      xv[k] = coord(dx, chain[row + dx]);
      yv[k] = coord(dy, chain[row + dy]);
    }
    pairCache = { xv, yv, dx, dy, count, burn };
    return pairCache;
  }

  function pairRange(values, d, fallback) {
    let lo = Infinity;
    let hi = -Infinity;
    for (const v of values) { if (v < lo) lo = v; if (v > hi) hi = v; }
    if (fallback !== undefined) { lo = Math.min(lo, fallback); hi = Math.max(hi, fallback); }
    if (!Number.isFinite(lo)) { lo = coord(d, prior[d].lo); hi = coord(d, prior[d].hi); }
    const pad = Math.max((hi - lo) * 0.12, prior[d].log ? 0.03 : 0.3);
    return [lo - pad, hi + pad];
  }

  function axisLabel(d) {
    const p = prior[d];
    return `${SYMBOL[p.name]}${p.unit ? ` (${p.unit})` : ""}`;
  }

  function ticksFor(d, lo, hi) {
    if (prior[d].log) return logTicks(lo, hi).map((v) => ({ at: Math.log10(v), text: axisNumber(v) }));
    return linTicks(lo, hi, 4).map((v) => ({ at: v, text: axisNumber(v) }));
  }

  function drawPair() {
    const s = scv.pair;
    const ctx = s.begin();
    if (!prior || s.w < 60) return;
    const P = pairSamples();
    const histW = 34;
    const m = { l: 46, r: 10 + histW, t: 6 + histW, b: 34 };
    const W = s.w - m.l - m.r;
    const H = s.h - m.t - m.b;
    const cx = current ? coord(P.dx, current[P.dx]) : undefined;
    const cy = current ? coord(P.dy, current[P.dy]) : undefined;
    const [xlo, xhi] = pairRange(P.xv, P.dx, cx);
    const [ylo, yhi] = pairRange(P.yv, P.dy, cy);
    const X = (v) => m.l + ((v - xlo) / (xhi - xlo)) * W;
    const Y = (v) => m.t + H - ((v - ylo) / (yhi - ylo)) * H;
    ctx.font = `11px ${F.mono}`;
    ctx.lineWidth = 1;
    ctx.fillStyle = C.surface2;
    ctx.fillRect(m.l, m.t, W, H);
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    for (const tk of ticksFor(P.dx, xlo, xhi)) {
      const xx = Math.round(X(tk.at)) + 0.5;
      ctx.strokeStyle = C.line;
      line(ctx, xx, m.t, xx, m.t + H);
      ctx.fillStyle = C.muted;
      ctx.fillText(tk.text, xx, m.t + H + 6);
    }
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (const tk of ticksFor(P.dy, ylo, yhi)) {
      const yy = Math.round(Y(tk.at)) + 0.5;
      ctx.strokeStyle = C.line;
      line(ctx, m.l, yy, m.l + W, yy);
      ctx.fillStyle = C.muted;
      ctx.fillText(tk.text, m.l - 6, yy);
    }
    ctx.strokeStyle = C.lineStrong;
    ctx.strokeRect(m.l + 0.5, m.t + 0.5, W, H);
    // Marginal histograms along the top and the right.
    const bins = 28;
    const hx = new Float64Array(bins);
    const hy = new Float64Array(bins);
    for (let k = 0; k < P.count; k++) {
      const bx = Math.min(bins - 1, Math.floor(((P.xv[k] - xlo) / (xhi - xlo)) * bins));
      const by = Math.min(bins - 1, Math.floor(((P.yv[k] - ylo) / (yhi - ylo)) * bins));
      hx[bx] += 1;
      hy[by] += 1;
    }
    const mx = Math.max(1, ...hx);
    const my = Math.max(1, ...hy);
    ctx.fillStyle = alphaOf(C.accent, 0.45);
    for (let b = 0; b < bins; b++) {
      const h = (hx[b] / mx) * (histW - 6);
      ctx.fillRect(m.l + (b * W) / bins, m.t - 4 - h, W / bins - 0.5, h);
      const w = (hy[b] / my) * (histW - 6);
      ctx.fillRect(m.l + W + 4, m.t + H - ((b + 1) * H) / bins, w, H / bins - 0.5);
    }
    ctx.fillStyle = alphaOf(C.accent, P.count > 1500 ? 0.3 : 0.55);
    const r = P.count > 1500 ? 1.4 : 2;
    for (let k = 0; k < P.count; k++) dot(ctx, X(P.xv[k]), Y(P.yv[k]), r);
    if (current) {
      ctx.strokeStyle = C.ink;
      ctx.lineWidth = 1.8;
      ring(ctx, X(cx), Y(cy), 5.5);
    }
    ctx.fillStyle = C.ink2;
    ctx.font = `500 11px ${F.mono}`;
    ctx.textAlign = "center";
    ctx.textBaseline = "alphabetic";
    ctx.fillText(axisLabel(P.dx), m.l + W / 2, s.h - 4);
    ctx.save();
    ctx.translate(11, m.t + H / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textBaseline = "middle";
    ctx.fillText(axisLabel(P.dy), 0, 0);
    ctx.restore();
    if (!P.count) {
      ctx.fillStyle = C.muted;
      ctx.font = `500 12px ${F.sans}`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(steps ? "Waiting for states after burn-in" : "Press Run to sample", m.l + W / 2, m.t + H / 2);
    }
    S.pairTitle.textContent = `${SYMBOL[scfg.py]} against ${SYMBOL[scfg.px]}, ${grouped(P.count)} states after burn-in`;
    scv.pair.canvas.setAttribute("aria-label", `Scatter of ${SYMBOL[scfg.py]} against ${SYMBOL[scfg.px]} for ${P.count} posterior states after burn-in, with marginal histograms and the current state ringed`);
  }

  // ------------------------------------------------------------ frame loop
  const kdirty = { main: true, kernel: true, lml: true };
  const sdirty = { main: true, trace: true, pair: true };
  let raf = 0;
  let lastFrame = 0;
  let timer = 0;

  function schedule() {
    if (raf || timer) return;
    // With reduced motion the live plots refresh twice a second instead of every frame.
    const wait = motion.matches ? Math.max(0, 500 - (performance.now() - lastFrame)) : 0;
    if (wait > 0) timer = setTimeout(() => { timer = 0; raf = requestAnimationFrame(frame); }, wait);
    else raf = requestAnimationFrame(frame);
  }

  function frame(now) {
    raf = 0;
    lastFrame = now;
    if (!C) readTheme();
    if (mode === "kernels") {
      for (const s of Object.values(kcv)) if (s.fit()) kdirty.main = kdirty.kernel = kdirty.lml = true;
      if (kdirty.main) { drawKMain(); kdirty.main = false; }
      if (kdirty.kernel) { drawKKernel(); kdirty.kernel = false; }
      if (kdirty.lml) { drawKLml(); kdirty.lml = false; }
    } else {
      for (const s of Object.values(scv)) if (s.fit()) sdirty.main = sdirty.trace = sdirty.pair = true;
      if (sdirty.main) { drawSMain(); sdirty.main = false; }
      if (sdirty.trace) { drawTrace(); sdirty.trace = false; }
      if (sdirty.pair) { drawPair(); sdirty.pair = false; }
    }
  }

  function markAll() {
    for (const key in kdirty) kdirty[key] = true;
    for (const key in sdirty) sdirty[key] = true;
    schedule();
  }

  const resize = new ResizeObserver(() => schedule());
  for (const s of [...Object.values(kcv), ...Object.values(scv)]) resize.observe(s.canvas);
  motion.addEventListener("change", () => markAll());
  T.onThemeChange(() => {
    readTheme();
    markAll();
  });
  document.fonts?.ready.then(() => markAll());

  readTheme();
  readKernelForm();
  computeKernelMode();
  setMode(mode);
}
