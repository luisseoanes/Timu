import type { ColorPlan, Periodicidad, PlanRead } from '@/types'

// Lo que comparten la ficha de un plan (`Planes.tsx`) y sus ventanas (`PlanFormularios.tsx`).

export const ETIQUETA_PELUDOS = ['1 peludo', '2 peludos (c/u)', '3 peludos (c/u)', '4 o más (c/u)']
export const PERIODOS: Record<Periodicidad, string> = { mensual: 'Mensual', trimestral: 'Trimestral', semestral: 'Semestral', anual: 'Anual' }
export const LARGOS = ['trimestral', 'semestral', 'anual'] as const

export function tarifa(plan: PlanRead, peludos: number): string {
  return plan.tarifas.find((t) => t.peludos === peludos)?.valor ?? '0'
}

export function valorLargo(plan: PlanRead | undefined, periodo: Periodicidad): number | string {
  const valor = plan?.tarifas_periodicidad.find((t) => t.periodicidad === periodo)?.valor
  return valor ? Number(valor) : ''
}

export const COLORES: Record<ColorPlan, string> = { verde: 'Verde', naranja: 'Naranja', azul: 'Azul' }
