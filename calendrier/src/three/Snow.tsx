import { useFrame, useThree } from '@react-three/fiber';
import { useMemo } from 'react';
import { BufferAttribute, BufferGeometry, ShaderMaterial, Vector3 } from 'three';
import { quality } from '../lib/quality';
import { useApp } from '../store';
import { ambience, layoutRef, shockCenter } from './fx';
import { rng } from './noise';

const vertex = /* glsl */ `
  attribute vec4 aSeed;
  attribute float aLayer;
  uniform float uTime;
  uniform vec2 uWind;
  uniform float uScale;
  uniform float uFocus;
  uniform float uDensity;
  uniform float uShock;
  uniform vec3 uShockCenter;
  uniform vec3 uCenter;
  varying float vAlpha;
  varying float vSoft;

  void main() {
    // Trois plans : loin (0), milieu (1), près de la caméra (2).
    vec3 size = aLayer < 0.5 ? vec3(90.0, 30.0, 40.0) : (aLayer < 1.5 ? vec3(44.0, 22.0, 14.0) : vec3(18.0, 14.0, 10.0));
    vec3 origin = aLayer < 0.5 ? vec3(0.0, 13.0, -14.0) : (aLayer < 1.5 ? vec3(0.0, 9.0, 4.0) : vec3(0.0, 7.0, 16.0));
    origin.x += uCenter.x;
    float fall = mix(0.55, 1.05, aSeed.y) * (aLayer > 1.5 ? 1.25 : 1.0);
    vec3 p = aSeed.xyz * size;
    p.y -= uTime * fall;
    p.x += uWind.x * (0.6 + aSeed.z * 0.6) + sin(uTime * (0.6 + aSeed.w) + aSeed.x * 20.0) * 0.35;
    p.z += uWind.y * 0.4 + cos(uTime * (0.5 + aSeed.y) + aSeed.z * 17.0) * 0.25;
    p = mod(p, size) - size * 0.5 + origin;

    // Onde de choc du final : les flocons sont repoussés par un anneau.
    vec3 rel = p - uShockCenter;
    float dist = length(rel);
    float ring = exp(-pow((dist - uShock) * 0.45, 2.0)) * step(0.01, uShock);
    p += normalize(rel + vec3(0.0001)) * ring * 2.2;

    vec4 mv = modelViewMatrix * vec4(p, 1.0);
    float depth = -mv.z;
    float base = aLayer < 0.5 ? 0.05 : (aLayer < 1.5 ? 0.06 : 0.055);
    base *= mix(0.6, 1.4, aSeed.w);
    float coc = clamp(abs(depth - uFocus) / max(depth, 0.1) * 1.6, 0.0, 1.0);
    vSoft = aLayer > 1.5 ? max(coc, 0.55) : coc * 0.6;
    float px = base * uScale / max(depth, 0.1) * (1.0 + vSoft * 1.8);
    gl_PointSize = clamp(px, 1.0, 64.0);
    gl_Position = projectionMatrix * mv;

    float visible = step(aSeed.w, uDensity);
    float fadeNear = smoothstep(1.2, 3.5, depth);
    vAlpha = visible * fadeNear * mix(0.95, 0.35, vSoft) * (aLayer < 0.5 ? 0.75 : 1.0);
  }
`;

const fragment = /* glsl */ `
  uniform float uReveal;
  varying float vAlpha;
  varying float vSoft;
  void main() {
    float d = length(gl_PointCoord - 0.5) * 2.0;
    float edge = mix(0.15, 1.0, vSoft);
    float a = 1.0 - smoothstep(1.0 - edge, 1.0, d);
    a *= vAlpha * uReveal;
    if (a < 0.01) discard;
    gl_FragColor = vec4(vec3(0.92, 0.95, 1.0), a);
  }
`;

function makeUniforms() {
  return {
    uTime: { value: 0 },
    uWind: { value: { x: 0, y: 0 } },
    uScale: { value: 400 },
    uFocus: { value: 22 },
    uDensity: { value: 0.72 },
    uShock: { value: 0 },
    uShockCenter: { value: shockCenter },
    uCenter: { value: new Vector3() },
    uReveal: { value: 0 },
  };
}

export function Snow() {
  const reduced = useApp((s) => s.reducedMotion);
  const count = reduced ? Math.round(quality.snowCount * 0.6) : quality.snowCount;
  const size = useThree((s) => s.size);
  const camera = useThree((s) => s.camera);

  const geometry = useMemo(() => {
    const random = rng(42);
    const seeds = new Float32Array(count * 4);
    const layers = new Float32Array(count);
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      seeds[i * 4] = random();
      seeds[i * 4 + 1] = random();
      seeds[i * 4 + 2] = random();
      seeds[i * 4 + 3] = random();
      const r = random();
      layers[i] = r < 0.6 ? 0 : r < 0.94 ? 1 : 2;
    }
    const geo = new BufferGeometry();
    geo.setAttribute('position', new BufferAttribute(positions, 3));
    geo.setAttribute('aSeed', new BufferAttribute(seeds, 4));
    geo.setAttribute('aLayer', new BufferAttribute(layers, 1));
    return geo;
  }, [count]);

  const [material, u] = useMemo(() => {
    const uniforms = makeUniforms();
    const mat = new ShaderMaterial({
      vertexShader: vertex,
      fragmentShader: fragment,
      uniforms,
      transparent: true,
      depthWrite: false,
    });
    return [mat, uniforms] as const;
  }, []);

  const sim = useMemo(() => ({ time: 0, wind: { x: 0, y: 0 } }), []);

  useFrame((state, rawDelta) => {
    const delta = Math.min(rawDelta, 0.05);
    const speed = ambience.snowSpeed * (reduced ? 0.4 : 1) * (1 + ambience.blizzard * 1.6);
    const t = state.clock.elapsedTime;
    sim.time += delta * speed;
    // Vent qui tourne : somme de sinus lents, rafales en blizzard.
    const windX = Math.sin(t * 0.11) * 0.7 + Math.sin(t * 0.047 + 1.3) * 0.9 + ambience.blizzard * 7;
    const windZ = Math.cos(t * 0.083) * 0.5;
    sim.wind.x += windX * delta * ambience.snowSpeed * (reduced ? 0.4 : 1);
    sim.wind.y += windZ * delta * ambience.snowSpeed * (reduced ? 0.4 : 1);
    u.uTime.value = sim.time;
    u.uWind.value = sim.wind;
    u.uDensity.value = 0.74 + ambience.blizzard * 0.26 + ambience.finale * 0.1;
    u.uShock.value = ambience.shock;
    u.uReveal.value = 0.35 + ambience.reveal * 0.65;
    const persp = camera as { fov?: number };
    const fov = ((persp.fov ?? 35) * Math.PI) / 180;
    u.uScale.value = (size.height * state.viewport.dpr * 0.5) / Math.tan(fov / 2);
    u.uFocus.value = camera.position.distanceTo(layoutRef.current.camTarget) * 0.85;
    u.uCenter.value.x = layoutRef.current.camTarget.x;
  });

  return <points geometry={geometry} material={material} frustumCulled={false} renderOrder={5} />;
}
