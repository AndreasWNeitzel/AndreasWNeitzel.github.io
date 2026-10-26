// Polytrope playground: the Lane-Emden equation solved live for the chosen index, scaled to a
// star, the index inferred from the luminosity, a Monte Carlo over the quoted uncertainties
// and a MESA model overlaid on the polytrope. The numerics live in polytrope-core.js; this
// file reads the controls and draws on canvases with the site's colour tokens, which are read
// again whenever the theme changes. The data load when the playground nears the viewport.
import { N_MAX, NODES, ANALYTIC, Grid, model, drawValue, quantile, solveLaneEmden } from "./polytrope-core.js";

const MINUS = "−";
const SUN = "☉";
const MC_MAX = 2000;
const FRAME_BUDGET_MS = 9;
const LOG_FLOOR = { rho: 1e-6, T: 3e3, P: 1e4, eps: 1e-4 };
const motion = matchMedia("(prefers-reduced-motion: reduce)");

const root = document.getElementById("pt-playground");
if (root) {
  const start = () => boot(root).catch((err) => {
    console.error(err);
    const state = root.querySelector(".pg-state");
    state.classList.add("is-alert");
    state.textContent = "The star data could not be loaded, so the playground cannot run here.";
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
const SUP = { "-": "⁻", 0: "⁰", 1: "¹", 2: "²", 3: "³", 4: "⁴", 5: "⁵", 6: "⁶", 7: "⁷", 8: "⁸", 9: "⁹" };
const sup = (k) => String(k).split("").map((c) => SUP[c] ?? c).join("");
const pow10 = (k) => `10${sup(k)}`;
const grouped = (v) => Math.round(v).toLocaleString("en-GB");
const neg = (s) => s.replace("-", MINUS);
// 2.07 × 10¹⁷ for large or small numbers, plain digits in between.
function sci(v, digits = 3) {
  if (!Number.isFinite(v)) return "n/a";
  if (v === 0) return "0";
  const a = Math.abs(v);
  if (a >= 0.01 && a < 1e4) return neg(String(Number(v.toPrecision(digits))));
  const k = Math.floor(Math.log10(a));
  const m = v / 10 ** k;
  return `${neg(m.toFixed(digits - 1))} × ${pow10(k)}`;
}
const fixed = (v, d) => neg(v.toFixed(d));
const lumText = (v) => (v >= 1e-3 && v < 1e4 ? neg(v.toPrecision(4)) : sci(v, 3));
function signedErr(q) {
  if (q.plus !== undefined) return `+${q.plus} ${MINUS}${q.minus}`;
  if (q.sigma_dex !== undefined) return `± ${q.sigma_dex} dex`;
  if (q.sigma !== undefined) return `± ${q.sigma}`;
  return "";
}

// ---------------------------------------------------------------- colour and canvas
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
    s.ctx.setLineDash([]);
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

// A log axis between lo and hi: integer decades, thinned so that labels stay apart.
function decades(lo, hi, maxLabels) {
  const k0 = Math.ceil(Math.log10(lo) - 1e-9);
  const k1 = Math.floor(Math.log10(hi) + 1e-9);
  const every = Math.max(1, Math.ceil((k1 - k0 + 1) / maxLabels));
  const out = [];
  for (let k = k0; k <= k1; k++) out.push({ v: 10 ** k, label: (k - k0) % every === 0 });
  return out;
}

// Draw a polyline from (x, y) samples, skipping points outside the y range.
function polyline(ctx, xs, ys, X, Y, lo) {
  ctx.beginPath();
  let on = false;
  for (let i = 0; i < xs.length; i++) {
    const y = ys[i];
    if (!(y > lo)) {
      on = false;
      continue;
    }
    const px = X(xs[i]);
    const py = Y(y);
    if (on) ctx.lineTo(px, py);
    else ctx.moveTo(px, py);
    on = true;
  }
  ctx.stroke();
}

// ---------------------------------------------------------------- the playground
async function boot(root) {
  const $ = (sel) => root.querySelector(sel);
  const T = siteTokens();
  const params = new URLSearchParams(location.search);

  const ui = {
    star: $(".pt-star"),
    draw: $(".pt-draw"),
    reset: $(".pt-reset"),
    live: $(".pg-live"),
    nstar: $(".pt-nstar"),
    lmodel: $(".pt-lmodel"),
    state: $(".pg-state"),
    obs: $(".pt-obs"),
    form: $(".pt-settings"),
    facts: $(".pt-facts"),
    check: $(".pt-check"),
    share: $(".pt-share"),
    mcKey: $(".pt-mc-key"),
    curveKey: $(".pt-curve-key"),
    mainKeys: root.querySelectorAll(".pt-main-key"),
    mainTip: $(".pt-main .pg-tip"),
    curveTip: $(".pt-curve .pg-tip"),
  };
  const cv = {
    main: surface($(".pt-main canvas")),
    curve: surface($(".pt-curve canvas")),
    hist: surface($(".pt-hist canvas")),
    theta: surface($(".pt-theta canvas")),
    eps: surface($(".pt-eps canvas")),
  };
  const sliders = {};
  for (const name of ["n", "M", "R", "X", "Z"]) {
    const input = ui.form.elements[name];
    sliders[name] = { input, out: input.closest(".pt-slider").querySelector("output") };
  }

  const [starsFile, mesaFile] = await Promise.all([
    fetch(root.dataset.stars).then((r) => r.json()),
    fetch(root.dataset.mesa).then((r) => r.json()),
  ]);
  const stars = starsFile.stars;
  const mesa = {
    x: mesaFile.arrays.x,
    rho: mesaFile.arrays.logRho.map((v) => 10 ** v),
    T: mesaFile.arrays.logT.map((v) => 10 ** v),
    P: mesaFile.arrays.logP.map((v) => 10 ** v),
    eps: mesaFile.arrays.eps_nuc,
    h1: mesaFile.arrays.h1,
    convBase: mesaFile.model.convective_envelope_base_x,
    age: mesaFile.model.star_age,
  };

  // ------------------------------------------------------------ state
  const grid = new Grid();
  let star = null;
  let P = { M: 1, R: 1, X: 0.7381, Z: 0.0134 };
  let n = 3;
  let Lobs = 1;
  let nStar = null;
  let cur = null;
  let curveData = null; // [n, L] on the coarse grid for the current P
  let C = null;
  let F = null;
  let checks = null;
  let hoverU = -1;
  let hoverN = NaN;
  let raf = 0;
  let mcRaf = 0;
  let resumeOnShow = false;
  const mc = { draws: [], fails: 0, running: false, guess: NaN, stats: null };
  const dirty = { main: true, curve: true, hist: true, theta: true, eps: true };
  const overlayOn = () => Boolean(star && star.mesa_overlay);
  const hasErrors = () => Boolean(star && (star.M.sigma || star.M.plus || star.R.sigma || star.L.sigma || star.L.sigma_dex));

  function readTheme() {
    const c = (name) => T.colour(name);
    C = {
      surface: c("--surface"), surface2: c("--surface-2"), line: c("--line"), lineStrong: c("--line-strong"),
      ink: c("--ink"), ink2: c("--ink-2"), muted: c("--muted"), accent: c("--accent"), accent2: c("--accent-2"),
      accentSoft: c("--accent-soft"),
    };
    const cs = getComputedStyle(document.documentElement);
    F = { mono: cs.getPropertyValue("--mono").trim() || "monospace", sans: cs.getPropertyValue("--sans").trim() || "sans-serif" };
  }

  function markAll() {
    for (const key in dirty) dirty[key] = true;
    schedule();
  }

  // Solve the whole grid once, in slices, so the page stays responsive meanwhile.
  async function warmGrid() {
    for (let i = 0; i < grid.count; i++) {
      grid.at(i);
      if (i % 40 === 39) await new Promise((r) => setTimeout(r, 0));
    }
  }

  // ------------------------------------------------------------ the model for the controls
  function recompute(fromSliders = false) {
    const guess = fromSliders && nStar !== null ? nStar : NaN;
    nStar = grid.indexAt(Lobs, P, guess);
    cur = model(grid.solution(n), P);
    curveData = null;
    updateReadout();
    updateFacts();
    for (const key of ["main", "curve", "theta", "eps"]) dirty[key] = true;
    schedule();
  }

  function setSlider(name, value) {
    const s = sliders[name];
    s.input.value = String(value);
    s.out.textContent = sliderText(name, Number(s.input.value));
  }

  function sliderText(name, v) {
    if (name === "n") return v.toFixed(2);
    if (name === "Z") return v.toFixed(3);
    return v.toFixed(2);
  }

  function readSliders() {
    n = Number(sliders.n.input.value);
    for (const k of ["M", "R", "X", "Z"]) P[k] = Number(sliders[k].input.value);
    for (const k in sliders) sliders[k].out.textContent = sliderText(k, Number(sliders[k].input.value));
  }

  // ------------------------------------------------------------ stars
  function option(value, text) {
    const o = document.createElement("option");
    o.value = value;
    o.textContent = text;
    return o;
  }

  function setStar(id) {
    star = stars.find((s) => s.id === id) ?? stars[0];
    ui.star.querySelector('option[value="custom"]')?.remove();
    ui.star.value = star.id;
    P = { M: star.M.value, R: star.R.value, X: star.X, Z: star.Z };
    Lobs = star.L.log10 !== undefined ? 10 ** star.L.log10 : star.L.value;
    for (const k of ["M", "R", "X", "Z"]) setSlider(k, P[k]);
    nStar = grid.indexAt(Lobs, P);
    n = nStar === null ? 3 : Math.round(nStar * 100) / 100;
    setSlider("n", n);
    resetMC();
    cur = model(grid.solution(n), P);
    curveData = null;
    updateObs();
    updateReadout();
    updateFacts();
    updateKeys();
    markAll();
  }

  function markCustom() {
    if (ui.star.value === "custom") return;
    ui.star.append(option("custom", `Custom values near ${star.name}`));
    ui.star.value = "custom";
  }

  function updateObs() {
    const q = (k, v) => (v.short ? (v.short.startsWith("log") ? v.short : `${k} ${v.short}`) : `${k} ${v.value}`);
    const feh = star.feh && star.feh.value !== undefined ? ` · [Fe/H] ${star.feh.value >= 0 ? "+" : MINUS}${Math.abs(star.feh.value)}` : "";
    ui.obs.textContent = `${q("M", star.M)} · ${q("R", star.R)} · ${q("L", star.L)}${feh}`;
  }

  // ------------------------------------------------------------ readouts
  function updateReadout() {
    ui.nstar.textContent = nStar === null ? "none" : fixed(nStar, 3);
    ui.lmodel.textContent = lumText(cur.LsunModel);
    if (mc.running) ui.state.textContent = "Drawing.";
    else if (!hasErrors()) ui.state.textContent = star.id === "mesa" ? "A model has no measurement errors, so there is nothing to draw." : "Nominal values carry no uncertainties; choose 61 Vir or GJ 504 to draw.";
    else if (mc.draws.length >= MC_MAX) ui.state.textContent = `Stopped after ${grouped(MC_MAX)} draws. Press Reset to start again.`;
    else if (mc.draws.length) ui.state.textContent = "Paused.";
    else ui.state.textContent = nStar === null ? "The model luminosity never reaches the observed one below n = 4.9." : "Press Draw to sample M, R and L from their uncertainties.";
    ui.state.classList.toggle("is-alert", nStar === null);
    ui.live.setAttribute("aria-busy", mc.running ? "true" : "false");
    ui.draw.disabled = !hasErrors() || nStar === null || (!mc.running && mc.draws.length >= MC_MAX);
    ui.draw.textContent = mc.running ? "Pause" : "Draw";
    ui.reset.disabled = !mc.draws.length && !mc.running;
    updateMCKey();
  }

  function updateMCKey() {
    const s = mc.stats;
    ui.mcKey.textContent = !s ? "no draws yet" : `${grouped(s.count)} draws · median ${fixed(s.median, 3)} · 68 % ${fixed(s.lo, 3)} to ${fixed(s.hi, 3)}`;
  }

  function updateKeys() {
    ui.curveKey.textContent = `L obs ${sci(Lobs, 4)} L${SUN}`;
    for (const el of ui.mainKeys) el.hidden = !overlayOn();
  }

  function updateFacts() {
    const { sol, scaled, lum } = cur;
    const pp = lum.L > 0 ? (100 * lum.Lpp) / lum.L : 0;
    const head = document.createElement("b");
    head.textContent = `n = ${fixed(n, 2)}`;
    const rest = ` · ξ₁ = ${fixed(sol.xi1, 4)} · ${MINUS}ξ₁²θ′(ξ₁) = ${fixed(sol.mr, 4)} · ρc = ${sci(scaled.rhoC)} g cm${sup(-3)} (${sci(scaled.rhoC / scaled.rhoMean)} ρ̄) · Tc = ${sci(scaled.TC / 1e6)} MK · Pc = ${sci(scaled.PC)} dyn cm${sup(-2)} · μ = ${fixed(scaled.mu, 3)} · L model = ${sci(cur.LsunModel)} L${SUN}`;
    ui.facts.replaceChildren(head, document.createTextNode(rest));
    ui.share.textContent = `At n = ${fixed(n, 2)} the pp chain gives ${fixed(pp, 1)} % of the model luminosity and the CNO cycle ${fixed(100 - pp, 1)} %.`;
    cv.main.canvas.setAttribute("aria-label", `Density, temperature, pressure and energy generation against fractional radius for the polytrope of index ${fixed(n, 2)}${overlayOn() ? " and for the MESA model" : ""}: central density ${sci(scaled.rhoC)} g per cubic centimetre, central temperature ${sci(scaled.TC / 1e6)} million kelvin.`);
  }

  // ------------------------------------------------------------ controls
  ui.star.addEventListener("change", () => {
    if (ui.star.value === "custom") return;
    stopMC();
    setStar(ui.star.value);
  });
  ui.form.addEventListener("submit", (e) => e.preventDefault());
  ui.form.addEventListener("input", (e) => {
    const name = e.target.name;
    readSliders();
    if (name === "n") {
      cur = model(grid.solution(n), P);
      updateReadout();
      updateFacts();
      dirty.main = dirty.curve = dirty.theta = dirty.eps = dirty.hist = true;
      schedule();
      return;
    }
    markCustom();
    stopMC();
    resetMC();
    recompute(true);
    dirty.hist = true;
  });
  ui.draw.addEventListener("click", () => (mc.running ? stopMC() : startMC()));
  ui.reset.addEventListener("click", () => {
    stopMC();
    resetMC();
    updateReadout();
    dirty.hist = true;
    schedule();
  });
  document.addEventListener("visibilitychange", () => {
    if (document.hidden && mc.running) {
      resumeOnShow = true;
      stopMC();
    } else if (!document.hidden && resumeOnShow) {
      resumeOnShow = false;
      startMC();
    }
  });

  // ------------------------------------------------------------ Monte Carlo
  function resetMC() {
    mc.draws = [];
    mc.fails = 0;
    mc.stats = null;
    mc.guess = NaN;
    updateMCKey();
  }

  function sample(q, centre) {
    if (q.sigma_dex !== undefined) return 10 ** (Math.log10(centre) + q.sigma_dex * drawValue({ value: 0, sigma: 1 }));
    return drawValue({ ...q, value: centre });
  }

  function oneDraw() {
    const s = { X: P.X, Z: P.Z, M: sample(star.M, P.M), R: sample(star.R, P.R) };
    const L = sample(star.L, Lobs);
    const v = grid.indexAt(L, s, Number.isFinite(mc.guess) ? mc.guess : nStar);
    if (v === null || !(s.M > 0) || !(s.R > 0) || !(L > 0)) {
      mc.fails++;
      return;
    }
    mc.draws.push(v);
    mc.guess = v;
  }

  function updateStats() {
    if (!mc.draws.length) {
      mc.stats = null;
      return;
    }
    const sorted = mc.draws.slice().sort((a, b) => a - b);
    mc.stats = { count: sorted.length, sorted, median: quantile(sorted, 0.5), lo: quantile(sorted, 0.16), hi: quantile(sorted, 0.84) };
  }

  function startMC() {
    if (!hasErrors() || nStar === null || mc.draws.length >= MC_MAX) return;
    mc.running = true;
    updateReadout();
    if (motion.matches) {
      // Reduced motion: the draws run in slices and the picture appears once, at the end.
      const slice = () => {
        if (!mc.running) return;
        const t0 = performance.now();
        while (performance.now() - t0 < 24 && mc.draws.length + mc.fails < MC_MAX) oneDraw();
        if (mc.draws.length + mc.fails < MC_MAX) {
          mcRaf = setTimeout(slice, 0);
          return;
        }
        finishMC();
      };
      mcRaf = setTimeout(slice, 0);
      return;
    }
    const frame = () => {
      if (!mc.running) return;
      const t0 = performance.now();
      while (performance.now() - t0 < FRAME_BUDGET_MS && mc.draws.length + mc.fails < MC_MAX) oneDraw();
      updateStats();
      updateMCKey();
      dirty.hist = true;
      schedule();
      if (mc.draws.length + mc.fails < MC_MAX) mcRaf = requestAnimationFrame(frame);
      else finishMC();
    };
    mcRaf = requestAnimationFrame(frame);
  }

  function finishMC() {
    mc.running = false;
    updateStats();
    updateReadout();
    dirty.hist = true;
    schedule();
  }

  function stopMC() {
    if (!mc.running) return;
    mc.running = false;
    cancelAnimationFrame(mcRaf);
    clearTimeout(mcRaf);
    updateStats();
    updateReadout();
    dirty.hist = true;
    schedule();
  }

  // ------------------------------------------------------------ the structure figure
  const PANELS = [
    { key: "rho", title: "Density", unit: `g cm${sup(-3)}` },
    { key: "T", title: "Temperature", unit: "K" },
    { key: "P", title: "Pressure", unit: `dyn cm${sup(-2)}` },
    { key: "eps", title: "Energy generation", unit: `erg g${sup(-1)} s${sup(-1)}` },
  ];

  // Polytrope profiles on the NODES + 1 samples, as physical values.
  function profiles() {
    const { sol, scaled, lum } = cur;
    const u = Array.from({ length: NODES + 1 }, (_, i) => i / NODES);
    const rho = u.map((_, i) => scaled.rhoC * sol.thn[i]);
    const T = u.map((_, i) => scaled.TC * sol.theta[i]);
    const Pr = u.map((_, i) => scaled.PC * (n === 0 ? sol.theta[i] : sol.theta[i] ** (n + 1)));
    const eps = u.map((_, i) => lum.pp[i] + lum.cno[i]);
    return { u, rho, T, P: Pr, eps };
  }

  function mainLayout() {
    const s = cv.main;
    const cols = s.w < 520 ? 1 : 2;
    const rows = PANELS.length / cols;
    const gapX = 26;
    const gapY = 14;
    const m = { l: 46, r: 12, t: 24, b: 24 };
    const pw = (s.w - gapX * (cols - 1)) / cols;
    const ph = (s.h - gapY * (rows - 1)) / rows;
    return PANELS.map((p, i) => {
      const c = i % cols;
      const r = Math.floor(i / cols);
      const x0 = c * (pw + gapX) + m.l;
      const y0 = r * (ph + gapY) + m.t;
      const w = pw - m.l - m.r;
      const h = ph - m.t - m.b;
      return { ...p, x0, y0, w, h, X: (u) => x0 + u * w };
    });
  }

  function drawMain() {
    const s = cv.main;
    const ctx = s.begin();
    if (!cur || s.w < 80) return;
    const pr = profiles();
    const L = mainLayout();
    const overlay = overlayOn();
    ctx.font = `11px ${F.mono}`;
    ctx.lineWidth = 1;
    for (const p of L) {
      const poly = pr[p.key];
      const mes = mesa[p.key];
      const lo = LOG_FLOOR[p.key];
      let top = poly[0];
      if (overlay) for (const v of mes) top = Math.max(top, v);
      const hi = top * 2.5;
      const Y = (v) => p.y0 + p.h - ((Math.log10(v) - Math.log10(lo)) / (Math.log10(hi) - Math.log10(lo))) * p.h;
      // frame, ticks
      ctx.strokeStyle = C.line;
      ctx.fillStyle = C.muted;
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";
      for (const t of decades(lo, hi, 6)) {
        const y = Math.round(Y(t.v)) + 0.5;
        line(ctx, p.x0, y, p.x0 + p.w, y);
        if (t.label) ctx.fillText(pow10(Math.round(Math.log10(t.v))), p.x0 - 6, y);
      }
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      for (const u of [0, 0.25, 0.5, 0.75, 1]) {
        const x = Math.round(p.X(u)) + 0.5;
        ctx.strokeStyle = C.line;
        line(ctx, x, p.y0, x, p.y0 + p.h);
        ctx.fillText(u === 0 ? "0" : u === 1 ? "1" : String(u), x, p.y0 + p.h + 6);
      }
      ctx.strokeStyle = C.lineStrong;
      line(ctx, p.x0 + 0.5, p.y0, p.x0 + 0.5, p.y0 + p.h);
      line(ctx, p.x0, p.y0 + p.h + 0.5, p.x0 + p.w, p.y0 + p.h + 0.5);
      // the convective envelope of the model
      if (overlay) {
        ctx.fillStyle = C.accentSoft;
        ctx.fillRect(p.X(mesa.convBase), p.y0, p.w - (p.X(mesa.convBase) - p.x0), p.h);
      }
      // titles
      ctx.textAlign = "left";
      ctx.textBaseline = "alphabetic";
      ctx.fillStyle = C.ink;
      ctx.font = `600 12px ${F.sans}`;
      ctx.fillText(p.title, p.x0, p.y0 - 9);
      const tw = ctx.measureText(p.title).width;
      ctx.fillStyle = C.muted;
      ctx.font = `11px ${F.mono}`;
      ctx.fillText(p.unit, p.x0 + tw + 8, p.y0 - 9);
      ctx.textAlign = "right";
      ctx.fillText("r / R", p.x0 + p.w, p.y0 - 9);
      // MESA marks
      if (overlay) {
        ctx.fillStyle = C.ink2;
        ctx.globalAlpha = 0.85;
        for (let i = 0; i < mesa.x.length; i++) {
          if (!(mes[i] > lo)) continue;
          dot(ctx, p.X(mesa.x[i]), Y(mes[i]), 2);
        }
        ctx.globalAlpha = 1;
      }
      // the polytrope
      ctx.save();
      ctx.beginPath();
      ctx.rect(p.x0 - 1, p.y0 - 1, p.w + 2, p.h + 2);
      ctx.clip();
      ctx.strokeStyle = C.accent;
      ctx.lineWidth = 2;
      ctx.lineJoin = "round";
      polyline(ctx, pr.u, poly, p.X, Y, lo);
      ctx.restore();
      ctx.lineWidth = 1;
      // the cursor
      if (hoverU >= 0) {
        ctx.strokeStyle = C.lineStrong;
        const x = Math.round(p.X(hoverU)) + 0.5;
        line(ctx, x, p.y0, x, p.y0 + p.h);
        const i = Math.round(hoverU * NODES);
        if (poly[i] > lo) {
          ctx.fillStyle = C.surface;
          dot(ctx, p.X(hoverU), Y(poly[i]), 5);
          ctx.fillStyle = C.accent;
          dot(ctx, p.X(hoverU), Y(poly[i]), 3.2);
        }
      }
      if (overlay && p.key === "rho") {
        ctx.fillStyle = C.muted;
        ctx.font = `11px ${F.mono}`;
        ctx.textAlign = "right";
        ctx.textBaseline = "top";
        ctx.fillText("convective", p.x0 + p.w - 4, p.y0 + 4);
        ctx.fillText("in MESA", p.x0 + p.w - 4, p.y0 + 17);
      }
      ctx.textBaseline = "alphabetic";
    }
  }

  function nearestZone(u) {
    let best = 0;
    let bd = Infinity;
    for (let i = 0; i < mesa.x.length; i++) {
      const d = Math.abs(mesa.x[i] - u);
      if (d < bd) {
        bd = d;
        best = i;
      }
    }
    return best;
  }

  function mainHover(e) {
    if (!cur) return;
    const rect = cv.main.canvas.getBoundingClientRect();
    const L = mainLayout();
    const p = L[0];
    const col = L.find((q) => e.clientX - rect.left >= q.x0 - 46 && e.clientX - rect.left <= q.x0 + q.w + 12) ?? p;
    const u = Math.min(1, Math.max(0, (e.clientX - rect.left - col.x0) / col.w));
    hoverU = u;
    const i = Math.round(u * NODES);
    const pr = profiles();
    const rows = [
      [`r / R = ${fixed(u, 3)}`],
      [`polytrope ρ ${sci(pr.rho[i])}, T ${sci(pr.T[i])}, P ${sci(pr.P[i])}, ε ${sci(pr.eps[i])}`],
    ];
    if (overlayOn()) {
      const z = nearestZone(u);
      rows.push([`MESA ρ ${sci(mesa.rho[z])}, T ${sci(mesa.T[z])}, P ${sci(mesa.P[z])}, ε ${sci(mesa.eps[z])}, X ${fixed(mesa.h1[z], 3)}`]);
    }
    ui.mainTip.replaceChildren(...rows.map(([t], k) => {
      const el = document.createElement(k === 0 ? "b" : "span");
      el.textContent = t;
      return el;
    }));
    ui.mainTip.hidden = false;
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const w = ui.mainTip.offsetWidth;
    const h = ui.mainTip.offsetHeight;
    ui.mainTip.style.left = `${Math.max(0, Math.min(x + 14, cv.main.w - w - 2))}px`;
    ui.mainTip.style.top = `${y + 16 + h > cv.main.h ? y - h - 10 : y + 16}px`;
    dirty.main = true;
    schedule();
  }

  cv.main.canvas.addEventListener("pointermove", mainHover);
  cv.main.canvas.addEventListener("pointerleave", () => {
    hoverU = -1;
    ui.mainTip.hidden = true;
    dirty.main = true;
    schedule();
  });

  // ------------------------------------------------------------ L(n)
  function curveFrame() {
    const s = cv.curve;
    const m = { l: 44, r: 12, t: 18, b: 22 };
    const W = s.w - m.l - m.r;
    const H = s.h - m.t - m.b;
    const l0 = -4;
    const l1 = 4;
    return { m, W, H, X: (v) => m.l + (v / N_MAX) * W, Y: (L) => m.t + (1 - (Math.log10(L) - l0) / (l1 - l0)) * H, l0, l1 };
  }

  function ensureCurve() {
    if (curveData) return curveData;
    curveData = [];
    for (let i = 0; i < grid.count; i += 5) curveData.push([i * grid.step, grid.lumAt(i, P)]);
    if ((grid.count - 1) % 5) curveData.push([(grid.count - 1) * grid.step, grid.lumAt(grid.count - 1, P)]);
    return curveData;
  }

  function drawCurve() {
    const s = cv.curve;
    const ctx = s.begin();
    if (!cur || s.w < 80) return;
    const f = curveFrame();
    const data = ensureCurve();
    ctx.font = `11px ${F.mono}`;
    ctx.lineWidth = 1;
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (let k = f.l0; k <= f.l1; k += 2) {
      const y = Math.round(f.Y(10 ** k)) + 0.5;
      ctx.strokeStyle = C.line;
      line(ctx, f.m.l, y, f.m.l + f.W, y);
      ctx.fillStyle = C.muted;
      ctx.fillText(pow10(k), f.m.l - 6, y);
    }
    ctx.strokeStyle = C.lineStrong;
    const base = f.m.t + f.H + 0.5;
    line(ctx, f.m.l, base, f.m.l + f.W, base);
    line(ctx, f.m.l + 0.5, f.m.t, f.m.l + 0.5, base);
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    for (let v = 0; v <= 4; v++) ctx.fillText(String(v), f.X(v), base + 6);
    ctx.textAlign = "left";
    ctx.fillStyle = C.muted;
    ctx.fillText("n", f.X(N_MAX) - 6, base + 6);
    ctx.textBaseline = "alphabetic";
    ctx.fillText(`L model / L${SUN}`, f.m.l - 38, f.m.t - 7);
    // the observed luminosity
    ctx.save();
    ctx.beginPath();
    ctx.rect(f.m.l, f.m.t - 1, f.W, f.H + 2);
    ctx.clip();
    ctx.setLineDash([4, 3]);
    ctx.strokeStyle = C.ink2;
    const yObs = Math.round(f.Y(Lobs)) + 0.5;
    line(ctx, f.m.l, yObs, f.m.l + f.W, yObs);
    ctx.setLineDash([]);
    // the slider's n
    ctx.strokeStyle = C.lineStrong;
    const xn = Math.round(f.X(n)) + 0.5;
    line(ctx, xn, f.m.t, xn, f.m.t + f.H);
    // the curve
    ctx.strokeStyle = C.accent;
    ctx.lineWidth = 2;
    ctx.lineJoin = "round";
    ctx.beginPath();
    let on = false;
    for (const [nv, L] of data) {
      if (!(L > 0)) continue;
      const x = f.X(nv);
      const y = f.Y(L);
      if (on) ctx.lineTo(x, y);
      else ctx.moveTo(x, y);
      on = true;
    }
    ctx.stroke();
    ctx.lineWidth = 1;
    // the root and the slider's point
    if (nStar !== null) {
      ctx.fillStyle = C.surface;
      dot(ctx, f.X(nStar), f.Y(Lobs), 6);
      ctx.fillStyle = C.accent;
      dot(ctx, f.X(nStar), f.Y(Lobs), 4);
    }
    if (cur.LsunModel > 0) {
      ctx.fillStyle = C.surface;
      dot(ctx, f.X(n), f.Y(cur.LsunModel), 5);
      ctx.fillStyle = C.ink;
      dot(ctx, f.X(n), f.Y(cur.LsunModel), 3);
    }
    ctx.restore();
    if (nStar !== null) {
      ctx.fillStyle = C.ink;
      ctx.font = `500 11px ${F.mono}`;
      ctx.textBaseline = "bottom";
      const label = `n = ${fixed(nStar, 3)} at L obs`;
      const lw = ctx.measureText(label).width;
      const lx = f.X(nStar) + 8 + lw > f.m.l + f.W ? f.X(nStar) - 8 - lw : f.X(nStar) + 8;
      ctx.textAlign = "left";
      ctx.fillText(label, lx, Math.max(f.m.t + 11, f.Y(Lobs) - 7));
    }
    if (Number.isFinite(hoverN)) {
      ctx.strokeStyle = C.lineStrong;
      const x = Math.round(f.X(hoverN)) + 0.5;
      line(ctx, x, f.m.t, x, f.m.t + f.H);
    }
  }

  cv.curve.canvas.addEventListener("pointermove", (e) => {
    if (!cur) return;
    const rect = cv.curve.canvas.getBoundingClientRect();
    const f = curveFrame();
    const v = Math.min(N_MAX, Math.max(0, ((e.clientX - rect.left - f.m.l) / f.W) * N_MAX));
    hoverN = Math.round(v * 100) / 100;
    const L = grid.lumAt(Math.round(hoverN / grid.step), P);
    ui.curveTip.replaceChildren();
    const head = document.createElement("b");
    head.textContent = `n = ${fixed(hoverN, 2)}`;
    const a = document.createElement("span");
    a.textContent = `L model ${sci(L)} L${SUN}`;
    ui.curveTip.append(head, a);
    ui.curveTip.hidden = false;
    const w = ui.curveTip.offsetWidth;
    ui.curveTip.style.left = `${Math.max(0, Math.min(f.X(hoverN) + 12, cv.curve.w - w - 4))}px`;
    ui.curveTip.style.top = `${f.m.t + 2}px`;
    dirty.curve = true;
    schedule();
  });
  cv.curve.canvas.addEventListener("pointerleave", () => {
    hoverN = NaN;
    ui.curveTip.hidden = true;
    dirty.curve = true;
    schedule();
  });
  cv.curve.canvas.addEventListener("click", () => {
    if (!Number.isFinite(hoverN)) return;
    n = hoverN;
    setSlider("n", n);
    cur = model(grid.solution(n), P);
    updateReadout();
    updateFacts();
    dirty.main = dirty.curve = dirty.theta = dirty.eps = dirty.hist = true;
    schedule();
  });

  // ------------------------------------------------------------ the histogram
  function drawHist() {
    const s = cv.hist;
    const ctx = s.begin();
    if (s.w < 80) return;
    const m = { l: 14, r: 14, t: 30, b: 24 };
    const W = s.w - m.l - m.r;
    const H = s.h - m.t - m.b;
    ctx.font = `11px ${F.mono}`;
    ctx.lineWidth = 1;
    const st = mc.stats;
    if (!st) {
      ctx.fillStyle = C.muted;
      ctx.font = `500 12px ${F.sans}`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      const msg = !star ? "" : !hasErrors() ? (star.id === "mesa" ? "A model carries no uncertainties." : "Nominal values carry no uncertainties.") : nStar === null ? "No index matches this luminosity." : "Press Draw to start.";
      ctx.fillText(msg, m.l + W / 2, m.t + H / 2);
      return;
    }
    const sorted = st.sorted;
    const q = (p) => quantile(sorted, p);
    const span = Math.max(0.02, q(0.995) - q(0.005));
    const binW = [0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1].find((b) => span / b <= 36) ?? 0.1;
    const x0 = Math.floor((q(0.005) - span * 0.12) / binW) * binW;
    const x1 = Math.ceil((q(0.995) + span * 0.12) / binW) * binW;
    const nb = Math.max(1, Math.round((x1 - x0) / binW));
    const counts = new Array(nb).fill(0);
    for (const v of sorted) {
      const b = Math.floor((v - x0) / binW);
      if (b >= 0 && b < nb) counts[b]++;
    }
    const peak = Math.max(1, ...counts);
    const X = (v) => m.l + ((v - x0) / (x1 - x0)) * W;
    const Y = (c) => m.t + H - (c / peak) * H;
    ctx.strokeStyle = C.lineStrong;
    const base = m.t + H + 0.5;
    line(ctx, m.l, base, m.l + W, base);
    // bars
    ctx.fillStyle = C.accent;
    ctx.globalAlpha = 0.75;
    for (let b = 0; b < nb; b++) {
      if (!counts[b]) continue;
      const xa = X(x0 + b * binW);
      const xb = X(x0 + (b + 1) * binW);
      ctx.fillRect(xa + 0.5, Y(counts[b]), Math.max(1, xb - xa - 1), base - Y(counts[b]));
    }
    ctx.globalAlpha = 1;
    // x ticks
    ctx.fillStyle = C.muted;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    const tickStep = [0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5].find((t) => (x1 - x0) / t <= 7) ?? 0.5;
    const dec = tickStep < 0.01 ? 3 : 2;
    for (let v = Math.ceil(x0 / tickStep) * tickStep; v <= x1 + 1e-9; v += tickStep) {
      const x = Math.round(X(v)) + 0.5;
      ctx.strokeStyle = C.line;
      line(ctx, x, base, x, base + 3);
      ctx.fillText(fixed(v, dec), x, base + 6);
    }
    ctx.textAlign = "right";
    ctx.fillText("n", m.l + W, base + 6);
    // median and the 68 percent interval
    ctx.setLineDash([3, 3]);
    ctx.strokeStyle = C.ink2;
    for (const v of [st.lo, st.hi]) {
      const x = Math.round(X(v)) + 0.5;
      line(ctx, x, m.t - 4, x, base);
    }
    ctx.setLineDash([]);
    ctx.strokeStyle = C.ink;
    ctx.lineWidth = 1.5;
    const xm = Math.round(X(st.median)) + 0.5;
    line(ctx, xm, m.t - 6, xm, base);
    ctx.lineWidth = 1;
    ctx.font = `500 11px ${F.mono}`;
    ctx.textBaseline = "bottom";
    const yl = m.t - 13;
    const medLabel = `median ${fixed(st.median, 3)}`;
    const mw = ctx.measureText(medLabel).width;
    const xl = Math.min(m.l + W - mw / 2, Math.max(m.l + mw / 2, xm));
    ctx.fillStyle = C.ink;
    ctx.textAlign = "center";
    ctx.fillText(medLabel, xl, yl);
    ctx.fillStyle = C.ink2;
    ctx.textAlign = "right";
    ctx.fillText(fixed(st.lo, 3), Math.min(xl - mw / 2 - 8, Math.round(X(st.lo)) - 4), yl);
    ctx.textAlign = "left";
    ctx.fillText(fixed(st.hi, 3), Math.max(xl + mw / 2 + 8, Math.round(X(st.hi)) + 4), yl);
    // the no-uncertainty root as a marker
    if (nStar !== null && nStar >= x0 && nStar <= x1) {
      ctx.fillStyle = C.accent2;
      const x = X(nStar);
      ctx.beginPath();
      ctx.moveTo(x, base - 1);
      ctx.lineTo(x - 5, base + 8);
      ctx.lineTo(x + 5, base + 8);
      ctx.closePath();
      ctx.fill();
    }
  }

  // ------------------------------------------------------------ theta(xi)
  function drawTheta() {
    const s = cv.theta;
    const ctx = s.begin();
    if (!cur || s.w < 80) return;
    const m = { l: 36, r: 46, t: 10, b: 24 };
    const W = s.w - m.l - m.r;
    const H = s.h - m.t - m.b;
    const xi1 = cur.sol.xi1;
    const xmax = Math.max(4, Math.min(xi1 * 1.04, 25));
    const X = (xi) => m.l + (xi / xmax) * W;
    const Y = (th) => m.t + H - ((th + 0.05) / 1.07) * H;
    ctx.font = `11px ${F.mono}`;
    ctx.lineWidth = 1;
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (const t of [0, 0.5, 1]) {
      const y = Math.round(Y(t)) + 0.5;
      ctx.strokeStyle = t === 0 ? C.lineStrong : C.line;
      line(ctx, m.l, y, m.l + W, y);
      ctx.fillStyle = C.muted;
      ctx.fillText(String(t), m.l - 6, y);
    }
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    const step = xmax > 12 ? 5 : xmax > 6 ? 2 : 1;
    for (let v = 0; v <= xmax; v += step) {
      const x = Math.round(X(v)) + 0.5;
      ctx.strokeStyle = C.line;
      line(ctx, x, m.t, x, m.t + H);
      ctx.fillStyle = C.muted;
      ctx.fillText(String(v), x, m.t + H + 6);
    }
    ctx.textAlign = "left";
    ctx.fillText("ξ", m.l + W + 8, m.t + H + 6);
    ctx.save();
    ctx.beginPath();
    ctx.rect(m.l, m.t - 2, W + m.r, H + 4);
    ctx.clip();
    // analytic references
    ctx.strokeStyle = C.muted;
    ctx.lineWidth = 1;
    ctx.font = `11px ${F.mono}`;
    ctx.textBaseline = "bottom";
    for (const k of [0, 1, 5]) {
      const a = ANALYTIC[k];
      const end = Math.min(xmax, a.xi1);
      ctx.beginPath();
      for (let i = 0; i <= 200; i++) {
        const xi = (i / 200) * end;
        const y = Y(a.theta(xi));
        if (i) ctx.lineTo(X(xi), y);
        else ctx.moveTo(X(xi), y);
      }
      ctx.stroke();
      ctx.fillStyle = C.muted;
      if (k === 5) {
        ctx.textAlign = "right";
        ctx.fillText("n = 5", X(end) - 2, Y(a.theta(end)) - 3);
      } else {
        // n = 0 to the left of its zero, n = 1 to the right of its zero
        ctx.textAlign = k === 0 ? "right" : "left";
        ctx.fillText(`n = ${k}`, X(end) + (k === 0 ? -5 : 5), Y(0) - 4);
      }
    }
    // the current n
    ctx.strokeStyle = C.accent;
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (let i = 0; i <= NODES; i++) {
      const xi = (i / NODES) * xi1;
      if (i) ctx.lineTo(X(xi), Y(cur.sol.theta[i]));
      else ctx.moveTo(X(xi), Y(cur.sol.theta[i]));
    }
    ctx.stroke();
    ctx.lineWidth = 1;
    const xe = X(Math.min(xi1, xmax));
    ctx.fillStyle = C.surface;
    dot(ctx, xe, Y(0), 5);
    ctx.fillStyle = C.accent;
    dot(ctx, xe, Y(0), 3.2);
    ctx.fillStyle = C.ink;
    ctx.font = `500 11px ${F.mono}`;
    ctx.textBaseline = "bottom";
    if (xi1 > xmax) {
      ctx.textAlign = "right";
      ctx.fillText(`n = ${fixed(n, 2)}, ξ₁ = ${fixed(xi1, 1)} beyond the axis`, xe - 8, Y(0) - 4);
    } else {
      // keep clear of the n = 1 label when the two surfaces are close
      const nearOne = xe >= X(ANALYTIC[1].xi1) - 6 && xe - X(ANALYTIC[1].xi1) < 70;
      ctx.textAlign = "left";
      ctx.fillText(`n = ${fixed(n, 2)}`, xe + 7, nearOne ? Y(0.2) - 4 : Y(0) - 4);
    }
    ctx.restore();
    ctx.fillStyle = C.muted;
    ctx.font = `11px ${F.mono}`;
    ctx.textAlign = "left";
    ctx.textBaseline = "alphabetic";
    ctx.fillText("θ", 6, m.t + 4);
  }

  // ------------------------------------------------------------ energy generation
  function drawEps() {
    const s = cv.eps;
    const ctx = s.begin();
    if (!cur || s.w < 80) return;
    const m = { l: 46, r: 34, t: 18, b: 24 };
    const W = s.w - m.l - m.r;
    const H = s.h - m.t - m.b;
    const { lum } = cur;
    const lo = 1e-4;
    let top = 0;
    for (let i = 0; i <= NODES; i++) top = Math.max(top, lum.pp[i], lum.cno[i]);
    const hi = Math.max(top * 2.5, 10 * lo);
    const X = (u) => m.l + u * W;
    const Y = (v) => m.t + H - ((Math.log10(v) - Math.log10(lo)) / (Math.log10(hi) - Math.log10(lo))) * H;
    const Yf = (f) => m.t + H - f * H;
    ctx.font = `11px ${F.mono}`;
    ctx.lineWidth = 1;
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (const t of decades(lo, hi, 6)) {
      const y = Math.round(Y(t.v)) + 0.5;
      ctx.strokeStyle = C.line;
      line(ctx, m.l, y, m.l + W, y);
      if (t.label) {
        ctx.fillStyle = C.muted;
        ctx.fillText(pow10(Math.round(Math.log10(t.v))), m.l - 6, y);
      }
    }
    ctx.textAlign = "left";
    for (const f of [0, 0.5, 1]) ctx.fillText(String(f), m.l + W + 6, Math.round(Yf(f)) + 0.5);
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    for (const u of [0, 0.25, 0.5, 0.75, 1]) {
      const x = Math.round(X(u)) + 0.5;
      ctx.strokeStyle = C.line;
      line(ctx, x, m.t, x, m.t + H);
      ctx.fillStyle = C.muted;
      ctx.fillText(String(u), x, m.t + H + 6);
    }
    ctx.strokeStyle = C.lineStrong;
    line(ctx, m.l, m.t + H + 0.5, m.l + W, m.t + H + 0.5);
    ctx.textAlign = "right";
    ctx.fillText("r / R", m.l + W, m.t + H + 6);
    const u = Array.from({ length: NODES + 1 }, (_, i) => i / NODES);
    ctx.save();
    ctx.beginPath();
    ctx.rect(m.l, m.t - 1, W, H + 2);
    ctx.clip();
    ctx.lineJoin = "round";
    // cumulative luminosity and the model's hydrogen
    const total = lum.cum[NODES] || 1;
    ctx.setLineDash([4, 3]);
    ctx.strokeStyle = C.ink2;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    for (let i = 0; i <= NODES; i++) {
      const y = Yf(lum.cum[i] / total);
      if (i) ctx.lineTo(X(u[i]), y);
      else ctx.moveTo(X(u[i]), y);
    }
    ctx.stroke();
    if (overlayOn()) {
      ctx.setLineDash([1, 3]);
      ctx.strokeStyle = C.muted;
      ctx.beginPath();
      for (let i = 0; i < mesa.x.length; i++) {
        const y = Yf(mesa.h1[i]);
        if (i) ctx.lineTo(X(mesa.x[i]), y);
        else ctx.moveTo(X(mesa.x[i]), y);
      }
      ctx.stroke();
    }
    ctx.setLineDash([]);
    ctx.lineWidth = 2;
    ctx.strokeStyle = C.accent2;
    polyline(ctx, u, lum.cno, X, Y, lo);
    ctx.strokeStyle = C.accent;
    polyline(ctx, u, lum.pp, X, Y, lo);
    ctx.restore();
    ctx.lineWidth = 1;
    ctx.fillStyle = C.muted;
    ctx.font = `11px ${F.mono}`;
    ctx.textAlign = "left";
    ctx.textBaseline = "alphabetic";
    ctx.fillText(`ε (erg g${sup(-1)} s${sup(-1)})`, m.l - 40, m.t - 7);
    ctx.textAlign = "right";
    ctx.fillText("fraction", m.l + W + 30, m.t - 7);
  }

  // ------------------------------------------------------------ frame loop
  function schedule() {
    if (!raf) raf = requestAnimationFrame(frame);
  }

  function frame() {
    raf = 0;
    for (const s of Object.values(cv)) if (s.fit()) for (const key in dirty) dirty[key] = true;
    if (!C) return;
    if (dirty.main) { drawMain(); dirty.main = false; }
    if (dirty.curve) { drawCurve(); dirty.curve = false; }
    if (dirty.hist) { drawHist(); dirty.hist = false; }
    if (dirty.theta) { drawTheta(); dirty.theta = false; }
    if (dirty.eps) { drawEps(); dirty.eps = false; }
  }

  // ------------------------------------------------------------ start
  readTheme();
  checks = { 0: solveLaneEmden(0), 1: solveLaneEmden(1) };
  ui.check.textContent = `Checked against the exact solutions: n = 0 gives ξ₁ = ${fixed(checks[0].xi1, 6)} (√6 = ${fixed(Math.sqrt(6), 6)}) and n = 1 gives ${fixed(checks[1].xi1, 6)} (π = ${fixed(Math.PI, 6)}); for n = 5 the solution θ = (1 + ξ²/3)^(${MINUS}1/2) never reaches zero, so the star has no surface.`;
  ui.star.replaceChildren(...stars.map((s) => option(s.id, s.label.replace(/M_sun/g, `M${SUN}`))));
  ui.star.disabled = false;
  for (const k in sliders) sliders[k].input.disabled = false;
  const first = stars.some((s) => s.id === params.get("star")) ? params.get("star") : stars[0].id;
  setStar(first);
  root.classList.add("is-ready");
  await warmGrid();
  if (params.get("draw") === "1") startMC();

  const resize = new ResizeObserver(() => schedule());
  for (const s of Object.values(cv)) resize.observe(s.canvas);
  motion.addEventListener("change", () => markAll());
  T.onThemeChange(() => {
    readTheme();
    markAll();
  });
  document.fonts?.ready.then(() => markAll());
}
