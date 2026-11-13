import { describe, expect, it } from 'vitest'

import type { EstacionRead } from '@/types'

import { accionPrincipal, conProximoCobro, delPeludo, meses, PROXIMO_COBRO, recorrido } from './linea'

let n = 0
function estacion(fecha: string, estado: EstacionRead['estado'], cambios: Partial<EstacionRead> = {}): EstacionRead {
  n += 1
  return { tipo: 'cuota', referencia_id: `e${n}`, fecha, estado, titulo: 'Cuota de octubre', mascota: null, mascota_id: null, ...cambios }
}

const HOY = '2026-11-12'
const vacuna = (fecha: string, estado: EstacionRead['estado'], mascota: string, id: string) =>
  estacion(fecha, estado, { tipo: 'preventivo', titulo: 'Vacuna', mascota, mascota_id: id })

describe('línea del portal', () => {
  it('agrupa lo vencido encima de hoy y deja lo que viene debajo', () => {
    const elementos = recorrido(
      [
        estacion('2026-12-21', 'futura', { titulo: 'Cuota de diciembre' }),
        estacion('2026-08-21', 'vencida', { titulo: 'Cuota de agosto' }),
        estacion('2026-09-21', 'vencida', { titulo: 'Cuota de septiembre' }),
        vacuna('2026-11-04', 'vencida', 'Luna', 'l'),
        vacuna('2026-11-04', 'vencida', 'Michi', 'm'),
        vacuna('2026-11-04', 'vencida', 'Luna', 'l'),
        estacion('2026-11-21', 'proxima', { titulo: 'Cuota de noviembre' }),
        estacion('2026-07-21', 'hecha', { titulo: 'Cuota de julio' }),
      ],
      HOY,
    )
    expect(elementos.map((e) => e.tipo)).toEqual(['hechas', 'cuotas-vencidas', 'preventivos-vencidos', 'hoy', 'estacion', 'estacion'])
    const preventivos = elementos[2]
    expect(preventivos.tipo === 'preventivos-vencidos' && preventivos.porMascota).toEqual([
      { mascota: 'Luna', mascotaId: 'l', cuantos: 2 },
      { mascota: 'Michi', mascotaId: 'm', cuantos: 1 },
    ])
    const despues = elementos.slice(4).map((e) => (e.tipo === 'estacion' ? e.estacion.titulo : e.tipo))
    expect(despues).toEqual(['Cuota de noviembre', 'Cuota de diciembre'])
  })

  it('lo vencido más antiguo va primero, y una visita sin cerrar va suelta', () => {
    const elementos = recorrido(
      [
        vacuna('2026-10-01', 'vencida', 'Luna', 'l'),
        estacion('2026-11-02', 'vencida', { tipo: 'servicio', titulo: 'Consulta domiciliaria', mascota: 'Luna', mascota_id: 'l' }),
        estacion('2026-10-21', 'vencida'),
      ],
      HOY,
    )
    expect(elementos.map((e) => e.tipo)).toEqual(['preventivos-vencidos', 'cuotas-vencidas', 'estacion', 'hoy', 'fin'])
  })

  it('una hecha de hoy no se pliega: se ve junto a lo de hoy', () => {
    const elementos = recorrido([estacion(HOY, 'hecha', { titulo: 'Cuota de noviembre' })], HOY)
    expect(elementos.map((e) => e.tipo)).toEqual(['hoy', 'estacion'])
  })

  it('pagar lo vencido va primero: con cuotas vencidas el plan no deja agendar', () => {
    const conTodo = recorrido([estacion('2026-10-21', 'vencida'), vacuna('2026-11-04', 'vencida', 'Luna', 'l')], HOY)
    expect(accionPrincipal(conTodo, true)).toBe('pagar-vencidas')
    const soloPreventivos = recorrido([vacuna('2026-11-04', 'vencida', 'Luna', 'l'), estacion('2026-11-21', 'proxima')], HOY)
    expect(accionPrincipal(soloPreventivos, true)).toBe('agendar-preventivos')
    // Sin poder agendar, lo siguiente que la familia sí puede hacer es pagar la próxima cuota.
    expect(accionPrincipal(soloPreventivos, false)).toBe('pagar-proxima')
    expect(accionPrincipal(recorrido([estacion('2026-11-21', 'proxima')], HOY), true)).toBe('pagar-proxima')
    expect(accionPrincipal(recorrido([vacuna('2026-11-21', 'proxima', 'Luna', 'l')], HOY), true)).toBeNull()
  })

  it('nombra los meses de las cuotas como se dicen', () => {
    const cuota = (titulo: string) => estacion('2026-08-21', 'vencida', { titulo })
    expect(meses([cuota('Cuota de agosto')])).toBe('agosto')
    expect(meses([cuota('Cuota de agosto'), cuota('Cuota de septiembre'), cuota('Cuota de octubre')])).toBe('agosto, septiembre y octubre')
  })

  it('la línea de un peludo es la suya, por id: dos peludos pueden llamarse igual', () => {
    const luna = vacuna('2026-11-04', 'vencida', 'Luna', 'l1')
    const otraLuna = vacuna('2026-11-04', 'vencida', 'Luna', 'l2')
    expect(delPeludo([luna, otraLuna, estacion('2026-10-21', 'vencida')], 'l1')).toEqual([luna])
  })

  it('no muere en hoy: sin nada después, cierra con lo que viene', () => {
    expect(recorrido([estacion('2026-10-21', 'vencida')], HOY).map((e) => e.tipo)).toEqual(['cuotas-vencidas', 'hoy', 'fin'])
  })

  it('el próximo cobro entra cuando su cuota aún no existe, pero no se paga desde ahí', () => {
    const vencida = estacion('2026-10-21', 'vencida')
    const con = conProximoCobro([vencida], { fecha: '2026-11-21' }, HOY)
    expect(con.map((e) => [e.referencia_id === PROXIMO_COBRO, e.estado])).toEqual([[false, 'vencida'], [true, 'proxima']])
    expect(accionPrincipal(recorrido(conProximoCobro([], { fecha: '2026-11-21' }, HOY), HOY), true)).toBeNull()
    // Si la línea ya trae la cuota, o el cobro ya pasó, no se repite.
    const cuota = estacion('2026-11-21', 'proxima')
    expect(conProximoCobro([cuota], { fecha: '2026-11-21' }, HOY)).toEqual([cuota])
    expect(conProximoCobro([], { fecha: '2026-11-01' }, HOY)).toEqual([])
    expect(conProximoCobro([], null, HOY)).toEqual([])
  })

  it('reparte los preventivos por peludo en el orden de la pantalla', () => {
    const [grupo] = recorrido([vacuna('2026-11-04', 'vencida', 'Luna', 'l'), vacuna('2026-11-04', 'vencida', 'Michi', 'm')], HOY, ['m', 'l'])
    expect(grupo.tipo === 'preventivos-vencidos' && grupo.porMascota.map((m) => m.mascota)).toEqual(['Michi', 'Luna'])
  })
})
