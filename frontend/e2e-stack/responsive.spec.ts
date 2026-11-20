import { readFileSync } from 'node:fs'
import path from 'node:path'

import AxeBuilder from '@axe-core/playwright'
import { expect, test, type Page } from '@playwright/test'

import { rutaDemo } from './datos'
import { sesion, type Perfil } from './sesiones'

/**
 * Recorrido responsive y de contraste (R0-QAA-02, docs/hoja-de-ruta-rediseno.md).
 *
 * Abre cada ruta de `src/App.tsx` con el perfil que la usa, contra el stack real y los datos
 * de `scripts.datos_demo`, y la mide a 375, 768, 900 y 1280 px. Falla si el documento desborda en
 * horizontal (una tabla dentro de su propio contenedor con desplazamiento sí se permite) o si
 * axe-core encuentra texto con contraste insuficiente (WCAG 2.2 AA, 1.4.3).
 *
 * Una ruta con `pestanas` se mide también con cada una de sus pestañas abierta: su contenido
 * no está en el DOM hasta que se elige. La clave de un fallo lleva entonces la pestaña
 * (`familias/:id#Cartera@375:desborde`). Cada pantalla rediseñada la activa al cerrarse. Una ruta
 * con `fichas` se mide además con cada ficha que abre desde la URL (`admin?plan@375:desborde`):
 * en el celular es lo que se ve al tocar una fila, y no es una ruta propia (R4-CIE-01).
 *
 * Una medida solo vale si la pantalla cargó sus datos. Con un 429 (el límite de la API es por
 * usuario, y el barrido hace muchas peticiones con el mismo) o un 5xx, la pantalla pinta un
 * error, que no desborda: daría por arreglado lo que no lo está. Ante un 429 se espera lo que
 * dice Retry-After y se vuelve a cargar; si el error sigue, la prueba falla.
 *
 * Cualquier fallo hace fallar la prueba: se arregla. La lista de deuda que tuvo (`PENDIENTES`,
 * R0-QAA-02) se vació en R2-PAN-10 y se retiró en R4-CIE-01.
 */

const ANCHOS = [375, 768, 900, 1280] as const
const ALTO = 900

type Fallo = 'desborde' | 'contraste'

interface Ruta {
  /** La ruta tal como la declara App.tsx: el `path` o `index` dentro de su espacio. */
  app: string
  /** Perfil con el que se abre; null para las páginas públicas. */
  perfil: Perfil | null
  /** Dirección que se abre. Las rutas con parámetros piden a la API un registro real. */
  url: string | ((page: Page) => Promise<string>)
  /** Mide también cada pestaña de la pantalla (ver arriba). */
  pestanas?: boolean
  /** Las fichas que la pantalla abre desde la URL, por su nombre, con un registro de datos_demo. */
  fichas?: (page: Page) => Promise<Record<string, string>>
}

const SIN_REGISTRO = '00000000-0000-7000-8000-000000000000'

async function pedir<T>(page: Page, url: string): Promise<T> {
  const respuesta = await page.request.get(`/api/v1${url}`)
  expect(respuesta.ok(), `GET ${url} respondió ${respuesta.status()}`).toBeTruthy()
  return (await respuesta.json()) as T
}

interface Familia { id: string; mascotas?: { id: string }[] }

/** Un registro de datos_demo por su nombre, nunca el primero del listado (docs/frontend/e2e-stack.md). */
async function deDatosDemo(page: Page, url: string, nombre: string): Promise<{ id: string }> {
  const respuesta = await pedir<{ id: string; nombre: string }[] | { items: { id: string; nombre: string }[] }>(page, url)
  const registro = (Array.isArray(respuesta) ? respuesta : respuesta.items).find((r) => r.nombre === nombre)
  expect(registro, `datos_demo deja «${nombre}»`).toBeTruthy()
  return registro!
}

async function familiaDemo(page: Page): Promise<Familia> {
  const { items } = await pedir<{ items: Familia[] }>(page, '/familias?q=Ana%20Ruiz')
  expect(items.length, 'datos_demo crea la familia Ana Ruiz').toBeGreaterThan(0)
  return items[0]
}

/** Una entrada de historia clínica y su mascota, de cualquier familia de datos_demo. */
async function entradaClinica(page: Page): Promise<{ mascota: string; entrada: string }> {
  // El médico no ve Familias (Sección 12): parte de sus borradores (datos_demo deja uno en Luna, con
  // su consulta firmada) y de las mascotas de sus servicios (con operacion_demo hay muchas más).
  const borradores = await pedir<{ mascota_id: string }[]>(page, '/clinica/borradores')
  const { items } = await pedir<{ items: { mascota: { id: string } | null }[] }>(page, '/servicios?limit=50')
  const mascotas = [...borradores.map((b) => b.mascota_id), ...items.flatMap((s) => (s.mascota ? [s.mascota.id] : []))]
  for (const id of new Set(mascotas)) {
    const historia = await pedir<{ id: string }[]>(page, `/clinica/mascotas/${id}/historia`)
    if (historia.length > 0) return { mascota: id, entrada: historia[0].id }
  }
  throw new Error('datos_demo no dejó ninguna entrada de historia clínica')
}

/**
 * Emite un carnet de una mascota de datos_demo con algo aplicado, para medir la verificación con
 * sus tablas (R3-PUB-03). Es lo que hace el equipo desde el panel; la página es pública y se abre
 * igual con la sesión de quien lo emitió.
 */
async function carnetEmitido(page: Page): Promise<string> {
  const { items } = await pedir<{ items: Familia[] }>(page, '/familias?limit=50')
  for (const familia of items) {
    for (const { id } of familia.mascotas ?? []) {
      const { aplicados } = await pedir<{ aplicados: unknown[] }>(page, `/preventivos/mascotas/${id}/carnet`)
      if (aplicados.length === 0) continue
      const emitido = await page.request.post(`/api/v1/preventivos/mascotas/${id}/carnet/pdf`)
      expect(emitido.ok(), `emitir el carnet respondió ${emitido.status()}`).toBeTruthy()
      return `/verificar/${((await emitido.json()) as { codigo: string }).codigo}`
    }
  }
  throw new Error('datos_demo no dejó ninguna mascota con un preventivo aplicado')
}

const RUTAS: Ruta[] = [
  // Páginas públicas. Las que necesitan un enlace válido se abren con uno inexistente: se
  // mide el estado de «enlace no válido», que es lo que ve quien llega con uno vencido. La
  // encuesta con su formulario se mide en e2e/publicas.spec.ts: su token solo está en la base.
  { app: 'index:portada', perfil: null, url: '/' },
  { app: '/planes/:plan', perfil: null, url: '/planes/mi-amigo-fiel' },
  { app: '/login', perfil: null, url: '/login' },
  { app: '/recuperar', perfil: null, url: '/recuperar' },
  { app: '/restablecer', perfil: null, url: '/restablecer' },
  { app: '/activar', perfil: null, url: '/activar' },
  { app: '/encuesta/:token', perfil: null, url: '/encuesta/enlace-inexistente' },
  { app: '/afiliacion', perfil: null, url: '/afiliacion' },
  { app: '/afiliacion/resultado', perfil: null, url: '/afiliacion/resultado' },
  { app: '/afiliacion/completar', perfil: null, url: '/afiliacion/completar' },

  // Panel del equipo.
  // Un Inicio por perfil (Sección 12): cada uno es otra pantalla, y cada uno se mide.
  { app: 'index:panel', perfil: 'atencion', url: '/panel' },
  { app: 'index:panel', perfil: 'admin', url: '/panel' },
  { app: 'index:panel', perfil: 'gerencia', url: '/panel' },
  { app: 'index:panel', perfil: 'comercial', url: '/panel' },
  { app: 'index:panel', perfil: 'operaciones', url: '/panel' },
  { app: 'familias', perfil: 'atencion', url: '/panel/familias' },
  {
    app: 'familias/:id',
    perfil: 'atencion',
    url: async (page) => `/panel/familias/${(await familiaDemo(page)).id}`,
    pestanas: true,
  },
  { app: 'cartera', perfil: 'atencion', url: '/panel/cartera' },
  { app: 'servicios', perfil: 'atencion', url: '/panel/servicios', pestanas: true },
  {
    app: 'servicios/:id',
    perfil: 'medico',
    url: async (page) => {
      const { items } = await pedir<{ items: { id: string }[] }>(page, '/servicios?limit=1')
      expect(items.length, 'datos_demo crea servicios').toBeGreaterThan(0)
      return `/panel/servicios/${items[0].id}`
    },
  },
  { app: 'tareas', perfil: 'atencion', url: '/panel/tareas' },
  { app: 'preventivos', perfil: 'atencion', url: '/panel/preventivos', pestanas: true },
  {
    app: 'clinica',
    perfil: 'medico',
    url: '/panel/clinica',
    pestanas: true,
    fichas: async () => ({ plantilla: '/panel/clinica?plantilla=otitis_externa' }),
  },
  { app: 'clinica/mascotas/:mascotaId', perfil: 'medico', url: async (page) => `/panel/clinica/mascotas/${(await entradaClinica(page)).mascota}` },
  { app: 'clinica/historias/:id', perfil: 'medico', url: async (page) => `/panel/clinica/historias/${(await entradaClinica(page)).entrada}` },
  {
    // La ruta de la médica, en el día en que datos_demo la dejó: sin ella se mediría el vacío.
    app: 'rutas',
    perfil: 'medico',
    url: async (page) => {
      const yo = await pedir<{ id: string }>(page, '/auth/me')
      return (await rutaDemo(page.request, yo.id)).url
    },
    fichas: async (page) => {
      const yo = await pedir<{ id: string }>(page, '/auth/me')
      const { dia, url } = await rutaDemo(page.request, yo.id)
      const rutas = await pedir<{ id: string; paradas: unknown[] }[]>(page, `/rutas?fecha=${dia}&responsable_id=${yo.id}`)
      const ruta = rutas.find((r) => r.paradas.length > 0)
      expect(ruta, 'datos_demo deja la ruta de la médica').toBeTruthy()
      return { ruta: `${url}${url.includes('?') ? '&' : '?'}ruta=${ruta!.id}` }
    },
  },
  // El planificador de rutas: lo que ve Operaciones (el médico ve su ruta, arriba).
  { app: 'rutas', perfil: 'operaciones', url: '/panel/rutas' },
  {
    app: 'campanas',
    perfil: 'comercial',
    url: '/panel/campanas',
    pestanas: true,
    fichas: async (page) => ({ campana: `/panel/campanas?campana=${(await deDatosDemo(page, '/campanas', 'Renovaciones del mes')).id}` }),
  },
  // Atención emite las remisiones; Operaciones lleva la red y su liquidación.
  { app: 'aliadas', perfil: 'atencion', url: '/panel/aliadas' },
  {
    app: 'aliadas',
    perfil: 'operaciones',
    url: '/panel/aliadas',
    pestanas: true,
    fichas: async (page) => {
      const clinica = await deDatosDemo(page, '/aliadas', 'Clínica Veterinaria del Norte')
      return { clinica: `/panel/aliadas?pestana=clinicas&clinica=${clinica.id}` }
    },
  },
  {
    app: 'comercial',
    perfil: 'comercial',
    url: '/panel/comercial',
    pestanas: true,
    fichas: async (page) => {
      const interesado = await deDatosDemo(page, '/comercial/interesados?q=Natalia', 'Natalia Gómez')
      return { interesado: `/panel/comercial?interesado=${interesado.id}` }
    },
  },
  { app: 'encuestas', perfil: 'atencion', url: '/panel/encuestas' },
  { app: 'mensajes', perfil: 'atencion', url: '/panel/mensajes' },
  // Con sus nueve pestañas: configura y nada más (Sección 12).
  {
    app: 'admin',
    perfil: 'admin',
    url: '/panel/admin',
    pestanas: true,
    fichas: async (page) => {
      const planes = await pedir<{ id: string; codigo: string }[]>(page, '/planes')
      const reglas = await pedir<{ id: string; codigo: string }[]>(page, '/reglas')
      const plan = planes.find((p) => p.codigo === 'mi_amigo_fiel')
      const regla = reglas.find((r) => r.codigo === 'alerta_mora_25')
      expect(plan && regla, 'el plan y la regla que siembran las migraciones').toBeTruthy()
      return { plan: `/panel/admin?plan=${plan!.id}`, regla: `/panel/admin?regla=${regla!.id}` }
    },
  },
  // La verificación pública de un carnet de verdad (R3-PUB-03): lo emite Atención al cliente.
  { app: '/verificar/:codigo', perfil: 'atencion', url: carnetEmitido },

  // Portal de familias.
  { app: 'index:portal', perfil: 'familia', url: '/portal' },
  { app: 'mascotas', perfil: 'familia', url: '/portal/mascotas' },
  { app: 'mascotas/nueva', perfil: 'familia', url: '/portal/mascotas/nueva' },
  {
    app: 'mascotas/:mascotaId',
    perfil: 'familia',
    url: async (page) => {
      const familia = await pedir<Familia>(page, '/portal/mi-familia')
      expect(familia.mascotas?.length, 'la familia de datos_demo tiene mascotas').toBeTruthy()
      return `/portal/mascotas/${familia.mascotas![0].id}`
    },
    pestanas: true,
  },
  { app: 'citas', perfil: 'familia', url: '/portal/citas', pestanas: true },
  { app: 'pagos', perfil: 'familia', url: '/portal/pagos' },
  {
    // Regreso desde la pasarela. Sin pagos en datos_demo se mide con un pago inexistente.
    app: 'pagos/:pagoId',
    perfil: 'familia',
    url: async (page) => {
      const pagos = await pedir<{ id: string }[]>(page, '/portal/pagos')
      return `/portal/pagos/${pagos[0]?.id ?? SIN_REGISTRO}`
    },
  },
  { app: 'datos', perfil: 'familia', url: '/portal/datos' },

  // Clínica aliada.
  { app: 'aliada', perfil: 'aliada', url: '/aliada' },
]

/** Elementos que se salen por la derecha de la ventana: los tres más anchos. */
async function desbordes(page: Page): Promise<string[]> {
  return page.evaluate(() => {
    const ancho = document.documentElement.clientWidth
    if (document.documentElement.scrollWidth <= ancho + 1) return []
    const describir = (e: Element) =>
      e.tagName.toLowerCase() + (e.id ? `#${e.id}` : '') + [...e.classList].map((c) => `.${c}`).join('')
    return [...document.body.querySelectorAll('*')]
      .map((e) => ({ e, derecha: e.getBoundingClientRect().right }))
      .filter(({ derecha }) => derecha > ancho + 1)
      .sort((a, b) => b.derecha - a.derecha)
      .slice(0, 3)
      .map(({ e, derecha }) => `${describir(e)} (hasta ${Math.round(derecha)} px)`)
  })
}

async function contrastes(page: Page): Promise<string[]> {
  const { violations } = await new AxeBuilder({ page }).withRules(['color-contrast']).analyze()
  return violations.flatMap((v) => v.nodes.slice(0, 3).map((n) => n.target.join(' ')))
}

async function esperarPantalla(page: Page) {
  await page.waitForLoadState('networkidle')
  await page.evaluate(() => document.fonts.ready)
}

/** Mide la pantalla que hay a la vista a los cuatro anchos y anota lo que falla. */
async function medir(page: Page, vista: string, encontrados: Map<string, string[]>) {
  for (const ancho of ANCHOS) {
    await page.setViewportSize({ width: ancho, height: ALTO })
    await page.evaluate(() => new Promise((listo) => requestAnimationFrame(() => requestAnimationFrame(listo))))
    const medidas: [Fallo, string[]][] = [
      ['desborde', await desbordes(page)],
      ['contraste', await contrastes(page)],
    ]
    for (const [fallo, detalle] of medidas) {
      if (detalle.length > 0) encontrados.set(`${vista}@${ancho}:${fallo}`, detalle)
    }
  }
}

interface FalloApi { estado: number; ruta: string; espera: number }

/**
 * Anota las respuestas de la API que dejan la pantalla en un error (429 y 5xx). En una página
 * pública no cuenta /auth/: sin sesión, el cliente pregunta por ella y la renueva, y esa
 * renovación comparte el límite del ingreso (10 por minuto y por IP), pero la página se pinta
 * igual con o sin sesión.
 */
function vigilarApi(page: Page, publica: boolean): FalloApi[] {
  const fallos: FalloApi[] = []
  page.on('response', (r) => {
    const estado = r.status()
    if (!r.url().includes('/api/') || (estado !== 429 && estado < 500)) return
    if (publica && r.url().includes('/api/v1/auth/')) return
    fallos.push({ estado, ruta: new URL(r.url()).pathname, espera: Number(r.headers()['retry-after'] ?? 1) })
  })
  return fallos
}

/** Carga (o vuelve a cargar) hasta que la API responde sin límite; falla si no lo consigue. */
async function cargarConDatos(page: Page, fallos: FalloApi[], cargar: (reintento: boolean) => Promise<void>) {
  for (let intento = 0; intento < 3; intento++) {
    fallos.length = 0
    await cargar(intento > 0)
    await esperarPantalla(page)
    const limite = fallos.find((f) => f.estado === 429)
    if (!limite) break
    const espera = Math.min(Math.max(limite.espera, 1), 60) * 1000 + 500
    // La espera no cuenta contra el tiempo de la prueba: se le suma.
    test.info().setTimeout(test.info().timeout + espera)
    await page.waitForTimeout(espera)
  }
  expect(
    fallos.map((f) => `${f.estado} ${f.ruta}`),
    'la API respondió con error: se mediría la pantalla de error, no la de verdad',
  ).toEqual([])
}

for (const perfil of [null, 'atencion', 'admin', 'gerencia', 'comercial', 'operaciones', 'medico', 'familia', 'aliada'] as const) {
  test.describe(perfil ? `responsive y contraste · ${perfil}` : 'responsive y contraste · público', () => {
    test.use({ storageState: perfil ? sesion(perfil) : { cookies: [], origins: [] } })

    for (const ruta of RUTAS.filter((r) => r.perfil === perfil)) {
      test(ruta.app, async ({ page }) => {
        await page.setViewportSize({ width: ANCHOS[ANCHOS.length - 1], height: ALTO })
        const url = typeof ruta.url === 'string' ? ruta.url : await ruta.url(page)
        const fallosApi = vigilarApi(page, perfil === null)
        await cargarConDatos(page, fallosApi, async (reintento) => {
          await (reintento ? page.reload() : page.goto(url))
        })
        // Si el perfil no puede entrar, ProtectedRoute lo saca: eso mediría otra pantalla.
        expect(new URL(page.url()).pathname, 'la ruta no redirige a otra pantalla').toBe(url.split('?')[0])

        const encontrados = new Map<string, string[]>()
        const pestanas = ruta.pestanas ? await page.getByRole('tab').allTextContents() : []
        if (ruta.pestanas) expect(pestanas.length, 'la pantalla tiene pestañas').toBeGreaterThan(0)
        for (const pestana of pestanas.length > 0 ? pestanas : [null]) {
          if (pestana) {
            await page.setViewportSize({ width: ANCHOS[ANCHOS.length - 1], height: ALTO })
            await cargarConDatos(page, fallosApi, async (reintento) => {
              if (reintento) {
                await page.reload()
                await esperarPantalla(page)
              }
              await page.getByRole('tab', { name: pestana, exact: true }).click()
            })
          }
          await medir(page, pestana ? `${ruta.app}#${pestana}` : ruta.app, encontrados)
        }

        const fichas = ruta.fichas ? await ruta.fichas(page) : {}
        for (const [nombre, direccion] of Object.entries(fichas)) {
          test.info().setTimeout(test.info().timeout + 20_000)
          await page.setViewportSize({ width: ANCHOS[ANCHOS.length - 1], height: ALTO })
          await cargarConDatos(page, fallosApi, async (reintento) => {
            await (reintento ? page.reload() : page.goto(direccion))
          })
          // La ficha de verdad: la vacía lleva el mismo nombre accesible (frontend/CLAUDE.md).
          await expect(page.locator('.ficha-abierta:not(.ficha-vacia)').first(), `se abre la ficha ${nombre}`).toBeVisible()
          await medir(page, `${ruta.app}?${nombre}`, encontrados)
        }

        expect([...encontrados].map(([clave, detalle]) => `${clave}: ${detalle.join(' | ')}`), 'fallos').toEqual([])
      })
    }
  })
}

test('el recorrido cubre todas las rutas de App.tsx', () => {
  const app = readFileSync(path.resolve('src/App.tsx'), 'utf-8')
  // Solo las pantallas: una ruta que envuelve a otras (`portal` con su PortalLayout) no cierra en `/>`,
  // y una que solo redirige (`<Navigate>`) no pinta nada que medir.
  const pantalla = (m: RegExpMatchArray) => !m[0].includes('<Navigate')
  const rutas = [...app.matchAll(/<Route\s+path="([^"]+)"\s+element=\{<[^>]*\/>\}\s*\/>/g)]
    .filter(pantalla)
    .map((m) => m[1])
    .filter((p) => p !== '*')
  const indices = [...app.matchAll(/<Route\s+index\s+element=\{<[^>]*\/>\}\s*\/>/g)].filter(pantalla).length
  // Una pantalla puede medirse con varios perfiles (el Inicio, Aliadas, Rutas): cada uno ve otra.
  const declaradas = [...new Set(RUTAS.map((r) => r.app))]
  expect(declaradas.filter((r) => !r.startsWith('index:')).sort()).toEqual(rutas.sort())
  expect(declaradas.filter((r) => r.startsWith('index:'))).toHaveLength(indices)
  const pares = RUTAS.map((r) => `${r.perfil} ${r.app}`)
  expect(new Set(pares).size, 'cada ruta aparece una sola vez por perfil').toBe(pares.length)
})
