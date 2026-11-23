import { lazy, Suspense, useCallback, useEffect, useState } from 'react';
import { bindPointer, playIntro, skipIntro } from './director';
import { params } from './lib/params';
import { reducedMotionQuery } from './lib/quality';
import { useApp } from './store';
import type { DebugSample } from './three/DebugStats';
import { A11yProxies } from './ui/A11yProxies';
import { DayCard } from './ui/DayCard';
import { DebugPanel } from './ui/DebugPanel';
import { Hud } from './ui/Hud';
import { IntroTitle } from './ui/IntroTitle';
import { Loader } from './ui/Loader';
import { Toast } from './ui/Toast';
import { ScreenFx } from './ui/ScreenFx';

const Stage = lazy(() => import('./Stage'));

export function App() {
  const [stats, setStats] = useState<DebugSample | null>(null);
  const [contextLost, setContextLost] = useState(false);
  const modelReady = useApp((s) => s.modelReady);
  const fontsReady = useApp((s) => s.fontsReady);
  const phase = useApp((s) => s.phase);

  useEffect(() => bindPointer(), []);

  useEffect(() => {
    const onChange = () => useApp.getState().setReducedMotion(reducedMotionQuery.matches);
    reducedMotionQuery.addEventListener('change', onChange);
    return () => reducedMotionQuery.removeEventListener('change', onChange);
  }, []);

  useEffect(() => {
    let alive = true;
    Promise.all([
      document.fonts.load('600 64px "Fraunces Variable"'),
      document.fonts.load('400 16px "Inter Variable"'),
      document.fonts.load('italic 400 32px "Fraunces Variable"'),
    ])
      .catch(() => undefined)
      .finally(() => {
        if (alive) useApp.getState().setFontsReady();
      });
    return () => {
      alive = false;
    };
  }, []);

  const startExperience = useCallback(() => {
    if (useApp.getState().phase !== 'loading') return;
    playIntro();
    if (params.skipIntro) skipIntro();
  }, []);

  const onContextLost = useCallback(() => setContextLost(true), []);

  const ready = modelReady && fontsReady;

  return (
    <div className={`app app--${phase}`}>
      <Suspense fallback={null}>
        <Stage onStats={setStats} onContextLost={onContextLost} />
      </Suspense>
      <ScreenFx />
      <IntroTitle />
      <Hud />
      <A11yProxies />
      <DayCard />
      <Toast />
      <Loader ready={ready} onDone={startExperience} />
      {params.debug && <DebugPanel stats={stats} />}
      {contextLost && (
        <div className="context-lost" role="alert">
          Le rendu 3D s’est interrompu. <button onClick={() => window.location.reload()}>Recharger</button>
        </div>
      )}
    </div>
  );
}
