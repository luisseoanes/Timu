import { estadoCuota } from '@/lib/estados'
import type { Tono } from '@/lib/estados'
import type { CuotaRead, PagoPortalRead } from '@/types'

import type { PlanPortal } from './api'

// Los pagos dichos a la familia (R3-POR-02). Cómo se nombran y se ordenan las cuotas es de cartera.

/** Antes de pagar: el pago no se hace en el portal (DEU-77). */
export const PAGO_EN_WOMPI = 'El pago se hace en Wompi, la pasarela de pagos: te llevamos allí y al terminar vuelves aquí.'

/**
 * Con varias cuotas vencidas y el plan en pausa o en mora, pagar una sola no lo cambia: se dice
 * antes de «Pagar esta» (DEU-77), no al volver de la pasarela.
 */
export function avisoPagoParcial(plan: PlanPortal | null | undefined, cuotas: CuotaRead[]): string | null {
  if (cuotas.filter((q) => estadoCuota(q) === 'vencida').length < 2) return null
  if (plan?.estado === 'congelada') return 'Si pagas solo una de tus cuotas vencidas, tu plan sigue en pausa hasta que pagues todas.'
  if (plan?.estado === 'en_mora') return 'Si pagas solo una de tus cuotas vencidas, seguirás sin poder agendar hasta que pagues todas.'
  return null
}

/** Qué le pasó al pago con el que la familia vuelve de la pasarela. */
export function avisoDelPago(pago: PagoPortalRead | undefined): { tono: Tono; texto: string } | null {
  if (!pago) return null
  switch (pago.estado) {
    case 'pendiente':
      return { tono: 'info', texto: 'Estamos esperando que la pasarela confirme tu pago. Esta página se actualiza sola.' }
    case 'aprobado':
      return { tono: 'ok', texto: '¡Listo! Recibimos tu pago.' }
    case 'rechazado':
      return { tono: 'peligro', texto: 'La pasarela no aprobó el pago y no se hizo ningún cobro. Puedes intentarlo de nuevo.' }
    default:
      return { tono: 'alerta', texto: 'Este pago no se completó. Escríbenos por WhatsApp si tienes dudas.' }
  }
}
