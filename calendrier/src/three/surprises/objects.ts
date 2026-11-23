import {
  CanvasTexture,
  CatmullRomCurve3,
  Color,
  CylinderGeometry,
  DoubleSide,
  Group,
  LatheGeometry,
  Mesh,
  MeshPhysicalMaterial,
  MeshStandardMaterial,
  RepeatWrapping,
  SphereGeometry,
  SRGBColorSpace,
  TorusGeometry,
  TubeGeometry,
  Vector2,
  Vector3,
  type BufferGeometry,
  type Material,
} from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import type { ObjectKind } from '../../content/days';
import { starGeometry } from '../geometries';

function canvasTexture(w: number, h: number, draw: (ctx: CanvasRenderingContext2D) => void): CanvasTexture {
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d');
  if (ctx) draw(ctx);
  const tex = new CanvasTexture(canvas);
  tex.colorSpace = SRGBColorSpace;
  tex.anisotropy = 4;
  return tex;
}

function mesh(geo: BufferGeometry, mat: Material, cast = true): Mesh {
  const m = new Mesh(geo, mat);
  m.castShadow = cast;
  return m;
}

/** Boule de Noël : verre laqué canneberge, frise dorée d'étoiles, attache. */
function boule(): Group {
  const g = new Group();
  const map = canvasTexture(1024, 512, (ctx) => {
    ctx.fillStyle = '#8e1f2e';
    ctx.fillRect(0, 0, 1024, 512);
    ctx.fillStyle = '#e8b964';
    ctx.fillRect(0, 236, 1024, 40);
    ctx.fillStyle = '#f3d08a';
    for (let i = 0; i < 16; i++) {
      const x = i * 64 + 32;
      for (const y of [150, 362]) {
        ctx.save();
        ctx.translate(x + (y > 256 ? 32 : 0), y);
        ctx.beginPath();
        for (let k = 0; k < 10; k++) {
          const r = k % 2 ? 9 : 22;
          const a = (k / 10) * Math.PI * 2 - Math.PI / 2;
          ctx.lineTo(Math.cos(a) * r, Math.sin(a) * r * 0.5);
        }
        ctx.fill();
        ctx.restore();
      }
    }
  });
  const glass = new MeshPhysicalMaterial({ map, roughness: 0.12, metalness: 0.35, clearcoat: 1, clearcoatRoughness: 0.08 });
  const gold = new MeshStandardMaterial({ color: '#e0b25c', metalness: 0.9, roughness: 0.28 });
  g.add(mesh(new SphereGeometry(0.62, 48, 32), glass));
  const cap = mesh(new CylinderGeometry(0.13, 0.15, 0.16, 20), gold);
  cap.position.y = 0.66;
  g.add(cap);
  const hook = mesh(new TorusGeometry(0.08, 0.018, 8, 24), gold);
  hook.position.y = 0.8;
  g.add(hook);
  return g;
}

/** Sucre d'orge : tube rayé rouge et blanc, crosse en arc. */
function sucre(): Group {
  const g = new Group();
  const pts: Vector3[] = [];
  for (let i = 0; i <= 10; i++) pts.push(new Vector3(0, -0.9 + i * 0.13, 0));
  for (let i = 1; i <= 14; i++) {
    const a = (i / 14) * Math.PI;
    pts.push(new Vector3(0.26 - Math.cos(a) * 0.26, 0.4 + Math.sin(a) * 0.3, 0));
  }
  const tube = new TubeGeometry(new CatmullRomCurve3(pts), 160, 0.085, 20, false);
  const map = canvasTexture(512, 64, (ctx) => {
    ctx.fillStyle = '#f7f1e6';
    ctx.fillRect(0, 0, 512, 64);
    ctx.fillStyle = '#c2192f';
    for (let x = -64; x < 576; x += 64) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x + 28, 0);
      ctx.lineTo(x + 28 + 40, 64);
      ctx.lineTo(x + 40, 64);
      ctx.fill();
    }
  });
  map.wrapS = RepeatWrapping;
  map.wrapT = RepeatWrapping;
  map.repeat.set(9, 1);
  const candy = new MeshPhysicalMaterial({ map, roughness: 0.22, clearcoat: 0.8, clearcoatRoughness: 0.15 });
  const m = mesh(tube, candy);
  m.position.x = -0.13;
  g.add(m);
  return g;
}

/** Flocon de glace : six branches facettées, reflets froids. */
function flocon(): Group {
  const g = new Group();
  const parts: BufferGeometry[] = [];
  for (let k = 0; k < 6; k++) {
    const a = (k / 6) * Math.PI * 2;
    const arm = new CylinderGeometry(0.045, 0.06, 0.9, 6);
    arm.translate(0, 0.45, 0);
    arm.rotateZ(a);
    parts.push(arm);
    for (const [d, len] of [
      [0.42, 0.26],
      [0.66, 0.18],
    ] as const) {
      for (const side of [-1, 1]) {
        const br = new CylinderGeometry(0.028, 0.035, len, 5);
        br.translate(0, len / 2, 0);
        br.rotateZ(side * 0.75);
        br.translate(0, d, 0);
        br.rotateZ(a);
        parts.push(br);
      }
    }
    const tip = new SphereGeometry(0.06, 8, 6);
    tip.translate(0, 0.92, 0);
    tip.rotateZ(a);
    parts.push(tip);
  }
  const hub = new CylinderGeometry(0.14, 0.14, 0.08, 6);
  hub.rotateX(Math.PI / 2);
  parts.push(hub);
  const geo = mergeGeometries(parts.map((p) => p.toNonIndexed()));
  geo.computeVertexNormals();
  const ice = new MeshPhysicalMaterial({
    color: '#cfe6ff',
    roughness: 0.08,
    metalness: 0.1,
    clearcoat: 1,
    emissive: new Color('#5aa8ff'),
    emissiveIntensity: 0.55,
    iridescence: 0.6,
  });
  g.add(mesh(geo, ice));
  return g;
}

/** Étoile en pain d'épices : biscuit épais et glaçage blanc sur le contour. */
function etoile(): Group {
  const g = new Group();
  const biscuit = new MeshStandardMaterial({ color: '#a3612c', roughness: 0.85 });
  g.add(mesh(starGeometry(0.78, 0.36, 0.16), biscuit));
  const outline: Vector3[] = [];
  for (let i = 0; i <= 10; i++) {
    const r = i % 2 === 0 ? 0.62 : 0.28;
    const a = (i / 10) * Math.PI * 2 + Math.PI / 2;
    outline.push(new Vector3(Math.cos(a) * r, Math.sin(a) * r, 0.17));
  }
  const icing = new MeshStandardMaterial({ color: '#fbf6ee', roughness: 0.45 });
  g.add(mesh(new TubeGeometry(new CatmullRomCurve3(outline, true, 'catmullrom', 0.1), 120, 0.03, 8, true), icing));
  const dot = new SphereGeometry(0.05, 12, 8);
  for (let i = 0; i < 5; i++) {
    const a = (i / 5) * Math.PI * 2 + Math.PI / 2;
    const m = mesh(dot, new MeshStandardMaterial({ color: i % 2 ? '#c2192f' : '#2b8a5a', roughness: 0.3 }));
    m.position.set(Math.cos(a) * 0.3, Math.sin(a) * 0.3, 0.19);
    g.add(m);
  }
  return g;
}

/** Cloche dorée et son ruban, battant suspendu (anime par le composant). */
function cloche(): Group {
  const g = new Group();
  const profile = [
    [0.0, 0.62],
    [0.12, 0.6],
    [0.24, 0.52],
    [0.3, 0.3],
    [0.34, 0.05],
    [0.44, -0.18],
    [0.58, -0.32],
    [0.62, -0.38],
    [0.58, -0.4],
  ].map(([x, y]) => new Vector2(x, y));
  const gold = new MeshPhysicalMaterial({ color: '#e5b34f', metalness: 1, roughness: 0.22, clearcoat: 0.6, side: DoubleSide });
  const bell = mesh(new LatheGeometry(profile, 48), gold);
  bell.name = 'bell';
  g.add(bell);
  const clapper = mesh(new SphereGeometry(0.1, 16, 12), gold);
  clapper.position.y = -0.38;
  clapper.name = 'clapper';
  g.add(clapper);
  const ribbon = new MeshStandardMaterial({ color: '#a51c2c', roughness: 0.5 });
  for (const side of [-1, 1]) {
    const loop = mesh(new TorusGeometry(0.17, 0.05, 10, 24), ribbon);
    loop.scale.set(1, 0.6, 0.6);
    loop.position.set(side * 0.17, 0.72, 0);
    loop.rotation.z = side * 0.4;
    g.add(loop);
  }
  const knot = mesh(new SphereGeometry(0.08, 12, 8), ribbon);
  knot.position.y = 0.7;
  g.add(knot);
  return g;
}

/** Tasse de chocolat chaud, crème et cannelle. La vapeur est émise par le composant. */
function chocolat(): Group {
  const g = new Group();
  const profile = [
    [0.0, -0.45],
    [0.4, -0.45],
    [0.46, -0.4],
    [0.5, 0.35],
    [0.53, 0.4],
    [0.47, 0.4],
    [0.44, -0.38],
    [0.0, -0.38],
  ].map(([x, y]) => new Vector2(x, y));
  const ceramic = new MeshPhysicalMaterial({ color: '#2b5547', roughness: 0.25, clearcoat: 0.7 });
  g.add(mesh(new LatheGeometry(profile, 48), ceramic));
  const handle = mesh(new TorusGeometry(0.2, 0.06, 12, 24, Math.PI * 1.3), ceramic);
  handle.position.set(0.52, -0.02, 0);
  handle.rotation.z = -Math.PI * 0.65;
  g.add(handle);
  const choc = mesh(new CylinderGeometry(0.45, 0.45, 0.02, 40), new MeshStandardMaterial({ color: '#4a2516', roughness: 0.35 }), false);
  choc.position.y = 0.32;
  g.add(choc);
  const cream = new MeshStandardMaterial({ color: '#fff8ec', roughness: 0.7 });
  const blobs: [number, number, number, number][] = [
    [0, 0.42, 0, 0.24],
    [0.16, 0.38, 0.08, 0.17],
    [-0.15, 0.38, -0.05, 0.16],
    [0.02, 0.55, 0.02, 0.14],
  ];
  for (const [x, y, z, r] of blobs) {
    const b = mesh(new SphereGeometry(r, 16, 12), cream);
    b.position.set(x, y, z);
    b.scale.y = 0.75;
    g.add(b);
  }
  const stick = mesh(new CylinderGeometry(0.03, 0.03, 0.7, 8), new MeshStandardMaterial({ color: '#7a3f1c', roughness: 0.9 }));
  stick.position.set(-0.22, 0.55, 0.1);
  stick.rotation.z = 0.5;
  g.add(stick);
  return g;
}

const BUILDERS: Record<ObjectKind, () => Group> = { boule, sucre, flocon, etoile, cloche, chocolat };

export function buildObject(kind: ObjectKind): Group {
  return BUILDERS[kind]();
}

export function disposeObject(root: Group): void {
  root.traverse((o) => {
    if (o instanceof Mesh) {
      o.geometry.dispose();
      const mats = Array.isArray(o.material) ? o.material : [o.material];
      for (const m of mats as MeshStandardMaterial[]) {
        m.map?.dispose();
        m.dispose();
      }
    }
  });
}
