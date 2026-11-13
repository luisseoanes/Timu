import { useState } from 'react'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { useNombreTipoServicio } from '@/features/catalogos'
import { descargar } from '@/lib/descargas'
import { mensajeError } from '@/lib/errores'
import { estadoCuota } from '@/lib/estados'
import { fecha, fechaHora, moneda } from '@/lib/formato'
import type { ServicioPortalRead } from '@/types'

import {
  urlContrato,
  useActualizarMisDatos,
  useCancelarPortal,
  useMiCuenta,
  useMiFamilia,
  useMisPagos,
  useMisServicios,
  usePagarPortal,
  useReprogramarPortal,
} from './api'
import { AgendarModal, SelectorCupo } from './Agenda'
import { DocumentosPortal } from './DocumentosPortal'

// --- Citas ------------------------------------------------------------------------------------

export function PortalCitas() {
  const [pasadas, setPasadas] = useState(false)
  const citas = useMisServicios(pasadas)
  const nombreTipo = useNombreTipoServicio()
  const familia = useMiFamilia()
  const [agendando, setAgendando] = useState(false)
  const [reprogramando, setReprogramando] = useState<ServicioPortalRead | null>(null)
  const [cancelando, setCancelando] = useState<ServicioPortalRead | null>(null)
  const nombreMascota = (id: string | null) => familia.data?.mascotas?.find((m) => m.id === id)?.nombre

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Mis citas</h3>
        <button className="btn btn-primario" type="button" onClick={() => setAgendando(true)}>
          <Icono nombre="mas" size={16} /> Agendar
        </button>
      </div>
      <label className="acciones" style={{ marginBottom: 'var(--e3)' }}>
        <input type="checkbox" checked={pasadas} onChange={(e) => setPasadas(e.target.checked)} />
        Ver también las pasadas
      </label>
      <Consulta consulta={citas} cargando="Cargando citas…" error="No pudimos cargar tus citas." vacio="No tienes citas." estaVacio={(d) => d.length === 0}>
        {(d) =>
          d.map((s) => {
            const abierta = s.estado === 'agendado' || s.estado === 'solicitado' || s.estado === 'pendiente_autorizacion'
            return (
              <div key={s.id} className="fila">
                <span className="fila-icono">
                  <Icono nombre="servicios" size={18} />
                </span>
                <div className="fila-cuerpo">
                  <strong>
                    {nombreTipo(s.tipo_codigo)}
                    {nombreMascota(s.mascota_id) ? ` · ${nombreMascota(s.mascota_id)}` : ''}
                  </strong>
                  <span>{fechaHora(s.programado_para)}</span>
                </div>
                <Distintivo dominio="servicio" valor={s.estado} />
                {abierta && (
                  <div className="acciones">
                    <button className="btn btn-plano" type="button" onClick={() => setReprogramando(s)}>
                      Cambiar fecha
                    </button>
                    <button className="btn btn-plano" type="button" onClick={() => setCancelando(s)}>
                      Cancelar
                    </button>
                  </div>
                )}
              </div>
            )
          })
        }
      </Consulta>
      <AgendarModal abierto={agendando} onCerrar={() => setAgendando(false)} />
      {reprogramando && <ReprogramarModal cita={reprogramando} onCerrar={() => setReprogramando(null)} />}
      <CancelarCitaModal cita={cancelando} onCerrar={() => setCancelando(null)} />
    </section>
  )
}

function ReprogramarModal({ cita, onCerrar }: { cita: ServicioPortalRead; onCerrar: () => void }) {
  const reprogramar = useReprogramarPortal()
  const [inicio, setInicio] = useState('')
  return (
    <Modal
      abierto
      onCambio={(v) => !v && onCerrar()}
      titulo="Cambiar la fecha"
      pie={
        <button className="btn btn-primario" type="submit" form="reprogramar-portal" disabled={!inicio || reprogramar.isPending}>
          Cambiar fecha
        </button>
      }
    >
      <form
        id="reprogramar-portal"
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const motivo = String(new FormData(e.currentTarget).get('motivo')).trim()
          reprogramar.mutate({ id: cita.id, inicio, motivo }, { onSuccess: onCerrar })
        }}
      >
        <SelectorCupo tipo={cita.tipo_codigo} valor={inicio} onCambio={setInicio} />
        <label className="campo ancho">
          <span>Motivo</span>
          <input className="input" name="motivo" required minLength={3} />
        </label>
        {reprogramar.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(reprogramar.error, 'No pudimos cambiar la fecha.')}
          </p>
        )}
      </form>
    </Modal>
  )
}

function CancelarCitaModal({ cita, onCerrar }: { cita: ServicioPortalRead | null; onCerrar: () => void }) {
  const cancelar = useCancelarPortal()
  return (
    <Modal
      abierto={cita !== null}
      onCambio={(v) => {
        if (!v) {
          cancelar.reset()
          onCerrar()
        }
      }}
      titulo="Cancelar la cita"
      pie={
        <button className="btn btn-primario" type="submit" form="cancelar-portal" disabled={cancelar.isPending}>
          Cancelar cita
        </button>
      }
    >
      <form
        id="cancelar-portal"
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const motivo = String(new FormData(e.currentTarget).get('motivo')).trim()
          if (cita) cancelar.mutate({ id: cita.id, motivo }, { onSuccess: onCerrar })
        }}
      >
        <label className="campo ancho">
          <span>Motivo</span>
          <input className="input" name="motivo" required minLength={3} />
        </label>
        {cancelar.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(cancelar.error, 'No pudimos cancelar la cita.')}
          </p>
        )}
      </form>
    </Modal>
  )
}

// --- Pagos ------------------------------------------------------------------------------------

export function PortalPagos() {
  const cuenta = useMiCuenta()
  const pagos = useMisPagos()
  const pagar = usePagarPortal()
  const [errorComprobante, setErrorComprobante] = useState<string | null>(null)

  return (
    <div className="pila">
      <section className="tarjeta">
        <div className="tarjeta-cabeza">
          <h3>Mi cuenta</h3>
        </div>
        <Consulta consulta={cuenta} cargando="Cargando tu cuenta…" error="No pudimos cargar tu cuenta.">
          {(c) =>
            c === null ? (
              <p className="apagado">Aún no tienes un contrato activo.</p>
            ) : (
              <div className="pila">
                <dl className="ficha">
                  <div><dt>Saldo pendiente</dt><dd className="numero">{moneda(c.saldo_pendiente)}</dd></div>
                  <div><dt>Vencido</dt><dd className="numero">{moneda(c.saldo_vencido)}</dd></div>
                  <div>
                    <dt>Próximo cobro</dt>
                    <dd className="numero">{c.proximo_cobro ? `${moneda(c.proximo_cobro.valor)} el ${fecha(c.proximo_cobro.fecha)}` : '—'}</dd>
                  </div>
                </dl>
                {c.cuotas
                  .filter((q) => q.estado !== 'pagada' && q.estado !== 'anulada')
                  .map((q) => (
                    <div key={q.id} className="fila">
                      <div className="fila-cuerpo">
                        <strong>{q.descripcion ?? q.periodo}</strong>
                        <span>
                          {moneda(Number(q.valor) - Number(q.valor_pagado))} · vence {fecha(q.fecha_vencimiento)}
                        </span>
                      </div>
                      <Distintivo dominio="cuota" valor={estadoCuota(q)} />
                      <button
                        className="btn btn-primario"
                        type="button"
                        disabled={pagar.isPending}
                        onClick={() => pagar.mutate(q.id, { onSuccess: (r) => window.location.assign(r.enlace_pago) })}
                      >
                        Pagar
                      </button>
                    </div>
                  ))}
                {pagar.isError && (
                  <p className="error" role="alert">
                    {mensajeError(pagar.error, 'No pudimos iniciar el pago.')}
                  </p>
                )}
              </div>
            )
          }
        </Consulta>
      </section>
      <section className="tarjeta">
        <div className="tarjeta-cabeza">
          <h3>Mis pagos</h3>
        </div>
        {errorComprobante && (
          <p className="error" role="alert">
            {errorComprobante}
          </p>
        )}
        <Consulta consulta={pagos} cargando="Cargando pagos…" error="No pudimos cargar tus pagos." vacio="Aún no tienes pagos." estaVacio={(d) => d.length === 0}>
          {(d) =>
            d.map((p) => (
              <div key={p.id} className="fila">
                <div className="fila-cuerpo">
                  <strong className="numero">{moneda(p.valor)}</strong>
                  <span>{p.fecha_pago ? fechaHora(p.fecha_pago) : fechaHora(p.created_at)}</span>
                </div>
                <Distintivo dominio="pago" valor={p.estado} />
                {p.estado === 'aprobado' && (
                  <button
                    className="btn btn-plano"
                    type="button"
                    onClick={() =>
                      descargar(`/portal/pagos/${p.id}/comprobante`, {}, `comprobante-${p.referencia_externa}.pdf`).catch((e) =>
                        setErrorComprobante(mensajeError(e, 'No pudimos descargar el comprobante.')),
                      )
                    }
                  >
                    <Icono nombre="descargar" size={16} /> Comprobante
                  </button>
                )}
              </div>
            ))
          }
        </Consulta>
      </section>
    </div>
  )
}

// --- Datos ------------------------------------------------------------------------------------

export function PortalDatos() {
  const familia = useMiFamilia()
  const actualizar = useActualizarMisDatos()
  const [errorContrato, setErrorContrato] = useState<string | null>(null)

  return (
    <div className="pila">
      <section className="tarjeta">
        <div className="tarjeta-cabeza">
          <h3>Mis datos</h3>
          <button
            className="btn btn-suave"
            type="button"
            onClick={async () => {
              setErrorContrato(null)
              try {
                window.open(await urlContrato(), '_blank', 'noopener')
              } catch (e) {
                setErrorContrato(mensajeError(e, 'No pudimos abrir el contrato.'))
              }
            }}
          >
            <Icono nombre="descargar" size={16} /> Mi contrato
          </button>
        </div>
        {errorContrato && (
          <p className="error" role="alert">
            {errorContrato}
          </p>
        )}
        <Consulta consulta={familia} cargando="Cargando…" error="No pudimos cargar tus datos.">
          {(f) => (
            <form
              className="formulario"
              onSubmit={(e) => {
                e.preventDefault()
                const d = new FormData(e.currentTarget)
                const cambios: Record<string, string> = {}
                for (const campo of ['email', 'telefono', 'barrio', 'direccion', 'complemento'] as const) {
                  const v = String(d.get(campo) ?? '').trim()
                  if (v !== (f[campo] ?? '')) cambios[campo] = v
                }
                actualizar.mutate(cambios)
              }}
            >
              <div className="campo ancho">
                <span>Titular</span>
                <p>
                  {f.titular_nombre} · {f.tipo_documento} {f.documento}
                </p>
              </div>
              <label className="campo">
                <span>Celular (WhatsApp)</span>
                <input className="input" name="telefono" defaultValue={f.telefono} inputMode="tel" required />
              </label>
              <label className="campo">
                <span>Correo</span>
                <input className="input" name="email" type="email" defaultValue={f.email ?? ''} />
              </label>
              <label className="campo">
                <span>Barrio</span>
                <input className="input" name="barrio" defaultValue={f.barrio} required minLength={2} maxLength={120} />
              </label>
              <label className="campo">
                <span>Dirección de las visitas</span>
                <input className="input" name="direccion" defaultValue={f.direccion ?? ''} />
              </label>
              <label className="campo ancho">
                <span>Complemento</span>
                <input
                  className="input"
                  name="complemento"
                  defaultValue={f.complemento ?? ''}
                  maxLength={255}
                  placeholder="Torre, apartamento, indicaciones"
                />
              </label>
              {actualizar.isError && (
                <p className="error ancho" role="alert">
                  {mensajeError(actualizar.error, 'No pudimos guardar tus datos.')}
                </p>
              )}
              {actualizar.isSuccess && (
                <p className="exito ancho" role="status">
                  Datos guardados.
                </p>
              )}
              <div className="acciones ancho">
                <button className="btn btn-primario" type="submit" disabled={actualizar.isPending}>
                  Guardar
                </button>
              </div>
            </form>
          )}
        </Consulta>
      </section>
      <DocumentosPortal />
    </div>
  )
}
