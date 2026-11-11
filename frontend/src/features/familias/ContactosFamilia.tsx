import { useState } from 'react'

import { Modal } from '@/components/Modal'
import { mensajeError } from '@/lib/errores'
import type { ContactoRead, FamiliaRead } from '@/types'

import { useActualizarContacto, useAgregarContacto, useBajaContacto, type DatosContacto } from './api'

/** Igual que en el backend: más contactos los rechaza la base. */
const MAX_CONTACTOS = 3

/**
 * 6.1 Contactos adicionales de la familia: solo para consulta del equipo. No tienen acceso
 * a la plataforma ni reciben sus mensajes.
 */
export function ContactosFamilia({ familia }: { familia: FamiliaRead }) {
  const contactos = familia.contactos ?? []
  const editable = !familia.dada_de_baja_en
  const lleno = contactos.length >= MAX_CONTACTOS
  const [editando, setEditando] = useState<ContactoRead | 'nuevo' | null>(null)
  const [quitando, setQuitando] = useState<ContactoRead | null>(null)

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Contactos adicionales</h3>
        {editable && (
          <button className="btn btn-suave" type="button" disabled={lleno} onClick={() => setEditando('nuevo')}>
            Añadir contacto
          </button>
        )}
      </div>
      <p className="apagado">
        Solo para consulta del equipo: no entran a la plataforma ni reciben mensajes. Máximo {MAX_CONTACTOS}.
      </p>
      {contactos.length === 0 ? (
        <p className="apagado">Esta familia no tiene contactos adicionales.</p>
      ) : (
        <div className="scroll-x">
          <table className="tabla tabla-apilable">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Celular</th>
                <th>Relación</th>
                <th>Correo</th>
                {editable && <th><span className="sr-only">Acciones</span></th>}
              </tr>
            </thead>
            <tbody>
              {contactos.map((c) => (
                <tr key={c.id}>
                  <td data-etiqueta="Nombre" className="principal">{c.nombre}</td>
                  <td data-etiqueta="Celular" className="numero">{c.telefono}</td>
                  <td data-etiqueta="Relación">{c.relacion ?? '—'}</td>
                  <td data-etiqueta="Correo">{c.email ?? '—'}</td>
                  {editable && (
                    <td className="tabla-acciones">
                      <button className="btn btn-plano" type="button" onClick={() => setEditando(c)}>
                        Editar
                      </button>
                      <button className="btn btn-plano btn-plano-peligro" type="button" onClick={() => setQuitando(c)}>
                        Quitar
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <ContactoModal familiaId={familia.id} contacto={editando} onCerrar={() => setEditando(null)} />
      <QuitarContactoModal familiaId={familia.id} contacto={quitando} onCerrar={() => setQuitando(null)} />
    </section>
  )
}

function ContactoModal({
  familiaId,
  contacto,
  onCerrar,
}: {
  familiaId: string
  contacto: ContactoRead | 'nuevo' | null
  onCerrar: () => void
}) {
  const agregar = useAgregarContacto(familiaId)
  const actualizar = useActualizarContacto(familiaId)
  const existente = contacto !== null && contacto !== 'nuevo' ? contacto : null
  const mutacion = existente ? actualizar : agregar

  function guardar(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const d = new FormData(e.currentTarget)
    const texto = (campo: string) => String(d.get(campo) ?? '').trim() || undefined
    const datos: DatosContacto = {
      nombre: texto('nombre') ?? '',
      telefono: texto('telefono') ?? '',
      relacion: texto('relacion'),
      email: texto('email'),
    }
    if (existente) actualizar.mutate({ id: existente.id, ...datos }, { onSuccess: onCerrar })
    else agregar.mutate(datos, { onSuccess: onCerrar })
  }

  return (
    <Modal
      abierto={contacto !== null}
      onCambio={(v) => {
        if (!v) {
          agregar.reset()
          actualizar.reset()
          onCerrar()
        }
      }}
      titulo={existente ? `Editar a ${existente.nombre}` : 'Añadir contacto'}
      pie={
        <button className="btn btn-primario" type="submit" form="contacto-familia" disabled={mutacion.isPending}>
          {mutacion.isPending ? 'Guardando…' : 'Guardar contacto'}
        </button>
      }
    >
      <form id="contacto-familia" className="formulario" onSubmit={guardar}>
        <label className="campo ancho">
          <span>Nombre</span>
          <input className="input" name="nombre" defaultValue={existente?.nombre} required minLength={2} maxLength={160} />
        </label>
        <label className="campo">
          <span>Celular</span>
          <input className="input" name="telefono" defaultValue={existente?.telefono} required inputMode="tel" />
        </label>
        <label className="campo">
          <span>Relación (opcional)</span>
          <input className="input" name="relacion" defaultValue={existente?.relacion ?? ''} maxLength={60} />
        </label>
        <label className="campo ancho">
          <span>Correo (opcional)</span>
          <input className="input" name="email" type="email" defaultValue={existente?.email ?? ''} />
        </label>
        {mutacion.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(mutacion.error, 'No fue posible guardar el contacto.')}
          </p>
        )}
      </form>
    </Modal>
  )
}

function QuitarContactoModal({
  familiaId,
  contacto,
  onCerrar,
}: {
  familiaId: string
  contacto: ContactoRead | null
  onCerrar: () => void
}) {
  const baja = useBajaContacto(familiaId)

  return (
    <Modal
      abierto={contacto !== null}
      onCambio={(v) => {
        if (!v) {
          baja.reset()
          onCerrar()
        }
      }}
      titulo={`Quitar a ${contacto?.nombre ?? 'el contacto'}`}
      descripcion="Deja de figurar como contacto de la familia. El registro se conserva en el historial."
      pie={
        <button
          className="btn btn-peligro"
          type="button"
          disabled={baja.isPending}
          onClick={() => contacto && baja.mutate(contacto.id, { onSuccess: onCerrar })}
        >
          {baja.isPending ? 'Quitando…' : 'Quitar contacto'}
        </button>
      }
    >
      {baja.isError ? (
        <p className="error" role="alert">
          {mensajeError(baja.error, 'No fue posible quitar el contacto.')}
        </p>
      ) : (
        <p>Podrás añadir otro en su lugar.</p>
      )}
    </Modal>
  )
}
