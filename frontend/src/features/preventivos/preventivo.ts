import type { EventoBandeja } from '@/types'

/** La dosis como la dice una persona: «dosis 2» en la serie inicial, «refuerzo» después. El número
 * de un refuerzo solo cuenta la secuencia: «dosis 1, refuerzo» se leía como dos cosas a la vez. */
export function dosis(numero: number, refuerzo: boolean): string {
  return refuerzo ? 'refuerzo' : `dosis ${numero}`
}

/** Un preventivo de una mascota, escrito igual en la bandeja, la estación y la autorización:
 * «Luna · Antirrábica canina, refuerzo». */
export function pedido(e: Pick<EventoBandeja, 'mascota_nombre' | 'nombre' | 'dosis_numero' | 'es_refuerzo'>): string {
  return `${e.mascota_nombre} · ${e.nombre}, ${dosis(e.dosis_numero, e.es_refuerzo)}`
}
