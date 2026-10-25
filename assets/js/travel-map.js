// Travel map: azimuthal equidistant projection centred on Porto, the same projection as
// figures/map/build_basemap.py, so the basemap (km coordinates) and the markers agree.
(() => {
  const host = document.querySelector("[data-travel-map]");
  if (!host || host.dataset.ready) return;
  host.dataset.ready = "1";

  const R = 6371.0, LAT0 = 41.1496, LON0 = -8.6110;
  const rad = (d) => (d * Math.PI) / 180;
  const project = (lat, lon) => {
    const p0 = rad(LAT0), l0 = rad(LON0), p = rad(lat), l = rad(lon);
    const cosc = Math.sin(p0) * Math.sin(p) + Math.cos(p0) * Math.cos(p) * Math.cos(l - l0);
    const c = Math.acos(Math.max(-1, Math.min(1, cosc)));
    const k = c < 1e-9 ? 1 : c / Math.sin(c);
    const x = R * k * Math.cos(p) * Math.sin(l - l0);
    const y = R * k * (Math.cos(p0) * Math.sin(p) - Math.sin(p0) * Math.cos(p) * Math.cos(l - l0));
    return [x, -y];
  };
  const distKm = (a, b) => {
    const dp = rad(b.lat - a.lat), dl = rad(b.lon - a.lon);
    const h = Math.sin(dp / 2) ** 2 + Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(dl / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(h));
  };
  const fmt = (n) => Math.round(n).toLocaleString("en-GB");
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[ch]));
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const NS = "http://www.w3.org/2000/svg";

  const data = JSON.parse(host.querySelector(".tmap-data").textContent);
  const byId = Object.fromEntries(data.places.map((p) => [p.id, p]));
  const home = byId[data.home];
  data.places.forEach((p) => { [p.x, p.y] = project(p.lat, p.lon); p.km = distKm(home, p); });

  const stage = host.querySelector(".tmap-stage");
  const canvas = host.querySelector(".tmap-canvas");
  const card = host.querySelector(".tmap-card");
  const segButtons = host.querySelectorAll("[data-view]");

  fetch(host.dataset.basemap).then((r) => r.text()).then((txt) => {
    canvas.innerHTML = txt;
    init(canvas.querySelector("svg"));
  }).catch(() => { canvas.innerHTML = '<p class="tmap-noscript">The map could not load. Every place is listed alongside.</p>'; });

  function init(svg) {
    const gRoutes = svg.querySelector(".tmap-routes");
    const gPlaces = svg.querySelector(".tmap-places");
    const gRings = svg.querySelector(".rings");
    let vb = svg.getAttribute("viewBox").split(/\s+/).map(Number);

    // ring labels
    const ringLabels = [];
    gRings.querySelectorAll("circle").forEach((c) => {
      const r = +c.getAttribute("r");
      const t = document.createElementNS(NS, "text");
      t.setAttribute("class", "ring-label");
      t.textContent = `${fmt(r)} km`;
      gRings.appendChild(t);
      ringLabels.push({ el: t, r });
    });

    // routes: quadratic arcs bent to the left of travel
    const routes = data.routes.map(([a, b, kind]) => {
      const A = byId[a], B = byId[b];
      const dx = B.x - A.x, dy = B.y - A.y, len = Math.hypot(dx, dy);
      const bend = kind === "commute" ? 0.35 : 0.22;
      const cx = (A.x + B.x) / 2 + (dy / len) * len * bend * -1;
      const cy = (A.y + B.y) / 2 - (dx / len) * len * bend * -1;
      const glow = document.createElementNS(NS, "path");
      glow.setAttribute("class", "route-glow");
      const path = document.createElementNS(NS, "path");
      path.setAttribute("class", `route${kind === "commute" ? " commute" : ""}`);
      gRoutes.append(glow, path);
      return { a: A, b: B, cx, cy, path, glow, t: 0 };
    });
    const drawRoute = (r, t) => {
      r.t = t;
      // de Casteljau: the first part of the quadratic up to t
      const x0 = r.a.x, y0 = r.a.y;
      const qx = x0 + (r.cx - x0) * t, qy = y0 + (r.cy - y0) * t;
      const mx = r.cx + (r.b.x - r.cx) * t, my = r.cy + (r.b.y - r.cy) * t;
      const ex = qx + (mx - qx) * t, ey = qy + (my - qy) * t;
      const d = t <= 0 ? "" : `M${x0.toFixed(1)} ${y0.toFixed(1)} Q${qx.toFixed(1)} ${qy.toFixed(1)} ${ex.toFixed(1)} ${ey.toFixed(1)}`;
      r.path.setAttribute("d", d); r.glow.setAttribute("d", d);
    };

    // places
    const marks = data.places.map((p) => {
      const g = document.createElementNS(NS, "g");
      g.setAttribute("class", `place${p.role === "home" ? " is-home" : ""}${p.role === "waypoint" ? " is-waypoint" : ""}`);
      g.setAttribute("tabindex", p.role === "waypoint" ? "-1" : "0");
      g.setAttribute("role", "button");
      g.setAttribute("aria-label", `${p.name}, ${p.country}`);
      g.dataset.place = p.id;
      const halo = document.createElementNS(NS, "circle");
      halo.setAttribute("class", "place-halo"); halo.setAttribute("r", p.role === "home" ? 13 : 9);
      const dot = document.createElementNS(NS, "circle");
      dot.setAttribute("class", "place-dot"); dot.setAttribute("r", p.role === "home" ? 6 : p.role === "waypoint" ? 3.5 : 5);
      const label = document.createElementNS(NS, "text");
      label.setAttribute("class", "place-label"); label.setAttribute("x", 9); label.setAttribute("y", 4);
      label.textContent = p.name;
      g.append(halo, dot, label);
      gPlaces.appendChild(g);
      return { p, g, label, w: p.name.length * 7 + 10 };
    });

    // view handling --------------------------------------------------------------
    const pxPerUnit = () => svg.clientWidth / vb[2];
    const lodFor = (w) => (w > 7000 ? "world" : w > 1100 ? "europe" : "portugal");
    const placeLabels = () => {
      const s = 1 / pxPerUnit();
      const taken = [];
      const prio = (m) => (m.p.role === "home" ? 0 : m.p.role === "waypoint" ? 3 : 1);
      [...marks].sort((a, b) => prio(a) - prio(b) || a.p.km - b.p.km).forEach((m) => {
        const sx = (m.p.x - vb[0]) * pxPerUnit(), sy = (m.p.y - vb[1]) * pxPerUnit();
        const box = [sx + 8, sy - 10, sx + 8 + m.w, sy + 8];
        const inView = sx > -20 && sy > -20 && sx < svg.clientWidth + 20 && sy < svg.clientHeight + 20;
        const clash = taken.some((t) => box[0] < t[2] && box[2] > t[0] && box[1] < t[3] && box[3] > t[1]);
        const show = inView && !clash && m.p.role !== "waypoint";
        m.label.style.display = show ? "" : "none";
        if (show) taken.push(box);
        taken.push([sx - 7, sy - 7, sx + 7, sy + 7]);
        m.g.setAttribute("transform", `translate(${m.p.x.toFixed(2)} ${m.p.y.toFixed(2)}) scale(${s.toFixed(4)})`);
      });
      ringLabels.forEach(({ el, r }) => {
        el.setAttribute("x", (r * 0.7071 + 4 * s).toFixed(1));
        el.setAttribute("y", (-r * 0.7071).toFixed(1));
        el.setAttribute("font-size", (11 * s).toFixed(2));
        const px = r * pxPerUnit();
        el.style.display = px > 46 && px < svg.clientWidth * 0.9 ? "" : "none";
      });
    };
    const fitView = (ids, pad = 0.18) => {
      const pts = ids.map((id) => byId[id]);
      let x0 = Math.min(...pts.map((p) => p.x)), x1 = Math.max(...pts.map((p) => p.x));
      let y0 = Math.min(...pts.map((p) => p.y)), y1 = Math.max(...pts.map((p) => p.y));
      let w = Math.max(x1 - x0, 80), h = Math.max(y1 - y0, 80);
      x0 -= w * pad; x1 += w * pad; y0 -= h * pad * 1.3; y1 += h * pad;
      w = x1 - x0; h = y1 - y0;
      const aspect = svg.clientWidth / Math.max(svg.clientHeight, 1);
      if (w / h > aspect) { const nh = w / aspect; y0 -= (nh - h) / 2; h = nh; } else { const nw = h * aspect; x0 -= (nw - w) / 2; w = nw; }
      return [x0, y0, w, h];
    };
    const setVB = (v) => {
      vb = v;
      svg.setAttribute("viewBox", v.map((n) => n.toFixed(1)).join(" "));
      svg.dataset.lod = lodFor(v[2]);
      placeLabels();
    };
    const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
    let anim = 0;
    const animateTo = (target, ms) => new Promise((done) => {
      cancelAnimationFrame(anim);
      if (reduced || ms <= 0) { setVB(target); done(); return; }
      const from = vb.slice(), t0 = performance.now();
      // interpolate the centre linearly and the width geometrically, for an even zoom
      const c0 = [from[0] + from[2] / 2, from[1] + from[3] / 2], c1 = [target[0] + target[2] / 2, target[1] + target[3] / 2];
      const step = (now) => {
        const k = ease(Math.min(1, (now - t0) / ms));
        const w = from[2] * Math.pow(target[2] / from[2], k), h = from[3] * Math.pow(target[3] / from[3], k);
        const cx = c0[0] + (c1[0] - c0[0]) * k, cy = c0[1] + (c1[1] - c0[1]) * k;
        setVB([cx - w / 2, cy - h / 2, w, h]);
        if (k < 1) anim = requestAnimationFrame(step); else done();
      };
      anim = requestAnimationFrame(step);
    });
    const drawRoutes = (list, ms, stagger) => Promise.all(list.map((r, i) => new Promise((done) => {
      if (reduced || ms <= 0) { drawRoute(r, 1); done(); return; }
      setTimeout(() => {
        const t0 = performance.now();
        const step = (now) => { const k = Math.min(1, (now - t0) / ms); drawRoute(r, ease(k)); if (k < 1) requestAnimationFrame(step); else done(); };
        requestAnimationFrame(step);
      }, i * stagger);
    })));
    const pressed = (name) => segButtons.forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.view === name)));
    const goView = (name, ms = 1100) => { pressed(name); return animateTo(fitView(data.views[name]), ms); };

    const inSet = (r, ids) => ids.includes(r.b.id);
    const narrative = async () => {
      closeCard();
      routes.forEach((r) => drawRoute(r, 0));
      pressed("portugal");
      setVB(fitView(data.views.portugal));
      await drawRoutes(routes.filter((r) => inSet(r, ["vila-do-conde", "guimaraes", "coimbra", "lisbon"])), 650, 180);
      await goView("europe", 1400);
      await drawRoutes(routes.filter((r) => inSet(r, ["cadiar", "lluc", "bologna", "aarhus"])), 800, 200);
      await drawRoutes(routes.filter((r) => inSet(r, ["padova"])), 450, 0);
      await goView("world", 1600);
      await drawRoutes(routes.filter((r) => inSet(r, ["santiago"])), 1100, 0);
      await drawRoutes(routes.filter((r) => inSet(r, ["paranal"])), 500, 0);
    };

    // cards ---------------------------------------------------------------------
    let openId = null, hideTimer = 0;
    const tagClass = (t) => `tag tag--${t}`;
    function openCard(id, anchorEl) {
      const p = byId[id]; if (!p || p.role === "waypoint") return;
      clearTimeout(hideTimer);
      openId = id;
      marks.forEach((m) => m.g.classList.toggle("is-active", m.p.id === id));
      routes.forEach((r) => r.path.classList.toggle("is-dim", !(r.a.id === id || r.b.id === id || (id === "paranal" && r.b.id === "santiago"))));
      host.querySelectorAll(".tmap-list [data-place]").forEach((b) => b.setAttribute("aria-current", String(b.dataset.place === id)));
      const items = p.items.slice(0, 6).map((it) => `<li><span class="${tagClass(it.tag)}">${esc(it.label)}</span><span>${it.title}${it.when ? ` <span class="kicker">${esc(it.when)}</span>` : ""}</span></li>`).join("");
      const more = p.items.length > 6 ? `<p class="kicker">and ${p.items.length - 6} more in the record</p>` : "";
      card.innerHTML = `${p.photo ? `<img src="${esc(p.photo)}" alt="${esc(p.photo_alt)}">` : `<div class="tmap-card-art"><span>${esc(p.name.toUpperCase())}</span><span>${p.lat.toFixed(2)}°, ${p.lon.toFixed(2)}°</span></div>`}
        <div class="card-body"><p class="where">${esc(p.country)}${p.role === "home" ? " · home base" : ` · ${fmt(p.km)} km from Porto`}</p><h3>${esc(p.name)}</h3>${p.blurb ? `<p>${p.blurb}</p>` : ""}${items ? `<ul>${items}</ul>` : ""}${more}${p.photo_credit ? `<p class="credit">Photo: ${esc(p.photo_credit)}</p>` : ""}</div>`;
      card.hidden = false;
      // position near the marker, inside the stage
      const sr = stage.getBoundingClientRect();
      const ar = (anchorEl || marks.find((m) => m.p.id === id).g).getBoundingClientRect();
      const cw = card.offsetWidth, ch = card.offsetHeight;
      let left = ar.left - sr.left + ar.width / 2 + 16, top = ar.top - sr.top - ch / 2;
      if (left + cw > sr.width - 12) left = ar.left - sr.left - cw - 16;
      left = Math.max(12, Math.min(left, sr.width - cw - 12));
      top = Math.max(56, Math.min(top, sr.height - ch - 12));
      card.style.left = `${left}px`; card.style.top = `${top}px`;
      requestAnimationFrame(() => card.classList.add("is-open"));
    }
    function closeCard() {
      openId = null; card.classList.remove("is-open");
      marks.forEach((m) => m.g.classList.remove("is-active"));
      routes.forEach((r) => r.path.classList.remove("is-dim"));
      host.querySelectorAll(".tmap-list [data-place]").forEach((b) => b.setAttribute("aria-current", "false"));
      hideTimer = setTimeout(() => { if (!openId) card.hidden = true; }, 200);
    }
    marks.forEach((m) => {
      m.g.addEventListener("pointerenter", () => openCard(m.p.id, m.g));
      m.g.addEventListener("pointerleave", () => { hideTimer = setTimeout(() => { if (!card.matches(":hover")) closeCard(); }, 260); });
      m.g.addEventListener("focus", () => openCard(m.p.id, m.g));
      m.g.addEventListener("blur", () => closeCard());
      m.g.addEventListener("click", (e) => { e.stopPropagation(); openCard(m.p.id, m.g); });
    });
    card.addEventListener("pointerleave", () => closeCard());
    stage.addEventListener("click", (e) => { if (!card.contains(e.target)) closeCard(); });
    addEventListener("keydown", (e) => { if (e.key === "Escape") closeCard(); });

    // controls ---------------------------------------------------------------------
    segButtons.forEach((b) => b.addEventListener("click", () => { closeCard(); goView(b.dataset.view); }));
    host.querySelector(".tmap-replay").addEventListener("click", () => narrative());
    const viewOf = (p) => (p.country === "Portugal" ? "portugal" : p.country === "Chile" ? "world" : "europe");
    host.querySelectorAll(".tmap-list [data-place]").forEach((b) => b.addEventListener("click", async () => {
      const p = byId[b.dataset.place];
      const v = p.id === "porto" ? "europe" : viewOf(p);
      await goView(v, 900);
      openCard(p.id);
    }));
    new ResizeObserver(() => setVB(fitView(data.views[[...segButtons].find((b) => b.getAttribute("aria-pressed") === "true")?.dataset.view || "world"]))).observe(stage);

    // first view: play the narrative once the map is in view
    setVB(fitView(data.views.world));
    routes.forEach((r) => drawRoute(r, reduced ? 1 : 0));
    if (reduced) { pressed("world"); return; }
    const io = new IntersectionObserver((entries) => {
      if (entries.some((e) => e.isIntersecting)) { io.disconnect(); narrative(); }
    }, { threshold: 0.45 });
    io.observe(stage);
  }
})();
