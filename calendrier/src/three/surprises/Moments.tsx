import gsap from 'gsap';
import { useEffect } from 'react';
import type { Mood } from '../../content/days';
import { moveCamera } from '../../director';
import { useApp } from '../../store';
import { ambience, shot } from '../fx';
import { sherlock } from '../sherlockApi';
import { sherlockShot, skyShot, groundShot, yawTowardCamera } from '../shots';

/** Sherlock joue une de ses animations de thème, cadré en plan rapproché. */
export function SherlockAction({ action }: { action: 'theme_objet' | 'theme_special' | 'dort' }) {
  useEffect(() => {
    const target = sherlockShot();
    const tl = gsap.timeline();
    tl.add(moveCamera(target, 1.4), 0);
    sherlock.lookAt(null);
    if (action === 'theme_special') {
      // Il se tourne vers nous, ramasse, vise… et la boule s'écrase sur l'écran.
      tl.call(() => sherlock.turn(yawTowardCamera(target.pos)), [], 0.2);
      tl.call(() => sherlock.play([{ name: 'theme_special' }, { name: 'ploc' }, { name: 'desole' }]), [], 0.7);
      tl.call(() => useApp.getState().fireScreenEvent('splat'), [], 0.7 + 2.02);
      tl.fromTo(shot, { shake: 0.05 }, { shake: 0, duration: 0.5, ease: 'power3.out' }, 0.7 + 2.02);
    } else if (action === 'theme_objet') {
      tl.call(() => sherlock.turn(yawTowardCamera(target.pos) * 0.6), [], 0.2);
      tl.call(() => sherlock.play([{ name: 'theme_objet' }, { name: 'reussite' }]), [], 0.6);
    } else {
      tl.to(ambience, { dim: 0.35, starry: 0.5, duration: 2.5, ease: 'sine.inOut' }, 0);
      tl.call(() => sherlock.play([{ name: 'dort_entree' }, { name: 'dort', loop: true }]), [], 0.6);
    }
    return () => {
      tl.kill();
    };
  }, [action]);
  return null;
}

/** Changement de ciel et de lumière. */
export function Ambiance({ mood }: { mood: Mood }) {
  useEffect(() => {
    const tl = gsap.timeline();
    if (mood === 'aurore') {
      tl.add(moveCamera(skyShot(), 2.4), 0);
      tl.to(ambience, { aurora: 1, dim: 0.25, duration: 3.2, ease: 'power2.inOut' }, 0.2);
    } else if (mood === 'etoiles') {
      tl.add(moveCamera(skyShot(), 2.4), 0);
      tl.to(ambience, { starry: 1, dim: 0.4, duration: 2.6, ease: 'power2.inOut' }, 0.2);
    } else {
      tl.add(moveCamera(groundShot(), 1.6), 0);
      tl.to(ambience, { blizzard: 1, duration: 2.2, ease: 'power3.in' }, 0);
      tl.fromTo(shot, { shake: 0 }, { shake: 0.025, duration: 2.2, ease: 'power2.in' }, 0);
      tl.to(shot, { shake: 0.008, duration: 3, ease: 'sine.inOut', repeat: -1, yoyo: true }, 2.2);
    }
    return () => {
      tl.kill();
      gsap.to(shot, { shake: 0, duration: 0.6 });
    };
  }, [mood]);
  return null;
}

/** Cadrage pour les petites scènes et les ciels. */
export function Reframe({ to }: { to: 'sky' | 'ground' }) {
  useEffect(() => {
    const tl = moveCamera(to === 'sky' ? skyShot() : groundShot(), 2.0);
    return () => {
      tl.kill();
    };
  }, [to]);
  return null;
}
