import { useQuery } from '@tanstack/react-query'

import { api } from '@/api/client'
import type { MiembroEquipo } from '@/types'

/** Personas del equipo interno para asignar (GET /auth/equipo, abierto a todo perfil interno). */
export function useEquipo(rol?: string) {
  return useQuery({
    queryKey: ['equipo', rol ?? null],
    staleTime: 5 * 60 * 1000,
    queryFn: async () => (await api.get<MiembroEquipo[]>('/auth/equipo', { params: { rol } })).data,
  })
}
