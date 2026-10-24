import { useQuery } from '@tanstack/react-query'

import { api } from '@/api/client'
import type { Page, ServicioRead, TareaRead } from '@/types'

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
    queryFn: async () => (await api.get<Indicadores>('/dashboard/indicadores', { params: filtros })).data,
  })
}

export function useDefiniciones() {
  return useQuery({
    queryKey: ['dashboard', 'definiciones'],
    staleTime: Infinity,
    queryFn: async () => (await api.get<Definicion[]>('/dashboard/definiciones')).data,
  })
}

/** Servicios de hoy en adelante, para «Próximos servicios». */
export function useProximosServicios(desde: string) {
  return useQuery({
    queryKey: ['servicios', { desde, proximos: true }],
    queryFn: async () =>
      (
        await api.get<Page<ServicioRead>>('/servicios', {
          params: { desde, estado: 'agendado', limit: 5, orden: 'programado_para' },
        })
      ).data,
  })
}

/** Conteos para «Requiere atención»: basta el `total` de cada listado. */
export function useAlertas() {
  return useQuery({
    queryKey: ['dashboard', 'alertas'],
    queryFn: async () => {
      const total = async (ruta: string, params: Record<string, unknown>) =>
        (await api.get<Page<unknown>>(ruta, { params: { ...params, limit: 1 } })).data.total
      const [tareasVencidas, preventivosPorAutorizar, enMora] = await Promise.all([
        total('/tareas', { vencidas: true }),
        total('/preventivos', { pendientes_autorizacion: true }),
        total('/cartera/contratos', { solo_mora: true }),
      ])
      return { tareasVencidas, preventivosPorAutorizar, enMora }
    },
  })
}

export function useMisTareas() {
  return useQuery({
    queryKey: ['tareas', { mias: true, estado: 'abierta' }],
    queryFn: async () =>
      (await api.get<Page<TareaRead>>('/tareas', { params: { mias: true, estado: 'abierta', limit: 5 } })).data,
  })
}
