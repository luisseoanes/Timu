import * as Menu from '@radix-ui/react-dropdown-menu'
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo, Insignia } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Paginacion } from '@/components/Paginacion'
import { useAuth } from '@/features/auth'
import { useCiudades } from '@/features/catalogos'
import { enlaceWhatsApp } from '@/lib/enlaces'
import { fechaCompacta, fechaCortaConDia, hora, hoyISO, diaISO } from '@/lib/formato'
import { puede } from '@/lib/permisos'
import type { EventoBandeja, FamiliaBandeja } from '@/types'

import { AgendarModal, AplicarModal, AutorizarModal, CancelarModal } from './AccionesPreventivo'
import { useBandejaPreventivos, useRecuentosPreventivos, type VistaBandeja } from './api'
import { dosis, pedido } from './preventivo'

const VISTAS: { valor: VistaBandeja; label: string; vacio: string }[] = [
  { valor: 'por_autorizar', label: 'Por autorizar', vacio: 'Nada por autorizar en el próximo mes.' },
  { valor: 'por_agendar', label: 'Por agendar', vacio: 'Todo lo autorizado del próximo mes ya tiene su visita.' },
  { valor: 'agendados', label: 'Agendados', vacio: 'Ningún preventivo tiene visita agendada.' },
  { valor: 'todos', label: 'Todos', vacio: 'No hay preventivos programados.' },
]

const POR_PAGINA = 20

type Accion = { tipo: 'autorizar'; grupo: FamiliaBandeja } | { tipo: 'agendar' | 'aplicar' | 'cancelar'; evento: EventoBandeja; grupo: FamiliaBandeja }

/** La bandeja de preventivos (R2-PAN-08): por siguiente paso, agrupada por familia porque la familia
 * autoriza de una vez. Cada preventivo lleva solo la acción que toca. */
export function BandejaPreventivos() {
  const { usuario } = useAuth()
  const [params, setParams] = useSearchParams()
  // `?autorizacion=1` es el enlace del Inicio a lo que espera autorización.
  const vista: VistaBandeja = VISTAS.find((v) => v.valor === params.get('vista'))?.valor ?? 'por_autorizar'
  const q = params.get('q') ?? ''
  const ciudad = params.get('ciudad') ?? ''
  const offset = Number(params.get('desde') ?? 0)
  const [accion, setAccion] = useState<Accion | null>(null)
  const ciudades = useCiudades()
  const clinico = puede(usuario, 'clinico')
  // En «Por autorizar» y «Por agendar» el estado es el de la vista: repetirlo en cada fila es ruido.
  const conEstado = vista === 'agendados' || vista === 'todos'

  const filtros = { q: q || undefined, ciudad: ciudad || undefined }
  const recuentos = useRecuentosPreventivos(filtros)
  const bandeja = useBandejaPreventivos({ ...filtros, vista, limit: POR_PAGINA, offset })

  function cambiar(cambios: Record<string, string>) {
    const siguiente = new URLSearchParams(params)
    siguiente.delete('desde')
    siguiente.delete('autorizacion')
    for (const [clave, valor] of Object.entries(cambios)) {
      if (valor) siguiente.set(clave, valor)
      else siguiente.delete(clave)
    }
    setParams(siguiente, { replace: true })
  }
  const cerrar = () => setAccion(null)

  return (
    <section className="tarjeta">
      <div className="filtros bandeja-filtros">
        <div className="segmento bandeja-vistas" role="group" aria-label="Vista de los preventivos">
          {VISTAS.map((v) => (
            <button
              key={v.valor}
              type="button"
              className="segmento-opcion"
              data-state={vista === v.valor ? 'active' : 'inactive'}
              aria-pressed={vista === v.valor}
              onClick={() => cambiar({ vista: v.valor })}
            >
              {v.label}
              {recuentos.data && (
                <>
                  {' '}
                  <span className="segmento-recuento numero">{recuentos.data[v.valor]}</span>
                </>
              )}
            </button>
          ))}
        </div>
        <label className="buscador bandeja-filtro">
          <Icono nombre="buscar" size={18} />
          <input type="search" placeholder="Titular o peludo" value={q} onChange={(e) => cambiar({ q: e.target.value })} aria-label="Buscar preventivos" />
        </label>
        <select className="input bandeja-filtro" value={ciudad} onChange={(e) => cambiar({ ciudad: e.target.value })} aria-label="Ciudad">
          <option value="">Todas las ciudades</option>
          {ciudades.data?.map((c) => (
            <option key={c.nombre} value={c.nombre}>{c.nombre}</option>
          ))}
        </select>
      </div>

      <Consulta
        consulta={bandeja}
        cargando="Cargando los preventivos…"
        error="No fue posible cargar los preventivos."
        vacio={q || ciudad ? 'Ningún preventivo de esta vista coincide con la búsqueda.' : VISTAS.find((v) => v.valor === vista)!.vacio}
        estaVacio={(d) => d.items.length === 0}
      >
        {(d) => (
          <>
            <div className="scroll-x">
              <table className="tabla tabla-apilable bandeja-tabla preventivos-tabla">
                <thead>
                  <tr>
                    <th>Preventivo</th>
                    <th>Toca</th>
                    {conEstado && <th>Estado</th>}
                    <th><span className="sr-only">Acciones</span></th>
                    <th><span className="sr-only">Más acciones</span></th>
                  </tr>
                </thead>
                {/* Un grupo por familia: la familia autoriza de una vez lo que tiene pendiente. */}
                {d.items.map((g) => {
                  const porAutorizar = g.eventos.filter((e) => e.siguiente === 'autorizar')
                  return (
                    <tbody key={g.familia_id} className="preventivos-familia">
                      <tr className="preventivos-familia-cabeza">
                        <th scope="rowgroup" colSpan={conEstado ? 5 : 4}>
                          <span className="preventivos-familia-titulo">
                            <Link to={`/familias/${g.familia_id}`}>{g.titular_nombre}</Link>
                            <span className="apagado">
                              {g.ciudad} · {g.eventos.length} {g.eventos.length === 1 ? 'preventivo' : 'preventivos'}
                            </span>
                          </span>
                          {porAutorizar.length > 0 && (
                            <span className="preventivos-familia-acciones">
                              <a className="btn btn-plano btn-accion" href={enlaceWhatsApp(g.telefono)} target="_blank" rel="noopener noreferrer">
                                <Icono nombre="mensaje" size={16} /> Escribir
                              </a>
                              <button className="btn btn-suave" type="button" onClick={() => setAccion({ tipo: 'autorizar', grupo: g })}>
                                Registrar autorización{porAutorizar.length > 1 ? ` (${porAutorizar.length})` : ''}
                              </button>
                            </span>
                          )}
                        </th>
                      </tr>
                      {g.eventos.map((e) => (
                        <FilaPreventivo
                          key={e.id}
                          evento={e}
                          clinico={clinico}
                          conEstado={conEstado}
                          onAccion={(tipo) => setAccion({ tipo, evento: e, grupo: g })}
                        />
                      ))}
                    </tbody>
                  )
                })}
              </table>
            </div>
            <Paginacion
              total={d.total}
              limit={d.limit}
              offset={d.offset}
              onCambio={(o) => {
                const siguiente = new URLSearchParams(params)
                if (o) siguiente.set('desde', String(o))
                else siguiente.delete('desde')
                setParams(siguiente, { replace: true })
              }}
            />
          </>
        )}
      </Consulta>

      {accion?.tipo === 'autorizar' && (
        <AutorizarModal
          titular={accion.grupo.titular_nombre}
          pedidos={accion.grupo.eventos
            .filter((e) => e.siguiente === 'autorizar')
            .map((e) => ({ id: e.id, titulo: pedido(e), fecha: e.fecha_programada }))}
          onCerrar={cerrar}
        />
      )}
      {accion?.tipo === 'agendar' && (
        <AgendarModal evento={accion.evento} titulo={`${accion.evento.nombre} de ${accion.evento.mascota_nombre}`} ciudad={accion.grupo.ciudad} onCerrar={cerrar} />
      )}
      {accion?.tipo === 'aplicar' && (
        <AplicarModal evento={accion.evento} titulo={`${accion.evento.nombre} de ${accion.evento.mascota_nombre}`} onCerrar={cerrar} />
      )}
      {accion?.tipo === 'cancelar' && (
        <CancelarModal evento={accion.evento} titulo={`${accion.evento.nombre} de ${accion.evento.mascota_nombre}`} onCerrar={cerrar} />
      )}
    </section>
  )
}

function FilaPreventivo({
  evento: e,
  clinico,
  conEstado,
  onAccion,
}: {
  evento: EventoBandeja
  clinico: boolean
  conEstado: boolean
  onAccion: (tipo: 'agendar' | 'aplicar' | 'cancelar') => void
}) {
  const vencido = e.fecha_programada < hoyISO()
  return (
    <tr>
      <td className="principal" data-etiqueta="Preventivo">
        <span className="bandeja-titulo">
          {e.mascota_nombre} · {e.nombre}
        </span>
        <div className="bandeja-detalle">
          <span>{dosis(e.dosis_numero, e.es_refuerzo)}</span>
        </div>
      </td>
      <td data-etiqueta="Toca">
        {/* Lo vencido con icono y palabra, no solo en rojo. */}
        {vencido ? (
          <span className="bandeja-vencida">
            <Icono nombre="alerta" size={14} />
            <span className="numero">{fechaCompacta(e.fecha_programada)} ·</span>
            <span>vencido</span>
          </span>
        ) : (
          <span className="numero sin-cortes">{fechaCompacta(e.fecha_programada)}</span>
        )}
      </td>
      {conEstado && (
      <td data-etiqueta="Estado">
        {e.siguiente === 'autorizar' ? (
          // Su propio icono: el triángulo es de lo vencido, y dos seguidos diluían esa señal.
          <Insignia tono="alerta" icono="llave">Por autorizar</Insignia>
        ) : e.siguiente === 'agendar' ? (
          <Insignia tono="info" icono="calendario">Por agendar</Insignia>
        ) : e.visita ? (
          <span className="preventivo-visita">
            <Distintivo dominio="servicio" valor={e.visita.estado} />
            <Link to={`/servicios/${e.visita.id}`} className="numero">
              {fechaCortaConDia(diaISO(e.visita.programado_para))} · {hora(e.visita.programado_para)}
            </Link>
          </span>
        ) : null}
      </td>
      )}
      <td className="tabla-acciones">
        {e.siguiente === 'agendar' && (
          <button className="btn btn-suave" type="button" onClick={() => onAccion('agendar')} aria-label={`Agendar ${e.nombre} de ${e.mascota_nombre}`}>
            Agendar visita
          </button>
        )}
      </td>
      <td className="preventivo-menu">
        <Menu.Root modal={false}>
          <Menu.Trigger className="btn btn-plano btn-icono" aria-label={`Más acciones de ${e.nombre} de ${e.mascota_nombre}`}>
            <Icono nombre="puntos" size={18} />
          </Menu.Trigger>
          <Menu.Portal>
            <Menu.Content className="menu" align="end" sideOffset={6}>
              {/* Lo aplicado sin visita: con visita, lo registra el servicio al completarse. */}
              {clinico && e.siguiente !== 'autorizar' && (
                <Menu.Item className="menu-item" onSelect={() => onAccion('aplicar')}>
                  Registrar aplicación sin visita
                </Menu.Item>
              )}
              <Menu.Item className="menu-item menu-item-peligro" onSelect={() => onAccion('cancelar')}>
                Cancelar preventivo
              </Menu.Item>
            </Menu.Content>
          </Menu.Portal>
        </Menu.Root>
      </td>
    </tr>
  )
}
