import { useState } from 'react'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Paginacion } from '@/components/Paginacion'
import { mensajeError } from '@/lib/errores'
import { diaISO, fechaCompacta, fechaHora, hora, telefono } from '@/lib/formato'

import { useBajas, useCrearBaja, useMensajes, usePlantillasWhatsApp, useQuitarBaja } from './api'

export function Mensajes() {
  const [estado, setEstado] = useState('')
  const [offset, setOffset] = useState(0)
  const mensajes = useMensajes({ estado: estado || undefined, limit: 25, offset })
  const bajas = useBajas()
  // Cada plantilla por el nombre que le da el equipo; el código de Meta si no lo tiene (DEU-10).
  const plantillas = usePlantillasWhatsApp()
  const nombrePlantilla = (codigo: string) => plantillas.data?.find((p) => p.nombre === codigo && p.titulo)?.titulo ?? codigo
  const crearBaja = useCrearBaja()
  const quitarBaja = useQuitarBaja()

  return (
    <div className="con-rail">
      <section className="tarjeta">
        <div className="tarjeta-cabeza">
          <h3>Mensajes de WhatsApp</h3>
          <select className="input bandeja-filtro" value={estado} onChange={(e) => { setEstado(e.target.value); setOffset(0) }} aria-label="Estado del mensaje">
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
                <table className="tabla tabla-apilable bandeja-tabla">
                  <thead>
                    <tr>
                      <th>Mensaje</th>
                      <th>Cuándo</th>
                      <th>Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {d.items.map((m) => (
                      <tr key={m.id}>
                        <td className="principal" data-etiqueta="Mensaje">
                          <span className="mensaje-contenido">{m.contenido ?? (m.plantilla ? `Plantilla «${nombrePlantilla(m.plantilla)}»` : '—')}</span>
                          <div className="bandeja-detalle">
                            {/* La dirección en palabras: una flecha sola no la lee nadie con lector de pantalla. */}
                            <span>{m.direccion === 'entrante' ? 'Escribió' : 'Le escribimos a'}</span>
                            <span className="numero sin-cortes">{telefono(m.destino)}</span>
                            {m.contenido && m.plantilla && <span>Plantilla «{nombrePlantilla(m.plantilla)}»</span>}
                          </div>
                          {m.error && <div className="error">{m.error}</div>}
                        </td>
                        <td data-etiqueta="Cuándo">
                          <span className="numero sin-cortes" title={fechaHora(m.created_at)}>
                            {fechaCompacta(diaISO(m.created_at))} · {hora(m.created_at)}
                          </span>
                        </td>
                        <td data-etiqueta="Estado">
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
            className="acciones campana-baja"
            onSubmit={(e) => {
              e.preventDefault()
              const fd = new FormData(e.currentTarget)
              const form = e.currentTarget
              crearBaja.mutate({ telefono: String(fd.get('telefono')).trim() }, { onSuccess: () => form.reset() })
            }}
          >
            <input className="input" name="telefono" aria-label="Celular a dar de baja" placeholder="Celular" inputMode="tel" required />
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
                    <strong className="numero">{telefono(x.destino)}</strong>
                    <span>Desde el {fechaCompacta(diaISO(x.created_at))}</span>
                  </div>
                  <button className="btn btn-plano" type="button" onClick={() => quitarBaja.mutate(x.destino)} aria-label={`Quitar la baja de ${telefono(x.destino)}`}>
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
