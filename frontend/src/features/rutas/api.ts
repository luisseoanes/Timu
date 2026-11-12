import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/api/client'
import type { PlanificacionRead, PorRutearRead, RutaRead } from '@/types'

export interface ResultadoPlanificacion {
  rutas?: number
  asignados?: number
  sin_asignar?: { servicio_id: string; motivo: string }[]
}

/** Las rutas de un día. Con `responsable`, solo las de esa persona: la de quien sale a campo. */
export function useRutas(fecha: string, filtros: { ciudad?: string; responsable?: string } = {}) {
  return useQuery({
    queryKey: ['rutas', fecha, filtros],
    queryFn: async () =>
      (
        await api.get<RutaRead[]>('/rutas', {
          params: { fecha, ciudad: filtros.ciudad || undefined, responsable_id: filtros.responsable },
        })
      ).data,
  })
}

/** Los domicilios del día que aún no están en ninguna ruta; sin ciudad, los de todas. */
export function usePorRutear(fecha: string, ciudad: string) {
  return useQuery({
    queryKey: ['rutas', 'por-rutear', fecha, ciudad],
    queryFn: async () =>
      (await api.get<PorRutearRead[]>('/rutas/por-rutear', { params: { fecha, ciudad: ciudad || undefined } })).data,
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
      (await api.post<RutaRead>(`/rutas/${id}/${accion}`)).data,
  )
}

export function useAccionParada() {
  return useMutacion(
    async ({ id, accion }: { id: string; accion: 'en-camino' | 'llegada' }) =>
      (await api.post<RutaRead>(`/rutas/paradas/${id}/${accion}`)).data,
  )
}

export function useSalidaParada() {
  return useMutacion(async ({ id, nota, evidencia }: { id: string; nota?: string; evidencia?: File }) => {
    const forma = new FormData()
    if (nota) forma.append('nota', nota)
    if (evidencia) forma.append('evidencia', evidencia)
    return (await api.post<RutaRead>(`/rutas/paradas/${id}/salida`, forma)).data
  })
}

export function useOmitirParada() {
  return useMutacion(
    async ({ id, motivo, cancelar_servicio }: { id: string; motivo: string; cancelar_servicio: boolean }) =>
      (await api.post<RutaRead>(`/rutas/paradas/${id}/omision`, { motivo, cancelar_servicio })).data,
  )
}

export function useAgregarParada() {
  return useMutacion(
    async ({ rutaId, servicioId }: { rutaId: string; servicioId: string }) =>
      (await api.post<RutaRead>(`/rutas/${rutaId}/paradas`, { servicio_id: servicioId })).data,
  )
}
