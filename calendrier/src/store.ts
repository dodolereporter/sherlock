import { create } from 'zustand';
import { loadOpened, saveOpened } from './lib/storage';

export type Phase = 'loading' | 'intro' | 'idle' | 'opening' | 'open' | 'closing';

export interface Toast {
  id: number;
  day: number;
  message: string;
}

interface AppState {
  phase: Phase;
  progress: number;
  modelReady: boolean;
  fontsReady: boolean;
  opened: number[];
  activeDay: number | null;
  /** La surprise est montée (après l'action d'ouverture). */
  revealed: boolean;
  toast: Toast | null;
  reducedMotion: boolean;
  /** Effets d'écran ponctuels (boule de neige, éclair blanc). */
  screenEvent: { type: 'splat' | 'flash'; id: number } | null;
  fireScreenEvent: (type: 'splat' | 'flash') => void;
  setPhase: (phase: Phase) => void;
  setProgress: (progress: number) => void;
  setModelReady: () => void;
  setFontsReady: () => void;
  markOpened: (day: number) => void;
  resetOpened: () => void;
  setActiveDay: (day: number | null) => void;
  setRevealed: (revealed: boolean) => void;
  showToast: (day: number, message: string) => void;
  clearToast: () => void;
  setReducedMotion: (value: boolean) => void;
}

let toastId = 0;

export const useApp = create<AppState>((set, get) => ({
  phase: 'loading',
  progress: 0,
  modelReady: false,
  fontsReady: false,
  opened: loadOpened(),
  activeDay: null,
  revealed: false,
  toast: null,
  reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  screenEvent: null,
  fireScreenEvent: (type) => set({ screenEvent: { type, id: ++toastId } }),
  setPhase: (phase) => set({ phase }),
  setProgress: (progress) => set({ progress }),
  setModelReady: () => set({ modelReady: true }),
  setFontsReady: () => set({ fontsReady: true }),
  markOpened: (day) => {
    if (get().opened.includes(day)) return;
    const opened = [...get().opened, day];
    saveOpened(opened);
    set({ opened });
  },
  resetOpened: () => {
    saveOpened([]);
    set({ opened: [] });
  },
  setActiveDay: (activeDay) => set({ activeDay }),
  setRevealed: (revealed) => set({ revealed }),
  showToast: (day, message) => set({ toast: { id: ++toastId, day, message } }),
  clearToast: () => set({ toast: null }),
  setReducedMotion: (reducedMotion) => set({ reducedMotion }),
}));
