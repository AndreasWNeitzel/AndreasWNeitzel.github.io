// The Research header film. Nine segments slide through one 16:9 stage like a train: each slides in from the right,
// holds, and starts to leave as the next starts to arrive. The pictures are clips drawn on one canvas; captions and
// labels are HTML over it, placed in fractions of the 1920 x 1080 frame, and never move while a segment moves.
// Clips load just before their segment and are let go after it; the film stops off screen and in a hidden tab.
// Under reduced motion (or ?static) the plate shows one still with its labels.
(() => {
  "use strict";
  const rf = document.querySelector(".rf");
  if (!rf) return;
  const plate = rf.closest(".plate");
  const words = JSON.parse(plate.querySelector(".rf-words").textContent);
  const still = matchMedia("(prefers-reduced-motion: reduce)").matches || new URLSearchParams(location.search).has("static");
  const FPS = 30, W = 1920, H = 1080, SLIDE = 40, TRAIN = 20, FEATHER = 160, START = 200;   // START: the still's frame of the missions

  // timings in frames; lead: the clip holds its first frame while sliding in and its last while sliding out
  const SEGS = [
    { id: "missions", clip: "rh-missions", len: 390, out: 350 },
    { id: "star", clip: "rh-star", len: 360, out: 320, capIn: 165, capOut: 312 },
    { id: "evolution", clip: "rh-evolution", len: 440, out: 400, lead: SLIDE, frames: 360 },
    { id: "seismo", clip: "rh-seismo", len: 440, out: 400, lead: SLIDE, frames: 360 },
    { id: "cluster", clip: "rh-cluster", len: 520, out: 480, loop: 480 },
    { id: "maps", clip: "rh-maps", len: 510, out: 470 },
    { id: "janus", clip: "rh-janus", len: 330, out: 290, loop: 360 },
    { id: "starfold", clip: "rh-starfold", len: 336, out: 296, lead: SLIDE, frames: 256 },
    { id: "hall", clip: "hall-hd", poster: "hall-hd", len: 330, out: 290, loop: 240 },
  ];
  let L = 0;
  for (const s of SEGS) { s.start = L; L += s.out + TRAIN; }
  const byId = Object.fromEntries(SEGS.map((s) => [s.id, s]));

  const smooth = (u) => { u = Math.min(Math.max(u, 0), 1); return u * u * (3 - 2 * u); };
  const easeOut = (u) => { u = Math.min(Math.max(u, 0), 1); return 1 - (1 - u) ** 3; };
  const easeIn = (u) => { u = Math.min(Math.max(u, 0), 1); return u ** 3; };
  const ramp = (f, a, b) => smooth((f - a) / (b - a));
  const local = (s, T) => { const f = (((T - s.start) % L) + L) % L; return f < s.len ? f : -1; };
  const clipFrame = (s, f) => s.loop ? f % s.loop : s.lead != null ? Math.min(Math.max(f - s.lead, 0), s.frames - 1) : Math.min(f, s.len - 1);
  const slideX = (s, f) => f < SLIDE ? 1 - easeOut(f / SLIDE) : f >= s.out ? -easeIn((f - s.out + 1) / (s.len - s.out)) : 0;
  const textOn = (s, f, a) => ramp(f, a, a + 15) * (1 - ramp(f, s.out - 12, s.out));

  // ---------- words over the picture ----------
  const svg = rf.querySelector(".rf-lines"), labs = rf.querySelector(".rf-labs"), capEl = rf.querySelector(".rf-cap");
  let D = null, ovKey = "";
  const px = (p) => [p[0] * W, p[1] * H];
  const lab = (html, p, align, op, cls = "") => op > 0.001
    ? `<div class="rf-lab${align === "l" ? " l" : align === "c" ? " c" : ""}${cls ? " " + cls : ""}" style="left:${(p[0] / W) * 100}%;top:${(p[1] / H) * 100}%;opacity:${op.toFixed(3)}">${html}</div>` : "";
  function part(pts, g) {                                           // the first fraction g of a polyline, by length
    if (g <= 0) return null;
    const seg = []; let tot = 0;
    for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg.push(d); tot += d; }
    let left = Math.min(g, 1) * tot; const out = [pts[0]];
    for (let i = 1; i < pts.length; i++) {
      if (left >= seg[i - 1]) { out.push(pts[i]); left -= seg[i - 1]; continue; }
      const u = left / seg[i - 1]; out.push([pts[i - 1][0] + u * (pts[i][0] - pts[i - 1][0]), pts[i - 1][1] + u * (pts[i][1] - pts[i - 1][1])]); break;
    }
    return out;
  }
  const line = (pts, g, op = 1) => { const p = part(pts, g); if (!p || op <= 0.001) return ""; const s = p.map((v) => `${v[0].toFixed(1)},${v[1].toFixed(1)}`).join(" ");
    return `<polyline class="u" points="${s}" style="opacity:${op}"/><polyline points="${s}" style="opacity:${op}"/>`; };
  const dot = (p, op) => op > 0.001 ? `<circle cx="${p[0]}" cy="${p[1]}" r="2.6" style="opacity:${op}"/>` : "";
  const lead45 = (p, rowY, labelX, side) => [p, [p[0] + side * Math.abs(p[1] - rowY), rowY], [labelX - side * 8, rowY]];   // 45 degrees, then level
  const num = (n) => Number(n).toLocaleString("en-GB");
  const sub = (t) => t.replace(/_z$/, "<sub>z</sub>").replace(/_max$/, "<sub>max</sub>");
  // the star: one column in zone order; parallel 45 degree leaders, the inner zones marked on the cut's right face,
  // the chromosphere in the bright limb ring and the corona in the glow beyond it
  const ZONES = [[960, 540], [1070, 525], [1150, 540], [1200, 600], [1266, 652], [1255, 787]], ZROWS = [184, 292, 400, 508, 616, 724], ZX = 1478;
  const STATIONS = [["s1_ms", 130, 150], ["s2_rgb_tip", 200, 215], ["s3_red_clump", 245, 260], ["s4_white_dwarf", 310, 310]];

  function overlay(act) {
    let lines = "", html = "", cap = null, capOp = 0;
    for (const [s, f] of act) {
      const fi = Math.floor(f), cf = clipFrame(s, f), off = 1 - ramp(f, s.out - 12, s.out);   // fi indexes the per-frame tracks
      if (s.id === "missions") {
        for (const c of Object.values(D.seg1.craft)) {
          const g = c.line[fi], o = c.opacity[fi];
          if (g <= 0 && o <= 0) continue;
          const lp = px(c.label);
          lines += line([px(c.start), lp], g);
          html += lab(c.style === "italic" ? `<i>${c.name}</i>` : c.name, [lp[0] + (c.side === "left" ? -10 : 10), lp[1]], c.side === "left" ? "l" : "r", o);
        }
      } else if (s.id === "star") {
        const out = 1 - ramp(f, 300, 312);
        ZONES.forEach((p, i) => {
          const t0 = 150 + 6 * i, g = ramp(f, t0, t0 + 14) * (out > 0 ? 1 : 0);
          lines += line(lead45(p, ZROWS[i], ZX, 1), g, out) + dot(p, Math.min(1, g * 3) * out);
          html += lab(words.zones[i], [ZX, ZROWS[i]], "r", ramp(f, t0 + 14, t0 + 26) * out);
        });
      } else if (s.id === "evolution") {
        const d = D.seg8, ax = textOn(s, f, SLIDE + 30), iso = textOn(s, f, SLIDE + 65);
        for (const [v, p] of Object.entries(d.teff)) html += lab(num(v), px(p), "c", ax, "tk");
        for (const [v, p] of Object.entries(d.lum)) html += lab(num(Number(v)), px(p), "l", ax, "tk");
        html += lab(words.axes.teff, px(d.title_teff), "c", ax, "tk") + lab(words.axes.lum, px(d.title_lum), "c", ax, "tk rot");
        for (const [v, p] of Object.entries(d.iso)) {
          const q = px(p), top = q[1] < 0.15 * H;
          html += lab(`${v} R<sub>☉</sub>`, top ? [q[0], q[1] - 20] : [q[0] + 12, q[1] - 16], top ? "c" : "r", iso, "tk dim");
        }
        STATIONS.forEach(([k, arrive, leave], i) => {
          const st = d.stations[k], c = px(st.centre), lp = px(st.label);
          html += lab(words.stations[i], [lp[0] + 4, lp[1]], "r", ramp(cf, arrive, arrive + 12) * off);
          const u = [lp[0] - c[0], lp[1] - c[1]], n = Math.hypot(u[0], u[1]);   // once the star has moved on, a fixed leader to the track
          if (n > 30) lines += line([[lp[0] - (u[0] / n) * 4, lp[1] - (u[1] / n) * 4], [c[0] + (u[0] / n) * 10, c[1] + (u[1] / n) * 10]], ramp(cf, leave + 4, leave + 16), off);
        });
      } else if (s.id === "seismo") {
        const d = D.seg9, ax = textOn(s, f, SLIDE + 30);
        for (const [v, p] of Object.entries(d.freq)) html += lab(num(v), px(p), "c", ax, "tk");
        html += lab(words.axes.freq, [px(d.title)[0], px(d.title)[1] + 30], "c", ax, "tk");
        html += lab("ν<sub>max</sub>", [px(d.nu_max)[0], px(d.nu_max)[1] + 16], "c", ramp(cf, 215, 230) * off, "tk");
        html += lab("Δν", px(d.delta_nu), "c", ramp(cf, 225, 240) * off);
        [[d.l0, 216, 576, -1], [d.l1, 238, 1478, 1], [d.l2, 486, 1478, 1]].forEach(([p, row, lx, side], i) => {
          const q = px(p), t0 = 232 + 6 * i, g = ramp(cf, t0, t0 + 14) * (off > 0 ? 1 : 0);
          lines += line(lead45(q, row, lx, side), g, off) + dot(q, Math.min(1, g * 3) * off);
          html += lab(`<i>l</i> = ${i}`, [lx, row], side > 0 ? "r" : "l", ramp(cf, t0 + 14, t0 + 26) * off);
        });
      } else if (s.id === "cluster") {
        const P = D.seg3.phases, on = f < s.out ? 1 : 0;
        html += lab(words.before, [0.955 * W, 0.1 * H], "l", ramp(cf, P.before[0], P.before[0] + 12) * (1 - ramp(cf, P.wipe[0] + 18, P.wipe[0] + 30)) * on);
        html += lab(words.after, [0.22 * W, 0.1 * H], "r", ramp(cf, P.wipe[0] + 10, P.wipe[0] + 22) * (1 - ramp(cf, P.resolved[1] - 12, P.resolved[1])) * on);
      } else if (s.id === "maps") {
        const fr = D.seg4.frame[Math.min(fi, D.seg4.frame.length - 1)], b = D.seg4.bar;
        for (const [k, m] of Object.entries(D.seg4.maps)) {
          const o = fr.legend[k]; if (!o || o <= 0.001) continue;
          const stops = m.stops.map((st) => `rgb(${st.rgb.map((v) => Math.round(v * 255)).join(" ")}) ${(st.t * 100).toFixed(1)}%`).join(",");
          const ticks = m.ticks.map((t, i) => `<span style="left:${m.tick_positions[i] * 100}%">${t}</span>`).join("");
          html += `<div class="rf-bar" style="left:${(b[0] / W) * 100}%;top:${(b[1] / H - 0.075) * 100}%;width:${(b[2] / W) * 100}%;opacity:${o}"><div>${sub(m.label)}${m.unit ? ` <span class="note">(${m.unit})</span>` : ""}${m.note ? `<div class="note">${m.note}</div>` : ""}</div><div class="g" style="background:linear-gradient(90deg,${stops})"></div><div class="ticks">${ticks}</div></div>`;
        }
      }
      let o = s.id === "maps" ? D.seg4.frame[Math.min(fi, D.seg4.frame.length - 1)].caption : s.capIn != null ? ramp(f, s.capIn, s.capIn + 20) * (1 - ramp(f, s.capOut - 12, s.capOut)) : textOn(s, f, SLIDE);
      if (slideX(s, f) !== 0) o = 0;
      const text = words.captions[s.id];
      if (text && o > capOp) { capOp = o; cap = text; }
    }
    const key = lines + html;
    if (key !== ovKey) { svg.innerHTML = lines; labs.innerHTML = html; ovKey = key; }
    if (cap && capEl.textContent !== cap) capEl.textContent = cap;
    capEl.style.opacity = capOp.toFixed(3);
  }

  // ---------- still: one frame of the missions with their labels ----------
  fetch(rf.dataset.data).then((r) => r.json()).then((data) => {
    D = data;
    overlay([[byId.missions, START]]);
    if (!still) run();
  }).catch(() => {});

  // ---------- film ----------
  function run() {
    const cv = rf.querySelector(".rf-cv"), ctx = cv.getContext("2d");
    const layer = document.createElement("canvas"), lctx = layer.getContext("2d");
    const av1 = document.createElement("video").canPlayType('video/mp4; codecs="av01.0.05M.08"') !== "";
    let T = START, last = performance.now(), onScreen = true, started = false, quiet = false, paused = false;

    function fit() {
      const r = rf.getBoundingClientRect(), k = Math.min((window.devicePixelRatio || 1), W / Math.max(r.width, 1));
      const w = Math.round(r.width * k), h = Math.round(r.height * k);
      if (w && (cv.width !== w || cv.height !== h)) { cv.width = layer.width = w; cv.height = layer.height = h; }
    }
    function want(s) {                                              // load a segment's clip and poster
      if (s.video) return;
      const v = document.createElement("video");
      v.muted = true; v.playsInline = true; v.preload = "auto"; v.loop = !!s.loop;
      v.src = rf.dataset.video + s.clip + (av1 ? ".av1.mp4" : ".h264.mp4");
      s.video = v;
      if (!s.img) { s.img = new Image(); s.img.decoding = "async"; s.img.src = rf.dataset.poster + (s.poster || s.clip) + ".poster.webp"; }
    }
    function drop(s) {                                              // let a clip go once its segment is over
      if (!s.video) return;
      s.video.pause(); s.video.removeAttribute("src"); s.video.load(); s.video = null;
    }
    function sync(play) {
      for (const s of SEGS) {
        const f = local(s, T), soon = local(s, T + 120);
        if (f < 0 && !(soon >= 0 && soon < 120)) { drop(s); continue; }
        want(s);
        const v = s.video;
        if (f < 0) { if (!v.paused) v.pause(); if (v.readyState >= 1 && v.currentTime > 0.05) v.currentTime = 0.5 / FPS; continue; }
        const at = (clipFrame(s, f) + 0.5) / FPS, dur = (s.loop || s.frames || s.len) / FPS;
        let err = Math.abs(v.currentTime - at); if (s.loop) err = Math.min(err, dur - err);
        const hold = s.lead != null && (f < s.lead || f - s.lead >= s.frames);
        if (err > 0.15 && v.readyState >= 1) v.currentTime = at;
        if (play && !hold) { if (v.paused) v.play().catch(() => {}); } else if (!v.paused) v.pause();
      }
    }
    function draw() {
      fit();
      const w = cv.width, h = cv.height, fw = (FEATHER / W) * w;
      ctx.globalCompositeOperation = "source-over"; ctx.fillStyle = "#000"; ctx.fillRect(0, 0, w, h);
      const act = [];
      for (const s of SEGS) { const f = local(s, T); if (f >= 0) act.push([s, f]); }
      for (const [s, f] of act) {
        const x = slideX(s, f) * w;
        lctx.globalCompositeOperation = "source-over"; lctx.clearRect(0, 0, w, h);
        if (s.video && s.video.readyState >= 2) lctx.drawImage(s.video, 0, 0, w, h);
        else if (s.img && s.img.complete && s.img.naturalWidth) lctx.drawImage(s.img, 0, 0, w, h);
        const k = Math.min(Math.abs(x) / ((300 / W) * w), 1);          // the side edges feather to black while moving
        if (k > 0) {
          lctx.globalCompositeOperation = "destination-in";
          const g = lctx.createLinearGradient(0, 0, w, 0), a = 1 - k;
          g.addColorStop(0, `rgba(0,0,0,${a})`); g.addColorStop(fw / w, "#000"); g.addColorStop(1 - fw / w, "#000"); g.addColorStop(1, `rgba(0,0,0,${a})`);
          lctx.fillStyle = g; lctx.fillRect(0, 0, w, h);
        }
        ctx.globalCompositeOperation = "screen";                       // two pictures on black meet like light
        ctx.drawImage(layer, Math.round(x), 0);
      }
      overlay(act);
      const q = local(byId.missions, T) < 0;
      if (q !== quiet) { plate.classList.toggle("rf-quiet", q); quiet = q; }
    }
    function tick(now) {
      const play = onScreen && !document.hidden;
      if (!started) {                                               // the still stays until the missions clip can take over at its frame
        sync(false);
        const v = byId.missions.video;
        if (v && v.readyState >= 3) { started = true; rf.classList.add("is-running"); last = now; }
      } else if (play) {
        T = (T + ((now - last) / 1000) * FPS) % L;
        sync(true); draw(); paused = false;
      } else if (!paused) { sync(false); paused = true; }           // off screen or hidden: hold the frame, draw nothing
      last = now;
      requestAnimationFrame(tick);
    }
    if ("IntersectionObserver" in window) new IntersectionObserver((e) => { onScreen = e[0].isIntersecting; }, { rootMargin: "80px" }).observe(plate);
    requestAnimationFrame(tick);
  }
})();
