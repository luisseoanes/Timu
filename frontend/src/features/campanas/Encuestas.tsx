import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Insignia } from '@/components/Distintivo'
import { Paginacion } from '@/components/Paginacion'
import { useAuth } from '@/features/auth'
import { useNombreTipoServicio } from '@/features/catalogos'
import { mensajeError } from '@/lib/errores'
import { fechaHora, hoyISO, porcentaje } from '@/lib/formato'
import { puede } from '@/lib/permisos'

import { useConfiguracionEncuestas, useEncuestas, useGuardarConfiguracion, useResumenEncuestas } from './api'

export function Encuestas() {
  const { usuario } = useAuth()
  const hoy = hoyISO()
  const resumen = useResumenEncuestas(`${hoy.slice(0, 8)}01`, hoy)
  const [soloBajas, setSoloBajas] = useState(false)
  const [offset, setOffset] = useState(0)
  const encuestas = useEncuestas({ estado: 'respondida', puntaje_max: soloBajas ? 3 : undefined, limit: 20, offset })
  const nombreTipo = useNombreTipoServicio()

  return (
    <div className="pila">
      <section className="tarjeta">
        <div className="tarjeta-cabeza">
          <h3>Satisfacción del mes</h3>
        </div>
        <Consulta consulta={resumen} cargando="Calculando…" error="No fue posible calcular la satisfacción.">
          {(r) => (
            <div className="pila">
              <div className="indicadores indicadores-pocos">
                <div className="indicador">
                  <span className="indicador-titulo">Promedio</span>
                  <strong className="indicador-valor numero">{r.promedio === null ? '—' : `${r.promedio} / 5`}</strong>
                </div>
                <div className="indicador">
                  <span className="indicador-titulo">Respondidas</span>
                  <strong className="indicador-valor numero">{r.respondidas}</strong>
                  <span className="indicador-detalle">de {r.enviadas} enviadas · {porcentaje(r.tasa_respuesta)}</span>
                </div>
              </div>
              {r.por_tipo_servicio.length > 0 && (
                <div className="ficha">
                  {r.por_tipo_servicio.map((t) => (
                    <div key={t.tipo_servicio}>
                      <dt>{nombreTipo(t.tipo_servicio)}</dt>
                      <dd className="numero">
                        {t.promedio} · {t.respuestas} resp.
                      </dd>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </Consulta>
      </section>
      <section className="tarjeta">
        <div className="tarjeta-cabeza">
          <h3>Respuestas</h3>
          <label className="acciones">
            <input type="checkbox" checked={soloBajas} onChange={(e) => { setSoloBajas(e.target.checked); setOffset(0) }} />
            Sólo calificaciones de 3 o menos
          </label>
        </div>
        <Consulta
          consulta={encuestas}
          cargando="Cargando respuestas…"
          error="No fue posible cargar las respuestas."
          vacio={soloBajas ? 'Nadie ha calificado con 3 o menos.' : 'Aún nadie ha respondido la encuesta.'}
          estaVacio={(d) => d.items.length === 0}
        >
          {(d) => (
            <>
              {d.items.map((e) => (
                <div key={e.id} className="fila">
                  <Insignia tono={(e.puntaje ?? 0) <= 3 ? 'alerta' : 'ok'}>{e.puntaje} / 5</Insignia>
                  <div className="fila-cuerpo">
                    <strong>{e.comentario ?? 'Sin comentario'}</strong>
                    <span>
                      {fechaHora(e.respondida_en)} · <Link to={`/familias/${e.familia_id}`}>Ver familia</Link> ·{' '}
                      <Link to={`/servicios/${e.servicio_id}`}>Ver servicio</Link>
                    </span>
                  </div>
                  {e.tarea_id && <Insignia tono="info">Con tarea de seguimiento</Insignia>}
                </div>
              ))}
              <Paginacion total={d.total} limit={d.limit} offset={d.offset} onCambio={setOffset} />
            </>
          )}
        </Consulta>
      </section>
      {puede(usuario, 'administrar') && <ConfiguracionEncuestas />}
    </div>
  )
}

function ConfiguracionEncuestas() {
  const configuracion = useConfiguracionEncuestas(true)
  const guardar = useGuardarConfiguracion()
  const general = configuracion.data?.find((c) => !c.tipo_servicio_codigo)

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Configuración general</h3>
      </div>
      <Consulta consulta={configuracion} cargando="Cargando…" error="No fue posible cargar la configuración.">
        {() => (
          <form
            className="formulario"
            onSubmit={(e) => {
              e.preventDefault()
              const fd = new FormData(e.currentTarget)
              guardar.mutate({
                tipo_servicio_codigo: null,
                encuesta_activa: fd.get('activa') === 'on',
                demora_horas: Number(fd.get('demora_horas')),
                plantilla_encuesta: general?.plantilla_encuesta ?? 'encuesta_satisfaccion',
                seguimiento_dias: fd.get('seguimiento_dias') ? Number(fd.get('seguimiento_dias')) : null,
                plantilla_seguimiento: general?.plantilla_seguimiento ?? 'seguimiento_post',
                umbral_alerta: Number(fd.get('umbral_alerta')),
                comentario: general?.comentario ?? null,
              })
            }}
          >
            <label className="acciones ancho">
              <input type="checkbox" name="activa" defaultChecked={general?.encuesta_activa ?? true} />
              Enviar encuesta después de cada servicio
            </label>
            <label className="campo">
              <span>Horas después del servicio</span>
              <input className="input" name="demora_horas" type="number" min={0} defaultValue={general?.demora_horas ?? 2} />
            </label>
            <label className="campo">
              <span>Seguimiento a los (días)</span>
              <input className="input" name="seguimiento_dias" type="number" min={1} defaultValue={general?.seguimiento_dias ?? ''} />
            </label>
            <label className="campo">
              <span>Alertar con puntaje de hasta</span>
              <input className="input" name="umbral_alerta" type="number" min={1} max={5} defaultValue={general?.umbral_alerta ?? 3} />
            </label>
            <div className="acciones ancho">
              <button className="btn btn-primario" type="submit" disabled={guardar.isPending}>
                Guardar
              </button>
              {guardar.isSuccess && (
                <span className="exito" role="status">
                  Guardado.
                </span>
              )}
              {guardar.isError && (
                <span className="error" role="alert">
                  {mensajeError(guardar.error, 'No fue posible guardar.')}
                </span>
              )}
            </div>
          </form>
        )}
      </Consulta>
    </section>
  )
}
