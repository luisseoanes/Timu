import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider, useAuth } from './AuthContext'
import { server } from '@/test/server'
import { sinSesion, USUARIO_ADMIN } from '@/test/handlers'

const API = '*/api/v1'

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

describe('AuthContext ante fallos que no son de sesión', () => {
  // Solo setTimeout es falso: MSW y las promesas siguen su curso real.
  beforeEach(() => vi.useFakeTimers({ toFake: ['setTimeout'], shouldAdvanceTime: true }))
  afterEach(() => vi.useRealTimers())

  function SondaError() {
    const { usuario, cargando, errorSesion, reintentarSesion } = useAuth()
    if (cargando) return <p>cargando</p>
    return (
      <div>
        <span data-testid="usuario">{usuario ? usuario.email : errorSesion ? 'sin respuesta' : 'sin sesion'}</span>
        <button onClick={reintentarSesion}>reintentar</button>
      </div>
    )
  }

  const montarError = () =>
    render(
      <AuthProvider>
        <SondaError />
      </AuthProvider>,
    )

  function respuestasDeMe(...respuestas: (() => Response)[]) {
    const llamadas: number[] = []
    server.use(
      http.get(`${API}/auth/me`, () => {
        llamadas.push(Date.now())
        return (respuestas.shift() ?? (() => HttpResponse.json(USUARIO_ADMIN)))()
      }),
    )
    return llamadas
  }

  it('un 429 no cierra la sesión: espera lo que pide Retry-After y reintenta', async () => {
    const llamadas = respuestasDeMe(() =>
      HttpResponse.json({ detail: 'Demasiadas peticiones' }, { status: 429, headers: { 'Retry-After': '2' } }),
    )
    montarError()
    await vi.advanceTimersByTimeAsync(1500)
    expect(llamadas).toHaveLength(1)
    await vi.advanceTimersByTimeAsync(1000)
    await waitFor(() => expect(screen.getByTestId('usuario')).toHaveTextContent('admin@timu.co'))
    expect(llamadas).toHaveLength(2)
  })

  it('un 5xx o la red caída también se reintentan', async () => {
    respuestasDeMe(
      () => new HttpResponse(null, { status: 503 }),
      () => HttpResponse.error(),
    )
    montarError()
    await vi.advanceTimersByTimeAsync(5000)
    await waitFor(() => expect(screen.getByTestId('usuario')).toHaveTextContent('admin@timu.co'))
  })

  it('si el servidor no contesta tras los reintentos avisa, no expulsa, y deja reintentar', async () => {
    const caido = () => new HttpResponse(null, { status: 502 })
    const llamadas = respuestasDeMe(caido, caido, caido, caido)
    montarError()
    await vi.advanceTimersByTimeAsync(14000)
    await waitFor(() => expect(screen.getByTestId('usuario')).toHaveTextContent('sin respuesta'))
    expect(llamadas).toHaveLength(4)

    await userEvent.click(screen.getByRole('button', { name: 'reintentar' }))
    await waitFor(() => expect(screen.getByTestId('usuario')).toHaveTextContent('admin@timu.co'))
  })

  it.each([401, 403])('un %i es una respuesta firme: «sin sesión» al instante, sin reintentos', async (estado) => {
    server.use(http.post(`${API}/auth/refresh`, () => new HttpResponse(null, { status: 401 })))
    const llamadas = respuestasDeMe(() => new HttpResponse(null, { status: estado }))
    montarError()
    await waitFor(() => expect(screen.getByTestId('usuario')).toHaveTextContent('sin sesion'))
    await vi.advanceTimersByTimeAsync(10000)
    expect(llamadas).toHaveLength(1)
  })

  it('si la renovación choca con el límite, la sesión sobrevive', async () => {
    // El access venció (401) y la renovación respondió 429: antes eso sacaba al usuario.
    respuestasDeMe(() => new HttpResponse(null, { status: 401 }))
    server.use(
      http.post(`${API}/auth/refresh`, () =>
        HttpResponse.json({ detail: 'Demasiadas peticiones' }, { status: 429, headers: { 'Retry-After': '1' } }),
      ),
    )
    montarError()
    await vi.advanceTimersByTimeAsync(1500)
    await waitFor(() => expect(screen.getByTestId('usuario')).toHaveTextContent('admin@timu.co'))
  })
})
