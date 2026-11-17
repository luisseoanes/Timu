import AxeBuilder from '@axe-core/playwright'
import { expect, test, type Page } from '@playwright/test'

// La encuesta y la verificación del carnet (R3-PUB-03) con la API interceptada. El barrido
// contra el stack solo puede abrir la encuesta con un enlace inexistente, porque su token vive en
// la base: aquí se miden el formulario y sus estados, que jsdom no pinta (las opciones esconden
// el `input` y se marcan pulsando la etiqueta).

const SATISFACCION = { tipo: 'satisfaccion', atencion: 'Consulta domiciliaria', fecha: '2026-10-27', mascota: 'Nina', respondida: false }
const SEGUIMIENTO = { ...SATISFACCION, tipo: 'seguimiento' }
const CARNET = {
  codigo: 'YCAHP9D98N',
  emitido_en: '2026-11-17T04:21:00Z',
  sha256: '5'.repeat(64),
  mascota: { nombre: 'Coco', especie: 'Canino', raza: 'Pug' },
  secciones: [
    {
      tipo: 'vacuna',
      titulo: 'Vacunación',
      aplicados: [
        {
          nombre: 'Polivalente canina (moquillo, parvovirus, hepatitis, parainfluenza)',
          dosis: 'Dosis 1',
          fecha_aplicacion: '2026-10-15',
          producto: 'Vanguard Plus',
          lote: 'VP31',
          peso_kg: null,
          aplicado_por: 'Dra. Sara Martínez',
          proxima_fecha: '2027-10-15',
        },
      ],
    },
    {
      tipo: 'desparasitacion_interna',
      titulo: 'Desparasitación interna',
      aplicados: [
        { nombre: 'Desparasitación interna canina', dosis: null, fecha_aplicacion: '2026-10-23', producto: 'Drontal', lote: 'DR15', peso_kg: 8.8, aplicado_por: 'Dra. Sara Martínez', proxima_fecha: '2027-01-21' },
      ],
    },
    { tipo: 'desparasitacion_externa', titulo: 'Desparasitación externa', aplicados: [] },
  ],
  pendientes: [
    { nombre: 'Desparasitación externa canina', dosis: null, fecha_programada: '2026-10-01', vencido: true },
    { nombre: 'Antirrábica canina', dosis: 'Dosis 2, refuerzo', fecha_programada: '2027-09-23', vencido: false },
  ],
}

async function abrir(page: Page, url: string, rutas: Record<string, unknown>) {
  await page.route('**/api/v1/**', (ruta) => ruta.fulfill({ status: 401, json: { detail: 'Sin sesión' } }))
  for (const [patron, cuerpo] of Object.entries(rutas)) {
    await page.route(patron, (ruta) => ruta.fulfill({ json: cuerpo }))
  }
  await page.goto(url)
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
}

/** Sin desborde horizontal ni texto con contraste insuficiente, a los anchos del barrido. */
async function medir(page: Page) {
  for (const ancho of [375, 1280]) {
    await page.setViewportSize({ width: ancho, height: 900 })
    const desborda = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1)
    expect(desborda, `desborda a ${ancho} px`).toBe(false)
    const { violations } = await new AxeBuilder({ page }).withRules(['color-contrast']).analyze()
    expect(violations.flatMap((v) => v.nodes.map((n) => n.target.join(' '))), `contraste a ${ancho} px`).toEqual([])
  }
}

test('la encuesta se califica pulsando la opción, y cabe sin desbordar', async ({ page }) => {
  await abrir(page, '/encuesta/tk1', { '**/api/v1/encuestas/respuesta/tk1': SATISFACCION })
  await page.getByText('Buena', { exact: true }).click()
  await expect(page.getByRole('radio', { name: /Buena/ })).toBeChecked()
  await expect(page.getByRole('button', { name: 'Enviar respuesta' })).toBeEnabled()
  await medir(page)
})

test('el seguimiento con una novedad muestra qué hacer si es urgente, y cabe sin desbordar', async ({ page }) => {
  await abrir(page, '/encuesta/tk1', { '**/api/v1/encuestas/respuesta/tk1': SEGUIMIENTO })
  await page.getByText('Algo no va bien', { exact: true }).click()
  await expect(page.getByRole('radio', { name: 'Algo no va bien' })).toBeChecked()
  await expect(page.getByText(/si es una urgencia/i)).toBeVisible()
  await medir(page)
})

test('la verificación del carnet apila sus tablas en el celular sin desbordar', async ({ page }) => {
  await abrir(page, '/verificar/YCAHP9D98N', { '**/api/v1/verificacion/carnets/YCAHP9D98N': CARNET })
  await expect(page.getByRole('heading', { level: 1, name: 'Carnet auténtico' })).toBeVisible()
  await medir(page)
})
