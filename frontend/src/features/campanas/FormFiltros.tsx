import { useCiudades, useEspecies, usePlanes } from '@/features/catalogos'
import { mensajeError } from '@/lib/errores'
import type { EstadoAfiliacion } from '@/types'

import { usePrevisualizarSegmento, type FiltrosSegmento } from './api'
import { TIPOS_PREVENTIVO } from './segmento'

const ESTADOS_AFILIACION: { valor: EstadoAfiliacion; label: string }[] = [
  { valor: 'activa', label: 'Activa' },
  { valor: 'en_mora', label: 'En mora' },
  { valor: 'congelada', label: 'Congelada' },
  { valor: 'prospecto', label: 'Prospecto' },
  { valor: 'cancelada', label: 'Cancelada' },
]

/** Filtros de segmento con conteo en vivo de la audiencia. */
export function FormFiltros({ valor, onCambio }: { valor: FiltrosSegmento; onCambio: (f: FiltrosSegmento) => void }) {
  const ciudades = useCiudades()
  const planes = usePlanes()
  const especies = useEspecies()
  const previsualizar = usePrevisualizarSegmento()

  function alternar<K extends 'ciudades' | 'estados' | 'planes' | 'especies' | 'tipos_preventivo'>(
    clave: K,
    item: NonNullable<FiltrosSegmento[K]>[number],
  ) {
    const actual = (valor[clave] ?? []) as string[]
    const nuevo = actual.includes(item) ? actual.filter((x) => x !== item) : [...actual, item]
    onCambio({ ...valor, [clave]: nuevo })
  }
  const numero = (clave: keyof FiltrosSegmento) => (e: React.ChangeEvent<HTMLInputElement>) =>
    onCambio({ ...valor, [clave]: e.target.value ? Number(e.target.value) : undefined })

  return (
    <fieldset className="pila filtros-segmento">
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
      {/* 6.18 Campañas por especie. */}
      <div className="grupo-chips" role="group" aria-label="Especies">
        {especies.data
          ?.filter((e) => e.activa)
          .map((e) => (
            <button key={e.codigo} type="button" className="cupo" aria-pressed={valor.especies?.includes(e.codigo) ?? false} onClick={() => alternar('especies', e.codigo)}>
              {e.nombre}
            </button>
          ))}
      </div>
      <div className="formulario">
        {/* 6.18 Campañas por zona: el barrio de la familia. */}
        <label className="campo ancho">
          <span>Barrios (separados por coma)</span>
          <input
            className="input"
            value={(valor.barrios ?? []).join(', ')}
            placeholder="Chapinero, El Poblado"
            onChange={(e) => {
              const barrios = e.target.value.split(',').map((b) => b.trimStart())
              onCambio({ ...valor, barrios: barrios.some((b) => b.trim()) ? barrios : undefined })
            }}
          />
        </label>
        <label className="campo">
          <span>Mascota de al menos (años)</span>
          <input className="input" type="number" min={0} value={valor.edad_min_anios ?? ''} onChange={numero('edad_min_anios')} />
        </label>
        <label className="campo">
          <span>Mascota de hasta (años)</span>
          <input className="input" type="number" min={0} value={valor.edad_max_anios ?? ''} onChange={numero('edad_max_anios')} />
        </label>
        <label className="campo">
          <span>Afiliadas desde</span>
          <input className="input" type="date" value={valor.afiliada_desde ?? ''} onChange={(e) => onCambio({ ...valor, afiliada_desde: e.target.value || undefined })} />
        </label>
        <label className="campo">
          <span>Afiliadas hasta</span>
          <input className="input" type="date" value={valor.afiliada_hasta ?? ''} onChange={(e) => onCambio({ ...valor, afiliada_hasta: e.target.value || undefined })} />
        </label>
      </div>
      {/* 6.18 Campañas preventivas: alguna mascota con un preventivo vencido o por vencer. */}
      <fieldset className="pila filtros-preventivos">
        <legend className="subtitulo">Preventivos</legend>
        <div className="formulario">
          <label className="acciones">
            <input type="checkbox" checked={valor.preventivo_vencido ?? false} onChange={(e) => onCambio({ ...valor, preventivo_vencido: e.target.checked || undefined })} />
            <span>Con un preventivo vencido</span>
          </label>
          <label className="campo">
            <span>Con un preventivo que vence en (días)</span>
            <input className="input" type="number" min={1} value={valor.preventivo_en_dias ?? ''} onChange={numero('preventivo_en_dias')} />
          </label>
        </div>
        <div className="grupo-chips" role="group" aria-label="Tipos de preventivo">
          {TIPOS_PREVENTIVO.map((t) => (
            <button key={t.valor} type="button" className="cupo" aria-pressed={valor.tipos_preventivo?.includes(t.valor) ?? false} onClick={() => alternar('tipos_preventivo', t.valor)}>
              {t.label}
            </button>
          ))}
        </div>
      </fieldset>
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
