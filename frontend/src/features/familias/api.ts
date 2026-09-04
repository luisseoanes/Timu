import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/api/client'
import type { EstadoAfiliacion, Familia, Page } from '@/types'

export interface FiltrosFamilias {
  q?: string
  ciudad?: string
  estado?: EstadoAfiliacion
  limit?: number
  offset?: number
}

export function useFamilias(filtros: FiltrosFamilias = {}) {
  return useQuery({
    queryKey: ['familias', filtros],
    queryFn: async () => {
      const { data } = await api.get<Page<Familia>>('/familias', { params: filtros })
      return data
    },
  })
}

export function useFamilia(id: string | undefined) {
  return useQuery({
    queryKey: ['familias', id],
    enabled: Boolean(id),
    queryFn: async () => {
      const { data } = await api.get<Familia>(`/familias/${id}`)
      return data
    },
  })
}

export function useCrearFamilia() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (payload: Partial<Familia>) => {
      const { data } = await api.post<Familia>('/familias', payload)
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['familias'] }),
  })
}
