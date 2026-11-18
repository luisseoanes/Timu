import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { mensajeError } from '@/lib/errores'
import { moneda } from '@/lib/formato'

import { MarcoPublico } from './MarcoPublico'
import { codigoDeRuta, enlaceAfiliacion, useDatosTimu } from './portada'
import { useCiudadesRegistro, usePlanesRegistro } from './registro'

const MESES = { trimestral: 3, semestral: 6, anual: 12 } as const

/** «Desde los 30 días. Hasta $850.000 por episodio.»: cada parte, una frase con su punto. */
const frases = (...partes: (string | null | undefined)[]) =>
  partes
    .map((p) => p?.trim().replace(/\.+$/, ''))
    .filter(Boolean)
    .map((p) => `${p}.`)
    .join(' ')

/**
 * La página de un plan (R3-PUB-04, `/planes/colita-feliz`): todo lo que cubre, de frente, con su
 * precio por peludos en la ciudad que elija la familia, sus adicionales y sus condiciones. Sustituye
 * a las páginas de cada plan de la web vieja (`/service/plan-…/`). Todo sale del catálogo.
 */
export function PlanPage() {
  const { plan: ruta = '' } = useParams()
  const ciudades = useCiudadesRegistro()
  const datos = useDatosTimu()
  const [elegida, setElegida] = useState('')
  const ciudad = elegida || (ciudades.data?.includes(datos.data?.clinica_ciudad ?? '') ? datos.data!.clinica_ciudad! : (ciudades.data?.[0] ?? ''))
  const planes = usePlanesRegistro(ciudad)
  const plan = planes.data?.find((p) => p.codigo === codigoDeRuta(ruta))

  useEffect(() => {
    if (plan) document.title = `${plan.nombre} · Planes de TIMU`
  }, [plan])

  return (
    <MarcoPublico>
      {ciudades.isError || planes.isError ? (
        <div className="seccion">
          <p className="aviso-error" role="alert">
            {mensajeError(ciudades.error ?? planes.error, 'No pudimos cargar el plan.')}
          </p>
        </div>
      ) : !planes.data ? (
        <div className="seccion esqueleto" role="status">
          <span className="sr-only">Cargando el plan…</span>
          <span className="esqueleto-linea" aria-hidden="true" />
          <span className="esqueleto-linea" aria-hidden="true" />
        </div>
      ) : !plan ? (
        <div className="seccion plan-vacio">
          <h1 className="seccion-titulo">Este plan no está a la venta{ciudad && ` en ${ciudad}`}</h1>
          <p>
            Puede que haya cambiado de nombre o que no se venda en tu ciudad. <Link to={{ pathname: '/', hash: 'planes' }}>Mira los planes de TIMU</Link>.
          </p>
        </div>
      ) : (
        <>
          <section className="plan-cabeza" data-color={plan.color} aria-labelledby="plan-titulo">
            <div className="plan-cabeza-texto">
              <h1 id="plan-titulo" className="plan-cabeza-titulo">
                {plan.nombre}
              </h1>
              <p className="plan-cabeza-frase">{plan.descripcion ?? 'Medicina veterinaria prepagada para tu perro o tu gato.'}</p>
              <p className="plan-cabeza-precio">
                Desde <strong className="numero">{moneda(plan.tarifas.find((t) => t.peludos === 1)?.valor)}</strong> al mes por peludo en {ciudad}
              </p>
              <div className="plan-cabeza-acciones">
                <Link className="btn btn-primario" to={enlaceAfiliacion({ ciudad, plan: plan.id })}>
                  Afiliar a mi peludo con {plan.nombre}
                </Link>
              </div>
            </div>
            {/* El plan como su línea (DESIGN.md, «La línea de metro»): una estación por servicio. */}
            <ol className="plan-linea" data-color={plan.color} aria-label={`Los servicios de ${plan.nombre}`}>
              {plan.beneficios.map((b) => (
                <li key={b.tipo_servicio_codigo}>
                  <span className="plan-linea-estacion" aria-hidden="true" />
                  <span className="plan-linea-nombre">{b.nombre}</span>
                </li>
              ))}
            </ol>
          </section>

          <div className="plan-cuerpo">
            <section className="plan-bloque" aria-labelledby="plan-cubre">
              <h2 id="plan-cubre" className="seccion-titulo">
                Lo que cubre
              </h2>
              <ul className="plan-lista">
                {plan.beneficios.map((b) => (
                  <li key={b.tipo_servicio_codigo}>
                    <span className="plan-lista-nombre">{b.nombre}</span>
                    <span className="plan-lista-valor">{b.texto}</span>
                    {(b.carencia || b.detalle) && <span className="plan-lista-detalle">{frases(b.carencia, b.detalle)}</span>}
                  </li>
                ))}
              </ul>
            </section>

            {plan.adicionales.length > 0 && (
              <section className="plan-bloque" aria-labelledby="plan-adicionales-titulo">
                <h2 id="plan-adicionales-titulo" className="seccion-titulo">
                  Además
                </h2>
                <ul className="plan-lista">
                  {plan.adicionales.map((a) => (
                    <li key={a.nombre}>
                      <span className="plan-lista-nombre">{a.nombre}</span>
                      <span className="plan-lista-valor">{a.cubre}</span>
                      {(a.carencia || a.detalle || a.tercero) && (
                        <span className="plan-lista-detalle">
                          {frases(a.tercero ? 'Lo presta un tercero' : null, a.carencia, a.detalle)}
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            <aside className="plan-lado" aria-label="Precio y condiciones">
              <section className="plan-precios" aria-labelledby="plan-precio-titulo">
                <h2 id="plan-precio-titulo" className="plan-lado-titulo">
                  Lo que pagas
                </h2>
                <div className="campo">
                  <label htmlFor="plan-ciudad">Ciudad</label>
                  <select id="plan-ciudad" className="input" value={ciudad} onChange={(e) => setElegida(e.target.value)}>
                    {ciudades.data?.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </div>
                <dl className="plan-precio-filas">
                  {plan.tarifas.map((t) => (
                    <div key={t.peludos}>
                      <dt>{t.peludos === 1 ? 'Un peludo' : t.peludos >= 4 ? '4 o más peludos' : `${t.peludos} peludos`}</dt>
                      <dd className="numero">
                        {moneda(t.valor)} <span className="apagado">al mes{t.peludos > 1 ? ' cada uno' : ''}</span>
                      </dd>
                    </div>
                  ))}
                </dl>
                {plan.tarifas_periodicidad.filter((t) => t.periodicidad !== 'mensual').length > 0 && (
                  <>
                    <p className="plan-lado-nota">Pagando por adelantado, un peludo:</p>
                    <dl className="plan-precio-filas">
                      {plan.tarifas_periodicidad
                        .filter((t): t is typeof t & { periodicidad: keyof typeof MESES } => t.periodicidad in MESES)
                        .map((t) => (
                          <div key={t.periodicidad}>
                            <dt>{MESES[t.periodicidad]} meses</dt>
                            <dd className="numero">{moneda(t.valor)}</dd>
                          </div>
                        ))}
                    </dl>
                  </>
                )}
              </section>
              {(plan.carencia || plan.exclusiones || plan.terminos_url) && (
                <section className="plan-condiciones" aria-labelledby="plan-condiciones-titulo">
                  <h2 id="plan-condiciones-titulo" className="plan-lado-titulo">
                    Condiciones
                  </h2>
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
                  </dl>
                  {plan.terminos_url && (
                    <a href={plan.terminos_url} target="_blank" rel="noreferrer">
                      Términos y condiciones
                    </a>
                  )}
                </section>
              )}
              <Link to={{ pathname: '/', hash: 'planes' }}>Compararlo con los otros planes</Link>
            </aside>
          </div>
        </>
      )}
    </MarcoPublico>
  )
}
