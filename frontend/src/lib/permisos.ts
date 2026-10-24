import type { Rol, Usuario } from '@/types'

/**
 * Qué roles pueden cada acción del panel. Es el mismo mapa que aplica el backend
 * (`requiere(...)` en cada router): aquí sólo decide qué se muestra; el servidor
 * sigue siendo quien autoriza. Si cambia un permiso allá, se cambia aquí en el
 * mismo commit.
 */
export const PERMISOS = {
  /** Familias: estado, baja, portal; cartera: pagos y contratos; afiliación asistida. */
  gestionarAfiliacion: ['admin', 'comercial'],
  /** Dashboard gerencial y exportables. */
  verIndicadores: ['admin', 'comercial', 'operaciones'],
  /** Franjas, bloqueos y programación de la agenda. */
  gestionarAgenda: ['admin', 'operaciones'],
  /** Historia clínica, preventivos (aplicar, autorizar) y respuestas virtuales. */
  clinico: ['admin', 'medico'],
  /** Lo que firma un profesional: sólo el médico. */
  medico: ['medico'],
  /** Planear, iniciar y cancelar rutas. */
  planearRutas: ['admin', 'operaciones'],
  /** Avanzar paradas en campo. */
  campo: ['admin', 'operaciones', 'medico'],
  /** Embudo comercial, campañas, segmentos y plantillas de WhatsApp. */
  mercadeo: ['admin', 'comercial'],
  /** Usuarios, reglas, catálogos, planes, IA y reportes programados. */
  administrar: ['admin'],
} as const satisfies Record<string, readonly Rol[]>

export type Accion = keyof typeof PERMISOS

/** Pantalla de inicio de cada perfil: las familias y las aliadas tienen su propio espacio. */
export function inicioDeRol(rol: Rol): string {
  if (rol === 'familia') return '/portal'
  if (rol === 'aliada') return '/aliada'
  return '/'
}

export function puede(usuario: Usuario | null | undefined, accion: Accion): boolean {
  return Boolean(usuario && (PERMISOS[accion] as readonly Rol[]).includes(usuario.rol))
}

export const NOMBRE_ROL: Record<Rol, string> = {
  admin: 'Administración',
  comercial: 'Comercial',
  operaciones: 'Operaciones',
  medico: 'Médico veterinario',
  familia: 'Familia afiliada',
  aliada: 'Clínica aliada',
}
