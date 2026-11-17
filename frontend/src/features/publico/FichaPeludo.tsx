import { useId, useState } from 'react'

import { Icono } from '@/components/Icono'
import { moneda } from '@/lib/formato'
import type { PlanPublico } from '@/types'

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
          {comparando && <Comparador id={`${id}-comparador`} planes={disponibles} nombre={nombre} totalPeludos={totalPeludos} />}
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

/**
 * Los planes lado a lado con las mismas filas, en el orden del catálogo que da la API: un
 * servicio que un plan no trae se dice «No incluye».
 */
function Comparador({
  id,
  planes,
  nombre,
  totalPeludos,
}: {
  id: string
  planes: PlanPublico[]
  nombre: string
  totalPeludos: number
}) {
  // Las filas: el precio, cada servicio que trae alguno de los planes y sus condiciones.
  const servicios = new Map<string, string>()
  for (const p of planes) for (const b of p.beneficios) if (!servicios.has(b.tipo_servicio_codigo)) servicios.set(b.tipo_servicio_codigo, b.nombre)
  const filas: [string, string, (p: PlanPublico) => string][] = [
    ['valor', 'Al mes', (p) => moneda(tarifaCon(p, totalPeludos))],
    ...[...servicios].map(
      ([codigo, servicio]): [string, string, (p: PlanPublico) => string] => [
        codigo,
        servicio,
        (p) => p.beneficios.find((b) => b.tipo_servicio_codigo === codigo)?.texto ?? 'No incluye',
      ],
    ),
  ]
  if (planes.some((p) => p.carencia)) filas.push(['carencia', 'Carencia', (p) => p.carencia ?? '—'])
  if (planes.some((p) => p.exclusiones)) filas.push(['exclusiones', 'No cubre', (p) => p.exclusiones ?? '—'])
  return (
    <div id={id} className="registro-comparador">
      <table className="tabla">
        <caption className="sr-only">Lo que cubre cada plan para {nombre}</caption>
        <thead>
          <tr>
            <th>Servicio</th>
            {planes.map((p) => (
              <th key={p.id} data-color={p.color}>
                {p.nombre}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {filas.map(([clave, servicio, valor]) => {
            const valores = planes.map(valor)
            // Lo que es igual en todos se dice una vez: la diferencia salta a la vista.
            const igual = valores.every((v) => v === valores[0])
            return (
              <tr key={clave}>
                <td className="principal" data-etiqueta="Servicio">
                  {servicio}
                </td>
                {igual ? (
                  <td colSpan={planes.length} className="registro-comparador-igual">
                    <span>
                      {valores[0]} <span className="registro-comparador-nota">· igual en los {planes.length}</span>
                    </span>
                  </td>
                ) : (
                  planes.map((p, i) => (
                    <td key={p.id} className="registro-comparador-valor">
                      {/* Apilado (en el celular), cada valor dice de qué plan es, con su color. */}
                      <span className="registro-comparador-plan" aria-hidden="true">
                        <span className="marcador-plan" data-color={p.color} />
                        {p.nombre}
                      </span>
                      <span>{valores[i]}</span>
                    </td>
                  ))
                )}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
