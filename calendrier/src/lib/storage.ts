import { params } from './params';

const KEY = params.demo || params.date ? 'sherlock-avent-2026:essai' : 'sherlock-avent-2026';

export function loadOpened(): number[] {
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((d): d is number => typeof d === 'number' && d >= 1 && d <= 24);
  } catch {
    return [];
  }
}

export function saveOpened(days: readonly number[]): void {
  try {
    window.localStorage.setItem(KEY, JSON.stringify([...days].sort((a, b) => a - b)));
  } catch {
    // Stockage indisponible (navigation privée stricte) : le calendrier reste utilisable sans mémoire.
  }
}

export const isTrialSession = KEY.endsWith(':essai');
