import js from '@eslint/js';
import globals from 'globals';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  { ignores: ['dist', 'captures', 'node_modules'] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.strict],
    files: ['src/**/*.{ts,tsx}'],
    languageOptions: { ecmaVersion: 2022, globals: globals.browser },
    plugins: { 'react-hooks': reactHooks, 'react-refresh': reactRefresh },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
    },
  },
  {
    // R3F : les objets three.js (matériaux, uniformes, maillages) sont mutés image par image hors de React.
    // La règle du compilateur React qui interdit ces mutations ne s'applique pas à ce code.
    files: ['src/three/**/*.{ts,tsx}'],
    rules: { 'react-hooks/immutability': 'off' },
  },
  {
    extends: [js.configs.recommended],
    // Les scripts Playwright exécutent aussi du code dans la page (page.evaluate).
    files: ['scripts/**/*.mjs', '*.js'],
    languageOptions: { ecmaVersion: 2022, globals: { ...globals.node, ...globals.browser } },
  },
  {
    extends: [js.configs.recommended, ...tseslint.configs.strict],
    files: ['vite.config.ts'],
    languageOptions: { globals: globals.node },
  },
);
