import gsap from 'gsap';
import { CustomEase } from 'gsap/CustomEase';
import { Vector3 } from 'three';
import { dayContent } from './content/days';
import { isUnlocked, waitMessage } from './lib/dates';
import { useApp } from './store';
import { ambience, boxFx, layoutRef, pointer, shot, spot } from './three/fx';
import { computeLayout, slotWorld } from './three/layout';
import { burst } from './three/sparklePool';
import { sherlock } from './three/sherlockApi';

gsap.registerPlugin(CustomEase);

// En navigation automatisée (captures Playwright à horloge pilotée), le temps avance par sauts :
// le lissage des à-coups de GSAP fausserait la chronologie des séquences.
if (navigator.webdriver) gsap.ticker.lagSmoothing(0);

/**
 * Courbes dessinées à la main pour la signature du projet.
 * - camera : départ très doux, arrivée longue (travelling feutré).
 * - door : la porte part sèchement, dépasse, revient.
 * - settle : retombée avec un rebond amorti.
 */
export const EASE = {
  camera: CustomEase.create('camera', 'M0,0 C0.62,0 0.18,1 1,1'),
  door: CustomEase.create('door', 'M0,0 C0.18,0 0.26,1.22 0.5,1.1 0.68,1.0 0.8,0.985 1,1'),
  settle: CustomEase.create('settle', 'M0,0 C0.12,0.6 0.2,1.12 0.38,1.06 0.55,0.99 0.7,1.01 1,1'),
  anticipate: CustomEase.create('anticipate', 'M0,0 C0.4,0 0.7,0.2 1,1'),
};

const reduced = () => useApp.getState().reducedMotion;

let cameraTween: gsap.core.Timeline | null = null;
let mainTimeline: gsap.core.Timeline | null = null;
let idleDrift: gsap.core.Tween | null = null;

function killMain() {
  mainTimeline?.kill();
  mainTimeline = null;
}

/** Plan principal (vue d'ensemble) selon la disposition courante. */
export function mainShot() {
  const l = layoutRef.current;
  return { pos: l.camPos.clone(), target: l.camTarget.clone(), fov: l.fov };
}

/**
 * Plan rapproché sur une case, avec Sherlock dans le cadre quand c'est possible.
 * Le contenu est calé dans la partie de l'écran que la carte ne couvre pas (gauche sur ordinateur, haut sur mobile).
 */
export function closeShot(day: number) {
  const l = layoutRef.current;
  const p = slotWorld(day, l);
  const aspect = window.innerWidth / window.innerHeight;
  const fov = l.portrait ? 38 : 30;
  const tanHalf = Math.tan((fov * Math.PI) / 360);
  if (l.portrait) {
    const top = p.y + 1.2;
    const bottom = p.y - 1.9;
    const halfH = (top - bottom) / 2;
    const dist = Math.max(halfH / (0.44 * tanHalf), 2.6 / (tanHalf * aspect), 9);
    const target = new Vector3(p.x * 0.6, (top + bottom) / 2 - dist * tanHalf * 0.48, p.z + 1.2);
    return { pos: target.clone().add(new Vector3(0, 0.6, dist)), target, fov };
  }
  const left = Math.min(l.sherlockPos.x - 2.8, p.x - 1.2);
  const right = p.x + 2.4;
  const top = Math.max(p.y + 1.0, 4.6);
  const bottom = Math.min(p.y - 1.4, 1.3);
  const halfW = (right - left) / 2;
  const halfH = (top - bottom) / 2;
  const dist = Math.max(halfW / (0.64 * tanHalf * aspect), halfH / (0.9 * tanHalf), 9);
  const target = new Vector3((left + right) / 2 + dist * tanHalf * aspect * 0.3, (top + bottom) / 2, 1.2);
  return { pos: target.clone().add(new Vector3(-1.2, 0.9, dist)), target, fov };
}

export function moveCamera(
  to: { pos: Vector3; target: Vector3; fov: number },
  duration: number,
  ease: string | gsap.EaseFunction = EASE.camera,
): gsap.core.Timeline {
  cameraTween?.kill();
  idleDrift?.kill();
  const tl = gsap.timeline();
  const d = reduced() ? Math.min(duration, 0.6) : duration;
  const e = reduced() ? 'sine.inOut' : ease;
  tl.to(shot.pos, { x: to.pos.x, y: to.pos.y, z: to.pos.z, duration: d, ease: e }, 0);
  tl.to(shot.target, { x: to.target.x, y: to.target.y, z: to.target.z, duration: d, ease: e }, 0);
  tl.to(shot, { fov: to.fov, duration: d, ease: e }, 0);
  cameraTween = tl;
  return tl;
}

/** Léger travelling avant une fois le plan posé : la caméra respire. */
function breathe(distance = 0.6, duration = 9) {
  if (reduced()) return;
  idleDrift?.kill();
  const dir = shot.target.clone().sub(shot.pos).normalize().multiplyScalar(distance);
  idleDrift = gsap.to(shot.pos, { x: `+=${dir.x}`, y: `+=${dir.y}`, z: `+=${dir.z}`, duration, ease: 'sine.inOut' });
}

/* ------------------------------------------------------------------ */
/* Disposition                                                          */
/* ------------------------------------------------------------------ */

export function onResize(aspect: number) {
  layoutRef.current = computeLayout(aspect);
  const { phase, activeDay } = useApp.getState();
  if (phase === 'idle') {
    const m = mainShot();
    shot.pos.copy(m.pos);
    shot.target.copy(m.target);
    shot.fov = m.fov;
  } else if ((phase === 'open' || phase === 'opening') && activeDay !== null && activeDay !== 24) {
    const c = closeShot(activeDay);
    shot.pos.copy(c.pos);
    shot.target.copy(c.target);
    shot.fov = c.fov;
  }
}

/* ------------------------------------------------------------------ */
/* Introduction                                                         */
/* ------------------------------------------------------------------ */

export function initDoors() {
  const { opened } = useApp.getState();
  boxFx.forEach((fx, i) => {
    const open = opened.includes(i + 1);
    fx.door = open ? 1 : 0;
    fx.glow = open ? 1 : 0;
  });
}

export function playIntro() {
  initDoors();
  const app = useApp.getState();
  app.setPhase('intro');
  const m = mainShot();
  killMain();

  if (reduced()) {
    shot.pos.copy(m.pos);
    shot.target.copy(m.target);
    shot.fov = m.fov;
    const tl = gsap.timeline({ onComplete: endIntro });
    tl.to(ambience, { reveal: 1, duration: 1.4, ease: 'sine.inOut' });
    tl.to({}, { duration: 1.2 });
    mainTimeline = tl;
    return;
  }

  // Départ : dans le ciel, la lune en vue, puis descente à la grue vers Sherlock.
  shot.pos.set(m.target.x - 6, m.target.y + 22, m.pos.z + 16);
  shot.target.set(m.target.x - 10, m.target.y + 26, -40);
  shot.fov = 44;
  shot.parallax = 0;
  ambience.reveal = 0;

  const tl = gsap.timeline({ onComplete: endIntro });
  tl.to(ambience, { reveal: 1, duration: 1.6, ease: 'power2.out' }, 0);
  tl.to(shot.target, { x: m.target.x, y: m.target.y, z: m.target.z, duration: 4.6, ease: EASE.camera }, 0.5);
  tl.to(shot.pos, { x: m.pos.x, y: m.pos.y, z: m.pos.z, duration: 5.0, ease: EASE.camera }, 0.5);
  tl.to(shot, { fov: m.fov, duration: 5.0, ease: 'power2.inOut' }, 0.5);

  // Les cases s'allument en cascade, de la base vers l'étoile.
  const order = [...boxFx.keys()].sort((a, b) => slotWorld(a + 1, layoutRef.current).y - slotWorld(b + 1, layoutRef.current).y);
  order.forEach((i, k) => {
    const fx = boxFx[i];
    if (!fx) return;
    tl.to(fx, { pulse: 1, duration: 0.22, ease: 'power2.out' }, 2.2 + k * 0.055);
    tl.to(fx, { pulse: 0, duration: 0.9, ease: 'expo.out' }, 2.42 + k * 0.055);
  });

  tl.call(() => sherlock.play([{ name: 'salut' }]), [], 4.3);
  tl.to(shot, { parallax: 1, duration: 1.5, ease: 'sine.inOut' }, 5.0);
  tl.to({}, { duration: 0.1 }, 6.4);
  mainTimeline = tl;
}

export function skipIntro() {
  if (useApp.getState().phase !== 'intro' || !mainTimeline) return;
  mainTimeline.progress(1);
}

function endIntro() {
  ambience.reveal = 1;
  shot.parallax = 1;
  boxFx.forEach((fx) => (fx.pulse = 0));
  mainTimeline = null;
  useApp.getState().setPhase('idle');
  breathe(0.4, 10);
}

/* ------------------------------------------------------------------ */
/* Survol et focus                                                      */
/* ------------------------------------------------------------------ */

let hovered: number | null = null;

export function hoverDay(day: number | null) {
  const app = useApp.getState();
  if (app.phase !== 'idle') day = null;
  if (day === hovered) return;
  const prev = hovered;
  hovered = day;
  document.body.style.cursor = day !== null ? 'pointer' : '';
  if (prev !== null) {
    const fx = boxFx[prev - 1];
    if (fx) gsap.to(fx, { hover: 0, duration: 0.4, ease: 'power3.out', overwrite: 'auto' });
  }
  if (day !== null) {
    const fx = boxFx[day - 1];
    if (fx) gsap.to(fx, { hover: 1, duration: reduced() ? 0.2 : 0.5, ease: 'back.out(2.4)', overwrite: 'auto' });
    const p = slotWorld(day, layoutRef.current);
    sherlock.lookAt(p);
    // Une lueur chaude vient caresser la case survolée.
    spot.pos.copy(p).add(new Vector3(0, 0.6, 1.6));
    gsap.to(spot, { intensity: isUnlocked(day) ? 5 : 2.5, duration: 0.4, ease: 'power2.out', overwrite: 'auto' });
  } else {
    sherlock.lookAt(null);
    if (app.phase === 'idle') gsap.to(spot, { intensity: 0, duration: 0.5, ease: 'power2.inOut', overwrite: 'auto' });
  }
}

/* ------------------------------------------------------------------ */
/* Clic                                                                 */
/* ------------------------------------------------------------------ */

export function clickDay(day: number) {
  const app = useApp.getState();
  if (app.phase === 'intro') {
    skipIntro();
    return;
  }
  if (app.phase !== 'idle') return;
  if (!isUnlocked(day)) refuse(day);
  else if (day === 24) void import('./finale').then((m) => m.playFinale());
  else openDay(day);
}

function refuse(day: number) {
  const fx = boxFx[day - 1];
  if (!fx) return;
  const p = slotWorld(day, layoutRef.current);
  useApp.getState().showToast(day, waitMessage(day));
  sherlock.lookAt(p);
  sherlock.play([{ name: 'desole' }]);
  if (reduced()) {
    gsap.fromTo(fx, { pulse: 0.6 }, { pulse: 0, duration: 0.8, ease: 'sine.out' });
    return;
  }
  const tl = gsap.timeline();
  tl.to(fx, { squash: 0.12, duration: 0.12, ease: 'power2.in' });
  tl.to(fx, { shake: 1, duration: 0.06, ease: 'none' }, 0.1);
  tl.to(fx, { squash: 0, duration: 0.6, ease: 'elastic.out(1, 0.35)' }, 0.22);
  tl.to(fx, { shake: 0, duration: 0.75, ease: 'power2.out' }, 0.2);
  tl.fromTo(shot, { shake: 0.06 }, { shake: 0, duration: 0.5, ease: 'power2.out' }, 0.12);
  tl.call(
    () =>
      burst(p.clone().add(new Vector3(0, 0, 0.7)), {
        count: 40,
        speed: 1.4,
        colors: ['#dfeaff', '#ffffff', '#b9cdf0'],
        life: [0.5, 1.0],
        size: [0.05, 0.12],
        up: 0.2,
      }),
    [],
    0.14,
  );
}

/** Réaction de Sherlock selon la surprise. */
function reactionFor(day: number): { name: string; loop?: boolean }[] {
  const s = dayContent(day).surprise;
  switch (s.kind) {
    case 'typo':
      return [{ name: 'parle_entree' }, { name: 'parle' }, { name: 'parle_sortie' }];
    case 'objet':
      return [{ name: 'reussite' }];
    case 'sherlock':
      return [{ name: 'alerte' }];
    case 'ambiance':
      return s.mood === 'blizzard'
        ? [{ name: 'inquiet_entree' }, { name: 'inquiet', loop: true }]
        : [{ name: 'reflechit_entree' }, { name: 'reflechit', loop: true }];
    case 'enigme':
      return [{ name: 'enquete_entree' }, { name: 'enquete', loop: true }];
    case 'scene':
      return [{ name: 'alerte' }, { name: 'reussite' }];
    case 'lanternes':
      return [{ name: 'idee' }];
    case 'feu':
      return [{ name: 'souleve_entree' }, { name: 'souleve' }, { name: 'atterrit' }];
    case 'final':
      return [{ name: 'reussite' }];
  }
}

/** Sortie propre de la boucle dans laquelle la surprise a laissé Sherlock. */
function exitFor(day: number): { name: string }[] {
  const s = dayContent(day).surprise;
  if (s.kind === 'enigme') return [{ name: 'enquete_sortie' }];
  if (s.kind === 'ambiance') return [{ name: s.mood === 'blizzard' ? 'inquiet_sortie' : 'reflechit_sortie' }];
  if (s.kind === 'sherlock' && s.action === 'dort') return [{ name: 'dort_sortie' }, { name: 'salut' }];
  return [{ name: 'salut' }];
}

export function openDay(day: number) {
  const app = useApp.getState();
  const fx = boxFx[day - 1];
  if (!fx) return;
  hoverDay(null);
  killMain();
  const already = app.opened.includes(day);
  app.setActiveDay(day);
  app.setRevealed(false);
  app.setPhase('opening');

  const p = slotWorld(day, layoutRef.current);
  const front = p.clone().add(new Vector3(0, 0, 0.75));
  sherlock.lookAt(p);
  sherlock.turn(layoutRef.current.portrait ? 0 : -0.2);

  const tl = gsap.timeline();
  mainTimeline = tl;
  const r = reduced();

  tl.to(shot, { parallax: 0.35, duration: 0.8, ease: 'sine.inOut' }, 0);
  tl.add(moveCamera(closeShot(day), 1.35), 0);
  spot.pos.copy(front).add(new Vector3(0, 0.4, 1.2));

  if (r) {
    tl.to(fx, { door: 1, glow: 1, duration: 0.8, ease: 'sine.inOut' }, 0.2);
    tl.to(spot, { intensity: 14, duration: 0.8, ease: 'sine.inOut' }, 0.2);
    tl.call(() => sherlock.play(reactionFor(day)), [], 0.4);
    tl.call(() => reveal(day), [], 0.9);
    return;
  }

  // Anticipation : Sherlock sort sa loupe, la case se tasse et frémit.
  tl.call(() => sherlock.play([{ name: 'enquete_entree' }, { name: 'enquete', loop: true }]), [], 0);
  tl.to(fx, { squash: 0.32, duration: 0.5, ease: EASE.anticipate }, 0.45);
  tl.to(fx, { shake: 0.35, duration: 0.4, ease: 'power1.in' }, 0.55);

  // Action : détente, la porte claque, la lumière jaillit.
  const hit = 0.98;
  tl.to(fx, { squash: -0.14, shake: 0, duration: 0.14, ease: 'power4.out' }, hit);
  tl.to(fx, { squash: 0, duration: 0.95, ease: 'elastic.out(1, 0.38)' }, hit + 0.14);
  if (!already) tl.to(fx, { door: 1, duration: 1.05, ease: EASE.door }, hit);
  tl.to(fx, { glow: 1, duration: 0.5, ease: 'power2.out' }, hit);
  tl.fromTo(fx, { pulse: 1 }, { pulse: 0, duration: 1.4, ease: 'expo.out' }, hit);
  tl.to(spot, { intensity: 26, duration: 0.12, ease: 'power2.out' }, hit);
  tl.to(spot, { intensity: 12, duration: 1.4, ease: 'expo.out' }, hit + 0.12);
  tl.fromTo(ambience, { flash: 0.35 }, { flash: 0, duration: 1.1, ease: 'expo.out' }, hit);
  tl.fromTo(shot, { shake: 0.05 }, { shake: 0, duration: 0.6, ease: 'power3.out' }, hit);
  tl.call(() => burst(front, { count: 160, speed: 3.6, spread: [1.1, 0.9, 1.4] }), [], hit + 0.02);
  tl.call(() => burst(front, { count: 60, speed: 1.4, size: [0.15, 0.3], life: [1.4, 2.4], up: 0.2 }), [], hit + 0.1);

  // Retombée : Sherlock réagit, la surprise et la typographie entrent.
  tl.call(() => sherlock.play(reactionFor(day)), [], hit + 0.35);
  tl.call(() => reveal(day), [], hit + 0.5);
}

function reveal(day: number) {
  const app = useApp.getState();
  app.markOpened(day);
  app.setRevealed(true);
  app.setPhase('open');
  mainTimeline = null;
  breathe(0.7, 10);
}

/* ------------------------------------------------------------------ */
/* Fermeture                                                            */
/* ------------------------------------------------------------------ */

export function closeDay() {
  const app = useApp.getState();
  if (app.phase !== 'open') return;
  const day = app.activeDay;
  app.setPhase('closing');
  killMain();
  const tl = gsap.timeline({
    onComplete: () => {
      const s = useApp.getState();
      s.setRevealed(false);
      s.setActiveDay(null);
      s.setPhase('idle');
      mainTimeline = null;
      breathe(0.4, 10);
    },
  });
  mainTimeline = tl;
  tl.add(moveCamera(mainShot(), 1.25), 0.25);
  tl.to(shot, { parallax: 1, duration: 1.2, ease: 'sine.inOut' }, 0.3);
  tl.to(spot, { intensity: 0, duration: 1.0, ease: 'power2.inOut' }, 0.2);
  tl.to(ambience, { aurora: 0, warm: 0, blizzard: 0, starry: 0, dim: 0, snowSpeed: 1, duration: 1.6, ease: 'sine.inOut' }, 0);
  if (day === 24) {
    tl.to(ambience, { finale: 0.35, shock: 0, duration: 1.6, ease: 'sine.inOut' }, 0);
    const { opened } = useApp.getState();
    boxFx.forEach((fx, i) => {
      if (!opened.includes(i + 1)) tl.to(fx, { door: 0, glow: 0, duration: 0.8, ease: 'power2.inOut' }, 0.4 + i * 0.02);
    });
  }
  tl.call(
    () => {
      sherlock.lookAt(null);
      sherlock.turn(0);
      sherlock.play(day !== null ? exitFor(day) : 'repos');
    },
    [],
    0.3,
  );
}

/* ------------------------------------------------------------------ */
/* Remise à zéro (sessions d'essai)                                     */
/* ------------------------------------------------------------------ */

export function resetAll() {
  const app = useApp.getState();
  if (app.phase !== 'idle') return;
  app.resetOpened();
  boxFx.forEach((fx, i) => {
    gsap.to(fx, { door: 0, glow: 0, duration: 0.6, delay: i * 0.025, ease: 'power3.inOut' });
  });
  gsap.to(ambience, { finale: 0, duration: 1, ease: 'sine.inOut' });
}

/* ------------------------------------------------------------------ */
/* Pointeur et gyroscope                                                */
/* ------------------------------------------------------------------ */

export function bindPointer(): () => void {
  const onMove = (e: PointerEvent) => {
    pointer.x = (e.clientX / window.innerWidth) * 2 - 1;
    pointer.y = -((e.clientY / window.innerHeight) * 2 - 1);
  };
  const onOrient = (e: DeviceOrientationEvent) => {
    if (e.gamma === null || e.beta === null) return;
    pointer.gx = Math.max(-1, Math.min(1, e.gamma / 25));
    pointer.gy = Math.max(-1, Math.min(1, (e.beta - 45) / 25));
  };
  window.addEventListener('pointermove', onMove, { passive: true });
  window.addEventListener('deviceorientation', onOrient, { passive: true });
  return () => {
    window.removeEventListener('pointermove', onMove);
    window.removeEventListener('deviceorientation', onOrient);
  };
}
