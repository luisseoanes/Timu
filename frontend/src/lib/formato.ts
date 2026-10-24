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

export function porcentaje(valor: number | null | undefined): string {
  return valor === null || valor === undefined ? '—' : `${Math.round(valor * 100)}%`
}
