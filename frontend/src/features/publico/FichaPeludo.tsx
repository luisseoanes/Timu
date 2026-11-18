import { useId, useState } from 'react'

import { Icono } from '@/components/Icono'
import { moneda } from '@/lib/formato'
import type { PlanPublico } from '@/types'

import { Comparador } from './Comparador'
import { ESPECIES_REGISTRO, planesPara, tarifaCon, type PeludoRegistro } from './registro'

/**
 * Un peludo de la manada (R3-PUB-02): su nombre, su especie y su plan. Los planes son pastillas
 * en su color; el elegido se abre con todo lo que cubre y sus condiciones, de frente, y
 * «Comparar los planes» pone las mismas filas de los planes lado a lado.
 */
export function FichaPeludo({
  indice,
  peludo,
  planes,
  totalPeludos,
  nombreRepetido,
  onCambio,
  onQuitar,
}: {
  indice: number
  peludo: PeludoRegistro
  planes: PlanPublico[]
  totalPeludos: number
  nombreRepetido: boolean
  onCambio: (cambio: Partial<PeludoRegistro>) => void
  onQuitar?: () => void
}) {
  const id = useId()
  const [comparando, setComparando] = useState(false)
  const disponibles = planesPara(planes, peludo.especie)
  const elegido = disponibles.find((p) => p.id === peludo.plan_id)
  const nombre = peludo.nombre.trim() || `Peludo ${indice + 1}`
  const especie = ESPECIES_REGISTRO.find((e) => e.codigo === peludo.especie)?.nombre

  return (
    <section className="registro-ficha" aria-labelledby={`${id}-titulo`}>
      <header className="registro-ficha-cabeza">
        <h2 id={`${id}-titulo`}>
          {nombre}
          {especie && <span className="registro-ficha-especie"> · {especie}</span>}
        </h2>
        {onQuitar && (
          <button className="btn btn-plano" type="button" onClick={onQuitar}>
            Quitar a {nombre}
          </button>
        )}
      </header>

      <div className="registro-ficha-datos">
        <div className="campo">
          <label htmlFor={`${id}-nombre`}>Nombre</label>
          <input
            id={`${id}-nombre`}
            className="input"
            value={peludo.nombre}
            onChange={(e) => onCambio({ nombre: e.target.value })}
            required
            maxLength={120}
            autoComplete="off"
            aria-invalid={nombreRepetido || undefined}
            aria-describedby={nombreRepetido ? `${id}-repetido` : undefined}
          />
          {nombreRepetido && (
            <span id={`${id}-repetido`} className="error">
              Otro peludo ya se llama así: cada uno necesita su nombre.
            </span>
          )}
        </div>
        <fieldset className="registro-especie">
          <legend>Es</legend>
          {ESPECIES_REGISTRO.map((e) => (
            <label key={e.codigo} className="registro-segmento">
              <input
                type="radio"
                name={`${id}-especie`}
                value={e.codigo}
                checked={peludo.especie === e.codigo}
                onChange={() => onCambio({ especie: e.codigo, plan_id: '' })}
              />
              <span>{e.nombre}</span>
            </label>
          ))}
        </fieldset>
      </div>

      <fieldset className="registro-planes">
        <legend>Su plan</legend>
        {disponibles.map((p) => (
          <label key={p.id} className="registro-plan" data-color={p.color}>
            <input
              type="radio"
              name={`${id}-plan`}
              value={p.id}
              checked={peludo.plan_id === p.id}
              onChange={() => onCambio({ plan_id: p.id })}
            />
            <span className="registro-plan-nombre">{p.nombre}</span>
            <span className="registro-plan-valor numero">
              {/* Si no cabe, «al mes» baja entero a su línea; el precio ya va unido (`moneda`). */}
              {moneda(tarifaCon(p, totalPeludos))} al{'\u00a0'}mes
            </span>
          </label>
        ))}
      </fieldset>

      {elegido ? (
        <Cobertura plan={elegido} />
      ) : (
        <p className="registro-ficha-nota">Elige un plan para ver todo lo que cubre y sus condiciones.</p>
      )}

      {disponibles.length > 1 && (
        <>
          <button
            className="btn btn-plano registro-comparar"
            type="button"
            aria-expanded={comparando}
            aria-controls={`${id}-comparador`}
            onClick={() => setComparando((v) => !v)}
          >
            <Icono nombre={comparando ? 'arriba' : 'abajo'} size={16} />
            {comparando ? 'Cerrar la comparación' : `Comparar los ${disponibles.length} planes`}
          </button>
          {comparando && <Comparador id={`${id}-comparador`} planes={disponibles} titulo={`Lo que cubre cada plan para ${nombre}`} totalPeludos={totalPeludos} />}
        </>
      )}
    </section>
  )
}

/** Lo que cubre el plan elegido, fila por fila, con su carencia y sus exclusiones de frente. */
function Cobertura({ plan }: { plan: PlanPublico }) {
  return (
    <div className="registro-cobertura" data-color={plan.color}>
      <p className="registro-cobertura-cabeza">Lo que cubre {plan.nombre}</p>
      <dl className="registro-filas">
        {plan.beneficios.map((b) => (
          <div key={b.tipo_servicio_codigo}>
            <dt>{b.nombre}</dt>
            <dd>{b.texto}</dd>
          </div>
        ))}
      </dl>
      <Condiciones plan={plan} />
    </div>
  )
}

/** La carencia, las exclusiones y los términos, cuando TIMU los escribió: nada se inventa. */
function Condiciones({ plan }: { plan: PlanPublico }) {
  if (!plan.carencia && !plan.exclusiones && !plan.terminos_url) return null
  return (
    <dl className="registro-condiciones">
      {plan.carencia && (
        <div>
          <dt>Carencia</dt>
          <dd>{plan.carencia}</dd>
        </div>
      )}
      {plan.exclusiones && (
        <div>
          <dt>No cubre</dt>
          <dd>{plan.exclusiones}</dd>
        </div>
      )}
      {plan.terminos_url && (
        <div>
          <dt>Términos</dt>
          <dd>
            <a href={plan.terminos_url} target="_blank" rel="noreferrer">
              Términos y condiciones de {plan.nombre}
            </a>
          </dd>
        </div>
      )}
    </dl>
  )
}
