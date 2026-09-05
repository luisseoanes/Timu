import { describe, expect, it } from 'vitest'

import { api } from './client'

describe('cliente de la API', () => {
  it('envía las credenciales para que viaje la cookie de sesión', () => {
    expect(api.defaults.withCredentials).toBe(true)
  })

  it('no expone ningún almacén de tokens', async () => {
    const modulo = await import('./client')
    expect(Object.keys(modulo)).toEqual(['api'])
  })
})
