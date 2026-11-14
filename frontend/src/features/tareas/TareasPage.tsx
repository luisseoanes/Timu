import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { Paginacion } from '@/components/Paginacion'
import { useAuth, useEquipo } from '@/features/auth'
import { useNombreTipoServicio } from '@/features/catalogos'
import { SelectorFamilia } from '@/features/familias'
import { mensajeError } from '@/lib/errores'
import { fechaCortaConDia, hoyISO } from '@/lib/formato'
import type { FamiliaRead, TareaRead } from '@/types'


import {
  AREAS,
  useAsignarTarea,
  useCerrarTarea,
  useCrearTarea,
  useIniciarTarea,
  useTareas,
  type Area,
  type FiltrosTareas,
} from './api'

type Vista = 'mias' | 'sin_asignar' | 'vencidas' | 'todas'

const VISTAS: { valor: Vista; label: string }[] = [
  { valor: 'mias', label: 'Mis tareas' },
  { valor: 'sin_asignar', label: 'Sin asignar' },
  { valor: 'vencidas', label: 'Vencidas' },
  { valor: 'todas', label: 'Todas' },
]

const POR_PAGINA = 25

/** Bandeja de tareas del equipo (F1-SER-06): lo que alguien tiene que resolver y para cuándo. */
export function TareasPage() {
  const { usuario } = useAuth()
  const [params] = useSearchParams()
  const [vista, setVista] = useState<Vista>(params.get('vencidas') === '1' ? 'vencidas' : 'todas')
  const [area, setArea] = useState<Area | ''>('')
  const [estado, setEstado] = useState('abierta')
  const [offset, setOffset] = useState(0)
  const [nueva, setNueva] = useState(false)
  const [cerrando, setCerrando] = useState<TareaRead | null>(null)
  const usuarios = useEquipo()
  const nombreTipo = useNombreTipoServicio()

  const filtros: FiltrosTareas = {
    area: area || undefined,
    estado: estado || undefined,
    mias: vista === 'mias' || undefined,
    sin_asignar: vista === 'sin_asignar' || undefined,
    vencidas: vista === 'vencidas' || undefined,
    limit: POR_PAGINA,
    offset,
  }
  const tareas = useTareas(filtros)
  const asignar = useAsignarTarea()
  const iniciar = useIniciarTarea()
  const errorAccion = asignar.error ?? iniciar.error
  const nombreDe = (id: string | null) =>
    !id ? 'Sin asignar' : id === usuario?.id ? 'Tú' : (usuarios.data?.find((u) => u.id === id)?.nombre ?? 'Otra persona')

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Tareas</h3>
        <button className="btn btn-primario" type="button" onClick={() => setNueva(true)}>
          <Icono nombre="mas" size={16} /> Nueva tarea
        </button>
      </div>
      <div className="filtros tareas-filtros">
        <div className="segmento tareas-vistas" role="group" aria-label="Vista de tareas">
          {VISTAS.map((v) => (
            <button
              key={v.valor}
              type="button"
              className="segmento-opcion"
              data-state={vista === v.valor ? 'active' : 'inactive'}
              aria-pressed={vista === v.valor}
              onClick={() => {
                setVista(v.valor)
                setOffset(0)
              }}
            >
              {v.label}
            </button>
          ))}
        </div>
        <select className="input tareas-filtro" value={area} onChange={(e) => { setArea(e.target.value as Area | ''); setOffset(0) }} aria-label="Área">
          <option value="">Todas las áreas</option>
          {AREAS.map((a) => (
            <option key={a.valor} value={a.valor}>{a.label}</option>
          ))}
        </select>
        <select className="input tareas-filtro" value={estado} onChange={(e) => { setEstado(e.target.value); setOffset(0) }} aria-label="Estado de la tarea">
          <option value="abierta">Abiertas</option>
          <option value="en_progreso">En progreso</option>
          <option value="cerrada">Cerradas</option>
          <option value="">Todas</option>
        </select>
      </div>
      {errorAccion && (
        <p className="error" role="alert">
          {mensajeError(errorAccion, 'No fue posible actualizar la tarea.')}
        </p>
      )}
      <Consulta
        consulta={tareas}
        cargando="Cargando tareas…"
        error="No fue posible cargar las tareas."
        vacio="No hay tareas en esta vista. ¡Todo al día!"
        estaVacio={(d) => d.items.length === 0}
      >
        {(d) => (
          <>
            <div className="scroll-x">
              <table className="tabla tabla-apilable tareas-tabla">
                <thead>
                  <tr>
                    <th>Tarea</th>
                    <th>Vence</th>
                    <th>Prioridad</th>
                    <th>Responsable</th>
                    <th><span className="sr-only">Acciones</span></th>
                  </tr>
                </thead>
                <tbody>
                  {d.items.map((t) => {
                    const vencida = t.estado !== 'cerrada' && t.vence_el !== null && t.vence_el < hoyISO()
                    const area = AREAS.find((a) => a.valor === t.area)?.label ?? t.area
                    return (
                      <tr key={t.id}>
                        <td className="principal" data-etiqueta="Tarea">
                          <span className="tarea-titulo">
                            {t.titulo}
                            <Distintivo dominio="tarea" valor={t.estado} />
                          </span>
                          {/* A quién afecta: la familia y, si es de un servicio, cuál y de quién. */}
                          <div className="tarea-detalle">
                            <span>{area}</span>
                            {t.familia && <Link to={`/familias/${t.familia.id}`}>{t.familia.titular_nombre}</Link>}
                            {t.servicio && (
                              <Link to={`/servicios/${t.servicio.id}`}>
                                {nombreTipo(t.servicio.tipo_codigo)}
                                {t.servicio.mascota_nombre && ` de ${t.servicio.mascota_nombre}`}
                              </Link>
                            )}
                          </div>
                          {t.descripcion && <div className="tarea-descripcion">{t.descripcion}</div>}
                        </td>
                        <td data-etiqueta="Vence">
                          {/* Lo vencido se dice en texto e icono, no solo en rojo. */}
                          {vencida ? (
                            <span className="tarea-vencida">
                              <Icono nombre="alerta" size={14} />
                              <span className="numero">{fechaCortaConDia(t.vence_el!)} ·</span>
                              <span>vencida</span>
                            </span>
                          ) : (
                            <span className="numero">{t.vence_el ? fechaCortaConDia(t.vence_el) : 'Sin fecha'}</span>
                          )}
                        </td>
                        <td data-etiqueta="Prioridad">
                          <Distintivo dominio="prioridad" valor={t.prioridad} />
                        </td>
                        <td data-etiqueta="Responsable">
                          {t.estado !== 'cerrada' ? (
                            <select
                              className="input tarea-responsable"
                              value={t.asignada_a_id ?? ''}
                              aria-label={`Responsable de ${t.titulo}`}
                              onChange={(e) => asignar.mutate({ id: t.id, usuario_id: e.target.value || null })}
                            >
                              <option value="">Sin asignar</option>
                              {usuarios.data?.map((u) => (
                                <option key={u.id} value={u.id}>{u.nombre}</option>
                              ))}
                            </select>
                          ) : (
                            nombreDe(t.asignada_a_id)
                          )}
                        </td>
                        <td className="tabla-acciones">
                          {!t.asignada_a_id && t.estado !== 'cerrada' && usuario && (
                            <button className="btn btn-suave" type="button" onClick={() => asignar.mutate({ id: t.id, usuario_id: usuario.id })}>
                              Tomar
                            </button>
                          )}
                          {t.estado === 'abierta' && t.asignada_a_id && (
                            <button className="btn btn-plano" type="button" onClick={() => iniciar.mutate(t.id)}>
                              Iniciar
                            </button>
                          )}
                          {t.estado !== 'cerrada' && (
                            <button className="btn btn-plano" type="button" onClick={() => setCerrando(t)}>
                              Cerrar
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
      <NuevaTareaModal abierto={nueva} onCerrar={() => setNueva(false)} />
      <CerrarTareaModal tarea={cerrando} onCerrar={() => setCerrando(null)} />
    </section>
  )
}

function NuevaTareaModal({ abierto, onCerrar }: { abierto: boolean; onCerrar: () => void }) {
  const crear = useCrearTarea()
  const [familia, setFamilia] = useState<FamiliaRead | null>(null)

  function guardar(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const d = new FormData(e.currentTarget)
    const dias = String(d.get('vence_en_dias') ?? '')
    crear.mutate(
      {
        titulo: String(d.get('titulo')).trim(),
        descripcion: String(d.get('descripcion') ?? '').trim() || undefined,
        area: d.get('area') as Area,
        prioridad: d.get('prioridad') as 'baja' | 'media' | 'alta',
        vence_en_dias: dias ? Number(dias) : undefined,
        familia_id: familia?.id,
      },
      {
        onSuccess: () => {
          setFamilia(null)
          onCerrar()
        },
      },
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
      titulo="Nueva tarea"
      pie={
        <button className="btn btn-primario" type="submit" form="nueva-tarea" disabled={crear.isPending}>
          Crear tarea
        </button>
      }
    >
      <form id="nueva-tarea" className="formulario" onSubmit={guardar}>
        <label className="campo ancho">
          <span>Qué hay que hacer</span>
          <input className="input" name="titulo" required minLength={3} />
        </label>
        <label className="campo ancho">
          <span>Detalle (opcional)</span>
          <textarea className="input" name="descripcion" rows={2} />
        </label>
        <label className="campo">
          <span>Área</span>
          <select className="input" name="area" defaultValue="operaciones">
            {AREAS.map((a) => (
              <option key={a.valor} value={a.valor}>{a.label}</option>
            ))}
          </select>
        </label>
        <label className="campo">
          <span>Prioridad</span>
          <select className="input" name="prioridad" defaultValue="media">
            <option value="alta">Alta</option>
            <option value="media">Media</option>
            <option value="baja">Baja</option>
          </select>
        </label>
        <label className="campo">
          <span>Vence en (días)</span>
          <input className="input" name="vence_en_dias" type="number" min={0} />
        </label>
        <div className="ancho">
          <SelectorFamilia valor={familia} onCambio={setFamilia} etiqueta="Familia relacionada (opcional)" />
        </div>
        {crear.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(crear.error, 'No fue posible crear la tarea.')}
          </p>
        )}
      </form>
    </Modal>
  )
}

function CerrarTareaModal({ tarea, onCerrar }: { tarea: TareaRead | null; onCerrar: () => void }) {
  const cerrar = useCerrarTarea()

  return (
    <Modal
      abierto={tarea !== null}
      onCambio={(v) => {
        if (!v) {
          cerrar.reset()
          onCerrar()
        }
      }}
      titulo="Cerrar tarea"
      descripcion={tarea?.titulo}
      pie={
        <button className="btn btn-primario" type="submit" form="cerrar-tarea" disabled={cerrar.isPending}>
          Cerrar tarea
        </button>
      }
    >
      <form
        id="cerrar-tarea"
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const resolucion = String(new FormData(e.currentTarget).get('resolucion')).trim()
          if (tarea) cerrar.mutate({ id: tarea.id, resolucion }, { onSuccess: onCerrar })
        }}
      >
        <label className="campo ancho">
          <span>Cómo se resolvió</span>
          <textarea className="input" name="resolucion" rows={3} required minLength={3} />
        </label>
        {cerrar.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(cerrar.error, 'No fue posible cerrar la tarea.')}
          </p>
        )}
      </form>
    </Modal>
  )
}
