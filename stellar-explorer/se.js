// Stellar Explorer. One star of the Sun's mass and metallicity, computed with MESA and GYRE, read
// from an HDF5 file in the browser. Every panel draws from the selected model's own stored profile
// and mode list. Plots are canvases drawn at device resolution; axis titles are KaTeX over them.
(() => {
  "use strict";

  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => Array.from(root.querySelectorAll(s));
  const TAU = Math.PI * 2;
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const lerp = (a, b, t) => a + (b - a) * t;
  const REDUCED = matchMedia("(prefers-reduced-motion: reduce)").matches;

  const PHASE = {
    PMS: ["#c084fc", "pre-main sequence"],
    ZAMS: ["#dff3ff", "zero-age main sequence"],
    MS: ["#67e8f9", "main sequence"],
    SGB: ["#fde68a", "subgiant branch"],
    RGB: ["#f87171", "red giant branch"],
    HeFlash: ["#ffffff", "helium flash"],
    HeCB: ["#fb7185", "core helium burning"],
    RC: ["#facc15", "red clump"],
    AGB: ["#fb923c", "asymptotic giant branch"],
    postAGB: ["#e2e8f0", "post-AGB"],
    WD: ["#94a3b8", "white dwarf"],
  };
  const ELL_COLOR = ["#dff3ff", "#ad93ff", "#5be8c4"];
  const CONV = "#7fdcff";
  const BURN = "#ff7a3d";
  const INK = { grid: "rgba(180,180,210,0.10)", axis: "rgba(180,180,210,0.35)", tick: "#b4b4ca", faint: "#74748c" };
  const MONO = "'Share Tech Mono', monospace";
  const UI = "'Rajdhani', sans-serif";

  // ------------------------------------------------------------------ formatting
  const SUP = { "-": "⁻", 0: "⁰", 1: "¹", 2: "²", 3: "³", 4: "⁴", 5: "⁵", 6: "⁶", 7: "⁷", 8: "⁸", 9: "⁹" };
  const sup = (k) => String(k).split("").map((c) => SUP[c] ?? c).join("");
  const pow10 = (k) => (k === 0 ? "1" : k === 1 ? "10" : "10" + sup(k));
  function sci(v, d = 2) {
    if (v === 0) return "0";
    const k = Math.floor(Math.log10(Math.abs(v)));
    const m = v / 10 ** k;
    if (k >= -2 && k <= 3) return Number(v.toPrecision(d + 1)).toString();
    return `${m.toFixed(d)}×10${sup(k)}`;
  }
  function age(gyr) {
    if (gyr >= 1) return [gyr.toFixed(gyr >= 10 ? 2 : 3), "Gyr"];
    if (gyr >= 1e-3) return [(gyr * 1e3).toPrecision(3), "Myr"];
    if (gyr >= 1e-6) return [(gyr * 1e6).toPrecision(3), "kyr"];
    return ["< 1", "kyr"];
  }
  function period(uHz) {
    const s = 1e6 / uHz;
    if (s < 90) return `${s.toFixed(1)} s`;
    if (s < 5400) return `${(s / 60).toFixed(1)} min`;
    if (s < 172800) return `${(s / 3600).toFixed(1)} h`;
    if (s < 86400 * 400) return `${(s / 86400).toFixed(1)} d`;
    return `${(s / 86400 / 365.25).toFixed(1)} yr`;
  }
  const tex = (el, s) => { if (el && window.katex) katex.render(s, el, { throwOnError: false }); else if (el) el.textContent = s; };

  // ------------------------------------------------------------------ canvas surfaces and axes
  function surface(canvas) {
    const s = { canvas, ctx: canvas.getContext("2d"), w: 0, h: 0, dpr: 1 };
    s.fit = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 3);
      const w = canvas.clientWidth, h = canvas.clientHeight;
      if (w === s.w && h === s.h && dpr === s.dpr) return false;
      Object.assign(s, { w, h, dpr });
      canvas.width = Math.max(1, Math.round(w * dpr));
      canvas.height = Math.max(1, Math.round(h * dpr));
      return true;
    };
    s.begin = () => {
      s.fit();
      const c = s.ctx;
      c.setTransform(s.dpr, 0, 0, s.dpr, 0, 0);
      c.clearRect(0, 0, s.w, s.h);
      c.globalAlpha = 1;
      c.setLineDash([]);
      c.lineWidth = 1;
      return c;
    };
    return s;
  }

  function scale(type, lo, hi, p0, p1) {
    if (type === "log") {
      const a = Math.log10(lo), b = Math.log10(hi);
      return { f: (v) => p0 + ((Math.log10(v) - a) / (b - a)) * (p1 - p0), inv: (p) => 10 ** (a + ((p - p0) / (p1 - p0)) * (b - a)), lo, hi, type };
    }
    return { f: (v) => p0 + ((v - lo) / (hi - lo)) * (p1 - p0), inv: (p) => lo + ((p - p0) / (p1 - p0)) * (hi - lo), lo, hi, type };
  }
  function linTicks(lo, hi, n) {
    const raw = (hi - lo) / Math.max(1, n);
    const mag = 10 ** Math.floor(Math.log10(raw));
    const norm = raw / mag;
    const step = (norm < 1.5 ? 1 : norm < 3.5 ? 2 : norm < 7.5 ? 5 : 10) * mag;
    const out = [];
    for (let v = Math.ceil(lo / step - 1e-9) * step; v <= hi + 1e-9 * step; v += step) out.push({ v: +v.toFixed(12), label: fmtLin(+v.toFixed(12), step), major: true });
    return out;
  }
  function fmtLin(v, step) {
    if (Math.abs(v) < 1e-12) return "0";
    if (Math.abs(v) >= 1e5) return sci(v, Math.abs(v) / step >= 100 ? 2 : 1);
    const d = Math.max(0, -Math.floor(Math.log10(step)));
    return v.toFixed(Math.min(d, 6));
  }
  function logTicks(lo, hi, maxLabels) {
    const k0 = Math.ceil(Math.log10(lo) - 1e-9), k1 = Math.floor(Math.log10(hi) + 1e-9);
    const every = Math.max(1, Math.ceil((k1 - k0 + 1) / maxLabels));
    const out = [];
    const minor = k1 - k0 <= 3;
    for (let k = k0 - 1; k <= k1; k++) {
      if (k >= k0) out.push({ v: 10 ** k, label: (k - k0) % every === 0 ? pow10(k) : "", major: true });
      if (minor) for (let m = 2; m < 10; m++) { const v = m * 10 ** k; if (v > lo && v < hi) out.push({ v, label: "", major: false }); }
    }
    return out;
  }
  const ticksFor = (sc, n) => (sc.type === "log" ? logTicks(sc.lo, sc.hi, n) : linTicks(sc.lo, sc.hi, n));

  // Draw a frame with ticks; box = {x0, y0, x1, y1}; X, Y are scales mapping data to pixels.
  function frame(c, box, X, Y, opt = {}) {
    const { x0, y0, x1, y1 } = box;
    c.fillStyle = opt.fill || "rgba(255,255,255,0.015)";
    c.fillRect(x0, y0, x1 - x0, y1 - y0);
    c.font = `11px ${MONO}`;
    c.textBaseline = "middle";
    const tx = opt.xTicks || ticksFor(X, opt.nx || 5);
    const ty = opt.yTicks || ticksFor(Y, opt.ny || 4);
    c.strokeStyle = INK.grid;
    for (const t of tx) { const p = X.f(t.v); if (p < x0 - 0.5 || p > x1 + 0.5 || !t.major) continue; c.beginPath(); c.moveTo(p, y0); c.lineTo(p, y1); c.stroke(); }
    for (const t of ty) { const p = Y.f(t.v); if (p < y0 - 0.5 || p > y1 + 0.5 || !t.major) continue; c.beginPath(); c.moveTo(x0, p); c.lineTo(x1, p); c.stroke(); }
    c.strokeStyle = INK.axis;
    c.beginPath(); c.moveTo(x0, y0); c.lineTo(x0, y1); c.lineTo(x1, y1); c.stroke();
    c.fillStyle = INK.tick;
    c.textAlign = "center";
    let lastX = -1e9;
    const inOrder = tx.map((t) => ({ ...t, p: X.f(t.v) })).sort((a, b) => a.p - b.p);
    for (const t of inOrder) {
      const p = t.p; if (p < x0 - 0.5 || p > x1 + 0.5) continue;
      c.beginPath(); c.moveTo(p, y1); c.lineTo(p, y1 + (t.major ? 4 : 2)); c.stroke();
      if (!t.label || !opt.xLabels) continue;
      const w = c.measureText(t.label).width;
      if (p - w / 2 < lastX + 6 || p + w / 2 > x1 + 10) continue;
      c.fillText(t.label, p, y1 + 12); lastX = p + w / 2;
    }
    c.textAlign = "right";
    let lastY = 1e9;
    for (const t of ty) {
      const p = Y.f(t.v); if (p < y0 - 0.5 || p > y1 + 0.5) continue;
      c.beginPath(); c.moveTo(x0 - (t.major ? 4 : 2), p); c.lineTo(x0, p); c.stroke();
      if (!t.label) continue;
      if (p > lastY - 13) continue;
      c.fillText(t.label, x0 - 6, p); lastY = p;
    }
  }
  function polyline(c, xs, ys, X, Y, keep) {
    c.beginPath();
    let on = false;
    for (let i = 0; i < xs.length; i++) {
      const y = ys[i], x = xs[i];
      if (!(keep ? keep(x, y) : isFinite(y)) || (X.type === "log" && !(x > 0))) { on = false; continue; }
      const px = X.f(x), py = Y.f(y);
      if (on) c.lineTo(px, py); else c.moveTo(px, py);
      on = true;
    }
    c.stroke();
  }
  function shadeZones(c, box, X, zones, color) {
    c.fillStyle = color;
    for (const [a, b] of zones) {
      const pa = clamp(X.f(Math.max(a, X.lo)), box.x0, box.x1), pb = clamp(X.f(Math.max(b, X.lo)), box.x0, box.x1);
      if (pb <= pa && b <= X.lo) continue;
      c.fillRect(pa, box.y0, Math.max(1, pb - pa), box.y1 - box.y0);
    }
  }
  function clipBox(c, box) { c.beginPath(); c.rect(box.x0, box.y0, box.x1 - box.x0, box.y1 - box.y0); c.clip(); }
  function marker(c, x, y, ell, r, filled) {
    c.beginPath();
    if (ell === 0) c.arc(x, y, r, 0, TAU);
    else if (ell === 1) { c.moveTo(x, y - r * 1.2); c.lineTo(x + r * 1.1, y + r * 0.75); c.lineTo(x - r * 1.1, y + r * 0.75); c.closePath(); }
    else c.rect(x - r * 0.9, y - r * 0.9, r * 1.8, r * 1.8);
    if (filled) c.fill(); else c.stroke();
  }

  // ------------------------------------------------------------------ data
  let H5 = null, T = null, HIST = null, ZONES = null;
  const CACHE = new Map();
  const arr = (p) => { const d = H5.get(p); if (!d) throw new Error("missing " + p); return Array.from(d.value); };
  const tryArr = (p) => { try { return arr(p); } catch (e) { return null; } };
  const decodeStr = (v) => (typeof v === "string" ? v : v && v.length !== undefined ? Array.from(v).map((ch) => String.fromCharCode(ch)).join("") : String(v)).replace(/\0/g, "").trim();

  function convZones(x, mt) {
    const out = [];
    let on = false, a = 0;
    for (let i = 0; i < x.length; i++) {
      if (mt[i] === 1 && !on) { on = true; a = x[i]; }
      if (mt[i] !== 1 && on) { on = false; out.push([a, x[i]]); }
    }
    if (on) out.push([a, 1]);
    return out;
  }
  function burnZones(x, eps, frac) {
    const peak = Math.max(...eps);
    if (!(peak > 0)) return { zones: [], peak: 0, xpeak: 0 };
    const thr = peak * frac;
    const out = [];
    let on = false, a = 0;
    for (let i = 0; i < x.length; i++) {
      if (eps[i] >= thr && !on) { on = true; a = x[i]; }
      if (eps[i] < thr && on) { on = false; out.push([a, x[i]]); }
    }
    if (on) out.push([a, 1]);
    return { zones: out, peak, xpeak: x[eps.indexOf(peak)] };
  }

  function loadTrack(buffer) {
    H5 = new hdf5.File(buffer);
    const n = arr("track/log_Teff").length;
    T = {
      n,
      logTeff: arr("track/log_Teff"), logL: arr("track/log_L"), logR: arr("track/log_R"), logg: tryArr("track/log_g"),
      age: arr("track/star_age"), Xc: arr("track/center_h1"), Yc: arr("track/center_he4"), mass: tryArr("track/star_mass"),
      mHe: tryArr("track/he_core_mass"), rgb: arr("track/teff_rgb"), phase: arr("track/phase").map(decodeStr),
      numax: arr("track/nu_max"), dnu: arr("track/delta_nu"), model: tryArr("track/model_number_orig"),
      hasGyre: tryArr("track/has_real_gyre"),
    };
    T.phase.forEach((p, i) => { if (p === "SGB" && T.logL[i] > 0.5) T.phase[i] = "RGB"; });
    const hT = tryArr("history/log_Teff"), hL = tryArr("history/log_L");
    HIST = hT && hL ? { logTeff: hT, logL: hL } : { logTeff: T.logTeff, logL: T.logL };
    ZONES = [];
    for (let i = 0; i < n; i++) {
      const x = arr(`profiles/${i}/x`), mt = arr(`profiles/${i}/mixing_type`), eps = arr(`profiles/${i}/eps_nuc`);
      ZONES.push({ conv: convZones(x, mt), burn: burnZones(x, eps, 0.1).zones });
    }
  }

  function model(i) {
    if (CACHE.has(i)) return CACHE.get(i);
    const g = (k) => arr(`profiles/${i}/${k}`);
    const p = { x: g("x"), logT: g("logT"), logRho: g("logRho"), logP: g("logP"), eps: g("eps_nuc"), conv_vel: g("conv_vel"), mt: g("mixing_type"), N2: g("brunt_N2"), Sl1sq: g("lamb_Sl1_sq"), kappa: g("opacity"), h1: g("h1"), he4: g("he4"), cs: g("c_sound") };
    p.conv = convZones(p.x, p.mt);
    p.burn = burnZones(p.x, p.eps, 0.01);
    let modes = [];
    const l = tryArr(`gyre/${i}/l`);
    if (l && l.length) {
      const freq = arr(`gyre/${i}/freq_uHz`), npg = arr(`gyre/${i}/n_pg`), np = tryArr(`gyre/${i}/n_p`), ng = tryArr(`gyre/${i}/n_g`), E = arr(`gyre/${i}/E_norm`);
      const type = (tryArr(`gyre/${i}/mode_type`) || []).map(decodeStr);
      const xg = arr(`gyre/${i}/x_profile`);
      modes = l.map((ell, j) => ({ j, l: ell, nu: freq[j], npg: npg[j], np: np ? np[j] : null, ng: ng ? ng[j] : null, E: E[j], type: type[j] || "p", xg, xi: null }));
      modes.sort((a, b) => a.nu - b.nu);
    }
    const m = { i, p, modes };
    if (CACHE.size > 16) CACHE.delete(CACHE.keys().next().value);
    CACHE.set(i, m);
    return m;
  }
  function eigen(i, mode) {
    if (!mode.xi) mode.xi = arr(`gyre/${i}/modes/${mode.j}/xi_r`);
    return mode.xi;
  }

  // ------------------------------------------------------------------ state
  const S = { i: 0, mode: null, xlog: false, pulsate: !REDUCED, playing: false, hover: null };
  let M = null; // the selected model's data

  // ------------------------------------------------------------------ stats
  function updateStats() {
    const i = S.i;
    const set = (id, v) => { $(id).textContent = v; };
    set("#s-model", T.model ? T.model[i] : i + 1);
    const [a, au] = age(T.age[i]); set("#s-age", a); $("#s-age-u").textContent = au;
    set("#s-teff", Math.round(10 ** T.logTeff[i]).toLocaleString("en-GB"));
    set("#s-l", sci(10 ** T.logL[i], 2));
    const R = 10 ** T.logR[i]; set("#s-r", R >= 100 ? R.toFixed(0) : R >= 1 ? R.toFixed(2) : sci(R, 2));
    set("#s-logg", T.logg ? T.logg[i].toFixed(2) : "");
    set("#s-xc", T.Xc[i].toFixed(3));
    set("#s-yc", T.Yc[i].toFixed(3));
    set("#s-mhe", T.mHe ? (T.mHe[i] > 0 ? T.mHe[i].toFixed(3) : "0") : "");
    const nm = T.numax[i], dn = T.dnu[i];
    set("#s-numax", nm >= 100 ? nm.toFixed(0) : nm >= 1 ? nm.toFixed(1) : sci(nm, 2));
    set("#s-dnu", dn >= 100 ? dn.toFixed(0) : dn >= 1 ? dn.toFixed(2) : sci(dn, 2));
    const ph = T.phase[i], [col, name] = PHASE[ph] || ["#fff", ph];
    const tag = $("#phase-tag");
    tag.textContent = name;
    tag.style.color = col; tag.style.borderColor = col; tag.style.background = col + "1f";
  }

  // ------------------------------------------------------------------ HR diagram
  const hr = { s: null, box: null, X: null, Y: null };
  function drawHR() {
    const c = hr.s.begin();
    const { w, h } = hr.s;
    const box = { x0: 46, y0: 26, x1: w - 60, y1: h - 40 };
    hr.box = box;
    const lo = Math.min(...HIST.logTeff) - 0.02, hi = Math.max(...HIST.logTeff) + 0.02;
    const Llo = Math.min(...HIST.logL) - 0.15, Lhi = Math.max(...HIST.logL) + 0.15;
    const X = scale("lin", hi, lo, box.x0, box.x1); // reversed
    const Y = scale("lin", Llo, Lhi, box.y1, box.y0);
    hr.X = X; hr.Y = Y;
    const xTicks = [2000, 3000, 4000, 5000, 6000, 8000, 10000, 15000, 20000, 30000, 50000, 70000, 100000, 150000, 200000]
      .filter((t) => Math.log10(t) > lo && Math.log10(t) < hi)
      .map((t) => ({ v: Math.log10(t), label: t >= 1000 ? `${t / 1000}k` : String(t), major: true }));
    const yTicks = [];
    for (let k = Math.ceil(Llo); k <= Math.floor(Lhi); k++) yTicks.push({ v: k, label: pow10(k), major: true });
    frame(c, box, X, Y, { xTicks, yTicks, xLabels: true });
    c.save(); clipBox(c, box);
    // lines of constant radius: log L = 2 log R + 4 (log T - log 5772)
    c.strokeStyle = "rgba(180,180,210,0.16)"; c.setLineDash([3, 4]); c.font = `10px ${MONO}`; c.fillStyle = INK.faint; c.textAlign = "left";
    for (const Rk of [0.01, 0.1, 1, 10, 100]) {
      const lT = (t) => 2 * Math.log10(Rk) + 4 * (t - Math.log10(5772));
      c.beginPath(); c.moveTo(X.f(hi), Y.f(lT(hi))); c.lineTo(X.f(lo), Y.f(lT(lo))); c.stroke();
      // label where the line meets the top or the right edge
      let tl = hi + (Lhi - lT(hi)) / 4; // temperature at which it hits the top
      let px, py;
      if (tl < hi && tl > lo) { px = X.f(tl); py = box.y0 + 10; } else { px = X.f(lo) - 34; py = Y.f(lT(lo)) - 6; }
      if (py > box.y0 && py < box.y1 && px > box.x0 && px < box.x1 - 30) c.fillText(`${Rk} R☉`, px + 3, py);
    }
    c.setLineDash([]);
    // the whole history
    c.strokeStyle = "rgba(232,232,242,0.5)"; c.lineWidth = 1;
    polyline(c, HIST.logTeff, HIST.logL, X, Y);
    // the stored models
    for (let i = 0; i < T.n; i++) {
      c.fillStyle = (PHASE[T.phase[i]] || ["#fff"])[0];
      c.beginPath(); c.arc(X.f(T.logTeff[i]), Y.f(T.logL[i]), i === S.i ? 4.5 : 3, 0, TAU); c.fill();
    }
    if (S.hover !== null && S.hover !== S.i) {
      c.strokeStyle = "#fff"; c.beginPath(); c.arc(X.f(T.logTeff[S.hover]), Y.f(T.logL[S.hover]), 6, 0, TAU); c.stroke();
    }
    const sx = X.f(T.logTeff[S.i]), sy = Y.f(T.logL[S.i]);
    c.strokeStyle = "rgba(223,243,255,0.45)"; c.setLineDash([2, 4]);
    c.beginPath(); c.moveTo(box.x0, sy); c.lineTo(sx, sy); c.lineTo(sx, box.y1); c.stroke();
    c.setLineDash([]);
    c.strokeStyle = "#fff"; c.lineWidth = 1.5; c.beginPath(); c.arc(sx, sy, 8, 0, TAU); c.stroke();
    c.restore();
    // phase legend along the bottom
    const present = [...new Set(T.phase)].filter((p) => PHASE[p]);
    c.font = `11px ${UI}`; c.textAlign = "left"; c.textBaseline = "middle";
    let lx = box.x0;
    for (const p of present) {
      c.fillStyle = PHASE[p][0]; c.beginPath(); c.arc(lx + 4, h - 12, 3, 0, TAU); c.fill();
      c.fillStyle = INK.tick; c.fillText(p, lx + 11, h - 12);
      lx += 18 + c.measureText(p).width;
      if (lx > box.x1 - 40) break;
    }
  }
  function hrNearest(px, py) {
    let best = 12, bi = null;
    for (let i = 0; i < T.n; i++) {
      const d = Math.hypot(hr.X.f(T.logTeff[i]) - px, hr.Y.f(T.logL[i]) - py);
      if (d < best) { best = d; bi = i; }
    }
    return bi;
  }

  // ------------------------------------------------------------------ timeline strip
  const strip = { s: null, X: null, Y: null, top: 18, bottom: 0 };
  function drawStrip() {
    const c = strip.s.begin();
    const { w, h } = strip.s;
    const x0 = 34, x1 = w - 6, y0 = strip.top, y1 = h - 4;
    strip.bottom = y1;
    const X = (i) => x0 + (i / T.n) * (x1 - x0);
    const Y = S.xlog ? scale("log", 1e-3, 1, y1, y0) : scale("lin", 0, 1, y1, y0);
    strip.X = X; strip.Y = Y;
    c.fillStyle = "rgba(255,255,255,0.03)"; c.fillRect(x0, y0, x1 - x0, y1 - y0);
    // phase runs
    c.font = `10.5px ${UI}`; c.textBaseline = "middle"; c.textAlign = "left";
    for (let i = 0; i < T.n;) {
      let j = i; while (j < T.n && T.phase[j] === T.phase[i]) j++;
      const col = (PHASE[T.phase[i]] || ["#fff"])[0];
      c.fillStyle = col; c.fillRect(X(i), y0 - 5, X(j) - X(i) - 1, 2);
      const label = T.phase[i];
      const tw = c.measureText(label).width;
      if (X(j) - X(i) > tw + 6) c.fillText(label, X(i) + 2, y0 - 11);
      i = j;
    }
    const wcol = X(1) - X(0);
    for (let i = 0; i < T.n; i++) {
      const px = X(i);
      const z = ZONES[i];
      c.fillStyle = CONV; c.globalAlpha = 0.6;
      for (const [a, b] of z.conv) {
        const pa = Y.f(Math.max(a, Y.lo)), pb = Y.f(Math.max(b, Y.lo));
        c.fillRect(px, Math.min(pa, pb), wcol + 0.5, Math.max(1, Math.abs(pa - pb)));
      }
      c.fillStyle = BURN; c.globalAlpha = 0.95;
      for (const [a, b] of z.burn) {
        const pa = Y.f(Math.max(a, Y.lo)), pb = Y.f(Math.max(b, Y.lo));
        c.fillRect(px, Math.min(pa, pb) - 0.5, wcol + 0.5, Math.max(1.5, Math.abs(pa - pb)));
      }
      c.globalAlpha = 1;
    }
    // y ticks: 0, 0.5, 1 or decades
    c.fillStyle = INK.faint; c.font = `10px ${MONO}`; c.textAlign = "right"; c.strokeStyle = INK.axis;
    const yt = S.xlog ? [1e-3, 1e-2, 1e-1, 1] : [0, 0.5, 1];
    yt.forEach((v, k) => { const p = Y.f(v); c.beginPath(); c.moveTo(x0 - 3, p); c.lineTo(x0, p); c.stroke(); if (k === 0 || k === yt.length - 1) c.fillText(S.xlog ? pow10(Math.round(Math.log10(v))) : String(v), x0 - 5, clamp(p, y0 + 5, y1 - 5)); });
    if (S.hover !== null) { c.fillStyle = "rgba(255,255,255,0.10)"; c.fillRect(X(S.hover), y0, wcol, y1 - y0); }
    const cx = X(S.i) + wcol / 2;
    c.strokeStyle = "#fff"; c.lineWidth = 1.2; c.beginPath(); c.moveTo(cx, y0 - 2); c.lineTo(cx, y1); c.stroke();
    c.fillStyle = "#fff"; c.beginPath(); c.moveTo(cx - 4, y0 - 7); c.lineTo(cx + 4, y0 - 7); c.lineTo(cx, y0 - 2); c.closePath(); c.fill();
  }
  const stripIndex = (px) => clamp(Math.floor(((px - 34) / (strip.s.w - 40)) * T.n), 0, T.n - 1);

  // ------------------------------------------------------------------ interior
  const int_ = { s: null, shells: null, cells: null, t0: 0, raf: null };
  function surfRGB(i) { const v = T.rgb[i]; return [(v >> 16) & 255, (v >> 8) & 255, v & 255]; }
  function thermal(t, srgb) {
    const stops = [[srgb, 0], [[255, 196, 120], 0.3], [[255, 236, 196], 0.68], [[255, 255, 250], 1]];
    let k = 0; while (k < stops.length - 2 && t > stops[k + 1][1]) k++;
    const [c0, t0] = stops[k], [c1, t1] = stops[k + 1];
    const f = clamp((t - t0) / (t1 - t0), 0, 1);
    return `rgb(${Math.round(lerp(c0[0], c1[0], f))},${Math.round(lerp(c0[1], c1[1], f))},${Math.round(lerp(c0[2], c1[2], f))})`;
  }
  function prepareInterior() {
    const p = M.p, n = p.x.length;
    const step = Math.max(1, Math.floor(n / 110));
    const idx = []; for (let k = 0; k < n; k += step) idx.push(k); if (idx[idx.length - 1] !== n - 1) idx.push(n - 1);
    const lc = p.logT[0], ls = p.logT[n - 1], srgb = surfRGB(S.i);
    int_.shells = idx.map((k) => ({ x: p.x[k], col: thermal((p.logT[k] - ls) / (lc - ls || 1), srgb), eps: p.eps[k], k }));
    int_.srgb = srgb;
    // a magnified view of the centre when the structure there is too small to see
    const burnOut = p.burn.zones.length ? Math.max(...p.burn.zones.map((z) => z[1])) : 0;
    const inner = (p.burn.peak > 0 && burnOut < 0.08) || (p.conv.length && p.conv[0][1] < 0.1 && p.conv[0][0] < 0.05);
    let xin = Math.max(2.5 * burnOut, p.conv.length && p.conv[0][1] < 0.1 ? 3 * p.conv[0][1] : 0, 0.002);
    const steps = [0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2];
    xin = steps.find((v) => v >= xin) || 0.2;
    int_.inset = inner ? xin : 0;
    int_.cellPhase = Math.random() * TAU;
    // the pulsation: xi_r of the selected mode interpolated onto the shells
    int_.xi = null;
    if (S.mode) {
      const xi = eigen(S.i, S.mode), xg = S.mode.xg;
      const v = int_.shells.map((sh) => {
        let k = 0; while (k < xg.length - 2 && xg[k + 1] < sh.x) k++;
        const t = xg[k + 1] !== xg[k] ? (sh.x - xg[k]) / (xg[k + 1] - xg[k]) : 0;
        return lerp(xi[k], xi[k + 1], clamp(t, 0, 1));
      });
      const peak = Math.max(...v.map(Math.abs)) || 1;
      int_.xi = v.map((q) => q / peak);
    }
  }
  const legendre = (l, c) => (l === 0 ? 1 : l === 1 ? c : 0.5 * (3 * c * c - 1));
  function drawInterior(tsec) {
    const s = int_.s, c = s.begin();
    const { w, h } = s;
    const p = M.p;
    // with a detail circle the star gives up room: to the right on wide panels, downward on narrow ones
    const narrow = w < h * 1.25;
    const R = Math.min(w, h) * (int_.inset ? (narrow ? 0.31 : 0.38) : 0.40);
    const cx = int_.inset ? (narrow ? w * 0.42 : w / 2 - w * 0.09) : w / 2;
    const cy = int_.inset && narrow ? h * 0.56 : h / 2;
    const K = 96;
    const amp = S.pulsate && int_.xi ? 0.055 * Math.cos(TAU * (tsec / 4)) : 0;
    const ell = S.mode ? S.mode.l : 0;
    const shellPath = (xf, ampl) => {
      c.beginPath();
      for (let k = 0; k <= K; k++) {
        const th = (k / K) * TAU;
        const r = xf * R * (1 + ampl * legendre(ell, Math.cos(th)));
        const px = cx + r * Math.sin(th), py = cy - r * Math.cos(th);
        if (k) c.lineTo(px, py); else c.moveTo(px, py);
      }
      c.closePath();
    };
    // glow outside the photosphere
    const [sr, sg, sb] = int_.srgb;
    const glow = c.createRadialGradient(cx, cy, R * 0.98, cx, cy, R * 1.25);
    glow.addColorStop(0, `rgba(${sr},${sg},${sb},0.28)`); glow.addColorStop(1, `rgba(${sr},${sg},${sb},0)`);
    c.fillStyle = glow; c.beginPath(); c.arc(cx, cy, R * 1.25, 0, TAU); c.fill();
    // shells from the outside in, deformed by the mode
    const sh = int_.shells;
    for (let i = sh.length - 1; i >= 0; i--) {
      if (sh[i].x * R < 0.6) continue;
      shellPath(sh[i].x, amp * (int_.xi ? int_.xi[i] : 0));
      c.fillStyle = sh[i].col; c.fill();
    }
    // nuclear burning as a glow where eps is within a hundredth of its peak
    if (p.burn.peak > 0) {
      c.save(); c.globalCompositeOperation = "source-over";
      for (let i = 0; i < sh.length; i++) {
        const f = sh[i].eps / p.burn.peak; if (f < 0.01) continue;
        const r = sh[i].x * R, dr = Math.max(3, (sh[Math.min(i + 1, sh.length - 1)].x - sh[i].x) * R * 1.5);
        const g = c.createRadialGradient(cx, cy, Math.max(0, r - dr), cx, cy, r + dr);
        const a = 0.55 * Math.sqrt(f);
        g.addColorStop(0, "rgba(255,80,30,0)"); g.addColorStop(0.5, `rgba(255,90,30,${a})`); g.addColorStop(1, "rgba(255,60,20,0)");
        c.fillStyle = g; c.beginPath(); c.arc(cx, cy, r + dr, 0, TAU); c.fill();
      }
      c.restore();
    }
    drawZoneMarks(c, cx, cy, R, p, tsec, 1);
    // limb darkening
    const limb = c.createRadialGradient(cx, cy, R * 0.6, cx, cy, R);
    limb.addColorStop(0, "rgba(0,0,0,0)"); limb.addColorStop(0.82, "rgba(0,0,0,0.05)"); limb.addColorStop(1, "rgba(0,0,0,0.4)");
    c.fillStyle = limb; shellPath(1, amp * (int_.xi ? int_.xi[sh.length - 1] : 0)); c.fill();
    // the photosphere outline, in the mode colour while it pulsates
    c.strokeStyle = S.pulsate && int_.xi ? ELL_COLOR[ell] : "rgba(255,255,255,0.35)"; c.lineWidth = 1; shellPath(1, amp * (int_.xi ? int_.xi[sh.length - 1] : 0)); c.stroke();
    // ruler along the horizontal radius, ticks at the zone boundaries
    const bounds = [...new Set([...p.conv.flat(), 1].map((v) => +v.toFixed(3)))].filter((v) => v > 0).sort((a, b) => a - b);
    const ry = cy + R + 18;
    c.strokeStyle = INK.axis; c.fillStyle = INK.tick; c.font = `11px ${MONO}`; c.textAlign = "center"; c.textBaseline = "top";
    c.beginPath(); c.moveTo(cx, ry); c.lineTo(cx + R, ry); c.stroke();
    c.beginPath(); c.moveTo(cx, ry - 3); c.lineTo(cx, ry + 3); c.stroke();
    c.fillText("0", cx, ry + 6);
    let lastTick = cx;
    for (const b of bounds) {
      const px = cx + b * R;
      c.beginPath(); c.moveTo(px, ry - 3); c.lineTo(px, ry + 3); c.stroke();
      if (px - lastTick > 26) { c.fillText(b === 1 ? "1 R" : b < 0.01 ? b.toFixed(3) : b.toFixed(2), px, ry + 6); lastTick = px; }
    }
    // scale bar: a round number of solar radii
    const Rstar = 10 ** T.logR[S.i];
    let Ls = 10 ** Math.floor(Math.log10(Rstar / 3));
    for (const m of [5, 2, 1]) if (m * Ls <= Rstar / 3) { Ls *= m; break; }
    const Lpx = (Ls / Rstar) * R;
    const bx = w - 14 - Lpx, by = h - 16;
    c.strokeStyle = INK.tick; c.beginPath(); c.moveTo(bx, by); c.lineTo(bx + Lpx, by); c.moveTo(bx, by - 4); c.lineTo(bx, by + 4); c.moveTo(bx + Lpx, by - 4); c.lineTo(bx + Lpx, by + 4); c.stroke();
    c.textAlign = "right"; c.textBaseline = "bottom"; c.fillText(`${Ls} R☉`, w - 14, by - 5);
    // detail view of the centre
    if (int_.inset) {
      const Ri = Math.min(w, h) * (narrow ? 0.17 : 0.21), ix = w - Ri - 18, iy = Ri + 18;
      const k = Ri / int_.inset;
      c.strokeStyle = INK.axis; c.setLineDash([3, 4]);
      c.beginPath(); c.arc(cx, cy, Math.max(2, int_.inset * R), 0, TAU); c.stroke();
      // two hairlines joining the small circle to the detail circle
      const ang = Math.atan2(iy - cy, ix - cx);
      for (const d of [-1, 1]) {
        const a = ang + d * Math.PI / 2;
        c.beginPath(); c.moveTo(cx + Math.max(2, int_.inset * R) * Math.cos(a), cy + Math.max(2, int_.inset * R) * Math.sin(a)); c.lineTo(ix + Ri * Math.cos(a), iy + Ri * Math.sin(a)); c.stroke();
      }
      c.setLineDash([]);
      c.save(); c.beginPath(); c.arc(ix, iy, Ri, 0, TAU); c.clip();
      c.fillStyle = "#0a0a0d"; c.fillRect(ix - Ri, iy - Ri, 2 * Ri, 2 * Ri);
      for (let i = sh.length - 1; i >= 0; i--) {
        if (sh[i].x > int_.inset * 1.05) continue;
        c.beginPath(); c.arc(ix, iy, Math.max(0.6, sh[i].x * k), 0, TAU); c.fillStyle = sh[i].col; c.fill();
      }
      if (p.burn.peak > 0) for (let i = 0; i < sh.length; i++) {
        const f = sh[i].eps / p.burn.peak; if (f < 0.01 || sh[i].x > int_.inset) continue;
        const r = sh[i].x * k, dr = Math.max(3, (sh[Math.min(i + 1, sh.length - 1)].x - sh[i].x) * k * 1.5);
        const g = c.createRadialGradient(ix, iy, Math.max(0, r - dr), ix, iy, r + dr);
        const a = 0.55 * Math.sqrt(f);
        g.addColorStop(0, "rgba(255,80,30,0)"); g.addColorStop(0.5, `rgba(255,90,30,${a})`); g.addColorStop(1, "rgba(255,60,20,0)");
        c.fillStyle = g; c.beginPath(); c.arc(ix, iy, r + dr, 0, TAU); c.fill();
      }
      drawZoneMarks(c, ix, iy, k, p, tsec, int_.inset);
      c.restore();
      c.strokeStyle = INK.axis; c.beginPath(); c.arc(ix, iy, Ri, 0, TAU); c.stroke();
      c.fillStyle = INK.tick; c.font = `11px ${MONO}`; c.textAlign = "center"; c.textBaseline = "top";
      c.fillText(`r < ${int_.inset} R`, ix, iy + Ri + 6);
    }
  }
  // zone overlays within x <= xmax: radial hairlines in radiative regions, circulation cells with
  // moving particles in convective ones, and a hairline at every boundary. k = pixels per unit x.
  function drawZoneMarks(c, cx, cy, k, p, tsec, xmax) {
    const rad = [];
    let a = 0;
    for (const [c0, c1] of p.conv) { if (c0 > a) rad.push([a, c0]); a = c1; }
    if (a < 1) rad.push([a, 1]);
    c.strokeStyle = "rgba(0,0,0,0.13)"; c.lineWidth = 0.8;
    for (const [r0, r1] of rad) {
      const a0 = Math.max(r0, 0.004 * (1 / k) * 60), a1 = Math.min(r1, xmax);
      if (a1 <= a0 || (a1 - a0) * k < 3) continue;
      c.beginPath();
      for (let d = 0; d < 360; d += 5) {
        const t = (d * Math.PI) / 180;
        const i0 = (a0 + (a1 - a0) * 0.06) * k, i1 = (a1 - (a1 - a0) * 0.06) * k;
        c.moveTo(cx + i0 * Math.sin(t), cy - i0 * Math.cos(t)); c.lineTo(cx + i1 * Math.sin(t), cy - i1 * Math.cos(t));
      }
      c.stroke();
    }
    c.lineWidth = 1;
    const rings = [];
    for (const [r0, r1] of p.conv) {
      let top = Math.min(r1, xmax);
      while (top > r0) {
        let bottom = Math.max(r0, top - clamp(0.3 * top, 0.03, 0.16));
        if (bottom - r0 < 0.02) bottom = r0;
        rings.push([bottom, top]);
        top = bottom;
      }
    }
    let ring = 0;
    for (const [a0, a1] of rings) {
      ring++;
      if (a1 <= a0) continue;
      const thick = (a1 - a0) * k;
      if (thick < 5) { // too thin for cells: a stippled band
        c.fillStyle = CONV; c.globalAlpha = 0.7;
        const rm = ((a0 + a1) / 2) * k;
        for (let d = 0; d < 360; d += 3) { const t = (d * Math.PI) / 180; c.beginPath(); c.arc(cx + rm * Math.sin(t), cy - rm * Math.cos(t), 0.9, 0, TAU); c.fill(); }
        c.globalAlpha = 1; continue;
      }
      const rm = ((a0 + a1) / 2) * k, rr = ((a1 - a0) / 2) * k * 0.72;
      const n = clamp(Math.round((TAU * rm) / (thick * 1.15)), 8, 80);
      c.strokeStyle = "rgba(10,60,95,0.6)"; c.lineWidth = 1.1;
      c.beginPath();
      for (let j = 0; j < n; j++) {
        const phc = (j / n) * TAU + int_.cellPhase + (ring % 2 ? 0 : TAU / n / 2), half = (TAU / n) * 0.42;
        for (let q = 0; q <= 24; q++) {
          const tau = (q / 24) * TAU;
          const r = rm + rr * Math.cos(tau), ph = phc + half * Math.sin(tau);
          const px = cx + r * Math.sin(ph), py = cy - r * Math.cos(ph);
          if (q) c.lineTo(px, py); else c.moveTo(px, py);
        }
      }
      c.stroke();
      // particles circulating, alternate cells in opposite senses
      c.lineWidth = 1; c.fillStyle = "#0b3e5e";
      for (let j = 0; j < n; j++) {
        const phc = (j / n) * TAU + int_.cellPhase + (ring % 2 ? 0 : TAU / n / 2), half = (TAU / n) * 0.42, dir = j % 2 ? 1 : -1;
        for (let q = 0; q < 2; q++) {
          const tau = dir * TAU * (tsec / 7 + q / 2 + j * 0.37);
          const r = rm + rr * Math.cos(tau), ph = phc + half * Math.sin(tau);
          c.beginPath(); c.arc(cx + r * Math.sin(ph), cy - r * Math.cos(ph), 1.3, 0, TAU); c.fill();
        }
      }
    }
    c.strokeStyle = "rgba(0,0,0,0.35)";
    for (const b of p.conv.flat()) { if (b <= 0 || b >= xmax) continue; c.beginPath(); c.arc(cx, cy, b * k, 0, TAU); c.stroke(); }
  }
  function updateModeCard() {
    const el = $("#int-mode");
    if (!S.mode) { el.innerHTML = M.modes.length ? "" : "no GYRE output for this model"; return; }
    const m = S.mode;
    el.innerHTML = `<span class="k"></span><br>ν = ${m.nu >= 100 ? m.nu.toFixed(1) : m.nu.toPrecision(3)} μHz, P = ${period(m.nu)}`;
    tex($(".k", el), `\\ell = ${m.l},\\ n_{pg} = ${m.npg}${m.type && m.type !== "p" ? `\\ (${m.type === "g" ? "g" : "mixed"})` : ""}`);
  }
  function animate(ts) {
    int_.raf = null;
    if (!int_.t0) int_.t0 = ts;
    const t = (ts - int_.t0) / 1000;
    drawInterior(t);
    if (!REDUCED && !document.hidden) int_.raf = requestAnimationFrame(animate);
  }
  function startAnim() { if (int_.raf === null) int_.raf = requestAnimationFrame(animate); }

  // ------------------------------------------------------------------ profiles (six small multiples)
  const PROF = [
    { id: "T", title: "T\\ [\\mathrm{K}]", y: (p) => p.logT.map((v) => 10 ** v), log: true },
    { id: "rho", title: "\\rho\\ [\\mathrm{g\\,cm^{-3}}]", y: (p) => p.logRho.map((v) => 10 ** v), log: true },
    { id: "P", title: "P\\ [\\mathrm{dyn\\,cm^{-2}}]", y: (p) => p.logP.map((v) => 10 ** v), log: true },
    { id: "eps", title: "\\varepsilon_{\\mathrm{nuc}}\\ [\\mathrm{erg\\,g^{-1}\\,s^{-1}}]", y: (p) => p.eps, log: true, floor: 1e-6 },
    { id: "kappa", title: "\\kappa\\ [\\mathrm{cm^{2}\\,g^{-1}}]", y: (p) => p.kappa, log: true },
    { id: "XY", title: "X,\\ Y", y: (p) => p.h1, y2: (p) => p.he4, log: false, lim: [0, 1] },
  ];
  const prof = { s: {}, hoverX: null };
  const xScale = (box) => (S.xlog ? scale("log", 1e-3, 1, box.x0, box.x1) : scale("lin", 0, 1, box.x0, box.x1));
  function drawProfiles() {
    for (const q of PROF) drawProfile(q);
  }
  function drawProfile(q) {
    const s = prof.s[q.id]; if (!s || !s.canvas.clientWidth) return;
    const c = s.begin();
    const { w, h } = s;
    const big = s.canvas.parentElement.classList.contains("is-max");
    const box = { x0: big ? 64 : 50, y0: 26, x1: w - 40, y1: h - 22 };
    const p = M.p;
    const ys = q.y(p), ys2 = q.y2 ? q.y2(p) : null;
    const X = xScale(box);
    let Y;
    if (q.log) {
      const pos = ys.filter((v) => v > 0);
      const hi = Math.max(...pos), lo0 = Math.min(...pos);
      const lo = Math.max(lo0, hi * (q.floor || 1e-12));
      Y = scale("log", lo / 1.5, hi * 3, box.y1, box.y0);
    } else {
      const [a, b] = q.lim; Y = scale("lin", a, b, box.y1, box.y0);
    }
    frame(c, box, X, Y, { xLabels: true, nx: big ? 8 : 4, ny: big ? 7 : 4 });
    c.save(); clipBox(c, box);
    shadeZones(c, box, X, p.conv, "rgba(127,220,255,0.10)");
    shadeZones(c, box, X, p.burn.zones, "rgba(255,122,61,0.12)");
    c.lineWidth = 1.6; c.strokeStyle = q.y2 ? ELL_COLOR[0] : "#ad93ff";
    polyline(c, p.x, ys, X, Y, (x, y) => (q.log ? y > 0 : isFinite(y)));
    if (ys2) { c.strokeStyle = "#5be8c4"; polyline(c, p.x, ys2, X, Y); }
    if (prof.hoverX !== null) {
      const px = X.f(prof.hoverX);
      c.strokeStyle = "rgba(255,255,255,0.5)"; c.setLineDash([2, 3]); c.beginPath(); c.moveTo(px, box.y0); c.lineTo(px, box.y1); c.stroke(); c.setLineDash([]);
    }
    c.restore();
    if (q.y2) { c.font = `11px ${UI}`; c.textBaseline = "middle"; c.textAlign = "left"; c.fillStyle = ELL_COLOR[0]; c.fillText("X", box.x0 + 8, box.y0 + 10); c.fillStyle = "#5be8c4"; c.fillText("Y", box.x0 + 22, box.y0 + 10); }
    const val = $(`#sm-${q.id} .sm-val`);
    if (prof.hoverX !== null) {
      const k = nearestX(p.x, prof.hoverX);
      val.textContent = ys2 ? `X ${ys[k].toFixed(3)}  Y ${ys2[k].toFixed(3)}` : sci(ys[k], 3);
    } else val.textContent = "";
  }
  function nearestX(x, v) { let k = 0, best = Infinity; for (let i = 0; i < x.length; i++) { const d = Math.abs(x[i] - v); if (d < best) { best = d; k = i; } } return k; }

  // ------------------------------------------------------------------ oscillations (four small multiples)
  const osc = { s: {}, hit: [] };
  function drawOsc() {
    drawProp(); drawEchelle(); drawInertia(); drawEigen();
  }
  function noteFor(id, text) {
    const n = $(`#sm-${id} .sm-note`); n.textContent = text || ""; n.style.display = text ? "flex" : "none";
  }
  function drawProp() {
    const s = osc.s.prop, c = s.begin(); const { w, h } = s; const p = M.p;
    const big = s.canvas.parentElement.classList.contains("is-max");
    const box = { x0: big ? 64 : 52, y0: 26, x1: w - 64, y1: h - 22 };
    const X = xScale(box);
    const toUHz = (sq) => (sq > 0 ? (Math.sqrt(sq) / TAU) * 1e6 : NaN);
    const N = p.N2.map(toUHz), S1 = p.Sl1sq.map(toUHz), S2 = p.Sl1sq.map((v) => toUHz(3 * v));
    const nus = M.modes.map((m) => m.nu);
    const nm = T.numax[S.i];
    const all = [...N, ...S1, ...nus, nm].filter((v) => v > 0 && isFinite(v));
    let lo = Math.min(...all), hi = Math.max(...all);
    if (nus.length) { lo = Math.max(lo, Math.min(...nus) / 30); hi = Math.min(hi, Math.max(...nus) * 30); }
    const Y = scale("log", lo, hi, box.y1, box.y0);
    frame(c, box, X, Y, { xLabels: true, nx: big ? 8 : 4, ny: big ? 7 : 4 });
    c.save(); clipBox(c, box);
    shadeZones(c, box, X, p.conv, "rgba(127,220,255,0.08)");
    // cavities of the selected mode: where it propagates as a p mode (above N and S_l) or a g mode (below both)
    if (S.mode) {
      const Sl = S.mode.l === 0 ? null : S.mode.l === 1 ? S1 : S2;
      const nu = S.mode.nu;
      c.fillStyle = `${ELL_COLOR[S.mode.l]}22`;
      for (let i = 0; i < p.x.length - 1; i++) {
        const nN = N[i] || 0, sl = Sl ? Sl[i] : 0;
        const pc = nu > nN && nu > sl, gc = Sl && nu < nN && nu < sl;
        if (!pc && !gc) continue;
        const a = X.f(Math.max(p.x[i], X.lo)), b = X.f(Math.max(p.x[i + 1], X.lo));
        c.fillRect(a, box.y0, Math.max(0.5, b - a), box.y1 - box.y0);
      }
      c.strokeStyle = ELL_COLOR[S.mode.l]; c.lineWidth = 1.2; c.beginPath(); c.moveTo(box.x0, Y.f(nu)); c.lineTo(box.x1, Y.f(nu)); c.stroke();
    }
    c.lineWidth = 1.5;
    c.strokeStyle = "#ffc45c"; polyline(c, p.x, N, X, Y, (x, y) => y > 0);
    c.strokeStyle = ELL_COLOR[1]; polyline(c, p.x, S1, X, Y, (x, y) => y > 0);
    c.strokeStyle = ELL_COLOR[2]; polyline(c, p.x, S2, X, Y, (x, y) => y > 0);
    if (nm > 0) { c.strokeStyle = "rgba(255,255,255,0.4)"; c.setLineDash([3, 4]); c.beginPath(); c.moveTo(box.x0, Y.f(nm)); c.lineTo(box.x1, Y.f(nm)); c.stroke(); c.setLineDash([]); }
    c.restore();
    c.font = `11px ${UI}`; c.textBaseline = "middle"; c.textAlign = "left";
    const items = [["N", "#ffc45c"], ["S₁", ELL_COLOR[1]], ["S₂", ELL_COLOR[2]], ["νmax", "rgba(255,255,255,0.6)"]];
    let lx = box.x0 + 8;
    for (const [t, col] of items) { c.fillStyle = col; c.fillText(t, lx, box.y0 + 10); lx += c.measureText(t).width + 12; }
  }
  function modeStyle(c, m) {
    c.fillStyle = ELL_COLOR[m.l] || "#fff"; c.strokeStyle = c.fillStyle;
    return m.type === "p" || m.type === "g";
  }
  function drawEchelle() {
    const s = osc.s.echelle, c = s.begin(); const { w, h } = s;
    const big = s.canvas.parentElement.classList.contains("is-max");
    const box = { x0: big ? 64 : 52, y0: 26, x1: w - 64, y1: h - 22 };
    const dn = T.dnu[S.i], modes = M.modes;
    osc.hit = osc.hit.filter((q) => q.panel !== "echelle");
    if (!modes.length || !(dn > 0)) { noteFor("echelle", "no GYRE output for this model"); return; }
    noteFor("echelle", "");
    const nus = modes.map((m) => m.nu);
    const lo = Math.min(...nus), hi = Math.max(...nus);
    const pad = Math.max(dn, (hi - lo) * 0.08);
    const X = scale("lin", 0, dn, box.x0, box.x1), Y = scale("lin", lo - pad, hi + pad, box.y1, box.y0);
    frame(c, box, X, Y, { xLabels: true, nx: big ? 6 : 3, ny: big ? 7 : 4 });
    const nm = T.numax[S.i];
    if (nm > lo - pad && nm < hi + pad) { c.strokeStyle = "rgba(255,255,255,0.4)"; c.setLineDash([3, 4]); c.beginPath(); c.moveTo(box.x0, Y.f(nm)); c.lineTo(box.x1, Y.f(nm)); c.stroke(); c.setLineDash([]); }
    c.lineWidth = 1.3;
    for (const m of modes) {
      const px = X.f(m.nu % dn), py = Y.f(m.nu);
      const filled = modeStyle(c, m);
      marker(c, px, py, m.l, big ? 5 : 4, filled);
      osc.hit.push({ panel: "echelle", x: px, y: py, m });
      if (m === S.mode) { c.strokeStyle = "#fff"; c.beginPath(); c.arc(px, py, 8, 0, TAU); c.stroke(); }
    }
    $("#sm-echelle .sm-val").textContent = `Δν = ${dn >= 10 ? dn.toFixed(1) : dn.toPrecision(3)} μHz`;
  }
  function drawInertia() {
    const s = osc.s.inertia, c = s.begin(); const { w, h } = s;
    const big = s.canvas.parentElement.classList.contains("is-max");
    const box = { x0: big ? 64 : 52, y0: 26, x1: w - 64, y1: h - 22 };
    const modes = M.modes;
    osc.hit = osc.hit.filter((q) => q.panel !== "inertia");
    if (!modes.length) { noteFor("inertia", "no GYRE output for this model"); return; }
    noteFor("inertia", "");
    const nus = modes.map((m) => m.nu), Es = modes.map((m) => m.E).filter((v) => v > 0);
    const lo = Math.min(...nus), hi = Math.max(...nus), pad = (hi - lo) * 0.08 || lo * 0.2;
    const X = scale("lin", lo - pad, hi + pad, box.x0, box.x1);
    const Y = scale("log", Math.min(...Es) / 2, Math.max(...Es) * 2, box.y1, box.y0);
    frame(c, box, X, Y, { xLabels: true, nx: big ? 7 : 4, ny: big ? 6 : 3 });
    const nm = T.numax[S.i];
    if (nm > X.lo && nm < X.hi) { c.strokeStyle = "rgba(255,255,255,0.4)"; c.setLineDash([3, 4]); c.beginPath(); c.moveTo(X.f(nm), box.y0); c.lineTo(X.f(nm), box.y1); c.stroke(); c.setLineDash([]); }
    c.lineWidth = 1.3;
    for (const m of modes) {
      if (!(m.E > 0)) continue;
      const px = X.f(m.nu), py = Y.f(m.E);
      const filled = modeStyle(c, m);
      marker(c, px, py, m.l, big ? 5 : 4, filled);
      osc.hit.push({ panel: "inertia", x: px, y: py, m });
      if (m === S.mode) { c.strokeStyle = "#fff"; c.beginPath(); c.arc(px, py, 8, 0, TAU); c.stroke(); }
    }
    // legend of degrees
    c.font = `11px ${UI}`; c.textBaseline = "middle"; c.textAlign = "left";
    let lx = box.x0 + 8;
    for (const l of [0, 1, 2]) { c.fillStyle = ELL_COLOR[l]; c.strokeStyle = ELL_COLOR[l]; marker(c, lx + 4, box.y0 + 10, l, 3.5, true); c.fillText(`ℓ=${l}`, lx + 12, box.y0 + 10); lx += 40; }
    c.fillStyle = INK.tick; c.strokeStyle = INK.tick; marker(c, lx + 4, box.y0 + 10, 0, 3.5, false); c.fillText("mixed", lx + 12, box.y0 + 10);
  }
  function drawEigen() {
    const s = osc.s.eigen, c = s.begin(); const { w, h } = s; const p = M.p;
    const big = s.canvas.parentElement.classList.contains("is-max");
    const box = { x0: big ? 64 : 52, y0: 26, x1: w - 64, y1: h - 22 };
    if (!S.mode) { noteFor("eigen", M.modes.length ? "" : "no GYRE output for this model"); $("#sm-eigen .sm-val").textContent = ""; return; }
    noteFor("eigen", "");
    const m = S.mode, xi0 = eigen(S.i, m);
    // weighted by r sqrt(rho): the quantity whose square integrates to the mode energy
    const xi = xi0.map((v, k) => v * m.xg[k] * Math.sqrt(10 ** p.logRho[k]));
    const peak = Math.max(...xi.map(Math.abs)) || 1;
    const X = xScale(box), Y = scale("lin", -1.1, 1.1, box.y1, box.y0);
    frame(c, box, X, Y, { xLabels: true, nx: big ? 8 : 4, ny: big ? 5 : 3 });
    c.save(); clipBox(c, box);
    shadeZones(c, box, X, p.conv, "rgba(127,220,255,0.08)");
    c.strokeStyle = INK.axis; c.beginPath(); c.moveTo(box.x0, Y.f(0)); c.lineTo(box.x1, Y.f(0)); c.stroke();
    c.strokeStyle = ELL_COLOR[m.l]; c.lineWidth = 1.6;
    polyline(c, m.xg, xi.map((v) => v / peak), X, Y);
    c.restore();
    $("#sm-eigen .sm-val").textContent = `ℓ=${m.l}  n=${m.npg}  ν=${m.nu >= 100 ? m.nu.toFixed(1) : m.nu.toPrecision(3)} μHz`;
  }

  // ------------------------------------------------------------------ selection
  function defaultMode(modes) {
    if (!modes.length) return null;
    const nm = T.numax[S.i];
    const pick = (l) => { let best = null, bd = Infinity; for (const m of modes) { if (m.l !== l) continue; const d = Math.abs(m.nu - nm); if (d < bd) { bd = d; best = m; } } return best; };
    return pick(1) || pick(0) || modes[0];
  }
  function select(i, keepMode) {
    i = clamp(i, 0, T.n - 1);
    S.i = i;
    M = model(i);
    if (!keepMode || !S.mode || !M.modes.includes(S.mode)) {
      const prev = S.mode;
      S.mode = prev && keepMode ? (M.modes.find((m) => m.l === prev.l && m.npg === prev.npg) || defaultMode(M.modes)) : defaultMode(M.modes);
    }
    updateStats();
    drawHR(); drawStrip();
    prepareInterior(); updateModeCard(); drawInterior(0); startAnim();
    drawProfiles(); drawOsc();
    history.replaceState(null, "", `#m${T.model ? T.model[i] : i}`);
  }
  function selectMode(m) {
    S.mode = m;
    prepareInterior(); updateModeCard(); drawInterior(0); startAnim();
    drawOsc();
  }
  function stepMode(d) {
    if (!M.modes.length || !S.mode) return;
    const k = M.modes.indexOf(S.mode);
    selectMode(M.modes[clamp(k + d, 0, M.modes.length - 1)]);
  }

  // ------------------------------------------------------------------ wiring
  function wire() {
    hr.s = surface($("#hr-canvas"));
    strip.s = surface($("#strip-canvas"));
    int_.s = surface($("#int-canvas"));
    for (const q of PROF) prof.s[q.id] = surface($(`#sm-${q.id} canvas`));
    for (const id of ["prop", "echelle", "inertia", "eigen"]) osc.s[id] = surface($(`#sm-${id} canvas`));

    const ro = new ResizeObserver((entries) => {
      for (const e of entries) {
        const el = e.target;
        if (el.id === "hr-body") drawHR();
        else if (el.id === "strip") drawStrip();
        else if (el.id === "int-body") drawInterior(0);
        else if (el.id === "prof-grid") drawProfiles();
        else if (el.id === "osc-grid") drawOsc();
      }
    });
    for (const id of ["hr-body", "strip", "int-body", "prof-grid", "osc-grid"]) ro.observe($("#" + id));

    // HR: hover and click on models
    const hrc = $("#hr-canvas");
    hrc.addEventListener("pointermove", (e) => {
      const r = hrc.getBoundingClientRect();
      const i = hrNearest(e.clientX - r.left, e.clientY - r.top);
      if (i !== S.hover) { S.hover = i; drawHR(); drawStrip(); }
      hrc.style.cursor = i === null ? "default" : "pointer";
      $("#hr-readout").textContent = i === null ? "" : readoutFor(i);
    });
    hrc.addEventListener("pointerleave", () => { S.hover = null; drawHR(); drawStrip(); $("#hr-readout").textContent = ""; });
    hrc.addEventListener("click", (e) => { const r = hrc.getBoundingClientRect(); const i = hrNearest(e.clientX - r.left, e.clientY - r.top); if (i !== null) select(i, true); });

    // strip: scrub
    const st = $("#strip");
    let dragging = false;
    const stripPick = (e) => { const r = st.getBoundingClientRect(); return stripIndex(e.clientX - r.left); };
    st.addEventListener("pointerdown", (e) => { dragging = true; st.setPointerCapture(e.pointerId); select(stripPick(e), true); });
    st.addEventListener("pointermove", (e) => {
      const i = stripPick(e);
      if (dragging) { if (i !== S.i) select(i, true); }
      else if (i !== S.hover) { S.hover = i; drawStrip(); drawHR(); }
      $("#strip-readout").textContent = readoutFor(i);
    });
    st.addEventListener("pointerup", () => { dragging = false; });
    st.addEventListener("pointerleave", () => { dragging = false; S.hover = null; drawStrip(); drawHR(); $("#strip-readout").textContent = ""; });

    // profiles: synced crosshair
    for (const q of PROF) {
      const cv = prof.s[q.id].canvas;
      cv.addEventListener("pointermove", (e) => {
        const r = cv.getBoundingClientRect();
        const big = cv.parentElement.classList.contains("is-max");
        const box = { x0: big ? 64 : 50, x1: r.width - 40 };
        const X = xScale(box);
        const v = X.inv(e.clientX - r.left);
        prof.hoverX = v >= X.lo && v <= X.hi ? v : null;
        drawProfiles();
        $("#prof-readout").textContent = prof.hoverX === null ? "" : `r/R = ${prof.hoverX.toFixed(3)}`;
      });
      cv.addEventListener("pointerleave", () => { prof.hoverX = null; drawProfiles(); $("#prof-readout").textContent = ""; });
    }
    // oscillation panels: click a mode
    for (const id of ["echelle", "inertia"]) {
      const cv = osc.s[id].canvas;
      const near = (e) => { const r = cv.getBoundingClientRect(); const px = e.clientX - r.left, py = e.clientY - r.top; let best = 10, bm = null; for (const q of osc.hit) { if (q.panel !== id) continue; const d = Math.hypot(q.x - px, q.y - py); if (d < best) { best = d; bm = q.m; } } return bm; };
      cv.addEventListener("pointermove", (e) => { const m = near(e); cv.style.cursor = m ? "pointer" : "default"; $("#osc-readout").textContent = m ? `ℓ=${m.l}  n=${m.npg}  ν=${m.nu >= 100 ? m.nu.toFixed(1) : m.nu.toPrecision(3)} μHz  E=${sci(m.E, 2)}${m.type !== "p" ? `  ${m.type === "g" ? "g" : "mixed"}` : ""}` : ""; });
      cv.addEventListener("pointerleave", () => { $("#osc-readout").textContent = ""; });
      cv.addEventListener("click", (e) => { const m = near(e); if (m) selectMode(m); });
    }
    // expand buttons
    for (const b of $$(".sm-zoom")) b.addEventListener("click", (e) => {
      e.stopPropagation();
      const sm = b.closest(".sm"), grid = sm.parentElement;
      const on = !sm.classList.contains("is-max");
      $$(".sm", grid).forEach((el) => el.classList.remove("is-max"));
      grid.classList.toggle("has-max", on);
      if (on) sm.classList.add("is-max");
      requestAnimationFrame(() => { if (grid.id === "prof-grid") drawProfiles(); else drawOsc(); });
    });
    // header controls
    $("#btn-prev").addEventListener("click", () => select(S.i - 1, true));
    $("#btn-next").addEventListener("click", () => select(S.i + 1, true));
    let playTimer = null;
    const setPlay = (on) => {
      S.playing = on; $("#btn-play").setAttribute("aria-pressed", on);
      $("#btn-play .ico-play").style.display = on ? "none" : ""; $("#btn-play .ico-pause").style.display = on ? "" : "none";
      clearInterval(playTimer);
      if (on) playTimer = setInterval(() => { if (S.i >= T.n - 1) setPlay(false); else select(S.i + 1, true); }, 900);
    };
    $("#btn-play").addEventListener("click", () => setPlay(!S.playing));
    $("#btn-pulse").addEventListener("click", () => { S.pulsate = !S.pulsate; $("#btn-pulse").setAttribute("aria-pressed", S.pulsate); drawInterior(0); startAnim(); });
    $("#btn-pulse").setAttribute("aria-pressed", S.pulsate);
    for (const b of $$("[data-xaxis]")) b.addEventListener("click", () => {
      S.xlog = b.dataset.xaxis === "log";
      $$("[data-xaxis]").forEach((x) => x.classList.toggle("on", x === b));
      drawStrip(); drawProfiles(); drawOsc();
    });
    $("#btn-info").addEventListener("click", () => $("#info").classList.toggle("open"));
    $("#info .close").addEventListener("click", () => $("#info").classList.remove("open"));
    $("#info").addEventListener("click", (e) => { if (e.target === $("#info")) $("#info").classList.remove("open"); });
    document.addEventListener("keydown", (e) => {
      if (e.target.matches("input, textarea")) return;
      if (e.key === "ArrowLeft") { select(S.i - 1, true); e.preventDefault(); }
      else if (e.key === "ArrowRight") { select(S.i + 1, true); e.preventDefault(); }
      else if (e.key === "[") stepMode(-1);
      else if (e.key === "]") stepMode(1);
      else if (e.key === " ") { e.preventDefault(); $("#btn-pulse").click(); }
      else if (e.key === "Escape") $("#info").classList.remove("open");
    });
    document.addEventListener("visibilitychange", () => { if (!document.hidden) startAnim(); });
    // KaTeX titles
    for (const [sel, s] of [
      ["#hr-body .ax-x", "T_{\\mathrm{eff}}\\ [\\mathrm{K}]"], ["#hr-body .ax-y", "L/L_\\odot"],
      ["#strip .ax", "r/R"],
      ["#sm-prop .ax-y", "\\nu\\ [\\mu\\mathrm{Hz}]"], ["#sm-echelle .ax-y", "\\nu\\ [\\mu\\mathrm{Hz}]"], ["#sm-echelle .ax-x", "\\nu \\bmod \\Delta\\nu"],
      ["#sm-inertia .ax-y", "E_{\\mathrm{norm}}"], ["#sm-inertia .ax-x", "\\nu\\ [\\mu\\mathrm{Hz}]"], ["#sm-eigen .ax-y", "\\xi_r\\, r\\sqrt{\\rho}\\ (\\mathrm{normalised})"],
      ["#st-age .stat-lbl", "t"], ["#st-teff .stat-lbl", "T_{\\mathrm{eff}}"], ["#st-l .stat-lbl", "L"], ["#st-r .stat-lbl", "R"], ["#st-logg .stat-lbl", "\\log g"],
      ["#st-xc .stat-lbl", "X_c"], ["#st-yc .stat-lbl", "Y_c"], ["#st-mhe .stat-lbl", "M_{\\mathrm{He}}"], ["#st-numax .stat-lbl", "\\nu_{\\max}"], ["#st-dnu .stat-lbl", "\\Delta\\nu"],
    ]) tex($(sel), s);
    for (const q of PROF) tex($(`#sm-${q.id} .ax-y`), q.title);
    for (const el of $$(".ax-x.rr")) tex(el, "r/R");
  }
  function readoutFor(i) {
    const [a, u] = age(T.age[i]);
    return `model ${T.model ? T.model[i] : i + 1}  ${T.phase[i]}  ${a} ${u}  ${Math.round(10 ** T.logTeff[i])} K`;
  }

  // ------------------------------------------------------------------ loading
  const DATA_URL = new URLSearchParams(location.search).get("data") || "https://raw.githubusercontent.com/AndreasWNeitzel/stellar-explorer-data/main/stellar_data_real.h5";
  const msg = (m) => { $("#ov-msg").textContent = m; };
  async function load() {
    try {
      const res = await fetch(DATA_URL);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const total = +res.headers.get("Content-Length") || 0;
      const reader = res.body.getReader(); const chunks = []; let got = 0;
      for (;;) {
        const { done, value } = await reader.read(); if (done) break;
        chunks.push(value); got += value.length;
        $("#ov-bar i").style.width = total ? `${(100 * got) / total}%` : "40%";
        msg(total ? `loading ${(got / 1e6).toFixed(1)} of ${(total / 1e6).toFixed(1)} MB` : `loading ${(got / 1e6).toFixed(1)} MB`);
      }
      const buf = new Uint8Array(got); let o = 0; for (const ch of chunks) { buf.set(ch, o); o += ch.length; }
      msg("reading the track");
      await new Promise((r) => setTimeout(r, 30));
      loadTrack(buf.buffer);
      wire();
      $("#app").classList.add("visible");
      $("#overlay").classList.add("hidden");
      const want = (location.hash.match(/^#m(\d+)$/) || [])[1], wantI = (location.hash.match(/^#i(\d+)$/) || [])[1];
      let start = Math.floor(T.n * 0.06);
      if (want && T.model) { const k = T.model.indexOf(+want); if (k >= 0) start = k; }
      if (wantI) start = clamp(+wantI, 0, T.n - 1);
      requestAnimationFrame(() => select(start));
    } catch (e) {
      msg(`could not load the data: ${e.message}`);
      $("#spinner").style.display = "none";
      console.error(e);
    }
  }
  load();
})();
