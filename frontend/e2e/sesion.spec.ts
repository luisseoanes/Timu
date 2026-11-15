import { expect, test, type Page } from '@playwright/test'

const USUARIO = {
  id: '11111111-1111-1111-1111-111111111111',
  email: 'admin@timu.co',
  nombre: 'Admin',
  rol: 'admin',
  activo: true,
}

// Sin sesión, el backend responde 401 también a la renovación. Hay que simularlo: sin
// backend, la renovación falla por red, el panel lo trata como un fallo pasajero y ofrece
// reintentar en vez de mandar al ingreso.
const sinRenovacion = (page: Page) =>
  page.route('**/api/v1/auth/refresh', (ruta) => ruta.fulfill({ status: 401, body: '' }))

test.describe('sesión', () => {
  test('sin sesión, cualquier ruta lleva al ingreso', async ({ page }) => {
    await page.route('**/api/v1/auth/me', (ruta) => ruta.fulfill({ status: 401, body: '' }))
    await sinRenovacion(page)
    await page.goto('/familias')
    await expect(page).toHaveURL(/\/login/)
  })

  test('el ingreso no deja credenciales en localStorage', async ({ page }) => {
    await page.route('**/api/v1/auth/me', (ruta) => ruta.fulfill({ status: 401, body: '' }))
    await sinRenovacion(page)
    await page.route('**/api/v1/auth/login', (ruta) =>
      ruta.fulfill({ json: { usuario: USUARIO } }),
    )
    await page.route('**/api/v1/familias*', (ruta) =>
      ruta.fulfill({ json: { items: [], total: 0, limit: 50, offset: 0 } }),
    )

    await page.goto('/login')
    await page.getByLabel(/correo|email/i).fill('admin@timu.co')
    await page.getByLabel('Contraseña', { exact: true }).fill('secreto123')
    await page.getByRole('button', { name: /ingresar|entrar/i }).click()

    await expect(page).not.toHaveURL(/\/login/)
    expect(await page.evaluate(() => window.localStorage.length)).toBe(0)
  })
})

// R3-PUB-01: lo que jsdom no aplica. A 390 px la franja marina no puede empujar la acción
// fuera de la primera pantalla, y la nota de datos va una sola vez (la del panel se oculta).
test.describe('activación de la cuenta', () => {
  test.use({ viewport: { width: 390, height: 844 } })

  test('saluda, deja la acción a la vista y entra al portal al activar', async ({ page }) => {
    await page.route('**/api/v1/**', (ruta) => ruta.fulfill({ json: [] }))
    await page.route('**/api/v1/auth/me', (ruta) => ruta.fulfill({ status: 401, body: '' }))
    await sinRenovacion(page)
    await page.route('**/api/v1/auth/enlace', (ruta) =>
      ruta.fulfill({ json: { estado: 'vigente', proposito: 'activacion', nombre: 'Ana' } }),
    )
    await page.route('**/api/v1/auth/restablecer', (ruta) =>
      ruta.fulfill({ json: { usuario: { ...USUARIO, email: 'ana@example.com', nombre: 'Ana Ruiz', rol: 'familia' } } }),
    )

    await page.goto('/activar?token=abc')
    await expect(page.getByRole('heading', { name: 'Hola, Ana' })).toBeVisible()
    const activar = page.getByRole('button', { name: 'Activar mi cuenta' })
    const caja = await activar.boundingBox()
    expect(caja && caja.y + caja.height).toBeLessThanOrEqual(844)
    await expect(page.getByText('Datos protegidos · Ley 1581 de 2012').filter({ visible: true })).toHaveCount(1)

    await page.getByLabel('Contraseña nueva').fill('segura1234')
    await page.getByLabel('Confirma la contraseña').fill('segura1234')
    await activar.click()
    await expect(page).toHaveURL(/\/portal$/)
  })
})
