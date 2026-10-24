import { useState } from 'react'
import { Link } from 'react-router-dom'

import { AnilloProgreso } from '@/components/AnilloProgreso'
import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { useAuth } from '@/features/auth/AuthContext'
import { useCiudades, useNombreTipoServicio } from '@/features/catalogos/api'
import { useServicios } from '@/features/servicios/api'
import { useEquipo } from '@/features/tareas/api'
import { mensajeError } from '@/lib/errores'
import { fecha, hora, hoyISO } from '@/lib/formato'
import { puede } from '@/lib/permisos'
import type { ServicioRead } from '@/types'

import {
  useAccionParada,
  useAccionRuta,
  useAgregarParada,
  useOmitirParada,
  usePlanificacion,
  usePlanificar,
  usePorRutear,
  useRutas,
  useSalidaParada,
  type Parada,
  type ResultadoPlanificacion,
  type Ruta,
} from './api'

const MOTIVOS_SIN_ASIGNAR: Record<string, string> = {
  sin_ubicacion: 'la familia no tiene ubicación',
  no_cabe_en_la_jornada: 'no cabe en la jornada',
}

/** Rutas domiciliarias del día (6.7): planear con el optimizador y seguir cada parada en campo. */
export function RutasPage() {
  const { usuario } = useAuth()
  const ciudades = useCiudades()
  const [dia, setDia] = useState(hoyISO())
  const [ciudad, setCiudad] = useState('Bogota')
  const rutas = useRutas(dia, ciudad)
  const porRutear = usePorRutear(dia, ciudad)
  const servicios = useServicios({ desde: dia, hasta: dia, ciudad: ciudad || undefined, limit: 200 })
  const equipo = useEquipo()
  const [planeando, setPlaneando] = useState(false)
  const porId = new Map((servicios.data?.items ?? []).map((s) => [s.id, s]))
  const nombre = (id: string) => equipo.data?.find((m) => m.id === id)?.nombre ?? 'Responsable'

  const paradas = (rutas.data ?? []).filter((r) => r.estado !== 'cancelada').flatMap((r) => r.paradas)
  const completadas = paradas.filter((p) => p.estado === 'completada').length

  return (
    <div className="con-rail">
      <div className="pila">
        <section className="tarjeta">
          <div className="filtros">
            <label className="acciones">
              Día
              <input className="input" style={{ width: 'auto' }} type="date" value={dia} onChange={(e) => setDia(e.target.value)} />
            </label>
            <select className="input" style={{ width: 'auto' }} value={ciudad} onChange={(e) => setCiudad(e.target.value)} aria-label="Ciudad">
              {ciudades.data?.map((c) => (
                <option key={c.codigo} value={c.nombre}>{c.nombre}</option>
              ))}
            </select>
            {puede(usuario, 'planearRutas') && (
              <button className="btn btn-primario" type="button" style={{ marginLeft: 'auto' }} onClick={() => setPlaneando(true)}>
                <Icono nombre="rutas" size={16} /> Planear rutas
              </button>
            )}
          </div>
        </section>

        <Consulta
          consulta={rutas}
          cargando="Cargando rutas…"
          error="No fue posible cargar las rutas."
          vacio={`No hay rutas para el ${fecha(dia)} en ${ciudad}.`}
          estaVacio={(d) => d.length === 0}
        >
          {(d) => (
            <div className="pila">
              {d.map((r) => (
                <TarjetaRuta
                  key={r.id}
                  ruta={r}
                  responsable={nombre(r.responsable_id)}
                  servicios={porId}
                  porRutear={porRutear.data ?? []}
                />
              ))}
            </div>
          )}
        </Consulta>
      </div>

      <aside className="rail">
        <section className="tarjeta">
          <div className="tarjeta-cabeza">
            <h3>Cumplimiento del día</h3>
          </div>
          <AnilloProgreso valor={paradas.length ? Math.round((completadas / paradas.length) * 100) : 0} />
          <p className="apagado" style={{ textAlign: 'center' }}>
            {completadas} de {paradas.length} paradas completadas
          </p>
        </section>
        <section className="tarjeta">
          <div className="tarjeta-cabeza">
            <h3>Por rutear</h3>
            <span className="distintivo distintivo-alerta">{porRutear.data?.length ?? 0}</span>
          </div>
          <Consulta
            consulta={porRutear}
            cargando="Buscando servicios…"
            error="No fue posible consultar."
            vacio="Todos los servicios a domicilio del día tienen ruta."
            estaVacio={(d) => d.length === 0}
          >
            {(d) =>
              d.map((s) => (
                <Link key={s.id} to={`/servicios/${s.id}`} className="fila">
                  <span className="fila-icono">
                    <Icono nombre="servicios" size={16} />
                  </span>
                  <span className="fila-cuerpo">
                    <strong>{hora(s.programado_para)}</strong>
                  </span>
                </Link>
              ))
            }
          </Consulta>
        </section>
      </aside>

      <PlanearModal abierto={planeando} onCerrar={() => setPlaneando(false)} dia={dia} ciudad={ciudad} />
    </div>
  )
}

function TarjetaRuta({
  ruta,
  responsable,
  servicios,
  porRutear,
}: {
  ruta: Ruta
  responsable: string
  servicios: Map<string, ServicioRead>
  porRutear: { id: string; programado_para: string }[]
}) {
  const { usuario } = useAuth()
  const accion = useAccionRuta()
  const agregar = useAgregarParada()
  const [agregando, setAgregando] = useState('')
  const enCampo = puede(usuario, 'campo')
  const abierta = ruta.estado === 'planificada' || ruta.estado === 'en_curso'

  return (
    <section className="tarjeta" aria-label={`Ruta de ${responsable}`}>
      <div className="tarjeta-cabeza">
        <div className="acciones">
          <h3>{responsable}</h3>
          <Distintivo dominio="ruta" valor={ruta.estado} />
          <span className="apagado numero">
            {ruta.paradas.length} paradas
            {ruta.distancia_km !== null && ` · ${ruta.distancia_km.toFixed(1)} km`}
            {ruta.duracion_min !== null && ` · ${Math.round(ruta.duracion_min)} min`}
          </span>
        </div>
        <div className="acciones">
          {ruta.estado === 'planificada' && enCampo && (
            <button className="btn btn-primario" type="button" disabled={accion.isPending} onClick={() => accion.mutate({ id: ruta.id, accion: 'inicio' })}>
              Iniciar ruta
            </button>
          )}
          {abierta && puede(usuario, 'planearRutas') && (
            <button className="btn btn-plano" type="button" disabled={accion.isPending} onClick={() => accion.mutate({ id: ruta.id, accion: 'cancelacion' })}>
              Cancelar ruta
            </button>
          )}
        </div>
      </div>
      {accion.isError && (
        <p className="error" role="alert">
          {mensajeError(accion.error, 'No fue posible actualizar la ruta.')}
        </p>
      )}
      <ol className="linea-tiempo">
        {ruta.paradas.map((p) => (
          <li key={p.id} className={p.estado === 'completada' ? 'hecho' : ''}>
            <FilaParada parada={p} servicio={servicios.get(p.servicio_id)} activa={ruta.estado === 'en_curso' && enCampo} />
          </li>
        ))}
      </ol>
      {abierta && puede(usuario, 'planearRutas') && porRutear.length > 0 && (
        <div className="acciones" style={{ marginTop: 'var(--e4)' }}>
          <select className="input" style={{ width: 'auto' }} value={agregando} onChange={(e) => setAgregando(e.target.value)} aria-label="Servicio por agregar">
            <option value="">Agregar un servicio a esta ruta…</option>
            {porRutear.map((s) => (
              <option key={s.id} value={s.id}>{hora(s.programado_para)}</option>
            ))}
          </select>
          <button
            className="btn btn-suave"
            type="button"
            disabled={!agregando || agregar.isPending}
            onClick={() => agregar.mutate({ rutaId: ruta.id, servicioId: agregando }, { onSuccess: () => setAgregando('') })}
          >
            Agregar
          </button>
          {agregar.isError && (
            <span className="error" role="alert">
              {mensajeError(agregar.error, 'No fue posible agregar.')}
            </span>
          )}
        </div>
      )}
    </section>
  )
}

function FilaParada({ parada: p, servicio, activa }: { parada: Parada; servicio?: ServicioRead; activa: boolean }) {
  const nombreTipo = useNombreTipoServicio()
  const avanzar = useAccionParada()
  const [modal, setModal] = useState<'salida' | 'omision' | null>(null)
  const abierta = p.estado !== 'completada' && p.estado !== 'omitida'

  return (
    <div className="pila" style={{ gap: 'var(--e1)' }}>
      <div className="acciones">
        <strong className="numero">{p.orden}.</strong>
        {servicio ? <Link to={`/servicios/${servicio.id}`}>{nombreTipo(servicio.tipo_codigo)}</Link> : <span>Servicio</span>}
        <Distintivo dominio="ruta" valor={p.estado} />
        <span className="apagado numero">
          {p.llegada_en ? `Llegó ${hora(p.llegada_en)}` : `Estimada ${hora(p.llegada_estimada)}`}
        </span>
      </div>
      {p.nota && <p className="apagado">{p.nota}</p>}
      {p.motivo_omision && <p className="apagado">Omitida: {p.motivo_omision}</p>}
      {activa && abierta && (
        <div className="acciones">
          {p.estado === 'pendiente' && (
            <button className="btn btn-suave" type="button" disabled={avanzar.isPending} onClick={() => avanzar.mutate({ id: p.id, accion: 'en-camino' })}>
              En camino
            </button>
          )}
          {(p.estado === 'pendiente' || p.estado === 'en_camino') && (
            <button className="btn btn-suave" type="button" disabled={avanzar.isPending} onClick={() => avanzar.mutate({ id: p.id, accion: 'llegada' })}>
              Llegué
            </button>
          )}
          {p.estado === 'en_sitio' && (
            <button className="btn btn-primario" type="button" onClick={() => setModal('salida')}>
              Terminar visita
            </button>
          )}
          <button className="btn btn-plano" type="button" onClick={() => setModal('omision')}>
            Omitir
          </button>
        </div>
      )}
      {avanzar.isError && (
        <p className="error" role="alert">
          {mensajeError(avanzar.error, 'No fue posible actualizar la parada.')}
        </p>
      )}
      <SalidaModal paradaId={p.id} abierto={modal === 'salida'} onCerrar={() => setModal(null)} />
      <OmisionModal paradaId={p.id} abierto={modal === 'omision'} onCerrar={() => setModal(null)} />
    </div>
  )
}

function SalidaModal({ paradaId, abierto, onCerrar }: { paradaId: string; abierto: boolean; onCerrar: () => void }) {
  const salida = useSalidaParada()
  const [evidencia, setEvidencia] = useState<File | undefined>()
  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          salida.reset()
          onCerrar()
        }
      }}
      titulo="Terminar visita"
      pie={
        <button className="btn btn-primario" type="submit" form={`salida-${paradaId}`} disabled={salida.isPending}>
          Registrar salida
        </button>
      }
    >
      <form
        id={`salida-${paradaId}`}
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const nota = String(new FormData(e.currentTarget).get('nota') ?? '').trim()
          salida.mutate({ id: paradaId, nota: nota || undefined, evidencia }, { onSuccess: onCerrar })
        }}
      >
        <label className="campo ancho">
          <span>Nota de la visita</span>
          <textarea className="input" name="nota" rows={3} />
        </label>
        <label className="campo ancho">
          <span>Evidencia (foto o PDF, opcional)</span>
          <input className="input" type="file" accept="image/*,application/pdf" onChange={(e) => setEvidencia(e.target.files?.[0])} />
        </label>
        {salida.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(salida.error, 'No fue posible registrar la salida.')}
          </p>
        )}
      </form>
    </Modal>
  )
}

function OmisionModal({ paradaId, abierto, onCerrar }: { paradaId: string; abierto: boolean; onCerrar: () => void }) {
  const omitir = useOmitirParada()
  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          omitir.reset()
          onCerrar()
        }
      }}
      titulo="Omitir parada"
      descripcion="Las paradas siguientes se renumeran."
      pie={
        <button className="btn btn-primario" type="submit" form={`omision-${paradaId}`} disabled={omitir.isPending}>
          Omitir parada
        </button>
      }
    >
      <form
        id={`omision-${paradaId}`}
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const d = new FormData(e.currentTarget)
          omitir.mutate(
            { id: paradaId, motivo: String(d.get('motivo')).trim(), cancelar_servicio: d.get('cancelar') === 'on' },
            { onSuccess: onCerrar },
          )
        }}
      >
        <label className="campo ancho">
          <span>Motivo</span>
          <textarea className="input" name="motivo" rows={2} required minLength={3} />
        </label>
        <label className="acciones ancho">
          <input type="checkbox" name="cancelar" />
          Cancelar también el servicio (si no, queda por reprogramar)
        </label>
        {omitir.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(omitir.error, 'No fue posible omitir.')}
          </p>
        )}
      </form>
    </Modal>
  )
}

function PlanearModal({ abierto, onCerrar, dia, ciudad }: { abierto: boolean; onCerrar: () => void; dia: string; ciudad: string }) {
  const equipo = useEquipo()
  const planificar = usePlanificar()
  const plan = usePlanificacion(planificar.data?.id ?? null)
  const [elegidos, setElegidos] = useState<string[]>([])
  const campo = (equipo.data ?? []).filter((m) => m.rol === 'medico' || m.rol === 'operaciones')
  const resultado = plan.data?.resultado as ResultadoPlanificacion | undefined

  function cerrar() {
    planificar.reset()
    setElegidos([])
    onCerrar()
  }

  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => !v && cerrar()}
      titulo={`Planear rutas · ${ciudad} · ${fecha(dia)}`}
      descripcion="El optimizador reparte los servicios a domicilio del día entre quienes salen a campo."
      pie={
        !planificar.data && (
          <button
            className="btn btn-primario"
            type="button"
            disabled={elegidos.length === 0 || planificar.isPending}
            onClick={() => planificar.mutate({ fecha: dia, ciudad, responsables: elegidos })}
          >
            Planear
          </button>
        )
      }
    >
      {!planificar.data ? (
        <fieldset className="pila" style={{ border: 0, padding: 0, margin: 0 }}>
          <legend className="subtitulo">Quiénes salen a campo</legend>
          {campo.length === 0 && <p className="apagado">No hay médicos ni personal de operaciones activos.</p>}
          {campo.map((m) => (
            <label key={m.id} className="acciones">
              <input
                type="checkbox"
                checked={elegidos.includes(m.id)}
                onChange={(e) => setElegidos((a) => (e.target.checked ? [...a, m.id] : a.filter((x) => x !== m.id)))}
              />
              {m.nombre} <span className="apagado">({m.rol === 'medico' ? 'médico' : 'operaciones'})</span>
            </label>
          ))}
        </fieldset>
      ) : plan.data?.estado === 'pendiente' || !plan.data ? (
        <p className="apagado" role="status">
          Optimizando rutas… esto toma unos segundos.
        </p>
      ) : plan.data.estado === 'fallida' ? (
        <p className="aviso-error" role="alert">
          No fue posible planear: {plan.data.error}
        </p>
      ) : (
        <div className="pila" role="status">
          <p className="aviso-ok">
            {resultado?.rutas?.length ?? 0} rutas creadas con {resultado?.asignados ?? 0} servicios.
          </p>
          {(resultado?.sin_asignar?.length ?? 0) > 0 && (
            <p className="aviso">
              {resultado?.sin_asignar?.length} servicios quedaron sin ruta:{' '}
              {resultado?.sin_asignar?.map((s) => MOTIVOS_SIN_ASIGNAR[s.motivo] ?? s.motivo).join(', ')}.
            </p>
          )}
          <button className="btn btn-suave" type="button" onClick={cerrar}>
            Ver rutas
          </button>
        </div>
      )}
      {planificar.isError && (
        <p className="error" role="alert">
          {mensajeError(planificar.error, 'No fue posible iniciar la planificación.')}
        </p>
      )}
    </Modal>
  )
}
