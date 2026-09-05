import { screen, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Route, Routes } from 'react-router-dom'

import { ProtectedRoute } from './ProtectedRoute'
import { sinSesion } from '@/test/handlers'
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
})
