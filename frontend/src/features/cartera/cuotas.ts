import type { CuotaRead } from '@/types'

// Las cuotas dichas a una persona: las usan el portal (R3-POR-02) y el panel (R2-PAN-08).

const MES = new Intl.DateTimeFormat('es-CO', { month: 'long' })

/** «Cuota de octubre», «Cuota de enero a marzo» si cubre varios meses, y el año solo si no es
 * este. La descripción del backend es técnica («Cuota 2026-08»): solo manda en los ajustes, que
 * los escribe el equipo. */
export function nombreCuota(q: Pick<CuotaRead, 'periodo' | 'descripcion' | 'tipo' | 'meses'>, hoy = new Date()): string {
  if (q.tipo !== 'cuota') return q.descripcion ?? 'Ajuste de plan'
  const [anio, mes] = q.periodo.split('-').map(Number)
  const inicio = new Date(anio, mes - 1, 1)
  const fin = new Date(anio, mes - 1 + Math.max(q.meses, 1) - 1, 1)
  const anioDe = (d: Date) => (d.getFullYear() === hoy.getFullYear() ? '' : ` de ${d.getFullYear()}`)
  if (fin.getTime() === inicio.getTime()) return `Cuota de ${MES.format(inicio)}${anioDe(inicio)}`
  const desde = MES.format(inicio) + (inicio.getFullYear() === fin.getFullYear() ? '' : ` de ${inicio.getFullYear()}`)
  return `Cuota de ${desde} a ${MES.format(fin)}${anioDe(fin)}`
}

/** Lo que falta por pagar: ni pagadas ni anuladas, de la más antigua a la más reciente. */
export function porPagar(cuotas: CuotaRead[]): CuotaRead[] {
  return cuotas
    .filter((q) => q.estado !== 'pagada' && q.estado !== 'anulada')
    .sort((a, b) => a.fecha_vencimiento.localeCompare(b.fecha_vencimiento))
}

export const saldoDe = (q: Pick<CuotaRead, 'valor' | 'valor_pagado'>) => Number(q.valor) - Number(q.valor_pagado)
