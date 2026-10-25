// Home timeline: draw each line of work as dashed arcs in the left gutter, from the degree it grew
// out of through its entries in date order. Hovering an entry or a legend key lights its threads.
(() => {
  const root = document.querySelector("[data-threads-root]");
  if (!root) return;
  const svg = root.querySelector("[data-threads-svg]");
  const list = root.querySelector("[data-timeline]");
  const threads = JSON.parse(root.querySelector("[data-threads-json]").textContent);
  const keys = document.querySelectorAll("[data-thread]");
  const NS = "http://www.w3.org/2000/svg";
  const rows = new Map([...list.querySelectorAll(".tl-row")].map((r) => [r.dataset.id, r]));

  const member = new Map();
  threads.forEach((t) => [t.parent, ...t.ids].forEach((id) => {
    if (!member.has(id)) member.set(id, new Set());
    member.get(id).add(t.key);
  }));
  rows.forEach((row, id) => { if (member.has(id)) row.dataset.threads = [...member.get(id)].join(" "); });

  const el = (name, attrs) => {
    const n = document.createElementNS(NS, name);
    Object.entries(attrs).forEach(([k, v]) => n.setAttribute(k, v));
    return n;
  };

  const draw = () => {
    const w = svg.clientWidth;
    if (!w) { svg.replaceChildren(); return; } // gutter hidden on narrow screens
    const h = root.clientHeight;
    const top = root.getBoundingClientRect().top;
    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    svg.setAttribute("height", h);
    const ax = w - 3;
    const yOf = (row) => {
      const b = row.getBoundingClientRect();
      return Math.round(b.top - top + Math.min(22, b.height / 2));
    };
    const frag = document.createDocumentFragment();
    threads.forEach((t, lane) => {
      const ys = [t.parent, ...t.ids].map((id) => rows.get(id)).filter((r) => r && !r.hidden).map(yOf);
      if (ys.length < 2) return;
      const g = el("g", { class: "th", "data-thread": t.key, style: `--th: var(${t.colour})` });
      let d = "";
      for (let i = 1; i < ys.length; i += 1) {
        const y1 = ys[i - 1];
        const y2 = ys[i];
        const b = Math.min(10 + lane * 10 + Math.abs(y2 - y1) * 0.02, w - 6);
        d += `M${ax} ${y1}C${ax - b} ${y1} ${ax - b} ${y2} ${ax} ${y2}`;
      }
      g.append(el("path", { d }));
      ys.forEach((y, i) => {
        const k = i === 0 ? 7 : 5;
        g.append(el("rect", { x: ax - k / 2, y: y - k / 2, width: k, height: k }));
      });
      frag.append(g);
    });
    svg.replaceChildren(frag);
  };

  const light = (on) => {
    root.classList.toggle("is-tracing", on.size > 0);
    svg.querySelectorAll(".th").forEach((g) => g.classList.toggle("on", on.has(g.dataset.thread)));
    rows.forEach((row) => {
      const mine = row.dataset.threads ? row.dataset.threads.split(" ") : [];
      row.classList.toggle("on", mine.some((k) => on.has(k)));
    });
    keys.forEach((k) => k.classList.toggle("on", on.has(k.dataset.thread)));
  };
  list.addEventListener("pointerover", (e) => {
    const row = e.target.closest(".tl-row");
    light(new Set(row && row.dataset.threads ? row.dataset.threads.split(" ") : []));
  });
  list.addEventListener("pointerleave", () => light(new Set()));
  keys.forEach((k) => {
    const on = () => light(new Set([k.dataset.thread]));
    const off = () => light(new Set());
    k.addEventListener("pointerenter", on);
    k.addEventListener("focus", on);
    k.addEventListener("pointerleave", off);
    k.addEventListener("blur", off);
  });

  let queued = false;
  const redraw = () => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => { queued = false; draw(); });
  };
  if ("ResizeObserver" in window) new ResizeObserver(redraw).observe(list);
  window.addEventListener("load", redraw);
  if (document.fonts) document.fonts.ready.then(redraw);
  draw();
})();
