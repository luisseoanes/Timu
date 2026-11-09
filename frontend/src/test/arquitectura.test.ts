import { readdirSync, readFileSync } from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

/**
 * Guarda de la arquitectura del panel (Secciones 3 y 4 del documento de requerimientos).
 *
 * Un dominio es una carpeta de `src/features/`. Lo que otros pueden usar de él lo exporta su
 * `index.ts`; el resto es interno. Capas, de abajo arriba:
 *
 * - Base: `src/api`, `src/components`, `src/lib`, `src/types`, `src/styles`. No conocen
 *   ningún dominio.
 * - Dominios base: `auth` (sesión, equipo) y `catalogos`. Los usan todos; ellos no usan a nadie.
 * - Dominios: usan la base, los dominios base y la superficie pública de otros, sin ciclos.
 * - Espacios de entrada: `admin`, `portal` y `publico`. Solo los monta `App.tsx`.
 * - Composición: `App.tsx`, `main.tsx`, `layouts/`, `routes/` y `test/`.
 *
 * ESLint rechaza `@/features/<dominio>/<fichero>`; esta prueba cubre lo que un patrón de
 * import no ve: rutas relativas que cruzan dominios, capas y ciclos.
 */

const SRC = path.resolve(__dirname, '..')
const BASE = ['api', 'components', 'lib', 'types', 'styles']
const DOMINIOS_BASE = ['auth', 'catalogos']
const ESPACIOS = ['admin', 'portal', 'publico']
const IMPORT = /(?:import|export)\s[^'"]*?from\s+['"]([^'"]+)['"]/g

interface Dependencia {
  fichero: string
  destino: string
  /** Dominio al que apunta, si apunta a uno. */
  dominio: string | null
}

function ficheros(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    const ruta = path.join(dir, e.name)
    if (e.isDirectory()) return ficheros(ruta)
    return /\.tsx?$/.test(e.name) ? [ruta] : []
  })
}

/** 'features/familias/api.ts' -> 'familias'. */
function dominioDe(relativo: string): string | null {
  const [carpeta, dominio] = relativo.split(path.sep)
  return carpeta === 'features' ? dominio : null
}

function resolver(fichero: string, destino: string): string | null {
  if (destino.startsWith('@/')) return destino.slice(2).split('/').join(path.sep)
  if (destino.startsWith('.')) return path.relative(SRC, path.resolve(path.dirname(fichero), destino))
  return null // paquete de npm
}

const dependencias: Dependencia[] = ficheros(SRC).flatMap((absoluto) => {
  const fichero = path.relative(SRC, absoluto)
  return [...readFileSync(absoluto, 'utf-8').matchAll(IMPORT)].flatMap(([, destino]) => {
    const resuelto = resolver(absoluto, destino)
    return resuelto === null ? [] : [{ fichero, destino, dominio: dominioDe(resuelto) }]
  })
})

const cruzadas = dependencias.filter(
  (d) => d.dominio !== null && d.dominio !== dominioDe(d.fichero),
)
const enCarpeta = (d: Dependencia, carpetas: string[]) =>
  carpetas.includes(d.fichero.split(path.sep)[0])
const deDominio = (d: Dependencia, dominios: string[]) =>
  dominios.includes(dominioDe(d.fichero) ?? '')
const describir = (ds: Dependencia[]) => ds.map((d) => `${d.fichero} -> ${d.destino}`)

describe('arquitectura del panel', () => {
  it('encuentra imports entre dominios', () => {
    expect(cruzadas.length).toBeGreaterThan(0)
  })

  it('entre dominios solo se importa la superficie pública', () => {
    const internas = cruzadas.filter((d) => !/^@\/features\/[a-z]+$/.test(d.destino))
    expect(describir(internas), 'usa @/features/<dominio> y exporta la pieza en su index.ts').toEqual([])
  })

  it('el index.ts de un dominio solo exporta piezas propias', () => {
    const ajenas = dependencias.filter((d) => d.fichero.endsWith(`${path.sep}index.ts`) && !d.destino.startsWith('./'))
    expect(describir(ajenas)).toEqual([])
  })

  it('la base no conoce ningún dominio', () => {
    expect(describir(cruzadas.filter((d) => enCarpeta(d, BASE))), 'una pieza de la base no puede depender de un dominio').toEqual([])
  })

  it('auth y catalogos no dependen de otro dominio', () => {
    expect(describir(cruzadas.filter((d) => deDominio(d, DOMINIOS_BASE)))).toEqual([])
  })

  it('los espacios de entrada solo los monta App.tsx', () => {
    const indebidas = cruzadas.filter((d) => ESPACIOS.includes(d.dominio!) && d.fichero !== 'App.tsx')
    expect(describir(indebidas)).toEqual([])
  })

  it('no hay ciclos entre dominios', () => {
    const grafo = new Map<string, Set<string>>()
    for (const d of cruzadas) {
      const origen = dominioDe(d.fichero)
      if (origen) grafo.set(origen, (grafo.get(origen) ?? new Set()).add(d.dominio!))
    }
    const ciclos: string[] = []
    const visitar = (nodo: string, camino: string[]) => {
      const i = camino.indexOf(nodo)
      if (i >= 0) return void ciclos.push([...camino.slice(i), nodo].join(' -> '))
      for (const siguiente of grafo.get(nodo) ?? []) visitar(siguiente, [...camino, nodo])
    }
    for (const nodo of grafo.keys()) visitar(nodo, [])
    expect([...new Set(ciclos)], 'invierte la dependencia o sube la pieza compartida a la base').toEqual([])
  })
})
