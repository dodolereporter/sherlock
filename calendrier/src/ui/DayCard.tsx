import gsap from 'gsap';
import { useEffect, useRef, useState } from 'react';
import { dayContent, KIND_LABEL } from '../content/days';
import { closeDay } from '../director';
import { useApp } from '../store';
import { sherlock } from '../three/sherlockApi';
import { SplitLetters, SplitWords } from './split';

/** Carte de la case ouverte : numéro, titre, texte, et l'énigme quand il y en a une. */
export function DayCard() {
  const day = useApp((s) => s.activeDay);
  const revealed = useApp((s) => s.revealed);
  const phase = useApp((s) => s.phase);
  if (day === null || day === 24 || !revealed) return null;
  return <Card key={day} day={day} closing={phase === 'closing'} />;
}

function Card({ day, closing }: { day: number; closing: boolean }) {
  const content = dayContent(day);
  const reduced = useApp((s) => s.reducedMotion);
  const root = useRef<HTMLElement>(null);
  const closeBtn = useRef<HTMLButtonElement>(null);
  const [answer, setAnswer] = useState(false);
  const surprise = content.surprise;
  const isTypo = surprise.kind === 'typo';

  useEffect(() => {
    const el = root.current;
    if (!el) return;
    closeBtn.current?.focus({ preventScroll: true });
    const tl = gsap.timeline();
    if (reduced) {
      tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: 0.5, ease: 'sine.out' });
      return () => {
        tl.kill();
      };
    }
    const q = (s: string) => el.querySelectorAll(s);
    tl.fromTo(
      el,
      { clipPath: 'inset(0% 0% 100% 0% round 22px)' },
      { clipPath: 'inset(0% 0% 0% 0% round 22px)', duration: 0.75, ease: 'expo.out' },
      0,
    );
    tl.fromTo(
      q('.card__numeral'),
      { yPercent: 40, opacity: 0, scale: 0.7 },
      { yPercent: 0, opacity: 1, scale: 1, duration: 1.1, ease: 'elastic.out(1, 0.55)' },
      0.1,
    );
    tl.fromTo(q('.card__eyebrow'), { x: -16, opacity: 0 }, { x: 0, opacity: 1, duration: 0.6, ease: 'power3.out' }, 0.2);
    tl.fromTo(
      q('.card__title .split-char'),
      { yPercent: 105, opacity: 0, rotate: 6 },
      { yPercent: 0, opacity: 1, rotate: 0, duration: 0.8, ease: 'expo.out', stagger: 0.022 },
      0.28,
    );
    tl.fromTo(q('.card__text .split-wordin'), { yPercent: 100 }, { yPercent: 0, duration: 0.7, ease: 'power4.out', stagger: 0.028 }, 0.5);
    tl.fromTo(q('.card__reveal'), { y: 14, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6, ease: 'power3.out', stagger: 0.08 }, 0.7);
    return () => {
      tl.kill();
    };
  }, [reduced]);

  useEffect(() => {
    const el = root.current;
    if (!closing || !el) return;
    const tween = reduced
      ? gsap.to(el, { opacity: 0, duration: 0.3 })
      : gsap.to(el, { y: 24, opacity: 0, scale: 0.97, duration: 0.35, ease: 'power2.in' });
    return () => {
      tween.kill();
    };
  }, [closing, reduced]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeDay();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  useEffect(() => {
    if (!answer) return;
    const el = root.current?.querySelector('.card__answer');
    sherlock.play([{ name: 'enquete_sortie' }, { name: 'idee' }]);
    if (!el || reduced) return;
    const tween = gsap.fromTo(
      el.querySelectorAll('.split-char'),
      { yPercent: 90, opacity: 0, filter: 'blur(6px)' },
      { yPercent: 0, opacity: 1, filter: 'blur(0px)', duration: 0.7, ease: 'expo.out', stagger: 0.03 },
    );
    return () => {
      tween.kill();
    };
  }, [answer, reduced]);

  return (
    <section
      className={`card card--${surprise.kind}${isTypo ? ' card--compact' : ''}`}
      ref={root}
      role="dialog"
      aria-modal="false"
      aria-labelledby={`card-title-${day}`}
    >
      <div className="card__head">
        <span className="card__numeral" aria-hidden="true">
          {day}
        </span>
        <span className="card__eyebrow">
          {KIND_LABEL[surprise.kind]} · {day} décembre
        </span>
      </div>
      <h2 className="card__title" id={`card-title-${day}`}>
        <SplitLetters text={content.title} />
      </h2>
      <p className="card__text">
        <SplitWords text={content.text} />
      </p>
      {surprise.kind === 'enigme' && (
        <div className="riddle card__reveal">
          <p className="riddle__q">{surprise.question}</p>
          {answer ? (
            <p className="card__answer" aria-live="polite">
              <SplitLetters text={surprise.answer} />
            </p>
          ) : (
            <button className="btn btn--gold" onClick={() => setAnswer(true)}>
              Révéler la réponse
            </button>
          )}
        </div>
      )}
      <button ref={closeBtn} className="card__close card__reveal" onClick={closeDay}>
        <span>Refermer</span>
        <kbd>Échap</kbd>
      </button>
    </section>
  );
}
