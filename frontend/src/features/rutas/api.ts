import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/api/client'
import type { PlanificacionRead } from '@/types'

export interface Parada {
  id: string
  servicio_id: string
  orden: number
  estado: 'pendiente' | 'en_camino' | 'en_sitio' | 'completada' | 'omitida' | string
  latitud: number | null
  longitud: number | null
  llegada_estimada: string | null
  llegada_en: string | null
  salida_en: string | null
  nota: string | null
  motivo_omision: string | null
}

/** Ruta tal como la presenta el backend (rutas/service.py: `presentar`). */
export interface Ruta {
  id: string
  fecha: string
  ciudad: string
  responsable_id: string
  estado: 'planificada' | 'en_curso' | 'finalizada' | 'cancelada' | string
  distancia_km: number | null
  duracion_min: number | null
  inicio_real: string | null
  fin_real: string | null
  paradas: Parada[]
}

export interface ResultadoPlanificacion {
  rutas?: string[]
  asignados?: number
  sin_asignar?: { servicio_id: string; motivo: string }[]
}

export function useRutas(fecha: string, ciudad: string) {
  return useQuery({
    queryKey: ['rutas', fecha, ciudad],
    queryFn: async () => (await api.get<Ruta[]>('/rutas', { params: { fecha, ciudad: ciudad || undefined } })).data,
  })
}

export function usePorRutear(fecha: string, ciudad: string) {
  return useQuery({
    queryKey: ['rutas', 'por-rutear', fecha, ciudad],
    enabled: Boolean(ciudad),
    queryFn: async () =>
      (await api.get<{ id: string; familia_id: string; programado_para: string }[]>('/rutas/por-rutear', { params: { fecha, ciudad } }))
        .data,
  })
}

/** La optimización corre en el worker: se consulta cada dos segundos mientras esté pendiente. */
export function usePlanificacion(id: string | null) {
  return useQuery({
    queryKey: ['rutas', 'planificacion', id],
    enabled: Boolean(id),
    refetchInterval: (q) => (q.state.data?.estado === 'pendiente' ? 2000 : false),
    queryFn: async () => (await api.get<PlanificacionRead>(`/rutas/planificaciones/${id}`)).data,
  })
}

function useMutacion<T, R>(fn: (datos: T) => Promise<R>) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: fn,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['rutas'] })
      void qc.invalidateQueries({ queryKey: ['servicios'] })
    },
  })
}

export function usePlanificar() {
  return useMutacion(
    async (datos: { fecha: string; ciudad: string; responsables: string[] }) =>
      (await api.post<PlanificacionRead>('/rutas/planificaciones', datos)).data,
  )
}

export function useAccionRuta() {
  return useMutacion(
    async ({ id, accion }: { id: string; accion: 'inicio' | 'cancelacion' }) =>
      (await api.post<Ruta>(`/rutas/${id}/${accion}`)).data,
  )
}

export function useAccionParada() {
  return useMutacion(
    async ({ id, accion }: { id: string; accion: 'en-camino' | 'llegada' }) =>
      (await api.post<Ruta>(`/rutas/paradas/${id}/${accion}`)).data,
  )
}

export function useSalidaParada() {
  return useMutacion(async ({ id, nota, evidencia }: { id: string; nota?: string; evidencia?: File }) => {
    const forma = new FormData()
    if (nota) forma.append('nota', nota)
    if (evidencia) forma.append('evidencia', evidencia)
    return (await api.post<Ruta>(`/rutas/paradas/${id}/salida`, forma)).data
  })
}

export function useOmitirParada() {
  return useMutacion(
    async ({ id, motivo, cancelar_servicio }: { id: string; motivo: string; cancelar_servicio: boolean }) =>
      (await api.post<Ruta>(`/rutas/paradas/${id}/omision`, { motivo, cancelar_servicio })).data,
  )
}

export function useAgregarParada() {
  return useMutacion(
    async ({ rutaId, servicioId }: { rutaId: string; servicioId: string }) =>
      (await api.post<Ruta>(`/rutas/${rutaId}/paradas`, { servicio_id: servicioId })).data,
  )
}
