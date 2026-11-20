import { estado } from '@/lib/estados'

import type { FiltrosSegmento, TipoPreventivo } from './api'

export const TIPOS_PREVENTIVO: { valor: TipoPreventivo; label: string }[] = [
  { valor: 'vacuna', label: 'Vacunas' },
  { valor: 'desparasitacion_interna', label: 'Desparasitación interna' },
  { valor: 'desparasitacion_externa', label: 'Desparasitación externa' },
]

/** A quién le llega un segmento, dicho para una persona: «En mora, Congelada · Bogotá · mora de
 * 30 días o más». Los estados por su nombre, no por su código. */
export function resumenFiltros(f: FiltrosSegmento): string {
  const partes = [
    f.estados?.length ? f.estados.map((e) => estado('afiliacion', e).label).join(', ') : null,
    f.ciudades?.length ? f.ciudades.join(', ') : null,
    f.barrios?.some((b) => b.trim()) ? f.barrios.map((b) => b.trim()).filter(Boolean).join(', ') : null,
    f.especies?.length ? f.especies.join(', ') : null,
    edad(f),
    preventivos(f),
    f.dias_mora_min ? `mora de ${f.dias_mora_min} días o más` : null,
    f.renovacion_en_dias ? `renuevan en ${f.renovacion_en_dias} días o menos` : null,
  ].filter(Boolean)
  return partes.join(' · ') || 'Todas las familias'
}

function edad(f: FiltrosSegmento): string | null {
  const { edad_min_anios: min, edad_max_anios: max } = f
  if (min !== undefined && max !== undefined) return `mascotas de ${min} a ${max} años`
  if (min !== undefined) return `mascotas de ${min} años o más`
  if (max !== undefined) return `mascotas de hasta ${max} años`
  return null
}

function preventivos(f: FiltrosSegmento): string | null {
  const cuando = [
    f.preventivo_vencido ? 'vencido' : null,
    f.preventivo_en_dias ? `que vence en ${f.preventivo_en_dias} días` : null,
  ].filter(Boolean)
  if (cuando.length === 0) return null
  const tipos = TIPOS_PREVENTIVO.filter((t) => f.tipos_preventivo?.includes(t.valor)).map((t) => t.label.toLowerCase())
  return `con un preventivo ${cuando.join(' o ')}${tipos.length ? ` (${tipos.join(', ')})` : ''}`
}
