import { readdirSync, readFileSync } from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

/**
 * Guarda de los tokens de diseño (docs/manual-de-marca.md, sección 15).
 *
 * Todo color sale de `src/styles/tokens.css`. Fuera de ese fichero no se escribe ningún
 * color a mano: ni en las hojas de estilo, ni en un `style={{}}`, ni en un atributo `fill`.
 * Y toda variable que se usa con `var(--…)` tiene que estar definida: una errata o un token
 * inventado no rompe la compilación, solo deja el elemento sin color.
 *
 * Los ejemplos de esta prueba escriben colores a propósito, así que ella misma no se revisa.
 */

const SRC = path.resolve(__dirname, '..')
const TOKENS = path.join('styles', 'tokens.css')
const ESTA_PRUEBA = path.join('test', 'tokens.test.ts')

const HEX = /#(?:[0-9a-f]{8}|[0-9a-f]{6}|[0-9a-f]{3,4})\b/i
const FUNCION_CSS = /\b(?:rgba?|hsla?|hwb|lab|lch|oklab|oklch|color)\(/i
const FUNCION_TS = /\b(?:rgba?|hsla?|hwb|lab|lch|oklab|oklch)\(/i
const NOMBRES = new Set(
  (
    'aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue ' +
    'blueviolet brown burlywood cadetblue chartreuse chocolate coral cornflowerblue cornsilk ' +
    'crimson cyan darkblue darkcyan darkgoldenrod darkgray darkgreen darkgrey darkkhaki ' +
    'darkmagenta darkolivegreen darkorange darkorchid darkred darksalmon darkseagreen ' +
    'darkslateblue darkslategray darkslategrey darkturquoise darkviolet deeppink deepskyblue ' +
    'dimgray dimgrey dodgerblue firebrick floralwhite forestgreen fuchsia gainsboro ghostwhite ' +
    'gold goldenrod gray green greenyellow grey honeydew hotpink indianred indigo ivory khaki ' +
    'lavender lavenderblush lawngreen lemonchiffon lightblue lightcoral lightcyan ' +
    'lightgoldenrodyellow lightgray lightgreen lightgrey lightpink lightsalmon lightseagreen ' +
    'lightskyblue lightslategray lightslategrey lightsteelblue lightyellow lime limegreen linen ' +
    'magenta maroon mediumaquamarine mediumblue mediumorchid mediumpurple mediumseagreen ' +
    'mediumslateblue mediumspringgreen mediumturquoise mediumvioletred midnightblue mintcream ' +
    'mistyrose moccasin navajowhite navy oldlace olive olivedrab orange orangered orchid ' +
    'palegoldenrod palegreen paleturquoise palevioletred papayawhip peachpuff peru pink plum ' +
    'powderblue purple rebeccapurple red rosybrown royalblue saddlebrown salmon sandybrown ' +
    'seagreen seashell sienna silver skyblue slateblue slategray slategrey snow springgreen ' +
    'steelblue tan teal thistle tomato turquoise violet wheat white whitesmoke yellow yellowgreen'
  ).split(' '),
)
/** Propiedades cuyo valor puede contener palabras que coinciden con un nombre de color. */
const SIN_NOMBRES_DE_COLOR = /^(?:font-family|font|content|grid-template-areas|grid-area|animation(?:-name)?|transition(?:-property)?|will-change)$/
/** Propiedades de estilo y atributos SVG que llevan un color en TypeScript. */
const PROPIEDAD_COLOR_TS =
  /\b(?:color|background(?:Color)?|border(?:Top|Right|Bottom|Left)?Color|outlineColor|caretColor|accentColor|fill|stroke|stopColor|floodColor|lightingColor)\s*[:=]\s*\{?\s*(['"`])([a-z]+)\1/gi
const PALABRAS_CSS = /\b(?:solid|dashed|dotted|gradient|inset|px|rem|em)\b/

function ficheros(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    const ruta = path.join(dir, e.name)
    if (e.isDirectory()) return ficheros(ruta)
    return /\.(?:css|tsx?)$/.test(e.name) ? [ruta] : []
  })
}

function nombreDeColor(valor: string): string | undefined {
  return valor
    .toLowerCase()
    .split(/[^a-z]+/)
    .find((palabra) => NOMBRES.has(palabra))
}

/** Colores escritos a mano en una hoja de estilo: `línea: declaración`. */
function coloresEnCss(css: string): string[] {
  const sinComentarios = css.replace(/\/\*[\s\S]*?\*\//g, (c) => c.replace(/[^\n]/g, ' '))
  const hallazgos: string[] = []
  // Solo el interior de los bloques más internos: así un selector (`:is(.red)`) nunca se
  // lee como valor.
  for (const bloque of sinComentarios.matchAll(/\{([^{}]*)\}/g)) {
    const inicio = bloque.index! + 1
    let desplazamiento = 0
    for (const declaracion of bloque[1].split(';')) {
      const separador = declaracion.indexOf(':')
      if (separador > 0) {
        const propiedad = declaracion.slice(0, separador).trim().toLowerCase()
        const valor = declaracion.slice(separador + 1)
        const nombre = SIN_NOMBRES_DE_COLOR.test(propiedad) ? undefined : nombreDeColor(valor)
        if (HEX.test(valor) || FUNCION_CSS.test(valor) || nombre) {
          const linea = sinComentarios.slice(0, inicio + desplazamiento).split('\n').length +
            (declaracion.match(/^\s*/)?.[0].split('\n').length ?? 1) - 1
          hallazgos.push(`${linea}: ${declaracion.trim()}`)
        }
      }
      desplazamiento += declaracion.length + 1
    }
  }
  return hallazgos
}

/** Colores escritos a mano en TypeScript: cadenas que son un color y estilos con un nombre de color. */
function coloresEnTs(codigo: string): string[] {
  const hallazgos: string[] = []
  for (const [literal, , contenido] of codigo.matchAll(/(['"`])((?:(?!\1)[^\\\n]|\\.)*)\1/g)) {
    const valor = contenido.trim()
    const hexEntero = new RegExp(`^${HEX.source}$`, 'i').test(valor)
    const hexEnEstilo = HEX.test(valor) && PALABRAS_CSS.test(valor)
    if (hexEntero || hexEnEstilo || FUNCION_TS.test(valor)) hallazgos.push(literal)
  }
  for (const [declaracion, , valor] of codigo.matchAll(PROPIEDAD_COLOR_TS)) {
    if (NOMBRES.has(valor.toLowerCase())) hallazgos.push(declaracion)
  }
  return hallazgos
}

const DEFINICION_CSS = /(?:^|[\s;{])(--[a-z0-9-]+)\s*:/gi
const DEFINICION_TS = /['"](--[a-z0-9-]+)['"]\s*:/gi
const USO = /var\(\s*(--[a-z0-9-]+)/gi

const fuentes = ficheros(SRC)
  .map((absoluto) => ({ fichero: path.relative(SRC, absoluto), texto: readFileSync(absoluto, 'utf-8') }))
  .filter(({ fichero }) => fichero !== ESTA_PRUEBA)

const definidas = new Set(
  fuentes.flatMap(({ fichero, texto }) =>
    [...texto.matchAll(fichero.endsWith('.css') ? DEFINICION_CSS : DEFINICION_TS)].map((m) => m[1]),
  ),
)

describe('guarda de tokens: comprobaciones de la propia guarda', () => {
  it('detecta un color escrito a mano en una hoja de estilo', () => {
    const css = `
      .a { color: #fff; }
      @media (min-width: 900px) { .b { background: rgb(0 0 0 / 45%); } }
      .c:hover { border: 1px solid white; }
      .d { --propio: oklch(70% 0.1 120); }`
    expect(coloresEnCss(css)).toEqual([
      '2: color: #fff',
      '3: background: rgb(0 0 0 / 45%)',
      '4: border: 1px solid white',
      '5: --propio: oklch(70% 0.1 120)',
    ])
  })

  it('no confunde selectores, fuentes ni comentarios con colores', () => {
    const css = `
      /* antes era #fff */
      .is-red:is(.tan) { color: var(--texto); font-family: "Nunito Sans", system-ui; }
      .e { transition: color .2s, background-color .2s; }`
    expect(coloresEnCss(css)).toEqual([])
  })

  it('detecta colores en estilos y atributos de TypeScript', () => {
    const tsx = `
      <div style={{ color: '#111537', boxShadow: '0 1px 2px rgba(0, 0, 0, .1)' }} />
      <path fill="white" />
      <span style={{ background: 'red' }} />
      const borde = '1px solid #ccc'`
    expect(coloresEnTs(tsx)).toEqual([
      "'#111537'",
      "'0 1px 2px rgba(0, 0, 0, .1)'",
      "'1px solid #ccc'",
      'fill="white"',
      "background: 'red'",
    ])
  })

  it('no confunde una dirección ni un token con un color', () => {
    const tsx = `
      const direccion = 'Calle 35 #66a 51, Laureles'
      <div style={{ color: 'var(--texto)', gap: 'var(--e2)' }} className="red" />`
    expect(coloresEnTs(tsx)).toEqual([])
  })

  it('encuentra las variables definidas en tokens.css', () => {
    expect(definidas.size).toBeGreaterThan(20)
  })
})

describe('guarda de tokens', () => {
  it('fuera de tokens.css no se escribe ningún color a mano', () => {
    const hallazgos = fuentes
      .filter(({ fichero }) => fichero !== TOKENS)
      .flatMap(({ fichero, texto }) =>
        (fichero.endsWith('.css') ? coloresEnCss(texto) : coloresEnTs(texto)).map((h) => `${fichero}:${h}`),
      )
    expect(hallazgos, 'usa un rol de src/styles/tokens.css (docs/manual-de-marca.md, sección 10)').toEqual([])
  })

  it('toda variable que se usa está definida', () => {
    const sinDefinir = fuentes.flatMap(({ fichero, texto }) =>
      [...texto.matchAll(USO)].map((m) => m[1]).filter((v) => !definidas.has(v)).map((v) => `${fichero}: ${v}`),
    )
    expect(sinDefinir, 'define la variable en tokens.css o corrige el nombre').toEqual([])
  })
})
