import { hora } from '@/lib/formato'
import type { FamiliaDeParada, ParadaRead, RutaRead } from '@/types'

/** Lo que distingue la línea: la parada que toca, las que ya se hicieron y las que faltan. */
export type EstadoEstacion = 'hecha' | 'actual' | 'pendiente'

const KM = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 1 })

/** La parada que toca: la que está en curso o, si ninguna lo está, la primera pendiente. Una
 * ruta cerrada (finalizada o cancelada) no tiene. */
export function paradaActual(ruta: RutaRead): ParadaRead | undefined {
  if (ruta.estado !== 'planificada' && ruta.estado !== 'en_curso') return undefined
  return (
    ruta.paradas.find((p) => p.estado === 'en_camino' || p.estado === 'en_sitio') ??
    ruta.paradas.find((p) => p.estado === 'pendiente')
  )
}

/** Las paradas que siguen en la ruta, en su orden: una omitida ya no es de la ruta. */
export function enRuta(ruta: RutaRead): ParadaRead[] {
  return ruta.paradas.filter((p) => p.estado !== 'omitida')
}

export function avance(rutas: RutaRead[]): { hechas: number; total: number } {
  const paradas = rutas.flatMap(enRuta)
  return { hechas: paradas.filter((p) => p.estado === 'completada').length, total: paradas.length }
}

/** «2 de 6 paradas · 18,4 km»: cuánto lleva y cuánto recorre. */
export function resumen(rutas: RutaRead[]): string {
  const { hechas, total } = avance(rutas)
  const km = rutas.reduce((suma, r) => suma + (r.distancia_km ?? 0), 0)
  const partes = [`${hechas} de ${total} ${total === 1 ? 'parada' : 'paradas'}`]
  if (km > 0) partes.push(`${KM.format(km)} km`)
  return partes.join(' · ')
}

/** «4 h 10 min» */
export function duracion(minutos: number | null): string | null {
  if (minutos === null) return null
  const [h, m] = [Math.floor(minutos / 60), Math.round(minutos % 60)]
  if (h === 0) return `${m} min`
  return m === 0 ? `${h} h` : `${h} h ${m} min`
}

/** La miniatura de la ruta dicha con palabras, para quien no la ve. */
export function descripcion(ruta: RutaRead): string {
  const { hechas, total } = avance([ruta])
  const actual = paradaActual(ruta)
  const base = `${hechas} de ${total} ${total === 1 ? 'parada hecha' : 'paradas hechas'}`
  if (!actual) return base
  const cuando = actual.llegada_estimada ? `, llegada estimada a las ${hora(actual.llegada_estimada)}` : ''
  return `${base}. Sigue ${actual.familia.titular_nombre}${cuando}`
}

export function estadoEstacion(parada: ParadaRead, actual: ParadaRead | undefined): EstadoEstacion {
  if (parada.estado === 'completada') return 'hecha'
  return parada.id === actual?.id ? 'actual' : 'pendiente'
}

/** A quién se atiende: «Jorge Ramírez · Max». */
export function aQuien(parada: ParadaRead): string {
  return parada.mascota ? `${parada.familia.titular_nombre} · ${parada.mascota.nombre}` : parada.familia.titular_nombre
}

/** Dónde queda, en una línea: «Cl 10 #32-115, El Poblado». Lo que la familia no tiene
 * registrado no se escribe; sin nada, se dice. */
export function donde(familia: FamiliaDeParada): string {
  return [familia.direccion, familia.barrio].filter(Boolean).join(', ') || 'Sin dirección registrada'
}

/** El número de casa de una dirección colombiana («# 100-12», «# 7 sur-170»): se lee como una
 * unidad, así que no se debe partir entre dos líneas. Devuelve lo de antes, el número y lo de
 * después; sin número, todo va en lo de antes. */
export function partirDireccion(texto: string): [string, string, string] {
  const numero = /#\s*[^\s,]+(?:\s+(?:sur|norte|este|oeste)[^\s,]*)?/i.exec(texto)
  if (!numero) return [texto, '', '']
  return [texto.slice(0, numero.index), numero[0], texto.slice(numero.index + numero[0].length)]
}

/** La navegación del celular hacia la parada: sus coordenadas, que son las que usó el
 * optimizador, o la dirección escrita si la parada no las tiene. */
export function comoLlegar(parada: ParadaRead, ciudad: string): string {
  const destino =
    parada.latitud !== null && parada.longitud !== null
      ? `${parada.latitud},${parada.longitud}`
      : [parada.familia.direccion, parada.familia.barrio, ciudad].filter(Boolean).join(', ')
  return `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(destino)}`
}

/** Los teléfonos se guardan en E.164 con «+»; WhatsApp los quiere sin él. */
export function enlaceWhatsApp(telefono: string): string {
  return `https://wa.me/${telefono.replace(/\D/g, '')}`
}
