import { fechaCorta, hoyISO } from '@/lib/formato'
import type { ColorPlan, EstacionRead } from '@/types'

import { esHoy, esTramo, recorrido, resumen } from './linea'

/** Color de la línea: el del plan o gris si la familia no tiene. */
type ColorLinea = ColorPlan | 'ninguno'

/** La línea en miniatura de una fila del listado: dibujo para quien ve, resumen para quien no. */
export function LineaMini({ estaciones, color = 'ninguno' }: { estaciones: EstacionRead[]; color?: ColorLinea }) {
  const elementos = recorrido(estaciones, hoyISO())
  return (
    <span className="linea-mini" data-color={color} role="img" aria-label={resumen(estaciones, fechaCorta)}>
      {elementos.map((el, i) =>
        esHoy(el) ? (
          <span key="hoy" className="linea-mini-hoy" />
        ) : esTramo(el) ? (
          <span key="tramo" className="linea-mini-punto" data-estado="hecha" />
        ) : (
          <span key={`${el.fecha}-${i}`} className="linea-mini-punto" data-estado={el.estado} />
        ),
      )}
    </span>
  )
}
