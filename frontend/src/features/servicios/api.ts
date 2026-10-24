import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/api/client'
import type {
  CupoRead,
  ElegibilidadRead,
  EstadoServicio,
  FranjaRead,
  Page,
  PasoRead,
  PendienteRead,
  ServicioRead,
} from '@/types'

export interface FiltrosServicios {
  familia_id?: string
  estado?: EstadoServicio
  ciudad?: string
  desde?: string
  hasta?: string
  limit?: number
  offset?: number
  orden?: string
}

export interface NuevoServicio {
  familia_id: string
  mascota_id?: string
  tipo_codigo: string
  inicio: string
  observaciones?: string
  pendiente_id?: string
}

/** Grafo de la máquina de estados (backend: servicios/state_machine.py). Sólo para decidir
 * qué botones ofrecer; quien valida la transición es el backend. */
export const TRANSICIONES: Record<EstadoServicio, EstadoServicio[]> = {
  solicitado: ['agendado', 'pendiente_autorizacion', 'cancelado'],
  pendiente_autorizacion: ['agendado', 'cancelado'],
  agendado: ['en_ruta', 'en_atencion', 'reprogramado', 'cancelado'],
  en_ruta: ['en_atencion', 'reprogramado', 'cancelado'],
  en_atencion: ['completado', 'cancelado'],
  reprogramado: ['agendado', 'cancelado'],
  completado: [],
  cancelado: [],
}

export function useServicios(filtros: FiltrosServicios) {
  return useQuery({
    queryKey: ['servicios', filtros],
    queryFn: async () => (await api.get<Page<ServicioRead>>('/servicios', { params: filtros })).data,
  })
}

export function useServicio(id: string) {
  return useQuery({
    queryKey: ['servicios', id],
    queryFn: async () => (await api.get<ServicioRead>(`/servicios/${id}`)).data,
  })
}

export function usePasos(id: string) {
  return useQuery({
    queryKey: ['servicios', id, 'pasos'],
    queryFn: async () => (await api.get<PasoRead[]>(`/servicios/${id}/pasos`)).data,
  })
}

export function usePendientes(filtros: { estado?: string; servicio_id?: string } = {}) {
  return useQuery({
    queryKey: ['pendientes', filtros],
    queryFn: async () => (await api.get<PendienteRead[]>('/pendientes', { params: filtros })).data,
  })
}

export function useElegibilidad(params: { familia_id: string; tipo_codigo: string; mascota_id?: string } | null) {
  return useQuery({
    queryKey: ['servicios', 'elegibilidad', params],
    enabled: Boolean(params?.familia_id && params.tipo_codigo),
    queryFn: async () => (await api.get<ElegibilidadRead>('/servicios/elegibilidad', { params })).data,
  })
}

export function useDisponibilidad(params: { fecha: string; ciudad: string; tipo_codigo: string } | null) {
  return useQuery({
    queryKey: ['agenda', 'disponibilidad', params],
    enabled: Boolean(params?.fecha && params.ciudad && params.tipo_codigo),
    queryFn: async () => (await api.get<CupoRead[]>('/agenda/disponibilidad', { params })).data,
  })
}

export function useFranjas(ciudad?: string) {
  return useQuery({
    queryKey: ['agenda', 'franjas', ciudad ?? null],
    queryFn: async () => (await api.get<FranjaRead[]>('/agenda/franjas', { params: { ciudad } })).data,
  })
}

/** Toda escritura de servicios refresca servicios, pendientes y agenda: se afectan entre sí. */
function useInvalidar() {
  const qc = useQueryClient()
  return () => {
    void qc.invalidateQueries({ queryKey: ['servicios'] })
    void qc.invalidateQueries({ queryKey: ['pendientes'] })
    void qc.invalidateQueries({ queryKey: ['agenda'] })
  }
}

export function useCrearServicio() {
  const invalidar = useInvalidar()
  return useMutation({
    mutationFn: async (datos: NuevoServicio) => (await api.post<ServicioRead>('/servicios', datos)).data,
    onSuccess: invalidar,
  })
}

export function useCambiarEstadoServicio(id: string) {
  const invalidar = useInvalidar()
  return useMutation({
    mutationFn: async (datos: { estado: EstadoServicio; motivo?: string }) =>
      (await api.post<ServicioRead>(`/servicios/${id}/estado`, datos)).data,
    onSuccess: invalidar,
  })
}

export function useReprogramar(id: string) {
  const invalidar = useInvalidar()
  return useMutation({
    mutationFn: async (datos: { inicio: string; motivo: string }) =>
      (await api.post<ServicioRead>(`/servicios/${id}/reprogramar`, datos)).data,
    onSuccess: invalidar,
  })
}

export function useAutorizar(id: string) {
  const invalidar = useInvalidar()
  return useMutation({
    mutationFn: async () => (await api.post<ServicioRead>(`/servicios/${id}/autorizar`)).data,
    onSuccess: invalidar,
  })
}

export function useCompletarPaso(id: string) {
  const invalidar = useInvalidar()
  return useMutation({
    mutationFn: async ({ paso, datos }: { paso: string; datos: Record<string, string> }) =>
      (await api.put<PasoRead>(`/servicios/${id}/pasos/${paso}`, { datos })).data,
    onSuccess: invalidar,
  })
}

export function useCrearPendiente(id: string) {
  const invalidar = useInvalidar()
  return useMutation({
    mutationFn: async (datos: { descripcion: string; requiere_autorizacion: boolean }) =>
      (await api.post<PendienteRead>(`/servicios/${id}/pendientes`, datos)).data,
    onSuccess: invalidar,
  })
}

export function useAutorizarPendiente() {
  const invalidar = useInvalidar()
  return useMutation({
    mutationFn: async ({ id, aprobado, medio }: { id: string; aprobado: boolean; medio: string }) =>
      (await api.post<PendienteRead>(`/pendientes/${id}/autorizacion`, { aprobado, medio })).data,
    onSuccess: invalidar,
  })
}

export function useAvancePendiente() {
  const invalidar = useInvalidar()
  return useMutation({
    mutationFn: async ({ id, estado, resolucion }: { id: string; estado: 'en_gestion' | 'resuelto'; resolucion?: string }) =>
      (await api.post<PendienteRead>(`/pendientes/${id}/avance`, { estado, resolucion })).data,
    onSuccess: invalidar,
  })
}

export function useCrearFranja() {
  const invalidar = useInvalidar()
  return useMutation({
    mutationFn: async (datos: Omit<FranjaRead, 'id' | 'activa'>) =>
      (await api.post<FranjaRead>('/agenda/franjas', datos)).data,
    onSuccess: invalidar,
  })
}

export function useActualizarFranja() {
  const invalidar = useInvalidar()
  return useMutation({
    mutationFn: async ({ id, ...params }: { id: string; capacidad?: number; activa?: boolean }) =>
      (await api.patch<FranjaRead>(`/agenda/franjas/${id}`, null, { params })).data,
    onSuccess: invalidar,
  })
}

export function useCrearBloqueo() {
  const invalidar = useInvalidar()
  return useMutation({
    mutationFn: async (datos: { fecha: string; ciudad?: string; modalidad?: string; motivo: string }) =>
      (await api.post('/agenda/bloqueos', datos)).data,
    onSuccess: invalidar,
  })
}
