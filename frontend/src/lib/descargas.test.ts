import { http, HttpResponse } from 'msw'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { descargar } from './descargas'
import { server } from '@/test/server'

// jsdom no implementa los métodos estáticos de URL para blobs: se reemplazan sólo esos dos,
// porque axios necesita el constructor de URL intacto.
const crear = vi.fn(() => 'blob:temporal')
const revocar = vi.fn()

describe('descargar', () => {
  beforeEach(() => {
    Object.defineProperty(URL, 'createObjectURL', { value: crear, configurable: true })
    Object.defineProperty(URL, 'revokeObjectURL', { value: revocar, configurable: true })
  })
  afterEach(() => vi.restoreAllMocks())

  it('usa el nombre que manda el servidor y libera la URL temporal', async () => {
    server.use(
      http.get('*/api/v1/reporte', () =>
        new HttpResponse('a,b\n1,2', {
          headers: { 'Content-Type': 'text/csv', 'Content-Disposition': 'attachment; filename="indicadores-octubre.csv"' },
        }),
      ),
    )
    let descargado = ''
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (this: HTMLAnchorElement) {
      descargado = `${this.download} ${this.href}`
    })

    await descargar('/reporte', { formato: 'csv' }, 'por-defecto.csv')

    expect(descargado).toBe('indicadores-octubre.csv blob:temporal')
    expect(revocar).toHaveBeenCalledWith('blob:temporal')
  })

  it('sin Content-Disposition usa el nombre por defecto', async () => {
    server.use(http.get('*/api/v1/reporte', () => new HttpResponse('x')))
    let nombre = ''
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (this: HTMLAnchorElement) {
      nombre = this.download
    })
    await descargar('/reporte', {}, 'por-defecto.csv')
    expect(nombre).toBe('por-defecto.csv')
  })
})
