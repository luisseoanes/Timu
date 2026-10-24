import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { Route, Routes, useLocation } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { AppLayout } from './AppLayout'
import { USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'

function Ubicacion() {
  const l = useLocation()
  return <p>En {l.pathname + l.search}</p>
}

function abrir(ruta = '/') {
  return renderizar(
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="*" element={<Ubicacion />} />
      </Route>
    </Routes>,
    { ruta },
  )
}

describe('AppLayout', () => {
  it('el administrador ve todos los módulos, administración incluida', async () => {
    abrir()
    const nav = await screen.findByRole('navigation', { name: 'Módulos' })
    expect(nav).toHaveTextContent('Administración')
    expect(nav).toHaveTextContent('Comercial')
    expect(await screen.findByText('Administración', { selector: '.usuario-datos span' })).toBeInTheDocument()
  })

  it('un médico no ve administración ni el embudo comercial', async () => {
    server.use(http.get('*/api/v1/auth/me', () => HttpResponse.json({ ...USUARIO_ADMIN, rol: 'medico' })))
    abrir()
    expect(await screen.findByText('Médico veterinario')).toBeInTheDocument()
    const nav = screen.getByRole('navigation', { name: 'Módulos' })
    expect(nav).not.toHaveTextContent('Administración')
    expect(nav).not.toHaveTextContent('Comercial')
    expect(nav).toHaveTextContent('Clínica')
  })

  it('titula la página según el módulo activo', async () => {
    abrir('/rutas')
    expect(await screen.findByRole('heading', { name: 'Rutas' })).toBeInTheDocument()
  })

  it('el buscador de la cabecera lleva a familias con la búsqueda', async () => {
    const user = userEvent.setup()
    abrir()
    await user.type(await screen.findByRole('searchbox', { name: 'Buscar familias' }), 'Ana Ruiz{Enter}')
    expect(await screen.findByText('En /familias?q=Ana%20Ruiz')).toBeInTheDocument()
  })
})
