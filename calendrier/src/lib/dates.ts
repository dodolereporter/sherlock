import { params } from './params';

/** Année du calendrier : les cases s'ouvrent du 1er au 24 décembre de cette année. */
export const CALENDAR_YEAR = 2026;

export function today(): Date {
  return params.date ?? new Date();
}

function dayStart(year: number, month: number, day: number): number {
  return new Date(year, month, day, 0, 0, 0, 0).getTime();
}

/** Vrai si la case peut être ouverte à la date courante. */
export function isUnlocked(day: number, now: Date = today()): boolean {
  if (params.demo) return true;
  return now.getTime() >= dayStart(CALENDAR_YEAR, 11, day);
}

/** Nombre de jours entiers à attendre avant l'ouverture (0 si ouverte). */
export function daysUntil(day: number, now: Date = today()): number {
  if (isUnlocked(day, now)) return 0;
  const startOfToday = dayStart(now.getFullYear(), now.getMonth(), now.getDate());
  return Math.max(1, Math.round((dayStart(CALENDAR_YEAR, 11, day) - startOfToday) / 86_400_000));
}

export function waitMessage(day: number): string {
  const n = daysUntil(day);
  if (n <= 1) return `Patience : la case ${day} s'ouvre demain.`;
  if (n < 30) return `Patience : encore ${n} jours avant la case ${day}.`;
  return `La case ${day} s'ouvrira le ${day} décembre.`;
}

export function formatToday(): string {
  return today().toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' });
}
