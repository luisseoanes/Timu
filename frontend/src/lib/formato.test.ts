import { describe, expect, it } from 'vitest'

import { mensajeError } from './errores'
import { estado } from './estados'
import { fecha, fechaHora, moneda, porcentaje } from './formato'

describe('formato colombiano', () => {
  it('muestra pesos sin decimales y con punto de miles', () => {
    expect(moneda('45000.00')).toMatch(/45\.000/)
    expect(moneda(null)).toBe('—')
  })

  it('no corre una fecha de calendario por la zona horaria', () => {
    expect(fecha('2026-10-24')).toBe('24/10/2026')
  })

  it('muestra los instantes en hora de Colombia', () => {
    // 14:30 UTC son las 9:30 de la mañana en Bogotá.
    expect(fechaHora('2026-10-24T14:30:00Z')).toMatch(/24\/10\/2026.*9:30/)
  })

  it('redondea los porcentajes', () => {
    expect(porcentaje(0.876)).toBe('88%')
    expect(porcentaje(null)).toBe('—')
  })
})

describe('estados', () => {
  it('da el mismo tono a un estado en cualquier módulo', () => {
    expect(estado('afiliacion', 'en_mora')).toEqual({ label: 'En mora', tono: 'alerta' })
  })

  it('no rompe la pantalla ante un estado desconocido', () => {
    expect(estado('servicio', 'en_revision')).toEqual({ label: 'en revision', tono: 'neutro' })
  })
})

describe('mensajeError', () => {
  it('sin respuesta del servidor, dice qué hacer', () => {
    expect(mensajeError(new Error('x'))).toMatch(/intenta de nuevo/i)
  })
})
