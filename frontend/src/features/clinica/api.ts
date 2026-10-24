import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/api/client'
import type { AdjuntoRead, FormulaRead, PlantillaConsultaRead, RespuestaRead, SolicitudVirtualRead } from '@/types'

/**
 * Entrada de historia clínica tal como la presenta el backend (clinica/service.py:
 * `presentar`). El médico y el admin la reciben completa; el resto del equipo, sólo el
 * resumen (cuándo, por qué y quién), así que los campos clínicos son opcionales.
 */
export interface EntradaHistoria {
  id: string
  mascota_id: string
  familia_id?: string
  servicio_id?: string | null
  profesional_id: string | null
  tipo: 'presencial' | 'domiciliaria' | string
  plantilla_codigo?: string | null
  fecha: string
  motivo: string
  anamnesis?: string | null
  examen_fisico?: string | null
  diagnostico?: string | null
  tratamiento?: string | null
  notas_internas?: string | null
  estado: 'borrador' | 'firmada' | 'corregida' | string
  version?: number
  reemplaza_id?: string | null
  firmada_en?: string | null
}

export const CAMPOS_CLINICOS = [
  { campo: 'motivo', label: 'Motivo de consulta' },
  { campo: 'anamnesis', label: 'Anamnesis' },
  { campo: 'examen_fisico', label: 'Examen físico' },
  { campo: 'diagnostico', label: 'Diagnóstico' },
  { campo: 'tratamiento', label: 'Tratamiento' },
  { campo: 'notas_internas', label: 'Notas internas (no las ve la familia)' },
] as const

export type CampoClinico = (typeof CAMPOS_CLINICOS)[number]['campo']
export type DatosEntrada = Partial<Record<CampoClinico, string>> & { fecha?: string }

/** Borrador de la IA para una consulta virtual (F4-IAA-03): lo revisa el médico, nunca sale solo. */
export interface BorradorIA {
  borrador: string
  senales_alarma: string[]
  recomendar_presencial: boolean
}

export interface ItemFormula {
  medicamento: string
  presentacion?: string
  dosis?: string
  frecuencia?: string
  duracion?: string
  indicaciones?: string
}

export function useHistoria(mascotaId: string, incluirCorregidas = false) {
  return useQuery({
    queryKey: ['clinica', 'historia', mascotaId, incluirCorregidas],
    queryFn: async () =>
      (
        await api.get<EntradaHistoria[]>(`/clinica/mascotas/${mascotaId}/historia`, {
          params: { incluir_corregidas: incluirCorregidas || undefined },
        })
      ).data,
  })
}

export function useEntrada(id: string) {
  return useQuery({
    queryKey: ['clinica', 'entrada', id],
    queryFn: async () => (await api.get<EntradaHistoria>(`/clinica/historias/${id}`)).data,
  })
}

export function useAdjuntos(historiaId: string) {
  return useQuery({
    queryKey: ['clinica', 'adjuntos', historiaId],
    queryFn: async () => (await api.get<AdjuntoRead[]>(`/clinica/historias/${historiaId}/adjuntos`)).data,
  })
}

export function usePlantillas() {
  return useQuery({
    queryKey: ['clinica', 'plantillas'],
    queryFn: async () => (await api.get<PlantillaConsultaRead[]>('/clinica/plantillas')).data,
  })
}

export function useRespuestas(estado?: string) {
  return useQuery({
    queryKey: ['clinica', 'respuestas', estado ?? null],
    queryFn: async () =>
      (await api.get<RespuestaRead[]>('/clinica/respuestas-virtuales', { params: { estado } })).data,
  })
}

export function useColaVirtual() {
  return useQuery({
    queryKey: ['clinica', 'cola'],
    // La cola cambia sola (llegan solicitudes, la IA deja borradores): se refresca sola.
    refetchInterval: 15000,
    queryFn: async () => (await api.get<SolicitudVirtualRead[]>('/clinica/virtual/cola')).data,
  })
}

function useMutacion<T, R>(fn: (datos: T) => Promise<R>) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: fn,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['clinica'] }),
  })
}

export function useCrearEntrada() {
  return useMutacion(
    async (datos: DatosEntrada & { mascota_id: string; tipo: string; servicio_id?: string; plantilla_codigo?: string }) =>
      (await api.post<EntradaHistoria>('/clinica/historias', datos)).data,
  )
}

export function useEditarEntrada(id: string) {
  return useMutacion(async (datos: DatosEntrada) => (await api.patch<EntradaHistoria>(`/clinica/historias/${id}`, datos)).data)
}

export function useFirmarEntrada(id: string) {
  return useMutacion(async () => (await api.post<EntradaHistoria>(`/clinica/historias/${id}/firma`)).data)
}

export function useCorregirEntrada(id: string) {
  return useMutacion(
    async (datos: DatosEntrada) => (await api.post<EntradaHistoria>(`/clinica/historias/${id}/correccion`, datos)).data,
  )
}

export function useAdjuntar(historiaId: string) {
  return useMutacion(async ({ archivo, descripcion }: { archivo: File; descripcion?: string }) => {
    const forma = new FormData()
    forma.append('archivo', archivo)
    if (descripcion) forma.append('descripcion', descripcion)
    return (await api.post<AdjuntoRead>(`/clinica/historias/${historiaId}/adjuntos`, forma)).data
  })
}

export async function urlAdjunto(id: string): Promise<string> {
  return (await api.get<{ url: string }>(`/clinica/adjuntos/${id}/url`)).data.url
}

export function useEmitirFormula(historiaId: string) {
  return useMutacion(
    async (datos: { items: ItemFormula[]; indicaciones?: string }) =>
      (await api.post<FormulaRead>(`/clinica/historias/${historiaId}/formulas`, datos)).data,
  )
}

export function useCrearSolicitudVirtual() {
  return useMutacion(
    async (datos: { mascota_id: string; motivo: string; prioridad: string; canal: 'panel' }) =>
      (await api.post<SolicitudVirtualRead>('/clinica/virtual', datos)).data,
  )
}

export function useTomarSolicitud() {
  return useMutacion(async (id: string) => (await api.post<SolicitudVirtualRead>(`/clinica/virtual/${id}/toma`)).data)
}

export function usePedirBorrador() {
  return useMutacion(async (id: string) => (await api.post(`/clinica/virtual/${id}/borrador`)).data)
}

export function useResponderSolicitud() {
  return useMutacion(
    async ({ id, ...datos }: { id: string; respuesta_codigo: string; variables: string[]; diagnostico?: string; notas_internas?: string }) =>
      (await api.post<SolicitudVirtualRead>(`/clinica/virtual/${id}/respuesta`, datos)).data,
  )
}

export function useCerrarSolicitud() {
  return useMutacion(async (id: string) => (await api.post<SolicitudVirtualRead>(`/clinica/virtual/${id}/cierre`)).data)
}

export function useCrearRespuesta() {
  return useMutacion(
    async (datos: { codigo: string; titulo: string; cuerpo: string; variables: string[] }) =>
      (await api.post<RespuestaRead>('/clinica/respuestas-virtuales', datos)).data,
  )
}

export function useAprobarRespuesta() {
  return useMutacion(
    async (codigo: string) => (await api.post<RespuestaRead>(`/clinica/respuestas-virtuales/${codigo}/aprobacion`)).data,
  )
}

export function useCrearPlantilla() {
  return useMutacion(
    async (datos: { codigo: string; nombre: string; tipo_servicio_codigo?: string; campos: Record<string, string> }) =>
      (await api.post<PlantillaConsultaRead>('/clinica/plantillas', datos)).data,
  )
}
