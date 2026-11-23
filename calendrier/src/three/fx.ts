import { Vector3 } from 'three';
import { computeLayout, type Layout } from './layout';

/**
 * États mutables animés par GSAP et lus dans useFrame.
 * Rien ici ne déclenche de rendu React : c'est la « table de mixage » de la mise en scène.
 */
export interface BoxFx {
  door: number;
  hover: number;
  shake: number;
  lift: number;
  glow: number;
  squash: number;
  pulse: number;
}

export const boxFx: BoxFx[] = Array.from({ length: 24 }, () => ({
  door: 0,
  hover: 0,
  shake: 0,
  lift: 0,
  glow: 0,
  squash: 0,
  pulse: 0,
}));

export const shot = {
  pos: new Vector3(0, 30, 40),
  target: new Vector3(0, 8, 0),
  fov: 30,
  /** 1 = parallaxe complet, 0 = coupé (séquences cadrées). */
  parallax: 1,
  shake: 0,
};

export const ambience = {
  aurora: 0,
  warm: 0,
  blizzard: 0,
  starry: 0,
  finale: 0,
  dim: 0,
  flash: 0,
  /** Multiplicateur de vitesse de la neige (0 = suspendue). */
  snowSpeed: 1,
  /** Onde de choc du final, rayon en unités monde. */
  shock: 0,
  /** Révélation de la scène pendant l'intro (0 noir, 1 visible). */
  reveal: 0,
};

export const pointer = { x: 0, y: 0, gx: 0, gy: 0 };

export const layoutRef: { current: Layout } = { current: computeLayout(window.innerWidth / window.innerHeight) };

/** Centre de l'onde de choc du final. */
export const shockCenter = new Vector3();

/** Lumière chaude qui accompagne la case active. */
export const spot = { pos: new Vector3(), intensity: 0 };

/** Projection écran de chaque case (px CSS), écrite par le projecteur 3D, lue par les boutons accessibles. */
export const screenSlots = Array.from({ length: 24 }, () => ({ x: -999, y: -999, size: 0, visible: false }));
