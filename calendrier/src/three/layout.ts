import { Vector3 } from 'three';

/** Taille d'une case et pas de la grille du sapin. */
export const BOX = 1.18;
export const STAR_BOX = 1.5;
export const PITCH_X = 1.36;
export const PITCH_Y = 1.42;

/** Disposition du sapin, de bas en haut : le tronc, cinq étages, l'étoile. */
export const ROWS: readonly (readonly number[])[] = [
  [9, 1, 16],
  [5, 19, 11, 2, 22, 14],
  [13, 7, 20, 3, 17],
  [21, 10, 4, 15],
  [8, 18, 12],
  [6, 23],
  [24],
];

export interface Slot {
  day: number;
  row: number;
  col: number;
  /** Position locale du centre de la case dans le groupe du sapin. */
  local: Vector3;
  size: number;
  /** 0 canneberge, 1 sapin, 2 crème, 3 or (étoile). */
  tint: number;
}

export const SLOTS: Slot[] = (() => {
  const out: Slot[] = [];
  ROWS.forEach((row, r) => {
    row.forEach((day, c) => {
      const isStar = day === 24;
      const size = isStar ? STAR_BOX : BOX;
      const x = (c - (row.length - 1) / 2) * PITCH_X;
      const y = BOX / 2 + r * PITCH_Y + (isStar ? (STAR_BOX - BOX) / 2 + 0.06 : 0);
      out.push({ day, row: r, col: c, local: new Vector3(x, y, 0), size, tint: isStar ? 3 : (r * 2 + c) % 3 });
    });
  });
  return out.sort((a, b) => a.day - b.day);
})();

export function slotOf(day: number): Slot {
  const slot = SLOTS[day - 1];
  if (!slot) throw new Error(`Case inconnue : ${day}`);
  return slot;
}

/** Étagères (branches) sous chaque étage, sauf sous le tronc. */
export const SHELVES = ROWS.slice(1, 6).map((row, i) => ({
  y: (i + 1) * PITCH_Y - 0.08,
  width: row.length * PITCH_X + 0.5,
}));

export interface Layout {
  portrait: boolean;
  treeOffset: Vector3;
  sherlockPos: Vector3;
  sherlockYaw: number;
  /** Plan principal de la caméra. */
  camPos: Vector3;
  camTarget: Vector3;
  fov: number;
}

const TREE_TOP = ROWS.length * PITCH_Y + 1.0;

/**
 * Cadrage principal calculé pour que tout tienne : du pied de Sherlock à l'étoile, de Sherlock au bord du sapin.
 */
export function computeLayout(aspect: number): Layout {
  const portrait = aspect < 0.85;
  const fov = portrait ? 40 : 32;
  const tanHalf = Math.tan((fov * Math.PI) / 360);
  if (portrait) {
    const treeOffset = new Vector3(0, 3.7, -1.4);
    const sherlockPos = new Vector3(-0.2, 0, 4.2);
    const top = treeOffset.y + TREE_TOP + 0.4;
    const bottom = -2.4;
    const halfH = (top - bottom) / 2;
    const halfW = (6 * PITCH_X + 1.0) / 2;
    const dist = Math.max(halfH / tanHalf, halfW / (tanHalf * aspect));
    const target = new Vector3(0, (top + bottom) / 2, 0);
    return { portrait, treeOffset, sherlockPos, sherlockYaw: 0.1, camPos: new Vector3(0, target.y - 0.6, dist), camTarget: target, fov };
  }
  const treeOffset = new Vector3(1.9, 0.45, 0);
  const sherlockPos = new Vector3(-4.1, 0, 3.4);
  const top = treeOffset.y + TREE_TOP + 0.3;
  const bottom = -2.2;
  const left = sherlockPos.x - 2.6;
  const right = treeOffset.x + 3 * PITCH_X + 1.0;
  const halfH = (top - bottom) / 2;
  const halfW = (right - left) / 2;
  const dist = Math.max(halfH / tanHalf, halfW / (tanHalf * aspect));
  const target = new Vector3((left + right) / 2, (top + bottom) / 2, 0);
  return {
    portrait,
    treeOffset,
    sherlockPos,
    sherlockYaw: 0.38,
    camPos: new Vector3(target.x - 0.8, target.y - 0.4, dist),
    camTarget: target,
    fov,
  };
}

/** Position monde du centre d'une case pour une disposition donnée. */
export function slotWorld(day: number, layout: Layout, out = new Vector3()): Vector3 {
  return out.copy(slotOf(day).local).add(layout.treeOffset);
}
