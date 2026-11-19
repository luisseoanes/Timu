import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/api/client'
import type {
  ContratoListado,
  ContratoRead,
  EstadoCuenta,
  EventoPasarelaRead,
  Page,
  PagoRead,
  RecuentosCartera,
  RecuentosEventosPasarela,
} from '@/types'

export type MedioPago = 'efectivo' | 'transferencia' | 'consignacion' | 'datafono' | 'otro'

export interface PagoManual {
  familia_id: string
  valor: string
  medio: MedioPago
  referencia: string
  fecha_pago?: string
  cuota_id?: string
  notas?: string
}

export interface FiltrosCartera {
  estado?: string
  ciudad?: string
  q?: string
  solo_mora?: boolean
  por_renovar?: boolean
  limit?: number
  offset?: number
}

export function useContratos(filtros: FiltrosCartera = {}) {
  return useQuery({
    queryKey: ['cartera', 'contratos', filtros],
    queryFn: async () =>
      (await api.get<Page<ContratoListado>>('/cartera/contratos', { params: filtros })).data,
  })
}

/** Cuántos contratos hay en cada vista de la bandeja, con los mismos filtros. */
export function useRecuentosCartera(filtros: Pick<FiltrosCartera, 'ciudad' | 'q'>) {
  return useQuery({
    queryKey: ['cartera', 'recuentos', filtros],
    queryFn: async () => (await api.get<RecuentosCartera>('/cartera/contratos/recuentos', { params: filtros })).data,
  })
}

/** Renovar extiende un año la vigencia del contrato (6.4). */
export function useRenovarContrato() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (contratoId: string) => (await api.post<ContratoRead>(`/cartera/contratos/${contratoId}/renovar`)).data,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['cartera'] })
      void qc.invalidateQueries({ queryKey: ['familias'] })
    },
  })
}

/** El estado de cuenta responde 404 cuando la familia aún no tiene contrato: no es un error. */
export function useEstadoCuenta(familiaId: string, habilitado = true) {
  return useQuery({
    queryKey: ['cartera', 'estado-cuenta', familiaId],
    enabled: habilitado,
    queryFn: async () => {
      const { data, status } = await api.get<EstadoCuenta>(
        `/cartera/familias/${familiaId}/estado-cuenta`,
        { validateStatus: (s) => s === 200 || s === 404 },
      )
      return status === 404 ? null : data
    },
  })
}

/** Un pago cambia el saldo y puede reactivar la familia: se refrescan ambos. */
export function useRegistrarPago() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (pago: PagoManual) => (await api.post<PagoRead>('/cartera/pagos', pago)).data,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['cartera'] })
      void qc.invalidateQueries({ queryKey: ['familias'] })
    },
  })
}

// --- Eventos de la pasarela de pagos: los revisa Atención al cliente (6.2) --------------------

export function useRecuentosEventosPasarela() {
  return useQuery({
    queryKey: ['pasarela', 'recuentos'],
    queryFn: async () => (await api.get<RecuentosEventosPasarela>('/cartera/eventos-pasarela/recuentos')).data,
  })
}

export function useEventosPasarela(estado?: string) {
  return useQuery({
    queryKey: ['pasarela', estado ?? null],
    queryFn: async () =>
      (await api.get<Page<EventoPasarelaRead>>('/cartera/eventos-pasarela', { params: { estado, limit: 50, orden: '-created_at' } })).data,
  })
}

export function useReprocesarEvento() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => (await api.post<EventoPasarelaRead>(`/cartera/eventos-pasarela/${id}/reprocesar`)).data,
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['pasarela'] }),
  })
}
