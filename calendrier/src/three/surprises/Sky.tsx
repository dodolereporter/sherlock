import { useFrame } from '@react-three/fiber';
import gsap from 'gsap';
import { useEffect, useLayoutEffect, useMemo, useRef } from 'react';
import {
  AdditiveBlending,
  BufferAttribute,
  Color,
  CylinderGeometry,
  DoubleSide,
  InstancedBufferAttribute,
  Matrix4,
  Mesh,
  MeshBasicMaterial,
  PlaneGeometry,
  Quaternion,
  ShaderMaterial,
  Vector3,
  type Group,
  type InstancedMesh,
} from 'three';
import { useApp } from '../../store';
import { ambience, layoutRef } from '../fx';
import { starGeometry } from '../geometries';
import { slotWorld } from '../layout';
import { rng } from '../noise';
import { burst } from '../sparklePool';

const LANTERNS = 40;
const AXIS_Z = new Vector3(0, 0, 1);

/** Lanternes de papier qui s'envolent depuis la clairière. */
export function Lanterns() {
  const ref = useRef<InstancedMesh>(null);
  const closing = useApp((s) => s.phase === 'closing');
  const reduced = useApp((s) => s.reducedMotion);
  const geo = useMemo(() => {
    // Papier éclairé par la flamme du bas : dégradé de luminosité du bas vers le haut.
    const g = new CylinderGeometry(0.2, 0.15, 0.42, 10, 4, true);
    const pos = g.attributes.position as BufferAttribute;
    const colors = new Float32Array(pos.count * 3);
    for (let i = 0; i < pos.count; i++) {
      const k = 1 - ((pos.getY(i) + 0.21) / 0.42) * 0.6;
      colors.set([k, k * k, k * k * k], i * 3);
    }
    g.setAttribute('color', new BufferAttribute(colors, 3));
    return g;
  }, []);
  const mat = useMemo(() => new MeshBasicMaterial({ toneMapped: false, side: DoubleSide, fog: false, vertexColors: true }), []);
  const seeds = useMemo(() => {
    const r = rng(21);
    return Array.from({ length: LANTERNS }, () => ({
      x: (r() - 0.5) * 16,
      z: r() * 5 + 1,
      delay: r() * 2.6,
      speed: 1.0 + r() * 0.7,
      sway: r() * Math.PI * 2,
      size: 0.9 + r() * 0.6,
    }));
  }, []);
  const s = useMemo(() => ({ t: 0, start: -1, fade: 1 }), []);
  const m = useMemo(() => new Matrix4(), []);
  const q = useMemo(() => new Quaternion(), []);
  const p = useMemo(() => new Vector3(), []);
  const sc = useMemo(() => new Vector3(), []);
  const c = useMemo(() => new Color(), []);

  useEffect(() => {
    const tw = gsap.to(ambience, { warm: 0.8, duration: 3, ease: 'sine.inOut' });
    return () => {
      tw.kill();
      geo.dispose();
      mat.dispose();
    };
  }, [geo, mat]);

  useEffect(() => {
    if (!closing) return;
    const tw = gsap.to(s, { fade: 0, duration: 0.8, ease: 'power2.in' });
    return () => {
      tw.kill();
    };
  }, [closing, s]);

  useLayoutEffect(() => {
    const mesh = ref.current;
    if (mesh && !mesh.instanceColor) mesh.instanceColor = new InstancedBufferAttribute(new Float32Array(LANTERNS * 3), 3);
  }, []);

  useFrame((frame) => {
    const mesh = ref.current;
    if (!mesh) return;
    const t = frame.clock.elapsedTime;
    // Temps écoulé réel (et non des pas plafonnés) : la montée reste juste même à faible cadence.
    if (s.start < 0) s.start = t;
    s.t = (t - s.start) * (reduced ? 0.5 : 1);
    const l = layoutRef.current;
    seeds.forEach((d, i) => {
      const age = Math.max(0, s.t - d.delay);
      const h = age * d.speed;
      p.set(l.camTarget.x + d.x + Math.sin(age * 0.6 + d.sway) * 0.6 + age * 0.25, 1.0 + h, d.z - h * 0.6);
      const born = Math.min(1, age * 2);
      sc.setScalar(Math.max(0.0001, d.size * born * s.fade));
      q.setFromAxisAngle(AXIS_Z, Math.sin(age * 0.8 + d.sway) * 0.12);
      m.compose(p, q, sc);
      mesh.setMatrixAt(i, m);
      const flicker = 0.85 + Math.sin(t * 9 + i) * 0.08 + Math.sin(t * 13.7 + i * 2) * 0.07;
      const k = 2.2 * flicker * born * Math.max(0, 1 - h / 45);
      c.setRGB(1.0 * k, 0.5 * k, 0.14 * k);
      mesh.setColorAt(i, c);
    });
    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
  });

  return <instancedMesh ref={ref} args={[geo, mat, LANTERNS]} frustumCulled={false} />;
}

const PALETTES = [
  ['#ffd38a', '#ffb45e', '#fff4dc'],
  ['#ff8fa0', '#e04a5f', '#ffe1e6'],
  ['#9fd0ff', '#d9ecff', '#ffffff'],
  ['#8ff0b8', '#3fcf8e', '#e6fff1'],
];

/** Feu d'artifice : fusées (traînées) puis gerbes, tout dans le même nuage de particules. */
export function Fireworks({ finale = false }: { finale?: boolean }) {
  const reduced = useApp((s) => s.reducedMotion);
  const rockets = useRef<{ from: Vector3; to: Vector3; start: number; dur: number; palette: number; done: boolean }[]>([]);
  const clock = useRef({ t: 0, start: -1, next: 0.2, count: 0 });

  useFrame((frame) => {
    const c = clock.current;
    if (c.start < 0) c.start = frame.clock.elapsedTime;
    c.t = frame.clock.elapsedTime - c.start;
    const l = layoutRef.current;
    if (c.t > c.next) {
      const x = l.camTarget.x + (Math.random() - 0.5) * (l.portrait ? 8 : 24);
      rockets.current.push({
        from: new Vector3(x * 0.7, 0.5, -4 - Math.random() * 3),
        to: new Vector3(x, (l.portrait ? 15 : 12) + Math.random() * 5, -5 - Math.random() * 4),
        start: c.t,
        dur: 0.9 + Math.random() * 0.4,
        palette: c.count % PALETTES.length,
        done: false,
      });
      c.count++;
      // Salve serrée au début, puis un rythme plus posé tant que la case reste ouverte.
      const pace = c.count < (finale ? 14 : 8) ? 0.3 + Math.random() * 0.35 : 0.9 + Math.random() * 0.8;
      c.next = c.t + (reduced ? 1.6 : pace);
    }
    for (const r of rockets.current) {
      if (r.done) continue;
      const k = (c.t - r.start) / r.dur;
      if (k >= 1) {
        r.done = true;
        const colors = PALETTES[r.palette] ?? PALETTES[0];
        burst(r.to, { count: reduced ? 90 : 220, speed: 10, colors, life: [1.6, 2.8], size: [0.45, 1.0], up: 0, spread: [1, 1, 0.6] });
        burst(r.to, { count: 30, speed: 2, colors: ['#ffffff'], life: [0.3, 0.6], size: [1.2, 2.0], up: 0 });
        ambience.flash = Math.max(ambience.flash, reduced ? 0.05 : 0.18);
        gsap.to(ambience, { flash: 0, duration: 0.8, ease: 'expo.out', overwrite: true });
        continue;
      }
      const e = 1 - Math.pow(1 - k, 2);
      const pos = r.from.clone().lerp(r.to, e);
      burst(pos, { count: 3, speed: 0.3, colors: ['#ffe7b8', '#ffb45e'], life: [0.35, 0.7], size: [0.25, 0.45], up: -0.2 });
    }
    rockets.current = rockets.current.filter((r) => !r.done || c.t - r.start < 3);
  });
  return null;
}

const rayVertex = /* glsl */ `
  varying vec2 vUv;
  void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }
`;
const rayFragment = /* glsl */ `
  uniform float uTime;
  uniform float uOpacity;
  varying vec2 vUv;
  void main() {
    vec2 p = vUv - 0.5;
    float r = length(p);
    float a = atan(p.y, p.x);
    float rays = pow(0.5 + 0.5 * sin(a * 12.0 + uTime * 0.6), 6.0) + pow(0.5 + 0.5 * sin(a * 7.0 - uTime * 0.4), 8.0) * 0.6;
    float fall = smoothstep(0.5, 0.05, r);
    float core = exp(-r * r * 60.0);
    vec3 col = vec3(1.0, 0.78, 0.45) * (rays * fall * 1.4 + core * 3.0);
    gl_FragColor = vec4(col * uOpacity, 1.0);
  }
`;

/** L'étoile du final : elle sort de la case 24, grandit au-dessus du sapin, rayonne. */
export function GrandStar() {
  const group = useRef<Group>(null);
  const reduced = useApp((s) => s.reducedMotion);
  const closing = useApp((s) => s.phase === 'closing');
  const s = useMemo(() => ({ rise: 0 }), []);
  const parts = useMemo(() => {
    const geo = starGeometry(0.9, 0.4, 0.22);
    const mat = new MeshBasicMaterial({ color: new Color('#ffcf7a').multiplyScalar(2.2), toneMapped: false });
    const uniforms = { uTime: { value: 0 }, uOpacity: { value: 0 } };
    const rayMat = new ShaderMaterial({
      vertexShader: rayVertex,
      fragmentShader: rayFragment,
      uniforms,
      transparent: true,
      depthWrite: false,
      blending: AdditiveBlending,
    });
    const star = new Mesh(geo, mat);
    const rays = new Mesh(new PlaneGeometry(9, 9), rayMat);
    rays.position.z = -0.3;
    return { star, rays, rayMat, uniforms };
  }, []);

  useEffect(() => {
    const tw = gsap.to(s, { rise: 1, duration: reduced ? 1.2 : 2.6, ease: reduced ? 'sine.inOut' : 'expo.out' });
    return () => {
      tw.kill();
      parts.star.geometry.dispose();
      (parts.star.material as MeshBasicMaterial).dispose();
      parts.rays.geometry.dispose();
      parts.rayMat.dispose();
    };
  }, [s, reduced, parts]);

  useEffect(() => {
    if (!closing) return;
    const tw = gsap.to(s, { rise: 0, duration: 0.9, ease: 'power3.in' });
    return () => {
      tw.kill();
    };
  }, [closing, s]);

  const from = useMemo(() => new Vector3(), []);
  useFrame((frame) => {
    const g = group.current;
    if (!g) return;
    const t = frame.clock.elapsedTime;
    slotWorld(24, layoutRef.current, from);
    g.position.set(from.x, from.y + s.rise * 2.6, from.z + 0.8 + s.rise * 0.4);
    g.scale.setScalar(Math.max(0.0001, s.rise * 1.25));
    parts.star.rotation.y = t * (reduced ? 0.4 : 1.1);
    parts.star.rotation.z = Math.sin(t * 0.8) * 0.08;
    parts.rays.lookAt(frame.camera.position);
    parts.uniforms.uTime.value = t;
    parts.uniforms.uOpacity.value = s.rise * (0.85 + Math.sin(t * 2.2) * 0.15);
  });

  return (
    <group ref={group}>
      <primitive object={parts.rays} />
      <primitive object={parts.star} />
    </group>
  );
}
