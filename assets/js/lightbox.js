// Lightbox. Static figures open as a copy in a modal dialog, where they zoom and pan. Live demos cannot
// be copied, so their own element is lifted into the top layer with the Popover API: it never leaves the
// DOM, which keeps its canvases, its stylesheet and its queries working. Styles load from here, and only
// on pages with something to enlarge. No dependencies.
(() => {
  const script = document.currentScript;

  // What gets a control. A host carries the control; the media inside it is chosen when it opens, since
  // some figures hold a wide and a narrow drawing and only one of them shows.
  const STATIC = [
    ".panel.blueprint:not(:has(.vlt-row))", ".vlt-row", ".paper-fig-svg", ".paper-fig-img", ".jn-frame", ".se-fig",
    ".sfb-figure", ".gallery figure", ".strip figure", ".tl-hero", "figure.panel.guide-wide", "figure:has(> video)",
  ].join(", ");
  const SKIP = ".plate, .hero, .card, .explainer, .row-item, .concept, .portal, .pg-wrap";
  // [the element that goes full screen, where its control sits]
  const LIVE = [[".sd-card", ".sd-stage--spec"], [".mw-card", ".mw-stage"], [".sfd-plot", ".sfd-stage"], ["#main > .panel", ".phead"]];
  const MEDIA = "svg:not(.i), img, video";
  const FOCUSABLE = "a[href], button:not(:disabled), input:not(:disabled), select, textarea, [tabindex]";
  const FIT = 0.94, MAX_ZOOM = 8, CLICK_ZOOM = 2.5, EASE = "cubic-bezier(.16, 1, .3, 1)";

  const motion = () => !matchMedia("(prefers-reduced-motion: reduce)").matches;
  const clamp = (v, a, b) => Math.min(Math.max(v, a), b);
  const isImageLink = (a) => /\.(webp|png|jpe?g|avif)$/i.test(a.pathname);
  // The scrollbar's width goes onto the body while it is gone, so nothing behind the overlay moves.
  const lock = (on) => {
    const html = document.documentElement;
    document.body.style.paddingInlineEnd = on ? innerWidth - html.clientWidth + "px" : "";
    html.classList.toggle("lb-lock", on);
  };
  const icon = (id) => `<svg class="i" aria-hidden="true"><use href="#${id}"></use></svg>`;

  // The line under an enlarged figure comes only from the data-credit marker on the figure or around it:
  // "own" for my work, any other value is the source's credit, and no marker means no line.
  const creditOf = (el) => {
    const v = el.closest("[data-credit]")?.dataset.credit;
    return v === "own" ? "© Andreas W. Neitzel" : v || "";
  };

  const label = (root) => {
    const m = root.matches("[aria-label]") ? root : root.querySelector("img[alt], svg[aria-label], canvas[aria-label], video[aria-label]");
    const text = (m && (m.alt || m.getAttribute("aria-label"))) || root.querySelector("svg title, figcaption")?.textContent || "";
    return text.trim().slice(0, 120) || "figure";
  };

  const control = (live) => {
    const b = document.createElement("button");
    b.type = "button"; b.className = live ? "lb-ctl lb-ctl--live" : "lb-ctl"; b.innerHTML = icon("i-expand");
    return b;
  };

  const closeButton = () => {
    const b = document.createElement("button");
    b.type = "button"; b.className = "lb-close"; b.setAttribute("aria-label", "Close"); b.innerHTML = icon("i-close");
    return b;
  };

  // Tab stays inside; a dialog alone would let it out to the browser's own controls.
  const trapTab = (box, e) => {
    if (e.key !== "Tab") return;
    const list = [...box.querySelectorAll(FOCUSABLE)].filter((n) => n.getClientRects().length && !n.closest("[inert]"));
    if (!list.length) return;
    const first = list[0], last = list[list.length - 1], on = document.activeElement;
    if (e.shiftKey ? on === first || !box.contains(on) : on === last) { e.preventDefault(); (e.shiftKey ? last : first).focus(); }
  };

  // ---- static figures -----------------------------------------------------------------------
  let dlg, view, frame, note, shut;

  function chooseMedia(host) {
    if (host.matches(".vlt-row")) return host; // two drawings that join at a seam: one picture
    return [...host.querySelectorAll(MEDIA)].find((el) => el.getClientRects().length && !el.closest("figcaption, .lb-ctl"));
  }

  // A drawing's inks are chosen for the surface it sits on, which is not always the page's (JANUS has its
  // own dark plate), so the copy takes that surface with it.
  const surface = (host) => {
    for (let n = host; n && n !== document.body; n = n.parentElement) {
      const c = getComputedStyle(n).backgroundColor;
      if (c !== "transparent" && c !== "rgba(0, 0, 0, 0)") return c;
    }
    return "var(--raised)";
  };

  // A copy of the media, its aspect ratio, and the sheet it sits on.
  function copyOf(el, host) {
    if (el.matches("img")) {
      const link = el.closest("a"), c = new Image();
      c.alt = el.alt; c.draggable = false; c.src = link && isImageLink(link) ? link.href : el.currentSrc || el.src;
      return { node: c, ratio: el.naturalWidth / el.naturalHeight || 1.6, sheet: host.matches(".paper-fig-img") ? "#fff" : "" };
    }
    if (el.matches("video")) {
      const c = el.cloneNode(true);
      c.muted = true;
      if (motion()) c.play().catch(() => {});
      return { node: c, ratio: el.videoWidth / el.videoHeight || 16 / 9, sheet: "" };
    }
    const c = el.cloneNode(true);
    c.removeAttribute("id");
    c.querySelector(":scope > .lb-ctl")?.remove();
    for (const n of [c, ...c.querySelectorAll("[data-build]")]) n.removeAttribute("data-build");
    c.style.cssText = el.matches("svg") ? "display:block;inline-size:100%;block-size:100%;min-inline-size:0;max-inline-size:none;max-block-size:none" : "inline-size:100%";
    const box = el.viewBox?.baseVal, r = el.getBoundingClientRect();
    return { node: c, ratio: box?.width ? box.width / box.height : r.width / r.height, sheet: surface(host), vector: true };
  }

  function createDialog() {
    dlg = document.createElement("dialog"); dlg.className = "lb";
    view = document.createElement("div"); view.className = "lb-view";
    frame = document.createElement("div");
    frame.inert = true; // pointer input goes to the view; links and stages in a copy stay out of the way
    view.append(frame);
    note = document.createElement("p"); note.className = "lb-credit"; note.hidden = true;
    const close = closeButton();
    dlg.append(view, note, close);
    document.body.append(dlg);

    let z = 1, x = 0, y = 0, ratio = 1, sheet = "", gesture = null, pinch = null;
    const pts = new Map();

    const apply = (smooth) => {
      const mx = Math.max(0, (frame.offsetWidth * z - view.clientWidth) / 2), my = Math.max(0, (frame.offsetHeight * z - view.clientHeight) / 2);
      x = clamp(x, -mx, mx); y = clamp(y, -my, my);
      frame.classList.toggle("is-smooth", !!smooth && motion());
      frame.style.transform = `translate(${x}px, ${y}px) scale(${z})`;
    };
    const zoomTo = (next, cx, cy, smooth) => {
      next = clamp(next, 1, MAX_ZOOM);
      const px = cx - view.clientWidth / 2, py = cy - view.clientHeight / 2;
      x = px - ((px - x) * next) / z; y = py - ((py - y) * next) / z; z = next;
      apply(smooth);
    };
    const fit = () => {
      const vw = view.clientWidth, vh = view.clientHeight, pad = sheet ? Math.round(Math.min(vw, vh) * 0.02) : 0;
      const w = Math.min(vw * FIT, (vh * FIT - 2 * pad) * ratio + 2 * pad);
      frame.style.padding = pad + "px"; frame.style.inlineSize = w + "px"; frame.style.blockSize = (w - 2 * pad) / ratio + 2 * pad + "px";
      z = 1; x = 0; y = 0; apply();
    };
    const overFrame = (e) => { const r = frame.getBoundingClientRect(); return e.clientX >= r.left && e.clientX <= r.right && e.clientY >= r.top && e.clientY <= r.bottom; };

    view.addEventListener("pointerdown", (e) => {
      view.setPointerCapture(e.pointerId);
      pts.set(e.pointerId, e);
      if (pts.size === 1) gesture = { sx: e.clientX, sy: e.clientY, ox: x, oy: y, moved: false, inside: overFrame(e) };
      else if (pts.size === 2) { const [a, b] = pts.values(); pinch = { d: Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY), z }; gesture.moved = true; }
    });
    view.addEventListener("pointermove", (e) => {
      view.style.cursor = gesture ? "grabbing" : overFrame(e) ? (z > 1 ? "grab" : "zoom-in") : "";
      if (!pts.has(e.pointerId)) return;
      pts.set(e.pointerId, e);
      if (pinch && pts.size === 2) {
        const [a, b] = pts.values();
        zoomTo((pinch.z * Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY)) / pinch.d, (a.clientX + b.clientX) / 2, (a.clientY + b.clientY) / 2);
      } else if (gesture) {
        const dx = e.clientX - gesture.sx, dy = e.clientY - gesture.sy;
        if (Math.hypot(dx, dy) > 6) gesture.moved = true;
        if (gesture.moved && z > 1) { x = gesture.ox + dx; y = gesture.oy + dy; apply(); }
      }
    });
    const release = (e) => {
      if (!pts.delete(e.pointerId)) return;
      pinch = null;
      if (pts.size) { const [p] = pts.values(); gesture = { sx: p.clientX, sy: p.clientY, ox: x, oy: y, moved: true, inside: true }; return; }
      const tap = e.type === "pointerup" && gesture && !gesture.moved;
      const inside = gesture?.inside;
      gesture = null;
      if (!tap) return;
      if (!inside) shut();
      else if (z > 1) { z = 1; x = 0; y = 0; apply(true); }
      else zoomTo(CLICK_ZOOM, e.clientX, e.clientY, true);
    };
    view.addEventListener("pointerup", release);
    view.addEventListener("pointercancel", release);
    view.addEventListener("wheel", (e) => {
      e.preventDefault();
      const k = e.deltaMode ? 0.05 : e.ctrlKey ? 0.01 : 0.002;
      zoomTo(z * Math.exp(-e.deltaY * k), e.clientX, e.clientY);
    }, { passive: false });

    dlg.addEventListener("keydown", (e) => {
      trapTab(dlg, e);
      const cx = view.clientWidth / 2, cy = view.clientHeight / 2, step = 80;
      const keys = {
        "+": () => zoomTo(z * 1.4, cx, cy, true), "=": () => zoomTo(z * 1.4, cx, cy, true), "-": () => zoomTo(z / 1.4, cx, cy, true), 0: () => zoomTo(1, cx, cy, true),
        ArrowLeft: () => { x += step; apply(true); }, ArrowRight: () => { x -= step; apply(true); }, ArrowUp: () => { y += step; apply(true); }, ArrowDown: () => { y -= step; apply(true); },
      };
      if (keys[e.key]) { e.preventDefault(); keys[e.key](); }
    });

    let trigger = null, top = 0;
    shut = () => {
      if (!dlg.open) return;
      if (motion()) dlg.animate({ opacity: [1, 0] }, { duration: 140 }).finished.then(() => dlg.close());
      else dlg.close();
    };
    close.addEventListener("click", shut);
    dlg.addEventListener("cancel", (e) => { e.preventDefault(); shut(); });
    dlg.addEventListener("close", () => {
      removeEventListener("resize", fit);
      frame.replaceChildren();
      lock(false);
      scrollTo({ top, behavior: "instant" });
      trigger?.focus({ preventScroll: true });
    });

    return (host, ctl) => {
      const el = chooseMedia(host);
      if (!el) return;
      const item = copyOf(el, host), from = el.getBoundingClientRect();
      trigger = ctl; top = scrollY; ratio = item.ratio; sheet = item.sheet;
      // Figures style their drawings through the classes around them, so the frame wears those too.
      const around = item.vector ? [...(host.closest("figure") || host).classList, ...host.classList].filter((c) => !/^(k-|reveal|is-in)/.test(c)) : [];
      frame.className = ["lb-frame", ...around].join(" ");
      frame.style.background = sheet;
      frame.replaceChildren(item.node);
      if (el.matches("img")) item.node.addEventListener("load", () => { ratio = item.node.naturalWidth / item.node.naturalHeight; fit(); }, { once: true });
      dlg.setAttribute("aria-label", label(host));
      note.textContent = creditOf(el); note.hidden = !note.textContent;
      lock(true);
      dlg.showModal();
      view.style.insetBlockEnd = note.hidden ? "" : note.offsetHeight + "px"; // the figure fits above the line
      addEventListener("resize", fit);
      fit();
      if (motion()) {
        const to = frame.getBoundingClientRect(), s = from.width / to.width;
        const dx = from.left + from.width / 2 - (to.left + to.width / 2), dy = from.top + from.height / 2 - (to.top + to.height / 2);
        frame.animate({ transform: [`translate(${dx}px, ${dy}px) scale(${s})`, "translate(0, 0) scale(1)"] }, { duration: 340, easing: EASE });
      }
    };
  }

  let openStatic;
  function attachStatic(host) {
    if (host.closest(SKIP) || !host.querySelector(MEDIA)) return;
    const link = host.querySelector("img")?.closest("a");
    if (link && !isImageLink(link) && !host.querySelector("svg:not(.i)") && !host.matches(".tl-hero")) return;
    if (getComputedStyle(host).position === "static") host.style.position = "relative";
    const ctl = control(false);
    ctl.setAttribute("aria-label", "Enlarge " + label(host));
    host.classList.add("lb-host");
    host.append(ctl);
    const open = () => { openStatic ||= createDialog(); openStatic(host, ctl); };
    ctl.addEventListener("click", (e) => { e.stopPropagation(); open(); });
    host.addEventListener("click", (e) => {
      if (e.defaultPrevented || e.button || e.metaKey || e.ctrlKey || e.shiftKey) return;
      if (!e.target.closest(MEDIA) || e.target.closest("button, [tabindex]")) return;
      const a = e.target.closest("a");
      if (a && !isImageLink(a)) return;
      e.preventDefault();
      open();
    });
    // a wide figure scrolls sideways on a phone; the control stays in the corner of the visible part
    host.addEventListener("scroll", () => { ctl.style.translate = `${host.scrollLeft}px 0`; }, { passive: true });
  }

  // ---- live demos ---------------------------------------------------------------------------
  function attachLive(el, dockSel) {
    const dock = el.querySelector(dockSel);
    if (!dock) return;
    if (getComputedStyle(dock).position === "static") dock.style.position = "relative";
    const ctl = control(true);
    ctl.setAttribute("aria-label", "Enlarge " + label(el));
    dock.append(ctl);
    let leave = null;
    const open = () => {
      const rect = el.getBoundingClientRect(), top = scrollY;
      lock(true);
      const slot = el.cloneNode(false); // keeps the demo's place in its grid, so the page behind holds still
      slot.removeAttribute("id"); slot.setAttribute("aria-hidden", "true");
      slot.style.cssText = `visibility:hidden;block-size:${rect.height}px`;
      el.after(slot);

      const hadLabel = el.hasAttribute("aria-label"), close = closeButton();
      if (!hadLabel) el.setAttribute("aria-label", label(el));
      el.setAttribute("role", "dialog"); el.setAttribute("aria-modal", "true");
      el.classList.add("lb-live");
      el.append(close);
      if (el.showPopover) { el.popover = "manual"; el.showPopover(); }

      // everything outside the demo goes inert, the same effect as a modal dialog
      const quiet = [];
      for (let n = el; n !== document.body; n = n.parentElement) {
        for (const s of n.parentElement.children) if (s !== n && !s.inert) { s.inert = true; quiet.push(s); }
      }
      if (motion()) el.animate({ opacity: [0, 1] }, { duration: 220, easing: EASE });
      close.focus();

      const keys = (e) => { if (e.key === "Escape") { e.preventDefault(); leave(); } else trapTab(el, e); };
      const outside = (e) => {
        const r = el.getBoundingClientRect();
        if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) leave();
      };
      document.addEventListener("keydown", keys, true);
      document.addEventListener("pointerdown", outside, true); // the backdrop is not a target in every browser
      close.addEventListener("click", () => leave());
      leave = () => {
        document.removeEventListener("keydown", keys, true);
        document.removeEventListener("pointerdown", outside, true);
        if (el.showPopover) { el.hidePopover(); el.removeAttribute("popover"); }
        close.remove();
        el.classList.remove("lb-live");
        el.removeAttribute("role"); el.removeAttribute("aria-modal");
        if (!hadLabel) el.removeAttribute("aria-label");
        slot.remove();
        for (const s of quiet) s.inert = false;
        lock(false);
        scrollTo({ top, behavior: "instant" });
        ctl.focus({ preventScroll: true });
      };
    };
    ctl.addEventListener("click", (e) => { e.stopPropagation(); open(); });
  }

  // ---- start: controls wait for their styles, so that none ever sits unstyled in the page -----------
  const statics = [...document.querySelectorAll(STATIC)];
  const lives = LIVE.flatMap(([sel, dock]) => [...document.querySelectorAll(sel)].map((el) => [el, dock]));
  if (!statics.length && !lives.length) return;
  const css = document.createElement("link");
  css.rel = "stylesheet"; css.href = script.src.replace(/js\/lightbox\.js.*$/, "css/lightbox.css");
  css.onload = () => { statics.forEach(attachStatic); lives.forEach(([el, dock]) => attachLive(el, dock)); };
  document.head.append(css);
})();
