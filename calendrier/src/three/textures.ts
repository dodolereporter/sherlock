import { CanvasTexture, LinearMipmapLinearFilter, SRGBColorSpace } from 'three';
import { rng } from './noise';

export const ATLAS_COLS = 6;
export const ATLAS_ROWS = 4;

/** Atlas des 24 chiffres, dessinés en Fraunces dorée sur fond transparent. */
export function createNumberAtlas(): CanvasTexture {
  const cell = 256;
  const canvas = document.createElement('canvas');
  canvas.width = cell * ATLAS_COLS;
  canvas.height = cell * ATLAS_ROWS;
  const ctx = canvas.getContext('2d');
  if (ctx) {
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    for (let i = 0; i < 24; i++) {
      const col = i % ATLAS_COLS;
      const row = Math.floor(i / ATLAS_COLS);
      const cx = col * cell + cell / 2;
      const cy = row * cell + cell / 2;
      const label = String(i + 1);
      ctx.font = `600 ${label.length > 1 ? 150 : 172}px "Fraunces Variable", Georgia, serif`;
      ctx.fillStyle = '#ffffff';
      ctx.fillText(label, cx, cy + 8);
      // Filet fin sous le chiffre.
      ctx.fillRect(cx - 30, cy + 92, 60, 5);
    }
  }
  const tex = new CanvasTexture(canvas);
  tex.colorSpace = SRGBColorSpace;
  tex.minFilter = LinearMipmapLinearFilter;
  tex.anisotropy = 4;
  tex.flipY = true;
  return tex;
}

/** Façade de porte : panneau en relief (map) et givre dans les coins (emissiveMap). */
export function createDoorTextures(): { map: CanvasTexture; frost: CanvasTexture } {
  const size = 512;
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d');
  if (ctx) {
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, size, size);
    // Fibres du bois peint.
    const random = rng(5);
    for (let i = 0; i < 220; i++) {
      const y = random() * size;
      ctx.strokeStyle = `rgba(0,0,0,${0.015 + random() * 0.03})`;
      ctx.lineWidth = 1 + random() * 2;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.bezierCurveTo(size * 0.3, y + random() * 8 - 4, size * 0.6, y + random() * 8 - 4, size, y + random() * 6 - 3);
      ctx.stroke();
    }
    // Panneau intérieur en creux.
    const inset = 44;
    ctx.strokeStyle = 'rgba(0,0,0,0.28)';
    ctx.lineWidth = 6;
    ctx.strokeRect(inset, inset, size - inset * 2, size - inset * 2);
    ctx.strokeStyle = 'rgba(255,255,255,0.35)';
    ctx.lineWidth = 3;
    ctx.strokeRect(inset + 5, inset + 5, size - inset * 2 - 10, size - inset * 2 - 10);
  }
  const frostCanvas = document.createElement('canvas');
  frostCanvas.width = size;
  frostCanvas.height = size;
  const fctx = frostCanvas.getContext('2d');
  if (fctx) {
    const ctx = fctx;
    const random = rng(9);
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, size, size);
    // Givre : cristaux en étoile concentrés dans les coins.
    const corners = [
      [0, 0],
      [size, 0],
      [0, size],
      [size, size],
    ] as const;
    for (const [cx, cy] of corners) {
      const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, size * 0.42);
      grad.addColorStop(0, 'rgba(235,244,255,0.85)');
      grad.addColorStop(0.45, 'rgba(225,238,255,0.25)');
      grad.addColorStop(1, 'rgba(225,238,255,0)');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, size, size);
      for (let i = 0; i < 70; i++) {
        const a = random() * Math.PI * 2;
        const r = Math.pow(random(), 1.8) * size * 0.34;
        const x = cx + Math.cos(a) * r;
        const y = cy + Math.sin(a) * r;
        const len = 4 + random() * 12;
        ctx.strokeStyle = `rgba(245,250,255,${0.35 + random() * 0.5})`;
        ctx.lineWidth = 1;
        for (let k = 0; k < 3; k++) {
          const b = (k * Math.PI) / 3 + a;
          ctx.beginPath();
          ctx.moveTo(x - Math.cos(b) * len, y - Math.sin(b) * len);
          ctx.lineTo(x + Math.cos(b) * len, y + Math.sin(b) * len);
          ctx.stroke();
        }
      }
    }
  }
  const map = new CanvasTexture(canvas);
  map.colorSpace = SRGBColorSpace;
  map.anisotropy = 4;
  const frost = new CanvasTexture(frostCanvas);
  frost.colorSpace = SRGBColorSpace;
  return { map, frost };
}
