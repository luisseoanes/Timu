import { Fragment, useState } from 'react'

import { Consulta } from '@/components/Consulta'
import { Icono } from '@/components/Icono'
import { descargar } from '@/lib/descargas'
import { mensajeError } from '@/lib/errores'
import { fecha, hoyISO, moneda } from '@/lib/formato'

import { type FilaLiquidacion, useLiquidacion } from './api'

/** Lo que TIMU le debe a cada aliada en el período (6.22): las atenciones reportadas, su valor
 * y cuánto cubre TIMU y cuánto pagan las familias. */
export function Liquidacion() {
  const hoy = hoyISO()
  const [desde, setDesde] = useState(`${hoy.slice(0, 8)}01`)
  const [hasta, setHasta] = useState(hoy)
  const liquidacion = useLiquidacion(desde, hasta, Boolean(desde && hasta))
  const [errorCsv, setErrorCsv] = useState<string | null>(null)
  // Las clínicas con su detalle a la vista: se abren y se cierran por separado.
  const [abiertas, setAbiertas] = useState<ReadonlySet<string>>(new Set())

  function alternar(clinica: string) {
    setAbiertas((antes) => {
      const despues = new Set(antes)
      if (!despues.delete(clinica)) despues.add(clinica)
      return despues
    })
  }

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h2>Liquidación a aliadas</h2>
        <button
          className="btn btn-suave"
          type="button"
          onClick={() => {
            setErrorCsv(null)
            descargar('/aliadas/liquidacion', { desde, hasta, formato: 'csv' }, `liquidacion-${desde}-${hasta}.csv`).catch((e) =>
              setErrorCsv(mensajeError(e, 'No fue posible descargar la liquidación.')),
            )
          }}
        >
          <Icono nombre="descargar" size={16} /> Descargar CSV
        </button>
      </div>
      <div className="filtros liquidacion-periodo">
        <label className="campo">
          <span>Desde</span>
          <input className="input" type="date" value={desde} max={hasta} onChange={(e) => setDesde(e.target.value)} />
        </label>
        <label className="campo">
          <span>Hasta</span>
          <input className="input" type="date" value={hasta} min={desde} onChange={(e) => setHasta(e.target.value)} />
        </label>
      </div>
      {errorCsv && (
        <p className="error" role="alert">
          {errorCsv}
        </p>
      )}
      <Consulta
        consulta={liquidacion}
        cargando="Calculando la liquidación…"
        error="No fue posible calcular la liquidación."
        vacio="Ninguna aliada reportó atenciones en el período."
        estaVacio={(d) => d.length === 0}
      >
        {(d) => (
          <div className="scroll-x">
            <table className="tabla tabla-apilable bandeja-tabla liquidacion-tabla">
              <thead>
                <tr>
                  <th>Clínica</th>
                  <th>Atenciones</th>
                  <th>Valor de las atenciones</th>
                  <th>Cubre TIMU</th>
                  <th>Pagan las familias</th>
                </tr>
              </thead>
              <tbody>
                {d.map((f) => {
                  const abierta = abiertas.has(f.clinica_id)
                  return (
                    <Fragment key={f.clinica_id}>
                      <tr className="liquidacion-fila" data-abierta={abierta || undefined}>
                        <td className="principal" data-etiqueta="Clínica">
                          {/* El detalle de cada atención, el mismo del CSV, sin descargarlo. */}
                          <button
                            className="liquidacion-abrir"
                            type="button"
                            aria-expanded={abierta}
                            aria-controls={`liquidacion-${f.clinica_id}`}
                            onClick={() => alternar(f.clinica_id)}
                          >
                            <Icono nombre="abajo" size={16} />
                            {f.clinica}
                          </button>
                          {f.nit && (
                            <div className="bandeja-detalle">
                              <span className="numero">NIT {f.nit}</span>
                            </div>
                          )}
                        </td>
                        <td className="numero" data-etiqueta="Atenciones">{f.atenciones}</td>
                        <td className="numero" data-etiqueta="Valor de las atenciones">{moneda(f.valor_atenciones)}</td>
                        <td className="numero" data-etiqueta="Cubre TIMU">{moneda(f.valor_cubierto)}</td>
                        <td className="numero" data-etiqueta="Pagan las familias">{moneda(f.valor_familias)}</td>
                      </tr>
                      {abierta && (
                        <tr className="liquidacion-detalle" id={`liquidacion-${f.clinica_id}`}>
                          <td colSpan={5}>
                            <table className="tabla tabla-apilable liquidacion-atenciones" aria-label={`Atenciones de ${f.clinica}`}>
                              <thead>
                                <tr>
                                  <th>Remisión</th>
                                  <th>Atendida</th>
                                  <th>Beneficio</th>
                                  <th>Valor</th>
                                  <th>Cubre TIMU</th>
                                  <th>Paga la familia</th>
                                </tr>
                              </thead>
                              <tbody>
                                {f.detalle.map((a) => (
                                  <tr key={a.codigo}>
                                    <td className="numero" data-etiqueta="Remisión">{a.codigo}</td>
                                    <td data-etiqueta="Atendida">{fecha(a.fecha_atencion)}</td>
                                    <td data-etiqueta="Beneficio">{a.beneficio ?? '—'}</td>
                                    <td className="numero" data-etiqueta="Valor">{moneda(a.valor_atencion)}</td>
                                    <td className="numero" data-etiqueta="Cubre TIMU">{moneda(a.valor_cubierto)}</td>
                                    <td className="numero" data-etiqueta="Paga la familia">
                                      {moneda(Number(a.valor_atencion) - Number(a.valor_cubierto))}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  )
                })}
              </tbody>
              {d.length > 1 && (
                <tfoot>
                  <tr>
                    <th scope="row" className="principal">Total</th>
                    <td className="numero" data-etiqueta="Atenciones">{d.reduce((t, f) => t + f.atenciones, 0)}</td>
                    <td className="numero" data-etiqueta="Valor de las atenciones">{moneda(suma(d, 'valor_atenciones'))}</td>
                    <td className="numero" data-etiqueta="Cubre TIMU">{moneda(suma(d, 'valor_cubierto'))}</td>
                    <td className="numero" data-etiqueta="Pagan las familias">{moneda(suma(d, 'valor_familias'))}</td>
                  </tr>
                </tfoot>
              )}
            </table>
          </div>
        )}
      </Consulta>
    </section>
  )
}

function suma(filas: FilaLiquidacion[], campo: 'valor_atenciones' | 'valor_cubierto' | 'valor_familias'): number {
  return filas.reduce((t, f) => t + Number(f[campo]), 0)
}
