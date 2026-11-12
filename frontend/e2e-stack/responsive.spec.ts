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
 * de `scripts.datos_demo`, y la mide a 375, 768 y 1280 px. Falla si el documento desborda en
 * horizontal (una tabla dentro de su propio contenedor con desplazamiento sí se permite) o si
 * axe-core encuentra texto con contraste insuficiente (WCAG 2.2 AA, 1.4.3).
 *
 * Una ruta con `pestanas` se mide también con cada una de sus pestañas abierta: su contenido
 * no está en el DOM hasta que se elige. La clave de un fallo lleva entonces la pestaña
 * (`familias/:id#Cartera@375:desborde`). Cada pantalla rediseñada la activa al cerrarse.
 *
 * Una medida solo vale si la pantalla cargó sus datos. Con un 429 (el límite de la API es por
 * usuario, y el barrido hace muchas peticiones con el mismo) o un 5xx, la pantalla pinta un
 * error, que no desborda: daría por arreglado lo que no lo está. Ante un 429 se espera lo que
 * dice Retry-After y se vuelve a cargar; si el error sigue, la prueba falla.
 *
 * PENDIENTES es la deuda del rediseño: cada entrada es un fallo medido en una ruta y un ancho.
 * La prueba falla si aparece un fallo que no está en la lista y también si una entrada ya no
 * falla, así que la lista solo puede encogerse. Debe quedar vacía en R4-CIE-01.
 */

const ANCHOS = [375, 768, 1280] as const
const ALTO = 900

type Fallo = 'desborde' | 'contraste'

// Medido el 2026-11-10. Con la paleta de la marca (R1-TOK-01) ya no queda ningún fallo de
// contraste; quedan los desbordes del responsive anterior al rediseño.
const PENDIENTES: ReadonlySet<string> = new Set([
  'aliadas@375:desborde',
  'campanas@375:desborde',
  'preventivos@375:desborde',
  'tareas@375:desborde',
])

interface Ruta {
  /** La ruta tal como la declara App.tsx: el `path` o `index` dentro de su espacio. */
  app: string
  /** Perfil con el que se abre; null para las páginas públicas. */
  perfil: Perfil | null
  /** Dirección que se abre. Las rutas con parámetros piden a la API un registro real. */
  url: string | ((page: Page) => Promise<string>)
  /** Mide también cada pestaña de la pantalla (ver arriba). */
  pestanas?: boolean
}

const SIN_REGISTRO = '00000000-0000-7000-8000-000000000000'

async function pedir<T>(page: Page, url: string): Promise<T> {
  const respuesta = await page.request.get(`/api/v1${url}`)
  expect(respuesta.ok(), `GET ${url} respondió ${respuesta.status()}`).toBeTruthy()
  return (await respuesta.json()) as T
}

interface Familia { id: string; mascotas?: { id: string }[] }

async function familiaDemo(page: Page): Promise<Familia> {
  const { items } = await pedir<{ items: Familia[] }>(page, '/familias?q=Ana%20Ruiz')
  expect(items.length, 'datos_demo crea la familia Ana Ruiz').toBeGreaterThan(0)
  return items[0]
}

/** Una entrada de historia clínica y su mascota, de cualquier familia de datos_demo. */
async function entradaClinica(page: Page): Promise<{ mascota: string; entrada: string }> {
  const { items } = await pedir<{ items: Familia[] }>(page, '/familias?limit=50')
  for (const familia of items) {
    for (const { id } of familia.mascotas ?? []) {
      const historia = await pedir<{ id: string }[]>(page, `/clinica/mascotas/${id}/historia`)
      if (historia.length > 0) return { mascota: id, entrada: historia[0].id }
    }
  }
  throw new Error('datos_demo no dejó ninguna entrada de historia clínica')
}

const RUTAS: Ruta[] = [
  // Páginas públicas. Las que necesitan un enlace válido se abren con uno inexistente: se
  // mide el estado de «enlace no válido», que es lo que ve quien llega con uno vencido.
  { app: '/login', perfil: null, url: '/login' },
  { app: '/recuperar', perfil: null, url: '/recuperar' },
  { app: '/restablecer', perfil: null, url: '/restablecer' },
  { app: '/activar', perfil: null, url: '/activar' },
  { app: '/encuesta/:token', perfil: null, url: '/encuesta/enlace-inexistente' },
  { app: '/verificar/:codigo', perfil: null, url: '/verificar/CODIGO-INEXISTENTE' },
  { app: '/afiliacion', perfil: null, url: '/afiliacion' },
  { app: '/afiliacion/resultado', perfil: null, url: '/afiliacion/resultado' },
  { app: '/afiliacion/completar', perfil: null, url: '/afiliacion/completar' },

  // Panel del equipo.
  { app: 'index:panel', perfil: 'equipo', url: '/' },
  { app: 'familias', perfil: 'equipo', url: '/familias' },
  {
    app: 'familias/:id',
    perfil: 'equipo',
    url: async (page) => `/familias/${(await familiaDemo(page)).id}`,
    pestanas: true,
  },
  { app: 'cartera', perfil: 'equipo', url: '/cartera' },
  { app: 'servicios', perfil: 'equipo', url: '/servicios' },
  {
    app: 'servicios/:id',
    perfil: 'medico',
    url: async (page) => {
      const { items } = await pedir<{ items: { id: string }[] }>(page, '/servicios?limit=1')
      expect(items.length, 'datos_demo crea servicios').toBeGreaterThan(0)
      return `/servicios/${items[0].id}`
    },
  },
  { app: 'tareas', perfil: 'equipo', url: '/tareas' },
  { app: 'preventivos', perfil: 'equipo', url: '/preventivos' },
  { app: 'clinica', perfil: 'medico', url: '/clinica' },
  { app: 'clinica/mascotas/:mascotaId', perfil: 'medico', url: async (page) => `/clinica/mascotas/${(await entradaClinica(page)).mascota}` },
  { app: 'clinica/historias/:id', perfil: 'medico', url: async (page) => `/clinica/historias/${(await entradaClinica(page)).entrada}` },
  {
    // La ruta de la médica, en el día en que datos_demo la dejó: sin ella se mediría el vacío.
    app: 'rutas',
    perfil: 'medico',
    url: async (page) => {
      const yo = await pedir<{ id: string }>(page, '/auth/me')
      return (await rutaDemo(page.request, yo.id)).url
    },
  },
  { app: 'campanas', perfil: 'equipo', url: '/campanas' },
  { app: 'aliadas', perfil: 'equipo', url: '/aliadas' },
  { app: 'comercial', perfil: 'equipo', url: '/comercial' },
  { app: 'admin', perfil: 'admin', url: '/admin' },

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
  },
  { app: 'citas', perfil: 'familia', url: '/portal/citas' },
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

for (const perfil of [null, 'equipo', 'medico', 'admin', 'familia', 'aliada'] as const) {
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
          const vista = pestana ? `${ruta.app}#${pestana}` : ruta.app
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

        const nuevos = [...encontrados].filter(([clave]) => !PENDIENTES.has(clave))
        const resueltos = [...PENDIENTES].filter(
          (p) => (p.startsWith(`${ruta.app}@`) || p.startsWith(`${ruta.app}#`)) && !encontrados.has(p),
        )
        expect(nuevos.map(([clave, detalle]) => `${clave}: ${detalle.join(' | ')}`), 'fallos nuevos').toEqual([])
        expect(resueltos, 'ya no fallan: sácalas de PENDIENTES').toEqual([])
      })
    }
  })
}

test('el recorrido cubre todas las rutas de App.tsx', () => {
  const app = readFileSync(path.resolve('src/App.tsx'), 'utf-8')
  // Solo las pantallas: una ruta que envuelve a otras (`portal` con su PortalLayout) no cierra en `/>`.
  const rutas = [...app.matchAll(/<Route\s+path="([^"]+)"\s+element=\{[^}]*\}\s*\/>/g)]
    .map((m) => m[1])
    .filter((p) => p !== '*')
  const indices = (app.match(/<Route\s+index\s+element=\{[^}]*\}\s*\/>/g) ?? []).length
  const declaradas = RUTAS.map((r) => r.app)
  expect(declaradas.filter((r) => !r.startsWith('index:')).sort()).toEqual(rutas.sort())
  expect(declaradas.filter((r) => r.startsWith('index:'))).toHaveLength(indices)
  expect(new Set(declaradas).size, 'cada ruta aparece una sola vez').toBe(declaradas.length)
})

test('PENDIENTES solo nombra rutas, anchos y fallos que existen', () => {
  const invalidas = [...PENDIENTES].filter((p) => {
    const [, app, pestana, ancho] = /^(.+?)(?:#([^@]+))?@(\d+):(?:desborde|contraste)$/.exec(p) ?? []
    const ruta = RUTAS.find((r) => r.app === app)
    return !ruta || (pestana !== undefined && !ruta.pestanas) || !(ANCHOS as readonly number[]).includes(Number(ancho))
  })
  expect(invalidas).toEqual([])
})
