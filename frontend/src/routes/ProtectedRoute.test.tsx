import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { Route, Routes } from 'react-router-dom'

import { ProtectedRoute } from './ProtectedRoute'
import { sinSesion, USUARIO_ADMIN } from '@/test/handlers'
import { server } from '@/test/server'
import { renderizar } from '@/test/utils'

const arbol = (roles?: Parameters<typeof ProtectedRoute>[0]['roles']) => (
  <Routes>
    <Route element={<ProtectedRoute roles={roles} />}>
      <Route path="/" element={<p>contenido protegido</p>} />
    </Route>
    <Route path="/login" element={<p>pantalla de ingreso</p>} />
  </Routes>
)

describe('ProtectedRoute', () => {
  it('manda al ingreso si no hay sesión', async () => {
    server.use(sinSesion)
    renderizar(arbol())
    await waitFor(() => expect(screen.getByText('pantalla de ingreso')).toBeInTheDocument())
  })

  it('deja pasar a un usuario con sesión', async () => {
    renderizar(arbol())
    await waitFor(() => expect(screen.getByText('contenido protegido')).toBeInTheDocument())
  })

  it('bloquea a quien no tiene el perfil requerido', async () => {
    renderizar(arbol(['medico']))
    await waitFor(() => expect(screen.queryByText('contenido protegido')).not.toBeInTheDocument())
  })

  it('permite el paso cuando el perfil coincide', async () => {
    renderizar(arbol(['admin']))
    await waitFor(() => expect(screen.getByText('contenido protegido')).toBeInTheDocument())
  })

  describe('si el servidor no contesta', () => {
    afterEach(() => vi.useRealTimers())

    it('avisa y deja reintentar en lugar de mandar al ingreso', async () => {
      vi.useFakeTimers({ toFake: ['setTimeout'], shouldAdvanceTime: true })
      let caido = true
      server.use(
        http.get('*/api/v1/auth/me', () => (caido ? new HttpResponse(null, { status: 503 }) : HttpResponse.json(USUARIO_ADMIN))),
      )
      renderizar(arbol())
      await vi.advanceTimersByTimeAsync(14000)
      expect(await screen.findByRole('alert')).toHaveTextContent('No pudimos comprobar tu sesión')
      expect(screen.queryByText('pantalla de ingreso')).not.toBeInTheDocument()

      caido = false
      await userEvent.click(screen.getByRole('button', { name: 'Reintentar' }))
      expect(await screen.findByText('contenido protegido')).toBeInTheDocument()
    })
  })
})
