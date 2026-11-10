/** Lo que comparten los formularios de una mascota en el panel. */

export const AYUDA_FECHA =
  'Si no sabes la fecha exacta, pon una aproximada: el día 1 del mes y el año en que crees que nació.'

/** Lee del formulario los campos de `CamposMascota`, con el prefijo que se les dio. */
export function leerCamposMascota(d: FormData, prefijo = '') {
  const esterilizada = String(d.get(`${prefijo}esterilizada`) ?? '')
  return {
    fecha_nacimiento: String(d.get(`${prefijo}fecha_nacimiento`) ?? ''),
    peso_kg: Number(d.get(`${prefijo}peso_kg`)),
    esterilizada: esterilizada === '' ? undefined : esterilizada === 'si',
  }
}

/** Los planes activos que se venden en la ciudad y cubren la especie (sin especies = todas). */
export function planesPara<P extends { activo: boolean; ciudades: string[]; especies: string[] }>(
  planes: P[] | undefined,
  ciudad: string,
  especie: string,
): P[] {
  return (planes ?? []).filter(
    (p) => p.activo && p.ciudades.includes(ciudad) && (p.especies.length === 0 || p.especies.includes(especie)),
  )
}
