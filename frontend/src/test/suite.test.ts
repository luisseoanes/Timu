import { readdirSync, readFileSync } from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

/**
 * Guarda de la suite: que el CI ejecute todas las pruebas que existen.
 *
 * Vitest solo recoge `src/**\/*.{test,spec}.{ts,tsx}` (vitest.config.ts) y Playwright
 * solo `e2e/` (playwright.config.ts) y `e2e-stack/` (playwright.stack.config.ts). Una
 * prueba escrita fuera de esos patrones no la corre nadie, y una desactivada deja de
 * comprobar algo sin que el CI se ponga rojo.
 * Ninguno de los dos casos hace fallar a los runners: por eso existe esta prueba.
 */

const RAIZ = path.resolve(__dirname, '../..')
const IGNORADOS = new Set(['node_modules', 'dist', 'coverage', 'playwright-report', 'playwright-report-stack', 'test-results'])
const ESTE_FICHERO = path.relative(RAIZ, __filename)

const PATRONES: Record<string, RegExp> = {
  src: /\.(test|spec)\.tsx?$/,
  e2e: /\.(test|spec)\.[cm]?[jt]sx?$/,
  // Recorridos contra el stack real: los corre el job «Stack con un solo comando».
  'e2e-stack': /\.(test|spec)\.[cm]?[jt]sx?$/,
}

// `it('…'`, `test('…'`, `describe('…'`, `test.describe('…'`; no `regex.test(valor)`.
const DEFINE_PRUEBAS = /(?<![.\w])(?:it|test|describe)(?:\.describe)?\s*\(\s*['"`]/
const DESACTIVADA =
  /(?<![.\w])(?:(?:it|test|describe)(?:\.describe)?\.(?:only|skip|todo|fixme)\w*|x(?:it|test|describe)|f(?:it|describe))\s*\(/

function codigo(dir: string): string[] {
  return readdirSync(path.join(RAIZ, dir), { withFileTypes: true }).flatMap((e) => {
    const relativo = path.join(dir, e.name)
    if (e.isDirectory()) return IGNORADOS.has(e.name) ? [] : codigo(relativo)
    return /\.[cm]?[jt]sx?$/.test(e.name) ? [relativo] : []
  })
}

const ficheros = codigo('.')
  .map((f) => path.normalize(f))
  .filter((f) => f !== ESTE_FICHERO)
  .map((f) => ({ ruta: f, texto: readFileSync(path.join(RAIZ, f), 'utf-8') }))

describe('suite de pruebas', () => {
  it('encuentra las pruebas del panel', () => {
    expect(ficheros.filter((f) => PATRONES.src.test(f.ruta)).length).toBeGreaterThan(0)
  })

  it('toda prueba vive donde un runner la recoge', () => {
    const huerfanas = ficheros
      .filter((f) => DEFINE_PRUEBAS.test(f.texto))
      .filter((f) => {
        const [carpeta] = f.ruta.split(path.sep)
        const patron = PATRONES[carpeta]
        return !patron || !patron.test(f.ruta)
      })
      .map((f) => f.ruta)
    expect(huerfanas, 'pruebas que ni Vitest ni Playwright ejecutan').toEqual([])
  })

  it('ninguna prueba está desactivada ni aislada', () => {
    const desactivadas = ficheros
      .flatMap((f) =>
        f.texto.split('\n').flatMap((linea, i) => (DESACTIVADA.test(linea) ? [`${f.ruta}:${i + 1}`] : [])),
      )
    expect(desactivadas, 'usa .only/.skip/.todo/.fixme: arréglala o bórrala').toEqual([])
  })
})
