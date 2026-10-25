(() => {
  const root = document.getElementById("sf-demo");
  if (!root) return;
  const canvas = root.querySelector("canvas.sf-map");
  const ctx = canvas.getContext("2d");
  const loadBtn = root.querySelector(".sf-load");
  const status = root.querySelector(".sf-status");
  const controls = root.querySelector(".sf-controls");
  const modeInputs = root.querySelectorAll('input[name="sf-mode"]');
  const slider = root.querySelector(".sf-refit");
  const refitLabel = root.querySelector(".sf-refit-label");
  const play = root.querySelector(".sf-play");
  const tip = root.querySelector(".sf-tip");
  const tipCanvas = tip.querySelector("canvas");
  const tipText = tip.querySelector("p");
  const groupsBody = root.querySelector(".sf-groups tbody");
  const T = window.siteTokens;
  let palette = T.categorical();
  let grey = T.colour("--context");
  const fragments = Array.from({ length: 51 }, (_, i) => `hsl(${(i * 137.508) % 360} 55% 48%)`);
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let D = null, pts = null, bounds = null, mode = "starfold", refit = 0, timer = null, hover = -1, maps = [], cells = null, cellSize = 0;

  const css = (name) => T.colour(name);
  T.onThemeChange(() => { palette = T.categorical(); grey = T.colour("--context"); if (D) { fillGroups(); draw(); } });

  async function load() {
    loadBtn.disabled = true;
    status.textContent = "Loading the recorded run.";
    try {
      const res = await fetch(root.dataset.src);
      D = await res.json();
    } catch (e) {
      status.textContent = "The recorded run could not be loaded.";
      loadBtn.disabled = false;
      return;
    }
    prepare();
    loadBtn.hidden = true;
    controls.hidden = false;
    status.hidden = true;
    fillGroups();
    resize();
  }

  function prepare() {
    const xs = D.layout.map((p) => p[0]), ys = D.layout.map((p) => p[1]);
    bounds = { x0: Math.min(...xs), x1: Math.max(...xs), y0: Math.min(...ys), y1: Math.max(...ys) };
    maps = D.world_labels.map((labels) => {
      const counts = new Map();
      labels.forEach((v, i) => {
        const ref = D.starfold_labels[i];
        if (v < 0 || ref < 0) return;
        const row = counts.get(v) || new Array(D.n_groups_starfold).fill(0);
        row[ref] += 1;
        counts.set(v, row);
      });
      const map = new Map();
      counts.forEach((row, v) => map.set(v, row.indexOf(Math.max(...row))));
      return map;
    });
    slider.max = D.world_labels.length - 1;
  }

  function resize() {
    if (!D) return;
    const dpr = window.devicePixelRatio || 1;
    const w = root.querySelector(".sf-figure").clientWidth;
    const h = Math.round(w * 0.6);
    canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
    canvas.style.height = h + "px";
    const pad = 18;
    const sx = (w - 2 * pad) / (bounds.x1 - bounds.x0), sy = (h - 2 * pad) / (bounds.y1 - bounds.y0);
    pts = D.layout.map((p) => [pad + (p[0] - bounds.x0) * sx, h - pad - (p[1] - bounds.y0) * sy]);
    cellSize = 24;
    cells = new Map();
    pts.forEach((p, i) => {
      const k = `${Math.floor(p[0] / cellSize)},${Math.floor(p[1] / cellSize)}`;
      (cells.get(k) || cells.set(k, []).get(k)).push(i);
    });
    draw();
  }

  function colour(i) {
    if (mode === "truth") return [palette[D.truth[i]], 0.9];
    if (mode === "defaults") { const v = D.default_labels[i]; return v < 0 ? [grey, 0.9] : [fragments[v % 51], 0.9]; }
    if (mode === "refit") {
      const v = D.world_labels[refit][i];
      if (v === -2) return null;
      if (v === -1) return [grey, 0.9];
      const ref = maps[refit].get(v);
      return ref === undefined ? [grey, 0.9] : [palette[ref], 1];
    }
    const v = D.starfold_labels[i];
    if (v < 0) return [grey, 0.9];
    return [palette[v], 0.25 + 0.75 * Math.max(D.own_support[i], 0)];
  }

  function draw() {
    if (!pts) return;
    const dpr = window.devicePixelRatio || 1;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = css("--surface");
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    const r = 2.6;
    for (let i = 0; i < pts.length; i++) {
      const c = colour(i);
      if (!c) continue;
      ctx.globalAlpha = c[1];
      ctx.beginPath(); ctx.arc(pts[i][0], pts[i][1], r, 0, Math.PI * 2);
      if (c[0] === grey) { ctx.strokeStyle = grey; ctx.lineWidth = 1; ctx.stroke(); }
      else { ctx.fillStyle = c[0]; ctx.fill(); }
    }
    ctx.globalAlpha = 1;
    if (hover >= 0) {
      ctx.strokeStyle = css("--ink"); ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.arc(pts[hover][0], pts[hover][1], r + 3, 0, Math.PI * 2); ctx.stroke();
    }
  }

  function nearest(x, y) {
    const cx = Math.floor(x / cellSize), cy = Math.floor(y / cellSize);
    let best = -1, bd = 12 * 12;
    for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) {
      const list = cells.get(`${cx + dx},${cy + dy}`);
      if (!list) continue;
      for (const i of list) {
        const d = (pts[i][0] - x) ** 2 + (pts[i][1] - y) ** 2;
        if (d < bd) { bd = d; best = i; }
      }
    }
    return best;
  }

  function showTip(i, x, y) {
    const tctx = tipCanvas.getContext("2d");
    const s = tipCanvas.width / 8;
    for (let k = 0; k < 64; k++) {
      const v = 255 - Math.round(D.pixels[i][k] * 255 / 16);
      tctx.fillStyle = `rgb(${v} ${v} ${v})`;
      tctx.fillRect((k % 8) * s, Math.floor(k / 8) * s, s, s);
    }
    const g = D.starfold_labels[i];
    const support = D.own_support[i];
    const groupText = g < 0 ? "left unassigned by Starfold" : `Starfold group ${g}, kept in ${Math.round(support * 100)} percent of the refits that sampled it`;
    tipText.textContent = `Written digit ${D.truth[i]}; ${groupText}.`;
    tip.hidden = false;
    const fig = root.querySelector(".sf-figure").getBoundingClientRect();
    tip.style.left = Math.min(x + 14, fig.width - tip.offsetWidth - 4) + "px";
    tip.style.top = Math.max(y - tip.offsetHeight - 10, 4) + "px";
  }

  function fillGroups() {
    const counts = new Array(D.n_groups_starfold).fill(0);
    D.starfold_labels.forEach((v) => { if (v >= 0) counts[v] += 1; });
    groupsBody.innerHTML = "";
    counts.forEach((n, g) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `<th scope="row"><span class="sf-swatch" style="background:${palette[g]}"></span>Group ${g}</th><td>${n}</td><td>${Math.round(D.group_recurrence[g] * 100)} percent</td>`;
      groupsBody.appendChild(tr);
    });
    const unassigned = D.starfold_labels.filter((v) => v < 0).length;
    const tr = document.createElement("tr");
    tr.innerHTML = `<th scope="row"><span class="sf-swatch" style="background:${grey}"></span>Unassigned</th><td>${unassigned}</td><td></td>`;
    groupsBody.appendChild(tr);
  }

  function setRefit(v) {
    refit = v; mode = "refit";
    modeInputs.forEach((m) => { m.checked = false; });
    refitLabel.textContent = `Refit ${v + 1} of ${D.world_labels.length}`;
    draw();
  }

  loadBtn.addEventListener("click", load);
  modeInputs.forEach((m) => m.addEventListener("change", () => { if (m.checked) { mode = m.value; stop(); draw(); } }));
  slider.addEventListener("input", () => setRefit(Number(slider.value)));
  function stop() { if (timer) { clearInterval(timer); timer = null; play.textContent = "Replay the refits"; } }
  play.addEventListener("click", () => {
    if (timer) { stop(); return; }
    play.textContent = "Pause";
    timer = setInterval(() => { const next = (refit + 1) % D.world_labels.length; slider.value = next; setRefit(next); }, 420);
  });
  if (reduced) play.hidden = true;
  canvas.addEventListener("mousemove", (e) => {
    if (!pts) return;
    const rect = canvas.getBoundingClientRect();
    const i = nearest(e.clientX - rect.left, e.clientY - rect.top);
    if (i !== hover) { hover = i; draw(); }
    if (i >= 0) showTip(i, e.clientX - rect.left, e.clientY - rect.top); else tip.hidden = true;
  });
  canvas.addEventListener("mouseleave", () => { hover = -1; tip.hidden = true; draw(); });
  window.addEventListener("resize", resize);
  if (new URLSearchParams(location.search).has("autoload")) load();
})();
