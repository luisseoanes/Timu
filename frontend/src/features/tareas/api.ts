import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/api/client'
import type { Page, Rol, TareaListado, TareaRead } from '@/types'

export type Area = 'comercial' | 'operaciones' | 'medico' | 'cartera' | 'servicio_cliente'

export const AREAS: { valor: Area; label: string }[] = [
  { valor: 'operaciones', label: 'Operaciones' },
  { valor: 'comercial', label: 'Comercial' },
  { valor: 'cartera', label: 'Cartera' },
  { valor: 'medico', label: 'Médica' },
  { valor: 'servicio_cliente', label: 'Servicio al cliente' },
]

/** Quién ve cada área (Sección 12, `AREAS_POR_ROL` de la API): solo a ellos se asigna una tarea;
 * a otro perfil se le perdería, porque no la vería ni en «Mis tareas». */
export const PERFILES_DEL_AREA: Record<Area, readonly Rol[]> = {
  comercial: ['comercial'],
  cartera: ['atencion_cliente'],
  servicio_cliente: ['atencion_cliente'],
  operaciones: ['operaciones'],
  medico: ['medico'],
}

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
    queryFn: async () => (await api.get<Page<TareaListado>>('/tareas', { params: filtros })).data,
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
