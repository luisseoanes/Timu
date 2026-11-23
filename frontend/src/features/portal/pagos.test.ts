import { describe, expect, it } from 'vitest'

import type { CuotaRead, PagoPortalRead } from '@/types'

import type { PlanPortal } from './api'
import { avisoDelPago, avisoPagoParcial } from './pagos'

describe('los pagos dichos a la familia', () => {
  it('dice qué pasó con el pago con el que se vuelve de la pasarela', () => {
    const pago = (estado: string) => ({ id: 'p', estado }) as PagoPortalRead
    expect(avisoDelPago(undefined)).toBeNull()
    expect(avisoDelPago(pago('pendiente'))?.texto).toMatch(/se actualiza sola/)
    expect(avisoDelPago(pago('aprobado'))?.tono).toBe('ok')
    expect(avisoDelPago(pago('rechazado'))?.texto).toMatch(/no se hizo ningún cobro/)
    expect(avisoDelPago(pago('reversado'))?.tono).toBe('alerta')
  })

  it('con varias vencidas y el plan en pausa, dice que pagar una no lo cambia (DEU-77)', () => {
    const vencida = { estado: 'pendiente', dias_mora: 10 } as CuotaRead
    const plan = (estado: string) => ({ estado }) as PlanPortal
    expect(avisoPagoParcial(plan('congelada'), [vencida, vencida])).toMatch(/sigue en pausa hasta que pagues todas/)
    expect(avisoPagoParcial(plan('en_mora'), [vencida, vencida])).toMatch(/sin poder agendar/)
    // Con una sola vencida, pagarla sí lo cambia; y al día no hay pausa que explicar.
    expect(avisoPagoParcial(plan('congelada'), [vencida, { estado: 'pendiente', dias_mora: 0 } as CuotaRead])).toBeNull()
    expect(avisoPagoParcial(plan('activa'), [vencida, vencida])).toBeNull()
    expect(avisoPagoParcial(undefined, [vencida, vencida])).toBeNull()
  })
})
