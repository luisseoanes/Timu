import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo, Insignia } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { Pestanas } from '@/components/Pestanas'
import { useAuth } from '@/features/auth'
import { useCiudades } from '@/features/catalogos'
import { mensajeError } from '@/lib/errores'
import { estado as etiquetaEstado } from '@/lib/estados'
import { hoyISO } from '@/lib/formato'
import { puede } from '@/lib/permisos'
import type { FranjaRead, PendienteRead } from '@/types'

import {
  useActualizarFranja,
  useAutorizarPendiente,
  useAvancePendiente,
  useCrearBloqueo,
  useCrearFranja,
  useFranjas,
  usePendientes,
} from './api'
import { FichaServicio } from './FichaServicio'
import { ServiciosLista } from './ServiciosLista'


export function ServiciosPage({ abierto }: { abierto?: string }) {
  const { usuario } = useAuth()
  const [params] = useSearchParams()
  const pestanas = [
    { valor: 'agenda', titulo: 'Servicios', contenido: <Agenda abierto={abierto} nuevoInicial={params.get('nuevo') === '1'} /> },
    { valor: 'pendientes', titulo: 'Pendientes', contenido: <Pendientes /> },
  ]
  if (puede(usuario, 'gestionarAgenda')) {
    pestanas.push({ valor: 'franjas', titulo: 'Franjas de agenda', contenido: <Franjas /> })
  }
  return <Pestanas etiqueta="Secciones de servicios" pestanas={pestanas} />
}

/** La agenda: el listado y, al lado, el servicio abierto o qué aparecerá al elegir uno. */
function Agenda({ abierto, nuevoInicial }: { abierto?: string; nuevoInicial: boolean }) {
  return (
    <div className="con-ficha" data-abierta={abierto ? 'true' : undefined}>
      <ServiciosLista seleccionado={abierto} nuevoInicial={nuevoInicial} />
      {abierto ? (
        // La clave reinicia la ficha al cambiar de servicio: el paso abierto vuelve a decidirse.
        <FichaServicio key={abierto} id={abierto} />
      ) : (
        <section className="ficha-abierta ficha-vacia" aria-label="Servicio abierto">
          <p>Elige un servicio para ver a quién se atiende, su estado y su acción, y los pasos de la atención.</p>
        </section>
      )}
    </div>
  )
}

const MEDIOS = ['whatsapp', 'llamada', 'presencial', 'portal', 'correo'] as const

const NOMBRE_MEDIO: Record<(typeof MEDIOS)[number], string> = {
  whatsapp: 'WhatsApp',
  llamada: 'Llamada',
  presencial: 'En persona',
  portal: 'Portal de la familia',
  correo: 'Correo',
}

function Pendientes() {
  const [estado, setEstado] = useState('pendiente_autorizacion')
  const pendientes = usePendientes({ estado: estado || undefined })
  const [gestionando, setGestionando] = useState<PendienteRead | null>(null)

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Pendientes derivados de atenciones</h3>
        <select className="input servicios-filtro" value={estado} onChange={(e) => setEstado(e.target.value)} aria-label="Estado del pendiente">
          <option value="">Todos</option>
          {['pendiente_autorizacion', 'autorizado', 'en_gestion', 'resuelto', 'rechazado'].map((e) => (
            <option key={e} value={e}>{etiquetaEstado('pendiente', e).label}</option>
          ))}
        </select>
      </div>
      <Consulta
        consulta={pendientes}
        cargando="Cargando pendientes…"
        error="No fue posible cargar los pendientes."
        vacio="No hay pendientes en este estado."
        estaVacio={(d) => d.length === 0}
      >
        {(d) => (
          <div className="scroll-x">
            <table className="tabla tabla-apilable">
              <thead>
                <tr>
                  <th>Pendiente</th>
                  <th>Servicio de origen</th>
                  <th>Estado</th>
                  <th><span className="sr-only">Acciones</span></th>
                </tr>
              </thead>
              <tbody>
                {d.map((p) => (
                  <tr key={p.id}>
                    <td className="principal" data-etiqueta="Pendiente">{p.descripcion}</td>
                    <td data-etiqueta="Servicio de origen">
                      <Link to={`/servicios/${p.servicio_origen_id}`}>Ver el servicio</Link>
                    </td>
                    <td data-etiqueta="Estado">
                      <Distintivo dominio="pendiente" valor={p.estado} />
                    </td>
                    <td className="tabla-acciones">
                      {p.estado !== 'resuelto' && p.estado !== 'rechazado' && (
                        <button className="btn btn-suave" type="button" onClick={() => setGestionando(p)}>
                          Gestionar
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Consulta>
      <GestionPendiente pendiente={gestionando} onCerrar={() => setGestionando(null)} />
    </section>
  )
}

function GestionPendiente({ pendiente, onCerrar }: { pendiente: PendienteRead | null; onCerrar: () => void }) {
  const autorizar = useAutorizarPendiente()
  const avanzar = useAvancePendiente()
  const [medio, setMedio] = useState<(typeof MEDIOS)[number]>('whatsapp')
  const [resolucion, setResolucion] = useState('')
  const error = autorizar.error ?? avanzar.error
  const porAutorizar = pendiente?.estado === 'pendiente_autorizacion'

  function cerrar() {
    autorizar.reset()
    avanzar.reset()
    setResolucion('')
    onCerrar()
  }

  return (
    <Modal
      abierto={pendiente !== null}
      onCambio={(v) => !v && cerrar()}
      titulo="Gestionar pendiente"
      descripcion={pendiente?.descripcion}
    >
      {porAutorizar ? (
        <div className="formulario">
          <label className="campo ancho">
            <span>Medio por el que la familia autorizó</span>
            <select className="input" value={medio} onChange={(e) => setMedio(e.target.value as (typeof MEDIOS)[number])}>
              {MEDIOS.map((m) => (
                <option key={m} value={m}>{NOMBRE_MEDIO[m]}</option>
              ))}
            </select>
          </label>
          <div className="acciones ancho">
            <button
              className="btn btn-primario"
              type="button"
              disabled={autorizar.isPending}
              onClick={() => pendiente && autorizar.mutate({ id: pendiente.id, aprobado: true, medio }, { onSuccess: cerrar })}
            >
              Autorizado por la familia
            </button>
            <button
              className="btn btn-plano"
              type="button"
              disabled={autorizar.isPending}
              onClick={() => pendiente && autorizar.mutate({ id: pendiente.id, aprobado: false, medio }, { onSuccess: cerrar })}
            >
              La familia no lo autorizó
            </button>
          </div>
        </div>
      ) : (
        <div className="formulario">
          <label className="campo ancho">
            <span>Resolución</span>
            <textarea className="input" rows={3} value={resolucion} onChange={(e) => setResolucion(e.target.value)} />
          </label>
          <div className="acciones ancho">
            {pendiente?.estado !== 'en_gestion' && (
              <button
                className="btn btn-suave"
                type="button"
                disabled={avanzar.isPending}
                onClick={() => pendiente && avanzar.mutate({ id: pendiente.id, estado: 'en_gestion' }, { onSuccess: cerrar })}
              >
                Pasar a gestión
              </button>
            )}
            <button
              className="btn btn-primario"
              type="button"
              disabled={avanzar.isPending || !resolucion.trim()}
              onClick={() =>
                pendiente &&
                avanzar.mutate({ id: pendiente.id, estado: 'resuelto', resolucion: resolucion.trim() }, { onSuccess: cerrar })
              }
            >
              Marcar resuelto
            </button>
          </div>
        </div>
      )}
      {error && (
        <p className="error" role="alert">
          {mensajeError(error, 'No fue posible actualizar el pendiente.')}
        </p>
      )}
    </Modal>
  )
}

const DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
const MODALIDADES: FranjaRead['modalidad'][] = ['domiciliario', 'preventivo', 'clinico', 'virtual', 'aliada']

const NOMBRE_MODALIDAD: Record<FranjaRead['modalidad'], string> = {
  domiciliario: 'A domicilio',
  preventivo: 'Preventiva',
  clinico: 'En la clínica',
  virtual: 'Virtual',
  aliada: 'Clínica aliada',
}

function Franjas() {
  const [ciudad, setCiudad] = useState('')
  const ciudades = useCiudades()
  const franjas = useFranjas(ciudad || undefined)
  const actualizar = useActualizarFranja()
  const [nueva, setNueva] = useState(false)
  const [bloqueo, setBloqueo] = useState(false)

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Franjas de agenda</h3>
        <div className="acciones">
          <button className="btn btn-plano" type="button" onClick={() => setBloqueo(true)}>
            Bloquear un día
          </button>
          <button className="btn btn-primario" type="button" onClick={() => setNueva(true)}>
            <Icono nombre="mas" size={16} /> Nueva franja
          </button>
        </div>
      </div>
      <div className="filtros servicios-tabla-filtros">
        <select className="input servicios-filtro" value={ciudad} onChange={(e) => setCiudad(e.target.value)} aria-label="Ciudad de las franjas">
          <option value="">Todas las ciudades</option>
          {ciudades.data?.map((c) => (
            <option key={c.codigo} value={c.nombre}>{c.nombre}</option>
          ))}
        </select>
      </div>
      <Consulta
        consulta={franjas}
        cargando="Cargando franjas…"
        error="No fue posible cargar las franjas."
        vacio="No hay franjas configuradas. Sin franjas no se puede agendar."
        estaVacio={(d) => d.length === 0}
      >
        {(d) => (
          <div className="scroll-x">
            <table className="tabla tabla-apilable">
              <thead>
                <tr>
                  <th>Día y horario</th>
                  <th>Ciudad</th>
                  <th>Modalidad</th>
                  <th>Capacidad</th>
                  <th>Estado</th>
                  <th><span className="sr-only">Acciones</span></th>
                </tr>
              </thead>
              <tbody>
                {d.map((f) => (
                  <tr key={f.id}>
                    <td className="principal" data-etiqueta="Día y horario">
                      {DIAS[f.dia_semana] ?? f.dia_semana} <span className="numero">{f.hora_inicio.slice(0, 5)} – {f.hora_fin.slice(0, 5)}</span>
                    </td>
                    <td data-etiqueta="Ciudad">{f.ciudad}</td>
                    <td data-etiqueta="Modalidad">{NOMBRE_MODALIDAD[f.modalidad]}</td>
                    <td className="numero" data-etiqueta="Capacidad">
                      {f.capacidad === 1 ? '1 servicio' : `${f.capacidad} servicios`}
                    </td>
                    <td data-etiqueta="Estado">
                      <Insignia tono={f.activa ? 'ok' : 'neutro'}>{f.activa ? 'Activa' : 'Inactiva'}</Insignia>
                    </td>
                    <td className="tabla-acciones">
                      <button
                        className="btn btn-plano"
                        type="button"
                        onClick={() => actualizar.mutate({ id: f.id, activa: !f.activa })}
                        aria-label={`${f.activa ? 'Desactivar' : 'Activar'} franja ${DIAS[f.dia_semana]} ${f.hora_inicio.slice(0, 5)}`}
                      >
                        {f.activa ? 'Desactivar' : 'Activar'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Consulta>
      <NuevaFranjaModal abierto={nueva} onCerrar={() => setNueva(false)} />
      <BloqueoModal abierto={bloqueo} onCerrar={() => setBloqueo(false)} />
    </section>
  )
}

function NuevaFranjaModal({ abierto, onCerrar }: { abierto: boolean; onCerrar: () => void }) {
  const crear = useCrearFranja()
  const ciudades = useCiudades()

  function guardar(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const d = new FormData(e.currentTarget)
    crear.mutate(
      {
        ciudad: String(d.get('ciudad')),
        modalidad: d.get('modalidad') as FranjaRead['modalidad'],
        dia_semana: Number(d.get('dia_semana')),
        hora_inicio: String(d.get('hora_inicio')),
        hora_fin: String(d.get('hora_fin')),
        capacidad: Number(d.get('capacidad')),
      },
      { onSuccess: onCerrar },
    )
  }

  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          crear.reset()
          onCerrar()
        }
      }}
      titulo="Nueva franja"
      descripcion="Bloque semanal en que se pueden agendar servicios de una modalidad en una ciudad."
      pie={
        <button className="btn btn-primario" type="submit" form="nueva-franja" disabled={crear.isPending}>
          Guardar franja
        </button>
      }
    >
      <form id="nueva-franja" className="formulario" onSubmit={guardar}>
        <label className="campo">
          <span>Ciudad</span>
          <select className="input" name="ciudad" required defaultValue="">
            <option value="" disabled>Selecciona</option>
            {ciudades.data?.map((c) => (
              <option key={c.codigo} value={c.nombre}>{c.nombre}</option>
            ))}
          </select>
        </label>
        <label className="campo">
          <span>Modalidad</span>
          <select className="input" name="modalidad" defaultValue="domiciliario">
            {MODALIDADES.map((m) => (
              <option key={m} value={m}>{NOMBRE_MODALIDAD[m]}</option>
            ))}
          </select>
        </label>
        <label className="campo">
          <span>Día</span>
          <select className="input" name="dia_semana" defaultValue="0">
            {DIAS.map((d, i) => (
              <option key={d} value={i}>{d}</option>
            ))}
          </select>
        </label>
        <label className="campo">
          <span>Capacidad (servicios simultáneos)</span>
          <input className="input" name="capacidad" type="number" min={1} defaultValue={1} required />
        </label>
        <label className="campo">
          <span>Desde</span>
          <input className="input" name="hora_inicio" type="time" required defaultValue="08:00" />
        </label>
        <label className="campo">
          <span>Hasta</span>
          <input className="input" name="hora_fin" type="time" required defaultValue="12:00" />
        </label>
        {crear.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(crear.error, 'No fue posible crear la franja.')}
          </p>
        )}
      </form>
    </Modal>
  )
}

function BloqueoModal({ abierto, onCerrar }: { abierto: boolean; onCerrar: () => void }) {
  const bloquear = useCrearBloqueo()
  const ciudades = useCiudades()

  function guardar(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const d = new FormData(e.currentTarget)
    bloquear.mutate(
      {
        fecha: String(d.get('fecha')),
        ciudad: String(d.get('ciudad')) || undefined,
        modalidad: String(d.get('modalidad')) || undefined,
        motivo: String(d.get('motivo')).trim(),
      },
      { onSuccess: onCerrar },
    )
  }

  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          bloquear.reset()
          onCerrar()
        }
      }}
      titulo="Bloquear un día"
      descripcion="Festivos, capacitaciones o cierres: ese día no se ofrecen cupos."
      pie={
        <button className="btn btn-primario" type="submit" form="bloqueo" disabled={bloquear.isPending}>
          Bloquear
        </button>
      }
    >
      <form id="bloqueo" className="formulario" onSubmit={guardar}>
        <label className="campo">
          <span>Fecha</span>
          <input className="input" name="fecha" type="date" required min={hoyISO()} />
        </label>
        <label className="campo">
          <span>Ciudad</span>
          <select className="input" name="ciudad" defaultValue="">
            <option value="">Todas</option>
            {ciudades.data?.map((c) => (
              <option key={c.codigo} value={c.nombre}>{c.nombre}</option>
            ))}
          </select>
        </label>
        <label className="campo">
          <span>Modalidad</span>
          <select className="input" name="modalidad" defaultValue="">
            <option value="">Todas</option>
            {MODALIDADES.map((m) => (
              <option key={m} value={m}>{NOMBRE_MODALIDAD[m]}</option>
            ))}
          </select>
        </label>
        <label className="campo">
          <span>Motivo</span>
          <input className="input" name="motivo" required minLength={3} />
        </label>
        {bloquear.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(bloquear.error, 'No fue posible bloquear el día.')}
          </p>
        )}
      </form>
    </Modal>
  )
}
