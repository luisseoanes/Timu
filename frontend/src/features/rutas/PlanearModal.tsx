import { useState } from 'react'

import { Modal } from '@/components/Modal'
import { useEquipo } from '@/features/auth'
import { useCiudades } from '@/features/catalogos'
import { mensajeError } from '@/lib/errores'
import { fechaLarga } from '@/lib/formato'

import { usePlanificacion, usePlanificar, type ResultadoPlanificacion } from './api'

const MOTIVOS_SIN_ASIGNAR: Record<string, string> = {
  sin_ubicacion: 'la familia no tiene ubicación',
  no_cabe_en_la_jornada: 'no cabe en la jornada',
}

/**
 * Planear las rutas de un día y una ciudad (6.7): el optimizador reparte los domicilios entre
 * quienes salen a campo. Corre en el worker, así que la ventana espera su resultado.
 */
export function PlanearModal({ dia, ciudadSugerida, onCerrar }: { dia: string; ciudadSugerida: string; onCerrar: () => void }) {
  const ciudades = useCiudades()
  const equipo = useEquipo()
  const planificar = usePlanificar()
  const plan = usePlanificacion(planificar.data?.id ?? null)
  const [elegida, setElegida] = useState(ciudadSugerida)
  const [elegidos, setElegidos] = useState<string[]>([])
  const activas = (ciudades.data ?? []).filter((c) => c.activa)
  const ciudad = elegida || activas[0]?.nombre || ''
  const campo = (equipo.data ?? []).filter((m) => m.rol === 'medico' || m.rol === 'operaciones')
  const resultado = plan.data?.resultado as ResultadoPlanificacion | undefined
  const sinRuta = resultado?.sin_asignar ?? []

  return (
    <Modal
      abierto
      onCambio={(v) => !v && onCerrar()}
      titulo="Planear rutas"
      descripcion={`Para el ${fechaLarga(dia)}. El optimizador reparte los domicilios del día entre quienes salen a campo.`}
      pie={
        !planificar.data ? (
          <button className="btn btn-primario" type="submit" form="planear-rutas" disabled={!ciudad || elegidos.length === 0 || planificar.isPending}>
            {planificar.isPending ? 'Enviando…' : 'Planear rutas'}
          </button>
        ) : (
          plan.data &&
          plan.data.estado !== 'pendiente' && (
            <button className="btn btn-secundario" type="button" onClick={onCerrar}>
              {plan.data.estado === 'lista' ? 'Ver las rutas' : 'Cerrar'}
            </button>
          )
        )
      }
    >
      {!planificar.data ? (
        <form
          id="planear-rutas"
          className="formulario"
          onSubmit={(e) => {
            e.preventDefault()
            planificar.mutate({ fecha: dia, ciudad, responsables: elegidos })
          }}
        >
          <label className="campo ancho">
            <span>Ciudad</span>
            <select className="input" value={ciudad} onChange={(e) => setElegida(e.target.value)} required>
              {activas.map((c) => (
                <option key={c.codigo} value={c.nombre}>
                  {c.nombre}
                </option>
              ))}
            </select>
          </label>
          <fieldset className="ancho">
            <legend>Quiénes salen a campo</legend>
            {campo.length === 0 && <p className="apagado">No hay médicos ni personal de operaciones activos. Créalos en Administración.</p>}
            {campo.map((m) => (
              <label key={m.id} className="acciones">
                <input
                  type="checkbox"
                  checked={elegidos.includes(m.id)}
                  onChange={(e) => setElegidos((a) => (e.target.checked ? [...a, m.id] : a.filter((x) => x !== m.id)))}
                />
                {m.nombre} <span className="apagado">({m.rol === 'medico' ? 'médico' : 'operaciones'})</span>
              </label>
            ))}
          </fieldset>
          {planificar.isError && (
            <p className="error ancho" role="alert">
              {mensajeError(planificar.error, 'No fue posible iniciar la planificación.')}
            </p>
          )}
        </form>
      ) : !plan.data || plan.data.estado === 'pendiente' ? (
        <div className="esqueleto" role="status">
          <span>Optimizando las rutas… toma unos segundos.</span>
          <span className="esqueleto-linea" aria-hidden="true" />
          <span className="esqueleto-linea" aria-hidden="true" />
        </div>
      ) : plan.data.estado === 'fallida' ? (
        <p className="aviso-error" role="alert">
          No fue posible planear: {plan.data.error}
        </p>
      ) : (
        <div className="pila" role="status">
          <p className="aviso-ok">
            {resultado?.rutas === 1 ? '1 ruta creada' : `${resultado?.rutas ?? 0} rutas creadas`} con{' '}
            {resultado?.asignados === 1 ? '1 servicio' : `${resultado?.asignados ?? 0} servicios`}.
          </p>
          {sinRuta.length > 0 && (
            <p className="aviso">
              {sinRuta.length === 1 ? '1 servicio quedó' : `${sinRuta.length} servicios quedaron`} sin ruta:{' '}
              {[...new Set(sinRuta.map((s) => MOTIVOS_SIN_ASIGNAR[s.motivo] ?? s.motivo))].join(', ')}. Siguen en «Por rutear».
            </p>
          )}
        </div>
      )}
    </Modal>
  )
}
