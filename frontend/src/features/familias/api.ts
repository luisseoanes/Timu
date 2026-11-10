import { useMutation, useQueries, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/api/client'
import type {
  CambioHistorial,
  CategoriaDocumento,
  CotizacionRead,
  ContactoRead,
  DocumentoRead,
  EstadoAfiliacion,
  EstadoCuenta,
  FamiliaRead,
  MensajeRead,
  Periodicidad,
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
  /** Obligatoria en el panel: si no se sabe la exacta, una aproximada. */
  fecha_nacimiento: string
  peso_kg: number
  esterilizada?: boolean
}

/** Lo que se corrige de una mascota. La especie no cambia: define su plan preventivo. */
export type CambiosMascota = Partial<Omit<NuevaMascota, 'especie' | 'raza'>> & { raza?: string | null }

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
    // Con afiliacion vigente, `plan_id` es el plan con que entra al contrato.
    mutationFn: async (mascota: NuevaMascota & { plan_id?: string }) =>
      (await api.post<MascotaRead>(`/familias/${familiaId}/mascotas`, mascota)).data,
    onSuccess: invalidar,
  })
}

export function useActualizarMascota() {
  const invalidar = useInvalidarFamilias()
  return useMutation({
    mutationFn: async ({ id, ...cambios }: CambiosMascota & { id: string }) =>
      (await api.patch<MascotaRead>(`/mascotas/${id}`, cambios)).data,
    onSuccess: invalidar,
  })
}

export function useSubirFotoMascota() {
  const invalidar = useInvalidarFamilias()
  return useMutation({
    mutationFn: async ({ id, foto }: { id: string; foto: File }) => {
      const forma = new FormData()
      forma.append('foto', foto)
      return (await api.put<MascotaRead>(`/mascotas/${id}/foto`, forma)).data
    },
    onSuccess: invalidar,
  })
}

export function useQuitarFotoMascota() {
  const invalidar = useInvalidarFamilias()
  return useMutation({
    mutationFn: async (id: string) => (await api.delete<MascotaRead>(`/mascotas/${id}/foto`)).data,
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

/** 6.1 Historial de comunicaciones de la familia, de lo más reciente a lo más antiguo. */
export function useMensajesFamilia(familiaId: string, offset: number) {
  return useQuery({
    queryKey: ['comunicaciones', 'mensajes', familiaId, offset],
    queryFn: async () =>
      (
        await api.get<Page<MensajeRead>>('/comunicaciones/mensajes', {
          params: { familia_id: familiaId, orden: '-created_at', limit: 20, offset },
        })
      ).data,
  })
}

/** 6.1 Documentos de la familia: los subidos y los generados (contratos, carnets, clínicos). */
export function useDocumentos(familiaId: string, mascotaId?: string) {
  return useQuery({
    queryKey: ['documentos', familiaId, mascotaId ?? null],
    queryFn: async () =>
      (
        await api.get<DocumentoRead[]>(`/familias/${familiaId}/documentos`, {
          params: mascotaId ? { mascota_id: mascotaId } : undefined,
        })
      ).data,
  })
}

export interface NuevoDocumento {
  archivo: File
  categoria: CategoriaDocumento
  descripcion?: string
  mascota_id?: string
  visible_familia: boolean
}

function useInvalidarDocumentos(familiaId: string) {
  const qc = useQueryClient()
  return () => qc.invalidateQueries({ queryKey: ['documentos', familiaId] })
}

export function useSubirDocumento(familiaId: string) {
  const invalidar = useInvalidarDocumentos(familiaId)
  return useMutation({
    mutationFn: async ({ archivo, ...datos }: NuevoDocumento) => {
      const forma = new FormData()
      forma.append('archivo', archivo)
      forma.append('categoria', datos.categoria)
      forma.append('visible_familia', String(datos.visible_familia))
      if (datos.descripcion) forma.append('descripcion', datos.descripcion)
      if (datos.mascota_id) forma.append('mascota_id', datos.mascota_id)
      return (await api.post<DocumentoRead>(`/familias/${familiaId}/documentos`, forma)).data
    },
    onSuccess: invalidar,
  })
}

export type CambiosDocumento = { categoria?: CategoriaDocumento; descripcion?: string | null; visible_familia?: boolean }

export function useActualizarDocumento(familiaId: string) {
  const invalidar = useInvalidarDocumentos(familiaId)
  return useMutation({
    mutationFn: async ({ id, ...cambios }: CambiosDocumento & { id: string }) =>
      (await api.patch<DocumentoRead>(`/documentos/${id}`, cambios)).data,
    onSuccess: invalidar,
  })
}

export function useQuitarDocumento(familiaId: string) {
  const invalidar = useInvalidarDocumentos(familiaId)
  return useMutation({
    mutationFn: async (id: string) => {
      await api.post(`/documentos/${id}/baja`)
    },
    onSuccess: invalidar,
  })
}

/** Un peludo con el plan elegido, para cotizar o afiliar. */
export interface PeludoElegido {
  mascota_id: string
  especie: string
  plan_id: string
}

/** 6.2 / 6.3 Lo que pagaría la afiliación con cada periodicidad, del mismo cálculo que cobra. */
export function useCotizacion(ciudad: string, peludos: PeludoElegido[]) {
  const completa = peludos.length > 0 && peludos.every((p) => p.plan_id)
  return useQuery({
    queryKey: ['planes', 'cotizacion', ciudad, peludos.map((p) => [p.especie, p.plan_id])],
    enabled: completa,
    queryFn: async () =>
      (
        await api.post<CotizacionRead[]>('/planes/cotizacion', {
          ciudad,
          peludos: peludos.map(({ especie, plan_id }) => ({ especie, plan_id })),
        })
      ).data,
  })
}

export interface InicioAfiliacion {
  solicitud_id: string
  valor: string
  enlace_pago: string
}

export interface DatosAfiliacion {
  peludos: { mascota_id: string; plan_id: string }[]
  periodicidad: Periodicidad
  medio_aceptacion: string
  detalle_aceptacion?: string
}

function useRefrescarAfiliacion() {
  const qc = useQueryClient()
  return () => {
    void qc.invalidateQueries({ queryKey: ['familias'] })
    void qc.invalidateQueries({ queryKey: ['cartera'] })
  }
}

/** F1-AFI Afiliación asistida: cada peludo con su plan; devuelve el enlace de pago. */
export function useAfiliarAsistida(familiaId: string) {
  const refrescar = useRefrescarAfiliacion()
  return useMutation({
    mutationFn: async (datos: DatosAfiliacion) =>
      (await api.post<InicioAfiliacion>('/afiliaciones/asistida', { familia_id: familiaId, ...datos })).data,
    onSuccess: refrescar,
  })
}

export function usePagoManualAfiliacion() {
  const refrescar = useRefrescarAfiliacion()
  return useMutation({
    mutationFn: async ({ solicitudId, ...datos }: { solicitudId: string; medio: string; comprobante: string }) =>
      (await api.post(`/afiliaciones/${solicitudId}/pago-manual`, datos)).data,
    onSuccess: refrescar,
  })
}

/** F1-PLA-02 Un peludo cambia de plan; cómo se cobra lo decide la regla `plan.cambio`. */
export function useCambiarPlanMascota() {
  const refrescar = useRefrescarAfiliacion()
  return useMutation({
    mutationFn: async ({ contratoId, mascotaId, planId }: { contratoId: string; mascotaId: string; planId: string }) =>
      (await api.post(`/planes/contratos/${contratoId}/cambio`, { mascota_id: mascotaId, plan_id: planId })).data,
    onSuccess: refrescar,
  })
}

