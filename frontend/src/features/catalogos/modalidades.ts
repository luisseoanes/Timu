import type { FranjaRead } from '@/types'

export type Modalidad = FranjaRead['modalidad']

// Los valores son los del backend (core/enums.py, TipoServicio).
export const MODALIDADES: Modalidad[] = ['domiciliario', 'preventivo', 'clinico', 'virtual', 'aliada']

export const NOMBRE_MODALIDAD: Record<Modalidad, string> = {
  domiciliario: 'A domicilio',
  preventivo: 'Preventiva',
  clinico: 'En la clínica',
  virtual: 'Virtual',
  aliada: 'Clínica aliada',
}

/** El nombre de una modalidad que llega como texto (el catálogo de tipos no la tipa). */
export function nombreModalidad(modalidad: string): string {
  return NOMBRE_MODALIDAD[modalidad as Modalidad] ?? modalidad
}
