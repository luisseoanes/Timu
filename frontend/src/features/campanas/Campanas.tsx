import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { useAuth } from '@/features/auth'
import { descargar } from '@/lib/descargas'
import { mensajeError } from '@/lib/errores'
import { diaISO, fechaCompacta, fechaCortaConDia, fechaHora, hora } from '@/lib/formato'
import { puede } from '@/lib/permisos'
import type { CampanaRead } from '@/types'

import {
  useCampanas,
  useCancelarCampana,
  useEjecuciones,
  usePrevisualizacionCampana,
  useProgramarCampana,
  useResultados,
  type FiltrosSegmento,
} from './api'
import { NuevaCampana } from './NuevaCampana'
import { resumenFiltros } from './segmento'

const RECURRENCIA: Record<string, string> = { ninguna: '', diaria: 'cada día', semanal: 'cada semana', mensual: 'cada mes' }

/** Cuándo sale una campaña, dicho para una persona. */
function cuandoSale(c: CampanaRead): string {
  const repite = RECURRENCIA[c.recurrencia] ?? c.recurrencia
  if (!c.proxima_ejecucion) return repite ? `Se repite ${repite}` : c.estado === 'borrador' ? 'Sin programar' : '—'
  const cuando = `${fechaCortaConDia(diaISO(c.proxima_ejecucion))} · ${hora(c.proxima_ejecucion)}`
  return repite ? `${cuando} · ${repite}` : cuando
}

/** Campañas (R2-PAN-09) en listado con ficha, como Familias: la campaña abierta vive en la URL
 * (`?campana=`), con su audiencia, su mensaje, su programación y sus resultados. */
export function Campanas() {
  const [params] = useSearchParams()
  const abierta = params.get('campana')
  return (
    <div className="con-ficha" data-abierta={abierta ? 'true' : undefined}>
      <CampanasLista seleccionada={abierta} />
      {abierta ? (
        <FichaCampana key={abierta} id={abierta} />
      ) : (
        <section className="ficha-abierta ficha-vacia" aria-label="Campaña abierta">
          <p>Abre una campaña para ver a quién le llega, qué mensaje sale y cómo le fue.</p>
        </section>
      )}
    </div>
  )
}

function CampanasLista({ seleccionada }: { seleccionada: string | null }) {
  const { usuario } = useAuth()
  const [params] = useSearchParams()
  const campanas = useCampanas()
  const [nueva, setNueva] = useState(false)
  const mercadeo = puede(usuario, 'mercadeo')
  const enlace = (id: string) => {
    const siguiente = new URLSearchParams(params)
    siguiente.set('campana', id)
    return `?${siguiente}`
  }

  return (
    <section className="listado" aria-labelledby="campanas-titulo">
      <div className="listado-cabeza">
        <h2 id="campanas-titulo">
          Campañas {campanas.data && <span className="apagado numero">{campanas.data.length}</span>}
        </h2>
        {mercadeo && (
          // Verde solo sin una campaña abierta: con la ficha a la vista, el verde es de ella.
          <button className={`btn ${seleccionada ? 'btn-suave' : 'btn-primario'}`} type="button" onClick={() => setNueva(true)}>
            <Icono nombre="mas" size={16} /> Nueva campaña
          </button>
        )}
      </div>
      <Consulta
        consulta={campanas}
        cargando="Cargando las campañas…"
        error="No fue posible cargar las campañas."
        vacio={mercadeo ? 'Aún no hay campañas. Crea una con «Nueva campaña».' : 'Aún no hay campañas.'}
        estaVacio={(d) => d.length === 0}
      >
        {(d) => (
          <ul className="listado-filas" aria-label="Campañas">
            {d.map((c) => (
              <li key={c.id} className="listado-fila" data-seleccionada={c.id === seleccionada}>
                <span className="listado-fila-cabeza">
                  <Link className="listado-fila-enlace" to={enlace(c.id)} aria-current={c.id === seleccionada ? 'page' : undefined}>
                    {c.nombre}
                  </Link>
                  <Distintivo dominio="campana" valor={c.estado} />
                </span>
                <span className="servicio-fila-datos">
                  <span>{resumenFiltros(c.segmento as FiltrosSegmento)}</span>
                  <span className="numero">{cuandoSale(c)}</span>
                </span>
              </li>
            ))}
          </ul>
        )}
      </Consulta>
      <NuevaCampana abierto={nueva} onCerrar={() => setNueva(false)} />
    </section>
  )
}

const RESULTADOS = [
  { clave: 'enviados', label: 'Enviados' },
  { clave: 'entregados', label: 'Entregados' },
  { clave: 'leidos', label: 'Leídos' },
  { clave: 'respondidos', label: 'Respondidos' },
  { clave: 'fallidos', label: 'No se enviaron' },
] as const

function FichaCampana({ id }: { id: string }) {
  const campanas = useCampanas()
  const c = campanas.data?.find((x) => x.id === id)
  return (
    <section className="ficha-abierta" aria-label="Campaña abierta">
      <Consulta consulta={campanas} cargando="Cargando la campaña…" error="No fue posible cargar la campaña.">
        {() => (c ? <Ficha campana={c} /> : <p className="apagado">Esta campaña ya no existe o no la puedes ver.</p>)}
      </Consulta>
    </section>
  )
}

function Ficha({ campana: c }: { campana: CampanaRead }) {
  const { usuario } = useAuth()
  const [params] = useSearchParams()
  const previa = usePrevisualizacionCampana(c.id)
  const resultados = useResultados(c.id)
  const ejecuciones = useEjecuciones(c.id)
  const programar = useProgramarCampana()
  const [cuando, setCuando] = useState('')
  const [recurrencia, setRecurrencia] = useState('ninguna')
  const [cancelando, setCancelando] = useState(false)
  const [confirmando, setConfirmando] = useState(false)
  const [errorCsv, setErrorCsv] = useState<string | null>(null)
  const mercadeo = puede(usuario, 'mercadeo')
  const editable = c.estado === 'borrador' || c.estado === 'programada'
  const volver = new URLSearchParams(params)
  volver.delete('campana')

  return (
    <>
      <header className="ficha-cabeza">
        <Link to={`?${volver}`} className="btn btn-plano ficha-volver" aria-label="Volver a las campañas">
          <Icono nombre="volver" size={16} />
        </Link>
        <h2 className="campana-titulo">{c.nombre}</h2>
        <div className="ficha-datos campana-quien">
          <Distintivo dominio="campana" valor={c.estado} />
          <span className="numero">{cuandoSale(c)}</span>
        </div>
      </header>

      <dl className="ficha campana-datos">
        <div>
          <dt>A quién le llega</dt>
          <dd>{resumenFiltros(c.segmento as FiltrosSegmento)}</dd>
        </div>
        <div>
          <dt>Plantilla</dt>
          <dd>
            {/* El nombre para el equipo (DEU-10); el código de Meta, como dato secundario. */}
            {c.plantilla_titulo ?? <span className="campana-plantilla">{c.plantilla ?? '—'}</span>}
            {c.plantilla_titulo && <span className="campana-plantilla-codigo">{c.plantilla}</span>}
          </dd>
        </div>
      </dl>

      <section className="bloque" aria-labelledby="campana-audiencia">
        <h3 id="campana-audiencia">Audiencia</h3>
        <Consulta consulta={previa} cargando="Calculando la audiencia…" error="No fue posible calcular la audiencia.">
          {(p) => (
            <>
              <p className="campana-audiencia">
                Le llega a <strong className="numero">{p.se_enviaran}</strong> de <span className="numero">{p.audiencia}</span>{' '}
                {p.audiencia === 1 ? 'familia' : 'familias'}
                {p.excluidos_por_baja > 0 && (
                  <>
                    {' '}
                    · <span className="numero">{p.excluidos_por_baja}</span> se dieron de baja de los mensajes
                  </>
                )}
                .
              </p>
              {p.ejemplos.map((e) => (
                <figure key={e.titular} className="campana-ejemplo">
                  <figcaption>Así le llega a {e.titular}</figcaption>
                  <p>{e.mensaje}</p>
                </figure>
              ))}
            </>
          )}
        </Consulta>
      </section>

      {mercadeo && editable && (
        <section className="bloque" aria-labelledby="campana-envio">
          <h3 id="campana-envio">Envío</h3>
          <div className="formulario">
            <div className="campo">
              <label htmlFor="campana-cuando">Enviar el</label>
              <input id="campana-cuando" className="input" type="datetime-local" value={cuando} onChange={(e) => setCuando(e.target.value)} aria-describedby="campana-cuando-ayuda" />
              <small id="campana-cuando-ayuda" className="campo-ayuda">Vacío, sale en cuanto lo confirmes.</small>
            </div>
            <label className="campo">
              <span>Repetir</span>
              <select className="input" value={recurrencia} onChange={(e) => setRecurrencia(e.target.value)}>
                <option value="ninguna">No repetir</option>
                <option value="diaria">Cada día</option>
                <option value="semanal">Cada semana</option>
                <option value="mensual">Cada mes</option>
              </select>
            </label>
            <div className="acciones ancho">
              <button
                className="btn btn-primario"
                type="button"
                disabled={programar.isPending}
                onClick={() =>
                  // Programada se puede cancelar antes de que salga; el envío inmediato no se deshace.
                  cuando ? programar.mutate({ id: c.id, cuando: `${cuando}:00-05:00`, recurrencia }) : setConfirmando(true)
                }
              >
                {programar.isPending ? 'Programando…' : cuando ? 'Programar envío' : 'Enviar ahora'}
              </button>
              {c.estado === 'programada' && (
                <button className="btn btn-plano btn-plano-peligro" type="button" onClick={() => setCancelando(true)}>
                  Cancelar campaña
                </button>
              )}
            </div>
          </div>
          {programar.isError && (
            <p className="error" role="alert">
              {mensajeError(programar.error, 'No fue posible programar la campaña.')}
            </p>
          )}
          {programar.isSuccess && (
            <p className="exito" role="status">
              {cuando ? 'Campaña programada.' : 'La campaña está saliendo.'}
            </p>
          )}
        </section>
      )}

      <section className="bloque" aria-labelledby="campana-resultados">
        <h3 id="campana-resultados">Cómo le fue</h3>
        {resultados.data && resultados.data.audiencia > 0 ? (
          <dl className="campana-resultados">
            {RESULTADOS.map((r) => (
              <div key={r.clave}>
                <dt>{r.label}</dt>
                <dd className="numero">{resultados.data[r.clave]}</dd>
              </div>
            ))}
          </dl>
        ) : resultados.isError ? (
          <p className="error" role="alert">No fue posible cargar los resultados.</p>
        ) : (
          <p className="apagado">Todavía no ha salido: aquí aparecerá cuántos mensajes se entregaron, se leyeron y se respondieron.</p>
        )}
        {(ejecuciones.data?.length ?? 0) > 0 && (
          <p className="campana-nota">
            Ha salido <span className="numero">{ejecuciones.data!.length}</span> {ejecuciones.data!.length === 1 ? 'vez' : 'veces'}; la última, el{' '}
            <span className="numero">{fechaCompacta(diaISO(ejecuciones.data![0]!.iniciada_en))}</span> a las{' '}
            <span className="numero" title={fechaHora(ejecuciones.data![0]!.iniciada_en)}>{hora(ejecuciones.data![0]!.iniciada_en)}</span>.
          </p>
        )}
        {/* Sin haber salido nunca no hay destinatarios que descargar. */}
        {(ejecuciones.data?.length ?? 0) > 0 && (
          <div className="acciones">
            <button
              className="btn btn-plano btn-accion campana-csv"
              type="button"
              onClick={() =>
                descargar(`/campanas/${c.id}/resultados`, { formato: 'csv' }, `campana-${c.nombre}.csv`).catch((e) =>
                  setErrorCsv(mensajeError(e, 'No fue posible descargar los destinatarios.')),
                )
              }
            >
              <Icono nombre="descargar" size={16} /> Destinatarios en CSV
            </button>
          </div>
        )}
        {errorCsv && (
          <p className="error" role="alert">
            {errorCsv}
          </p>
        )}
      </section>
      {cancelando && <CancelarModal campana={c} onCerrar={() => setCancelando(false)} />}
      {confirmando && (
        <Modal
          abierto
          onCambio={(v) => !v && setConfirmando(false)}
          titulo={previa.data ? `Enviar ahora a ${previa.data.se_enviaran} ${previa.data.se_enviaran === 1 ? 'familia' : 'familias'}` : 'Enviar ahora'}
          descripcion="Los mensajes empiezan a salir en cuanto lo confirmes, y no se pueden retirar."
          pie={
            <>
              <button className="btn btn-secundario" type="button" onClick={() => setConfirmando(false)}>
                Volver
              </button>
              <button
                className="btn btn-primario"
                type="button"
                onClick={() => {
                  programar.mutate({ id: c.id, recurrencia })
                  setConfirmando(false)
                }}
              >
                Enviar ahora
              </button>
            </>
          }
        >
          <p className="campana-nota">
            Plantilla «{c.plantilla_titulo ?? c.plantilla ?? '—'}» · {resumenFiltros(c.segmento as FiltrosSegmento)}
          </p>
        </Modal>
      )}
    </>
  )
}

function CancelarModal({ campana: c, onCerrar }: { campana: CampanaRead; onCerrar: () => void }) {
  const cancelar = useCancelarCampana()
  return (
    <Modal
      abierto
      onCambio={(v) => !v && onCerrar()}
      titulo={`Cancelar «${c.nombre}»`}
      descripcion="No saldrá ningún mensaje más de esta campaña. No se deshace: para volver a enviarla, crea otra."
      pie={
        <>
          <button className="btn btn-secundario" type="button" onClick={onCerrar}>
            Mantenerla
          </button>
          <button className="btn btn-peligro" type="button" disabled={cancelar.isPending} onClick={() => cancelar.mutate(c.id, { onSuccess: onCerrar })}>
            {cancelar.isPending ? 'Cancelando…' : 'Cancelar campaña'}
          </button>
        </>
      }
    >
      {cancelar.isError && (
        <p className="error" role="alert">
          {mensajeError(cancelar.error, 'No fue posible cancelar la campaña.')}
        </p>
      )}
    </Modal>
  )
}
