import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { Modal } from '@/components/Modal'
import { useTiposServicio } from '@/features/catalogos/api'
import { SelectorFamilia } from '@/features/familias/SelectorFamilia'
import { mensajeError } from '@/lib/errores'
import { hora, hoyISO } from '@/lib/formato'
import type { FamiliaRead } from '@/types'

import { useCrearServicio, useDisponibilidad, useElegibilidad } from './api'

/**
 * Agendar un servicio: familia → mascota → tipo → día → franja con cupo. Antes de
 * guardar se muestra si el plan de la familia lo cubre (elegibilidad, 6.5).
 */
export function NuevoServicioModal({
  abierto,
  onCambio,
  familiaInicial = null,
}: {
  abierto: boolean
  onCambio: (v: boolean) => void
  familiaInicial?: FamiliaRead | null
}) {
  const navegar = useNavigate()
  const [familia, setFamilia] = useState<FamiliaRead | null>(familiaInicial)
  const [mascotaId, setMascotaId] = useState('')
  const [tipo, setTipo] = useState('')
  const [dia, setDia] = useState(hoyISO())
  const [inicio, setInicio] = useState('')
  const [observaciones, setObservaciones] = useState('')
  const tipos = useTiposServicio()
  const crear = useCrearServicio()

  const elegibilidad = useElegibilidad(
    familia && tipo ? { familia_id: familia.id, tipo_codigo: tipo, mascota_id: mascotaId || undefined } : null,
  )
  const cupos = useDisponibilidad(familia && tipo ? { fecha: dia, ciudad: familia.ciudad, tipo_codigo: tipo } : null)
  const mascotas = familia?.mascotas?.filter((m) => m.activa) ?? []

  function cerrar(v: boolean) {
    if (!v) {
      crear.reset()
      setInicio('')
    }
    onCambio(v)
  }

  function guardar(e: React.FormEvent) {
    e.preventDefault()
    if (!familia || !inicio) return
    crear.mutate(
      {
        familia_id: familia.id,
        mascota_id: mascotaId || undefined,
        tipo_codigo: tipo,
        inicio,
        observaciones: observaciones.trim() || undefined,
      },
      { onSuccess: (s) => navegar(`/servicios/${s.id}`) },
    )
  }

  return (
    <Modal
      abierto={abierto}
      onCambio={cerrar}
      titulo="Agendar servicio"
      descripcion="Elige la familia, la mascota y una franja con cupo en su ciudad."
      pie={
        <button
          className="btn btn-primario"
          type="submit"
          form="nuevo-servicio"
          disabled={!familia || !tipo || !inicio || crear.isPending}
        >
          {crear.isPending ? 'Agendando…' : 'Agendar'}
        </button>
      }
    >
      <form id="nuevo-servicio" className="formulario" onSubmit={guardar}>
        <div className="ancho">
          <SelectorFamilia
            valor={familia}
            onCambio={(f) => {
              setFamilia(f)
              setMascotaId('')
              setInicio('')
            }}
          />
        </div>
        <label className="campo">
          <span>Mascota</span>
          <select className="input" value={mascotaId} onChange={(e) => setMascotaId(e.target.value)} disabled={!familia}>
            <option value="">Toda la familia</option>
            {mascotas.map((m) => (
              <option key={m.id} value={m.id}>{m.nombre}</option>
            ))}
          </select>
        </label>
        <label className="campo">
          <span>Tipo de servicio</span>
          <select
            className="input"
            value={tipo}
            onChange={(e) => {
              setTipo(e.target.value)
              setInicio('')
            }}
            required
          >
            <option value="" disabled>
              {tipos.isPending ? 'Cargando…' : 'Selecciona el tipo'}
            </option>
            {tipos.data
              ?.filter((t) => t.activo)
              .map((t) => (
                <option key={t.codigo} value={t.codigo}>
                  {t.nombre} · {t.duracion_min} min
                </option>
              ))}
          </select>
        </label>

        {elegibilidad.data && (
          <p className={`ancho ${elegibilidad.data.elegible ? 'aviso-ok' : 'aviso-error'}`} role="status">
            {elegibilidad.data.elegible
              ? 'El plan de la familia cubre este servicio.'
              : `No está cubierto: ${elegibilidad.data.motivos.join(' ')}`}
          </p>
        )}

        <label className="campo">
          <span>Día</span>
          <input
            className="input"
            type="date"
            min={hoyISO()}
            value={dia}
            onChange={(e) => {
              setDia(e.target.value)
              setInicio('')
            }}
            required
          />
        </label>

        <fieldset className="ancho">
          <legend className="subtitulo">Franja</legend>
          {!familia || !tipo ? (
            <p className="apagado">Elige la familia y el tipo para ver los cupos.</p>
          ) : cupos.isPending ? (
            <p className="apagado">Buscando cupos…</p>
          ) : cupos.isError ? (
            <p className="error" role="alert">
              {mensajeError(cupos.error, 'No fue posible consultar la agenda.')}
            </p>
          ) : cupos.data.length === 0 ? (
            <p className="apagado">No hay franjas en {familia.ciudad} ese día. Prueba otra fecha.</p>
          ) : (
            <div className="cupos">
              {cupos.data.map((c) => (
                <button
                  key={c.inicio}
                  type="button"
                  className="cupo"
                  aria-pressed={inicio === c.inicio}
                  disabled={c.disponibles === 0}
                  onClick={() => setInicio(c.inicio)}
                  title={`${c.disponibles} cupos`}
                >
                  {hora(c.inicio)} – {hora(c.fin)}
                </button>
              ))}
            </div>
          )}
        </fieldset>

        <label className="campo ancho">
          <span>Observaciones (opcional)</span>
          <textarea className="input" rows={2} value={observaciones} onChange={(e) => setObservaciones(e.target.value)} />
        </label>

        {crear.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(crear.error, 'No fue posible agendar el servicio.')}
          </p>
        )}
      </form>
    </Modal>
  )
}
