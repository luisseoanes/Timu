import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { CarteraPage } from './CarteraPage'
import { FAMILIA } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'
import type { ContratoListado } from '@/types'

const CONTRATO: ContratoListado = {
  id: 'c1',
  numero: 'TM-0001',
  familia_id: FAMILIA.id,
  titular: FAMILIA.titular_nombre,
  ciudad: 'Bogota',
  plan: 'Plan Esencial',
  estado: 'en_mora',
  valor_mensual: '89000.00',
  saldo_vencido: '178000.00',
  dias_mora: 40,
  fecha_renovacion: '2027-01-01',
}

const RUTA = '*/api/v1/cartera/contratos'

describe('CarteraPage', () => {
  it('muestra el estado de carga', () => {
    server.use(http.get(RUTA, () => HttpResponse.json({ items: [CONTRATO], total: 1, limit: 25, offset: 0 })))
    renderizar(<CarteraPage />)
    expect(screen.getByText(/cargando cartera/i)).toBeInTheDocument()
  })

  it('lista los contratos con su mora y enlaza a la familia', async () => {
    server.use(http.get(RUTA, () => HttpResponse.json({ items: [CONTRATO], total: 1, limit: 25, offset: 0 })))
    renderizar(<CarteraPage />)
    const enlace = await screen.findByRole('link', { name: FAMILIA.titular_nombre })
    expect(enlace).toHaveAttribute('href', `/familias/${FAMILIA.id}`)
    const fila = within(enlace.closest('tr')!)
    expect(fila.getByText('40')).toBeInTheDocument()
    expect(fila.getByText('En mora')).toBeInTheDocument()
  })

  it('muestra el estado vacío', async () => {
    server.use(http.get(RUTA, () => HttpResponse.json({ items: [], total: 0, limit: 25, offset: 0 })))
    renderizar(<CarteraPage />)
    expect(await screen.findByText('Ningún contrato coincide con el filtro.')).toBeInTheDocument()
  })

  it('muestra el error del servidor', async () => {
    server.use(http.get(RUTA, () => HttpResponse.json({ detail: 'Servicio no disponible' }, { status: 503 })))
    renderizar(<CarteraPage />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Servicio no disponible')
  })

  it('filtra sólo los contratos con saldo vencido', async () => {
    const consultas: string[] = []
    server.use(
      http.get(RUTA, ({ request }) => {
        consultas.push(new URL(request.url).search)
        return HttpResponse.json({ items: [CONTRATO], total: 1, limit: 25, offset: 0 })
      }),
    )
    const user = userEvent.setup()
    renderizar(<CarteraPage />)
    await user.click(await screen.findByRole('checkbox', { name: /sólo con saldo vencido/i }))
    await waitFor(() => expect(consultas.some((c) => c.includes('solo_mora=true'))).toBe(true))
  })
})
