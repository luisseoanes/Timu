import * as Menu from '@radix-ui/react-dropdown-menu'
import { useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo, Insignia } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { useEquipo } from '@/features/auth'
import { mensajeError } from '@/lib/errores'
import { diaISO, fechaCompacta, fechaHora, hora, telefono } from '@/lib/formato'
import type { ConversacionDelInteresado, InteresadoRead, MensajeRead } from '@/types'

import {
  ETAPAS,
  useActualizarInteresado,
  useConversacionDelInteresado,
  useInteresado,
  useLiberarConversacion,
  usePerderInteresado,
  useReactivarInteresado,
  useResponderConversacion,
} from './api'
import { mascotasDe, mensajesWebDe, nombreDe, nombreEtapa, nombreOrigen } from './interesado'

/** El interesado abierto: dónde va en el embudo, qué toca y su conversación de WhatsApp. */
export function FichaInteresado({ id }: { id: string }) {
  const interesado = useInteresado(id)
  const conversacion = useConversacionDelInteresado(id)
  return (
    <section className="ficha-abierta" aria-label="Interesado abierto">
      <Consulta consulta={interesado} cargando="Cargando el interesado…" error="No fue posible cargar el interesado.">
        {(i) => <Ficha interesado={i} conversacion={conversacion.data} conversacionCargando={conversacion.isPending} conversacionError={conversacion.isError} />}
      </Consulta>
    </section>
  )
}

function Ficha({
  interesado: i,
  conversacion,
  conversacionCargando,
  conversacionError,
}: {
  interesado: InteresadoRead
  conversacion: ConversacionDelInteresado | undefined
  conversacionCargando: boolean
  conversacionError: boolean
}) {
  const [params] = useSearchParams()
  const [perdiendo, setPerdiendo] = useState(false)
  const actualizar = useActualizarInteresado()
  const reactivar = useReactivarInteresado()
  const equipo = useEquipo('comercial')
  // Si alguien espera a un asesor en WhatsApp, contestarle es lo que toca: el verde es «Enviar».
  const esperaAsesor = conversacion?.conversacion?.estado === 'con_asesor'
  const errorAccion = actualizar.error ?? reactivar.error
  const volver = new URLSearchParams(params)
  volver.delete('interesado')
  const mascotas = mascotasDe(i.datos)

  return (
    <>
      <header className="ficha-cabeza">
        <Link to={`?${volver}`} className="btn btn-plano ficha-volver" aria-label="Volver a los interesados">
          <Icono nombre="volver" size={16} />
        </Link>
        <h2 className="comercial-titulo">{nombreDe(i)}</h2>
        <div className="ficha-datos comercial-quien">
          <Distintivo dominio="etapa" valor={i.etapa} />
          {i.nombre && i.telefono && <span className="numero">{telefono(i.telefono)}</span>}
          {i.email && <span>{i.email}</span>}
          {i.ciudad && <span>{i.ciudad}</span>}
        </div>
        <div className="ficha-acciones">
          {i.siguiente_etapa && (
            <button
              className={`btn ${esperaAsesor ? 'btn-suave' : 'btn-primario'}`}
              type="button"
              disabled={actualizar.isPending}
              onClick={() => actualizar.mutate({ id: i.id, etapa: i.siguiente_etapa! })}
            >
              Pasar a {nombreEtapa(i.siguiente_etapa).toLowerCase()}
            </button>
          )}
          {i.etapa === 'perdido' && (
            <button className="btn btn-primario" type="button" disabled={reactivar.isPending} onClick={() => reactivar.mutate(i.id)}>
              Reactivar
            </button>
          )}
          {i.etapa !== 'perdido' && i.etapa !== 'afiliado' && (
            <Menu.Root modal={false}>
              <Menu.Trigger className="btn btn-secundario btn-icono" aria-label={`Más acciones con ${nombreDe(i)}`}>
                <Icono nombre="puntos" size={18} />
              </Menu.Trigger>
              <Menu.Portal>
                <Menu.Content className="menu" align="start" sideOffset={6}>
                  <Menu.Item className="menu-item menu-item-peligro" onSelect={() => setPerdiendo(true)}>
                    Marcar como perdido
                  </Menu.Item>
                </Menu.Content>
              </Menu.Portal>
            </Menu.Root>
          )}
        </div>
        {i.etapa === 'en_afiliacion' && (
          <p className="comercial-nota">Se afilia desde Familias: al completar la afiliación pasa a «Afiliado».</p>
        )}
        {errorAccion && (
          <p className="error" role="alert">
            {mensajeError(errorAccion, 'No fue posible actualizar el interesado.')}
          </p>
        )}
      </header>

      <LineaEtapas etapa={i.etapa} />
      {i.etapa === 'perdido' && i.motivo_perdida && <p className="comercial-nota">Perdido: {i.motivo_perdida}.</p>}

      <dl className="ficha comercial-ficha">
        <div>
          <dt>Responsable</dt>
          <dd>
            <select
              className="input"
              value={i.responsable_id ?? ''}
              aria-label="Responsable"
              onChange={(e) => actualizar.mutate({ id: i.id, responsable_id: e.target.value || null })}
            >
              <option value="">Sin asignar</option>
              {equipo.data?.map((m) => (
                <option key={m.id} value={m.id}>{m.nombre}</option>
              ))}
            </select>
          </dd>
        </div>
        <div>
          <dt>Cómo llegó</dt>
          <dd>{nombreOrigen(i.origen)}</dd>
        </div>
        <div>
          <dt>Plan sugerido</dt>
          <dd>{i.plan_sugerido ?? 'Todavía no'}</dd>
        </div>
        {mascotas && (
          <div>
            <dt>Mascotas</dt>
            <dd>{mascotas}</dd>
          </div>
        )}
        <div>
          <dt>Primer contacto</dt>
          <dd className="numero">{fechaCompacta(diaISO(i.created_at))}</dd>
        </div>
        {i.familia_id && (
          <div>
            <dt>Familia</dt>
            <dd>
              <Link to={`/panel/familias/${i.familia_id}`}>Abrir su ficha</Link>
            </dd>
          </div>
        )}
      </dl>

      <MensajesWeb interesado={i} />
      <Conversacion interesado={i} conversacion={conversacion} cargando={conversacionCargando} error={conversacionError} esperaAsesor={esperaAsesor} />
      <PerdidaModal interesado={perdiendo ? i : null} onCerrar={() => setPerdiendo(false)} />
    </>
  )
}

/** Lo que escribió en el formulario de contacto de la portada (R3-PUB-04): se responde por
 * WhatsApp o al correo, y la tarea «Responder el mensaje de la web» lo recuerda. */
function MensajesWeb({ interesado: i }: { interesado: InteresadoRead }) {
  const mensajes = mensajesWebDe(i.datos)
  if (mensajes.length === 0) return null
  return (
    <section className="bloque" aria-labelledby="mensajes-web-titulo">
      <h3 id="mensajes-web-titulo">Lo que escribió en la página web</h3>
      <ol className="comercial-mensajes-web" aria-label={`Mensajes de la web de ${nombreDe(i)}`}>
        {mensajes.map((m) => (
          <li key={m.fecha}>
            <span className="apagado numero">
              {fechaHora(m.fecha)}
              {m.mascota && ` · ${m.mascota}${m.especie ? `, ${m.especie === 'canino' ? 'perro' : 'gato'}` : ''}`}
            </span>
            <p>{m.mensaje}</p>
          </li>
        ))}
      </ol>
    </section>
  )
}

/** Las etapas del embudo como una línea: lo recorrido lleno, la actual con su halo. */
function LineaEtapas({ etapa }: { etapa: string }) {
  const actual = ETAPAS.findIndex((e) => e.valor === etapa)
  return (
    <ol className="comercial-etapas" aria-label="Etapas del embudo" style={{ ['--avance' as string]: Math.max(actual, 0) / (ETAPAS.length - 1) }}>
      {ETAPAS.map((e, n) => {
        const estado = actual < 0 ? 'pendiente' : n < actual ? 'hecha' : n === actual ? 'actual' : 'pendiente'
        return (
          <li key={e.valor} data-estado={estado} aria-current={estado === 'actual' ? 'step' : undefined}>
            <span className="consulta-estacion" aria-hidden="true" />
            <span className="consulta-estacion-nombre">{e.label}</span>
          </li>
        )
      })}
    </ol>
  )
}

function Conversacion({
  interesado: i,
  conversacion,
  cargando,
  error,
  esperaAsesor,
}: {
  interesado: InteresadoRead
  conversacion: ConversacionDelInteresado | undefined
  cargando: boolean
  error: boolean
  esperaAsesor: boolean
}) {
  const [texto, setTexto] = useState('')
  const lista = useRef<HTMLOListElement>(null)
  const responder = useResponderConversacion()
  const ultimo = conversacion?.mensajes.at(-1)?.id
  // Hay mensajes anteriores fuera de la vista: el borde de arriba se desvanece.
  const [hayAnteriores, setHayAnteriores] = useState(false)
  // Como en un chat, la conversación abre en lo último que se dijo.
  useEffect(() => {
    const l = lista.current
    if (!l) return
    l.scrollTop = l.scrollHeight
    setHayAnteriores(l.scrollTop > 1)
  }, [ultimo])
  const liberar = useLiberarConversacion()
  const conv = conversacion?.conversacion

  return (
    <section className="bloque comercial-conversacion" aria-labelledby="conversacion-titulo">
      <div className="comercial-conversacion-cabeza">
        <h3 id="conversacion-titulo">Conversación de WhatsApp</h3>
        {conv &&
          (esperaAsesor ? (
            <Insignia tono="alerta" icono="mensaje">Espera a un asesor</Insignia>
          ) : (
            <Insignia tono="info">Atiende el asistente</Insignia>
          ))}
      </div>
      {!i.telefono ? (
        <p className="apagado">Sin celular: no hay conversación de WhatsApp.</p>
      ) : cargando ? (
        <p className="apagado" role="status">Cargando la conversación…</p>
      ) : error ? (
        <p className="error" role="alert">No fue posible cargar la conversación.</p>
      ) : !conversacion || conversacion.mensajes.length === 0 ? (
        // Quien escribe al WhatsApp de TIMU llega con su conversación: «WhatsApp» sin mensajes es
        // que alguien lo registró a mano (escribió a otro número, por ejemplo).
        <p className="apagado">
          {i.origen === 'whatsapp'
            ? 'No hay mensajes suyos en el WhatsApp de TIMU: se registró a mano.'
            : 'Todavía no ha escrito por WhatsApp.'}
        </p>
      ) : (
        <ol
          ref={lista}
          className="comercial-mensajes"
          aria-label={`Mensajes con ${nombreDe(i)}`}
          tabIndex={0}
          data-anteriores={hayAnteriores || undefined}
          onScroll={(e) => setHayAnteriores(e.currentTarget.scrollTop > 1)}
        >
          {conversacion.mensajes.map((m) => (
            <Mensaje key={m.id} mensaje={m} />
          ))}
        </ol>
      )}
      {conv && (
        <form
          className="comercial-responder"
          onSubmit={(e) => {
            e.preventDefault()
            responder.mutate({ id: conv.id, texto: texto.trim() }, { onSuccess: () => setTexto('') })
          }}
        >
          <label className="campo">
            <span>Responder por WhatsApp</span>
            <textarea className="input" rows={2} value={texto} onChange={(e) => setTexto(e.target.value)} required maxLength={4000} />
          </label>
          <div className="acciones">
            {esperaAsesor && (
              <button className="btn btn-plano" type="button" disabled={liberar.isPending} onClick={() => liberar.mutate(conv.id)}>
                Devolver al asistente
              </button>
            )}
            <button className={`btn ${esperaAsesor ? 'btn-primario' : 'btn-secundario'}`} type="submit" disabled={responder.isPending}>
              <Icono nombre="mensaje" size={16} /> {responder.isPending ? 'Enviando…' : 'Enviar'}
            </button>
          </div>
          {(responder.isError || liberar.isError) && (
            <p className="error" role="alert">
              {mensajeError(responder.error ?? liberar.error, 'No fue posible completar la acción.')}
            </p>
          )}
        </form>
      )}
    </section>
  )
}

function Mensaje({ mensaje: m }: { mensaje: MensajeRead }) {
  const entrante = m.direccion === 'entrante'
  return (
    <li className="comercial-mensaje" data-direccion={m.direccion}>
      <span className="sr-only">{entrante ? 'Escribió:' : 'Respondimos:'}</span>
      <p>{m.contenido ?? (m.plantilla ? `Plantilla «${m.plantilla}»` : '—')}</p>
      <span className="comercial-mensaje-hora numero" title={fechaHora(m.created_at)}>
        {fechaCompacta(diaISO(m.created_at))} · {hora(m.created_at)}
        {m.estado === 'fallido' && ' · no se envió'}
      </span>
    </li>
  )
}

const MOTIVOS = ['Precio', 'Sin cobertura en su zona', 'Eligió otra opción', 'No responde', 'Otro']

function PerdidaModal({ interesado, onCerrar }: { interesado: InteresadoRead | null; onCerrar: () => void }) {
  const perder = usePerderInteresado()
  function cerrar() {
    perder.reset()
    onCerrar()
  }
  if (!interesado) return null
  return (
    <Modal
      abierto
      onCambio={(v) => !v && cerrar()}
      titulo={`Marcar a ${nombreDe(interesado)} como perdido`}
      descripcion="Sale del embudo abierto. Se puede reactivar desde «Perdidos»."
      pie={
        <button className="btn btn-peligro" type="submit" form="perdida" disabled={perder.isPending}>
          {perder.isPending ? 'Guardando…' : 'Marcar como perdido'}
        </button>
      }
    >
      <form
        id="perdida"
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const motivo = String(new FormData(e.currentTarget).get('motivo')).trim()
          perder.mutate({ id: interesado.id, motivo }, { onSuccess: cerrar })
        }}
      >
        <label className="campo ancho">
          <span>Motivo</span>
          <select className="input" name="motivo" defaultValue="Precio">
            {MOTIVOS.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </label>
        {perder.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(perder.error, 'No fue posible guardar.')}
          </p>
        )}
      </form>
    </Modal>
  )
}
