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

/** Sin desborde horizontal ni fallos de WCAG 2.2 A o AA (axe-core), a los anchos del barrido. */
async function medir(page: Page) {
  for (const ancho of [375, 1280]) {
    await page.setViewportSize({ width: ancho, height: 900 })
    const desborda = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1)
    expect(desborda, `desborda a ${ancho} px`).toBe(false)
    // Todas las reglas de WCAG 2.2 A y AA, como el barrido contra el stack (R4-CIE-02).
    const { violations } = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze()
    expect(violations.flatMap((v) => v.nodes.map((n) => `${v.id}: ${n.target.join(' ')}`)), `accesibilidad a ${ancho} px`).toEqual([])
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

// El registro en línea (R3-PUB-02): las fichas de la manada, el comparador y el pago, con el
// catálogo interceptado. Las pastillas de plan y las formas de pago esconden su `input`.
const BENEFICIOS = [
  { tipo_servicio_codigo: 'atencion_aliada', nombre: 'Atención en clínica aliada', cupo: 2, periodo_cupo: 'anual', cobertura_pct: 40, copago: '0.00', texto: '2 al año · cubre el 40 %' },
  { tipo_servicio_codigo: 'consulta_domiciliaria', nombre: 'Consulta domiciliaria', cupo: 1, periodo_cupo: 'mensual', cobertura_pct: 100, copago: '0.00', texto: '1 al mes' },
  { tipo_servicio_codigo: 'orientacion_virtual', nombre: 'Orientación veterinaria virtual', cupo: null, periodo_cupo: 'anual', cobertura_pct: 100, copago: '0.00', texto: 'Sin tope de usos' },
]
const PLAN_REGISTRO = (id: string, nombre: string, color: string, valor: string) => ({
  id,
  codigo: id,
  nombre,
  descripcion: null,
  especies: ['canino', 'felino'],
  color,
  tarifas: [{ peludos: 1, valor }],
  tarifas_periodicidad: [],
  beneficios: BENEFICIOS,
  // R3-PUB-04: la API dice los adicionales de cada plan, y el comparador tiene sus filas.
  adicionales: [{ nombre: 'Servicio fúnebre', cubre: '100 %', detalle: null, carencia: 'Desde los 30 días', tercero: false }],
  carencia: 'Sin periodo de carencia.',
  exclusiones: 'Excluye preexistencias. Los beneficios no se acumulan y los topes aplican por episodio.',
  terminos_url: null,
})
const COTIZACION_REGISTRO = ['mensual', 'trimestral', 'semestral', 'anual'].map((periodicidad, i) => ({
  periodicidad,
  meses: [1, 3, 6, 12][i],
  tarifa_de: 1,
  peludos: [{ especie: 'canino', plan_id: 'fiel', plan_nombre: 'Mi Amigo Fiel', valor_mensual: '69000.00' }],
  valor_mensual: '69000.00',
  valor_periodo: String(69000 * [1, 3, 6, 12][i]!),
  descuento: false,
  ahorro: '0.00',
}))

test('el registro arma la manada, compara y paga sin desbordar ni fallos de accesibilidad', async ({ page }) => {
  await page.route('**/api/v1/**', (ruta) => ruta.fulfill({ status: 401, json: { detail: 'Sin sesión' } }))
  await page.route('**/api/v1/afiliaciones/registro/ciudades', (ruta) => ruta.fulfill({ json: ['Bogotá', 'Medellín'] }))
  await page.route('**/api/v1/afiliaciones/registro/planes**', (ruta) =>
    ruta.fulfill({
      json: [
        PLAN_REGISTRO('colita', 'Colita Feliz', 'naranja', '35500.00'),
        PLAN_REGISTRO('fiel', 'Mi Amigo Fiel', 'verde', '69000.00'),
        PLAN_REGISTRO('siempre', 'Amigos por Siempre', 'azul', '98000.00'),
      ],
    }),
  )
  await page.route('**/api/v1/afiliaciones/registro/cotizacion', (ruta) => ruta.fulfill({ json: COTIZACION_REGISTRO }))
  await page.setViewportSize({ width: 375, height: 812 })
  await page.goto('/afiliacion')
  await page.getByLabel('¿En qué ciudad vives?').selectOption('Medellín')
  await page.getByRole('button', { name: 'Confirmo que solo voy a afiliar perros o gatos' }).click()
  await page.getByRole('region', { name: /^Peludo 1/ }).getByLabel('Nombre').fill('Toby')
  // La ficha toma el nombre del peludo en cuanto se escribe.
  const ficha = page.getByRole('region', { name: /^Toby/ })
  // La pastilla se elige pulsando su etiqueta: el radio va escondido.
  await ficha.getByText('Mi Amigo Fiel', { exact: true }).click()
  await expect(ficha.getByRole('radio', { name: /Mi Amigo Fiel/ })).toBeChecked()
  await ficha.getByRole('button', { name: 'Comparar los 3 planes' }).click()
  await expect(ficha.getByRole('table')).toBeVisible()
  await medir(page)

  await page.getByRole('button', { name: 'Elegir cómo pagar' }).click()
  await page.getByText('Trimestral', { exact: true }).click()
  await expect(page.getByRole('radio', { name: /Trimestral/ })).toBeChecked()
  await expect(page.getByRole('button', { name: /^Pagar \$\s207\.000$/ })).toBeVisible()
  await medir(page)
})
