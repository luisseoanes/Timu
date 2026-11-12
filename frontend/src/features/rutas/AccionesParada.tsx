import * as Menu from '@radix-ui/react-dropdown-menu'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { useAuth } from '@/features/auth'
import { useTiposServicio } from '@/features/catalogos'
import { usePasos } from '@/features/servicios'
import { mensajeError } from '@/lib/errores'
import { puede } from '@/lib/permisos'
import type { ParadaRead, RutaRead } from '@/types'

import { useAccionParada, useAccionRuta, useOmitirParada, useSalidaParada } from './api'
import { comoLlegar, enlaceWhatsApp } from './ruta'

/**
 * Lo que se hace con una parada. La de estado es una sola, la que toca (iniciar la ruta, salir
 * hacia la familia, llegar, terminar), y solo la lleva la parada actual: así la pantalla tiene
 * una única acción verde. Llegar a la casa y hablar con la familia sirven en cualquier parada;
 * lo raro y lo que no se deshace va en el menú.
 */
export function AccionesParada({ ruta, parada, actual }: { ruta: RutaRead; parada: ParadaRead; actual: boolean }) {
  const { usuario } = useAuth()
  const ruteo = useAccionRuta()
  const avanzar = useAccionParada()
  const [modal, setModal] = useState<'salida' | 'omision' | null>(null)
  const enCampo = puede(usuario, 'campo')
  const enCurso = ruta.estado === 'en_curso'
  const ocupada = ruteo.isPending || avanzar.isPending
  const { familia, mascota } = parada
  // La acción de estado es la principal (verde) solo para quien hace la ruta. Quien coordina
  // también puede avanzarla (para cerrar el día si alguien olvidó marcar), pero en su vista la
  // acción principal es planear.
  const estado = ruta.responsable_id === usuario?.id ? 'btn btn-primario' : 'btn btn-secundario'

  return (
    <>
      <div className="estacion-acciones">
        {actual && enCampo && ruta.estado === 'planificada' && ruta.responsable_id === usuario?.id && (
          <button className="btn btn-primario" type="button" disabled={ocupada} onClick={() => ruteo.mutate({ id: ruta.id, accion: 'inicio' })}>
            {ruteo.isPending ? 'Iniciando…' : 'Iniciar ruta'}
          </button>
        )}
        {actual && enCampo && enCurso && parada.estado === 'pendiente' && (
          <button className={estado} type="button" disabled={ocupada} onClick={() => avanzar.mutate({ id: parada.id, accion: 'en-camino' })}>
            {avanzar.isPending ? 'Avisando…' : 'Voy en camino'}
          </button>
        )}
        {actual && enCampo && enCurso && parada.estado === 'en_camino' && (
          <button className={estado} type="button" disabled={ocupada} onClick={() => avanzar.mutate({ id: parada.id, accion: 'llegada' })}>
            {avanzar.isPending ? 'Registrando…' : 'Llegué'}
          </button>
        )}
        {actual && enCampo && enCurso && parada.estado === 'en_sitio' && (
          <Terminar parada={parada} clase={estado} onTerminar={() => setModal('salida')} />
        )}
        <a className="btn btn-secundario" href={comoLlegar(parada, ruta.ciudad)} target="_blank" rel="noopener noreferrer">
          <Icono nombre="rutas" size={16} />
          Cómo llegar
        </a>
        <a className="btn btn-secundario btn-icono" href={`tel:${familia.telefono}`} aria-label={`Llamar a ${familia.titular_nombre}`}>
          <Icono nombre="llamar" size={18} />
        </a>
        <Menu.Root modal={false}>
          <Menu.Trigger className="btn btn-secundario btn-icono" aria-label={`Más acciones con ${familia.titular_nombre}`}>
            <Icono nombre="puntos" size={18} />
          </Menu.Trigger>
          <Menu.Portal>
            <Menu.Content className="menu" align="end" sideOffset={6}>
              {/* Llegar sin haber avisado: «Voy en camino» le escribe a la familia, y decírselo
                  en su puerta sobra. */}
              {actual && enCampo && enCurso && parada.estado === 'pendiente' && (
                <Menu.Item className="menu-item" disabled={ocupada} onSelect={() => avanzar.mutate({ id: parada.id, accion: 'llegada' })}>
                  Ya llegué
                </Menu.Item>
              )}
              <Menu.Item asChild>
                <a className="menu-item" href={enlaceWhatsApp(familia.telefono)} target="_blank" rel="noopener noreferrer">
                  Escribir por WhatsApp
                </a>
              </Menu.Item>
              <Menu.Item asChild>
                <Link className="menu-item" to={`/servicios/${parada.servicio_id}`}>
                  Ver el servicio
                </Link>
              </Menu.Item>
              {mascota && puede(usuario, 'clinico') && (
                <Menu.Item asChild>
                  <Link className="menu-item" to={`/clinica/mascotas/${mascota.id}`}>
                    Historia clínica de {mascota.nombre}
                  </Link>
                </Menu.Item>
              )}
              {enCampo && (
                <>
                  <Menu.Separator className="menu-separador" />
                  <Menu.Item className="menu-item menu-item-peligro" onSelect={() => setModal('omision')}>
                    Omitir parada
                  </Menu.Item>
                </>
              )}
            </Menu.Content>
          </Menu.Portal>
        </Menu.Root>
      </div>
      {ruteo.isError && (
        <p className="error" role="alert">
          {mensajeError(ruteo.error, 'No fue posible iniciar la ruta.')}
        </p>
      )}
      {avanzar.isError && (
        <p className="error" role="alert">
          {mensajeError(avanzar.error, 'No fue posible actualizar la parada.')}
        </p>
      )}
      <SalidaModal parada={parada} abierto={modal === 'salida'} onCerrar={() => setModal(null)} />
      <OmisionModal parada={parada} abierto={modal === 'omision'} onCerrar={() => setModal(null)} />
    </>
  )
}

/**
 * La acción de una parada en sitio. El servicio no se cierra sin sus pasos obligatorios (la API
 * lo rechaza), y esos pasos se registran en la ficha del servicio: mientras falte alguno, la
 * acción lleva allí y dice qué falta; con todos, termina la visita.
 */
function Terminar({ parada, clase, onTerminar }: { parada: ParadaRead; clase: string; onTerminar: () => void }) {
  const tipos = useTiposServicio()
  const pasos = usePasos(parada.servicio_id)
  const definicion = tipos.data?.find((t) => t.codigo === parada.tipo_codigo)?.pasos ?? []
  const hechos = new Set((pasos.data ?? []).map((p) => p.paso_codigo))
  const faltan = definicion.filter((p) => p.obligatorio && !hechos.has(p.codigo))
  if (tipos.isPending || pasos.isPending) {
    return (
      <button className={clase} type="button" disabled>
        Terminar visita
      </button>
    )
  }
  if (faltan.length === 0) {
    return (
      <button className={clase} type="button" onClick={onTerminar}>
        Terminar visita
      </button>
    )
  }
  return (
    <>
      <Link className={clase} to={`/servicios/${parada.servicio_id}`}>
        Registrar la atención
      </Link>
      <p className="estacion-pendiente">
        Antes de terminar la visita falta registrar: {faltan.map((p) => p.nombre).join(', ')}.
      </p>
    </>
  )
}

function SalidaModal({ parada, abierto, onCerrar }: { parada: ParadaRead; abierto: boolean; onCerrar: () => void }) {
  const salida = useSalidaParada()
  const [evidencia, setEvidencia] = useState<File | undefined>()
  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          salida.reset()
          onCerrar()
        }
      }}
      titulo="Terminar visita"
      descripcion={`${parada.familia.titular_nombre}: el servicio queda completado y la ruta sigue con la próxima parada.`}
      pie={
        <button className="btn btn-primario" type="submit" form={`salida-${parada.id}`} disabled={salida.isPending}>
          {salida.isPending ? 'Registrando…' : 'Registrar salida'}
        </button>
      }
    >
      <form
        id={`salida-${parada.id}`}
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const nota = String(new FormData(e.currentTarget).get('nota') ?? '').trim()
          salida.mutate({ id: parada.id, nota: nota || undefined, evidencia }, { onSuccess: onCerrar })
        }}
      >
        <label className="campo ancho">
          <span>Nota de la visita (opcional)</span>
          <textarea className="input" name="nota" rows={3} />
        </label>
        <label className="campo ancho">
          <span>Evidencia (foto o PDF, opcional)</span>
          <input className="input" type="file" accept="image/*,application/pdf" onChange={(e) => setEvidencia(e.target.files?.[0])} />
        </label>
        {salida.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(salida.error, 'No fue posible registrar la salida.')}
          </p>
        )}
      </form>
    </Modal>
  )
}

function OmisionModal({ parada, abierto, onCerrar }: { parada: ParadaRead; abierto: boolean; onCerrar: () => void }) {
  const omitir = useOmitirParada()
  return (
    <Modal
      abierto={abierto}
      onCambio={(v) => {
        if (!v) {
          omitir.reset()
          onCerrar()
        }
      }}
      titulo="Omitir parada"
      descripcion={`${parada.familia.titular_nombre} sale de la ruta y las paradas siguientes se renumeran.`}
      pie={
        <button className="btn btn-peligro" type="submit" form={`omision-${parada.id}`} disabled={omitir.isPending}>
          {omitir.isPending ? 'Omitiendo…' : 'Omitir parada'}
        </button>
      }
    >
      <form
        id={`omision-${parada.id}`}
        className="formulario"
        onSubmit={(e) => {
          e.preventDefault()
          const d = new FormData(e.currentTarget)
          omitir.mutate(
            { id: parada.id, motivo: String(d.get('motivo')).trim(), cancelar_servicio: d.get('cancelar') === 'on' },
            { onSuccess: onCerrar },
          )
        }}
      >
        <label className="campo ancho">
          <span>Motivo</span>
          <textarea className="input" name="motivo" rows={2} required minLength={3} maxLength={255} />
        </label>
        <label className="acciones ancho">
          <input type="checkbox" name="cancelar" />
          Cancelar también el servicio (si no, queda por rutear de nuevo)
        </label>
        {omitir.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(omitir.error, 'No fue posible omitir la parada.')}
          </p>
        )}
      </form>
    </Modal>
  )
}
