import gsap from 'gsap';
import { Vector3 } from 'three';
import { EASE, moveCamera } from './director';
import { useApp } from './store';
import { ambience, boxFx, layoutRef, shockCenter, shot, spot } from './three/fx';
import { slotWorld, SLOTS } from './three/layout';
import { burst } from './three/sparklePool';
import { sherlock } from './three/sherlockApi';
import { finaleShot } from './three/shots';

/**
 * Case 24 : le grand final.
 * Anticipation (la neige se fige, la scène s'éteint, une vague de lumière monte le sapin),
 * action (l'étoile éclate, onde de choc, toutes les portes s'ouvrent),
 * retombée (aurore, feux, grand mouvement de grue, typographie).
 */
export function playFinale() {
  const app = useApp.getState();
  if (app.phase !== 'idle') return;
  app.setActiveDay(24);
  app.setRevealed(false);
  app.setPhase('opening');
  const reduced = app.reducedMotion;
  const l = layoutRef.current;
  const star = slotWorld(24, l);
  const front = star.clone().add(new Vector3(0, 0, 1));
  sherlock.lookAt(star);
  sherlock.turn(l.portrait ? 0 : -0.25);
  spot.pos.copy(front).add(new Vector3(0, 0.4, 1.4));

  const tl = gsap.timeline();
  const byHeight = [...SLOTS].sort((a, b) => a.local.y - b.local.y || a.local.x - b.local.x);

  if (reduced) {
    tl.add(moveCamera(finaleShot(), 1.2), 0);
    tl.to(ambience, { finale: 1, aurora: 0.6, warm: 0.6, duration: 2.4, ease: 'sine.inOut' }, 0);
    tl.call(() => useApp.getState().fireScreenEvent('flash'), [], 0.6);
    byHeight.forEach((slot, k) => {
      const fx = boxFx[slot.day - 1];
      if (fx) tl.to(fx, { door: 1, glow: 1, duration: 0.8, ease: 'sine.inOut' }, 0.4 + k * 0.03);
    });
    tl.call(() => sherlock.play([{ name: 'reussite' }]), [], 0.8);
    tl.call(reveal, [], 1.6);
    return;
  }

  // 1. Anticipation (0 → 3.2 s).
  tl.to(ambience, { dim: 0.85, duration: 2.0, ease: 'power2.inOut' }, 0);
  tl.to(ambience, { snowSpeed: 0, duration: 2.4, ease: 'power3.inOut' }, 0.2);
  tl.to(shot, { parallax: 0, duration: 1.0, ease: 'sine.inOut' }, 0);
  const closeTarget = star.clone().add(new Vector3(0, l.portrait ? -1.2 : -0.6, 0.6));
  const closePos = closeTarget.clone().add(new Vector3(l.portrait ? 0 : -1.4, -1.6, l.portrait ? 12 : 10));
  tl.add(moveCamera({ pos: closePos, target: closeTarget, fov: l.portrait ? 40 : 30 }, 3.0, 'power2.inOut'), 0);
  tl.call(() => sherlock.play([{ name: 'reflechit_entree' }, { name: 'reflechit', loop: true }]), [], 0.1);

  // Vague de lumière qui monte le sapin et converge vers l'étoile.
  byHeight.forEach((slot) => {
    const fx = boxFx[slot.day - 1];
    if (!fx || slot.day === 24) return;
    const at = 0.7 + slot.row * 0.3 + Math.abs(slot.local.x) * 0.03;
    tl.to(fx, { pulse: 1, duration: 0.25, ease: 'power2.out' }, at);
    tl.to(fx, { pulse: 0, duration: 0.8, ease: 'expo.out' }, at + 0.25);
  });
  const starFx = boxFx[23];
  if (!starFx) return;
  tl.to(starFx, { squash: 0.42, duration: 0.7, ease: EASE.anticipate }, 2.55);
  tl.to(starFx, { shake: 0.8, duration: 0.7, ease: 'power2.in' }, 2.55);
  tl.to(starFx, { pulse: 1.2, duration: 0.7, ease: 'power2.in' }, 2.55);

  // 2. Action (3.25 s).
  const hit = 3.25;
  tl.to(starFx, { squash: -0.25, shake: 0, duration: 0.12, ease: 'power4.out' }, hit);
  tl.to(starFx, { squash: 0, duration: 1.1, ease: 'elastic.out(1, 0.3)' }, hit + 0.12);
  tl.to(starFx, { door: 1, glow: 1, duration: 0.9, ease: EASE.door }, hit);
  tl.to(starFx, { pulse: 0, duration: 2, ease: 'expo.out' }, hit + 0.2);
  tl.call(
    () => {
      useApp.getState().fireScreenEvent('flash');
      shockCenter.copy(star);
      burst(front, { count: 320, speed: 7, spread: [1.4, 1.2, 1.2], size: [0.1, 0.3], life: [1.4, 2.8] });
      burst(front, { count: 120, speed: 2.5, colors: ['#ffffff', '#cfe2ff'], size: [0.15, 0.35], life: [2, 3.4], up: 0.1 });
    },
    [],
    hit,
  );
  tl.fromTo(ambience, { flash: 1 }, { flash: 0, duration: 2.2, ease: 'expo.out' }, hit);
  tl.fromTo(ambience, { shock: 0 }, { shock: 70, duration: 3.2, ease: 'power2.out' }, hit);
  tl.fromTo(shot, { shake: 0.14 }, { shake: 0, duration: 1.2, ease: 'power3.out' }, hit);
  tl.to(ambience, { dim: 0, duration: 1.0, ease: 'power2.out' }, hit);
  tl.to(ambience, { finale: 1, aurora: 0.5, warm: 0.4, duration: 3, ease: 'power2.out' }, hit);
  tl.to(ambience, { snowSpeed: 1, duration: 3.5, ease: 'power2.inOut' }, hit + 0.6);
  tl.fromTo(spot, { intensity: 0 }, { intensity: 60, duration: 0.15, ease: 'power2.out' }, hit);
  tl.to(spot, { intensity: 18, duration: 2, ease: 'expo.out' }, hit + 0.15);
  tl.call(
    () => sherlock.play([{ name: 'souleve_entree' }, { name: 'souleve' }, { name: 'atterrit' }, { name: 'reussite' }]),
    [],
    hit + 0.1,
  );

  // Toutes les portes s'ouvrent en cascade, de l'étoile vers le tronc.
  [...byHeight].reverse().forEach((slot, k) => {
    const fx = boxFx[slot.day - 1];
    if (!fx || slot.day === 24) return;
    tl.to(fx, { door: 1, duration: 0.9, ease: EASE.door }, hit + 0.25 + k * 0.045);
    tl.to(fx, { glow: 1, duration: 0.6, ease: 'power2.out' }, hit + 0.25 + k * 0.045);
  });

  // 3. Retombée : grand mouvement de grue vers le plan large.
  tl.add(moveCamera(finaleShot(), 4.6, EASE.camera), hit + 0.9);
  tl.call(reveal, [], hit + 1.6);
  tl.to(shot, { parallax: 0.6, duration: 2, ease: 'sine.inOut' }, hit + 4);
}

function reveal() {
  const app = useApp.getState();
  app.markOpened(24);
  app.setRevealed(true);
  app.setPhase('open');
}
