import * as Menu from '@radix-ui/react-dropdown-menu'
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
import { NOMBRE_ROL, puede } from '@/lib/permisos'
import type { FamiliaRead, TareaListado, TareaRead } from '@/types'


import {
  AREAS,
  PERFILES_DEL_AREA,
  useAsignarTarea,
  useCerrarTarea,
  useCrearTarea,
  useIniciarTarea,
  useTareas,
  type Area,
  type FiltrosTareas,
} from './api'

type Vista = 'mias' | 'pedidas' | 'sin_asignar' | 'vencidas' | 'todas'

const VISTAS: { valor: Vista; label: string }[] = [
  { valor: 'mias', label: 'Mis tareas' },
  // Las que pedí, también a otras áreas: para seguirlas (decidido con el usuario el 2026-11-20).
  { valor: 'pedidas', label: 'Pedidas por mí' },
  { valor: 'sin_asignar', label: 'Sin asignar' },
  { valor: 'vencidas', label: 'Vencidas' },
  { valor: 'todas', label: 'Todas' },
]

const POR_PAGINA = 25

/** De dónde salió una tarea que no pidió nadie desde el panel, en palabras. */
function origenAutomatico(t: TareaListado): string | null {
  if (t.origen === 'conversacion') return 'el asistente de WhatsApp la pasó a un asesor'
  if (t.origen === 'encuesta') return 'una encuesta con novedad'
  if (t.origen_nombre) return `«${t.origen_nombre}»`
  return null
}

/** Bandeja de tareas del equipo (6.4): lo que alguien tiene que resolver y para cuándo. */
export function TareasPage() {
  const { usuario } = useAuth()
  const [params] = useSearchParams()
  // Abre en lo propio (crítica de R4-CIE-02: abría en «Todas»), y sin nada propio en lo que nadie
  // tiene. Hasta que se elige una vista, la de entrada depende de si hay tareas propias pendientes.
  const [elegida, setElegida] = useState<Vista | null>(params.get('vencidas') === '1' ? 'vencidas' : null)
  const propias = useTareas({ mias: true, estado: 'pendiente', limit: 1 })
  const vista: Vista = elegida ?? (propias.data?.total === 0 ? 'sin_asignar' : 'mias')
  const setVista = (v: Vista) => setElegida(v)
  const [area, setArea] = useState<Area | ''>('')
  // Pendientes: abiertas y en progreso. Con «Abiertas», iniciar una tarea la sacaba de la vista.
  const [estado, setEstado] = useState('pendiente')
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
    pedidas_por_mi: vista === 'pedidas' || undefined,
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
        <h2>Tareas</h2>
        <button className="btn btn-primario" type="button" onClick={() => setNueva(true)}>
          <Icono nombre="mas" size={16} /> Nueva tarea
        </button>
      </div>
      <div className="filtros bandeja-filtros">
        <div className="segmento bandeja-vistas" role="group" aria-label="Vista de tareas">
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
        <select className="input bandeja-filtro" value={area} onChange={(e) => { setArea(e.target.value as Area | ''); setOffset(0) }} aria-label="Área">
          <option value="">Todas las áreas</option>
          {AREAS.map((a) => (
            <option key={a.valor} value={a.valor}>{a.label}</option>
          ))}
        </select>
        <select className="input bandeja-filtro" value={estado} onChange={(e) => { setEstado(e.target.value); setOffset(0) }} aria-label="Estado de la tarea">
          <option value="pendiente">Pendientes</option>
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
              <table className="tabla tabla-apilable bandeja-tabla">
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
                    // Una de otra área (en «Pedidas por mí») se sigue, pero la trabaja su área.
                    const trabajable = Boolean(usuario && PERFILES_DEL_AREA[t.area as Area]?.includes(usuario.rol))
                    const automatica = origenAutomatico(t)
                    return (
                      <tr key={t.id}>
                        <td className="principal" data-etiqueta="Tarea">
                          <span className="bandeja-titulo">
                            {t.titulo}
                            <Distintivo dominio="tarea" valor={t.estado} />
                          </span>
                          {/* A quién afecta: la familia y, si es de un servicio, cuál y de quién. */}
                          <div className="bandeja-detalle">
                            <span>{area}</span>
                            {t.creada_por ? (
                              <span>
                                Pedida por {t.creada_por.nombre} ({NOMBRE_ROL[t.creada_por.rol]})
                              </span>
                            ) : (
                              automatica && <span>Automática: {automatica}</span>
                            )}
                            {t.familia && <Link to={`/panel/familias/${t.familia.id}`}>{t.familia.titular_nombre}</Link>}
                            {t.servicio && (
                              <Link to={`/panel/servicios/${t.servicio.id}`}>
                                {nombreTipo(t.servicio.tipo_codigo)}
                                {t.servicio.mascota_nombre && ` de ${t.servicio.mascota_nombre}`}
                              </Link>
                            )}
                          </div>
                          {t.descripcion && (
                            <div className="tarea-descripcion" title={t.descripcion}>
                              {t.descripcion}
                            </div>
                          )}
                        </td>
                        <td data-etiqueta="Vence">
                          {/* Lo vencido se dice en texto e icono, no solo en rojo. */}
                          {vencida ? (
                            <span className="bandeja-vencida">
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
                        <td data-etiqueta="Responsable">{nombreDe(t.asignada_a_id)}</td>
                        <td className="tabla-acciones">
                          {trabajable && (
                            <AccionesTarea
                              tarea={t}
                              usuarioId={usuario?.id}
                              equipo={(usuarios.data ?? []).filter(
                                (u) => PERFILES_DEL_AREA[t.area as Area]?.includes(u.rol) || u.id === t.asignada_a_id,
                              )}
                              onAsignar={(usuarioId) => asignar.mutate({ id: t.id, usuario_id: usuarioId })}
                              onIniciar={() => iniciar.mutate(t.id)}
                              onCerrar={() => setCerrando(t)}
                            />
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

/**
 * Lo que se hace con una tarea, sin tres controles por fila (crítica de R4-CIE-02): una sola acción
 * a la vista —«Tomar» si nadie la tiene, «Cerrar» si es de quien mira, la conversación si viene del
 * asistente— y el resto (asignarla a otra persona, iniciarla, cerrarla) en el menú de tres puntos.
 */
function AccionesTarea({
  tarea: t,
  usuarioId,
  equipo,
  onAsignar,
  onIniciar,
  onCerrar,
}: {
  tarea: TareaListado
  usuarioId: string | undefined
  /** Quienes ven el área de la tarea, y quien ya la tenía. */
  equipo: { id: string; nombre: string }[]
  onAsignar: (usuarioId: string | null) => void
  onIniciar: () => void
  onCerrar: () => void
}) {
  if (t.estado === 'cerrada') return null
  const conversacion = t.origen === 'conversacion'
  const libre = !t.asignada_a_id
  const mia = Boolean(usuarioId) && t.asignada_a_id === usuarioId
  return (
    <>
      {/* La del asistente de WhatsApp es la conversación: se atiende allí, y al terminarla la tarea se
          cierra sola. */}
      {conversacion ? (
        <Link className="btn btn-suave" to="/panel/comercial?pestana=conversaciones">
          Ver la conversación
        </Link>
      ) : libre && usuarioId ? (
        <button className="btn btn-suave" type="button" onClick={() => onAsignar(usuarioId)}>
          Tomar
        </button>
      ) : (
        mia && (
          <button className="btn btn-suave" type="button" onClick={onCerrar}>
            Cerrar
          </button>
        )
      )}
      <Menu.Root modal={false}>
        <Menu.Trigger className="btn btn-plano btn-icono" aria-label={`Más acciones de ${t.titulo}`}>
          <Icono nombre="puntos" size={18} />
        </Menu.Trigger>
        <Menu.Portal>
          <Menu.Content className="menu" align="end" sideOffset={6}>
            <Menu.Sub>
              <Menu.SubTrigger className="menu-item menu-item-sub">
                Asignar a…
                <Icono nombre="derecha" size={14} />
              </Menu.SubTrigger>
              <Menu.Portal>
                <Menu.SubContent className="menu" sideOffset={4}>
                  <Menu.Item className="menu-item" disabled={libre} onSelect={() => onAsignar(null)}>
                    Sin asignar
                  </Menu.Item>
                  {equipo.map((u) => (
                    <Menu.Item
                      key={u.id}
                      className={u.id === t.asignada_a_id ? 'menu-item active' : 'menu-item'}
                      disabled={u.id === t.asignada_a_id}
                      onSelect={() => onAsignar(u.id)}
                    >
                      {u.id === usuarioId ? `${u.nombre} (tú)` : u.nombre}
                    </Menu.Item>
                  ))}
                </Menu.SubContent>
              </Menu.Portal>
            </Menu.Sub>
            {t.estado === 'abierta' && !libre && (
              <Menu.Item className="menu-item" onSelect={onIniciar}>
                Iniciar
              </Menu.Item>
            )}
            {!mia && !conversacion && (
              <Menu.Item className="menu-item" onSelect={onCerrar}>
                Cerrar
              </Menu.Item>
            )}
            {t.familia && (
              <Menu.Item className="menu-item" asChild>
                <Link to={`/panel/familias/${t.familia.id}`}>Ver la familia</Link>
              </Menu.Item>
            )}
          </Menu.Content>
        </Menu.Portal>
      </Menu.Root>
    </>
  )
}

function NuevaTareaModal({ abierto, onCerrar }: { abierto: boolean; onCerrar: () => void }) {
  const crear = useCrearTarea()
  const { usuario } = useAuth()
  const equipo = useEquipo()
  const [familia, setFamilia] = useState<FamiliaRead | null>(null)
  const [area, setArea] = useState<Area>('operaciones')
  // El responsable, solo entre quienes ven el área: a otro se le perdería (Sección 12).
  const delArea = (equipo.data ?? []).filter((u) => PERFILES_DEL_AREA[area].includes(u.rol))

  function guardar(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const d = new FormData(e.currentTarget)
    const dias = String(d.get('vence_en_dias') ?? '')
    crear.mutate(
      {
        titulo: String(d.get('titulo')).trim(),
        descripcion: String(d.get('descripcion') ?? '').trim() || undefined,
        area,
        prioridad: d.get('prioridad') as 'baja' | 'media' | 'alta',
        vence_en_dias: dias ? Number(dias) : undefined,
        familia_id: familia?.id,
        asignada_a_id: String(d.get('asignada_a_id') ?? '') || undefined,
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
          <span>¿Para qué área?</span>
          <select className="input" name="area" value={area} onChange={(e) => setArea(e.target.value as Area)}>
            {AREAS.map((a) => (
              <option key={a.valor} value={a.valor}>{a.label}</option>
            ))}
          </select>
        </label>
        <div className="campo">
          <label htmlFor="nueva-tarea-responsable">Responsable (opcional)</label>
          {/* `key`: al cambiar de área, el responsable elegido de la otra ya no vale. */}
          <select key={area} id="nueva-tarea-responsable" className="input" name="asignada_a_id" defaultValue="">
            <option value="">La toma alguien del área</option>
            {delArea.map((u) => (
              <option key={u.id} value={u.id}>{u.nombre}</option>
            ))}
          </select>
        </div>
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
        {/* Buscar una familia pide verlas: el médico, que también crea tareas, no las ve. */}
        {puede(usuario, 'verFamilias') && (
          <div className="ancho">
            <SelectorFamilia valor={familia} onCambio={setFamilia} etiqueta="Familia relacionada (opcional)" />
          </div>
        )}
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
