import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/api/client'
import type { CarnetEmitidoRead, EventoRead, Page } from '@/types'

export interface FiltrosPreventivos {
  mascota_id?: string
  estado?: 'programado' | 'aplicado' | 'cancelado'
  desde?: string
  hasta?: string
  pendientes_autorizacion?: boolean
  limit?: number
  offset?: number
}

export interface FilaCarnet {
  id: string
  tipo: string
  nombre: string
  dosis: number
  refuerzo: boolean
  fecha_programada: string
  fecha_aplicacion: string | null
  producto: string | null
  lote: string | null
  /** F2-PRE-07 El de la mascota el día de la aplicación, si se anotó. */
  peso_kg: number | null
  proxima_fecha: string | null
}

/** `GET /preventivos/mascotas/{id}/carnet` (F2-PRE-05). */
export interface Carnet {
  mascota: { id: string; nombre: string; especie: string; raza: string | null; fecha_nacimiento: string | null }
  aplicados: FilaCarnet[]
  vencidos: FilaCarnet[]
  proximos: FilaCarnet[]
}

export type MedioAutorizacion = 'whatsapp' | 'telefono' | 'presencial' | 'portal' | 'formulario'

export function usePreventivos(filtros: FiltrosPreventivos) {
  return useQuery({
    queryKey: ['preventivos', filtros],
    queryFn: async () => (await api.get<Page<EventoRead>>('/preventivos', { params: filtros })).data,
  })
}

export function useCarnet(mascotaId: string | null) {
  return useQuery({
    queryKey: ['preventivos', 'carnet', mascotaId],
    enabled: Boolean(mascotaId),
    queryFn: async () => (await api.get<Carnet>(`/preventivos/mascotas/${mascotaId}/carnet`)).data,
  })
}

function useMutacion<T, R>(fn: (datos: T) => Promise<R>) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: fn,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['preventivos'] })
      void qc.invalidateQueries({ queryKey: ['servicios'] })
    },
  })
}

export function useGenerarCalendario() {
  return useMutacion(
    async (mascotaId: string) => (await api.post<EventoRead[]>(`/preventivos/mascotas/${mascotaId}/calendario`)).data,
  )
}

export function useAutorizarPreventivo() {
  return useMutacion(
    async ({ id, medio, aprobado }: { id: string; medio: MedioAutorizacion; aprobado: boolean }) =>
      (await api.post<EventoRead>(`/preventivos/${id}/autorizacion`, { medio, aprobado })).data,
  )
}

export function useAplicarPreventivo() {
  return useMutacion(
    async ({ id, ...datos }: { id: string; fecha: string; producto: string; lote?: string; peso_kg?: number }) =>
      (await api.post<EventoRead>(`/preventivos/${id}/aplicacion`, datos)).data,
  )
}

export function useAgendarPreventivo() {
  return useMutacion(
    async ({ id, ...datos }: { id: string; inicio: string; observaciones?: string }) =>
      (await api.post<EventoRead>(`/preventivos/${id}/agendar`, datos)).data,
  )
}

export function useCancelarPreventivo() {
  return useMutacion(
    async ({ id, motivo }: { id: string; motivo: string }) =>
      (await api.post<EventoRead>(`/preventivos/${id}/cancelacion`, { motivo })).data,
  )
}

export function useEmitirCarnet() {
  return useMutacion(
    async (mascotaId: string) =>
      (await api.post<CarnetEmitidoRead>(`/preventivos/mascotas/${mascotaId}/carnet/pdf`)).data,
  )
}
