import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/api/client'
import type { ConversacionRead, InteresadoRead, Page } from '@/types'

export const ETAPAS = [
  { valor: 'nuevo', label: 'Nuevo' },
  { valor: 'contactado', label: 'Contactado' },
  { valor: 'cotizado', label: 'Cotizado' },
  { valor: 'en_afiliacion', label: 'En afiliación' },
  { valor: 'afiliado', label: 'Afiliado' },
] as const

export const ORIGENES = ['panel', 'referido', 'evento', 'campana', 'whatsapp', 'formulario'] as const

export interface Embudo {
  total: number
  por_etapa: Record<string, number>
  por_origen: Record<string, { total: number; afiliados: number }>
  conversion: number | null
}

export interface FiltrosInteresados {
  etapa?: string
  origen?: string
  q?: string
  limit?: number
  offset?: number
}

export function useInteresados(filtros: FiltrosInteresados) {
  return useQuery({
    queryKey: ['comercial', 'interesados', filtros],
    queryFn: async () =>
      (await api.get<Page<InteresadoRead>>('/comercial/interesados', { params: { ...filtros, orden: '-created_at' } })).data,
  })
}

export function useEmbudo(desde: string, hasta: string) {
  return useQuery({
    queryKey: ['comercial', 'embudo', desde, hasta],
    queryFn: async () => (await api.get<Embudo>('/comercial/embudo', { params: { desde, hasta } })).data,
  })
}

export function useConversaciones(estado?: string) {
  return useQuery({
    queryKey: ['comercial', 'conversaciones', estado ?? null],
    refetchInterval: 15000,
    queryFn: async () =>
      (await api.get<ConversacionRead[]>('/comercial/conversaciones', { params: { estado } })).data,
  })
}

export function useArbol(habilitado: boolean) {
  return useQuery({
    queryKey: ['comercial', 'arbol'],
    enabled: habilitado,
    queryFn: async () => (await api.get<Record<string, unknown>>('/comercial/arbol')).data,
  })
}

function useMutacion<T, R>(fn: (datos: T) => Promise<R>) {
  const qc = useQueryClient()
  return useMutation({ mutationFn: fn, onSuccess: () => qc.invalidateQueries({ queryKey: ['comercial'] }) })
}

export function useCrearInteresado() {
  return useMutacion(
    async (datos: { nombre?: string; telefono?: string; email?: string; ciudad?: string; origen: string }) =>
      (await api.post<InteresadoRead>('/comercial/interesados', datos)).data,
  )
}

export function useActualizarInteresado() {
  return useMutacion(
    async ({ id, ...datos }: { id: string; etapa?: string; responsable_id?: string | null; nombre?: string; ciudad?: string }) =>
      (await api.patch<InteresadoRead>(`/comercial/interesados/${id}`, datos)).data,
  )
}

export function usePerderInteresado() {
  return useMutacion(
    async ({ id, motivo }: { id: string; motivo: string }) =>
      (await api.post<InteresadoRead>(`/comercial/interesados/${id}/perdida`, { motivo })).data,
  )
}

export function useReactivarInteresado() {
  return useMutacion(
    async (id: string) => (await api.post<InteresadoRead>(`/comercial/interesados/${id}/reactivacion`)).data,
  )
}

export function useResponderConversacion() {
  return useMutacion(
    async ({ id, texto }: { id: string; texto: string }) =>
      (await api.post(`/comercial/conversaciones/${id}/mensajes`, { texto })).data,
  )
}

export function useLiberarConversacion() {
  return useMutacion(
    async (id: string) => (await api.post<ConversacionRead>(`/comercial/conversaciones/${id}/liberacion`)).data,
  )
}

export function usePublicarArbol() {
  return useMutacion(
    async (datos: { nodos: Record<string, unknown>; nota?: string }) => (await api.put('/comercial/arbol', datos)).data,
  )
}
