import { describe, expect, it } from 'vitest'

import type { PlanPortal } from './api'
import { alPagar, cupo, estadoDelPlan, finDeLinea, frase, motivoSinAgendar, planesDe } from './plan'

const plan = (estado: string, mascotas = ['Luna', 'Michi']): PlanPortal => ({
  estado,
  periodicidad: 'mensual',
  valor_periodo: '75000.00',
  valor_mensual: '75000.00',
  fecha_inicio: '2026-01-01',
  fecha_renovacion: '2027-01-01',
  mascotas: mascotas.map((m) => ({ mascota_id: m, mascota: m, plan: 'Plan Familiar', color: 'verde' as const, valor_mensual: '37500.00', beneficios: [] })),
})

describe('el plan dicho a la familia', () => {
  it('dice por qué está como está y qué hacer', () => {
    expect(frase(plan('activa'), 0)).toBe('Tu plan está al día. Se renueva el 1 de enero de 2027.')
    expect(frase(plan('congelada'), 3)).toBe('Tus 3 cuotas vencidas pausaron el plan. Al pagar, Luna y Michi recuperan sus beneficios.')
    expect(frase(plan('congelada', ['Luna']), 1)).toBe('Tu cuota vencida pausó el plan. Al pagar, Luna recupera sus beneficios.')
    expect(frase(plan('congelada'), 0)).toMatch(/en pausa/)
    // Sin la línea no se sabe cuántas: no inventa un número ni dice que no hay ninguna.
    expect(frase(plan('congelada'), null)).toBe('Tus cuotas vencidas pausaron el plan. Al pagar, Luna y Michi recuperan sus beneficios.')
    expect(frase(plan('en_mora'), 2)).toMatch(/Ponte al día/)
    expect(frase(plan('cancelada'), 0)).toMatch(/cancelado/)
    expect(frase(plan('prospecto'), 0)).toMatch(/en proceso/)
    expect(frase(null, 0)).toMatch(/Aún no tienes un plan activo/)
  })

  it('solo deja agendar con el plan activo, como la elegibilidad del backend', () => {
    expect(motivoSinAgendar(plan('activa'))).toBeNull()
    expect(motivoSinAgendar(plan('congelada'))).toBe('Tu plan está en pausa por cuotas vencidas: al pagarlas, podrás agendar.')
    expect(motivoSinAgendar(plan('en_mora'))).toBe('Tienes cuotas vencidas: al pagarlas, podrás agendar.')
    expect(motivoSinAgendar(null)).toMatch(/plan activo/)
    expect(motivoSinAgendar(plan('cancelada'))).toMatch(/WhatsApp/)
    expect(motivoSinAgendar(undefined)).not.toBeNull()
  })

  it('dice el cupo de frente, sin «ilimitado»', () => {
    const b = { tipo_servicio: 'x', cupo: 6, periodo: 'anual', usados: 2, disponibles: 4, cobertura_pct: 100 }
    expect(cupo(b)).toBe('le quedan 4 de 6 este año')
    expect(cupo({ ...b, periodo: 'mensual', cupo: 2, disponibles: 1 })).toBe('le queda 1 de 2 este mes')
    expect(cupo({ ...b, cupo: null, disponibles: null })).toBe('sin tope de usos este año')
  })

  it('para la familia el plan congelado está «en pausa», la misma palabra que la frase, y avisa', () => {
    expect(estadoDelPlan('congelada')).toEqual({ label: 'En pausa', tono: 'alerta' })
    expect(estadoDelPlan('activa').tono).toBe('ok')
    expect(estadoDelPlan('otro')).toEqual({ label: 'En proceso', tono: 'info' })
  })

  it('agrupa los peludos por plan, con el color del catálogo', () => {
    const p = plan('activa', ['Luna', 'Michi'])
    p.mascotas[1] = { ...p.mascotas[1], plan: 'Colita Feliz', color: 'naranja' }
    expect(planesDe(p)).toEqual([
      { nombre: 'Plan Familiar', color: 'verde', mascotas: ['Luna'] },
      { nombre: 'Colita Feliz', color: 'naranja', mascotas: ['Michi'] },
    ])
  })

  it('cierra la línea diciendo qué viene, según el plan', () => {
    expect(finDeLinea(plan('congelada'))).toMatch(/^Al ponerte al día/)
    expect(finDeLinea(plan('activa'), 'Luna')).toBe('Nada más programado. Cuando agendes una visita para Luna, aparece aquí.')
    // La línea de un peludo no lleva cuotas: su cierre no las promete.
    expect(finDeLinea(plan('congelada'), 'Michi')).toBe('Al ponerte al día, aquí aparecen las vacunas, desparasitaciones y visitas que agendes para Michi.')
  })

  it('junto al saldo dice qué cambia al pagar', () => {
    expect(alPagar(plan('congelada'))).toMatch(/sale de la pausa/)
    expect(alPagar(plan('en_mora'))).toMatch(/volver a agendar/)
    expect(alPagar(plan('activa'))).toBeNull()
  })
})
