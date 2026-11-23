export function NoWebGL() {
  return (
    <main className="nowebgl" role="alert">
      <svg viewBox="0 0 64 64" width="72" height="72" aria-hidden="true">
        <g stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" fill="none">
          <path d="M32 6v52M9.5 19l45 26M9.5 45l45-26" />
          <path d="M26 10l6 6 6-6M26 54l6-6 6 6M10 27l8-2-2-8M54 37l-8 2 2 8M10 37l8 2-2 8M54 27l-8-2 2-8" />
        </g>
      </svg>
      <h1>Le calendrier de Sherlock</h1>
      <p>Ce calendrier est une scène 3D : il a besoin de WebGL 2, que ce navigateur ou cet appareil ne fournit pas.</p>
      <p className="nowebgl__hint">
        Essayez un navigateur récent (Firefox, Chrome, Safari, Edge) et vérifiez que l’accélération matérielle est activée.
      </p>
    </main>
  );
}
