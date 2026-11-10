import type { ReactNode } from 'react'

import { Icono, type NombreIcono } from '@/components/Icono'
import { estado, type Dominio, type Tono } from '@/lib/estados'

/** Cada tono tiene su forma además de su color: el estado nunca se lee solo por el color
 * (WCAG 1.4.1; docs/manual-de-marca.md, sección 10). */
const ICONO: Record<Tono, NombreIcono> = {
  ok: 'check',
  alerta: 'alerta',
  info: 'info',
  peligro: 'cerrar',
  neutro: 'menos',
}

/** Pastilla de estado: fondo tintado, icono y texto. */
export function Insignia({ tono, title, children }: { tono: Tono; title?: string; children: ReactNode }) {
  return (
    <span className={`distintivo distintivo-${tono}`} title={title}>
      <Icono nombre={ICONO[tono]} size={12} />
      {children}
    </span>
  )
}

/** Distintivo de estado: el tono y el texto salen del mapeo único de `lib/estados.ts`. */
export function Distintivo({ dominio, valor }: { dominio: Dominio; valor: string }) {
  const { label, tono } = estado(dominio, valor)
  return <Insignia tono={tono}>{label}</Insignia>
}
