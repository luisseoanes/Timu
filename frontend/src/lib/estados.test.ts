import { describe, expect, it } from 'vitest'

import { estadoCuota } from './estados'

describe('estadoCuota', () => {
  it('una cuota abierta con mora se ve vencida, aunque la API la guarde pendiente o parcial', () => {
    expect(estadoCuota({ estado: 'pendiente', dias_mora: 82 })).toBe('vencida')
    expect(estadoCuota({ estado: 'parcial', dias_mora: 3 })).toBe('vencida')
  })

  it('sin mora, o pagada o anulada, se ve como la guarda la API', () => {
    expect(estadoCuota({ estado: 'pendiente', dias_mora: 0 })).toBe('pendiente')
    expect(estadoCuota({ estado: 'pagada', dias_mora: 0 })).toBe('pagada')
    expect(estadoCuota({ estado: 'anulada', dias_mora: 40 })).toBe('anulada')
  })
})
