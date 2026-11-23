import { useProgress } from '@react-three/drei';
import { Canvas } from '@react-three/fiber';
import { useCallback, useEffect } from 'react';
import { NoToneMapping, SRGBColorSpace } from 'three';
import { quality } from './lib/quality';
import { useApp } from './store';
import type { DebugSample } from './three/DebugStats';
import { Experience } from './three/Experience';
import { Projector } from './three/Projector';

/** Remonte la progression du chargement des ressources 3D vers l'écran de chargement. */
function ProgressBridge() {
  const progress = useProgress((s) => s.progress);
  const setProgress = useApp((s) => s.setProgress);
  useEffect(() => {
    setProgress(progress);
  }, [progress, setProgress]);
  return null;
}

/** Tout ce qui dépend de three.js : chargé à part, derrière l'écran de chargement. */
export default function Stage({ onStats, onContextLost }: { onStats: (s: DebugSample) => void; onContextLost: () => void }) {
  const onCreated = useCallback(
    ({ gl }: { gl: { domElement: HTMLCanvasElement } }) => {
      gl.domElement.addEventListener('webglcontextlost', (e) => {
        e.preventDefault();
        onContextLost();
      });
    },
    [onContextLost],
  );
  return (
    <>
      <ProgressBridge />
      <Canvas
        className="scene"
        shadows="percentage"
        dpr={[1, quality.maxDpr]}
        gl={{
          antialias: false,
          powerPreference: 'high-performance',
          stencil: false,
          toneMapping: NoToneMapping,
          outputColorSpace: SRGBColorSpace,
        }}
        camera={{ fov: 30, near: 0.1, far: 600, position: [0, 20, 40] }}
        onCreated={onCreated}
        aria-hidden="true"
      >
        <Experience onStats={onStats} />
        <Projector />
      </Canvas>
    </>
  );
}
