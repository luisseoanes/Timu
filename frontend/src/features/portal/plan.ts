import type { Tono } from '@/lib/estados'
import type { ColorPlan } from '@/types'

import type { BeneficioPortal, PlanPortal } from './api'

// Cómo se le dice a la familia en qué está su plan y qué le cubre: las condiciones se dicen de
// frente (PRODUCT.md), nunca con «ilimitado».

/** Los peludos del plan, como se nombran en una frase: «Luna y Michi». */
function peludos(p: PlanPortal): string {
  const nombres = p.mascotas.map((m) => m.mascota)
  return nombres.length <= 1 ? (nombres[0] ?? 'tus peludos') : `${nombres.slice(0, -1).join(', ')} y ${nombres[nombres.length - 1]}`
}

/** «21 de enero de 2027»: la fecha dicha como se dice, igual que en el resto del portal. */
const FECHA_CON_ANIO = new Intl.DateTimeFormat('es-CO', { day: 'numeric', month: 'long', year: 'numeric' })
function fechaDicha(iso: string): string {
  const [anio, mes, dia] = iso.slice(0, 10).split('-').map(Number)
  return FECHA_CON_ANIO.format(new Date(anio, mes - 1, dia))
}

/** El estado del plan dicho en una frase, con qué hacer (las condiciones se dicen de frente).
 * `cuotasVencidas` es null mientras no se sabe (la línea no llegó o falló): la frase no
 * inventa un número ni dice que no hay ninguna. */
export function frase(p: PlanPortal | null, cuotasVencidas: number | null): string {
  if (p === null) return 'Aún no tienes un plan activo. Escríbenos por WhatsApp para afiliarte.'
  const cuotas = cuotasVencidas === 1 ? 'Tu cuota vencida' : `Tus ${cuotasVencidas} cuotas vencidas`
  switch (p.estado) {
    case 'activa':
      return `Tu plan está al día. Se renueva el ${fechaDicha(p.fecha_renovacion)}.`
    case 'en_mora':
      return 'Tienes cuotas vencidas. Ponte al día para seguir agendando visitas.'
    case 'congelada':
      if (cuotasVencidas === null) {
        return `Tus cuotas vencidas pausaron el plan. Al pagar, ${peludos(p)} ${p.mascotas.length === 1 ? 'recupera sus' : 'recuperan sus'} beneficios.`
      }
      return cuotasVencidas > 0
        ? `${cuotas} ${cuotasVencidas === 1 ? 'pausó' : 'pausaron'} el plan. Al pagar, ${peludos(p)} ${p.mascotas.length === 1 ? 'recupera sus' : 'recuperan sus'} beneficios.`
        : 'Tu plan está en pausa. Escríbenos por WhatsApp para reactivarlo.'
    case 'cancelada':
      return 'Tu plan está cancelado. Escríbenos por WhatsApp si quieres volver.'
    default:
      return 'Tu afiliación está en proceso. Te escribimos por WhatsApp cuando quede activa.'
  }
}

/** Por qué no se puede agendar desde el portal ahora, o null si se puede: lo decide el plan,
 * igual que la elegibilidad del backend. */
export function motivoSinAgendar(p: PlanPortal | null | undefined): string | null {
  if (p === undefined) return 'Cargando tu plan…'
  if (p === null) return 'Necesitas un plan activo para agendar.'
  if (p.estado === 'activa') return null
  if (p.estado === 'congelada' || p.estado === 'en_mora') return 'Se agendan al ponerte al día.'
  return 'Escríbenos por WhatsApp para agendar.'
}

/** Lo que le queda de un beneficio: «le quedan 4 de 6 este año» o «sin tope de usos este mes». */
export function cupo(b: BeneficioPortal): string {
  const periodo = b.periodo === 'anual' ? 'este año' : 'este mes'
  if (b.disponibles === null) return `sin tope de usos ${periodo}`
  return `le ${b.disponibles === 1 ? 'queda' : 'quedan'} ${b.disponibles} de ${b.cupo} ${periodo}`
}

/**
 * El estado del plan con las palabras de la frase: para la familia, «congelada» es «en pausa»
 * (la misma palabra en la pastilla y en la frase), con tono de aviso. El panel conserva el
 * término del equipo en `lib/estados.ts`.
 */
const ESTADOS: Record<string, { label: string; tono: Tono }> = {
  activa: { label: 'Activo', tono: 'ok' },
  en_mora: { label: 'Cuotas vencidas', tono: 'alerta' },
  congelada: { label: 'En pausa', tono: 'alerta' },
  cancelada: { label: 'Cancelado', tono: 'peligro' },
}
export function estadoDelPlan(estado: string): { label: string; tono: Tono } {
  return ESTADOS[estado] ?? { label: 'En proceso', tono: 'info' }
}

/** Los planes de la familia, una vez cada uno, con su color y sus peludos. */
export function planesDe(p: PlanPortal): { nombre: string; color: ColorPlan; mascotas: string[] }[] {
  const planes = new Map<string, { nombre: string; color: ColorPlan; mascotas: string[] }>()
  for (const m of p.mascotas) {
    const actual = planes.get(m.plan) ?? { nombre: m.plan, color: m.color, mascotas: [] }
    planes.set(m.plan, { ...actual, mascotas: [...actual.mascotas, m.mascota] })
  }
  return [...planes.values()]
}

/** Lo que dice la línea cuando no hay nada después de hoy. */
export function finDeLinea(p: PlanPortal | null | undefined, peludo?: string): string {
  const pausado = p?.estado === 'congelada' || p?.estado === 'en_mora'
  // La línea de un peludo no lleva cuotas (son de la familia): no se le prometen.
  if (peludo) {
    return pausado
      ? `Al ponerte al día, aquí aparecen las vacunas, desparasitaciones y visitas que agendes para ${peludo}.`
      : `Nada más programado. Cuando agendes una visita para ${peludo}, aparece aquí.`
  }
  return pausado
    ? 'Al ponerte al día, aquí aparecen tus próximas cuotas y las visitas que agendes para tus peludos.'
    : 'Nada más programado. Cuando agendes una visita para tus peludos, aparece aquí.'
}
