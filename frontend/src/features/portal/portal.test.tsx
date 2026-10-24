import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { PortalCitas, PortalDatos, PortalInicio, PortalPagos } from './PortalPages'
import { FAMILIA, USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'

const API = '*/api/v1'

const comoFamilia = [
  http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'familia', nombre: 'Ana Ruiz' })),
  http.get(`${API}/portal/mi-familia`, () => HttpResponse.json(FAMILIA)),
]

describe('Portal de la familia', () => {
  it('el inicio saluda, muestra el plan con lo que queda de cada beneficio y avisa la mora', async () => {
    server.use(
      ...comoFamilia,
      http.get(`${API}/portal/plan`, () =>
        HttpResponse.json({
          plan: 'Plan Familiar',
          estado: 'activa',
          valor_mensual: '75000.00',
          fecha_inicio: '2026-01-01',
          fecha_renovacion: '2027-01-01',
          beneficios: [{ tipo_servicio: 'consulta_domiciliaria', cupo: 6, periodo: 'anual', usados: 2, disponibles: 4, cobertura_pct: 100 }],
        }),
      ),
      http.get(`${API}/portal/estado-cuenta`, () => HttpResponse.json({ saldo_vencido: '75000.00', cuotas: [], pagos: [] })),
      http.get(`${API}/portal/servicios`, () => HttpResponse.json([])),
    )
    renderizar(<PortalInicio />)
    expect(await screen.findByRole('heading', { name: 'Hola, Ana' })).toBeInTheDocument()
    expect(await screen.findByText(/te quedan 4 de 6 este año/)).toBeInTheDocument()
    expect(await screen.findByRole('alert')).toHaveTextContent('vencidos')
  })

  it('sin contrato invita a afiliarse en lugar de fallar', async () => {
    server.use(
      ...comoFamilia,
      http.get(`${API}/portal/plan`, () => HttpResponse.json({ detail: 'Sin plan' }, { status: 404 })),
      http.get(`${API}/portal/estado-cuenta`, () => HttpResponse.json({ detail: 'Sin contrato' }, { status: 404 })),
      http.get(`${API}/portal/servicios`, () => HttpResponse.json([])),
    )
    renderizar(<PortalInicio />)
    expect(await screen.findByText(/aún no tienes un plan activo/i)).toBeInTheDocument()
  })

  it('agenda una visita eligiendo mascota, tipo y horario', async () => {
    let enviado: unknown = null
    server.use(
      ...comoFamilia,
      http.get(`${API}/portal/servicios`, () => HttpResponse.json([])),
      http.get(`${API}/portal/disponibilidad`, () =>
        HttpResponse.json([{ inicio: '2099-01-10T14:00:00Z', fin: '2099-01-10T14:45:00Z', disponibles: 1 }]),
      ),
      http.post(`${API}/portal/servicios`, async ({ request }) => {
        enviado = await request.json()
        return HttpResponse.json({ id: 's1', mascota_id: 'm', tipo_codigo: 'consulta_domiciliaria', estado: 'agendado', programado_para: '2099-01-10T14:00:00Z', termina_en: null }, { status: 201 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<PortalCitas />)
    expect(await screen.findByText('No tienes citas.')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /agendar/i }))
    const modal = await screen.findByRole('dialog')
    await waitFor(() => expect(within(modal).getByRole('option', { name: 'Consulta domiciliaria' })).toBeInTheDocument())
    await user.selectOptions(within(modal).getByLabelText('Tipo de visita'), 'consulta_domiciliaria')
    await user.click(await within(modal).findByRole('button', { pressed: false }))
    await user.click(within(modal).getByRole('button', { name: 'Agendar' }))
    expect(await within(modal).findByText(/tu visita quedó/i)).toBeInTheDocument()
    expect(enviado).toMatchObject({ mascota_id: FAMILIA.mascotas?.[0]?.id, tipo_codigo: 'consulta_domiciliaria', inicio: '2099-01-10T14:00:00Z' })
  })

  it('paga una cuota y lleva a la pasarela', async () => {
    let pagada: unknown = null
    server.use(
      ...comoFamilia,
      http.get(`${API}/portal/estado-cuenta`, () =>
        HttpResponse.json({
          saldo_pendiente: '75000.00',
          saldo_vencido: '0.00',
          proximo_cobro: null,
          cuotas: [{ id: 'q1', periodo: '2026-11', tipo: 'mensual', fecha_vencimiento: '2026-11-05', valor: '75000.00', valor_pagado: '0.00', estado: 'pendiente', dias_mora: 0, descripcion: 'Cuota noviembre' }],
          pagos: [],
        }),
      ),
      http.get(`${API}/portal/pagos`, () => HttpResponse.json([])),
      http.post(`${API}/portal/pagos`, async ({ request }) => {
        pagada = await request.json()
        return HttpResponse.json({ detail: 'Pasarela no disponible' }, { status: 503 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<PortalPagos />)
    await user.click(await screen.findByRole('button', { name: 'Pagar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Pasarela no disponible')
    expect(pagada).toEqual({ cuota_id: 'q1' })
  })

  it('actualiza sólo los datos que cambiaron', async () => {
    let cambios: unknown = null
    server.use(
      ...comoFamilia,
      http.patch(`${API}/portal/mi-familia`, async ({ request }) => {
        cambios = await request.json()
        return HttpResponse.json(FAMILIA)
      }),
    )
    const user = userEvent.setup()
    renderizar(<PortalDatos />)
    await user.type(await screen.findByLabelText('Dirección de las visitas'), 'Calle 80 # 15-20')
    await user.click(screen.getByRole('button', { name: 'Guardar' }))
    await waitFor(() => expect(cambios).toEqual({ direccion: 'Calle 80 # 15-20' }))
  })
})
