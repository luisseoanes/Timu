import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

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
})
