import { useState } from 'react'

import { Consulta } from '@/components/Consulta'
import { Distintivo, Insignia } from '@/components/Distintivo'
import { Paginacion } from '@/components/Paginacion'
import { mensajeError } from '@/lib/errores'
import { fecha, fechaHora } from '@/lib/formato'

import {
  useBajas,
  useCrearBaja,
  useMensajes,
  useQuitarBaja,
} from './api'

export function Mensajes() {
  const [estado, setEstado] = useState('')
  const [offset, setOffset] = useState(0)
  const mensajes = useMensajes({ estado: estado || undefined, limit: 25, offset })
  const bajas = useBajas()
  const crearBaja = useCrearBaja()
  const quitarBaja = useQuitarBaja()

  return (
    <div className="con-rail">
      <section className="tarjeta">
        <div className="tarjeta-cabeza">
          <h3>Mensajes de WhatsApp</h3>
          <select className="input" style={{ width: 'auto' }} value={estado} onChange={(e) => { setEstado(e.target.value); setOffset(0) }} aria-label="Estado del mensaje">
            <option value="">Todos</option>
            <option value="fallido">Fallidos</option>
            <option value="encolado">En cola</option>
            <option value="leido">Leídos</option>
            <option value="recibido">Recibidos</option>
          </select>
        </div>
        <Consulta
          consulta={mensajes}
          cargando="Cargando mensajes…"
          error="No fue posible cargar los mensajes."
          vacio="No hay mensajes."
          estaVacio={(d) => d.items.length === 0}
        >
          {(d) => (
            <>
              <div className="scroll-x">
                <table className="tabla">
                  <thead>
                    <tr>
                      <th>Fecha</th>
                      <th>Destino</th>
                      <th>Contenido</th>
                      <th>Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {d.items.map((m) => (
                      <tr key={m.id}>
                        <td className="numero">{fechaHora(m.created_at)}</td>
                        <td className="numero">
                          {m.direccion === 'entrante' ? '← ' : '→ '}
                          {m.destino ?? '—'}
                        </td>
                        <td>
                          {m.plantilla ? <Insignia tono="neutro">{m.plantilla}</Insignia> : null} {m.contenido}
                          {m.error && <div className="error">{m.error}</div>}
                        </td>
                        <td>
                          <Distintivo dominio="mensaje" valor={m.estado} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Paginacion total={d.total} limit={d.limit} offset={d.offset} onCambio={setOffset} />
            </>
          )}
        </Consulta>
      </section>
      <aside className="rail">
        <section className="tarjeta">
          <div className="tarjeta-cabeza">
            <h3>Dados de baja</h3>
          </div>
          <p className="apagado">No reciben campañas masivas; los avisos del servicio sí les llegan.</p>
          <form
            className="acciones"
            style={{ marginBlock: 'var(--e3)' }}
            onSubmit={(e) => {
              e.preventDefault()
              const fd = new FormData(e.currentTarget)
              const form = e.currentTarget
              crearBaja.mutate({ telefono: String(fd.get('telefono')).trim() }, { onSuccess: () => form.reset() })
            }}
          >
            <input className="input" name="telefono" aria-label="Celular a dar de baja" placeholder="Celular" required style={{ flex: 1 }} />
            <button className="btn btn-suave" type="submit" disabled={crearBaja.isPending}>
              Agregar
            </button>
          </form>
          {(crearBaja.isError || quitarBaja.isError) && (
            <p className="error" role="alert">
              {mensajeError(crearBaja.error ?? quitarBaja.error, 'No fue posible actualizar las bajas.')}
            </p>
          )}
          <Consulta consulta={bajas} cargando="Cargando…" error="No fue posible cargar las bajas." vacio="Nadie se ha dado de baja." estaVacio={(b) => b.length === 0}>
            {(b) =>
              b.map((x) => (
                <div key={x.id} className="fila">
                  <div className="fila-cuerpo">
                    <strong className="numero">{x.destino}</strong>
                    <span>{fecha(x.created_at.slice(0, 10))}</span>
                  </div>
                  <button className="btn btn-plano" type="button" onClick={() => quitarBaja.mutate(x.destino)} aria-label={`Quitar la baja de ${x.destino}`}>
                    Quitar
                  </button>
                </div>
              ))
            }
          </Consulta>
        </section>
      </aside>
    </div>
  )
}
