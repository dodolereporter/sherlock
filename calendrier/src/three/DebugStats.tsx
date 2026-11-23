import { useFrame, useThree } from '@react-three/fiber';
import { useEffect, useRef } from 'react';

export interface DebugSample {
  fps: number;
  calls: number;
  triangles: number;
  points: number;
  geometries: number;
  textures: number;
}

declare global {
  interface Window {
    __debugStats?: DebugSample;
  }
}

/**
 * Compte les appels de dessin et triangles de l'image entière (ombres et post-traitement compris) :
 * la remise à zéro automatique est coupée et faite ici, avant le premier rendu de l'image.
 */
export function DebugStats({ onSample }: { onSample: (s: DebugSample) => void }) {
  const gl = useThree((s) => s.gl);
  const frames = useRef({ count: 0, last: 0, fps: 0 });

  useEffect(() => {
    gl.info.autoReset = false;
    return () => {
      gl.info.autoReset = true;
    };
  }, [gl]);

  useFrame(() => {
    gl.info.reset();
  }, -100);

  useFrame(() => {
    const f = frames.current;
    f.count++;
    const now = performance.now();
    if (now - f.last >= 500) {
      f.fps = (f.count * 1000) / (now - f.last);
      f.count = 0;
      f.last = now;
      const sample: DebugSample = {
        fps: Math.round(f.fps),
        calls: gl.info.render.calls,
        triangles: gl.info.render.triangles,
        points: gl.info.render.points,
        geometries: gl.info.memory.geometries,
        textures: gl.info.memory.textures,
      };
      window.__debugStats = sample;
      onSample(sample);
    }
  }, 100);

  return null;
}
