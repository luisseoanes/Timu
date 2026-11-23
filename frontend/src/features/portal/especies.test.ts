import { describe, expect, it } from 'vitest'

import { nombreEspecie } from './especies'

describe('la especie dicha a la familia (DEU-80)', () => {
  const catalogo = [
    { codigo: 'canino', nombre: 'Canino' },
    { codigo: 'felino', nombre: 'Felino' },
    { codigo: 'ave', nombre: 'Ave' },
  ]

  it('dice «Perro» y «Gato», como el alta y el registro, y no el nombre del catálogo', () => {
    expect(nombreEspecie('canino', catalogo)).toBe('Perro')
    expect(nombreEspecie('felino', catalogo)).toBe('Gato')
  })

  it('otra especie va con el nombre del catálogo, y sin catálogo con su código', () => {
    expect(nombreEspecie('ave', catalogo)).toBe('Ave')
    expect(nombreEspecie('ave', undefined)).toBe('ave')
  })
})
