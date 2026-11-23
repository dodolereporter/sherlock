import { useFrame } from '@react-three/fiber';
import { useLayoutEffect, useMemo, useRef } from 'react';
import {
  BufferAttribute,
  BufferGeometry,
  Color,
  ConeGeometry,
  CylinderGeometry,
  DoubleSide,
  InstancedMesh,
  LatheGeometry,
  MeshLambertMaterial,
  MeshStandardMaterial,
  Object3D,
  PlaneGeometry,
  Vector2,
  type Group,
  type Mesh,
  type PointLight,
} from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { quality } from '../lib/quality';
import { ambience, layoutRef } from './fx';
import { createFootprints, createSnowMaterial, sparkleTime } from './materials';
import { fbm2, rng } from './noise';

function groundHeight(x: number, z: number): number {
  const r = Math.hypot(x * 0.8, z);
  const far = Math.min(1, Math.max(0, (r - 9) / 26));
  const drifts = (fbm2(x * 0.07 + 3.1, z * 0.07 - 1.7) - 0.45) * (0.35 + far * 5.5);
  const ripples = (fbm2(x * 0.9, z * 0.9) - 0.5) * 0.06;
  const back = z < -14 ? (z + 14) * -0.06 : 0;
  return drifts + ripples + back * far;
}

function useGround() {
  return useMemo(() => {
    const geo = new PlaneGeometry(220, 220, 130, 130);
    geo.rotateX(-Math.PI / 2);
    const pos = geo.attributes.position as BufferAttribute;
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i);
      const z = pos.getZ(i);
      pos.setY(i, groundHeight(x, z));
    }
    geo.computeVertexNormals();
    return geo;
  }, []);
}

function useKnoll() {
  return useMemo(() => {
    // Butte de neige sous le sapin : profil tourné, sommet aplati, bord irrégulier.
    const pts: Vector2[] = [];
    const steps = 22;
    for (let i = 0; i <= steps; i++) {
      const t = i / steps;
      const radius = 0.001 + Math.pow(t, 0.55) * 1.0 + Math.pow(t, 6) * 0.55;
      const height = 1 - Math.pow(t, 2.6);
      pts.push(new Vector2(radius, height));
    }
    const geo = new LatheGeometry(pts, 64);
    const pos = geo.attributes.position as BufferAttribute;
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i);
      const y = pos.getY(i);
      const z = pos.getZ(i);
      const n = fbm2(x * 2.2 + 5, z * 2.2) - 0.5;
      const edge = 1 - y;
      pos.setXYZ(i, x * (1 + n * 0.25 * edge), y + n * 0.05, z * (1 + n * 0.25 * edge));
    }
    geo.computeVertexNormals();
    return geo;
  }, []);
}

function ridgeGeometry(seed: number, width: number, height: number, snowLine: number, rockColor: string) {
  const segments = 220;
  const random = rng(seed);
  const offset = random() * 100;
  const positions: number[] = [];
  const colors: number[] = [];
  const indices: number[] = [];
  const rock = new Color(rockColor);
  const snow = new Color('#c9d7ea');
  const tmp = new Color();
  for (let i = 0; i <= segments; i++) {
    const t = i / segments;
    const x = (t - 0.5) * width;
    const peak = Math.pow(fbm2(t * 7 + offset, seed * 0.13, 5), 1.6) * height * 2.1;
    const top = peak + height * 0.15;
    positions.push(x, top, 0, x, -4, 0);
    const snowAmount = Math.min(1, Math.max(0, (top - snowLine) / (height * 0.5)));
    tmp.copy(rock).lerp(snow, 0.35 + snowAmount * 0.65);
    colors.push(tmp.r, tmp.g, tmp.b, rock.r, rock.g, rock.b);
    if (i < segments) {
      const a = i * 2;
      indices.push(a, a + 1, a + 2, a + 1, a + 3, a + 2);
    }
  }
  const geo = new BufferGeometry();
  geo.setAttribute('position', new BufferAttribute(new Float32Array(positions), 3));
  geo.setAttribute('color', new BufferAttribute(new Float32Array(colors), 3));
  geo.setIndex(indices);
  geo.computeVertexNormals();
  return geo;
}

function pineGeometry() {
  const parts: BufferGeometry[] = [];
  const tiers = [
    { r: 1.25, h: 1.9, y: 1.35 },
    { r: 0.98, h: 1.65, y: 2.35 },
    { r: 0.7, h: 1.4, y: 3.25 },
    { r: 0.42, h: 1.05, y: 4.0 },
  ];
  const trunk = new CylinderGeometry(0.14, 0.2, 1.0, 6);
  trunk.translate(0, 0.5, 0);
  parts.push(trunk);
  for (const tier of tiers) {
    const cone = new ConeGeometry(tier.r, tier.h, 9, 1);
    cone.translate(0, tier.y, 0);
    parts.push(cone);
  }
  const nonIndexed = parts.map((p) => p.toNonIndexed());
  const geo = mergeGeometries(nonIndexed);
  geo.computeVertexNormals();
  const normal = geo.attributes.normal as BufferAttribute;
  const pos = geo.attributes.position as BufferAttribute;
  const colors = new Float32Array(pos.count * 3);
  const needle = new Color('#1d3a33');
  const snow = new Color('#dfe8f3');
  const bark = new Color('#2a2220');
  const c = new Color();
  for (let i = 0; i < pos.count; i++) {
    const y = pos.getY(i);
    const ny = normal.getY(i);
    if (y < 1.0) c.copy(bark);
    else c.copy(needle).lerp(snow, Math.min(1, Math.max(0, (ny - 0.25) * 2.2)));
    colors[i * 3] = c.r;
    colors[i * 3 + 1] = c.g;
    colors[i * 3 + 2] = c.b;
  }
  geo.setAttribute('color', new BufferAttribute(colors, 3));
  return geo;
}

function Forest() {
  const ref = useRef<InstancedMesh>(null);
  const geometry = useMemo(() => pineGeometry(), []);
  const material = useMemo(() => new MeshLambertMaterial({ vertexColors: true }), []);
  const count = quality.forestCount;
  useLayoutEffect(() => {
    const mesh = ref.current;
    if (!mesh) return;
    const random = rng(7);
    const o = new Object3D();
    let placed = 0;
    let guard = 0;
    while (placed < count && guard < 4000) {
      guard++;
      const x = (random() - 0.5) * 120;
      const z = -9 - random() * 55;
      // Clairière dégagée derrière le sapin pour garder la silhouette lisible.
      if (Math.abs(x) < 12 && z > -20) continue;
      const s = 0.8 + random() * 1.2 + Math.max(0, -z - 20) * 0.02;
      o.position.set(x, groundHeight(x, z) - 0.2, z);
      o.rotation.set(0, random() * Math.PI * 2, 0);
      o.scale.set(s, s * (0.9 + random() * 0.5), s);
      o.updateMatrix();
      mesh.setMatrixAt(placed, o.matrix);
      placed++;
    }
    // Deux grands sapins de premier plan qui encadrent l'image.
    const frame = [
      { x: -17, z: 4, s: 2.4 },
      { x: 15.5, z: 3, s: 2.1 },
    ];
    for (const f of frame) {
      if (placed >= count) break;
      o.position.set(f.x, groundHeight(f.x, f.z) - 0.3, f.z);
      o.rotation.set(0, 0.4, 0);
      o.scale.setScalar(f.s);
      o.updateMatrix();
      mesh.setMatrixAt(placed, o.matrix);
      placed++;
    }
    mesh.count = placed;
    mesh.instanceMatrix.needsUpdate = true;
    mesh.computeBoundingSphere();
  }, [count]);
  return <instancedMesh ref={ref} args={[geometry, material, count + 2]} receiveShadow />;
}

function Mountains() {
  const ridges = useMemo(
    () => [
      { geo: ridgeGeometry(3, 520, 34, 26, '#24364f'), z: -230, y: -2 },
      { geo: ridgeGeometry(11, 420, 22, 16, '#1d2c42'), z: -150, y: -3 },
      { geo: ridgeGeometry(29, 300, 12, 9, '#16233a'), z: -85, y: -2.5 },
    ],
    [],
  );
  const material = useMemo(() => new MeshLambertMaterial({ vertexColors: true, side: DoubleSide }), []);
  return (
    <group>
      {ridges.map((r) => (
        <mesh key={r.z} geometry={r.geo} material={material} position={[0, r.y, r.z]} />
      ))}
    </group>
  );
}

function Lantern({ side }: { side: -1 | 1 }) {
  const group = useRef<Group>(null);
  const light = useRef<PointLight>(null);
  const glass = useMemo(
    () => new MeshStandardMaterial({ color: '#ffcf8a', emissive: new Color('#ffad4d'), emissiveIntensity: 3.2, roughness: 0.4 }),
    [],
  );
  const iron = useMemo(() => new MeshStandardMaterial({ color: '#1a1b20', roughness: 0.6, metalness: 0.5 }), []);
  useFrame((state) => {
    const l = layoutRef.current;
    const g = group.current;
    if (!g) return;
    if (l.portrait) g.position.set(side * 3.3, 0, 4.4);
    else if (side < 0) g.position.set(l.sherlockPos.x - 2.3, 0, l.sherlockPos.z - 1.6);
    else g.position.set(l.treeOffset.x + 5.1, 0, 1.3);
    const t = state.clock.elapsedTime;
    const flicker = 0.92 + Math.sin(t * 7.3 + side) * 0.04 + Math.sin(t * 13.1) * 0.03;
    const boost = 1 + ambience.warm * 1.4 + ambience.finale * 0.6;
    const level = flicker * boost * (1 - ambience.dim * 0.7) * ambience.reveal;
    if (light.current) light.current.intensity = (l.portrait ? 12 : 24) * level;
    glass.emissiveIntensity = 3.2 * level;
  });
  return (
    <group ref={group}>
      <mesh position={[0, 1.15, 0]} material={iron} castShadow>
        <cylinderGeometry args={[0.06, 0.08, 2.3, 8]} />
      </mesh>
      <mesh position={[0, 2.45, 0]} material={glass}>
        <cylinderGeometry args={[0.2, 0.17, 0.42, 6]} />
      </mesh>
      <mesh position={[0, 2.72, 0]} material={iron} castShadow>
        <coneGeometry args={[0.3, 0.22, 6]} />
      </mesh>
      <pointLight ref={light} position={[0, 2.45, 0.25]} color="#ffb45e" intensity={24} distance={18} decay={1.7} />
    </group>
  );
}

export function Landscape() {
  const ground = useGround();
  const knollGeo = useKnoll();
  const prints = useMemo(() => createFootprints(), []);
  const snow = useMemo(() => createSnowMaterial(undefined, prints), [prints]);
  const knollSnow = useMemo(() => createSnowMaterial(), []);
  const knoll = useRef<Mesh>(null);

  useFrame((state) => {
    sparkleTime.value = state.clock.elapsedTime;
    const k = knoll.current;
    if (!k) return;
    const l = layoutRef.current;
    prints.rect.x = l.sherlockPos.x;
    prints.rect.y = l.sherlockPos.z;
    const height = l.treeOffset.y + 0.02;
    k.position.set(l.treeOffset.x, -0.05, l.treeOffset.z + 0.2);
    k.scale.set(l.portrait ? 3.8 : 3.4, height + 0.05, l.portrait ? 2.6 : 2.1);
  });

  return (
    <group>
      <mesh geometry={ground} material={snow} receiveShadow />
      <mesh ref={knoll} geometry={knollGeo} material={knollSnow} receiveShadow castShadow />
      <Mountains />
      <Forest />
      <Lantern side={-1} />
      <Lantern side={1} />
    </group>
  );
}
