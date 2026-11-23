import { useFrame } from '@react-three/fiber';
import gsap from 'gsap';
import { useEffect, useLayoutEffect, useMemo, useRef } from 'react';
import {
  BoxGeometry,
  Color,
  CylinderGeometry,
  Group,
  InstancedMesh,
  Matrix4,
  Mesh,
  MeshStandardMaterial,
  Quaternion,
  SphereGeometry,
  TorusGeometry,
  Vector3,
  type Material,
} from 'three';
import { useApp } from '../../store';
import { layoutRef } from '../fx';
import { burst } from '../sparklePool';
import { sherlock } from '../sherlockApi';

const SLEEPERS = 72;

function trackParams() {
  const l = layoutRef.current;
  const center = new Vector3(l.treeOffset.x, 0.03, l.treeOffset.z + 0.6);
  return { center, rx: l.portrait ? 5.0 : 5.6, rz: l.portrait ? 3.3 : 3.1 };
}

function ellipsePoint(u: number, out: Vector3) {
  const { center, rx, rz } = trackParams();
  return out.set(center.x + Math.cos(u) * rx, center.y, center.z + Math.sin(u) * rz);
}

function car(body: string, kind: 'loco' | 'wagon'): Group {
  const g = new Group();
  const paint = new MeshStandardMaterial({ color: body, roughness: 0.45, metalness: 0.2 });
  const dark = new MeshStandardMaterial({ color: '#1b1d22', roughness: 0.6, metalness: 0.5 });
  const brass = new MeshStandardMaterial({ color: '#d9a956', roughness: 0.3, metalness: 0.9 });
  const add = (m: Mesh) => {
    m.castShadow = true;
    g.add(m);
    return m;
  };
  add(new Mesh(new BoxGeometry(1.25, 0.12, 0.62), dark)).position.y = 0.26;
  if (kind === 'loco') {
    const boiler = add(new Mesh(new CylinderGeometry(0.24, 0.24, 0.8, 20), paint));
    boiler.rotation.z = Math.PI / 2;
    boiler.position.set(0.16, 0.56, 0);
    const cab = add(new Mesh(new BoxGeometry(0.42, 0.62, 0.56), paint));
    cab.position.set(-0.4, 0.64, 0);
    const roof = add(new Mesh(new BoxGeometry(0.52, 0.06, 0.66), dark));
    roof.position.set(-0.4, 0.98, 0);
    const chimney = add(new Mesh(new CylinderGeometry(0.09, 0.06, 0.32, 12), dark));
    chimney.position.set(0.42, 0.9, 0);
    chimney.name = 'chimney';
    const band = add(new Mesh(new TorusGeometry(0.245, 0.02, 8, 24), brass));
    band.rotation.y = Math.PI / 2;
    band.position.set(0.0, 0.56, 0);
    const lamp = new Mesh(
      new SphereGeometry(0.07, 12, 8),
      new MeshStandardMaterial({ color: '#ffe0a8', emissive: new Color('#ffb45e'), emissiveIntensity: 6 }),
    );
    lamp.position.set(0.58, 0.62, 0);
    g.add(lamp);
  } else {
    const tub = add(new Mesh(new BoxGeometry(1.05, 0.36, 0.56), paint));
    tub.position.y = 0.5;
    // Chargement : petits cadeaux.
    const colors = ['#e7dac2', '#2b5547', '#e8b964'];
    colors.forEach((c, i) => {
      const gift = add(new Mesh(new BoxGeometry(0.26, 0.24, 0.26), new MeshStandardMaterial({ color: c, roughness: 0.6 })));
      gift.position.set(-0.3 + i * 0.3, 0.8, (i % 2) * 0.08 - 0.04);
      gift.rotation.y = i * 0.5;
    });
  }
  const wheelGeo = new CylinderGeometry(0.13, 0.13, 0.06, 16);
  for (const x of [-0.38, 0.38]) {
    for (const z of [-0.31, 0.31]) {
      const w = add(new Mesh(wheelGeo, brass));
      w.rotation.x = Math.PI / 2;
      w.position.set(x, 0.14, z);
      w.name = 'wheel';
    }
  }
  return g;
}

/** Le petit train : les rails se posent, puis il fait le tour du sapin en fumant. */
export function Train() {
  const reduced = useApp((s) => s.reducedMotion);
  const closing = useApp((s) => s.phase === 'closing');
  const sleepers = useRef<InstancedMesh>(null);
  const rails = useRef<InstancedMesh>(null);
  const cars = useMemo(() => [car('#8e2a36', 'loco'), car('#2b5547', 'wagon'), car('#8e2a36', 'wagon')], []);
  const state = useMemo(() => ({ track: 0, u: -Math.PI * 0.95, speed: 0, show: 0, nextPuff: 0 }), []);
  const mats = useMemo(
    () => ({
      wood: new MeshStandardMaterial({ color: '#4a3326', roughness: 0.9 }),
      steel: new MeshStandardMaterial({ color: '#9aa4b3', roughness: 0.35, metalness: 0.9 }),
    }),
    [],
  );
  const geos = useMemo(() => ({ sleeper: new BoxGeometry(0.16, 0.05, 0.9), rail: new BoxGeometry(0.06, 0.06, 1) }), []);

  useEffect(() => {
    const tl = gsap.timeline();
    tl.to(state, { track: 1, duration: reduced ? 0.8 : 1.8, ease: 'power2.inOut' }, 0);
    tl.to(state, { show: 1, duration: 0.4 }, reduced ? 0.6 : 1.4);
    tl.to(state, { speed: reduced ? 0.25 : 0.55, duration: 1.6, ease: 'power2.out' }, reduced ? 0.6 : 1.4);
    sherlock.play([{ name: 'alerte' }, { name: 'reussite' }]);
    return () => {
      tl.kill();
    };
  }, [state, reduced]);

  useEffect(() => {
    if (!closing) return;
    const tl = gsap.timeline();
    tl.to(state, { show: 0, duration: 0.3 }, 0);
    tl.to(state, { track: 0, duration: 0.6, ease: 'power2.in' }, 0);
    return () => {
      tl.kill();
    };
  }, [closing, state]);

  useEffect(
    () => () => {
      for (const c of cars) {
        c.traverse((o) => {
          if (o instanceof Mesh) {
            o.geometry.dispose();
            (o.material as Material).dispose();
          }
        });
      }
      mats.wood.dispose();
      mats.steel.dispose();
      geos.sleeper.dispose();
      geos.rail.dispose();
    },
    [cars, mats, geos],
  );

  const m = useMemo(() => new Matrix4(), []);
  const q = useMemo(() => new Quaternion(), []);
  const p = useMemo(() => new Vector3(), []);
  const p2 = useMemo(() => new Vector3(), []);
  const sc = useMemo(() => new Vector3(), []);
  const up = useMemo(() => new Vector3(0, 1, 0), []);

  useLayoutEffect(() => {
    if (sleepers.current) sleepers.current.count = SLEEPERS;
  }, []);

  useFrame((frame, rawDelta) => {
    const delta = Math.min(rawDelta, 0.05);
    const s = sleepers.current;
    const r = rails.current;
    if (!s || !r) return;
    // Traverses et rails apparaissent en tournant autour du sapin.
    for (let i = 0; i < SLEEPERS; i++) {
      const u = (i / SLEEPERS) * Math.PI * 2;
      const local = Math.min(1, Math.max(0, state.track * 1.25 - i / SLEEPERS));
      ellipsePoint(u, p);
      ellipsePoint(u + 0.01, p2);
      const yaw = Math.atan2(p2.x - p.x, p2.z - p.z);
      q.setFromAxisAngle(up, yaw + Math.PI / 2);
      p.y += (1 - local) * 1.2;
      m.compose(p, q, sc.setScalar(Math.max(0.0001, local)));
      s.setMatrixAt(i, m);
      for (const side of [-1, 1]) {
        const { rx, rz } = trackParams();
        const len = Math.hypot(-Math.sin(u) * rx, Math.cos(u) * rz) * ((Math.PI * 2) / SLEEPERS) * 1.02;
        const off = new Vector3(Math.cos(yaw), 0, -Math.sin(yaw)).multiplyScalar(side * 0.3);
        q.setFromAxisAngle(up, yaw);
        m.compose(
          p
            .clone()
            .add(off)
            .setY(p.y + 0.05),
          q,
          sc.set(Math.max(0.0001, local), Math.max(0.0001, local), len * Math.max(0.0001, local)),
        );
        r.setMatrixAt(i * 2 + (side > 0 ? 1 : 0), m);
      }
    }
    s.instanceMatrix.needsUpdate = true;
    r.instanceMatrix.needsUpdate = true;

    state.u += state.speed * delta;
    const t = frame.clock.elapsedTime;
    cars.forEach((c, i) => {
      const u = state.u - i * 0.26;
      ellipsePoint(u, p);
      ellipsePoint(u + 0.02, p2);
      c.position.copy(p);
      c.rotation.y = Math.atan2(p2.x - p.x, p2.z - p.z) - Math.PI / 2;
      c.scale.setScalar(Math.max(0.0001, state.show) * 0.95);
      c.position.y += Math.abs(Math.sin(t * 9 + i)) * 0.015;
      c.traverse((o) => {
        if (o.name === 'wheel') o.rotation.y -= state.speed * delta * 25;
      });
    });
    const loco = cars[0];
    if (loco && state.show > 0.9 && t > state.nextPuff) {
      const chimney = loco.getObjectByName('chimney');
      if (chimney) {
        chimney.getWorldPosition(p);
        burst(p.add(new Vector3(0, 0.25, 0)), {
          count: 3,
          speed: 0.35,
          colors: ['#dfe6ef', '#b6c1cf'],
          life: [1.2, 2.0],
          size: [0.2, 0.42],
          up: 2.2,
        });
      }
      state.nextPuff = t + 0.18;
    }
  });

  return (
    <group>
      <instancedMesh ref={sleepers} args={[geos.sleeper, mats.wood, SLEEPERS]} castShadow receiveShadow frustumCulled={false} />
      <instancedMesh ref={rails} args={[geos.rail, mats.steel, SLEEPERS * 2]} frustumCulled={false} />
      {cars.map((c, i) => (
        <primitive key={i} object={c} />
      ))}
    </group>
  );
}
