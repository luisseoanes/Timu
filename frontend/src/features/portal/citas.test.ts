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
    // Comparte el tono de Confirmada, no su icono (techo 41).
    expect(estadoDeCita('completado').icono).toBe('huella')
    expect(estadoDeCita('agendado').icono).toBeUndefined()
    expect(estadoDeCita('desconocido')).toEqual({ label: 'desconocido', tono: 'neutro' })
  })

  it('ofrece lo que dice el backend en cada cita, no lo que deduciría de su estado', () => {
    const confirmada = cita('agendado', null)
    expect(puedeCambiar(confirmada)).toBe(false)
    expect(puedeCambiar({ ...confirmada, puede_cambiar: true })).toBe(true)
    // Confirmada pero en la ruta del día, o a pocas horas: el backend dice que no (DEU-2).
    expect(puedeCancelar({ ...confirmada, puede_cancelar: false, sin_cambios: 'Faltan menos de 4 horas' })).toBe(false)
    expect(puedeCancelar({ ...cita('pendiente_autorizacion', null), puede_cancelar: true })).toBe(true)
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
