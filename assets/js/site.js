// Site behaviour: theme, header state, the arrival build, sections that build once as they arrive,
// loops that play only on screen, the pointer light on the concept cards, FIG 1 captions,
// record filters, one-time figure builds and the idle start of the globe. No dependencies.
(() => {
  const root = document.documentElement;
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  const still = reduced.matches || new URLSearchParams(location.search).has("static");

  // ---- theme ------------------------------------------------------------------
  const themeBtn = document.querySelector(".theme");
  if (themeBtn) {
    const dark = matchMedia("(prefers-color-scheme: dark)");
    const current = () => root.dataset.theme || (dark.matches ? "dark" : "light");
    const label = () => themeBtn.setAttribute("aria-label", current() === "dark" ? "Switch to light theme" : "Switch to dark theme");
    themeBtn.addEventListener("click", () => {
      const next = current() === "dark" ? "light" : "dark";
      root.dataset.theme = next; label();
      try { localStorage.setItem("theme", next); } catch (e) { /* storage unavailable */ }
      document.dispatchEvent(new CustomEvent("themechange"));
    });
    dark.addEventListener("change", label);
    label();
    themeBtn.hidden = false;
  }

  // ---- header: solid once the page scrolls; on the home page it floats over the photograph first ----
  const header = document.querySelector(".site-header");
  const home = document.body.classList.contains("home");
  if (header) {
    const onScroll = () => header.toggleAttribute("data-scrolled", scrollY > (home ? 160 : 4));
    addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  // ---- arrival: one short build, then the page is still -----------------------------
  if (document.body.classList.contains("intro")) {
    const heroImg = document.querySelector(".hero img");
    const go = () => requestAnimationFrame(() => {
      document.body.classList.remove("intro");
    });
    if (still) document.body.classList.remove("intro");
    else Promise.all([document.fonts.ready, heroImg ? heroImg.decode().catch(() => {}) : null]).then(go);
  }

  // ---- blocks build once as they arrive; a card waits for its images --------------------
  const show = (el) => {
    const imgs = [...el.querySelectorAll("img")].filter((i) => !i.complete && i.offsetParent);
    const wait = new Promise((r) => setTimeout(r, 1200));
    Promise.race([wait, Promise.all(imgs.map((i) => i.decode().catch(() => {})))]).then(() => el.classList.add("is-in"));
  };
  const targets = document.querySelectorAll(".k-up, .k-left, .k-scale, .k-card, .reveal, .year");
  document.querySelectorAll(".mi .k-left").forEach((el, k) => { el.style.transitionDelay = (k % 3) * 0.08 + Math.floor(k / 3) * 0.12 + "s"; });
  document.querySelectorAll(".year").forEach((y) => y.querySelectorAll(".k-row").forEach((r, k) => { r.style.transitionDelay = Math.min(k, 10) * 0.05 + "s"; }));
  document.querySelectorAll(".strip figure").forEach((el, k) => { el.style.transitionDelay = k * 0.08 + "s"; });
  if (still || !("IntersectionObserver" in window)) targets.forEach((el) => el.classList.add("is-in"));
  else {
    const io = new IntersectionObserver((entries) => entries.forEach((e) => { if (e.isIntersecting) { show(e.target); io.unobserve(e.target); } }), { threshold: 0.12, rootMargin: "0px 0px -6% 0px" });
    targets.forEach((el) => io.observe(el));
  }

  // ---- loops play only while on screen and while the tab is visible -----------------
  const vids = [...document.querySelectorAll("video[autoplay]")];
  document.querySelectorAll("video[data-start]").forEach((v) => { const seek = () => { v.currentTime = +v.dataset.start; }; v.readyState ? seek() : v.addEventListener("loadedmetadata", seek, { once: true }); });
  if (vids.length) {
    if (reduced.matches) vids.forEach((v) => { v.removeAttribute("autoplay"); v.pause(); });
    else {
      const vio = new IntersectionObserver((entries) => entries.forEach((e) => {
        e.target._on = e.isIntersecting;
        if (e.isIntersecting && !document.hidden) e.target.play().catch(() => {}); else e.target.pause();
      }), { rootMargin: "120px" });
      vids.forEach((v) => vio.observe(v));
      document.addEventListener("visibilitychange", () => vids.forEach((v) => (document.hidden || !v._on) ? v.pause() : v.play().catch(() => {})));
    }
  }

  // ---- pointer light on the concept plates --------------------------------------
  document.querySelectorAll(".concept .plate").forEach((p) => p.addEventListener("pointermove", (e) => {
    const r = p.getBoundingClientRect();
    p.style.setProperty("--mx", (e.clientX - r.left) + "px"); p.style.setProperty("--my", (e.clientY - r.top) + "px");
  }, { passive: true }));

  // ---- home portals: their loops play only while the card is hovered ------------------
  if (!reduced.matches) document.querySelectorAll(".portal").forEach((card) => {
    const vs = [...card.querySelectorAll("video[data-hover]")];
    if (!vs.length) return;
    card.addEventListener("pointerenter", () => vs.forEach((v) => { v.classList.add("on"); v.play().catch(() => {}); }));
    card.addEventListener("pointerleave", () => vs.forEach((v) => { v.classList.remove("on"); v.pause(); }));
  });

  // ---- every card that links somewhere says so on hover, as the home portals do ------
  document.querySelectorAll(".concept .plate, .explainer .pic, .row-item .pic, .mi a").forEach((pic) => {
    const more = document.createElement("span");
    more.className = "card-more"; more.setAttribute("aria-hidden", "true");
    more.innerHTML = '<span>Learn more</span><span class="go"><svg class="i"><use href="#i-arrow"/></svg></span>';
    pic.appendChild(more);
  });


  // ---- staged figures: hover, focus or tap a stage; its line shows in the readout ---------
  document.querySelectorAll("[data-stagefig]").forEach((fg) => {
    const lines = JSON.parse(fg.querySelector("[data-captions]").textContent);
    const titleEl = fg.querySelector("[data-read-title]");
    const lineEl = fg.querySelector("[data-read-line]");
    const rest = lineEl.innerHTML = lineEl.innerHTML.replace("Hover", matchMedia("(hover: none)").matches ? "Tap" : "Hover");
    const stages = fg.querySelectorAll(".jn-stage");
    let held = null;
    const set = (key) => {
      const c = key && lines[key];
      stages.forEach((s) => s.classList.toggle("is-active", !!c && s.dataset.stage === key));
      fg.classList.toggle("has-active", !!c);
      titleEl.innerHTML = c ? c.title : "";
      lineEl.innerHTML = c ? c.line : rest;
    };
    stages.forEach((s) => {
      s.addEventListener("pointerenter", (e) => { if (e.pointerType === "mouse") set(s.dataset.stage); });
      s.addEventListener("pointerleave", (e) => { if (e.pointerType === "mouse") set(held); });
      s.addEventListener("focus", () => { if (s.matches(":focus-visible")) { held = s.dataset.stage; set(held); } });
      s.addEventListener("blur", () => { held = null; set(null); });
      s.addEventListener("click", (e) => { e.stopPropagation(); held = held === s.dataset.stage ? null : s.dataset.stage; set(held); });
      s.addEventListener("keydown", (e) => { if (e.key === "Escape") s.blur(); });
    });
    fg.addEventListener("click", () => { held = null; set(null); });
  });

  // ---- the album: on touch screens a tap shows a tile's panel; a second tap, a tap elsewhere or Escape hides it ----
  const album = document.querySelector("[data-album]");
  if (album) {
    const tiles = album.querySelectorAll(".vis-tile");
    const close = () => tiles.forEach((t) => t.classList.remove("is-open"));
    tiles.forEach((t) => t.addEventListener("click", (e) => {
      if (e.target.closest("a") || matchMedia("(hover: hover)").matches) return;
      const open = !t.classList.contains("is-open");
      close(); t.classList.toggle("is-open", open); e.stopPropagation();
    }));
    document.addEventListener("click", close);
    album.addEventListener("keydown", (e) => { if (e.key === "Escape") { close(); if (album.contains(document.activeElement)) document.activeElement.blur(); } });
  }

  // ---- the record: one kind at a time; empty years fold away --------------------------
  const buttons = document.querySelectorAll(".filters [data-filter]");
  if (buttons.length) buttons.forEach((b) => b.addEventListener("click", () => {
    const f = b.dataset.filter;
    buttons.forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    document.querySelectorAll(".tl-row").forEach((r) => { r.hidden = f !== "all" && !r.dataset.kind.split(" ").includes(f); });
    document.querySelectorAll(".year").forEach((y) => {
      const n = y.querySelectorAll(".tl-row:not([hidden])").length; y.hidden = n === 0;
      const small = y.querySelector("h3 small"); if (small) small.textContent = n + (n === 1 ? " entry" : " entries");
    });
  }));

  // ---- figure builds: draw each schematic once, when it first enters the view ----------
  const builds = document.querySelectorAll("[data-build]");
  if (builds.length && !reduced.matches && "IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => entries.forEach((e) => { if (!e.isIntersecting) return; e.target.dataset.build = "run"; io.unobserve(e.target); }), { threshold: 0.3 });
    builds.forEach((el) => { el.dataset.build = "armed"; io.observe(el); });
  }

  // ---- the globe: its libraries and maps load once the page is idle ---------------
  const globe = document.querySelector("[data-globe]");
  if (globe) {
    const load = (src) => new Promise((res, rej) => { const s = document.createElement("script"); s.src = src; s.defer = true; s.onload = res; s.onerror = rej; document.head.appendChild(s); });
    const start = () => load(globe.dataset.vendor + "d3-array.min.js").then(() => load(globe.dataset.vendor + "d3-geo.min.js")).then(() => load(globe.dataset.vendor + "topojson-client.min.js")).then(() => load(globe.dataset.script)).catch(() => {});
    // loaded while the page is idle, never during a scroll: parsing the maps would stall it
    const idle = window.requestIdleCallback || ((f) => setTimeout(f, 300));
    if (document.readyState === "complete") idle(start); else addEventListener("load", () => idle(start), { once: true });
  }
})();
