import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { Paginacion } from '@/components/Paginacion'
import { Pestanas } from '@/components/Pestanas'
import { useAuth } from '@/features/auth/AuthContext'
import { useFamilia } from '@/features/familias/api'
import { SelectorFamilia } from '@/features/familias/SelectorFamilia'
import { useDisponibilidad } from '@/features/servicios/api'
import { mensajeError } from '@/lib/errores'
import { fecha, hora, hoyISO } from '@/lib/formato'
import { puede } from '@/lib/permisos'
import type { EventoRead, FamiliaRead } from '@/types'

import {
  useAgendarPreventivo,
  useAplicarPreventivo,
  useAutorizarPreventivo,
  useCancelarPreventivo,
  useCarnet,
  useEmitirCarnet,
  useGenerarCalendario,
  useMascotas,
  usePreventivos,
  type FilaCarnet,
  type FiltrosPreventivos,
  type MedioAutorizacion,
} from './api'

const TIPOS: Record<string, string> = {
  vacuna: 'Vacuna',
  desparasitacion_interna: 'Desparasitación interna',
  desparasitacion_externa: 'Desparasitación externa',
}
// Mismo mapa que preventivos/service.py: TIPO_SERVICIO.
const TIPO_SERVICIO: Record<string, string> = {
  vacuna: 'vacunacion',
  desparasitacion_interna: 'desparasitacion',
  desparasitacion_externa: 'desparasitacion',
}

export function PreventivosPage() {
  const [params] = useSearchParams()
  return (
    <Pestanas
      etiqueta="Secciones de preventivos"
      pestanas={[
        { valor: 'agenda', titulo: 'Calendario preventivo', contenido: <Calendario porAutorizar={params.get('autorizacion') === '1'} /> },
        { valor: 'carnet', titulo: 'Carnet por mascota', contenido: <CarnetMascota /> },
      ]}
    />
  )
}

const POR_PAGINA = 25

function Calendario({ porAutorizar }: { porAutorizar: boolean }) {
  const [estado, setEstado] = useState<FiltrosPreventivos['estado'] | ''>('programado')
  const [soloAutorizacion, setSoloAutorizacion] = useState(porAutorizar)
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')
  const [offset, setOffset] = useState(0)
  const [gestionando, setGestionando] = useState<EventoRead | null>(null)
  const eventos = usePreventivos({
    estado: estado || undefined,
    pendientes_autorizacion: soloAutorizacion || undefined,
    desde: desde || undefined,
    hasta: hasta || undefined,
    limit: POR_PAGINA,
    offset,
  })
  const mascotas = useMascotas(eventos.data?.items.map((e) => e.mascota_id) ?? [])
  const hoy = hoyISO()

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Calendario preventivo</h3>
        <span className="apagado numero">{eventos.data?.total ?? 0} eventos</span>
      </div>
      <div className="filtros" style={{ marginBottom: 'var(--e4)' }}>
        <select className="input" style={{ width: 'auto' }} value={estado} onChange={(e) => { setEstado(e.target.value as FiltrosPreventivos['estado'] | ''); setOffset(0) }} aria-label="Estado">
          <option value="programado">Programados</option>
          <option value="aplicado">Aplicados</option>
          <option value="cancelado">Cancelados</option>
          <option value="">Todos</option>
        </select>
        <label className="acciones">
          Desde
          <input className="input" style={{ width: 'auto' }} type="date" value={desde} onChange={(e) => { setDesde(e.target.value); setOffset(0) }} />
        </label>
        <label className="acciones">
          Hasta
          <input className="input" style={{ width: 'auto' }} type="date" value={hasta} onChange={(e) => { setHasta(e.target.value); setOffset(0) }} />
        </label>
        <label className="acciones">
          <input type="checkbox" checked={soloAutorizacion} onChange={(e) => { setSoloAutorizacion(e.target.checked); setOffset(0) }} />
          Sólo por autorizar
        </label>
      </div>
      <Consulta
        consulta={eventos}
        cargando="Cargando el calendario…"
        error="No fue posible cargar el calendario."
        vacio="No hay eventos preventivos con estos filtros."
        estaVacio={(d) => d.items.length === 0}
      >
        {(d) => (
          <>
            <div className="scroll-x">
              <table className="tabla">
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Mascota</th>
                    <th>Preventivo</th>
                    <th>Autorización</th>
                    <th>Estado</th>
                    <th><span className="sr-only">Acciones</span></th>
                  </tr>
                </thead>
                <tbody>
                  {d.items.map((e) => {
                    const m = mascotas.get(e.mascota_id)
                    const vencido = e.estado === 'programado' && e.fecha_programada < hoy
                    return (
                      <tr key={e.id}>
                        <td className={`numero${vencido ? ' error' : ''}`}>{fecha(e.fecha_programada)}</td>
                        <td className="principal">
                          {m ? <Link to={`/familias/${m.familia_id}`}>{m.nombre}</Link> : '…'}
                        </td>
                        <td>
                          {TIPOS[e.tipo] ?? e.tipo} · dosis {e.dosis_numero}
                          {e.es_refuerzo && ' (refuerzo)'}
                        </td>
                        <td>
                          {!e.requiere_autorizacion ? (
                            <span className="apagado">No requiere</span>
                          ) : e.autorizado ? (
                            <span className="distintivo distintivo-ok">Autorizado</span>
                          ) : (
                            <span className="distintivo distintivo-alerta">Por autorizar</span>
                          )}
                        </td>
                        <td>
                          <Distintivo dominio="preventivo" valor={vencido ? 'vencido' : e.estado} />
                          {e.servicio_id && (
                            <div>
                              <Link to={`/servicios/${e.servicio_id}`}>Servicio agendado</Link>
                            </div>
                          )}
                        </td>
                        <td>
                          {e.estado === 'programado' && (
                            <button className="btn btn-suave" type="button" onClick={() => setGestionando(e)}>
                              Gestionar
                            </button>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
            <Paginacion total={d.total} limit={d.limit} offset={d.offset} onCambio={setOffset} />
          </>
        )}
      </Consulta>
      <GestionPreventivo evento={gestionando} onCerrar={() => setGestionando(null)} />
    </section>
  )
}

type Accion = 'autorizar' | 'agendar' | 'aplicar' | 'cancelar'

function GestionPreventivo({ evento, onCerrar }: { evento: EventoRead | null; onCerrar: () => void }) {
  const { usuario } = useAuth()
  const [accion, setAccion] = useState<Accion | null>(null)
  const autorizar = useAutorizarPreventivo()
  const agendar = useAgendarPreventivo()
  const aplicar = useAplicarPreventivo()
  const cancelar = useCancelarPreventivo()
  const error = autorizar.error ?? agendar.error ?? aplicar.error ?? cancelar.error
  const pendiente = autorizar.isPending || agendar.isPending || aplicar.isPending || cancelar.isPending

  function cerrar() {
    for (const m of [autorizar, agendar, aplicar, cancelar]) m.reset()
    setAccion(null)
    onCerrar()
  }

  if (!evento) return null
  const porAutorizar = evento.requiere_autorizacion && !evento.autorizado
  const disponibles: { valor: Accion; label: string }[] = [
    ...(porAutorizar ? [{ valor: 'autorizar' as const, label: 'Registrar autorización' }] : []),
    ...(!evento.servicio_id && !porAutorizar ? [{ valor: 'agendar' as const, label: 'Agendar visita' }] : []),
    ...(puede(usuario, 'clinico') && !porAutorizar ? [{ valor: 'aplicar' as const, label: 'Registrar aplicación' }] : []),
    { valor: 'cancelar', label: 'Cancelar' },
  ]

  return (
    <Modal
      abierto
      onCambio={(v) => !v && cerrar()}
      titulo={`${TIPOS[evento.tipo] ?? evento.tipo} · dosis ${evento.dosis_numero}`}
      descripcion={`Programado para el ${fecha(evento.fecha_programada)}.`}
    >
      <div className="pila">
        <div className="acciones" role="group" aria-label="Acción">
          {disponibles.map((a) => (
            <button
              key={a.valor}
              type="button"
              className={`btn ${accion === a.valor ? 'btn-primario' : 'btn-suave'}`}
              aria-pressed={accion === a.valor}
              onClick={() => setAccion(a.valor)}
            >
              {a.label}
            </button>
          ))}
        </div>

        {accion === 'autorizar' && (
          <FormAutorizacion
            pendiente={pendiente}
            onEnviar={(medio, aprobado) => autorizar.mutate({ id: evento.id, medio, aprobado }, { onSuccess: cerrar })}
          />
        )}
        {accion === 'agendar' && (
          <FormAgendar
            evento={evento}
            pendiente={pendiente}
            onEnviar={(inicio) => agendar.mutate({ id: evento.id, inicio }, { onSuccess: cerrar })}
          />
        )}
        {accion === 'aplicar' && (
          <form
            className="formulario"
            onSubmit={(e) => {
              e.preventDefault()
              const d = new FormData(e.currentTarget)
              aplicar.mutate(
                {
                  id: evento.id,
                  fecha: String(d.get('fecha')),
                  producto: String(d.get('producto')).trim(),
                  lote: String(d.get('lote') ?? '').trim() || undefined,
                },
                { onSuccess: cerrar },
              )
            }}
          >
            <label className="campo">
              <span>Fecha de aplicación</span>
              <input className="input" name="fecha" type="date" max={hoyISO()} defaultValue={hoyISO()} required />
            </label>
            <label className="campo">
              <span>Producto</span>
              <input className="input" name="producto" required />
            </label>
            <label className="campo">
              <span>Lote</span>
              <input className="input" name="lote" />
            </label>
            <div className="acciones ancho">
              <button className="btn btn-primario" type="submit" disabled={pendiente}>
                Registrar aplicación
              </button>
            </div>
          </form>
        )}
        {accion === 'cancelar' && (
          <form
            className="formulario"
            onSubmit={(e) => {
              e.preventDefault()
              const motivo = String(new FormData(e.currentTarget).get('motivo')).trim()
              cancelar.mutate({ id: evento.id, motivo }, { onSuccess: cerrar })
            }}
          >
            <label className="campo ancho">
              <span>Motivo de la cancelación</span>
              <textarea className="input" name="motivo" rows={2} required minLength={3} />
            </label>
            <div className="acciones ancho">
              <button className="btn btn-primario" type="submit" disabled={pendiente}>
                Cancelar preventivo
              </button>
            </div>
          </form>
        )}
        {error && (
          <p className="error" role="alert">
            {mensajeError(error, 'No fue posible completar la acción.')}
          </p>
        )}
      </div>
    </Modal>
  )
}

function FormAutorizacion({ pendiente, onEnviar }: { pendiente: boolean; onEnviar: (m: MedioAutorizacion, ok: boolean) => void }) {
  const [medio, setMedio] = useState<MedioAutorizacion>('whatsapp')
  return (
    <div className="formulario">
      <label className="campo ancho">
        <span>Medio por el que respondió la familia</span>
        <select className="input" value={medio} onChange={(e) => setMedio(e.target.value as MedioAutorizacion)}>
          <option value="whatsapp">WhatsApp</option>
          <option value="telefono">Teléfono</option>
          <option value="presencial">Presencial</option>
          <option value="portal">Portal</option>
          <option value="formulario">Formulario</option>
        </select>
      </label>
      <div className="acciones ancho">
        <button className="btn btn-primario" type="button" disabled={pendiente} onClick={() => onEnviar(medio, true)}>
          La familia autorizó
        </button>
        <button className="btn btn-plano" type="button" disabled={pendiente} onClick={() => onEnviar(medio, false)}>
          No autorizó
        </button>
      </div>
    </div>
  )
}

function FormAgendar({ evento, pendiente, onEnviar }: { evento: EventoRead; pendiente: boolean; onEnviar: (inicio: string) => void }) {
  const mascota = useMascotas([evento.mascota_id]).get(evento.mascota_id)
  const familia = useFamilia(mascota?.familia_id)
  const [dia, setDia] = useState(evento.fecha_programada < hoyISO() ? hoyISO() : evento.fecha_programada)
  const [inicio, setInicio] = useState('')
  const cupos = useDisponibilidad(
    familia.data ? { fecha: dia, ciudad: familia.data.ciudad, tipo_codigo: TIPO_SERVICIO[evento.tipo] ?? 'vacunacion' } : null,
  )
  return (
    <div className="formulario">
      <label className="campo">
        <span>Día de la visita</span>
        <input className="input" type="date" min={hoyISO()} value={dia} onChange={(e) => { setDia(e.target.value); setInicio('') }} />
      </label>
      <div className="ancho">
        {cupos.isPending ? (
          <p className="apagado">Buscando cupos…</p>
        ) : cupos.data?.length === 0 ? (
          <p className="apagado">No hay franjas ese día.</p>
        ) : (
          <div className="cupos" role="group" aria-label="Franjas disponibles">
            {cupos.data?.map((c) => (
              <button
                key={c.inicio}
                type="button"
                className="cupo"
                aria-pressed={inicio === c.inicio}
                disabled={c.disponibles === 0}
                onClick={() => setInicio(c.inicio)}
              >
                {hora(c.inicio)}
              </button>
            ))}
          </div>
        )}
      </div>
      <div className="acciones ancho">
        <button className="btn btn-primario" type="button" disabled={!inicio || pendiente} onClick={() => onEnviar(inicio)}>
          Agendar visita
        </button>
      </div>
    </div>
  )
}

function CarnetMascota() {
  const [familia, setFamilia] = useState<FamiliaRead | null>(null)
  const [mascotaId, setMascotaId] = useState<string | null>(null)
  const carnet = useCarnet(mascotaId)
  const generar = useGenerarCalendario()
  const emitir = useEmitirCarnet()
  const mascotas = familia?.mascotas?.filter((m) => m.activa) ?? []

  return (
    <div className="pila">
      <section className="tarjeta">
        <div className="formulario">
          <div className="ancho">
            <SelectorFamilia
              valor={familia}
              onCambio={(f) => {
                setFamilia(f)
                setMascotaId(f?.mascotas?.find((m) => m.activa)?.id ?? null)
                generar.reset()
                emitir.reset()
              }}
            />
          </div>
          {familia && (
            <label className="campo">
              <span>Mascota</span>
              <select className="input" value={mascotaId ?? ''} onChange={(e) => setMascotaId(e.target.value || null)}>
                {mascotas.map((m) => (
                  <option key={m.id} value={m.id}>{m.nombre}</option>
                ))}
              </select>
            </label>
          )}
        </div>
      </section>

      {mascotaId && (
        <section className="tarjeta">
          <div className="tarjeta-cabeza">
            <h3>Carnet de {carnet.data?.mascota.nombre ?? '…'}</h3>
            <div className="acciones">
              <button className="btn btn-suave" type="button" disabled={generar.isPending} onClick={() => generar.mutate(mascotaId)}>
                Generar calendario
              </button>
              <button className="btn btn-primario" type="button" disabled={emitir.isPending} onClick={() => emitir.mutate(mascotaId)}>
                <Icono nombre="descargar" size={16} /> Emitir carnet PDF
              </button>
            </div>
          </div>
          {generar.isSuccess && (
            <p className="aviso-ok" role="status">
              Calendario actualizado: {generar.data.length} eventos nuevos.
            </p>
          )}
          {emitir.isSuccess && (
            <p className="aviso-ok" role="status">
              Carnet emitido con código <strong className="numero">{emitir.data.codigo}</strong>.{' '}
              <a href={emitir.data.url} target="_blank" rel="noreferrer">Abrir PDF</a> ·{' '}
              <Link to={`/verificar/${emitir.data.codigo}`}>Página de verificación</Link>
            </p>
          )}
          {(generar.isError || emitir.isError) && (
            <p className="error" role="alert">
              {mensajeError(generar.error ?? emitir.error, 'No fue posible completar la acción.')}
            </p>
          )}
          <Consulta consulta={carnet} cargando="Cargando el carnet…" error="No fue posible cargar el carnet.">
            {(c) => (
              <div className="tres-columnas">
                <ListaCarnet titulo="Aplicados" filas={c.aplicados} vacio="Aún no hay aplicaciones registradas." tono="ok" />
                <ListaCarnet titulo="Vencidos" filas={c.vencidos} vacio="Nada vencido." tono="peligro" />
                <ListaCarnet titulo="Próximos" filas={c.proximos} vacio="Sin programación. Genera el calendario." tono="info" />
              </div>
            )}
          </Consulta>
        </section>
      )}
    </div>
  )
}

function ListaCarnet({ titulo, filas, vacio, tono }: { titulo: string; filas: FilaCarnet[]; vacio: string; tono: string }) {
  return (
    <div>
      <h4 className="subtitulo">
        {titulo} <span className={`distintivo distintivo-${tono}`}>{filas.length}</span>
      </h4>
      {filas.length === 0 ? (
        <p className="apagado">{vacio}</p>
      ) : (
        <ul className="pila" style={{ listStyle: 'none', margin: 0, padding: 0, gap: 'var(--e2)' }}>
          {filas.map((f) => (
            <li key={f.id} className="fila">
              <span className="fila-icono">
                <Icono nombre="preventivos" size={16} />
              </span>
              <span className="fila-cuerpo">
                <strong>
                  {f.nombre} · dosis {f.dosis}
                </strong>
                <span>
                  {f.fecha_aplicacion ? `Aplicado ${fecha(f.fecha_aplicacion)}` : `Programado ${fecha(f.fecha_programada)}`}
                  {f.producto ? ` · ${f.producto}` : ''}
                  {f.lote ? ` · lote ${f.lote}` : ''}
                </span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
