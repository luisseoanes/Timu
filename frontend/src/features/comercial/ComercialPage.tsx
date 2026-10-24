import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { Paginacion } from '@/components/Paginacion'
import { Pestanas } from '@/components/Pestanas'
import { useAuth } from '@/features/auth/AuthContext'
import { useEquipo } from '@/features/tareas/api'
import { mensajeError } from '@/lib/errores'
import { fecha, fechaHora, hoyISO, porcentaje } from '@/lib/formato'
import { puede } from '@/lib/permisos'
import type { InteresadoRead } from '@/types'

import {
  ETAPAS,
  ORIGENES,
  useActualizarInteresado,
  useArbol,
  useConversaciones,
  useCrearInteresado,
  useEmbudo,
  useInteresados,
  useLiberarConversacion,
  usePerderInteresado,
  usePublicarArbol,
  useReactivarInteresado,
  useResponderConversacion,
} from './api'

export function ComercialPage() {
  const { usuario } = useAuth()
  const pestanas = [
    { valor: 'embudo', titulo: 'Embudo', contenido: <EmbudoComercial /> },
    { valor: 'conversaciones', titulo: 'Conversaciones', contenido: <Conversaciones /> },
  ]
  if (puede(usuario, 'administrar')) pestanas.push({ valor: 'arbol', titulo: 'Guion del bot', contenido: <Arbol /> })
  return <Pestanas etiqueta="Secciones comerciales" pestanas={pestanas} />
}

const POR_PAGINA = 25

function EmbudoComercial() {
  const hoy = hoyISO()
  const embudo = useEmbudo(`${hoy.slice(0, 8)}01`, hoy)
  const [etapa, setEtapa] = useState('')
  const [origen, setOrigen] = useState('')
  const [q, setQ] = useState('')
  const [offset, setOffset] = useState(0)
  const [nuevo, setNuevo] = useState(false)
  const [perdiendo, setPerdiendo] = useState<InteresadoRead | null>(null)
  const interesados = useInteresados({ etapa: etapa || undefined, origen: origen || undefined, q: q || undefined, limit: POR_PAGINA, offset })
  const actualizar = useActualizarInteresado()
  const reactivar = useReactivarInteresado()
  const equipo = useEquipo('comercial')
  const errorAccion = actualizar.error ?? reactivar.error

  return (
    <div className="pila">
      <section className="tarjeta" aria-labelledby="titulo-embudo">
        <div className="tarjeta-cabeza">
          <h3 id="titulo-embudo">Embudo del mes</h3>
          {embudo.data && <span className="apagado">Conversión {porcentaje(embudo.data.conversion)}</span>}
        </div>
        <Consulta consulta={embudo} cargando="Calculando el embudo…" error="No fue posible calcular el embudo.">
          {(e) => (
            <div className="etapas">
              {[...ETAPAS, { valor: 'perdido', label: 'Perdido' } as const].map((et) => (
                <button
                  key={et.valor}
                  type="button"
                  className="etapa"
                  aria-pressed={etapa === et.valor}
                  onClick={() => {
                    setEtapa(etapa === et.valor ? '' : et.valor)
                    setOffset(0)
                  }}
                >
                  <span className="indicador-titulo">{et.label}</span>
                  <strong className="indicador-valor numero">{e.por_etapa[et.valor] ?? 0}</strong>
                </button>
              ))}
            </div>
          )}
        </Consulta>
      </section>

      <section className="tarjeta">
        <div className="tarjeta-cabeza">
          <h3>Interesados</h3>
          <button className="btn btn-primario" type="button" onClick={() => setNuevo(true)}>
            <Icono nombre="mas" size={16} /> Nuevo interesado
          </button>
        </div>
        <div className="filtros" style={{ marginBottom: 'var(--e4)' }}>
          <label className="buscador">
            <Icono nombre="buscar" size={18} />
            <input type="search" aria-label="Buscar interesados" placeholder="Nombre o celular" value={q} onChange={(e) => { setQ(e.target.value); setOffset(0) }} />
          </label>
          <select className="input" style={{ width: 'auto' }} value={origen} onChange={(e) => { setOrigen(e.target.value); setOffset(0) }} aria-label="Origen">
            <option value="">Todos los orígenes</option>
            {ORIGENES.map((o) => (
              <option key={o} value={o}>{o}</option>
            ))}
          </select>
          {etapa && (
            <button className="btn btn-plano" type="button" onClick={() => setEtapa('')}>
              Quitar filtro de etapa
            </button>
          )}
        </div>
        {errorAccion && (
          <p className="error" role="alert">
            {mensajeError(errorAccion, 'No fue posible actualizar el interesado.')}
          </p>
        )}
        <Consulta
          consulta={interesados}
          cargando="Cargando interesados…"
          error="No fue posible cargar los interesados."
          vacio="No hay interesados con estos filtros."
          estaVacio={(d) => d.items.length === 0}
        >
          {(d) => (
            <>
              <div className="scroll-x">
                <table className="tabla">
                  <thead>
                    <tr>
                      <th>Interesado</th>
                      <th>Origen</th>
                      <th>Plan sugerido</th>
                      <th>Responsable</th>
                      <th>Último contacto</th>
                      <th>Etapa</th>
                    </tr>
                  </thead>
                  <tbody>
                    {d.items.map((i) => (
                      <tr key={i.id}>
                        <td className="principal">
                          {i.familia_id ? <Link to={`/familias/${i.familia_id}`}>{i.nombre ?? i.telefono}</Link> : (i.nombre ?? 'Sin nombre')}
                          <div className="apagado numero">
                            {i.telefono ?? i.email ?? '—'}
                            {i.ciudad ? ` · ${i.ciudad}` : ''}
                          </div>
                        </td>
                        <td>{i.origen}</td>
                        <td>{i.plan_sugerido ?? '—'}</td>
                        <td>
                          <select
                            className="input"
                            value={i.responsable_id ?? ''}
                            aria-label={`Responsable de ${i.nombre ?? i.telefono}`}
                            onChange={(e) => actualizar.mutate({ id: i.id, responsable_id: e.target.value || null })}
                          >
                            <option value="">Sin asignar</option>
                            {equipo.data?.map((m) => (
                              <option key={m.id} value={m.id}>{m.nombre}</option>
                            ))}
                          </select>
                        </td>
                        <td className="numero">{i.ultimo_contacto ? fechaHora(i.ultimo_contacto) : fecha(i.created_at.slice(0, 10))}</td>
                        <td>
                          {i.etapa === 'perdido' ? (
                            <div className="acciones">
                              <Distintivo dominio="etapa" valor="perdido" />
                              <button className="btn btn-plano" type="button" onClick={() => reactivar.mutate(i.id)}>
                                Reactivar
                              </button>
                            </div>
                          ) : i.etapa === 'afiliado' ? (
                            <Distintivo dominio="etapa" valor="afiliado" />
                          ) : (
                            <div className="acciones">
                              <select
                                className="input"
                                value={i.etapa}
                                aria-label={`Etapa de ${i.nombre ?? i.telefono}`}
                                onChange={(e) => actualizar.mutate({ id: i.id, etapa: e.target.value })}
                              >
                                {ETAPAS.filter((et) => et.valor !== 'afiliado').map((et) => (
                                  <option key={et.valor} value={et.valor} disabled={et.valor === 'nuevo'}>{et.label}</option>
                                ))}
                              </select>
                              <button className="btn btn-plano" type="button" onClick={() => setPerdiendo(i)}>
                                Perdido
                              </button>
                            </div>
                          )}
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
      <NuevoInteresado abierto={nuevo} onCerrar={() => setNuevo(false)} />
      <PerdidaModal interesado={perdiendo} onCerrar={() => setPerdiendo(null)} />
    </div>
  )
}

function NuevoInteresado({ abierto, onCerrar }: { abierto: boolean; onCerrar: () => void }) {
  const crear = useCrearInteresado()
  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          crear.reset()
          onCerrar()
        }
      }}
      titulo="Nuevo interesado"
      descripcion="Con el celular basta; si ya escribió por WhatsApp, se une a su conversación."
      pie={
        <button className="btn btn-primario" type="submit" form="nuevo-interesado" disabled={crear.isPending}>
          Guardar
        </button>
      }
    >
      <form
        id="nuevo-interesado"
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const d = new FormData(e.currentTarget)
          const t = (c: string) => String(d.get(c) ?? '').trim() || undefined
          crear.mutate(
            { nombre: t('nombre'), telefono: t('telefono'), email: t('email'), ciudad: t('ciudad'), origen: String(d.get('origen')) },
            { onSuccess: onCerrar },
          )
        }}
      >
        <label className="campo">
          <span>Nombre</span>
          <input className="input" name="nombre" />
        </label>
        <label className="campo">
          <span>Celular</span>
          <input className="input" name="telefono" inputMode="tel" />
        </label>
        <label className="campo">
          <span>Correo</span>
          <input className="input" name="email" type="email" />
        </label>
        <label className="campo">
          <span>Ciudad</span>
          <input className="input" name="ciudad" />
        </label>
        <label className="campo">
          <span>Origen</span>
          <select className="input" name="origen" defaultValue="panel">
            {ORIGENES.map((o) => (
              <option key={o} value={o}>{o}</option>
            ))}
          </select>
        </label>
        {crear.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(crear.error, 'No fue posible guardar el interesado.')}
          </p>
        )}
      </form>
    </Modal>
  )
}

function PerdidaModal({ interesado, onCerrar }: { interesado: InteresadoRead | null; onCerrar: () => void }) {
  const perder = usePerderInteresado()
  return (
    <Modal
      abierto={interesado !== null}
      onCambio={(v) => {
        if (!v) {
          perder.reset()
          onCerrar()
        }
      }}
      titulo="Marcar como perdido"
      descripcion={interesado?.nombre ?? interesado?.telefono ?? undefined}
      pie={
        <button className="btn btn-primario" type="submit" form="perdida" disabled={perder.isPending}>
          Marcar perdido
        </button>
      }
    >
      <form
        id="perdida"
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const motivo = String(new FormData(e.currentTarget).get('motivo')).trim()
          if (interesado) perder.mutate({ id: interesado.id, motivo }, { onSuccess: onCerrar })
        }}
      >
        <label className="campo ancho">
          <span>Motivo</span>
          <select className="input" name="motivo" defaultValue="Precio">
            {['Precio', 'Sin cobertura en su zona', 'Eligió otra opción', 'No responde', 'Otro'].map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </label>
        {perder.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(perder.error, 'No fue posible actualizar.')}
          </p>
        )}
      </form>
    </Modal>
  )
}

function Conversaciones() {
  const { usuario } = useAuth()
  const [estado, setEstado] = useState('asesor')
  const conversaciones = useConversaciones(estado || undefined)
  const responder = useResponderConversacion()
  const liberar = useLiberarConversacion()
  const [abierta, setAbierta] = useState<string | null>(null)
  const [texto, setTexto] = useState('')

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Conversaciones de WhatsApp</h3>
        <select className="input" style={{ width: 'auto' }} value={estado} onChange={(e) => setEstado(e.target.value)} aria-label="Estado de la conversación">
          <option value="asesor">Esperan a un asesor</option>
          <option value="automatica">Atiende el bot</option>
          <option value="">Todas</option>
        </select>
      </div>
      <Consulta
        consulta={conversaciones}
        cargando="Cargando conversaciones…"
        error="No fue posible cargar las conversaciones."
        vacio="No hay conversaciones en este estado."
        estaVacio={(d) => d.length === 0}
      >
        {(d) =>
          d.map((c) => (
            <div key={c.id} className="pila" style={{ gap: 'var(--e2)', paddingBlock: 'var(--e3)', borderBottom: '1px solid var(--linea)' }}>
              <div className="acciones">
                <strong className="numero">{c.telefono}</strong>
                <span className={`distintivo distintivo-${c.estado === 'asesor' ? 'alerta' : 'info'}`}>
                  {c.estado === 'asesor' ? 'Espera asesor' : c.estado === 'automatica' ? 'Bot' : c.estado}
                </span>
                <span className="apagado">
                  Paso «{c.nodo}» · {fechaHora(c.updated_at)}
                </span>
                <div className="acciones" style={{ marginLeft: 'auto' }}>
                  <button className="btn btn-suave" type="button" onClick={() => { setAbierta(abierta === c.id ? null : c.id); setTexto('') }}>
                    Responder
                  </button>
                  {c.estado === 'asesor' && (
                    <button className="btn btn-plano" type="button" disabled={liberar.isPending} onClick={() => liberar.mutate(c.id)}>
                      Devolver al bot
                    </button>
                  )}
                </div>
              </div>
              {Object.keys(c.datos).length > 0 && (
                <p className="apagado">
                  {Object.entries(c.datos)
                    .map(([k, v]) => `${k}: ${String(v)}`)
                    .join(' · ')}
                </p>
              )}
              {abierta === c.id && (
                <form
                  className="acciones"
                  onSubmit={(e) => {
                    e.preventDefault()
                    responder.mutate({ id: c.id, texto: texto.trim() }, { onSuccess: () => { setTexto(''); setAbierta(null) } })
                  }}
                >
                  <input
                    className="input"
                    style={{ flex: 1 }}
                    aria-label={`Mensaje para ${c.telefono}`}
                    placeholder={`Escribe como ${usuario?.nombre ?? 'asesor'}…`}
                    value={texto}
                    onChange={(e) => setTexto(e.target.value)}
                    required
                  />
                  <button className="btn btn-primario" type="submit" disabled={responder.isPending}>
                    <Icono nombre="mensaje" size={16} /> Enviar
                  </button>
                </form>
              )}
            </div>
          ))
        }
      </Consulta>
      {(responder.isError || liberar.isError) && (
        <p className="error" role="alert">
          {mensajeError(responder.error ?? liberar.error, 'No fue posible completar la acción.')}
        </p>
      )}
    </section>
  )
}

function Arbol() {
  const arbol = useArbol(true)
  const publicar = usePublicarArbol()
  const [texto, setTexto] = useState<string | null>(null)
  const [nota, setNota] = useState('')
  const [errorJson, setErrorJson] = useState<string | null>(null)

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Guion del bot comercial</h3>
      </div>
      <p className="apagado" style={{ marginBottom: 'var(--e4)' }}>
        Cada nodo tiene su mensaje y sus opciones. Al publicar se valida el árbol completo y la versión anterior queda guardada.
      </p>
      <Consulta consulta={arbol} cargando="Cargando el guion…" error="No fue posible cargar el guion.">
        {(nodos) => (
          <form
            className="pila"
            onSubmit={(e) => {
              e.preventDefault()
              setErrorJson(null)
              try {
                const parseado = JSON.parse(texto ?? JSON.stringify(nodos)) as Record<string, unknown>
                publicar.mutate({ nodos: parseado, nota: nota.trim() || undefined })
              } catch {
                setErrorJson('El guion no es un JSON válido.')
              }
            }}
          >
            <label className="campo">
              <span>Nodos (JSON)</span>
              <textarea
                className="input codigo"
                rows={18}
                spellCheck={false}
                value={texto ?? JSON.stringify(nodos, null, 2)}
                onChange={(e) => setTexto(e.target.value)}
              />
            </label>
            <label className="campo">
              <span>Nota de la versión</span>
              <input className="input" value={nota} onChange={(e) => setNota(e.target.value)} />
            </label>
            {(errorJson || publicar.isError) && (
              <p className="error" role="alert">
                {errorJson ?? mensajeError(publicar.error, 'El guion no es válido.')}
              </p>
            )}
            {publicar.isSuccess && (
              <p className="exito" role="status">
                Versión publicada.
              </p>
            )}
            <div className="acciones">
              <button className="btn btn-primario" type="submit" disabled={publicar.isPending}>
                Publicar versión
              </button>
            </div>
          </form>
        )}
      </Consulta>
    </section>
  )
}
