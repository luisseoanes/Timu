import type { UseQueryResult } from '@tanstack/react-query'
import type { ReactNode } from 'react'

import { esErrorPasajero, mensajeError } from '@/lib/errores'

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
  if (consulta.isPending) {
    // Esqueleto en vez de un texto suelto; el texto queda para el lector de pantalla.
    return (
      <div className="esqueleto" role="status">
        <span className="sr-only">{cargando}</span>
        <span className="esqueleto-linea" aria-hidden="true" />
        <span className="esqueleto-linea" aria-hidden="true" />
        <span className="esqueleto-linea" aria-hidden="true" />
      </div>
    )
  }
  if (consulta.isError) {
    // «Reintentar» solo cuando el fallo es pasajero: ante un permiso o un dato inválido,
    // repetir la petición da el mismo error y el botón engañaría.
    return (
      <div className="aviso-error consulta-error" role="alert">
        <p>
          {error} {mensajeError(consulta.error, 'Intenta de nuevo en un momento.')}
        </p>
        {esErrorPasajero(consulta.error) && (
          <button className="btn btn-secundario" type="button" onClick={() => void consulta.refetch()}>
            Reintentar
          </button>
        )}
      </div>
    )
  }
  if (vacio && estaVacio?.(consulta.data)) return <p className="apagado">{vacio}</p>
  return <>{children(consulta.data)}</>
}
