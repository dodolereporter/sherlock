import gsap from 'gsap';
import { useEffect, useRef } from 'react';
import { resetAll } from '../director';
import { formatToday, isUnlocked } from '../lib/dates';
import { params } from '../lib/params';
import { isTrialSession } from '../lib/storage';
import { useApp } from '../store';
import { SplitLetters } from './split';

const coarse = window.matchMedia('(pointer: coarse)').matches;

export function Hud() {
  const phase = useApp((s) => s.phase);
  const opened = useApp((s) => s.opened);
  const reduced = useApp((s) => s.reducedMotion);
  const root = useRef<HTMLElement>(null);
  const shown = phase !== 'loading' && phase !== 'intro';
  const quiet = phase === 'opening' || phase === 'open';
  const available = Array.from({ length: 24 }, (_, i) => i + 1).filter((d) => isUnlocked(d)).length;
  const pct = opened.length / 24;

  useEffect(() => {
    const el = root.current;
    if (!el || !shown) return;
    const tl = gsap.timeline();
    if (reduced) {
      tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: 0.6 });
    } else {
      tl.fromTo(
        el.querySelectorAll('.hud__title .split-char'),
        { yPercent: 100, opacity: 0 },
        { yPercent: 0, opacity: 1, duration: 0.8, ease: 'expo.out', stagger: 0.018 },
      );
      tl.fromTo(
        el.querySelectorAll('.hud__reveal'),
        { y: 12, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.7, ease: 'power3.out', stagger: 0.07 },
        0.2,
      );
    }
    return () => {
      tl.kill();
    };
  }, [shown, reduced]);

  if (!shown) return null;
  const trialLabel = params.demo ? 'Mode démo : tout est ouvert' : params.date ? `Date simulée : ${formatToday()}` : null;
  return (
    <header className={`hud${quiet ? ' hud--quiet' : ''}`} ref={root}>
      <div className="hud__brand">
        <span className="hud__eyebrow hud__reveal">Décembre 2026</span>
        <h1 className="hud__title">
          <SplitLetters text="Le calendrier de Sherlock" />
        </h1>
        <div className="hud__todaywrap">
          <p className="hud__today hud__reveal">
            {available === 0 ? `Nous sommes le ${formatToday()}. Première case le 1er décembre.` : `Nous sommes le ${formatToday()}.`}
          </p>
        </div>
      </div>
      <div className="hud__side hud__reveal">
        <div className="progress" role="img" aria-label={`${opened.length} cases ouvertes sur 24`}>
          <svg viewBox="0 0 44 44" aria-hidden="true">
            <circle className="progress__track" cx="22" cy="22" r="19" />
            <circle className="progress__bar" cx="22" cy="22" r="19" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - pct} />
          </svg>
          <span className="progress__count">
            {opened.length}
            <small>/24</small>
          </span>
        </div>
        {trialLabel && (
          <div className="trial">
            <span>{trialLabel}</span>
            {isTrialSession && (
              <button className="trial__reset" onClick={resetAll} disabled={phase !== 'idle' || opened.length === 0}>
                Tout refermer
              </button>
            )}
          </div>
        )}
      </div>
      <div className="hud__hintwrap">
        <p className="hud__hint hud__reveal" aria-hidden="true">
          {coarse ? 'Touchez une case pour l’ouvrir' : 'Cliquez une case ou naviguez au clavier (Tab, flèches)'}
        </p>
      </div>
    </header>
  );
}
