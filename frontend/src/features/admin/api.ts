import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/api/client'
import type {
  FamiliaParaSuprimir,
  BorradorRegla,
  CasoRead,
  ColorPlan,
  ConsultaRead,
  DatosTimuIn,
  DatosTimuRead,
  EnPalabras,
  EsquemaPreventivoRead,
  EventoDeReglas,
  Page,
  PlanRead,
  PromptRead,
  RecuentosUsuarios,
  ReglaRead,
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
  /** R3-PUB-04: hasta cuánto cubre por episodio (vacío = sin tope), desde cuántos días de
   * afiliada aplica y su detalle, que dicen la portada, el registro y el contrato. */
  tope_episodio: string | null
  carencia_dias: number | null
  detalle: string | null
}

/** Lo que el plan da sin ser un tipo de servicio que se agenda (R3-PUB-04). */
export interface Adicional {
  nombre: string
  cubre: string
  detalle: string | null
  carencia_dias: number | null
  tercero: boolean
}

// --- Lecturas ---------------------------------------------------------------------------------

export interface FiltrosUsuarios {
  grupo: keyof RecuentosUsuarios
  q?: string
  limit: number
  offset: number
}

export function useUsuarios(filtros: FiltrosUsuarios) {
  return useQuery({
    queryKey: ['usuarios', filtros],
    placeholderData: keepPreviousData,
    queryFn: async () => (await api.get<Page<UsuarioRead>>('/auth/usuarios', { params: filtros })).data,
  })
}

export function useRecuentosUsuarios(q?: string) {
  return useQuery({
    queryKey: ['usuarios', 'recuentos', q ?? null],
    queryFn: async () => (await api.get<RecuentosUsuarios>('/auth/usuarios/recuentos', { params: { q } })).data,
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

/** 6.2 / 6.3 Tarifa por peludo con 1, 2, 3 y 4 o más peludos, y el precio de cada periodo
 * largo para un solo peludo (vacío = sin descuento). Los valores van como texto: son dinero. */
export interface Tarifas {
  por_peludos: [string, string, string, string]
  trimestral?: string
  semestral?: string
  anual?: string
}

/** Las condiciones que el registro dice de frente (R3-PUB-02). Vacío = sin escribir. */
export interface CondicionesPlan {
  carencia: string
  exclusiones: string
  terminos_url: string
}

export interface NuevoPlan extends CondicionesPlan {
  codigo: string
  nombre: string
  descripcion?: string
  ciudades: string[]
  especies: string[]
  color: ColorPlan
  tarifas: Tarifas
}

export function useCrearPlan() {
  return useMutacion(async (datos: NuevoPlan) => (await api.post<PlanRead>('/planes', datos)).data, 'planes')
}

export function useActualizarPlan() {
  return useMutacion(
    async ({
      id,
      ...datos
    }: { id: string; activo?: boolean; nombre?: string; descripcion?: string | null; color?: ColorPlan } & Partial<CondicionesPlan>) =>
      (await api.patch<PlanRead>(`/planes/${id}`, datos)).data,
    'planes',
  )
}

export function useGuardarTarifas() {
  return useMutacion(
    async ({ id, tarifas }: { id: string; tarifas: Tarifas }) => (await api.put<PlanRead>(`/planes/${id}/tarifas`, tarifas)).data,
    'planes',
  )
}

export function useGuardarCiudades() {
  return useMutacion(
    async ({ id, ciudades }: { id: string; ciudades: string[] }) =>
      (await api.put<PlanRead>(`/planes/${id}/ciudades`, ciudades)).data,
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

export function useGuardarAdicionales() {
  return useMutacion(
    async ({ id, adicionales }: { id: string; adicionales: Adicional[] }) =>
      (await api.put<PlanRead>(`/planes/${id}/adicionales`, adicionales)).data,
    'planes',
  )
}

/** Lo que dice de TIMU la portada pública (R3-PUB-04). */
export function useDatosTimu() {
  return useQuery({
    queryKey: ['institucional'],
    queryFn: async () => (await api.get<DatosTimuRead>('/institucional')).data,
  })
}

export function useGuardarDatosTimu() {
  return useMutacion(async (datos: DatosTimuIn) => (await api.put<DatosTimuRead>('/institucional', datos)).data, 'institucional')
}

/** Lo que se guarda de una regla desde el editor por campos (DEU-8). */
export interface DatosRegla {
  nombre?: string
  descripcion?: string | null
  condicion?: Record<string, unknown>
  accion?: Record<string, unknown>
  prioridad?: number
  detener?: boolean
  plan_id?: string | null
  vigente_desde?: string | null
  vigente_hasta?: string | null
  activa?: boolean
}

export function useActualizarRegla() {
  return useMutacion(
    async ({ id, ...datos }: { id: string } & DatosRegla) => (await api.patch<ReglaRead>(`/reglas/${id}`, datos)).data,
    'reglas',
  )
}

/** El código interno no se pide: la API lo saca del nombre. */
export function useCrearRegla() {
  return useMutacion(
    async (datos: DatosRegla & { nombre: string; evento: string; accion: Record<string, unknown> }) =>
      (await api.post<ReglaRead>('/reglas', datos)).data,
    'reglas',
  )
}

/** Cada evento con los datos que da a sus reglas y lo que pueden hacer, con sus opciones. */
export function useEventosReglas() {
  return useQuery({
    queryKey: ['reglas', 'eventos'],
    queryFn: async () => (await api.get<EventoDeReglas[]>('/reglas/eventos')).data,
  })
}

/** La regla a medio escribir, en palabras y validada como al guardarla (sin guardar nada). */
export function useReglaEnPalabras(borrador: BorradorRegla | null) {
  return useQuery({
    queryKey: ['reglas', 'en-palabras', borrador],
    queryFn: async () => (await api.post<EnPalabras>('/reglas/describir', borrador)).data,
    enabled: borrador !== null,
    placeholderData: keepPreviousData,
    retry: false,
  })
}

/** Lo que aplicaría a un contexto (reglas/router.py: `probar`), sin ejecutar nada. */
export interface ReglaQueAplica {
  regla: string
  nombre: string
  accion_texto: string
}

export function useProbarReglas() {
  return useMutation({
    mutationFn: async (datos: { evento: string; contexto: Record<string, unknown> }) =>
      (await api.post<ReglaQueAplica[]>('/reglas/probar', datos)).data,
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

// --- Supresion de datos (Ley 1581): sin abrir la ficha de la familia ----------------------------

export function useParaSuprimir(documento: string) {
  return useQuery({
    queryKey: ['supresion', documento],
    queryFn: async () => (await api.get<FamiliaParaSuprimir>('/familias/supresion', { params: { documento } })).data,
    enabled: documento.length >= 3,
    retry: false,
  })
}

export function useAnonimizar() {
  return useMutacion(async (familiaId: string) => (await api.post(`/familias/${familiaId}/anonimizar`)).data, 'supresion')
}
