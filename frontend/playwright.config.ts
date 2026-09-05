import { defineConfig, devices } from '@playwright/test'

/**
 * Pruebas de extremo a extremo sobre la aplicación compilada.
 *
 * La API se intercepta con `page.route` en cada prueba: el contrato real con el
 * backend lo cubren sus pruebas de integración contra PostgreSQL, y levantar el
 * stack completo aquí haría la suite lenta y frágil sin cubrir nada nuevo.
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? [['html', { open: 'never' }], ['list']] : 'list',
  use: {
    baseURL: 'http://localhost:4173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'npm run preview -- --port 4173',
    url: 'http://localhost:4173',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
})
