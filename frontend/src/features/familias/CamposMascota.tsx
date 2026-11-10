import { useId } from 'react'

import { hoyISO } from '@/lib/formato'

import { AYUDA_FECHA } from './mascota'

/**
 * Fecha de nacimiento, peso y esterilización de una mascota. La fecha y el peso son
 * obligatorios en el panel (6.1); la fecha puede ser aproximada.
 */
export function CamposMascota({
  prefijo = '',
  valores,
}: {
  prefijo?: string
  valores?: { fecha_nacimiento?: string | null; peso_kg?: number | null; esterilizada?: boolean | null }
}) {
  const id = useId()
  const esterilizada = valores?.esterilizada === true ? 'si' : valores?.esterilizada === false ? 'no' : ''
  return (
    <>
      <div className="campo">
        <label htmlFor={`${id}-fecha`}>Fecha de nacimiento</label>
        <input
          id={`${id}-fecha`}
          className="input"
          name={`${prefijo}fecha_nacimiento`}
          type="date"
          required
          max={hoyISO()}
          defaultValue={valores?.fecha_nacimiento ?? ''}
          aria-describedby={`${id}-ayuda`}
        />
        <small id={`${id}-ayuda`} className="campo-ayuda">
          {AYUDA_FECHA}
        </small>
      </div>
      <label className="campo">
        <span>Peso (kg)</span>
        <input
          className="input"
          name={`${prefijo}peso_kg`}
          type="number"
          inputMode="decimal"
          required
          min={0.1}
          max={149.9}
          step={0.1}
          defaultValue={valores?.peso_kg ?? ''}
        />
      </label>
      <label className="campo">
        <span>Esterilizada (opcional)</span>
        <select className="input" name={`${prefijo}esterilizada`} defaultValue={esterilizada}>
          <option value="">Sin dato</option>
          <option value="si">Sí</option>
          <option value="no">No</option>
        </select>
      </label>
    </>
  )
}
