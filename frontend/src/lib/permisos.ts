import type { Rol, Usuario } from '@/types'

/**
 * Qué perfiles pueden cada cosa del panel (Sección 12: «cada perfil deberá contar con permisos
 * diferenciados de acuerdo con sus funciones»; docs/perfiles-y-permisos.md). Es el mismo reparto
 * que aplica la API (`requiere(...)` en cada router, congelado en `tests/test_permisos.py`):
 * aquí solo decide qué se muestra; el servidor sigue siendo quien autoriza. Si cambia un permiso
 * allá, se cambia aquí en el mismo commit.
 */
export const PERMISOS = {
  /** Usuarios, planes, reglas, catálogos, plantillas de WhatsApp, IA, Datos de TIMU y supresión. */
  administrar: ['admin'],
  /** El tablero de la Sección 8, sus exportables y los reportes programados. */
  verIndicadores: ['gerencia'],
  /** La ficha de familia, con lo que cada perfil ve de ella. */
  verFamilias: ['comercial', 'atencion_cliente', 'operaciones'],
  /** Interesados, conversaciones, afiliación asistida, campañas y segmentos. */
  mercadeo: ['comercial'],
  /** Dar de alta una familia (la afilia Comercial o la registra Atención al cliente). */
  altaFamilia: ['comercial', 'atencion_cliente'],
  /** Afiliar a un plan: el contrato (6.12). */
  afiliar: ['comercial'],
  /** Renovar un contrato (6.4). */
  renovar: ['comercial'],
  /** Contratos y renovaciones en Cartera. */
  verCartera: ['comercial', 'atencion_cliente'],
  /** Cartera, pagos y estado de la familia: baja, congelamiento, acceso al portal (6.2, 6.23). */
  cartera: ['atencion_cliente'],
  /** Servicios: solicitudes, agenda y los suyos (el médico). */
  servicios: ['atencion_cliente', 'operaciones', 'medico'],
  /** Franjas, bloqueos y programación de la agenda. */
  gestionarAgenda: ['operaciones'],
  /** La bandeja de preventivos. */
  preventivos: ['atencion_cliente', 'operaciones', 'medico'],
  /** Autorizar con la familia (6.6, 6.9). */
  autorizarConLaFamilia: ['atencion_cliente'],
  /** Historia clínica, atención virtual, respuestas aprobadas y plantillas de consulta. */
  clinico: ['medico'],
  /** Lo que firma un profesional. */
  medico: ['medico'],
  /** Planear, iniciar y cancelar rutas. */
  planearRutas: ['operaciones'],
  /** Avanzar paradas en campo. */
  campo: ['operaciones', 'medico'],
  /** La bandeja de tareas, cada perfil con las de su área. */
  tareas: ['comercial', 'atencion_cliente', 'operaciones', 'medico'],
  /** El módulo de Aliadas, con lo que cada perfil ve de él. */
  aliadas: ['gerencia', 'atencion_cliente', 'operaciones'],
  /** Emitir y anular remisiones (6.22). */
  remisiones: ['atencion_cliente'],
  /** Clínicas aliadas y sus convenios. */
  redAliadas: ['operaciones'],
  /** La liquidación de los convenios: Operaciones la gestiona y Gerencia la ve como informe. */
  liquidacion: ['gerencia', 'operaciones'],
  /** Los mensajes de WhatsApp y las bajas (6.19): Comercial y Atención al cliente. */
  mensajes: ['comercial', 'atencion_cliente'],
  /** Quitar una baja: lo pide la familia y lo registra Atención; Comercial da de baja, no reactiva. */
  reactivarEnvios: ['atencion_cliente'],
  /** Las respuestas de las encuestas: Atención las trabaja y Gerencia las analiza (6.20). */
  encuestas: ['gerencia', 'atencion_cliente'],
  /** La satisfacción del mes y por tipo de servicio: el análisis es de Gerencia (Sección 8). */
  analizarEncuestas: ['gerencia'],
} as const satisfies Record<string, readonly Rol[]>

export type Accion = keyof typeof PERMISOS

/** Pantalla de inicio de cada perfil: las familias y las aliadas tienen su propio espacio. */
export function inicioDeRol(rol: Rol): string {
  if (rol === 'familia') return '/portal'
  if (rol === 'aliada') return '/aliada'
  // La raíz es la portada pública (R3-PUB-04): el panel del equipo vive en /panel.
  return '/panel'
}

export function puede(usuario: Usuario | null | undefined, accion: Accion): boolean {
  return Boolean(usuario && (PERMISOS[accion] as readonly Rol[]).includes(usuario.rol))
}

export const NOMBRE_ROL: Record<Rol, string> = {
  admin: 'Administración',
  gerencia: 'Gerencia',
  comercial: 'Comercial',
  atencion_cliente: 'Atención al cliente',
  operaciones: 'Operaciones',
  medico: 'Médico veterinario',
  familia: 'Familia afiliada',
  aliada: 'Clínica aliada',
}
