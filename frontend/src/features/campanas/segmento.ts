import type { EstadoAfiliacion } from '@/types'

import type { FiltrosSegmento } from './api'

export const ESTADOS_AFILIACION: { valor: EstadoAfiliacion; label: string }[] = [
  { valor: 'activa', label: 'Activa' },
  { valor: 'en_mora', label: 'En mora' },
  { valor: 'congelada', label: 'Congelada' },
  { valor: 'prospecto', label: 'Prospecto' },
  { valor: 'cancelada', label: 'Cancelada' },
]

export function resumenFiltros(f: FiltrosSegmento): string {
  const partes = [
    f.estados?.length ? f.estados.join(', ') : null,
    f.ciudades?.length ? f.ciudades.join(', ') : null,
    f.dias_mora_min ? `mora ≥ ${f.dias_mora_min} días` : null,
    f.renovacion_en_dias ? `renuevan en ${f.renovacion_en_dias} días` : null,
  ].filter(Boolean)
  return partes.join(' · ') || 'Todas las familias'
}
