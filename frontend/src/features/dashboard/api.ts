import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/api/client'
import type {
  ContratoListado,
  ConversacionRead,
  DatosTimuRead,
  EventoRead,
  Page,
  PlantillaFaltante,
  RecuentosUsuarios,
  ReporteRead,
  ServicioListado,
  TareaRead,
} from '@/types'

/** Respuesta de `GET /dashboard/indicadores` (definiciones en docs/indicadores.md). */
export interface Indicadores {
  periodo: { desde: string; hasta: string; ciudad: string | null }
  indicadores: {
    afiliaciones: number
    retiros: number
    vigentes: number
    recaudo: number
    facturado: number
    recaudo_del_facturado: number | null
    mora: { contratos_en_mora: number; saldo_vencido: number; porcentaje: number | null }
    cumplimiento_rutas: {
      paradas_planeadas: number
      paradas_completadas: number
      cumplimiento: number | null
      puntualidad: number | null
    }
    servicios_por_tipo: Record<string, number>
    satisfaccion: { enviadas: number; respondidas: number; promedio: number | null; tasa_respuesta: number | null }
  }
}

export type ValoresIndicadores = Indicadores['indicadores']

/** Un mes de la serie: los mismos indicadores; `parcial` si el mes aún no termina. */
export interface MesEvolucion {
  periodo: Indicadores['periodo']
  indicadores: Partial<ValoresIndicadores>
  parcial: boolean
}

/** Respuesta de `GET /dashboard/evolucion`: 12 meses y el período con que se compara. */
export interface Evolucion {
  anterior: { periodo: Indicadores['periodo']; indicadores: Partial<ValoresIndicadores> }
  meses: MesEvolucion[]
}

export interface Definicion {
  codigo: string
  nombre: string
  formula: string
  unidad: string
}

export interface FiltrosIndicadores {
  desde: string
  hasta: string
  ciudad?: string
}

export function useIndicadores(filtros: FiltrosIndicadores) {
  return useQuery({
    queryKey: ['dashboard', 'indicadores', filtros],
    // Al cambiar el período, las cifras de antes siguen a la vista mientras llegan las nuevas.
    placeholderData: keepPreviousData,
    queryFn: async () => (await api.get<Indicadores>('/dashboard/indicadores', { params: filtros })).data,
  })
}

/** `codigos`: lo que dibujan las series de las cifras a la vista (`codigosDe`); la API rechaza los
 * que no son del perfil. */
export function useEvolucion(filtros: FiltrosIndicadores, codigos: string[]) {
  return useQuery({
    queryKey: ['dashboard', 'evolucion', filtros, codigos],
    placeholderData: keepPreviousData,
    queryFn: async () =>
      (
        await api.get<Evolucion>('/dashboard/evolucion', {
          params: { ...filtros, codigos },
          paramsSerializer: { indexes: null },
        })
      ).data,
  })
}

/** Con `activa` en false no se piden: el Inicio solo las enseña al abrir una serie. */
export function useDefiniciones(activa = true) {
  return useQuery({
    queryKey: ['dashboard', 'definiciones'],
    enabled: activa,
    staleTime: Infinity,
    queryFn: async () => (await api.get<Definicion[]>('/dashboard/definiciones')).data,
  })
}

/** Servicios agendados de hoy en adelante: lo que viene en la línea del equipo. Veinte bastan
 * para hoy y para agrupar los días siguientes; el total dice cuántos quedan fuera. */
export function useProximosServicios(desde: string, habilitado = true) {
  return useQuery({
    queryKey: ['servicios', { desde, proximos: true }],
    enabled: habilitado,
    queryFn: async () =>
      (
        await api.get<Page<ServicioListado>>('/servicios', {
          params: { desde, estado: 'agendado', limit: 20, orden: 'programado_para' },
        })
      ).data,
  })
}

/** Cuántos hay y el primero de la fila: para contar un grupo de vencidos con su ejemplo. */
export interface Grupo<T> {
  total: number
  primero: T | undefined
}

async function grupo<T>(ruta: string, params: Record<string, unknown>): Promise<Grupo<T>> {
  const { items, total } = (await api.get<Page<T>>(ruta, { params: { ...params, limit: 1 } })).data
  return { total, primero: items[0] }
}

const NADA: Grupo<never> = { total: 0, primero: undefined }

/** Qué grupos de lo vencido pide cada perfil (Sección 12): solo los que puede leer. */
export interface GruposVencidos {
  mora: boolean
  preventivos: boolean
  tareas: boolean
}

/** Lo vencido de cada perfil. Cartera lista primero el contrato más atrasado; preventivos y
 * tareas, el más antiguo (las tareas ya llegan solo de su área). */
export function useVencidos(grupos: GruposVencidos = { mora: true, preventivos: true, tareas: true }) {
  return useQuery({
    queryKey: ['dashboard', 'vencidos', grupos],
    queryFn: async () => {
      const [mora, preventivos, tareas] = await Promise.all([
        grupos.mora ? grupo<ContratoListado>('/cartera/contratos', { solo_mora: true }) : NADA,
        grupos.preventivos ? grupo<EventoRead>('/preventivos', { pendientes_autorizacion: true }) : NADA,
        grupos.tareas ? grupo<TareaRead>('/tareas', { vencidas: true, orden: 'vence_el' }) : NADA,
      ])
      return { mora, preventivos, tareas }
    },
  })
}

/** Lo de Comercial para hoy: las conversaciones que esperan a un asesor y los contratos por
 * renovar (6.4, 6.11). */
export function useComercialHoy(habilitado: boolean) {
  return useQuery({
    queryKey: ['dashboard', 'comercial'],
    enabled: habilitado,
    queryFn: async () => {
      const [conversaciones, renovaciones] = await Promise.all([
        api.get<ConversacionRead[]>('/comercial/conversaciones', { params: { estado: 'con_asesor' } }).then((r) => r.data),
        grupo<ContratoListado>('/cartera/contratos', { por_renovar: true, orden: 'fecha_renovacion' }),
      ])
      return { conversaciones, renovaciones }
    },
  })
}

/** Lo que falta configurar (el Inicio del administrador): las plantillas que citan las reglas y no
 * están aprobadas, los Datos de TIMU y los usuarios inactivos. Mismas claves que Administración. */
export function useLoQueFalta() {
  return useQuery({
    queryKey: ['dashboard', 'configuracion'],
    queryFn: async () => {
      const [plantillas, datos, usuarios] = await Promise.all([
        api.get<PlantillaFaltante[]>('/reglas/plantillas-faltantes').then((r) => r.data),
        api.get<DatosTimuRead>('/institucional').then((r) => r.data),
        api.get<RecuentosUsuarios>('/auth/usuarios/recuentos').then((r) => r.data),
      ])
      return { plantillas, datos, usuarios }
    },
  })
}

/** Consulta sin firmar del médico: solo lo que la línea cuenta de ella. */
export interface Borrador {
  id: string
  fecha: string
}

/** Lo pendiente del médico: sus consultas sin firmar y sus tareas vencidas y abiertas. */
export function useMisPendientes() {
  return useQuery({
    queryKey: ['dashboard', 'mis-pendientes'],
    queryFn: async () => {
      const [borradores, vencidas, abiertas] = await Promise.all([
        api.get<Borrador[]>('/clinica/borradores').then((r) => r.data),
        grupo<TareaRead>('/tareas', { mias: true, vencidas: true, orden: 'vence_el' }),
        api
          .get<Page<TareaRead>>('/tareas', { params: { mias: true, estado: 'abierta', limit: 5, orden: 'vence_el' } })
          .then((r) => r.data),
      ])
      return { borradores, vencidas, abiertas }
    },
  })
}

// --- Reportes programados (Sección 8): los programa Gerencia ---------------------------------

export function useReportes() {
  return useQuery({
    queryKey: ['reportes'],
    queryFn: async () => (await api.get<ReporteRead[]>('/dashboard/reportes')).data,
  })
}

export function useGuardarReporte() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...datos }: { id?: string; nombre: string; periodicidad: string; destinatarios: string[]; indicadores: string[]; ciudad?: string; activo: boolean }) =>
      (id ? await api.put<ReporteRead>(`/dashboard/reportes/${id}`, datos) : await api.post<ReporteRead>('/dashboard/reportes', datos)).data,
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['reportes'] }),
  })
}
