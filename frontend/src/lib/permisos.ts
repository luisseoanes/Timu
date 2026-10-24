import type { Rol, Usuario } from '@/types'

/**
 * Qué roles pueden cada acción del panel. Es el mismo mapa que aplica el backend
 * (`requiere(...)` en cada router): aquí sólo decide qué botones se muestran; el
 * servidor sigue siendo quien autoriza.
 */
export const PERMISOS = {
  /** POST /familias/{id}/estado, /baja, /acceso-portal y POST /cartera/pagos. */
  gestionarAfiliacion: ['admin', 'comercial'],
} as const satisfies Record<string, readonly Rol[]>

export function puede(usuario: Usuario | null | undefined, accion: keyof typeof PERMISOS): boolean {
  return Boolean(usuario && (PERMISOS[accion] as readonly Rol[]).includes(usuario.rol))
}
