import { useFrame } from '@react-three/fiber';
import { useMemo } from 'react';
import { BackSide, ShaderMaterial } from 'three';
import { ambience } from './fx';
import { MOON_DIR, SKY_HORIZON } from './palette';

const vertex = /* glsl */ `
  varying vec3 vDir;
  void main() {
    vDir = normalize(position);
    vec4 p = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    gl_Position = p.xyww;
  }
`;

const fragment = /* glsl */ `
  uniform float uTime;
  uniform float uAurora;
  uniform float uStarry;
  uniform float uFinale;
  uniform float uWarm;
  uniform float uDim;
  uniform float uReveal;
  uniform float uShoot;
  uniform vec3 uMoonDir;
  uniform vec3 uHorizon;
  varying vec3 vDir;

  float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
  float noise(vec2 p) {
    vec2 i = floor(p); vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
  }
  float fbm(vec2 p) {
    float v = 0.0; float a = 0.5;
    for (int i = 0; i < 4; i++) { v += a * noise(p); p *= 2.03; a *= 0.5; }
    return v;
  }

  void main() {
    vec3 d = normalize(vDir);
    float h = clamp(d.y, -0.2, 1.0);

    // Dégradé de l'heure bleue : horizon ardoise, zénith encre.
    vec3 zenith = vec3(0.010, 0.020, 0.050);
    vec3 mid = vec3(0.030, 0.060, 0.120);
    vec3 col = mix(uHorizon, mid, smoothstep(0.0, 0.18, h));
    col = mix(col, zenith, smoothstep(0.15, 0.75, h));
    // Lueur chaude derrière les crêtes (village dans la vallée).
    col += vec3(0.20, 0.10, 0.04) * exp(-abs(h - 0.01) * 22.0) * (0.35 + uWarm * 0.9);

    // Étoiles procédurales : grille sur la sphère, scintillement.
    vec2 sp = vec2(atan(d.z, d.x) * 120.0, h * 140.0);
    vec2 cell = floor(sp);
    float rnd = hash(cell);
    float starMask = step(0.985 - uStarry * 0.02, rnd);
    vec2 sub = fract(sp) - 0.5 - (vec2(hash(cell + 3.1), hash(cell + 7.7)) - 0.5) * 0.6;
    float star = starMask * smoothstep(0.16, 0.0, length(sub));
    float tw = 0.55 + 0.45 * sin(uTime * (1.5 + rnd * 3.0) + rnd * 40.0);
    col += vec3(0.85, 0.9, 1.0) * star * tw * smoothstep(0.05, 0.35, h) * (0.9 + uStarry * 1.6);

    // Lune et halo.
    float md = dot(d, uMoonDir);
    float moon = smoothstep(0.99935, 0.99955, md);
    float crater = fbm(d.xy * 380.0) * 0.25;
    col = mix(col, vec3(1.0, 0.97, 0.9) * (1.35 - crater), moon);
    col += vec3(0.45, 0.55, 0.75) * pow(max(md, 0.0), 900.0) * 0.9;
    col += vec3(0.20, 0.27, 0.42) * pow(max(md, 0.0), 40.0) * 0.35;

    // Aurore boréale : rideaux de bruit le long d'une bande.
    float aur = uAurora + uFinale * 0.8;
    if (aur > 0.001) {
      vec2 ap = vec2(atan(d.z, d.x) * 2.2, h);
      float curtain = fbm(vec2(ap.x * 3.0 + uTime * 0.05, uTime * 0.03));
      float band = smoothstep(0.08, 0.3, h) * smoothstep(0.75, 0.32, h);
      float rays = pow(fbm(vec2(ap.x * 22.0 + curtain * 4.0, h * 2.0 - uTime * 0.2)), 2.0);
      float shape = smoothstep(0.35, 0.8, curtain + h * 0.3) * band;
      vec3 green = vec3(0.15, 0.95, 0.55);
      vec3 violet = vec3(0.45, 0.25, 0.85);
      vec3 ac = mix(green, violet, smoothstep(0.3, 0.65, h));
      col += ac * shape * (0.35 + rays * 1.6) * aur;
    }

    // Étoile filante.
    if (uShoot > 0.0 && uShoot < 1.0) {
      vec2 a = vec2(-0.2, 0.55);
      vec2 b = vec2(0.45, 0.3);
      vec2 p = vec2(atan(d.x, -d.z), h);
      vec2 head = mix(a, b, uShoot);
      vec2 dir = normalize(b - a);
      vec2 rel = p - head;
      float along = dot(rel, -dir);
      float across = abs(dot(rel, vec2(-dir.y, dir.x)));
      float trail = smoothstep(0.0025, 0.0, across) * smoothstep(0.25, 0.0, along) * step(0.0, along);
      col += vec3(1.0, 0.95, 0.85) * trail * 2.5 * sin(uShoot * 3.14159);
    }

    col *= mix(1.0, 0.45, uDim);
    col *= uReveal;
    gl_FragColor = vec4(col, 1.0);
    #include <colorspace_fragment>
  }
`;

function makeUniforms() {
  return {
    uTime: { value: 0 },
    uAurora: { value: 0 },
    uStarry: { value: 0 },
    uFinale: { value: 0 },
    uWarm: { value: 0 },
    uDim: { value: 0 },
    uReveal: { value: 0 },
    uShoot: { value: 0 },
    uMoonDir: { value: MOON_DIR },
    uHorizon: { value: SKY_HORIZON.clone().convertSRGBToLinear() },
  };
}

export function Sky() {
  const [material, u] = useMemo(() => {
    const uniforms = makeUniforms();
    const mat = new ShaderMaterial({
      vertexShader: vertex,
      fragmentShader: fragment,
      side: BackSide,
      depthWrite: false,
      fog: false,
      uniforms,
    });
    return [mat, uniforms] as const;
  }, []);

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    u.uTime.value = t;
    u.uAurora.value = ambience.aurora;
    u.uStarry.value = ambience.starry;
    u.uFinale.value = ambience.finale;
    u.uWarm.value = ambience.warm;
    u.uDim.value = ambience.dim;
    u.uReveal.value = 0.25 + ambience.reveal * 0.75;
    u.uShoot.value = ambience.starry > 0.5 ? (t * 0.45) % 2.2 : 0;
  });

  return (
    <mesh material={material} renderOrder={-10} frustumCulled={false}>
      <sphereGeometry args={[400, 48, 24]} />
    </mesh>
  );
}
