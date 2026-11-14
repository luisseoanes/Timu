import { fechaCorta, moneda, porcentaje } from '@/lib/formato'
import type { Rol } from '@/types'

import type { Evolucion, MesEvolucion, ValoresIndicadores } from './api'

/** Valores de un mes de la serie: el backend solo manda los códigos que se le piden. */
type Valores = Partial<ValoresIndicadores>

export type CodigoCifra = 'vigentes' | 'afiliaciones' | 'recaudo' | 'mora' | 'rutas' | 'satisfaccion'

/** Escala del eje de un gráfico: decide el formato de los valores y su dominio. */
export type Escala = 'entero' | 'moneda' | 'proporcion' | 'puntaje'

export interface Serie {
  nombre: string
  valor: (v: Valores) => number | null | undefined
}

export interface DefCifra {
  codigo: CodigoCifra
  titulo: string
  /** Indicador de docs/indicadores.md cuya fórmula explica la cifra. */
  indicador: string
  escala: Escala
  /** Si subir es una buena noticia: decide el tono de la variación. */
  subeEsBueno: boolean
  /** La primera es la cifra; las demás acompañan en el gráfico (dos como máximo). */
  series: [Serie] | [Serie, Serie]
  detalle: (v: ValoresIndicadores) => string
}

export const CIFRAS: Record<CodigoCifra, DefCifra> = {
  vigentes: {
    codigo: 'vigentes',
    titulo: 'Vigentes',
    indicador: 'vigentes',
    escala: 'entero',
    subeEsBueno: true,
    series: [{ nombre: 'Contratos vigentes', valor: (v) => v.vigentes }],
    detalle: () => 'contratos al cierre',
  },
  afiliaciones: {
    codigo: 'afiliaciones',
    titulo: 'Afiliaciones',
    indicador: 'afiliaciones',
    escala: 'entero',
    subeEsBueno: true,
    series: [
      { nombre: 'Afiliaciones', valor: (v) => v.afiliaciones },
      { nombre: 'Retiros', valor: (v) => v.retiros },
    ],
    detalle: (v) => (v.retiros === 1 ? '1 retiro' : `${v.retiros} retiros`),
  },
  recaudo: {
    codigo: 'recaudo',
    titulo: 'Recaudo',
    indicador: 'recaudo',
    escala: 'moneda',
    subeEsBueno: true,
    series: [
      { nombre: 'Recaudo', valor: (v) => v.recaudo },
      { nombre: 'Facturado', valor: (v) => v.facturado },
    ],
    detalle: (v) =>
      v.recaudo_del_facturado === null
        ? 'ninguna cuota vence en el período'
        : `${porcentaje(v.recaudo_del_facturado)} de lo facturado`,
  },
  mora: {
    codigo: 'mora',
    titulo: 'En mora',
    indicador: 'mora',
    escala: 'entero',
    subeEsBueno: false,
    series: [{ nombre: 'Contratos en mora', valor: (v) => v.mora?.contratos_en_mora }],
    detalle: (v) =>
      v.mora.contratos_en_mora === 0
        ? 'ningún contrato con cuotas vencidas'
        : `${porcentaje(v.mora.porcentaje)} de vigentes · ${moneda(v.mora.saldo_vencido)}`,
  },
  rutas: {
    codigo: 'rutas',
    titulo: 'Rutas',
    indicador: 'cumplimiento_rutas',
    escala: 'proporcion',
    subeEsBueno: true,
    series: [
      { nombre: 'Cumplimiento', valor: (v) => v.cumplimiento_rutas?.cumplimiento },
      { nombre: 'Puntualidad', valor: (v) => v.cumplimiento_rutas?.puntualidad },
    ],
    detalle: (v) =>
      v.cumplimiento_rutas.paradas_planeadas === 0
        ? 'ninguna parada planeada'
        : `${v.cumplimiento_rutas.paradas_completadas} de ${v.cumplimiento_rutas.paradas_planeadas} paradas · puntualidad ${porcentaje(v.cumplimiento_rutas.puntualidad)}`,
  },
  satisfaccion: {
    codigo: 'satisfaccion',
    titulo: 'Satisfacción',
    indicador: 'satisfaccion',
    escala: 'puntaje',
    subeEsBueno: true,
    series: [{ nombre: 'Puntaje promedio', valor: (v) => v.satisfaccion?.promedio }],
    detalle: (v) =>
      v.satisfaccion.enviadas === 0
        ? 'ninguna encuesta enviada'
        : `${v.satisfaccion.respondidas} de ${v.satisfaccion.enviadas} encuestas respondidas`,
  },
}

/** Cada perfil ve primero lo de su área (decidido con el usuario el 2026-11-13). */
export function ordenCifras(rol: Rol | undefined): CodigoCifra[] {
  if (rol === 'operaciones') return ['rutas', 'satisfaccion', 'mora', 'vigentes', 'afiliaciones', 'recaudo']
  return ['vigentes', 'afiliaciones', 'recaudo', 'mora', 'rutas', 'satisfaccion']
}

const ENTERO = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 })
const DECIMAL = new Intl.NumberFormat('es-CO', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
const COMPACTO = new Intl.NumberFormat('es-CO', { notation: 'compact', maximumFractionDigits: 1 })

/** La cifra tal como se lee en la franja. */
export function formatear(valor: number | null | undefined, escala: Escala): string {
  if (valor === null || valor === undefined) return '—'
  if (escala === 'moneda') return moneda(valor)
  if (escala === 'proporcion') return porcentaje(valor)
  if (escala === 'puntaje') return `${DECIMAL.format(valor)} / 5`
  return ENTERO.format(valor)
}

/** Las marcas del eje: compactas desde mil («$ 1,2 M»), porcentajes sin decimales. */
export function formatearEje(valor: number, escala: Escala): string {
  if (escala === 'moneda') return `$ ${COMPACTO.format(valor)}`
  if (escala === 'proporcion') return `${Math.round(valor * 100)}%`
  if (escala === 'puntaje') return DECIMAL.format(valor)
  return COMPACTO.format(valor)
}

export type Tono = 'buena' | 'mala' | 'neutra'

export interface Variacion {
  /** «12%», «3 más», «4 puntos», «0,2»: el tamaño del cambio; la flecha dice el sentido. */
  texto: string
  direccion: 'sube' | 'baja' | 'igual'
  tono: Tono
}

/** Cuánto cambió la cifra contra el período comparable. Sin dato en uno de los dos, null. */
export function variacion(def: DefCifra, actual: number | null | undefined, anterior: number | null | undefined): Variacion | null {
  if (actual === null || actual === undefined || anterior === null || anterior === undefined) return null
  const diferencia = actual - anterior
  let texto: string
  let cero: boolean
  if (def.escala === 'proporcion') {
    const puntos = Math.round(diferencia * 100)
    cero = puntos === 0
    texto = `${Math.abs(puntos)} ${Math.abs(puntos) === 1 ? 'punto' : 'puntos'}`
  } else if (def.escala === 'puntaje') {
    cero = Math.abs(diferencia) < 0.05
    texto = DECIMAL.format(Math.abs(diferencia))
  } else if (def.escala === 'moneda') {
    // Un recaudo se compara en proporción; si antes no hubo, la diferencia en pesos.
    const relativa = anterior === 0 ? null : Math.round((diferencia / anterior) * 100)
    cero = relativa === null ? diferencia === 0 : relativa === 0
    texto = relativa === null ? `${moneda(Math.abs(diferencia))} ${diferencia > 0 ? 'más' : 'menos'}` : `${Math.abs(relativa)}%`
  } else {
    cero = diferencia === 0
    texto = `${ENTERO.format(Math.abs(diferencia))} ${diferencia > 0 ? 'más' : 'menos'}`
  }
  if (cero) return { texto: 'sin cambio', direccion: 'igual', tono: 'neutra' }
  const sube = diferencia > 0
  return { texto, direccion: sube ? 'sube' : 'baja', tono: sube === def.subeEsBueno ? 'buena' : 'mala' }
}

/** «contra 1 oct – 13 oct»: con qué se compara, en las palabras de la franja. */
export function contraQue(evolucion: Evolucion | undefined): string | null {
  if (!evolucion) return null
  const { desde, hasta } = evolucion.anterior.periodo
  return desde === hasta ? `contra el ${fechaCorta(desde)}` : `contra ${fechaCorta(desde)} – ${fechaCorta(hasta)}`
}

/** El primer nombre de verdad: «Dra. Diana Soto» saluda a Diana, no a «Dra.». */
export function primerNombre(nombre: string | undefined): string {
  return (nombre ?? '').split(/\s+/).find((p) => p && !p.endsWith('.')) ?? ''
}

// --- Ejes de los gráficos ---------------------------------------------------------------------

const MES_CORTO = new Intl.DateTimeFormat('es-CO', { month: 'short' })
const MES_LARGO = new Intl.DateTimeFormat('es-CO', { month: 'long', year: 'numeric' })

function fechaLocal(iso: string): Date {
  const [anio, mes, dia] = iso.slice(0, 10).split('-').map(Number)
  return new Date(anio, mes - 1, dia)
}

export function mesCorto(iso: string): string {
  return MES_CORTO.format(fechaLocal(iso)).replace('.', '')
}

export function mesLargo(mes: MesEvolucion): string {
  const nombre = MES_LARGO.format(fechaLocal(mes.periodo.desde))
  return mes.parcial ? `${nombre}, hasta el ${Number(mes.periodo.hasta.slice(8, 10))}` : nombre
}

/** Un paso redondo (1, 2, 2,5 o 5 por una potencia de 10) que deja el máximo en cuatro marcas. */
function pasoRedondo(bruto: number, entero: boolean): number {
  const potencia = 10 ** Math.floor(Math.log10(bruto))
  const paso = [1, 2, 2.5, 5, 10].map((f) => f * potencia).find((p) => p >= bruto) ?? 10 * potencia
  return entero ? Math.max(1, Math.ceil(paso)) : paso
}

export function dominio(escala: Escala, valores: number[]): { min: number; max: number; marcas: number[] } {
  if (escala === 'proporcion') return { min: 0, max: 1, marcas: [0, 0.25, 0.5, 0.75, 1] }
  if (escala === 'puntaje') return { min: 1, max: 5, marcas: [1, 2, 3, 4, 5] }
  const mayor = Math.max(0, ...valores)
  const paso = pasoRedondo(mayor > 0 ? mayor / 4 : 1, escala === 'entero')
  return { min: 0, max: paso * 4, marcas: [0, 1, 2, 3, 4].map((n) => n * paso) }
}
