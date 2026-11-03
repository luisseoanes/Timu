import { http, HttpResponse } from 'msw'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { server } from '@/test/server'

import { api } from './client'

const API = '*/api/v1'

/** Endpoint que responde 401 hasta que la sesión se renueva. */
function protegido(estado: { renovada: boolean }) {
  return http.get(`${API}/familias`, () =>
    estado.renovada
      ? HttpResponse.json({ items: [], total: 0, limit: 50, offset: 0 })
      : new HttpResponse(null, { status: 401 }),
  )
}

describe('cliente de la API', () => {
  it('envía las credenciales para que viaje la cookie de sesión', () => {
    expect(api.defaults.withCredentials).toBe(true)
  })

  it('no expone ningún almacén de tokens', async () => {
    const modulo = await import('./client')
    expect(Object.keys(modulo)).toEqual(['api'])
  })

  it('renueva la sesión vencida y reintenta la petición', async () => {
    const estado = { renovada: false }
    server.use(
      protegido(estado),
      http.post(`${API}/auth/refresh`, () => {
        estado.renovada = true
        return HttpResponse.json({})
      }),
    )
    const { data } = await api.get('/familias')
    expect(data.total).toBe(0)
  })

  it('varias peticiones vencidas comparten una sola renovación', async () => {
    const estado = { renovada: false }
    let renovaciones = 0
    server.use(
      protegido(estado),
      http.post(`${API}/auth/refresh`, async () => {
        renovaciones += 1
        await new Promise((r) => setTimeout(r, 20))
        estado.renovada = true
        return HttpResponse.json({})
      }),
    )
    await Promise.all([api.get('/familias'), api.get('/familias'), api.get('/familias')])
    // Presentar dos veces el refresh ya rotado haría que el backend cerrara todas las sesiones.
    expect(renovaciones).toBe(1)
  })

  it('si la renovación falla, la petición falla con 401', async () => {
    server.use(
      protegido({ renovada: false }),
      http.post(`${API}/auth/refresh`, () => new HttpResponse(null, { status: 401 })),
    )
    await expect(api.get('/familias')).rejects.toMatchObject({ response: { status: 401 } })
  })

  describe('cuando la renovación no es un 401', () => {
    afterEach(() => vi.unstubAllGlobals())

    function enPantallaProtegida() {
      const asignar = vi.fn()
      vi.stubGlobal('location', { ...window.location, pathname: '/familias', assign: asignar })
      return asignar
    }

    it('un 429 o un 5xx en la renovación se devuelven a la pantalla sin sacar al usuario', async () => {
      const asignar = enPantallaProtegida()
      for (const estado of [429, 503]) {
        server.use(
          protegido({ renovada: false }),
          http.post(`${API}/auth/refresh`, () => HttpResponse.json({ detail: 'Pasajero' }, { status: estado })),
        )
        await expect(api.get('/familias')).rejects.toMatchObject({ response: { status: estado } })
      }
      expect(asignar).not.toHaveBeenCalled()
    })

    it.each([401, 403, 404])('un %i en la renovación es firme: cierra la sesión y lleva al ingreso', async (estado) => {
      const asignar = enPantallaProtegida()
      server.use(
        protegido({ renovada: false }),
        http.post(`${API}/auth/refresh`, () => new HttpResponse(null, { status: estado })),
      )
      await expect(api.get('/familias')).rejects.toMatchObject({ response: { status: 401 } })
      expect(asignar).toHaveBeenCalledWith('/login')
    })

    it('si tras renovar la petición falla por otra cosa, llega ese error y no un 401', async () => {
      const asignar = enPantallaProtegida()
      let renovada = false
      server.use(
        http.get(`${API}/familias`, () =>
          renovada ? HttpResponse.json({ detail: 'Fallo interno' }, { status: 500 }) : new HttpResponse(null, { status: 401 }),
        ),
        http.post(`${API}/auth/refresh`, () => {
          renovada = true
          return HttpResponse.json({})
        }),
      )
      await expect(api.get('/familias')).rejects.toMatchObject({ response: { status: 500 } })
      expect(asignar).not.toHaveBeenCalled()
    })
  })
})
