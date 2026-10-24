import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { useAuth } from '@/features/auth/AuthContext'
import { useNombreTipoServicio, useTiposServicio } from '@/features/catalogos/api'
import { useFamilia } from '@/features/familias/api'
import { mensajeError } from '@/lib/errores'
import { estado as etiquetaEstado } from '@/lib/estados'
import { fechaHora } from '@/lib/formato'
import { puede } from '@/lib/permisos'
import type { EstadoServicio, PasoTipoRead, ServicioRead } from '@/types'

import {
  TRANSICIONES,
  useAutorizar,
  useCambiarEstadoServicio,
  useCompletarPaso,
  useCrearPendiente,
  usePasos,
  usePendientes,
  useReprogramar,
  useServicio,
} from './api'

// Texto de cada botón de avance: dice la acción, no el estado de destino.
const ACCION: Partial<Record<EstadoServicio, string>> = {
  agendado: 'Confirmar agenda',
  pendiente_autorizacion: 'Enviar a autorización',
  en_ruta: 'Salir en ruta',
  en_atencion: 'Iniciar atención',
  completado: 'Completar servicio',
}

export function ServicioDetallePage() {
  const { id = '' } = useParams()
  const servicio = useServicio(id)

  return (
    <Consulta consulta={servicio} cargando="Cargando el servicio…" error="No fue posible cargar el servicio.">
      {(s) => <DetalleServicio servicio={s} />}
    </Consulta>
  )
}

function DetalleServicio({ servicio: s }: { servicio: ServicioRead }) {
  const { usuario } = useAuth()
  const familia = useFamilia(s.familia_id)
  const nombreTipo = useNombreTipoServicio()
  const mascota = familia.data?.mascotas?.find((m) => m.id === s.mascota_id)
  const autorizar = useAutorizar(s.id)
  const [modal, setModal] = useState<'reprogramar' | 'cancelar' | null>(null)
  const estado = s.estado as EstadoServicio

  return (
    <div className="pila">
      <div className="detalle-cabeza">
        <Link to="/servicios" className="btn btn-plano" aria-label="Volver a servicios">
          <Icono nombre="volver" size={16} />
        </Link>
        <h1>{nombreTipo(s.tipo_codigo)}</h1>
        <Distintivo dominio="servicio" valor={s.estado} />
      </div>

      <div className="con-rail">
        <div className="pila">
          <section className="tarjeta">
            <dl className="ficha">
              <div>
                <dt>Familia</dt>
                <dd>
                  {familia.data ? <Link to={`/familias/${s.familia_id}`}>{familia.data.titular_nombre}</Link> : '…'}
                </dd>
              </div>
              <div><dt>Mascota</dt><dd>{mascota?.nombre ?? (s.mascota_id ? '…' : 'Toda la familia')}</dd></div>
              <div><dt>Programado</dt><dd className="numero">{fechaHora(s.programado_para)}</dd></div>
              <div><dt>Termina</dt><dd className="numero">{fechaHora(s.termina_en)}</dd></div>
              <div><dt>Ciudad</dt><dd>{s.ciudad}</dd></div>
              <div>
                <dt>Autorización</dt>
                <dd>{s.requiere_autorizacion ? (s.autorizado ? `Autorizado ${fechaHora(s.autorizado_en)}` : 'Pendiente') : 'No requiere'}</dd>
              </div>
            </dl>
            {s.observaciones && <p style={{ marginTop: 'var(--e4)' }}>{s.observaciones}</p>}
            {s.motivo_estado && <p className="apagado">Motivo del último cambio: {s.motivo_estado}</p>}
          </section>

          <PasosAtencion servicio={s} />
          <PendientesServicio servicio={s} />
        </div>

        <aside className="rail">
          <section className="tarjeta">
            <div className="tarjeta-cabeza">
              <h3>Acciones</h3>
            </div>
            <AccionesEstado servicio={s} onModal={setModal} />
            {s.requiere_autorizacion && !s.autorizado && puede(usuario, 'clinico') && (
              <button
                className="btn btn-suave btn-bloque"
                type="button"
                style={{ marginTop: 'var(--e2)' }}
                disabled={autorizar.isPending}
                onClick={() => autorizar.mutate()}
              >
                Autorizar servicio
              </button>
            )}
            {autorizar.isError && (
              <p className="error" role="alert">
                {mensajeError(autorizar.error, 'No fue posible autorizar.')}
              </p>
            )}
            {TRANSICIONES[estado].length === 0 && <p className="apagado">El servicio ya está cerrado.</p>}
          </section>
        </aside>
      </div>

      <ReprogramarModal servicio={s} abierto={modal === 'reprogramar'} onCerrar={() => setModal(null)} />
      <CancelarModal servicio={s} abierto={modal === 'cancelar'} onCerrar={() => setModal(null)} />
    </div>
  )
}

function AccionesEstado({ servicio, onModal }: { servicio: ServicioRead; onModal: (m: 'reprogramar' | 'cancelar') => void }) {
  const cambiar = useCambiarEstadoServicio(servicio.id)
  const destinos = TRANSICIONES[servicio.estado as EstadoServicio]

  return (
    <div className="pila" style={{ gap: 'var(--e2)' }}>
      {destinos
        .filter((d) => d !== 'reprogramado' && d !== 'cancelado')
        .map((d) => (
          <button
            key={d}
            className="btn btn-primario btn-bloque"
            type="button"
            disabled={cambiar.isPending}
            onClick={() => cambiar.mutate({ estado: d })}
          >
            {ACCION[d] ?? etiquetaEstado('servicio', d).label}
          </button>
        ))}
      {destinos.includes('reprogramado') && (
        <button className="btn btn-suave btn-bloque" type="button" onClick={() => onModal('reprogramar')}>
          Reprogramar
        </button>
      )}
      {destinos.includes('cancelado') && (
        <button className="btn btn-plano btn-bloque" type="button" onClick={() => onModal('cancelar')}>
          Cancelar servicio
        </button>
      )}
      {cambiar.isError && (
        <p className="error" role="alert">
          {mensajeError(cambiar.error, 'No fue posible cambiar el estado.')}
        </p>
      )}
    </div>
  )
}

function PasosAtencion({ servicio }: { servicio: ServicioRead }) {
  const tipos = useTiposServicio()
  const pasos = usePasos(servicio.id)
  const definicion = tipos.data?.find((t) => t.codigo === servicio.tipo_codigo)?.pasos ?? []
  if (definicion.length === 0) return null
  const enAtencion = servicio.estado === 'en_atencion'

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Pasos de la atención</h3>
        {!enAtencion && <span className="apagado">Se registran durante la atención</span>}
      </div>
      <Consulta consulta={pasos} cargando="Cargando pasos…" error="No fue posible cargar los pasos.">
        {(hechos) => (
          <ol className="linea-tiempo">
            {definicion.map((p) => {
              const hecho = hechos.find((h) => h.paso_codigo === p.codigo)
              return (
                <li key={p.codigo} className={hecho ? 'hecho' : ''}>
                  <Paso servicioId={servicio.id} paso={p} datos={hecho?.datos} editable={enAtencion} />
                </li>
              )
            })}
          </ol>
        )}
      </Consulta>
    </section>
  )
}

function Paso({
  servicioId,
  paso,
  datos,
  editable,
}: {
  servicioId: string
  paso: PasoTipoRead
  datos?: Record<string, unknown>
  editable: boolean
}) {
  const completar = useCompletarPaso(servicioId)
  const [abierto, setAbierto] = useState(false)
  const campos = paso.campos ?? []

  function guardar(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const d = new FormData(e.currentTarget)
    const valores = Object.fromEntries(campos.map((c) => [c, String(d.get(c) ?? '').trim()]))
    completar.mutate({ paso: paso.codigo, datos: valores }, { onSuccess: () => setAbierto(false) })
  }

  return (
    <div className="pila" style={{ gap: 'var(--e2)' }}>
      <div className="acciones">
        <strong>{paso.nombre}</strong>
        {!paso.obligatorio && <span className="distintivo distintivo-neutro">Opcional</span>}
        {datos && <span className="distintivo distintivo-ok">Registrado</span>}
        {editable && !abierto && (
          <button className="btn btn-plano" type="button" onClick={() => setAbierto(true)}>
            {datos ? 'Editar' : 'Registrar'}
          </button>
        )}
      </div>
      {datos && !abierto && (
        <dl className="ficha">
          {Object.entries(datos).map(([k, v]) => (
            <div key={k}>
              <dt>{k.replace(/_/g, ' ')}</dt>
              <dd>{String(v)}</dd>
            </div>
          ))}
        </dl>
      )}
      {abierto && (
        <form className="formulario" onSubmit={guardar} aria-label={`Paso ${paso.nombre}`}>
          {campos.length === 0 && <p className="apagado ancho">Este paso no pide datos: guárdalo para marcarlo hecho.</p>}
          {campos.map((c) => (
            <label key={c} className="campo ancho">
              <span>{c.charAt(0).toUpperCase() + c.slice(1).replace(/_/g, ' ')}</span>
              <textarea className="input" name={c} rows={2} required defaultValue={datos ? String(datos[c] ?? '') : ''} />
            </label>
          ))}
          {completar.isError && (
            <p className="error ancho" role="alert">
              {mensajeError(completar.error, 'No fue posible guardar el paso.')}
            </p>
          )}
          <div className="acciones ancho">
            <button className="btn btn-primario" type="submit" disabled={completar.isPending}>
              Guardar paso
            </button>
            <button className="btn btn-plano" type="button" onClick={() => setAbierto(false)}>
              Cancelar
            </button>
          </div>
        </form>
      )}
    </div>
  )
}

function PendientesServicio({ servicio }: { servicio: ServicioRead }) {
  const pendientes = usePendientes({ servicio_id: servicio.id })
  const crear = useCrearPendiente(servicio.id)
  const [descripcion, setDescripcion] = useState('')
  const [requiere, setRequiere] = useState(true)

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Pendientes derivados</h3>
      </div>
      <Consulta
        consulta={pendientes}
        cargando="Cargando pendientes…"
        error="No fue posible cargar los pendientes."
        vacio="Esta atención no dejó pendientes."
        estaVacio={(d) => d.length === 0}
      >
        {(d) => (
          <ul className="pila" style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {d.map((p) => (
              <li key={p.id} className="acciones">
                <span style={{ flex: 1 }}>{p.descripcion}</span>
                <Distintivo dominio="pendiente" valor={p.estado} />
              </li>
            ))}
          </ul>
        )}
      </Consulta>
      <form
        className="formulario"
        style={{ marginTop: 'var(--e4)' }}
        onSubmit={(e) => {
          e.preventDefault()
          crear.mutate(
            { descripcion: descripcion.trim(), requiere_autorizacion: requiere },
            { onSuccess: () => setDescripcion('') },
          )
        }}
      >
        <label className="campo ancho">
          <span>Nuevo pendiente</span>
          <input
            className="input"
            value={descripcion}
            onChange={(e) => setDescripcion(e.target.value)}
            placeholder="Ej.: control en 15 días, examen de sangre"
            required
            minLength={3}
          />
        </label>
        <label className="acciones">
          <input type="checkbox" checked={requiere} onChange={(e) => setRequiere(e.target.checked)} />
          Requiere autorización de la familia
        </label>
        <button className="btn btn-suave" type="submit" disabled={crear.isPending}>
          Agregar pendiente
        </button>
        {crear.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(crear.error, 'No fue posible crear el pendiente.')}
          </p>
        )}
      </form>
    </section>
  )
}

function ReprogramarModal({ servicio, abierto, onCerrar }: { servicio: ServicioRead; abierto: boolean; onCerrar: () => void }) {
  const reprogramar = useReprogramar(servicio.id)

  function guardar(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const d = new FormData(e.currentTarget)
    // datetime-local no lleva zona: se interpreta en hora de Colombia (-05:00).
    const inicio = `${String(d.get('inicio'))}:00-05:00`
    reprogramar.mutate({ inicio, motivo: String(d.get('motivo')).trim() }, { onSuccess: onCerrar })
  }

  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          reprogramar.reset()
          onCerrar()
        }
      }}
      titulo="Reprogramar servicio"
      descripcion="La familia recibe la nueva fecha por WhatsApp."
      pie={
        <button className="btn btn-primario" type="submit" form="reprogramar" disabled={reprogramar.isPending}>
          Reprogramar
        </button>
      }
    >
      <form id="reprogramar" className="formulario" onSubmit={guardar}>
        <label className="campo">
          <span>Nueva fecha y hora</span>
          <input className="input" name="inicio" type="datetime-local" required />
        </label>
        <label className="campo ancho">
          <span>Motivo</span>
          <textarea className="input" name="motivo" rows={2} required minLength={3} />
        </label>
        {reprogramar.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(reprogramar.error, 'No fue posible reprogramar.')}
          </p>
        )}
      </form>
    </Modal>
  )
}

function CancelarModal({ servicio, abierto, onCerrar }: { servicio: ServicioRead; abierto: boolean; onCerrar: () => void }) {
  const cambiar = useCambiarEstadoServicio(servicio.id)

  function guardar(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const motivo = String(new FormData(e.currentTarget).get('motivo')).trim()
    cambiar.mutate({ estado: 'cancelado', motivo }, { onSuccess: onCerrar })
  }

  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          cambiar.reset()
          onCerrar()
        }
      }}
      titulo="Cancelar servicio"
      descripcion="El cupo se libera y la familia recibe el aviso."
      pie={
        <button className="btn btn-primario" type="submit" form="cancelar-servicio" disabled={cambiar.isPending}>
          Confirmar cancelación
        </button>
      }
    >
      <form id="cancelar-servicio" className="formulario" onSubmit={guardar}>
        <label className="campo ancho">
          <span>Motivo de la cancelación</span>
          <textarea className="input" name="motivo" rows={3} required minLength={3} />
        </label>
        {cambiar.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(cambiar.error, 'No fue posible cancelar.')}
          </p>
        )}
      </form>
    </Modal>
  )
}
