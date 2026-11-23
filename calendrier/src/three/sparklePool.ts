import { Color, type BufferAttribute, type BufferGeometry, type Vector3 } from 'three';

export const POOL = 2600;

interface BurstOptions {
  count?: number;
  speed?: number;
  spread?: [number, number, number];
  colors?: string[];
  life?: [number, number];
  size?: [number, number];
  up?: number;
}

export const pool = {
  cursor: 0,
  time: 0,
  geometry: null as BufferGeometry | null,
};

/** Émet une gerbe de particules (une seule géométrie partagée, un seul appel de dessin). */
export function burst(origin: Vector3, options: BurstOptions = {}): void {
  const geo = pool.geometry;
  if (!geo) return;
  const {
    count = 120,
    speed = 3,
    spread = [1, 1, 1],
    colors = ['#ffd38a', '#ffb45e', '#fff4dc'],
    life = [0.9, 1.8],
    size = [0.08, 0.2],
    up = 0.6,
  } = options;
  const pos = geo.getAttribute('position') as BufferAttribute;
  const vel = geo.getAttribute('aVel') as BufferAttribute;
  const col = geo.getAttribute('aColor') as BufferAttribute;
  const lif = geo.getAttribute('aLife') as BufferAttribute;
  const c = new Color();
  for (let n = 0; n < count; n++) {
    const i = pool.cursor;
    pool.cursor = (pool.cursor + 1) % POOL;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    const r = speed * (0.35 + Math.random() * 0.65);
    pos.setXYZ(i, origin.x, origin.y, origin.z);
    vel.setXYZ(
      i,
      Math.sin(phi) * Math.cos(theta) * r * spread[0],
      (Math.cos(phi) * spread[1] + up) * r,
      Math.abs(Math.sin(phi) * Math.sin(theta)) * r * spread[2],
    );
    c.set(colors[Math.floor(Math.random() * colors.length)] ?? '#ffffff');
    col.setXYZ(i, c.r, c.g, c.b);
    lif.setXYZ(i, pool.time, life[0] + Math.random() * (life[1] - life[0]), size[0] + Math.random() * (size[1] - size[0]));
  }
  pos.needsUpdate = true;
  vel.needsUpdate = true;
  col.needsUpdate = true;
  lif.needsUpdate = true;
}
