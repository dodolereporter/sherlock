import { useFrame } from '@react-three/fiber';
import gsap from 'gsap';
import { useEffect, useMemo, useRef } from 'react';
import { AdditiveBlending, Color, Mesh, MeshBasicMaterial, RingGeometry, Vector3, type Group } from 'three';
import type { ObjectKind } from '../../content/days';
import { useApp } from '../../store';
import { layoutRef } from '../fx';
import { slotWorld } from '../layout';
import { burst } from '../sparklePool';
import { buildObject, disposeObject } from './objects';

const SCALE: Record<ObjectKind, number> = { boule: 1.4, sucre: 1.6, flocon: 1.5, etoile: 1.45, cloche: 1.45, chocolat: 1.4 };

/** Objet 3D qui jaillit de la case, se présente en tournant, puis rentre à la fermeture. */
export function SurpriseObject({ day, kind }: { day: number; kind: ObjectKind }) {
  const group = useRef<Group>(null);
  const root = useMemo(() => buildObject(kind), [kind]);
  const reduced = useApp((s) => s.reducedMotion);
  const closing = useApp((s) => s.phase === 'closing');
  const state = useMemo(() => ({ appear: 0, spin: 0, nextPuff: 0, ring: 0 }), []);
  const ringMesh = useMemo(() => {
    const m = new Mesh(
      new RingGeometry(0.55, 0.6, 64),
      new MeshBasicMaterial({
        color: new Color('#ffd48a').multiplyScalar(2),
        transparent: true,
        blending: AdditiveBlending,
        depthWrite: false,
        toneMapped: false,
      }),
    );
    m.visible = kind === 'cloche';
    return m;
  }, [kind]);

  useEffect(
    () => () => {
      disposeObject(root);
      ringMesh.geometry.dispose();
      (ringMesh.material as MeshBasicMaterial).dispose();
    },
    [root, ringMesh],
  );

  useEffect(() => {
    const tween = reduced
      ? gsap.to(state, { appear: 1, duration: 0.7, ease: 'sine.out' })
      : gsap.to(state, { appear: 1, duration: 1.35, ease: 'back.out(1.6)' });
    return () => {
      tween.kill();
    };
  }, [state, reduced]);

  useEffect(() => {
    if (!closing) return;
    const tween = gsap.to(state, { appear: 0, duration: 0.55, ease: 'back.in(1.8)' });
    return () => {
      tween.kill();
    };
  }, [closing, state]);

  const from = useMemo(() => new Vector3(), []);
  const to = useMemo(() => new Vector3(), []);

  useFrame((frame) => {
    const g = group.current;
    if (!g) return;
    const t = frame.clock.elapsedTime;
    const l = layoutRef.current;
    slotWorld(day, l, from);
    to.copy(from).add(l.portrait ? new Vector3(0, -0.75, 2.4) : new Vector3(-0.5, -0.1, 2.3));
    const a = state.appear;
    g.position.lerpVectors(from, to, Math.min(1, a));
    g.position.y += Math.sin(t * 1.3) * 0.07 * a;
    // Les cases hautes sont filmées de plus loin : l'objet grandit avec la hauteur.
    const lift = 1 + Math.max(0, from.y - 3) * 0.06;
    g.scale.setScalar(Math.max(0.0001, a) * SCALE[kind] * lift);
    const motion = reduced ? 0.3 : 1;
    g.rotation.set(Math.sin(t * 0.7) * 0.12 * motion, (1 - a) * 5 + Math.sin(t * 0.45) * 0.6 * motion, Math.sin(t * 0.9) * 0.05 * motion);

    if (kind === 'cloche') {
      // La cloche sonne : balancier amorti qui repart toutes les 2,4 s, ondes sonores dorées.
      const phase = t % 2.4;
      const swing = Math.sin(phase * 7.5) * Math.exp(-phase * 1.4) * 0.45 * motion;
      g.rotation.z = swing;
      const clapper = root.getObjectByName('clapper');
      if (clapper) clapper.position.x = -Math.sin(phase * 7.5 - 0.6) * Math.exp(-phase * 1.4) * 0.12 * motion;
      const k = (phase / 2.4) % 1;
      ringMesh.position.copy(g.position);
      ringMesh.scale.setScalar(1 + k * 3.5);
      (ringMesh.material as MeshBasicMaterial).opacity = (1 - k) * 0.6 * a;
      ringMesh.lookAt(frame.camera.position);
    }
    if (a > 0.95 && t > state.nextPuff) {
      if (kind === 'chocolat') {
        burst(g.position.clone().add(new Vector3(0, 0.75, 0)), {
          count: 4,
          speed: 0.25,
          colors: ['#e9eef5', '#cfd8e3'],
          life: [1.6, 2.6],
          size: [0.18, 0.4],
          up: 3,
          spread: [0.6, 0.2, 0.6],
        });
        state.nextPuff = t + 0.16;
      } else if (kind === 'flocon' || kind === 'boule' || kind === 'etoile' || kind === 'sucre') {
        burst(g.position.clone().add(new Vector3((Math.random() - 0.5) * 1.2, (Math.random() - 0.5) * 1.2, 0.3)), {
          count: 2,
          speed: 0.3,
          colors: kind === 'flocon' ? ['#cfe6ff', '#ffffff'] : ['#ffe3a6', '#ffffff'],
          life: [0.6, 1.2],
          size: [0.06, 0.14],
          up: 0.2,
        });
        state.nextPuff = t + 0.12;
      }
    }
  });

  return (
    <>
      <group ref={group}>
        <primitive object={root} />
      </group>
      <primitive object={ringMesh} />
    </>
  );
}
