import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { Pestanas } from '@/components/Pestanas'
import { useAuth } from '@/features/auth/AuthContext'
import { SelectorFamilia } from '@/features/familias/SelectorFamilia'
import { useMascotas } from '@/features/preventivos/api'
import { mensajeError } from '@/lib/errores'
import { fechaHora } from '@/lib/formato'
import { puede } from '@/lib/permisos'
import type { FamiliaRead, RespuestaRead, SolicitudVirtualRead } from '@/types'

import {
  useAprobarRespuesta,
  useCerrarSolicitud,
  useColaVirtual,
  useCrearPlantilla,
  useCrearRespuesta,
  useCrearSolicitudVirtual,
  usePedirBorrador,
  usePlantillas,
  useRespuestas,
  useResponderSolicitud,
  useTomarSolicitud,
  CAMPOS_CLINICOS,
  type BorradorIA,
} from './api'

export function ClinicaPage() {
  const { usuario } = useAuth()
  const pestanas = [{ valor: 'historia', titulo: 'Historia clínica', contenido: <BuscarHistoria /> }]
  if (puede(usuario, 'clinico')) {
    pestanas.push(
      { valor: 'virtual', titulo: 'Atención virtual', contenido: <AtencionVirtual /> },
      { valor: 'respuestas', titulo: 'Respuestas aprobadas', contenido: <Respuestas /> },
      { valor: 'plantillas', titulo: 'Plantillas de consulta', contenido: <Plantillas /> },
    )
  }
  return <Pestanas etiqueta="Secciones de clínica" pestanas={pestanas} />
}

function BuscarHistoria() {
  const [familia, setFamilia] = useState<FamiliaRead | null>(null)
  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Abrir una historia clínica</h3>
      </div>
      <SelectorFamilia valor={familia} onCambio={setFamilia} etiqueta="Familia de la mascota" />
      {familia && (
        <div className="mascotas" style={{ marginTop: 'var(--e4)' }}>
          {(familia.mascotas ?? []).map((m) => (
            <Link key={m.id} to={`/clinica/mascotas/${m.id}`} className="acceso">
              <Icono nombre="huella" />
              {m.nombre}
              <span className="apagado">{m.activa ? m.especie : 'De baja'}</span>
            </Link>
          ))}
        </div>
      )}
    </section>
  )
}

function AtencionVirtual() {
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
        <h3>Cola de orientación virtual</h3>
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
            <table className="tabla">
              <thead>
                <tr>
                  <th>Llegó</th>
                  <th>Mascota</th>
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
                      <td className="numero">{fechaHora(s.created_at)}</td>
                      <td className="principal">{mascotas.get(s.mascota_id)?.nombre ?? '…'}</td>
                      <td>{s.motivo}</td>
                      <td>
                        <Distintivo dominio="prioridad" valor={s.prioridad} />
                      </td>
                      <td>
                        <Distintivo dominio="virtual" valor={s.estado} />
                        {s.borrador_ia && <span className="distintivo distintivo-info">Borrador IA</span>}
                      </td>
                      <td>
                        {esMedico && !s.asignada_a_id && (
                          <button className="btn btn-suave" type="button" disabled={tomar.isPending} onClick={() => tomar.mutate(s.id)}>
                            Tomar
                          </button>
                        )}
                        {(mia || puede(usuario, 'administrar')) && (
                          <button className="btn btn-primario" type="button" onClick={() => setAbierta(s)}>
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
          {s.historia_id && <Link to={`/clinica/historias/${s.historia_id}`}>Ver en la historia</Link>}
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

function Respuestas() {
  const { usuario } = useAuth()
  const respuestas = useRespuestas()
  const aprobar = useAprobarRespuesta()
  const [nueva, setNueva] = useState(false)

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Respuestas aprobadas</h3>
        <button className="btn btn-suave" type="button" onClick={() => setNueva(true)}>
          <Icono nombre="mas" size={16} /> Nueva respuesta
        </button>
      </div>
      <p className="apagado" style={{ marginBottom: 'var(--e4)' }}>
        La orientación virtual sólo sale de estas respuestas. Las variables van numeradas en el texto: {'{{1}}'}, {'{{2}}'}…
      </p>
      {aprobar.isError && (
        <p className="error" role="alert">
          {mensajeError(aprobar.error, 'No fue posible aprobar.')}
        </p>
      )}
      <Consulta
        consulta={respuestas}
        cargando="Cargando respuestas…"
        error="No fue posible cargar las respuestas."
        vacio="Aún no hay respuestas. Crea la primera."
        estaVacio={(d) => d.length === 0}
      >
        {(d) =>
          d.map((r: RespuestaRead) => (
            <div key={r.codigo} className="fila">
              <div className="fila-cuerpo">
                <strong>{r.titulo}</strong>
                <span>{r.cuerpo}</span>
              </div>
              <span className={`distintivo distintivo-${r.estado === 'aprobada' ? 'ok' : 'alerta'}`}>
                {r.estado === 'aprobada' ? 'Aprobada' : 'Por aprobar'}
              </span>
              {r.estado !== 'aprobada' && puede(usuario, 'administrar') && (
                <button className="btn btn-plano" type="button" onClick={() => aprobar.mutate(r.codigo)}>
                  Aprobar
                </button>
              )}
            </div>
          ))
        }
      </Consulta>
      <NuevaRespuesta abierto={nueva} onCerrar={() => setNueva(false)} />
    </section>
  )
}

function NuevaRespuesta({ abierto, onCerrar }: { abierto: boolean; onCerrar: () => void }) {
  const crear = useCrearRespuesta()
  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          crear.reset()
          onCerrar()
        }
      }}
      titulo="Nueva respuesta"
      descripcion="Queda por aprobar hasta que la administración la revise."
      pie={
        <button className="btn btn-primario" type="submit" form="nueva-respuesta" disabled={crear.isPending}>
          Guardar
        </button>
      }
    >
      <form
        id="nueva-respuesta"
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const d = new FormData(e.currentTarget)
          const cuerpo = String(d.get('cuerpo')).trim()
          const variables = String(d.get('variables') ?? '')
            .split(',')
            .map((v) => v.trim())
            .filter(Boolean)
          crear.mutate(
            { codigo: String(d.get('codigo')).trim(), titulo: String(d.get('titulo')).trim(), cuerpo, variables },
            { onSuccess: onCerrar },
          )
        }}
      >
        <label className="campo">
          <span>Código</span>
          <input className="input" name="codigo" required pattern="[a-z0-9_]+" title="minúsculas, números y guion bajo" />
        </label>
        <label className="campo">
          <span>Título</span>
          <input className="input" name="titulo" required />
        </label>
        <label className="campo ancho">
          <span>Texto (variables numeradas: {'{{1}}'}, {'{{2}}'}…)</span>
          <textarea className="input" name="cuerpo" rows={4} required placeholder="Hola, para {{1}} recomendamos…" />
        </label>
        <label className="campo ancho">
          <span>Nombre de cada variable, en orden y separados por coma</span>
          <input className="input" name="variables" placeholder="mascota, medicamento" />
        </label>
        {crear.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(crear.error, 'No fue posible guardar.')}
          </p>
        )}
      </form>
    </Modal>
  )
}

function Plantillas() {
  const plantillas = usePlantillas()
  const crear = useCrearPlantilla()
  const [nueva, setNueva] = useState(false)

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Plantillas de consulta</h3>
        <button className="btn btn-suave" type="button" onClick={() => setNueva(true)}>
          <Icono nombre="mas" size={16} /> Nueva plantilla
        </button>
      </div>
      <Consulta
        consulta={plantillas}
        cargando="Cargando plantillas…"
        error="No fue posible cargar las plantillas."
        vacio="No hay plantillas. Agilizan el registro de consultas frecuentes."
        estaVacio={(d) => d.length === 0}
      >
        {(d) =>
          d.map((p) => (
            <div key={p.codigo} className="fila">
              <div className="fila-cuerpo">
                <strong>{p.nombre}</strong>
                <span>{Object.keys(p.campos).join(', ') || 'Sin campos prellenados'}</span>
              </div>
            </div>
          ))
        }
      </Consulta>
      <Modal
        abierto={nueva}
        onCambio={(v) => {
          if (!v) {
            crear.reset()
            setNueva(false)
          }
        }}
        titulo="Nueva plantilla"
        descripcion="Los campos que llenes aquí aparecen prellenados al registrar una consulta."
        pie={
          <button className="btn btn-primario" type="submit" form="nueva-plantilla" disabled={crear.isPending}>
            Guardar plantilla
          </button>
        }
      >
        <form
          id="nueva-plantilla"
          className="formulario"
          onSubmit={(e) => {
            e.preventDefault()
            const d = new FormData(e.currentTarget)
            const campos: Record<string, string> = {}
            for (const { campo } of CAMPOS_CLINICOS) {
              const v = String(d.get(campo) ?? '').trim()
              if (v) campos[campo] = v
            }
            crear.mutate(
              { codigo: String(d.get('codigo')).trim(), nombre: String(d.get('nombre')).trim(), campos },
              { onSuccess: () => setNueva(false) },
            )
          }}
        >
          <label className="campo">
            <span>Código</span>
            <input className="input" name="codigo" required pattern="[a-z0-9_]+" />
          </label>
          <label className="campo">
            <span>Nombre</span>
            <input className="input" name="nombre" required />
          </label>
          {CAMPOS_CLINICOS.filter((c) => c.campo !== 'notas_internas').map(({ campo, label }) => (
            <label key={campo} className="campo ancho">
              <span>{label}</span>
              <textarea className="input" name={campo} rows={2} />
            </label>
          ))}
          {crear.isError && (
            <p className="error ancho" role="alert">
              {mensajeError(crear.error, 'No fue posible guardar la plantilla.')}
            </p>
          )}
        </form>
      </Modal>
    </section>
  )
}
