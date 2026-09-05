import js from '@eslint/js'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import globals from 'globals'
import tseslint from 'typescript-eslint'

export default tseslint.config(
  { ignores: ['dist', 'coverage', 'playwright-report', 'test-results', 'node_modules'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
      // El cliente de axios es el único que puede hablar con la API (docs/frontend/conventions.md).
      'no-restricted-globals': ['error', { name: 'fetch', message: 'Usa el cliente de @/api/client.' }],
      'no-restricted-properties': [
        'error',
        {
          object: 'window',
          property: 'localStorage',
          message: 'La sesión va en cookie httpOnly; no guardes credenciales en localStorage.',
        },
      ],
    },
  },
  {
    files: ['**/*.test.{ts,tsx}', 'src/test/**', 'e2e/**'],
    languageOptions: { globals: { ...globals.browser, ...globals.node } },
    rules: {
      // Las pruebas comprueban justamente que la aplicación NO usa localStorage,
      // así que necesitan poder nombrarlo.
      'no-restricted-properties': 'off',
    },
  },
)
