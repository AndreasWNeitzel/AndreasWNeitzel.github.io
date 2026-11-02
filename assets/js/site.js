// Site behaviour: theme, header state, the arrival build, sections that build once as they arrive,
// loops that play only on screen, the pointer light on the concept cards, portal drift, FIG 1 captions,
// record filters, one-time figure builds and the lazy start of the globe. No dependencies.
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
      document.querySelectorAll(".concept").forEach((c, k) => { c.style.transitionDelay = (0.5 + k * 0.08) + "s"; });
      document.body.classList.remove("intro");
      setTimeout(() => document.querySelectorAll(".concept").forEach((c) => { c.style.transitionDelay = ""; }), 1900);
    });
    if (still) document.body.classList.remove("intro");
    else Promise.all([document.fonts.ready, heroImg ? heroImg.decode().catch(() => {}) : null]).then(go);
  }

  // ---- blocks build once as they arrive; a card waits for its images --------------------
  const show = (el) => {
    const imgs = [...el.querySelectorAll("img")].filter((i) => !i.complete);
    Promise.all(imgs.map((i) => i.decode().catch(() => {}))).then(() => el.classList.add("is-in"));
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

  // ---- portals: the pictures drift slowly with the scroll; the spine runs only while on screen ----
  const portals = [...document.querySelectorAll(".portal")];
  if (portals.length && !still) {
    let queued = false;
    const drift = () => {
      if (queued) return; queued = true;
      requestAnimationFrame(() => {
        queued = false;
        portals.forEach((p) => {
          const r = p.getBoundingClientRect();
          if (r.bottom < -100 || r.top > innerHeight + 100) return;
          const k = (r.top + r.height / 2 - innerHeight / 2) / innerHeight;
          p.style.setProperty("--py", (-k * 36).toFixed(1) + "px");
        });
      });
    };
    addEventListener("scroll", drift, { passive: true }); drift();
    const section = document.querySelector(".portals");
    if (section) new IntersectionObserver((es) => es.forEach((e) => section.classList.toggle("is-live", e.isIntersecting))).observe(section);
  }

  // ---- FIG 1: stage captions ------------------------------------------------------
  const fig = document.getElementById("fig1");
  if (fig && fig.querySelector("[data-captions]")) {
    const caps = JSON.parse(fig.querySelector("[data-captions]").textContent);
    const titleEl = fig.querySelector("[data-cap-title]");
    const textEl = fig.querySelector("[data-cap-text]");
    const stages = fig.querySelectorAll(".f1-stage");
    const set = (key) => {
      stages.forEach((s) => s.classList.toggle("is-active", s.dataset.stage === key));
      fig.classList.toggle("has-active", !!(key && caps[key]));
      if (key && caps[key]) { titleEl.textContent = caps[key][0]; textEl.textContent = caps[key][1]; }
    };
    stages.forEach((s) => {
      s.addEventListener("pointerenter", () => set(s.dataset.stage));
      s.addEventListener("focus", () => set(s.dataset.stage));
      s.addEventListener("click", () => set(s.dataset.stage));
    });
    fig.addEventListener("pointerleave", () => set(null));
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

  // ---- the globe: its libraries and maps load when the section approaches ---------------
  const globe = document.querySelector("[data-globe]");
  if (globe) {
    const load = (src) => new Promise((res, rej) => { const s = document.createElement("script"); s.src = src; s.defer = true; s.onload = res; s.onerror = rej; document.head.appendChild(s); });
    const start = () => load(globe.dataset.vendor + "d3-array.min.js").then(() => load(globe.dataset.vendor + "d3-geo.min.js")).then(() => load(globe.dataset.vendor + "topojson-client.min.js")).then(() => load(globe.dataset.script)).catch(() => {});
    if ("IntersectionObserver" in window) {
      const io = new IntersectionObserver((entries) => { if (entries.some((e) => e.isIntersecting)) { io.disconnect(); start(); } }, { rootMargin: "700px 0px" });
      io.observe(globe);
    } else start();
  }
})();
