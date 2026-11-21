import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import { BurbujaMensaje } from '@/components/BurbujaMensaje'
import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { Paginacion } from '@/components/Paginacion'
import { useAuth } from '@/features/auth'
import { mensajeError } from '@/lib/errores'
import { diaISO, fechaCompacta, fechaHora, hora, telefono } from '@/lib/formato'
import { puede } from '@/lib/permisos'
import type { MensajeRead } from '@/types'

import { useBajas, useConversacion, useCrearBaja, useMensajes, usePlantillasWhatsApp, useQuitarBaja, type FiltrosMensajes } from './api'

export function Mensajes() {
  const [estado, setEstado] = useState('')
  const [direccion, setDireccion] = useState<FiltrosMensajes['direccion'] | ''>('')
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')
  const [texto, setTexto] = useState('')
  // La búsqueda sale al dejar de escribir, y desde tres caracteres: lo que exige la API.
  const [busqueda, setBusqueda] = useState('')
  const [offset, setOffset] = useState(0)
  const [abierto, setAbierto] = useState<MensajeRead | null>(null)
  useEffect(() => {
    const limpio = texto.trim()
    const espera = setTimeout(() => {
      setBusqueda(limpio.length >= 3 ? limpio : '')
      setOffset(0)
    }, 300)
    return () => clearTimeout(espera)
  }, [texto])
  const mensajes = useMensajes({
    estado: estado || undefined,
    q: busqueda || undefined,
    direccion: direccion || undefined,
    desde: desde || undefined,
    hasta: hasta || undefined,
    limit: 25,
    offset,
  })
  const filtrando = Boolean(estado || busqueda || direccion || desde || hasta)
  const bajas = useBajas()
  // Cada plantilla por el nombre que le da el equipo; el código de Meta si no lo tiene (DEU-10).
  const plantillas = usePlantillasWhatsApp()
  const nombrePlantilla = (codigo: string) => plantillas.data?.find((p) => p.nombre === codigo && p.titulo)?.titulo ?? codigo
  const crearBaja = useCrearBaja()
  const quitarBaja = useQuitarBaja()
  const { usuario } = useAuth()
  const reactiva = puede(usuario, 'reactivarEnvios')

  function quitarFiltros() {
    setEstado('')
    setDireccion('')
    setDesde('')
    setHasta('')
    setTexto('')
    setBusqueda('')
    setOffset(0)
  }

  return (
    <div className="con-rail">
      <section className="tarjeta">
        <div className="tarjeta-cabeza">
          <h2>Mensajes de WhatsApp</h2>
        </div>
        <div className="filtros bandeja-filtros mensajes-filtros">
          <label className="buscador">
            <Icono nombre="buscar" size={18} />
            <input
              type="search"
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              placeholder="Buscar en el mensaje o el número"
              aria-label="Buscar en el mensaje o el número"
            />
          </label>
          <select className="input bandeja-filtro" value={direccion} onChange={(e) => { setDireccion(e.target.value as FiltrosMensajes['direccion'] | ''); setOffset(0) }} aria-label="Quién escribió">
            <option value="">Todos</option>
            <option value="entrante">Los que nos escribieron</option>
            <option value="saliente">Los que enviamos</option>
          </select>
          <select className="input bandeja-filtro" value={estado} onChange={(e) => { setEstado(e.target.value); setOffset(0) }} aria-label="Estado del mensaje">
            <option value="">Cualquier estado</option>
            <option value="fallido">Fallidos</option>
            <option value="encolado">En cola</option>
            <option value="leido">Leídos</option>
            <option value="recibido">Recibidos</option>
          </select>
          <label className="campo mensajes-fecha">
            <span>Desde</span>
            <input className="input" type="date" value={desde} max={hasta || undefined} onChange={(e) => { setDesde(e.target.value); setOffset(0) }} />
          </label>
          <label className="campo mensajes-fecha">
            <span>Hasta</span>
            <input className="input" type="date" value={hasta} min={desde || undefined} onChange={(e) => { setHasta(e.target.value); setOffset(0) }} />
          </label>
          {filtrando && (
            <button className="btn btn-plano" type="button" onClick={quitarFiltros}>
              Quitar filtros
            </button>
          )}
        </div>
        <Consulta
          consulta={mensajes}
          cargando="Cargando mensajes…"
          error="No fue posible cargar los mensajes."
          vacio={filtrando ? 'Ningún mensaje coincide con la búsqueda.' : 'No hay mensajes.'}
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
                          {/* El mensaje abre la conversación entera con ese número, para ponerse en contexto. */}
                          {/* El nombre del botón es el mensaje que se ve, y después lo que hace (WCAG 2.5.3). */}
                          <button className="mensaje-abrir" type="button" onClick={() => setAbierto(m)}>
                            <span className="mensaje-contenido">{m.contenido ?? (m.plantilla ? `Plantilla «${nombrePlantilla(m.plantilla)}»` : '—')}</span>
                            <span className="sr-only">: ver la conversación con {telefono(m.destino)}</span>
                          </button>
                          <div className="bandeja-detalle">
                            {/* La dirección en palabras: una flecha sola no la lee nadie con lector de pantalla. */}
                            <span className="mensaje-direccion" data-direccion={m.direccion}>
                              <Icono nombre={m.direccion === 'entrante' ? 'entrante' : 'saliente'} size={14} />
                              {m.direccion === 'entrante' ? 'Escribió' : 'Le escribimos a'}
                            </span>
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
            <h2>Dados de baja</h2>
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
                  {reactiva && (
                    <button className="btn btn-plano" type="button" onClick={() => quitarBaja.mutate(x.destino)} aria-label={`Quitar la baja de ${telefono(x.destino)}`}>
                      Quitar
                    </button>
                  )}
                </div>
              ))
            }
          </Consulta>
        </section>
      </aside>
      <Conversacion mensaje={abierto} nombrePlantilla={nombrePlantilla} onCerrar={() => setAbierto(null)} />
    </div>
  )
}

/** La conversación entera con el número de un mensaje, en orden, abierta en ese mensaje. */
function Conversacion({
  mensaje,
  nombrePlantilla,
  onCerrar,
}: {
  mensaje: MensajeRead | null
  nombrePlantilla: (codigo: string) => string
  onCerrar: () => void
}) {
  const conversacion = useConversacion(mensaje?.destino ?? null)
  const { usuario } = useAuth()
  const lista = useRef<HTMLOListElement>(null)
  // Al abrirla, el mensaje desde el que se abrió queda a la vista.
  useEffect(() => {
    lista.current?.querySelector('[data-destacado]')?.scrollIntoView?.({ block: 'center' })
  }, [conversacion.data])
  if (!mensaje) return null
  return (
    <Modal
      abierto
      onCambio={(v) => !v && onCerrar()}
      titulo={`Conversación con ${telefono(mensaje.destino)}`}
      descripcion="Todo lo que nos escribió y le escribimos por WhatsApp, del más viejo al más nuevo."
      pie={
        mensaje.familia_id && puede(usuario, 'verFamilias') ? (
          <Link className="btn btn-suave" to={`/panel/familias/${mensaje.familia_id}`}>
            Ver la familia
          </Link>
        ) : undefined
      }
    >
      <Consulta consulta={conversacion} cargando="Cargando la conversación…" error="No fue posible cargar la conversación.">
        {(mensajes) => (
          <ol ref={lista} className="comercial-mensajes mensajes-conversacion" aria-label={`Mensajes con ${telefono(mensaje.destino)}`} tabIndex={0}>
            {mensajes.map((m) => (
              <BurbujaMensaje key={m.id} mensaje={m} nombrePlantilla={nombrePlantilla} destacado={m.id === mensaje.id} />
            ))}
          </ol>
        )}
      </Consulta>
    </Modal>
  )
}
