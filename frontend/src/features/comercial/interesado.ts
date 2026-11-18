import { telefono } from '@/lib/formato'
import type { InteresadoRead } from '@/types'

import { ETAPAS, ORIGENES } from './api'

/** Cómo se nombra a un interesado: su nombre, o su celular si el bot no lo sabe (no lo pregunta). */
export function nombreDe(i: Pick<InteresadoRead, 'nombre' | 'telefono' | 'email'>): string {
  return i.nombre ?? (i.telefono ? telefono(i.telefono) : (i.email ?? 'Sin nombre'))
}

/** Orígenes que no se eligen al registrar a mano pero que el backend guarda: el registro en línea
 * (`afiliaciones`) anota de dónde vino la persona. */
const OTROS_ORIGENES: Record<string, string> = {
  afiliacion: 'Registro en línea',
  web: 'Página web',
  landing: 'Página web',
}

export function nombreOrigen(origen: string): string {
  return ORIGENES.find((o) => o.valor === origen)?.label ?? OTROS_ORIGENES[origen] ?? origen
}

export function nombreEtapa(etapa: string): string {
  return ETAPAS.find((e) => e.valor === etapa)?.label ?? (etapa === 'perdido' ? 'Perdido' : etapa)
}

/** Las mascotas que dijo tener en la conversación con el bot («2 perros y un gato»). */
export function mascotasDe(datos: Record<string, unknown>): string | null {
  const especies = Array.isArray(datos.mascotas) ? (datos.mascotas as string[]) : []
  if (especies.length === 0) return null
  const perros = especies.filter((e) => e === 'canino').length
  const gatos = especies.filter((e) => e === 'felino').length
  const partes = [perros && `${perros} ${perros === 1 ? 'perro' : 'perros'}`, gatos && `${gatos} ${gatos === 1 ? 'gato' : 'gatos'}`]
  return partes.filter(Boolean).join(' y ') || `${especies.length} mascotas`
}

/** Un mensaje del formulario de contacto de la portada (R3-PUB-04, `comercial.contacto_web`). */
export interface MensajeWeb {
  fecha: string
  mascota: string | null
  especie: 'canino' | 'felino' | null
  mensaje: string
}

/** Los mensajes que dejó en la portada, del más reciente al más viejo (el backend guarda veinte). */
export function mensajesWebDe(datos: Record<string, unknown>): MensajeWeb[] {
  return Array.isArray(datos.mensajes_web) ? [...(datos.mensajes_web as MensajeWeb[])].reverse() : []
}
