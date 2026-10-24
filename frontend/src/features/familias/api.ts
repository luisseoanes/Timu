import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/api/client'
import type {
  CambioHistorial,
  EstadoAfiliacion,
  EstadoCuenta,
  FamiliaRead,
  MascotaRead,
  Page,
  ServicioRead,
} from '@/types'

export interface FiltrosFamilias {
  q?: string
  ciudad?: string
  estado?: EstadoAfiliacion
  incluir_bajas?: boolean
  limit?: number
  offset?: number
}

export interface NuevaMascota {
  nombre: string
  especie: string
  raza?: string
  sexo?: 'macho' | 'hembra'
  fecha_nacimiento?: string
}

export interface NuevaFamilia {
  titular_nombre: string
  tipo_documento: string
  documento: string
  telefono: string
  email?: string
  ciudad: string
  direccion?: string
  notas?: string
  mascotas: NuevaMascota[]
}

export type CambiosFamilia = Partial<
  Pick<NuevaFamilia, 'titular_nombre' | 'telefono' | 'email' | 'ciudad' | 'direccion' | 'notas'>
>

export function useFamilias(filtros: FiltrosFamilias = {}) {
  return useQuery({
    queryKey: ['familias', filtros],
    queryFn: async () => (await api.get<Page<FamiliaRead>>('/familias', { params: filtros })).data,
  })
}

export function useFamilia(id: string | undefined) {
  return useQuery({
    queryKey: ['familias', id],
    enabled: Boolean(id),
    queryFn: async () => (await api.get<FamiliaRead>(`/familias/${id}`)).data,
  })
}

export function useHistorial(id: string) {
  return useQuery({
    queryKey: ['familias', id, 'historial'],
    queryFn: async () => (await api.get<CambioHistorial[]>(`/familias/${id}/historial`)).data,
  })
}

/** El estado de cuenta responde 404 cuando la familia aún no tiene contrato: no es un error. */
export function useEstadoCuenta(familiaId: string) {
  return useQuery({
    queryKey: ['cartera', 'estado-cuenta', familiaId],
    queryFn: async () => {
      const { data, status } = await api.get<EstadoCuenta>(
        `/cartera/familias/${familiaId}/estado-cuenta`,
        { validateStatus: (s) => s === 200 || s === 404 },
      )
      return status === 404 ? null : data
    },
  })
}

export function useServiciosFamilia(familiaId: string) {
  return useQuery({
    queryKey: ['servicios', { familia_id: familiaId }],
    queryFn: async () =>
      (await api.get<Page<ServicioRead>>('/servicios', { params: { familia_id: familiaId, orden: '-programado_para' } }))
        .data,
  })
}

function useInvalidarFamilias() {
  const qc = useQueryClient()
  return () => qc.invalidateQueries({ queryKey: ['familias'] })
}

export function useCrearFamilia() {
  const invalidar = useInvalidarFamilias()
  return useMutation({
    mutationFn: async (datos: NuevaFamilia) => (await api.post<FamiliaRead>('/familias', datos)).data,
    onSuccess: invalidar,
  })
}

export function useActualizarFamilia(id: string) {
  const invalidar = useInvalidarFamilias()
  return useMutation({
    mutationFn: async (cambios: CambiosFamilia) =>
      (await api.patch<FamiliaRead>(`/familias/${id}`, cambios)).data,
    onSuccess: invalidar,
  })
}

export function useCambiarEstado(id: string) {
  const invalidar = useInvalidarFamilias()
  return useMutation({
    mutationFn: async (datos: { estado: EstadoAfiliacion; motivo?: string }) =>
      (await api.post<FamiliaRead>(`/familias/${id}/estado`, datos)).data,
    onSuccess: invalidar,
  })
}

export function useDarDeBaja(id: string) {
  const invalidar = useInvalidarFamilias()
  return useMutation({
    mutationFn: async (motivo: string) =>
      (await api.post<FamiliaRead>(`/familias/${id}/baja`, { motivo })).data,
    onSuccess: invalidar,
  })
}

export function useHabilitarPortal(id: string) {
  const invalidar = useInvalidarFamilias()
  return useMutation({
    mutationFn: async () => (await api.post<FamiliaRead>(`/familias/${id}/acceso-portal`)).data,
    onSuccess: invalidar,
  })
}

export function useAgregarMascota(familiaId: string) {
  const invalidar = useInvalidarFamilias()
  return useMutation({
    mutationFn: async (mascota: NuevaMascota) =>
      (await api.post<MascotaRead>(`/familias/${familiaId}/mascotas`, mascota)).data,
    onSuccess: invalidar,
  })
}

export function useBajaMascota() {
  const invalidar = useInvalidarFamilias()
  return useMutation({
    mutationFn: async ({ id, motivo }: { id: string; motivo: string }) =>
      (await api.post<MascotaRead>(`/mascotas/${id}/baja`, { motivo })).data,
    onSuccess: invalidar,
  })
}
