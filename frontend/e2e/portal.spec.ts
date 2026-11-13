import { expect, test, type Page } from '@playwright/test'

// R3-POR-01: el inicio del portal con la API interceptada. Lo que aquí se comprueba es CSS
// que jsdom no aplica: que lo hecho se pliega de verdad y que «hoy» queda en la primera
// pantalla del celular.

const FAMILIA = {
  id: 'f1',
  titular_nombre: 'Ana Ruiz',
  mascotas: [{ id: 'm1', nombre: 'Luna', especie: 'canino', raza: 'Criolla', activa: true, foto_url: null }],
}

function dentroDe(dias: number): string {
  const d = new Date()
  d.setDate(d.getDate() + dias)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const estacion = (dias: number, estado: string, titulo: string, referencia_id: string) => ({
  tipo: 'cuota',
  referencia_id,
  fecha: dentroDe(dias),
  estado,
  titulo,
  mascota: null,
  mascota_id: null,
})

async function comoFamilia(page: Page) {
  // El último handler registrado gana: primero lo que no importa, luego lo de la prueba.
  await page.route('**/api/v1/**', (ruta) => ruta.fulfill({ json: [] }))
  await page.route('**/api/v1/auth/me', (ruta) =>
    ruta.fulfill({ json: { id: 'u1', email: 'ana@example.com', nombre: 'Ana Ruiz', rol: 'familia', activo: true } }),
  )
  await page.route('**/api/v1/portal/mi-familia', (ruta) => ruta.fulfill({ json: FAMILIA }))
  await page.route('**/api/v1/portal/plan', (ruta) =>
    ruta.fulfill({
      json: {
        estado: 'activa',
        periodicidad: 'mensual',
        valor_periodo: '75000.00',
        valor_mensual: '75000.00',
        fecha_inicio: '2026-01-21',
        fecha_renovacion: '2027-01-21',
        mascotas: [{ mascota_id: 'm1', mascota: 'Luna', plan: 'Plan Familiar', color: 'verde', valor_mensual: '75000.00', beneficios: [] }],
      },
    }),
  )
  await page.route('**/api/v1/portal/estado-cuenta', (ruta) =>
    ruta.fulfill({ json: { saldo_pendiente: '0.00', saldo_vencido: '0.00', proximo_cobro: null, cuotas: [], pagos: [] } }),
  )
  await page.route('**/api/v1/portal/linea', (ruta) =>
    ruta.fulfill({
      json: {
        familia_id: 'f1',
        planes: [{ plan_id: 'p1', nombre: 'Plan Familiar', color: 'verde', mascotas: ['Luna'] }],
        estaciones: [
          ...Array.from({ length: 6 }, (_, i) => estacion(-30 * (6 - i), 'hecha', `Cuota ${i + 1}`, `h${i}`)),
          estacion(9, 'proxima', 'Cuota de noviembre', 'q1'),
        ],
      },
    }),
  )
}

test.describe('portal de la familia', () => {
  test.use({ viewport: { width: 390, height: 844 } })

  test('lo hecho se pliega de verdad y «hoy» queda en la primera pantalla', async ({ page }) => {
    await comoFamilia(page)
    await page.goto('/portal')
    const linea = page.getByRole('list', { name: /tu línea/i })
    const pliegue = linea.getByRole('button', { name: /6 hechas/ })
    await expect(pliegue).toBeVisible()
    await expect(linea.getByText(/Cuota 1/)).toBeHidden()
    await expect(linea.getByText(/^Hoy · /)).toBeInViewport()

    await pliegue.click()
    await expect(pliegue).toHaveAttribute('aria-expanded', 'true')
    await expect(linea.getByText(/Cuota 1/)).toBeVisible()
    await pliegue.click()
    await expect(linea.getByText(/Cuota 1/)).toBeHidden()
  })
})
