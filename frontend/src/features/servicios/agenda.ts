import { diaISO, fechaCortaConDia, hoyISO } from '@/lib/formato'
import type { ServicioListado } from '@/types'

function sumarDias(iso: string, dias: number): string {
  const d = new Date(`${iso}T12:00:00Z`)
  d.setUTCDate(d.getUTCDate() + dias)
  return d.toISOString().slice(0, 10)
}

/** El día anterior a hoy en Colombia: el tope de «Atrasados». */
export function ayer(hoy = hoyISO()): string {
  return sumarDias(hoy, -1)
}

/** «Hoy · vie 13 nov», «Mañana · sáb 14 nov» o «lun 16 nov»: el día de un grupo del listado. */
export function rotuloDia(dia: string, hoy = hoyISO()): string {
  if (dia === hoy) return `Hoy · ${fechaCortaConDia(dia)}`
  if (dia === sumarDias(hoy, 1)) return `Mañana · ${fechaCortaConDia(dia)}`
  return fechaCortaConDia(dia)
}

/** Los servicios agrupados por día, en el orden en que llegan; los que no tienen hora, al final. */
export function porDia(items: ServicioListado[]): { dia: string | null; servicios: ServicioListado[] }[] {
  const grupos: { dia: string | null; servicios: ServicioListado[] }[] = []
  for (const s of items) {
    const dia = s.programado_para ? diaISO(s.programado_para) : null
    const ultimo = grupos.at(-1)
    if (ultimo && ultimo.dia === dia) ultimo.servicios.push(s)
    else grupos.push({ dia, servicios: [s] })
  }
  return grupos
}
