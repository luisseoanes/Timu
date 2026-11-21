import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it, vi } from 'vitest'

import { SelectorFamilia } from './SelectorFamilia'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'

const API = '*/api/v1'

describe('SelectorFamilia', () => {
  it('si la búsqueda falla lo dice, en vez de dejar la lista como si no hubiera familias', async () => {
    // R4-CIE-02: el médico recibía 403 de /familias y veía la lista vacía, sin ningún aviso.
    server.use(http.get(`${API}/familias`, () => HttpResponse.json({ detail: 'No tienes permiso para ver familias' }, { status: 403 })))
    renderizar(<SelectorFamilia valor={null} onCambio={vi.fn()} />)
    await userEvent.setup().type(screen.getByRole('searchbox'), 'Ana')
    expect(await screen.findByRole('alert')).toHaveTextContent('No tienes permiso para ver familias')
    expect(screen.queryByText('Ninguna familia coincide.')).not.toBeInTheDocument()
  })
})
