import { moneda } from '@/lib/formato'

/** «80 % hasta $ 200.000»: lo que cubre TIMU de una atención en la aliada, por remisión o por
 * convenio. El convenio la trae opcional en su tipo: el backend la deja en 100 si no se envía. */
export function cobertura(r: { cobertura_pct?: number; tope_cubierto?: string | null }): string {
  return `${r.cobertura_pct ?? 100} %${r.tope_cubierto ? ` hasta ${moneda(r.tope_cubierto)}` : ''}`
}
