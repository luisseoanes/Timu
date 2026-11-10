import { useState } from 'react'
import { Link } from 'react-router-dom'

import { FotoEditable } from '@/components/FotoEditable'
import { Modal } from '@/components/Modal'
import { mensajeError } from '@/lib/errores'
import { mesEnCurso, moneda } from '@/lib/formato'
import type { FamiliaRead, MascotaRead } from '@/types'

import {
  useActualizarMascota,
  useCambiarPlanMascota,
  useEstadoCuenta,
  useQuitarFotoMascota,
  useResumenServicios,
  useSubirFotoMascota,
  type CambiosMascota,
} from './api'
import { CamposMascota } from './CamposMascota'
import { ElegirPlan } from './ElegirPlan'
import { leerCamposMascota } from './mascota'

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
          <PlanYServicios familia={familia} mascota={mascota} editable={editable} />
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
  const quitar = useQuitarFotoMascota()
  const fallo = subir.error ?? quitar.error
  return (
    <FotoEditable
      url={mascota.foto_url}
      alt={`Foto de ${mascota.nombre}`}
      editable={editable}
      ocupada={subir.isPending || quitar.isPending}
      error={fallo ? mensajeError(fallo, 'No fue posible guardar la foto.') : null}
      onSubir={(foto) => {
        quitar.reset()
        subir.mutate({ id: mascota.id, foto })
      }}
      onQuitar={() => {
        subir.reset()
        quitar.mutate(mascota.id)
      }}
    />
  )
}

function PlanYServicios({
  familia,
  mascota,
  editable,
}: {
  familia: FamiliaRead
  mascota: MascotaRead
  editable: boolean
}) {
  const cuenta = useEstadoCuenta(familia.id)
  const servicios = useResumenServicios(familia.id, { ...mesEnCurso(), mascota_id: mascota.id })
  const vigente = cuenta.data && cuenta.data.contrato.estado !== 'cancelada' ? cuenta.data : null
  const afiliada = vigente?.mascotas.find((m) => m.mascota_id === mascota.id)
  const plan = cuenta.isPending
    ? 'Cargando el plan…'
    : cuenta.isError
      ? 'No fue posible cargar el plan.'
      : !vigente
        ? 'La familia no tiene un plan vigente.'
        : afiliada
          ? `Plan ${afiliada.plan_nombre}: paga ${moneda(afiliada.valor_mensual)} al mes.`
          : 'No está afiliada en el contrato de la familia.'
  const delMes = servicios.isPending
    ? 'Cargando sus servicios…'
    : servicios.isError
      ? 'No fue posible cargar sus servicios.'
      : `Este mes: ${servicios.data.pendientes.length} pendientes y ${servicios.data.utilizados.length} utilizados. El detalle está en la pestaña Servicios.`
  return (
    <div className="pila">
      <div>
        <p>{plan}</p>
        <p className="apagado">{delMes}</p>
      </div>
      {editable && vigente && afiliada && (
        <CambioDePlan
          contratoId={vigente.contrato.id}
          familia={familia}
          mascota={mascota}
          planActual={afiliada.plan_id}
        />
      )}
    </div>
  )
}

/** F1-PLA-02 El peludo pasa a otro plan; cómo se cobra lo decide la regla `plan.cambio`. */
function CambioDePlan({
  contratoId,
  familia,
  mascota,
  planActual,
}: {
  contratoId: string
  familia: FamiliaRead
  mascota: MascotaRead
  planActual: string
}) {
  const cambiar = useCambiarPlanMascota()
  const [plan, setPlan] = useState(planActual)
  return (
    <div className="acciones">
      <ElegirPlan etiqueta="Cambiar de plan" ciudad={familia.ciudad} especie={mascota.especie} valor={plan} onCambio={setPlan} />
      <button
        className="btn btn-suave"
        type="button"
        disabled={plan === planActual || cambiar.isPending}
        onClick={() => cambiar.mutate({ contratoId, mascotaId: mascota.id, planId: plan })}
      >
        {cambiar.isPending ? 'Cambiando…' : 'Cambiar plan'}
      </button>
      {cambiar.isSuccess && (
        <p className="apagado" role="status">
          Plan cambiado.
        </p>
      )}
      {cambiar.isError && (
        <p className="error" role="alert">
          {mensajeError(cambiar.error, 'No fue posible cambiar el plan.')}
        </p>
      )}
    </div>
  )
}
