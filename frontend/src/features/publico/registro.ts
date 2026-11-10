import { useMutation, useQuery } from '@tanstack/react-query'

import { api } from '@/api/client'
import type {
  CotizacionRead,
  InicioRegistro,
  Periodicidad,
  PlanPublico,
  RegistroRead,
  ReintentoRegistro,
  ResultadoRegistro,
} from '@/types'

const REGISTRO = '/afiliaciones/registro'

/** Solo perros y gatos (decisión de TIMU), con sus códigos del catálogo de especies. */
export const ESPECIES_REGISTRO = [
  { codigo: 'canino', nombre: 'Perro' },
  { codigo: 'felino', nombre: 'Gato' },
] as const

export interface PeludoRegistro {
  nombre: string
  especie: string
  plan_id: string
}

export interface DatosRegistro {
  ciudad: string
  peludos: PeludoRegistro[]
  periodicidad: Periodicidad
  contacto: { nombre: string; telefono: string; email: string }
  acepta_condiciones: boolean
  acepta_tratamiento_datos: boolean
  /** Campo trampa: queda vacío para las personas. */
  sitio_web?: string
}

export interface FormularioRegistro {
  token: string
  titular: {
    titular_nombre: string
    tipo_documento: string
    documento: string
    telefono: string
    email: string
    barrio: string
    direccion: string
    complemento?: string
  }
  contactos: { nombre: string; telefono: string; relacion?: string }[]
  clave: string
  peludos: {
    posicion: number
    nombre: string
    raza?: string
    sexo?: 'macho' | 'hembra'
    fecha_nacimiento: string
    peso_kg: number
  }[]
}

/**
 * El token del registro vive en la pestaña que pagó (sessionStorage): solo sirve para
 * completar ese registro y deja de valer al completarlo. Va aquí y no en la URL de vuelta
 * de la pasarela, que quedaría en sus registros. Si no está (otra pestaña, otro equipo),
 * la familia usa el enlace que le enviamos.
 */
const CLAVE_TOKEN = 'timu-registro'

export function guardarToken(token: string): void {
  try {
    window.sessionStorage.setItem(CLAVE_TOKEN, token)
  } catch {
    // Sin almacenamiento disponible: queda el enlace por correo y WhatsApp.
  }
}

export function leerToken(): string | null {
  try {
    return window.sessionStorage.getItem(CLAVE_TOKEN)
  } catch {
    return null
  }
}

export function olvidarToken(): void {
  try {
    window.sessionStorage.removeItem(CLAVE_TOKEN)
  } catch {
    // Nada que olvidar.
  }
}

export function useCiudadesRegistro() {
  return useQuery({
    queryKey: ['registro', 'ciudades'],
    queryFn: async () => (await api.get<string[]>(`${REGISTRO}/ciudades`)).data,
  })
}

export function usePlanesRegistro(ciudad: string) {
  return useQuery({
    queryKey: ['registro', 'planes', ciudad],
    enabled: Boolean(ciudad),
    queryFn: async () => (await api.get<PlanPublico[]>(`${REGISTRO}/planes`, { params: { ciudad } })).data,
  })
}

/** El mismo cálculo que cobra el backend, con cada periodicidad. */
export function useCotizacionRegistro(ciudad: string, peludos: { especie: string; plan_id: string }[]) {
  const completa = Boolean(ciudad) && peludos.length > 0 && peludos.every((p) => p.plan_id)
  return useQuery({
    queryKey: ['registro', 'cotizacion', ciudad, peludos.map((p) => [p.especie, p.plan_id])],
    enabled: completa,
    queryFn: async () => (await api.post<CotizacionRead[]>(`${REGISTRO}/cotizacion`, { ciudad, peludos })).data,
  })
}

export function useIniciarRegistro() {
  return useMutation({
    mutationFn: async (datos: DatosRegistro) => (await api.post<InicioRegistro>(REGISTRO, datos)).data,
  })
}

/** Mientras la pasarela no responde, se vuelve a preguntar cada pocos segundos. */
export function useConsultaRegistro(token: string | null) {
  return useQuery({
    queryKey: ['registro', 'consulta', token],
    enabled: Boolean(token),
    retry: false,
    refetchInterval: (consulta) => (esperandoPago(consulta.state.data) ? 4000 : false),
    queryFn: async () => (await api.post<RegistroRead>(`${REGISTRO}/consulta`, { token })).data,
  })
}

/** El pago sigue en la pasarela: ni confirmado ni rechazado. */
export function esperandoPago(registro: RegistroRead | undefined): boolean {
  return registro?.estado === 'pendiente_pago' && (registro.estado_pago ?? 'pendiente') === 'pendiente'
}

/** Tras un rechazo, otro enlace de pago para el mismo registro: lo elegido no se pierde. */
export function useReintentarRegistro() {
  return useMutation({
    mutationFn: async (token: string) =>
      (await api.post<ReintentoRegistro>(`${REGISTRO}/reintentar`, { token })).data,
  })
}

export function useCompletarRegistro() {
  return useMutation({
    mutationFn: async (datos: FormularioRegistro) =>
      (await api.post<ResultadoRegistro>(`${REGISTRO}/completar`, datos)).data,
  })
}

/** Tras completar, la sesión ya está abierta: las fotos se suben como en el portal. */
export async function subirFotos(fotos: Map<string, File>): Promise<void> {
  if (fotos.size === 0) return
  const familia = (await api.get<{ mascotas?: { id: string; nombre: string }[] }>('/portal/mi-familia')).data
  for (const mascota of familia.mascotas ?? []) {
    const foto = fotos.get(mascota.nombre.trim().toLowerCase())
    if (!foto) continue
    const forma = new FormData()
    forma.append('foto', foto)
    await api.put(`/portal/mascotas/${mascota.id}/foto`, forma)
  }
}
