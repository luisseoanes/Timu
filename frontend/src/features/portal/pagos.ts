import type { Tono } from '@/lib/estados'
import type { PagoPortalRead } from '@/types'

// Los pagos dichos a la familia (R3-POR-02). Cómo se nombran y se ordenan las cuotas es de cartera.

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
