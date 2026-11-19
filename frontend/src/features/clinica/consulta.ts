import type { EntradaHistoria } from './api'

/** Los apartados de la consulta, en el orden en que se recorre: las estaciones de la guía. */
export const ESTACIONES = [
  {
    campo: 'motivo',
    titulo: 'Motivo de consulta',
    // Dentro de una frase: «Prellena el motivo de consulta y el tratamiento».
    enFrase: 'el motivo de consulta',
    corto: 'Motivo',
    ayuda: () => 'Por qué consulta la familia, con sus palabras.',
  },
  {
    campo: 'anamnesis',
    titulo: 'Anamnesis',
    enFrase: 'la anamnesis',
    corto: 'Anamnesis',
    ayuda: () => 'Lo que cuenta la familia: desde cuándo, qué ha comido, qué ha cambiado.',
  },
  {
    campo: 'examen_fisico',
    titulo: 'Examen físico',
    enFrase: 'el examen físico',
    corto: 'Examen',
    ayuda: (mascota: string) => `Lo que encuentras al examinar a ${mascota}.`,
  },
  {
    campo: 'diagnostico',
    titulo: 'Diagnóstico',
    enFrase: 'el diagnóstico',
    corto: 'Diagnóstico',
    ayuda: () => 'El diagnóstico o la sospecha, y lo que falta por descartar.',
  },
  {
    campo: 'tratamiento',
    titulo: 'Tratamiento',
    enFrase: 'el tratamiento',
    // «Plan», como en las notas clínicas: «Tratamiento» no cabe junto a «Diagnóstico» a 390 px.
    corto: 'Plan',
    ayuda: () => 'Lo que se le indica a la familia: medicamentos, dieta, controles.',
  },
] as const

export type CampoGuiado = (typeof ESTACIONES)[number]['campo']

/** Qué apartados prellena una plantilla y cuáles deja en blanco, en el orden de la consulta. */
export function apartadosDePlantilla(campos: Record<string, string>) {
  const llena = ESTACIONES.filter((e) => campos[e.campo]?.trim())
  return { llena, falta: ESTACIONES.filter((e) => !llena.includes(e)) }
}

const LISTA = new Intl.ListFormat('es', { type: 'conjunction' })

/** «motivo, diagnóstico y tratamiento». */
export function enPalabras(partes: readonly string[]): string {
  return LISTA.format(partes)
}
/** Lo escrito en cada apartado, más las notas internas, que van con el tratamiento. */
export type Valores = Record<CampoGuiado | 'notas_internas', string>

export const VACIOS: Valores = {
  motivo: '',
  anamnesis: '',
  examen_fisico: '',
  diagnostico: '',
  tratamiento: '',
  notas_internas: '',
}

export function valoresDe(entrada: EntradaHistoria | undefined): Valores {
  if (!entrada) return { ...VACIOS }
  return Object.fromEntries(
    Object.keys(VACIOS).map((campo) => [campo, (entrada[campo as keyof EntradaHistoria] as string | null | undefined) ?? '']),
  ) as Valores
}

/** Los campos que cambiaron desde lo último guardado, ya sin espacios sobrantes. */
export function cambios(valores: Valores, guardados: Valores): Partial<Valores> {
  const distintos: Partial<Valores> = {}
  for (const campo of Object.keys(VACIOS) as (keyof Valores)[]) {
    if (valores[campo].trim() !== guardados[campo].trim()) distintos[campo] = valores[campo].trim()
  }
  return distintos
}

/**
 * Lo que falta para firmar, en el orden de la guía. El motivo y el diagnóstico los pide la
 * historia clínica; el tratamiento, la visita: sin él, el servicio no se puede cerrar.
 */
export function faltanParaFirmar(valores: Valores, conVisita: boolean): CampoGuiado[] {
  const exigidos: CampoGuiado[] = ['motivo', 'diagnostico', ...(conVisita ? (['tratamiento'] as const) : [])]
  return ESTACIONES.map((e) => e.campo).filter((c) => exigidos.includes(c) && !valores[c].trim())
}

/** El apartado que sigue, en el texto del botón: «examen físico». */
export function siguienteDe(actual: number): string {
  return ESTACIONES[actual + 1].titulo.toLowerCase()
}

export function tituloDe(campo: CampoGuiado): string {
  return ESTACIONES.find((e) => e.campo === campo)!.titulo
}

/** Dónde se abre una consulta: en el primer apartado vacío, o en el último si ya está todo. */
export function estacionInicial(valores: Valores): number {
  const vacia = ESTACIONES.findIndex((e) => !valores[e.campo].trim())
  return vacia === -1 ? ESTACIONES.length - 1 : vacia
}

/** La consulta firmada más reciente que no es esta: la referencia de lo que se anotó la última vez. */
export function anteriorFirmada(historia: EntradaHistoria[], excluir?: string): EntradaHistoria | undefined {
  return historia
    .filter((e) => e.estado === 'firmada' && e.id !== excluir)
    .sort((a, b) => b.fecha.localeCompare(a.fecha))[0]
}
