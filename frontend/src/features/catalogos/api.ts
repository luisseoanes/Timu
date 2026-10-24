import { useQuery } from '@tanstack/react-query'

import { api } from '@/api/client'
import type { CiudadRead, EspecieRead, PlanRead, TipoServicioRead } from '@/types'

// Los catálogos cambian poco: se mantienen en caché diez minutos.
const DIEZ_MINUTOS = 10 * 60 * 1000

export function useCiudades() {
  return useQuery({
    queryKey: ['catalogos', 'ciudades'],
    staleTime: DIEZ_MINUTOS,
    queryFn: async () => (await api.get<CiudadRead[]>('/catalogos/ciudades')).data,
  })
}

export function useEspecies() {
  return useQuery({
    queryKey: ['catalogos', 'especies'],
    staleTime: DIEZ_MINUTOS,
    queryFn: async () => (await api.get<EspecieRead[]>('/catalogos/especies')).data,
  })
}

export function useTiposServicio(modalidad?: string) {
  return useQuery({
    queryKey: ['catalogos', 'tipos-servicio', modalidad ?? null],
    staleTime: DIEZ_MINUTOS,
    queryFn: async () =>
      (await api.get<TipoServicioRead[]>('/catalogos/tipos-servicio', { params: { modalidad } })).data,
  })
}

export function usePlanes() {
  return useQuery({
    queryKey: ['planes'],
    staleTime: DIEZ_MINUTOS,
    queryFn: async () => (await api.get<PlanRead[]>('/planes')).data,
  })
}

/** Nombre legible de un tipo de servicio por su código. `ServicioRead.tipo` es la
 * modalidad (domiciliario, preventivo…); el nombre vive en el catálogo. */
export function useNombreTipoServicio(): (codigo: string) => string {
  const tipos = useTiposServicio()
  return (codigo) => tipos.data?.find((t) => t.codigo === codigo)?.nombre ?? codigo.replace(/_/g, ' ')
}
