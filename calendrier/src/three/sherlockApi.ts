import type { Vector3 } from 'three';

export type Step = { name: string; loop?: boolean };

export interface SherlockApi {
  /** Joue une suite d'animations ; la dernière boucle si `loop`, sinon retour à `repos`. */
  play: (steps: Step[] | string) => void;
  /** Point regardé (monde) ; null = suit le pointeur. */
  lookAt: (target: Vector3 | null) => void;
  /** Rotation du corps (radians, ajoutée à l'orientation de base). */
  turn: (yaw: number) => void;
}

/** Télécommande de Sherlock : le composant branche ses vraies fonctions au montage. */
export const sherlock: SherlockApi = {
  play: () => undefined,
  lookAt: () => undefined,
  turn: () => undefined,
};
