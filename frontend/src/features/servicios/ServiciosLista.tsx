import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Paginacion } from '@/components/Paginacion'
import { useCiudades, useNombreTipoServicio } from '@/features/catalogos'
import { estado as etiquetaEstado } from '@/lib/estados'
import { diaISO, fechaCortaConDia, hora, hoyISO } from '@/lib/formato'
import type { EstadoServicio, ServicioListado } from '@/types'

import { ayer, porDia, rotuloDia } from './agenda'
import { useServicios } from './api'
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

const POR_PAGINA = 25

/**
 * El listado de servicios, a la izquierda del panel. Los filtros y la página viven en la URL:
 * abrir un servicio y volver no los pierde. Cada fila dice a quién se atiende.
 */
export function ServiciosLista({ seleccionado, nuevoInicial = false }: { seleccionado?: string; nuevoInicial?: boolean }) {
  const [params, setParams] = useSearchParams()
  const [nuevo, setNuevo] = useState(nuevoInicial)
  const ciudades = useCiudades()
  const estado = (params.get('estado') ?? '') as EstadoServicio | ''
  const ciudad = params.get('ciudad') ?? ''
  // Sin «desde» en la URL, la agenda empieza hoy; «desde=» vacío la abre a todo lo anterior.
  const desde = params.has('desde') ? (params.get('desde') ?? '') : hoyISO()
  const hasta = params.get('hasta') ?? ''
  const offset = Number(params.get('pagina') ?? 0)
  const servicios = useServicios({
    estado: estado || undefined,
    ciudad: ciudad || undefined,
    desde: desde || undefined,
    hasta: hasta || undefined,
    limit: POR_PAGINA,
    offset,
    orden: 'programado_para',
  })
  // En la vista de la agenda (desde hoy, sin estado ni «hasta»), lo de antes que sigue abierto va
  // encima de hoy: un «Por autorizar» de la semana pasada no puede quedar escondido.
  const vistaAgenda = desde === hoyISO() && !estado && !hasta && offset === 0
  const anteriores = useServicios(
    { abiertos: true, ciudad: ciudad || undefined, hasta: ayer(), limit: 50, orden: 'programado_para' },
    vistaAgenda,
  )
  const atrasados = vistaAgenda ? (anteriores.data?.items ?? []) : []
  // El recuento de la cabecera cuenta también los atrasados: son filas del listado.
  const totalAtrasados = vistaAgenda ? (anteriores.data?.total ?? 0) : 0
  const sufijo = params.toString() ? `?${params}` : ''
  const filtrado = Boolean(estado || ciudad || hasta || desde !== hoyISO())

  function cambiar(clave: string, valor: string) {
    const nuevos = new URLSearchParams(params)
    if (valor || clave === 'desde') nuevos.set(clave, valor)
    else nuevos.delete(clave)
    if (clave !== 'pagina') nuevos.delete('pagina')
    setParams(nuevos, { replace: true })
  }

  return (
    <section className="listado" aria-labelledby="servicios-titulo">
      <div className="listado-cabeza">
        <h2 id="servicios-titulo">
          Servicios <span className="apagado numero">{(servicios.data?.total ?? 0) + totalAtrasados}</span>
        </h2>
        {/* Una sola acción verde llena por vista: con un servicio abierto, la principal es la suya. */}
        <button className={`btn ${seleccionado ? 'btn-suave' : 'btn-primario'}`} type="button" onClick={() => setNuevo(true)}>
          <Icono nombre="mas" size={16} />
          Agendar servicio
        </button>
      </div>

      <div className="filtros servicios-filtros">
        <select className="input" value={estado} onChange={(e) => cambiar('estado', e.target.value)} aria-label="Estado">
          <option value="">Todos los estados</option>
          {ESTADOS.map((e) => (
            <option key={e} value={e}>
              {etiquetaEstado('servicio', e).label}
            </option>
          ))}
        </select>
        <select className="input" value={ciudad} onChange={(e) => cambiar('ciudad', e.target.value)} aria-label="Ciudad">
          <option value="">Todas las ciudades</option>
          {ciudades.data?.map((c) => (
            <option key={c.codigo} value={c.nombre}>
              {c.nombre}
            </option>
          ))}
        </select>
        <label className="campo">
          <span>Desde</span>
          <input className="input" type="date" value={desde} onChange={(e) => cambiar('desde', e.target.value)} />
        </label>
        <label className="campo">
          <span>Hasta</span>
          <input className="input" type="date" value={hasta} onChange={(e) => cambiar('hasta', e.target.value)} />
        </label>
      </div>

      <Consulta
        consulta={servicios}
        cargando="Cargando servicios…"
        error="No fue posible cargar los servicios."
        vacio={
          filtrado
            ? 'Ningún servicio coincide con estos filtros. Quita alguno o amplía las fechas.'
            : 'No hay servicios agendados desde hoy. Agenda uno con «Agendar servicio».'
        }
        estaVacio={(d) => d.items.length === 0 && atrasados.length === 0}
      >
        {(d) => (
          <>
            <ul className="listado-filas" aria-label="Servicios">
              {atrasados.length > 0 && (
                <li className="servicios-dia" data-atrasados="true">
                  <span className="servicios-dia-rotulo">
                    <Icono nombre="alerta" size={14} />
                    Atrasados · <span className="numero">{totalAtrasados}</span>
                  </span>
                  <ul className="servicios-dia-filas">
                    {atrasados.map((s) => (
                      <FilaServicio key={s.id} servicio={s} seleccionado={seleccionado} sufijo={sufijo} conDia />
                    ))}
                  </ul>
                  {totalAtrasados > atrasados.length && (
                    <p className="servicios-mas">
                      Y {totalAtrasados - atrasados.length} atrasados más: vacía «Desde» para verlos todos.
                    </p>
                  )}
                </li>
              )}
              {porDia(d.items).map((g) => (
                <li key={g.dia ?? 'sin-fecha'} className="servicios-dia">
                  <span className="servicios-dia-rotulo">
                    {g.dia ? rotuloDia(g.dia) : 'Sin fecha'} · <span className="numero">{g.servicios.length}</span>
                  </span>
                  <ul className="servicios-dia-filas">
                    {g.servicios.map((s) => (
                      <FilaServicio key={s.id} servicio={s} seleccionado={seleccionado} sufijo={sufijo} />
                    ))}
                  </ul>
                </li>
              ))}
            </ul>
            <Paginacion
              total={d.total}
              limit={d.limit}
              offset={d.offset}
              onCambio={(n) => cambiar('pagina', n ? String(n) : '')}
            />
          </>
        )}
      </Consulta>

      <NuevoServicioModal abierto={nuevo} onCambio={setNuevo} />
    </section>
  )
}

/** Una fila del listado: a quién se atiende, cuándo y en qué estado. */
function FilaServicio({
  servicio: s,
  seleccionado,
  sufijo,
  conDia = false,
}: {
  servicio: ServicioListado
  seleccionado?: string
  sufijo: string
  /** Fuera de su día (en «Atrasados»), la fila dice también la fecha. */
  conDia?: boolean
}) {
  const nombreTipo = useNombreTipoServicio()
  return (
    <li className="listado-fila" data-seleccionada={s.id === seleccionado}>
      <span className="listado-fila-cabeza">
        {/* El enlace es solo el título; ::after lo extiende a toda la fila. */}
        <Link className="listado-fila-enlace" to={`/servicios/${s.id}${sufijo}`} aria-current={s.id === seleccionado ? 'page' : undefined}>
          {s.mascota ? `${s.mascota.nombre} · ${nombreTipo(s.tipo_codigo)}` : nombreTipo(s.tipo_codigo)}
        </Link>
        <Distintivo dominio="servicio" valor={s.estado} />
      </span>
      <span className="servicio-fila-datos">
        {s.programado_para && (
          <span className="numero">
            {conDia ? `${fechaCortaConDia(diaISO(s.programado_para))} · ` : ''}
            {hora(s.programado_para)}
          </span>
        )}
        <span>{s.familia.titular_nombre}</span>
        <span>{s.ciudad}</span>
      </span>
      {/* Solo si el estado no lo dice ya: «Pendiente de autorización» lo lleva en su distintivo. */}
      {s.requiere_autorizacion && !s.autorizado && !['cancelado', 'pendiente_autorizacion'].includes(s.estado) && (
        <span className="servicio-fila-alerta">
          <Icono nombre="alerta" size={14} />
          Por autorizar
        </span>
      )}
    </li>
  )
}
