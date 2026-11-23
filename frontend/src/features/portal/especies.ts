import type { EspecieRead } from '@/types'

/** Solo perros y gatos (decisión de TIMU), como en el registro en línea. */
export const ESPECIES_DE_LA_FAMILIA = [
  { codigo: 'canino', nombre: 'Perro' },
  { codigo: 'felino', nombre: 'Gato' },
] as const

/**
 * La especie dicha a la familia (DEU-80): el catálogo la nombra para el equipo («Canino»), y el alta
 * de un peludo y el registro en línea la dicen como la familia («Perro»). Una especie que no sea
 * perro ni gato, con el nombre del catálogo.
 */
export function nombreEspecie(codigo: string, catalogo: Pick<EspecieRead, 'codigo' | 'nombre'>[] | undefined): string {
  return (
    ESPECIES_DE_LA_FAMILIA.find((e) => e.codigo === codigo)?.nombre ??
    catalogo?.find((e) => e.codigo === codigo)?.nombre ??
    codigo
  )
}
