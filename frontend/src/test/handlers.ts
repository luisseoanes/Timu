import { http, HttpResponse } from 'msw'

import type { CiudadRead, EspecieRead, FamiliaRead, Usuario } from '@/types'

export const USUARIO_ADMIN: Usuario = {
  id: '11111111-1111-1111-1111-111111111111',
  email: 'admin@timu.co',
  nombre: 'Admin',
  rol: 'admin',
  activo: true,
}

export const FAMILIA: FamiliaRead = {
  id: '22222222-2222-2222-2222-222222222222',
  titular_nombre: 'Ana Ruiz',
  tipo_documento: 'CC',
  documento: '1020304050',
  email: null,
  telefono: '573001112233',
  ciudad: 'Bogota',
  direccion: null,
  latitud: null,
  longitud: null,
  geo_precision: null,
  origen: 'manual',
  estado: 'activa',
  notas: null,
  dada_de_baja_en: null,
  motivo_baja: null,
  usuario_portal_id: null,
  mascotas: [
    {
      id: '33333333-3333-3333-3333-333333333333',
      familia_id: '22222222-2222-2222-2222-222222222222',
      nombre: 'Luna',
      especie: 'perro',
      raza: 'Criolla',
      sexo: 'hembra',
      fecha_nacimiento: '2021-03-10',
      activa: true,
    },
  ],
}

export const CIUDADES: CiudadRead[] = [
  { codigo: '11001', nombre: 'Bogota', departamento: 'Bogota D.C.', latitud: null, longitud: null, activa: true },
]

export const ESPECIES: EspecieRead[] = [
  { codigo: 'perro', nombre: 'Perro', activa: true },
  { codigo: 'gato', nombre: 'Gato', activa: true },
]

const API = '*/api/v1'
const vacia = { items: [], total: 0, limit: 50, offset: 0 }

export const handlers = [
  http.get(`${API}/auth/me`, () => HttpResponse.json(USUARIO_ADMIN)),
  http.post(`${API}/auth/login`, () => HttpResponse.json({ usuario: USUARIO_ADMIN })),
  http.post(`${API}/auth/logout`, () => HttpResponse.json({ detail: 'Sesion cerrada' })),
  http.get(`${API}/catalogos/ciudades`, () => HttpResponse.json(CIUDADES)),
  http.get(`${API}/catalogos/especies`, () => HttpResponse.json(ESPECIES)),
  http.get(`${API}/familias`, () =>
    HttpResponse.json({ items: [FAMILIA], total: 1, limit: 50, offset: 0 }),
  ),
  http.get(`${API}/familias/:id`, () => HttpResponse.json(FAMILIA)),
  http.get(`${API}/familias/:id/historial`, () => HttpResponse.json([])),
  // Sin contrato por defecto; las pruebas de cartera lo reemplazan.
  http.get(`${API}/cartera/familias/:id/estado-cuenta`, () =>
    HttpResponse.json({ detail: 'La familia no tiene contrato' }, { status: 404 }),
  ),
  http.get(`${API}/servicios`, () => HttpResponse.json(vacia)),
  http.get(`${API}/tareas`, () => HttpResponse.json(vacia)),
  http.get(`${API}/preventivos`, () => HttpResponse.json(vacia)),
  http.get(`${API}/cartera/contratos`, () => HttpResponse.json(vacia)),
  http.get(`${API}/dashboard/definiciones`, () => HttpResponse.json([])),
  http.get(`${API}/dashboard/indicadores`, () =>
    HttpResponse.json({
      periodo: { desde: '2026-10-01', hasta: '2026-10-24', ciudad: null },
      indicadores: {
        afiliaciones: 0,
        retiros: 0,
        vigentes: 0,
        recaudo: 0,
        facturado: 0,
        recaudo_del_facturado: null,
        mora: { contratos_en_mora: 0, saldo_vencido: 0, porcentaje: null },
        cumplimiento_rutas: { paradas_planeadas: 0, paradas_completadas: 0, cumplimiento: null, puntualidad: null },
        servicios_por_tipo: {},
        satisfaccion: { enviadas: 0, respondidas: 0, promedio: null, tasa_respuesta: null },
      },
    }),
  ),
]

/** Respuesta de sesión ausente, para probar la rama de no autenticado. */
export const sinSesion = http.get(`${API}/auth/me`, () => new HttpResponse(null, { status: 401 }))
