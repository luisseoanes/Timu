import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Insignia } from '@/components/Distintivo'
import { Modal } from '@/components/Modal'
import { mensajeError } from '@/lib/errores'
import { diaISO, fechaCompacta, hora, telefono } from '@/lib/formato'
import type { ConversacionRead } from '@/types'

import { useConversaciones, useLiberarConversacion, useResponderConversacion } from './api'

// Los valores son los del backend (comercial/router.py): automatica | con_asesor.
const VISTAS = [
  { valor: 'con_asesor', label: 'Por atender', vacio: 'Nadie espera a un asesor. Cuando alguien lo pida por WhatsApp, aparece aquí.' },
  { valor: 'automatica', label: 'Con el asistente', vacio: 'El asistente no está atendiendo ninguna conversación.' },
  { valor: '', label: 'Todas', vacio: 'Todavía nadie ha escrito por WhatsApp.' },
] as const

// Lo que guarda el asistente (comercial/conversacion.py); el resto son capturas del guion.
const DATOS: Record<string, string> = {
  ciudad: 'Ciudad',
  ciudad_sin_cobertura: 'Ciudad sin cobertura',
  mascotas: 'Mascotas',
  plan: 'Plan sugerido',
}

/** El nombre de un dato en palabras: nunca la clave del guion tal cual. */
function nombreDato(clave: string): string {
  const texto = clave.replaceAll('_', ' ')
  return DATOS[clave] ?? texto.charAt(0).toUpperCase() + texto.slice(1)
}

/** Lo que la persona le contó al asistente: ciudad, mascotas, el plan que le sugirió. */
function contado(c: ConversacionRead): string {
  const partes = Object.entries(c.datos)
    .filter(([, v]) => v !== null && v !== '' && !(Array.isArray(v) && v.length === 0))
    .map(([k, v]) => `${nombreDato(k)}: ${Array.isArray(v) ? v.join(', ') : String(v)}`)
  return partes.join(' · ') || 'Aún no ha contado nada'
}

/** Las conversaciones de WhatsApp como bandeja: las que esperan a una persona, primero. */
export function Conversaciones() {
  const [estado, setEstado] = useState<string>('con_asesor')
  const [respondiendo, setRespondiendo] = useState<ConversacionRead | null>(null)
  const conversaciones = useConversaciones(estado || undefined)
  const liberar = useLiberarConversacion()

  return (
    <section className="tarjeta">
      <div className="filtros bandeja-filtros">
        <div className="segmento bandeja-vistas bandeja-vistas-tres" role="group" aria-label="Estado de las conversaciones">
          {VISTAS.map((v) => (
            <button
              key={v.valor}
              type="button"
              className="segmento-opcion"
              data-state={estado === v.valor ? 'active' : 'inactive'}
              aria-pressed={estado === v.valor}
              onClick={() => setEstado(v.valor)}
            >
              {v.label}
            </button>
          ))}
        </div>
      </div>
      {liberar.isError && (
        <p className="error" role="alert">
          {mensajeError(liberar.error, 'No fue posible devolver la conversación al asistente.')}
        </p>
      )}
      <Consulta
        consulta={conversaciones}
        cargando="Cargando las conversaciones…"
        error="No fue posible cargar las conversaciones."
        vacio={VISTAS.find((v) => v.valor === estado)!.vacio}
        estaVacio={(d) => d.length === 0}
      >
        {(d) => (
          <div className="scroll-x">
            <table className="tabla tabla-apilable bandeja-tabla conversaciones-tabla">
              <thead>
                <tr>
                  <th>Quién</th>
                  <th>Lo que contó</th>
                  <th>Último mensaje</th>
                  <th>Estado</th>
                  <th><span className="sr-only">Acciones</span></th>
                </tr>
              </thead>
              <tbody>
                {d.map((c) => (
                  <tr key={c.id}>
                    <td className="principal" data-etiqueta="Quién">
                      {c.interesado_nombre ?? <span className="numero">{telefono(c.telefono)}</span>}
                      <div className="bandeja-detalle">
                        {c.interesado_nombre && <span className="numero">{telefono(c.telefono)}</span>}
                        <span>{c.interesado_id ? 'Interesado' : 'Familia afiliada'}</span>
                      </div>
                    </td>
                    <td data-etiqueta="Lo que contó">{contado(c)}</td>
                    <td data-etiqueta="Último mensaje">
                      <span className="numero sin-cortes">
                        {fechaCompacta(diaISO(c.updated_at))} · {hora(c.updated_at)}
                      </span>
                    </td>
                    <td data-etiqueta="Estado">
                      {c.estado === 'con_asesor' ? (
                        <Insignia tono="alerta" icono="mensaje">Espera a un asesor</Insignia>
                      ) : (
                        <Insignia tono="info">Atiende el asistente</Insignia>
                      )}
                    </td>
                    <td className="tabla-acciones">
                      {/* La de un interesado se contesta en su ficha, con su historia; la de una familia, aquí. */}
                      {c.interesado_id ? (
                        <Link className="btn btn-suave" to={`/panel/comercial?interesado=${c.interesado_id}`}>
                          Abrir conversación
                        </Link>
                      ) : (
                        <button className="btn btn-suave" type="button" onClick={() => setRespondiendo(c)}>
                          Responder
                        </button>
                      )}
                      {c.estado === 'con_asesor' && (
                        <button className="btn btn-plano" type="button" disabled={liberar.isPending} onClick={() => liberar.mutate(c.id)}>
                          Devolver al asistente
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Consulta>
      {respondiendo && <ResponderModal conversacion={respondiendo} onCerrar={() => setRespondiendo(null)} />}
    </section>
  )
}

function ResponderModal({ conversacion: c, onCerrar }: { conversacion: ConversacionRead; onCerrar: () => void }) {
  const responder = useResponderConversacion()
  return (
    <Modal
      abierto
      onCambio={(v) => !v && onCerrar()}
      titulo={`Responder a ${telefono(c.telefono)}`}
      descripcion="Sale por WhatsApp desde el número de TIMU, dentro de las 24 horas desde su último mensaje."
      pie={
        <button className="btn btn-primario" type="submit" form="responder-conversacion" disabled={responder.isPending}>
          {responder.isPending ? 'Enviando…' : 'Enviar'}
        </button>
      }
    >
      <form
        id="responder-conversacion"
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const texto = String(new FormData(e.currentTarget).get('texto')).trim()
          responder.mutate({ id: c.id, texto }, { onSuccess: onCerrar })
        }}
      >
        <label className="campo ancho">
          <span>Mensaje</span>
          <textarea className="input" name="texto" rows={4} required maxLength={4000} />
        </label>
        {responder.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(responder.error, 'No fue posible enviar el mensaje.')}
          </p>
        )}
      </form>
    </Modal>
  )
}
