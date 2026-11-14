import { describe, expect, it } from 'vitest'

import type { CuotaRead } from '@/types'

import { nombreCuota, porPagar, saldoDe } from './cuotas'

const cuota = (cambios: Partial<CuotaRead>): CuotaRead => ({
  id: 'q',
  periodo: '2026-10',
  tipo: 'cuota',
  meses: 1,
  fecha_vencimiento: '2026-10-21',
  valor: '75000.00',
  valor_pagado: '0.00',
  estado: 'pendiente',
  dias_mora: 0,
  descripcion: null,
  ...cambios,
})

describe('las cuotas dichas a una persona', () => {
  it('nombra la cuota por su mes, con el año solo si no es este', () => {
    const hoy = new Date(2026, 10, 12)
    expect(nombreCuota(cuota({}), hoy)).toBe('Cuota de octubre')
    expect(nombreCuota(cuota({ periodo: '2025-12' }), hoy)).toBe('Cuota de diciembre de 2025')
    // La descripción del backend es técnica: en una cuota no se usa.
    expect(nombreCuota(cuota({ descripcion: 'Cuota 2026-10' }), hoy)).toBe('Cuota de octubre')
    expect(nombreCuota(cuota({ periodo: '2026-01', meses: 3 }), hoy)).toBe('Cuota de enero a marzo')
    expect(nombreCuota(cuota({ periodo: '2026-11', meses: 3 }), hoy)).toBe('Cuota de noviembre de 2026 a enero de 2027')
    expect(nombreCuota(cuota({ tipo: 'ajuste', descripcion: 'Ajuste por agregar a Kira' }), hoy)).toBe('Ajuste por agregar a Kira')
    expect(nombreCuota(cuota({ tipo: 'ajuste2' }), hoy)).toBe('Ajuste de plan')
  })

  it('por pagar: ni pagadas ni anuladas, de la más antigua a la más reciente, con lo que falta', () => {
    const cuotas = [
      cuota({ id: 'nov', fecha_vencimiento: '2026-11-21' }),
      cuota({ id: 'pagada', estado: 'pagada' }),
      cuota({ id: 'sep', fecha_vencimiento: '2026-09-21', valor_pagado: '25000.00' }),
      cuota({ id: 'anulada', estado: 'anulada' }),
    ]
    expect(porPagar(cuotas).map((q) => q.id)).toEqual(['sep', 'nov'])
    expect(saldoDe(porPagar(cuotas)[0]!)).toBe(50000)
  })
})
