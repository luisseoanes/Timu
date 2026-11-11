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
