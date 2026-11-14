import { useParams } from 'react-router-dom'

import { ServiciosPage } from './ServiciosPage'

/** Un servicio abierto: Servicios con sus pestañas, el listado a la izquierda y la ficha a la
 * derecha; en el celular, la ficha. */
export function ServicioDetallePage() {
  const { id = '' } = useParams()
  return <ServiciosPage abierto={id} />
}
