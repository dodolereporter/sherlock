/** Réglages de qualité choisis une fois au démarrage selon l'appareil. */
export interface Quality {
  tier: 'high' | 'low';
  maxDpr: number;
  shadowMapSize: number;
  snowCount: number;
  multisampling: number;
  forestCount: number;
}

function detect(): Quality {
  const coarse = window.matchMedia('(pointer: coarse)').matches;
  const small = Math.min(window.innerWidth, window.innerHeight) < 700;
  const cores = navigator.hardwareConcurrency || 4;
  const low = coarse || small || cores <= 4;
  return low
    ? { tier: 'low', maxDpr: 1.5, shadowMapSize: 1024, snowCount: 3500, multisampling: 0, forestCount: 46 }
    : { tier: 'high', maxDpr: 2, shadowMapSize: 2048, snowCount: 7000, multisampling: 4, forestCount: 70 };
}

export const quality: Quality = detect();

export const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
