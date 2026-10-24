import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { Pestanas } from '@/components/Pestanas'
import { useAuth } from '@/features/auth/AuthContext'
import { useNombreTipoServicio, useTiposServicio } from '@/features/catalogos/api'
import { descargar } from '@/lib/descargas'
import { mensajeError } from '@/lib/errores'
import { fecha, fechaHora, hora, hoyISO, moneda } from '@/lib/formato'
import type { ServicioPortalRead } from '@/types'

import {
  urlContrato,
  useActualizarMisDatos,
  useAgendarPortal,
  useCancelarPortal,
  useCarnetPdfPortal,
  useCarnetPortal,
  useDisponibilidadPortal,
  useHistoriaPortal,
  useMiCuenta,
  useMiFamilia,
  useMiPlan,
  useMisPagos,
  useMisServicios,
  useOrientacionVirtual,
  usePagarPortal,
  useReprogramarPortal,
} from './api'

// --- Inicio -----------------------------------------------------------------------------------

export function PortalInicio() {
  const { usuario } = useAuth()
  const plan = useMiPlan()
  const cuenta = useMiCuenta()
  const citas = useMisServicios()
  const nombreTipo = useNombreTipoServicio()
  const [orientacion, setOrientacion] = useState(false)
  const [agendando, setAgendando] = useState(false)

  return (
    <div className="pila">
      <section className="portal-hola">
        <h1>Hola, {usuario?.nombre?.split(' ')[0]}</h1>
        <p>¿Qué necesitan hoy tus mascotas?</p>
        <div className="accesos">
          <button className="acceso" type="button" onClick={() => setAgendando(true)}>
            <Icono nombre="calendario" />
            Agendar visita
          </button>
          <button className="acceso" type="button" onClick={() => setOrientacion(true)}>
            <Icono nombre="mensaje" />
            Orientación virtual
          </button>
          <Link className="acceso" to="/portal/mascotas">
            <Icono nombre="preventivos" />
            Carnet de vacunas
          </Link>
          <Link className="acceso" to="/portal/pagos">
            <Icono nombre="pago" />
            Pagar
          </Link>
        </div>
      </section>

      {cuenta.data && Number(cuenta.data.saldo_vencido) > 0 && (
        <p className="aviso-error" role="alert">
          Tienes {moneda(cuenta.data.saldo_vencido)} vencidos. <Link to="/portal/pagos">Pagar ahora</Link>
        </p>
      )}

      <div className="dos-columnas">
        <section className="tarjeta">
          <div className="tarjeta-cabeza">
            <h3>Próximas citas</h3>
            <Link to="/portal/citas">Ver todas</Link>
          </div>
          <Consulta consulta={citas} cargando="Cargando citas…" error="No pudimos cargar tus citas." vacio="No tienes citas próximas." estaVacio={(d) => d.length === 0}>
            {(d) =>
              d.slice(0, 3).map((s) => (
                <div key={s.id} className="fila">
                  <span className="fila-icono">
                    <Icono nombre="servicios" size={18} />
                  </span>
                  <div className="fila-cuerpo">
                    <strong>{nombreTipo(s.tipo_codigo)}</strong>
                    <span>{fechaHora(s.programado_para)}</span>
                  </div>
                  <Distintivo dominio="servicio" valor={s.estado} />
                </div>
              ))
            }
          </Consulta>
        </section>

        <section className="tarjeta">
          <div className="tarjeta-cabeza">
            <h3>Mi plan</h3>
          </div>
          <Consulta consulta={plan} cargando="Cargando tu plan…" error="No pudimos cargar tu plan.">
            {(p) =>
              p === null ? (
                <p className="apagado">Aún no tienes un plan activo. Escríbenos por WhatsApp para afiliarte.</p>
              ) : (
                <div className="pila" style={{ gap: 'var(--e3)' }}>
                  <div className="acciones">
                    <strong className="indicador-valor">{p.plan}</strong>
                    <Distintivo dominio="afiliacion" valor={p.estado} />
                  </div>
                  <span className="apagado">
                    {moneda(p.valor_mensual)} al mes · renueva el {fecha(p.fecha_renovacion)}
                  </span>
                  <ul className="beneficios">
                    {p.beneficios.map((b) => (
                      <li key={b.tipo_servicio}>
                        <Icono nombre="check" size={14} /> {nombreTipo(b.tipo_servicio)}:{' '}
                        {b.disponibles === null ? 'ilimitado' : `te quedan ${b.disponibles} de ${b.cupo} este ${b.periodo === 'anual' ? 'año' : 'mes'}`}
                      </li>
                    ))}
                  </ul>
                </div>
              )
            }
          </Consulta>
        </section>
      </div>
      <AgendarModal abierto={agendando} onCerrar={() => setAgendando(false)} />
      <OrientacionModal abierto={orientacion} onCerrar={() => setOrientacion(false)} />
    </div>
  )
}

function OrientacionModal({ abierto, onCerrar }: { abierto: boolean; onCerrar: () => void }) {
  const familia = useMiFamilia()
  const pedir = useOrientacionVirtual()
  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          pedir.reset()
          onCerrar()
        }
      }}
      titulo="Orientación virtual"
      descripcion="Un médico veterinario te responde por WhatsApp. Si es una urgencia, llama a la línea de emergencias."
      pie={
        !pedir.isSuccess && (
          <button className="btn btn-primario" type="submit" form="orientacion" disabled={pedir.isPending}>
            Enviar consulta
          </button>
        )
      }
    >
      {pedir.isSuccess ? (
        <p className="aviso-ok" role="status">
          Recibimos tu consulta. Te escribimos pronto por WhatsApp.
        </p>
      ) : (
        <form
          id="orientacion"
          className="formulario"
          onSubmit={(e) => {
            e.preventDefault()
            const d = new FormData(e.currentTarget)
            pedir.mutate({ mascota_id: String(d.get('mascota_id')), motivo: String(d.get('motivo')).trim() })
          }}
        >
          <label className="campo ancho">
            <span>¿Sobre quién es la consulta?</span>
            <select className="input" name="mascota_id" required>
              {familia.data?.mascotas
                ?.filter((m) => m.activa)
                .map((m) => (
                  <option key={m.id} value={m.id}>{m.nombre}</option>
                ))}
            </select>
          </label>
          <label className="campo ancho">
            <span>Cuéntanos qué pasa</span>
            <textarea className="input" name="motivo" rows={4} required minLength={5} />
          </label>
          {pedir.isError && (
            <p className="error ancho" role="alert">
              {mensajeError(pedir.error, 'No pudimos enviar tu consulta.')}
            </p>
          )}
        </form>
      )}
    </Modal>
  )
}

// --- Mascotas ---------------------------------------------------------------------------------

export function PortalMascotas() {
  const familia = useMiFamilia()
  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Mis mascotas</h3>
      </div>
      <Consulta consulta={familia} cargando="Cargando…" error="No pudimos cargar tus mascotas.">
        {(f) => (
          <div className="mascotas">
            {(f.mascotas ?? [])
              .filter((m) => m.activa)
              .map((m) => (
                <Link key={m.id} to={`/portal/mascotas/${m.id}`} className="acceso">
                  <Icono nombre="huella" />
                  {m.nombre}
                  <span className="apagado">{m.raza ?? m.especie}</span>
                </Link>
              ))}
          </div>
        )}
      </Consulta>
    </section>
  )
}

export function PortalMascota() {
  const { mascotaId = '' } = useParams()
  const familia = useMiFamilia()
  const mascota = familia.data?.mascotas?.find((m) => m.id === mascotaId)
  return (
    <div className="pila">
      <div className="detalle-cabeza">
        <Link to="/portal/mascotas" className="btn btn-plano" aria-label="Volver a mis mascotas">
          <Icono nombre="volver" size={16} />
        </Link>
        <h1>{mascota?.nombre ?? '…'}</h1>
      </div>
      <Pestanas
        etiqueta={`Secciones de ${mascota?.nombre ?? 'la mascota'}`}
        pestanas={[
          { valor: 'carnet', titulo: 'Carnet', contenido: <CarnetPortal mascotaId={mascotaId} /> },
          { valor: 'historia', titulo: 'Historia clínica', contenido: <HistoriaPortal mascotaId={mascotaId} /> },
        ]}
      />
    </div>
  )
}

function CarnetPortal({ mascotaId }: { mascotaId: string }) {
  const carnet = useCarnetPortal(mascotaId)
  const pdf = useCarnetPdfPortal()
  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Carnet de vacunación</h3>
        <button className="btn btn-suave" type="button" disabled={pdf.isPending} onClick={() => pdf.mutate(mascotaId)}>
          <Icono nombre="descargar" size={16} /> Descargar PDF
        </button>
      </div>
      {pdf.isSuccess && (
        <p className="aviso-ok" role="status">
          Listo: <a href={pdf.data.url} target="_blank" rel="noreferrer">abrir el carnet</a>. Código de verificación{' '}
          <strong className="numero">{pdf.data.codigo}</strong>.
        </p>
      )}
      {pdf.isError && (
        <p className="error" role="alert">
          {mensajeError(pdf.error, 'No pudimos generar el PDF.')}
        </p>
      )}
      <Consulta consulta={carnet} cargando="Cargando el carnet…" error="No pudimos cargar el carnet.">
        {(c) => (
          <div className="pila">
            {c.vencidos.length > 0 && (
              <p className="aviso-error">
                {c.vencidos.length} preventivo(s) vencido(s): {c.vencidos.map((v) => v.nombre).join(', ')}. Agenda una visita.
              </p>
            )}
            <ul className="linea-tiempo">
              {c.aplicados.map((a) => (
                <li key={a.id} className="hecho">
                  <strong>{a.nombre}</strong> · dosis {a.dosis}
                  <div className="apagado">Aplicado el {fecha(a.fecha_aplicacion)}</div>
                </li>
              ))}
              {c.proximos.map((a) => (
                <li key={a.id}>
                  <strong>{a.nombre}</strong> · dosis {a.dosis}
                  <div className="apagado">Programado para el {fecha(a.fecha_programada)}</div>
                </li>
              ))}
            </ul>
            {c.aplicados.length === 0 && c.proximos.length === 0 && <p className="apagado">Aún no hay preventivos registrados.</p>}
          </div>
        )}
      </Consulta>
    </section>
  )
}

function HistoriaPortal({ mascotaId }: { mascotaId: string }) {
  const historia = useHistoriaPortal(mascotaId)
  return (
    <section className="tarjeta">
      <Consulta consulta={historia} cargando="Cargando la historia…" error="No pudimos cargar la historia." vacio="Aún no hay consultas registradas." estaVacio={(d) => d.length === 0}>
        {(d) => (
          <ol className="linea-tiempo">
            {d.map((e) => (
              <li key={e.id} className="hecho">
                <strong className="numero">{fecha(e.fecha)}</strong> · {e.motivo}
                {e.diagnostico && <p>Diagnóstico: {e.diagnostico}</p>}
                {e.tratamiento && <p className="apagado">Tratamiento: {e.tratamiento}</p>}
              </li>
            ))}
          </ol>
        )}
      </Consulta>
    </section>
  )
}

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

function SelectorCupo({ tipo, valor, onCambio }: { tipo: string; valor: string; onCambio: (inicio: string) => void }) {
  const [dia, setDia] = useState(hoyISO())
  const cupos = useDisponibilidadPortal(dia, tipo)
  return (
    <>
      <label className="campo">
        <span>Día</span>
        <input className="input" type="date" min={hoyISO()} value={dia} onChange={(e) => { setDia(e.target.value); onCambio('') }} />
      </label>
      <div className="ancho">
        {!tipo ? (
          <p className="apagado">Elige el tipo de visita para ver los horarios.</p>
        ) : cupos.isPending ? (
          <p className="apagado">Buscando horarios…</p>
        ) : cupos.isError ? (
          <p className="error" role="alert">
            {mensajeError(cupos.error, 'No pudimos consultar la agenda.')}
          </p>
        ) : cupos.data.filter((c) => c.disponibles > 0).length === 0 ? (
          <p className="apagado">No hay horarios ese día. Prueba otra fecha.</p>
        ) : (
          <div className="cupos" role="group" aria-label="Horarios disponibles">
            {cupos.data
              .filter((c) => c.disponibles > 0)
              .map((c) => (
                <button key={c.inicio} type="button" className="cupo" aria-pressed={valor === c.inicio} onClick={() => onCambio(c.inicio)}>
                  {hora(c.inicio)}
                </button>
              ))}
          </div>
        )}
      </div>
    </>
  )
}

function AgendarModal({ abierto, onCerrar }: { abierto: boolean; onCerrar: () => void }) {
  const familia = useMiFamilia()
  const tipos = useTiposServicio()
  const agendar = useAgendarPortal()
  const [tipo, setTipo] = useState('')
  const [inicio, setInicio] = useState('')
  const enCasa = tipos.data?.filter((t) => t.activo && (t.modalidad === 'domiciliario' || t.modalidad === 'preventivo')) ?? []

  function cerrar() {
    agendar.reset()
    setTipo('')
    setInicio('')
    onCerrar()
  }

  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => !v && cerrar()}
      titulo="Agendar una visita"
      descripcion="Te confirmamos por WhatsApp. Algunos servicios requieren autorización antes de confirmarse."
      pie={
        !agendar.isSuccess && (
          <button className="btn btn-primario" type="submit" form="agendar-portal" disabled={!inicio || agendar.isPending}>
            Agendar
          </button>
        )
      }
    >
      {agendar.isSuccess ? (
        <p className="aviso-ok" role="status">
          ¡Listo! Tu visita quedó para el {fechaHora(agendar.data.programado_para)}.
        </p>
      ) : (
        <form
          id="agendar-portal"
          className="formulario"
          onSubmit={(e) => {
            e.preventDefault()
            const d = new FormData(e.currentTarget)
            agendar.mutate({
              mascota_id: String(d.get('mascota_id')),
              tipo_codigo: tipo,
              inicio,
              observaciones: String(d.get('observaciones') ?? '').trim() || undefined,
            })
          }}
        >
          <label className="campo">
            <span>Mascota</span>
            <select className="input" name="mascota_id" required>
              {familia.data?.mascotas
                ?.filter((m) => m.activa)
                .map((m) => (
                  <option key={m.id} value={m.id}>{m.nombre}</option>
                ))}
            </select>
          </label>
          <label className="campo">
            <span>Tipo de visita</span>
            <select className="input" value={tipo} onChange={(e) => { setTipo(e.target.value); setInicio('') }} required>
              <option value="" disabled>Elige</option>
              {enCasa.map((t) => (
                <option key={t.codigo} value={t.codigo}>{t.nombre}</option>
              ))}
            </select>
          </label>
          <SelectorCupo tipo={tipo} valor={inicio} onCambio={setInicio} />
          <label className="campo ancho">
            <span>¿Algo que debamos saber? (opcional)</span>
            <textarea className="input" name="observaciones" rows={2} />
          </label>
          {agendar.isError && (
            <p className="error ancho" role="alert">
              {mensajeError(agendar.error, 'No pudimos agendar la visita.')}
            </p>
          )}
        </form>
      )}
    </Modal>
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
                      <Distintivo dominio="cuota" valor={q.estado} />
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
              for (const campo of ['email', 'telefono', 'direccion'] as const) {
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
            <label className="campo ancho">
              <span>Dirección de las visitas</span>
              <input className="input" name="direccion" defaultValue={f.direccion ?? ''} />
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
  )
}
