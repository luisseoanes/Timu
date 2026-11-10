import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Modal } from '@/components/Modal'
import { mensajeError } from '@/lib/errores'
import { mesEnCurso } from '@/lib/formato'
import type { FamiliaRead, MascotaRead } from '@/types'

import {
  useActualizarMascota,
  useEstadoCuenta,
  useResumenServicios,
  useSubirFotoMascota,
  type CambiosMascota,
} from './api'
import { CamposMascota } from './CamposMascota'
import { leerCamposMascota } from './mascota'

/** Igual que el backend: JPG, PNG o WEBP de hasta 5 MB. */
const FORMATOS_FOTO = 'image/jpeg,image/png,image/webp'
const MAX_FOTO = 5 * 1024 * 1024

/**
 * 6.1 Ficha de una mascota en el panel: foto, datos editables, el plan que tiene, sus
 * servicios del mes y los enlaces a su historia clínica y a su carnet preventivo.
 */
export function FichaMascotaModal({
  familia,
  mascota,
  nombreEspecie,
  onCerrar,
}: {
  familia: FamiliaRead
  mascota: MascotaRead | null
  nombreEspecie: (codigo: string) => string
  onCerrar: () => void
}) {
  const actualizar = useActualizarMascota()
  const editable = Boolean(mascota?.activa) && !familia.dada_de_baja_en

  function guardar(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!mascota) return
    const d = new FormData(e.currentTarget)
    const raza = String(d.get('raza') ?? '').trim()
    const sexo = String(d.get('sexo') ?? '')
    const cambios: CambiosMascota = {
      nombre: String(d.get('nombre') ?? '').trim(),
      raza: raza || null,
      ...(sexo ? { sexo: sexo as 'macho' | 'hembra' } : {}),
      ...leerCamposMascota(d),
    }
    actualizar.mutate({ id: mascota.id, ...cambios })
  }

  return (
    <Modal
      abierto={mascota !== null}
      onCambio={(v) => {
        if (!v) {
          actualizar.reset()
          onCerrar()
        }
      }}
      titulo={mascota?.nombre ?? 'Mascota'}
      descripcion={mascota ? `${nombreEspecie(mascota.especie)}${mascota.activa ? '' : ' · de baja'}` : undefined}
      pie={
        editable ? (
          <button className="btn btn-primario" type="submit" form="ficha-mascota" disabled={actualizar.isPending}>
            {actualizar.isPending ? 'Guardando…' : 'Guardar cambios'}
          </button>
        ) : undefined
      }
    >
      {mascota && (
        <div className="pila">
          <FotoMascota mascota={mascota} editable={editable} />
          <PlanYServicios familiaId={familia.id} mascotaId={mascota.id} />
          <div className="acciones">
            <Link to={`/clinica/mascotas/${mascota.id}`} className="btn btn-suave">
              Historia clínica
            </Link>
            <Link to={`/preventivos?mascota=${mascota.id}`} className="btn btn-suave">
              Carnet preventivo
            </Link>
          </div>
          <form id="ficha-mascota" key={mascota.id} className="formulario" onSubmit={guardar}>
            <fieldset className="ancho formulario" disabled={!editable}>
              <legend className="ancho">Datos</legend>
              <label className="campo">
                <span>Nombre</span>
                <input className="input" name="nombre" defaultValue={mascota.nombre} required maxLength={120} />
              </label>
              <label className="campo">
                <span>Raza (opcional)</span>
                <input className="input" name="raza" defaultValue={mascota.raza ?? ''} maxLength={80} />
              </label>
              <label className="campo">
                <span>Sexo</span>
                <select className="input" name="sexo" defaultValue={mascota.sexo ?? ''}>
                  <option value="">Sin dato</option>
                  <option value="hembra">Hembra</option>
                  <option value="macho">Macho</option>
                </select>
              </label>
              <CamposMascota valores={mascota} />
            </fieldset>
            {actualizar.isSuccess && (
              <p className="ancho apagado" role="status">
                Cambios guardados.
              </p>
            )}
            {actualizar.isError && (
              <p className="error ancho" role="alert">
                {mensajeError(actualizar.error, 'No fue posible guardar los cambios.')}
              </p>
            )}
          </form>
        </div>
      )}
    </Modal>
  )
}

function FotoMascota({ mascota, editable }: { mascota: MascotaRead; editable: boolean }) {
  const subir = useSubirFotoMascota()
  const [aviso, setAviso] = useState<string | null>(null)

  function elegir(e: React.ChangeEvent<HTMLInputElement>) {
    const foto = e.target.files?.[0]
    e.target.value = ''
    if (!foto) return
    subir.reset()
    if (foto.size > MAX_FOTO) {
      setAviso('La foto pesa más de 5 MB. Elige una más liviana.')
      return
    }
    setAviso(null)
    subir.mutate({ id: mascota.id, foto })
  }

  return (
    <div className="mascota-cabeza">
      {mascota.foto_url ? (
        <img className="foto-mascota" src={mascota.foto_url} alt={`Foto de ${mascota.nombre}`} />
      ) : (
        <div className="foto-mascota" aria-hidden="true">
          Sin foto
        </div>
      )}
      {editable && (
        <label className="btn btn-suave">
          {subir.isPending ? 'Subiendo…' : mascota.foto_url ? 'Cambiar foto' : 'Subir foto'}
          <input className="sr-only" type="file" accept={FORMATOS_FOTO} onChange={elegir} disabled={subir.isPending} />
        </label>
      )}
      {(aviso || subir.isError) && (
        <p className="error" role="alert">
          {aviso ?? mensajeError(subir.error, 'No fue posible subir la foto.')}
        </p>
      )}
    </div>
  )
}

function PlanYServicios({ familiaId, mascotaId }: { familiaId: string; mascotaId: string }) {
  const cuenta = useEstadoCuenta(familiaId)
  const servicios = useResumenServicios(familiaId, { ...mesEnCurso(), mascota_id: mascotaId })
  const plan = cuenta.isPending
    ? 'Cargando el plan…'
    : cuenta.isError
      ? 'No fue posible cargar el plan.'
      : cuenta.data
        ? `Plan ${cuenta.data.plan.nombre}, el de la familia.`
        : 'La familia no tiene un plan vigente.'
  const delMes = servicios.isPending
    ? 'Cargando sus servicios…'
    : servicios.isError
      ? 'No fue posible cargar sus servicios.'
      : `Este mes: ${servicios.data.pendientes.length} pendientes y ${servicios.data.utilizados.length} utilizados. El detalle está en la pestaña Servicios.`
  return (
    <div>
      <p>{plan}</p>
      <p className="apagado">{delMes}</p>
    </div>
  )
}
