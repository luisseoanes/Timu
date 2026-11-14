import { http, HttpResponse } from 'msw'

import type { CiudadRead, EspecieRead, FamiliaRead, PlanRead, TipoServicioRead, Usuario } from '@/types'

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
  barrio: 'Chapinero',
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

/** Un plan como lo publica TIMU: tarifa por peludo de 1 a 4+, periodos largos y ciudades. */
export const PLAN: PlanRead = {
  id: 'p1',
  codigo: 'colita_feliz',
  nombre: 'Colita Feliz',
  descripcion: null,
  ciudades: ['Bogota', 'Medellin'],
  tarifas: [
    { peludos: 1, valor: '35500.00' },
    { peludos: 2, valor: '30500.00' },
    { peludos: 3, valor: '26000.00' },
    { peludos: 4, valor: '24000.00' },
  ],
  tarifas_periodicidad: [
    { periodicidad: 'semestral', valor: '202350.00' },
    { periodicidad: 'anual', valor: '378000.00' },
  ],
  especies: ['perro', 'gato'],
  activo: true,
  color: 'naranja',
  beneficios: [],
}

export const CIUDADES: CiudadRead[] = [
  { codigo: '11001', nombre: 'Bogota', departamento: 'Bogota D.C.', latitud: null, longitud: null, activa: true },
]

export const ESPECIES: EspecieRead[] = [
  { codigo: 'perro', nombre: 'Perro', activa: true },
  { codigo: 'gato', nombre: 'Gato', activa: true },
]

export const TIPOS_SERVICIO: TipoServicioRead[] = [
  {
    codigo: 'consulta_domiciliaria',
    nombre: 'Consulta domiciliaria',
    modalidad: 'domiciliario',
    duracion_min: 45,
    requiere_autorizacion: false,
    activo: true,
    pasos: [
      { codigo: 'valoracion', nombre: 'Valoracion clinica', obligatorio: true, campos: ['hallazgos'] },
      { codigo: 'plan', nombre: 'Plan y recomendaciones', obligatorio: true, campos: ['recomendaciones'] },
    ],
  },
  {
    codigo: 'vacunacion',
    nombre: 'Vacunación',
    modalidad: 'preventivo',
    duracion_min: 30,
    requiere_autorizacion: true,
    activo: true,
    pasos: [],
  },
]

const API = '*/api/v1'
const vacia = { items: [], total: 0, limit: 50, offset: 0 }

export const handlers = [
  http.get(`${API}/auth/me`, () => HttpResponse.json(USUARIO_ADMIN)),
  http.post(`${API}/auth/login`, () => HttpResponse.json({ usuario: USUARIO_ADMIN })),
  http.post(`${API}/auth/logout`, () => HttpResponse.json({ detail: 'Sesion cerrada' })),
  // Sin cookie de renovación: cuando /auth/me responde 401, el cliente intenta renovar y
  // esto es lo que contestaría el backend a un navegador sin sesión.
  http.post(`${API}/auth/refresh`, () => HttpResponse.json({ detail: 'Sesion invalida' }, { status: 401 })),
  // Catálogos que cargan los selectores de varios formularios aunque la prueba no los mire.
  http.get(`${API}/auth/equipo`, () => HttpResponse.json([])),
  http.get(`${API}/planes`, () => HttpResponse.json([])),
  http.get(`${API}/aliadas`, () => HttpResponse.json([])),
  http.get(`${API}/clinica/plantillas`, () => HttpResponse.json([])),
  // Lo que carga Clínica al abrirla un médico: su ruta de hoy y sus consultas sin firmar.
  http.get(`${API}/clinica/borradores`, () => HttpResponse.json([])),
  http.get(`${API}/rutas`, () => HttpResponse.json([])),
  http.get(`${API}/catalogos/ciudades`, () => HttpResponse.json(CIUDADES)),
  http.get(`${API}/catalogos/especies`, () => HttpResponse.json(ESPECIES)),
  http.get(`${API}/catalogos/tipos-servicio`, () => HttpResponse.json(TIPOS_SERVICIO)),
  http.get(`${API}/agenda/franjas`, () => HttpResponse.json([])),
  http.get(`${API}/pendientes`, () => HttpResponse.json([])),
  http.get(`${API}/servicios/:id/pasos`, () => HttpResponse.json([])),
  http.get(`${API}/familias`, () =>
    HttpResponse.json({ items: [FAMILIA], total: 1, limit: 50, offset: 0 }),
  ),
  http.get(`${API}/familias/:id`, () => HttpResponse.json(FAMILIA)),
  http.get(`${API}/familias/:id/historial`, () => HttpResponse.json([])),
  // La línea y los planes de cada familia (R2-PAN-02): vacíos salvo que la prueba los defina.
  http.get(`${API}/afiliaciones/lineas`, ({ request }) =>
    HttpResponse.json(
      new URL(request.url).searchParams.getAll('familia_id').map((familia_id) => ({ familia_id, planes: [], estaciones: [] })),
    ),
  ),
  http.get(`${API}/familias/:id/linea`, ({ params }) =>
    HttpResponse.json({ familia_id: params.id, planes: [], estaciones: [] }),
  ),
  // Sin contrato por defecto; las pruebas de cartera lo reemplazan.
  http.get(`${API}/cartera/familias/:id/estado-cuenta`, () =>
    HttpResponse.json({ detail: 'La familia no tiene contrato' }, { status: 404 }),
  ),
  http.get(`${API}/servicios`, () => HttpResponse.json(vacia)),
  http.get(`${API}/servicios/resumen`, ({ request }) => {
    const params = new URL(request.url).searchParams
    return HttpResponse.json({
      desde: params.get('desde'),
      hasta: params.get('hasta'),
      utilizados: [],
      pendientes: [],
      cancelados: [],
      pendientes_atencion: [],
      cupos: [],
    })
  }),
  http.get(`${API}/comunicaciones/mensajes`, () => HttpResponse.json(vacia)),
  http.get(`${API}/portal/documentos`, () => HttpResponse.json([])),
  // El portal por defecto: sin plan ni contrato, sin citas y con la línea vacía. Las pruebas
  // del inicio y de cada peludo los reemplazan.
  http.get(`${API}/portal/linea`, () => HttpResponse.json({ familia_id: FAMILIA.id, planes: [], estaciones: [] })),
  http.get(`${API}/portal/plan`, () => HttpResponse.json({ detail: 'Sin plan' }, { status: 404 })),
  http.get(`${API}/portal/estado-cuenta`, () => HttpResponse.json({ detail: 'Sin contrato' }, { status: 404 })),
  http.get(`${API}/portal/servicios`, () => HttpResponse.json([])),
  http.get(`${API}/tareas`, () => HttpResponse.json(vacia)),
  http.get(`${API}/preventivos`, () => HttpResponse.json(vacia)),
  http.get(`${API}/cartera/contratos`, () => HttpResponse.json(vacia)),
  http.get(`${API}/dashboard/definiciones`, () => HttpResponse.json([])),
  // Sin historia: la franja no dice variación ni dibuja series. Las pruebas del Inicio la dan.
  http.get(`${API}/dashboard/evolucion`, () =>
    HttpResponse.json({
      anterior: { periodo: { desde: '2026-09-01', hasta: '2026-09-24', ciudad: null }, indicadores: {} },
      meses: [],
    }),
  ),
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
