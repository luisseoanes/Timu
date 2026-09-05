import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { AuthProvider, useAuth } from './AuthContext'
import { server } from '@/test/server'
import { sinSesion } from '@/test/handlers'

function Sonda() {
  const { usuario, cargando, login, logout } = useAuth()
  if (cargando) return <p>cargando</p>
  return (
    <div>
      <span data-testid="usuario">{usuario ? usuario.email : 'sin sesion'}</span>
      <button onClick={() => login('admin@timu.co', 'secreto123')}>entrar</button>
      <button onClick={() => logout()}>salir</button>
    </div>
  )
}

const montar = () =>
  render(
    <AuthProvider>
      <Sonda />
    </AuthProvider>,
  )

describe('AuthContext', () => {
  it('recupera la sesión preguntando al backend, no leyendo el token', async () => {
    montar()
    await waitFor(() => expect(screen.getByTestId('usuario')).toHaveTextContent('admin@timu.co'))
  })

  it('queda sin sesión cuando el backend responde 401', async () => {
    server.use(sinSesion)
    montar()
    await waitFor(() => expect(screen.getByTestId('usuario')).toHaveTextContent('sin sesion'))
  })

  it('inicia sesión sin guardar nada en localStorage', async () => {
    server.use(sinSesion)
    montar()
    await waitFor(() => screen.getByTestId('usuario'))

    await userEvent.click(screen.getByRole('button', { name: 'entrar' }))
    await waitFor(() => expect(screen.getByTestId('usuario')).toHaveTextContent('admin@timu.co'))
    expect(window.localStorage.length).toBe(0)
  })

  it('cierra sesión avisando al backend para que borre la cookie', async () => {
    montar()
    await waitFor(() => expect(screen.getByTestId('usuario')).toHaveTextContent('admin@timu.co'))

    await userEvent.click(screen.getByRole('button', { name: 'salir' }))
    await waitFor(() => expect(screen.getByTestId('usuario')).toHaveTextContent('sin sesion'))
  })
})
