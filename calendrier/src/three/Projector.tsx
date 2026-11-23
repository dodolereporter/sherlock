import { useFrame } from '@react-three/fiber';
import { useMemo } from 'react';
import { Vector3 } from 'three';
import { layoutRef, screenSlots } from './fx';
import { SLOTS, slotWorld } from './layout';

/** Projette chaque case à l'écran pour y poser les boutons accessibles. */
export function Projector() {
  const v = useMemo(() => new Vector3(), []);
  const edge = useMemo(() => new Vector3(), []);
  useFrame((state) => {
    const { camera, size } = state;
    for (const slot of SLOTS) {
      const out = screenSlots[slot.day - 1];
      if (!out) continue;
      slotWorld(slot.day, layoutRef.current, v);
      edge.copy(v);
      edge.x += slot.size / 2;
      v.project(camera);
      edge.project(camera);
      out.x = (v.x * 0.5 + 0.5) * size.width;
      out.y = (-v.y * 0.5 + 0.5) * size.height;
      out.size = Math.abs(edge.x - v.x) * size.width;
      out.visible = v.z < 1;
    }
  });
  return null;
}
