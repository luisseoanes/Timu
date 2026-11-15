import { useState } from 'react'

import { Icono } from '@/components/Icono'

/** Campo de contraseña con su botón para verla. Lo comparten el ingreso y el enlace. */
export function CampoClave({
  id,
  etiqueta,
  autoComplete,
  valor,
  onCambio,
  invalido = false,
  ayuda,
  minLength,
}: {
  id: string
  etiqueta: string
  autoComplete: 'current-password' | 'new-password'
  valor: string
  onCambio: (v: string) => void
  invalido?: boolean
  ayuda?: string
  minLength?: number
}) {
  const [visible, setVisible] = useState(false)
  return (
    <div className="campo">
      <label htmlFor={id}>{etiqueta}</label>
      <span className="campo-adorno">
        <Icono nombre="candado" size={18} />
        <input
          id={id}
          className="input"
          type={visible ? 'text' : 'password'}
          autoComplete={autoComplete}
          minLength={minLength}
          value={valor}
          onChange={(e) => onCambio(e.target.value)}
          aria-invalid={invalido || undefined}
          aria-describedby={ayuda ? `${id}-ayuda` : undefined}
          required
        />
        <button
          type="button"
          className="campo-accion"
          aria-label={visible ? 'Ocultar contraseña' : 'Mostrar contraseña'}
          aria-pressed={visible}
          onClick={() => setVisible((v) => !v)}
        >
          <Icono nombre={visible ? 'ojo-cerrado' : 'ojo'} size={18} />
        </button>
      </span>
      {ayuda && (
        <span id={`${id}-ayuda`} className="campo-ayuda">
          {ayuda}
        </span>
      )}
    </div>
  )
}
