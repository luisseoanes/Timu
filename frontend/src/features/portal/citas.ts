import type { Tono } from '@/lib/estados'
import type { ServicioPortalRead } from '@/types'

// Las citas dichas a la familia (R3-POR-02): el estado con sus palabras y qué se puede hacer
// con cada una, según lo que dice el backend (`portal/service.py`, `que_puede`).

const ESTADOS: Record<string, { label: string; tono: Tono; explicacion?: string }> = {
  solicitado: { label: 'Recibida', tono: 'info', explicacion: 'TIMU te confirma la hora por WhatsApp.' },
  pendiente_autorizacion: { label: 'Por autorizar', tono: 'alerta', explicacion: 'TIMU la autoriza antes de confirmarla.' },
  // Confirmada lleva el visto; lo que pasa ahora (en camino, en atención) va en informativo.
  agendado: { label: 'Confirmada', tono: 'ok' },
  reprogramado: { label: 'Con otra fecha', tono: 'alerta' },
  en_ruta: { label: 'En camino', tono: 'info', explicacion: 'El médico va en camino.' },
  en_atencion: { label: 'En atención', tono: 'info', explicacion: 'El médico está con tu peludo.' },
  completado: { label: 'Atendida', tono: 'ok' },
  cancelado: { label: 'Cancelada', tono: 'neutro' },
}

export function estadoDeCita(estado: string): { label: string; tono: Tono; explicacion?: string } {
  return ESTADOS[estado] ?? { label: estado, tono: 'neutro' }
}

/** Qué se puede hacer con una cita lo dice el backend en cada una (estado, ruta y antelación): el
 * portal no copia sus reglas (DEU-2). */
export const puedeCambiar = (s: ServicioPortalRead) => s.puede_cambiar ?? false

export const puedeCancelar = (s: ServicioPortalRead) => s.puede_cancelar ?? false

const CERRADAS = new Set(['completado', 'cancelado'])
/** Una visita en camino o en atención es de ahora, aunque su hora ya pasó. */
const ESTA_EN_CURSO = new Set(['en_ruta', 'en_atencion'])

/** Las pasadas: atendidas, canceladas o con la hora ya cumplida; de la más reciente a la más antigua. */
export function pasadas(todas: ServicioPortalRead[], ahora = new Date()): ServicioPortalRead[] {
  return todas
    .filter((s) => CERRADAS.has(s.estado) || (s.programado_para !== null && new Date(s.programado_para) < ahora && !ESTA_EN_CURSO.has(s.estado)))
    .sort((a, b) => (b.programado_para ?? '').localeCompare(a.programado_para ?? ''))
}
