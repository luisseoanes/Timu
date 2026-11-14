import { useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo, Insignia } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { useAuth } from '@/features/auth'
import { useNombreTipoServicio, useTiposServicio } from '@/features/catalogos'
import { useFamilia } from '@/features/familias'
import { mensajeError } from '@/lib/errores'
import { estado as etiquetaEstado } from '@/lib/estados'
import { diaISO, fechaCorta, fechaCortaConDia, hora } from '@/lib/formato'
import { puede } from '@/lib/permisos'
import type { EstadoServicio, PasoRead, PasoTipoRead, ServicioRead } from '@/types'

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

/** La ficha de un servicio, a la derecha del listado (o sola en el celular). */
export function FichaServicio({ id }: { id: string }) {
  const servicio = useServicio(id)
  const ref = useRef<HTMLElement>(null)
  // Abrir una fila del final del listado deja la ficha arriba, fuera de la vista: se trae.
  useEffect(() => {
    const ficha = ref.current
    if (ficha && ficha.getBoundingClientRect().top < 0) ficha.scrollIntoView?.({ block: 'start' })
  }, [])
  return (
    <section ref={ref} className="ficha-abierta servicio-ficha" aria-label="Servicio abierto">
      <Consulta consulta={servicio} cargando="Cargando el servicio…" error="No fue posible cargar el servicio.">
        {(s) => <Ficha servicio={s} />}
      </Consulta>
    </section>
  )
}

/** Lo que falta para cerrar la atención: los pasos obligatorios sin registrar. */
function pasosQueFaltan(definicion: PasoTipoRead[], hechos: PasoRead[]): PasoTipoRead[] {
  return definicion.filter((p) => p.obligatorio && !hechos.some((h) => h.paso_codigo === p.codigo))
}

function Ficha({ servicio: s }: { servicio: ServicioRead }) {
  const [params] = useSearchParams()
  const familia = useFamilia(s.familia_id)
  const tipos = useTiposServicio()
  const nombreTipo = useNombreTipoServicio()
  const pasos = usePasos(s.id)
  const [modal, setModal] = useState<'reprogramar' | 'cancelar' | null>(null)
  const definicion = tipos.data?.find((t) => t.codigo === s.tipo_codigo)?.pasos ?? []
  const enAtencion = s.estado === 'en_atencion'
  const faltan = pasos.data ? pasosQueFaltan(definicion, pasos.data) : []
  // Sin saber aún qué pasos pide el tipo o cuáles hay hechos, completar se bloquea: el backend
  // lo rechazaría si faltara alguno.
  const pasosPorSaber = !tipos.data || (definicion.some((p) => p.obligatorio) && !pasos.data)
  // En atención, la ficha abre en el primer paso que falta: es lo que el médico vino a hacer.
  const [elegido, setAbierto] = useState<string | null | undefined>(undefined)
  const abierto = elegido === undefined ? (enAtencion ? (faltan[0]?.codigo ?? null) : null) : elegido
  const mascota = familia.data?.mascotas?.find((m) => m.id === s.mascota_id)
  const desdeRuta = params.get('origen') === 'ruta'
  const lista = new URLSearchParams(params)
  lista.delete('origen')
  const volver = `/servicios${lista.toString() ? `?${lista}` : ''}`

  return (
    <>
      <header className="ficha-cabeza">
        <Link to={desdeRuta ? '/rutas' : volver} className="btn btn-plano ficha-volver" aria-label={desdeRuta ? 'Volver a mi ruta' : 'Volver a servicios'}>
          <Icono nombre="volver" size={16} />
        </Link>
        <h2 className="consulta-titulo">{nombreTipo(s.tipo_codigo)}</h2>
        <p className="servicio-quien">
          {s.mascota_id ? (mascota ? `${mascota.nombre} (${mascota.especie})` : '…') : 'Toda la familia'}
          {' · '}
          {familia.data ? <Link to={`/familias/${s.familia_id}`}>{familia.data.titular_nombre}</Link> : '…'}
        </p>
        <div className="ficha-datos">
          <Distintivo dominio="servicio" valor={s.estado} />
          {s.programado_para && (
            <span className="numero">
              {fechaCortaConDia(diaISO(s.programado_para))} · {hora(s.programado_para)}
            </span>
          )}
          <span>{s.ciudad}</span>
          {s.requiere_autorizacion &&
            (s.autorizado ? (
              <Insignia tono="ok">
                {s.autorizado_en ? `Autorizado el ${fechaCorta(diaISO(s.autorizado_en))}` : 'Autorizado'}
              </Insignia>
            ) : (
              <Insignia tono="alerta">Por autorizar</Insignia>
            ))}
        </div>
        <AccionesServicio
          servicio={s}
          faltan={faltan}
          pasosPorSaber={pasosPorSaber}
          verdeOcupado={abierto !== null}
          desdeRuta={desdeRuta}
          onModal={setModal}
        />
      </header>

      {(s.observaciones || s.motivo_estado) && (
        <div className="servicio-notas">
          {s.observaciones && <p>{s.observaciones}</p>}
          {s.motivo_estado && <p className="apagado">Motivo del último cambio: {s.motivo_estado}</p>}
        </div>
      )}

      {definicion.length > 0 && (
        <PasosAtencion
          servicio={s}
          definicion={definicion}
          pasos={pasos}
          abierto={abierto}
          onAbrir={setAbierto}
          onGuardado={(codigo) => {
            // Tras guardar, el siguiente que falta; si no queda ninguno, ninguno abierto.
            const siguiente = faltan.find((p) => p.codigo !== codigo)
            setAbierto(siguiente?.codigo ?? null)
          }}
        />
      )}
      <PendientesServicio servicio={s} />

      <ReprogramarModal servicio={s} abierto={modal === 'reprogramar'} onCerrar={() => setModal(null)} />
      <CancelarModal servicio={s} abierto={modal === 'cancelar'} onCerrar={() => setModal(null)} />
    </>
  )
}

/**
 * Las acciones del servicio, en una fila: la de estado que toca en verde (salir en ruta si es a
 * domicilio, iniciar o completar la atención), las demás secundarias y cancelar al final, en
 * rojo plano. Completar se bloquea mientras falten pasos obligatorios, y dice cuáles. Con un paso
 * abierto, el verde es el de guardar ese paso: aquí no hay otro.
 */
function AccionesServicio({
  servicio,
  faltan,
  pasosPorSaber,
  verdeOcupado,
  desdeRuta,
  onModal,
}: {
  servicio: ServicioRead
  faltan: PasoTipoRead[]
  pasosPorSaber: boolean
  verdeOcupado: boolean
  desdeRuta: boolean
  onModal: (m: 'reprogramar' | 'cancelar') => void
}) {
  const { usuario } = useAuth()
  const cambiar = useCambiarEstadoServicio(servicio.id)
  const autorizar = useAutorizar(servicio.id)
  const estado = servicio.estado as EstadoServicio
  const destinos = TRANSICIONES[estado]
  const adelante = destinos.filter((d) => d !== 'reprogramado' && d !== 'cancelado')
  // A domicilio se sale en ruta; en la clínica o en una aliada se empieza directamente.
  const principal = estado === 'agendado' && servicio.tipo !== 'domiciliario' ? 'en_atencion' : adelante[0]
  const otras = adelante.filter((d) => d !== principal && !(d === 'en_ruta' && servicio.tipo !== 'domiciliario'))
  const bloqueada = principal === 'completado' && (faltan.length > 0 || pasosPorSaber)
  const porAutorizar = servicio.requiere_autorizacion && !servicio.autorizado && puede(usuario, 'clinico')
  const cerrado = destinos.length === 0

  return (
    <div className="ficha-acciones servicio-acciones">
      {principal && (
        <button
          className={`btn ${verdeOcupado || bloqueada ? 'btn-secundario' : 'btn-primario'}`}
          type="button"
          disabled={cambiar.isPending || bloqueada}
          onClick={() => cambiar.mutate({ estado: principal })}
        >
          {ACCION[principal] ?? etiquetaEstado('servicio', principal).label}
        </button>
      )}
      {otras.map((d) => (
        <button key={d} className="btn btn-secundario" type="button" disabled={cambiar.isPending} onClick={() => cambiar.mutate({ estado: d })}>
          {ACCION[d] ?? etiquetaEstado('servicio', d).label}
        </button>
      ))}
      {porAutorizar && (
        <button className="btn btn-suave" type="button" disabled={autorizar.isPending} onClick={() => autorizar.mutate()}>
          Autorizar servicio
        </button>
      )}
      {desdeRuta && (
        <Link className={`btn ${cerrado && !verdeOcupado ? 'btn-primario' : 'btn-secundario'}`} to="/rutas">
          Volver a mi ruta
        </Link>
      )}
      {destinos.includes('reprogramado') && (
        <button className="btn btn-secundario" type="button" onClick={() => onModal('reprogramar')}>
          Reprogramar
        </button>
      )}
      {destinos.includes('cancelado') && (
        <button className="btn btn-plano btn-plano-peligro" type="button" onClick={() => onModal('cancelar')}>
          Cancelar servicio
        </button>
      )}
      {bloqueada && faltan.length > 0 && (
        <p className="servicio-falta">
          <Icono nombre="alerta" size={14} />
          Para completar falta registrar: {faltan.map((p) => p.nombre).join(', ')}.
        </p>
      )}
      {cerrado && <p className="apagado">El servicio ya está cerrado.</p>}
      {(cambiar.isError || autorizar.isError) && (
        <p className="error" role="alert">
          {cambiar.isError
            ? mensajeError(cambiar.error, 'No fue posible cambiar el estado.')
            : mensajeError(autorizar.error, 'No fue posible autorizar.')}
        </p>
      )}
    </div>
  )
}

/** Los pasos del servicio como estaciones: registrado, obligatorio por registrar u opcional. */
function PasosAtencion({
  servicio,
  definicion,
  pasos,
  abierto,
  onAbrir,
  onGuardado,
}: {
  servicio: ServicioRead
  definicion: PasoTipoRead[]
  pasos: ReturnType<typeof usePasos>
  abierto: string | null
  onAbrir: (codigo: string | null) => void
  onGuardado: (codigo: string) => void
}) {
  const enAtencion = servicio.estado === 'en_atencion'
  const cerrado = servicio.estado === 'completado' || servicio.estado === 'cancelado'

  return (
    <section className="servicio-bloque" aria-labelledby="pasos-titulo">
      <h3 id="pasos-titulo" className="servicio-bloque-titulo">
        Pasos de la atención
      </h3>
      {!enAtencion && !cerrado && <p className="apagado">Se registran durante la atención: al iniciarla se abre el primero que falta.</p>}
      <Consulta consulta={pasos} cargando="Cargando pasos…" error="No fue posible cargar los pasos.">
        {(hechos) => (
          <ol className="servicio-pasos">
            {definicion.map((p) => {
              const hecho = hechos.find((h) => h.paso_codigo === p.codigo)
              const estado = hecho ? 'hecho' : p.obligatorio ? 'falta' : 'opcional'
              return (
                <li key={p.codigo} className="servicio-paso" data-estado={estado}>
                  <span className="servicio-paso-punto" aria-hidden="true">
                    {hecho && <Icono nombre="check" size={12} />}
                  </span>
                  <Paso
                    servicioId={servicio.id}
                    paso={p}
                    datos={hecho?.datos}
                    editable={enAtencion}
                    abierto={abierto === p.codigo}
                    onAbrir={(v) => onAbrir(v ? p.codigo : null)}
                    onGuardado={() => onGuardado(p.codigo)}
                  />
                </li>
              )
            })}
          </ol>
        )}
      </Consulta>
    </section>
  )
}

/** Un campo del paso como lo lee una persona: «valoracion_clinica» → «Valoracion clinica». */
function rotuloCampo(campo: string): string {
  return campo.charAt(0).toUpperCase() + campo.slice(1).replace(/_/g, ' ')
}

function Paso({
  servicioId,
  paso,
  datos,
  editable,
  abierto,
  onAbrir,
  onGuardado,
}: {
  servicioId: string
  paso: PasoTipoRead
  datos?: Record<string, unknown>
  editable: boolean
  abierto: boolean
  onAbrir: (abierto: boolean) => void
  onGuardado: () => void
}) {
  const completar = useCompletarPaso(servicioId)
  const campos = paso.campos ?? []

  function guardar(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const d = new FormData(e.currentTarget)
    const valores = Object.fromEntries(campos.map((c) => [c, String(d.get(c) ?? '').trim()]))
    completar.mutate({ paso: paso.codigo, datos: valores }, { onSuccess: onGuardado })
  }

  return (
    <div className="servicio-paso-cuerpo">
      <div className="servicio-paso-cabeza">
        <strong>{paso.nombre}</strong>
        <span className="servicio-paso-estado">{datos ? 'Registrado' : paso.obligatorio ? 'Obligatorio' : 'Opcional'}</span>
        {editable && !abierto && (
          <button className="btn btn-secundario" type="button" onClick={() => onAbrir(true)} aria-label={`${datos ? 'Editar' : 'Registrar'} ${paso.nombre}`}>
            {datos ? 'Editar' : 'Registrar'}
          </button>
        )}
      </div>
      {datos && !abierto && Object.keys(datos).length > 0 && (
        <dl className="servicio-paso-datos">
          {Object.entries(datos).map(([k, v]) => (
            <div key={k}>
              <dt>{rotuloCampo(k)}</dt>
              <dd>{String(v)}</dd>
            </div>
          ))}
        </dl>
      )}
      {abierto && (
        <form className="formulario servicio-paso-formulario" onSubmit={guardar} aria-label={`Paso ${paso.nombre}`}>
          {campos.length === 0 && <p className="apagado ancho">Este paso no pide datos: guárdalo para marcarlo hecho.</p>}
          {campos.map((c) => (
            <label key={c} className="campo ancho">
              <span>{rotuloCampo(c)}</span>
              <textarea className="input" name={c} rows={3} required defaultValue={datos ? String(datos[c] ?? '') : ''} />
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
            <button className="btn btn-plano" type="button" onClick={() => onAbrir(false)}>
              Cancelar
            </button>
          </div>
        </form>
      )}
    </div>
  )
}

/** Lo que la atención deja para después: la lista y, al pedirlo, el formulario para añadir uno. */
function PendientesServicio({ servicio }: { servicio: ServicioRead }) {
  const pendientes = usePendientes({ servicio_id: servicio.id })
  const crear = useCrearPendiente(servicio.id)
  const [agregando, setAgregando] = useState(false)
  const [descripcion, setDescripcion] = useState('')
  const [requiere, setRequiere] = useState(true)

  return (
    <section className="servicio-bloque" aria-labelledby="pendientes-titulo">
      <div className="servicio-bloque-cabeza">
        <h3 id="pendientes-titulo" className="servicio-bloque-titulo">
          Pendientes derivados
        </h3>
        {!agregando && (
          <button className="btn btn-secundario" type="button" onClick={() => setAgregando(true)}>
            <Icono nombre="mas" size={16} />
            Agregar pendiente
          </button>
        )}
      </div>
      <Consulta
        consulta={pendientes}
        cargando="Cargando pendientes…"
        error="No fue posible cargar los pendientes."
        vacio="Esta atención no dejó pendientes. Si queda algo para después (un control, un examen), agrégalo aquí."
        estaVacio={(d) => d.length === 0}
      >
        {(d) => (
          <ul className="servicio-pendientes">
            {d.map((p) => (
              <li key={p.id}>
                <span>{p.descripcion}</span>
                <Distintivo dominio="pendiente" valor={p.estado} />
              </li>
            ))}
          </ul>
        )}
      </Consulta>
      {agregando && (
        <form
          className="formulario"
          aria-label="Nuevo pendiente"
          onSubmit={(e) => {
            e.preventDefault()
            crear.mutate(
              { descripcion: descripcion.trim(), requiere_autorizacion: requiere },
              {
                onSuccess: () => {
                  setDescripcion('')
                  setAgregando(false)
                },
              },
            )
          }}
        >
          <label className="campo ancho">
            <span>Qué queda pendiente</span>
            <input
              className="input"
              value={descripcion}
              onChange={(e) => setDescripcion(e.target.value)}
              placeholder="Ej.: control en 15 días, examen de sangre"
              required
              minLength={3}
            />
          </label>
          <label className="acciones ancho">
            <input type="checkbox" checked={requiere} onChange={(e) => setRequiere(e.target.checked)} />
            Requiere autorización de la familia
          </label>
          {crear.isError && (
            <p className="error ancho" role="alert">
              {mensajeError(crear.error, 'No fue posible crear el pendiente.')}
            </p>
          )}
          <div className="acciones ancho">
            <button className="btn btn-secundario" type="submit" disabled={crear.isPending}>
              Guardar pendiente
            </button>
            <button className="btn btn-plano" type="button" onClick={() => setAgregando(false)}>
              Cancelar
            </button>
          </div>
        </form>
      )}
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
        <button className="btn btn-peligro" type="submit" form="cancelar-servicio" disabled={cambiar.isPending}>
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
