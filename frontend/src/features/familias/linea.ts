import type { EstacionRead } from '@/types'

/**
 * La línea de la familia como un plano de metro (contrato de dirección del panel,
 * .impeccable/surfaces): el año completo, sin paginar ni desplazar, con «hoy» marcado.
 * Las estaciones del mismo día comparten parada; las hechas antiguas se pliegan en un tramo;
 * lo vencido y lo próximo siempre se ve.
 */

export type EstadoParada = EstacionRead['estado']

export interface Parada {
  fecha: string
  estado: EstadoParada
  estaciones: EstacionRead[]
}

export interface Tramo {
  tipo: 'tramo'
  paradas: Parada[]
}

/** Lo vencido agrupado en vertical: sigue en rojo, dice cuántas y desde cuándo, y se despliega. */
export interface GrupoVencidas {
  tipo: 'vencidas'
  paradas: Parada[]
}

export type Elemento = Parada | Tramo | GrupoVencidas | { tipo: 'hoy' }

/** Cuando un día junta varias estaciones, la parada toma el estado más urgente. */
const URGENCIA: Record<EstadoParada, number> = { vencida: 3, proxima: 2, futura: 1, hecha: 0 }

export const esTramo = (e: Elemento): e is Tramo => 'tipo' in e && e.tipo === 'tramo'
export const esHoy = (e: Elemento): e is { tipo: 'hoy' } => 'tipo' in e && e.tipo === 'hoy'
export const esGrupoVencidas = (e: Elemento): e is GrupoVencidas => 'tipo' in e && e.tipo === 'vencidas'

/** Desde cuántas paradas vencidas se agrupan en vertical. */
export const MINIMO_GRUPO_VENCIDAS = 3

export function paradas(estaciones: EstacionRead[]): Parada[] {
  const porFecha = new Map<string, EstacionRead[]>()
  for (const e of [...estaciones].sort((a, b) => a.fecha.localeCompare(b.fecha))) {
    porFecha.set(e.fecha, [...(porFecha.get(e.fecha) ?? []), e])
  }
  return [...porFecha].map(([fecha, grupo]) => ({
    fecha,
    estaciones: grupo,
    estado: grupo.reduce<EstadoParada>((peor, e) => (URGENCIA[e.estado] > URGENCIA[peor] ? e.estado : peor), 'hecha'),
  }))
}

/**
 * Las paradas con «hoy» en su sitio. Antes de hoy, las hechas se pliegan en un tramo al
 * principio salvo la última, que da contexto; solo se pliega si son al menos dos. Lo vencido
 * nunca se esconde: con `agruparVencidas` (la línea en vertical, en el celular), tres o más
 * paradas vencidas van en un grupo que dice cuántas son, para que «hoy» y la próxima queden en
 * la primera pantalla, como en el portal.
 */
export function recorrido(
  estaciones: EstacionRead[],
  hoy: string,
  desplegado = false,
  agruparVencidas = false,
): Elemento[] {
  const todas = paradas(estaciones)
  const pasadas = todas.filter((p) => p.fecha < hoy)
  const desdeHoy = todas.filter((p) => p.fecha >= hoy)
  const hechas = pasadas.filter((p) => p.estado === 'hecha')
  const plegadas = desplegado || hechas.length < 3 ? [] : hechas.slice(0, -1)
  let visibles: (Parada | GrupoVencidas)[] = pasadas.filter((p) => !plegadas.includes(p))
  const vencidas = visibles.filter((p): p is Parada => !esGrupoVencidas(p) && p.estado === 'vencida')
  if (agruparVencidas && vencidas.length >= MINIMO_GRUPO_VENCIDAS) {
    const donde = visibles.indexOf(vencidas[0])
    const resto = visibles.filter((p) => !vencidas.includes(p as Parada))
    visibles = [...resto.slice(0, donde), { tipo: 'vencidas', paradas: vencidas }, ...resto.slice(donde)]
  }
  return [
    ...(plegadas.length > 0 ? [{ tipo: 'tramo' as const, paradas: plegadas }] : []),
    ...visibles,
    { tipo: 'hoy' as const },
    ...desdeHoy,
  ]
}

/** Ancho mínimo de una parada para que su rótulo no pise el de al lado. */
export const ANCHO_MINIMO_PARADA = 96

/** Horizontal solo si cada elemento cabe con su rótulo; si no, vertical. La decide el ancho
 * real de la línea, no el de la ventana: la misma ficha es estrecha junto al listado. */
export function orientacion(ancho: number, elementos: number): 'horizontal' | 'vertical' {
  return elementos > 0 && ancho / elementos < ANCHO_MINIMO_PARADA ? 'vertical' : 'horizontal'
}

/** Resumen de la línea para quien no la ve: lo vencido y lo próximo. */
export function resumen(estaciones: EstacionRead[], fechaCorta: (iso: string) => string): string {
  const vencidas = estaciones.filter((e) => e.estado === 'vencida').length
  const proxima = estaciones.find((e) => e.estado === 'proxima')
  const partes = [
    vencidas === 0 ? 'Nada vencido' : `${vencidas} ${vencidas === 1 ? 'vencida' : 'vencidas'}`,
    proxima ? `próxima: ${proxima.titulo} el ${fechaCorta(proxima.fecha)}` : 'nada programado',
  ]
  return partes.join(', ')
}
