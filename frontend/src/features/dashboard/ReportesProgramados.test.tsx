import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { ReportesProgramados } from './ReportesProgramados'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'

const API = '*/api/v1'

// Los reportes por correo los programa Gerencia, en su Inicio (Sección 8, docs/perfiles-y-permisos.md).
describe('Reportes programados', () => {
  it('crea un reporte con sus indicadores', async () => {
    const pedidos: unknown[] = []
    server.use(
      http.get(`${API}/dashboard/reportes`, () => HttpResponse.json([])),
      http.get(`${API}/dashboard/definiciones`, () =>
        HttpResponse.json([{ codigo: 'recaudo', nombre: 'Recaudo', formula: 'Suma de pagos', unidad: 'COP' }]),
      ),
      http.post(`${API}/dashboard/reportes`, async ({ request }) => {
        pedidos.push(await request.json())
        return HttpResponse.json({}, { status: 201 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<ReportesProgramados />)
    expect(await screen.findByText('No hay reportes programados.')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /nuevo reporte/i }))
    const modal = await screen.findByRole('dialog')
    await user.type(within(modal).getByLabelText('Nombre'), 'Gerencia semanal')
    await user.type(within(modal).getByLabelText(/destinatarios/i), 'gerencia@timu.co, socios@timu.co')
    await user.click(await within(modal).findByRole('button', { name: 'Recaudo' }))
    await user.click(within(modal).getByRole('button', { name: 'Guardar' }))
    await waitFor(() =>
      expect(pedidos).toEqual([
        {
          nombre: 'Gerencia semanal',
          periodicidad: 'semanal',
          destinatarios: ['gerencia@timu.co', 'socios@timu.co'],
          indicadores: ['recaudo'],
          activo: true,
        },
      ]),
    )
  })
})
