import { useState } from 'react'

import { Consulta } from '@/components/Consulta'
import { Icono } from '@/components/Icono'
import { descargar } from '@/lib/descargas'
import { mensajeError } from '@/lib/errores'
import { hoyISO, moneda } from '@/lib/formato'

import { useLiquidacion } from './api'

export function Liquidacion() {
  const hoy = hoyISO()
  const [desde, setDesde] = useState(`${hoy.slice(0, 8)}01`)
  const [hasta, setHasta] = useState(hoy)
  const liquidacion = useLiquidacion(desde, hasta, true)
  const [errorCsv, setErrorCsv] = useState<string | null>(null)

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Liquidación a aliadas</h3>
        <button
          className="btn btn-suave"
          type="button"
          onClick={() =>
            descargar('/aliadas/liquidacion', { desde, hasta, formato: 'csv' }, `liquidacion-${desde}-${hasta}.csv`).catch((e) =>
              setErrorCsv(mensajeError(e, 'No fue posible descargar.')),
            )
          }
        >
          <Icono nombre="descargar" size={16} /> CSV
        </button>
      </div>
      <div className="filtros" style={{ marginBottom: 'var(--e4)' }}>
        <label className="acciones">
          Desde
          <input className="input" style={{ width: 'auto' }} type="date" value={desde} onChange={(e) => setDesde(e.target.value)} />
        </label>
        <label className="acciones">
          Hasta
          <input className="input" style={{ width: 'auto' }} type="date" value={hasta} onChange={(e) => setHasta(e.target.value)} />
        </label>
      </div>
      {errorCsv && (
        <p className="error" role="alert">
          {errorCsv}
        </p>
      )}
      <Consulta
        consulta={liquidacion}
        cargando="Calculando…"
        error="No fue posible calcular la liquidación."
        vacio="No hubo atenciones en aliadas en el período."
        estaVacio={(d) => d.length === 0}
      >
        {(d) => (
          <div className="scroll-x">
            <table className="tabla">
              <thead>
                <tr>
                  <th>Clínica</th>
                  <th>Atenciones</th>
                  <th>Valor atenciones</th>
                  <th>A cargo de TIMU</th>
                  <th>A cargo de familias</th>
                </tr>
              </thead>
              <tbody>
                {d.map((f) => (
                  <tr key={f.clinica_id}>
                    <td className="principal">
                      {f.clinica}
                      {f.nit && <div className="apagado numero">NIT {f.nit}</div>}
                    </td>
                    <td className="numero">{f.atenciones}</td>
                    <td className="numero">{moneda(f.valor_atenciones)}</td>
                    <td className="numero">{moneda(f.valor_cubierto)}</td>
                    <td className="numero">{moneda(f.valor_familias)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Consulta>
    </section>
  )
}
