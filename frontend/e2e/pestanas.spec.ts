import { expect, test, type Page } from '@playwright/test'

// DEU-66: en el celular la tira de pestañas se desplaza en su fila. Si no cabe, el borde por el
// que sigue se desvanece (`data-desborda`), para que la última pestaña cortada no parezca un
// rótulo roto. jsdom no mide el desbordamiento: se prueba aquí. La ficha de familia, con sus siete
// pestañas, es la tira que no cabe a 390 px (Administración pasó a un índice en DEU-76).

test.use({ viewport: { width: 390, height: 844 } })

const FAMILIA = {
  id: 'f1',
  titular_nombre: 'Ana Ruiz',
  tipo_documento: 'CC',
  documento: '1020304050',
  email: null,
  telefono: '573001112233',
  ciudad: 'Bogotá',
  barrio: 'Chapinero',
  direccion: null,
  latitud: null,
  longitud: null,
  geo_precision: null,
  origen: 'manual',
  estado: 'activa',
  notas: null,
  dada_de_baja_en: null,
  motivo_baja: null,
  usuario_portal_id: null,
  mascotas: [],
}

async function abrirFicha(page: Page, ruta: string) {
  // El último handler registrado gana: primero el comodín, luego lo de la prueba.
  await page.route('**/api/v1/**', (r) => r.fulfill({ json: [] }))
  await page.route('**/api/v1/auth/me', (r) =>
    r.fulfill({ json: { id: 'u1', email: 'atencion@timu.co', nombre: 'Mariana Ortiz', rol: 'atencion_cliente', activo: true } }),
  )
  await page.route('**/api/v1/familias/f1', (r) => r.fulfill({ json: FAMILIA }))
  await page.route('**/api/v1/familias/f1/linea', (r) => r.fulfill({ json: { familia_id: 'f1', planes: [], estaciones: [] } }))
  // Una familia sin contrato: la ficha lo dice en vez de su cartera.
  await page.route('**/api/v1/cartera/familias/f1/estado-cuenta', (r) =>
    r.fulfill({ status: 404, json: { detail: 'La familia no tiene contrato' } }),
  )
  // El listado de al lado, con sus filtros en la consulta.
  await page.route((url) => url.pathname === '/api/v1/familias', (r) =>
    r.fulfill({ json: { items: [FAMILIA], total: 1, limit: 25, offset: 0 } }),
  )
  await page.goto(ruta)
  return page.getByRole('tablist', { name: /Secciones de/ })
}

test('la tira de pestañas que no cabe dice por dónde sigue', async ({ page }) => {
  const tira = await abrirFicha(page, '/panel/familias/f1')
  await expect(tira).toHaveAttribute('data-desborda', 'derecha')
  await tira.evaluate((t) => t.scrollTo({ left: t.scrollWidth }))
  await expect(tira).toHaveAttribute('data-desborda', 'izquierda')
})

test('la pestaña activa se ve entera aunque la tira no quepa', async ({ page }) => {
  const tira = await abrirFicha(page, '/panel/familias/f1')
  const ultima = tira.getByRole('tab').last()
  await ultima.click()
  await expect(ultima).toHaveAttribute('data-state', 'active')
  await expect
    .poll(async () => {
      const [t, a] = [await tira.boundingBox(), await ultima.boundingBox()]
      return t && a ? a.x >= t.x - 1 && a.x + a.width <= t.x + t.width + 1 : false
    })
    .toBe(true)
})
