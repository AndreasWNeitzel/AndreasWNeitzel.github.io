// Ringing-star demonstration for the field guide (_includes/seismo-demo.html): a rotating star
// whose surface moves in one oscillation mode, beside the model spectrum of such a star from the
// asteroseismic scaling relations. Colours come only from the site tokens (assets/js/tokens.js).
(() => {
  "use strict";
  const root = document.querySelector("[data-seismo]");
  const T = window.siteTokens;
  if (!root || !T) return;
  const $ = (s) => root.querySelector(s);
  const TAU = 2 * Math.PI;
  const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);
  const lerp = (a, b, k) => a + (b - a) * k;
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");

  // ------------------------------------------------------------------ physics
  // nu_max follows the acoustic cut-off (Brown et al. 1991, ApJ 368, 599) and Delta nu the square
  // root of the mean density (Kjeldsen and Bedding 1995, A&A 293, 87); solar references from
  // Huber et al. (2011, ApJ 743, 143). Teff stays at the solar value.
  const NUMAX_SUN = 3090, DNU_SUN = 135.1, TEFF_SUN = 5777, TEFF = 5777;
  const numaxOf = (M, R) => NUMAX_SUN * (M / (R * R)) * Math.pow(TEFF / TEFF_SUN, -0.5);
  const dnuOf = (M, R) => DNU_SUN * Math.sqrt(M / (R * R * R));
  // Visibilities V_l^2 measured in Kepler red giants and the envelope FWHM 0.66 nu_max^0.88
  // (Mosser et al. 2012, A&A 537, A30).
  const VIS = [1, 1.35, 0.64, 0.071];
  const HALF = 3; // the spectrum spans nu_max +- 3 Delta nu

  // nu_nl = Delta nu (n + l/2 + eps - d_0l). Below Delta nu = 20 uHz, eps and d_0l follow the
  // red-giant universal pattern (Mosser et al. 2011, A&A 525, L9); at 135.1 uHz they are the
  // Sun's, from BiSON frequencies (Broomhall et al. 2009, MNRAS 396, L100); linear in
  // log Delta nu between and held beyond.
  function comb(dnu) {
    const L = Math.log10(dnu), w = clamp((L - 1.30103) / 0.82963, 0, 1);
    const giant = [0.634 + 0.546 * L, -0.056 - 0.002 * L, 0.131 - 0.033 * L, 0.28];
    return giant.map((g, i) => lerp(g, [1.456, 0.023, 0.067, 0.141][i], w));
  }

  // Granulation: two super-Lorentzians with exponent 4 whose rms amplitude and characteristic
  // frequencies scale with nu_max (Kallinger et al. 2014, A&A 570, A41), in ppm^2 per uHz.
  function granulation(numax) {
    const a2 = Math.pow(3382 * Math.pow(numax, -0.609), 2) * (2 * Math.SQRT2) / Math.PI;
    const b1 = 0.317 * Math.pow(numax, 0.97), b2 = 0.948 * Math.pow(numax, 0.992);
    return (nu) => {
      const u = (nu / b1) ** 4, v = (nu / b2) ** 4;
      return a2 / b1 / (1 + u) + a2 / b2 / (1 + v);
    };
  }

  function model(M, R) {
    const numax = numaxOf(M, R), dnu = dnuOf(M, R), [eps, d1, d2, d3] = comb(dnu), d0l = [0, d1, d2, d3];
    const sig = (0.66 * Math.pow(numax, 0.88)) / 2.3548, bg = granulation(numax), B = bg(numax);
    // Display choices: radial peaks ten times the background at nu_max, so that both read on a
    // linear axis (in real data the ratio grows with the length of the time series), and
    // linewidths near 1 uHz for the Sun that narrow as nu_max^0.5 towards red giants.
    const H0 = 10 * B, lo = numax - HALF * dnu, hi = numax + HALF * dnu, peaks = [];
    for (let n = Math.floor(lo / dnu - eps) - 2; n <= Math.ceil(hi / dnu - eps) + 1; n += 1) {
      for (let l = 0; l <= 3; l += 1) {
        const nu = dnu * (n + l / 2 + eps - d0l[l]);
        if (nu <= 0 || nu < lo - dnu / 2 || nu > hi + dnu / 2) continue;
        const env = Math.exp(-0.5 * ((nu - numax) / sig) ** 2);
        peaks.push({ n, l, nu, env, h: VIS[l] * env * H0 });
      }
    }
    peaks.sort((a, b) => a.nu - b.nu);
    const top = peaks.reduce((a, b) => (b.h > a.h ? b : a));
    return { numax, dnu, sig, bg, H0, lo, hi, peaks, top, white: 0.03 * B, gamma: Math.sqrt(numax / NUMAX_SUN) };
  }

  // On screen a mode at the Sun's nu_max makes 0.55 cycles per second, and stars with a lower
  // nu_max ring more slowly on screen too.
  const fShow = (nu, numax) => 0.55 * (nu / numax) * Math.pow(numax / NUMAX_SUN, 0.18);

  // ---------------------------------------------------------------- harmonics
  // Associated Legendre P_l^m(x), 0 <= m <= l, by the standard three-term recurrence.
  function legendreP(l, m, x) {
    let pmm = 1;
    if (m > 0) {
      const s = Math.sqrt(Math.max(0, 1 - x * x));
      for (let i = 1, f = 1; i <= m; i += 1, f += 2) pmm *= -f * s;
    }
    if (l === m) return pmm;
    let pmmp1 = x * (2 * m + 1) * pmm;
    for (let ll = m + 2; ll <= l; ll += 1) {
      const pll = (x * (2 * ll - 1) * pmmp1 - (ll + m - 1) * pmm) / (ll - m);
      pmm = pmmp1;
      pmmp1 = pll;
    }
    return pmmp1;
  }
  // (l, |m|) for l <= 3, the orthonormal-harmonic factor of each, and the peak |P_l^m| that
  // scales a single mode to unit amplitude.
  const LM = [];
  for (let l = 0; l <= 3; l += 1) for (let m = 0; m <= l; m += 1) LM.push([l, m]);
  const lmIdx = (l, m) => (l * (l + 1)) / 2 + Math.abs(m);
  const fac = (k) => (k < 2 ? 1 : k * fac(k - 1));
  const NORM = LM.map(([l, m]) => Math.sqrt(((2 * l + 1) / (4 * Math.PI)) * (fac(l - m) / fac(l + m))));
  const PMAX = LM.map(([l, m]) => {
    let mx = 0;
    for (let k = 0; k <= 720; k += 1) mx = Math.max(mx, Math.abs(legendreP(l, m, Math.cos((Math.PI * k) / 720))));
    return mx;
  });
  // Colatitudes where P_l^m(cos theta) changes sign: the nodal circles.
  function nodeRings(l, m) {
    const out = [];
    let pt = 1e-4, pv = legendreP(l, m, Math.cos(pt));
    for (let k = 1; k <= 720; k += 1) {
      const th = k === 720 ? Math.PI - 1e-4 : (Math.PI * k) / 720, v = legendreP(l, m, Math.cos(th));
      if (v < 0 !== pv < 0) out.push(pt + ((th - pt) * pv) / (pv - v));
      pt = th;
      pv = v;
    }
    return out;
  }

  // Surface mesh, 3 degrees a side: rows of colatitude, columns of body longitude.
  const NTH = 60, NPH = 120, ROW = NPH + 1, NV = (NTH + 1) * ROW;
  const sinT = new Float64Array(NTH + 1), cosT = new Float64Array(NTH + 1), PN = new Float64Array((NTH + 1) * 10);
  for (let i = 0; i <= NTH; i += 1) {
    sinT[i] = Math.sin((Math.PI * i) / NTH);
    cosT[i] = Math.cos((Math.PI * i) / NTH);
    for (let q = 0; q < 10; q += 1) PN[i * 10 + q] = NORM[q] * legendreP(LM[q][0], LM[q][1], cosT[i]);
  }
  const CK = [], SK = [];
  for (let k = 0; k <= 3; k += 1) {
    CK.push(Float64Array.from({ length: ROW }, (_, j) => Math.cos((k * TAU * j) / NPH)));
    SK.push(Float64Array.from({ length: ROW }, (_, j) => Math.sin((k * TAU * j) / NPH)));
  }

  // ------------------------------------------------------------------ colours
  const pc = document.createElement("canvas").getContext("2d", { willReadFrequently: true });
  pc.canvas.width = pc.canvas.height = 1;
  function rgb(name) {
    pc.clearRect(0, 0, 1, 1);
    pc.fillStyle = "#000";
    pc.fillStyle = T.colour(name);
    pc.fillRect(0, 0, 1, 1);
    return Array.from(pc.getImageData(0, 0, 1, 1).data.slice(0, 3));
  }
  const lin = (c) => ((c /= 255) <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4));
  const srgb = (v) => Math.round(255 * (v <= 0.0031308 ? 12.92 * Math.max(v, 0) : 1.055 * Math.pow(Math.min(v, 1), 1 / 2.4) - 0.055));
  function oklab(c) {
    const [r, g, b] = c.map(lin);
    const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
    const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
    const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
    return [0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s, 1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s, 0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s];
  }
  function linFromOklab([L, a, b]) {
    const l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3;
    const m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3;
    const s = (L - 0.0894841775 * a - 1.291485548 * b) ** 3;
    return [4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s, -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s];
  }

  // Surface colour: a warm photosphere blended towards --cat-0 where the surface is pulled in and
  // --cat-2 where it is pushed out, then limb-darkened in linear light with coefficients that are
  // larger in blue light than in red, as on the Sun (Neckel and Labs 1994, Sol. Phys. 153, 91).
  const NXI = 129, NMU = 49, LIMB = [0.55, 0.66, 0.8];
  let LUT = [], C = {};
  function palette() {
    const ink = rgb("--ink"), bg = rgb("--bg"), lum = (c) => 0.2126 * lin(c[0]) + 0.7152 * lin(c[1]) + 0.0722 * lin(c[2]);
    const dark = lum(bg) < lum(ink), paper = oklab(dark ? ink : bg), amber = oklab(rgb("--cat-1"));
    const mid = amber.map((v, i) => lerp(v, paper[i], 0.5)), ends = [oklab(rgb("--cat-0")), oklab(rgb("--cat-2"))];
    LUT = new Array(NXI * NMU);
    for (let k = 0; k < NXI; k += 1) {
      const x = -1 + (2 * k) / (NXI - 1), c = linFromOklab(mid.map((v, i) => lerp(v, ends[x < 0 ? 0 : 1][i], Math.abs(x))));
      for (let j = 0; j < NMU; j += 1) {
        const mu = j / (NMU - 1);
        LUT[k * NMU + j] = `rgb(${c.map((v, i) => srgb(v * (1 - LIMB[i] * (1 - mu)))).join(",")})`;
      }
    }
    const m = linFromOklab(mid).map(srgb), deep = dark ? bg : ink, acc = rgb("--accent");
    const css = (c, a) => `rgba(${c.join(",")},${a})`;
    const fam = getComputedStyle(root).getPropertyValue("--mono").trim() || "monospace";
    C = {
      glow: css(m, dark ? 0.34 : 0.2), glow0: css(m, 0), grid: css(deep, dark ? 0.16 : 0.12), node: css(deep, 0.5),
      ink2: T.colour("--ink-2"), muted: T.colour("--muted"), line: T.colour("--line-strong"),
      accent: T.colour("--accent"), accent2: T.colour("--accent-2"),
      fill: css(acc, dark ? 0.13 : 0.09), band: css(rgb("--context"), 0.6),
      cin: LUT[NMU - 1], cmid: LUT[((NXI - 1) / 2) * NMU + NMU - 1], cout: LUT[NXI * NMU - 1],
      font: (px) => `500 ${px}px ${fam}`,
    };
  }

  // ------------------------------------------------------------------- voices
  // A voice is what the star plays: one mode, P_l^|m|(cos theta) cos(m phi - omega t), whose
  // pattern travels around the axis when m is not zero, or many modes near nu_max whose complex
  // amplitudes wander as convection excites and damps them.
  const S = { M: 1, R: 1, star: null, l: 1, m: 0, sel: null, hover: null, mix: false, playing: !reduced.matches, t: 0, spin: 0.6 };
  let voice = null, prev = null, fade0 = 0, mixVoice = null;
  const FADE = 0.35, TAU_EXC = 4;

  function mulberry(seed) {
    return () => {
      seed = (seed + 0x6d2b79f5) | 0;
      let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function gauss(r) {
    const a = Math.sqrt(-2 * Math.log(Math.max(r(), 1e-12))), b = TAU * r();
    return [a * Math.cos(b), a * Math.sin(b)];
  }
  function one(peak, m) {
    const l = peak.l, q = lmIdx(l, m);
    return { kind: "one", l, m, q, peak, k: 1 / (NORM[q] * PMAX[q]), f: fShow(peak.nu, S.star.numax), ph: 0, rings: nodeRings(l, Math.abs(m)) };
  }
  // The three peaks of each degree 0 to 2 nearest nu_max and the nearest of degree 3, each with
  // all 2l + 1 values of m; amplitudes and phases carry over when the star changes.
  function several(old) {
    const st = S.star, rnd = old ? old.rnd : mulberry(20261025), pick = [], comps = [];
    for (let l = 0; l <= 3; l += 1) {
      const own = st.peaks.filter((p) => p.l === l).sort((a, b) => Math.abs(a.nu - st.numax) - Math.abs(b.nu - st.numax));
      pick.push(...own.slice(0, l < 3 ? 3 : 1));
    }
    let power = 0;
    for (const p of pick) {
      for (let m = -p.l; m <= p.l; m += 1) {
        const sd = Math.sqrt(p.env), g = gauss(rnd);
        comps.push({ q: lmIdx(p.l, m), m, sd, f: fShow(p.nu, st.numax), ph: 0, zr: sd * g[0] * Math.SQRT1_2, zi: sd * g[1] * Math.SQRT1_2 });
        power += p.env;
      }
    }
    if (old && old.comps.length === comps.length) {
      comps.forEach((c, i) => {
        const o = old.comps[i], k = o.sd > 0 ? c.sd / o.sd : 1;
        Object.assign(c, { ph: o.ph, zr: o.zr * k, zi: o.zi * k });
      });
    }
    return { kind: "mix", pick, comps, rnd, norm: 0.55 / Math.sqrt(power / (8 * Math.PI)) };
  }
  // Coefficients of cos(|m| phi) and sin(|m| phi) for each (l, |m|), weighted by w.
  function addCoef(v, w, out) {
    if (v.kind === "one") {
      out[2 * v.q] += w * v.k * Math.cos(v.ph);
      out[2 * v.q + 1] += w * v.k * Math.sign(v.m) * Math.sin(v.ph);
      return;
    }
    const g = w * v.norm;
    for (const c of v.comps) {
      const cp = Math.cos(c.ph), sp = Math.sin(c.ph);
      out[2 * c.q] += g * (c.zr * cp + c.zi * sp);
      out[2 * c.q + 1] += g * Math.sign(c.m) * (c.zr * sp - c.zi * cp);
    }
  }
  function advance(v, dt) {
    if (!v) return;
    if (v.kind === "one") {
      v.ph += TAU * v.f * dt;
      return;
    }
    const a = Math.exp(-dt / TAU_EXC), b = Math.sqrt(1 - a * a) * Math.SQRT1_2;
    for (const c of v.comps) {
      const g = gauss(v.rnd);
      c.ph += TAU * c.f * dt;
      c.zr = c.zr * a + c.sd * b * g[0];
      c.zi = c.zi * a + c.sd * b * g[1];
    }
  }
  function fadeK() {
    if (!prev) return 1;
    const k = clamp((S.t - fade0) / FADE, 0, 1);
    if (k >= 1) prev = null;
    return k * k * (3 - 2 * k);
  }

  // --------------------------------------------------------------------- star
  // Spin axis inclined 70 degrees to the line of sight, drawn displacement 6.5 per cent of the
  // radius, one turn every 30 s.
  const INC = (70 * Math.PI) / 180, CA = Math.sin(INC), SA = Math.cos(INC), AMP = 0.065, SPIN = TAU / 30;
  const VX = new Float64Array(NV), VY = new Float64Array(NV), VZ = new Float64Array(NV), VA = new Float64Array(NV);
  const coef = new Float64Array(20), head = new Int32Array(NXI * NMU), link = new Int32Array(NTH * NPH);
  const star = { cv: $(".sd-stage--star canvas"), w: 0 };
  star.ctx = star.cv.getContext("2d");

  function drawStar() {
    const { ctx, w } = star;
    if (!w || !voice) return;
    const cx = w / 2, cy = w * 0.52, R = w * 0.35, cs = Math.cos(S.spin), ss = Math.sin(S.spin);
    ctx.clearRect(0, 0, w, w);

    // Displace the mesh radially by the field and turn it about the spin axis.
    coef.fill(0);
    const k = fadeK();
    if (prev) addCoef(prev, 1 - k, coef);
    addCoef(voice, k, coef);
    const act = [], ck = [], sk = [], c0 = [], c1 = [];
    for (let q = 0; q < 10; q += 1) {
      if (!coef[2 * q] && !coef[2 * q + 1]) continue;
      act.push(q);
      ck.push(CK[LM[q][1]]);
      sk.push(SK[LM[q][1]]);
      c0.push(coef[2 * q]);
      c1.push(coef[2 * q + 1]);
    }
    const na = act.length;
    for (let i = 0, v = 0; i <= NTH; i += 1) {
      for (let j = 0; j <= NPH; j += 1, v += 1) {
        let xi = 0;
        for (let a = 0; a < na; a += 1) xi += PN[i * 10 + act[a]] * (c0[a] * ck[a][j] + c1[a] * sk[a][j]);
        const r = 1 + AMP * clamp(xi, -1.6, 1.6), rs = r * sinT[i], y = r * cosT[i];
        const x = rs * (CK[1][j] * cs - SK[1][j] * ss), z = -rs * (SK[1][j] * cs + CK[1][j] * ss);
        VX[v] = x;
        VY[v] = y * CA - z * SA;
        VZ[v] = y * SA + z * CA;
        VA[v] = xi;
      }
    }

    const glow = ctx.createRadialGradient(cx, cy, R * 0.8, cx, cy, R * 1.45);
    glow.addColorStop(0, C.glow);
    glow.addColorStop(1, C.glow0);
    ctx.fillStyle = glow;
    ctx.fillRect(0, 0, w, w);
    const axis = (y0, y1) => {
      ctx.save();
      ctx.setLineDash([4, 4]);
      ctx.strokeStyle = C.muted;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(cx, cy - y0 * R * CA);
      ctx.lineTo(cx, cy - y1 * R * CA);
      ctx.stroke();
      ctx.restore();
    };
    axis(-1.3, 1.3);

    // Facets that face the viewer, shaded by limb darkening with the cosine of their normal to the
    // line of sight, are gathered by colour and filled one colour at a time; each facet is grown
    // by half a pixel about its centre so that no seams show between neighbours.
    head.fill(-1);
    for (let i = 0; i < NTH; i += 1) {
      for (let j = 0; j < NPH; j += 1) {
        const a = i * ROW + j, b = a + 1, c = a + ROW + 1, d = a + ROW;
        const ex = VX[c] - VX[a], ey = VY[c] - VY[a], ez = VZ[c] - VZ[a], fx = VX[d] - VX[b], fy = VY[d] - VY[b], fz = VZ[d] - VZ[b];
        const nx = ey * fz - ez * fy, ny = ez * fx - ex * fz;
        let nz = ex * fy - ey * fx;
        if (nx * (VX[a] + VX[c]) + ny * (VY[a] + VY[c]) + nz * (VZ[a] + VZ[c]) < 0) nz = -nz;
        if (nz <= 0) continue;
        const mu = nz / Math.hypot(nx, ny, nz), xi = clamp((VA[a] + VA[b] + VA[c] + VA[d]) * 0.25, -1, 1);
        const bin = Math.round((xi + 1) * 0.5 * (NXI - 1)) * NMU + Math.round(mu * (NMU - 1)), id = i * NPH + j;
        link[id] = head[bin];
        head[bin] = id;
      }
    }
    let mx = 0, my = 0;
    const corner = (v, first) => {
      const x = cx + R * VX[v], y = cy - R * VY[v], dx = x - mx, dy = y - my, g = 0.5 / (Math.sqrt(dx * dx + dy * dy) + 1e-6);
      if (first) ctx.moveTo(x + dx * g, y + dy * g);
      else ctx.lineTo(x + dx * g, y + dy * g);
    };
    for (let bin = 0; bin < head.length; bin += 1) {
      if (head[bin] < 0) continue;
      ctx.beginPath();
      for (let id = head[bin]; id >= 0; id = link[id]) {
        const i = (id / NPH) | 0, a = i * ROW + id - i * NPH, b = a + 1, c = a + ROW + 1, d = a + ROW;
        mx = cx + R * 0.25 * (VX[a] + VX[b] + VX[c] + VX[d]);
        my = cy - R * 0.25 * (VY[a] + VY[b] + VY[c] + VY[d]);
        corner(a, true);
        corner(b, false);
        corner(c, false);
        corner(d, false);
        ctx.closePath();
      }
      ctx.fillStyle = LUT[bin];
      ctx.fill();
    }

    // Graticule every 30 degrees, carried by the moving surface.
    const pen = (v, on) => {
      if (VZ[v] <= 0.02) return false;
      if (on) ctx.lineTo(cx + R * VX[v], cy - R * VY[v]);
      else ctx.moveTo(cx + R * VX[v], cy - R * VY[v]);
      return true;
    };
    ctx.strokeStyle = C.grid;
    ctx.lineWidth = 0.75;
    ctx.beginPath();
    for (let i = 10; i < NTH; i += 10) for (let j = 0, on = false; j <= NPH; j += 1) on = pen(i * ROW + j, on);
    for (let j = 0; j < NPH; j += 10) for (let i = 0, on = false; i <= NTH; i += 1) on = pen(i * ROW + j, on);
    ctx.stroke();

    // Nodal lines of a single mode: circles of latitude where P_l^m vanishes and, when m is not
    // zero, 2|m| meridians where cos(m phi - omega t) vanishes, which travel with the pattern.
    if (voice.kind === "one" && voice.l > 0) {
      const curve = (fn, steps) => {
        for (let s = 0, on = false; s <= steps; s += 1) {
          const [th, ph] = fn(s / steps), x = Math.sin(th) * Math.cos(ph + S.spin), z = -Math.sin(th) * Math.sin(ph + S.spin), y = Math.cos(th);
          const X = cx + R * x, Y = cy - R * (y * CA - z * SA);
          if (y * SA + z * CA > 0.02) {
            if (on) ctx.lineTo(X, Y);
            else ctx.moveTo(X, Y);
            on = true;
          } else on = false;
        }
      };
      ctx.globalAlpha = k;
      ctx.strokeStyle = C.node;
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      for (const th of voice.rings) curve((u) => [th, u * TAU], 120);
      for (let n = 0; n < 2 * Math.abs(voice.m); n += 1) curve((u) => [u * Math.PI, (Math.PI / 2 + n * Math.PI + voice.ph) / voice.m], 60);
      ctx.stroke();
      ctx.globalAlpha = 1;
    }

    // Visible end of the axis and an arrow for the sense of spin.
    axis(1.04, 1.3);
    const arc = [];
    for (let n = 0; n <= 40; n += 1) {
      const ph = 0.5 + n / 8, x = 0.4567 * Math.cos(ph), z = -0.4567 * Math.sin(ph), y = 1.0227;
      arc.push([cx + R * x, cy - R * (y * CA - z * SA)]);
    }
    ctx.strokeStyle = ctx.fillStyle = C.accent2;
    ctx.lineWidth = 1.6;
    ctx.beginPath();
    arc.forEach(([X, Y], n) => (n ? ctx.lineTo(X, Y) : ctx.moveTo(X, Y)));
    ctx.stroke();
    const [tx, ty] = arc[40], [px, py] = arc[38], ul = Math.hypot(tx - px, ty - py) || 1, ux = (tx - px) / ul, uy = (ty - py) / ul;
    ctx.beginPath();
    ctx.moveTo(tx + 2 * ux, ty + 2 * uy);
    ctx.lineTo(tx - 7 * ux - 4 * uy, ty - 7 * uy + 4 * ux);
    ctx.lineTo(tx - 7 * ux + 4 * uy, ty - 7 * uy - 4 * ux);
    ctx.fill();

    // Key to the colours.
    const ly = w - 9, lw = Math.min(56, w * 0.2), lg = ctx.createLinearGradient(22, 0, 22 + lw, 0);
    lg.addColorStop(0, C.cin);
    lg.addColorStop(0.5, C.cmid);
    lg.addColorStop(1, C.cout);
    ctx.font = C.font(10);
    ctx.textBaseline = "middle";
    ctx.textAlign = "left";
    ctx.fillStyle = C.muted;
    ctx.fillText("in", 4, ly);
    ctx.fillText("out", 27 + lw, ly);
    ctx.fillStyle = lg;
    ctx.fillRect(22, ly - 2.5, lw, 5);
  }

  // ----------------------------------------------------------------- spectrum
  const spec = { cv: $(".sd-stage--spec canvas"), w: 0, h: 0, hits: [], top: 0, base: 0 };
  spec.ctx = spec.cv.getContext("2d");
  const fmt = (v, d) => v.toLocaleString("en-GB", { minimumFractionDigits: d, maximumFractionDigits: d });
  function niceStep(raw) {
    const p = Math.pow(10, Math.floor(Math.log10(raw))), r = raw / p;
    return p * (r < 1.5 ? 1 : r < 3 ? 2 : r < 7 ? 5 : 10);
  }
  // A symbol with an optional subscript, such as nu_max.
  function symbol(ctx, main, sub, x, y, align) {
    ctx.font = C.font(11);
    const a = ctx.measureText(main).width;
    ctx.font = C.font(8.5);
    const b = sub ? ctx.measureText(sub).width + 0.5 : 0, x0 = align === "right" ? x - a - b : x - (a + b) / 2;
    ctx.textAlign = "left";
    ctx.font = C.font(11);
    ctx.fillText(main, x0, y);
    if (!sub) return;
    ctx.font = C.font(8.5);
    ctx.fillText(sub, x0 + a + 0.5, y + 3);
  }

  function drawSpec() {
    const { ctx, w, h } = spec, st = S.star;
    if (!w || !st) return;
    ctx.clearRect(0, 0, w, h);
    const x0 = 18, x1 = w - 4, top = 36, base = h - 22, lo = st.lo, hi = st.hi;
    const per = (hi - lo) / (x1 - x0), X = (nu) => x0 + (nu - lo) / per, hw = Math.max(st.gamma / 2, 1.1 * per);
    const B = (nu) => st.bg(nu) + st.white;
    const P = (nu) => st.peaks.reduce((p, k) => p + k.h / (1 + ((nu - k.nu) / hw) ** 2), B(nu));
    const fs = [];
    for (let x = x0; x <= x1; x += 0.5) fs.push(lo + (x - x0) * per);
    for (const k of st.peaks) if (k.nu > lo && k.nu < hi) fs.push(k.nu);
    fs.sort((a, b) => a - b);
    const ps = fs.map(P), ymax = Math.max(...ps) * 1.08, Y = (p) => base - (p / ymax) * (base - top);
    Object.assign(spec, { top, base });
    const trace = (fn, step) => {
      for (let x = x0; x < x1 + step; x += step) {
        const xx = Math.min(x, x1);
        ctx.lineTo(xx, Y(fn(lo + (xx - x0) * per)));
      }
    };

    // Power under the curve, the granulation band, the envelope of the dipole peaks, the curve.
    ctx.beginPath();
    ctx.moveTo(x0, base);
    fs.forEach((f, i) => ctx.lineTo(X(f), Y(ps[i])));
    ctx.lineTo(x1, base);
    ctx.fillStyle = C.fill;
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(x0, base);
    trace(B, 3);
    ctx.lineTo(x1, base);
    ctx.fillStyle = C.band;
    ctx.fill();
    ctx.save();
    ctx.setLineDash([3, 3]);
    ctx.strokeStyle = C.accent2;
    ctx.lineWidth = 1;
    ctx.beginPath();
    trace((nu) => B(nu) + VIS[1] * st.H0 * Math.exp(-0.5 * ((nu - st.numax) / st.sig) ** 2), 3);
    ctx.stroke();
    ctx.restore();
    ctx.beginPath();
    fs.forEach((f, i) => ctx.lineTo(X(f), Y(ps[i])));
    ctx.strokeStyle = C.ink2;
    ctx.lineWidth = 1.1;
    ctx.lineJoin = "round";
    ctx.stroke();

    // The peak on the star, or every peak in the mixture, and the degree above each peak.
    const marked = voice.kind === "mix" ? voice.pick : [voice.peak];
    ctx.strokeStyle = ctx.fillStyle = C.accent;
    ctx.lineWidth = 2;
    for (const p of marked) {
      if (p.nu < lo || p.nu > hi) continue;
      const x = X(p.nu), y = Y(P(p.nu));
      ctx.beginPath();
      ctx.moveTo(x, base);
      ctx.lineTo(x, y);
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(x, y, 2.6, 0, TAU);
      ctx.fill();
    }
    spec.hits = [];
    ctx.font = C.font(10);
    ctx.textBaseline = "alphabetic";
    for (const p of st.peaks) {
      if (p.nu < lo || p.nu > hi) continue;
      const x = X(p.nu), on = marked.includes(p);
      if (p.h > 0.025 * st.top.h) spec.hits.push({ p, x });
      if (p.h < 0.12 * st.top.h && !on) continue;
      ctx.fillStyle = on ? C.accent : C.muted;
      ctx.textAlign = p.l === 2 ? "right" : p.l === 0 ? "left" : "center";
      ctx.fillText(String(p.l), x + (p.l === 2 ? -1.5 : p.l === 0 ? 1.5 : 0), Y(P(p.nu)) - 6);
    }

    // nu_max, and Delta nu between two radial peaks just above it.
    const xm = X(st.numax);
    ctx.save();
    ctx.setLineDash([2, 3]);
    ctx.strokeStyle = C.muted;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(xm, base);
    ctx.lineTo(xm, top - 16);
    ctx.stroke();
    ctx.restore();
    ctx.fillStyle = C.ink2;
    symbol(ctx, "ν", "max", xm - 4, top - 16, "right");
    const r0 = st.peaks.find((p) => p.l === 0 && X(p.nu) > xm + 8 && p.nu + st.dnu < hi);
    if (r0) {
      const a = X(r0.nu), b = X(r0.nu + st.dnu), yb = top - 15;
      ctx.strokeStyle = C.ink2;
      ctx.beginPath();
      ctx.moveTo(a, yb + 4);
      ctx.lineTo(a, yb);
      ctx.lineTo(b, yb);
      ctx.lineTo(b, yb + 4);
      ctx.stroke();
      ctx.save();
      ctx.setLineDash([1, 3]);
      ctx.strokeStyle = C.muted;
      ctx.beginPath();
      ctx.moveTo(a, yb + 6);
      ctx.lineTo(a, Y(P(r0.nu)) - 16);
      ctx.moveTo(b, yb + 6);
      ctx.lineTo(b, Y(P(r0.nu + st.dnu)) - 16);
      ctx.stroke();
      ctx.restore();
      symbol(ctx, "Δν", "", (a + b) / 2, yb - 3, "center");
    }

    // Frequency axis, with the title at the right and ticks that do not collide with it.
    ctx.strokeStyle = C.line;
    ctx.beginPath();
    ctx.moveTo(x0, base + 0.5);
    ctx.lineTo(x1, base + 0.5);
    ctx.stroke();
    ctx.font = C.font(10);
    ctx.fillStyle = C.muted;
    ctx.textBaseline = "top";
    const title = "Frequency (µHz)", tw = ctx.measureText(title).width, step = niceStep((hi - lo) / 5);
    ctx.textAlign = "right";
    ctx.fillText(title, x1, base + 6);
    ctx.textAlign = "center";
    for (let v = Math.ceil(lo / step) * step; v <= hi; v += step) {
      const x = X(v), s = fmt(v, step < 1 ? 1 : 0), sw = ctx.measureText(s).width;
      ctx.beginPath();
      ctx.moveTo(x, base);
      ctx.lineTo(x, base + 3);
      ctx.stroke();
      if (x + sw / 2 < x1 - tw - 8 && x - sw / 2 > 0) ctx.fillText(s, x, base + 6);
    }
    ctx.save();
    ctx.translate(7, (top + base) / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("Power", 0, 0);
    ctx.restore();
  }

  // ---------------------------------------------------------------- interface
  const NAMES = ["Radial", "Dipole", "Quadrupole", "Octupole"], WORDS = ["no", "one", "two", "three"];
  const signed = (m) => (m > 0 ? `+${m}` : m < 0 ? `−${-m}` : "0");
  const periodOf = (nu, long) => {
    const s = 1e6 / nu;
    return s < 5400 ? `${fmt(s / 60, 1)} ${long ? "minutes" : "min"}` : `${fmt(s / 3600, 1)} ${long ? "hours" : "h"}`;
  };
  const clock = (nu) => `One cycle takes ${fmt(1 / fShow(nu, S.star.numax), 1)} s here and ${periodOf(nu, true)} in the star.`;
  function describe() {
    const v = voice;
    if (v.kind === "mix") return `${v.comps.length} modes near ν<sub>max</sub> at once, each excited and damped by convection, so the pattern never repeats. ${clock(S.star.numax)}`;
    let s = `${NAMES[v.l]} mode (<i>l</i> = ${v.l}, <i>m</i> = ${signed(v.m)}): `;
    if (v.l === 0) s += "the whole star swells and shrinks, with no nodal lines.";
    else {
      s += `${WORDS[v.l]} nodal line${v.l > 1 ? "s" : ""}, ${v.m ? WORDS[Math.abs(v.m)] : "none"} through the poles; `;
      s += v.m ? `the pattern travels ${v.m > 0 ? "with" : "against"} the rotation.` : "red and blue swap in place.";
    }
    return `${s} ${clock(v.peak.nu)}`;
  }

  const massIn = $("[data-mass]"), radIn = $("[data-radius]"), mSeg = $("[data-m]"), LN12 = Math.log(12);
  function syncUI() {
    root.querySelectorAll("[data-l] button").forEach((b) => b.setAttribute("aria-pressed", String(!S.mix && +b.dataset.v === S.l)));
    if (mSeg.dataset.l !== String(S.l)) {
      mSeg.dataset.l = String(S.l);
      let html = "";
      for (let m = -S.l; m <= S.l; m += 1) html += `<button type="button" data-v="${m}" aria-pressed="false">${signed(m)}</button>`;
      mSeg.innerHTML = html;
    }
    mSeg.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", String(!S.mix && +b.dataset.v === S.m)));
    $(".sd-mix").setAttribute("aria-pressed", String(S.mix));
    $(".sd-play").textContent = S.playing ? "Pause" : "Play";
    $(".sd-desc").innerHTML = describe();
  }
  function readouts() {
    const st = S.star, M = fmt(S.M, 2), R = fmt(S.R, S.R < 9.995 ? 2 : 1);
    $("[data-numax]").textContent = `${fmt(st.numax, st.numax >= 100 ? 0 : st.numax >= 10 ? 1 : 2)} µHz`;
    $("[data-dnu]").textContent = `${fmt(st.dnu, st.dnu >= 10 ? 1 : 2)} µHz`;
    $("[data-period]").textContent = `every ${periodOf(st.top.nu)}`;
    $("[data-mass-out]").innerHTML = `${M} M<sub>☉</sub>`;
    $("[data-radius-out]").innerHTML = `${R} R<sub>☉</sub>`;
    massIn.setAttribute("aria-valuetext", `${M} solar masses`);
    radIn.setAttribute("aria-valuetext", `${R} solar radii`);
  }

  // What the star plays: the peak under the pointer, else the mixture, else the chosen peak.
  // Keeping the same (l, m) keeps the phase, so dragging a slider does not jolt the star.
  function retune() {
    const peak = S.hover || S.sel;
    let next;
    if (S.mix && !S.hover) next = mixVoice || (mixVoice = several(null));
    else {
      const m = clamp(S.m, -peak.l, peak.l);
      if (voice && voice.kind === "one" && voice.l === peak.l && voice.m === m) {
        voice.peak = peak;
        voice.f = fShow(peak.nu, S.star.numax);
        next = voice;
      } else next = one(peak, m);
    }
    if (next !== voice) {
      prev = voice && S.playing ? voice : null;
      fade0 = S.t;
      voice = next;
    }
    syncUI();
    drawSpec();
    if (!running()) drawStar();
  }
  const tallestOf = (l) => S.star.peaks.filter((p) => p.l === l).reduce((a, b) => (b.h > a.h ? b : a));
  function setStar(M, R) {
    Object.assign(S, { M, R, star: model(M, R), hover: null });
    S.sel = tallestOf(S.l);
    if (mixVoice) mixVoice = several(mixVoice);
    if (voice && voice.kind === "mix") voice = mixVoice;
    if (prev && prev.kind === "mix") prev = null;
    readouts();
    retune();
  }
  function choose(p) {
    Object.assign(S, { sel: p, l: p.l, m: clamp(S.m, -p.l, p.l), mix: false, hover: null });
    retune();
  }
  const pressed = (sel, fn) => $(sel).addEventListener("click", (ev) => {
    const b = ev.target.closest("button");
    if (b) fn(+b.dataset.v);
  });
  pressed("[data-l]", (l) => {
    Object.assign(S, { l, m: clamp(S.m, -l, l), mix: false });
    S.sel = tallestOf(l);
    retune();
  });
  pressed("[data-m]", (m) => {
    Object.assign(S, { m, mix: false });
    retune();
  });
  $(".sd-mix").addEventListener("click", () => {
    S.mix = !S.mix;
    retune();
  });
  $(".sd-play").addEventListener("click", () => {
    S.playing = !S.playing;
    syncUI();
    kick();
  });
  massIn.addEventListener("input", () => setStar(+massIn.value, S.R));
  // The radius slider is logarithmic; R is rounded to the shown digits so the readouts agree.
  radIn.addEventListener("input", () => {
    const R = Math.exp((LN12 * radIn.value) / 1000), d = R < 9.995 ? 100 : 10;
    setStar(S.M, Math.round(R * d) / d);
  });
  root.querySelectorAll("[data-preset]").forEach((b) =>
    b.addEventListener("click", () => {
      const [M, R] = b.dataset.preset.split(",").map(Number);
      massIn.value = String(M);
      radIn.value = String(Math.round((1000 * Math.log(R)) / LN12));
      setStar(M, R);
    }),
  );

  // A peak under the mouse previews its mode; a click or tap chooses it; with the spectrum
  // focused, the arrow keys step through the peaks.
  function hitAt(ev) {
    const r = spec.cv.getBoundingClientRect(), x = ev.clientX - r.left, y = ev.clientY - r.top;
    if (y < spec.top - 24 || y > spec.base + 6) return null;
    let best = null, bd = 9;
    for (const hh of spec.hits) {
      const d = Math.abs(hh.x - x);
      if (d < bd) [bd, best] = [d, hh.p];
    }
    return best;
  }
  spec.cv.addEventListener("pointermove", (ev) => {
    const p = hitAt(ev);
    spec.cv.style.cursor = p ? "pointer" : "";
    if (ev.pointerType === "mouse" && p !== S.hover) {
      S.hover = p;
      retune();
    }
  });
  spec.cv.addEventListener("pointerleave", () => {
    if (!S.hover) return;
    S.hover = null;
    retune();
  });
  spec.cv.addEventListener("click", (ev) => {
    const p = hitAt(ev);
    if (p) choose(p);
  });
  spec.cv.addEventListener("keydown", (ev) => {
    if (ev.key !== "ArrowLeft" && ev.key !== "ArrowRight") return;
    ev.preventDefault();
    const list = spec.hits.map((hh) => hh.p);
    let i = list.indexOf(S.sel);
    if (i < 0) i = list.indexOf(S.star.top);
    const p = list[clamp(i + (ev.key === "ArrowRight" ? 1 : -1), 0, list.length - 1)];
    if (p) choose(p);
  });

  // -------------------------------------------------------------------- loop
  // The star moves only while it is on screen and playing; with reduced motion it starts still.
  let raf = 0, last = 0, onScreen = false;
  const running = () => S.playing && onScreen;
  function kick() {
    if (!running() || raf) return;
    last = performance.now();
    raf = requestAnimationFrame(tick);
  }
  function tick(now) {
    raf = 0;
    const dt = Math.min((now - last) / 1000, 0.05);
    last = now;
    S.t += dt;
    S.spin += SPIN * dt;
    advance(voice, dt);
    advance(prev, dt);
    drawStar();
    kick();
  }
  function fit(o, square) {
    const r = o.cv.getBoundingClientRect(), dpr = Math.min(window.devicePixelRatio || 1, 2);
    o.w = Math.round(r.width);
    o.h = Math.round(square ? r.width : r.height);
    o.cv.width = Math.round(o.w * dpr);
    o.cv.height = Math.round(o.h * dpr);
    o.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  function redraw() {
    fit(star, true);
    fit(spec, false);
    drawStar();
    drawSpec();
  }

  palette();
  setStar(1, 1);
  redraw();
  const ro = new ResizeObserver(redraw);
  ro.observe(star.cv);
  ro.observe(spec.cv);
  if ("IntersectionObserver" in window) {
    new IntersectionObserver((es) => {
      onScreen = es[es.length - 1].isIntersecting;
      kick();
    }, { rootMargin: "60px" }).observe(root);
  } else {
    onScreen = true;
    kick();
  }
  T.onThemeChange(() => {
    palette();
    drawStar();
    drawSpec();
  });
  reduced.addEventListener("change", () => {
    if (!reduced.matches || !S.playing) return;
    S.playing = false;
    syncUI();
  });
  if (document.fonts) document.fonts.ready.then(redraw);
})();
