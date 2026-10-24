/** Paginación por desplazamiento, para los listados que devuelven `Page<T>`. */
export function Paginacion({
  total,
  limit,
  offset,
  onCambio,
}: {
  total: number
  limit: number
  offset: number
  onCambio: (offset: number) => void
}) {
  if (total <= limit) return null
  const desde = offset + 1
  const hasta = Math.min(offset + limit, total)
  return (
    <nav className="paginacion" aria-label="Paginación">
      <span className="numero">
        {desde}–{hasta} de {total}
      </span>
      <button
        className="btn btn-plano"
        type="button"
        disabled={offset === 0}
        onClick={() => onCambio(Math.max(0, offset - limit))}
      >
        Anterior
      </button>
      <button
        className="btn btn-plano"
        type="button"
        disabled={hasta >= total}
        onClick={() => onCambio(offset + limit)}
      >
        Siguiente
      </button>
    </nav>
  )
}
