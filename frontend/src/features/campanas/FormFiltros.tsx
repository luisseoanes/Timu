import { useCiudades, usePlanes } from '@/features/catalogos'
import { mensajeError } from '@/lib/errores'

import { usePrevisualizarSegmento, type FiltrosSegmento } from './api'
import { ESTADOS_AFILIACION } from './segmento'

/** Filtros de segmento con conteo en vivo de la audiencia. */
export function FormFiltros({ valor, onCambio }: { valor: FiltrosSegmento; onCambio: (f: FiltrosSegmento) => void }) {
  const ciudades = useCiudades()
  const planes = usePlanes()
  const previsualizar = usePrevisualizarSegmento()

  function alternar<K extends 'ciudades' | 'estados' | 'planes'>(clave: K, item: NonNullable<FiltrosSegmento[K]>[number]) {
    const actual = (valor[clave] ?? []) as string[]
    const nuevo = actual.includes(item) ? actual.filter((x) => x !== item) : [...actual, item]
    onCambio({ ...valor, [clave]: nuevo })
  }
  const numero = (clave: keyof FiltrosSegmento) => (e: React.ChangeEvent<HTMLInputElement>) =>
    onCambio({ ...valor, [clave]: e.target.value ? Number(e.target.value) : undefined })

  return (
    <fieldset className="pila" style={{ border: 0, margin: 0, padding: 0 }}>
      <legend className="subtitulo">Quiénes reciben</legend>
      <div className="grupo-chips" role="group" aria-label="Estados de afiliación">
        {ESTADOS_AFILIACION.map((e) => (
          <button key={e.valor} type="button" className="cupo" aria-pressed={valor.estados?.includes(e.valor) ?? false} onClick={() => alternar('estados', e.valor)}>
            {e.label}
          </button>
        ))}
      </div>
      <div className="grupo-chips" role="group" aria-label="Ciudades">
        {ciudades.data?.slice(0, 12).map((c) => (
          <button key={c.codigo} type="button" className="cupo" aria-pressed={valor.ciudades?.includes(c.nombre) ?? false} onClick={() => alternar('ciudades', c.nombre)}>
            {c.nombre}
          </button>
        ))}
      </div>
      <div className="grupo-chips" role="group" aria-label="Planes">
        {planes.data?.map((p) => (
          <button key={p.id} type="button" className="cupo" aria-pressed={valor.planes?.includes(p.codigo) ?? false} onClick={() => alternar('planes', p.codigo)}>
            {p.nombre}
          </button>
        ))}
      </div>
      <div className="formulario">
        <label className="campo">
          <span>Días de mora mínimos</span>
          <input className="input" type="number" min={0} value={valor.dias_mora_min ?? ''} onChange={numero('dias_mora_min')} />
        </label>
        <label className="campo">
          <span>Sin servicio hace (días)</span>
          <input className="input" type="number" min={0} value={valor.sin_servicio_dias ?? ''} onChange={numero('sin_servicio_dias')} />
        </label>
        <label className="campo">
          <span>Renuevan en (días)</span>
          <input className="input" type="number" min={0} value={valor.renovacion_en_dias ?? ''} onChange={numero('renovacion_en_dias')} />
        </label>
        <label className="campo">
          <span>Mascotas mínimas</span>
          <input className="input" type="number" min={1} value={valor.mascotas_min ?? ''} onChange={numero('mascotas_min')} />
        </label>
      </div>
      <div className="acciones">
        <button className="btn btn-suave" type="button" disabled={previsualizar.isPending} onClick={() => previsualizar.mutate(valor)}>
          Contar audiencia
        </button>
        {previsualizar.data && (
          <span role="status">
            <strong className="numero">{previsualizar.data.total}</strong> familias
            {previsualizar.data.muestra.length > 0 && (
              <span className="apagado"> · {previsualizar.data.muestra.slice(0, 3).map((m) => m.titular).join(', ')}…</span>
            )}
          </span>
        )}
        {previsualizar.isError && (
          <span className="error" role="alert">
            {mensajeError(previsualizar.error, 'No fue posible contar.')}
          </span>
        )}
      </div>
    </fieldset>
  )
}
