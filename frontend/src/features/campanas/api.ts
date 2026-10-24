import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/api/client'
import type {
  BajaRead,
  CampanaRead,
  ConfiguracionRead,
  EjecucionRead,
  EncuestaRead,
  EstadoAfiliacion,
  MensajeRead,
  Page,
  PlantillaWhatsAppRead,
  SegmentoRead,
} from '@/types'

/** Filtros de un segmento (campanas/segmentos.py: FiltrosSegmento). Vacío = sin filtro. */
export interface FiltrosSegmento {
  ciudades?: string[]
  estados?: EstadoAfiliacion[]
  planes?: string[]
  especies?: string[]
  origenes?: string[]
  dias_mora_min?: number
  sin_servicio_dias?: number
  mascotas_min?: number
  afiliada_desde?: string
  afiliada_hasta?: string
  renovacion_en_dias?: number
}

export interface Previsualizacion {
  total: number
  muestra: { id: string; titular: string; ciudad: string; estado: string }[]
}

export interface PrevisualizacionCampana {
  audiencia: number
  excluidos_por_baja: number
  se_enviaran: number
  ejemplos: { titular: string; mensaje: string }[]
}

export interface ResultadosCampana {
  audiencia: number
  excluidos: number
  encolados: number
  enviados: number
  entregados: number
  leidos: number
  respondidos: number
  fallidos: number
}

export interface ResumenEncuestas {
  enviadas: number
  respondidas: number
  tasa_respuesta: number | null
  promedio: number | null
  por_responsable: { responsable: string; respuestas: number; promedio: number }[]
  por_tipo_servicio: { tipo_servicio: string; respuestas: number; promedio: number }[]
}

export function useCampanas() {
  return useQuery({
    queryKey: ['campanas'],
    queryFn: async () => (await api.get<CampanaRead[]>('/campanas')).data,
  })
}

export function useEjecuciones(id: string | null) {
  return useQuery({
    queryKey: ['campanas', id, 'ejecuciones'],
    enabled: Boolean(id),
    queryFn: async () => (await api.get<EjecucionRead[]>(`/campanas/${id}/ejecuciones`)).data,
  })
}

export function useResultados(id: string | null) {
  return useQuery({
    queryKey: ['campanas', id, 'resultados'],
    enabled: Boolean(id),
    queryFn: async () => (await api.get<ResultadosCampana>(`/campanas/${id}/resultados`)).data,
  })
}

export function usePrevisualizacionCampana(id: string | null) {
  return useQuery({
    queryKey: ['campanas', id, 'previsualizacion'],
    enabled: Boolean(id),
    queryFn: async () => (await api.get<PrevisualizacionCampana>(`/campanas/${id}/previsualizacion`)).data,
  })
}

export function useSegmentos() {
  return useQuery({
    queryKey: ['segmentos'],
    queryFn: async () => (await api.get<SegmentoRead[]>('/segmentos')).data,
  })
}

export function usePrevisualizarSegmento() {
  return useMutation({
    mutationFn: async (filtros: FiltrosSegmento) =>
      (await api.post<Previsualizacion>('/segmentos/previsualizacion', filtros)).data,
  })
}

export function usePlantillasWhatsApp() {
  return useQuery({
    queryKey: ['comunicaciones', 'plantillas'],
    queryFn: async () => (await api.get<PlantillaWhatsAppRead[]>('/comunicaciones/plantillas')).data,
  })
}

export function useMensajes(filtros: { estado?: string; limit?: number; offset?: number }) {
  return useQuery({
    queryKey: ['comunicaciones', 'mensajes', filtros],
    queryFn: async () =>
      (await api.get<Page<MensajeRead>>('/comunicaciones/mensajes', { params: { ...filtros, orden: '-created_at' } })).data,
  })
}

export function useBajas() {
  return useQuery({
    queryKey: ['comunicaciones', 'bajas'],
    queryFn: async () => (await api.get<BajaRead[]>('/comunicaciones/bajas')).data,
  })
}

export function useEncuestas(filtros: { estado?: string; puntaje_max?: number; limit?: number; offset?: number }) {
  return useQuery({
    queryKey: ['encuestas', filtros],
    queryFn: async () =>
      (await api.get<Page<EncuestaRead>>('/encuestas', { params: { ...filtros, orden: '-programada_para' } })).data,
  })
}

export function useResumenEncuestas(desde: string, hasta: string) {
  return useQuery({
    queryKey: ['encuestas', 'resumen', desde, hasta],
    queryFn: async () => (await api.get<ResumenEncuestas>('/encuestas/resumen', { params: { desde, hasta } })).data,
  })
}

export function useConfiguracionEncuestas(habilitado: boolean) {
  return useQuery({
    queryKey: ['encuestas', 'configuracion'],
    enabled: habilitado,
    queryFn: async () => (await api.get<ConfiguracionRead[]>('/encuestas/configuracion')).data,
  })
}

function useMutacion<T, R>(fn: (datos: T) => Promise<R>, claves: string[][]) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: fn,
    onSuccess: () => claves.forEach((queryKey) => void qc.invalidateQueries({ queryKey })),
  })
}

export function useCrearCampana() {
  return useMutacion(
    async (datos: { nombre: string; plantilla: string; variables: string[]; segmento_id?: string; segmento?: FiltrosSegmento }) =>
      (await api.post<CampanaRead>('/campanas', datos)).data,
    [['campanas']],
  )
}

export function useProgramarCampana() {
  return useMutacion(
    async ({ id, ...datos }: { id: string; cuando?: string; recurrencia: string }) =>
      (await api.post<CampanaRead>(`/campanas/${id}/programacion`, datos)).data,
    [['campanas']],
  )
}

export function useCancelarCampana() {
  return useMutacion(async (id: string) => (await api.post<CampanaRead>(`/campanas/${id}/cancelacion`)).data, [['campanas']])
}

export function useCrearSegmento() {
  return useMutacion(
    async (datos: { nombre: string; descripcion?: string; filtros: FiltrosSegmento }) =>
      (await api.post<SegmentoRead>('/segmentos', datos)).data,
    [['segmentos']],
  )
}

export function useCrearPlantillaWhatsApp() {
  return useMutacion(
    async (datos: { nombre: string; categoria: string; cuerpo: string; variables: string[] }) =>
      (await api.post<PlantillaWhatsAppRead>('/comunicaciones/plantillas', datos)).data,
    [['comunicaciones', 'plantillas']],
  )
}

export function useEstadoPlantilla() {
  return useMutacion(
    async ({ id, ...datos }: { id: string; estado_aprobacion: string; activa?: boolean }) =>
      (await api.patch<PlantillaWhatsAppRead>(`/comunicaciones/plantillas/${id}/estado`, datos)).data,
    [['comunicaciones', 'plantillas']],
  )
}

export function useCrearBaja() {
  return useMutacion(
    async (datos: { telefono?: string; email?: string; motivo?: string }) =>
      (await api.post<BajaRead>('/comunicaciones/bajas', datos)).data,
    [['comunicaciones', 'bajas']],
  )
}

export function useQuitarBaja() {
  return useMutacion(
    async (destino: string) => (await api.delete(`/comunicaciones/bajas/${encodeURIComponent(destino)}`)).data,
    [['comunicaciones', 'bajas']],
  )
}

export function useGuardarConfiguracion() {
  return useMutacion(
    async (datos: Omit<ConfiguracionRead, 'id'>) => (await api.put<ConfiguracionRead>('/encuestas/configuracion', datos)).data,
    [['encuestas', 'configuracion']],
  )
}
