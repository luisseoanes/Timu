// Espejo tipado de los schemas Pydantic del backend (app/schemas, app/modules/*/schemas.py).
// Lo generado desde el OpenAPI vive en api.ts (backend/scripts/generar_tipos_frontend.py);
// aquí quedan los tipos que el panel usa con su propia forma.

import type { Rol } from './api'

export * from './api'

export interface Usuario {
  id: string
  email: string
  nombre: string
  rol: Rol
  activo: boolean
}

export interface Sesion {
  /** El token no viaja en el cuerpo: va en la cookie httpOnly que pone el backend. */
  usuario: Usuario
}

export interface Page<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}
