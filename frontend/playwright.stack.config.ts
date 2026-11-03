import { defineConfig, devices } from '@playwright/test'

/**
 * Recorridos de extremo a extremo contra el stack real (docker compose): panel, API,
 * PostgreSQL, Redis y el almacenamiento S3 de verdad, sin nada simulado. Los corre el job «Stack con un
 * solo comando» del CI después de `scripts.datos_demo`, que crea los usuarios y datos que
 * recorren. `e2e/` sigue siendo la suite rápida con la API interceptada.
 *
 * En local: docker compose up -d, datos_demo y luego
 *   E2E_BASE_URL=http://localhost:5173 npm run test:e2e:stack
 */
export default defineConfig({
  testDir: './e2e-stack',
  // Comparten la base: en serie, para que un recorrido no pise los datos de otro.
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: process.env.CI ? [['html', { open: 'never', outputFolder: 'playwright-report-stack' }], ['list']] : 'list',
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:5173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    // Ingresa una vez por perfil y guarda la sesión: ver e2e-stack/sesiones.ts.
    { name: 'sesiones', testMatch: /sesiones\.setup\.ts/ },
    { name: 'chromium', use: { ...devices['Desktop Chrome'] }, dependencies: ['sesiones'] },
  ],
})
