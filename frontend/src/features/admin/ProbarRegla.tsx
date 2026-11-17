import { mensajeError } from '@/lib/errores'
import type { ReglaRead } from '@/types'

import { useProbarReglas } from './api'

/** Pone un valor en su ruta con puntos («familia.estado»), como lo lee el motor. */
function conValor(contexto: Record<string, unknown>, ruta: string, valor: unknown): void {
  const partes = ruta.split('.')
  let actual = contexto
  for (const parte of partes.slice(0, -1)) {
    actual[parte] = (actual[parte] as Record<string, unknown> | undefined) ?? {}
    actual = actual[parte] as Record<string, unknown>
  }
  actual[partes.at(-1)!] = valor
}

/** Probar la regla abierta: los datos que mira su condición, cada uno con su nombre, y lo que
 * aplicaría en palabras. Evalúa sin ejecutar nada. */
export function ProbarRegla({ regla: r }: { regla: ReglaRead }) {
  const probar = useProbarReglas()
  return (
    <section className="bloque" aria-labelledby="regla-probar">
      <h3 id="regla-probar">Probar esta regla</h3>
      <p className="admin-nota">Escribe los datos de un caso y mira qué reglas de este evento aplicarían. No se ejecuta nada.</p>
      <form
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const d = new FormData(e.currentTarget)
          const contexto: Record<string, unknown> = {}
          for (const c of r.campos_condicion) {
            const texto = String(d.get(c.campo) ?? '').trim()
            if (texto !== '') conValor(contexto, c.campo, c.numerico ? Number(texto) : texto)
          }
          probar.mutate({ evento: r.evento, contexto })
        }}
      >
        {r.campos_condicion.map((c) => (
          <label key={c.campo} className="campo">
            <span>{c.nombre}</span>
            <input className="input" name={c.campo} type={c.numerico ? 'number' : 'text'} />
          </label>
        ))}
        {r.campos_condicion.length === 0 && <p className="admin-nota ancho">Esta regla aplica siempre: no mira ningún dato.</p>}
        <div className="acciones ancho">
          <button className="btn btn-suave" type="submit" disabled={probar.isPending}>
            {probar.isPending ? 'Probando…' : 'Probar'}
          </button>
        </div>
      </form>
      {probar.isError && (
        <p className="error" role="alert">
          {mensajeError(probar.error, 'No fue posible probar la regla.')}
        </p>
      )}
      {probar.data && (
        <div role="status" className="regla-resultado">
          <p>
            <strong>{probar.data.some((x) => x.regla === r.codigo) ? 'Esta regla aplica.' : 'Esta regla no aplica con estos datos.'}</strong>
          </p>
          {probar.data.length === 0 ? (
            <p className="admin-nota">Ninguna regla de este evento aplicaría.</p>
          ) : (
            <ul className="regla-aplican" aria-label="Reglas que aplicarían">
              {probar.data.map((x) => (
                <li key={x.regla}>
                  <strong>{x.nombre}</strong>
                  <span>{x.accion_texto}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  )
}
