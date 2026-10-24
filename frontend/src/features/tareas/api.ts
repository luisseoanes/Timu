import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/api/client'
import type { MiembroEquipo, Page, TareaRead } from '@/types'

export type Area = 'comercial' | 'operaciones' | 'medico' | 'cartera' | 'servicio_cliente'

export const AREAS: { valor: Area; label: string }[] = [
  { valor: 'operaciones', label: 'Operaciones' },
  { valor: 'comercial', label: 'Comercial' },
  { valor: 'cartera', label: 'Cartera' },
  { valor: 'medico', label: 'Médica' },
  { valor: 'servicio_cliente', label: 'Servicio al cliente' },
]

export interface FiltrosTareas {
  area?: Area
  estado?: string
  mias?: boolean
  sin_asignar?: boolean
  vencidas?: boolean
  familia_id?: string
  limit?: number
  offset?: number
}

export interface NuevaTarea {
  titulo: string
  descripcion?: string
  area: Area
  prioridad: 'baja' | 'media' | 'alta'
  vence_en_dias?: number
  familia_id?: string
  asignada_a_id?: string
}

export function useTareas(filtros: FiltrosTareas) {
  return useQuery({
    queryKey: ['tareas', filtros],
    queryFn: async () => (await api.get<Page<TareaRead>>('/tareas', { params: filtros })).data,
  })
}

/** Personas del equipo interno para asignar (GET /auth/equipo, abierto a todo perfil interno). */
export function useEquipo(rol?: string) {
  return useQuery({
    queryKey: ['equipo', rol ?? null],
    staleTime: 5 * 60 * 1000,
    queryFn: async () => (await api.get<MiembroEquipo[]>('/auth/equipo', { params: { rol } })).data,
  })
}

function useMutacionTarea<T>(fn: (datos: T) => Promise<TareaRead>) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: fn,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tareas'] }),
  })
}

export function useCrearTarea() {
  return useMutacionTarea(async (datos: NuevaTarea) => (await api.post<TareaRead>('/tareas', datos)).data)
}

export function useAsignarTarea() {
  return useMutacionTarea(
    async ({ id, usuario_id }: { id: string; usuario_id: string | null }) =>
      (await api.patch<TareaRead>(`/tareas/${id}/asignacion`, { usuario_id })).data,
  )
}

export function useIniciarTarea() {
  return useMutacionTarea(async (id: string) => (await api.post<TareaRead>(`/tareas/${id}/iniciar`)).data)
}

export function useCerrarTarea() {
  return useMutacionTarea(
    async ({ id, resolucion }: { id: string; resolucion: string }) =>
      (await api.post<TareaRead>(`/tareas/${id}/cerrar`, { resolucion })).data,
  )
}
