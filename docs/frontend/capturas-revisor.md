# Capturas para el revisor final

Cada superficie del rediseño se cierra con el agente `impeccable-finish-reviewer`, que no tiene
navegador: juzga solo por las capturas que se le pasan. **Una captura inválida le cuesta una
ronda entera**, porque responde `recapture` y no puntúa nada hasta tenerla. Este documento junta
lo aprendido al cerrar Familias, Rutas, Clínica, el portal, el Inicio y Servicios (2026-11-10 a
2026-11-14). El orden de las unidades está en la [hoja de ruta](../hoja-de-ruta-rediseno.md).

## Qué se captura

- **Una carpeta por superficie**: `.impeccable/review/<superficie>/` (ignorada por git), con el
  nombre `perfil-estado-ancho.png` (`operaciones-abierto-1440.png`). Las de Familias están
  sueltas en `.impeccable/review/`.
- **Los cuatro anchos**: 1440, 1180, 900 y 390 px (alto 900, o 844 a 390), con cada perfil que
  usa la pantalla. El barrido responsive solo mide 375, 768 y 1280: los 900 de cada superficie
  se comprueban aquí.
- **Cada estado que importa**, no solo el reposo: la ficha abierta, cada pestaña, la ventana
  abierta, el error. Al pasárselas al revisor, se le dice cuáles son obligatorias.
- **Página completa para leer la composición; solo el viewport para probar posición.** Una
  afirmación del tipo «la ficha queda a la vista al abrir la última fila» no la acepta con una
  captura de página completa: hace falta la del viewport, tomada tras la acción.

## Cómo se toman sin que salgan mal

- **Esperar a un elemento de la pantalla (su título), no solo a la red.** La espera de sesión no
  se distingue por texto (el lema va dentro del SVG del logo) y una captura tomada antes enseña
  el esqueleto.
- **Volver arriba antes de una de página completa** (`window.scrollTo(0, 0)`): si la página quedó
  desplazada, la barra fija sale pintada a media página. A 390 la barra inferior sale pintada a
  844 px de alto; es un artefacto conocido de la página completa y se le avisa al revisor.
- **Abrir y validar cada fichero antes de mandarlo**: que no esté en blanco, que enseñe lo que
  dice su nombre y que no se haya quedado a medio cargar.

## Sesiones y cupos

- **El ingreso por script es un formulario**: `request.post('/api/v1/auth/login', { form: {
  username, password } })`. Con `data` (JSON) responde 422.
- **Una sesión por perfil, guardada en un fichero** y reutilizada en vez de ingresar en cada
  script: el ingreso y la renovación admiten 10 por minuto por IP.
- **Tras cada contexto del navegador se vuelve a guardar su `storageState`**: la renovación rota
  el token, y si el siguiente contexto carga uno ya rotado, el backend lo trata como robo y
  cierra todas las sesiones del usuario.
- **Con una sesión guardada hace más de 30 minutos, el token de acceso ha vencido**: antes de
  pedir nada con `page.request`, carga una pantalla y espera a `networkidle` para que se renueve.
  (En el e2e no pasa: las sesiones son recién creadas.)
- **Lotes por usuario con un minuto entre lotes**: la API admite 120 peticiones por minuto por
  usuario, y una carga del panel gasta de 8 a 12. No captures con `comercial@timu.co` justo
  antes del e2e contra el stack, que lo deja sin cupo (429).

## Estados que los datos no tienen

- **Los que gastan datos** (una parada que se cierra, una consulta que se firma) se capturan en el
  orden en que los datos lo permiten: primero lo que exige el estado anterior.
- **Los que `datos_demo` no tiene** (una familia al día, citas en camino, un pago rechazado) se
  simulan interceptando la API con `page.route` en el script, y se le dice al revisor qué capturas
  son simuladas. La respuesta simulada tiene que ser realista: un 503 sin cuerpo, no uno con un
  `detail` inventado, que el revisor toma por texto del servidor.
- **Los que dependen de la hora** (un servicio de hoy que aún no llega, de noche) se capturan con
  el reloj del navegador fijado: ``page.clock.setFixedTime(new Date(`${hoy}T13:00:00Z`))`` antes
  de `page.goto`. Los datos siguen siendo los reales.
- **Si `datos_demo` se sembró otro día**, la ruta de la médica no aparece: vuelve a correr
  `docker compose exec -T api python -m scripts.datos_demo`.

## El script

Vive en el scratchpad y se copia a `frontend/` solo para ejecutarlo (`eslint .` lo recogería y
`verificar` fallaría); se borra al terminar. Como `/tmp` se vacía al reiniciar, este es el
esqueleto que se usó para Servicios:

```js
// Uso: SESIONES=<carpeta con sesiones/> node _capturar.mjs <salida> [lote...]
import { mkdirSync } from 'node:fs'
import { join } from 'node:path'

import { chromium } from '@playwright/test'

const [OUT, ...ELEGIDOS] = process.argv.slice(2)
const BASE = 'http://localhost:5173'
const ALTOS = { 1440: 900, 1180: 900, 900: 900, 390: 844 }
mkdirSync(OUT, { recursive: true })

// [perfil, estado, ancho, url, opciones]: un lote por usuario y tanda.
const LOTES = {
  listado: [1440, 1180, 900, 390].map((a) => ['operaciones', 'listado', a, '/servicios']),
  medico: [['medico', 'ficha', 390, '/servicios/:id?origen=ruta']],
}

const navegador = await chromium.launch()
for (const [n, lote] of (ELEGIDOS.length ? ELEGIDOS : Object.keys(LOTES)).entries()) {
  if (n) await new Promise((r) => setTimeout(r, 65000)) // un minuto entre lotes: el cupo de la API
  for (const [perfil, estado, ancho, url, op = {}] of LOTES[lote]) {
    const sesion = join(process.env.SESIONES, 'sesiones', `${perfil}.json`)
    const ctx = await navegador.newContext({ storageState: sesion, viewport: { width: ancho, height: ALTOS[ancho] } })
    const page = await ctx.newPage()
    if (op.reloj) await page.clock.setFixedTime(new Date(op.reloj))
    await page.goto(BASE + url)
    await page.waitForSelector('.contenido h1', { timeout: 20000 }) // un elemento, no solo la red
    await page.waitForLoadState('networkidle')
    await page.evaluate(() => window.scrollTo(0, 0))
    await page.screenshot({ path: join(OUT, `${perfil}-${estado}-${ancho}.png`), fullPage: !op.soloViewport })
    await ctx.storageState({ path: sesion }) // la renovación rotó el token
    await ctx.close()
  }
}
await navegador.close()
```

Las sesiones se crean una vez con el ingreso por formulario de arriba (`request.newContext` y
`ctx.storageState({ path })`), y un id real (`:id`) se pide a la API con `page.request` después de
cargar una pantalla.

## Lo que se le pasa al revisor

La petición original, las respuestas que dio el usuario, el contrato de la superficie
(`.impeccable/surfaces/`), los ficheros del artefacto, la lista de capturas con lo que enseña cada
una (y cuáles son simuladas), los hallazgos del hook y la ruta de
`.claude/skills/impeccable/reference/craft-floor.md`. Sin comp aprobado (construcción en código),
la referencia de crítica es el boceto elegido en el sorteo o, si no hubo sorteo, las superficies
ya cerradas del mismo mundo. Tras un `fix`, los arreglos se recapturan sobre los mismos ficheros y
se le piden puntuados (resolved, partial o unresolved) al mismo revisor.

## La skill

- `impeccable concept-seed --help` no imprime la ayuda: ejecuta una tirada sin modo. La forma del
  payload de la página de decisión la da `serve-question --schema`.
- `serve-question --wait --key <k>` sale con 3 cada 60 s sin respuesta: se repite en bucle en
  segundo plano hasta que salga 0.
