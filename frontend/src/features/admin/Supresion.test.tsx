import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { Supresion } from './Supresion'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'

const API = '*/api/v1'
const FAMILIA = { id: 'f1', titular_nombre: 'Ana Ruiz', mascotas: 2, estado: 'cancelada', anonimizada: false, con_contrato_vigente: false }

// Ley 1581: el administrador anonimiza sin abrir la ficha (docs/perfiles-y-permisos.md).
describe('Supresión de datos', () => {
  it('busca por documento, muestra solo lo mínimo y anonimiza tras confirmarlo en rojo', async () => {
    const pedidos: string[] = []
    server.use(
      http.get(`${API}/familias/supresion`, ({ request }) => {
        pedidos.push(`buscar ${new URL(request.url).searchParams.get('documento')}`)
        return HttpResponse.json(FAMILIA)
      }),
      http.post(`${API}/familias/f1/anonimizar`, () => {
        pedidos.push('anonimizar')
        return HttpResponse.json({})
      }),
    )
    const user = userEvent.setup()
    renderizar(<Supresion />)
    await user.type(screen.getByLabelText('Documento del titular'), ' 1020304050 ')
    await user.click(screen.getByRole('button', { name: 'Buscar' }))
    expect(await screen.findByText('Ana Ruiz')).toBeInTheDocument()
    expect(screen.getByText('2 mascotas · Cancelada')).toBeInTheDocument()
    const enLaFila = screen.getByRole('button', { name: 'Anonimizar' })
    // DEU-83: en la fila, plano rojo; el rojo lleno confirma en la ventana.
    expect(enLaFila).toHaveClass('btn-plano-peligro')
    expect(enLaFila).not.toHaveClass('btn-peligro')
    await user.click(enLaFila)
    const modal = await screen.findByRole('dialog', { name: 'Anonimizar a Ana Ruiz' })
    expect(within(modal).getByRole('button', { name: 'Anonimizar' })).toHaveClass('btn-peligro')
    await user.click(within(modal).getByRole('button', { name: 'Anonimizar' }))
    // Tras anonimizar se vuelve a pedir la familia, para decir que ya está anonimizada.
    await waitFor(() => expect(pedidos.slice(0, 2)).toEqual(['buscar 1020304050', 'anonimizar']))
  })

  it('con un contrato vigente no ofrece anonimizar: dice que Atención lo cancela antes', async () => {
    server.use(
      http.get(`${API}/familias/supresion`, () => HttpResponse.json({ ...FAMILIA, estado: 'activa', con_contrato_vigente: true })),
    )
    const user = userEvent.setup()
    renderizar(<Supresion />)
    await user.type(screen.getByLabelText('Documento del titular'), '1020304050')
    await user.click(screen.getByRole('button', { name: 'Buscar' }))
    expect(await screen.findByText(/Atención al cliente lo cancela antes de anonimizar/)).toBeInTheDocument()
    expect(screen.getByText('Contrato vigente')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Anonimizar' })).not.toBeInTheDocument()
  })

  it('dice si ninguna familia tiene ese documento, y no ofrece anonimizar una ya anonimizada', async () => {
    server.use(
      http.get(`${API}/familias/supresion`, ({ request }) =>
        new URL(request.url).searchParams.get('documento') === '999'
          ? HttpResponse.json({ detail: 'No hay ninguna familia con ese documento' }, { status: 404 })
          : HttpResponse.json({ ...FAMILIA, anonimizada: true }),
      ),
    )
    const user = userEvent.setup()
    renderizar(<Supresion />)
    const campo = screen.getByLabelText('Documento del titular')
    await user.type(campo, '999')
    await user.click(screen.getByRole('button', { name: 'Buscar' }))
    expect(await screen.findByText(/No hay ninguna familia con ese documento/)).toBeInTheDocument()
    await user.clear(campo)
    await user.type(campo, '1020304050')
    await user.click(screen.getByRole('button', { name: 'Buscar' }))
    expect(await screen.findByText('Ya anonimizada')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Anonimizar' })).not.toBeInTheDocument()
  })
})
