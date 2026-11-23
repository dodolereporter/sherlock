import gsap from 'gsap';
import { useEffect, useRef } from 'react';
import { dayContent } from '../content/days';
import { closeDay } from '../director';
import { useApp } from '../store';
import { SplitLetters, SplitWords } from './split';

/** Message typographique plein écran (cases « Message »). */
function TypoOverlay({ lines, closing }: { lines: readonly string[]; closing: boolean }) {
  const root = useRef<HTMLDivElement>(null);
  const reduced = useApp((s) => s.reducedMotion);
  useEffect(() => {
    const el = root.current;
    if (!el) return;
    const tl = gsap.timeline();
    if (reduced) {
      tl.fromTo(el.querySelectorAll('.typo__line'), { opacity: 0 }, { opacity: 1, duration: 0.8, stagger: 0.5, ease: 'sine.inOut' });
    } else {
      el.querySelectorAll('.typo__line').forEach((line, i) => {
        const at = 0.15 + i * 0.75;
        tl.fromTo(
          line.querySelectorAll('.split-char'),
          { yPercent: 120, rotate: (i % 2 ? -1 : 1) * 10, opacity: 0 },
          { yPercent: 0, rotate: 0, opacity: 1, duration: 1.0, ease: 'expo.out', stagger: 0.026 },
          at,
        );
        tl.fromTo(line.querySelector('.typo__underline'), { scaleX: 0 }, { scaleX: 1, duration: 0.9, ease: 'expo.inOut' }, at + 0.45);
      });
      tl.to(el, { y: -10, duration: 6, ease: 'sine.inOut' }, 0);
    }
    return () => {
      tl.kill();
    };
  }, [reduced]);
  useEffect(() => {
    const el = root.current;
    if (!closing || !el) return;
    const t = gsap.to(el.querySelectorAll('.split-char'), { yPercent: -80, opacity: 0, duration: 0.35, ease: 'power2.in', stagger: 0.004 });
    return () => {
      t.kill();
    };
  }, [closing]);
  return (
    <div className="typo" ref={root} aria-hidden="true">
      {lines.map((line, i) => (
        <p className={`typo__line typo__line--${i}`} key={line}>
          <SplitLetters text={line} />
          <span className="typo__underline" />
        </p>
      ))}
    </div>
  );
}

/** Boule de neige qui s'écrase sur l'écran (case 10). */
function Splat({ id }: { id: number }) {
  const root = useRef<HTMLDivElement>(null);
  const reduced = useApp((s) => s.reducedMotion);
  useEffect(() => {
    const el = root.current;
    if (!el) return;
    const tl = gsap.timeline();
    if (reduced) {
      tl.fromTo(el, { opacity: 0 }, { opacity: 0.9, duration: 0.3 }).to(el, { opacity: 0, duration: 1.2, delay: 1.6 });
    } else {
      tl.fromTo(el, { scale: 0.2, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.16, ease: 'power4.out' });
      tl.fromTo(el.querySelectorAll('.splat__bit'), { scale: 0 }, { scale: 1, duration: 0.3, ease: 'back.out(3)', stagger: 0.01 }, 0.05);
      tl.to(el.querySelectorAll('.splat__drip'), { y: 'random(60, 160)', duration: 2.6, ease: 'power1.in', stagger: 0.12 }, 0.4);
      tl.to(el, { opacity: 0, filter: 'blur(6px)', duration: 1.2, ease: 'power2.in' }, 2.6);
    }
    return () => {
      tl.kill();
    };
  }, [id, reduced]);
  const bits = Array.from({ length: 14 }, (_, i) => {
    const a = (i / 14) * Math.PI * 2 + (i % 3) * 0.3;
    const r = 70 + ((i * 37) % 50);
    return { x: Math.cos(a) * r, y: Math.sin(a) * r, s: 10 + ((i * 13) % 18) };
  });
  return (
    <div className="splat" ref={root} aria-hidden="true">
      <svg viewBox="-160 -160 320 320">
        <defs>
          <radialGradient id="splat-g" cx="40%" cy="38%" r="70%">
            <stop offset="0" stopColor="#ffffff" />
            <stop offset="0.7" stopColor="#e6eef8" />
            <stop offset="1" stopColor="#b8c9de" />
          </radialGradient>
        </defs>
        <path
          fill="url(#splat-g)"
          d="M-62 -20 C-70 -70 -20 -82 6 -66 C30 -92 78 -66 66 -28 C98 -10 88 40 52 46 C48 86 -2 92 -20 64 C-56 84 -92 46 -70 18 C-100 0 -88 -30 -62 -20Z"
        />
        {bits.map((b, i) => (
          <circle className="splat__bit" key={i} cx={b.x} cy={b.y} r={b.s / 2} fill="#eef4fb" />
        ))}
        {[-30, 8, 40].map((x, i) => (
          <g className="splat__drip" key={x}>
            <path fill="#e6eef8" d={`M${x - 7} 40 Q${x} ${70 + i * 10} ${x + 7} 40Z`} />
            <circle cx={x} cy={64 + i * 10} r="7" fill="#e6eef8" />
          </g>
        ))}
      </svg>
    </div>
  );
}

function Flash({ id }: { id: number }) {
  const root = useRef<HTMLDivElement>(null);
  const reduced = useApp((s) => s.reducedMotion);
  useEffect(() => {
    const el = root.current;
    if (!el) return;
    const t = gsap.fromTo(el, { opacity: reduced ? 0.25 : 0.9 }, { opacity: 0, duration: reduced ? 1.2 : 1.6, ease: 'expo.out' });
    return () => {
      t.kill();
    };
  }, [id, reduced]);
  return <div className="flash" ref={root} aria-hidden="true" />;
}

/** Grande typographie du final (case 24). */
function FinaleOverlay({ closing }: { closing: boolean }) {
  const root = useRef<HTMLDivElement>(null);
  const closeBtn = useRef<HTMLButtonElement>(null);
  const reduced = useApp((s) => s.reducedMotion);
  const content = dayContent(24);
  useEffect(() => {
    const el = root.current;
    if (!el) return;
    closeBtn.current?.focus({ preventScroll: true });
    const tl = gsap.timeline();
    if (reduced) {
      tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: 1.2, ease: 'sine.inOut' });
    } else {
      const chars = el.querySelectorAll('.finale__title .split-char');
      tl.fromTo(
        chars,
        { yPercent: 140, scaleY: 1.6, opacity: 0, filter: 'blur(14px)' },
        {
          yPercent: 0,
          scaleY: 1,
          opacity: 1,
          filter: 'blur(0px)',
          duration: 1.5,
          ease: 'elastic.out(1, 0.5)',
          stagger: { each: 0.07, from: 'center' },
        },
        0,
      );
      tl.fromTo(
        el.querySelector('.finale__eyebrow'),
        { opacity: 0, letterSpacing: '1em' },
        { opacity: 1, letterSpacing: '0.5em', duration: 1.8, ease: 'expo.out' },
        0.3,
      );
      tl.fromTo(
        el.querySelectorAll('.finale__sub .split-wordin'),
        { yPercent: 100 },
        { yPercent: 0, duration: 0.9, ease: 'power4.out', stagger: 0.04 },
        1.1,
      );
      tl.fromTo(el.querySelector('.finale__close'), { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.7, ease: 'power3.out' }, 2.0);
      tl.to(chars, { y: -6, duration: 1.6, ease: 'sine.inOut', stagger: { each: 0.08, repeat: -1, yoyo: true } }, 2.2);
    }
    return () => {
      tl.kill();
    };
  }, [reduced]);
  useEffect(() => {
    const el = root.current;
    if (!closing || !el) return;
    const t = gsap.to(el, { opacity: 0, y: -20, duration: 0.5, ease: 'power2.in' });
    return () => {
      t.kill();
    };
  }, [closing]);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeDay();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);
  return (
    <div className="finale" ref={root} role="dialog" aria-labelledby="finale-title">
      <span className="finale__eyebrow">24 décembre 2026</span>
      <h2 className="finale__title" id="finale-title">
        <SplitLetters text={content.title} />
      </h2>
      <p className="finale__sub">
        <SplitWords text={content.text} />
      </p>
      <button ref={closeBtn} className="finale__close card__close" onClick={closeDay}>
        <span>Revenir au sapin</span>
        <kbd>Échap</kbd>
      </button>
    </div>
  );
}

export function ScreenFx() {
  const day = useApp((s) => s.activeDay);
  const revealed = useApp((s) => s.revealed);
  const phase = useApp((s) => s.phase);
  const event = useApp((s) => s.screenEvent);
  const content = day !== null ? dayContent(day) : null;
  const closing = phase === 'closing';
  return (
    <>
      {revealed && content?.surprise.kind === 'typo' && <TypoOverlay key={day} lines={content.surprise.lines} closing={closing} />}
      {revealed && day === 24 && <FinaleOverlay closing={closing} />}
      {event?.type === 'splat' && <Splat key={event.id} id={event.id} />}
      {event?.type === 'flash' && <Flash key={event.id} id={event.id} />}
    </>
  );
}
