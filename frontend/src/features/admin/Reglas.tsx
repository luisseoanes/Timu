import * as Menu from '@radix-ui/react-dropdown-menu'
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Insignia } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { mensajeError } from '@/lib/errores'
import { fechaCompacta } from '@/lib/formato'
import type { ReglaRead } from '@/types'

import { useActualizarRegla, useReglas } from './api'
import { EditorRegla } from './EditorRegla'
import { ProbarRegla } from './ProbarRegla'

/** Reglas de negocio configurables (Sección 7) en listado con ficha (R2-PAN-10): agrupadas por el
 * evento que las evalúa, y la abierta (`?regla=`) dice en palabras cuándo aplica y qué hace. */
export function Reglas() {
  const [params] = useSearchParams()
  const abierta = params.get('regla')
  return (
    <div className="con-ficha" data-abierta={abierta ? 'true' : undefined}>
      <ReglasLista seleccionada={abierta} />
      {abierta ? (
        <FichaRegla key={abierta} id={abierta} />
      ) : (
        <section className="ficha-abierta ficha-vacia" aria-label="Regla abierta">
          <p>Abre una regla para ver cuándo aplica y qué hace.</p>
        </section>
      )}
    </div>
  )
}

function ReglasLista({ seleccionada }: { seleccionada: string | null }) {
  const [params] = useSearchParams()
  const reglas = useReglas()
  const [nueva, setNueva] = useState(false)
  const enlace = (id: string) => {
    const siguiente = new URLSearchParams(params)
    siguiente.set('regla', id)
    return `?${siguiente}`
  }

  return (
    <section className="listado" aria-labelledby="reglas-titulo">
      <div className="listado-cabeza">
        <h2 id="reglas-titulo">
          Reglas {reglas.data && <span className="apagado numero">{reglas.data.length}</span>}
        </h2>
        {/* Verde solo sin una regla abierta: con la ficha a la vista, el verde es de ella. */}
        <button className={`btn ${seleccionada ? 'btn-suave' : 'btn-primario'}`} type="button" onClick={() => setNueva(true)}>
          <Icono nombre="mas" size={16} /> Nueva regla
        </button>
      </div>
      {nueva && <EditorRegla onCerrar={() => setNueva(false)} />}
      <Consulta consulta={reglas} cargando="Cargando las reglas…" error="No fue posible cargar las reglas." vacio="Aún no hay reglas. Crea la primera con «Nueva regla»." estaVacio={(d) => d.length === 0}>
        {(d) => (
          <ul className="listado-filas" aria-label="Reglas por evento">
            {porEvento(d).map(([evento, del]) => (
              <li key={evento} className="servicios-dia">
                <span className="servicios-dia-rotulo">
                  {del[0]!.evento_nombre}
                  {del[0]!.retirada && ' (retirado)'}
                  {/* El recuento va pegado al nombre: solo, en otra línea, no se sabe de qué es. */}
                  <span className="sin-cortes">
                    {' '}
                    · <span className="numero">{del.length}</span>
                  </span>
                </span>
                <ul className="servicios-dia-filas">
                  {del.map((r) => (
                    <li key={r.id} className="listado-fila" data-seleccionada={r.id === seleccionada}>
                      <span className="listado-fila-cabeza">
                        {/* El enlace es solo el nombre; ::after lo extiende a toda la fila. */}
                        <Link className="listado-fila-enlace" to={enlace(r.id)} aria-current={r.id === seleccionada ? 'page' : undefined}>
                          {r.nombre}
                        </Link>
                        {r.retirada ? <Insignia tono="neutro">Retirada</Insignia> : !r.activa && <Insignia tono="neutro">Inactiva</Insignia>}
                      </span>
                      <span className="servicio-fila-datos">
                        <span>{r.condicion_texto}</span>
                      </span>
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        )}
      </Consulta>
    </section>
  )
}

/** Agrupa por evento en el orden en que llegan (la API ordena por evento y prioridad). */
function porEvento(reglas: ReglaRead[]): [string, ReglaRead[]][] {
  const grupos = new Map<string, ReglaRead[]>()
  for (const r of reglas) grupos.set(r.evento, [...(grupos.get(r.evento) ?? []), r])
  return [...grupos]
}

function FichaRegla({ id }: { id: string }) {
  const reglas = useReglas()
  const r = reglas.data?.find((x) => x.id === id)
  return (
    <section className="ficha-abierta" aria-label="Regla abierta">
      <Consulta consulta={reglas} cargando="Cargando la regla…" error="No fue posible cargar la regla.">
        {() => (r ? <Ficha regla={r} /> : <p className="apagado">Esta regla ya no existe.</p>)}
      </Consulta>
    </section>
  )
}

function Ficha({ regla: r }: { regla: ReglaRead }) {
  const [params] = useSearchParams()
  const actualizar = useActualizarRegla()
  const [editando, setEditando] = useState(false)
  const volver = new URLSearchParams(params)
  volver.delete('regla')

  return (
    <>
      <header className="ficha-cabeza">
        <Link to={`?${volver}`} className="btn btn-plano ficha-volver" aria-label="Volver a las reglas">
          <Icono nombre="volver" size={16} />
        </Link>
        <h2>{r.nombre}</h2>
        <div className="ficha-datos admin-quien">
          {r.retirada ? <Insignia tono="neutro">Retirada</Insignia> : !r.activa && <Insignia tono="neutro">Inactiva</Insignia>}
          <span>{r.evento_nombre}</span>
        </div>
        {/* Una regla de un evento retirado ya no se evalúa ni se puede editar: solo se lee. */}
        {r.retirada ? (
          <p className="admin-nota">Evento retirado: {r.retirada.charAt(0).toLowerCase() + r.retirada.slice(1)}. Esta regla ya no se evalúa ni se puede editar.</p>
        ) : (
        <div className="ficha-acciones">
          <button className="btn btn-primario" type="button" onClick={() => setEditando(true)}>
            Editar regla
          </button>
          <Menu.Root modal={false}>
            <Menu.Trigger className="btn btn-secundario btn-icono" aria-label={`Más acciones con ${r.nombre}`}>
              <Icono nombre="puntos" size={18} />
            </Menu.Trigger>
            <Menu.Portal>
              <Menu.Content className="menu" align="end" sideOffset={6}>
                {/* Desactivar es reversible: la regla deja de evaluarse y conserva su configuración. */}
                <Menu.Item className="menu-item" onSelect={() => actualizar.mutate({ id: r.id, activa: !r.activa })}>
                  {r.activa ? 'Desactivar regla' : 'Activar regla'}
                </Menu.Item>
              </Menu.Content>
            </Menu.Portal>
          </Menu.Root>
        </div>
        )}
        {!r.retirada && !r.activa && <p className="admin-nota">Inactiva: el sistema no la evalúa.</p>}
        {actualizar.isError && (
          <p className="error" role="alert">
            {mensajeError(actualizar.error, 'No fue posible actualizar la regla.')}
          </p>
        )}
      </header>

      <dl className="ficha">
        <div className="ancho">
          <dt>Cuándo aplica</dt>
          <dd>{r.condicion_texto}</dd>
        </div>
        <div className="ancho">
          <dt>Qué hace</dt>
          <dd>{r.accion_texto}</dd>
        </div>
        <div>
          <dt>Prioridad</dt>
          <dd className="numero">{r.prioridad}</dd>
        </div>
        <div>
          <dt>Si aplica</dt>
          <dd>{r.detener ? 'No evalúa las siguientes' : 'Sigue con las siguientes'}</dd>
        </div>
        {(r.vigente_desde || r.vigente_hasta) && (
          <div>
            <dt>Vigencia</dt>
            <dd className="numero">
              {r.vigente_desde && `Desde el ${fechaCompacta(r.vigente_desde)}`}
              {r.vigente_desde && r.vigente_hasta && ' '}
              {r.vigente_hasta && `hasta el ${fechaCompacta(r.vigente_hasta)}`}
            </dd>
          </div>
        )}
        {r.descripcion && (
          <div className="ancho">
            <dt>Para qué sirve</dt>
            <dd>{r.descripcion}</dd>
          </div>
        )}
      </dl>
      <p className="admin-nota">Las reglas de un mismo evento se evalúan de menor a mayor prioridad.</p>
      {!r.retirada && <ProbarRegla regla={r} />}
      {editando && <EditorRegla regla={r} onCerrar={() => setEditando(false)} />}
    </>
  )
}
