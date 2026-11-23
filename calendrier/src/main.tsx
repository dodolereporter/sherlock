import '@fontsource-variable/fraunces/soft.css';
import '@fontsource-variable/fraunces/soft-italic.css';
import '@fontsource-variable/inter/index.css';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './App';
import { NoWebGL } from './ui/NoWebGL';
import './styles.css';

function hasWebGL(): boolean {
  try {
    const canvas = document.createElement('canvas');
    return !!canvas.getContext('webgl2');
  } catch {
    return false;
  }
}

const root = document.getElementById('root');
if (root) {
  createRoot(root).render(<StrictMode>{hasWebGL() ? <App /> : <NoWebGL />}</StrictMode>);
}
