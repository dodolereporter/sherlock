import { useAnimations } from '@react-three/drei';
import { useFrame, useLoader } from '@react-three/fiber';
import { useEffect, useMemo, useRef } from 'react';
import {
  LoopOnce,
  LoopRepeat,
  MathUtils,
  Mesh,
  Quaternion,
  SphereGeometry,
  type BufferAttribute,
  type MeshStandardMaterial,
  Vector3,
  type AnimationAction,
  type Bone,
  type Group,
  type Object3D,
} from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { layoutRef, pointer } from './fx';
import { createSnowMaterial } from './materials';
import { fbm2 } from './noise';
import { MODEL_URL } from './model';
import { sherlock, type Step } from './sherlockApi';

const FADE = 0.28;
const tmpV = new Vector3();
const tmpQ = new Quaternion();
const yawQ = new Quaternion();
const pitchQ = new Quaternion();
const AXIS_Y = new Vector3(0, 1, 0);
const AXIS_X = new Vector3(1, 0, 0);
const HEAD_CENTER = new Vector3(0, 1.95, 0);

export function Sherlock() {
  const group = useRef<Group>(null);
  const { scene, animations } = useLoader(GLTFLoader, MODEL_URL, (loader) => {
    loader.setMeshoptDecoder(MeshoptDecoder);
  });
  const { actions, mixer } = useAnimations(animations, group);

  const bones = useMemo(() => {
    const find = (name: string) => scene.getObjectByName(name) as Bone | undefined;
    const eyeL = find('eye_L');
    const eyeR = find('eye_R');
    return {
      head: find('head'),
      eyeL,
      eyeR,
      eyeRestL: eyeL?.quaternion.clone() ?? new Quaternion(),
      eyeRestR: eyeR?.quaternion.clone() ?? new Quaternion(),
    };
  }, [scene]);

  // Neige qui s'accumule lentement sur la casquette (accrochée à l'os de la tête).
  const capSnow = useMemo(() => {
    const geo = new SphereGeometry(0.5, 24, 10, 0, Math.PI * 2, 0, Math.PI / 2);
    const pos = geo.attributes.position as BufferAttribute;
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i);
      const z = pos.getZ(i);
      const n = fbm2(x * 5 + 1, z * 5) - 0.5;
      pos.setY(i, Math.max(0, pos.getY(i) * 0.5 + n * 0.12));
    }
    geo.computeVertexNormals();
    const m = new Mesh(geo, createSnowMaterial('#eef3fa'));
    m.castShadow = true;
    return m;
  }, []);

  useEffect(() => {
    const head = bones.head;
    if (!head) return;
    head.add(capSnow);
    capSnow.position.set(0.02, 1.12, -0.08);
    capSnow.rotation.set(-0.12, 0, 0.04);
    return () => {
      head.remove(capSnow);
      capSnow.geometry.dispose();
      (capSnow.material as MeshStandardMaterial).dispose();
    };
  }, [bones, capSnow]);

  useEffect(() => {
    scene.traverse((o: Object3D) => {
      if (o instanceof Mesh) {
        o.castShadow = true;
        o.receiveShadow = true;
        o.frustumCulled = false;
      }
    });
  }, [scene]);

  // État d'animation (hors React).
  const anim = useRef({
    current: null as AnimationAction | null,
    queue: [] as Step[],
    look: null as Vector3 | null,
    lookSmooth: new Vector3(0, 3, 10),
    yawTarget: 0,
    yaw: 0,
    nextBlink: 2,
    nextIdle: 9,
  });

  useEffect(() => {
    const state = anim.current;
    const get = (name: string) => actions[name] ?? null;

    const start = (step: Step) => {
      const action = get(step.name);
      if (!action) return;
      action.reset();
      action.setLoop(step.loop ? LoopRepeat : LoopOnce, step.loop ? Infinity : 1);
      action.clampWhenFinished = !step.loop;
      action.enabled = true;
      action.setEffectiveWeight(1);
      action.play();
      if (state.current && state.current !== action) state.current.crossFadeTo(action, FADE, false);
      else action.fadeIn(FADE);
      state.current = action;
    };

    const next = () => {
      const step = state.queue.shift();
      if (step) start(step);
      else start({ name: 'repos', loop: true });
    };

    const onFinished = (e: { action: AnimationAction }) => {
      if (e.action === state.current) next();
      if (e.action === get('cligne')) e.action.stop();
    };
    mixer.addEventListener('finished', onFinished);

    sherlock.play = (steps) => {
      const list: Step[] = typeof steps === 'string' ? [{ name: steps }] : steps;
      state.queue = list.slice(1);
      const first = list[0];
      if (first) start(first);
    };
    sherlock.lookAt = (target) => {
      state.look = target ? target.clone() : null;
    };
    sherlock.turn = (yaw) => {
      state.yawTarget = yaw;
    };

    start({ name: 'repos', loop: true });
    return () => {
      mixer.removeEventListener('finished', onFinished);
      mixer.stopAllAction();
    };
  }, [actions, mixer]);

  useFrame((_, rawDelta) => {
    const g = group.current;
    if (!g) return;
    const delta = Math.min(rawDelta, 0.05);
    const state = anim.current;
    const layout = layoutRef.current;
    const t = performance.now() / 1000;

    // Clignements et petites variations de repos.
    if (t > state.nextBlink) {
      const blink = actions.cligne;
      if (blink) {
        blink.reset().setLoop(LoopOnce, 1).play();
        blink.setEffectiveWeight(1);
      }
      state.nextBlink = t + 2.2 + Math.random() * 3.5;
    }
    if (t > state.nextIdle) {
      if (state.current === actions.repos && state.queue.length === 0) {
        sherlock.play(Math.random() < 0.5 ? 'repos_variante_1' : 'repos_variante_2');
      }
      state.nextIdle = t + 11 + Math.random() * 8;
    }

    // Position et orientation du corps.
    g.position.copy(layout.sherlockPos);
    state.yaw = MathUtils.damp(state.yaw, state.yawTarget, 4, delta);
    g.rotation.y = layout.sherlockYaw + state.yaw;

    // Regard : cible explicite, sinon le pointeur (une cible devant lui).
    const target = state.look ?? tmpV.set(layout.sherlockPos.x + pointer.x * 7, 3.2 + pointer.y * 3, layout.sherlockPos.z + 9);
    state.lookSmooth.x = MathUtils.damp(state.lookSmooth.x, target.x, 6, delta);
    state.lookSmooth.y = MathUtils.damp(state.lookSmooth.y, target.y, 6, delta);
    state.lookSmooth.z = MathUtils.damp(state.lookSmooth.z, target.z, 6, delta);

    const head = bones.head;
    if (head) {
      const local = g.worldToLocal(tmpV.copy(state.lookSmooth));
      const headLocal = local.sub(HEAD_CENTER);
      const yaw = MathUtils.clamp(Math.atan2(headLocal.x, Math.max(0.5, headLocal.z)), -0.9, 0.9);
      const pitch = MathUtils.clamp(Math.atan2(headLocal.y, Math.hypot(headLocal.x, headLocal.z)), -0.5, 0.6);
      yawQ.setFromAxisAngle(AXIS_Y, yaw * 0.45);
      pitchQ.setFromAxisAngle(AXIS_X, -pitch * 0.35);
      head.quaternion.multiply(tmpQ.copy(yawQ).multiply(pitchQ));
      // Les yeux glissent sur le visage pour le reste du regard.
      yawQ.setFromAxisAngle(AXIS_Y, yaw * 0.3);
      pitchQ.setFromAxisAngle(AXIS_X, -pitch * 0.25);
      tmpQ.copy(yawQ).multiply(pitchQ);
      bones.eyeL?.quaternion.copy(bones.eyeRestL).premultiply(tmpQ);
      bones.eyeR?.quaternion.copy(bones.eyeRestR).premultiply(tmpQ);
    }
    // 0,4 → 1 en deux minutes : la neige s'installe pendant qu'on regarde.
    const grow = 0.4 + Math.min(1, t / 120) * 0.6;
    capSnow.scale.set(1.15 * (0.7 + grow * 0.3), grow, 1.05 * (0.7 + grow * 0.3));
  });

  return (
    <group ref={group} dispose={null}>
      <primitive object={scene} />
    </group>
  );
}
