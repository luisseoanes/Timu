import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/api/client'
import type { ClinicaRead, ConvenioRead, RemisionRead } from '@/types'

export interface FilaLiquidacion {
  clinica_id: string
  clinica: string
  nit: string | null
  atenciones: number
  valor_atenciones: string
  valor_cubierto: string
  valor_familias: string
  detalle: { codigo: string; fecha_atencion: string; beneficio: string | null; valor_atencion: string; valor_cubierto: string }[]
}

/** Lo que ve la clínica aliada al validar un código (aliadas/service.py: `vista_aliada`). */
export interface RemisionAliada {
  codigo: string
  estado: string
  vigente: boolean
  vence_en: string
  titular: string
  documento_ultimos: string
  mascota: { nombre: string; especie: string; raza: string | null }
  motivo: string
  beneficio: string | null
  cobertura_pct: number
  tope_cubierto: string | null
  valor_cubierto: string | null
}

export function useClinicas(ciudad?: string, incluirInactivas = false) {
  return useQuery({
    queryKey: ['aliadas', 'clinicas', ciudad ?? null, incluirInactivas],
    queryFn: async () =>
      (await api.get<ClinicaRead[]>('/aliadas', { params: { ciudad, incluir_inactivas: incluirInactivas || undefined } })).data,
  })
}

export function useConvenios(clinicaId: string | null) {
  return useQuery({
    queryKey: ['aliadas', 'convenios', clinicaId],
    enabled: Boolean(clinicaId),
    queryFn: async () => (await api.get<ConvenioRead[]>(`/aliadas/${clinicaId}/convenios`)).data,
  })
}

export function useRemisiones(filtros: { clinica_id?: string; familia_id?: string; estado?: string }) {
  return useQuery({
    queryKey: ['aliadas', 'remisiones', filtros],
    queryFn: async () => (await api.get<RemisionRead[]>('/aliadas/remisiones', { params: filtros })).data,
  })
}

export function useLiquidacion(desde: string, hasta: string, habilitado: boolean) {
  return useQuery({
    queryKey: ['aliadas', 'liquidacion', desde, hasta],
    enabled: habilitado,
    queryFn: async () => (await api.get<FilaLiquidacion[]>('/aliadas/liquidacion', { params: { desde, hasta } })).data,
  })
}

export function useRemisionAliada(codigo: string | null) {
  return useQuery({
    queryKey: ['aliada', 'remision', codigo],
    enabled: Boolean(codigo),
    retry: false,
    queryFn: async () => (await api.get<RemisionAliada>(`/aliadas/mi-clinica/remisiones/${codigo}`)).data,
  })
}

function useMutacion<T, R>(fn: (datos: T) => Promise<R>, clave: string) {
  const qc = useQueryClient()
  return useMutation({ mutationFn: fn, onSuccess: () => qc.invalidateQueries({ queryKey: [clave] }) })
}

export function useCrearClinica() {
  return useMutacion(
    async (datos: Omit<ClinicaRead, 'id' | 'activa'>) => (await api.post<ClinicaRead>('/aliadas', datos)).data,
    'aliadas',
  )
}

export function useActualizarClinica() {
  return useMutacion(
    async ({ id, ...datos }: { id: string; activa?: boolean; telefono?: string; email?: string; servicios?: string }) =>
      (await api.patch<ClinicaRead>(`/aliadas/${id}`, datos)).data,
    'aliadas',
  )
}

export function useCrearConvenio() {
  return useMutacion(
    async ({ clinicaId, ...datos }: { clinicaId: string; beneficio: string; cobertura_pct: number; tarifa: string; tope_cubierto?: string; vigente_desde: string; plan_id?: string }) =>
      (await api.post<ConvenioRead>(`/aliadas/${clinicaId}/convenios`, datos)).data,
    'aliadas',
  )
}

export function useEmitirRemision() {
  return useMutacion(
    async (datos: { clinica_id: string; mascota_id: string; motivo: string; convenio_id?: string }) =>
      (await api.post<RemisionRead>('/aliadas/remisiones', datos)).data,
    'aliadas',
  )
}

export function useAnularRemision() {
  return useMutacion(
    async ({ id, motivo }: { id: string; motivo: string }) =>
      (await api.post<RemisionRead>(`/aliadas/remisiones/${id}/anulacion`, { motivo })).data,
    'aliadas',
  )
}

export function useReportarAtencion(codigo: string) {
  return useMutacion(
    async (datos: { fecha: string; valor_atencion: string; resumen: string }) =>
      (await api.post<RemisionAliada>(`/aliadas/mi-clinica/remisiones/${codigo}/atencion`, datos)).data,
    'aliada',
  )
}
