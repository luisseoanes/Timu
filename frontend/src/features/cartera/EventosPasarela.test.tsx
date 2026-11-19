import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { beforeEach, describe, expect, it } from 'vitest'

import { CarteraPage } from './CarteraPage'
import { sesionDe } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'

const API = '*/api/v1'

// La pasarela de pagos la revisa Atención al cliente, en Cartera (Sección 12, docs/perfiles-y-permisos.md).
beforeEach(() =>
  server.use(
    sesionDe('atencion_cliente'),
    http.get(`${API}/cartera/contratos`, () => HttpResponse.json({ items: [], total: 0, limit: 25, offset: 0 })),
    http.get(`${API}/cartera/contratos/recuentos`, () => HttpResponse.json({ en_mora: 0, por_renovar: 0, todos: 0 })),
  ),
)

describe('Cartera: eventos de la pasarela de pagos', () => {
  it('la vista de eventos en la URL abre la pestaña de la pasarela', async () => {
    const estados: (string | null)[] = []
    server.use(
      http.get(`${API}/cartera/eventos-pasarela/recuentos`, () => HttpResponse.json({ error: 0, procesado: 2, todos: 2 })),
      http.get(`${API}/cartera/eventos-pasarela`, ({ request }) => {
        estados.push(new URL(request.url).searchParams.get('estado'))
        return HttpResponse.json({ items: [], total: 0, limit: 50, offset: 0 })
      }),
    )
    renderizar(<CarteraPage />, { ruta: '/panel/cartera?eventos=procesado' })
    expect(await screen.findByRole('button', { name: 'Procesados 2' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('tab', { name: 'Pasarela de pagos' })).toHaveAttribute('aria-selected', 'true')
    await waitFor(() => expect(estados).toContain('procesado'))
  })

  it('dice cada evento en palabras y reprocesa uno con error', async () => {
    const pedidos: unknown[] = []
    server.use(
      http.get(`${API}/cartera/eventos-pasarela`, () =>
        HttpResponse.json({
          items: [{ id: 'ev1', proveedor: 'wompi', tipo: 'transaction.updated', referencia: 'TX-1', estado: 'error', intentos: 2, error: 'Pago no encontrado', procesado_en: null, created_at: '2026-10-24T10:00:00Z' }],
          total: 1,
          limit: 50,
          offset: 0,
        }),
      ),
      http.get(`${API}/cartera/eventos-pasarela/recuentos`, () => HttpResponse.json({ error: 1, procesado: 4, todos: 5 })),
      http.post(`${API}/cartera/eventos-pasarela/ev1/reprocesar`, () => {
        pedidos.push('reprocesar')
        return HttpResponse.json({})
      }),
    )
    const user = userEvent.setup()
    renderizar(<CarteraPage />)
    await user.click(await screen.findByRole('tab', { name: 'Pasarela de pagos' }))
    expect(await screen.findByText('Pago no encontrado')).toBeInTheDocument()
    // El evento en palabras, no el código del proveedor.
    expect(screen.getByText('Cambio en un pago')).toBeInTheDocument()
    expect(screen.getByText('Wompi')).toBeInTheDocument()
    // Cada vista dice cuántos tiene, y la elegida vive en la URL, como en las demás bandejas (DEU-26).
    expect(await screen.findByRole('button', { name: 'Con error 1' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'Procesados 4' })).toHaveAttribute('aria-pressed', 'false')
    await user.click(screen.getByRole('button', { name: 'Reprocesar el evento TX-1' }))
    await waitFor(() => expect(pedidos).toEqual(['reprocesar']))
  })

  it('Comercial no ve la pasarela: solo los contratos', async () => {
    server.use(sesionDe('comercial'))
    renderizar(<CarteraPage />)
    expect(await screen.findByRole('searchbox', { name: 'Buscar contratos' })).toBeInTheDocument()
    expect(screen.queryByRole('tab', { name: 'Pasarela de pagos' })).not.toBeInTheDocument()
  })
})
