import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo, Insignia } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { useAuth } from '@/features/auth'
import { SelectorFamilia, useMascotas } from '@/features/familias'
import { mensajeError } from '@/lib/errores'
import { fechaHora } from '@/lib/formato'
import { puede } from '@/lib/permisos'
import type { FamiliaRead, SolicitudVirtualRead } from '@/types'

import {
  useCerrarSolicitud,
  useColaVirtual,
  useCrearSolicitudVirtual,
  usePedirBorrador,
  useRespuestas,
  useResponderSolicitud,
  useTomarSolicitud,
  type BorradorIA,
} from './api'

export function AtencionVirtual() {
  const { usuario } = useAuth()
  const cola = useColaVirtual()
  const mascotas = useMascotas(cola.data?.map((s) => s.mascota_id) ?? [])
  const [abierta, setAbierta] = useState<SolicitudVirtualRead | null>(null)
  const [nueva, setNueva] = useState(false)
  const tomar = useTomarSolicitud()
  const esMedico = puede(usuario, 'medico')

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h2>Cola de orientación virtual</h2>
        <button className="btn btn-suave" type="button" onClick={() => setNueva(true)}>
          <Icono nombre="mas" size={16} /> Registrar solicitud
        </button>
      </div>
      {tomar.isError && (
        <p className="error" role="alert">
          {mensajeError(tomar.error, 'No fue posible tomar la solicitud.')}
        </p>
      )}
      <Consulta
        consulta={cola}
        cargando="Cargando la cola…"
        error="No fue posible cargar la cola."
        vacio="No hay solicitudes en espera."
        estaVacio={(d) => d.length === 0}
      >
        {(d) => (
          <div className="scroll-x">
            <table className="tabla tabla-apilable">
              <thead>
                <tr>
                  <th>Mascota</th>
                  <th>Llegó</th>
                  <th>Motivo</th>
                  <th>Prioridad</th>
                  <th>Estado</th>
                  <th><span className="sr-only">Acciones</span></th>
                </tr>
              </thead>
              <tbody>
                {d.map((s) => {
                  const mia = s.asignada_a_id === usuario?.id
                  return (
                    <tr key={s.id}>
                      <td className="principal" data-etiqueta="Mascota">{mascotas.get(s.mascota_id)?.nombre ?? '…'}</td>
                      <td className="numero" data-etiqueta="Llegó">{fechaHora(s.created_at)}</td>
                      <td data-etiqueta="Motivo">{s.motivo}</td>
                      <td data-etiqueta="Prioridad">
                        <Distintivo dominio="prioridad" valor={s.prioridad} />
                      </td>
                      <td data-etiqueta="Estado">
                        <span className="acciones">
                          <Distintivo dominio="virtual" valor={s.estado} />
                          {s.borrador_ia && <Insignia tono="info">Borrador IA</Insignia>}
                        </span>
                      </td>
                      <td className="tabla-acciones">
                        {esMedico && !s.asignada_a_id && (
                          <button className="btn btn-suave" type="button" disabled={tomar.isPending} onClick={() => tomar.mutate(s.id)}>
                            Tomar
                          </button>
                        )}
                        {/* Una por fila: ninguna es verde llena, la cola no tiene una acción principal. */}
                        {mia && (
                          <button className="btn btn-suave" type="button" onClick={() => setAbierta(s)}>
                            Atender
                          </button>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </Consulta>
      {abierta && (
        <AtenderSolicitud
          solicitud={cola.data?.find((s) => s.id === abierta.id) ?? abierta}
          nombreMascota={mascotas.get(abierta.mascota_id)?.nombre}
          onCerrar={() => setAbierta(null)}
        />
      )}
      <NuevaSolicitud abierto={nueva} onCerrar={() => setNueva(false)} />
    </section>
  )
}

function AtenderSolicitud({
  solicitud: s,
  nombreMascota,
  onCerrar,
}: {
  solicitud: SolicitudVirtualRead
  nombreMascota?: string
  onCerrar: () => void
}) {
  const { usuario } = useAuth()
  const respuestas = useRespuestas('aprobada')
  const borrador = usePedirBorrador()
  const responder = useResponderSolicitud()
  const cerrar = useCerrarSolicitud()
  const [codigo, setCodigo] = useState('')
  const [variables, setVariables] = useState<string[]>([])
  const [diagnostico, setDiagnostico] = useState('')
  const plantilla = respuestas.data?.find((r) => r.codigo === codigo)
  const ia = s.borrador_ia as BorradorIA | null | undefined
  const esMedico = puede(usuario, 'medico') && s.asignada_a_id === usuario?.id
  const vistaPrevia = plantilla
    ? // Las variables son posicionales: {{1}}, {{2}}… (clinica/service.py: render).
      plantilla.cuerpo.replace(/\{\{(\d+)\}\}/g, (_, n: string) => {
        const i = Number(n) - 1
        return variables[i] || `[${plantilla.variables[i] ?? n}]`
      })
    : ''

  return (
    <Modal abierto onCambio={(v) => !v && onCerrar()} titulo={`Orientación virtual · ${nombreMascota ?? ''}`} descripcion={s.motivo}>
      <div className="pila">
        {s.respuesta ? (
          <div className="aviso-ok" role="status">
            Respondida: {s.respuesta}
          </div>
        ) : (
          <>
            <section className="borrador-ia" aria-label="Borrador de la IA">
              <div className="acciones">
                <Icono nombre="ia" size={18} />
                <strong>Borrador sugerido</strong>
                <span className="apagado">Lo revisas tú; nunca se envía solo.</span>
              </div>
              {ia ? (
                <>
                  <p style={{ whiteSpace: 'pre-wrap' }}>{ia.borrador}</p>
                  {ia.senales_alarma.length > 0 && (
                    <p className="aviso-error">Señales de alarma: {ia.senales_alarma.join(', ')}</p>
                  )}
                  {ia.recomendar_presencial && <p className="aviso">La IA sugiere una valoración presencial.</p>}
                </>
              ) : borrador.isSuccess ? (
                <p className="apagado">Pedido. Llega en unos segundos; la cola se actualiza sola.</p>
              ) : (
                esMedico && (
                  <button className="btn btn-suave" type="button" disabled={borrador.isPending} onClick={() => borrador.mutate(s.id)}>
                    Pedir borrador a la IA
                  </button>
                )
              )}
              {borrador.isError && (
                <p className="error" role="alert">
                  {mensajeError(borrador.error, 'No fue posible pedir el borrador.')}
                </p>
              )}
            </section>

            {esMedico && (
              <form
                className="formulario"
                onSubmit={(e) => {
                  e.preventDefault()
                  responder.mutate(
                    { id: s.id, respuesta_codigo: codigo, variables, diagnostico: diagnostico.trim() || undefined },
                    { onSuccess: onCerrar },
                  )
                }}
              >
                <label className="campo ancho">
                  <span>Respuesta aprobada</span>
                  <select
                    className="input"
                    value={codigo}
                    onChange={(e) => {
                      setCodigo(e.target.value)
                      setVariables([])
                    }}
                    required
                  >
                    <option value="" disabled>Elige la respuesta</option>
                    {respuestas.data?.map((r) => (
                      <option key={r.codigo} value={r.codigo}>{r.titulo}</option>
                    ))}
                  </select>
                </label>
                {plantilla?.variables.map((v, i) => (
                  <label key={v} className="campo">
                    <span>{v.replace(/_/g, ' ')}</span>
                    <input
                      className="input"
                      required
                      value={variables[i] ?? ''}
                      onChange={(e) => setVariables((a) => plantilla.variables.map((_, j) => (j === i ? e.target.value : (a[j] ?? ''))))}
                    />
                  </label>
                ))}
                {plantilla && <p className="aviso ancho">{vistaPrevia}</p>}
                <label className="campo ancho">
                  <span>Diagnóstico para la historia (opcional)</span>
                  <input className="input" value={diagnostico} onChange={(e) => setDiagnostico(e.target.value)} />
                </label>
                {responder.isError && (
                  <p className="error ancho" role="alert">
                    {mensajeError(responder.error, 'No fue posible responder.')}
                  </p>
                )}
                <div className="acciones ancho">
                  <button className="btn btn-primario" type="submit" disabled={!codigo || responder.isPending}>
                    Enviar respuesta
                  </button>
                </div>
              </form>
            )}
          </>
        )}
        <div className="acciones">
          <button className="btn btn-plano" type="button" disabled={cerrar.isPending} onClick={() => cerrar.mutate(s.id, { onSuccess: onCerrar })}>
            Cerrar solicitud
          </button>
          {s.historia_id && <Link to={`/panel/clinica/historias/${s.historia_id}`}>Ver en la historia</Link>}
        </div>
        {cerrar.isError && (
          <p className="error" role="alert">
            {mensajeError(cerrar.error, 'No fue posible cerrar.')}
          </p>
        )}
      </div>
    </Modal>
  )
}

function NuevaSolicitud({ abierto, onCerrar }: { abierto: boolean; onCerrar: () => void }) {
  const crear = useCrearSolicitudVirtual()
  const [familia, setFamilia] = useState<FamiliaRead | null>(null)

  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          crear.reset()
          setFamilia(null)
          onCerrar()
        }
      }}
      titulo="Registrar solicitud de orientación"
      descripcion="Para consultas que llegan por teléfono o en persona."
      pie={
        <button className="btn btn-primario" type="submit" form="nueva-solicitud" disabled={!familia || crear.isPending}>
          Registrar
        </button>
      }
    >
      <form
        id="nueva-solicitud"
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const d = new FormData(e.currentTarget)
          crear.mutate(
            {
              mascota_id: String(d.get('mascota_id')),
              motivo: String(d.get('motivo')).trim(),
              prioridad: String(d.get('prioridad')),
              canal: 'panel',
            },
            { onSuccess: onCerrar },
          )
        }}
      >
        <div className="ancho">
          <SelectorFamilia valor={familia} onCambio={setFamilia} />
        </div>
        <label className="campo">
          <span>Mascota</span>
          <select className="input" name="mascota_id" required disabled={!familia}>
            {(familia?.mascotas ?? [])
              .filter((m) => m.activa)
              .map((m) => (
                <option key={m.id} value={m.id}>{m.nombre}</option>
              ))}
          </select>
        </label>
        <label className="campo">
          <span>Prioridad</span>
          <select className="input" name="prioridad" defaultValue="media">
            <option value="alta">Alta</option>
            <option value="media">Media</option>
            <option value="baja">Baja</option>
          </select>
        </label>
        <label className="campo ancho">
          <span>Motivo de la consulta</span>
          <textarea className="input" name="motivo" rows={3} required minLength={5} />
        </label>
        {crear.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(crear.error, 'No fue posible registrar la solicitud.')}
          </p>
        )}
      </form>
    </Modal>
  )
}
