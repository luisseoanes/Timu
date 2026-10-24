/**
 * Etiqueta y tono de cada estado del sistema. Un solo mapeo para toda la aplicación,
 * para que el mismo estado se vea igual en cualquier módulo (docs/frontend/components.md).
 */

export type Tono = 'ok' | 'alerta' | 'info' | 'peligro' | 'neutro'

export interface Estado {
  label: string
  tono: Tono
}

const AFILIACION: Record<string, Estado> = {
  activa: { label: 'Activa', tono: 'ok' },
  prospecto: { label: 'Prospecto', tono: 'info' },
  en_mora: { label: 'En mora', tono: 'alerta' },
  congelada: { label: 'Congelada', tono: 'neutro' },
  cancelada: { label: 'Cancelada', tono: 'peligro' },
}

const SERVICIO: Record<string, Estado> = {
  solicitado: { label: 'Solicitado', tono: 'info' },
  pendiente_autorizacion: { label: 'Por autorizar', tono: 'alerta' },
  agendado: { label: 'Agendado', tono: 'info' },
  reprogramado: { label: 'Reprogramado', tono: 'alerta' },
  en_ruta: { label: 'En ruta', tono: 'info' },
  en_atencion: { label: 'En atención', tono: 'info' },
  completado: { label: 'Completado', tono: 'ok' },
  cancelado: { label: 'Cancelado', tono: 'peligro' },
}

const CUOTA: Record<string, Estado> = {
  pendiente: { label: 'Pendiente', tono: 'info' },
  parcial: { label: 'Abono parcial', tono: 'alerta' },
  pagada: { label: 'Pagada', tono: 'ok' },
  vencida: { label: 'Vencida', tono: 'peligro' },
  anulada: { label: 'Anulada', tono: 'neutro' },
}

const PAGO: Record<string, Estado> = {
  pendiente: { label: 'Pendiente', tono: 'info' },
  aprobado: { label: 'Aprobado', tono: 'ok' },
  rechazado: { label: 'Rechazado', tono: 'peligro' },
  reversado: { label: 'Reversado', tono: 'peligro' },
  anulado: { label: 'Anulado', tono: 'neutro' },
}

const TAREA: Record<string, Estado> = {
  abierta: { label: 'Abierta', tono: 'info' },
  en_progreso: { label: 'En progreso', tono: 'alerta' },
  cerrada: { label: 'Cerrada', tono: 'ok' },
}

const PRIORIDAD: Record<string, Estado> = {
  alta: { label: 'Alta', tono: 'peligro' },
  media: { label: 'Media', tono: 'alerta' },
  baja: { label: 'Baja', tono: 'neutro' },
}

const PREVENTIVO: Record<string, Estado> = {
  programado: { label: 'Programado', tono: 'info' },
  aplicado: { label: 'Aplicado', tono: 'ok' },
  cancelado: { label: 'Cancelado', tono: 'neutro' },
  vencido: { label: 'Vencido', tono: 'peligro' },
}

const RUTA: Record<string, Estado> = {
  planificada: { label: 'Planificada', tono: 'info' },
  en_curso: { label: 'En curso', tono: 'alerta' },
  finalizada: { label: 'Finalizada', tono: 'ok' },
  cancelada: { label: 'Cancelada', tono: 'neutro' },
  pendiente: { label: 'Pendiente', tono: 'info' },
  en_camino: { label: 'En camino', tono: 'alerta' },
  en_sitio: { label: 'En sitio', tono: 'alerta' },
  completada: { label: 'Completada', tono: 'ok' },
  omitida: { label: 'Omitida', tono: 'neutro' },
}

const HISTORIA: Record<string, Estado> = {
  borrador: { label: 'Borrador', tono: 'alerta' },
  firmada: { label: 'Firmada', tono: 'ok' },
  corregida: { label: 'Corregida', tono: 'neutro' },
}

const VIRTUAL: Record<string, Estado> = {
  en_cola: { label: 'En cola', tono: 'alerta' },
  en_atencion: { label: 'En atención', tono: 'info' },
  respondida: { label: 'Respondida', tono: 'ok' },
  cerrada: { label: 'Cerrada', tono: 'neutro' },
}

const CAMPANA: Record<string, Estado> = {
  borrador: { label: 'Borrador', tono: 'neutro' },
  programada: { label: 'Programada', tono: 'info' },
  en_envio: { label: 'Enviando', tono: 'alerta' },
  finalizada: { label: 'Finalizada', tono: 'ok' },
  cancelada: { label: 'Cancelada', tono: 'peligro' },
}

const ETAPA: Record<string, Estado> = {
  nuevo: { label: 'Nuevo', tono: 'info' },
  contactado: { label: 'Contactado', tono: 'info' },
  cotizado: { label: 'Cotizado', tono: 'alerta' },
  en_afiliacion: { label: 'En afiliación', tono: 'alerta' },
  afiliado: { label: 'Afiliado', tono: 'ok' },
  perdido: { label: 'Perdido', tono: 'neutro' },
}

const REMISION: Record<string, Estado> = {
  emitida: { label: 'Emitida', tono: 'info' },
  utilizada: { label: 'Utilizada', tono: 'ok' },
  anulada: { label: 'Anulada', tono: 'neutro' },
}

const PENDIENTE: Record<string, Estado> = {
  pendiente_autorizacion: { label: 'Por autorizar', tono: 'alerta' },
  autorizado: { label: 'Autorizado', tono: 'info' },
  en_gestion: { label: 'En gestión', tono: 'info' },
  resuelto: { label: 'Resuelto', tono: 'ok' },
  rechazado: { label: 'Rechazado', tono: 'neutro' },
}

const MENSAJE: Record<string, Estado> = {
  encolado: { label: 'En cola', tono: 'neutro' },
  enviado: { label: 'Enviado', tono: 'info' },
  entregado: { label: 'Entregado', tono: 'info' },
  leido: { label: 'Leído', tono: 'ok' },
  fallido: { label: 'Fallido', tono: 'peligro' },
  recibido: { label: 'Recibido', tono: 'info' },
  omitido: { label: 'Omitido', tono: 'neutro' },
}

export const ESTADOS = {
  afiliacion: AFILIACION,
  servicio: SERVICIO,
  cuota: CUOTA,
  pago: PAGO,
  tarea: TAREA,
  prioridad: PRIORIDAD,
  preventivo: PREVENTIVO,
  ruta: RUTA,
  historia: HISTORIA,
  virtual: VIRTUAL,
  campana: CAMPANA,
  etapa: ETAPA,
  remision: REMISION,
  pendiente: PENDIENTE,
  mensaje: MENSAJE,
} as const

export type Dominio = keyof typeof ESTADOS

/** Estado desconocido: se muestra tal cual, en tono neutro, en vez de romper la pantalla. */
export function estado(dominio: Dominio, valor: string): Estado {
  return ESTADOS[dominio][valor] ?? { label: valor.replaceAll('_', ' '), tono: 'neutro' }
}
