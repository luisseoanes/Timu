import { describe, expect, it } from 'vitest'

import { enlaceWhatsApp } from './enlaces'

describe('enlaces', () => {
  it('escribe a WhatsApp sin el «+» del teléfono', () => {
    expect(enlaceWhatsApp('+57 300 111 2233')).toBe('https://wa.me/573001112233')
  })
})
