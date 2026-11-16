import { useState } from 'react'

import { Consulta } from '@/components/Consulta'
import { Icono } from '@/components/Icono'
import { descargar } from '@/lib/descargas'
import { mensajeError } from '@/lib/errores'
import { hoyISO, moneda } from '@/lib/formato'

import { type FilaLiquidacion, useLiquidacion } from './api'

/** Lo que TIMU le debe a cada aliada en el período (F2-ALI-04): las atenciones reportadas, su valor
 * y cuánto cubre TIMU y cuánto pagan las familias. */
export function Liquidacion() {
  const hoy = hoyISO()
  const [desde, setDesde] = useState(`${hoy.slice(0, 8)}01`)
  const [hasta, setHasta] = useState(hoy)
  const liquidacion = useLiquidacion(desde, hasta, Boolean(desde && hasta))
  const [errorCsv, setErrorCsv] = useState<string | null>(null)

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Liquidación a aliadas</h3>
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
                {d.map((f) => (
                  <tr key={f.clinica_id}>
                    <td className="principal" data-etiqueta="Clínica">
                      {f.clinica}
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
                ))}
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
