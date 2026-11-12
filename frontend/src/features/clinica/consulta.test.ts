import { describe, expect, it } from 'vitest'

import type { EntradaHistoria } from './api'
import { VACIOS, anteriorFirmada, cambios, estacionInicial, faltanParaFirmar, siguienteDe, valoresDe } from './consulta'

const entrada = (id: string, fecha: string, estado: string, extra: Partial<EntradaHistoria> = {}): EntradaHistoria => ({
  id,
  mascota_id: 'm1',
  profesional_id: 'p1',
  tipo: 'domiciliaria',
  fecha,
  motivo: 'Vómito',
  estado,
  ...extra,
})

describe('la consulta guiada', () => {
  it('toma lo escrito de la consulta, con vacío donde no hay nada', () => {
    const valores = valoresDe(entrada('h1', '2026-11-12', 'borrador', { diagnostico: 'Gastritis', anamnesis: null }))
    expect(valores).toEqual({ ...VACIOS, motivo: 'Vómito', diagnostico: 'Gastritis' })
    expect(valoresDe(undefined)).toEqual(VACIOS)
  })

  it('guarda solo lo que cambió, sin espacios sobrantes', () => {
    const guardados = { ...VACIOS, motivo: 'Vómito' }
    expect(cambios({ ...guardados, motivo: ' Vómito ', diagnostico: '  Gastritis ' }, guardados)).toEqual({ diagnostico: 'Gastritis' })
    expect(cambios(guardados, guardados)).toEqual({})
  })

  it('para firmar pide motivo y diagnóstico, y el tratamiento si es la consulta de una visita', () => {
    expect(faltanParaFirmar(VACIOS, false)).toEqual(['motivo', 'diagnostico'])
    const conDiagnostico = { ...VACIOS, motivo: 'Vómito', diagnostico: 'Gastritis' }
    expect(faltanParaFirmar(conDiagnostico, false)).toEqual([])
    expect(faltanParaFirmar(conDiagnostico, true)).toEqual(['tratamiento'])
    expect(faltanParaFirmar({ ...conDiagnostico, tratamiento: '  ' }, true)).toEqual(['tratamiento'])
  })

  it('abre en el primer apartado vacío, o en el último si ya está todo', () => {
    expect(estacionInicial(VACIOS)).toBe(0)
    expect(estacionInicial({ ...VACIOS, motivo: 'Vómito', anamnesis: 'Comió basura' })).toBe(2)
    const completa = { ...VACIOS, motivo: 'a', anamnesis: 'b', examen_fisico: 'c', diagnostico: 'd', tratamiento: 'e' }
    expect(estacionInicial(completa)).toBe(4)
  })

  it('el botón nombra el apartado que sigue por su título', () => {
    expect(siguienteDe(1)).toBe('examen físico')
    expect(siguienteDe(3)).toBe('tratamiento')
  })

  it('la referencia es la última consulta firmada, no esta ni un borrador', () => {
    const historia = [
      entrada('h3', '2026-11-12', 'borrador'),
      entrada('h1', '2026-03-03', 'firmada'),
      entrada('h2', '2026-08-12', 'firmada'),
      entrada('h0', '2026-09-01', 'corregida'),
    ]
    expect(anteriorFirmada(historia)?.id).toBe('h2')
    expect(anteriorFirmada(historia, 'h2')?.id).toBe('h1')
    expect(anteriorFirmada([])).toBeUndefined()
  })
})
