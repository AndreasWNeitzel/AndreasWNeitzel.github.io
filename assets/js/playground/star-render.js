// One star on a canvas, drawn from the mass, radius and luminosity the polytrope page computes.
// WebGL2 with a WebGL1 fallback, no dependencies. A full-screen triangle carries one fragment
// shader: the disc is a sphere whose normal feeds three-dimensional simplex noise for the
// granulation, the intensity falls off with a linear limb-darkening law, the colour comes from
// a blackbody table built here (Planck's law against the CIE 1931 colour matching functions)
// and sampled at the depth-dependent temperature of a grey atmosphere, and a thin chromosphere
// plus a faint corona feather the limb into a dark vignette with a fixed procedural star field.
// The loop pauses when the canvas leaves the viewport or the tab is hidden; with reduced motion
// one frame is drawn per change and nothing animates. No text is drawn.

const T_SUN = 5772;
const TABLE_MIN = 2000;
const TABLE_MAX = 40000;
const TABLE_N = 381; // every 100 K
const reduced = typeof matchMedia === "function" ? matchMedia("(prefers-reduced-motion: reduce)") : { matches: false, addEventListener() {}, removeEventListener() {} };

// ---------------------------------------------------------------- blackbody to sRGB
// Planck's law integrated against the CIE 1931 two-degree observer, in the multi-lobe
// piecewise-Gaussian fit of Wyman, Sloan and Shirley (2013, JCGT 2, 1), then XYZ to linear sRGB
// (D65) with negative channels clipped and the largest channel set to one, so the table carries
// the chromaticity only; the shader sets the brightness. Stored sRGB-encoded in eight bits.
// The white point stays D65, the white of an sRGB screen. A 5000 K (D50) white was tried and
// runs the wrong way: adapting it to the screen turns a 5772 K blackbody into (224, 231, 255),
// a blue-white Sun, because the Sun is hotter than that white. Under D65 the Sun is
// (255, 241, 234), a faintly warm white, and the limb, cooler, shows warmer.
function blackbodyTable() {
  const lobe = (l, mu, s1, s2) => {
    const t = (l - mu) / (l < mu ? s1 : s2);
    return Math.exp(-0.5 * t * t);
  };
  const xbar = (l) => 1.056 * lobe(l, 599.8, 37.9, 31.0) + 0.362 * lobe(l, 442.0, 16.0, 26.7) - 0.065 * lobe(l, 501.1, 20.4, 26.2);
  const ybar = (l) => 0.821 * lobe(l, 568.8, 46.9, 40.5) + 0.286 * lobe(l, 530.9, 16.3, 31.1);
  const zbar = (l) => 1.217 * lobe(l, 437.0, 11.8, 36.0) + 0.681 * lobe(l, 459.0, 26.0, 13.8);
  const c2 = 1.438776877e-2; // second radiation constant, m K
  const encode = (v) => (v <= 0.0031308 ? 12.92 * v : 1.055 * v ** (1 / 2.4) - 0.055);
  const data = new Uint8Array(TABLE_N * 4);
  for (let i = 0; i < TABLE_N; i++) {
    const T = TABLE_MIN + ((TABLE_MAX - TABLE_MIN) * i) / (TABLE_N - 1);
    let X = 0;
    let Y = 0;
    let Z = 0;
    for (let l = 380; l <= 780; l += 2) {
      const lm = l * 1e-9;
      const B = 1 / (lm ** 5 * (Math.exp(c2 / (lm * T)) - 1));
      X += B * xbar(l);
      Y += B * ybar(l);
      Z += B * zbar(l);
    }
    let r = 3.2406 * X - 1.5372 * Y - 0.4986 * Z;
    let g = -0.9689 * X + 1.8758 * Y + 0.0415 * Z;
    let b = 0.0557 * X - 0.204 * Y + 1.057 * Z;
    const top = Math.max(r, g, b);
    r = Math.max(0, r / top);
    g = Math.max(0, g / top);
    b = Math.max(0, b / top);
    data[i * 4] = Math.round(255 * encode(r));
    data[i * 4 + 1] = Math.round(255 * encode(g));
    data[i * 4 + 2] = Math.round(255 * encode(b));
    data[i * 4 + 3] = 255;
  }
  return data;
}

// Linear limb-darkening coefficient against effective temperature, a piecewise-linear
// approximation to the V-band values of Claret (2000, A&A 363, 1081) for dwarfs: about 0.75 at
// 4000 K, 0.6 at 5800 K and 0.45 at 8000 K, held constant beyond the ends.
function limbCoefficient(teff) {
  const pts = [[3000, 0.82], [4000, 0.75], [5800, 0.6], [8000, 0.45], [12000, 0.35]];
  if (teff <= pts[0][0]) return pts[0][1];
  for (let i = 1; i < pts.length; i++) {
    if (teff <= pts[i][0]) {
      const f = (teff - pts[i - 1][0]) / (pts[i][0] - pts[i - 1][0]);
      return pts[i - 1][1] + f * (pts[i][1] - pts[i - 1][1]);
    }
  }
  return pts[pts.length - 1][1];
}

// ---------------------------------------------------------------- shaders
const VERT = `
attribute vec2 aPos;
void main() { gl_Position = vec4(aPos, 0.0, 1.0); }
`;

const FRAG = `
#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif
#ifdef WEBGL2
out vec4 fragColour;
#define gl_FragColor fragColour
#endif
uniform vec2 uRes;
uniform float uDpr;
uniform vec2 uCentre;
uniform float uRadius;
uniform float uTime;
uniform sampler2D uTable;
uniform vec3 uTableInfo;
uniform float uTeff;
uniform float uLimb;
uniform float uCells;
uniform float uContrast;
uniform float uDetail;
uniform float uPix;

// Simplex noise in three dimensions after the MIT-licensed implementation of Gustavson and
// McEwan (webgl-noise, github.com/ashima/webgl-noise).
vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 permute(vec4 x) { return mod289(((x * 34.0) + 1.0) * x); }
vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }
float snoise(vec3 v) {
  const vec2 C = vec2(1.0 / 6.0, 1.0 / 3.0);
  const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
  vec3 i = floor(v + dot(v, C.yyy));
  vec3 x0 = v - i + dot(i, C.xxx);
  vec3 g = step(x0.yzx, x0.xyz);
  vec3 l = 1.0 - g;
  vec3 i1 = min(g.xyz, l.zxy);
  vec3 i2 = max(g.xyz, l.zxy);
  vec3 x1 = x0 - i1 + C.xxx;
  vec3 x2 = x0 - i2 + C.yyy;
  vec3 x3 = x0 - D.yyy;
  i = mod289(i);
  vec4 p = permute(permute(permute(i.z + vec4(0.0, i1.z, i2.z, 1.0)) + i.y + vec4(0.0, i1.y, i2.y, 1.0)) + i.x + vec4(0.0, i1.x, i2.x, 1.0));
  float n_ = 0.142857142857;
  vec3 ns = n_ * D.wyz - D.xzx;
  vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
  vec4 x_ = floor(j * ns.z);
  vec4 y_ = floor(j - 7.0 * x_);
  vec4 x = x_ * ns.x + ns.yyyy;
  vec4 y = y_ * ns.x + ns.yyyy;
  vec4 h = 1.0 - abs(x) - abs(y);
  vec4 b0 = vec4(x.xy, y.xy);
  vec4 b1 = vec4(x.zw, y.zw);
  vec4 s0 = floor(b0) * 2.0 + 1.0;
  vec4 s1 = floor(b1) * 2.0 + 1.0;
  vec4 sh = -step(h, vec4(0.0));
  vec4 a0 = b0.xzyw + s0.xzyw * sh.xxyy;
  vec4 a1 = b1.xzyw + s1.xzyw * sh.zzww;
  vec3 p0 = vec3(a0.xy, h.x);
  vec3 p1 = vec3(a0.zw, h.y);
  vec3 p2 = vec3(a1.xy, h.z);
  vec3 p3 = vec3(a1.zw, h.w);
  vec4 norm = taylorInvSqrt(vec4(dot(p0, p0), dot(p1, p1), dot(p2, p2), dot(p3, p3)));
  p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
  vec4 m = max(0.6 - vec4(dot(x0, x0), dot(x1, x1), dot(x2, x2), dot(x3, x3)), 0.0);
  m = m * m;
  return 42.0 * dot(m * m, vec4(dot(p0, x0), dot(p1, x1), dot(p2, x2), dot(p3, x3)));
}

float hash21(vec2 p) {
  vec3 p3 = fract(vec3(p.xyx) * 0.1031);
  p3 += dot(p3, p3.yzx + 33.33);
  return fract((p3.x + p3.y) * p3.z);
}

vec3 toLinear(vec3 c) { return pow(c, vec3(2.2)); }
vec3 toSrgb(vec3 c) {
  vec3 lo = 12.92 * c;
  vec3 hi = 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055;
  return mix(lo, hi, step(0.0031308, c));
}

// chromaticity of a blackbody at T, from the table, sRGB-encoded with the largest channel one
vec3 chroma(float T) {
  float s = (clamp(T, uTableInfo.x, uTableInfo.y) - uTableInfo.x) / (uTableInfo.y - uTableInfo.x);
  float u = (s * (uTableInfo.z - 1.0) + 0.5) / uTableInfo.z;
  return texture2D(uTable, vec2(u, 0.5)).rgb;
}
vec3 blackbody(float T) { return toLinear(chroma(T)); }

vec3 hash33(vec3 p) {
  p = fract(p * vec3(0.1031, 0.1030, 0.0973));
  p += dot(p, p.yxz + 33.33);
  return fract((p.xxy + p.yxx) * p.zyx);
}

// Cellular field in three dimensions: the distances to the nearest and second-nearest feature
// point of a jittered lattice, the points wandering so that the cells churn over tens of seconds.
vec2 cellular(vec3 p, float t) {
  vec3 i = floor(p);
  vec3 f = fract(p);
  float f1 = 8.0;
  float f2 = 8.0;
  for (int x = -1; x <= 1; x++) {
    for (int y = -1; y <= 1; y++) {
      for (int z = -1; z <= 1; z++) {
        vec3 o = vec3(float(x), float(y), float(z));
        vec3 h = hash33(i + o);
        vec3 pt = o + 0.5 + 0.38 * sin(t * (0.2 + 0.2 * h) + 6.2831 * h);
        vec3 r = pt - f;
        float d = dot(r, r);
        if (d < f1) { f2 = f1; f1 = d; } else if (d < f2) { f2 = d; }
      }
    }
  }
  return sqrt(vec2(f1, f2));
}

// Granulation at two scales. A whole-disc image cannot resolve granules (about a thousand fit
// across the Sun), so where cells would span few pixels the surface is a soft mottle of smooth
// simplex noise, evolving over about 20 s, with no cell structure in it. Where a cell spans more
// than about 12 device pixels (uDetail above 0) the cells fade in as white-light images show
// them (DKIST, SST): bright, slightly domed granules that darken gradually into broad
// intergranular lanes, about a quarter to a third of a cell wide, with a few bright points in
// the lanes. F2 minus F1 of the cellular field is zero on a cell boundary and grows towards the
// centre; a smooth curve of it gives the broad lane, and F1 alone the dome. The lattice is warped
// by simplex noise so that no two cells match. Returns a relative intensity from 0 on the lane
// floor to about 1 on a granule top.
float granules(vec3 q, float t) {
  float warp = snoise(q * 0.33 + vec3(17.0, 0.0, t * 0.015));
  vec3 p = q + vec3(warp * 0.5, warp * -0.4, warp * 0.3 + t * 0.03);
  float mottle = 0.5 + 0.45 * snoise(p * 1.1 + vec3(0.0, 0.0, t * 0.05)) + 0.25 * snoise(p * 2.3 + vec3(3.0, 8.0, t * 0.07));
  if (uDetail <= 0.0) return mottle;
  vec2 w = cellular(p, t);
  float e = (w.y - w.x) * (0.9 + 0.35 * warp);
  // a smooth rise out of the lane, widened by one pixel's footprint in units of e, so that a
  // lane near pixel width is averaged, as a detector would, instead of drawn as a hard line
  float rise = smoothstep(-0.5 * uPix, 0.42 + uPix, e);
  // the dome: granule centres a little brighter than their edges
  float dome = exp(-3.0 * w.x * w.x);
  float fine = snoise(p * 2.6 + vec3(0.0, 0.0, t * 0.04));
  // bright points: small, sparse, only on the lane floor
  float bp = smoothstep(0.78, 0.95, snoise(p * 3.4 + vec3(41.0, 7.0, t * 0.02))) * (1.0 - smoothstep(0.0, 0.1, e));
  float g = rise * (0.82 + 0.18 * dome) + 0.11 * fine;
  return mix(mottle, clamp(g, 0.0, 1.05) + 0.75 * bp, uDetail);
}

// a fixed, very faint field of points behind the star
vec3 starField(vec2 css) {
  float size = 26.0;
  vec2 cell = floor(css / size);
  vec2 f = fract(css / size);
  float h = hash21(cell + 3.7);
  if (h < 0.74) return vec3(0.0);
  vec2 pos = vec2(hash21(cell + 1.3), hash21(cell + 8.9)) * 0.7 + 0.15;
  float dpx = length((f - pos) * size);
  float b = (h - 0.74) / 0.26;
  b = b * b * b;
  float s = exp(-dpx * dpx / 0.8) * (0.02 + 0.22 * b);
  vec3 tint = mix(vec3(1.0, 0.9, 0.8), vec3(0.82, 0.9, 1.0), hash21(cell + 5.1));
  return tint * s;
}

void main() {
  vec2 frag = gl_FragCoord.xy;
  vec2 p = (frag - uCentre) / uRadius;
  float d = length(p);
  float px = 1.0 / uRadius;

  // Display mapping: intensity goes to the screen value linearly, as in scaled solar
  // continuum images (SDO/HMI intensitygrams), so the limb at 1 - u of the centre shows at that
  // fraction; the colour of each point is its blackbody chromaticity, sRGB-encoded. The disc
  // centre sits just below clipping.
  const float EXPOSURE = 1.0;

  // background: the dark plate with a vignette and the star field
  vec2 v = (frag - 0.5 * uRes) / (0.5 * min(uRes.x, uRes.y));
  float vig = smoothstep(0.1, 1.6, length(v));
  vec3 col = toSrgb(vec3(0.0046, 0.0041, 0.0036) * (1.0 - 0.7 * vig) + starField(frag / uDpr));

  // the chromosphere, a thin rim at the limb's own brightness, and the corona falling away
  vec3 tint = chroma(uTeff);
  float limbI = (1.0 - uLimb) * EXPOSURE;
  float out1 = max(d - 1.0, 0.0);
  float chromo = exp(-out1 / 0.008) * limbI * 0.55;
  // bloom: a wide faint glow in the star's colour, a few per cent of the disc centre,
  // falling off over about a quarter of a radius, so the disc reads as a light source
  float bloom = EXPOSURE * (0.06 * exp(-out1 / 0.25) + 0.02 * exp(-out1 / 0.08));
  col += tint * (chromo + bloom);

  // the disc
  if (d < 1.0 + 2.0 * px) {
    float r2 = min(dot(p, p), 1.0);
    float mu = sqrt(1.0 - r2);
    vec3 n = vec3(p, mu);
    float a = uTime * 0.012;
    float ca = cos(a);
    float sa = sin(a);
    vec3 rn = vec3(ca * n.x + sa * n.z, n.y, -sa * n.x + ca * n.z);
    float g = granules(rn * (uCells * 0.5), uTime);
    // a two per cent variation on the scale of a few granules, slower than the cells
    float big = snoise(rn * 3.0 + vec3(0.0, 0.0, uTime * 0.01)) * 0.02;
    // the granulation contrast falls towards the limb, where the cells are foreshortened
    float vis = smoothstep(0.0, 0.25, mu) * mix(0.35, 1.0, mu);
    float ld = 1.0 - uLimb * (1.0 - mu);
    // the emergent temperature of a grey atmosphere seen at angle mu (Eddington approximation)
    float Tmu = uTeff * pow(0.75 * (mu + 0.6667), 0.25);
    // Resolved cells darken from just under the granule tops, with a lane floor about
    // 2 uContrast below them; the mottle varies about a level just above its mean of 0.5, so
    // that it does not dim the disc and the centre stays just below clipping.
    float gran = 1.0 - 2.0 * uContrast * vis * (mix(0.6, 0.9, uDetail) - g);
    vec3 disc = chroma(Tmu) * EXPOSURE * ld * (gran + big);
    float edge = 1.0 - smoothstep(1.0 - 1.5 * px, 1.0 + 0.5 * px, d);
    col = mix(col, disc, edge);
  }

  col = clamp(col, 0.0, 1.0) + (hash21(frag + 0.37) - 0.5) / 255.0;
  gl_FragColor = vec4(col, 1.0);
}
`;

// ---------------------------------------------------------------- the renderer
export function create(canvas, options = {}) {
  const attrs = { alpha: false, antialias: false, depth: false, stencil: false, premultipliedAlpha: false, powerPreference: "high-performance" };
  let gl = options.webgl1 ? null : canvas.getContext("webgl2", attrs);
  let isGL2 = Boolean(gl);
  if (!gl) gl = canvas.getContext("webgl", attrs) || canvas.getContext("experimental-webgl", attrs);
  if (!gl) return { set() {}, destroy() {}, frameTime: () => NaN, supported: false };

  const state = { mass: 1, radius: 1, lum: 1, X: 0.7381, Z: 0.0134, n: 3, teff: T_SUN };
  let prog = null;
  let U = {};
  let buf = null;
  let tex = null;
  let raf = 0;
  let visible = true;
  let lost = false;
  const t0 = performance.now();
  const stats = { last: 0, mean: NaN };

  function compile(type, src) {
    const header = isGL2
      ? (type === gl.VERTEX_SHADER ? "#version 300 es\n#define attribute in\n" : "#version 300 es\n#define WEBGL2\n#define texture2D texture\n")
      : "";
    const sh = gl.createShader(type);
    gl.shaderSource(sh, header + src);
    gl.compileShader(sh);
    if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) {
      const log = gl.getShaderInfoLog(sh);
      gl.deleteShader(sh);
      throw new Error(`star-render shader: ${log}`);
    }
    return sh;
  }

  function setup() {
    const vs = compile(gl.VERTEX_SHADER, VERT);
    const fs = compile(gl.FRAGMENT_SHADER, FRAG);
    prog = gl.createProgram();
    gl.attachShader(prog, vs);
    gl.attachShader(prog, fs);
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(`star-render link: ${gl.getProgramInfoLog(prog)}`);
    gl.deleteShader(vs);
    gl.deleteShader(fs);
    U = {};
    for (const name of ["uRes", "uDpr", "uCentre", "uRadius", "uTime", "uTable", "uTableInfo", "uTeff", "uLimb", "uCells", "uContrast", "uDetail", "uPix"]) U[name] = gl.getUniformLocation(prog, name);
    buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(prog, "aPos");
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, TABLE_N, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, blackbodyTable());
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.useProgram(prog);
    gl.uniform1i(U.uTable, 0);
    gl.uniform3f(U.uTableInfo, TABLE_MIN, TABLE_MAX, TABLE_N);
  }

  function fit() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = Math.max(1, Math.round(canvas.clientWidth * dpr));
    const h = Math.max(1, Math.round(canvas.clientHeight * dpr));
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
    }
    return dpr;
  }

  // the apparent radius: the Sun fills 55 per cent of the shorter side, other radii on a log
  // scale so that 0.5 to 3 solar radii fit the frame
  function apparentRadius(w, h) {
    const f = Math.min(1.7, Math.max(0.3, 1 + 0.58 * Math.log(state.radius)));
    return 0.275 * Math.min(w, h) * f;
  }

  function draw(now) {
    if (lost) return;
    const dpr = fit();
    const w = canvas.width;
    const h = canvas.height;
    const R = apparentRadius(w, h);
    // granule size against surface gravity in solar units: angular size proportional to
    // g^-1/2, so the count across the disc grows as g^1/2 from about 70 on the Sun, clamped
    // and never finer than four device pixels. Real granules are far smaller still (about a
    // thousand across the solar disc), so on a whole-disc view they are a fine mottle.
    const g = state.mass / (state.radius * state.radius);
    const cells = Math.max(30, Math.min(140, 70 * Math.sqrt(g), (2 * R) / 4));
    const cellPx = (2 * R) / cells;
    // the cell structure emerges only where a cell spans more than about 12 device pixels
    const emerge = Math.min(1, Math.max(0, (cellPx - 9) / 6));
    const detail = emerge * emerge * (3 - 2 * emerge);
    // rms granulation contrast: near 15 per cent where cells are resolved, as in white-light
    // images (DKIST, SST); at whole-disc scale, where a real image shows almost none, a mottle
    // of 2 to 3 per cent rms, whose darkest patches sit about 6 per cent below the mean
    const contrast = 0.075 + (0.15 - 0.075) * detail;
    gl.viewport(0, 0, w, h);
    gl.useProgram(prog);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.uniform2f(U.uRes, w, h);
    gl.uniform1f(U.uDpr, dpr);
    gl.uniform2f(U.uCentre, w / 2, h / 2);
    gl.uniform1f(U.uRadius, R);
    gl.uniform1f(U.uTime, reduced.matches ? 0 : (now - t0) / 1000);
    gl.uniform1f(U.uTeff, state.teff);
    gl.uniform1f(U.uLimb, limbCoefficient(state.teff));
    gl.uniform1f(U.uCells, cells);
    gl.uniform1f(U.uContrast, contrast);
    gl.uniform1f(U.uDetail, detail);
    // one device pixel spans about 1 / cellPx of a cell; e runs about twice as fast as distance
    gl.uniform1f(U.uPix, 2 / cellPx);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  }

  function tick(now) {
    raf = 0;
    if (stats.last) {
      const dt = now - stats.last;
      stats.mean = Number.isNaN(stats.mean) ? dt : stats.mean * 0.9 + dt * 0.1;
    }
    stats.last = now;
    draw(now);
    if (running()) raf = requestAnimationFrame(tick);
  }

  const running = () => visible && !document.hidden && !reduced.matches && !lost;

  function schedule() {
    if (lost) return;
    if (running()) {
      if (!raf) raf = requestAnimationFrame(tick);
    } else {
      cancelAnimationFrame(raf);
      raf = 0;
      stats.last = 0;
      if (visible && !document.hidden) draw(performance.now());
    }
  }

  function onVisibility() {
    stats.last = 0;
    schedule();
  }
  const io = "IntersectionObserver" in window
    ? new IntersectionObserver((entries) => {
      visible = entries.some((e) => e.isIntersecting);
      stats.last = 0;
      schedule();
    }, { threshold: 0 })
    : null;
  io?.observe(canvas);
  const ro = "ResizeObserver" in window ? new ResizeObserver(() => { if (!running()) draw(performance.now()); }) : null;
  ro?.observe(canvas);
  document.addEventListener("visibilitychange", onVisibility);
  reduced.addEventListener("change", onVisibility);

  function onLost(e) {
    e.preventDefault();
    lost = true;
    cancelAnimationFrame(raf);
    raf = 0;
  }
  function onRestored() {
    lost = false;
    setup();
    schedule();
  }
  canvas.addEventListener("webglcontextlost", onLost);
  canvas.addEventListener("webglcontextrestored", onRestored);

  try {
    setup();
  } catch (err) {
    console.error(err);
    io?.disconnect();
    ro?.disconnect();
    document.removeEventListener("visibilitychange", onVisibility);
    reduced.removeEventListener("change", onVisibility);
    return { set() {}, destroy() {}, frameTime: () => NaN, supported: false };
  }
  schedule();

  return {
    supported: true,
    set(p) {
      if (p.mass > 0) state.mass = p.mass;
      if (p.radius > 0) state.radius = p.radius;
      if (p.lum > 0) state.lum = p.lum;
      if (p.X !== undefined) state.X = p.X;
      if (p.Z !== undefined) state.Z = p.Z;
      if (p.n !== undefined) state.n = p.n;
      state.teff = p.teff > 0 ? p.teff : T_SUN * (state.lum / (state.radius * state.radius)) ** 0.25;
      if (!running()) draw(performance.now());
      return state.teff;
    },
    frameTime: () => stats.mean,
    destroy() {
      cancelAnimationFrame(raf);
      raf = 0;
      io?.disconnect();
      ro?.disconnect();
      document.removeEventListener("visibilitychange", onVisibility);
      reduced.removeEventListener("change", onVisibility);
      canvas.removeEventListener("webglcontextlost", onLost);
      canvas.removeEventListener("webglcontextrestored", onRestored);
      if (prog) gl.deleteProgram(prog);
      if (buf) gl.deleteBuffer(buf);
      if (tex) gl.deleteTexture(tex);
      gl.getExtension("WEBGL_lose_context")?.loseContext();
    },
  };
}

export const StarRender = { create };
export default StarRender;
