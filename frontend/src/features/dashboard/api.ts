import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { api } from '@/api/client'
import type { ContratoListado, EventoRead, Page, ServicioRead, TareaRead } from '@/types'

/** Respuesta de `GET /dashboard/indicadores` (definiciones en docs/indicadores.md). */
export interface Indicadores {
  periodo: { desde: string; hasta: string; ciudad: string | null }
  indicadores: {
    afiliaciones: number
    retiros: number
    vigentes: number
    recaudo: number
    facturado: number
    recaudo_del_facturado: number | null
    mora: { contratos_en_mora: number; saldo_vencido: number; porcentaje: number | null }
    cumplimiento_rutas: {
      paradas_planeadas: number
      paradas_completadas: number
      cumplimiento: number | null
      puntualidad: number | null
    }
    servicios_por_tipo: Record<string, number>
    satisfaccion: { enviadas: number; respondidas: number; promedio: number | null; tasa_respuesta: number | null }
  }
}

export type ValoresIndicadores = Indicadores['indicadores']

/** Un mes de la serie: los mismos indicadores; `parcial` si el mes aún no termina. */
export interface MesEvolucion {
  periodo: Indicadores['periodo']
  indicadores: Partial<ValoresIndicadores>
  parcial: boolean
}

/** Respuesta de `GET /dashboard/evolucion`: 12 meses y el período con que se compara. */
export interface Evolucion {
  anterior: { periodo: Indicadores['periodo']; indicadores: Partial<ValoresIndicadores> }
  meses: MesEvolucion[]
}

export interface Definicion {
  codigo: string
  nombre: string
  formula: string
  unidad: string
}

export interface FiltrosIndicadores {
  desde: string
  hasta: string
  ciudad?: string
}

export function useIndicadores(filtros: FiltrosIndicadores) {
  return useQuery({
    queryKey: ['dashboard', 'indicadores', filtros],
    // Al cambiar el período, las cifras de antes siguen a la vista mientras llegan las nuevas.
    placeholderData: keepPreviousData,
    queryFn: async () => (await api.get<Indicadores>('/dashboard/indicadores', { params: filtros })).data,
  })
}

/** Lo que dibujan las series: todo menos el reparto por tipo, que no tiene evolución. */
const CODIGOS_SERIE = [
  'afiliaciones',
  'retiros',
  'vigentes',
  'recaudo',
  'facturado',
  'mora',
  'cumplimiento_rutas',
  'satisfaccion',
]

export function useEvolucion(filtros: FiltrosIndicadores) {
  return useQuery({
    queryKey: ['dashboard', 'evolucion', filtros],
    placeholderData: keepPreviousData,
    queryFn: async () =>
      (
        await api.get<Evolucion>('/dashboard/evolucion', {
          params: { ...filtros, codigos: CODIGOS_SERIE },
          paramsSerializer: { indexes: null },
        })
      ).data,
  })
}

/** Con `activa` en false no se piden: el Inicio solo las enseña al abrir una serie. */
export function useDefiniciones(activa = true) {
  return useQuery({
    queryKey: ['dashboard', 'definiciones'],
    enabled: activa,
    staleTime: Infinity,
    queryFn: async () => (await api.get<Definicion[]>('/dashboard/definiciones')).data,
  })
}

/** Servicios agendados de hoy en adelante: lo que viene en la línea del equipo. Veinte bastan
 * para hoy y para agrupar los días siguientes; el total dice cuántos quedan fuera. */
export function useProximosServicios(desde: string) {
  return useQuery({
    queryKey: ['servicios', { desde, proximos: true }],
    queryFn: async () =>
      (
        await api.get<Page<ServicioRead>>('/servicios', {
          params: { desde, estado: 'agendado', limit: 20, orden: 'programado_para' },
        })
      ).data,
  })
}

/** Cuántos hay y el primero de la fila: para contar un grupo de vencidos con su ejemplo. */
export interface Grupo<T> {
  total: number
  primero: T | undefined
}

async function grupo<T>(ruta: string, params: Record<string, unknown>): Promise<Grupo<T>> {
  const { items, total } = (await api.get<Page<T>>(ruta, { params: { ...params, limit: 1 } })).data
  return { total, primero: items[0] }
}

/** Lo vencido del equipo. Cartera lista primero el contrato más atrasado; preventivos y
 * tareas, el más antiguo. */
export function useVencidos() {
  return useQuery({
    queryKey: ['dashboard', 'vencidos'],
    queryFn: async () => {
      const [mora, preventivos, tareas] = await Promise.all([
        grupo<ContratoListado>('/cartera/contratos', { solo_mora: true }),
        grupo<EventoRead>('/preventivos', { pendientes_autorizacion: true }),
        grupo<TareaRead>('/tareas', { vencidas: true, orden: 'vence_el' }),
      ])
      return { mora, preventivos, tareas }
    },
  })
}

/** Consulta sin firmar del médico: solo lo que la línea cuenta de ella. */
export interface Borrador {
  id: string
  fecha: string
}

/** Lo pendiente del médico: sus consultas sin firmar y sus tareas vencidas y abiertas. */
export function useMisPendientes() {
  return useQuery({
    queryKey: ['dashboard', 'mis-pendientes'],
    queryFn: async () => {
      const [borradores, vencidas, abiertas] = await Promise.all([
        api.get<Borrador[]>('/clinica/borradores').then((r) => r.data),
        grupo<TareaRead>('/tareas', { mias: true, vencidas: true, orden: 'vence_el' }),
        api
          .get<Page<TareaRead>>('/tareas', { params: { mias: true, estado: 'abierta', limit: 5, orden: 'vence_el' } })
          .then((r) => r.data),
      ])
      return { borradores, vencidas, abiertas }
    },
  })
}
