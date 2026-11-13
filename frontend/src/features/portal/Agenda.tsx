import { useState } from 'react'

import { Modal } from '@/components/Modal'
import { useTiposServicio } from '@/features/catalogos'
import { mensajeError } from '@/lib/errores'
import { fechaHora, hora, hoyISO } from '@/lib/formato'

import { useAgendarPortal, useDisponibilidadPortal, useMiFamilia, useOrientacionVirtual } from './api'

// Agendar una visita y pedir orientación: se abren desde el inicio, la ficha de cada peludo y
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

/** Agendar una visita en casa. Desde la ficha de un peludo llega con él elegido. */
export function AgendarModal({ abierto, onCerrar, mascotaId }: { abierto: boolean; onCerrar: () => void; mascotaId?: string }) {
  const familia = useMiFamilia()
  const tipos = useTiposServicio()
  const agendar = useAgendarPortal()
  const [tipo, setTipo] = useState('')
  const [inicio, setInicio] = useState('')
  const enCasa = tipos.data?.filter((t) => t.activo && (t.modalidad === 'domiciliario' || t.modalidad === 'preventivo')) ?? []

  function cerrar() {
    agendar.reset()
    setTipo('')
    setInicio('')
    onCerrar()
  }

  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => !v && cerrar()}
      titulo="Agendar una visita"
      descripcion="Te confirmamos por WhatsApp. Algunos servicios requieren autorización antes de confirmarse."
      pie={
        !agendar.isSuccess && (
          <button className="btn btn-primario" type="submit" form="agendar-portal" disabled={!inicio || agendar.isPending}>
            Agendar
          </button>
        )
      }
    >
      {agendar.isSuccess ? (
        <p className="aviso-ok" role="status">
          ¡Listo! Tu visita quedó para el {fechaHora(agendar.data.programado_para)}.
        </p>
      ) : (
        <form
          id="agendar-portal"
          className="formulario"
          onSubmit={(e) => {
            e.preventDefault()
            const d = new FormData(e.currentTarget)
            agendar.mutate({
              mascota_id: String(d.get('mascota_id')),
              tipo_codigo: tipo,
              inicio,
              observaciones: String(d.get('observaciones') ?? '').trim() || undefined,
            })
          }}
        >
          <label className="campo">
            <span>Mascota</span>
            <select className="input" name="mascota_id" required defaultValue={mascotaId}>
              {familia.data?.mascotas
                ?.filter((m) => m.activa)
                .map((m) => (
                  <option key={m.id} value={m.id}>{m.nombre}</option>
                ))}
            </select>
          </label>
          <label className="campo">
            <span>Tipo de visita</span>
            <select className="input" value={tipo} onChange={(e) => { setTipo(e.target.value); setInicio('') }} required>
              <option value="" disabled>Elige</option>
              {enCasa.map((t) => (
                <option key={t.codigo} value={t.codigo}>{t.nombre}</option>
              ))}
            </select>
          </label>
          <SelectorCupo tipo={tipo} valor={inicio} onCambio={setInicio} />
          <label className="campo ancho">
            <span>¿Algo que debamos saber? (opcional)</span>
            <textarea className="input" name="observaciones" rows={2} />
          </label>
          {agendar.isError && (
            <p className="error ancho" role="alert">
              {mensajeError(agendar.error, 'No pudimos agendar la visita.')}
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
