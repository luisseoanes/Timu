import { useState } from 'react'

import { Modal } from '@/components/Modal'
import { mensajeError } from '@/lib/errores'
import { fechaCortaConDia, fechaHora, hora, hoyISO } from '@/lib/formato'

import { useAgendarPortal, useDisponibilidadPortal, useMiFamilia, useMiPlan, useOrientacionVirtual, usePreventivosPorAgendar } from './api'

// Agendar una cita y pedir orientación: se abren desde el inicio, la ficha de cada peludo y
// las citas.

export function SelectorCupo({ tipo, valor, onCambio }: { tipo: string; valor: string; onCambio: (inicio: string) => void }) {
  const [dia, setDia] = useState(hoyISO())
  const cupos = useDisponibilidadPortal(dia, tipo)
  return (
    <>
      <label className="campo">
        <span>Día</span>
        <input className="input" type="date" min={hoyISO()} value={dia} onChange={(e) => { setDia(e.target.value); onCambio('') }} />
      </label>
      <div className="ancho">
        {!tipo ? (
          <p className="apagado">Elige el tipo de visita para ver los horarios.</p>
        ) : cupos.isPending ? (
          <p className="apagado">Buscando horarios…</p>
        ) : cupos.isError ? (
          <p className="error" role="alert">
            {mensajeError(cupos.error, 'No pudimos consultar la agenda.')}
          </p>
        ) : cupos.data.filter((c) => c.disponibles > 0).length === 0 ? (
          <p className="apagado">No hay horarios ese día. Prueba otra fecha.</p>
        ) : (
          <div className="cupos" role="group" aria-label="Horarios disponibles">
            {cupos.data
              .filter((c) => c.disponibles > 0)
              .map((c) => (
                <button key={c.inicio} type="button" className="cupo" aria-pressed={valor === c.inicio} onClick={() => onCambio(c.inicio)}>
                  {hora(c.inicio)}
                </button>
              ))}
          </div>
        )}
      </div>
    </>
  )
}

/** Agendar una cita: lo que la familia puede agendar sola lo dice el plan (`tipos_agendables`),
 * en casa o en la clínica. Desde la ficha de un peludo llega con él elegido. */
export function AgendarModal({ abierto, onCerrar, mascotaId }: { abierto: boolean; onCerrar: () => void; mascotaId?: string }) {
  const familia = useMiFamilia()
  const plan = useMiPlan()
  const agendar = useAgendarPortal()
  const [tipo, setTipo] = useState('')
  const [inicio, setInicio] = useState('')
  const [mascota, setMascota] = useState(mascotaId ?? '')
  const [preventivo, setPreventivo] = useState('')
  const tipos = plan.data?.tipos_agendables ?? []
  const elegido = tipos.find((t) => t.codigo === tipo)
  const activas = familia.data?.mascotas?.filter((m) => m.activa) ?? []
  const mascotaElegida = mascota || activas[0]?.id || ''
  // Una visita preventiva es la de un preventivo concreto (DEU-3): al completarse, lo aplica.
  const esPreventivo = elegido?.modalidad === 'preventivo'
  const porAgendar = usePreventivosPorAgendar(abierto && esPreventivo)
  const deEsta = porAgendar.data?.filter((p) => p.mascota_id === mascotaElegida && p.tipo_servicio_codigo === tipo) ?? []
  const nombreMascota = activas.find((m) => m.id === mascotaElegida)?.nombre ?? 'Tu peludo'

  function cerrar() {
    agendar.reset()
    setTipo('')
    setInicio('')
    setPreventivo('')
    onCerrar()
  }

  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => !v && cerrar()}
      titulo="Agendar una cita"
      descripcion="Te confirmamos por WhatsApp. Algunos servicios requieren autorización antes de confirmarse."
      pie={
        !agendar.isSuccess && (
          <button
            className="btn btn-primario"
            type="submit"
            form="agendar-portal"
            disabled={!inicio || (esPreventivo && !preventivo) || agendar.isPending}
          >
            Agendar
          </button>
        )
      }
    >
      {agendar.isSuccess ? (
        <p className="aviso-ok" role="status">
          ¡Listo! Tu cita quedó para el {fechaHora(agendar.data.programado_para)}.
        </p>
      ) : (
        <form
          id="agendar-portal"
          className="formulario"
          onSubmit={(e) => {
            e.preventDefault()
            const d = new FormData(e.currentTarget)
            agendar.mutate({
              mascota_id: mascotaElegida,
              tipo_codigo: tipo,
              inicio,
              observaciones: String(d.get('observaciones') ?? '').trim() || undefined,
              preventivo_id: esPreventivo ? preventivo : undefined,
            })
          }}
        >
          <label className="campo">
            <span>Mascota</span>
            <select
              className="input"
              name="mascota_id"
              required
              value={mascotaElegida}
              onChange={(e) => {
                setMascota(e.target.value)
                setPreventivo('')
              }}
            >
              {activas.map((m) => (
                <option key={m.id} value={m.id}>{m.nombre}</option>
              ))}
            </select>
          </label>
          <label className="campo">
            <span>Qué necesitas</span>
            <select className="input" value={tipo} onChange={(e) => { setTipo(e.target.value); setInicio(''); setPreventivo('') }} required>
              <option value="" disabled>Elige</option>
              {tipos.map((t) => (
                <option key={t.codigo} value={t.codigo}>
                  {t.nombre}
                  {t.modalidad === 'clinico' ? ' · en la clínica' : ' · en casa'}
                </option>
              ))}
            </select>
          </label>
          {elegido?.modalidad === 'clinico' && (
            <p className="campo-ayuda ancho">Es en la clínica TIMU, no en tu casa.</p>
          )}
          {esPreventivo &&
            (porAgendar.isPending ? (
              <p className="campo-ayuda ancho">Buscando sus preventivos…</p>
            ) : deEsta.length === 0 ? (
              <p className="campo-ayuda ancho">{nombreMascota} no tiene preventivos de este tipo por agendar.</p>
            ) : (
              <label className="campo ancho">
                <span>Cuál</span>
                <select className="input" value={preventivo} onChange={(e) => setPreventivo(e.target.value)} required>
                  <option value="" disabled>Elige</option>
                  {deEsta.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.nombre} · {p.vencido ? `tocaba el ${fechaCortaConDia(p.fecha_programada)}` : `toca el ${fechaCortaConDia(p.fecha_programada)}`}
                    </option>
                  ))}
                </select>
              </label>
            ))}
          <SelectorCupo tipo={tipo} valor={inicio} onCambio={setInicio} />
          <label className="campo ancho">
            <span>¿Algo que debamos saber? (opcional)</span>
            <textarea className="input" name="observaciones" rows={2} />
          </label>
          {agendar.isError && (
            <p className="error ancho" role="alert">
              {mensajeError(agendar.error, 'No pudimos agendar la cita.')}
            </p>
          )}
        </form>
      )}
    </Modal>
  )
}

export function OrientacionModal({ abierto, onCerrar }: { abierto: boolean; onCerrar: () => void }) {
  const familia = useMiFamilia()
  const pedir = useOrientacionVirtual()
  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          pedir.reset()
          onCerrar()
        }
      }}
      titulo="Orientación virtual"
      descripcion="Un médico veterinario te responde por WhatsApp. Si es una urgencia, llama a la línea de emergencias."
      pie={
        !pedir.isSuccess && (
          <button className="btn btn-primario" type="submit" form="orientacion" disabled={pedir.isPending}>
            Enviar consulta
          </button>
        )
      }
    >
      {pedir.isSuccess ? (
        <p className="aviso-ok" role="status">
          Recibimos tu consulta. Te escribimos pronto por WhatsApp.
        </p>
      ) : (
        <form
          id="orientacion"
          className="formulario"
          onSubmit={(e) => {
            e.preventDefault()
            const d = new FormData(e.currentTarget)
            pedir.mutate({ mascota_id: String(d.get('mascota_id')), motivo: String(d.get('motivo')).trim() })
          }}
        >
          <label className="campo ancho">
            <span>¿Sobre quién es la consulta?</span>
            <select className="input" name="mascota_id" required>
              {familia.data?.mascotas
                ?.filter((m) => m.activa)
                .map((m) => (
                  <option key={m.id} value={m.id}>{m.nombre}</option>
                ))}
            </select>
          </label>
          <label className="campo ancho">
            <span>Cuéntanos qué pasa</span>
            <textarea className="input" name="motivo" rows={4} required minLength={5} />
          </label>
          {pedir.isError && (
            <p className="error ancho" role="alert">
              {mensajeError(pedir.error, 'No pudimos enviar tu consulta.')}
            </p>
          )}
        </form>
      )}
    </Modal>
  )
}
