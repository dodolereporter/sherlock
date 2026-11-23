import gsap from 'gsap';
import { useEffect, useRef, useState } from 'react';
import { useApp } from '../store';

const ARMS = [0, 60, 120, 180, 240, 300];

/** Écran de chargement : un flocon se dessine au rythme du chargement, puis s'ouvre sur la scène. */
export function Loader({ ready, onDone }: { ready: boolean; onDone: () => void }) {
  const progress = useApp((s) => s.progress);
  const root = useRef<HTMLDivElement>(null);
  const flake = useRef<SVGSVGElement>(null);
  const [gone, setGone] = useState(false);
  const [shown, setShown] = useState(0);
  const shownRef = useRef(0);
  const reduced = useApp((s) => s.reducedMotion);
  const started = useRef(0);
  useEffect(() => {
    started.current = performance.now();
  }, []);

  // Affichage lissé du pourcentage.
  useEffect(() => {
    const target = ready ? 100 : Math.min(progress, 96);
    const obj = { v: shownRef.current };
    const tween = gsap.to(obj, {
      v: target,
      duration: 0.6,
      ease: 'power2.out',
      onUpdate: () => {
        shownRef.current = obj.v;
        setShown(obj.v);
      },
    });
    return () => {
      tween.kill();
    };
  }, [progress, ready]);

  useEffect(() => {
    if (!ready || gone) return;
    const wait = Math.max(0, 1.3 - (performance.now() - started.current) / 1000);
    const el = root.current;
    const svg = flake.current;
    const tl = gsap.timeline({ delay: wait + 0.25, onComplete: () => setGone(true) });
    tl.call(
      () => {
        // La scène devient interactive dès que le masque s'ouvre.
        if (el) el.style.pointerEvents = 'none';
        onDone();
      },
      [],
      0.35,
    );
    if (el && svg) {
      if (reduced) {
        tl.to(el, { opacity: 0, duration: 0.6, ease: 'sine.inOut' }, 0);
      } else {
        tl.to(svg, { rotate: 60, scale: 0.6, duration: 0.35, ease: 'back.in(2)' }, 0);
        tl.to(svg, { scale: 9, opacity: 0, duration: 0.9, ease: 'expo.in' }, 0.3);
        tl.to(el, { '--hole': '150%', duration: 1.3, ease: 'expo.inOut' }, 0.35);
        tl.to(el.querySelector('.loader__text'), { y: 16, opacity: 0, duration: 0.4, ease: 'power2.in' }, 0);
      }
    }
    return () => {
      tl.kill();
    };
  }, [ready, gone, onDone, reduced]);

  if (gone) return null;
  const k = shown / 100;
  return (
    <div className="loader" ref={root} role="status" aria-live="polite">
      <svg ref={flake} className="loader__flake" viewBox="-50 -50 100 100" aria-hidden="true">
        {ARMS.map((a, i) => {
          const local = Math.min(1, Math.max(0, k * 6 - i));
          return (
            <g key={a} transform={`rotate(${a})`} style={{ opacity: 0.25 + local * 0.75 }}>
              <path
                pathLength={1}
                strokeDasharray="1 1"
                strokeDashoffset={1 - local}
                d="M0 0 V-40 M0 -16 L-9 -25 M0 -16 L9 -25 M0 -29 L-6 -35 M0 -29 L6 -35"
              />
            </g>
          );
        })}
        <circle r={4 + k * 2} />
      </svg>
      <div className="loader__text">
        <span className="loader__eyebrow">Le calendrier de Sherlock</span>
        <span className="loader__pct">{Math.round(shown)}&thinsp;%</span>
        <span className="loader__hint">
          {k < 0.5 ? 'Sherlock enfile son écharpe…' : k < 1 ? 'La neige commence à tomber…' : 'C’est prêt.'}
        </span>
      </div>
    </div>
  );
}
