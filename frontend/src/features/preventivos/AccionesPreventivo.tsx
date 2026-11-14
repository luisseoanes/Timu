import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Modal } from '@/components/Modal'
import type { GestionarPreventivoProps } from '@/features/familias'
import { useDisponibilidad } from '@/features/servicios'
import { mensajeError } from '@/lib/errores'
import { fechaCompacta, fechaCortaConDia, hora, hoyISO } from '@/lib/formato'
import type { EventoBandeja, EventoRead } from '@/types'

import {
  useAgendarPreventivo,
  useAplicarPreventivo,
  useAutorizarVarios,
  useCancelarPreventivo,
  useBandejaPreventivos,
  type MedioAutorizacion,
} from './api'
import { pedido } from './preventivo'

// Mismo mapa que preventivos/service.py: TIPO_SERVICIO.
const TIPO_SERVICIO: Record<string, string> = {
  vacuna: 'vacunacion',
  desparasitacion_interna: 'desparasitacion',
  desparasitacion_externa: 'desparasitacion',
}

const MEDIOS: { valor: MedioAutorizacion; label: string }[] = [
  { valor: 'whatsapp', label: 'WhatsApp' },
  { valor: 'telefono', label: 'Teléfono' },
  { valor: 'presencial', label: 'Presencial' },
  { valor: 'portal', label: 'Portal' },
  { valor: 'formulario', label: 'Formulario' },
]

interface Pedido {
  id: string
  /** «Rocky · Antirrábica canina, refuerzo» (`pedido`) */
  titulo: string
  fecha: string
}

/** La familia autoriza (o no) de una vez lo que se le pidió. Llega todo marcado: quien la atiende
 * desmarca lo que la familia no autorizó. */
export function AutorizarModal({
  titular,
  pedidos,
  descripcion = 'Lo que la familia respondió. Al autorizar, la visita de lo ya agendado queda autorizada también.',
  onCerrar,
}: {
  titular: string
  pedidos: Pedido[]
  descripcion?: string
  onCerrar: () => void
}) {
  const [elegidos, setElegidos] = useState(() => new Set(pedidos.map((p) => p.id)))
  const [medio, setMedio] = useState<MedioAutorizacion>('whatsapp')
  const autorizar = useAutorizarVarios()
  const ids = pedidos.filter((p) => elegidos.has(p.id)).map((p) => p.id)

  function enviar(aprobado: boolean) {
    autorizar.mutate({ eventos: ids, medio, aprobado }, { onSuccess: onCerrar })
  }

  return (
    <Modal
      abierto
      onCambio={(v) => !v && onCerrar()}
      titulo={`Autorización de ${titular}`}
      descripcion={descripcion}
      pie={
        <>
          <button className="btn btn-plano btn-plano-peligro" type="button" disabled={!ids.length || autorizar.isPending} onClick={() => enviar(false)}>
            No autorizó
          </button>
          <button className="btn btn-primario" type="button" disabled={!ids.length || autorizar.isPending} onClick={() => enviar(true)}>
            {autorizar.isPending ? 'Registrando…' : ids.length === 1 ? 'La familia autorizó' : `La familia autorizó los ${ids.length}`}
          </button>
        </>
      }
    >
      <div className="formulario">
        <fieldset className="campo ancho preventivo-pedidos">
          <legend>Qué autorizó</legend>
          {pedidos.map((p) => (
            <label key={p.id} className="preventivo-pedido">
              <input
                type="checkbox"
                checked={elegidos.has(p.id)}
                onChange={(e) => {
                  const siguiente = new Set(elegidos)
                  if (e.target.checked) siguiente.add(p.id)
                  else siguiente.delete(p.id)
                  setElegidos(siguiente)
                }}
              />
              <span>
                {p.titulo} <span className="apagado numero">· {fechaCompacta(p.fecha)}</span>
              </span>
            </label>
          ))}
        </fieldset>
        <label className="campo ancho">
          <span>Por dónde respondió</span>
          <select className="input" value={medio} onChange={(e) => setMedio(e.target.value as MedioAutorizacion)}>
            {MEDIOS.map((m) => (
              <option key={m.valor} value={m.valor}>{m.label}</option>
            ))}
          </select>
        </label>
        <p className="campo-ayuda ancho">Si no autorizó, lo desmarcado sigue pendiente y lo marcado se cancela.</p>
        {autorizar.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(autorizar.error, 'No fue posible registrar la autorización.')}
          </p>
        )}
      </div>
    </Modal>
  )
}

/** Agendar la visita de un preventivo contra la disponibilidad real de su ciudad. */
export function AgendarModal({ evento, titulo, ciudad, onCerrar }: { evento: EventoRead; titulo: string; ciudad: string; onCerrar: () => void }) {
  const [dia, setDia] = useState(evento.fecha_programada < hoyISO() ? hoyISO() : evento.fecha_programada)
  const [inicio, setInicio] = useState('')
  const agendar = useAgendarPreventivo()
  const cupos = useDisponibilidad({ fecha: dia, ciudad, tipo_codigo: TIPO_SERVICIO[evento.tipo] ?? 'vacunacion' })
  return (
    <Modal
      abierto
      onCambio={(v) => !v && onCerrar()}
      titulo={`Agendar ${titulo}`}
      descripcion={`${evento.fecha_programada < hoyISO() ? 'Tocaba' : 'Toca'} el ${fechaCortaConDia(evento.fecha_programada)}. La visita es en casa de la familia, en ${ciudad}.`}
      pie={
        <button className="btn btn-primario" type="button" disabled={!inicio || agendar.isPending} onClick={() => agendar.mutate({ id: evento.id, inicio }, { onSuccess: onCerrar })}>
          {agendar.isPending ? 'Agendando…' : inicio ? `Agendar a las ${hora(inicio)}` : 'Elige una franja'}
        </button>
      }
    >
      <div className="formulario">
        <label className="campo">
          <span>Día de la visita</span>
          <input className="input" type="date" min={hoyISO()} value={dia} onChange={(e) => { setDia(e.target.value); setInicio('') }} />
        </label>
        <div className="ancho">
          {cupos.isPending ? (
            <p className="apagado" role="status">Buscando franjas…</p>
          ) : cupos.isError ? (
            <p className="error" role="alert">{mensajeError(cupos.error, 'No fue posible consultar las franjas.')}</p>
          ) : cupos.data?.length === 0 ? (
            <p className="apagado">No hay franjas ese día. Prueba con otro.</p>
          ) : (
            <div className="cupos" role="group" aria-label="Franjas disponibles">
              {cupos.data?.map((c) => (
                <button key={c.inicio} type="button" className="cupo" aria-pressed={inicio === c.inicio} disabled={c.disponibles === 0} onClick={() => setInicio(c.inicio)}>
                  {hora(c.inicio)}
                </button>
              ))}
            </div>
          )}
        </div>
        {agendar.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(agendar.error, 'No fue posible agendar la visita.')}
          </p>
        )}
      </div>
    </Modal>
  )
}

/** Lo aplicado sin visita (en la clínica o fuera): con visita, lo registra el servicio al completarse. */
export function AplicarModal({ evento, titulo, onCerrar }: { evento: EventoRead; titulo: string; onCerrar: () => void }) {
  const aplicar = useAplicarPreventivo()
  return (
    <Modal
      abierto
      onCambio={(v) => !v && onCerrar()}
      titulo={`Registrar aplicación de ${titulo}`}
      descripcion="Para lo que se aplicó sin visita. Con visita, se registra solo al completar su servicio."
      pie={
        <button className="btn btn-primario" type="submit" form="aplicar-preventivo" disabled={aplicar.isPending}>
          {aplicar.isPending ? 'Registrando…' : 'Registrar aplicación'}
        </button>
      }
    >
      <form
        id="aplicar-preventivo"
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const d = new FormData(e.currentTarget)
          aplicar.mutate(
            {
              id: evento.id,
              fecha: String(d.get('fecha')),
              producto: String(d.get('producto')).trim(),
              lote: String(d.get('lote') ?? '').trim() || undefined,
              peso_kg: d.get('peso_kg') ? Number(d.get('peso_kg')) : undefined,
            },
            { onSuccess: onCerrar },
          )
        }}
      >
        <label className="campo">
          <span>Fecha de aplicación</span>
          <input className="input" name="fecha" type="date" max={hoyISO()} defaultValue={hoyISO()} required />
        </label>
        <label className="campo">
          <span>Producto</span>
          <input className="input" name="producto" required minLength={2} />
        </label>
        <label className="campo">
          <span>Lote</span>
          <input className="input" name="lote" />
        </label>
        {/* 6.8 «Registrar peso cuando sea pertinente»: el de hoy, que va al carnet. */}
        <label className="campo">
          <span>Peso (kg, opcional)</span>
          <input className="input" name="peso_kg" type="number" min={0.1} max={149} step={0.1} inputMode="decimal" />
        </label>
        {aplicar.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(aplicar.error, 'No fue posible registrar la aplicación.')}
          </p>
        )}
      </form>
    </Modal>
  )
}

export function CancelarModal({ evento, titulo, onCerrar }: { evento: EventoRead; titulo: string; onCerrar: () => void }) {
  const cancelar = useCancelarPreventivo()
  return (
    <Modal
      abierto
      onCambio={(v) => !v && onCerrar()}
      titulo={`Cancelar ${titulo}`}
      descripcion="Sale del calendario y del carnet como pendiente. No se deshace."
      pie={
        <button className="btn btn-peligro" type="submit" form="cancelar-preventivo" disabled={cancelar.isPending}>
          {cancelar.isPending ? 'Cancelando…' : 'Cancelar preventivo'}
        </button>
      }
    >
      <form
        id="cancelar-preventivo"
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const motivo = String(new FormData(e.currentTarget).get('motivo')).trim()
          cancelar.mutate({ id: evento.id, motivo }, { onSuccess: onCerrar })
        }}
      >
        <label className="campo ancho">
          <span>Motivo</span>
          <textarea className="input" name="motivo" rows={2} required minLength={3} placeholder="Por ejemplo: se lo aplicaron en otra clínica" />
        </label>
        {cancelar.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(cancelar.error, 'No fue posible cancelar el preventivo.')}
          </p>
        )}
      </form>
    </Modal>
  )
}

/** Gestionar los preventivos de una estación desde fuera de Preventivos (la línea de una familia):
 * abre el paso que les toca. Lo que falte por autorizar se pide de una vez, como en la bandeja; si
 * todo está autorizado, se agenda el primero que no tenga visita. Lee la bandeja de esa familia, que
 * trae el nombre de cada esquema («Antirrábica», no «Vacuna»). Lo monta `App.tsx` en la ficha de
 * Familias, que no importa este dominio. */
export function GestionarPreventivo({ familiaId, eventoIds, onCerrar }: GestionarPreventivoProps) {
  const bandeja = useBandejaPreventivos({ vista: 'todos', familia_id: familiaId })
  const grupo = bandeja.data?.items[0]
  const deLaEstacion = (grupo?.eventos ?? []).filter((e) => eventoIds.includes(e.id))

  if (bandeja.isPending || bandeja.isError) {
    return (
      <Modal abierto onCambio={(v) => !v && onCerrar()} titulo="Preventivos">
        {bandeja.isError ? (
          <p className="error" role="alert">No fue posible cargar los preventivos.</p>
        ) : (
          <p className="apagado" role="status">Cargando los preventivos…</p>
        )}
      </Modal>
    )
  }
  if (!grupo || deLaEstacion.length === 0) {
    return (
      <Modal abierto onCambio={(v) => !v && onCerrar()} titulo="Preventivos">
        <p>{eventoIds.length === 1 ? 'Este preventivo ya no está pendiente: se aplicó o se canceló.' : 'Estos preventivos ya no están pendientes: se aplicaron o se cancelaron.'}</p>
      </Modal>
    )
  }
  const titulo = (e: EventoBandeja) => `${e.nombre} de ${e.mascota_nombre}`
  const porAutorizar = deLaEstacion.filter((e) => e.siguiente === 'autorizar')
  if (porAutorizar.length > 0) {
    return (
      <AutorizarModal
        titular={grupo.titular_nombre}
        pedidos={porAutorizar.map((e) => ({ id: e.id, titulo: pedido(e), fecha: e.fecha_programada }))}
        descripcion="Antes de agendar la visita, la familia tiene que autorizarlo. Después, se agenda desde la misma estación."
        onCerrar={onCerrar}
      />
    )
  }
  const sinVisita = deLaEstacion.find((e) => e.siguiente === 'agendar')
  if (sinVisita) return <AgendarModal evento={sinVisita} titulo={titulo(sinVisita)} ciudad={grupo.ciudad} onCerrar={onCerrar} />
  const [conVisita] = deLaEstacion
  return (
    <Modal abierto onCambio={(v) => !v && onCerrar()} titulo={titulo(conVisita)} descripcion="Ya tiene su visita agendada. Al completarla, el preventivo queda aplicado.">
      <Link className="btn btn-secundario" to={`/servicios/${conVisita.servicio_id}`}>
        Abrir la visita
      </Link>
    </Modal>
  )
}
