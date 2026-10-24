import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { Paginacion } from '@/components/Paginacion'
import { Pestanas } from '@/components/Pestanas'
import { useAuth } from '@/features/auth/AuthContext'
import { useCiudades, usePlanes, useNombreTipoServicio } from '@/features/catalogos/api'
import { descargar } from '@/lib/descargas'
import { mensajeError } from '@/lib/errores'
import { fecha, fechaHora, hoyISO, porcentaje } from '@/lib/formato'
import { puede } from '@/lib/permisos'
import type { CampanaRead, EstadoAfiliacion } from '@/types'

import {
  useBajas,
  useCampanas,
  useCancelarCampana,
  useConfiguracionEncuestas,
  useCrearBaja,
  useCrearCampana,
  useCrearPlantillaWhatsApp,
  useCrearSegmento,
  useEjecuciones,
  useEncuestas,
  useEstadoPlantilla,
  useGuardarConfiguracion,
  useMensajes,
  usePlantillasWhatsApp,
  usePrevisualizacionCampana,
  usePrevisualizarSegmento,
  useProgramarCampana,
  useQuitarBaja,
  useResultados,
  useResumenEncuestas,
  useSegmentos,
  type FiltrosSegmento,
} from './api'

export function CampanasPage() {
  const { usuario } = useAuth()
  const pestanas = [
    { valor: 'campanas', titulo: 'Campañas', contenido: <Campanas /> },
    { valor: 'segmentos', titulo: 'Segmentos', contenido: <Segmentos /> },
    { valor: 'encuestas', titulo: 'Encuestas', contenido: <Encuestas /> },
    { valor: 'mensajes', titulo: 'Mensajes', contenido: <Mensajes /> },
  ]
  if (puede(usuario, 'mercadeo')) pestanas.push({ valor: 'plantillas', titulo: 'Plantillas de WhatsApp', contenido: <PlantillasWhatsApp /> })
  return <Pestanas etiqueta="Secciones de campañas" pestanas={pestanas} />
}

// --- Campañas -------------------------------------------------------------------------------

function Campanas() {
  const { usuario } = useAuth()
  const campanas = useCampanas()
  const [nueva, setNueva] = useState(false)
  const [abierta, setAbierta] = useState<CampanaRead | null>(null)
  const mercadeo = puede(usuario, 'mercadeo')

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Campañas por WhatsApp</h3>
        {mercadeo && (
          <button className="btn btn-primario" type="button" onClick={() => setNueva(true)}>
            <Icono nombre="mas" size={16} /> Nueva campaña
          </button>
        )}
      </div>
      <Consulta
        consulta={campanas}
        cargando="Cargando campañas…"
        error="No fue posible cargar las campañas."
        vacio="Aún no hay campañas."
        estaVacio={(d) => d.length === 0}
      >
        {(d) => (
          <div className="scroll-x">
            <table className="tabla">
              <thead>
                <tr>
                  <th>Campaña</th>
                  <th>Plantilla</th>
                  <th>Programación</th>
                  <th>Estado</th>
                  <th><span className="sr-only">Acciones</span></th>
                </tr>
              </thead>
              <tbody>
                {d.map((c) => (
                  <tr key={c.id}>
                    <td className="principal">{c.nombre}</td>
                    <td className="numero">{c.plantilla}</td>
                    <td>
                      {c.proxima_ejecucion ? fechaHora(c.proxima_ejecucion) : '—'}
                      {c.recurrencia !== 'ninguna' && <span className="apagado"> · {c.recurrencia}</span>}
                    </td>
                    <td>
                      <Distintivo dominio="campana" valor={c.estado} />
                    </td>
                    <td>
                      <button className="btn btn-suave" type="button" onClick={() => setAbierta(c)}>
                        Ver
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Consulta>
      <NuevaCampana abierto={nueva} onCerrar={() => setNueva(false)} />
      {abierta && <DetalleCampana campana={d(campanas.data, abierta)} mercadeo={mercadeo} onCerrar={() => setAbierta(null)} />}
    </section>
  )
}

/** La versión más reciente de la campaña abierta (tras programar o cancelar cambia). */
function d(lista: CampanaRead[] | undefined, actual: CampanaRead): CampanaRead {
  return lista?.find((c) => c.id === actual.id) ?? actual
}

function DetalleCampana({ campana: c, mercadeo, onCerrar }: { campana: CampanaRead; mercadeo: boolean; onCerrar: () => void }) {
  const previa = usePrevisualizacionCampana(c.id)
  const resultados = useResultados(c.id)
  const ejecuciones = useEjecuciones(c.id)
  const programar = useProgramarCampana()
  const cancelar = useCancelarCampana()
  const [cuando, setCuando] = useState('')
  const [recurrencia, setRecurrencia] = useState('ninguna')
  const [errorCsv, setErrorCsv] = useState<string | null>(null)
  const editable = c.estado === 'borrador' || c.estado === 'programada'

  return (
    <Modal abierto onCambio={(v) => !v && onCerrar()} titulo={c.nombre} descripcion={`Plantilla ${c.plantilla}`}>
      <div className="pila">
        <Consulta consulta={previa} cargando="Calculando la audiencia…" error="No fue posible previsualizar.">
          {(p) => (
            <>
              <div className="indicadores">
                <div className="indicador">
                  <span className="indicador-titulo">Audiencia</span>
                  <strong className="indicador-valor numero">{p.audiencia}</strong>
                </div>
                <div className="indicador">
                  <span className="indicador-titulo">Dados de baja</span>
                  <strong className="indicador-valor numero">{p.excluidos_por_baja}</strong>
                </div>
                <div className="indicador">
                  <span className="indicador-titulo">Se enviarán</span>
                  <strong className="indicador-valor numero">{p.se_enviaran}</strong>
                </div>
              </div>
              {p.ejemplos.map((e) => (
                <div key={e.titular} className="mensaje-ejemplo">
                  <span className="apagado">Para {e.titular}</span>
                  <p>{e.mensaje}</p>
                </div>
              ))}
            </>
          )}
        </Consulta>

        {resultados.data && resultados.data.audiencia > 0 && (
          <div className="ficha">
            {(['enviados', 'entregados', 'leidos', 'respondidos', 'fallidos'] as const).map((k) => (
              <div key={k}>
                <dt>{k}</dt>
                <dd className="numero">{resultados.data[k]}</dd>
              </div>
            ))}
          </div>
        )}
        {(ejecuciones.data?.length ?? 0) > 0 && (
          <p className="apagado">
            {ejecuciones.data?.length} ejecuciones · última {fechaHora(ejecuciones.data?.[0]?.iniciada_en)}
          </p>
        )}

        {mercadeo && editable && (
          <div className="formulario">
            <label className="campo">
              <span>Enviar el (vacío = ahora)</span>
              <input className="input" type="datetime-local" value={cuando} onChange={(e) => setCuando(e.target.value)} />
            </label>
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
                onClick={() => programar.mutate({ id: c.id, cuando: cuando ? `${cuando}:00-05:00` : undefined, recurrencia })}
              >
                {cuando ? 'Programar envío' : 'Enviar ahora'}
              </button>
              {c.estado === 'programada' && (
                <button className="btn btn-plano" type="button" disabled={cancelar.isPending} onClick={() => cancelar.mutate(c.id)}>
                  Cancelar campaña
                </button>
              )}
            </div>
          </div>
        )}
        <button
          className="btn btn-plano"
          type="button"
          onClick={() =>
            descargar(`/campanas/${c.id}/resultados`, { formato: 'csv' }, `campana-${c.nombre}.csv`).catch((e) =>
              setErrorCsv(mensajeError(e, 'No fue posible descargar.')),
            )
          }
        >
          <Icono nombre="descargar" size={16} /> Destinatarios en CSV
        </button>
        {(programar.isError || cancelar.isError || errorCsv) && (
          <p className="error" role="alert">
            {errorCsv ?? mensajeError(programar.error ?? cancelar.error, 'No fue posible completar la acción.')}
          </p>
        )}
        {programar.isSuccess && (
          <p className="exito" role="status">
            Campaña programada.
          </p>
        )}
      </div>
    </Modal>
  )
}

function NuevaCampana({ abierto, onCerrar }: { abierto: boolean; onCerrar: () => void }) {
  const crear = useCrearCampana()
  const plantillas = usePlantillasWhatsApp()
  const segmentos = useSegmentos()
  const [plantilla, setPlantilla] = useState('')
  const [segmentoId, setSegmentoId] = useState('')
  const [filtros, setFiltros] = useState<FiltrosSegmento>({})
  const elegida = plantillas.data?.find((p) => p.nombre === plantilla)
  const aprobadas = plantillas.data?.filter((p) => p.estado_aprobacion === 'aprobada' && p.activa) ?? []

  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          crear.reset()
          onCerrar()
        }
      }}
      titulo="Nueva campaña"
      descripcion="Sólo se envían plantillas aprobadas por Meta. Quien se dio de baja queda fuera."
      pie={
        <button className="btn btn-primario" type="submit" form="nueva-campana" disabled={!plantilla || crear.isPending}>
          Crear campaña
        </button>
      }
    >
      <form
        id="nueva-campana"
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const fd = new FormData(e.currentTarget)
          // Cada variable sale de un dato de la familia o de un texto fijo (campanas/service.py: _variables).
          const variables = (elegida?.variables ?? []).map((_, i) => {
            const fuente = String(fd.get(`fuente_${i}`) ?? 'titular_nombre')
            return fuente === 'texto' ? `texto:${String(fd.get(`texto_${i}`) ?? '')}` : fuente
          })
          crear.mutate(
            {
              nombre: String(fd.get('nombre')).trim(),
              plantilla,
              variables,
              segmento_id: segmentoId || undefined,
              segmento: segmentoId ? undefined : filtros,
            },
            { onSuccess: onCerrar },
          )
        }}
      >
        <label className="campo ancho">
          <span>Nombre</span>
          <input className="input" name="nombre" required />
        </label>
        <label className="campo">
          <span>Plantilla</span>
          <select className="input" value={plantilla} onChange={(e) => setPlantilla(e.target.value)} required>
            <option value="" disabled>
              {aprobadas.length ? 'Elige la plantilla' : 'No hay plantillas aprobadas'}
            </option>
            {aprobadas.map((p) => (
              <option key={p.id} value={p.nombre}>{p.nombre}</option>
            ))}
          </select>
        </label>
        <label className="campo">
          <span>Audiencia</span>
          <select className="input" value={segmentoId} onChange={(e) => setSegmentoId(e.target.value)}>
            <option value="">Filtros a la medida</option>
            {segmentos.data?.map((s) => (
              <option key={s.id} value={s.id}>{s.nombre}</option>
            ))}
          </select>
        </label>
        {elegida && <p className="aviso ancho">{elegida.cuerpo}</p>}
        {elegida?.variables.map((v, i) => (
          <fieldset key={v} className="formulario ancho">
            <legend className="ancho">Variable {`{{${v}}}`}</legend>
            <label className="campo">
              <span>Se llena con</span>
              <select className="input" name={`fuente_${i}`} defaultValue="titular_nombre">
                <option value="titular_nombre">Nombre del titular</option>
                <option value="mascota_nombre">Nombre de la mascota</option>
                <option value="ciudad">Ciudad</option>
                <option value="plan">Plan</option>
                <option value="texto">Texto fijo</option>
              </select>
            </label>
            <label className="campo">
              <span>Texto fijo (si aplica)</span>
              <input className="input" name={`texto_${i}`} />
            </label>
          </fieldset>
        ))}
        {!segmentoId && (
          <div className="ancho">
            <FormFiltros valor={filtros} onCambio={setFiltros} />
          </div>
        )}
        {crear.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(crear.error, 'No fue posible crear la campaña.')}
          </p>
        )}
      </form>
    </Modal>
  )
}

const ESTADOS_AFILIACION: { valor: EstadoAfiliacion; label: string }[] = [
  { valor: 'activa', label: 'Activa' },
  { valor: 'en_mora', label: 'En mora' },
  { valor: 'congelada', label: 'Congelada' },
  { valor: 'prospecto', label: 'Prospecto' },
  { valor: 'cancelada', label: 'Cancelada' },
]

/** Filtros de segmento con conteo en vivo de la audiencia. */
function FormFiltros({ valor, onCambio }: { valor: FiltrosSegmento; onCambio: (f: FiltrosSegmento) => void }) {
  const ciudades = useCiudades()
  const planes = usePlanes()
  const previsualizar = usePrevisualizarSegmento()

  function alternar<K extends 'ciudades' | 'estados' | 'planes'>(clave: K, item: NonNullable<FiltrosSegmento[K]>[number]) {
    const actual = (valor[clave] ?? []) as string[]
    const nuevo = actual.includes(item) ? actual.filter((x) => x !== item) : [...actual, item]
    onCambio({ ...valor, [clave]: nuevo })
  }
  const numero = (clave: keyof FiltrosSegmento) => (e: React.ChangeEvent<HTMLInputElement>) =>
    onCambio({ ...valor, [clave]: e.target.value ? Number(e.target.value) : undefined })

  return (
    <fieldset className="pila" style={{ border: 0, margin: 0, padding: 0 }}>
      <legend className="subtitulo">Quiénes reciben</legend>
      <div className="grupo-chips" role="group" aria-label="Estados de afiliación">
        {ESTADOS_AFILIACION.map((e) => (
          <button key={e.valor} type="button" className="cupo" aria-pressed={valor.estados?.includes(e.valor) ?? false} onClick={() => alternar('estados', e.valor)}>
            {e.label}
          </button>
        ))}
      </div>
      <div className="grupo-chips" role="group" aria-label="Ciudades">
        {ciudades.data?.slice(0, 12).map((c) => (
          <button key={c.codigo} type="button" className="cupo" aria-pressed={valor.ciudades?.includes(c.nombre) ?? false} onClick={() => alternar('ciudades', c.nombre)}>
            {c.nombre}
          </button>
        ))}
      </div>
      <div className="grupo-chips" role="group" aria-label="Planes">
        {planes.data?.map((p) => (
          <button key={p.id} type="button" className="cupo" aria-pressed={valor.planes?.includes(p.codigo) ?? false} onClick={() => alternar('planes', p.codigo)}>
            {p.nombre}
          </button>
        ))}
      </div>
      <div className="formulario">
        <label className="campo">
          <span>Días de mora mínimos</span>
          <input className="input" type="number" min={0} value={valor.dias_mora_min ?? ''} onChange={numero('dias_mora_min')} />
        </label>
        <label className="campo">
          <span>Sin servicio hace (días)</span>
          <input className="input" type="number" min={0} value={valor.sin_servicio_dias ?? ''} onChange={numero('sin_servicio_dias')} />
        </label>
        <label className="campo">
          <span>Renuevan en (días)</span>
          <input className="input" type="number" min={0} value={valor.renovacion_en_dias ?? ''} onChange={numero('renovacion_en_dias')} />
        </label>
        <label className="campo">
          <span>Mascotas mínimas</span>
          <input className="input" type="number" min={1} value={valor.mascotas_min ?? ''} onChange={numero('mascotas_min')} />
        </label>
      </div>
      <div className="acciones">
        <button className="btn btn-suave" type="button" disabled={previsualizar.isPending} onClick={() => previsualizar.mutate(valor)}>
          Contar audiencia
        </button>
        {previsualizar.data && (
          <span role="status">
            <strong className="numero">{previsualizar.data.total}</strong> familias
            {previsualizar.data.muestra.length > 0 && (
              <span className="apagado"> · {previsualizar.data.muestra.slice(0, 3).map((m) => m.titular).join(', ')}…</span>
            )}
          </span>
        )}
        {previsualizar.isError && (
          <span className="error" role="alert">
            {mensajeError(previsualizar.error, 'No fue posible contar.')}
          </span>
        )}
      </div>
    </fieldset>
  )
}

// --- Segmentos ------------------------------------------------------------------------------

function Segmentos() {
  const { usuario } = useAuth()
  const segmentos = useSegmentos()
  const crear = useCrearSegmento()
  const [nuevo, setNuevo] = useState(false)
  const [filtros, setFiltros] = useState<FiltrosSegmento>({})

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Segmentos guardados</h3>
        {puede(usuario, 'mercadeo') && (
          <button className="btn btn-suave" type="button" onClick={() => setNuevo(true)}>
            <Icono nombre="mas" size={16} /> Nuevo segmento
          </button>
        )}
      </div>
      <Consulta
        consulta={segmentos}
        cargando="Cargando segmentos…"
        error="No fue posible cargar los segmentos."
        vacio="No hay segmentos guardados."
        estaVacio={(s) => s.length === 0}
      >
        {(s) =>
          s.map((seg) => (
            <div key={seg.id} className="fila">
              <span className="fila-icono">
                <Icono nombre="familias" size={16} />
              </span>
              <div className="fila-cuerpo">
                <strong>{seg.nombre}</strong>
                <span>{seg.descripcion ?? resumenFiltros(seg.filtros as FiltrosSegmento)}</span>
              </div>
            </div>
          ))
        }
      </Consulta>
      <Modal
        abierto={nuevo}
        onCambio={(v) => {
          if (!v) {
            crear.reset()
            setNuevo(false)
          }
        }}
        titulo="Nuevo segmento"
        pie={
          <button className="btn btn-primario" type="submit" form="nuevo-segmento" disabled={crear.isPending}>
            Guardar segmento
          </button>
        }
      >
        <form
          id="nuevo-segmento"
          className="formulario"
          onSubmit={(e) => {
            e.preventDefault()
            const fd = new FormData(e.currentTarget)
            crear.mutate(
              { nombre: String(fd.get('nombre')).trim(), descripcion: String(fd.get('descripcion') ?? '').trim() || undefined, filtros },
              { onSuccess: () => { setNuevo(false); setFiltros({}) } },
            )
          }}
        >
          <label className="campo">
            <span>Nombre</span>
            <input className="input" name="nombre" required />
          </label>
          <label className="campo">
            <span>Descripción</span>
            <input className="input" name="descripcion" />
          </label>
          <div className="ancho">
            <FormFiltros valor={filtros} onCambio={setFiltros} />
          </div>
          {crear.isError && (
            <p className="error ancho" role="alert">
              {mensajeError(crear.error, 'No fue posible guardar el segmento.')}
            </p>
          )}
        </form>
      </Modal>
    </section>
  )
}

function resumenFiltros(f: FiltrosSegmento): string {
  const partes = [
    f.estados?.length ? f.estados.join(', ') : null,
    f.ciudades?.length ? f.ciudades.join(', ') : null,
    f.dias_mora_min ? `mora ≥ ${f.dias_mora_min} días` : null,
    f.renovacion_en_dias ? `renuevan en ${f.renovacion_en_dias} días` : null,
  ].filter(Boolean)
  return partes.join(' · ') || 'Todas las familias'
}

// --- Encuestas ------------------------------------------------------------------------------

function Encuestas() {
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
              <div className="indicadores">
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
          vacio="No hay respuestas con este filtro."
          estaVacio={(d) => d.items.length === 0}
        >
          {(d) => (
            <>
              {d.items.map((e) => (
                <div key={e.id} className="fila">
                  <span className={`distintivo distintivo-${(e.puntaje ?? 0) <= 3 ? 'alerta' : 'ok'}`}>{e.puntaje} / 5</span>
                  <div className="fila-cuerpo">
                    <strong>{e.comentario ?? 'Sin comentario'}</strong>
                    <span>
                      {fechaHora(e.respondida_en)} · <Link to={`/familias/${e.familia_id}`}>Ver familia</Link> ·{' '}
                      <Link to={`/servicios/${e.servicio_id}`}>Ver servicio</Link>
                    </span>
                  </div>
                  {e.tarea_id && <span className="distintivo distintivo-info">Con tarea de seguimiento</span>}
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

// --- Mensajes y bajas -----------------------------------------------------------------------

function Mensajes() {
  const [estado, setEstado] = useState('')
  const [offset, setOffset] = useState(0)
  const mensajes = useMensajes({ estado: estado || undefined, limit: 25, offset })
  const bajas = useBajas()
  const crearBaja = useCrearBaja()
  const quitarBaja = useQuitarBaja()

  return (
    <div className="con-rail">
      <section className="tarjeta">
        <div className="tarjeta-cabeza">
          <h3>Mensajes de WhatsApp</h3>
          <select className="input" style={{ width: 'auto' }} value={estado} onChange={(e) => { setEstado(e.target.value); setOffset(0) }} aria-label="Estado del mensaje">
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
                <table className="tabla">
                  <thead>
                    <tr>
                      <th>Fecha</th>
                      <th>Destino</th>
                      <th>Contenido</th>
                      <th>Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {d.items.map((m) => (
                      <tr key={m.id}>
                        <td className="numero">{fechaHora(m.created_at)}</td>
                        <td className="numero">
                          {m.direccion === 'entrante' ? '← ' : '→ '}
                          {m.destino ?? '—'}
                        </td>
                        <td>
                          {m.plantilla ? <span className="distintivo distintivo-neutro">{m.plantilla}</span> : null} {m.contenido}
                          {m.error && <div className="error">{m.error}</div>}
                        </td>
                        <td>
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
            className="acciones"
            style={{ marginBlock: 'var(--e3)' }}
            onSubmit={(e) => {
              e.preventDefault()
              const fd = new FormData(e.currentTarget)
              const form = e.currentTarget
              crearBaja.mutate({ telefono: String(fd.get('telefono')).trim() }, { onSuccess: () => form.reset() })
            }}
          >
            <input className="input" name="telefono" aria-label="Celular a dar de baja" placeholder="Celular" required style={{ flex: 1 }} />
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
                    <strong className="numero">{x.destino}</strong>
                    <span>{fecha(x.created_at.slice(0, 10))}</span>
                  </div>
                  <button className="btn btn-plano" type="button" onClick={() => quitarBaja.mutate(x.destino)} aria-label={`Quitar la baja de ${x.destino}`}>
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

// --- Plantillas de WhatsApp -----------------------------------------------------------------

function PlantillasWhatsApp() {
  const plantillas = usePlantillasWhatsApp()
  const crear = useCrearPlantillaWhatsApp()
  const estado = useEstadoPlantilla()
  const [nueva, setNueva] = useState(false)

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Plantillas de WhatsApp</h3>
        <button className="btn btn-suave" type="button" onClick={() => setNueva(true)}>
          <Icono nombre="mas" size={16} /> Nueva plantilla
        </button>
      </div>
      <p className="apagado" style={{ marginBottom: 'var(--e4)' }}>
        Meta aprueba cada plantilla antes de que se pueda usar. Registra aquí el estado que muestra el administrador de WhatsApp.
      </p>
      {estado.isError && (
        <p className="error" role="alert">
          {mensajeError(estado.error, 'No fue posible cambiar el estado.')}
        </p>
      )}
      <Consulta consulta={plantillas} cargando="Cargando…" error="No fue posible cargar las plantillas." vacio="No hay plantillas." estaVacio={(p) => p.length === 0}>
        {(p) => (
          <div className="scroll-x">
            <table className="tabla">
              <thead>
                <tr>
                  <th>Plantilla</th>
                  <th>Categoría</th>
                  <th>Texto</th>
                  <th>Aprobación</th>
                  <th>Activa</th>
                </tr>
              </thead>
              <tbody>
                {p.map((pl) => (
                  <tr key={pl.id}>
                    <td className="principal numero">
                      {pl.nombre} <span className="apagado">v{pl.version}</span>
                    </td>
                    <td>{pl.categoria}</td>
                    <td>{pl.cuerpo}</td>
                    <td>
                      <select
                        className="input"
                        value={pl.estado_aprobacion}
                        aria-label={`Aprobación de ${pl.nombre}`}
                        onChange={(e) => estado.mutate({ id: pl.id, estado_aprobacion: e.target.value })}
                      >
                        {['borrador', 'enviada', 'aprobada', 'rechazada', 'pausada'].map((s) => (
                          <option key={s} value={s}>{s}</option>
                        ))}
                      </select>
                    </td>
                    <td>
                      <input
                        type="checkbox"
                        checked={pl.activa}
                        aria-label={`${pl.nombre} activa`}
                        onChange={(e) => estado.mutate({ id: pl.id, estado_aprobacion: pl.estado_aprobacion, activa: e.target.checked })}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Consulta>
      <Modal
        abierto={nueva}
        onCambio={(v) => {
          if (!v) {
            crear.reset()
            setNueva(false)
          }
        }}
        titulo="Nueva plantilla de WhatsApp"
        pie={
          <button className="btn btn-primario" type="submit" form="nueva-plantilla-wa" disabled={crear.isPending}>
            Guardar
          </button>
        }
      >
        <form
          id="nueva-plantilla-wa"
          className="formulario"
          onSubmit={(e) => {
            e.preventDefault()
            const fd = new FormData(e.currentTarget)
            const cuerpo = String(fd.get('cuerpo')).trim()
            const variables = [...cuerpo.matchAll(/\{\{(\d+)\}\}/g)].map((m) => m[1] ?? '')
            crear.mutate(
              { nombre: String(fd.get('nombre')).trim(), categoria: String(fd.get('categoria')), cuerpo, variables: [...new Set(variables)] },
              { onSuccess: () => setNueva(false) },
            )
          }}
        >
          <label className="campo">
            <span>Nombre (como en Meta)</span>
            <input className="input" name="nombre" required pattern="[a-z0-9_]+" />
          </label>
          <label className="campo">
            <span>Categoría</span>
            <select className="input" name="categoria" defaultValue="utility">
              <option value="utility">Utilidad</option>
              <option value="marketing">Marketing</option>
              <option value="authentication">Autenticación</option>
            </select>
          </label>
          <label className="campo ancho">
            <span>Texto (variables {'{{1}}'}, {'{{2}}'}…)</span>
            <textarea className="input" name="cuerpo" rows={4} required />
          </label>
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
