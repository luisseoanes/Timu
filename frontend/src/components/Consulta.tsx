import type { UseQueryResult } from '@tanstack/react-query'
import type { ReactNode } from 'react'

import { mensajeError } from '@/lib/errores'

/**
 * Las tres pantallas obligatorias de toda consulta (docs/frontend/conventions.md):
 * cargando, error y vacío. Con datos, entrega el contenido.
 */
export function Consulta<T>({
  consulta,
  cargando,
  error,
  vacio,
  estaVacio,
  children,
}: {
  consulta: UseQueryResult<T>
  /** Qué se está cargando: `Cargando servicios…` */
  cargando: string
  /** Qué no se pudo cargar: se completa con la causa que da el servidor. */
  error: string
  /** Por qué no hay nada, dicho desde quien usa el sistema. */
  vacio?: string
  estaVacio?: (datos: T) => boolean
  children: (datos: T) => ReactNode
}) {
  if (consulta.isPending) return <p className="apagado">{cargando}</p>
  if (consulta.isError) {
    return (
      <p className="error" role="alert">
        {error} {mensajeError(consulta.error, 'Intenta de nuevo en un momento.')}
      </p>
    )
  }
  if (vacio && estaVacio?.(consulta.data)) return <p className="apagado">{vacio}</p>
  return <>{children(consulta.data)}</>
}
