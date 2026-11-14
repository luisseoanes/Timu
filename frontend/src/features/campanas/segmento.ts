import { estado } from '@/lib/estados'

import type { FiltrosSegmento } from './api'

/** A quién le llega un segmento, dicho para una persona: «En mora, Congelada · Bogotá · mora de
 * 30 días o más». Los estados por su nombre, no por su código. */
export function resumenFiltros(f: FiltrosSegmento): string {
  const partes = [
    f.estados?.length ? f.estados.map((e) => estado('afiliacion', e).label).join(', ') : null,
    f.ciudades?.length ? f.ciudades.join(', ') : null,
    f.dias_mora_min ? `mora de ${f.dias_mora_min} días o más` : null,
    f.renovacion_en_dias ? `renuevan en ${f.renovacion_en_dias} días o menos` : null,
  ].filter(Boolean)
  return partes.join(' · ') || 'Todas las familias'
}
