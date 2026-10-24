import { isAxiosError } from 'axios'

/**
 * Mensaje para mostrar cuando una petición falla. El backend responde siempre con el
 * mismo formato (`detail`, `codigo`, `request_id`); su `detail` ya está escrito para
 * quien usa el sistema. Si no hay respuesta, se dice qué pasó y qué hacer.
 */
export function mensajeError(error: unknown, porDefecto = 'No fue posible completar la acción. Intenta de nuevo.'): string {
  if (isAxiosError(error)) {
    if (!error.response) return 'No hay conexión con el servidor. Revisa tu red e intenta de nuevo.'
    const cuerpo = error.response.data as { detail?: unknown; errores?: { mensaje: string }[] } | undefined
    if (cuerpo?.errores?.length) return cuerpo.errores.map((e) => e.mensaje).join(' ')
    if (typeof cuerpo?.detail === 'string') return cuerpo.detail
    if (error.response.status === 403) return 'Tu perfil no tiene permiso para esta acción.'
  }
  return porDefecto
}
