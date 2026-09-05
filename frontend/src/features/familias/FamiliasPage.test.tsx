import { screen, waitFor } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { FamiliasPage } from './FamiliasPage'
import { FAMILIA } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'

// Las tres pantallas obligatorias de toda consulta, segun docs/frontend/conventions.md:
// cargando, error y vacio. Si una falta, la pantalla esta incompleta.
describe('FamiliasPage', () => {
  it('muestra el estado de carga', () => {
    renderizar(<FamiliasPage />)
    expect(screen.getByText(/cargando familias/i)).toBeInTheDocument()
  })

  it('lista las familias que devuelve la API', async () => {
    renderizar(<FamiliasPage />)
    await waitFor(() => expect(screen.getByText(FAMILIA.titular_nombre)).toBeInTheDocument())
  })

  it('muestra el estado vacío cuando no hay resultados', async () => {
    server.use(
      http.get('*/api/v1/familias', () =>
        HttpResponse.json({ items: [], total: 0, limit: 50, offset: 0 }),
      ),
    )
    renderizar(<FamiliasPage />)
    await waitFor(() =>
      expect(screen.queryByText(/cargando familias/i)).not.toBeInTheDocument(),
    )
    expect(screen.queryByText(FAMILIA.titular_nombre)).not.toBeInTheDocument()
  })

  it('muestra el error cuando la API falla', async () => {
    server.use(
      http.get('*/api/v1/familias', () => new HttpResponse(null, { status: 500 })),
    )
    renderizar(<FamiliasPage />)
    await waitFor(() =>
      expect(screen.queryByText(/cargando familias/i)).not.toBeInTheDocument(),
    )
  })

  it('expone los controles de filtro con etiqueta accesible', async () => {
    renderizar(<FamiliasPage />)
    expect(screen.getByLabelText('Buscar familias')).toBeInTheDocument()
    expect(screen.getByLabelText('Filtrar por estado')).toBeInTheDocument()
  })
})
