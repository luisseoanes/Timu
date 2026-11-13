import { describe, expect, it } from 'vitest'

import type { ServicioPortalRead } from '@/types'

import { estadoDeCita, pasadas, puedeCambiar, puedeCancelar } from './citas'

const cita = (estado: string, programado_para: string | null, id = estado): ServicioPortalRead => ({
  id,
  mascota_id: null,
  tipo_codigo: 'consulta_domiciliaria',
  estado,
  programado_para,
  termina_en: null,
})

describe('las citas dichas a la familia', () => {
  it('nombra cada estado con sus palabras, y explica los que piden algo', () => {
    expect(estadoDeCita('en_ruta')).toEqual({ label: 'En camino', tono: 'info', explicacion: 'El médico va en camino.' })
    expect(estadoDeCita('completado').label).toBe('Atendida')
    expect(estadoDeCita('desconocido')).toEqual({ label: 'desconocido', tono: 'neutro' })
  })

  it('solo ofrece lo que el backend acepta', () => {
    expect(puedeCambiar(cita('agendado', null))).toBe(true)
    expect(puedeCambiar(cita('pendiente_autorizacion', null))).toBe(false)
    expect(puedeCancelar(cita('pendiente_autorizacion', null))).toBe(true)
    expect(puedeCancelar(cita('solicitado', null))).toBe(false)
    expect(puedeCancelar(cita('en_ruta', null))).toBe(false)
  })

  it('las pasadas: cerradas o con la hora cumplida, sin las que están en curso, la más reciente primero', () => {
    const ahora = new Date('2026-11-12T15:00:00Z')
    const todas = [
      cita('agendado', '2026-11-20T15:00:00Z', 'futura'),
      cita('completado', '2026-10-01T15:00:00Z', 'vieja'),
      cita('en_ruta', '2026-11-12T13:00:00Z', 'en-curso'),
      cita('agendado', '2026-11-05T15:00:00Z', 'sin-cerrar'),
      cita('cancelado', '2026-12-01T15:00:00Z', 'cancelada'),
    ]
    expect(pasadas(todas, ahora).map((c) => c.id)).toEqual(['cancelada', 'sin-cerrar', 'vieja'])
  })
})
