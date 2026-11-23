import { useFrame, useThree } from '@react-three/fiber';
import { useEffect, useMemo } from 'react';
import { MathUtils, Vector3, type PerspectiveCamera } from 'three';
import { onResize } from '../director';
import { useApp } from '../store';
import { pointer, shot } from './fx';

/** Caméra entièrement mise en scène : plan GSAP + parallaxe borné + secousse. */
export function CameraRig() {
  const camera = useThree((s) => s.camera) as PerspectiveCamera;
  const size = useThree((s) => s.size);
  const reduced = useApp((s) => s.reducedMotion);
  const smooth = useMemo(() => ({ x: 0, y: 0 }), []);
  const right = useMemo(() => new Vector3(), []);
  const up = useMemo(() => new Vector3(), []);
  const look = useMemo(() => new Vector3(), []);

  useEffect(() => {
    onResize(size.width / size.height);
  }, [size.width, size.height]);

  useFrame((state, rawDelta) => {
    const delta = Math.min(rawDelta, 0.05);
    const amount = reduced ? 0 : shot.parallax;
    const px = (pointer.x + pointer.gx) * amount;
    const py = (pointer.y - pointer.gy * 0.6) * amount;
    smooth.x = MathUtils.damp(smooth.x, px, 2.6, delta);
    smooth.y = MathUtils.damp(smooth.y, py, 2.6, delta);

    camera.position.copy(shot.pos);
    look.copy(shot.target);
    // Parallaxe : la caméra glisse latéralement, la cible bouge moins (effet de profondeur).
    right.set(1, 0, 0);
    up.set(0, 1, 0);
    camera.position.addScaledVector(right, smooth.x * 0.9).addScaledVector(up, smooth.y * 0.45);
    look.addScaledVector(right, smooth.x * 0.25).addScaledVector(up, smooth.y * 0.12);
    if (shot.shake > 0 && !reduced) {
      const t = state.clock.elapsedTime;
      camera.position.x += Math.sin(t * 71) * shot.shake;
      camera.position.y += Math.cos(t * 83) * shot.shake;
    }
    camera.lookAt(look);
    if (Math.abs(camera.fov - shot.fov) > 0.001) {
      camera.fov = shot.fov;
      camera.updateProjectionMatrix();
    }
  });

  return null;
}
