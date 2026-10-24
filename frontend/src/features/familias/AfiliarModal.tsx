import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { api } from '@/api/client'
import { Modal } from '@/components/Modal'
import { usePlanes } from '@/features/catalogos/api'
import { mensajeError } from '@/lib/errores'
import { moneda } from '@/lib/formato'
import type { FamiliaRead } from '@/types'

interface InicioAfiliacion {
  solicitud_id: string
  valor: string
  enlace_pago: string
}

/**
 * Afiliación asistida (F1-AFI): el comercial elige el plan y deja registrada cómo
 * aceptó la familia. Se genera el enlace de pago; si la familia ya pagó por otro medio,
 * se registra el pago manual y la afiliación queda activa.
 */
export function AfiliarModal({ familia, abierto, onCerrar }: { familia: FamiliaRead; abierto: boolean; onCerrar: () => void }) {
  const qc = useQueryClient()
  const planes = usePlanes()
  const [inicio, setInicio] = useState<InicioAfiliacion | null>(null)
  const refrescar = () => {
    void qc.invalidateQueries({ queryKey: ['familias'] })
    void qc.invalidateQueries({ queryKey: ['cartera'] })
  }
  const afiliar = useMutation({
    mutationFn: async (datos: { plan_id: string; medio_aceptacion: string; detalle_aceptacion?: string }) =>
      (await api.post<InicioAfiliacion>('/afiliaciones/asistida', { familia_id: familia.id, ...datos })).data,
    onSuccess: (r) => {
      setInicio(r)
      refrescar()
    },
  })
  const pagoManual = useMutation({
    mutationFn: async (datos: { medio: string; comprobante: string }) =>
      (await api.post(`/afiliaciones/${inicio?.solicitud_id}/pago-manual`, datos)).data,
    onSuccess: refrescar,
  })

  function cerrar() {
    afiliar.reset()
    pagoManual.reset()
    setInicio(null)
    onCerrar()
  }

  return (
    <Modal abierto={abierto} onCambio={(v) => !v && cerrar()} titulo={`Afiliar a ${familia.titular_nombre}`}>
      {pagoManual.isSuccess ? (
        <p className="aviso-ok" role="status">
          Pago registrado: la afiliación quedó activa y la familia recibe su bienvenida por WhatsApp.
        </p>
      ) : inicio ? (
        <div className="pila">
          <p className="aviso-ok" role="status">
            Afiliación iniciada por {moneda(inicio.valor)}. Envía este enlace de pago a la familia:
          </p>
          <input className="input codigo" readOnly value={inicio.enlace_pago} aria-label="Enlace de pago" onFocus={(e) => e.target.select()} />
          <form
            className="formulario"
            onSubmit={(e) => {
              e.preventDefault()
              const d = new FormData(e.currentTarget)
              pagoManual.mutate({ medio: String(d.get('medio')), comprobante: String(d.get('comprobante')).trim() })
            }}
          >
            <p className="subtitulo ancho">¿Ya pagó por otro medio?</p>
            <label className="campo">
              <span>Medio</span>
              <select className="input" name="medio" defaultValue="transferencia">
                <option value="transferencia">Transferencia</option>
                <option value="consignacion">Consignación</option>
                <option value="efectivo">Efectivo</option>
                <option value="datafono">Datáfono</option>
              </select>
            </label>
            <label className="campo">
              <span>Comprobante</span>
              <input className="input" name="comprobante" required minLength={3} />
            </label>
            {pagoManual.isError && (
              <p className="error ancho" role="alert">
                {mensajeError(pagoManual.error, 'No fue posible registrar el pago.')}
              </p>
            )}
            <button className="btn btn-suave ancho" type="submit" disabled={pagoManual.isPending}>
              Registrar pago recibido
            </button>
          </form>
        </div>
      ) : (
        <form
          className="formulario"
          onSubmit={(e) => {
            e.preventDefault()
            const d = new FormData(e.currentTarget)
            afiliar.mutate({
              plan_id: String(d.get('plan_id')),
              medio_aceptacion: String(d.get('medio_aceptacion')),
              detalle_aceptacion: String(d.get('detalle') ?? '').trim() || undefined,
            })
          }}
        >
          <label className="campo ancho">
            <span>Plan</span>
            <select className="input" name="plan_id" required defaultValue="">
              <option value="" disabled>Elige el plan</option>
              {planes.data
                ?.filter((p) => p.activo)
                .map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nombre} · {moneda(p.valor_mensual)} · hasta {p.cupos_mascotas} mascotas
                  </option>
                ))}
            </select>
          </label>
          <label className="campo">
            <span>Cómo aceptó las condiciones</span>
            <select className="input" name="medio_aceptacion" defaultValue="whatsapp">
              <option value="whatsapp">Por WhatsApp</option>
              <option value="llamada">En llamada</option>
              <option value="presencial">En persona</option>
            </select>
          </label>
          <label className="campo">
            <span>Soporte (quién, cuándo)</span>
            <input className="input" name="detalle" />
          </label>
          {afiliar.isError && (
            <p className="error ancho" role="alert">
              {mensajeError(afiliar.error, 'No fue posible iniciar la afiliación.')}
            </p>
          )}
          <button className="btn btn-primario ancho" type="submit" disabled={afiliar.isPending}>
            Iniciar afiliación
          </button>
        </form>
      )}
    </Modal>
  )
}
