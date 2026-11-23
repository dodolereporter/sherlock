import gsap from 'gsap';
import { useEffect, useRef } from 'react';
import { skipIntro } from '../director';
import { useApp } from '../store';
import { SplitLetters } from './split';

/** Grand titre de l'introduction et bouton pour la passer. */
export function IntroTitle() {
  const phase = useApp((s) => s.phase);
  const reduced = useApp((s) => s.reducedMotion);
  const root = useRef<HTMLDivElement>(null);
  const skip = useRef<HTMLButtonElement>(null);
  const visible = phase === 'intro';

  useEffect(() => {
    const el = root.current;
    if (!el || !visible) return;
    const chars = el.querySelectorAll('.intro__title .split-char');
    const tl = gsap.timeline();
    if (reduced) {
      tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: 0.8, ease: 'sine.out' });
    } else {
      tl.fromTo(
        el.querySelector('.intro__eyebrow'),
        { opacity: 0, letterSpacing: '0.9em' },
        { opacity: 1, letterSpacing: '0.42em', duration: 1.6, ease: 'expo.out' },
        1.0,
      );
      tl.fromTo(
        chars,
        { yPercent: 110, rotate: 8, opacity: 0, filter: 'blur(8px)' },
        { yPercent: 0, rotate: 0, opacity: 1, filter: 'blur(0px)', duration: 1.1, ease: 'expo.out', stagger: 0.035 },
        1.25,
      );
      tl.fromTo(el.querySelector('.intro__rule'), { scaleX: 0 }, { scaleX: 1, duration: 1.2, ease: 'expo.inOut' }, 1.9);
      tl.fromTo(el.querySelector('.intro__sub'), { y: 14, opacity: 0 }, { y: 0, opacity: 1, duration: 0.9, ease: 'power3.out' }, 2.3);
      // Sortie : le titre s'élève et se dissout pendant que la caméra se pose.
      tl.to(chars, { yPercent: -60, opacity: 0, filter: 'blur(6px)', duration: 0.7, ease: 'power3.in', stagger: 0.015 }, 4.9);
      tl.to(
        [el.querySelector('.intro__eyebrow'), el.querySelector('.intro__sub'), el.querySelector('.intro__rule')],
        { opacity: 0, y: -12, duration: 0.5, ease: 'power2.in' },
        4.95,
      );
    }
    if (skip.current) gsap.fromTo(skip.current, { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.6, delay: 1.2, ease: 'power3.out' });
    return () => {
      tl.kill();
    };
  }, [visible, reduced]);

  useEffect(() => {
    if (!visible) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' || e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        skipIntro();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [visible]);

  if (!visible) return null;
  return (
    <>
      <div className="intro" ref={root} aria-live="polite">
        <span className="intro__eyebrow">Décembre 2026</span>
        <h1 className="intro__title">
          <SplitLetters text="Le calendrier" className="intro__line" />
          <SplitLetters text="de Sherlock" className="intro__line intro__line--em" />
        </h1>
        <span className="intro__rule" aria-hidden="true" />
        <span className="intro__sub">Vingt-quatre cases, une enquête par soir</span>
      </div>
      <button ref={skip} className="skip" onClick={skipIntro} autoFocus>
        Passer l’intro <kbd>Échap</kbd>
      </button>
    </>
  );
}
