/**
 * Formatos de presentación en español de Colombia. Todas las horas se muestran en la
 * zona de la operación (America/Bogota), sin importar dónde esté el navegador.
 */

const ZONA = 'America/Bogota'

const MONEDA = new Intl.NumberFormat('es-CO', {
  style: 'currency',
  currency: 'COP',
  maximumFractionDigits: 0,
})

/** `45000` o `"45000.00"` → `$ 45.000` */
export function moneda(valor: number | string | null | undefined): string {
  if (valor === null || valor === undefined || valor === '') return '—'
  return MONEDA.format(Number(valor))
}

/** Fecha de calendario (`2026-10-24`) sin desplazarla por zona horaria. */
export function fecha(valor: string | null | undefined): string {
  if (!valor) return '—'
  const [anio, mes, dia] = valor.slice(0, 10).split('-')
  return `${dia}/${mes}/${anio}`
}

const FECHA_CORTA = new Intl.DateTimeFormat('es-CO', { day: 'numeric', month: 'short' })

/** «18 nov»: día y mes de una fecha ISO, sin pasar por la zona horaria del navegador. */
export function fechaCorta(valor: string): string {
  const [anio, mes, dia] = valor.slice(0, 10).split('-').map(Number)
  const partes = FECHA_CORTA.formatToParts(new Date(anio, mes - 1, dia))
  const parte = (tipo: string) => partes.find((p) => p.type === tipo)?.value.replace('.', '') ?? ''
  return `${parte('day')} ${parte('month')}`
}

const FECHA_HORA = new Intl.DateTimeFormat('es-CO', {
  timeZone: ZONA,
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
  hour: 'numeric',
  minute: '2-digit',
})

const HORA = new Intl.DateTimeFormat('es-CO', { timeZone: ZONA, hour: 'numeric', minute: '2-digit' })

/** Instante (`2026-10-24T14:30:00Z`) en hora de Colombia. */
export function fechaHora(valor: string | null | undefined): string {
  return valor ? FECHA_HORA.format(new Date(valor)) : '—'
}

export function hora(valor: string | null | undefined): string {
  return valor ? HORA.format(new Date(valor)) : '—'
}

function partesDeHora(valor: string) {
  const partes = HORA.formatToParts(new Date(valor))
  const parte = (tipo: string) => partes.find((p) => p.type === tipo)?.value ?? ''
  return { reloj: `${parte('hour')}:${parte('minute')}`, periodo: parte('dayPeriod') }
}

/** Una franja en hora de Colombia: «10:00 – 11:00 a. m.», o con los dos periodos si cruza el
 * mediodía («11:30 a. m. – 12:30 p. m.»). Sin las dos horas no hay franja. */
export function rangoHoras(desde: string | null | undefined, hasta: string | null | undefined): string | null {
  if (!desde || !hasta) return null
  const [inicio, fin] = [partesDeHora(desde), partesDeHora(hasta)]
  return inicio.periodo === fin.periodo
    ? `${inicio.reloj} – ${fin.reloj} ${fin.periodo}`
    : `${inicio.reloj} ${inicio.periodo} – ${fin.reloj} ${fin.periodo}`
}

const FECHA_LARGA = new Intl.DateTimeFormat('es-CO', { weekday: 'long', day: 'numeric', month: 'long' })

/** «jueves, 12 de noviembre»: una fecha de calendario con su día de la semana. */
export function fechaLarga(valor: string): string {
  const [anio, mes, dia] = valor.slice(0, 10).split('-').map(Number)
  return FECHA_LARGA.format(new Date(anio, mes - 1, dia))
}

const DIA_SEMANA = new Intl.DateTimeFormat('es-CO', { weekday: 'short' })

/** «sáb 14 nov»: una fecha de calendario corta, con su día de la semana. */
export function fechaCortaConDia(valor: string): string {
  const [anio, mes, dia] = valor.slice(0, 10).split('-').map(Number)
  return `${DIA_SEMANA.format(new Date(anio, mes - 1, dia)).replace('.', '')} ${fechaCorta(valor)}`
}

/** Edad a partir de la fecha de nacimiento: en meses hasta el año, después en años. */
export function edad(nacimiento: string | null | undefined, hoy = new Date()): string | null {
  if (!nacimiento) return null
  const [a, m, d] = nacimiento.slice(0, 10).split('-').map(Number)
  let meses = (hoy.getFullYear() - a) * 12 + (hoy.getMonth() + 1 - m) - (hoy.getDate() < d ? 1 : 0)
  if (meses < 0) meses = 0
  if (meses < 12) return `${meses} ${meses === 1 ? 'mes' : 'meses'}`
  const anios = Math.floor(meses / 12)
  return `${anios} ${anios === 1 ? 'año' : 'años'}`
}

/** Hoy en Colombia como `YYYY-MM-DD`, para filtros y valores por defecto. */
export function hoyISO(): string {
  return new Intl.DateTimeFormat('en-CA', { timeZone: ZONA }).format(new Date())
}

/** Peso de una mascota como en Colombia: «8,4 kg», sin decimales si no los tiene. */
export function peso(kg: number | null | undefined): string {
  if (kg === null || kg === undefined) return '—'
  return `${new Intl.NumberFormat('es-CO', { maximumFractionDigits: 1 }).format(kg)} kg`
}

export function porcentaje(valor: number | null | undefined): string {
  return valor === null || valor === undefined ? '—' : `${Math.round(valor * 100)}%`
}

/** Primer y último día del mes en curso en Colombia, como `YYYY-MM-DD`. */
export function mesEnCurso(): { desde: string; hasta: string } {
  const [anio, mes] = hoyISO().split('-')
  const ultimo = new Date(Number(anio), Number(mes), 0).getDate()
  return { desde: `${anio}-${mes}-01`, hasta: `${anio}-${mes}-${String(ultimo).padStart(2, '0')}` }
}
