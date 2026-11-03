// The globe on the home page: an orthographic projection painted on a canvas (sea, graticule, land, routes
// along great circles from Porto), with the places and their labels as SVG on top so they can be hovered.
// Three maps: Natural Earth 1:110m for the whole globe, and two regional cuts of 1:10m for Europe with
// North Africa and South America, and for Iberia. On arrival the routes draw out in three stages
// (Portugal, Europe, the world); drag to turn, zoom with the buttons, click a place to fly to it.
(() => {
  const wrap = document.querySelector("[data-globe]");
  if (!wrap || !window.d3 || !window.topojson) return;
  const data = JSON.parse(wrap.querySelector("[data-places]").textContent);
  const PLACES = data.places, HOME = data.home;
  const ROUTES = data.routes.map((r) => [r[0], r[1]]);
  const P = Object.fromEntries(PLACES.map((p) => [p.id, p]));
  const VISITED = new Set(["620", "724", "380", "208", "152"]);   // Portugal, Spain, Italy, Denmark, Chile (ISO 3166 numeric)
  const FLAG = { Portugal: "portugal", Spain: "spain", Italy: "italy", Denmark: "denmark", Chile: "chile" };
  const ORDER = ["Portugal", "Spain", "Italy", "Denmark", "Chile"];
  const VIEWS = { portugal: { c: [-8.4, 39.8], k: 14 }, europe: { c: [2, 47], k: 4.2 }, world: { c: [-32, 12], k: 1 } };
  const stageOf = (p) => p.country === "Portugal" ? 0 : p.country === "Chile" ? 2 : 1;
  const STAGE = [[], [], []];
  ROUTES.forEach((r) => { if (r[1] !== HOME) STAGE[stageOf(P[r[1]])].push(r[1]); });
  const still = matchMedia("(prefers-reduced-motion: reduce)").matches || new URLSearchParams(location.search).has("static");
  const cv = wrap.querySelector("canvas.map"), svg = wrap.querySelector("svg.globe"), tip = wrap.querySelector(".tip"), stage = wrap.querySelector(".stage"), list = wrap.querySelector(".places");
  const NS = "http://www.w3.org/2000/svg";
  let view = { lon: VIEWS.world.c[0], lat: VIEWS.world.c[1], k: 1 }, drawn = Object.fromEntries(ROUTES.map((r) => [r[1], still ? 1 : 0])), anim = 0, moving = 0;
  let world = null, mid = null, near = null, paint = null, pal = {};
  const el = (n, a = {}, parent = svg) => { const e = document.createElementNS(NS, n); for (const k in a) e.setAttribute(k, a[k]); parent.appendChild(e); return e; };
  // colours resolved by the browser (light-dark() included), cached until the theme changes
  const probe = document.createElement("i"); probe.style.display = "none"; document.body.appendChild(probe);
  const colour = (n) => pal[n] || ((probe.style.color = `var(${n})`), (pal[n] = getComputedStyle(probe).color));
  const repaint = () => { pal = {}; if (paint) paint(); };
  document.addEventListener("themechange", repaint);
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", repaint);

  // years for the list and the cards, from the line each place carries
  const years = (p) => { const ys = [...new Set((p.line.match(/20\d\d/g) || []))]; if (p.id === HOME) return "home"; if (/\bto\b/.test(p.line) && ys.length > 1) return ys.join(" to "); return ys.join(", "); };
  const short = (p) => p.line.replace(/,?\s*(in\s+)?(May\s+)?20\d\d(\s+to\s+20\d\d)?\.?$/, ".").replace("..", ".");

  function setup() {
    const W = svg.clientWidth, H = svg.clientHeight, R = Math.min(W, H) * 0.42, dpr = Math.min(2, devicePixelRatio || 1);
    cv.width = W * dpr; cv.height = H * dpr;
    const ctx = cv.getContext("2d"); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const proj = d3.geoOrthographic().translate([W / 2, H / 2]).clipAngle(90).precision(0), path = d3.geoPath(proj, ctx);
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.innerHTML = "";
    const dots = el("g");
    // each country keeps its centre and angular radius, so a zoomed view projects only what can be seen;
    // a polygon larger than a hemisphere is wound the wrong way for d3 and would fill the globe, so it is skipped
    const feats = (w) => w.type === "FeatureCollection" ? w.features : topojson.feature(w, w.objects.countries).features;
    const mk = (w) => feats(w).filter((f) => d3.geoArea(f) < 2 * Math.PI).map((f) => {
      const c = d3.geoCentroid(f), b = d3.geoBounds(f);
      const r = Math.max(...[[b[0][0], b[0][1]], [b[1][0], b[1][1]], [b[0][0], b[1][1]], [b[1][0], b[0][1]]].map((q) => d3.geoDistance(c, q)));
      return { f, c, r, v: VISITED.has(f.id) };
    });
    const coarse = mk(world), M = mid ? mk(mid) : coarse;
    const nearIds = near ? new Set(near.features.map((f) => f.id)) : new Set();
    const N = near ? mk(near).concat(M.filter((q) => !nearIds.has(q.f.id))) : M;
    const MIDS = new Set(M.map((q) => q.f.id)), NIDS = new Set(N.map((q) => q.f.id));
    const inBox = (b, l, t) => l > b[0] && l < b[2] && t > b[1] && t < b[3];
    const segs = ROUTES.map(([a, b]) => { const A = P[a], B = P[b], ip = d3.geoInterpolate([A.lon, A.lat], [B.lon, B.lat]); return { b, pts: d3.range(0, 1.0001, 1 / 64).map(ip) }; });
    const marks = PLACES.map((p) => {
      const d = el("circle", { class: "dot" + (p.id === HOME ? " home" : ""), r: p.id === HOME ? 5 : 3.8 }, dots), h = el("circle", { class: "hit", r: 12 }, dots), t = el("text", { class: "lab", dx: 9, dy: 4 }, dots);
      t.textContent = p.name;
      h.addEventListener("pointerenter", () => showTip(p)); h.addEventListener("pointerleave", hideTip); h.addEventListener("click", () => focusPlace(p));
      return { p, d, h, t };
    });
    const gr = d3.geoGraticule().step([10, 10]).precision(1)();   // points every degree keep the meridians curved without resampling
    paint = () => {
      proj.scale(R * view.k).rotate([-view.lon, -view.lat, 0]);
      ctx.clearRect(0, 0, W, H);
      ctx.beginPath(); path({ type: "Sphere" }); ctx.fillStyle = colour("--sea"); ctx.fill();
      ctx.beginPath(); path(gr); ctx.strokeStyle = "rgba(255,255,255,.08)"; ctx.lineWidth = .6; ctx.stroke();
      const m = view.k >= 8 && inBox([-12, 35, 4, 45], view.lon, view.lat) ? N : view.k >= 2.5 && (inBox([-20, 30, 35, 66], view.lon, view.lat) || inBox([-80, -45, -55, -10], view.lon, view.lat)) ? M : coarse;
      const reach = Math.min(Math.PI / 2, 1.15 * Math.hypot(W, H) / 2 / (R * view.k)) + 0.05, ctr = [view.lon, view.lat];
      const layer = (L, edge) => {
        const seen = L.filter((q) => d3.geoDistance(q.c, ctr) - q.r < reach);
        ctx.beginPath(); seen.forEach((q) => path(q.f)); ctx.fillStyle = colour("--land"); ctx.fill(); if (edge) { ctx.strokeStyle = colour("--land-edge"); ctx.lineWidth = .5; ctx.stroke(); }
        ctx.beginPath(); seen.filter((q) => q.v).forEach((q) => path(q.f)); ctx.fillStyle = colour("--visit-fill"); ctx.fill(); if (edge) { ctx.strokeStyle = colour("--visit"); ctx.lineWidth = .7; ctx.stroke(); }
      };
      // the whole world first, then the regional detail over it, so the view never ends at a region's edge;
      // countries the detail redraws are left out of the coarse pass, or its looser coastline shows past the fine one
      if (m !== coarse) { const ids = m === N ? NIDS : MIDS; layer(coarse.filter((q) => !ids.has(q.f.id)), false); layer(m, true); } else layer(m, true);
      const sr = R * view.k, g = ctx.createRadialGradient(W / 2 - sr * .25, H / 2 - sr * .3, sr * .55, W / 2, H / 2, sr);
      g.addColorStop(0, "rgba(0,0,0,0)"); g.addColorStop(1, "rgba(0,0,0,.38)"); ctx.beginPath(); path({ type: "Sphere" }); ctx.fillStyle = g; ctx.fill();
      ctx.strokeStyle = colour("--flow"); ctx.lineWidth = 1.8; ctx.lineCap = "round";
      segs.forEach((s) => { const f = drawn[s.b]; if (f <= 0) return; ctx.beginPath(); path({ type: "LineString", coordinates: s.pts.slice(0, Math.max(2, Math.round(s.pts.length * f))) }); ctx.stroke(); });
      const c = [view.lon, view.lat], placed = [];
      marks.forEach((mk_) => {
        const vis = d3.geoDistance([mk_.p.lon, mk_.p.lat], c) < Math.PI / 2 - 0.02, xy = proj([mk_.p.lon, mk_.p.lat]);
        const inside = xy && xy[0] > 0 && xy[0] < W && xy[1] > 0 && xy[1] < H;
        const on = vis && inside && (mk_.p.id === HOME || drawn[mk_.p.id] > 0.98);
        [mk_.d, mk_.h].forEach((e) => { e.style.display = on ? "" : "none"; if (on) { e.setAttribute("cx", xy[0]); e.setAttribute("cy", xy[1]); } });
        const lab = on && !placed.some((q) => Math.abs(q[0] - xy[0]) < 70 && Math.abs(q[1] - xy[1]) < 16);
        if (lab) placed.push(xy);
        mk_.t.style.display = lab ? "" : "none"; if (lab) { mk_.t.setAttribute("x", xy[0]); mk_.t.setAttribute("y", xy[1]); }
        mk_.xy = xy;
      });
      svg._marks = marks;
    };
    paint();
  }

  const ease = (t) => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  const settle = () => { if (--moving <= 0) { moving = 0; paint(); } };
  const fly = (to, ms) => new Promise((res0) => {
    moving++; const res = () => { settle(); res0(); };
    const a = { ...view }, id = ++anim, t0 = performance.now(), dl = ((to.lon - a.lon + 540) % 360) - 180;
    const step = (now) => { if (id !== anim) return res(); const t = Math.min(1, (now - t0) / ms), e = ease(t);
      view = { lon: a.lon + dl * e, lat: a.lat + (to.lat - a.lat) * e, k: Math.exp(Math.log(a.k) + (Math.log(to.k) - Math.log(a.k)) * e) };
      paint(); t < 1 ? requestAnimationFrame(step) : res(); };
    requestAnimationFrame(step);
  });
  const drawSet = (ids, ms) => new Promise((res0) => {
    moving++; const res = () => { settle(); res0(); };
    const id = anim, t0 = performance.now();
    const step = (now) => { if (id !== anim) return res(); const t = Math.min(1, (now - t0) / ms);
      ids.forEach((b, k) => { drawn[b] = Math.min(1, Math.max(0, t * (1 + 0.35 * (ids.length - 1)) - 0.35 * k)); });
      paint(); t < 1 ? requestAnimationFrame(step) : res(); };
    requestAnimationFrame(step);
  });
  const V = (n) => ({ lon: VIEWS[n].c[0], lat: VIEWS[n].c[1], k: VIEWS[n].k });
  let played = false;
  async function play() {
    if (!world) return;
    if (still) { view = V("world"); paint(); return; }
    ROUTES.forEach((r) => { drawn[r[1]] = 0; }); anim++; moving++; view = V("portugal"); paint();
    await drawSet(STAGE[0], 1100); await fly(V("europe"), 1500); await drawSet(STAGE[1], 1300); await fly(V("world"), 1800); await drawSet(STAGE[2], 1300); settle();
  }
  wrap.querySelectorAll(".ctrl button").forEach((b) => b.addEventListener("click", () => {
    const z = b.dataset.z;
    if (z === "in") fly({ ...view, k: Math.min(30, view.k * 1.8) }, 450);
    if (z === "out") fly({ ...view, k: Math.max(0.8, view.k / 1.8) }, 450);
    if (z === "reset") fly(V("world"), 1100);
    if (z === "replay") play();
  }));
  let drag = null;
  svg.addEventListener("pointerdown", (e) => { if (e.target.classList.contains("hit")) return; moving++; drag = { x: e.clientX, y: e.clientY, v: { ...view } }; anim++; svg.setPointerCapture(e.pointerId); hideTip(); });
  svg.addEventListener("pointermove", (e) => { if (!drag) return; const s = 0.28 / drag.v.k; view = { lon: drag.v.lon - (e.clientX - drag.x) * s, lat: Math.max(-75, Math.min(75, drag.v.lat + (e.clientY - drag.y) * s)), k: drag.v.k }; paint(); });
  svg.addEventListener("pointerup", () => { if (drag) { drag = null; settle(); } });
  svg.addEventListener("wheel", (e) => { if (!e.ctrlKey) return; e.preventDefault(); view = { ...view, k: Math.max(0.8, Math.min(30, view.k * Math.exp(-e.deltaY * 0.01))) }; paint(); }, { passive: false });

  function showTip(p) {
    const m = svg._marks && svg._marks.find((q) => q.p === p); if (!m || !m.xy) return;
    tip.innerHTML = `<div class="ph">${p.photo ? `<img src="${p.photo}" alt="">` : ""}<div class="cap"><svg class="flag" width="18" height="12"><use href="#f-${FLAG[p.country]}"/></svg><b>${p.name}</b><span>${p.id === HOME ? "Home" : years(p)}</span></div>${p.credit ? `<small>${p.credit}</small>` : ""}</div><p>${short(p)}</p>`;
    const W = stage.clientWidth, x = m.xy[0] + 18 + 280 > W ? m.xy[0] - 298 : m.xy[0] + 18, y = Math.max(12, Math.min(stage.clientHeight - 260, m.xy[1] - 80));
    tip.style.left = x + "px"; tip.style.top = y + "px"; tip.classList.add("on");
  }
  function hideTip() { tip.classList.remove("on"); }
  async function focusPlace(p) {
    list.querySelectorAll("button").forEach((b) => b.toggleAttribute("aria-current", b.dataset.id === p.id));
    ROUTES.forEach((r) => { drawn[r[1]] = 1; });
    const k = p.country === "Portugal" ? 10 : p.country === "Chile" ? 3 : 4;
    await fly({ lon: p.lon, lat: p.lat, k }, 1200); showTip(p);
  }
  // the list: by country, then by date
  const sortKey = (p) => { const y = (p.line.match(/20\d\d/) || ["2017"])[0]; return p.id === HOME ? 2017 : +y; };
  ORDER.forEach((cn) => {
    const ps = PLACES.filter((p) => p.country === cn).sort((a, b) => sortKey(a) - sortKey(b)); if (!ps.length) return;
    const h = document.createElement("h3"); h.innerHTML = `<svg class="flag" width="18" height="12"><use href="#f-${FLAG[cn]}"/></svg>${cn}`; list.appendChild(h);
    ps.forEach((p) => { const b = document.createElement("button"); b.type = "button"; b.dataset.id = p.id; b.innerHTML = `<span class="nm">${p.name}</span><span class="yr">${years(p)}</span>`; b.addEventListener("click", () => focusPlace(p)); list.appendChild(b); });
  });
  const maps = wrap.dataset.maps;
  Promise.all(["countries-110m.json", "globe-mid.json", "globe-near.json"].map((f) => fetch(maps + f).then((r) => r.json()))).then(([w, m, n]) => {
    world = w; mid = m; near = n; setup();
    const go = () => { if (!played) { played = true; play(); } };
    if (wrap.classList.contains("is-in")) go(); else new IntersectionObserver((es, io) => { if (es.some((e) => e.isIntersecting)) { io.disconnect(); go(); } }, { threshold: 0.3 }).observe(wrap);
  });
  addEventListener("resize", () => { if (world) setup(); });
})();
