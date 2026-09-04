// Espejo tipado de los schemas Pydantic del backend (app/schemas, app/modules/*/schemas.py).

export type Rol = 'admin' | 'comercial' | 'operaciones' | 'medico' | 'familia'

export type EstadoAfiliacion = 'prospecto' | 'activa' | 'en_mora' | 'congelada' | 'cancelada'

export type EstadoServicio =
  | 'solicitado'
  | 'agendado'
  | 'en_ruta'
  | 'en_atencion'
  | 'completado'
  | 'pendiente_autorizacion'
  | 'reprogramado'
  | 'cancelado'

export interface Usuario {
  id: string
  email: string
  nombre: string
  rol: Rol
  activo: boolean
}

export interface Token {
  access_token: string
  token_type: string
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
