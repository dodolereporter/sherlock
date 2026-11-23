import { useFrame, type ThreeEvent } from '@react-three/fiber';
import { useEffect, useLayoutEffect, useMemo, useRef } from 'react';
import {
  BackSide,
  BoxGeometry,
  BufferGeometry,
  Color,
  IcosahedronGeometry,
  InstancedBufferAttribute,
  InstancedMesh,
  Matrix4,
  MeshBasicMaterial,
  MeshStandardMaterial,
  PlaneGeometry,
  Quaternion,
  SphereGeometry,
  Vector3,
  type BufferAttribute,
  type Group,
  type Mesh,
} from 'three';
import { RoundedBoxGeometry } from 'three/examples/jsm/geometries/RoundedBoxGeometry.js';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { clickDay, hoverDay } from '../director';
import { isUnlocked } from '../lib/dates';
import { useApp } from '../store';
import { ambience, boxFx, layoutRef } from './fx';
import { SHELVES, SLOTS } from './layout';
import { createSnowMaterial } from './materials';
import { starGeometry } from './geometries';
import { fbm2, rng } from './noise';
import { ATLAS_COLS, ATLAS_ROWS, createDoorTextures, createNumberAtlas } from './textures';

const WALL = 0.07;
const DOOR_T = 0.06;
const TINTS = ['#8e2a36', '#2b5547', '#e7dac2', '#d9a54a'].map((c) => new Color(c));
const WARM = new Color('#ffb15a');
const INNER_DARK = new Color('#2a1a12');

function hollowBox(): BufferGeometry {
  const parts: BufferGeometry[] = [];
  const add = (w: number, h: number, d: number, x: number, y: number, z: number) => {
    const g = new RoundedBoxGeometry(w, h, d, 2, 0.025);
    g.translate(x, y, z);
    parts.push(g);
  };
  add(1, 1, WALL, 0, 0, -0.5 + WALL / 2);
  add(WALL, 1, 1, -0.5 + WALL / 2, 0, 0);
  add(WALL, 1, 1, 0.5 - WALL / 2, 0, 0);
  add(1, WALL, 1, 0, 0.5 - WALL / 2, 0);
  add(1, WALL, 1, 0, -0.5 + WALL / 2, 0);
  return mergeGeometries(parts);
}

function snowCap(): BufferGeometry {
  const g = new SphereGeometry(0.5, 28, 10, 0, Math.PI * 2, 0, Math.PI / 2);
  const pos = g.attributes.position as BufferAttribute;
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i);
    const y = pos.getY(i);
    const z = pos.getZ(i);
    const n = fbm2(x * 6 + 2, z * 6) - 0.5;
    pos.setXYZ(i, x * 1.08, Math.max(0, y * 0.32 + n * 0.06 * (y > 0.01 ? 1 : 0)), z * 1.08);
  }
  g.computeVertexNormals();
  return g;
}

const m4 = new Matrix4();
const boxM = new Matrix4();
const doorM = new Matrix4();
const tmpM = new Matrix4();
const q = new Quaternion();
const v = new Vector3();
const s = new Vector3();
const AXIS_Y = new Vector3(0, 1, 0);
const AXIS_Z = new Vector3(0, 0, 1);
const glowColor = new Color();

/** Lit l'état des cases pour savoir lesquelles sont ouvrables (calculé une fois). */
const unlocked = SLOTS.map((slot) => isUnlocked(slot.day));

export function AdventTree() {
  const group = useRef<Group>(null);
  const bodyRef = useRef<InstancedMesh>(null);
  const doorRef = useRef<InstancedMesh>(null);
  const innerRef = useRef<InstancedMesh>(null);
  const numberRef = useRef<InstancedMesh>(null);
  const knobRef = useRef<InstancedMesh>(null);
  const capRef = useRef<InstancedMesh>(null);
  const shelfRef = useRef<InstancedMesh>(null);
  const shelfSnowRef = useRef<InstancedMesh>(null);
  const bulbRef = useRef<InstancedMesh>(null);
  const topper = useRef<Mesh>(null);
  const fontsReady = useApp((st) => st.fontsReady);

  const geos = useMemo(() => {
    const door = new RoundedBoxGeometry(0.985, 0.985, DOOR_T, 2, 0.02);
    door.translate(0.4925, 0, 0);
    const number = new PlaneGeometry(0.6, 0.6);
    const cells = new Float32Array(24 * 2);
    const glow = new Float32Array(24);
    SLOTS.forEach((slot, i) => {
      const idx = slot.day - 1;
      cells[i * 2] = (idx % ATLAS_COLS) / ATLAS_COLS;
      cells[i * 2 + 1] = (ATLAS_ROWS - 1 - Math.floor(idx / ATLAS_COLS)) / ATLAS_ROWS;
    });
    number.setAttribute('aCell', new InstancedBufferAttribute(cells, 2));
    number.setAttribute('aGlow', new InstancedBufferAttribute(glow, 1));
    return {
      body: hollowBox(),
      door,
      number,
      inner: new BoxGeometry(1 - WALL * 2 - 0.012, 1 - WALL * 2 - 0.012, 1 - WALL * 2 - 0.012),
      knob: new SphereGeometry(0.045, 12, 8),
      cap: snowCap(),
      shelf: new RoundedBoxGeometry(1, 0.16, 1.35, 2, 0.05),
      bulb: new IcosahedronGeometry(0.06, 1),
      star: starGeometry(0.42, 0.18, 0.1),
    };
  }, []);

  const mats = useMemo(() => {
    const { map, frost } = createDoorTextures();
    const body = new MeshStandardMaterial({ roughness: 0.72, metalness: 0.02 });
    const door = new MeshStandardMaterial({
      map,
      roughness: 0.6,
      metalness: 0.02,
      emissive: new Color('#c4d8f0'),
      emissiveMap: frost,
      emissiveIntensity: 0.32,
    });
    const inner = new MeshBasicMaterial({ side: BackSide, toneMapped: false });
    const number = new MeshStandardMaterial({
      color: '#e8b964',
      metalness: 0.75,
      roughness: 0.32,
      transparent: true,
      alphaTest: 0.35,
      emissive: new Color('#6b4a12'),
      emissiveIntensity: 0.35,
    });
    number.onBeforeCompile = (shader) => {
      shader.vertexShader = shader.vertexShader
        .replace('#include <common>', '#include <common>\nattribute vec2 aCell;\nattribute float aGlow;\nvarying float vGlow;')
        .replace(
          '#include <uv_vertex>',
          `#include <uv_vertex>\n#ifdef USE_MAP\nvMapUv = uv * vec2(${(1 / ATLAS_COLS).toFixed(6)}, ${(1 / ATLAS_ROWS).toFixed(6)}) + aCell;\n#endif\nvGlow = aGlow;`,
        );
      shader.fragmentShader = shader.fragmentShader
        .replace('#include <common>', '#include <common>\nvarying float vGlow;')
        .replace(
          '#include <emissivemap_fragment>',
          '#include <emissivemap_fragment>\ntotalEmissiveRadiance += vec3(1.0, 0.68, 0.3) * vGlow * 2.2;',
        );
    };
    const knob = new MeshStandardMaterial({ color: '#d8a957', metalness: 0.9, roughness: 0.25 });
    const shelf = new MeshStandardMaterial({ color: '#203a31', roughness: 0.8 });
    const bulb = new MeshBasicMaterial({ toneMapped: false });
    const star = new MeshStandardMaterial({
      color: '#f3c66b',
      metalness: 0.85,
      roughness: 0.22,
      emissive: new Color('#ffb648'),
      emissiveIntensity: 0.6,
    });
    return { body, door, inner, number, knob, shelf, bulb, star, snow: createSnowMaterial('#e2eaf4') };
  }, []);

  // Atlas des chiffres, redessiné quand la police est prête.
  useEffect(() => {
    const atlas = createNumberAtlas();
    mats.number.map = atlas;
    mats.number.needsUpdate = true;
    return () => atlas.dispose();
  }, [fontsReady, mats]);

  // Garland : ampoules le long du bord de chaque étagère, en chaînette.
  const bulbs = useMemo(() => {
    const out: { pos: Vector3; phase: number }[] = [];
    const random = rng(3);
    SHELVES.forEach((shelf) => {
      const n = Math.round(shelf.width * 2.4);
      for (let i = 0; i < n; i++) {
        const t = i / (n - 1);
        const x = (t - 0.5) * shelf.width * 0.98;
        const sag = Math.sin(((t * shelf.width) / 1.36) * Math.PI) ** 2 * 0.18;
        out.push({ pos: new Vector3(x, shelf.y - 0.12 - sag, 0.7), phase: random() * Math.PI * 2 });
      }
    });
    return out;
  }, []);

  // Couleurs fixes et éléments statiques.
  useLayoutEffect(() => {
    const body = bodyRef.current;
    const door = doorRef.current;
    const cap = capRef.current;
    const shelf = shelfRef.current;
    const shelfSnow = shelfSnowRef.current;
    if (!body || !door || !cap || !shelf || !shelfSnow) return;
    SLOTS.forEach((slot, i) => {
      const tint = TINTS[slot.tint] ?? TINTS[0];
      if (tint) {
        body.setColorAt(i, tint.clone().multiplyScalar(0.82));
        door.setColorAt(i, tint);
      }
    });
    if (body.instanceColor) body.instanceColor.needsUpdate = true;
    if (door.instanceColor) door.instanceColor.needsUpdate = true;
    SHELVES.forEach((sh, i) => {
      m4.compose(v.set(0, sh.y, 0.05), q.identity(), s.set(sh.width, 1, 1));
      shelf.setMatrixAt(i, m4);
      m4.compose(v.set(0, sh.y + 0.07, 0.12), q.identity(), s.set(sh.width * 0.98, 0.55, 1.25));
      shelfSnow.setMatrixAt(i, m4);
    });
    shelf.instanceMatrix.needsUpdate = true;
    shelfSnow.instanceMatrix.needsUpdate = true;
  }, []);

  const capVariation = useMemo(() => {
    const random = rng(11);
    return SLOTS.map(() => ({ rot: random() * Math.PI * 2, sx: 0.95 + random() * 0.1, sy: 0.8 + random() * 0.6 }));
  }, []);

  useFrame((state) => {
    const g = group.current;
    const body = bodyRef.current;
    const door = doorRef.current;
    const inner = innerRef.current;
    const number = numberRef.current;
    const knob = knobRef.current;
    const cap = capRef.current;
    const bulb = bulbRef.current;
    if (!g || !body || !door || !inner || !number || !knob || !cap || !bulb) return;
    g.position.copy(layoutRef.current.treeOffset);
    const t = state.clock.elapsedTime;
    const glowAttr = geos.number.getAttribute('aGlow') as InstancedBufferAttribute;
    const dim = 1 - ambience.dim * 0.75;
    const activeDay = useApp.getState().activeDay;

    SLOTS.forEach((slot, i) => {
      const fx = boxFx[slot.day - 1];
      if (!fx) return;
      const size = slot.size;
      const sq = fx.squash;
      const sx = 1 + sq * 0.35;
      const sy = 1 - sq * 0.5;
      const shakeX = Math.sin(t * 61) * fx.shake * 0.05;
      const rotZ = Math.sin(t * 43) * fx.shake * 0.07;
      v.set(slot.local.x + shakeX, slot.local.y - (1 - sy) * size * 0.5 + fx.lift * 0.12, slot.local.z + fx.hover * 0.38 + fx.lift * 0.35);
      q.setFromAxisAngle(AXIS_Z, rotZ);
      const scale = size * (1 + fx.hover * 0.07 + fx.pulse * 0.06);
      boxM.compose(v, q, s.set(scale * sx, scale * sy, scale));
      body.setMatrixAt(i, boxM);

      inner.setMatrixAt(i, boxM);

      // Porte : charnière à gauche, s'ouvre vers la caméra.
      const ajar = unlocked[i] ? fx.hover * 0.32 : 0;
      const rattle = Math.sin(t * 52) * fx.shake * 0.1 + fx.shake * 0.05;
      const angle = fx.door * 1.95 + ajar + rattle;
      doorM.copy(boxM).multiply(tmpM.makeTranslation(-0.4925, 0, 0.5 - DOOR_T / 2 + 0.004));
      doorM.multiply(tmpM.makeRotationAxis(AXIS_Y, -angle));
      door.setMatrixAt(i, doorM);
      m4.copy(doorM).multiply(tmpM.makeTranslation(0.4925, 0.02, DOOR_T / 2 + 0.003));
      number.setMatrixAt(i, m4);
      m4.copy(doorM).multiply(tmpM.makeTranslation(0.86, -0.02, DOOR_T / 2 + 0.03));
      knob.setMatrixAt(i, m4);

      const cv = capVariation[i];
      if (cv) {
        m4.copy(boxM).multiply(tmpM.makeTranslation(0, 0.5, 0));
        m4.multiply(tmpM.makeRotationY(cv.rot)).multiply(tmpM.makeScale(cv.sx, cv.sy, cv.sx));
        cap.setMatrixAt(i, m4);
      }

      // Intérieur : bois sombre qui s'embrase quand la case est ouverte.
      const heat = Math.min(1, fx.glow + ajar * 2.2) * dim;
      // Case active : foyer vif ; cases déjà ouvertes : braises douces.
      const active = slot.day === activeDay ? 2.2 : 1;
      glowColor
        .copy(INNER_DARK)
        .lerp(WARM, Math.min(1, heat))
        .multiplyScalar(0.3 + heat * 1.15 * active + fx.pulse * 2.5);
      inner.setColorAt(i, glowColor);
      glowAttr.setX(i, (fx.hover * 1.3 + fx.pulse * 0.8 + ambience.finale * 0.3) * dim);
    });

    body.instanceMatrix.needsUpdate = true;
    door.instanceMatrix.needsUpdate = true;
    // Sphères englobantes à jour pour le lancer de rayon (les cases bougent).
    body.computeBoundingSphere();
    door.computeBoundingSphere();
    inner.instanceMatrix.needsUpdate = true;
    number.instanceMatrix.needsUpdate = true;
    knob.instanceMatrix.needsUpdate = true;
    cap.instanceMatrix.needsUpdate = true;
    if (inner.instanceColor) inner.instanceColor.needsUpdate = true;
    glowAttr.needsUpdate = true;

    // Guirlande qui scintille en vagues.
    bulbs.forEach((b, i) => {
      m4.makeTranslation(b.pos.x, b.pos.y, b.pos.z);
      bulb.setMatrixAt(i, m4);
      const wave = 0.5 + 0.5 * Math.sin(t * 1.6 - b.pos.x * 0.7 + b.phase * 0.3);
      const k = (0.6 + wave * 2.2 + ambience.finale * 2.5) * dim * ambience.reveal;
      glowColor.setRGB(1.0 * k, 0.62 * k, 0.28 * k);
      bulb.setColorAt(i, glowColor);
    });
    bulb.instanceMatrix.needsUpdate = true;
    if (bulb.instanceColor) bulb.instanceColor.needsUpdate = true;

    const star = topper.current;
    const starSlot = SLOTS[23];
    if (star && starSlot) {
      star.position.set(starSlot.local.x, starSlot.local.y + starSlot.size * 0.5 + 0.55 + Math.sin(t * 1.2) * 0.05, 0.1);
      star.rotation.y = Math.sin(t * 0.6) * 0.35 + ambience.finale * t * 1.5;
      star.scale.setScalar(1 + ambience.finale * 0.35);
      mats.star.emissiveIntensity = (0.6 + Math.sin(t * 2) * 0.15 + ambience.finale * 3 + (boxFx[23]?.pulse ?? 0) * 2) * dim;
    }
  });

  const onMove = (e: ThreeEvent<PointerEvent>) => {
    e.stopPropagation();
    const slot = e.instanceId !== undefined ? SLOTS[e.instanceId] : undefined;
    hoverDay(slot ? slot.day : null);
  };
  const onOut = () => hoverDay(null);
  const onClick = (e: ThreeEvent<MouseEvent>) => {
    e.stopPropagation();
    const slot = e.instanceId !== undefined ? SLOTS[e.instanceId] : undefined;
    if (slot) clickDay(slot.day);
  };

  return (
    <group ref={group}>
      <instancedMesh
        ref={bodyRef}
        args={[geos.body, mats.body, 24]}
        castShadow
        receiveShadow
        onPointerMove={onMove}
        onPointerOut={onOut}
        onClick={onClick}
      />
      <instancedMesh
        ref={doorRef}
        args={[geos.door, mats.door, 24]}
        castShadow
        receiveShadow
        onPointerMove={onMove}
        onPointerOut={onOut}
        onClick={onClick}
      />
      <instancedMesh ref={innerRef} args={[geos.inner, mats.inner, 24]} />
      <instancedMesh ref={numberRef} args={[geos.number, mats.number, 24]} />
      <instancedMesh ref={knobRef} args={[geos.knob, mats.knob, 24]} />
      <instancedMesh ref={capRef} args={[geos.cap, mats.snow, 24]} receiveShadow />
      <instancedMesh ref={shelfRef} args={[geos.shelf, mats.shelf, SHELVES.length]} castShadow receiveShadow />
      <instancedMesh ref={shelfSnowRef} args={[geos.cap, mats.snow, SHELVES.length]} receiveShadow />
      <instancedMesh ref={bulbRef} args={[geos.bulb, mats.bulb, bulbs.length]} />
      <mesh ref={topper} geometry={geos.star} material={mats.star} castShadow />
    </group>
  );
}
