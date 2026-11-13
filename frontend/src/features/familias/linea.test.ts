import { describe, expect, it } from 'vitest'

import type { EstacionRead } from '@/types'

import { esHoy, esTramo, orientacion, paradas, recorrido, resumen } from './linea'

let n = 0
function estacion(fecha: string, estado: EstacionRead['estado'], titulo = 'Cuota'): EstacionRead {
  n += 1
  return { tipo: 'cuota', referencia_id: `e${n}`, fecha, estado, titulo, mascota: null, mascota_id: null }
}

const HOY = '2026-11-10'

describe('línea de la familia', () => {
  it('junta en una parada lo del mismo día y le da el estado más urgente', () => {
    const [parada] = paradas([estacion('2026-09-05', 'hecha'), estacion('2026-09-05', 'vencida')])
    expect(parada.estaciones).toHaveLength(2)
    expect(parada.estado).toBe('vencida')
  })

  it('pone «hoy» entre lo pasado y lo que viene', () => {
    const elementos = recorrido([estacion('2026-12-05', 'proxima'), estacion('2026-10-05', 'hecha')], HOY)
    expect(elementos.map((e) => (esHoy(e) ? 'hoy' : esTramo(e) ? 'tramo' : e.fecha))).toEqual([
      '2026-10-05',
      'hoy',
      '2026-12-05',
    ])
  })

  it('pliega las hechas antiguas salvo la última, y nunca lo vencido', () => {
    const elementos = recorrido(
      [
        estacion('2026-06-05', 'hecha'),
        estacion('2026-07-05', 'vencida'),
        estacion('2026-08-05', 'hecha'),
        estacion('2026-09-05', 'hecha'),
        estacion('2026-12-05', 'proxima'),
      ],
      HOY,
    )
    const [tramo, ...resto] = elementos
    expect(esTramo(tramo) && tramo.paradas.map((p) => p.fecha)).toEqual(['2026-06-05', '2026-08-05'])
    expect(resto.map((e) => (esHoy(e) ? 'hoy' : !esTramo(e) && `${e.fecha} ${e.estado}`))).toEqual([
      '2026-07-05 vencida',
      '2026-09-05 hecha',
      'hoy',
      '2026-12-05 proxima',
    ])
  })

  it('no pliega cuando hay pocas hechas ni cuando se pide desplegar', () => {
    const pocas = [estacion('2026-08-05', 'hecha'), estacion('2026-09-05', 'hecha')]
    expect(recorrido(pocas, HOY).some(esTramo)).toBe(false)
    const muchas = [...pocas, estacion('2026-10-05', 'hecha')]
    expect(recorrido(muchas, HOY).some(esTramo)).toBe(true)
    expect(recorrido(muchas, HOY, true).some(esTramo)).toBe(false)
  })

  it('resume lo vencido y lo próximo para quien no ve la línea', () => {
    const corta = (iso: string) => iso.slice(5)
    expect(resumen([estacion('2026-07-05', 'vencida'), estacion('2026-11-18', 'proxima', 'Vacuna')], corta)).toBe(
      '1 vencida, próxima: Vacuna el 11-18',
    )
    expect(resumen([], corta)).toBe('Nada vencido, nada programado')
  })

  it('pasa a vertical cuando las paradas no caben con su rótulo', () => {
    expect(orientacion(900, 7)).toBe('horizontal')
    expect(orientacion(600, 7)).toBe('vertical')
    expect(orientacion(0, 0)).toBe('horizontal')
  })
})
