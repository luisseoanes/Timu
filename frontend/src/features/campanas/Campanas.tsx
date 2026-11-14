import { useState } from 'react'

import { Consulta } from '@/components/Consulta'
import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { useAuth } from '@/features/auth'
import { descargar } from '@/lib/descargas'
import { mensajeError } from '@/lib/errores'
import { fechaHora } from '@/lib/formato'
import { puede } from '@/lib/permisos'
import type { CampanaRead } from '@/types'

import {
  useCampanas,
  useCancelarCampana,
  useCrearCampana,
  useEjecuciones,
  usePlantillasWhatsApp,
  usePrevisualizacionCampana,
  useProgramarCampana,
  useResultados,
  useSegmentos,
  type FiltrosSegmento,
} from './api'
import { FormFiltros } from './FormFiltros'

export function Campanas() {
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
