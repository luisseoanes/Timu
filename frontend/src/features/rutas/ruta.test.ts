import { describe, expect, it } from 'vitest'

import type { ParadaRead, RutaRead } from '@/types'

import {
  aQuien,
  avance,
  comoLlegar,
  descripcion,
  donde,
  duracion,
  enlaceWhatsApp,
  enRuta,
  estadoEstacion,
  paradaActual,
  partirDireccion,
  resumen,
} from './ruta'

function parada(orden: number, estado: ParadaRead['estado'], extra: Partial<ParadaRead> = {}): ParadaRead {
  return {
    id: `p${orden}`,
    servicio_id: `s${orden}`,
    orden,
    estado,
    latitud: 4.7,
    longitud: -74.05,
    llegada_estimada: '2026-11-12T15:20:00Z',
    llegada_en: null,
    salida_en: null,
    nota: null,
    motivo_omision: null,
    tipo_codigo: 'consulta_domiciliaria',
    observaciones: null,
    ventana_desde: '2026-11-12T15:00:00Z',
    ventana_hasta: '2026-11-12T16:00:00Z',
    familia: { id: `f${orden}`, titular_nombre: `Familia ${orden}`, telefono: '+573001112233', direccion: 'Cra 43A # 7 sur-170', complemento: null, barrio: 'El Poblado' },
    mascota: { id: `m${orden}`, nombre: 'Max', especie: 'perro', fecha_nacimiento: null, peso_kg: null },
    ...extra,
  }
}

function ruta(paradas: ParadaRead[], extra: Partial<RutaRead> = {}): RutaRead {
  return {
    id: 'r1',
    fecha: '2026-11-12',
    ciudad: 'Medellin',
    responsable_id: 'm1',
    estado: 'en_curso',
    distancia_km: 18.4,
    duracion_min: 250,
    inicio_real: null,
    fin_real: null,
    paradas,
    ...extra,
  }
}

describe('la parada que toca', () => {
  it('es la que está en curso, aunque haya pendientes antes en la lista', () => {
    const r = ruta([parada(1, 'completada'), parada(2, 'pendiente'), parada(3, 'en_sitio')])
    expect(paradaActual(r)?.id).toBe('p3')
  })

  it('sin ninguna en curso, es la primera pendiente', () => {
    expect(paradaActual(ruta([parada(1, 'completada'), parada(2, 'pendiente'), parada(3, 'pendiente')]))?.id).toBe('p2')
  })

  it('una ruta cerrada no tiene', () => {
    expect(paradaActual(ruta([parada(1, 'pendiente')], { estado: 'cancelada' }))).toBeUndefined()
    expect(paradaActual(ruta([parada(1, 'completada')], { estado: 'finalizada' }))).toBeUndefined()
  })

  it('da a cada parada su lugar en la línea', () => {
    const r = ruta([parada(1, 'completada'), parada(2, 'en_camino'), parada(3, 'pendiente')])
    const actual = paradaActual(r)
    expect(r.paradas.map((p) => estadoEstacion(p, actual))).toEqual(['hecha', 'actual', 'pendiente'])
  })
})

describe('el avance de la ruta', () => {
  const r = ruta([parada(1, 'completada'), parada(2, 'en_camino'), parada(3, 'pendiente'), parada(4, 'omitida')])

  it('no cuenta una parada omitida: ya no es de la ruta', () => {
    expect(enRuta(r).map((p) => p.id)).toEqual(['p1', 'p2', 'p3'])
    expect(avance([r])).toEqual({ hechas: 1, total: 3 })
  })

  it('se dice con las paradas y los kilómetros, con coma decimal', () => {
    expect(resumen([r])).toBe('1 de 3 paradas · 18,4 km')
    expect(resumen([ruta([parada(1, 'completada')], { distancia_km: null })])).toBe('1 de 1 parada')
  })

  it('suma varias rutas de la misma persona', () => {
    expect(resumen([r, ruta([parada(5, 'pendiente')], { distancia_km: 1.6 })])).toBe('1 de 4 paradas · 20 km')
  })

  it('describe la miniatura para quien no la ve', () => {
    expect(descripcion(r)).toMatch(/^1 de 3 paradas hechas\. Sigue Familia 2, llegada estimada a las 10:20/)
    expect(descripcion(ruta([parada(1, 'completada')], { estado: 'finalizada' }))).toBe('1 de 1 parada hecha')
    expect(descripcion(ruta([parada(1, 'pendiente', { llegada_estimada: null })]))).toBe('0 de 1 parada hecha. Sigue Familia 1')
  })

  it('escribe la duración en horas y minutos', () => {
    expect(duracion(250)).toBe('4 h 10 min')
    expect(duracion(120)).toBe('2 h')
    expect(duracion(45)).toBe('45 min')
    expect(duracion(null)).toBeNull()
  })
})

describe('a quién y dónde', () => {
  it('nombra a la familia y a su mascota', () => {
    expect(aQuien(parada(1, 'pendiente'))).toBe('Familia 1 · Max')
    expect(aQuien(parada(1, 'pendiente', { mascota: null }))).toBe('Familia 1')
  })

  it('escribe solo lo que la familia tiene registrado, y si no tiene nada, lo dice', () => {
    const p = parada(1, 'pendiente')
    expect(donde(p.familia)).toBe('Cra 43A # 7 sur-170, El Poblado')
    expect(donde({ ...p.familia, direccion: null })).toBe('El Poblado')
    expect(donde({ ...p.familia, barrio: null })).toBe('Cra 43A # 7 sur-170')
    expect(donde({ ...p.familia, direccion: null, barrio: null })).toBe('Sin dirección registrada')
  })

  it('lleva la navegación a las coordenadas que usó el optimizador', () => {
    expect(comoLlegar(parada(1, 'pendiente'), 'Medellin')).toBe('https://www.google.com/maps/dir/?api=1&destination=4.7%2C-74.05')
  })

  it('sin coordenadas, a la dirección escrita con su ciudad', () => {
    const sinCoordenadas = parada(1, 'pendiente', { latitud: null, longitud: null })
    expect(new URL(comoLlegar(sinCoordenadas, 'Medellin')).searchParams.get('destination')).toBe(
      'Cra 43A # 7 sur-170, El Poblado, Medellin',
    )
    const sinBarrio = { ...sinCoordenadas, familia: { ...sinCoordenadas.familia, barrio: null } }
    expect(new URL(comoLlegar(sinBarrio, 'Medellin')).searchParams.get('destination')).toBe('Cra 43A # 7 sur-170, Medellin')
  })

  it('aparta el número de casa para que no se parta entre dos líneas', () => {
    expect(partirDireccion('Avenida 19 # 100-12, Chapinero')).toEqual(['Avenida 19 ', '# 100-12', ', Chapinero'])
    expect(partirDireccion('Cra 43A # 7 sur-170')).toEqual(['Cra 43A ', '# 7 sur-170', ''])
    expect(partirDireccion('Chapinero')).toEqual(['Chapinero', '', ''])
  })

  it('escribe a WhatsApp sin el «+» del teléfono', () => {
    expect(enlaceWhatsApp('+57 300 111 2233')).toBe('https://wa.me/573001112233')
  })
})
