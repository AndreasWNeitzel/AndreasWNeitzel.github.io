// Orbits playground: controls, the integration loop and the canvas drawing for two problems
// that share the integrators in orbits-physics.js, satellites around a point-mass Earth and
// stars in the MWPotential2014 model of the Milky Way. Every number comes from orbits.json.
// Canvas colours come from the site tokens (window.siteTokens) and are read again whenever
// the theme changes. Nothing moves until the visitor presses Run.
import {
  galaxySystem, pointMassSystem, leapfrogStep, eulerStep, rk4Adaptive, stateFromElements, osculating, elevationDeg,
} from "./orbits-physics.js";

const MINUS = "−";
const RK4_TOL = 1e-10;
const MAX_FRAME_S = 0.1; // real seconds integrated per frame at most
const REDUCED_FRAME_MS = 250;
const HISTORY_CAP = 3000;
const motion = matchMedia("(prefers-reduced-motion: reduce)");

const root = document.getElementById("orbits-playground");
if (root) {
  const start = () => boot(root).catch((err) => {
    console.error(err);
    const state = root.querySelector(".pg-state");
    state.classList.add("is-alert");
    state.textContent = "The orbit data could not be loaded, so the playground cannot run here.";
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
const grouped = (v) => (v < 0 ? MINUS : "") + Math.round(Math.abs(v)).toLocaleString("en-GB");
const fixed = (v, d) => (v < 0 ? MINUS : "") + Math.abs(v).toFixed(d);
const axisNumber = (v) => (v < 0 ? MINUS : "") + String(Number(Math.abs(v).toPrecision(3)));
const sup = (n) => String(n).replace("-", MINUS).replace(/[0-9]/g, (c) => "⁰¹²³⁴⁵⁶⁷⁸⁹"[Number(c)]);
function sci(v) {
  if (!(v > 0)) return "0";
  const e = Math.floor(Math.log10(v));
  const m = v / 10 ** e;
  return `${m.toFixed(1)} × 10${sup(e)}`;
}
const pm = (v, err, d) => `${fixed(v, d)} ± ${Math.abs(err).toFixed(d)}`;
const degrees = (v) => `${fixed(v, 2)}°`;

function hms(seconds) {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${d} d ${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}
const myr = (t) => (t >= 1000 ? `${(t / 1000).toFixed(2)} Gyr` : `${Math.round(t)} Myr`);

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

const niceMax = (v) => {
  if (v <= 0) return 1;
  const e = 10 ** Math.floor(Math.log10(v));
  for (const m of [1, 2, 2.5, 5, 10]) if (m * e >= v) return m * e;
  return 10 * e;
};
// Round a span of seconds up to whole hours or days that divide into four ticks.
const HOUR_SPANS = [3600, 7200, 14400, 21600, 43200, 86400, 172800, 345600, 691200, 1382400];
const niceSeconds = (v) => HOUR_SPANS.find((h) => h >= v) ?? niceMax(v / 86400) * 86400;

// Labels stacked apart when their anchors are close, so names stay legible at the start,
// when every star sits at the Sun.
function spreadLabels(items, gap) {
  const sorted = [...items].sort((a, b) => a.y - b.y);
  const groups = [];
  for (const it of sorted) {
    const g = groups.find((grp) => grp.some((o) => Math.abs(o.x - it.x) < 70 && Math.abs(o.y - it.y) < gap * 1.2));
    if (g) g.push(it);
    else groups.push([it]);
  }
  for (const g of groups) {
    if (g.length < 2) continue;
    g.sort((a, b) => a.y - b.y);
    const mid = g.reduce((s, o) => s + o.y, 0) / g.length;
    g.forEach((o, i) => { o.ly = mid + (i - (g.length - 1) / 2) * gap; });
  }
  for (const it of items) if (it.ly === undefined) it.ly = it.y;
}

// ---------------------------------------------------------------- the playground
async function boot(root) {
  const $ = (sel) => root.querySelector(sel);
  const T = siteTokens();
  const params = new URLSearchParams(location.search);

  const ui = {
    modeButtons: [...root.querySelectorAll(".ob-mode button")],
    run: $(".ob-run-btn"), step: $(".ob-step"), reset: $(".ob-reset"), launch: $(".ob-launch"),
    live: $(".pg-live"), state: $(".pg-state"), form: $(".ob-settings"),
    time: $(".ob-time"), alt: $(".ob-alt"), speed: $(".ob-speed"), ecc: $(".ob-ecc"), eccRef: $(".ob-ecc-ref"),
    zmax: $(".ob-zmax"), zmaxRef: $(".ob-zmax-ref"), lz: $(".ob-lz"), lzRef: $(".ob-lz-ref"),
    E: $(".ob-energy-value"), ERef: $(".ob-e-ref"), err: $(".ob-err"), stepNow: $(".ob-stepnow"),
    mainTitle: $(".ob-main-title"), mainKey: $(".ob-main-key"), mainCap: $(".ob-main-cap"),
    sideTitle: $(".ob-side-title"), sideKey: $(".ob-side-key"),
    mainCanvas: $(".ob-main canvas"), sideCanvas: $(".ob-side canvas"), energyTip: $(".ob-energy .pg-tip"),
    tables: { sats: $(".ob-table-sats"), stations: $(".ob-table-stations"), stars: $(".ob-table-stars"), potential: $(".ob-table-potential") },
  };
  const cv = { main: surface(ui.mainCanvas), side: surface(ui.sideCanvas), energy: surface($(".ob-energy canvas")) };
  const f = ui.form.elements;

  const res = await fetch(root.dataset.src);
  if (!res.ok) throw new Error(`orbits.json: ${res.status}`);
  const D = await res.json();

  // ------------------------------------------------------------ colours and fonts
  let C = null;
  let F = null;
  function readTheme() {
    const c = (name) => T.colour(name);
    C = {
      surface: c("--surface"), surface2: c("--surface-2"), line: c("--line"), lineStrong: c("--line-strong"),
      ink: c("--ink"), ink2: c("--ink-2"), muted: c("--muted"), accent: c("--accent"), accent2: c("--accent-2"),
      cat: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((i) => c(`--cat-${i}`)),
    };
    const cs = getComputedStyle(document.documentElement);
    F = { mono: cs.getPropertyValue("--mono").trim() || "monospace", sans: cs.getPropertyValue("--sans").trim() || "sans-serif" };
  }
  readTheme();
  const bodyColour = (b) => (b.test ? C.ink2 : C.cat[b.cat]);

  // ------------------------------------------------------------ the two problems
  const earthGM = D.earth.gm_km3_s2;
  const earthSys = pointMassSystem(earthGM);
  const galaxySys = galaxySystem(D.potential);
  const omega = D.earth.rotation_rate_rad_s;
  const RE = D.earth.radius_km;
  const tpNames = { x: "x", y: "y", z: "z" };

  const MODES = {
    earth: {
      sys: earthSys,
      steps: [1, 5, 10, 30, 60, 120, 300], step: 10, stepLabel: (h) => `${h} s`,
      speeds: [[600, "10 min per s"], [1800, "30 min per s"], [3600, "1 h per s"], [10800, "3 h per s"]], speed: 3600,
      trailEvery: 120, sampleEvery: 60, historyEvery: 60,
      title: "Around the Earth", sideTitle: "Visible from the ground",
      cap: "Drag to turn the view. A line from a station to a satellite means the satellite is above that station's horizon.",
      mainAria: "Three Molniya satellites and a geostationary satellite around the rotating Earth, drawn to scale",
      sideAria: "Timeline of when each satellite is above the horizon of Porto, Moscow and the third station",
      bodies() {
        const M = D.molniya;
        const c = M.constellation;
        const raan0 = c.apogee_longitude_deg - 90;
        const out = [];
        for (let k = 0; k < c.count; k++) {
          const raan = raan0 + k * c.raan_spacing_deg;
          const m0 = (((180 + k * c.mean_anomaly_spacing_deg) % 360) + 360) % 360;
          out.push({
            name: `Molniya ${k + 1}`, short: `M${k + 1}`, cat: [0, 1, 4][k],
            s0: stateFromElements(earthGM, M.semi_major_axis_km, M.eccentricity, M.inclination_deg, raan, M.argument_of_perigee_deg, m0),
            period: M.period_s, elements: { a: M.semi_major_axis_km, e: M.eccentricity, i: M.inclination_deg, raan, argp: M.argument_of_perigee_deg, m0 },
          });
        }
        out.push({
          name: "Geostationary", short: "GEO", cat: 2,
          s0: stateFromElements(earthGM, D.geo.radius_km, 0, 0, 0, 0, D.geo.longitude_deg),
          period: D.geo.period_s, elements: { a: D.geo.radius_km, e: 0, i: 0, raan: 0, argp: 0, m0: D.geo.longitude_deg },
        });
        return out;
      },
    },
    galaxy: {
      sys: galaxySys,
      steps: [0.1, 0.25, 0.5, 1, 2, 5, 10], step: 0.5, stepLabel: (h) => `${h} Myr`,
      speeds: [[10, "10 Myr per s"], [25, "25 Myr per s"], [50, "50 Myr per s"], [100, "100 Myr per s"], [200, "200 Myr per s"]], speed: 50,
      trailEvery: 1, sampleEvery: 1, historyEvery: 2,
      title: "Face-on, from the north Galactic pole", sideTitle: "Distance from the axis against height",
      cap: "The disc turns clockwise. The dashed ring is the Sun's circle at R = 8 kpc; the rings are 5 kpc apart.",
      mainAria: "Orbits of six stars in the plane of the Milky Way, seen from the north Galactic pole",
      sideAria: "Orbits of six stars as distance from the Galactic axis against height above the plane",
      bodies() {
        const shorts = { "61 Virginis": "61 Vir", "Proxima Centauri": "Proxima", "Barnard's star": "Barnard", "Lalande 21185": "Lalande", "Kapteyn's star": "Kapteyn", "HD 140283": "HD 140283" };
        return D.stars.map((st, i) => ({
          name: st.name, short: shorts[st.name] || st.name, cat: [0, 1, 2, 4, 6, 9][i], star: st,
          s0: Float64Array.from([...st.galactocentric.xyz_kpc, ...st.galactocentric.vxyz_km_s]),
        }));
      },
    },
  };

  // ------------------------------------------------------------ state
  let mode = null;
  let M = null;
  let bodies = [];
  let running = false;
  let t = 0;
  let acc = 0;
  let integrator = "leapfrog";
  let h = 10;
  let speed = 3600;
  let follow = 0;
  let view = { az: -35, el: 24 };
  let stations = [];
  let visibility = null; // Uint8Array(stations x bodies x VIS_N)
  let visHead = 0;
  let visCount = 0;
  const VIS_N = 1440; // samples of 60 s in the 24 h window
  let nextTrail = 0;
  let nextSample = 0;
  let nextHistory = 0;
  let extent = { R: 12, z: 1.5 };
  let lastFrame = 0;
  let raf = 0;
  let resumeOnShow = false;
  let hoverHistory = -1;
  let testParticle = null;
  const dirty = { main: true, side: true, energy: true };

  function setStations() {
    stations = D.stations.map((st) => ({ ...st, lat: st.lat_deg, lon: st.lon_deg, short: st.short_name || st.name }));
    stations[2].lat = Number(f.lat.value);
  }

  function makeBody(spec) {
    const b = { ...spec, s: Float64Array.from(spec.s0), a: new Float64Array(3), h: 0, E0: 0, Lz0: 0,
      trail: new Float32Array(3 * (mode === "earth" ? Math.ceil(spec.period / M.trailEvery) + 2 : 12000)), trailHead: 0, trailCount: 0,
      hist: new Float32Array(2 * HISTORY_CAP), histCount: 0, histEvery: M.historyEvery,
      Rmin: Infinity, Rmax: 0, zmax: 0, errMax: 0 };
    M.sys.accel(b.s[0], b.s[1], b.s[2], b.a);
    b.E0 = M.sys.energy(...b.s);
    b.Lz0 = Lz(b.s);
    pushTrail(b);
    track(b);
    return b;
  }

  // L_z with galpy's sign, positive for rotation with the disc, in the astropy frame of the data.
  const Lz = (s) => -(s[0] * s[4] - s[1] * s[3]);

  function pushTrail(b) {
    const n = b.trail.length / 3;
    const i = b.trailHead;
    b.trail[3 * i] = b.s[0];
    b.trail[3 * i + 1] = b.s[1];
    b.trail[3 * i + 2] = b.s[2];
    b.trailHead = (i + 1) % n;
    b.trailCount = Math.min(n, b.trailCount + 1);
  }

  // Extremes so far: the spherical radius for the eccentricity, as galpy defines it, and |z|.
  function track(b) {
    if (mode !== "galaxy") return;
    const R = Math.hypot(b.s[0], b.s[1]);
    const r = Math.hypot(R, b.s[2]);
    b.Rmin = Math.min(b.Rmin, r);
    b.Rmax = Math.max(b.Rmax, r);
    b.zmax = Math.max(b.zmax, Math.abs(b.s[2]));
    if (R * 1.12 > extent.R) extent.R = Math.ceil((R * 1.12) / 5) * 5;
    if (Math.abs(b.s[2]) * 1.15 > extent.z) extent.z = Math.ceil(Math.abs(b.s[2]) * 1.15 * 2) / 2;
  }

  function pushHistory(b) {
    const E = M.sys.energy(...b.s);
    const err = Math.abs((E - b.E0) / b.E0);
    b.errMax = Math.max(b.errMax, err);
    if (b.histCount === HISTORY_CAP) {
      // thin the record: keep every second point and sample half as often from now on
      for (let i = 0; i < HISTORY_CAP / 2; i++) {
        b.hist[2 * i] = b.hist[4 * i];
        b.hist[2 * i + 1] = b.hist[4 * i + 1];
      }
      b.histCount = HISTORY_CAP / 2;
      b.histEvery *= 2;
    }
    b.hist[2 * b.histCount] = t;
    b.hist[2 * b.histCount + 1] = err;
    b.histCount++;
  }

  function rebuild() {
    M = MODES[mode];
    bodies = M.bodies().map(makeBody);
    if (mode === "galaxy" && testParticle) bodies.push(makeBody(testParticle));
    t = 0;
    acc = 0;
    nextTrail = M.trailEvery;
    nextSample = 0;
    nextHistory = 0;
    extent = { R: 12, z: 1.5 };
    for (const b of bodies) track(b);
    if (mode === "earth") {
      setStations();
      visibility = new Uint8Array(stations.length * bodies.length * VIS_N);
      visHead = 0;
      visCount = 0;
      sampleVisibility();
    }
    for (const b of bodies) pushHistory(b);
    nextHistory = M.historyEvery;
    hoverHistory = -1;
    ui.energyTip.hidden = true;
    follow = Math.min(follow, bodies.length - 1);
    markAll();
    updateReadout();
  }

  // ------------------------------------------------------------ stations and visibility
  function stationVector(st, time, out) {
    const lat = (st.lat * Math.PI) / 180;
    const lon = (st.lon * Math.PI) / 180 + omega * time;
    out[0] = Math.cos(lat) * Math.cos(lon);
    out[1] = Math.cos(lat) * Math.sin(lon);
    out[2] = Math.sin(lat);
    return out;
  }

  const U = [0, 0, 0];
  function visible(st, b, time) {
    return elevationDeg(b.s, stationVector(st, time, U), RE) > 0;
  }

  function sampleVisibility() {
    const nb = bodies.length;
    for (let i = 0; i < stations.length; i++) {
      for (let j = 0; j < nb; j++) visibility[(i * nb + j) * VIS_N + visHead] = visible(stations[i], bodies[j], t) ? 1 : 0;
    }
    visHead = (visHead + 1) % VIS_N;
    visCount = Math.min(VIS_N, visCount + 1);
  }

  function clearStationVisibility(i) {
    const nb = bodies.length;
    for (let j = 0; j < nb; j++) visibility.fill(0, (i * nb + j) * VIS_N, (i * nb + j + 1) * VIS_N);
    // re-sample the present so the row is not empty
    for (let j = 0; j < nb; j++) {
      const k = (visHead - 1 + VIS_N) % VIS_N;
      visibility[(i * nb + j) * VIS_N + k] = visible(stations[i], bodies[j], t) ? 1 : 0;
    }
  }

  // ------------------------------------------------------------ integration
  function afterStep() {
    if (t >= nextTrail) {
      for (const b of bodies) pushTrail(b);
      nextTrail += M.trailEvery;
    }
    for (const b of bodies) track(b);
    if (mode === "earth" && t >= nextSample + M.sampleEvery - 1e-9) {
      sampleVisibility();
      nextSample += M.sampleEvery;
    }
    if (t >= nextHistory - 1e-9) {
      for (const b of bodies) pushHistory(b);
      nextHistory += M.historyEvery;
    }
  }

  function advance(span) {
    if (integrator === "rk4") {
      const chunk = Math.max(M.sampleEvery, h);
      let left = span;
      while (left > 0) {
        const d = Math.min(left, chunk);
        for (const b of bodies) rk4Adaptive(M.sys, b, d, h, RK4_TOL);
        t += d;
        left -= d;
        afterStep();
      }
      return;
    }
    const step = integrator === "leapfrog" ? leapfrogStep : eulerStep;
    acc += span;
    while (acc >= h - 1e-12) {
      for (const b of bodies) step(M.sys, b, h);
      t += h;
      acc -= h;
      afterStep();
    }
  }

  // ------------------------------------------------------------ controls
  function fillSelect(select, options, value) {
    select.replaceChildren(...options.map(([v, label]) => {
      const o = document.createElement("option");
      o.value = String(v);
      o.textContent = label;
      return o;
    }));
    select.value = String(value);
  }

  function fillFollow() {
    fillSelect(f.follow, bodies.map((b, i) => [i, b.name]), follow);
  }

  function setMode(next, keepRun = false) {
    if (mode === next) return;
    const was = running;
    pause();
    note = "";
    mode = next;
    root.dataset.mode = mode;
    for (const btn of ui.modeButtons) btn.setAttribute("aria-pressed", btn.dataset.mode === mode ? "true" : "false");
    M = MODES[mode];
    h = M.step;
    speed = M.speed;
    fillSelect(f.step, M.steps.map((v) => [v, M.stepLabel(v)]), h);
    fillSelect(f.speed, M.speeds, speed);
    follow = 0;
    ui.mainTitle.textContent = M.title;
    ui.sideTitle.textContent = M.sideTitle;
    ui.mainCap.textContent = M.cap;
    ui.mainCanvas.setAttribute("aria-label", M.mainAria);
    ui.sideCanvas.setAttribute("aria-label", M.sideAria);
    rebuild();
    fillFollow();
    buildKeys();
    if (keepRun && was) run();
  }

  function buildKeys() {
    const key = (b) => {
      const span = document.createElement("span");
      const i = document.createElement("i");
      i.className = "ob-k";
      i.style.background = bodyColour(b);
      span.append(i, document.createTextNode(b.short));
      return span;
    };
    ui.mainKey.replaceChildren(...bodies.map(key));
    if (mode === "earth") ui.sideKey.textContent = "last 24 h";
    else ui.sideKey.textContent = "R and z in kpc";
  }

  function run() {
    if (running) return;
    running = true;
    lastFrame = 0;
    ui.run.textContent = "Pause";
    ui.live.setAttribute("aria-busy", "true");
    schedule();
    updateReadout();
  }

  function pause() {
    if (!running) return;
    running = false;
    ui.run.textContent = "Run";
    ui.live.setAttribute("aria-busy", "false");
    updateReadout();
  }

  ui.run.addEventListener("click", () => (running ? pause() : run()));
  ui.step.addEventListener("click", () => {
    pause();
    if (integrator === "rk4") {
      for (const b of bodies) rk4Adaptive(M.sys, b, h, h, RK4_TOL);
      t += h;
      afterStep();
    } else {
      const step = integrator === "leapfrog" ? leapfrogStep : eulerStep;
      for (const b of bodies) step(M.sys, b, h);
      t += h;
      afterStep();
    }
    markAll();
    updateReadout();
  });
  ui.reset.addEventListener("click", () => {
    pause();
    note = "";
    rebuild();
  });
  for (const btn of ui.modeButtons) btn.addEventListener("click", () => setMode(btn.dataset.mode));

  ui.form.addEventListener("submit", (e) => e.preventDefault());
  ui.form.addEventListener("change", (e) => {
    const name = e.target.name;
    if (name === "integrator" || name === "step") {
      integrator = f.integrator.value;
      h = Number(f.step.value);
      note = name === "integrator" ? "Started again with the new integrator." : "Started again with the new step.";
      const was = running;
      pause();
      rebuild();
      if (was) run();
    } else if (name === "speed") {
      speed = Number(f.speed.value);
      note = "";
      updateReadout();
    } else if (name === "follow") {
      follow = Number(f.follow.value);
      markAll();
      updateReadout();
    }
  });
  ui.form.addEventListener("input", (e) => {
    const name = e.target.name;
    if (name === "lat") {
      f.latout.value = `${Number(f.lat.value).toFixed(1)}°`;
      if (mode === "earth") {
        stations[2].lat = Number(f.lat.value);
        clearStationVisibility(2);
        buildStationsTable();
        markAll();
      }
    } else if (name.startsWith("tp")) {
      f.tpRout.value = `${Number(f.tpR.value).toFixed(1)} kpc`;
      f.tpZout.value = `${fixed(Number(f.tpZ.value), 1)} kpc`;
      f.tpVRout.value = `${fixed(Number(f.tpVR.value), 0)} km/s`;
      f.tpVPout.value = `${fixed(Number(f.tpVP.value), 0)} km/s`;
      f.tpVZout.value = `${fixed(Number(f.tpVZ.value), 0)} km/s`;
    }
  });

  // The test particle starts at the Sun's azimuth: x = -R, y = 0. There the outward radial
  // direction is -x and rotation with the disc is +y.
  ui.launch.addEventListener("click", () => {
    const R = Number(f.tpR.value);
    const z = Number(f.tpZ.value);
    const vR = Number(f.tpVR.value);
    const vP = Number(f.tpVP.value);
    const vZ = Number(f.tpVZ.value);
    testParticle = { name: "Test particle", short: "test", test: true, cat: 8, s0: Float64Array.from([-R, 0, z, -vR, vP, vZ]) };
    const idx = bodies.findIndex((b) => b.test);
    const nb = makeBody(testParticle);
    nb.E0 = M.sys.energy(...nb.s);
    pushHistory(nb);
    if (idx >= 0) bodies[idx] = nb;
    else bodies.push(nb);
    follow = bodies.findIndex((b) => b.test);
    fillFollow();
    buildKeys();
    markAll();
    updateReadout();
  });

  document.addEventListener("visibilitychange", () => {
    if (document.hidden && running) {
      resumeOnShow = true;
      pause();
    } else if (!document.hidden && resumeOnShow) {
      resumeOnShow = false;
      run();
    }
  });

  // ------------------------------------------------------------ readouts
  const STATES = { idle: "Paused. Press Run, or Step for one step.", running: "Running." };
  let note = "";

  function updateReadout() {
    const b = bodies[follow];
    if (!b) return;
    const E = M.sys.energy(...b.s);
    const err = Math.abs((E - b.E0) / b.E0);
    ui.err.textContent = sci(err);
    ui.stepNow.textContent = integrator === "rk4" && b.h ? `RK4 step ${mode === "earth" ? `${b.h.toFixed(1)} s` : `${b.h.toFixed(3)} Myr`}` : "";
    if (mode === "earth") {
      ui.time.textContent = hms(t);
      const o = osculating(earthGM, b.s);
      ui.alt.textContent = grouped(o.r - RE);
      ui.speed.textContent = o.v.toFixed(2);
    } else {
      ui.time.textContent = myr(t);
      const e = b.Rmax > 0 ? (b.Rmax - b.Rmin) / (b.Rmax + b.Rmin) : 0;
      ui.ecc.textContent = e.toFixed(3);
      ui.zmax.textContent = b.zmax.toFixed(2);
      ui.lz.textContent = grouped(Lz(b.s));
      ui.E.textContent = grouped(E);
      const r = b.star && b.star.reference;
      ui.eccRef.textContent = r ? `galpy ${r.eccentricity.toFixed(3)}` : "";
      ui.zmaxRef.textContent = r ? `kpc, galpy ${r.zmax_kpc.toFixed(2)}` : "kpc";
      ui.lzRef.textContent = r ? `kpc km/s, galpy ${grouped(r.Lz_kpc_km_s)}` : "kpc km/s";
      ui.ERef.textContent = r ? `km²/s², galpy ${grouped(r.energy_km2_s2)}` : "km²/s²";
    }
    ui.state.textContent = (running ? STATES.running : STATES.idle) + (note ? ` ${note}` : "");
  }

  // ------------------------------------------------------------ Earth view
  const rad = Math.PI / 180;
  function projector() {
    const s = cv.main;
    const az = view.az * rad;
    const el = view.el * rad;
    const [ca, sa, ce, se] = [Math.cos(az), Math.sin(az), Math.cos(el), Math.sin(el)];
    const span = (D.molniya.apogee_radius_km + 1000) * 2;
    const scale = Math.min(s.w, s.h - 24) / span;
    const cx = s.w / 2;
    const cy = s.h / 2;
    const out = { X: 0, Y: 0, Z: 0, sx: 0, sy: 0, hidden: false };
    return {
      scale, cx, cy,
      to(x, y, z) {
        const x1 = x * ca + y * sa;
        const y1 = -x * sa + y * ca;
        out.X = x1;
        out.Y = y1 * se + z * ce;
        out.Z = -y1 * ce + z * se;
        out.sx = cx + out.X * scale;
        out.sy = cy - out.Y * scale;
        out.hidden = out.Z < 0 && out.X * out.X + out.Y * out.Y < RE * RE;
        return out;
      },
    };
  }

  function drawEarth() {
    const s = cv.main;
    const ctx = s.begin();
    if (s.w < 40) return;
    const P = projector();
    const r = RE * P.scale;
    ctx.lineJoin = "round";
    ctx.lineCap = "round";
    // trails behind the Earth first, faint
    const drawTrail = (b, hiddenPass) => {
      const n = b.trail.length / 3;
      ctx.strokeStyle = bodyColour(b);
      ctx.lineWidth = b === bodies[follow] ? 1.6 : 1.1;
      ctx.globalAlpha = hiddenPass ? 0.16 : 0.7;
      ctx.beginPath();
      let pen = false;
      for (let k = 0; k < b.trailCount; k++) {
        const i = (b.trailHead - b.trailCount + k + n) % n;
        const p = P.to(b.trail[3 * i], b.trail[3 * i + 1], b.trail[3 * i + 2]);
        if (p.hidden !== hiddenPass) { pen = false; continue; }
        if (pen) ctx.lineTo(p.sx, p.sy);
        else ctx.moveTo(p.sx, p.sy);
        pen = true;
      }
      ctx.stroke();
    };
    for (const b of bodies) drawTrail(b, true);
    // the Earth
    ctx.globalAlpha = 1;
    ctx.fillStyle = C.surface2;
    dot(ctx, P.cx, P.cy, r);
    ctx.strokeStyle = C.lineStrong;
    ctx.lineWidth = 1;
    ring(ctx, P.cx, P.cy, r);
    // graticule, front side only: parallels and meridian planes turning with the Earth
    const theta = omega * t;
    const arc = (points) => {
      ctx.beginPath();
      let pen = false;
      for (const [x, y, z] of points) {
        const p = P.to(x, y, z);
        if (p.Z < 0) { pen = false; continue; }
        if (pen) ctx.lineTo(p.sx, p.sy);
        else ctx.moveTo(p.sx, p.sy);
        pen = true;
      }
      ctx.stroke();
    };
    ctx.strokeStyle = C.lineStrong;
    ctx.globalAlpha = 0.55;
    for (const lat of [-60, -30, 0, 30, 60]) {
      const cl = Math.cos(lat * rad);
      const sl = Math.sin(lat * rad);
      ctx.lineWidth = lat === 0 ? 1 : 0.6;
      arc(Array.from({ length: 73 }, (_, i) => { const a = (i / 72) * 2 * Math.PI; return [RE * cl * Math.cos(a), RE * cl * Math.sin(a), RE * sl]; }));
    }
    ctx.lineWidth = 0.6;
    for (let k = 0; k < 6; k++) {
      const lon = theta + k * 30 * rad;
      arc(Array.from({ length: 73 }, (_, i) => { const a = (i / 72) * 2 * Math.PI; return [RE * Math.cos(a) * Math.cos(lon), RE * Math.cos(a) * Math.sin(lon), RE * Math.sin(a)]; }));
    }
    // stations
    const stationPts = [];
    ctx.globalAlpha = 1;
    ctx.font = `500 10px ${F.mono}`;
    ctx.textBaseline = "middle";
    for (const st of stations) {
      const u = stationVector(st, t, [0, 0, 0]);
      const p = P.to(RE * u[0], RE * u[1], RE * u[2]);
      const front = p.Z >= 0;
      stationPts.push({ st, u, sx: p.sx, sy: p.sy, front });
      ctx.globalAlpha = front ? 1 : 0.25;
      ctx.fillStyle = C.ink;
      dot(ctx, p.sx, p.sy, 2.4);
    }
    // sight lines from front-side stations to the satellites above their horizon
    ctx.lineWidth = 1;
    for (const sp of stationPts) {
      if (!sp.front) continue;
      for (const b of bodies) {
        if (elevationDeg(b.s, sp.u, RE) <= 0) continue;
        const p = P.to(b.s[0], b.s[1], b.s[2]);
        ctx.globalAlpha = 0.35;
        ctx.strokeStyle = bodyColour(b);
        line(ctx, sp.sx, sp.sy, p.sx, p.sy);
      }
    }
    // station labels, placed just beyond the Earth's disc on the station's side
    const stLabels = [];
    for (const sp of stationPts) {
      if (!sp.front) continue;
      const dx = sp.sx - P.cx;
      const dy = sp.sy - P.cy;
      const d = Math.hypot(dx, dy) || 1;
      const push = r + 6;
      stLabels.push({ x: P.cx + (dx / d) * push, y: P.cy + (dy / d) * push, right: dx >= 0, text: sp.st.short, lx: sp.sx, ly0: sp.sy });
    }
    spreadLabels(stLabels, 11);
    ctx.globalAlpha = 1;
    ctx.font = `500 10px ${F.mono}`;
    for (const l of stLabels) {
      ctx.strokeStyle = C.line;
      ctx.lineWidth = 1;
      line(ctx, l.lx, l.ly0, l.x, l.ly);
      ctx.fillStyle = C.ink2;
      ctx.textAlign = l.right ? "left" : "right";
      ctx.fillText(l.text, l.x + (l.right ? 3 : -3), l.ly);
    }
    // trails in front, then the satellites
    for (const b of bodies) drawTrail(b, false);
    const labels = [];
    bodies.forEach((b, i) => {
      const p = P.to(b.s[0], b.s[1], b.s[2]);
      ctx.globalAlpha = p.hidden ? 0.3 : 1;
      ctx.fillStyle = C.surface;
      dot(ctx, p.sx, p.sy, 5);
      ctx.fillStyle = bodyColour(b);
      dot(ctx, p.sx, p.sy, 3.4);
      if (i === follow) {
        ctx.strokeStyle = C.ink;
        ctx.lineWidth = 1.5;
        ring(ctx, p.sx, p.sy, 7.5);
      }
      labels.push({ x: p.sx, y: p.sy, text: b.short, hidden: p.hidden });
    });
    spreadLabels(labels, 12);
    ctx.font = `500 11px ${F.mono}`;
    ctx.textAlign = "left";
    for (const l of labels) {
      ctx.globalAlpha = l.hidden ? 0.4 : 1;
      ctx.fillStyle = C.ink2;
      ctx.fillText(l.text, l.x + 9, l.ly);
    }
    // scale note
    ctx.globalAlpha = 1;
    ctx.fillStyle = C.muted;
    ctx.font = `500 10px ${F.mono}`;
    ctx.textAlign = "left";
    ctx.textBaseline = "alphabetic";
    const bar = 10000 * P.scale;
    ctx.strokeStyle = C.lineStrong;
    ctx.lineWidth = 1;
    line(ctx, 12, s.h - 12.5, 12 + bar, s.h - 12.5);
    ctx.fillText("10,000 km", 12 + bar + 6, s.h - 9);
    ctx.textAlign = "right";
    ctx.fillText(`view: azimuth ${Math.round(view.az)}°, elevation ${Math.round(view.el)}°`, s.w - 10, s.h - 9);
  }

  // dragging turns the view
  let drag = null;
  ui.mainCanvas.addEventListener("pointerdown", (e) => {
    if (mode !== "earth") return;
    drag = { x: e.clientX, y: e.clientY, az: view.az, el: view.el };
    ui.mainCanvas.setPointerCapture(e.pointerId);
    ui.mainCanvas.classList.add("is-dragging");
  });
  ui.mainCanvas.addEventListener("pointermove", (e) => {
    if (!drag) return;
    view.az = drag.az - (e.clientX - drag.x) * 0.4;
    view.el = Math.max(-85, Math.min(85, drag.el + (e.clientY - drag.y) * 0.4));
    dirty.main = true;
    schedule();
  });
  const endDrag = () => { drag = null; ui.mainCanvas.classList.remove("is-dragging"); };
  ui.mainCanvas.addEventListener("pointerup", endDrag);
  ui.mainCanvas.addEventListener("pointercancel", endDrag);

  // ------------------------------------------------------------ visibility timeline
  function drawVisibility() {
    const s = cv.side;
    const ctx = s.begin();
    if (s.w < 60 || !visibility) return;
    const nb = bodies.length;
    ctx.font = `500 10px ${F.mono}`;
    // The movable station is labelled by the latitude it is at, not by a fixed name.
    const label = (st) => (st.adjustable_latitude ? `${Math.round(st.lat)}\u00b0 N` : st.name);
    const left = 8 + Math.ceil(Math.max(...stations.map((st) => ctx.measureText(label(st)).width)));
    const right = 8 + Math.ceil(ctx.measureText("Molniya 100%").width);
    const W = s.w - left - right - 8;
    const top = 6;
    const bottom = s.h - 18;
    const groupH = (bottom - top) / stations.length;
    const rowGap = 2;
    const rowH = Math.max(3, (groupH - 8 - rowGap * (nb - 1)) / nb);
    const windowS = VIS_N * M.sampleEvery;
    const tEnd = Math.max(t, windowS);
    const tStart = tEnd - windowS;
    const X = (time) => left + ((time - tStart) / windowS) * W;
    // time axis, hours since the start
    ctx.strokeStyle = C.line;
    ctx.fillStyle = C.muted;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.lineWidth = 1;
    const first = Math.ceil(tStart / 21600) * 21600;
    for (let time = first; time <= tEnd + 1; time += 21600) {
      const x = Math.round(X(time)) + 0.5;
      line(ctx, x, top, x, bottom);
      ctx.fillText(`${Math.round(time / 3600)} h`, x, bottom + 5);
    }
    stations.forEach((st, i) => {
      const y0 = top + i * groupH + 4;
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";
      ctx.fillStyle = C.ink2;
      ctx.fillText(label(st), left - 8, y0 + (groupH - 8) / 2);
      let anyMolniya = 0;
      let geo = 0;
      const any = new Uint8Array(VIS_N);
      bodies.forEach((b, j) => {
        const base = (i * nb + j) * VIS_N;
        const y = y0 + j * (rowH + rowGap);
        ctx.fillStyle = bodyColour(b);
        ctx.globalAlpha = 0.9;
        let runStart = -1;
        let count = 0;
        for (let k = 0; k < visCount; k++) {
          const idx = (visHead - visCount + k + VIS_N) % VIS_N;
          const on = visibility[base + idx];
          const time = t - (visCount - 1 - k) * M.sampleEvery;
          if (on) {
            count++;
            if (j < nb - 1) any[k] = 1;
          }
          if (on && runStart < 0) runStart = time;
          if ((!on || k === visCount - 1) && runStart >= 0) {
            const end = on ? time + M.sampleEvery : time;
            ctx.fillRect(X(runStart), y, Math.max(1, X(end) - X(runStart)), rowH);
            runStart = -1;
          }
        }
        if (j === nb - 1) geo = count / Math.max(1, visCount);
      });
      for (let k = 0; k < visCount; k++) anyMolniya += any[k];
      anyMolniya /= Math.max(1, visCount);
      ctx.globalAlpha = 1;
      ctx.fillStyle = C.muted;
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      const yc = y0 + (groupH - 8) / 2;
      ctx.fillText(`Molniya ${Math.round(anyMolniya * 100)}%`, left + W + 8, yc - 6);
      ctx.fillText(`GEO ${Math.round(geo * 100)}%`, left + W + 8, yc + 6);
    });
  }

  // ------------------------------------------------------------ Galaxy views
  function drawFaceOn() {
    const s = cv.main;
    const ctx = s.begin();
    if (s.w < 40) return;
    const W = extent.R;
    const scale = (Math.min(s.w, s.h) / 2 - 16) / W;
    const cx = s.w / 2;
    const cy = s.h / 2;
    const X = (x) => cx + x * scale;
    const Y = (y) => cy - y * scale;
    ctx.lineWidth = 1;
    ctx.font = `500 10px ${F.mono}`;
    ctx.textBaseline = "bottom";
    ctx.textAlign = "left";
    for (let R = 5; R <= W; R += 5) {
      ctx.strokeStyle = C.line;
      ctx.setLineDash([]);
      ring(ctx, cx, cy, R * scale);
      ctx.fillStyle = C.muted;
      ctx.fillText(R === 5 ? "5 kpc" : String(R), X(R) + 3, cy - 3);
    }
    ctx.strokeStyle = C.lineStrong;
    ctx.setLineDash([4, 4]);
    ring(ctx, cx, cy, D.potential.R0_kpc * scale);
    ctx.setLineDash([]);
    // the centre and the Sun
    ctx.strokeStyle = C.ink2;
    line(ctx, cx - 5, cy, cx + 5, cy);
    line(ctx, cx, cy - 5, cx, cy + 5);
    const sx = X(-D.solar.galcen_distance_kpc);
    const sy = Y(0);
    ctx.fillStyle = C.ink2;
    dot(ctx, sx, sy, 1.5);
    ring(ctx, sx, sy, 4.5);
    ctx.textAlign = "right";
    ctx.textBaseline = "top";
    ctx.fillStyle = C.muted;
    ctx.fillText("Sun", sx - 7, sy + 2);
    ctx.textAlign = "left";
    ctx.fillText("centre", cx + 7, cy + 2);
    drawTrails2D(ctx, (x, y) => [X(x), Y(y)], true, 1, 1);
  }

  function drawMeridional() {
    const s = cv.side;
    const ctx = s.begin();
    if (s.w < 60) return;
    ctx.font = `10px ${F.mono}`;
    const m = { l: 34, r: 10, t: 8, b: 26 };
    const W = s.w - m.l - m.r;
    const H = s.h - m.t - m.b;
    const Rmax = extent.R;
    const zl = extent.z;
    const X = (R) => m.l + (R / Rmax) * W;
    const Y = (z) => m.t + H / 2 - (z / zl) * (H / 2);
    ctx.lineWidth = 1;
    ctx.fillStyle = C.muted;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    for (let R = 0; R <= Rmax; R += 5) {
      const x = Math.round(X(R)) + 0.5;
      ctx.strokeStyle = R === 0 ? C.lineStrong : C.line;
      line(ctx, x, m.t, x, m.t + H);
      ctx.fillText(String(R), x, m.t + H + 4);
    }
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    const zStep = zl >= 4 ? 2 : zl >= 2 ? 1 : 0.5;
    for (let z = -zl; z <= zl + 1e-9; z += zStep) {
      const y = Math.round(Y(z)) + 0.5;
      ctx.strokeStyle = Math.abs(z) < 1e-9 ? C.lineStrong : C.line;
      line(ctx, m.l, y, m.l + W, y);
      ctx.fillStyle = C.muted;
      ctx.fillText(axisNumber(z), m.l - 5, y);
    }
    ctx.textAlign = "left";
    ctx.textBaseline = "top";
    ctx.fillText("z (kpc)", m.l + 4, m.t + 1);
    ctx.textAlign = "center";
    ctx.fillText("R (kpc)", m.l + W / 2, m.t + H + 15);
    const sx = X(D.solar.galcen_distance_kpc);
    const sy = Y(D.solar.z_sun_pc / 1000);
    ctx.strokeStyle = C.ink2;
    ctx.fillStyle = C.ink2;
    dot(ctx, sx, sy, 1.5);
    ring(ctx, sx, sy, 4.5);
    drawTrails2D(ctx, (x, y, z) => [X(Math.hypot(x, y)), Y(z)], false, 1, 0.8);
  }

  function drawTrails2D(ctx, map, labelAll, alphaFollow, alphaOthers) {
    ctx.lineJoin = "round";
    ctx.lineCap = "round";
    const order = bodies.map((_, i) => i).sort((a, b) => (a === follow) - (b === follow));
    for (const i of order) {
      const b = bodies[i];
      const n = b.trail.length / 3;
      ctx.strokeStyle = bodyColour(b);
      ctx.lineWidth = i === follow ? 1.6 : 1;
      ctx.globalAlpha = i === follow ? alphaFollow : alphaOthers * 0.75;
      if (b.test) ctx.setLineDash([3, 3]);
      ctx.beginPath();
      for (let k = 0; k < b.trailCount; k++) {
        const j = (b.trailHead - b.trailCount + k + n) % n;
        const [x, y] = map(b.trail[3 * j], b.trail[3 * j + 1], b.trail[3 * j + 2]);
        if (k) ctx.lineTo(x, y);
        else ctx.moveTo(x, y);
      }
      ctx.stroke();
      ctx.setLineDash([]);
    }
    const labels = [];
    bodies.forEach((b, i) => {
      const [x, y] = map(b.s[0], b.s[1], b.s[2]);
      ctx.globalAlpha = 1;
      ctx.fillStyle = C.surface;
      dot(ctx, x, y, 4.6);
      ctx.fillStyle = bodyColour(b);
      dot(ctx, x, y, 3.2);
      if (i === follow) {
        ctx.strokeStyle = C.ink;
        ctx.lineWidth = 1.5;
        ring(ctx, x, y, 7);
      }
      if (labelAll || i === follow) labels.push({ x, y, text: b.short });
    });
    spreadLabels(labels, 12);
    ctx.font = `500 10px ${F.mono}`;
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    for (const l of labels) {
      ctx.fillStyle = C.ink2;
      ctx.fillText(l.text, l.x + 8, l.ly);
    }
  }

  // ------------------------------------------------------------ energy error
  function energyFrame() {
    const s = cv.energy;
    const m = { l: 44, r: 12, t: 10, b: 22 };
    let lo = Infinity;
    let hi = -Infinity;
    for (const b of bodies) {
      for (let i = 0; i < b.histCount; i++) {
        const v = b.hist[2 * i + 1];
        if (v > 0) { lo = Math.min(lo, v); hi = Math.max(hi, v); }
      }
    }
    if (!Number.isFinite(lo)) { lo = 1e-12; hi = 1e-6; }
    let l0 = Math.floor(Math.log10(Math.max(lo, 1e-17)));
    let l1 = Math.ceil(Math.log10(hi));
    if (l1 - l0 < 3) l1 = l0 + 3;
    const xMax = mode === "earth" ? niceSeconds(Math.max(t, 3600)) : niceMax(Math.max(t, 100));
    const W = s.w - m.l - m.r;
    const H = s.h - m.t - m.b;
    return { m, W, H, l0, l1, xMax, X: (tt) => m.l + (tt / xMax) * W, Y: (v) => m.t + (1 - (Math.log10(v) - l0) / (l1 - l0)) * H };
  }

  function drawEnergy() {
    const s = cv.energy;
    const ctx = s.begin();
    if (s.w < 60 || !bodies.length) return;
    const fr = energyFrame();
    ctx.font = `10px ${F.mono}`;
    ctx.lineWidth = 1;
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    const every = fr.l1 - fr.l0 > 8 ? 4 : fr.l1 - fr.l0 > 4 ? 2 : 1;
    for (let e = fr.l0; e <= fr.l1; e++) {
      const y = Math.round(fr.Y(10 ** e)) + 0.5;
      ctx.strokeStyle = C.line;
      line(ctx, fr.m.l, y, fr.m.l + fr.W, y);
      if ((e - fr.l0) % every === 0) {
        ctx.fillStyle = C.muted;
        ctx.fillText(`10${sup(e)}`, fr.m.l - 6, y);
      }
    }
    ctx.strokeStyle = C.lineStrong;
    const base = fr.m.t + fr.H + 0.5;
    line(ctx, fr.m.l, base, fr.m.l + fr.W, base);
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.fillStyle = C.muted;
    const ticks = 4;
    for (let i = 0; i <= ticks; i++) {
      const tt = (fr.xMax * i) / ticks;
      const label = mode === "earth" ? (fr.xMax > 86400 ? `${Number((tt / 86400).toPrecision(3))} d` : `${Number((tt / 3600).toPrecision(3))} h`) : (fr.xMax >= 1000 ? `${Number((tt / 1000).toPrecision(3))} Gyr` : `${Math.round(tt)} Myr`);
      ctx.fillText(label, Math.min(fr.X(tt), fr.m.l + fr.W - 14), base + 6);
    }
    ctx.lineJoin = "round";
    const order = bodies.map((_, i) => i).sort((a, b) => (a === follow) - (b === follow));
    for (const i of order) {
      const b = bodies[i];
      ctx.strokeStyle = bodyColour(b);
      ctx.lineWidth = i === follow ? 2 : 1;
      ctx.globalAlpha = i === follow ? 1 : 0.55;
      if (b.test) ctx.setLineDash([3, 3]);
      ctx.beginPath();
      let pen = false;
      for (let k = 0; k < b.histCount; k++) {
        const v = b.hist[2 * k + 1];
        if (!(v > 0)) { pen = false; continue; }
        const x = fr.X(b.hist[2 * k]);
        const y = fr.Y(v);
        if (pen) ctx.lineTo(x, y);
        else ctx.moveTo(x, y);
        pen = true;
      }
      ctx.stroke();
      ctx.setLineDash([]);
    }
    ctx.globalAlpha = 1;
    if (t === 0) {
      ctx.fillStyle = C.muted;
      ctx.font = `500 12px ${F.sans}`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("Press Run to start", fr.m.l + fr.W / 2, fr.m.t + fr.H / 2);
    }
    if (hoverHistory >= 0) {
      const b = bodies[follow];
      const k = Math.min(hoverHistory, b.histCount - 1);
      const x = Math.round(fr.X(b.hist[2 * k])) + 0.5;
      ctx.strokeStyle = C.lineStrong;
      ctx.lineWidth = 1;
      line(ctx, x, fr.m.t, x, fr.m.t + fr.H);
      const v = b.hist[2 * k + 1];
      if (v > 0) {
        ctx.fillStyle = C.surface;
        dot(ctx, fr.X(b.hist[2 * k]), fr.Y(v), 5);
        ctx.fillStyle = bodyColour(b);
        dot(ctx, fr.X(b.hist[2 * k]), fr.Y(v), 3.2);
      }
    }
  }

  cv.energy.canvas.addEventListener("pointermove", (e) => {
    const b = bodies[follow];
    if (!b || b.histCount < 2) return;
    const rect = cv.energy.canvas.getBoundingClientRect();
    const fr = energyFrame();
    const tt = ((e.clientX - rect.left - fr.m.l) / fr.W) * fr.xMax;
    let best = 0;
    let bd = Infinity;
    for (let k = 0; k < b.histCount; k++) {
      const dd = Math.abs(b.hist[2 * k] - tt);
      if (dd < bd) { bd = dd; best = k; }
    }
    hoverHistory = best;
    ui.energyTip.replaceChildren();
    const head = document.createElement("b");
    head.textContent = `${b.name}, ${mode === "earth" ? hms(b.hist[2 * best]) : myr(b.hist[2 * best])}`;
    const a = document.createElement("span");
    a.textContent = `|E − E₀| / |E₀| = ${sci(b.hist[2 * best + 1])}`;
    ui.energyTip.append(head, a);
    ui.energyTip.hidden = false;
    const x = fr.X(b.hist[2 * best]);
    const w = ui.energyTip.offsetWidth;
    ui.energyTip.style.left = `${Math.max(0, Math.min(x + 12, cv.energy.w - w - 4))}px`;
    ui.energyTip.style.top = `${fr.m.t + 4}px`;
    dirty.energy = true;
    schedule();
  });
  cv.energy.canvas.addEventListener("pointerleave", () => {
    hoverHistory = -1;
    ui.energyTip.hidden = true;
    dirty.energy = true;
    schedule();
  });

  // ------------------------------------------------------------ details tables
  function table(container, head, rows) {
    const tbl = document.createElement("table");
    const thead = document.createElement("thead");
    const tr = document.createElement("tr");
    for (const [label, numeric] of head) {
      const th = document.createElement("th");
      th.scope = "col";
      th.innerHTML = label;
      if (numeric) th.className = "num";
      tr.append(th);
    }
    thead.append(tr);
    const tbody = document.createElement("tbody");
    for (const row of rows) {
      const r = document.createElement("tr");
      row.forEach((cell, i) => {
        const td = document.createElement("td");
        if (cell instanceof Node) td.append(cell);
        else td.textContent = String(cell);
        if (head[i][1]) td.className = "num";
        r.append(td);
      });
      tbody.append(r);
    }
    tbl.append(thead, tbody);
    container.replaceChildren(tbl);
  }

  function swatch(b, text) {
    const span = document.createElement("span");
    const i = document.createElement("i");
    i.className = "ob-dot";
    i.style.background = bodyColour(b);
    const bold = document.createElement("b");
    bold.textContent = text;
    span.append(i, bold);
    return span;
  }

  function buildStationsTable() {
      table(ui.tables.stations, [["Station"], ["Latitude", 1], ["Longitude", 1], ["Note"]],
        D.stations.map((st, i) => [st.name, `${Math.abs(st.adjustable_latitude && stations[i] ? stations[i].lat : st.lat_deg).toFixed(2)}° ${st.lat_deg >= 0 ? "N" : "S"}`, `${Math.abs(st.lon_deg).toFixed(2)}° ${st.lon_deg >= 0 ? "E" : "W"}`, st.adjustable_latitude ? `latitude adjustable from ${st.adjustable_latitude[0]} to ${st.adjustable_latitude[1]} degrees; the geostationary satellite sets below the horizon at ${(Math.acos(RE / D.geo.radius_km) / rad).toFixed(1)} degrees` : "fixed station"]));
  }

  function buildTables() {
    const earthBodies = MODES.earth.bodies();
    const Mo = D.molniya;
    table(ui.tables.sats, [["Satellite"], ["a (km)", 1], ["e", 1], ["i", 1], ["Ω", 1], ["ω", 1], ["M₀", 1], ["Period", 1], ["Perigee alt. (km)", 1], ["Apogee alt. (km)", 1], ["v at perigee (km/s)", 1], ["v at apogee (km/s)", 1]],
      earthBodies.map((b) => {
        const el = b.elements;
        const geo = b.short === "GEO";
        return [swatch({ ...b }, b.name), grouped(el.a), el.e.toFixed(2), degrees(el.i), degrees(((el.raan % 360) + 360) % 360), degrees(el.argp), degrees(el.m0),
          hms(b.period).replace(/^0 d /, "") + (geo ? " (sidereal day)" : " (half a sidereal day)"),
          geo ? grouped(D.geo.altitude_km) : grouped(Mo.perigee_altitude_km), geo ? grouped(D.geo.altitude_km) : grouped(Mo.apogee_altitude_km),
          geo ? D.geo.speed_km_s.toFixed(3) : Mo.perigee_speed_km_s.toFixed(3), geo ? D.geo.speed_km_s.toFixed(3) : Mo.apogee_speed_km_s.toFixed(3)];
      }));
    buildStationsTable();
    const gb = MODES.galaxy.bodies();
    table(ui.tables.stars, [["Star"], ["<em>Gaia</em> DR3 source_id"], ["G", 1], ["Parallax (mas)", 1], ["RV (km/s)", 1], ["Distance (pc)", 1], ["x, y, z (kpc)"], ["v<sub>x</sub>, v<sub>y</sub>, v<sub>z</sub> (km/s)"], ["e (galpy)", 1], ["z<sub>max</sub> (kpc)", 1], ["R<sub>peri</sub>, R<sub>apo</sub> (kpc)", 1], ["L<sub>z</sub> (kpc km/s)", 1]],
      gb.map((b) => {
        const st = b.star;
        const g = st.gaia;
        const gc = st.galactocentric;
        const r = st.reference;
        const link = document.createElement("a");
        link.href = `https://vizier.cds.unistra.fr/viz-bin/VizieR-5?-ref=VIZ&-out.add=.&-source=I/355/gaiadr3&Source=${st.source_id}`;
        link.textContent = String(st.source_id);
        return [swatch(b, st.name), link, g.phot_g_mean_mag.toFixed(2), pm(g.parallax, g.parallax_error, 3), pm(g.radial_velocity, g.radial_velocity_error, 2), pm(gc.distance_pc, gc.distance_error_pc, 2),
          gc.xyz_kpc.map((v, i) => pm(v, gc.xyz_error_kpc[i], 4)).join(", "), gc.vxyz_km_s.map((v, i) => pm(v, gc.vxyz_error_km_s[i], 1)).join(", "),
          r.eccentricity.toFixed(3), r.zmax_kpc.toFixed(2), `${r.rperi_kpc.toFixed(2)}, ${r.rapo_kpc.toFixed(2)}`, grouped(r.Lz_kpc_km_s)];
      }));
    const P = D.potential;
    const mw = galaxySys.mw;
    const msun = (v) => { const e = Math.floor(Math.log10(v)); return `${(v / 10 ** e).toFixed(1)} × 10${sup(e)}`; };
    table(ui.tables.potential, [["Component"], ["Form"], ["Parameters"], ["Share of the radial force at 8 kpc", 1], ["Mass (solar masses)", 1]], [
      ["Bulge", P.bulge.form, `α = ${P.bulge.alpha}, cut-off radius ${P.bulge.rc_kpc} kpc`, `${Math.round(P.bulge.force_fraction_at_R0 * 100)}%`, msun(mw.masses.bulge_within(245))],
      ["Disc", P.disc.form, `a = ${P.disc.a_kpc} kpc, b = ${P.disc.b_kpc} kpc`, `${Math.round(P.disc.force_fraction_at_R0 * 100)}%`, msun(mw.masses.disc_total_msun)],
      ["Halo", P.halo.form, `scale radius ${P.halo.a_kpc} kpc`, `${Math.round(P.halo.force_fraction_at_R0 * 100)}%`, `${msun(mw.masses.halo_within(245))} within 245 kpc`],
    ]);
  }

  // ------------------------------------------------------------ frame loop
  function markAll() {
    for (const key in dirty) dirty[key] = true;
    schedule();
  }

  function schedule() {
    if (!raf) raf = requestAnimationFrame(frame);
  }

  function frame(now) {
    raf = 0;
    for (const s of Object.values(cv)) if (s.fit()) for (const key in dirty) dirty[key] = true;
    if (running) {
      if (lastFrame && motion.matches && now - lastFrame < REDUCED_FRAME_MS) {
        schedule();
        return;
      }
      const dtReal = lastFrame ? Math.min(MAX_FRAME_S, (now - lastFrame) / 1000) : 0;
      lastFrame = now;
      if (dtReal > 0) {
        advance(speed * dtReal);
        for (const key in dirty) dirty[key] = true;
        updateReadout();
      }
    }
    if (dirty.main) { (mode === "earth" ? drawEarth : drawFaceOn)(); dirty.main = false; }
    if (dirty.side) { (mode === "earth" ? drawVisibility : drawMeridional)(); dirty.side = false; }
    if (dirty.energy) { drawEnergy(); dirty.energy = false; }
    if (running) schedule();
  }

  const resize = new ResizeObserver(() => markAll());
  for (const s of Object.values(cv)) resize.observe(s.canvas);
  T.onThemeChange(() => {
    readTheme();
    buildKeys();
    buildTables();
    markAll();
  });
  document.fonts?.ready.then(() => markAll());

  // ------------------------------------------------------------ start
  buildTables();
  for (const b of [ui.run, ui.step, ui.reset, ui.launch]) b.disabled = false;
  integrator = f.integrator.value;
  const wanted = params.get("mode") === "galaxy" ? "galaxy" : "earth";
  setMode(wanted);
  root.classList.add("is-ready");
  // ?skip=<simulated time> advances before the first frame and ?autorun=1 starts running;
  // both exist for automated screenshots only.
  const skip = Number(params.get("skip"));
  if (skip > 0) {
    advance(skip);
    markAll();
    updateReadout();
  }
  if (params.get("autorun") === "1") run();
}
