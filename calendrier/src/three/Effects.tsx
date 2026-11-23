import { useFrame, useThree } from '@react-three/fiber';
import {
  BlendFunction,
  BloomEffect,
  EffectComposer,
  EffectPass,
  KernelSize,
  NoiseEffect,
  RenderPass,
  ToneMappingEffect,
  ToneMappingMode,
  VignetteEffect,
} from 'postprocessing';
import { useEffect, useMemo } from 'react';
import { HalfFloatType } from 'three';
import { quality } from '../lib/quality';
import { ambience } from './fx';

/** Chaîne d'image : bloom, tone mapping Neutral (Khronos), vignettage, grain. Rendu pris en main (priorité 1). */
export function Effects() {
  const gl = useThree((s) => s.gl);
  const scene = useThree((s) => s.scene);
  const camera = useThree((s) => s.camera);
  const size = useThree((s) => s.size);
  const dpr = useThree((s) => s.viewport.dpr);

  const { composer, bloom } = useMemo(() => {
    const c = new EffectComposer(gl, { multisampling: quality.multisampling, frameBufferType: HalfFloatType });
    c.addPass(new RenderPass(scene, camera));
    const b = new BloomEffect({
      mipmapBlur: true,
      intensity: 0.95,
      luminanceThreshold: 0.82,
      luminanceSmoothing: 0.18,
      radius: 0.78,
      kernelSize: KernelSize.LARGE,
    });
    const tone = new ToneMappingEffect({ mode: ToneMappingMode.NEUTRAL });
    const vignette = new VignetteEffect({ offset: 0.28, darkness: 0.62 });
    const noise = new NoiseEffect({ premultiply: true, blendFunction: BlendFunction.SOFT_LIGHT });
    noise.blendMode.opacity.value = 0.045;
    c.addPass(new EffectPass(camera, b, tone, vignette, noise));
    return { composer: c, bloom: b };
  }, [gl, scene, camera]);

  useEffect(() => () => composer.dispose(), [composer]);

  useEffect(() => {
    composer.setSize(size.width, size.height);
  }, [composer, size.width, size.height, dpr]);

  useFrame((_, delta) => {
    bloom.intensity = 0.95 + ambience.flash * 2.2 + ambience.finale * 0.35;
    composer.render(delta);
  }, 1);

  return null;
}
