// Simplex noise by Ashima Arts / Stefan Gustavson (MIT), used for the drift of unsorted text.
const noise = /* glsl */ `
vec4 permute(vec4 x) { return mod(((x * 34.0) + 1.0) * x, 289.0); }
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
  vec3 x2 = x0 - i2 + 2.0 * C.xxx;
  vec3 x3 = x0 - 1.0 + 3.0 * C.xxx;
  i = mod(i, 289.0);
  vec4 p = permute(permute(permute(
    i.z + vec4(0.0, i1.z, i2.z, 1.0)) +
    i.y + vec4(0.0, i1.y, i2.y, 1.0)) +
    i.x + vec4(0.0, i1.x, i2.x, 1.0));
  float n_ = 1.0 / 7.0;
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
`

export const particleVertex = /* glsl */ `
uniform float uTime;
uniform float uPixelRatio;
uniform float uSize;
uniform float uAspect;
uniform float uDrift;
uniform float uCluster;
uniform float uFocus;
uniform vec3 uQuery;
uniform float uRadius;
uniform float uRetrieve;
uniform vec3 uSlots[5];
uniform float uClump;
uniform float uGlyph;
uniform vec3 uGlyphOffset;
uniform float uGlyphScale;
uniform float uLine;
uniform vec3 uLineOffset;
uniform vec2 uLineScale;
uniform float uBlink;
uniform vec2 uMouse;
uniform float uMouseForce;
uniform float uVelocity;
uniform float uThink;
uniform float uPulse;

attribute vec3 aCluster;
attribute vec3 aGlyph;
attribute vec3 aLine;
attribute vec4 aRand;      // x: stagger, y: size, z: phase, w: source slot
attribute float aSelected; // 1 for the passages the story's question retrieves

varying float vHighlight;
varying float vAlpha;

${noise}

// Staggered 0..1 so each transition ripples through the cloud instead of moving in lockstep
float stage(float t, float r) {
  float x = clamp(t * 1.6 - r * 0.6, 0.0, 1.0);
  return x * x * (3.0 - 2.0 * x);
}

void main() {
  // 1. Noise -> embedding clusters
  float c = stage(uCluster, aRand.x);
  vec3 p = mix(position, aCluster, c);
  float t = uTime * 0.08;
  vec3 drift = vec3(
    snoise(p * 0.3 + vec3(t, 0.0, aRand.z)),
    snoise(p * 0.3 + vec3(0.0, t, aRand.z + 17.0)),
    snoise(p * 0.3 + vec3(aRand.z + 31.0, 0.0, t))
  );
  p += drift * uDrift * mix(0.7, 0.1, c);

  // 2. Radius search around the question
  // the live probe reaches a little further than the story's retrieved set, so it reads at a glance
  float live = 1.0 - smoothstep(uRadius * 0.9, uRadius * 1.6, distance(aCluster, uQuery));
  float hl = max(live * uFocus, aSelected * max(uRetrieve, uGlyph));

  // 3. Retrieved passages step forward into five source clumps
  float r = stage(uRetrieve, aRand.x) * aSelected;
  vec3 slot = uSlots[int(aRand.w)] + (aCluster - uQuery) * uClump;
  p = mix(p, slot, r);

  // 4. Everything becomes the citation mark, 5. then the input's underline and caret
  float g = stage(uGlyph, aRand.x);
  p = mix(p, aGlyph * uGlyphScale + uGlyphOffset, g);
  float l = stage(uLine, aRand.x);
  p = mix(p, vec3(aLine.x * uLineScale.x, aLine.y * uLineScale.y, aLine.z) + uLineOffset, l);

  // Chat: the field leans toward the question while thinking and flashes when an answer lands
  p = mix(p, uQuery + (p - uQuery) * 0.45, uThink * (0.35 + 0.4 * aRand.x));
  hl = max(hl, (uPulse + uThink * 0.35) * aSelected);

  // Cursor pushes nearby particles aside, measured on screen so it feels the same at any depth
  vec4 clip = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
  vec2 dm = (clip.xy / clip.w - uMouse) * vec2(uAspect, 1.0);
  float push = (1.0 - smoothstep(0.0, 0.22, length(dm))) * uMouseForce;
  p.xy += normalize(dm + 1e-5) * push * push * 0.06 * clip.w;

  // Scroll velocity smears the cloud vertically
  p.y += uVelocity * (aRand.y - 0.5) * 1.2;

  vec4 mv = modelViewMatrix * vec4(p, 1.0);
  gl_Position = projectionMatrix * mv;
  gl_PointSize = uSize * (0.45 + aRand.y) * (1.0 + hl * 0.8 + push + 0.5 * (1.0 - c)) * uPixelRatio * (8.0 / -mv.z);

  float depth = smoothstep(22.0, 5.0, -mv.z);
  float dim = mix(1.0, 0.18, uRetrieve * (1.0 - aSelected) * (1.0 - g));
  float blink = mix(1.0, uBlink, aSelected * l);
  vHighlight = hl;
  vAlpha = depth * dim * blink * (0.4 + 0.6 * hl + push * 0.8) * mix(1.8, 1.0, c);
}
`

export const particleFragment = /* glsl */ `
uniform vec3 uBase;
uniform vec3 uAccent;
uniform float uOpacity;
varying float vHighlight;
varying float vAlpha;

void main() {
  float d = length(gl_PointCoord - 0.5);
  if (d > 0.5) discard;
  float a = smoothstep(0.5, 0.0, d);
  gl_FragColor = vec4(mix(uBase, uAccent, vHighlight), a * a * vAlpha * uOpacity);
}
`
