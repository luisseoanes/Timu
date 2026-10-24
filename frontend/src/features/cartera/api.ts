import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/api/client'
import type { ContratoListado, Page, PagoRead } from '@/types'

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
