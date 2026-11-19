import type { ReactNode } from 'react'

import { useAuth } from '@/features/auth'
import { fechaLarga, hoyISO } from '@/lib/formato'

import { primerNombre } from './cifras'

/** La cabecera de cada Inicio: el saludo es el h1, con el día y lo que resume la pantalla. */
export function Saludo({ resumen, children }: { resumen: string; children?: ReactNode }) {
  const { usuario } = useAuth()
  const dia = fechaLarga(hoyISO())
  return (
    <header className="inicio-cabeza">
      <div>
        <h1>Hola, {primerNombre(usuario?.nombre)}</h1>
        <p>
          {dia.charAt(0).toUpperCase() + dia.slice(1)} · {resumen}
        </p>
      </div>
      {children}
    </header>
  )
}
