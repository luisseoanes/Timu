import type { MensajeRead } from '@/types'

import { diaISO, fechaCompacta, fechaHora, hora } from '@/lib/formato'

/**
 * Un mensaje de una conversación de WhatsApp: lo que escribió la persona a la izquierda, lo que le
 * escribimos a la derecha (`.comercial-mensaje`). Va dentro de una lista `.comercial-mensajes`.
 * `destacado` marca el mensaje desde el que se abrió la conversación.
 */
export function BurbujaMensaje({
  mensaje: m,
  nombrePlantilla = (codigo) => codigo,
  destacado = false,
}: {
  mensaje: MensajeRead
  nombrePlantilla?: (codigo: string) => string
  destacado?: boolean
}) {
  const entrante = m.direccion === 'entrante'
  return (
    <li className="comercial-mensaje" data-direccion={m.direccion} data-destacado={destacado || undefined} aria-current={destacado || undefined}>
      <span className="sr-only">{entrante ? 'Escribió:' : 'Le escribimos:'}</span>
      <p>{m.contenido ?? (m.plantilla ? `Plantilla «${nombrePlantilla(m.plantilla)}»` : '—')}</p>
      <span className="comercial-mensaje-hora numero" title={fechaHora(m.created_at)}>
        {fechaCompacta(diaISO(m.created_at))} · {hora(m.created_at)}
        {m.estado === 'fallido' && ' · no se envió'}
      </span>
    </li>
  )
}
