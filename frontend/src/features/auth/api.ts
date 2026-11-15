import { useQuery } from '@tanstack/react-query'

import { api } from '@/api/client'
import type { EstadoEnlace, MiembroEquipo } from '@/types'

/** Personas del equipo interno para asignar (GET /auth/equipo, abierto a todo perfil interno). */
export function useEquipo(rol?: string) {
  return useQuery({
    queryKey: ['equipo', rol ?? null],
    staleTime: 5 * 60 * 1000,
    queryFn: async () => (await api.get<MiembroEquipo[]>('/auth/equipo', { params: { rol } })).data,
  })
}

/**
 * Si el enlace de recuperación o de activación sirve, sin gastarlo (POST /auth/enlace: el
 * token va en el cuerpo, no en la URL). Comparte el límite estricto del ingreso, así que no
 * se reintenta solo: la pantalla ofrece «Reintentar».
 */
export function useEstadoEnlace(token: string) {
  return useQuery({
    queryKey: ['enlace', token],
    enabled: token !== '',
    retry: false,
    staleTime: Infinity,
    queryFn: async () => (await api.post<EstadoEnlace>('/auth/enlace', { token })).data,
  })
}
