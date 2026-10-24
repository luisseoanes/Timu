import { useState } from 'react'

import { Consulta } from '@/components/Consulta'
import { Modal } from '@/components/Modal'
import { mensajeError } from '@/lib/errores'
import type { ReglaRead } from '@/types'

import { useActualizarRegla, useEventosReglas, useProbarReglas, useReglas } from './api'

/** Reglas de negocio configurables (F0-12): mora, avisos, renovaciones, elegibilidad. */
export function Reglas() {
  const eventos = useEventosReglas()
  const [evento, setEvento] = useState('')
  const reglas = useReglas(evento || undefined)
  const actualizar = useActualizarRegla()
  const [editando, setEditando] = useState<ReglaRead | null>(null)
  const [probando, setProbando] = useState(false)

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Reglas de negocio</h3>
        <div className="acciones">
          <select className="input" style={{ width: 'auto' }} value={evento} onChange={(e) => setEvento(e.target.value)} aria-label="Evento">
            <option value="">Todos los eventos</option>
            {Object.entries(eventos.data ?? {}).map(([codigo, descripcion]) => (
              <option key={codigo} value={codigo}>{descripcion}</option>
            ))}
          </select>
          <button className="btn btn-suave" type="button" onClick={() => setProbando(true)}>
            Probar reglas
          </button>
        </div>
      </div>
      {actualizar.isError && (
        <p className="error" role="alert">
          {mensajeError(actualizar.error, 'No fue posible actualizar la regla.')}
        </p>
      )}
      <Consulta consulta={reglas} cargando="Cargando reglas…" error="No fue posible cargar las reglas." vacio="No hay reglas para este evento." estaVacio={(d) => d.length === 0}>
        {(d) => (
          <div className="scroll-x">
            <table className="tabla">
              <thead>
                <tr>
                  <th>Regla</th>
                  <th>Evento</th>
                  <th>Prioridad</th>
                  <th>Activa</th>
                  <th><span className="sr-only">Acciones</span></th>
                </tr>
              </thead>
              <tbody>
                {d.map((r) => (
                  <tr key={r.id}>
                    <td className="principal">
                      {r.nombre}
                      <div className="apagado codigo">{resumenCondicion(r.condicion)}</div>
                    </td>
                    <td>{eventos.data?.[r.evento] ?? r.evento}</td>
                    <td className="numero">{r.prioridad}</td>
                    <td>
                      <input
                        type="checkbox"
                        checked={r.activa}
                        aria-label={`${r.nombre} activa`}
                        onChange={(e) => actualizar.mutate({ id: r.id, activa: e.target.checked })}
                      />
                    </td>
                    <td>
                      <button className="btn btn-plano" type="button" onClick={() => setEditando(r)}>
                        Editar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Consulta>
      {editando && <EditarRegla regla={editando} onCerrar={() => setEditando(null)} />}
      <ProbarReglas abierto={probando} onCerrar={() => setProbando(false)} eventos={eventos.data ?? {}} />
    </section>
  )
}

function resumenCondicion(c: Record<string, unknown>): string {
  if (!c || Object.keys(c).length === 0) return 'siempre'
  if (typeof c.campo === 'string') return `${c.campo} ${String(c.op)} ${JSON.stringify(c.valor)}`
  return JSON.stringify(c)
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

function ProbarReglas({ abierto, onCerrar, eventos }: { abierto: boolean; onCerrar: () => void; eventos: Record<string, string> }) {
  const probar = useProbarReglas()
  const [errorJson, setErrorJson] = useState<string | null>(null)

  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          probar.reset()
          onCerrar()
        }
      }}
      titulo="Probar reglas"
      descripcion="Evalúa sin ejecutar nada: muestra qué reglas aplicarían a un contexto."
      pie={
        <button className="btn btn-primario" type="submit" form="probar-reglas" disabled={probar.isPending}>
          Evaluar
        </button>
      }
    >
      <form
        id="probar-reglas"
        className="pila"
        onSubmit={(e) => {
          e.preventDefault()
          setErrorJson(null)
          const d = new FormData(e.currentTarget)
          try {
            probar.mutate({ evento: String(d.get('evento')), contexto: JSON.parse(String(d.get('contexto'))) as Record<string, unknown> })
          } catch {
            setErrorJson('El contexto no es un JSON válido.')
          }
        }}
      >
        <label className="campo">
          <span>Evento</span>
          <select className="input" name="evento">
            {Object.entries(eventos).map(([codigo, descripcion]) => (
              <option key={codigo} value={codigo}>{descripcion}</option>
            ))}
          </select>
        </label>
        <label className="campo">
          <span>Contexto</span>
          <textarea className="input codigo" name="contexto" rows={4} spellCheck={false} defaultValue={'{\n  "dias_mora": 30\n}'} />
        </label>
        {(errorJson || probar.isError) && (
          <p className="error" role="alert">
            {errorJson ?? mensajeError(probar.error, 'No fue posible evaluar.')}
          </p>
        )}
        {probar.data && (
          <div role="status">
            {probar.data.length === 0 ? (
              <p className="apagado">Ninguna regla aplica a este contexto.</p>
            ) : (
              <pre className="codigo bloque-codigo">{JSON.stringify(probar.data, null, 2)}</pre>
            )}
          </div>
        )}
      </form>
    </Modal>
  )
}
