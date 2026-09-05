import react from '@vitejs/plugin-react'
import path from 'node:path'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { '@': path.resolve(__dirname, 'src') } },
  test: {
    // Sólo las pruebas de componentes: e2e/ es territorio de Playwright.
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    css: false,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov'],
      include: ['src/**/*.{ts,tsx}'],
      // Sin lógica que probar: tipos, punto de entrada y utilidades de las propias pruebas.
      exclude: ['src/types/**', 'src/main.tsx', 'src/test/**', 'src/**/*.d.ts'],
      thresholds: { lines: 60, functions: 60, branches: 60, statements: 60 },
    },
  },
})
