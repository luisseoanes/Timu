import { useQuery } from '@tanstack/react-query'

import { api } from '@/api/client'
import type { DatosTimuRead, PlanPublico } from '@/types'

/** Lo que dice de TIMU la portada (R3-PUB-04): lo escribe Administración → Datos de TIMU. */
export function useDatosTimu() {
  return useQuery({
    queryKey: ['portada', 'institucional'],
    staleTime: 5 * 60_000,
    queryFn: async () => (await api.get<DatosTimuRead>('/institucional')).data,
  })
}

/** La dirección de un plan: `/planes/colita-feliz` para `colita_feliz`. */
export const rutaDePlan = (plan: Pick<PlanPublico, 'codigo'>) => `/planes/${plan.codigo.replace(/_/g, '-')}`
export const codigoDeRuta = (ruta: string) => ruta.replace(/-/g, '_')

/** La afiliación con lo que ya eligió en la portada: el registro arranca con eso. */
export function enlaceAfiliacion({ ciudad, perros = 0, gatos = 0, plan }: { ciudad?: string; perros?: number; gatos?: number; plan?: string }) {
  const p = new URLSearchParams()
  if (ciudad) p.set('ciudad', ciudad)
  if (perros) p.set('perros', String(perros))
  if (gatos) p.set('gatos', String(gatos))
  if (plan) p.set('plan', plan)
  const q = p.toString()
  return q ? `/afiliacion?${q}` : '/afiliacion'
}

/** Lo menos que paga un peludo al mes entre los planes: el «desde» de la portada. */
export function desdeMensual(planes: PlanPublico[], peludos = 1): string | undefined {
  const n = Math.min(Math.max(peludos, 1), 4)
  const valores = planes.map((p) => p.tarifas.find((t) => t.peludos === n)?.valor).filter((v): v is string => Boolean(v))
  if (valores.length === 0) return undefined
  return valores.reduce((a, b) => (Number(b) < Number(a) ? b : a))
}
