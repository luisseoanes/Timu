import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/api/client'
import type {
  AltaIniciada,
  AltaPeludoRead,
  ColorPlan,
  CotizacionAltaRead,
  CupoRead,
  DocumentoRead,
  EstadoCuenta,
  FamiliaRead,
  InicioPago,
  LineaFamiliaRead,
  MascotaRead,
  PagoPortalRead,
  PeludoNuevoIn,
  Periodicidad,
  PlanPublico,
  ServicioPortalRead,
} from '@/types'

import type { Carnet } from '@/features/preventivos'

export interface BeneficioPortal {
  tipo_servicio: string
  cupo: number | null
  periodo: string
  usados: number
  disponibles: number | null
  cobertura_pct: number
}

/** La afiliación vigente: cada peludo con su plan, lo que paga y sus beneficios. */
export interface PlanPortal {
  estado: string
  periodicidad: Periodicidad
  valor_periodo: string
  valor_mensual: string
  fecha_inicio: string
  fecha_renovacion: string
  mascotas: { mascota_id: string; mascota: string; plan: string; color: ColorPlan; valor_mensual: string; beneficios: BeneficioPortal[] }[]
}

/** Historia en la vista de la familia: todo lo clínico menos las notas internas. */
export interface EntradaPortal {
  id: string
  fecha: string
  tipo: string
  motivo: string
  diagnostico: string | null
  tratamiento: string | null
  examen_fisico: string | null
  estado: string
}

export function useMiFamilia() {
  return useQuery({
    queryKey: ['portal', 'familia'],
    queryFn: async () => (await api.get<FamiliaRead>('/portal/mi-familia')).data,
  })
}

/** Sin contrato vigente la familia aún no tiene plan: 404 no es un error aquí. */
export function useMiPlan() {
  return useQuery({
    queryKey: ['portal', 'plan'],
    queryFn: async () => {
      const r = await api.get<PlanPortal>('/portal/plan', { validateStatus: (s) => s === 200 || s === 404 })
      return r.status === 404 ? null : r.data
    },
  })
}

export function useMiCuenta() {
  return useQuery({
    queryKey: ['portal', 'cuenta'],
    queryFn: async () => {
      const r = await api.get<EstadoCuenta>('/portal/estado-cuenta', { validateStatus: (s) => s === 200 || s === 404 })
      return r.status === 404 ? null : r.data
    },
  })
}

/** R3-POR-01 La línea de la familia (cuotas, preventivos y visitas): el inicio la abre en «hoy». */
export function useMiLinea() {
  return useQuery({
    queryKey: ['portal', 'linea'],
    queryFn: async () => (await api.get<LineaFamiliaRead>('/portal/linea')).data,
  })
}

export function useMisServicios(incluirPasados = false) {
  return useQuery({
    queryKey: ['portal', 'servicios', incluirPasados],
    queryFn: async () =>
      (await api.get<ServicioPortalRead[]>('/portal/servicios', { params: { incluir_pasados: incluirPasados || undefined } })).data,
  })
}

export function useDisponibilidadPortal(fecha: string, tipo: string) {
  return useQuery({
    queryKey: ['portal', 'disponibilidad', fecha, tipo],
    enabled: Boolean(fecha && tipo),
    queryFn: async () => (await api.get<CupoRead[]>('/portal/disponibilidad', { params: { fecha, tipo_codigo: tipo } })).data,
  })
}

export function useHistoriaPortal(mascotaId: string) {
  return useQuery({
    queryKey: ['portal', 'historia', mascotaId],
    queryFn: async () => (await api.get<EntradaPortal[]>(`/portal/mascotas/${mascotaId}/historia`)).data,
  })
}

export function useCarnetPortal(mascotaId: string) {
  return useQuery({
    queryKey: ['portal', 'carnet', mascotaId],
    queryFn: async () => (await api.get<Carnet>(`/portal/mascotas/${mascotaId}/carnet`)).data,
  })
}

/** 6.1 Sus contratos, sus carnets y los documentos que el equipo marcó visibles. */
export function useMisDocumentos() {
  return useQuery({
    queryKey: ['portal', 'documentos'],
    queryFn: async () => (await api.get<DocumentoRead[]>('/portal/documentos')).data,
  })
}

/** 6.1 Lo único de sus mascotas que la familia cambia: la foto. */
export function useFotoMascotaPortal(mascotaId: string) {
  const qc = useQueryClient()
  const recargar = () => qc.invalidateQueries({ queryKey: ['portal', 'familia'] })
  const url = `/portal/mascotas/${mascotaId}/foto`
  const subir = useMutation({
    mutationFn: async (foto: File) => {
      const forma = new FormData()
      forma.append('foto', foto)
      return (await api.put<MascotaRead>(url, forma)).data
    },
    onSuccess: recargar,
  })
  const quitar = useMutation({
    mutationFn: async () => (await api.delete<MascotaRead>(url)).data,
    onSuccess: recargar,
  })
  return { subir, quitar }
}

export function useMisPagos() {
  return useQuery({
    queryKey: ['portal', 'pagos'],
    queryFn: async () => (await api.get<PagoPortalRead[]>('/portal/pagos')).data,
  })
}

function useMutacion<T, R>(fn: (datos: T) => Promise<R>) {
  const qc = useQueryClient()
  return useMutation({ mutationFn: fn, onSuccess: () => qc.invalidateQueries({ queryKey: ['portal'] }) })
}

export function useActualizarMisDatos() {
  return useMutacion(
    async (datos: {
      email?: string
      telefono?: string
      barrio?: string
      direccion?: string
      complemento?: string
      ciudad?: string
    }) =>
      (await api.patch<FamiliaRead>('/portal/mi-familia', datos)).data,
  )
}

export function useAgendarPortal() {
  return useMutacion(
    async (datos: { mascota_id: string; tipo_codigo: string; inicio: string; observaciones?: string }) =>
      (await api.post<ServicioPortalRead>('/portal/servicios', datos)).data,
  )
}

export function useReprogramarPortal() {
  return useMutacion(
    async ({ id, ...datos }: { id: string; inicio: string; motivo: string }) =>
      (await api.post<ServicioPortalRead>(`/portal/servicios/${id}/reprogramacion`, datos)).data,
  )
}

export function useCancelarPortal() {
  return useMutacion(
    async ({ id, motivo }: { id: string; motivo: string }) =>
      (await api.post<ServicioPortalRead>(`/portal/servicios/${id}/cancelacion`, { motivo })).data,
  )
}

export function useOrientacionVirtual() {
  return useMutacion(
    async (datos: { mascota_id: string; motivo: string }) =>
      (await api.post<{ id: string; estado: string }>('/portal/orientacion-virtual', datos)).data,
  )
}

export function usePagarPortal() {
  return useMutacion(async (cuotaId?: string) => (await api.post<InicioPago>('/portal/pagos', { cuota_id: cuotaId })).data)
}

export function useCarnetPdfPortal() {
  return useMutacion(
    async (mascotaId: string) => (await api.post<{ codigo: string; url: string }>(`/portal/mascotas/${mascotaId}/carnet/pdf`)).data,
  )
}

export async function urlContrato(): Promise<string> {
  return (await api.get<{ url: string }>('/portal/contrato')).data.url
}

export async function urlAdjuntoPortal(id: string): Promise<string> {
  return (await api.get<{ url: string }>(`/portal/adjuntos/${id}/url`)).data.url
}

/** 6.1 Los planes que se venden en la ciudad de la familia, para el peludo nuevo. */
export function usePlanesAlta() {
  return useQuery({
    queryKey: ['portal', 'peludos', 'planes'],
    queryFn: async () => (await api.get<PlanPublico[]>('/portal/peludos/planes')).data,
  })
}

/** El valor nuevo del contrato y lo que se paga hoy: lo calcula el backend. */
export function useCotizacionAlta(especie: string, planId: string) {
  return useQuery({
    queryKey: ['portal', 'peludos', 'cotizacion', especie, planId],
    enabled: Boolean(especie && planId),
    retry: false,
    queryFn: async () =>
      (await api.post<CotizacionAltaRead>('/portal/peludos/cotizacion', { especie, plan_id: planId })).data,
  })
}

/** Mientras un pago espera a la pasarela, se vuelve a preguntar cada pocos segundos. */
export function useAltasPeludo() {
  return useQuery({
    queryKey: ['portal', 'peludos', 'altas'],
    refetchInterval: (consulta) =>
      consulta.state.data?.some((a) => a.estado === 'pendiente_pago' && a.estado_pago === 'pendiente') ? 5000 : false,
    queryFn: async () => (await api.get<AltaPeludoRead[]>('/portal/peludos/altas')).data,
  })
}

export function useAgregarPeludo() {
  return useMutacion(async (datos: PeludoNuevoIn) => (await api.post<AltaIniciada>('/portal/peludos', datos)).data)
}
