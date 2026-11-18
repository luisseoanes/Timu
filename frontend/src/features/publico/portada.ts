import { useQuery } from '@tanstack/react-query'

import { api } from '@/api/client'
import type { AliadaPublica, DatosTimuRead, PlanPublico } from '@/types'

/** Lo que dice de TIMU la portada (R3-PUB-04): lo escribe Administración → Datos de TIMU. */
export function useDatosTimu() {
  return useQuery({
    queryKey: ['portada', 'institucional'],
    staleTime: 5 * 60_000,
    queryFn: async () => (await api.get<DatosTimuRead>('/institucional')).data,
  })
}

/** Las aliadas que Administración pone en la portada, en su orden de la red. */
export function useAliadasPublicas() {
  return useQuery({
    queryKey: ['portada', 'aliadas'],
    staleTime: 5 * 60_000,
    queryFn: async () => (await api.get<AliadaPublica[]>('/aliadas/publicas')).data,
  })
}

/** La dirección de un plan: `/planes/colita-feliz` para `colita_feliz`. */
export const rutaDePlan = (plan: Pick<PlanPublico, 'codigo'>) => `/planes/${plan.codigo.replace(/_/g, '-')}`
export const codigoDeRuta = (ruta: string) => ruta.replace(/-/g, '_')

/** La afiliación con lo que ya eligió en la portada: el registro arranca con eso. */
export function enlaceAfiliacion({ ciudad, perros = 0, gatos = 0, plan }: { ciudad?: string; perros?: number; gatos?: number; plan?: string }) {
  const p = new URLSearchParams()
  if (ciudad) p.set('ciudad', ciudad)
  if (perros) p.set('perros', String(perros))
  if (gatos) p.set('gatos', String(gatos))
  if (plan) p.set('plan', plan)
  const q = p.toString()
  return q ? `/afiliacion?${q}` : '/afiliacion'
}

/** Una estación de la red: un barrio (o un municipio sin barrio) con sus aliadas. */
export interface Estacion {
  clave: string
  nombre: string
  /** El municipio, cuando la estación es un barrio. */
  ciudad: string | null
  aliadas: AliadaPublica[]
  /** Aquí está la clínica de TIMU: la estación de intercambio. */
  clinicaTimu: boolean
}

/** Lo que no tiene sede abierta al público: va a la familia o atiende por remisión. */
const SIN_SEDE = new Set(['especialista', 'farmacia', 'funeraria'])

const normal = (s: string) =>
  s
    .normalize('NFD')
    .replace(/\p{M}/gu, '')
    .toLowerCase()
    .trim()

/**
 * La red TIMU como una línea (R3-PUB-04): las aliadas con sede son estaciones, en el orden que
 * fija Administración, y las seguidas del mismo barrio comparten estación. Un municipio sin barrios
 * en la red es una estación; en uno que ya los tiene, una aliada sin barrio no inventa la estación
 * del municipio entre los barrios y va con los servicios. La clínica de TIMU es la estación de
 * intercambio: la de su barrio, o una propia al principio si ninguna aliada está allí.
 */
export function redTimu(aliadas: AliadaPublica[], datos?: Pick<DatosTimuRead, 'clinica_barrio' | 'clinica_ciudad'> | null) {
  const estaciones: Estacion[] = []
  const servicios: AliadaPublica[] = []
  const conBarrios = new Set(aliadas.filter((a) => a.barrio && !SIN_SEDE.has(a.tipo)).map((a) => normal(a.ciudad)))
  for (const a of aliadas) {
    if (SIN_SEDE.has(a.tipo) || (!a.barrio && conBarrios.has(normal(a.ciudad)))) {
      servicios.push(a)
      continue
    }
    const nombre = a.barrio ?? a.ciudad
    const clave = `${normal(a.ciudad)}:${normal(nombre)}`
    const ultima = estaciones.at(-1)
    if (ultima?.clave === clave) ultima.aliadas.push(a)
    else estaciones.push({ clave, nombre, ciudad: a.barrio ? a.ciudad : null, aliadas: [a], clinicaTimu: false })
  }
  const barrio = datos?.clinica_barrio ? normal(datos.clinica_barrio) : null
  const ciudad = datos?.clinica_ciudad ? normal(datos.clinica_ciudad) : null
  if (barrio || ciudad) {
    // «Los Conquistadores, Laureles» está en la estación «Laureles» de Medellín.
    const suya = estaciones.find(
      (e) => (!ciudad || normal(e.ciudad ?? e.nombre) === ciudad) && e.ciudad !== null && barrio !== null && barrio.includes(normal(e.nombre)),
    )
    if (suya) suya.clinicaTimu = true
    else
      estaciones.unshift({
        clave: 'timu',
        nombre: datos?.clinica_barrio ?? datos?.clinica_ciudad ?? '',
        ciudad: datos?.clinica_barrio ? (datos.clinica_ciudad ?? null) : null,
        aliadas: [],
        clinicaTimu: true,
      })
  }
  return { estaciones, servicios }
}

/** Lo menos que paga un peludo al mes entre los planes: el «desde» de la portada. */
export function desdeMensual(planes: PlanPublico[], peludos = 1): string | undefined {
  const n = Math.min(Math.max(peludos, 1), 4)
  const valores = planes.map((p) => p.tarifas.find((t) => t.peludos === n)?.valor).filter((v): v is string => Boolean(v))
  if (valores.length === 0) return undefined
  return valores.reduce((a, b) => (Number(b) < Number(a) ? b : a))
}
