import * as Menu from '@radix-ui/react-dropdown-menu'
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Insignia } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { mensajeError } from '@/lib/errores'
import { fechaCompacta } from '@/lib/formato'
import type { ReglaRead } from '@/types'

import { useActualizarRegla, useReglas } from './api'
import { ProbarRegla } from './ProbarRegla'

/** Reglas de negocio configurables (F0-12) en listado con ficha (R2-PAN-10): agrupadas por el
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
      </div>
      <Consulta consulta={reglas} cargando="Cargando las reglas…" error="No fue posible cargar las reglas." vacio="No hay reglas configuradas." estaVacio={(d) => d.length === 0}>
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
      {editando && <EditarRegla regla={r} onCerrar={() => setEditando(false)} />}
    </>
  )
}

function EditarRegla({ regla, onCerrar }: { regla: ReglaRead; onCerrar: () => void }) {
  const actualizar = useActualizarRegla()
  const [errorJson, setErrorJson] = useState<string | null>(null)

  return (
    <Modal
      abierto
      onCambio={(v) => !v && onCerrar()}
      titulo={regla.nombre}
      descripcion="Condición y acción en JSON. El backend las valida antes de guardar."
      pie={
        <button className="btn btn-primario" type="submit" form="editar-regla" disabled={actualizar.isPending}>
          Guardar
        </button>
      }
    >
      <form
        id="editar-regla"
        className="pila"
        onSubmit={(e) => {
          e.preventDefault()
          setErrorJson(null)
          const d = new FormData(e.currentTarget)
          try {
            actualizar.mutate(
              {
                id: regla.id,
                prioridad: Number(d.get('prioridad')),
                condicion: JSON.parse(String(d.get('condicion'))),
                accion: JSON.parse(String(d.get('accion'))),
              },
              { onSuccess: onCerrar },
            )
          } catch {
            setErrorJson('La condición o la acción no es un JSON válido.')
          }
        }}
      >
        <label className="campo">
          <span>Prioridad (menor se evalúa primero)</span>
          <input className="input" name="prioridad" type="number" defaultValue={regla.prioridad} />
        </label>
        <label className="campo">
          <span>Condición</span>
          <textarea className="input codigo" name="condicion" rows={5} spellCheck={false} defaultValue={JSON.stringify(regla.condicion, null, 2)} />
        </label>
        <label className="campo">
          <span>Acción</span>
          <textarea className="input codigo" name="accion" rows={5} spellCheck={false} defaultValue={JSON.stringify(regla.accion, null, 2)} />
        </label>
        {(errorJson || actualizar.isError) && (
          <p className="error" role="alert">
            {errorJson ?? mensajeError(actualizar.error, 'La regla no es válida.')}
          </p>
        )}
      </form>
    </Modal>
  )
}
