/** Paramètres d'URL lus une seule fois au démarrage. */
export interface AppParams {
  /** Date simulée (?date=AAAA-MM-JJ), sinon null. */
  date: Date | null;
  /** ?demo=1 : toutes les cases sont ouvrables. */
  demo: boolean;
  /** ?debug=1 : affiche FPS, appels de dessin et triangles. */
  debug: boolean;
  /** ?intro=0 : saute l'introduction (utile en test). */
  skipIntro: boolean;
}

function parseDate(value: string | null): Date | null {
  if (!value) return null;
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) return null;
  const [, y, m, d] = match;
  const date = new Date(Number(y), Number(m) - 1, Number(d), 12);
  return Number.isNaN(date.getTime()) ? null : date;
}

function readParams(): AppParams {
  const search = new URLSearchParams(window.location.search);
  return {
    date: parseDate(search.get('date')),
    demo: search.get('demo') === '1',
    debug: search.get('debug') === '1',
    skipIntro: search.get('intro') === '0',
  };
}

export const params: AppParams = readParams();
