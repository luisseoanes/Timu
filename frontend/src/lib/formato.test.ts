import { describe, expect, it } from 'vitest'

import { mensajeError } from './errores'
import { estado } from './estados'
import { diaISO, edad, fecha, fechaCorta, fechaCortaConDia, fechaHora, fechaLarga, moneda, peso, porcentaje, rangoHoras } from './formato'

describe('formato colombiano', () => {
  it('muestra pesos sin decimales y con punto de miles', () => {
    expect(moneda('45000.00')).toMatch(/45\.000/)
    expect(moneda(null)).toBe('—')
  })

  it('no corre una fecha de calendario por la zona horaria', () => {
    expect(fecha('2026-10-24')).toBe('24/10/2026')
  })

  it('abrevia una fecha a día y mes, sin mover el día por la zona horaria', () => {
    expect(fechaCorta('2026-11-18')).toBe('18 nov')
    expect(fechaCorta('2027-01-01')).toBe('1 ene')
  })

  it('muestra los instantes en hora de Colombia', () => {
    // 14:30 UTC son las 9:30 de la mañana en Bogotá.
    expect(fechaHora('2026-10-24T14:30:00Z')).toMatch(/24\/10\/2026.*9:30/)
  })

  it('escribe una franja con el periodo una sola vez, o los dos si cruza el mediodía', () => {
    // 15:00 y 16:00 UTC son las 10 y las 11 de la mañana en Bogotá.
    expect(rangoHoras('2026-11-12T15:00:00Z', '2026-11-12T16:00:00Z')).toMatch(/^10:00 – 11:00 a\.\sm\.$/)
    expect(rangoHoras('2026-11-12T16:30:00Z', '2026-11-12T17:30:00Z')).toMatch(/^11:30 a\.\sm\. – 12:30 p\.\sm\.$/)
    expect(rangoHoras('2026-11-12T15:00:00Z', null)).toBeNull()
  })

  it('nombra el día de la semana de una fecha de calendario', () => {
    expect(fechaLarga('2026-11-12')).toBe('jueves, 12 de noviembre')
    expect(fechaCortaConDia('2026-11-14')).toBe('sáb 14 nov')
  })

  it('da la edad en meses hasta el año y después en años', () => {
    const hoy = new Date(2026, 10, 12)
    expect(edad('2020-09-09', hoy)).toBe('6 años')
    expect(edad('2025-11-12', hoy)).toBe('1 año')
    expect(edad('2026-03-20', hoy)).toBe('7 meses')
    expect(edad('2026-10-01', hoy)).toBe('1 mes')
    expect(edad('2027-01-01', hoy)).toBe('0 meses')
    expect(edad(null)).toBeNull()
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

  it('escribe el peso con coma decimal y sin ceros de más', () => {
    expect(peso(8.4)).toBe('8,4 kg')
    expect(peso(12)).toBe('12 kg')
    expect(peso(null)).toBe('—')
  })

  it('el día de un instante es el de Colombia, no el de UTC', () => {
    expect(diaISO('2026-11-13T00:30:00Z')).toBe('2026-11-12')
    expect(diaISO('2026-11-12T15:00:00Z')).toBe('2026-11-12')
  })
})
