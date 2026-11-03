// Stellar Explorer: the star cut open, drawn with WebGL from the selected model's own profile.
// One fragment shader ray-casts a sphere with the octant toward the viewer removed (camera 45
// degrees in azimuth and 30 degrees above the equator), so three quarter-disc faces show the
// interior. Everything that varies across the star comes from a 512 x 2 texture built here from
// the profile, indexed by log r/R: the temperature index from log T, the convective flag from
// the mixing type, the nuclear energy generation, the selected mode's radial displacement, the
// pressure scale height and the convective velocity. The photosphere takes the data file's own
// colour for the effective temperature, darkened toward the limb with a linear law whose
// coefficient follows Teff; granules are sized from log g. Textures of cells, granules and
// ripples are drawn, their places and scales are the model's. Classic script; exposes SEStar.
(() => {
  "use strict";

  const N = 512; // texels across log r/R from -3 to 0, the profiles' own range
  const LOG_MIN = -3;

  // Linear limb-darkening coefficient against effective temperature, a piecewise-linear
  // approximation to the V-band values of Claret (2000, A&A 363, 1081), as on the Build a star page.
  function limbCoefficient(teff) {
    const pts = [[3000, 0.82], [4000, 0.75], [5800, 0.6], [8000, 0.45], [12000, 0.35], [30000, 0.3]];
    if (teff <= pts[0][0]) return pts[0][1];
    for (let i = 1; i < pts.length; i++) {
      if (teff <= pts[i][0]) {
        const f = (teff - pts[i - 1][0]) / (pts[i][0] - pts[i - 1][0]);
        return pts[i - 1][1] + f * (pts[i][1] - pts[i - 1][1]);
      }
    }
    return pts[pts.length - 1][1];
  }

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
uniform vec2 uCentre;      // device pixels, origin bottom left
uniform float uRadius;     // device pixels per unit radius
uniform vec3 uRight;       // screen axes and the direction to the camera, in star coordinates
uniform vec3 uUp;
uniform vec3 uView;
uniform float uScale;      // r/R at the outer edge of the drawn ball (1, or the detail circle's radius)
uniform float uTime;
uniform float uPulse;      // displacement amplitude times cos(omega t)
uniform float uEll;
uniform float uXiSurf;
uniform vec3 uSurf;        // photosphere colour, sRGB
uniform float uLimb;
uniform float uCells;      // granules across the disc
uniform float uMinCell;    // smallest drawn cell in units of R
uniform float uDetail;     // 0 where granules are too small to resolve, 1 where they are resolved
uniform vec3 uPlate;
uniform sampler2D uProf;

vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 permute(vec4 x) { return mod289(((x * 34.0) + 1.0) * x); }
vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }
// Simplex noise in three dimensions after the MIT-licensed implementation of Gustavson and
// McEwan (webgl-noise, github.com/ashima/webgl-noise).
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
vec3 hash33(vec3 p) {
  p = fract(p * vec3(0.1031, 0.1030, 0.0973));
  p += dot(p, p.yxz + 33.33);
  return fract((p.xxy + p.yxx) * p.zyx);
}
// distances to the nearest and second-nearest point of a jittered lattice whose points wander
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

vec3 toLin(vec3 c) { return c * c; }
vec3 toSrgb(vec3 c) { return sqrt(max(c, 0.0)); }

float legendre(float c) {
  if (uEll < 0.5) return 1.0;
  if (uEll < 1.5) return c;
  return 0.5 * (3.0 * c * c - 1.0);
}
// the profile at r/R: x temperature index, y convective, z sqrt of eps / peak, w displacement
vec4 prof(float r) {
  float u = (log(max(r, 0.001)) / 2.302585 + 3.0) / 3.0;
  return texture2D(uProf, vec2(clamp(u, 0.0, 1.0), 0.25));
}
// the second row: x log10 of the pressure scale height mapped from -4..0, y convective velocity,
// z the low byte of the temperature index
vec4 prof2(float r) {
  float u = (log(max(r, 0.001)) / 2.302585 + 3.0) / 3.0;
  return texture2D(uProf, vec2(clamp(u, 0.0, 1.0), 0.75));
}
float xiAt(float r) { return prof(r).w * 2.0 - 1.0; }
// high and low bytes, each interpolated linearly by the sampler, so their sum is too
float tIndex(vec4 a, vec4 b) { return (a.x * 65280.0 + b.z * 255.0) / 65535.0; }

// colour ramp for the cut faces, ordered by temperature: deep red under the photosphere,
// orange and gold through the envelope and radiative zone, white at the centre
vec3 ramp(float t) {
  vec3 c0 = vec3(0.50, 0.15, 0.05);
  vec3 c1 = vec3(0.74, 0.30, 0.09);
  vec3 c2 = vec3(0.89, 0.53, 0.20);
  vec3 c3 = vec3(0.95, 0.74, 0.42);
  vec3 c4 = vec3(0.99, 0.91, 0.74);
  vec3 c5 = vec3(1.00, 0.99, 0.96);
  float s = clamp(t, 0.0, 1.0);
  if (s < 0.2) return mix(c0, c1, s / 0.2);
  if (s < 0.4) return mix(c1, c2, (s - 0.2) / 0.2);
  if (s < 0.6) return mix(c2, c3, (s - 0.4) / 0.2);
  if (s < 0.82) return mix(c3, c4, (s - 0.6) / 0.22);
  return mix(c4, c5, (s - 0.82) / 0.18);
}

// classify a screen point: 0 sky, 1 photosphere, 2 to 4 the faces x = 0, y = 0, z = 0
// P returns the hit point in star coordinates (unit ball), d the screen distance in radii
float hitWarp(vec2 s) {
  float l = length(s);
  if (l < 1e-5) return 1.0;
  vec3 dir = (s.x * uRight + s.y * uUp) / l;
  return 1.0 + uPulse * uXiSurf * legendre(dir.z);
}
int classify(vec2 s, out vec3 P) {
  vec2 q = s / hitWarp(s);
  float q2 = dot(q, q);
  P = vec3(0.0);
  if (q2 >= 1.0) return 0;
  vec3 P1 = q.x * uRight + q.y * uUp + sqrt(1.0 - q2) * uView;
  if (!(P1.x > 0.0 && P1.y > 0.0 && P1.z > 0.0)) { P = P1; return 1; }
  // inside the removed octant: march to the first of the three planes the ray leaves through
  vec3 tt = P1 / uView; // uView has positive components, the ray runs along -uView
  int k = 2;
  float t = tt.x;
  if (tt.y < t) { t = tt.y; k = 3; }
  if (tt.z < t) { t = tt.z; k = 4; }
  vec3 Q = P1 - t * uView;
  if (dot(Q, Q) >= 1.0) return 0;
  P = Q;
  return k;
}

vec3 sky(float d) {
  vec3 col = toLin(uPlate);
  if (uScale < 0.999) return col;
  float out1 = max(d - 1.0, 0.0);
  // a restrained warm glow: a thin bright rim and a soft falloff over about a fifth of a radius
  float rim = 0.20 * exp(-out1 / 0.018);
  float halo = 0.075 * exp(-out1 / 0.12) + 0.035 * exp(-out1 / 0.42);
  vec3 warm = mix(vec3(1.0, 0.86, 0.62), toLin(uSurf), 0.35);
  return col + warm * (rim + halo);
}

vec3 photosphere(vec3 P, vec2 s) {
  vec3 n = normalize(P);
  float mu = clamp(dot(n, uView), 0.0, 1.0);
  if (uScale < 0.999) {
    // the detail ball: its outside is the interior at its own radius
    return toLin(ramp(pow(tIndex(prof(uScale), prof2(uScale)), 2.2))) * (0.55 + 0.45 * mu);
  }
  float a = uTime * 0.009;
  float ca = cos(a), sa = sin(a);
  vec3 rn = vec3(ca * n.x - sa * n.y, sa * n.x + ca * n.y, n.z);
  vec3 g3 = rn * (uCells * 0.5);
  float warp = snoise(g3 * 0.33 + vec3(17.0, 0.0, uTime * 0.012));
  vec3 gp = g3 + vec3(warp * 0.5, -warp * 0.4, warp * 0.3);
  // whole-disc scale: a soft mottle; where a granule spans more than about 12 device pixels the
  // cells fade in with their lanes (the approach of the Build a star page)
  float mottle = 0.5 + 0.45 * snoise(gp * 1.1 + vec3(0.0, 0.0, uTime * 0.05)) + 0.2 * snoise(gp * 2.3 + vec3(3.0, 8.0, uTime * 0.07));
  float g = mottle;
  if (uDetail > 0.0) {
    vec2 w = cellular(gp, uTime * 0.6);
    float e = w.y - w.x;
    float cell = smoothstep(0.0, 0.42, e) * (0.82 + 0.18 * exp(-3.0 * w.x * w.x));
    g = mix(mottle, cell, uDetail);
  }
  float vis = smoothstep(0.0, 0.3, mu) * mix(0.4, 1.0, mu);
  float ld = 1.0 - uLimb * (1.0 - mu);
  // a raised part of the surface is hotter, a sunken part cooler (radial modes muted)
  float bump = uPulse * uXiSurf * legendre(n.z) * (uEll < 0.5 ? 1.2 : 3.0);
  // the data file's colour for Teff, deepened toward gold for display; the limb is cooler, so redder:
  // the blue and green channels fall a little faster toward it
  vec3 base = pow(uSurf, vec3(2.4 + 1.0 * (1.0 - mu)));
  // the intensity goes to the screen value linearly, so the limb shows at 1 - u of the centre
  float contrast = mix(0.07, 0.12, uDetail);
  vec3 disp = base * ld * (1.0 - 2.0 * contrast * vis * (0.62 - g)) * (1.0 + bump);
  return toLin(disp);
}

vec3 face(vec3 P, int k) {
  float rr = length(P);
  float cosT = rr > 1e-5 ? P.z / rr : 0.0;
  float r = rr * uScale;
  // the pulsation: the material at this place came from r0
  float fs = 1.0;
  if (uScale > 0.999) {
    vec2 sp = vec2(dot(P, uRight), dot(P, uUp));
    fs = hitWarp(sp);
  }
  float rt = r * fs;
  float r0 = rt / (1.0 + uPulse * xiAt(rt) * legendre(cosT));
  vec4 pr = prof(r0);
  vec4 p2 = prof2(r0);
  float t = pow(tIndex(pr, p2), 2.2);
  vec3 col = toLin(ramp(t));
  float conv = smoothstep(0.25, 0.75, pr.y);
  // convective cells sized by the local pressure scale height, never finer than a few pixels
  if (conv > 0.0) {
    float hp = pow(10.0, p2.x * 4.0 - 4.0);
    float size = clamp(hp * 1.2, uMinCell, 0.22);
    vec3 cp = P * uScale / size;
    float wv = snoise(cp * 0.45 + vec3(3.0, 1.0, uTime * 0.03));
    vec2 w = cellular(cp + 0.6 * vec3(wv, -wv, 0.5 * wv), uTime * 0.35);
    float up = smoothstep(0.02, 0.5, w.y - w.x);
    float vigour = 0.55 + 0.45 * p2.y;
    col *= mix(1.0, 0.62 + 0.62 * up, conv * vigour);
  }
  // radiative zones: faint shells drifting outward
  float rad = 1.0 - conv;
  if (rad > 0.0) {
    float f = fract(r0 / 0.14 - uTime * 0.03 + 0.08 * snoise(P * 3.0 + uTime * 0.05));
    float shell = exp(-pow((f - 0.5) / 0.035, 2.0));
    float speck = snoise(P * uScale * 60.0 + vec3(0.0, 0.0, uTime * 0.2));
    col *= 1.0 + rad * (0.05 * shell + 0.025 * speck);
  }
  // nuclear burning, from eps_nuc: an additive glow toward white
  float b = pr.z * pr.z;
  col += vec3(1.0, 0.86, 0.62) * (1.3 * b + 0.25 * pr.z) * (0.9 + 0.1 * snoise(P * 9.0 + uTime * 0.3));
  // a hairline where the energy transport changes
  float edge = abs(pr.y - 0.5);
  col *= mix(0.72, 1.0, smoothstep(0.0, 0.18, edge));
  // the three faces lit differently so the cut reads in depth
  float lit = k == 2 ? 0.80 : (k == 3 ? 0.90 : 1.0);
  return col * lit;
}

vec3 shade(vec2 s, int k, vec3 P) {
  if (k == 0) return sky(length(s / hitWarp(s)));
  if (k == 1) return photosphere(P, s);
  return face(P, k);
}

void main() {
  vec2 s = (gl_FragCoord.xy - uCentre) / uRadius;
  float px = 1.0 / uRadius;
  vec3 P;
  int k = classify(s, P);
  // the detail ball paints only itself, so the main star's glow shows around it
  if (uScale < 0.999 && length(s) > 1.0 + 1.5 * px) discard;
  // two by two supersampling where the four corners disagree, on edges only
  vec3 Pa; vec3 Pb; vec3 Pc; vec3 Pd;
  vec2 o1 = vec2(-0.25, -0.25) * px, o2 = vec2(0.25, -0.25) * px, o3 = vec2(-0.25, 0.25) * px, o4 = vec2(0.25, 0.25) * px;
  int ka = classify(s + o1, Pa), kb = classify(s + o2, Pb), kc = classify(s + o3, Pc), kd = classify(s + o4, Pd);
  vec3 col;
  if (ka == k && kb == k && kc == k && kd == k) {
    col = shade(s, k, P);
  } else {
    col = 0.25 * (shade(s + o1, ka, Pa) + shade(s + o2, kb, Pb) + shade(s + o3, kc, Pc) + shade(s + o4, kd, Pd));
  }
  col = min(col, vec3(1.0));
  vec2 h = gl_FragCoord.xy * vec2(0.1031, 0.1030);
  float n = fract(sin(dot(h, vec2(12.9898, 78.233))) * 43758.5453);
  gl_FragColor = vec4(toSrgb(col) + (n - 0.5) / 255.0, 1.0);
}
`;

  function create(canvas) {
    const attrs = { alpha: false, antialias: false, depth: false, stencil: false, premultipliedAlpha: false, preserveDrawingBuffer: true };
    const gl = canvas.getContext("webgl", attrs) || canvas.getContext("experimental-webgl", attrs);
    if (!gl) return { supported: false };
    let prog = null, tex = null, U = {};
    const compile = (type, src) => {
      const sh = gl.createShader(type);
      gl.shaderSource(sh, src);
      gl.compileShader(sh);
      if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) throw new Error("star shader: " + gl.getShaderInfoLog(sh));
      return sh;
    };
    try {
      prog = gl.createProgram();
      gl.attachShader(prog, compile(gl.VERTEX_SHADER, VERT));
      gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, FRAG));
      gl.linkProgram(prog);
      if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error("star link: " + gl.getProgramInfoLog(prog));
    } catch (e) {
      console.error(e);
      return { supported: false };
    }
    gl.useProgram(prog);
    for (const n of ["uCentre", "uRadius", "uRight", "uUp", "uView", "uScale", "uTime", "uPulse", "uEll", "uXiSurf", "uSurf", "uLimb", "uCells", "uMinCell", "uDetail", "uPlate", "uProf"]) U[n] = gl.getUniformLocation(prog, n);
    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(prog, "aPos");
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    for (const [p, v] of [[gl.TEXTURE_MIN_FILTER, gl.LINEAR], [gl.TEXTURE_MAG_FILTER, gl.LINEAR], [gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE], [gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE]]) gl.texParameteri(gl.TEXTURE_2D, p, v);
    gl.uniform1i(U.uProf, 0);

    // camera: azimuth 45 degrees, 30 degrees above the equator; screen y up
    const AZ = Math.PI / 4, EL = Math.PI / 6;
    const view = [Math.cos(EL) * Math.cos(AZ), Math.cos(EL) * Math.sin(AZ), Math.sin(EL)];
    const right = [-Math.sin(AZ), Math.cos(AZ), 0];
    const up = [view[1] * right[2] - view[2] * right[1], view[2] * right[0] - view[0] * right[2], view[0] * right[1] - view[1] * right[0]];
    gl.uniform3fv(U.uRight, right);
    gl.uniform3fv(U.uUp, up);
    gl.uniform3fv(U.uView, view);

    const st = { surf: [1, 0.9, 0.8], limb: 0.6, cells: 60, xiSurf: 0, ell: 0, plate: [0.06, 0.055, 0.05] };

    // the profile texture; p has x, logT, mt, eps, logP, conv_vel; xi on the same grid or null
    function setModel(p, xi, opt) {
      const n = p.x.length;
      const lc = p.logT[0], ls = p.logT[n - 1];
      const epsPeak = Math.max(...p.eps);
      const cvPeak = Math.max(...p.conv_vel.map((v) => (isFinite(v) ? v : 0))) || 1;
      // pressure scale height -dr / d ln P, in units of R, from neighbouring points
      const hp = p.x.map((_, k) => {
        const a = Math.max(0, k - 1), b = Math.min(n - 1, k + 1);
        const dlnP = (p.logP[b] - p.logP[a]) * Math.LN10;
        return dlnP < 0 ? (p.x[b] - p.x[a]) / -dlnP : 1;
      });
      let xiPeak = 0;
      if (xi) for (const v of xi) xiPeak = Math.max(xiPeak, Math.abs(v));
      const data = new Uint8Array(N * 2 * 4);
      let k = 0;
      for (let j = 0; j < N; j++) {
        const r = 10 ** (LOG_MIN + (-LOG_MIN * j) / (N - 1));
        while (k < n - 2 && p.x[k + 1] < r) k++;
        const f = p.x[k + 1] > p.x[k] ? Math.min(1, Math.max(0, (r - p.x[k]) / (p.x[k + 1] - p.x[k]))) : 0;
        const at = (arr) => arr[k] + (arr[k + 1] - arr[k]) * f;
        const near = f < 0.5 ? k : k + 1;
        const t = (at(p.logT) - ls) / (lc - ls || 1);
        const conv = p.mt[near] === 1 ? 1 : 0;
        const eps = epsPeak > 0 ? Math.sqrt(Math.max(0, at(p.eps)) / epsPeak) : 0;
        const x = xi && xiPeak > 0 ? at(xi) / xiPeak : 0;
        const h = Math.min(1, Math.max(0, (Math.log10(Math.max(1e-4, at(hp))) + 4) / 4));
        const cv = Math.sqrt(Math.max(0, at(p.conv_vel)) / cvPeak);
        const q = (v) => Math.round(255 * Math.min(1, Math.max(0, v)));
        data.set([q(t), q(conv), q(eps), q(0.5 + 0.5 * x)], j * 4);
        const t16 = Math.round(65535 * Math.min(1, Math.max(0, t)));
        data[j * 4] = t16 >> 8;
        data.set([q(h), q(cv), t16 & 255, 255], (N + j) * 4);
      }
      gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, N, 2, 0, gl.RGBA, gl.UNSIGNED_BYTE, data);
      st.surf = opt.rgb.map((v) => v / 255);
      st.limb = limbCoefficient(opt.teff);
      // granules across the disc grow in number as g^1/2, about 70 on the Sun (as on the Build a star page)
      st.cells = Math.max(14, Math.min(120, 70 * Math.sqrt(10 ** (opt.logg - 4.438))));
      st.xiSurf = xi && xiPeak > 0 ? xi[xi.length - 1] / xiPeak : 0;
      st.ell = opt.ell || 0;
    }

    function fit() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const w = Math.max(1, Math.round(canvas.clientWidth * dpr)), h = Math.max(1, Math.round(canvas.clientHeight * dpr));
      if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
      return dpr;
    }

    // views: [{cx, cy, R (css pixels), scale (r/R at the edge), pulse}], t in seconds
    function draw(views, t) {
      const dpr = fit();
      const H = canvas.height;
      gl.viewport(0, 0, canvas.width, H);
      gl.disable(gl.SCISSOR_TEST);
      gl.clearColor(st.plate[0], st.plate[1], st.plate[2], 1);
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.useProgram(prog);
      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.uniform3fv(U.uSurf, st.surf);
      gl.uniform3fv(U.uPlate, st.plate);
      gl.uniform1f(U.uLimb, st.limb);
      gl.uniform1f(U.uEll, st.ell);
      gl.uniform1f(U.uXiSurf, st.xiSurf);
      gl.uniform1f(U.uTime, t);
      gl.enable(gl.SCISSOR_TEST);
      for (const v of views) {
        const R = v.R * dpr;
        const cells = Math.min(st.cells, (2 * R) / 5);
        gl.uniform1f(U.uCells, cells);
        const cellPx = (2 * R) / cells, emerge = Math.min(1, Math.max(0, (cellPx - 9) / 6));
        gl.uniform1f(U.uDetail, emerge * emerge * (3 - 2 * emerge));
        gl.uniform2f(U.uCentre, v.cx * dpr, H - v.cy * dpr);
        gl.uniform1f(U.uRadius, R);
        gl.uniform1f(U.uScale, v.scale);
        gl.uniform1f(U.uPulse, v.pulse || 0);
        // a drawn cell spans at least five device pixels
        gl.uniform1f(U.uMinCell, (5 / R) * v.scale);
        // the main star fills the canvas (its glow too); a detail ball only its own square
        const ext = v.scale < 0.999 ? 1.04 * R : Math.max(canvas.width, H) * 2;
        const x0 = Math.max(0, Math.floor(v.cx * dpr - ext)), y0 = Math.max(0, Math.floor(H - v.cy * dpr - ext));
        gl.scissor(x0, y0, Math.min(canvas.width, Math.ceil(2 * ext)), Math.min(H, Math.ceil(2 * ext)));
        gl.drawArrays(gl.TRIANGLES, 0, 3);
      }
      gl.disable(gl.SCISSOR_TEST);
    }

    function setPlate(rgb) { st.plate = rgb; }
    return { supported: true, setModel, draw, setPlate };
  }

  window.SEStar = { create };
})();
