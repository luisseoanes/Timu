import { usePlanes } from '@/features/catalogos'
import { moneda } from '@/lib/formato'

import { planesPara } from './mascota'

/**
 * Plan de un peludo: solo los que se venden en la ciudad de la familia y cubren su especie,
 * con el precio de lista (la tarifa de un peludo; con más, cada uno paga menos).
 */
export function ElegirPlan({
  etiqueta,
  ciudad,
  especie,
  valor,
  onCambio,
  name,
}: {
  etiqueta: string
  ciudad: string
  especie: string
  valor?: string
  onCambio?: (planId: string) => void
  name?: string
}) {
  const planes = usePlanes()
  const disponibles = planesPara(planes.data, ciudad, especie)
  return (
    <label className="campo">
      <span>{etiqueta}</span>
      <select
        className="input"
        name={name}
        required
        value={onCambio ? (valor ?? '') : undefined}
        defaultValue={onCambio ? undefined : (valor ?? '')}
        onChange={onCambio ? (e) => onCambio(e.target.value) : undefined}
        disabled={planes.isPending}
      >
        <option value="" disabled>
          {planes.isPending ? 'Cargando planes…' : disponibles.length ? 'Elige el plan' : `Sin planes en ${ciudad}`}
        </option>
        {disponibles.map((p) => (
          <option key={p.id} value={p.id}>
            {p.nombre} · desde {moneda(p.tarifas.find((t) => t.peludos === 1)?.valor)} al mes
          </option>
        ))}
      </select>
    </label>
  )
}
