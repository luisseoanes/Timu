import { useState } from 'react'

import { Distintivo } from '@/components/Distintivo'
import { useAuth } from '@/features/auth'
import { RegistrarPagoModal, useEstadoCuenta } from '@/features/cartera'
import { mensajeError } from '@/lib/errores'
import { estadoCuota } from '@/lib/estados'
import { fecha, moneda } from '@/lib/formato'
import { puede } from '@/lib/permisos'
import type { FamiliaRead } from '@/types'

import { AfiliarModal } from './AfiliarModal'

/** Estado de cuenta de la familia y registro de pagos recibidos fuera de la pasarela. */
export function CarteraFamilia({ familia }: { familia: FamiliaRead }) {
  const { usuario } = useAuth()
  const cuenta = useEstadoCuenta(familia.id)
  const [pagando, setPagando] = useState(false)
  const [afiliando, setAfiliando] = useState(false)

  if (cuenta.isPending) return <p className="apagado">Cargando estado de cuenta…</p>
  if (cuenta.isError) {
    return (
      <p className="error" role="alert">
        No fue posible cargar el estado de cuenta. {mensajeError(cuenta.error, 'Intenta de nuevo en un momento.')}
      </p>
    )
  }
  if (cuenta.data === null) {
    return (
      <section className="tarjeta">
        <p className="apagado">Esta familia aún no tiene contrato: no hay cuotas ni pagos.</p>
        {puede(usuario, 'gestionarAfiliacion') && (
          <button className="btn btn-suave" type="button" style={{ marginTop: 'var(--e3)' }} onClick={() => setAfiliando(true)}>
            Afiliar a un plan
          </button>
        )}
        <AfiliarModal familia={familia} abierto={afiliando} onCerrar={() => setAfiliando(false)} />
      </section>
    )
  }

  const c = cuenta.data
  const abiertas = c.cuotas.filter((q) => q.estado !== 'pagada' && q.estado !== 'anulada')

  return (
    <div className="pila">
      <section className="tarjeta">
        <div className="tarjeta-cabeza">
          <h3>
            Contrato {c.contrato.numero} · pago {c.contrato.periodicidad}
          </h3>
          {puede(usuario, 'gestionarAfiliacion') && (
            <button className="btn btn-suave" type="button" onClick={() => setPagando(true)}>
              Registrar pago
            </button>
          )}
        </div>
        <dl className="ficha">
          <div><dt>Valor de cada cuota</dt><dd className="numero">{moneda(c.contrato.valor_periodo)}</dd></div>
          <div><dt>Valor mensual de los peludos</dt><dd className="numero">{moneda(c.contrato.valor_mensual)}</dd></div>
          <div><dt>Saldo pendiente</dt><dd className="numero">{moneda(c.saldo_pendiente)}</dd></div>
          <div><dt>Saldo vencido</dt><dd className="numero">{moneda(c.saldo_vencido)}</dd></div>
          <div><dt>Días de mora</dt><dd className="numero">{c.dias_mora}</dd></div>
          <div><dt>Saldo a favor</dt><dd className="numero">{moneda(c.saldo_a_favor)}</dd></div>
          <div>
            <dt>Próximo cobro</dt>
            <dd className="numero">
              {c.proximo_cobro ? `${moneda(c.proximo_cobro.valor)} el ${fecha(c.proximo_cobro.fecha)}` : '—'}
            </dd>
          </div>
          <div><dt>Renovación</dt><dd className="numero">{fecha(c.contrato.fecha_renovacion)}</dd></div>
        </dl>
      </section>

      <section className="tarjeta">
        <div className="tarjeta-cabeza">
          <h3>Peludos afiliados</h3>
        </div>
        {c.mascotas.length === 0 ? (
          <p className="apagado">El contrato no tiene peludos vigentes.</p>
        ) : (
          <div className="scroll-x">
            <table className="tabla tabla-apilable" aria-label="Peludos afiliados">
              <thead>
                <tr>
                  <th>Peludo</th>
                  <th>Plan</th>
                  <th>Al mes</th>
                </tr>
              </thead>
              <tbody>
                {c.mascotas.map((m) => (
                  <tr key={m.mascota_id}>
                    <td data-etiqueta="Peludo" className="principal">{m.nombre}</td>
                    <td data-etiqueta="Plan">{m.plan_nombre}</td>
                    <td data-etiqueta="Al mes" className="numero">{moneda(m.valor_mensual)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="tarjeta">
        <div className="tarjeta-cabeza">
          <h3>Cuotas</h3>
        </div>
        {c.cuotas.length === 0 ? (
          <p className="apagado">El contrato todavía no ha generado cuotas.</p>
        ) : (
          <div className="scroll-x">
            <table className="tabla tabla-apilable">
              <thead>
                <tr>
                  <th>Periodo</th>
                  <th>Vence</th>
                  <th>Valor</th>
                  <th>Pagado</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {c.cuotas.map((q) => (
                  <tr key={q.id}>
                    <td data-etiqueta="Periodo" className="principal">{q.descripcion ?? q.periodo}</td>
                    <td data-etiqueta="Vence" className="numero">{fecha(q.fecha_vencimiento)}</td>
                    <td data-etiqueta="Valor" className="numero">{moneda(q.valor)}</td>
                    <td data-etiqueta="Pagado" className="numero">{moneda(q.valor_pagado)}</td>
                    <td data-etiqueta="Estado">
                      <Distintivo dominio="cuota" valor={estadoCuota(q)} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="tarjeta">
        <div className="tarjeta-cabeza">
          <h3>Pagos</h3>
        </div>
        {c.pagos.length === 0 ? (
          <p className="apagado">No hay pagos registrados.</p>
        ) : (
          <div className="scroll-x">
            <table className="tabla tabla-apilable">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Valor</th>
                  <th>Medio</th>
                  <th>Referencia</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {c.pagos.map((p) => (
                  <tr key={p.id}>
                    <td data-etiqueta="Fecha" className="numero">{fecha(p.fecha_pago?.slice(0, 10))}</td>
                    <td data-etiqueta="Valor" className="numero">{moneda(p.valor)}</td>
                    <td data-etiqueta="Medio">{p.medio ?? p.proveedor}</td>
                    <td data-etiqueta="Referencia" className="numero">{p.referencia_externa}</td>
                    <td data-etiqueta="Estado">
                      <Distintivo dominio="pago" valor={p.estado} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <RegistrarPagoModal
        familiaId={familia.id}
        cuotas={abiertas}
        abierto={pagando}
        onCerrar={() => setPagando(false)}
      />
    </div>
  )
}
