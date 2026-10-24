import { useState } from 'react'

import { Consulta } from '@/components/Consulta'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { useDefiniciones } from '@/features/dashboard/api'
import { mensajeError } from '@/lib/errores'
import { fechaHora } from '@/lib/formato'
import type { ReporteRead } from '@/types'

import { useEventosPasarela, useGuardarReporte, useReportes, useReprocesarEvento } from './api'

const PERIODICIDAD: Record<string, string> = {
  diaria: 'Cada día (el día anterior)',
  semanal: 'Los lunes (la semana anterior)',
  mensual: 'El día 1 (el mes anterior)',
}

/** Reportes programados por correo (F4-DAS-03) y eventos de la pasarela con error. */
export function Reportes() {
  const reportes = useReportes()
  const guardar = useGuardarReporte()
  const [editando, setEditando] = useState<ReporteRead | 'nuevo' | null>(null)

  return (
    <div className="pila">
      <section className="tarjeta">
        <div className="tarjeta-cabeza">
          <h3>Reportes programados</h3>
          <button className="btn btn-primario" type="button" onClick={() => setEditando('nuevo')}>
            <Icono nombre="mas" size={16} /> Nuevo reporte
          </button>
        </div>
        {guardar.isError && (
          <p className="error" role="alert">
            {mensajeError(guardar.error, 'No fue posible actualizar el reporte.')}
          </p>
        )}
        <Consulta consulta={reportes} cargando="Cargando…" error="No fue posible cargar los reportes." vacio="No hay reportes programados." estaVacio={(d) => d.length === 0}>
          {(d) =>
            d.map((r) => (
              <div key={r.id} className="fila">
                <span className="fila-icono">
                  <Icono nombre="correo" size={16} />
                </span>
                <div className="fila-cuerpo">
                  <strong>{r.nombre}</strong>
                  <span>
                    {PERIODICIDAD[r.periodicidad] ?? r.periodicidad} · {r.destinatarios.join(', ')}
                    {r.ultimo_envio && ` · último envío ${fechaHora(r.ultimo_envio)}`}
                  </span>
                  {r.ultimo_error && <span className="error">{r.ultimo_error}</span>}
                </div>
                <label className="acciones">
                  <input
                    type="checkbox"
                    checked={r.activo}
                    aria-label={`${r.nombre} activo`}
                    onChange={(e) =>
                      guardar.mutate({
                        id: r.id,
                        nombre: r.nombre,
                        periodicidad: r.periodicidad,
                        destinatarios: r.destinatarios,
                        indicadores: r.indicadores,
                        ciudad: r.ciudad ?? undefined,
                        activo: e.target.checked,
                      })
                    }
                  />
                </label>
                <button className="btn btn-plano" type="button" onClick={() => setEditando(r)}>
                  Editar
                </button>
              </div>
            ))
          }
        </Consulta>
      </section>
      <EventosPasarela />
      {editando && <EditarReporte reporte={editando === 'nuevo' ? null : editando} onCerrar={() => setEditando(null)} />}
    </div>
  )
}

function EditarReporte({ reporte, onCerrar }: { reporte: ReporteRead | null; onCerrar: () => void }) {
  const guardar = useGuardarReporte()
  const definiciones = useDefiniciones()
  const [indicadores, setIndicadores] = useState<string[]>(reporte?.indicadores ?? [])

  return (
    <Modal
      abierto
      onCambio={(v) => !v && onCerrar()}
      titulo={reporte ? `Editar ${reporte.nombre}` : 'Nuevo reporte'}
      descripcion="Llega por correo con el período anterior en Excel. Sin indicadores elegidos, van todos."
      pie={
        <button className="btn btn-primario" type="submit" form="reporte" disabled={guardar.isPending}>
          Guardar
        </button>
      }
    >
      <form
        id="reporte"
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const d = new FormData(e.currentTarget)
          guardar.mutate(
            {
              id: reporte?.id,
              nombre: String(d.get('nombre')).trim(),
              periodicidad: String(d.get('periodicidad')),
              destinatarios: String(d.get('destinatarios'))
                .split(/[,\s]+/)
                .map((x) => x.trim())
                .filter(Boolean),
              indicadores,
              activo: reporte?.activo ?? true,
            },
            { onSuccess: onCerrar },
          )
        }}
      >
        <label className="campo">
          <span>Nombre</span>
          <input className="input" name="nombre" defaultValue={reporte?.nombre} required />
        </label>
        <label className="campo">
          <span>Periodicidad</span>
          <select className="input" name="periodicidad" defaultValue={reporte?.periodicidad ?? 'semanal'}>
            {Object.entries(PERIODICIDAD).map(([v, l]) => (
              <option key={v} value={v}>{l}</option>
            ))}
          </select>
        </label>
        <label className="campo ancho">
          <span>Destinatarios (correos separados por coma)</span>
          <input className="input" name="destinatarios" defaultValue={reporte?.destinatarios.join(', ')} required />
        </label>
        <fieldset className="ancho grupo-chips" style={{ border: 0, padding: 0, margin: 0 }}>
          <legend className="subtitulo">Indicadores</legend>
          {definiciones.data?.map((d) => (
            <button
              key={d.codigo}
              type="button"
              className="cupo"
              aria-pressed={indicadores.includes(d.codigo)}
              title={d.formula}
              onClick={() => setIndicadores((a) => (a.includes(d.codigo) ? a.filter((x) => x !== d.codigo) : [...a, d.codigo]))}
            >
              {d.nombre}
            </button>
          ))}
        </fieldset>
        {guardar.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(guardar.error, 'No fue posible guardar el reporte.')}
          </p>
        )}
      </form>
    </Modal>
  )
}

function EventosPasarela() {
  const [estado, setEstado] = useState('error')
  const eventos = useEventosPasarela(estado || undefined)
  const reprocesar = useReprocesarEvento()

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Eventos de la pasarela de pagos</h3>
        <select className="input" style={{ width: 'auto' }} value={estado} onChange={(e) => setEstado(e.target.value)} aria-label="Estado del evento">
          <option value="error">Con error</option>
          <option value="procesado">Procesados</option>
          <option value="">Todos</option>
        </select>
      </div>
      {reprocesar.isError && (
        <p className="error" role="alert">
          {mensajeError(reprocesar.error, 'No fue posible reprocesar.')}
        </p>
      )}
      <Consulta consulta={eventos} cargando="Cargando…" error="No fue posible cargar los eventos." vacio="Sin eventos en este estado." estaVacio={(d) => d.items.length === 0}>
        {(d) => (
          <div className="scroll-x">
            <table className="tabla">
              <thead>
                <tr>
                  <th>Recibido</th>
                  <th>Evento</th>
                  <th>Referencia</th>
                  <th>Estado</th>
                  <th><span className="sr-only">Acciones</span></th>
                </tr>
              </thead>
              <tbody>
                {d.items.map((ev) => (
                  <tr key={ev.id}>
                    <td className="numero">{fechaHora(ev.created_at)}</td>
                    <td>
                      {ev.proveedor} · {ev.tipo}
                    </td>
                    <td className="numero">{ev.referencia ?? '—'}</td>
                    <td>
                      {ev.estado}
                      {ev.error && <div className="error">{ev.error}</div>}
                    </td>
                    <td>
                      {ev.estado !== 'procesado' && (
                        <button className="btn btn-suave" type="button" disabled={reprocesar.isPending} onClick={() => reprocesar.mutate(ev.id)}>
                          Reprocesar
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Consulta>
    </section>
  )
}
