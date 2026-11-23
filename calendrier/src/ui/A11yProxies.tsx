import { useEffect, useRef, type KeyboardEvent } from 'react';
import { clickDay, hoverDay } from '../director';
import { isUnlocked } from '../lib/dates';
import { useApp } from '../store';
import { screenSlots } from '../three/fx';
import { ROWS, slotOf } from '../three/layout';

function label(day: number, opened: boolean): string {
  if (opened) return `Case ${day}, déjà ouverte : revoir la surprise`;
  if (isUnlocked(day)) return day === 24 ? 'Case 24, le grand final : ouvrir' : `Case ${day} : ouvrir`;
  return `Case ${day}, verrouillée jusqu’au ${day} décembre`;
}

/** Voisin dans la grille du sapin pour les flèches du clavier. */
function neighbour(day: number, key: string): number | null {
  const slot = slotOf(day);
  const row = ROWS[slot.row];
  if (!row) return null;
  if (key === 'ArrowLeft') return row[slot.col - 1] ?? null;
  if (key === 'ArrowRight') return row[slot.col + 1] ?? null;
  const target = ROWS[slot.row + (key === 'ArrowUp' ? 1 : -1)];
  if (!target) return null;
  const x = slotOf(day).local.x;
  let best: number | null = null;
  let bestDist = Infinity;
  for (const d of target) {
    const dist = Math.abs(slotOf(d).local.x - x);
    if (dist < bestDist) {
      bestDist = dist;
      best = d;
    }
  }
  return best;
}

/**
 * 24 vrais boutons, invisibles, posés sur la projection écran de chaque case.
 * Ils portent les libellés, le focus clavier et l'anneau de focus ; la souris passe au travers vers la 3D.
 */
export function A11yProxies() {
  const phase = useApp((s) => s.phase);
  const opened = useApp((s) => s.opened);
  const activeDay = useApp((s) => s.activeDay);
  const refs = useRef<(HTMLButtonElement | null)[]>([]);
  const interactive = phase === 'idle';
  const lastActive = useRef<number | null>(null);

  useEffect(() => {
    let raf = 0;
    const tick = () => {
      refs.current.forEach((btn, i) => {
        const s = screenSlots[i];
        if (!btn || !s) return;
        const size = Math.max(28, s.size * 1.08);
        btn.style.transform = `translate3d(${(s.x - size / 2).toFixed(1)}px, ${(s.y - size / 2).toFixed(1)}px, 0)`;
        btn.style.width = `${size.toFixed(1)}px`;
        btn.style.height = `${size.toFixed(1)}px`;
      });
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  // Rend le focus à la case refermée.
  useEffect(() => {
    if (activeDay !== null) lastActive.current = activeDay;
    if (phase === 'idle' && lastActive.current !== null) {
      refs.current[lastActive.current - 1]?.focus({ preventScroll: true });
      lastActive.current = null;
    }
  }, [phase, activeDay]);

  const onKey = (day: number) => (e: KeyboardEvent<HTMLButtonElement>) => {
    if (!e.key.startsWith('Arrow')) return;
    e.preventDefault();
    const next = neighbour(day, e.key);
    if (next !== null) refs.current[next - 1]?.focus({ preventScroll: true });
  };

  return (
    <nav className="proxies" aria-label="Les 24 cases du calendrier" inert={!interactive}>
      {Array.from({ length: 24 }, (_, i) => {
        const day = i + 1;
        const isOpen = opened.includes(day);
        return (
          <button
            key={day}
            ref={(el) => {
              refs.current[i] = el;
            }}
            className="proxy"
            data-day={day}
            aria-label={label(day, isOpen)}
            onFocus={() => hoverDay(day)}
            onBlur={() => hoverDay(null)}
            onClick={() => clickDay(day)}
            onKeyDown={onKey(day)}
          />
        );
      })}
    </nav>
  );
}
