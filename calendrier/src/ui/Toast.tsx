import gsap from 'gsap';
import { useEffect, useRef } from 'react';
import { useApp } from '../store';

/** Message de refus d'une case verrouillée. */
export function Toast() {
  const toast = useApp((s) => s.toast);
  const clear = useApp((s) => s.clearToast);
  const reduced = useApp((s) => s.reducedMotion);
  const el = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const node = el.current;
    if (!toast || !node) return;
    const tl = gsap.timeline({ onComplete: clear });
    if (reduced) {
      tl.fromTo(node, { opacity: 0 }, { opacity: 1, duration: 0.3 });
    } else {
      tl.fromTo(node, { y: 30, opacity: 0, scale: 0.92 }, { y: 0, opacity: 1, scale: 1, duration: 0.55, ease: 'back.out(2.2)' });
      tl.fromTo(
        node.querySelector('.toast__lock'),
        { rotate: 0 },
        { keyframes: { rotate: [-14, 12, -8, 5, 0] }, duration: 0.6, ease: 'power2.out' },
        0.1,
      );
    }
    tl.to(node, { y: reduced ? 0 : 12, opacity: 0, duration: 0.4, ease: 'power2.in' }, 2.8);
    return () => {
      tl.kill();
    };
  }, [toast, clear, reduced]);

  return (
    <div className="toast-region" aria-live="polite">
      {toast && (
        <div className="toast" ref={el} key={toast.id}>
          <svg className="toast__lock" viewBox="0 0 24 24" aria-hidden="true">
            <rect x="5" y="10.5" width="14" height="10" rx="2.5" />
            <path d="M8 10.5V8a4 4 0 0 1 8 0v2.5" />
          </svg>
          <span>{toast.message}</span>
        </div>
      )}
    </div>
  );
}
