import { useState } from 'react'

import { Distintivo } from '@/components/Distintivo'
import { Modal } from '@/components/Modal'
import { useAuth } from '@/features/auth/AuthContext'
import { useRegistrarPago, type MedioPago } from '@/features/cartera/api'
import { mensajeError } from '@/lib/errores'
import { fecha, moneda } from '@/lib/formato'
import { puede } from '@/lib/permisos'
import type { CuotaRead, FamiliaRead } from '@/types'

import { useEstadoCuenta } from './api'

const MEDIOS: { valor: MedioPago; label: string }[] = [
  { valor: 'transferencia', label: 'Transferencia' },
  { valor: 'consignacion', label: 'Consignación' },
  { valor: 'efectivo', label: 'Efectivo' },
  { valor: 'datafono', label: 'Datáfono' },
  { valor: 'otro', label: 'Otro' },
]

/** Estado de cuenta de la familia y registro de pagos recibidos fuera de la pasarela. */
export function CarteraFamilia({ familia }: { familia: FamiliaRead }) {
  const { usuario } = useAuth()
  const cuenta = useEstadoCuenta(familia.id)
  const [pagando, setPagando] = useState(false)

  if (cuenta.isPending) return <p className="apagado">Cargando estado de cuenta…</p>
  if (cuenta.isError) {
    return (
      <p className="error" role="alert">
        No fue posible cargar el estado de cuenta. {mensajeError(cuenta.error, 'Intenta de nuevo en un momento.')}
      </p>
    )
  }
  if (cuenta.data === null) {
    return <p className="apagado">Esta familia aún no tiene contrato: no hay cuotas ni pagos.</p>
  }

  const c = cuenta.data
  const abiertas = c.cuotas.filter((q) => q.estado !== 'pagada' && q.estado !== 'anulada')

  return (
    <div className="pila">
      <section className="tarjeta">
        <div className="tarjeta-cabeza">
          <h3>
            Contrato {c.contrato.numero} · {c.plan.nombre}
          </h3>
          {puede(usuario, 'gestionarAfiliacion') && (
            <button className="btn btn-primario" type="button" onClick={() => setPagando(true)}>
              Registrar pago
            </button>
          )}
        </div>
        <dl className="ficha">
          <div><dt>Valor mensual</dt><dd className="numero">{moneda(c.contrato.valor_mensual)}</dd></div>
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
          <h3>Cuotas</h3>
        </div>
        {c.cuotas.length === 0 ? (
          <p className="apagado">El contrato todavía no ha generado cuotas.</p>
        ) : (
          <div className="scroll-x">
            <table className="tabla">
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
                    <td className="principal">{q.descripcion ?? q.periodo}</td>
                    <td className="numero">{fecha(q.fecha_vencimiento)}</td>
                    <td className="numero">{moneda(q.valor)}</td>
                    <td className="numero">{moneda(q.valor_pagado)}</td>
                    <td>
                      <Distintivo dominio="cuota" valor={q.estado} />
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
            <table className="tabla">
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
                    <td className="numero">{fecha(p.fecha_pago?.slice(0, 10))}</td>
                    <td className="numero">{moneda(p.valor)}</td>
                    <td>{p.medio ?? p.proveedor}</td>
                    <td className="numero">{p.referencia_externa}</td>
                    <td>
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

function RegistrarPagoModal({
  familiaId,
  cuotas,
  abierto,
  onCerrar,
}: {
  familiaId: string
  cuotas: CuotaRead[]
  abierto: boolean
  onCerrar: () => void
}) {
  const registrar = useRegistrarPago()

  function guardar(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const d = new FormData(e.currentTarget)
    const opcional = (campo: string) => String(d.get(campo) ?? '').trim() || undefined
    registrar.mutate(
      {
        familia_id: familiaId,
        valor: String(d.get('valor') ?? ''),
        medio: d.get('medio') as MedioPago,
        referencia: String(d.get('referencia') ?? '').trim(),
        cuota_id: opcional('cuota_id'),
        notas: opcional('notas'),
      },
      { onSuccess: onCerrar },
    )
  }

  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          registrar.reset()
          onCerrar()
        }
      }}
      titulo="Registrar pago"
      descripcion="Para pagos recibidos fuera de la pasarela. Sin cuota indicada, se aplica a la más antigua."
      pie={
        <button className="btn btn-primario" type="submit" form="registrar-pago" disabled={registrar.isPending}>
          {registrar.isPending ? 'Registrando…' : 'Registrar pago'}
        </button>
      }
    >
      <form id="registrar-pago" className="formulario" onSubmit={guardar}>
        <label className="campo">
          <span>Valor (COP)</span>
          <input className="input" name="valor" type="number" min="1" step="1" required inputMode="numeric" />
        </label>
        <label className="campo">
          <span>Medio</span>
          <select className="input" name="medio" defaultValue="transferencia">
            {MEDIOS.map((m) => (
              <option key={m.valor} value={m.valor}>{m.label}</option>
            ))}
          </select>
        </label>
        <label className="campo">
          <span>Referencia o comprobante</span>
          <input className="input" name="referencia" required minLength={3} />
        </label>
        <label className="campo">
          <span>Cuota</span>
          <select className="input" name="cuota_id" defaultValue="">
            <option value="">La más antigua pendiente</option>
            {cuotas.map((q) => (
              <option key={q.id} value={q.id}>
                {q.descripcion ?? q.periodo} · {moneda(q.valor)}
              </option>
            ))}
          </select>
        </label>
        <label className="campo ancho">
          <span>Notas (opcional)</span>
          <textarea className="input" name="notas" rows={2} />
        </label>
        {registrar.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(registrar.error, 'No fue posible registrar el pago.')}
          </p>
        )}
      </form>
    </Modal>
  )
}
