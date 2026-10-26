// Site behaviour: theme toggle, header state, card spotlight, FIG 1 stage captions,
// timeline filters, lazy start of the travel map and one-time figure builds. No dependencies.
(() => {
  const root = document.documentElement;
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");

  // ---- theme toggle -------------------------------------------------------
  const themeBtn = document.querySelector(".theme");
  if (themeBtn) {
    const dark = matchMedia("(prefers-color-scheme: dark)");
    const current = () => root.dataset.theme || (dark.matches ? "dark" : "light");
    const label = () => themeBtn.setAttribute("aria-label", current() === "dark" ? "Switch to light theme" : "Switch to dark theme");
    themeBtn.addEventListener("click", () => {
      const next = current() === "dark" ? "light" : "dark";
      const apply = () => { root.dataset.theme = next; label(); };
      try { localStorage.setItem("theme", next); } catch (e) { /* storage unavailable */ }
      if (document.startViewTransition && !reduced.matches) document.startViewTransition(apply); else apply();
    });
    dark.addEventListener("change", label);
    label();
    themeBtn.hidden = false;
  }

  // ---- header hairline once the page scrolls --------------------------------
  const header = document.querySelector(".site-header");
  if (header) {
    const onScroll = () => header.toggleAttribute("data-scrolled", scrollY > 4);
    addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  // ---- spotlight that follows the pointer on interactive cards ---------------
  document.addEventListener("pointermove", (ev) => {
    const card = ev.target.closest && ev.target.closest("[data-spotlight]");
    if (!card) return;
    const r = card.getBoundingClientRect();
    card.style.setProperty("--mx", `${ev.clientX - r.left}px`);
    card.style.setProperty("--my", `${ev.clientY - r.top}px`);
  }, { passive: true });

  // ---- reveal on scroll ----------------------------------------------------------
  const revealed = document.querySelectorAll(".reveal");
  if (revealed.length && "IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("is-in"); io.unobserve(e.target); } });
    }, { rootMargin: "0px 0px -12% 0px", threshold: 0.08 });
    revealed.forEach((el) => io.observe(el));
  } else {
    revealed.forEach((el) => el.classList.add("is-in"));
  }

  // ---- FIG 1: stage captions -------------------------------------------------
  const fig = document.getElementById("fig1");
  if (fig) {
    const caps = {
      gaia: ["Gaia.", "ESA's satellite measures the position, motion and a low-resolution spectrum of each star. Data Release 3 has XP spectra for about 220 million stars; Data Release 4 will have them for about 1.8 billion."],
      xp: ["XP spectrum.", "Each star's spectrum from 360 to 990 nm, from Gaia's blue and red photometers. The shape carries temperature, gravity and chemistry, blurred at low resolution. The curve drawn is the measured spectrum of one red giant, Gaia DR3 5289554869898620416."],
      seismo: ["Asteroseismology.", "Oscillating red giants observed by TESS and Kepler have seismic masses and ages. They anchor and test the network on stars whose physics is known."],
      janus: ["JANUS.", "An ensemble of eight neural networks, each a conditional normalising flow, that turns an XP spectrum into a distribution over six stellar labels. Shown at TASC10/KASC17 and IMAS13; the paper is in preparation."],
      labels: ["Labels with reliability.", "Teff, log g, [M/H], [α/M], [Fe/H] and [Mg/H], each with a per-star median and spread, plus a calibrated probability that the prediction misses and a novelty score for stars unlike the training set."],
      starfold: ["Starfold.", "My open-source package for finding groups without labels: UMAP and HDBSCAN with an unsupervised search, refit 32 times to measure how often each group recurs."],
      galaxy: ["The Milky Way.", "Grouped by chemistry, age and motion, stars separate into the thin disc, thick disc, halo and accreted debris, the populations that record how the Galaxy was assembled. My 2025 paper tested this on a simulated galaxy."],
      apogee: ["APOGEE DR19.", "The high-resolution infrared survey whose stellar parameters and abundances are the training labels. JANUS learns the mapping from the XP spectrum to these values on the stars both surveys observed, and applies it to the rest."],
      inputs: ["The inputs.", "Each star enters as numbers: 110 coefficients of its XP spectrum, with its parallax, photometry and extinction. No spectrum is fitted line by line; the network reads the whole shape."],
      alpha: ["Two α sequences.", "The disc's α-rich and α-poor sequences in the [α/M] against [M/H] plane. JANUS separates them; the same network trained without the spectrum merges them, which shows that the spectrum carries the chemistry."],
      sample: ["The TESS giants.", "Red giants whose oscillations TESS measured, with seismic masses and ages. They are the stars the catalogue covers; the ages come from the ArqueoGal pipeline, not from JANUS."],
      test: ["Withheld stars.", "Stars kept out of training. The robust scatter of JANUS about APOGEE DR19 on them: 32 K in Teff, 0.072 dex in log g, 0.051 dex in [M/H] and 0.021 dex in [α/M], with calibrated uncertainties."],
      catalogue: ["The catalogue.", "144,304 TESS red giants with JANUS chemistry, about nine times as many as have APOGEE DR19 values passing the same cuts. The chemistry layer of ArqueoGal, to be released through the project."],
      hpc: ["Compute.", "Responsible investigator on two approved FCT allocations: 1,002,400 core-hours and 1,000 H100 GPU-hours on MareNostrum 5, and 299,520 core-hours and 1,500 A100 GPU-hours on Deucalion."],
    };
    const titleEl = fig.querySelector("[data-cap-title]");
    const textEl = fig.querySelector("[data-cap-text]");
    const defTitle = titleEl.innerHTML, defText = textEl.innerHTML;
    const stages = fig.querySelectorAll(".f1-stage");
    const set = (key) => {
      stages.forEach((s) => s.classList.toggle("is-active", s.dataset.stage === key));
      fig.classList.toggle("has-active", !!key);
      if (key && caps[key]) { titleEl.textContent = caps[key][0]; textEl.textContent = caps[key][1]; }
      else { titleEl.innerHTML = defTitle; textEl.innerHTML = defText; }
    };
    stages.forEach((s) => {
      s.addEventListener("pointerenter", () => set(s.dataset.stage));
      s.addEventListener("focus", () => set(s.dataset.stage));
      s.addEventListener("click", () => set(s.dataset.stage));
    });
    fig.addEventListener("pointerleave", () => set(null));
  }

  // ---- timeline filters --------------------------------------------------------
  const tl = document.querySelector("[data-timeline]");
  if (tl) {
    const rows = tl.querySelectorAll(".tl-row");
    const buttons = document.querySelectorAll("[data-filter]");
    buttons.forEach((b) => b.addEventListener("click", () => {
      const f = b.dataset.filter;
      buttons.forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
      rows.forEach((r) => { r.hidden = f !== "all" && !r.dataset.kind.split(" ").includes(f); });
    }));
  }

  // ---- travel map: load the basemap when the section approaches -----------------
  const map = document.querySelector("[data-travel-map]");
  if (map) {
    const start = () => {
      const s = document.createElement("script");
      s.src = map.dataset.script; s.defer = true;
      document.head.appendChild(s);
    };
    if ("IntersectionObserver" in window) {
      const io = new IntersectionObserver((entries) => {
        if (entries.some((e) => e.isIntersecting)) { io.disconnect(); start(); }
      }, { rootMargin: "600px 0px" });
      io.observe(map);
    } else start();
  }

  // ---- figure builds: draw each schematic once, when it first enters the view ------
  const builds = document.querySelectorAll("[data-build]");
  if (builds.length && !reduced.matches && "IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (!e.isIntersecting) return;
        e.target.dataset.build = "run";
        io.unobserve(e.target);
      });
    }, { threshold: 0.3 });
    builds.forEach((el) => { el.dataset.build = "armed"; io.observe(el); });
  }
})();
