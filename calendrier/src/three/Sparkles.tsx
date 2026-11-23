import { useFrame } from '@react-three/fiber';
import { useMemo } from 'react';
import { AdditiveBlending, BufferAttribute, BufferGeometry, ShaderMaterial } from 'three';
import { pool, POOL } from './sparklePool';

const vertex = /* glsl */ `
  attribute vec3 aVel;
  attribute vec3 aColor;
  attribute vec3 aLife; // naissance, durée, taille
  uniform float uTime;
  uniform float uScale;
  varying vec3 vColor;
  varying float vAlpha;
  void main() {
    float age = uTime - aLife.x;
    float k = clamp(age / aLife.y, 0.0, 1.0);
    float alive = step(0.0, age) * step(age, aLife.y);
    // Traînée : vitesse amortie, gravité légère, petite dérive.
    float drag = (1.0 - exp(-age * 2.2)) / 2.2;
    vec3 p = position + aVel * drag + vec3(0.0, -0.9, 0.0) * age * age * 0.5;
    vec4 mv = modelViewMatrix * vec4(p, 1.0);
    float twinkle = 0.65 + 0.35 * sin(age * 30.0 + aLife.z * 50.0);
    gl_PointSize = alive * aLife.z * uScale / max(-mv.z, 0.1) * (1.0 - k * 0.6);
    gl_Position = projectionMatrix * mv;
    vColor = aColor;
    vAlpha = alive * (1.0 - k * k) * twinkle;
  }
`;

const fragment = /* glsl */ `
  varying vec3 vColor;
  varying float vAlpha;
  void main() {
    vec2 c = gl_PointCoord - 0.5;
    float d = length(c) * 2.0;
    float core = exp(-d * d * 7.0);
    float cross = exp(-abs(c.x) * 40.0) * exp(-abs(c.y) * 5.0) + exp(-abs(c.y) * 40.0) * exp(-abs(c.x) * 5.0);
    float a = (core + cross * 0.45) * vAlpha;
    if (a < 0.01) discard;
    gl_FragColor = vec4(vColor * a, a);
  }
`;

export function Sparkles() {
  const [geometry, material, uniforms] = useMemo(() => {
    const geo = new BufferGeometry();
    geo.setAttribute('position', new BufferAttribute(new Float32Array(POOL * 3), 3));
    geo.setAttribute('aVel', new BufferAttribute(new Float32Array(POOL * 3), 3));
    geo.setAttribute('aColor', new BufferAttribute(new Float32Array(POOL * 3), 3));
    const life = new Float32Array(POOL * 3);
    for (let i = 0; i < POOL; i++) life[i * 3] = -100;
    geo.setAttribute('aLife', new BufferAttribute(life, 3));
    const u = { uTime: { value: 0 }, uScale: { value: 500 } };
    const mat = new ShaderMaterial({
      vertexShader: vertex,
      fragmentShader: fragment,
      uniforms: u,
      transparent: true,
      depthWrite: false,
      blending: AdditiveBlending,
      toneMapped: false,
    });
    return [geo, mat, u] as const;
  }, []);

  useFrame((state) => {
    pool.geometry = geometry;
    pool.time = state.clock.elapsedTime;
    uniforms.uTime.value = pool.time;
    const cam = state.camera as { fov?: number };
    uniforms.uScale.value = (state.size.height * state.viewport.dpr * 0.5) / Math.tan(((cam.fov ?? 35) * Math.PI) / 360);
  });

  return <points geometry={geometry} material={material} frustumCulled={false} renderOrder={8} />;
}
