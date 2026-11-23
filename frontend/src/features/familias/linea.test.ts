import { describe, expect, it } from 'vitest'

import type { EstacionRead } from '@/types'

import { colorDeEstacion, colorDeLinea, esGrupoVencidas, esTramo, orientacion, paradas, recorrido, resumen, type Elemento } from './linea'

/** Cada elemento en una palabra: «hoy», «tramo», «vencidas» o la fecha y el estado de la parada. */
const clave = (e: Elemento) => ('tipo' in e ? e.tipo : `${e.fecha} ${e.estado}`)

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
    expect(elementos.map(clave)).toEqual(['2026-10-05 hecha', 'hoy', '2026-12-05 proxima'])
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
    expect(resto.map(clave)).toEqual([
      '2026-07-05 vencida',
      '2026-09-05 hecha',
      'hoy',
      '2026-12-05 proxima',
    ])
  })

  it('en vertical agrupa tres o más vencidas para que «hoy» suba, sin esconderlas', () => {
    const estaciones = [
      estacion('2026-07-05', 'vencida'),
      estacion('2026-08-01', 'hecha'),
      estacion('2026-08-05', 'vencida'),
      estacion('2026-09-05', 'vencida'),
      estacion('2026-09-05', 'vencida', 'Vacuna'),
      estacion('2026-12-05', 'proxima'),
    ]
    const agrupado = recorrido(estaciones, HOY, false, true)
    expect(agrupado.map(clave)).toEqual(['vencidas', '2026-08-01 hecha', 'hoy', '2026-12-05 proxima'])
    const grupo = agrupado.find(esGrupoVencidas)
    expect(grupo?.paradas.map((p) => p.fecha)).toEqual(['2026-07-05', '2026-08-05', '2026-09-05'])
    // En horizontal (o con el grupo abierto) cada vencida va en su parada.
    expect(recorrido(estaciones, HOY).some(esGrupoVencidas)).toBe(false)
    // Con dos vencidas no hay grupo: caben.
    expect(recorrido(estaciones.slice(1, 3), HOY, false, true).some(esGrupoVencidas)).toBe(false)
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

describe('el color de la línea con uno o varios planes (DEU-78)', () => {
  const verde = { color: 'verde' as const, mascotas: ['Luna'] }
  const naranja = { color: 'naranja' as const, mascotas: ['Michi'] }

  it('con un plan va en su color, sin plan en gris y con varios en marino', () => {
    expect(colorDeLinea([verde])).toBe('verde')
    expect(colorDeLinea([])).toBe('ninguno')
    expect(colorDeLinea([verde, naranja])).toBe('varios')
    // Dos planes del mismo color no son «varios».
    expect(colorDeLinea([verde, { color: 'verde', mascotas: ['Max'] }])).toBe('verde')
  })

  it('con varios planes, cada estación toma el del plan de su peludo', () => {
    const planes = [verde, naranja]
    expect(colorDeEstacion(planes, [{ mascota: 'Luna' }])).toBe('verde')
    expect(colorDeEstacion(planes, [{ mascota: 'Michi' }])).toBe('naranja')
    // Una cuota es de la familia, y un día con los dos peludos no es de un plan: marino.
    expect(colorDeEstacion(planes, [{ mascota: null }])).toBeUndefined()
    expect(colorDeEstacion(planes, [{ mascota: 'Luna' }, { mascota: 'Michi' }])).toBeUndefined()
    // Con un solo plan no hace falta: el punto ya va en el color de la línea.
    expect(colorDeEstacion([verde], [{ mascota: 'Luna' }])).toBeUndefined()
  })
})
