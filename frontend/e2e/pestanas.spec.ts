import { expect, test } from '@playwright/test'

// DEU-66: en el celular la tira de pestañas se desplaza en su fila. Si no cabe, el borde por el
// que sigue se desvanece (`data-desborda`), para que la última pestaña cortada no parezca un
// rótulo roto. jsdom no mide el desbordamiento: se prueba aquí.

test.use({ viewport: { width: 390, height: 844 } })

test('la tira de pestañas que no cabe dice por dónde sigue', async ({ page }) => {
  // El último handler registrado gana: primero el comodín, luego lo de la prueba.
  await page.route('**/api/v1/**', (ruta) => ruta.fulfill({ json: [] }))
  await page.route('**/api/v1/auth/me', (ruta) =>
    ruta.fulfill({ json: { id: 'u1', email: 'admin@timu.co', nombre: 'Admin', rol: 'admin', activo: true } }),
  )
  await page.goto('/campanas')
  const tira = page.getByRole('tablist', { name: 'Secciones de campañas' })
  await expect(tira).toHaveAttribute('data-desborda', 'derecha')
  await tira.evaluate((t) => t.scrollTo({ left: t.scrollWidth }))
  await expect(tira).toHaveAttribute('data-desborda', 'izquierda')
})

test('la pestaña activa se ve entera aunque la tira no quepa', async ({ page }) => {
  await page.route('**/api/v1/**', (ruta) => ruta.fulfill({ json: [] }))
  await page.route('**/api/v1/auth/me', (ruta) =>
    ruta.fulfill({ json: { id: 'u1', email: 'admin@timu.co', nombre: 'Admin', rol: 'admin', activo: true } }),
  )
  await page.goto('/aliadas?pestana=liquidacion')
  const tira = page.getByRole('tablist', { name: 'Secciones de aliadas' })
  const activa = tira.getByRole('tab', { name: 'Liquidación' })
  await expect(activa).toHaveAttribute('data-state', 'active')
  await expect
    .poll(async () => {
      const [t, a] = [await tira.boundingBox(), await activa.boundingBox()]
      return t && a ? a.x >= t.x - 1 && a.x + a.width <= t.x + t.width + 1 : false
    })
    .toBe(true)
})
