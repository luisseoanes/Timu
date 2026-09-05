import { http, HttpResponse } from 'msw'

import type { Familia, Usuario } from '@/types'

export const USUARIO_ADMIN: Usuario = {
  id: '11111111-1111-1111-1111-111111111111',
  email: 'admin@timu.co',
  nombre: 'Admin',
  rol: 'admin',
  activo: true,
}

export const FAMILIA: Familia = {
  id: '22222222-2222-2222-2222-222222222222',
  titular_nombre: 'Ana Ruiz',
  documento: '1020304050',
  email: null,
  telefono: '573001112233',
  ciudad: 'Bogota',
  direccion: null,
  latitud: null,
  longitud: null,
  estado: 'activa',
  notas: null,
  mascotas: [],
}

const API = '*/api/v1'

export const handlers = [
  http.get(`${API}/auth/me`, () => HttpResponse.json(USUARIO_ADMIN)),
  http.post(`${API}/auth/login`, () => HttpResponse.json({ usuario: USUARIO_ADMIN })),
  http.post(`${API}/auth/logout`, () => HttpResponse.json({ detail: 'Sesion cerrada' })),
  http.get(`${API}/familias`, () =>
    HttpResponse.json({ items: [FAMILIA], total: 1, limit: 50, offset: 0 }),
  ),
]

/** Respuesta de sesión ausente, para probar la rama de no autenticado. */
export const sinSesion = http.get(`${API}/auth/me`, () => new HttpResponse(null, { status: 401 }))
