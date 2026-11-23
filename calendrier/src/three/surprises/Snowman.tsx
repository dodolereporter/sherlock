import { useFrame } from '@react-three/fiber';
import gsap from 'gsap';
import { useEffect, useMemo, useRef } from 'react';
import {
  BufferAttribute,
  ConeGeometry,
  CylinderGeometry,
  IcosahedronGeometry,
  MeshStandardMaterial,
  SphereGeometry,
  TorusGeometry,
  Vector3,
  type Group,
} from 'three';
import { useApp } from '../../store';
import { layoutRef } from '../fx';
import { createSnowMaterial } from '../materials';
import { fbm2 } from '../noise';
import { burst } from '../sparklePool';
import { sherlock } from '../sherlockApi';

function lumpySphere(r: number, seed: number) {
  const g = new IcosahedronGeometry(r, 5);
  const pos = g.attributes.position as BufferAttribute;
  for (let i = 0; i < pos.count; i++) {
    const v = new Vector3(pos.getX(i), pos.getY(i), pos.getZ(i));
    const n = fbm2(v.x * 3 + seed, v.z * 3 + v.y * 2) - 0.5;
    v.multiplyScalar(1 + n * 0.08);
    pos.setXYZ(i, v.x, v.y, v.z);
  }
  g.computeVertexNormals();
  return g;
}

function snowmanPosition(out = new Vector3()): Vector3 {
  const l = layoutRef.current;
  return l.portrait ? out.set(2.7, 0, 3.6) : out.set(l.treeOffset.x - 3.4, 0, 3.9);
}

/** Le bonhomme de neige se construit tout seul : boules qui tombent et s'écrasent, puis détails en cascade. */
export function Snowman() {
  const root = useRef<Group>(null);
  const reduced = useApp((s) => s.reducedMotion);
  const closing = useApp((s) => s.phase === 'closing');
  const parts = useMemo(
    () => ({
      snow: createSnowMaterial('#e6edf6'),
      coal: new MeshStandardMaterial({ color: '#16171b', roughness: 0.5 }),
      carrot: new MeshStandardMaterial({ color: '#e0701e', roughness: 0.55 }),
      scarf: new MeshStandardMaterial({ color: '#8e2a36', roughness: 0.85 }),
      twig: new MeshStandardMaterial({ color: '#4a3326', roughness: 0.9 }),
      hat: new MeshStandardMaterial({ color: '#1d2230', roughness: 0.6 }),
      base: lumpySphere(0.95, 1),
      mid: lumpySphere(0.7, 2),
      head: lumpySphere(0.5, 3),
      eye: new SphereGeometry(0.055, 10, 8),
      nose: new ConeGeometry(0.07, 0.42, 12),
      ring: new TorusGeometry(0.5, 0.11, 10, 28),
      arm: new CylinderGeometry(0.03, 0.045, 1.1, 6),
      brim: new CylinderGeometry(0.48, 0.48, 0.05, 28),
      crown: new CylinderGeometry(0.32, 0.34, 0.5, 28),
    }),
    [],
  );
  const s = useMemo(
    () => ({ b1: 0, b2: 0, b3: 0, sq1: 0, sq2: 0, sq3: 0, eyes: 0, nose: 0, scarf: 0, arms: 0, hat: 0, hatY: 0, all: 1 }),
    [],
  );

  useEffect(() => {
    const at = snowmanPosition();
    sherlock.lookAt(at.clone().add(new Vector3(0, 1.5, 0)));
    sherlock.play([{ name: 'alerte' }, { name: 'enquete_entree' }, { name: 'enquete' }, { name: 'enquete_sortie' }, { name: 'reussite' }]);
    const tl = gsap.timeline();
    if (reduced) {
      tl.to(s, { b1: 1, b2: 1, b3: 1, eyes: 1, nose: 1, scarf: 1, arms: 1, hat: 1, duration: 1.2, ease: 'sine.inOut' });
      return () => {
        tl.kill();
      };
    }
    const drop = (k: 1 | 2 | 3, time: number, y: number) => {
      const key = `b${k}` as const;
      const sq = `sq${k}` as const;
      tl.fromTo(s, { [key]: 0 }, { [key]: 1, duration: 0.55, ease: 'power2.in' }, time);
      tl.to(s, { [sq]: 1, duration: 0.08, ease: 'power2.out' }, time + 0.55);
      tl.to(s, { [sq]: 0, duration: 0.7, ease: 'elastic.out(1, 0.35)' }, time + 0.63);
      tl.call(
        () =>
          burst(at.clone().add(new Vector3(0, y, 0.3)), {
            count: 50,
            speed: 1.8,
            colors: ['#ffffff', '#dfeaff'],
            life: [0.5, 1.0],
            size: [0.06, 0.14],
            up: 0.3,
            spread: [1.4, 0.4, 1.4],
          }),
        [],
        time + 0.55,
      );
    };
    drop(1, 0.2, 0.3);
    drop(2, 0.75, 1.35);
    drop(3, 1.3, 2.2);
    tl.to(s, { eyes: 1, duration: 0.45, ease: 'back.out(3)' }, 2.1);
    tl.to(s, { nose: 1, duration: 0.5, ease: 'back.out(2.5)' }, 2.3);
    tl.to(s, { scarf: 1, duration: 0.7, ease: 'elastic.out(1, 0.5)' }, 2.45);
    tl.to(s, { arms: 1, duration: 0.6, ease: 'back.out(2)' }, 2.65);
    tl.fromTo(s, { hat: 1, hatY: 3 }, { hatY: 0, duration: 0.7, ease: 'bounce.out' }, 2.8);
    return () => {
      tl.kill();
    };
  }, [s, reduced]);

  useEffect(() => {
    if (!closing) return;
    const t = gsap.to(s, { all: 0, duration: 0.5, ease: 'back.in(2)' });
    return () => {
      t.kill();
    };
  }, [closing, s]);

  useEffect(
    () => () => {
      Object.values(parts).forEach((p) => p.dispose());
    },
    [parts],
  );

  const pos = useMemo(() => new Vector3(), []);
  useFrame(() => {
    const g = root.current;
    if (!g) return;
    snowmanPosition(pos);
    g.position.copy(pos);
    g.scale.setScalar(Math.max(0.0001, s.all));
    g.rotation.y = layoutRef.current.portrait ? -0.3 : -0.45;
    const [base, mid, head, details] = g.children;
    const place = (o: typeof base, k: number, sq: number, y: number, fall: number) => {
      if (!o) return;
      o.visible = k > 0.001;
      o.position.y = y + (1 - k) * fall;
      o.scale.set(1 + sq * 0.25, Math.max(0.0001, 1 - sq * 0.3), 1 + sq * 0.25);
    };
    place(base, s.b1, s.sq1, 0.82, 9);
    place(mid, s.b2, s.sq2, 2.0, 9);
    place(head, s.b3, s.sq3, 2.92, 9);
    if (details) {
      details.position.y = 0;
      const [eyes, nose, scarf, arms, hat] = details.children;
      if (eyes) eyes.scale.setScalar(Math.max(0.0001, s.eyes));
      if (nose) nose.scale.set(1, Math.max(0.0001, s.nose), 1);
      if (scarf) scarf.scale.setScalar(Math.max(0.0001, s.scarf));
      if (arms) arms.scale.setScalar(Math.max(0.0001, s.arms));
      if (hat) {
        hat.visible = s.hat > 0;
        hat.position.y = s.hatY;
      }
    }
  });

  return (
    <group ref={root}>
      <mesh geometry={parts.base} material={parts.snow} castShadow receiveShadow />
      <mesh geometry={parts.mid} material={parts.snow} castShadow receiveShadow />
      <mesh geometry={parts.head} material={parts.snow} castShadow receiveShadow />
      <group>
        <group position={[0, 2.98, 0.44]}>
          <mesh geometry={parts.eye} material={parts.coal} position={[-0.16, 0.06, 0]} />
          <mesh geometry={parts.eye} material={parts.coal} position={[0.16, 0.06, 0]} />
          {[-0.2, -0.1, 0, 0.1, 0.2].map((x) => (
            <mesh
              key={x}
              geometry={parts.eye}
              material={parts.coal}
              scale={0.6}
              position={[x, -0.2 - (0.04 - Math.abs(x) * 0.25), -0.02]}
            />
          ))}
        </group>
        <group position={[0, 2.9, 0.46]}>
          <mesh geometry={parts.nose} material={parts.carrot} rotation={[Math.PI / 2, 0, 0]} position={[0, 0, 0.18]} castShadow />
        </group>
        <group position={[0, 2.5, 0]}>
          <mesh geometry={parts.ring} material={parts.scarf} rotation={[Math.PI / 2, 0, 0]} castShadow />
          <mesh
            geometry={parts.arm}
            material={parts.scarf}
            scale={[3.2, 0.5, 2]}
            position={[0.3, -0.35, 0.42]}
            rotation={[0.2, 0, 0.25]}
            castShadow
          />
        </group>
        <group position={[0, 2.1, 0]}>
          <mesh geometry={parts.arm} material={parts.twig} position={[-0.95, 0.25, 0]} rotation={[0, 0, 1.0]} castShadow />
          <mesh geometry={parts.arm} material={parts.twig} position={[0.95, 0.35, 0]} rotation={[0, 0, -1.25]} castShadow />
        </group>
        <group>
          <group position={[0, 3.36, 0]} rotation={[0, 0, -0.12]}>
            <mesh geometry={parts.brim} material={parts.hat} castShadow />
            <mesh geometry={parts.crown} material={parts.hat} position={[0, 0.27, 0]} castShadow />
          </group>
        </group>
      </group>
    </group>
  );
}
