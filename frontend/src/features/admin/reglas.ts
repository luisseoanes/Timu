import type { CampoEvento, EventoDeReglas, ReglaRead } from '@/types'

// El editor de reglas por campos (DEU-8): la condición se escribe como una lista de
// comparaciones unidas por «todas» o «alguna», un solo nivel. Lo que el motor admite además
// (grupos dentro de grupos, «no se cumple») solo se escribe por la API: el editor lo lee en
// palabras y lo conserva sin tocarlo.

export type Union = 'todas' | 'alguna'

/** Una comparación en el formulario: el valor, como lo escribe el control (texto o lista). */
export interface Comparacion {
  campo: string
  op: string
  valor: string | string[]
}

export interface CondicionEditable {
  union: Union
  comparaciones: Comparacion[]
}

/** Las comparaciones de una condición guardada, o `null` si tiene más de un nivel. */
export function leerCondicion(condicion: Record<string, unknown>): CondicionEditable | null {
  if (Object.keys(condicion).length === 0) return { union: 'todas', comparaciones: [] }
  if ('campo' in condicion) {
    const simple = aComparacion(condicion)
    return simple && { union: 'todas', comparaciones: [simple] }
  }
  const union: Union | null = 'todas' in condicion ? 'todas' : 'alguna' in condicion ? 'alguna' : null
  if (!union || !Array.isArray(condicion[union])) return null
  const comparaciones = (condicion[union] as Record<string, unknown>[]).map(aComparacion)
  if (comparaciones.some((c) => c === null)) return null
  return { union, comparaciones: comparaciones as Comparacion[] }
}

function aComparacion(c: Record<string, unknown>): Comparacion | null {
  if (typeof c.campo !== 'string' || typeof c.op !== 'string' || !('valor' in c)) return null
  const valor = Array.isArray(c.valor) ? c.valor.map(String) : String(c.valor)
  return { campo: c.campo, op: c.op, valor }
}

/** El valor que entiende el motor según el tipo del campo: número, sí o no, texto o lista. */
function valorDelMotor(campo: CampoEvento, c: Comparacion): unknown {
  if (Array.isArray(c.valor)) return c.valor
  if (campo.tipo === 'numero') return Number(c.valor)
  if (campo.tipo === 'si_no') return c.valor === 'true'
  return c.valor
}

/** La condición como la guarda el motor: vacía es «siempre». */
export function armarCondicion(editable: CondicionEditable, campos: CampoEvento[]): Record<string, unknown> {
  const partes = editable.comparaciones.map((c) => {
    const campo = campos.find((x) => x.campo === c.campo)!
    return { campo: c.campo, op: c.op, valor: valorDelMotor(campo, c) }
  })
  if (partes.length === 0) return {}
  if (partes.length === 1) return partes[0]!
  return { [editable.union]: partes }
}

/** Si una comparación ya dice algo: un número, una opción o al menos una de la lista. */
export function comparacionCompleta(c: Comparacion): boolean {
  return Array.isArray(c.valor) ? c.valor.length > 0 : c.valor.trim() !== ''
}

/** Una comparación nueva sobre un campo: su primera comparación y, si es de sí o no, «sí». */
export function nuevaComparacion(campo: CampoEvento): Comparacion {
  const op = campo.operadores[0]!.valor
  return { campo: campo.campo, op, valor: valorInicial(campo, op) }
}

export function valorInicial(campo: CampoEvento, op: string): string | string[] {
  if (op === 'in' || op === 'nin') return []
  if (campo.tipo === 'si_no') return 'true'
  return ''
}

/** Los parámetros de la acción guardada, como texto para los controles. */
export function leerParametros(accion: Record<string, unknown>): Record<string, string> {
  return Object.fromEntries(
    Object.entries(accion)
      .filter(([clave]) => clave !== 'tipo')
      .map(([clave, valor]) => [clave, String(valor)]),
  )
}

/** La acción como la guarda el motor, con cada parámetro de su tipo. Lo vacío no viaja: la API
 * pone el valor por defecto. La clave de un aviso no la escribe el equipo: la conserva la API. */
export function armarAccion(evento: EventoDeReglas, tipo: string, parametros: Record<string, string>): Record<string, unknown> {
  const accion = evento.acciones.find((a) => a.tipo === tipo)!
  const salida: Record<string, unknown> = { tipo }
  for (const p of accion.parametros) {
    const texto = (parametros[p.nombre] ?? '').trim()
    if (texto === '') continue
    salida[p.nombre] = p.tipo === 'numero' ? Number(texto) : texto
  }
  return salida
}

/** Si la acción tiene todo lo que pide. */
export function accionCompleta(evento: EventoDeReglas, tipo: string, parametros: Record<string, string>): boolean {
  const accion = evento.acciones.find((a) => a.tipo === tipo)
  return !!accion && accion.parametros.every((p) => !p.requerido || (parametros[p.nombre] ?? '').trim() !== '')
}

/** Los valores iniciales de una acción: los de la regla, o los que propone la API. */
export function parametrosIniciales(evento: EventoDeReglas, tipo: string, regla?: ReglaRead): Record<string, string> {
  if (regla && regla.accion.tipo === tipo) return leerParametros(regla.accion)
  const accion = evento.acciones.find((a) => a.tipo === tipo)
  return Object.fromEntries(
    (accion?.parametros ?? []).filter((p) => p.por_defecto !== null).map((p) => [p.nombre, String(p.por_defecto)]),
  )
}
