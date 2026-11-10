import { useMutation, useQueries, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/api/client'
import type {
  CambioHistorial,
  ContactoRead,
  EstadoAfiliacion,
  EstadoCuenta,
  FamiliaRead,
  MascotaRead,
  Page,
  ResumenServiciosRead,
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
  barrio: string
  direccion?: string
  complemento?: string
  notas?: string
  mascotas: NuevaMascota[]
}

export type CambiosFamilia = Partial<
  Pick<
    NuevaFamilia,
    'titular_nombre' | 'telefono' | 'email' | 'ciudad' | 'barrio' | 'direccion' | 'complemento' | 'notas'
  >
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

/** Nombre y familia de las mascotas de un listado: una consulta por mascota distinta, cacheada. */
export function useMascotas(ids: string[]) {
  const unicos = [...new Set(ids)]
  const consultas = useQueries({
    queries: unicos.map((id) => ({
      queryKey: ['mascotas', id],
      staleTime: 5 * 60 * 1000,
      queryFn: async () => (await api.get<MascotaRead>(`/mascotas/${id}`)).data,
    })),
  })
  const porId = new Map<string, MascotaRead>()
  consultas.forEach((c) => c.data && porId.set(c.data.id, c.data))
  return porId
}

/** 6.1 Contacto adicional: solo consulta, sin acceso a la plataforma ni mensajes. */
export interface DatosContacto {
  nombre: string
  telefono: string
  relacion?: string
  email?: string
}

export function useAgregarContacto(familiaId: string) {
  const invalidar = useInvalidarFamilias()
  return useMutation({
    mutationFn: async (datos: DatosContacto) =>
      (await api.post<ContactoRead>(`/familias/${familiaId}/contactos`, datos)).data,
    onSuccess: invalidar,
  })
}

export function useActualizarContacto(familiaId: string) {
  const invalidar = useInvalidarFamilias()
  return useMutation({
    mutationFn: async ({ id, ...datos }: Partial<DatosContacto> & { id: string }) =>
      (await api.patch<ContactoRead>(`/familias/${familiaId}/contactos/${id}`, datos)).data,
    onSuccess: invalidar,
  })
}

export function useBajaContacto(familiaId: string) {
  const invalidar = useInvalidarFamilias()
  return useMutation({
    mutationFn: async (id: string) => {
      await api.post(`/familias/${familiaId}/contactos/${id}/baja`)
    },
    onSuccess: invalidar,
  })
}

/** Rango y filtros del resumen de servicios de la ficha: fechas en formato AAAA-MM-DD. */
export interface FiltrosResumen {
  desde: string
  hasta: string
  mascota_id?: string
  incluir_cancelados?: boolean
}

/** 6.1 Utilizados y pendientes de la familia (o de una mascota) en un rango, con su cupo. */
export function useResumenServicios(familiaId: string, filtros: FiltrosResumen) {
  return useQuery({
    queryKey: ['servicios', 'resumen', familiaId, filtros],
    // Mientras se escribe una fecha, o con el rango al revés, no hay nada que pedir.
    enabled: Boolean(filtros.desde && filtros.hasta) && filtros.desde <= filtros.hasta,
    queryFn: async () =>
      (
        await api.get<ResumenServiciosRead>('/servicios/resumen', {
          params: { familia_id: familiaId, ...filtros },
        })
      ).data,
  })
}

