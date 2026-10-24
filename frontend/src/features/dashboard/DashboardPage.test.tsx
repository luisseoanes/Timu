import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { DashboardPage } from './DashboardPage'
import type { Indicadores } from './api'
import { USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'

const API = '*/api/v1'

const INDICADORES: Indicadores = {
  periodo: { desde: '2026-10-01', hasta: '2026-10-24', ciudad: null },
  indicadores: {
    afiliaciones: 12,
    retiros: 2,
    vigentes: 340,
    recaudo: 15300000,
    facturado: 18000000,
    recaudo_del_facturado: 0.85,
    mora: { contratos_en_mora: 21, saldo_vencido: 1890000, porcentaje: 0.062 },
    cumplimiento_rutas: { paradas_planeadas: 120, paradas_completadas: 111, cumplimiento: 0.925, puntualidad: 0.8 },
    servicios_por_tipo: { 'Consulta domiciliaria': 40, Vacunación: 25 },
    satisfaccion: { enviadas: 60, respondidas: 42, promedio: 4.6, tasa_respuesta: 0.7 },
  },
}

describe('DashboardPage', () => {
  it('muestra los indicadores del período con su detalle', async () => {
    server.use(http.get(`${API}/dashboard/indicadores`, () => HttpResponse.json(INDICADORES)))
    renderizar(<DashboardPage />)
    expect(await screen.findByText('340')).toBeInTheDocument()
    expect(screen.getByText('93%')).toBeInTheDocument()
    expect(screen.getByText('4.6 / 5')).toBeInTheDocument()
    const barras = screen.getByRole('list', { name: 'Servicios completados por tipo' })
    expect(within(barras).getByText('Consulta domiciliaria')).toBeInTheDocument()
    expect(within(barras).getByText('40')).toBeInTheDocument()
  })

  it('vuelve a consultar al cambiar la ciudad', async () => {
    const ciudades: (string | null)[] = []
    server.use(
      http.get(`${API}/dashboard/indicadores`, ({ request }) => {
        ciudades.push(new URL(request.url).searchParams.get('ciudad'))
        return HttpResponse.json(INDICADORES)
      }),
    )
    const user = userEvent.setup()
    renderizar(<DashboardPage />)
    await screen.findByText('340')
    await user.selectOptions(screen.getByLabelText('Ciudad'), 'Bogota')
    await screen.findByText('340')
    expect(ciudades).toContain('Bogota')
  })

  it('muestra el error si no se pueden calcular', async () => {
    server.use(
      http.get(`${API}/dashboard/indicadores`, () => HttpResponse.json({ detail: 'Fallo la consulta' }, { status: 500 })),
    )
    renderizar(<DashboardPage />)
    expect(await screen.findByText(/no fue posible calcular los indicadores/i)).toBeInTheDocument()
  })

  it('señala lo que requiere atención con su cantidad', async () => {
    server.use(
      http.get(`${API}/tareas`, () => HttpResponse.json({ items: [], total: 3, limit: 1, offset: 0 })),
      http.get(`${API}/cartera/contratos`, () => HttpResponse.json({ items: [], total: 5, limit: 1, offset: 0 })),
    )
    renderizar(<DashboardPage />)
    const enMora = await screen.findByRole('link', { name: /contratos en mora/i })
    expect(await within(enMora).findByText('5')).toBeInTheDocument()
    expect(within(screen.getByRole('link', { name: /tareas vencidas/i })).getByText('3')).toBeInTheDocument()
  })

  it('el médico ve sus tareas, no los indicadores gerenciales', async () => {
    server.use(
      http.get(`${API}/auth/me`, () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'medico' })),
      http.get(`${API}/tareas`, () =>
        HttpResponse.json({
          items: [{ id: 't1', titulo: 'Llamar a Ana', prioridad: 'alta', vence_el: '2026-10-25', estado: 'abierta' }],
          total: 1,
          limit: 5,
          offset: 0,
        }),
      ),
    )
    renderizar(<DashboardPage />)
    expect(await screen.findByText('Llamar a Ana')).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Indicadores' })).not.toBeInTheDocument()
  })
})
