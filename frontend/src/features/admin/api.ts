import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/api/client'
import type {
  CasoRead,
  ConsultaRead,
  EsquemaPreventivoRead,
  EventoPasarelaRead,
  Page,
  PlanRead,
  PromptRead,
  ReglaRead,
  ReporteRead,
  Rol,
  UsuarioRead,
} from '@/types'

export interface ConsumoIA {
  mes: string
  gasto_usd: number
  presupuesto_usd: number
  disponible_usd: number
  por_prompt: { prompt: string; estado: string; consultas: number; costo_usd: number }[]
}

export interface EvaluacionPrompt {
  total: number
  aprobados: number
  detalle: { caso: string; aprobado: boolean; motivo: string }[]
  en: string
}

export interface Beneficio {
  tipo_servicio_codigo: string
  cupo: number | null
  periodo_cupo: 'mensual' | 'anual'
  cobertura_pct: number
  copago: string
}

// --- Lecturas ---------------------------------------------------------------------------------

export function useUsuarios(rol?: string) {
  return useQuery({
    queryKey: ['usuarios', rol ?? null],
    queryFn: async () =>
      (await api.get<Page<UsuarioRead>>('/auth/usuarios', { params: { rol, limit: 200 } })).data,
  })
}

export function usePlanesAdmin() {
  return useQuery({
    queryKey: ['planes', 'admin'],
    queryFn: async () => (await api.get<PlanRead[]>('/planes', { params: { incluir_inactivos: true } })).data,
  })
}

export function useReglas(evento?: string) {
  return useQuery({
    queryKey: ['reglas', evento ?? null],
    queryFn: async () => (await api.get<ReglaRead[]>('/reglas', { params: { evento } })).data,
  })
}

export function useEventosReglas() {
  return useQuery({
    queryKey: ['reglas', 'eventos'],
    staleTime: Infinity,
    queryFn: async () => (await api.get<Record<string, string>>('/reglas/eventos')).data,
  })
}

export function useEsquemas() {
  return useQuery({
    queryKey: ['catalogos', 'esquemas'],
    queryFn: async () => (await api.get<EsquemaPreventivoRead[]>('/catalogos/esquemas-preventivos')).data,
  })
}

export function useCiudadesTodas() {
  return useQuery({
    queryKey: ['catalogos', 'ciudades', 'todas'],
    queryFn: async () =>
      (await api.get<{ codigo: string; nombre: string; departamento: string; activa: boolean }[]>('/catalogos/ciudades', { params: { incluir_inactivas: true } })).data,
  })
}

export function usePrompts() {
  return useQuery({
    queryKey: ['ia', 'prompts'],
    queryFn: async () => (await api.get<PromptRead[]>('/ia/prompts')).data,
  })
}

export function useCasos() {
  return useQuery({
    queryKey: ['ia', 'casos'],
    queryFn: async () => (await api.get<CasoRead[]>('/ia/casos')).data,
  })
}

export function useConsultasIA() {
  return useQuery({
    queryKey: ['ia', 'consultas'],
    queryFn: async () => (await api.get<ConsultaRead[]>('/ia/consultas')).data,
  })
}

export function useConsumoIA() {
  return useQuery({
    queryKey: ['ia', 'consumo'],
    queryFn: async () => (await api.get<ConsumoIA>('/ia/consumo')).data,
  })
}

export function useReportes() {
  return useQuery({
    queryKey: ['reportes'],
    queryFn: async () => (await api.get<ReporteRead[]>('/dashboard/reportes')).data,
  })
}

export function useEventosPasarela(estado?: string) {
  return useQuery({
    queryKey: ['pasarela', estado ?? null],
    queryFn: async () =>
      (await api.get<Page<EventoPasarelaRead>>('/cartera/eventos-pasarela', { params: { estado, limit: 50, orden: '-created_at' } })).data,
  })
}

// --- Escrituras -------------------------------------------------------------------------------

function useMutacion<T, R>(fn: (datos: T) => Promise<R>, ...claves: string[]) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: fn,
    onSuccess: () => claves.forEach((c) => void qc.invalidateQueries({ queryKey: [c] })),
  })
}

export function useCrearUsuario() {
  return useMutacion(
    async (datos: { nombre: string; email?: string; telefono?: string; rol: Rol; password: string; clinica_aliada_id?: string }) =>
      (await api.post<UsuarioRead>('/auth/usuarios', datos)).data,
    'usuarios',
    'equipo',
  )
}

export function useActualizarUsuario() {
  return useMutacion(
    async ({ id, ...datos }: { id: string; rol?: Rol; activo?: boolean; nombre?: string }) =>
      (await api.patch<UsuarioRead>(`/auth/usuarios/${id}`, datos)).data,
    'usuarios',
    'equipo',
  )
}

export function useCrearPlan() {
  return useMutacion(
    async (datos: { codigo: string; nombre: string; descripcion?: string; ciudad?: string; valor_mensual: string; cupos_mascotas: number }) =>
      (await api.post<PlanRead>('/planes', datos)).data,
    'planes',
  )
}

export function useActualizarPlan() {
  return useMutacion(
    async ({ id, ...datos }: { id: string; valor_mensual?: string; activo?: boolean; cupos_mascotas?: number; nombre?: string }) =>
      (await api.patch<PlanRead>(`/planes/${id}`, datos)).data,
    'planes',
  )
}

export function useGuardarBeneficios() {
  return useMutacion(
    async ({ id, beneficios }: { id: string; beneficios: Beneficio[] }) =>
      (await api.put<PlanRead>(`/planes/${id}/beneficios`, beneficios)).data,
    'planes',
  )
}

export function useActualizarRegla() {
  return useMutacion(
    async ({ id, ...datos }: { id: string; activa?: boolean; condicion?: unknown; accion?: unknown; prioridad?: number }) =>
      (await api.patch<ReglaRead>(`/reglas/${id}`, datos)).data,
    'reglas',
  )
}

export function useProbarReglas() {
  return useMutation({
    mutationFn: async (datos: { evento: string; contexto: Record<string, unknown> }) =>
      (await api.post<unknown[]>('/reglas/probar', datos)).data,
  })
}

export function useActivarCatalogo() {
  return useMutacion(
    async ({ catalogo, codigo, activo }: { catalogo: string; codigo: string; activo: boolean }) =>
      (await api.patch(`/catalogos/${catalogo}/${codigo}/activo`, { activo })).data,
    'catalogos',
  )
}

export function useCrearPrompt() {
  return useMutacion(
    async (datos: { codigo: string; sistema: string; nota?: string }) => (await api.post<PromptRead>('/ia/prompts', datos)).data,
    'ia',
  )
}

export function useEvaluarPrompt() {
  return useMutacion(
    async (id: string) => (await api.post<EvaluacionPrompt>(`/ia/prompts/${id}/evaluacion`)).data,
    'ia',
  )
}

export function useActivarPrompt() {
  return useMutacion(async (id: string) => (await api.post<PromptRead>(`/ia/prompts/${id}/activacion`)).data, 'ia')
}

export function useSembrarPrompts() {
  return useMutacion(async () => (await api.post('/ia/prompts/sembrar')).data, 'ia')
}

export function useCrearCaso() {
  return useMutacion(
    async (datos: { prompt_codigo: string; nombre: string; entrada: string; esperado: Record<string, unknown> }) =>
      (await api.post<CasoRead>('/ia/casos', datos)).data,
    'ia',
  )
}

export function useGuardarReporte() {
  return useMutacion(
    async ({ id, ...datos }: { id?: string; nombre: string; periodicidad: string; destinatarios: string[]; indicadores: string[]; ciudad?: string; activo: boolean }) =>
      (id ? await api.put<ReporteRead>(`/dashboard/reportes/${id}`, datos) : await api.post<ReporteRead>('/dashboard/reportes', datos)).data,
    'reportes',
  )
}

export function useReprocesarEvento() {
  return useMutacion(
    async (id: string) => (await api.post<EventoPasarelaRead>(`/cartera/eventos-pasarela/${id}/reprocesar`)).data,
    'pasarela',
  )
}
