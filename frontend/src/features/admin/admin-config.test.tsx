import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { AdminPage } from './AdminPage'
import { PLAN as PLAN_TIMU } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'

const API = '*/api/v1'

const base = [http.get(`${API}/auth/usuarios`, () => HttpResponse.json({ items: [], total: 0, limit: 200, offset: 0 }))]

const PLAN = {
  ...PLAN_TIMU,
  beneficios: [{ id: 'b1', tipo_servicio_codigo: 'consulta_domiciliaria', cupo: 6, periodo_cupo: 'anual', cobertura_pct: 100, copago: '0' }],
}

const REGLA = {
  id: 'rg1',
  codigo: 'alerta_mora_25',
  nombre: 'Aviso de mora a los 25 días',
  descripcion: null,
  evento: 'cartera.alerta',
  condicion: { op: 'gte', campo: 'dias_mora', valor: 25 },
  accion: { tipo: 'notificar', plantilla: 'aviso_congelamiento' },
  prioridad: 75,
  detener: false,
  plan_id: null,
  vigente_desde: null,
  vigente_hasta: null,
  activa: true,
}

async function abrirPestana(nombre: string) {
  const user = userEvent.setup()
  renderizar(<AdminPage />)
  await user.click(await screen.findByRole('tab', { name: nombre }))
  return user
}

describe('Administración: planes', () => {
  it('muestra las tarifas por número de peludos, los periodos largos y las ciudades', async () => {
    server.use(...base, http.get(`${API}/planes`, () => HttpResponse.json([PLAN])))
    await abrirPestana('Planes')
    const plan = await screen.findByRole('article', { name: 'Colita Feliz' })
    expect(within(plan).getByText(/Bogota, Medellin/)).toBeInTheDocument()
    const tarifas = within(plan).getByLabelText('Tarifas de Colita Feliz')
    expect(within(tarifas).getByText('4 o más (c/u)')).toBeInTheDocument()
    expect(within(tarifas).getByText('Anual (1 peludo)')).toBeInTheDocument()
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
    const user = await abrirPestana('Planes')
    const plan = await screen.findByRole('article', { name: 'Colita Feliz' })
    await user.click(within(plan).getByRole('button', { name: 'Editar' }))
    const modal = await screen.findByRole('dialog')
    expect(within(modal).getByLabelText('4 o más (c/u)')).toHaveValue(24000)
    const uno = within(modal).getByLabelText('1 peludo')
    await user.clear(uno)
    await user.type(uno, '36000')
    await user.type(within(modal).getByLabelText('Trimestral'), '103800')
    await user.clear(within(modal).getByLabelText('Anual'))
    await user.click(within(modal).getByRole('button', { name: 'Quitar beneficio' }))
    await user.selectOptions(within(modal).getByLabelText('Agregar beneficio'), 'vacunacion')
    await user.type(within(modal).getByLabelText('Cupo (vacío = ilimitado)'), '4')
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    await waitFor(() => expect(pedidos).toHaveLength(4))
    expect(pedidos).toEqual([
      ['plan', { nombre: 'Colita Feliz' }],
      ['ciudades', ['Bogota']],
      ['tarifas', { por_peludos: ['36000', '30500', '26000', '24000'], trimestral: '103800', semestral: '202350' }],
      ['beneficios', [{ tipo_servicio_codigo: 'vacunacion', cupo: 4, periodo_cupo: 'anual', cobertura_pct: 100, copago: '0' }]],
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
    const user = await abrirPestana('Planes')
    await user.click(within(await screen.findByRole('article', { name: 'Colita Feliz' })).getByRole('button', { name: 'Editar' }))
    const modal = await screen.findByRole('dialog')
    await user.click(within(modal).getByLabelText('Bogota'))
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    expect(await within(modal).findByText('Elige al menos una ciudad donde se vende el plan.')).toBeInTheDocument()
    expect(llamadas).toBe(0)
  })

  it('crea un plan con sus tarifas, sus ciudades y sus especies', async () => {
    let creado: unknown = null
    server.use(
      ...base,
      http.get(`${API}/planes`, () => HttpResponse.json([])),
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
    await user.click(within(modal).getByLabelText('Bogota'))
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
    await user.click(within(modal).getByRole('button', { name: 'Crear plan' }))
    await waitFor(() =>
      expect(creado).toEqual({
        codigo: 'mi_amigo_fiel',
        nombre: 'Mi Amigo Fiel',
        especies: ['perro'],
        ciudades: ['Bogota'],
        tarifas: { por_peludos: ['69000', '61000', '57500', '57000'], semestral: '393300' },
      }),
    )
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
    const user = await abrirPestana('Planes')
    await user.click(await screen.findByRole('button', { name: 'Desactivar' }))
    await waitFor(() => expect(cambio).toEqual({ activo: false }))
  })
})

describe('Administración: reglas', () => {
  it('muestra la condición legible, activa y desactiva, y edita en JSON', async () => {
    const cambios: unknown[] = []
    server.use(
      ...base,
      http.get(`${API}/reglas/eventos`, () => HttpResponse.json({ 'cartera.alerta': 'Avisos escalonados de mora' })),
      http.get(`${API}/reglas`, () => HttpResponse.json([REGLA])),
      http.patch(`${API}/reglas/rg1`, async ({ request }) => {
        cambios.push(await request.json())
        return HttpResponse.json(REGLA)
      }),
    )
    const user = await abrirPestana('Reglas')
    expect(await screen.findByText('dias_mora gte 25')).toBeInTheDocument()
    await user.click(screen.getByLabelText('Aviso de mora a los 25 días activa'))
    await user.click(screen.getByRole('button', { name: 'Editar' }))
    const modal = await screen.findByRole('dialog')
    const condicion = within(modal).getByLabelText('Condición')
    await user.clear(condicion)
    await user.click(condicion)
    await user.paste('{"op": "gte", "campo": "dias_mora", "valor": 20}')
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    await waitFor(() => expect(cambios).toHaveLength(2))
    expect(cambios[0]).toEqual({ activa: false })
    expect(cambios[1]).toMatchObject({ prioridad: 75, condicion: { op: 'gte', campo: 'dias_mora', valor: 20 } })
  })

  it('avisa si el JSON no es válido y prueba reglas sin ejecutarlas', async () => {
    let prueba: unknown = null
    server.use(
      ...base,
      http.get(`${API}/reglas/eventos`, () => HttpResponse.json({ 'cartera.alerta': 'Avisos escalonados de mora' })),
      http.get(`${API}/reglas`, () => HttpResponse.json([REGLA])),
      http.post(`${API}/reglas/probar`, async ({ request }) => {
        prueba = await request.json()
        return HttpResponse.json([{ regla: 'alerta_mora_25', nombre: 'Aviso', accion: {} }])
      }),
    )
    const user = await abrirPestana('Reglas')
    await user.click(await screen.findByRole('button', { name: 'Editar' }))
    let modal = await screen.findByRole('dialog')
    const accion = within(modal).getByLabelText('Acción')
    await user.clear(accion)
    await user.type(accion, 'no es json')
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('no es un JSON válido')
    await user.keyboard('{Escape}')

    await user.click(screen.getByRole('button', { name: 'Probar reglas' }))
    modal = await screen.findByRole('dialog')
    await user.click(within(modal).getByRole('button', { name: 'Evaluar' }))
    expect(await within(modal).findByText(/alerta_mora_25/)).toBeInTheDocument()
    expect(prueba).toEqual({ evento: 'cartera.alerta', contexto: { dias_mora: 30 } })
  })
})

describe('Administración: catálogos', () => {
  it('desactiva una ciudad sin borrarla', async () => {
    let cambio: unknown = null
    server.use(
      ...base,
      http.get(`${API}/catalogos/ciudades`, () => HttpResponse.json([{ codigo: '11001', nombre: 'Bogota', departamento: 'Bogota D.C.', activa: true }])),
      http.get(`${API}/catalogos/esquemas-preventivos`, () =>
        HttpResponse.json([{ codigo: 'rabia', especie_codigo: 'canino', tipo: 'vacuna', nombre: 'Rabia', edad_minima_semanas: 12, dosis_iniciales: 1, intervalo_inicial_dias: 0, intervalo_refuerzo_dias: 365, requiere_autorizacion: true, activo: true }]),
      ),
      http.patch(`${API}/catalogos/ciudades/11001/activo`, async ({ request }) => {
        cambio = await request.json()
        return HttpResponse.json({})
      }),
    )
    const user = await abrirPestana('Catálogos')
    expect(await screen.findByText(/refuerzo cada 365 días/)).toBeInTheDocument()
    await user.click(await screen.findByLabelText('Bogota con cobertura'))
    await waitFor(() => expect(cambio).toEqual({ activo: false }))
  })
})

describe('Administración: reportes y pasarela', () => {
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
      http.post(`${API}/cartera/eventos-pasarela/ev1/reprocesar`, () => {
        pedidos.push('reprocesar')
        return HttpResponse.json({})
      }),
    )
    const user = await abrirPestana('Reportes y pasarela')
    expect(await screen.findByText('Pago no encontrado')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Reprocesar' }))
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
