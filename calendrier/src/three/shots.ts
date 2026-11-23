import { Vector3 } from 'three';
import { layoutRef } from './fx';

export interface Shot {
  pos: Vector3;
  target: Vector3;
  fov: number;
}

/** Plan rapproché sur Sherlock, décalé pour laisser la place à la carte. */
export function sherlockShot(): Shot {
  const l = layoutRef.current;
  const head = l.sherlockPos.clone().add(new Vector3(0, 2.1, 0));
  if (l.portrait) {
    const target = head.clone().add(new Vector3(0, -1.9, 0));
    return { pos: target.clone().add(new Vector3(0.6, 0.9, 11.5)), target, fov: 40 };
  }
  const target = head.clone().add(new Vector3(2.3, 0.1, 0));
  return { pos: target.clone().add(new Vector3(-1.2, 0.5, 11)), target, fov: 32 };
}

/** Plan large qui lève les yeux vers le ciel (aurores, lanternes, feu d'artifice). */
export function skyShot(): Shot {
  const l = layoutRef.current;
  const target = l.camTarget.clone().add(new Vector3(l.portrait ? 0 : 1.5, l.portrait ? 4 : 4.6, -4));
  const pos = l.camPos.clone().add(new Vector3(l.portrait ? 0 : -1.5, -1.6, 3));
  return { pos, target, fov: l.fov + 6 };
}

/** Plan d'ensemble un peu reculé (petites scènes au sol). */
export function groundShot(): Shot {
  const l = layoutRef.current;
  const target = l.camTarget.clone().add(new Vector3(0, -1.6, 1.5));
  const pos = l.camPos.clone().add(new Vector3(0, 1.4, 2.5));
  return { pos, target, fov: l.fov + 2 };
}

/** Plan large du final : grue reculée, légèrement décalée. */
export function finaleShot(): Shot {
  const l = layoutRef.current;
  // Sur ordinateur, la scène glisse à gauche pour laisser la typographie à droite.
  // Sur mobile, la scène remonte au-dessus de la typographie placée en bas.
  const target = l.camTarget.clone().add(new Vector3(l.portrait ? 0 : 3.4, l.portrait ? -2.6 : 1.4, 0));
  const back = l.camPos.clone().sub(l.camTarget).multiplyScalar(1.22);
  const pos = target
    .clone()
    .add(back)
    .add(new Vector3(l.portrait ? 0 : 2.5, 1.2, 0));
  return { pos, target, fov: l.fov };
}

/** Lacet à donner à Sherlock pour qu'il regarde la caméra. */
export function yawTowardCamera(camera: Vector3): number {
  const l = layoutRef.current;
  return Math.atan2(camera.x - l.sherlockPos.x, camera.z - l.sherlockPos.z) - l.sherlockYaw;
}
