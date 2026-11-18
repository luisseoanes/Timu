import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { AdminPage } from './AdminPage'
import { PLAN as PLAN_TIMU } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'

const API = '*/api/v1'

const base = [
  http.get(`${API}/auth/usuarios/recuentos`, () => HttpResponse.json({ equipo: 0, aliadas: 0, familias: 0, inactivos: 0 })),
  http.get(`${API}/auth/usuarios`, () => HttpResponse.json({ items: [], total: 0, limit: 25, offset: 0 })),
]

const PLAN = {
  ...PLAN_TIMU,
  beneficios: [{ id: 'b1', tipo_servicio_codigo: 'consulta_domiciliaria', cupo: 6, periodo_cupo: 'anual', cobertura_pct: 100, copago: '0' }],
  adicionales: [
    { id: 'a1', nombre: 'Servicio fúnebre', cubre: '100 %', detalle: null, carencia_dias: 30, tercero: false },
    { id: 'a2', nombre: 'Baño y peluquería', cubre: '30 %', detalle: 'Con un tercero.', carencia_dias: null, tercero: true },
  ],
}

/** Abre la ficha de un registro de una pestaña (`?plan=p1`, `?regla=rg1`) y espera a su título. */
async function abrirFicha(pestana: string, ruta: string, region: string, titulo: string) {
  const user = userEvent.setup()
  renderizar(<AdminPage />, { ruta })
  await user.click(await screen.findByRole('tab', { name: pestana }))
  const ficha = await screen.findByRole('region', { name: region })
  await within(ficha).findByRole('heading', { level: 2, name: titulo })
  return { user, ficha }
}

async function abrirPestana(nombre: string) {
  const user = userEvent.setup()
  renderizar(<AdminPage />)
  await user.click(await screen.findByRole('tab', { name: nombre }))
  return user
}

describe('Administración: planes', () => {
  it('abre un plan con sus tarifas por número de peludos, los periodos largos y las ciudades', async () => {
    server.use(...base, http.get(`${API}/planes`, () => HttpResponse.json([PLAN])))
    const user = await abrirPestana('Planes')
    expect(await screen.findByText(/Abre un plan para ver/)).toBeInTheDocument()
    await user.click(await screen.findByRole('link', { name: 'Colita Feliz' }))
    const ficha = screen.getByRole('region', { name: 'Plan abierto' })
    expect(await within(ficha).findByText('Bogotá · Medellín')).toBeInTheDocument()
    const tarifas = within(ficha).getByLabelText('Tarifas de Colita Feliz')
    expect(within(tarifas).getByText('4 o más (c/u)')).toBeInTheDocument()
    expect(within(ficha).getByText('Anual')).toBeInTheDocument()
    // Con la ficha abierta, «Nuevo plan» deja el verde a «Editar plan».
    expect(screen.getByRole('button', { name: /nuevo plan/i })).toHaveClass('btn-suave')
    expect(within(ficha).getByRole('button', { name: 'Editar plan' })).toHaveClass('btn-primario')
  })

  it('dice las condiciones que ve quien se afilia, y que sin escribirlas el registro no las muestra', async () => {
    server.use(
      ...base,
      http.get(`${API}/planes`, () =>
        HttpResponse.json([{ ...PLAN, exclusiones: 'Excluye preexistencias.', terminos_url: 'https://timu.com.co/terminos' }]),
      ),
    )
    const { ficha } = await abrirFicha('Planes', '/panel/admin?plan=p1', 'Plan abierto', 'Colita Feliz')
    const condiciones = within(ficha).getByRole('region', { name: 'Condiciones que ve quien se afilia' })
    expect(condiciones).toHaveTextContent('Sin escribir: el registro no la muestra.')
    expect(condiciones).toHaveTextContent('Excluye preexistencias.')
    expect(within(condiciones).getByRole('link', { name: 'https://timu.com.co/terminos' })).toBeInTheDocument()
  })

  it('con la misma tarifa para cualquier número de peludos, la dice en una frase', async () => {
    const iguales = PLAN.tarifas.map((t) => ({ ...t, valor: '45000.00' }))
    server.use(...base, http.get(`${API}/planes`, () => HttpResponse.json([{ ...PLAN, tarifas: iguales }])))
    const user = await abrirPestana('Planes')
    await user.click(await screen.findByRole('link', { name: 'Colita Feliz' }))
    const ficha = screen.getByRole('region', { name: 'Plan abierto' })
    expect(await within(ficha).findByText(/por peludo, tenga la afiliación los peludos que tenga/)).toBeInTheDocument()
    expect(within(ficha).queryByLabelText('Tarifas de Colita Feliz')).not.toBeInTheDocument()
  })

  it('edita ciudades, tarifas y beneficios en un solo guardado', async () => {
    const pedidos: [string, unknown][] = []
    const registrar = (ruta: string) => async ({ request }: { request: Request }) => {
      pedidos.push([ruta, await request.json()])
      return HttpResponse.json(PLAN)
    }
    server.use(
      ...base,
      http.get(`${API}/planes`, () => HttpResponse.json([PLAN])),
      http.patch(`${API}/planes/p1`, registrar('plan')),
      http.put(`${API}/planes/p1/ciudades`, registrar('ciudades')),
      http.put(`${API}/planes/p1/tarifas`, registrar('tarifas')),
      http.put(`${API}/planes/p1/beneficios`, registrar('beneficios')),
    )
    const { user, ficha } = await abrirFicha('Planes', '/panel/admin?plan=p1', 'Plan abierto', 'Colita Feliz')
    await user.click(within(ficha).getByRole('button', { name: 'Editar plan' }))
    const modal = await screen.findByRole('dialog')
    expect(within(modal).getByLabelText('4 o más (c/u)')).toHaveValue(24000)
    const uno = within(modal).getByLabelText('1 peludo')
    await user.clear(uno)
    await user.type(uno, '36000')
    await user.type(within(modal).getByLabelText('Trimestral'), '103800')
    await user.clear(within(modal).getByLabelText('Anual'))
    await user.click(within(modal).getByRole('button', { name: 'Quitar beneficio' }))
    await user.selectOptions(within(modal).getByLabelText('Agregar beneficio'), 'vacunacion')
    await user.type(within(modal).getByLabelText('Cupo (vacío = sin tope de usos)'), '4')
    // R3-PUB-04: hasta cuánto cubre por episodio y desde cuándo aplica.
    await user.type(within(modal).getByLabelText('Tope por episodio (COP, vacío = sin tope)'), '850000')
    await user.type(within(modal).getByLabelText('Aplica desde (días de afiliada)'), '30')
    expect(within(modal).getByLabelText('Color del plan')).toHaveValue('naranja')
    await user.selectOptions(within(modal).getByLabelText('Color del plan'), 'azul')
    // Las condiciones que el registro dice de frente (R3-PUB-02).
    await user.type(within(modal).getByLabelText('Carencia'), 'Sin periodo de carencia.')
    await user.type(within(modal).getByLabelText('Exclusiones'), 'Excluye preexistencias.')
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    await waitFor(() => expect(pedidos).toHaveLength(4))
    expect(pedidos).toEqual([
      [
        'plan',
        {
          nombre: 'Colita Feliz',
          color: 'azul',
          carencia: 'Sin periodo de carencia.',
          exclusiones: 'Excluye preexistencias.',
          terminos_url: '',
        },
      ],
      ['ciudades', ['Bogotá']],
      ['tarifas', { por_peludos: ['36000', '30500', '26000', '24000'], trimestral: '103800', semestral: '202350' }],
      [
        'beneficios',
        [
          {
            tipo_servicio_codigo: 'vacunacion',
            cupo: 4,
            periodo_cupo: 'anual',
            cobertura_pct: 100,
            copago: '0',
            tope_episodio: '850000',
            carencia_dias: 30,
            detalle: null,
          },
        ],
      ],
    ])
  })

  it('no guarda un plan sin ciudades', async () => {
    let llamadas = 0
    server.use(
      ...base,
      http.get(`${API}/planes`, () => HttpResponse.json([PLAN])),
      http.patch(`${API}/planes/p1`, () => {
        llamadas += 1
        return HttpResponse.json(PLAN)
      }),
    )
    const { user, ficha } = await abrirFicha('Planes', '/panel/admin?plan=p1', 'Plan abierto', 'Colita Feliz')
    await user.click(within(ficha).getByRole('button', { name: 'Editar plan' }))
    const modal = await screen.findByRole('dialog')
    await user.click(within(modal).getByLabelText('Bogotá'))
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    expect(await within(modal).findByText('Elige al menos una ciudad donde se vende el plan.')).toBeInTheDocument()
    expect(llamadas).toBe(0)
  })

  it('crea un plan con sus tarifas, sus ciudades y sus especies, y abre su ficha', async () => {
    let creado: unknown = null
    server.use(
      ...base,
      http.get(`${API}/planes`, () => HttpResponse.json(creado ? [PLAN] : [])),
      http.post(`${API}/planes`, async ({ request }) => {
        creado = await request.json()
        return HttpResponse.json(PLAN, { status: 201 })
      }),
    )
    const user = await abrirPestana('Planes')
    await user.click(await screen.findByRole('button', { name: /nuevo plan/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Código'), 'mi_amigo_fiel')
    await user.type(within(modal).getByLabelText('Nombre'), 'Mi Amigo Fiel')
    await user.click(within(modal).getByLabelText('Bogotá'))
    await user.click(within(modal).getByLabelText('Perro'))
    for (const [campo, valor] of [
      ['1 peludo', '69000'],
      ['2 peludos (c/u)', '61000'],
      ['3 peludos (c/u)', '57500'],
      ['4 o más (c/u)', '57000'],
      ['Semestral', '393300'],
    ] as const) {
      await user.type(within(modal).getByLabelText(campo), valor)
    }
    expect(within(modal).getByLabelText('Color del plan')).toHaveValue('verde')
    await user.click(within(modal).getByRole('button', { name: 'Crear plan' }))
    await waitFor(() =>
      expect(creado).toEqual({
        codigo: 'mi_amigo_fiel',
        nombre: 'Mi Amigo Fiel',
        especies: ['perro'],
        color: 'verde',
        carencia: '',
        exclusiones: '',
        terminos_url: '',
        ciudades: ['Bogotá'],
        tarifas: { por_peludos: ['69000', '61000', '57500', '57000'], semestral: '393300' },
      }),
    )
    // Lo siguiente es configurar sus beneficios: se abre su ficha.
    const titulo = await screen.findByRole('heading', { level: 2, name: 'Colita Feliz' }, { timeout: 5000 })
    expect(titulo.closest('section')).toHaveAccessibleName('Plan abierto')
  })

  it('desactiva un plan', async () => {
    let cambio: unknown = null
    server.use(
      ...base,
      http.get(`${API}/planes`, () => HttpResponse.json([PLAN])),
      http.patch(`${API}/planes/p1`, async ({ request }) => {
        cambio = await request.json()
        return HttpResponse.json({ ...PLAN, activo: false })
      }),
    )
    const { user, ficha } = await abrirFicha('Planes', '/panel/admin?plan=p1', 'Plan abierto', 'Colita Feliz')
    await user.click(within(ficha).getByRole('button', { name: 'Más acciones con Colita Feliz' }))
    await user.click(await screen.findByRole('menuitem', { name: 'Desactivar plan' }))
    await waitFor(() => expect(cambio).toEqual({ activo: false }))
  })
})

describe('Administración: catálogos', () => {
  it('desactiva una ciudad sin borrarla', async () => {
    let cambio: unknown = null
    server.use(
      ...base,
      http.get(`${API}/catalogos/ciudades`, () => HttpResponse.json([{ codigo: '11001', nombre: 'Bogotá', departamento: 'Bogotá D.C.', activa: true }])),
      http.get(`${API}/catalogos/esquemas-preventivos`, () =>
        HttpResponse.json([{ codigo: 'rabia', especie_codigo: 'canino', tipo: 'vacuna', nombre: 'Rabia', edad_minima_semanas: 12, dosis_iniciales: 1, intervalo_inicial_dias: 0, intervalo_refuerzo_dias: 365, requiere_autorizacion: true, activo: true }]),
      ),
      http.patch(`${API}/catalogos/ciudades/11001/activo`, async ({ request }) => {
        cambio = await request.json()
        return HttpResponse.json({})
      }),
    )
    const user = await abrirPestana('Catálogos')
    // Una sola dosis no tiene intervalo inicial: nada de «1 dosis cada 0 días».
    expect(await screen.findByText(/1 dosis · refuerzo cada 365 días/)).toBeInTheDocument()
    // Apagar dice qué deja de pasar y se confirma en rojo.
    await user.click(await screen.findByRole('button', { name: 'Apagar Bogotá' }))
    const ventana = await screen.findByRole('dialog', { name: 'Apagar Bogotá' })
    expect(cambio).toBeNull()
    const confirmar = within(ventana).getByRole('button', { name: 'Apagar' })
    expect(confirmar).toHaveClass('btn-peligro')
    await user.click(confirmar)
    await waitFor(() => expect(cambio).toEqual({ activo: false }))
  })
})

describe('Administración: catálogos apagados', () => {
  it('encender es directo y el estado se lee escrito', async () => {
    let cambio: unknown = null
    server.use(
      ...base,
      http.get(`${API}/catalogos/ciudades`, () => HttpResponse.json([{ codigo: '05001', nombre: 'Medellín', departamento: 'Antioquia', activa: false }])),
      http.get(`${API}/catalogos/esquemas-preventivos`, () => HttpResponse.json([])),
      http.patch(`${API}/catalogos/ciudades/05001/activo`, async ({ request }) => {
        cambio = await request.json()
        return HttpResponse.json({})
      }),
    )
    const user = await abrirPestana('Catálogos')
    const fila = (await screen.findByText('Medellín')).closest('.fila') as HTMLElement
    expect(within(fila).getByText('Apagado')).toBeInTheDocument()
    await user.click(within(fila).getByRole('button', { name: 'Encender Medellín' }))
    await waitFor(() => expect(cambio).toEqual({ activo: true }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})

describe('Administración: reportes y pasarela', () => {
  it('abre la vista de eventos que dice la URL', async () => {
    const estados: (string | null)[] = []
    server.use(
      ...base,
      http.get(`${API}/dashboard/reportes`, () => HttpResponse.json([])),
      http.get(`${API}/dashboard/definiciones`, () => HttpResponse.json([])),
      http.get(`${API}/cartera/eventos-pasarela/recuentos`, () => HttpResponse.json({ error: 0, procesado: 2, todos: 2 })),
      http.get(`${API}/cartera/eventos-pasarela`, ({ request }) => {
        estados.push(new URL(request.url).searchParams.get('estado'))
        return HttpResponse.json({ items: [], total: 0, limit: 50, offset: 0 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<AdminPage />, { ruta: '/panel/admin?eventos=procesado' })
    await user.click(await screen.findByRole('tab', { name: 'Reportes y pasarela' }))
    expect(await screen.findByRole('button', { name: 'Procesados 2' })).toHaveAttribute('aria-pressed', 'true')
    await waitFor(() => expect(estados).toContain('procesado'))
  })

  it('crea un reporte con sus indicadores y reprocesa un evento con error', async () => {
    const pedidos: unknown[] = []
    server.use(
      ...base,
      http.get(`${API}/dashboard/reportes`, () => HttpResponse.json([])),
      http.get(`${API}/dashboard/definiciones`, () =>
        HttpResponse.json([{ codigo: 'recaudo', nombre: 'Recaudo', formula: 'Suma de pagos', unidad: 'COP' }]),
      ),
      http.post(`${API}/dashboard/reportes`, async ({ request }) => {
        pedidos.push(await request.json())
        return HttpResponse.json({}, { status: 201 })
      }),
      http.get(`${API}/cartera/eventos-pasarela`, () =>
        HttpResponse.json({
          items: [{ id: 'ev1', proveedor: 'wompi', tipo: 'transaction.updated', referencia: 'TX-1', estado: 'error', intentos: 2, error: 'Pago no encontrado', procesado_en: null, created_at: '2026-10-24T10:00:00Z' }],
          total: 1,
          limit: 50,
          offset: 0,
        }),
      ),
      http.get(`${API}/cartera/eventos-pasarela/recuentos`, () =>
        HttpResponse.json({ error: 1, procesado: 4, todos: 5 }),
      ),
      http.post(`${API}/cartera/eventos-pasarela/ev1/reprocesar`, () => {
        pedidos.push('reprocesar')
        return HttpResponse.json({})
      }),
    )
    const user = await abrirPestana('Reportes y pasarela')
    expect(await screen.findByText('Pago no encontrado')).toBeInTheDocument()
    // El evento en palabras, no el código del proveedor.
    expect(screen.getByText('Cambio en un pago')).toBeInTheDocument()
    expect(screen.getByText('Wompi')).toBeInTheDocument()
    // Cada vista dice cuántos tiene, y la elegida vive en la URL, como en las demás bandejas (DEU-26).
    expect(await screen.findByRole('button', { name: 'Con error 1' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'Procesados 4' })).toHaveAttribute('aria-pressed', 'false')
    await user.click(screen.getByRole('button', { name: 'Reprocesar el evento TX-1' }))
    await user.click(screen.getByRole('button', { name: /nuevo reporte/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Nombre'), 'Gerencia semanal')
    await user.type(within(modal).getByLabelText(/destinatarios/i), 'gerencia@timu.co, socios@timu.co')
    await user.click(await within(modal).findByRole('button', { name: 'Recaudo' }))
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    await waitFor(() => expect(pedidos).toHaveLength(2))
    expect(pedidos).toContainEqual({
      nombre: 'Gerencia semanal',
      periodicidad: 'semanal',
      destinatarios: ['gerencia@timu.co', 'socios@timu.co'],
      indicadores: ['recaudo'],
      activo: true,
    })
  })
})
