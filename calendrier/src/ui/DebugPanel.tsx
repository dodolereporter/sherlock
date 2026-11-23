import type { DebugSample } from '../three/DebugStats';

export function DebugPanel({ stats }: { stats: DebugSample | null }) {
  return (
    <aside className="debug" aria-label="Mesures de rendu">
      <dl>
        <dt>FPS</dt>
        <dd data-k="fps">{stats?.fps ?? '–'}</dd>
        <dt>Appels de dessin</dt>
        <dd data-k="calls">{stats?.calls ?? '–'}</dd>
        <dt>Triangles</dt>
        <dd data-k="triangles">{stats ? stats.triangles.toLocaleString('fr-FR') : '–'}</dd>
        <dt>Points</dt>
        <dd>{stats ? stats.points.toLocaleString('fr-FR') : '–'}</dd>
        <dt>Géométries</dt>
        <dd>{stats?.geometries ?? '–'}</dd>
        <dt>Textures</dt>
        <dd>{stats?.textures ?? '–'}</dd>
      </dl>
    </aside>
  );
}
