import { useState } from 'react'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Paginacion } from '@/components/Paginacion'
import { fechaHora } from '@/lib/formato'
import type { MensajeRead } from '@/types'

import { useMensajesFamilia } from './api'

const CANALES: Record<string, string> = { whatsapp: 'WhatsApp', email: 'Correo' }

/** Qué se dijo: el texto si lo hay; si no, la plantilla con la que salió. */
function resumen(m: MensajeRead): string {
  if (m.contenido) return m.contenido
  return m.plantilla ? `Plantilla «${m.plantilla}»` : '—'
}

/** 6.1 Historial de comunicaciones de la familia: lo enviado y lo recibido, por cualquier canal. */
export function ComunicacionesFamilia({ familiaId }: { familiaId: string }) {
  const [offset, setOffset] = useState(0)
  const mensajes = useMensajesFamilia(familiaId, offset)
  return (
    <section className="tarjeta">
      <Consulta
        consulta={mensajes}
        cargando="Cargando las comunicaciones…"
        error="No fue posible cargar las comunicaciones."
        vacio="Esta familia todavía no tiene comunicaciones."
        estaVacio={(d) => d.items.length === 0}
      >
        {(d) => (
          <>
            <div className="scroll-x">
              <table className="tabla tabla-apilable" aria-label="Comunicaciones">
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Canal</th>
                    <th>Sentido</th>
                    <th>Mensaje</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {d.items.map((m) => (
                    <tr key={m.id}>
                      <td data-etiqueta="Fecha" className="numero">{fechaHora(m.enviado_en ?? m.created_at)}</td>
                      <td data-etiqueta="Canal">{CANALES[m.canal] ?? m.canal}</td>
                      <td data-etiqueta="Sentido">{m.direccion === 'entrante' ? 'Recibido' : 'Enviado'}</td>
                      <td data-etiqueta="Mensaje">
                        {resumen(m)}
                        {m.masivo && <span className="apagado"> · campaña</span>}
                        {m.error && <p className="error">{m.error}</p>}
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
  )
}
