import { describe, expect, it } from 'vitest'

import type { PagoPortalRead } from '@/types'

import { avisoDelPago } from './pagos'

describe('los pagos dichos a la familia', () => {
  it('dice qué pasó con el pago con el que se vuelve de la pasarela', () => {
    const pago = (estado: string) => ({ id: 'p', estado }) as PagoPortalRead
    expect(avisoDelPago(undefined)).toBeNull()
    expect(avisoDelPago(pago('pendiente'))?.texto).toMatch(/se actualiza sola/)
    expect(avisoDelPago(pago('aprobado'))?.tono).toBe('ok')
    expect(avisoDelPago(pago('rechazado'))?.texto).toMatch(/no se hizo ningún cobro/)
    expect(avisoDelPago(pago('reversado'))?.tono).toBe('alerta')
  })
})
