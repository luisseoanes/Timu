import type { ReactNode } from 'react'

import { Icono } from '@/components/Icono'
import { MarcaTimu } from '@/components/MarcaTimu'

/** El año de una familia, como un plano de metro: lo hecho, hoy y lo que viene. Decorativo. */
const ESTACIONES: { nombre: string; tipo: 'hecha' | 'proxima' | 'programada' }[] = [
  { nombre: 'Afiliación', tipo: 'hecha' },
  { nombre: 'Vacunas', tipo: 'hecha' },
  { nombre: 'Visita en casa', tipo: 'proxima' },
  { nombre: 'Renovación', tipo: 'programada' },
]

/**
 * Pantallas de acceso (ingreso, recuperación, restablecimiento y activación). Desde 900 px,
 * el panel marino con el logo, la frase de la pantalla y la línea a la izquierda, y el
 * formulario a la derecha; por debajo, una franja marina arriba y el formulario debajo.
 * La frase le habla a quien llega: la activación, a la familia.
 */
export function AccesoLayout({
  frase = 'Tu peludito, bien cuidado.',
  children,
}: {
  frase?: string
  children: ReactNode
}) {
  return (
    <div className="ingreso">
      <aside className="ingreso-marca">
        <span className="ingreso-logo">
          <MarcaTimu claro />
        </span>
        <span className="ingreso-logo-compacto">
          <MarcaTimu claro compacta />
        </span>
        <div className="ingreso-mensaje">
          <p className="ingreso-frase">{frase}</p>
          <LineaDeMarca />
        </div>
        <NotaDatos />
      </aside>

      <main className="ingreso-contenido">
        <div className="ingreso-panel">
          {children}
          <NotaDatos />
        </div>
      </main>
    </div>
  )
}

/** La línea de la familia en la señalética del metro, sobre marino (regla 6 del manual). */
function LineaDeMarca() {
  return (
    <ol className="ingreso-linea" aria-hidden="true">
      {ESTACIONES.map((e, i) => (
        <li key={e.nombre} className="ingreso-estacion" data-tipo={e.tipo}>
          {i === 2 && (
            <span className="ingreso-hoy">
              <span>Hoy</span>
            </span>
          )}
          <span className="ingreso-punto" />
          <span className="ingreso-rotulo">{e.nombre}</span>
        </li>
      ))}
    </ol>
  )
}

function NotaDatos() {
  return (
    <p className="ingreso-legal">
      <Icono nombre="escudo" size={16} /> Datos protegidos · Ley 1581 de 2012
    </p>
  )
}
