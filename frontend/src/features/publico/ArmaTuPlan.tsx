import { useId } from 'react'
import { Link } from 'react-router-dom'

import { Icono } from '@/components/Icono'
import { moneda } from '@/lib/formato'
import type { PlanPublico } from '@/types'

import { desdeMensual, enlaceAfiliacion } from './portada'
import { useCiudadesRegistro } from './registro'

const MAX_POR_ESPECIE = 10

export interface Manada {
  ciudad: string
  perros: number
  gatos: number
}

/** Un contador de − y +: cuántos perros o gatos tiene la familia. */
function Contador({ etiqueta, valor, minimo, onCambio }: { etiqueta: string; valor: number; minimo: number; onCambio: (n: number) => void }) {
  const id = useId()
  return (
    <div className="campo arma-contador" role="group" aria-labelledby={id}>
      <span id={id} className="arma-contador-etiqueta">
        {etiqueta}
      </span>
      <div className="arma-contador-control">
        <button type="button" className="btn btn-plano btn-icono" aria-label={`Un ${etiqueta.toLowerCase().slice(0, -1)} menos`} disabled={valor <= minimo} onClick={() => onCambio(valor - 1)}>
          <Icono nombre="menos" size={18} />
        </button>
        <output className="numero" aria-live="polite">
          {valor}
        </output>
        <button
          type="button"
          className="btn btn-plano btn-icono"
          aria-label={`Un ${etiqueta.toLowerCase().slice(0, -1)} más`}
          disabled={valor >= MAX_POR_ESPECIE}
          onClick={() => onCambio(valor + 1)}
        >
          <Icono nombre="mas" size={18} />
        </button>
      </div>
    </div>
  )
}

/**
 * «Arma tu plan» (R3-PUB-04): la familia dice dónde vive y cuántos peludos tiene, y ve lo menos que
 * paga cada uno al mes con el precio que da la API (por peludo, baja con cuantos más). «Ver mis
 * planes» abre la afiliación con eso ya elegido. Es el único verde lleno de la portada.
 */
export function ArmaTuPlan({
  manada,
  planes,
  cargando,
  onCambio,
}: {
  manada: Manada
  planes: PlanPublico[]
  cargando: boolean
  onCambio: (m: Manada) => void
}) {
  const ciudades = useCiudadesRegistro()
  const total = manada.perros + manada.gatos
  const desde = desdeMensual(planes, total)
  return (
    <form className="arma" aria-labelledby="arma-titulo" onSubmit={(e) => e.preventDefault()}>
      <h2 id="arma-titulo" className="arma-titulo">
        Arma tu plan
      </h2>
      <div className="campo">
        <label htmlFor="arma-ciudad">¿Dónde vives?</label>
        <select
          id="arma-ciudad"
          className="input"
          value={manada.ciudad}
          disabled={ciudades.isPending}
          onChange={(e) => onCambio({ ...manada, ciudad: e.target.value })}
        >
          {ciudades.isPending && <option value="">Cargando ciudades…</option>}
          {ciudades.data?.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>
      <div className="arma-contadores">
        <Contador etiqueta="Perros" valor={manada.perros} minimo={manada.gatos ? 0 : 1} onCambio={(perros) => onCambio({ ...manada, perros })} />
        <Contador etiqueta="Gatos" valor={manada.gatos} minimo={manada.perros ? 0 : 1} onCambio={(gatos) => onCambio({ ...manada, gatos })} />
      </div>
      <div className="arma-cierre">
        <p className="arma-precio" aria-live="polite">
          {cargando ? (
            'Calculando…'
          ) : desde ? (
            <>
              {total === 1 ? 'Tu peludo, desde' : `${total} peludos, desde`}
              <strong className="numero">{moneda(desde)}</strong>
              {total === 1 ? 'al mes' : 'al mes cada uno'}
            </>
          ) : (
            'Aún no vendemos planes en esta ciudad.'
          )}
        </p>
        <Link className="btn btn-primario arma-ir" to={enlaceAfiliacion({ ciudad: manada.ciudad, perros: manada.perros, gatos: manada.gatos })}>
          Ver mis planes
        </Link>
      </div>
    </form>
  )
}
