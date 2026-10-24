import { useState } from 'react'

import { useCiudades } from '@/features/catalogos/api'
import { mensajeError } from '@/lib/errores'
import type { FamiliaRead } from '@/types'

import { useActualizarFamilia, type CambiosFamilia } from './api'

const CAMPOS: (keyof CambiosFamilia)[] = ['titular_nombre', 'telefono', 'email', 'ciudad', 'direccion', 'notas']

/** Datos del titular, en lectura; «Editar» los vuelve formulario. */
export function DatosFamilia({ familia }: { familia: FamiliaRead }) {
  const [editando, setEditando] = useState(false)
  const actualizar = useActualizarFamilia(familia.id)
  const ciudades = useCiudades()

  function guardar(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const d = new FormData(e.currentTarget)
    // Sólo viaja lo que cambió: así la bitácora registra cambios reales.
    const cambios: CambiosFamilia = {}
    for (const campo of CAMPOS) {
      const nuevo = String(d.get(campo) ?? '').trim()
      if (nuevo !== (familia[campo] ?? '')) cambios[campo] = nuevo || undefined
    }
    if (Object.keys(cambios).length === 0) return setEditando(false)
    actualizar.mutate(cambios, { onSuccess: () => setEditando(false) })
  }

  if (!editando) {
    return (
      <section className="tarjeta">
        <div className="tarjeta-cabeza">
          <h3>Titular</h3>
          <button className="btn btn-suave" type="button" onClick={() => setEditando(true)}>
            Editar
          </button>
        </div>
        <dl className="ficha">
          <div><dt>Documento</dt><dd className="numero">{familia.tipo_documento} {familia.documento}</dd></div>
          <div><dt>Celular</dt><dd className="numero">{familia.telefono}</dd></div>
          <div><dt>Correo</dt><dd>{familia.email ?? '—'}</dd></div>
          <div><dt>Ciudad</dt><dd>{familia.ciudad}</dd></div>
          <div><dt>Dirección</dt><dd>{familia.direccion ?? '—'}</dd></div>
          <div><dt>Origen</dt><dd>{familia.origen}</dd></div>
          {familia.notas && <div><dt>Notas</dt><dd>{familia.notas}</dd></div>}
        </dl>
        {actualizar.isSuccess && <p className="exito" role="status">Cambios guardados.</p>}
      </section>
    )
  }

  return (
    <section className="tarjeta">
      <div className="tarjeta-cabeza">
        <h3>Editar titular</h3>
      </div>
      <form className="formulario" onSubmit={guardar}>
        <label className="campo ancho">
          <span>Nombre del titular</span>
          <input className="input" name="titular_nombre" defaultValue={familia.titular_nombre} required minLength={2} />
        </label>
        <label className="campo">
          <span>Celular</span>
          <input className="input" name="telefono" defaultValue={familia.telefono} required inputMode="tel" />
        </label>
        <label className="campo">
          <span>Correo</span>
          <input className="input" name="email" type="email" defaultValue={familia.email ?? ''} />
        </label>
        <label className="campo">
          <span>Ciudad</span>
          <select className="input" name="ciudad" defaultValue={familia.ciudad}>
            {/* La ciudad actual se conserva aunque el catálogo ya no la tenga activa. */}
            <option value={familia.ciudad}>{familia.ciudad}</option>
            {ciudades.data
              ?.filter((c) => c.activa && c.nombre !== familia.ciudad)
              .map((c) => (
                <option key={c.codigo} value={c.nombre}>{c.nombre}</option>
              ))}
          </select>
        </label>
        <label className="campo">
          <span>Dirección</span>
          <input className="input" name="direccion" defaultValue={familia.direccion ?? ''} />
        </label>
        <label className="campo ancho">
          <span>Notas</span>
          <textarea className="input" name="notas" rows={3} defaultValue={familia.notas ?? ''} />
        </label>
        {actualizar.isError && (
          <p className="error ancho" role="alert">
            {mensajeError(actualizar.error, 'No fue posible guardar los cambios.')}
          </p>
        )}
        <div className="acciones ancho">
          <button className="btn btn-primario" type="submit" disabled={actualizar.isPending}>
            {actualizar.isPending ? 'Guardando…' : 'Guardar cambios'}
          </button>
          <button className="btn btn-plano" type="button" onClick={() => setEditando(false)}>
            Cancelar
          </button>
        </div>
      </form>
    </section>
  )
}
