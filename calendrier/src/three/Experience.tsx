import { useFrame, useThree } from '@react-three/fiber';
import { Suspense, useEffect, useMemo, useRef } from 'react';
import {
  BackSide,
  Color,
  FogExp2,
  Mesh,
  MeshBasicMaterial,
  PlaneGeometry,
  PMREMGenerator,
  Scene,
  SphereGeometry,
  type DirectionalLight,
  type HemisphereLight,
  type PointLight,
} from 'three';
import { params } from '../lib/params';
import { quality } from '../lib/quality';
import { useApp } from '../store';
import { AdventTree } from './AdventTree';
import { CameraRig } from './CameraRig';
import { DebugStats, type DebugSample } from './DebugStats';
import { Effects } from './Effects';
import { ambience, layoutRef, spot } from './fx';
import { Landscape } from './Landscape';
import { Sherlock } from './Sherlock';
import { SKY_HORIZON } from './palette';
import { Sky } from './Sky';
import { Snow } from './Snow';
import { Sparkles } from './Sparkles';
import { Surprises } from './surprises/Surprises';

/** Environnement de reflets procédural : ciel froid en haut, braises chaudes sur un côté. */
function ProceduralEnvironment() {
  const gl = useThree((s) => s.gl);
  const scene = useThree((s) => s.scene);
  useEffect(() => {
    const env = new Scene();
    const sky = new Mesh(new SphereGeometry(10, 16, 8), new MeshBasicMaterial({ color: '#16253c', side: BackSide }));
    env.add(sky);
    const panels: [string, number, [number, number, number], number][] = [
      ['#9fb8de', 2.2, [0, 9, 0], 8],
      ['#ffb45e', 3.5, [-7, 2, 5], 3],
      ['#ffd8a8', 2.0, [7, 3, 4], 2.5],
    ];
    for (const [color, intensity, position, size] of panels) {
      const m = new Mesh(
        new PlaneGeometry(size, size),
        new MeshBasicMaterial({ color: new Color(color).multiplyScalar(intensity), side: BackSide }),
      );
      m.position.set(...position);
      m.lookAt(0, 0, 0);
      env.add(m);
    }
    const pmrem = new PMREMGenerator(gl);
    const target = pmrem.fromScene(env, 0.035);
    scene.environment = target.texture;
    scene.environmentIntensity = 0.3;
    return () => {
      scene.environment = null;
      target.dispose();
      pmrem.dispose();
      env.traverse((o) => {
        if (o instanceof Mesh) {
          o.geometry.dispose();
          (o.material as MeshBasicMaterial).dispose();
        }
      });
    };
  }, [gl, scene]);
  return null;
}

function Lights() {
  const moon = useRef<DirectionalLight>(null);
  const hemi = useRef<HemisphereLight>(null);
  const warm = useRef<PointLight>(null);
  const scene = useThree((s) => s.scene);
  const fog = useMemo(() => new FogExp2(SKY_HORIZON.getHex(), 0.02), []);
  const fogBase = useMemo(() => SKY_HORIZON.clone(), []);
  const fogStorm = useMemo(() => new Color('#7d8ea8'), []);

  useEffect(() => {
    scene.fog = fog;
    return () => {
      scene.fog = null;
    };
  }, [scene, fog]);

  useFrame(() => {
    const l = layoutRef.current;
    const reveal = ambience.reveal;
    const dim = 1 - ambience.dim * 0.8;
    const m = moon.current;
    if (m) {
      m.position.set(l.camTarget.x - 12, 20, 16);
      m.target.position.set(l.camTarget.x, 2, 0);
      m.target.updateMatrixWorld();
      m.intensity = (2.1 + ambience.starry * 0.6 + ambience.finale * 0.5) * reveal * dim;
    }
    const h = hemi.current;
    if (h) h.intensity = (0.72 + ambience.aurora * 0.5 + ambience.finale * 0.5) * reveal * dim;
    if (h) h.color.setRGB(0.36 + ambience.warm * 0.4, 0.48 + ambience.aurora * 0.35 + ambience.warm * 0.2, 0.86);
    const w = warm.current;
    if (w) {
      w.position.copy(spot.pos);
      w.intensity = spot.intensity * (1 + ambience.flash * 2);
    }
    fog.density = 0.02 + ambience.blizzard * 0.026 - ambience.finale * 0.004;
    // En blizzard, le brouillard blanchit : la tempête éclaire au lieu d'éteindre.
    fog.color.copy(fogBase).lerp(fogStorm, ambience.blizzard * 0.6);
  });

  return (
    <>
      <hemisphereLight ref={hemi} args={['#5c7bc4', '#121827', 0.6]} />
      <directionalLight
        ref={moon}
        color="#a9c2f2"
        intensity={1.9}
        castShadow
        shadow-mapSize={[quality.shadowMapSize, quality.shadowMapSize]}
        shadow-camera-left={-16}
        shadow-camera-right={16}
        shadow-camera-top={16}
        shadow-camera-bottom={-6}
        shadow-camera-near={1}
        shadow-camera-far={70}
        shadow-bias={-0.0004}
        shadow-normalBias={0.03}
        shadow-radius={5}
      />
      <pointLight ref={warm} color="#ffb45e" intensity={0} distance={16} decay={1.6} />
    </>
  );
}

export function Experience({ onStats }: { onStats: (s: DebugSample) => void }) {
  const modelReady = useApp((s) => s.modelReady);
  return (
    <>
      <CameraRig />
      <Lights />
      <ProceduralEnvironment />
      <Sky />
      <Landscape />
      <AdventTree />
      <Suspense fallback={null}>
        <Sherlock />
        <ModelReady />
      </Suspense>
      <Snow />
      <Sparkles />
      {modelReady && <Surprises />}
      <Effects />
      {params.debug && <DebugStats onSample={onStats} />}
    </>
  );
}

function ModelReady() {
  const setModelReady = useApp((s) => s.setModelReady);
  useEffect(() => {
    setModelReady();
  }, [setModelReady]);
  return null;
}
