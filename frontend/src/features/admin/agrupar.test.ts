import { describe, expect, it } from 'vitest'

import { agruparPorMotivo } from './agrupar'

describe('lo que falló por el mismo motivo (DEU-73)', () => {
  it('dice cada motivo una vez, con lo que falló por él, en el orden en que aparece', () => {
    const casos = [
      { caso: 'Pregunta general', motivo: 'Sin IA configurada' },
      { caso: 'Consulta médica', motivo: 'Sin IA configurada' },
      { caso: 'Descuento', motivo: 'Inventó un descuento' },
      { caso: 'Tema ajeno', motivo: 'Sin IA configurada' },
      { caso: 'Saludo', motivo: null },
    ]
    expect(agruparPorMotivo(casos, (c) => c.motivo, (c) => c.caso)).toEqual([
      { motivo: 'Sin IA configurada', nombres: ['Pregunta general', 'Consulta médica', 'Tema ajeno'] },
      { motivo: 'Inventó un descuento', nombres: ['Descuento'] },
    ])
  })
})
