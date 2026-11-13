import type { EstacionRead } from '@/types'

/**
 * La línea de la familia en el portal, abierta en «hoy» (contrato de la superficie del portal,
 * .impeccable/surfaces): encima lo vencido, debajo lo que viene. A diferencia de la del panel,
 * lo vencido se agrupa (las cuotas en una estación, los preventivos en otra) para que «hoy»
 * quede siempre en la primera pantalla del celular, y lo hecho se pliega en un tramo.
 */

export interface PorMascota {
  mascota: string
  mascotaId: string | null
  cuantos: number
}

export type Elemento =
  | { tipo: 'hechas'; estaciones: EstacionRead[] }
  | { tipo: 'cuotas-vencidas'; estaciones: EstacionRead[]; desde: string }
  | { tipo: 'preventivos-vencidos'; estaciones: EstacionRead[]; desde: string; porMascota: PorMascota[] }
  | { tipo: 'estacion'; estacion: EstacionRead }
  | { tipo: 'hoy' }
  /** Sin nada después de hoy, la línea no muere en «hoy»: cierra diciendo qué viene. */
  | { tipo: 'fin' }

/** El próximo cobro que anuncia el estado de cuenta cuando su cuota aún no existe. */
export const PROXIMO_COBRO = 'proximo-cobro'

/** Lo que puede pasar desde la línea; una sola de ellas va en verde (`accionPrincipal`). */
export type Accion = 'pagar-vencidas' | 'agendar-preventivos' | 'pagar-proxima'

/** `orden`: los ids de los peludos en el orden en que la pantalla los muestra. */
export function recorrido(estaciones: EstacionRead[], hoy: string, orden: string[] = []): Elemento[] {
  const porFecha = [...estaciones].sort((a, b) => a.fecha.localeCompare(b.fecha))
  const hechas = porFecha.filter((e) => e.estado === 'hecha' && e.fecha < hoy)
  const vencidas = porFecha.filter((e) => e.estado === 'vencida')
  const cuotas = vencidas.filter((e) => e.tipo === 'cuota')
  const preventivos = vencidas.filter((e) => e.tipo === 'preventivo')
  // Un servicio vencido es una visita que pasó sin cerrarse: es raro y cada uno es distinto,
  // así que va suelto, con su fecha.
  const sueltas = vencidas.filter((e) => e.tipo === 'servicio')
  const desdeHoy = porFecha.filter((e) => e.estado !== 'vencida' && !(e.estado === 'hecha' && e.fecha < hoy))

  const grupos: Elemento[] = []
  if (cuotas.length > 0) grupos.push({ tipo: 'cuotas-vencidas', estaciones: cuotas, desde: cuotas[0].fecha })
  if (preventivos.length > 0) {
    grupos.push({ tipo: 'preventivos-vencidos', estaciones: preventivos, desde: preventivos[0].fecha, porMascota: porMascota(preventivos, orden) })
  }
  grupos.push(...sueltas.map((estacion) => ({ tipo: 'estacion' as const, estacion })))
  // Lo vencido se ordena por lo más antiguo de cada grupo: lo que lleva más tiempo, arriba.
  grupos.sort((a, b) => fechaDe(a).localeCompare(fechaDe(b)))

  return [
    ...(hechas.length > 0 ? [{ tipo: 'hechas' as const, estaciones: hechas }] : []),
    ...grupos,
    { tipo: 'hoy' as const },
    ...desdeHoy.map((estacion) => ({ tipo: 'estacion' as const, estacion })),
    ...(desdeHoy.length === 0 ? [{ tipo: 'fin' as const }] : []),
  ]
}

/**
 * Con el plan en pausa no se generan cuotas nuevas, pero el estado de cuenta sí dice el
 * próximo cobro: entra como estación (sin botón de pago, porque esa cuota aún no existe) si la
 * línea no trae ya una cuota desde hoy.
 */
export function conProximoCobro(estaciones: EstacionRead[], cobro: { fecha: string } | null | undefined, hoy: string): EstacionRead[] {
  if (!cobro || cobro.fecha < hoy) return estaciones
  if (estaciones.some((e) => e.tipo === 'cuota' && e.fecha >= hoy && e.estado !== 'vencida')) return estaciones
  const hayProxima = estaciones.some((e) => e.estado === 'proxima')
  return [
    ...estaciones,
    { tipo: 'cuota', referencia_id: PROXIMO_COBRO, fecha: cobro.fecha, estado: hayProxima ? 'futura' : 'proxima', titulo: 'Próximo cobro', mascota: null, mascota_id: null },
  ]
}

function fechaDe(e: Elemento): string {
  if (e.tipo === 'estacion') return e.estacion.fecha
  if (e.tipo === 'cuotas-vencidas' || e.tipo === 'preventivos-vencidos') return e.desde
  return ''
}

/** Cuántos preventivos vencidos tiene cada peludo, en el orden de la pantalla. */
function porMascota(estaciones: EstacionRead[], orden: string[]): PorMascota[] {
  const cuenta = new Map<string, PorMascota>()
  for (const e of estaciones) {
    const clave = e.mascota_id ?? e.mascota ?? ''
    const actual = cuenta.get(clave)
    cuenta.set(clave, { mascota: e.mascota ?? 'Sin peludo', mascotaId: e.mascota_id, cuantos: (actual?.cuantos ?? 0) + 1 })
  }
  const posicion = (m: PorMascota) => {
    const i = m.mascotaId ? orden.indexOf(m.mascotaId) : -1
    return i === -1 ? orden.length : i
  }
  return [...cuenta.values()].sort((a, b) => posicion(a) - posicion(b))
}

/**
 * La acción verde de la línea: lo más urgente que la familia puede hacer. Pagar lo vencido va
 * primero, porque con cuotas vencidas el plan no deja agendar; después, agendar los preventivos
 * vencidos; si no, pagar la próxima cuota. Sin nada de eso, la línea no lleva verde.
 */
export function accionPrincipal(elementos: Elemento[], puedeAgendar: boolean): Accion | null {
  if (elementos.some((e) => e.tipo === 'cuotas-vencidas')) return 'pagar-vencidas'
  if (puedeAgendar && elementos.some((e) => e.tipo === 'preventivos-vencidos')) return 'agendar-preventivos'
  const proxima = elementos.find((e) => e.tipo === 'estacion' && e.estacion.estado === 'proxima')
  if (proxima?.tipo === 'estacion' && proxima.estacion.tipo === 'cuota' && proxima.estacion.referencia_id !== PROXIMO_COBRO) return 'pagar-proxima'
  return null
}

/** «agosto, septiembre y octubre», a partir de los títulos de las cuotas («Cuota de agosto»). */
export function meses(estaciones: EstacionRead[]): string {
  const nombres = estaciones.map((e) => e.titulo.replace(/^Cuota de /, ''))
  if (nombres.length <= 1) return nombres.join('')
  return `${nombres.slice(0, -1).join(', ')} y ${nombres[nombres.length - 1]}`
}

/** Las estaciones de un peludo: sus preventivos y sus visitas (las cuotas son de la familia). */
export function delPeludo(estaciones: EstacionRead[], mascotaId: string): EstacionRead[] {
  return estaciones.filter((e) => e.mascota_id === mascotaId)
}

/** Lo vencido de un peludo: sus preventivos y sus visitas sin cerrar. */
export function vencidasDe(estaciones: EstacionRead[], mascotaId: string): number {
  return estaciones.filter((e) => e.mascota_id === mascotaId && e.estado === 'vencida').length
}
