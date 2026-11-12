import * as Menu from '@radix-ui/react-dropdown-menu'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Distintivo } from '@/components/Distintivo'
import { Icono } from '@/components/Icono'
import { Modal } from '@/components/Modal'
import { useAuth } from '@/features/auth'
import { useNombreTipoServicio } from '@/features/catalogos'
import { mensajeError } from '@/lib/errores'
import { hora } from '@/lib/formato'
import { puede } from '@/lib/permisos'
import type { PorRutearRead, RutaRead } from '@/types'

import { useAccionRuta, useAgregarParada } from './api'
import { LineaRuta } from './LineaRuta'
import { duracion, enRuta, resumen } from './ruta'

/**
 * La ruta que abrió quien coordina: de quién es, cómo va y su línea. Agregar lo que quedó por
 * rutear y cancelar la ruta antes de que arranque son de operaciones.
 */
export function RutaAbierta({
  ruta,
  responsable,
  volver,
  porRutear,
}: {
  ruta: RutaRead
  responsable: string
  /** A dónde vuelve el celular, que muestra el listado o la ruta, no los dos. */
  volver: string
  porRutear: PorRutearRead[]
}) {
  const { usuario } = useAuth()
  const nombreTipo = useNombreTipoServicio()
  const agregar = useAgregarParada()
  const cancelar = useAccionRuta()
  const [cancelando, setCancelando] = useState(false)
  const gestiona = puede(usuario, 'planearRutas') && (ruta.estado === 'planificada' || ruta.estado === 'en_curso')
  const candidatos = gestiona ? porRutear.filter((s) => s.ciudad === ruta.ciudad) : []
  const cancelable = gestiona && ruta.estado === 'planificada'
  const tiempo = duracion(ruta.duracion_min)
  const servicios = enRuta(ruta).length

  return (
    <section className="ficha-abierta" aria-label="Ruta abierta">
      <header className="ficha-cabeza">
        <Link to={volver} className="btn btn-plano ficha-volver" aria-label="Volver a las rutas">
          <Icono nombre="volver" size={16} />
        </Link>
        <h2>{responsable}</h2>
        <div className="ficha-datos">
          <Distintivo dominio="ruta" valor={ruta.estado} />
          <span className="numero">
            {resumen([ruta])}
            {tiempo && ` · ${tiempo}`}
          </span>
          <span className="apagado">{ruta.ciudad}</span>
        </div>
        {(candidatos.length > 0 || cancelable) && (
          <div className="ficha-acciones">
            {candidatos.length > 0 && (
              <Menu.Root modal={false}>
                <Menu.Trigger className="btn btn-suave" disabled={agregar.isPending}>
                  {agregar.isPending ? 'Agregando…' : 'Agregar un servicio'}
                  <Icono nombre="abajo" size={16} />
                </Menu.Trigger>
                <Menu.Portal>
                  <Menu.Content className="menu" align="start" sideOffset={6}>
                    {candidatos.map((s) => (
                      <Menu.Item
                        key={s.id}
                        className="menu-item"
                        onSelect={() => agregar.mutate({ rutaId: ruta.id, servicioId: s.id })}
                      >
                        <span className="numero">{hora(s.programado_para)}</span>
                        {s.familia.titular_nombre} · {nombreTipo(s.tipo_codigo)}
                      </Menu.Item>
                    ))}
                  </Menu.Content>
                </Menu.Portal>
              </Menu.Root>
            )}
            {cancelable && (
              <button className="btn btn-plano btn-plano-peligro" type="button" onClick={() => setCancelando(true)}>
                Cancelar ruta
              </button>
            )}
            {agregar.isError && (
              <p className="error" role="alert">
                {mensajeError(agregar.error, 'No fue posible agregar el servicio.')}
              </p>
            )}
          </div>
        )}
      </header>

      <LineaRuta ruta={ruta} />

      <Modal
        abierto={cancelando}
        onCambio={(v) => {
          if (!v) {
            cancelar.reset()
            setCancelando(false)
          }
        }}
        titulo="Cancelar la ruta"
        descripcion={`La ruta de ${responsable} se deshace antes de arrancar.`}
        pie={
          <button
            className="btn btn-peligro"
            type="button"
            disabled={cancelar.isPending}
            onClick={() => cancelar.mutate({ id: ruta.id, accion: 'cancelacion' }, { onSuccess: () => setCancelando(false) })}
          >
            {cancelar.isPending ? 'Cancelando…' : 'Cancelar la ruta'}
          </button>
        }
      >
        <p>
          {servicios === 1 ? 'Su servicio vuelve' : `Sus ${servicios} servicios vuelven`} a quedar por rutear. Las familias
          ya recibieron la franja de llegada: al planear de nuevo se les avisa la que quede.
        </p>
        {cancelar.isError && (
          <p className="error" role="alert">
            {mensajeError(cancelar.error, 'No fue posible cancelar la ruta.')}
          </p>
        )}
      </Modal>
    </section>
  )
}
