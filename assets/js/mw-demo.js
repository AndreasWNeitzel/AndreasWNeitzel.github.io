// Milky Way map for the field guide (_includes/mw-demo.html): 160,000 Gaia DR3 red giants
// within 5 kpc of the Sun (assets/data/mw/giants.bin, built by figures/map/build_mw_points.py)
// drawn in raw WebGL as additive soft points, sized by distance and coloured by metallicity or
// distance. The camera orbits the Sun; a tour pulls out from the Sun and circles the disc.
(() => {
  "use strict";
  const root = document.querySelector("[data-mw]");
  if (!root) return;
  const $ = (s) => root.querySelector(s);
  const cv = $("canvas"), stage = $(".mw-stage"), load = $(".mw-load"), playBtn = $(".mw-play");
  const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);
  const lerp = (a, b, k) => a + (b - a) * k;
  const smooth = (k) => ((k = clamp(k, 0, 1)), k * k * (3 - 2 * k));
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  const N = +root.dataset.n || 160000;

  const OPTS = { alpha: false, antialias: false, depth: false, stencil: false, premultipliedAlpha: false, powerPreference: "high-performance" };
  const gl = cv.getContext("webgl2", OPTS) || cv.getContext("webgl", OPTS);
  if (!gl) {
    root.classList.add("mw--nogl");
    load.textContent = "This map needs WebGL, which this browser does not provide.";
    return;
  }

  // ------------------------------------------------------------------ shaders
  // Sprite diameter 30 pc in perspective, between 2.5 and 9 pixels at device pixel ratio 1.
  // A near star grows and its peak dims as the inverse 1.5 power of its size, so it reads as a
  // brighter point rather than a blob, while the density of the field sets the tone.
  const VS = `
attribute vec3 a_pos; attribute float a_feh;
uniform mat4 u_vp; uniform float u_px, u_min, u_max, u_mode, u_alpha; uniform vec2 u_ramp;
varying vec3 v_col;
const vec3 COOL = vec3(0.42, 0.62, 1.0); const vec3 WARM = vec3(1.0, 0.68, 0.32);
void main() {
  vec4 clip = u_vp * vec4(a_pos, 1.0);
  gl_Position = clip;
  float s = clamp(u_px / max(clip.w, 0.01), u_min, u_max);
  gl_PointSize = s;
  float v = u_mode < 0.5 ? a_feh * 0.02 : length(a_pos);
  float t = clamp((v - u_ramp.x) / (u_ramp.y - u_ramp.x), 0.0, 1.0);
  v_col = mix(COOL, WARM, t) * (u_alpha * min(1.0, pow(2.5 / s, 1.5)));
}`;
  const FS = `
precision mediump float; varying vec3 v_col;
void main() {
  vec2 d = gl_PointCoord * 2.0 - 1.0; float r2 = dot(d, d);
  if (r2 > 1.0) discard;
  gl_FragColor = vec4(v_col * exp(-4.0 * r2), 1.0);
}`;
  const LVS = `attribute vec3 a_pos; uniform mat4 u_vp; void main() { gl_Position = u_vp * vec4(a_pos, 1.0); }`;
  const LFS = `precision mediump float; uniform vec4 u_col; void main() { gl_FragColor = u_col; }`;
  // The light is summed in a half-float buffer and compressed with a logarithm, so that the
  // dense inner disc and the sparse edges both keep their contrast: a single star shows as a
  // point, and a column of a hundred stars is brighter, not white. The hue is kept and only the
  // brightest columns drift a little towards white.
  const TVS = `attribute vec2 a_pos; varying vec2 v_uv; void main() { v_uv = a_pos * 0.5 + 0.5; gl_Position = vec4(a_pos, 0.0, 1.0); }`;
  const TFS = `
precision mediump float; uniform sampler2D u_tex; uniform float u_e, u_ref; uniform vec3 u_bg; varying vec2 v_uv;
void main() {
  vec3 a = texture2D(u_tex, v_uv).rgb;
  float L = max(a.r, max(a.g, a.b));
  float m = pow(log(1.0 + u_e * L) / log(1.0 + u_e * u_ref), 1.15);
  vec3 o = L > 0.0 ? a * (m / L) : vec3(0.0);
  o = mix(o, vec3(m), 0.3 * m * m);
  gl_FragColor = vec4(u_bg + o, 1.0);
}`;

  function program(vs, fs) {
    const p = gl.createProgram();
    for (const [type, src] of [[gl.VERTEX_SHADER, vs], [gl.FRAGMENT_SHADER, fs]]) {
      const sh = gl.createShader(type);
      gl.shaderSource(sh, src);
      gl.compileShader(sh);
      if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(sh));
      gl.attachShader(p, sh);
    }
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
    return p;
  }
  const P = program(VS, FS), L = program(LVS, LFS), TP = program(TVS, TFS);
  const U = {};
  for (const n of ["u_vp", "u_px", "u_min", "u_max", "u_mode", "u_alpha", "u_ramp"]) U[n] = gl.getUniformLocation(P, n);
  const LU = { vp: gl.getUniformLocation(L, "u_vp"), col: gl.getUniformLocation(L, "u_col") };
  const TU = { tex: gl.getUniformLocation(TP, "u_tex"), e: gl.getUniformLocation(TP, "u_e"), ref: gl.getUniformLocation(TP, "u_ref"), bg: gl.getUniformLocation(TP, "u_bg") };
  const aPos = gl.getAttribLocation(P, "a_pos"), aFeh = gl.getAttribLocation(P, "a_feh"), lPos = gl.getAttribLocation(L, "a_pos"), tPos = gl.getAttribLocation(TP, "a_pos");
  const MAXPT = Math.min(9, gl.getParameter(gl.ALIASED_POINT_SIZE_RANGE)[1]);
  gl.enable(gl.BLEND);

  // Half-float accumulation target: WebGL2 with EXT_color_buffer_float, or WebGL1 with the
  // half-float texture extensions; without either, the points are added straight to the
  // screen at a lower weight.
  const isGL2 = typeof WebGL2RenderingContext !== "undefined" && gl instanceof WebGL2RenderingContext;
  let hdr = null;
  (function setupHdr() {
    let type, internal;
    if (isGL2) {
      if (!gl.getExtension("EXT_color_buffer_float")) return;
      type = gl.HALF_FLOAT;
      internal = gl.RGBA16F;
    } else {
      const ext = gl.getExtension("OES_texture_half_float");
      if (!ext || !gl.getExtension("EXT_color_buffer_half_float")) return;
      type = ext.HALF_FLOAT_OES;
      internal = gl.RGBA;
    }
    const tex = gl.createTexture(), fb = gl.createFramebuffer();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texImage2D(gl.TEXTURE_2D, 0, internal, 4, 4, 0, gl.RGBA, type, null);
    gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
    const ok = gl.checkFramebufferStatus(gl.FRAMEBUFFER) === gl.FRAMEBUFFER_COMPLETE;
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    if (ok) hdr = { tex, fb, type, internal, w: 4, h: 4 };
  })();
  const quad = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, quad);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  function sizeHdr() {
    if (!hdr || (hdr.w === cv.width && hdr.h === cv.height)) return;
    gl.bindTexture(gl.TEXTURE_2D, hdr.tex);
    gl.texImage2D(gl.TEXTURE_2D, 0, hdr.internal, cv.width, cv.height, 0, gl.RGBA, hdr.type, null);
    hdr.w = cv.width;
    hdr.h = cv.height;
  }

  // Rings every kiloparsec on the Galactic plane and the line from the Sun to the Galactic
  // centre direction, as one buffer of line segments.
  const SEG = 180, ring = [];
  for (let r = 1; r <= 5; r += 1) {
    for (let i = 0; i < SEG; i += 1) {
      const a0 = (2 * Math.PI * i) / SEG, a1 = (2 * Math.PI * (i + 1)) / SEG;
      ring.push(r * Math.cos(a0), r * Math.sin(a0), 0, r * Math.cos(a1), r * Math.sin(a1), 0);
    }
  }
  ring.push(0, 0, 0, 5, 0, 0);
  const ringBuf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, ringBuf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(ring), gl.STATIC_DRAW);
  const nRing = ring.length / 3;

  // -------------------------------------------------------------------- data
  let pos = null, posBuf = null, fehBuf = null;
  function half(h) {
    const s = h >> 15 ? -1 : 1, e = (h >> 10) & 31, m = h & 1023;
    if (e === 0) return s * m * 2 ** -24;
    if (e === 31) return m ? NaN : s * Infinity;
    return s * (1 + m / 1024) * 2 ** (e - 15);
  }
  fetch(root.dataset.src)
    .then((r) => (r.ok ? r.arrayBuffer() : Promise.reject(new Error(r.status))))
    .then((buf) => {
      const u16 = new Uint16Array(buf, 0, 3 * N), feh = new Int8Array(buf, 6 * N, N);
      pos = new Float32Array(3 * N);
      for (let i = 0; i < N; i += 1) {
        pos[3 * i] = half(u16[i]);
        pos[3 * i + 1] = half(u16[N + i]);
        pos[3 * i + 2] = half(u16[2 * N + i]);
      }
      posBuf = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, posBuf);
      gl.bufferData(gl.ARRAY_BUFFER, pos, gl.STATIC_DRAW);
      fehBuf = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, fehBuf);
      gl.bufferData(gl.ARRAY_BUFFER, feh, gl.STATIC_DRAW);
      root.classList.add("mw--ready");
      moved = true;
      draw();
    })
    .catch(() => {
      load.textContent = "The star data did not load.";
    });

  // ------------------------------------------------------------------ camera
  // The camera orbits the Sun: yaw and pitch of the direction from the Sun to the camera, and
  // the distance. From the Sun means a camera 20 pc behind the Sun looking at the Galactic
  // centre, so that a drag there turns the view rather than the Galaxy.
  const FOV = (50 * Math.PI) / 180, SPRITE = 0.03;
  const VIEWS = {
    sun: { yaw: Math.PI, pitch: 0, dist: 0.02 },
    above: { yaw: Math.PI, pitch: 1.55, dist: 11.5 },
    edge: { yaw: -Math.PI / 2, pitch: 0, dist: 12 },
  };
  const cam = { ...VIEWS.edge };
  const S = { mode: "feh", view: "edge", playing: false, tour: 0, trans: null, w: 0, h: 0, dpr: 1 };
  const RAMP = { feh: [-1.1, -0.4], dist: [5, 0] };
  const TOUR = 20;
  let moved = true, raf = 0, last = null, onScreen = false, frameMs = 0;
  const vp = new Float32Array(16), proj = new Float32Array(16), view = new Float32Array(16);
  const stats = { frames: 0, ms: 0 };
  root.mwStats = stats;

  function perspective(out, fovy, aspect, near, far) {
    const f = 1 / Math.tan(fovy / 2), nf = 1 / (near - far);
    out.fill(0);
    out[0] = f / aspect;
    out[5] = f;
    out[10] = (far + near) * nf;
    out[11] = -1;
    out[14] = 2 * far * near * nf;
  }
  function lookAt(out, eye, up) {
    // Target is the origin.
    let zx = eye[0], zy = eye[1], zz = eye[2], l = Math.hypot(zx, zy, zz);
    zx /= l; zy /= l; zz /= l;
    let xx = up[1] * zz - up[2] * zy, xy = up[2] * zx - up[0] * zz, xz = up[0] * zy - up[1] * zx;
    l = Math.hypot(xx, xy, xz);
    xx /= l; xy /= l; xz /= l;
    const yx = zy * xz - zz * xy, yy = zz * xx - zx * xz, yz = zx * xy - zy * xx;
    out.set([xx, yx, zx, 0, xy, yy, zy, 0, xz, yz, zz, 0, -(xx * eye[0] + xy * eye[1] + xz * eye[2]), -(yx * eye[0] + yy * eye[1] + yz * eye[2]), -(zx * eye[0] + zy * eye[1] + zz * eye[2]), 1]);
  }
  function multiply(out, a, b) {
    for (let c = 0; c < 4; c += 1) {
      for (let r = 0; r < 4; r += 1) {
        out[4 * c + r] = a[r] * b[4 * c] + a[4 + r] * b[4 * c + 1] + a[8 + r] * b[4 * c + 2] + a[12 + r] * b[4 * c + 3];
      }
    }
  }
  function updateMatrices() {
    const cp = Math.cos(cam.pitch);
    const eye = [cam.dist * cp * Math.cos(cam.yaw), cam.dist * cp * Math.sin(cam.yaw), cam.dist * Math.sin(cam.pitch)];
    perspective(proj, FOV, S.w / S.h, 0.01, 80);
    lookAt(view, eye, [0, 0, 1]);
    multiply(vp, proj, view);
  }

  // The tour: a pull-out from the Sun along the anticentre direction that clears the nearest
  // stars in the first seconds and eases out near 10 kpc, rising above the plane while circling
  // a third of the way round, to end on an oblique view of the disc.
  function tourAt(u) {
    cam.dist = 0.02 + 10.5 * Math.pow(smooth(u / 0.82), 1.6);
    cam.pitch = 0.6 * smooth((u - 0.12) / 0.75);
    cam.yaw = Math.PI - 2.3 * smooth((u - 0.05) / 0.95);
  }
  function setTour(u) {
    S.tour = clamp(u, 0, 1);
    tourAt(S.tour);
    moved = true;
  }
  function goTo(name, instant) {
    const v = VIEWS[name];
    S.view = name;
    stopTour();
    syncUI();
    if (instant || reduced.matches) {
      Object.assign(cam, v);
      S.trans = null;
      moved = true;
      kick();
      return;
    }
    let yaw = v.yaw, d = yaw - cam.yaw;
    while (d > Math.PI) d -= 2 * Math.PI;
    while (d < -Math.PI) d += 2 * Math.PI;
    yaw = cam.yaw + d;
    S.trans = { from: { ...cam }, to: { ...v, yaw }, t: 0 };
    kick();
  }
  function stopTour() {
    if (!S.playing) return;
    S.playing = false;
    syncUI();
  }
  function syncUI() {
    playBtn.textContent = S.playing ? "Pause" : S.tour >= 1 ? "Replay" : "Play";
    playBtn.setAttribute("aria-pressed", String(S.playing));
    root.querySelectorAll("[data-view]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.view === S.view)));
    root.querySelectorAll("[data-mode]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.mode === S.mode)));
  }

  // --------------------------------------------------------------------- draw
  const marks = {};
  root.querySelectorAll("[data-mark]").forEach((el) => (marks[el.dataset.mark] = el));
  const MARK_AT = { sun: [0, 0, 0], gc: [5, 0, 0], r5: [-3.5355, 3.5355, 0] };
  function place(el, p) {
    const w = vp[3] * p[0] + vp[7] * p[1] + vp[11] * p[2] + vp[15];
    if (w < 0.15) return void (el.hidden = true);
    const x = (vp[0] * p[0] + vp[4] * p[1] + vp[8] * p[2] + vp[12]) / w, y = (vp[1] * p[0] + vp[5] * p[1] + vp[9] * p[2] + vp[13]) / w;
    if (x < -1.05 || x > 1.05 || y < -1.05 || y > 1.05) return void (el.hidden = true);
    el.hidden = false;
    el.style.left = `${((x + 1) / 2) * S.w}px`;
    el.style.top = `${((1 - y) / 2) * S.h}px`;
  }
  const countOut = $("[data-count]"), fmt = (n) => n.toLocaleString("en-GB");
  let countTick = 0;
  function countVisible() {
    let n = 0;
    const m = vp;
    for (let i = 0; i < N; i += 1) {
      const x = pos[3 * i], y = pos[3 * i + 1], z = pos[3 * i + 2];
      const w = m[3] * x + m[7] * y + m[11] * z + m[15];
      if (w <= 0.01) continue;
      const cx = m[0] * x + m[4] * y + m[8] * z + m[12];
      if (cx < -w || cx > w) continue;
      const cy = m[1] * x + m[5] * y + m[9] * z + m[13];
      if (cy < -w || cy > w) continue;
      n += 1;
    }
    countOut.textContent = `${fmt(n)} of ${fmt(N)}`;
  }

  let bg = [12 / 255, 11 / 255, 10 / 255];
  function readBg() {
    const m = /(\d+)\D+(\d+)\D+(\d+)/.exec(getComputedStyle(stage).backgroundColor || "");
    if (m) bg = [m[1] / 255, m[2] / 255, m[3] / 255];
  }

  // Exposure: the level that reaches white grows with the camera's distance, since a far
  // camera stacks many more stars on each pixel than one standing at the Sun.
  const EXPO = { alpha: 0.6, e: 1.2, direct: 0.22, ref: () => clamp(2 + 1.2 * cam.dist, 2, 16) };
  function draw() {
    if (!S.w || !S.h) return;
    const t0 = performance.now();
    updateMatrices();
    sizeHdr();
    gl.viewport(0, 0, cv.width, cv.height);

    if (pos) {
      gl.bindFramebuffer(gl.FRAMEBUFFER, hdr ? hdr.fb : null);
      gl.clearColor(hdr ? 0 : bg[0], hdr ? 0 : bg[1], hdr ? 0 : bg[2], 1);
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.blendFunc(gl.ONE, gl.ONE);
      gl.useProgram(P);
      gl.uniformMatrix4fv(U.u_vp, false, vp);
      gl.uniform1f(U.u_px, (SPRITE * (cv.height / 2)) / Math.tan(FOV / 2));
      gl.uniform1f(U.u_min, 2.5 * S.dpr);
      gl.uniform1f(U.u_max, MAXPT * S.dpr);
      gl.uniform1f(U.u_mode, S.mode === "feh" ? 0 : 1);
      gl.uniform1f(U.u_alpha, hdr ? EXPO.alpha : EXPO.direct);
      gl.uniform2f(U.u_ramp, RAMP[S.mode][0], RAMP[S.mode][1]);
      gl.bindBuffer(gl.ARRAY_BUFFER, posBuf);
      gl.enableVertexAttribArray(aPos);
      gl.vertexAttribPointer(aPos, 3, gl.FLOAT, false, 0, 0);
      gl.bindBuffer(gl.ARRAY_BUFFER, fehBuf);
      gl.enableVertexAttribArray(aFeh);
      gl.vertexAttribPointer(aFeh, 1, gl.BYTE, false, 0, 0);
      gl.drawArrays(gl.POINTS, 0, N);
      if (hdr) {
        gl.bindFramebuffer(gl.FRAMEBUFFER, null);
        gl.disable(gl.BLEND);
        gl.useProgram(TP);
        gl.activeTexture(gl.TEXTURE0);
        gl.bindTexture(gl.TEXTURE_2D, hdr.tex);
        gl.uniform1i(TU.tex, 0);
        gl.uniform1f(TU.e, EXPO.e);
        gl.uniform1f(TU.ref, EXPO.ref());
        gl.uniform3f(TU.bg, bg[0], bg[1], bg[2]);
        gl.bindBuffer(gl.ARRAY_BUFFER, quad);
        gl.enableVertexAttribArray(tPos);
        gl.vertexAttribPointer(tPos, 2, gl.FLOAT, false, 0, 0);
        gl.drawArrays(gl.TRIANGLES, 0, 3);
        gl.enable(gl.BLEND);
      }
      if (moved && (countTick += 1) % 4 === 1) countVisible();
    } else {
      gl.bindFramebuffer(gl.FRAMEBUFFER, null);
      gl.clearColor(bg[0], bg[1], bg[2], 1);
      gl.clear(gl.COLOR_BUFFER_BIT);
    }

    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
    gl.useProgram(L);
    gl.uniformMatrix4fv(LU.vp, false, vp);
    gl.uniform4f(LU.col, 0.62, 0.6, 0.57, 0.3);
    gl.bindBuffer(gl.ARRAY_BUFFER, ringBuf);
    gl.enableVertexAttribArray(lPos);
    gl.vertexAttribPointer(lPos, 3, gl.FLOAT, false, 0, 0);
    gl.drawArrays(gl.LINES, 0, nRing);

    for (const k in marks) place(marks[k], MARK_AT[k]);
    moved = false;
    frameMs = performance.now() - t0;
    stats.frames += 1;
    stats.ms += frameMs;
  }

  // --------------------------------------------------------------------- loop
  // Frames run only while the tour plays, a view transition runs, or the camera has moved,
  // and only while the figure is on screen.
  const animating = () => S.playing || S.trans;
  function kick() {
    if (raf || !onScreen) return;
    last = null;
    raf = requestAnimationFrame(tick);
  }
  function tick(now) {
    raf = 0;
    const dt = last === null ? 0 : clamp((now - last) / 1000, 0, 0.25);
    last = now;
    try {
      if (S.playing) {
        setTour(S.tour + dt / TOUR);
        if (S.tour >= 1) stopTour();
      } else if (S.trans) {
        const tr = S.trans, k = smooth((tr.t += dt / 1.4));
        cam.yaw = lerp(tr.from.yaw, tr.to.yaw, k);
        cam.pitch = lerp(tr.from.pitch, tr.to.pitch, k);
        cam.dist = Math.exp(lerp(Math.log(tr.from.dist), Math.log(tr.to.dist), k));
        moved = true;
        if (tr.t >= 1) S.trans = null;
      }
      if (moved || animating()) draw();
    } finally {
      if (animating() && onScreen) raf = requestAnimationFrame(tick);
    }
  }
  function fit() {
    const r = stage.getBoundingClientRect();
    S.dpr = Math.min(window.devicePixelRatio || 1, 2);
    S.w = Math.round(r.width);
    S.h = Math.round(r.height);
    cv.width = Math.round(S.w * S.dpr);
    cv.height = Math.round(S.h * S.dpr);
    moved = true;
    draw();
  }

  // -------------------------------------------------------------- interaction
  playBtn.addEventListener("click", () => {
    if (S.playing) {
      stopTour();
      return;
    }
    S.trans = null;
    if (S.tour >= 1) setTour(0);
    S.view = "";
    if (reduced.matches) {
      setTour(1);
      syncUI();
      kick();
      return;
    }
    S.playing = true;
    syncUI();
    kick();
  });
  root.querySelectorAll("[data-view]").forEach((b) => b.addEventListener("click", () => goTo(b.dataset.view)));
  root.querySelectorAll("[data-mode]").forEach((b) =>
    b.addEventListener("click", () => {
      S.mode = b.dataset.mode;
      const feh = S.mode === "feh";
      $("[data-scale-title]").textContent = feh ? "[Fe/H]" : "distance";
      $("[data-scale-hi]").textContent = feh ? "−0.4" : "0 kpc";
      $("[data-scale-lo]").textContent = feh ? "−1.1" : "5 kpc";
      syncUI();
      moved = true;
      kick();
      if (!animating()) draw();
    }),
  );

  const ptr = new Map();
  let pinch = 0;
  function userMoved() {
    stopTour();
    S.trans = null;
    S.view = "";
    syncUI();
  }
  cv.addEventListener("pointerdown", (ev) => {
    cv.setPointerCapture(ev.pointerId);
    ptr.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
    if (ptr.size === 2) {
      const [a, b] = [...ptr.values()];
      pinch = Math.hypot(a.x - b.x, a.y - b.y);
    }
  });
  cv.addEventListener("pointermove", (ev) => {
    const p = ptr.get(ev.pointerId);
    if (!p) return;
    const dx = ev.clientX - p.x, dy = ev.clientY - p.y;
    p.x = ev.clientX;
    p.y = ev.clientY;
    if (ptr.size === 1) {
      if (!dx && !dy) return;
      userMoved();
      cam.yaw -= dx * 0.006;
      cam.pitch = clamp(cam.pitch + dy * 0.006, -1.55, 1.55);
    } else {
      const [a, b] = [...ptr.values()], d = Math.hypot(a.x - b.x, a.y - b.y);
      if (pinch > 0 && d > 0) {
        userMoved();
        cam.dist = clamp((cam.dist * pinch) / d, 0.02, 40);
      }
      pinch = d;
    }
    moved = true;
    if (!animating()) draw();
  });
  const release = (ev) => ptr.delete(ev.pointerId);
  cv.addEventListener("pointerup", release);
  cv.addEventListener("pointercancel", release);
  cv.addEventListener(
    "wheel",
    (ev) => {
      if (!ev.ctrlKey && !ev.metaKey) return;
      ev.preventDefault();
      userMoved();
      cam.dist = clamp(cam.dist * Math.exp(ev.deltaY * (ev.deltaMode ? 0.05 : 0.0015)), 0.02, 40);
      moved = true;
      draw();
    },
    { passive: false },
  );
  cv.addEventListener("keydown", (ev) => {
    const k = ev.key;
    const turn = { ArrowLeft: [-0.06, 0], ArrowRight: [0.06, 0], ArrowUp: [0, 0.06], ArrowDown: [0, -0.06] }[k];
    const zoom = k === "+" || k === "=" ? 0.85 : k === "-" || k === "_" ? 1 / 0.85 : 0;
    if (!turn && !zoom) return;
    ev.preventDefault();
    userMoved();
    if (turn) {
      cam.yaw += turn[0];
      cam.pitch = clamp(cam.pitch + turn[1], -1.55, 1.55);
    } else cam.dist = clamp(cam.dist * zoom, 0.02, 40);
    moved = true;
    draw();
  });

  // ---------------------------------------------------------------- lifecycle
  readBg();
  fit();
  syncUI();
  new ResizeObserver(fit).observe(stage);
  if ("IntersectionObserver" in window) {
    new IntersectionObserver((es) => {
      onScreen = es[es.length - 1].isIntersecting;
      if (onScreen) {
        moved = true;
        draw();
        kick();
      }
    }, { rootMargin: "60px" }).observe(root);
  } else {
    onScreen = true;
    kick();
  }
  reduced.addEventListener("change", () => {
    if (reduced.matches) stopTour();
  });
  cv.addEventListener("webglcontextlost", (ev) => {
    ev.preventDefault();
    stopTour();
    load.textContent = "The graphics context was lost; reload the page to draw the map again.";
    root.classList.remove("mw--ready");
  });
})();
