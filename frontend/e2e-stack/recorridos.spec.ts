import { expect, test } from '@playwright/test'

import { rutaDemo } from './datos'
import { sesion } from './sesiones'

/**
 * Recorridos contra el stack real, con los usuarios de `scripts.datos_demo`. Nada se
 * intercepta: si un contrato entre panel y API se rompe, o el entorno no quedó bien
 * levantado, falla aquí y no en producción. El ingreso de cada perfil ya lo hizo
 * sesiones.setup.ts por el formulario real.
 */

test.describe('atención al cliente', () => {
  test.use({ storageState: sesion('atencion') })

  test('busca una familia en el panel y abre su ficha con sus mascotas', async ({ page }) => {
    await page.goto('/panel')
    // En el Inicio el h1 es el saludo: la cabecera del módulo no se repite.
    await expect(page.getByRole('heading', { level: 1, name: /^Hola, / })).toBeVisible()
    await page.getByRole('link', { name: 'Familias' }).first().click()
    await page.getByRole('link', { name: 'Ana Ruiz' }).click()
    await expect(page.getByRole('heading', { name: 'Ana Ruiz' })).toBeVisible()
    await page.getByRole('tab', { name: 'Mascotas' }).click()
    await expect(page.getByRole('tabpanel', { name: 'Mascotas' }).getByText('Luna')).toBeVisible()
    // La sesión vive en cookies httpOnly: el navegador no guarda credenciales a la vista.
    expect(await page.evaluate(() => window.localStorage.length)).toBe(0)
  })

  test('una ventana abierta queda por encima de la línea y de las barras', async ({ page }) => {
    // En el celular la ficha de una mascota es una hoja que sube desde abajo sobre la línea.
    await page.setViewportSize({ width: 390, height: 844 })
    // Sin cargar antes el Inicio: la sesión del setup sigue vigente y cada pantalla gasta cupo.
    const familias = await (await page.request.get('/api/v1/familias', { params: { q: 'Ana Ruiz' } })).json()
    await page.goto(`/panel/familias/${familias.items[0].id}`)
    await expect(page.locator('.parada-punto').first()).toBeVisible()
    await page.getByRole('tab', { name: 'Mascotas' }).click()
    await page.getByRole('button', { name: 'Ficha' }).first().click()
    await expect(page.getByRole('dialog')).toBeVisible()
    const encima = await page.evaluate(() => {
      // Radix quita los eventos de puntero a todo lo que queda fuera de la ventana, y
      // elementFromPoint se los salta: se devuelven mientras se mide el orden de pintado.
      const antes = document.body.style.pointerEvents
      document.body.style.pointerEvents = 'auto'
      const tapan = [...document.querySelectorAll('.parada-punto, .linea-hoy, .barra-marca, .barra-inferior')].flatMap((e) => {
        const r = e.getBoundingClientRect()
        const [x, y] = [r.left + r.width / 2, r.top + r.height / 2]
        if (r.width === 0 || y < 0 || y > window.innerHeight) return []
        return document.elementFromPoint(x, y)?.closest('[role="dialog"], .velo') ? [] : [e.className]
      })
      document.body.style.pointerEvents = antes
      return tapan
    })
    expect(encima, 'elementos pintados sobre la ventana').toEqual([])
  })

  test('en un formulario cada control conserva su altura aunque el vecino lleve ayuda', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto('/panel/familias')
    await page.getByRole('button', { name: 'Nueva familia' }).click()
    const ventana = page.getByRole('dialog', { name: 'Nueva familia' })
    await expect(ventana).toBeVisible()
    // «Sexo» comparte fila con «Fecha de nacimiento», que lleva un texto de ayuda debajo.
    const sexo = await ventana.getByLabel('Sexo (opcional)').boundingBox()
    const peso = await ventana.getByLabel('Peso (kg)').boundingBox()
    expect(Math.round(sexo!.height)).toBe(Math.round(peso!.height))
  })

  test('el pie de una ventana larga se ve sin desplazarla', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.goto('/panel/familias')
    await page.getByRole('button', { name: 'Nueva familia' }).click()
    const ventana = page.getByRole('dialog', { name: 'Nueva familia' })
    const guardar = ventana.getByRole('button', { name: 'Guardar familia' })
    await expect(guardar).toBeVisible()
    // La ventana recorta lo que se sale de ella: el botón tiene que acabar antes que su borde.
    const [boton, caja] = [await guardar.boundingBox(), await ventana.boundingBox()]
    expect(boton!.y + boton!.height, 'el botón principal se ve entero').toBeLessThanOrEqual(caja!.y + caja!.height)
  })

  test('la ficha de familia tiene una sola acción verde llena en cada pestaña', async ({ page }) => {
    // Manual de marca, sección 11, regla 2: un solo botón principal por vista.
    await page.setViewportSize({ width: 1440, height: 900 })
    // Una familia con próxima estación: su ficha lleva ya la acción verde de la cabecera, y
    // cualquier otra verde en una pestaña sería la segunda.
    const { items } = await (await page.request.get('/api/v1/familias', { params: { limit: 50 } })).json()
    const ids = items.map((f: { id: string }) => f.id)
    const lineas = await (
      await page.request.get(`/api/v1/afiliaciones/lineas?${ids.map((id: string) => `familia_id=${id}`).join('&')}`)
    ).json()
    const conProxima = lineas.find((l: { estaciones: { estado: string }[] }) => l.estaciones.some((e) => e.estado === 'proxima'))
    expect(conProxima, 'datos_demo deja alguna familia con una estación próxima').toBeTruthy()
    await page.goto(`/panel/familias/${conProxima.familia_id}`)
    await expect(page.locator('.ficha-acciones .btn-primario')).toBeVisible()
    const verdes: Record<string, number> = {}
    for (const pestana of await page.getByRole('tab').allTextContents()) {
      await page.getByRole('tab', { name: pestana, exact: true }).click()
      await page.waitForLoadState('networkidle')
      verdes[pestana] = await page.locator('.btn-primario:visible').count()
    }
    expect(Object.entries(verdes).filter(([, n]) => n > 1)).toEqual([])
  })

  test('la foto de una mascota se sube y su URL firmada abre desde el navegador', async ({ page }) => {
    // `page.request` comparte las cookies de la sesión del navegador, sin cargar ninguna pantalla.
    const familias = await (await page.request.get('/api/v1/familias', { params: { q: 'Ana Ruiz' } })).json()
    const mascota = familias.items[0].mascotas[0]
    // PNG de 1×1: el backend valida el tipo por contenido, no por extensión.
    const png = Buffer.from(
      'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC',
      'base64',
    )
    const subida = await page.request.put(`/api/v1/mascotas/${mascota.id}/foto`, {
      multipart: { foto: { name: 'luna.png', mimeType: 'image/png', buffer: png } },
    })
    try {
      expect(subida.ok()).toBeTruthy()
      const { foto_url } = await subida.json()
      // La URL apunta al almacenamiento publicado en el host, no al nombre interno del contenedor.
      expect(foto_url).not.toContain('almacenamiento:8333')
      const imagen = await page.request.get(foto_url)
      expect(imagen.status()).toBe(200)
      expect(imagen.headers()['content-type']).toBe('image/png')
    } finally {
      // La mascota vuelve a quedar como estaba: un PNG de 1×1 no puede quedarse como la foto que
      // el portal de Ana enseña en las capturas (DEU-16).
      if (!mascota.foto_url) await page.request.delete(`/api/v1/mascotas/${mascota.id}/foto`)
    }
  })
})

test.describe('comercial', () => {
  test.use({ storageState: sesion('comercial') })

  test('la bandeja de conversaciones carga contra la API real', async ({ page }) => {
    // Con la API simulada esto pasaba aunque el panel pedía un estado que la API rechaza.
    const respuesta = page.waitForResponse((r) => r.url().includes('/api/v1/comercial/conversaciones'))
    await page.goto('/panel/comercial')
    await page.getByRole('tab', { name: 'Conversaciones' }).click()
    expect((await respuesta).status()).toBe(200)
    await expect(page.getByRole('alert')).toHaveCount(0)
  })
})

test.describe('gerencia en el inicio', () => {
  // El tablero de la Sección 8 es de Gerencia (Sección 12).
  test.use({ storageState: sesion('gerencia') })

  test('una cifra abre su serie de 12 meses servida por la API, con una sola acción verde', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 })
    const serie = page.waitForResponse((r) => r.url().includes('/api/v1/dashboard/evolucion'))
    await page.goto('/panel')
    expect((await serie).status()).toBe(200)
    const cifras = page.getByRole('list', { name: 'Cifras del período' })
    await expect(cifras.getByRole('button')).toHaveCount(6)
    await cifras.getByRole('button', { name: /^Recaudo/ }).click()
    const abierta = page.getByRole('region', { name: 'Recaudo en los últimos 12 meses' })
    await expect(abierta.getByRole('group', { name: /mes a mes/ })).toBeVisible()
    await abierta.getByText('Ver los datos').click()
    // La cabecera y los 12 meses.
    await expect(abierta.getByRole('row')).toHaveCount(13)
    // Gerencia mide y no opera: en lugar del día, sus reportes por correo (Sección 12).
    await expect(page.getByRole('heading', { name: 'Reportes programados' })).toBeVisible()
    await expect(page.locator('.btn-primario:visible')).toHaveCount(1)
    await expect(page.getByRole('alert')).toHaveCount(0)
  })
})

test.describe('administración en reglas', () => {
  // Con el perfil de administración: solo él edita reglas. No guarda nada: una regla creada en
  // cada pasada cambiaría la operación que recorren los demás.
  test.use({ storageState: sesion('admin') })

  test('una regla nueva se escribe por campos y la API la dice en palabras antes de guardar', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    // A 390 px el índice de Administración es un selector: la sección se abre por su dirección.
    await page.goto('/panel/admin?pestana=reglas')
    await page.getByRole('button', { name: 'Nueva regla' }).click()
    const ventana = page.getByRole('dialog', { name: 'Nueva regla' })
    await ventana.getByLabel('Cuándo se revisa').selectOption('servicio.elegibilidad')
    await ventana.getByRole('button', { name: 'Añadir una condición' }).click()
    // Las ciudades salen del catálogo de la base, con sus tildes.
    await ventana.getByRole('combobox', { name: 'Valor de la condición 1' }).selectOption('Medellín')
    const descrita = page.waitForResponse((r) => r.url().includes('/api/v1/reglas/describir'))
    await ventana.getByLabel('Motivo que se le dice al equipo').fill('Sin domicilio por ahora')
    expect((await descrita).status()).toBe(200)
    const palabras = ventana.getByRole('region', { name: 'La regla en palabras' })
    await expect(palabras).toContainText('Ciudad de la familia: Medellín')
    await expect(palabras).toContainText('No lo permite: Sin domicilio por ahora')
    const crear = ventana.getByRole('button', { name: 'Crear regla' })
    const [boton, caja] = [await crear.boundingBox(), await ventana.boundingBox()]
    expect(boton!.y + boton!.height, 'el botón principal se ve entero').toBeLessThanOrEqual(caja!.y + caja!.height)
    await ventana.getByRole('button', { name: 'Cerrar' }).click()
    await expect(ventana).toBeHidden()
  })
})

test.describe('atención en servicios', () => {
  // Atención agenda y sigue los servicios (6.5).
  test.use({ storageState: sesion('atencion') })

  test('el listado dice a quién se atiende y abre la ficha sin perder el listado', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 })
    // Sin el filtro de fecha: los datos de demostración se siembran en otro día.
    await page.goto('/panel/servicios?desde=')
    const listado = page.getByRole('list', { name: 'Servicios' })
    // El último del listado: abrirlo no puede dejar la ficha arriba, fuera de la pantalla.
    const ultimo = listado.getByRole('link').last()
    await expect(ultimo).toBeVisible()
    await ultimo.click()
    const ficha = page.getByRole('region', { name: 'Servicio abierto' })
    await expect(ficha.getByRole('heading', { level: 2 })).toBeInViewport()
    // La ficha va fija al desplazar: la fila pulsada no se sale de la vista y, al volver arriba
    // del listado, la ficha sigue a la vista (techo 42).
    await expect(ultimo).toBeInViewport()
    await page.mouse.wheel(0, -3000)
    await expect(listado.getByRole('link').first()).toBeInViewport()
    await expect(ficha.getByRole('heading', { level: 2 })).toBeInViewport()
    // El listado sigue al lado, con la fila abierta marcada y el filtro de la URL intacto.
    await expect(listado.locator('[aria-current="page"]')).toHaveCount(1)
    expect(new URL(page.url()).searchParams.has('desde')).toBe(true)
    // Como mucho una verde: un servicio cerrado no tiene acción que tocar.
    expect(await page.locator('.btn-primario:visible').count()).toBeLessThanOrEqual(1)
    await expect(page.getByRole('alert')).toHaveCount(0)
  })
})

test.describe('atención en cartera y preventivos', () => {
  // Atención cobra y pide las autorizaciones a la familia (6.2, 6.9).
  test.use({ storageState: sesion('atencion') })

  test('la cartera abre en lo que se debe y cobra desde la fila con las cuotas de la familia', async ({ page }) => {
    await page.goto('/panel/cartera')
    await expect(page.getByRole('button', { name: /^Vencidas \d+$/ })).toHaveAttribute('aria-pressed', 'true')
    // datos_demo deja a Ana Ruiz con cuotas vencidas.
    await page.getByRole('button', { name: 'Registrar pago de Ana Ruiz' }).click()
    const ventana = page.getByRole('dialog', { name: 'Registrar pago de Ana Ruiz' })
    // Abre con la cuota vencida más antigua puesta.
    await expect(ventana.getByLabel('Cuota')).not.toHaveValue('')
    await page.keyboard.press('Escape')
    await expect(page.getByRole('alert')).toHaveCount(0)
  })

  test('los preventivos se piden a cada familia de una vez y en «Todos» dicen su estado', async ({ page }) => {
    await page.goto('/panel/preventivos')
    const autorizar = page.getByRole('button', { name: /^Registrar autorización/ }).first()
    await autorizar.click()
    const ventana = page.getByRole('dialog', { name: /^Autorización de / })
    // Llega todo lo pendiente de la familia marcado.
    await expect(ventana.getByRole('checkbox').first()).toBeChecked()
    await page.keyboard.press('Escape')
    await page.getByRole('button', { name: /^Todos \d+$/ }).click()
    await expect(page.getByRole('columnheader', { name: 'Estado' })).toBeVisible()
    await expect(page.getByRole('alert')).toHaveCount(0)
  })
})

test.describe('comercial en sus conversaciones', () => {
  // Comercial contesta a quien espera un asesor (6.11).
  test.use({ storageState: sesion('comercial') })

  test('la conversación que espera a un asesor lleva a la ficha del interesado, con sus mensajes', async ({ page }) => {
    await page.goto('/panel/comercial')
    await page.getByRole('tab', { name: 'Conversaciones' }).click()
    // datos_demo deja a Natalia Gómez pidiendo un asesor por WhatsApp.
    await page.getByRole('link', { name: 'Abrir conversación' }).first().click()
    const ficha = page.getByRole('region', { name: 'Interesado abierto' })
    await expect(ficha.getByRole('list', { name: /^Mensajes con / })).toBeVisible()
    await expect(ficha.getByText('Espera a un asesor')).toBeVisible()
    await expect(ficha.getByRole('list', { name: 'Etapas del embudo' })).toBeVisible()
    await expect(page.getByRole('alert')).toHaveCount(0)
  })
})

test.describe('médico en el inicio', () => {
  test.use({ storageState: sesion('medico') })

  test('entra a su jornada: lo que tiene sin firmar, Hoy y las paradas de su ruta', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/panel')
    await expect(page.getByRole('heading', { level: 1, name: /^Hola, / })).toBeVisible()
    const jornada = page.getByRole('list', { name: 'Tu jornada' })
    await expect(jornada.getByText(/^Hoy · /)).toBeVisible()
    // El médico no ve las cifras de la gerencia: la API se las negaría.
    await expect(page.getByRole('list', { name: 'Cifras del período' })).toHaveCount(0)
    await expect(page.getByRole('navigation', { name: 'Módulos principales' }).getByRole('link', { name: 'Inicio' })).toHaveAttribute('aria-current', 'page')
    await expect(page.getByRole('alert')).toHaveCount(0)
  })
})

test.describe('médico en ruta', () => {
  test.use({ storageState: sesion('medico') })

  // Solo lectura: avanzar paradas gastaría la ruta de prueba y la siguiente pasada no tendría
  // qué recorrer. Lo que cambia el estado lo cubren las pruebas del panel y las del backend.
  test('abre en su ruta del día: la parada que sigue dice a dónde ir y a quién atiende', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    const yo = await (await page.request.get('/api/v1/auth/me')).json()
    const { url } = await rutaDemo(page.request, yo.id)
    const rutas = page.waitForResponse((r) => r.url().includes('/api/v1/rutas?'))
    await page.goto(url)
    expect(new URL((await rutas).url()).searchParams.get('responsable_id')).toBe(yo.id)

    const paradas = page.getByRole('list', { name: 'Paradas de la ruta' })
    await expect(paradas).toBeVisible()
    // La parada que toca lleva su dirección como título, y la navegación del celular.
    await expect(paradas.getByRole('heading', { level: 3 }).first()).toBeVisible()
    const llegar = paradas.getByRole('link', { name: 'Cómo llegar' }).first()
    await expect(llegar).toHaveAttribute('href', /^https:\/\/www\.google\.com\/maps\/dir\/\?api=1&destination=/)
    await expect(paradas.getByRole('link', { name: /^Llamar a / }).first()).toHaveAttribute('href', /^tel:\+57/)
    await expect(page.getByRole('alert')).toHaveCount(0)
  })

  test('el resumen de la ruta se parte sin dejar un punto colgado (DEU-80)', async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 700 })
    const yo = await (await page.request.get('/api/v1/auth/me')).json()
    await page.goto((await rutaDemo(page.request, yo.id)).url)
    const resumen = page.locator('.rutas-resumen').first()
    await expect(resumen).toBeVisible()
    // La pieza que empieza una línea lleva su punto en el aire recortado, a la izquierda de la fila.
    const { piezas, lineas, colgados } = await resumen.evaluate((p) => {
      const borde = p.getBoundingClientRect().left
      const cajas = [...p.querySelectorAll('.rutas-pieza')].map((s) => s.getBoundingClientRect())
      const empiezan = cajas.filter((r, i) => i === 0 || r.top > cajas[i - 1]!.top + 1)
      return { piezas: cajas.length, lineas: empiezan.length, colgados: empiezan.filter((r) => r.left >= borde - 1).length }
    })
    expect(piezas, 'paradas, kilómetros y hora de llegada').toBeGreaterThan(2)
    expect(lineas, 'a 320 px el resumen se parte').toBeGreaterThan(1)
    expect(colgados, 'piezas que empiezan línea con su punto a la vista').toBe(0)
  })
})

test.describe('médico en clínica', () => {
  test.use({ storageState: sesion('medico') })

  // Solo lectura, como en Rutas: firmar gastaría el borrador que deja datos_demo.
  test('abre en su trabajo pendiente y sigue un borrador en la consulta guiada', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/panel/clinica')
    const sinFirmar = page.getByRole('region', { name: 'Consultas sin firmar' })
    await sinFirmar.getByRole('link').first().click()
    const guia = page.getByRole('list', { name: 'Apartados de la consulta' })
    await expect(guia).toBeVisible()
    await expect(guia.getByRole('button')).toHaveCount(5)
    await expect(guia.locator('[aria-current="step"]')).toHaveCount(1)
    // Una sola acción verde: la de seguir o firmar la consulta.
    await expect(page.locator('.btn-primario:visible')).toHaveCount(1)
    await expect(page.getByRole('alert')).toHaveCount(0)
  })

  // Solo lectura también: la consulta nace al dejar el motivo, y avanzar dejaría un borrador en
  // cada pasada. Que la plantilla llena los demás apartados lo prueba clinica.test.tsx.
  test('una consulta nueva parte de una plantilla de datos_demo y la usa de punto de partida', async ({ page, playwright, baseURL }) => {
    await page.goto('/panel/clinica')
    // El médico no ve Familias (Sección 12): la mascota se busca con la sesión de Atención.
    const atencion = await playwright.request.newContext({ baseURL, storageState: sesion('atencion') })
    const familias = await atencion.get('/api/v1/familias', { params: { q: 'Ana Ruiz', limit: 5 } })
    expect(familias.ok(), `GET /familias respondió ${familias.status()}`).toBeTruthy()
    const { items } = (await familias.json()) as { items: { titular_nombre: string; mascotas: { id: string; nombre: string }[] }[] }
    const michi = items.find((f) => f.titular_nombre === 'Ana Ruiz')?.mascotas.find((m) => m.nombre === 'Michi')
    expect(michi, 'datos_demo no dejó a Michi, de Ana Ruiz').toBeTruthy()
    await atencion.dispose()

    await page.goto(`/panel/clinica/mascotas/${michi!.id}?nueva=1`)
    const plantilla = page.getByLabel('Plantilla')
    for (const nombre of ['Control general', 'Gastroenteritis leve', 'Otitis externa']) {
      await expect(plantilla.getByRole('option', { name: nombre })).toBeAttached()
    }
    await plantilla.selectOption({ label: 'Otitis externa' })
    await expect(page.getByRole('textbox', { name: 'Motivo de consulta' })).toHaveValue('Se rasca las orejas y sacude la cabeza.')
    await expect(page.getByRole('alert')).toHaveCount(0)
  })
})

test.describe('operaciones en rutas', () => {
  test.use({ storageState: sesion('operaciones') })

  test('ve las rutas del día y abre una con sus paradas', async ({ page }) => {
    const { url } = await rutaDemo(page.request)
    await page.goto(url)
    const listado = page.getByRole('region', { name: /Rutas del día/ })
    // La fila de una ruta con paradas, no el primer enlace: «Por rutear» va en la misma región y
    // sus servicios pueden pintarse antes que las rutas.
    const conParadas = listado.getByRole('listitem').filter({ has: page.getByRole('img', { name: /de [1-9]\d* paradas? hechas?/ }) })
    await conParadas.first().getByRole('link').click()
    const abierta = page.getByRole('region', { name: 'Ruta abierta' })
    await expect(abierta.getByRole('list', { name: 'Paradas de la ruta' })).toBeVisible()
    await expect(abierta.getByRole('heading', { level: 2 })).not.toHaveText('Sin responsable')
    await expect(page.getByRole('alert')).toHaveCount(0)
  })
})

test.describe('familia', () => {
  test.use({ storageState: sesion('familia') })

  test('entra a su portal, ve su línea abierta en hoy y sus peludos, y no llega al panel del equipo', async ({ page }) => {
    await page.goto('/panel')
    await expect(page).toHaveURL(/\/portal/)
    await expect(page.getByRole('heading', { level: 1, name: 'Hola, Ana' })).toBeVisible()
    // R3-POR-01: la línea de la familia, servida por /portal/linea, abre en «hoy».
    await expect(page.getByRole('list', { name: /tu línea/i }).getByText(/^Hoy · /)).toBeVisible()
    await page.getByRole('navigation', { name: 'Portal' }).getByRole('link', { name: 'Peludos' }).click()
    await expect(page.getByRole('heading', { level: 1, name: 'Tus peludos' })).toBeVisible()
    await expect(page.getByRole('link', { name: /luna/i })).toBeVisible()
    // R3-POR-02: Ana debe cuotas, así que sus pagos ofrecen un solo verde por lo pendiente.
    await page.getByRole('navigation', { name: 'Portal' }).getByRole('link', { name: 'Pagos' }).click()
    await expect(page.getByRole('heading', { level: 1, name: 'Tus pagos' })).toBeVisible()
    await expect(page.locator('.btn-primario')).toHaveCount(1)
    await expect(page.getByRole('button', { name: /^Pagar \$/ }).first()).toHaveClass(/btn-primario/)
    await page.goto('/panel/familias')
    await expect(page).toHaveURL(/\/portal/)
  })
})

test.describe('clínica aliada', () => {
  test.use({ storageState: sesion('aliada') })

  test('valida una remisión emitida sin consumirla', async ({ page, playwright, baseURL }) => {
    // El código lo consulta el equipo, como haría quien emite la remisión.
    const equipo = await playwright.request.newContext({ baseURL, storageState: sesion('atencion') })
    const remisiones = await (await equipo.get('/api/v1/aliadas/remisiones', { params: { estado: 'emitida' } })).json()
    await equipo.dispose()
    // La de datos_demo, por su motivo: con la operación sembrada hay otras emitidas, y la primera
    // del listado (la que vence antes) puede ser una ya vencida, que la clínica no valida.
    const vigente = remisiones.find(
      (r: { motivo: string; vencida: boolean }) => r.motivo === 'Radiografía de cadera por cojera' && !r.vencida,
    )
    expect(vigente, 'datos_demo debe dejar una remisión emitida y vigente').toBeTruthy()
    const codigo: string = vigente.codigo

    await page.goto('/panel')
    await expect(page).toHaveURL(/\/aliada/)
    // La barra dice en qué clínica se está: la aliada lee su propia fila (migración 0049).
    await expect(page.getByRole('banner')).toContainText('Clínica Veterinaria del Norte')
    await page.getByLabel('Código de la remisión').fill(codigo.toLowerCase())
    await page.getByRole('button', { name: 'Validar' }).click()
    await expect(page.getByText(/Se puede atender hasta el/)).toBeVisible()
    await expect(page.getByText('Radiografía de cadera por cojera')).toBeVisible()
    // La especie en palabras: la aliada lee el catálogo (antes salía «canino»).
    await expect(page.getByRole('heading', { name: /Rocky · Canino/ })).toBeVisible()

    // Lo que cubre TIMU lo calcula la API antes de reportar; la remisión no se gasta.
    await page.getByLabel('Valor de la atención').fill('100000')
    await expect(page.getByText('Paga la familia')).toBeVisible()
    await expect(page.getByText(/^\$\s80\.000$/)).toBeVisible()
    await expect(page.getByText(/^\$\s20\.000$/)).toBeVisible()
    await expect(page.getByRole('button', { name: 'Reportar atención' })).toBeEnabled()
    await expect(page.getByRole('region', { name: 'Atendidas' })).toBeVisible()
  })
})

test.describe('una familia que se afilia', () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test('arma su manada con el catálogo real y llega al pago con lo que cobra el backend', async ({ page }) => {
    // R3-PUB-02: los planes, lo que cubren y el precio salen de la API de verdad. No se paga: la
    // pasarela de pruebas de Wompi sigue pendiente de TIMU.
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/afiliacion')
    await page.getByLabel('¿En qué ciudad vives?').selectOption('Medellín')
    await page.getByRole('button', { name: 'Confirmo que solo voy a afiliar perros o gatos' }).click()
    await page.getByRole('region', { name: /^Peludo 1/ }).getByLabel('Nombre').fill('Toby')
    // La ficha toma el nombre del peludo en cuanto se escribe.
    const ficha = page.getByRole('region', { name: /^Toby/ })
    await ficha.getByText('Mi Amigo Fiel', { exact: true }).click()
    // Lo que cubre, dicho por la API en palabras, y las condiciones del plan.
    await expect(ficha.getByText('Lo que cubre Mi Amigo Fiel')).toBeVisible()
    await expect(ficha.getByText('Consulta domiciliaria')).toBeVisible()
    await ficha.getByRole('button', { name: /^Comparar los \d planes$/ }).click()
    await expect(ficha.getByRole('table', { name: /Lo que cubre cada plan para Toby/ })).toBeVisible()
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1)).toBe(true)

    // El total de la familia es el que cobra el pago mensual (precios provisionales: no se fijan aquí).
    const resumen = page.getByRole('complementary', { name: 'Tu afiliación' })
    const total = resumen.locator('.registro-total strong')
    await expect(total).toHaveText(/^\$\s[\d.]+ al mes$/)
    const valor = (await total.textContent())!.replace(' al mes', '')
    await resumen.getByRole('button', { name: 'Elegir cómo pagar' }).click()
    await expect(page.getByRole('heading', { level: 1, name: '¿Cómo quieres pagar?' })).toBeVisible()
    await expect(page.getByRole('button', { name: `Pagar ${valor}` })).toBeVisible()
  })

  test('llega desde la portada con su manada armada y ve todo lo que cubre un plan', async ({ page }) => {
    // R3-PUB-04: los planes, las aliadas y los datos de TIMU los dejó `datos_demo` por la API.
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/')
    await expect(page.getByRole('heading', { level: 1, name: 'Tu peludito, bien cuidado.' })).toBeVisible()
    const arma = page.getByRole('form', { name: 'Arma tu plan' })
    await arma.getByLabel('¿Dónde vives?').selectOption('Medellín')
    await arma.getByRole('button', { name: 'Un gato más' }).click()
    await expect(arma.getByText(/^2 peludos, desde/)).toBeVisible()
    // La red sale de Administración → Aliadas, con la clínica de TIMU en su estación.
    await expect(page.getByRole('list', { name: 'Estaciones de la red TIMU' }).getByText("The Dog's Club", { exact: true })).toBeAttached()
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1)).toBe(true)

    await arma.getByRole('link', { name: 'Ver mis planes' }).click()
    await expect(page).toHaveURL(/\/afiliacion\?ciudad=Medell%C3%ADn&perros=1&gatos=1$/)
    await expect(page.getByRole('region', { name: /^Peludo 2/ }).getByRole('radio', { name: 'Gato' })).toBeChecked()

    await page.goto('/service/plan-mi-amigo-fiel/')
    await expect(page).toHaveURL(/\/planes\/mi-amigo-fiel$/)
    await expect(page.getByRole('heading', { level: 1, name: 'Mi Amigo Fiel' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Además' })).toBeVisible()
    await expect(page.getByRole('link', { name: 'Afiliar a mi peludo con Mi Amigo Fiel' })).toHaveAttribute('href', /plan=/)
  })
})
