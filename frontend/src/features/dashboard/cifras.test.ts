import { describe, expect, it } from 'vitest'

import type { Evolucion } from './api'
import { CIFRAS, contraQue, dominio, formatear, formatearEje, mesLargo, ordenCifras, primerNombre, variacion } from './cifras'

describe('variación contra el período comparable', () => {
  it('un porcentaje cambia en puntos, no en porcentaje de porcentaje', () => {
    expect(variacion(CIFRAS.rutas, 0.94, 0.9)).toEqual({ texto: '4 puntos', direccion: 'sube', tono: 'buena' })
    expect(variacion(CIFRAS.rutas, 0.89, 0.9)).toEqual({ texto: '1 punto', direccion: 'baja', tono: 'mala' })
  })

  it('más contratos en mora es una mala noticia', () => {
    expect(variacion(CIFRAS.mora, 21, 18)).toEqual({ texto: '3 más', direccion: 'sube', tono: 'mala' })
    expect(variacion(CIFRAS.mora, 15, 18)?.tono).toBe('buena')
  })

  it('el recaudo se compara en proporción y, sin recaudo antes, en pesos', () => {
    expect(variacion(CIFRAS.recaudo, 1_100_000, 1_000_000)).toEqual({ texto: '10%', direccion: 'sube', tono: 'buena' })
    expect(variacion(CIFRAS.recaudo, 495_000, 0)?.texto).toMatch(/^\$\s495\.000 más$/)
  })

  it('dice «sin cambio» cuando no se mueve, y nada sin dato con qué comparar', () => {
    expect(variacion(CIFRAS.vigentes, 4, 4)).toEqual({ texto: 'sin cambio', direccion: 'igual', tono: 'neutra' })
    expect(variacion(CIFRAS.satisfaccion, 4.62, 4.6)?.direccion).toBe('igual')
    expect(variacion(CIFRAS.rutas, 0.5, null)).toBeNull()
    expect(variacion(CIFRAS.rutas, null, 0.5)).toBeNull()
  })
})

describe('formatos', () => {
  it('cada escala se lee como en Colombia', () => {
    expect(formatear(4.6, 'puntaje')).toBe('4,6 / 5')
    expect(formatear(0.925, 'proporcion')).toBe('93%')
    expect(formatear(1234, 'entero')).toBe('1.234')
    expect(formatear(null, 'moneda')).toBe('—')
    expect(formatearEje(1_200_000, 'moneda')).toMatch(/^\$ 1,2\sM/)
    expect(formatearEje(0.5, 'proporcion')).toBe('50%')
  })

  it('el eje termina en un número redondo con cuatro marcas', () => {
    expect(dominio('entero', [3, 7, 9])).toEqual({ min: 0, max: 12, marcas: [0, 3, 6, 9, 12] })
    expect(dominio('moneda', [495_000, 240_000]).max).toBe(800_000)
    expect(dominio('entero', [])).toEqual({ min: 0, max: 4, marcas: [0, 1, 2, 3, 4] })
    expect(dominio('puntaje', [4.6]).min).toBe(1)
  })

  it('el mes en curso dice hasta qué día va', () => {
    const mes = { periodo: { desde: '2026-11-01', hasta: '2026-11-13', ciudad: null }, indicadores: {}, parcial: true }
    expect(mesLargo(mes)).toBe('noviembre de 2026, hasta el 13')
    expect(mesLargo({ ...mes, parcial: false })).toBe('noviembre de 2026')
  })

  it('nombra el período con que se compara', () => {
    const evolucion: Evolucion = {
      anterior: { periodo: { desde: '2026-10-01', hasta: '2026-10-13', ciudad: null }, indicadores: {} },
      meses: [],
    }
    expect(contraQue(evolucion)).toBe('contra 1 oct – 13 oct')
    expect(contraQue(undefined)).toBeNull()
  })
})

describe('el saludo y el orden', () => {
  it('saluda por el nombre, no por el tratamiento', () => {
    expect(primerNombre('Dra. Sara Díaz')).toBe('Sara')
    expect(primerNombre('Valentina Ríos')).toBe('Valentina')
    expect(primerNombre(undefined)).toBe('')
  })

  it('operaciones ve primero rutas y satisfacción; los demás, afiliados y cartera', () => {
    expect(ordenCifras('operaciones').slice(0, 2)).toEqual(['rutas', 'satisfaccion'])
    expect(ordenCifras('comercial').slice(0, 2)).toEqual(['vigentes', 'afiliaciones'])
    expect(new Set(ordenCifras('admin'))).toEqual(new Set(ordenCifras('operaciones')))
  })
})
