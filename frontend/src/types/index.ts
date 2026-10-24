// Espejo tipado de los schemas Pydantic del backend (app/schemas, app/modules/*/schemas.py).
// Lo generado desde el OpenAPI vive en api.ts (backend/scripts/generar_tipos_frontend.py);
// aquí quedan los tipos que el panel usa con su propia forma.

import type { EstadoAfiliacion, Rol } from './api'

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

export interface Mascota {
  id: string
  familia_id: string
  nombre: string
  especie: string
  raza?: string | null
  sexo?: string | null
  fecha_nacimiento?: string | null
  peso_kg?: number | null
}

export interface Familia {
  id: string
  titular_nombre: string
  documento: string
  email?: string | null
  telefono: string
  ciudad: string
  direccion?: string | null
  latitud?: number | null
  longitud?: number | null
  notas?: string | null
  estado: EstadoAfiliacion
  mascotas: Mascota[]
}

export interface Page<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}
