import { Modal } from '@/components/Modal'
import { mensajeError } from '@/lib/errores'
import { moneda } from '@/lib/formato'
import type { CuotaRead } from '@/types'

import { type MedioPago, useRegistrarPago } from './api'

const MEDIOS: { valor: MedioPago; label: string }[] = [
  { valor: 'transferencia', label: 'Transferencia' },
  { valor: 'consignacion', label: 'Consignación' },
  { valor: 'efectivo', label: 'Efectivo' },
  { valor: 'datafono', label: 'Datáfono' },
  { valor: 'otro', label: 'Otro' },
]

/** Pago recibido fuera de la pasarela. Con `cuotaId` (desde una estación de la línea) llega con
 * la cuota elegida y su saldo como valor. */
export function RegistrarPagoModal({
  familiaId,
  cuotas,
  cuotaId,
  abierto,
  onCerrar,
}: {
  familiaId: string
  cuotas: CuotaRead[]
  cuotaId?: string
  abierto: boolean
  onCerrar: () => void
}) {
  const elegida = cuotas.find((q) => q.id === cuotaId)
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
          <input
            className="input"
            name="valor"
            type="number"
            min="1"
            step="1"
            required
            inputMode="numeric"
            defaultValue={elegida ? Number(elegida.valor) - Number(elegida.valor_pagado) : undefined}
          />
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
          <select className="input" name="cuota_id" defaultValue={elegida?.id ?? ''}>
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
