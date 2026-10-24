import { useState } from 'react'

import { Modal } from '@/components/Modal'
import { mensajeError } from '@/lib/errores'
import type { EstadoAfiliacion, FamiliaRead } from '@/types'

import { useCambiarEstado, useDarDeBaja, useHabilitarPortal } from './api'

// Estados que se fijan a mano. `en_mora` lo deriva cartera y no se ofrece.
const ESTADOS_MANUALES: { valor: EstadoAfiliacion; label: string }[] = [
  { valor: 'prospecto', label: 'Prospecto' },
  { valor: 'activa', label: 'Activa' },
  { valor: 'congelada', label: 'Congelada' },
  { valor: 'cancelada', label: 'Cancelada' },
]

/** Acciones de afiliación: sólo las ve quien puede ejecutarlas (admin y comercial). */
export function AccionesFamilia({ familia }: { familia: FamiliaRead }) {
  const [modal, setModal] = useState<'estado' | 'baja' | null>(null)
  const portal = useHabilitarPortal(familia.id)
  const dadaDeBaja = Boolean(familia.dada_de_baja_en)

  return (
    <div className="acciones" style={{ marginLeft: 'auto' }}>
      {!familia.usuario_portal_id && !dadaDeBaja && (
        <button className="btn btn-suave" type="button" disabled={portal.isPending} onClick={() => portal.mutate()}>
          {portal.isPending ? 'Habilitando…' : 'Habilitar portal'}
        </button>
      )}
      {!dadaDeBaja && (
        <>
          <button className="btn btn-suave" type="button" onClick={() => setModal('estado')}>
            Cambiar estado
          </button>
          <button className="btn btn-plano" type="button" onClick={() => setModal('baja')}>
            Dar de baja
          </button>
        </>
      )}
      {portal.isError && (
        <p className="error" role="alert">
          {mensajeError(portal.error, 'No fue posible habilitar el portal.')}
        </p>
      )}
      {portal.isSuccess && (
        <p className="exito" role="status">
          Portal habilitado: la familia recibirá el enlace de activación.
        </p>
      )}
      <CambiarEstadoModal familia={familia} abierto={modal === 'estado'} onCerrar={() => setModal(null)} />
      <BajaModal familia={familia} abierto={modal === 'baja'} onCerrar={() => setModal(null)} />
    </div>
  )
}

function CambiarEstadoModal({ familia, abierto, onCerrar }: { familia: FamiliaRead; abierto: boolean; onCerrar: () => void }) {
  const cambiar = useCambiarEstado(familia.id)

  function guardar(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const d = new FormData(e.currentTarget)
    const motivo = String(d.get('motivo') ?? '').trim()
    cambiar.mutate(
      { estado: d.get('estado') as EstadoAfiliacion, motivo: motivo || undefined },
      { onSuccess: onCerrar },
    )
  }

  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          cambiar.reset()
          onCerrar()
        }
      }}
      titulo="Cambiar estado de afiliación"
      descripcion="El cambio queda en el historial de la familia con el motivo."
      pie={
        <button className="btn btn-primario" type="submit" form="cambiar-estado" disabled={cambiar.isPending}>
          {cambiar.isPending ? 'Guardando…' : 'Cambiar estado'}
        </button>
      }
    >
      <form id="cambiar-estado" className="formulario" onSubmit={guardar}>
        <label className="campo ancho">
          <span>Nuevo estado</span>
          <select className="input" name="estado" defaultValue={familia.estado === 'en_mora' ? 'activa' : familia.estado}>
            {ESTADOS_MANUALES.map((e) => (
              <option key={e.valor} value={e.valor}>{e.label}</option>
            ))}
          </select>
        </label>
        <label className="campo ancho">
          <span>Motivo</span>
          <textarea className="input" name="motivo" rows={3} />
        </label>
        {cambiar.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(cambiar.error, 'No fue posible cambiar el estado.')}
          </p>
        )}
      </form>
    </Modal>
  )
}

function BajaModal({ familia, abierto, onCerrar }: { familia: FamiliaRead; abierto: boolean; onCerrar: () => void }) {
  const baja = useDarDeBaja(familia.id)

  function guardar(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const motivo = String(new FormData(e.currentTarget).get('motivo') ?? '').trim()
    baja.mutate(motivo, { onSuccess: onCerrar })
  }

  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          baja.reset()
          onCerrar()
        }
      }}
      titulo="Dar de baja a la familia"
      descripcion="La familia sale de los listados y deja de recibir cobros y servicios. Sus datos y su historial se conservan."
      pie={
        <button className="btn btn-primario" type="submit" form="baja-familia" disabled={baja.isPending}>
          {baja.isPending ? 'Guardando…' : 'Confirmar baja'}
        </button>
      }
    >
      <form id="baja-familia" className="formulario" onSubmit={guardar}>
        <label className="campo ancho">
          <span>Motivo de la baja</span>
          <textarea className="input" name="motivo" rows={3} required minLength={3} />
        </label>
        {baja.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(baja.error, 'No fue posible dar de baja a la familia.')}
          </p>
        )}
      </form>
    </Modal>
  )
}
