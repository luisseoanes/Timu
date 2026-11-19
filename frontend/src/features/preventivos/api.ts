import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/api/client'
import type { CarnetEmitidoRead, EventoRead, FamiliaBandeja, Page, RecuentosBandeja } from '@/types'

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
  /** 6.8 El de la mascota el día de la aplicación, si se anotó. */
  peso_kg: number | null
  /** Quien registró la aplicación, como el sello del carnet impreso. */
  aplicado_por: string | null
  proxima_fecha: string | null
}

/** `GET /preventivos/mascotas/{id}/carnet` (6.15). */
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

export type VistaBandeja = keyof RecuentosBandeja

export interface FiltrosBandeja {
  vista: VistaBandeja
  ciudad?: string
  q?: string
  /** Los de una familia: su línea en la ficha de Familias. */
  familia_id?: string
  limit?: number
  offset?: number
}

/** Lo que falta por autorizar, por agendar o lo ya agendado, por familia (R2-PAN-08). */
export function useBandejaPreventivos(filtros: FiltrosBandeja) {
  return useQuery({
    queryKey: ['preventivos', 'bandeja', filtros],
    queryFn: async () => (await api.get<Page<FamiliaBandeja>>('/preventivos/bandeja', { params: filtros })).data,
  })
}

export function useRecuentosPreventivos(filtros: Pick<FiltrosBandeja, 'ciudad' | 'q'>) {
  return useQuery({
    queryKey: ['preventivos', 'recuentos', filtros],
    queryFn: async () => (await api.get<RecuentosBandeja>('/preventivos/bandeja/recuentos', { params: filtros })).data,
  })
}

export function useCarnet(mascotaId: string | null) {
  return useQuery({
    queryKey: ['preventivos', 'carnet', mascotaId],
    enabled: Boolean(mascotaId),
    queryFn: async () => (await api.get<Carnet>(`/preventivos/mascotas/${mascotaId}/carnet`)).data,
  })
}

/** `ademas`: otras cachés que cambian con la mutación, además de preventivos y servicios. */
function useMutacion<T, R>(fn: (datos: T) => Promise<R>, ademas: string[] = []) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: fn,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['preventivos'] })
      void qc.invalidateQueries({ queryKey: ['servicios'] })
      for (const clave of ademas) void qc.invalidateQueries({ queryKey: [clave] })
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

/** La familia autoriza (o no) de una vez lo que se le pidió: todo o nada. */
export function useAutorizarVarios() {
  return useMutacion(
    async ({ eventos, medio, aprobado }: { eventos: string[]; medio: MedioAutorizacion; aprobado: boolean }) =>
      (await api.post<EventoRead[]>('/preventivos/autorizaciones', { eventos, medio, aprobado })).data,
    // Autorizar puede autorizar la visita ya agendada, y la línea de la familia cambia.
    ['familias'],
  )
}

export function useAplicarPreventivo() {
  return useMutacion(
    async ({ id, ...datos }: { id: string; fecha: string; producto: string; lote?: string; peso_kg?: number }) =>
      (await api.post<EventoRead>(`/preventivos/${id}/aplicacion`, datos)).data,
    // El peso anotado pasa a la ficha de la mascota (6.8).
    ['familias', 'mascotas'],
  )
}

export function useAgendarPreventivo() {
  return useMutacion(
    async ({ id, ...datos }: { id: string; inicio: string; observaciones?: string }) =>
      (await api.post<EventoRead>(`/preventivos/${id}/agendar`, datos)).data,
    ['familias'],
  )
}

export function useCancelarPreventivo() {
  return useMutacion(
    async ({ id, motivo }: { id: string; motivo: string }) =>
      (await api.post<EventoRead>(`/preventivos/${id}/cancelacion`, { motivo })).data,
    ['familias'],
  )
}

export function useEmitirCarnet() {
  return useMutacion(
    async (mascotaId: string) =>
      (await api.post<CarnetEmitidoRead>(`/preventivos/mascotas/${mascotaId}/carnet/pdf`)).data,
  )
}
