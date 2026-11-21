/**
 * Lo que se ve mientras llega el código de una pantalla (el paquete va partido por espacio y por
 * módulo: la portada no descarga el panel). El mismo esqueleto que una consulta que carga.
 */
export function CargandoPantalla() {
  return (
    <div className="esqueleto" role="status">
      <span className="sr-only">Cargando…</span>
      <span className="esqueleto-linea" aria-hidden="true" />
      <span className="esqueleto-linea" aria-hidden="true" />
      <span className="esqueleto-linea" aria-hidden="true" />
    </div>
  )
}
