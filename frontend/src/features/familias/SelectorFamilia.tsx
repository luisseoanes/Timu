import { useState } from 'react'

import { Icono } from '@/components/Icono'
import { mensajeError } from '@/lib/errores'
import type { FamiliaRead } from '@/types'

import { useFamilias } from './api'

/**
 * Buscar y elegir una familia dentro de un formulario. Lo usan servicios, tareas,
 * remisiones y la afiliación asistida. Con la familia elegida muestra su resumen y
 * permite cambiarla.
 */
export function SelectorFamilia({
  valor,
  onCambio,
  etiqueta = 'Familia',
  enfocar = false,
}: {
  valor: FamiliaRead | null
  onCambio: (familia: FamiliaRead | null) => void
  etiqueta?: string
  /** Al montarse, el foco va a la búsqueda: es lo primero que se llena en el formulario. */
  enfocar?: boolean
}) {
  const [q, setQ] = useState('')
  const resultados = useFamilias({ q: q || undefined, limit: 6 })

  if (valor) {
    return (
      <div className="campo">
        <span>{etiqueta}</span>
        <div className="seleccion">
          <span className="fila-icono">
            <Icono nombre="familias" size={18} />
          </span>
          <span className="fila-cuerpo">
            <strong>{valor.titular_nombre}</strong>
            <span className="seleccion-dato">
              {valor.documento} · {valor.ciudad}
            </span>
          </span>
          <button className="btn btn-plano" type="button" onClick={() => onCambio(null)}>
            Cambiar
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="campo">
      <label className="campo">
        <span>{etiqueta}</span>
        <span className="buscador">
          <Icono nombre="buscar" size={18} />
          <input
            type="search"
            placeholder="Nombre, documento o celular"
            autoFocus={enfocar}
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </span>
      </label>
      {q.trim().length > 1 && (
        <ul className="opciones" aria-label="Familias encontradas">
          {resultados.isPending && <li className="apagado">Buscando…</li>}
          {/* Un fallo (un perfil sin Familias, la red) se dice: la lista vacía se leía como «no hay». */}
          {resultados.isError && (
            <li className="apagado" role="alert">
              {mensajeError(resultados.error, 'No fue posible buscar la familia.')}
            </li>
          )}
          {resultados.data?.items.length === 0 && <li className="apagado">Ninguna familia coincide.</li>}
          {resultados.data?.items.map((f) => (
            <li key={f.id}>
              <button type="button" className="opcion" onClick={() => onCambio(f)}>
                <strong>{f.titular_nombre}</strong>
                <span>
                  {f.documento} · {f.ciudad}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
