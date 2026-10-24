import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { Paginacion } from '@/components/Paginacion'
import { Pestanas } from '@/components/Pestanas'
import { useAuth } from '@/features/auth/AuthContext'
import { useCiudades, useNombreTipoServicio } from '@/features/catalogos/api'
import { mensajeError } from '@/lib/errores'
import { estado as etiquetaEstado } from '@/lib/estados'
import { fechaHora, hoyISO } from '@/lib/formato'
import { puede } from '@/lib/permisos'
import type { EstadoServicio, FranjaRead, PendienteRead } from '@/types'

import {
  useActualizarFranja,
  useAutorizarPendiente,
  useAvancePendiente,
  useCrearBloqueo,
  useCrearFranja,
  useFranjas,
  usePendientes,
  useServicios,
} from './api'
import { NuevoServicioModal } from './NuevoServicioModal'

const ESTADOS: EstadoServicio[] = [
  'solicitado',
  'pendiente_autorizacion',
  'agendado',
  'reprogramado',
  'en_ruta',
  'en_atencion',
  'completado',
  'cancelado',
]

export function ServiciosPage() {
  const { usuario } = useAuth()
  const [params] = useSearchParams()
  const pestanas = [
    { valor: 'agenda', titulo: 'Servicios', contenido: <ListadoServicios nuevoInicial={params.get('nuevo') === '1'} /> },
    { valor: 'pendientes', titulo: 'Pendientes', contenido: <Pendientes /> },
  ]
  if (puede(usuario, 'gestionarAgenda')) {
    pestanas.push({ valor: 'franjas', titulo: 'Franjas de agenda', contenido: <Franjas /> })
  }
  return <Pestanas etiqueta="Secciones de servicios" pestanas={pestanas} />
}

const POR_PAGINA = 25

function ListadoServicios({ nuevoInicial }: { nuevoInicial: boolean }) {
  const [estado, setEstado] = useState<EstadoServicio | ''>('')
  const [ciudad, setCiudad] = useState('')
  const [desde, setDesde] = useState(hoyISO())
  const [hasta, setHasta] = useState('')
  const [offset, setOffset] = useState(0)
  const [nuevo, setNuevo] = useState(nuevoInicial)
  const ciudades = useCiudades()
  const nombreTipo = useNombreTipoServicio()
  const servicios = useServicios({
    estado: estado || undefined,
    ciudad: ciudad || undefined,
    desde: desde || undefined,
    hasta: hasta || undefined,
    limit: POR_PAGINA,
    offset,
    orden: 'programado_para',
  })
  const filtro = <T,>(set: (v: T) => void) => (v: T) => {
    set(v)
    setOffset(0)
  }

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Servicios</h3>
        <span className="apagado numero">{servicios.data?.total ?? 0} servicios</span>
      </div>
      <div className="filtros" style={{ marginBottom: 'var(--e4)' }}>
        <select className="input" style={{ width: 'auto' }} value={estado} onChange={(e) => filtro(setEstado)(e.target.value as EstadoServicio | '')} aria-label="Estado">
          <option value="">Todos los estados</option>
          {ESTADOS.map((e) => (
            <option key={e} value={e}>{etiquetaEstado('servicio', e).label}</option>
          ))}
        </select>
        <select className="input" style={{ width: 'auto' }} value={ciudad} onChange={(e) => filtro(setCiudad)(e.target.value)} aria-label="Ciudad">
          <option value="">Todas las ciudades</option>
          {ciudades.data?.map((c) => (
            <option key={c.codigo} value={c.nombre}>{c.nombre}</option>
          ))}
        </select>
        <label className="acciones">
          Desde
          <input className="input" style={{ width: 'auto' }} type="date" value={desde} onChange={(e) => filtro(setDesde)(e.target.value)} />
        </label>
        <label className="acciones">
          Hasta
          <input className="input" style={{ width: 'auto' }} type="date" value={hasta} onChange={(e) => filtro(setHasta)(e.target.value)} />
        </label>
        <button className="btn btn-primario" type="button" style={{ marginLeft: 'auto' }} onClick={() => setNuevo(true)}>
          <Icono nombre="mas" size={16} /> Agendar servicio
        </button>
      </div>
      <Consulta
        consulta={servicios}
        cargando="Cargando servicios…"
        error="No fue posible cargar los servicios."
        vacio="No hay servicios con estos filtros."
        estaVacio={(d) => d.items.length === 0}
      >
        {(d) => (
          <>
            <div className="scroll-x">
              <table className="tabla">
                <thead>
                  <tr>
                    <th>Programado</th>
                    <th>Servicio</th>
                    <th>Ciudad</th>
                    <th>Autorización</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {d.items.map((s) => (
                    <tr key={s.id}>
                      <td className="numero">{fechaHora(s.programado_para)}</td>
                      <td className="principal">
                        <Link to={`/servicios/${s.id}`}>{nombreTipo(s.tipo_codigo)}</Link>
                      </td>
                      <td>{s.ciudad}</td>
                      <td>
                        {s.requiere_autorizacion ? (
                          s.autorizado ? (
                            <span className="distintivo distintivo-ok">Autorizado</span>
                          ) : (
                            <span className="distintivo distintivo-alerta">Por autorizar</span>
                          )
                        ) : (
                          <span className="apagado">No requiere</span>
                        )}
                      </td>
                      <td>
                        <Distintivo dominio="servicio" valor={s.estado} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Paginacion total={d.total} limit={d.limit} offset={d.offset} onCambio={setOffset} />
          </>
        )}
      </Consulta>
      <NuevoServicioModal abierto={nuevo} onCambio={setNuevo} />
    </section>
  )
}

const MEDIOS = ['whatsapp', 'llamada', 'presencial', 'portal', 'correo'] as const

function Pendientes() {
  const [estado, setEstado] = useState('pendiente_autorizacion')
  const pendientes = usePendientes({ estado: estado || undefined })
  const [gestionando, setGestionando] = useState<PendienteRead | null>(null)

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Pendientes derivados de atenciones</h3>
        <select className="input" style={{ width: 'auto' }} value={estado} onChange={(e) => setEstado(e.target.value)} aria-label="Estado del pendiente">
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
            <table className="tabla">
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
                    <td className="principal">{p.descripcion}</td>
                    <td>
                      <Link to={`/servicios/${p.servicio_origen_id}`}>Ver servicio</Link>
                    </td>
                    <td>
                      <Distintivo dominio="pendiente" valor={p.estado} />
                    </td>
                    <td>
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
                <option key={m} value={m}>{m}</option>
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
      <div className="filtros" style={{ marginBottom: 'var(--e4)' }}>
        <select className="input" style={{ width: 'auto' }} value={ciudad} onChange={(e) => setCiudad(e.target.value)} aria-label="Ciudad de las franjas">
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
            <table className="tabla">
              <thead>
                <tr>
                  <th>Ciudad</th>
                  <th>Día</th>
                  <th>Horario</th>
                  <th>Modalidad</th>
                  <th>Capacidad</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {d.map((f) => (
                  <tr key={f.id}>
                    <td>{f.ciudad}</td>
                    <td>{DIAS[f.dia_semana] ?? f.dia_semana}</td>
                    <td className="numero">
                      {f.hora_inicio.slice(0, 5)} – {f.hora_fin.slice(0, 5)}
                    </td>
                    <td>{f.modalidad}</td>
                    <td className="numero">{f.capacidad}</td>
                    <td>
                      <button
                        className={`btn ${f.activa ? 'btn-suave' : 'btn-plano'}`}
                        type="button"
                        onClick={() => actualizar.mutate({ id: f.id, activa: !f.activa })}
                        aria-label={`${f.activa ? 'Desactivar' : 'Activar'} franja ${DIAS[f.dia_semana]} ${f.hora_inicio.slice(0, 5)}`}
                      >
                        {f.activa ? 'Activa' : 'Inactiva'}
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
              <option key={m} value={m}>{m}</option>
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
              <option key={m} value={m}>{m}</option>
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
