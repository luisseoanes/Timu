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
      // Justo por debajo de lo medido: frenan la degradación. Se suben cuando la
      // cobertura sube y no se bajan sin una razón en el cuerpo del commit.
      thresholds: { lines: 87, functions: 86, branches: 76, statements: 86 },
    },
  },
})
