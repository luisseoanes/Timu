import { expect, test, type Page } from '@playwright/test'

// Techo 67: al cargar el acceso, lo hecho de la línea se dibuja hasta «Hoy», un tramo tras otro.
// jsdom no aplica el CSS: se comprueba aquí, con y sin movimiento reducido.

async function animaciones(page: Page) {
  await page.route('**/api/v1/**', (ruta) => ruta.fulfill({ status: 401, json: { detail: 'Sin sesión' } }))
  await page.goto('/login')
  const tramos = page.locator('.ingreso-estacion[data-tipo="hecha"]')
  await expect(tramos).toHaveCount(2)
  return {
    tramos: await tramos.evaluateAll((els) =>
      els.map((el) => {
        const estilo = getComputedStyle(el, '::before')
        return { nombre: estilo.animationName, espera: estilo.animationDelay }
      }),
    ),
    hoy: await page.locator('.ingreso-hoy > span').evaluate((el) => getComputedStyle(el).animationName),
  }
}

test('lo hecho de la línea se dibuja hasta «Hoy» al cargar', async ({ page }) => {
  const { tramos, hoy } = await animaciones(page)
  expect(tramos.map((t) => t.nombre)).toEqual(['ingreso-tramo', 'ingreso-tramo'])
  // El segundo tramo empieza cuando termina el primero.
  expect(tramos[0]!.espera).toBe('0s')
  expect(tramos[1]!.espera).not.toBe('0s')
  expect(hoy).toBe('ingreso-hoy')
})

test.describe('con movimiento reducido', () => {
  test.use({ reducedMotion: 'reduce' })

  test('la línea sale entera, sin dibujarse', async ({ page }) => {
    const { tramos, hoy } = await animaciones(page)
    expect(tramos.map((t) => t.nombre)).toEqual(['none', 'none'])
    expect(hoy).toBe('none')
  })
})
