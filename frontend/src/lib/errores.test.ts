import { AxiosError, AxiosHeaders } from 'axios'
import { describe, expect, it } from 'vitest'

import { esErrorPasajero } from './errores'

const conEstado = (status?: number) =>
  new AxiosError('fallo', 'ERR', undefined, undefined, status === undefined
    ? undefined
    : { status, statusText: '', headers: {}, config: { headers: new AxiosHeaders() }, data: {} })

describe('esErrorPasajero', () => {
  it.each([undefined, 408, 429, 500, 502, 503])('%s se arregla esperando', (estado) => {
    expect(esErrorPasajero(conEstado(estado))).toBe(true)
  })

  it.each([400, 401, 403, 404, 409, 422])('%i es una respuesta firme', (estado) => {
    expect(esErrorPasajero(conEstado(estado))).toBe(false)
  })

  it('lo que no viene de axios no es pasajero', () => {
    expect(esErrorPasajero(new Error('otra cosa'))).toBe(false)
  })
})
