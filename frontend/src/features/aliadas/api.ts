import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/api/client'
import type {
  AtendidasAliada,
  ClinicaRead,
  CoberturaAliada,
  ConvenioRead,
  MiClinica,
  RecuentosRemisiones,
  RemisionRead,
  RemisionVistaAliada,
} from '@/types'

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

export function useRecuentosRemisiones(clinicaId?: string) {
  return useQuery({
    queryKey: ['aliadas', 'remisiones', 'recuentos', clinicaId ?? null],
    queryFn: async () =>
      (await api.get<RecuentosRemisiones>('/aliadas/remisiones/recuentos', { params: { clinica_id: clinicaId } })).data,
  })
}

export function useLiquidacion(desde: string, hasta: string, habilitado: boolean) {
  return useQuery({
    queryKey: ['aliadas', 'liquidacion', desde, hasta],
    enabled: habilitado,
    queryFn: async () => (await api.get<FilaLiquidacion[]>('/aliadas/liquidacion', { params: { desde, hasta } })).data,
  })
}

// --- Espacio de la clínica aliada (R3-ALI-01) ---

/** En qué clínica está quien ingresa. */
export function useMiClinica() {
  return useQuery({
    queryKey: ['aliada', 'clinica'],
    queryFn: async () => (await api.get<MiClinica>('/aliadas/mi-clinica')).data,
  })
}

/** Lo que la clínica atendió en el período, con lo que cubrió TIMU (la API suma). */
export function useAtendidas(desde: string, hasta: string) {
  return useQuery({
    queryKey: ['aliada', 'atendidas', desde, hasta],
    queryFn: async () =>
      (await api.get<AtendidasAliada>('/aliadas/mi-clinica/atendidas', { params: { desde, hasta } })).data,
  })
}

export function useRemisionAliada(codigo: string | null) {
  return useQuery({
    queryKey: ['aliada', 'remision', codigo],
    enabled: Boolean(codigo),
    retry: false,
    queryFn: async () => (await api.get<RemisionVistaAliada>(`/aliadas/mi-clinica/remisiones/${codigo}`)).data,
  })
}

/** Lo que cubre TIMU de un valor y lo que paga la familia, antes de reportar: lo calcula la API
 * con la misma cuenta del reporte. */
export function useCoberturaAliada(codigo: string, valor: string | null) {
  return useQuery({
    queryKey: ['aliada', 'cobertura', codigo, valor],
    enabled: Boolean(valor),
    retry: false,
    placeholderData: (anterior) => anterior,
    queryFn: async () =>
      (
        await api.get<CoberturaAliada>(`/aliadas/mi-clinica/remisiones/${codigo}/cobertura`, {
          params: { valor_atencion: valor },
        })
      ).data,
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

/** `alReportar` corre en el `onSuccess` del hook: el formulario que reporta se desmonta en cuanto la
 * remisión pasa a atendida, y el `onSuccess` de su `mutate` ya no llegaría. */
export function useReportarAtencion(codigo: string, alReportar?: () => void) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (datos: { fecha: string; valor_atencion: string; resumen: string }) =>
      (await api.post<RemisionVistaAliada>(`/aliadas/mi-clinica/remisiones/${codigo}/atencion`, datos)).data,
    // La remisión abierta pasa a «Atendida» con lo que devuelve el reporte, y lo atendido del mes
    // se recarga para sumarla.
    onSuccess: (vista) => {
      alReportar?.()
      qc.setQueryData(['aliada', 'remision', codigo], vista)
      return qc.invalidateQueries({ queryKey: ['aliada', 'atendidas'] })
    },
  })
}
