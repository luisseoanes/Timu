// Generado por backend/scripts/generar_tipos_frontend.py desde el OpenAPI.
// No editar a mano: si cambia un schema de Pydantic, se regenera en el mismo cambio.
// Los decimales llegan como string en JSON; se formatean con lib/formato.ts.

export type Rol = 'admin' | 'comercial' | 'operaciones' | 'medico' | 'familia' | 'aliada'

export type EstadoAfiliacion = 'prospecto' | 'activa' | 'en_mora' | 'congelada' | 'cancelada'

export type EstadoServicio = 'solicitado' | 'agendado' | 'en_ruta' | 'en_atencion' | 'completado' | 'pendiente_autorizacion' | 'reprogramado' | 'cancelado'

export type TipoDocumento = 'CC' | 'CE' | 'TI' | 'PA' | 'PPT' | 'NIT'

export interface MascotaRead {
  nombre: string
  especie: string
  raza?: string | null
  sexo?: 'macho' | 'hembra' | null
  fecha_nacimiento?: string | null
  peso_kg?: number | null
  esterilizada?: boolean | null
  id: string
  familia_id: string
  activa: boolean
  motivo_baja?: string | null
  foto_url?: string | null
}

export interface FamiliaRead {
  titular_nombre: string
  tipo_documento?: TipoDocumento
  documento: string
  email?: string | null
  telefono: string
  ciudad: string
  direccion?: string | null
  notas?: string | null
  id: string
  estado: EstadoAfiliacion
  latitud: number | null
  longitud: number | null
  geo_precision: string | null
  origen: string
  dada_de_baja_en: string | null
  motivo_baja: string | null
  usuario_portal_id: string | null
  mascotas?: MascotaRead[]
}

export interface CambioHistorial {
  fecha: string
  accion: string
  usuario_id: string | null
  cambios: Record<string, unknown>
}

export interface UsuarioRead {
  id: string
  email: string | null
  telefono: string | null
  nombre: string
  rol: Rol
  activo: boolean
  clinica_aliada_id?: string | null
}

export interface CiudadRead {
  codigo: string
  nombre: string
  departamento: string
  latitud: number | null
  longitud: number | null
  activa: boolean
}

export interface EspecieRead {
  codigo: string
  nombre: string
  activa: boolean
}

export interface TipoServicioRead {
  codigo: string
  nombre: string
  modalidad: string
  duracion_min: number
  requiere_autorizacion: boolean
  activo: boolean
}

export interface PlanRead {
  id: string
  codigo: string
  nombre: string
  descripcion: string | null
  ciudad: string | null
  valor_mensual: string
  cupos_mascotas: number
  especies: string[]
  activo: boolean
  beneficios: BeneficioRead[]
}

export interface BeneficioRead {
  tipo_servicio_codigo: string
  cupo?: number | null
  periodo_cupo?: 'mensual' | 'anual'
  cobertura_pct?: number
  copago?: string
  id: string
}

export interface ContratoListado {
  id: string
  numero: string
  familia_id: string
  titular: string
  ciudad: string
  plan: string
  estado: string
  valor_mensual: string
  saldo_vencido: string
  dias_mora: number
  fecha_renovacion: string
}

export interface ContratoRead {
  id: string
  numero: string
  familia_id: string
  plan_id: string
  fecha_inicio: string
  fecha_renovacion: string
  fecha_fin: string | null
  dia_corte: number
  valor_plan: string
  mascotas_adicionales: number
  valor_adicional_mascota: string
  valor_mensual: string
  saldo_a_favor: string
  estado: string
  aceptado_en: string | null
  medio_aceptacion: string | null
}

export interface CuotaRead {
  id: string
  periodo: string
  tipo: string
  fecha_vencimiento: string
  valor: string
  valor_pagado: string
  estado: string
  dias_mora: number
  descripcion: string | null
}

export interface PagoRead {
  id: string
  familia_id: string
  cuota_id: string | null
  referencia_externa: string
  proveedor: string
  medio: string | null
  valor: string
  estado: string
  fecha_pago: string | null
  aplicado: boolean
}

export interface PlanResumen {
  id: string
  codigo: string
  nombre: string
}

export interface ProximoCobro {
  fecha: string
  valor: string
}

export interface EstadoCuenta {
  contrato: ContratoRead
  plan: PlanResumen
  estado: string
  saldo_pendiente: string
  saldo_vencido: string
  saldo_a_favor: string
  dias_mora: number
  proximo_cobro: ProximoCobro | null
  cuotas: CuotaRead[]
  pagos: PagoRead[]
}

export interface EventoPasarelaRead {
  id: string
  proveedor: string
  tipo: string
  referencia: string | null
  estado: string
  intentos: number
  error: string | null
  procesado_en: string | null
  created_at: string
}

export interface TareaRead {
  id: string
  titulo: string
  descripcion: string | null
  area: string
  prioridad: string
  estado: string
  vence_el: string | null
  asignada_a_id: string | null
  familia_id: string | null
  servicio_id: string | null
  contrato_id: string | null
  origen: string | null
  cerrada_en: string | null
  resolucion: string | null
  created_at: string
}

export interface ServicioRead {
  id: string
  familia_id: string
  mascota_id: string | null
  tipo_codigo: string
  tipo: string
  estado: string
  ciudad: string
  programado_para: string | null
  termina_en: string | null
  requiere_autorizacion: boolean
  autorizado: boolean
  autorizado_en: string | null
  profesional_id: string | null
  pendiente_origen_id: string | null
  observaciones: string | null
  motivo_estado: string | null
}

export interface PendienteRead {
  id: string
  servicio_origen_id: string
  descripcion: string
  requiere_autorizacion: boolean
  estado: string
  autorizado_por_id: string | null
  autorizado_en: string | null
  medio_autorizacion: string | null
  resolucion: string | null
}

export interface PasoRead {
  paso_codigo: string
  datos: Record<string, unknown>
  completado_por_id: string | null
  created_at: string
}

export interface CupoRead {
  inicio: string
  fin: string
  disponibles: number
}

export interface ElegibilidadRead {
  elegible: boolean
  motivos: string[]
}

export interface EventoRead {
  id: string
  mascota_id: string
  esquema_codigo: string | null
  tipo: string
  dosis_numero: number
  es_refuerzo: boolean
  estado: string
  fecha_programada: string
  fecha_aplicacion: string | null
  proxima_fecha: string | null
  producto: string | null
  lote: string | null
  requiere_autorizacion: boolean
  autorizado: boolean
  medio_autorizacion: string | null
  autorizado_en: string | null
  notificado_en: string | null
  servicio_id: string | null
}

export interface CarnetEmitidoRead {
  codigo: string
  url: string
  sha256: string
}

export interface AdjuntoRead {
  id: string
  historia_id: string
  nombre_archivo: string
  content_type: string | null
  descripcion: string | null
  created_at: string
}

export interface FormulaRead {
  id: string
  url: string
}

export interface PlanificacionRead {
  id: string
  fecha: string
  ciudad: string
  responsables: string[]
  estado: string
  resultado: Record<string, unknown>
  error: string | null
  created_at: string
}

export interface CampanaRead {
  id: string
  nombre: string
  canal: string
  plantilla: string | null
  variables: string[]
  segmento_id: string | null
  segmento: Record<string, unknown>
  estado: string
  programada_para: string | null
  recurrencia: string
  proxima_ejecucion: string | null
}

export interface SegmentoRead {
  id: string
  nombre: string
  descripcion: string | null
  filtros: Record<string, unknown>
}

export interface EjecucionRead {
  id: string
  iniciada_en: string
  terminada_en: string | null
  estado: string
  audiencia: number
  excluidos: number
}

export interface InteresadoRead {
  id: string
  nombre: string | null
  telefono: string | null
  email: string | null
  ciudad: string | null
  origen: string
  etapa: string
  responsable_id: string | null
  familia_id: string | null
  plan_sugerido: string | null
  datos: Record<string, unknown>
  motivo_perdida: string | null
  ultimo_contacto: string | null
  created_at: string
}

export interface ConversacionRead {
  id: string
  telefono: string
  interesado_id: string | null
  nodo: string
  datos: Record<string, unknown>
  estado: string
  asesor_id: string | null
  tarea_id: string | null
  updated_at: string
}

export interface EncuestaRead {
  id: string
  servicio_id: string
  familia_id: string
  responsable_id: string | null
  tipo: string
  estado: string
  programada_para: string
  enviada_en: string | null
  respondida_en: string | null
  canal_respuesta: string | null
  puntaje: number | null
  comentario: string | null
  tarea_id: string | null
}

export interface ClinicaRead {
  nombre: string
  nit?: string | null
  ciudad: string
  direccion?: string | null
  telefono?: string | null
  email?: string | null
  servicios?: string | null
  id: string
  activa: boolean
}

export interface ConvenioRead {
  plan_id?: string | null
  beneficio: string
  cobertura_pct?: number
  tarifa: string
  tope_cubierto?: string | null
  vigente_desde: string
  vigente_hasta?: string | null
  id: string
  clinica_id: string
  activo: boolean
}

export interface RemisionRead {
  id: string
  codigo: string
  clinica_id: string
  familia_id: string
  mascota_id: string
  servicio_id: string
  motivo: string
  beneficio_aplicado: string | null
  cobertura_pct: number
  tope_cubierto: string | null
  vence_en: string
  estado: string
  fecha_atencion: string | null
  valor_atencion: string | null
  valor_cubierto: string | null
  created_at: string
}

export interface ReporteRead {
  id: string
  nombre: string
  periodicidad: string
  destinatarios: string[]
  indicadores: string[]
  ciudad: string | null
  activo: boolean
  ultimo_envio: string | null
  ultimo_error: string | null
}

export interface PromptRead {
  id: string
  codigo: string
  version: number
  sistema: string
  estado: string
  nota: string | null
  evaluado_en: string | null
  evaluacion: Record<string, unknown>
}

export interface CasoRead {
  prompt_codigo: 'comercial_guion' | 'veterinario_borrador'
  nombre: string
  entrada: string
  esperado: Record<string, unknown>
  id: string
}

export interface ConsultaRead {
  id: string
  created_at: string
  prompt_codigo: string
  prompt_version: number | null
  modelo: string | null
  estado: string
  contexto: string | null
  tokens_entrada: number
  tokens_salida: number
  tokens_cache_lectura: number
  costo_usd: number
  latencia_ms: number | null
  error: string | null
}

export interface MensajeRead {
  id: string
  familia_id: string | null
  canal: string
  direccion: string
  destino: string | null
  plantilla: string | null
  contenido: string | null
  estado: string
  intentos: number
  error: string | null
  masivo: boolean
  enviado_en: string | null
  entregado_en: string | null
  leido_en: string | null
  created_at: string
}

export interface FranjaRead {
  ciudad: string
  modalidad: 'domiciliario' | 'preventivo' | 'clinico' | 'virtual' | 'aliada'
  dia_semana: number
  hora_inicio: string
  hora_fin: string
  capacidad?: number
  id: string
  activa: boolean
}

export interface RespuestaRead {
  codigo: string
  titulo: string
  cuerpo: string
  variables: string[]
  estado: string
}

export interface SolicitudVirtualRead {
  id: string
  familia_id: string
  mascota_id: string
  canal: string
  motivo: string
  estado: string
  prioridad: string
  asignada_a_id: string | null
  respuesta: string | null
  historia_id: string | null
  borrador_ia?: Record<string, unknown> | null
  borrador_en?: string | null
  created_at: string
}

export interface PlantillaConsultaRead {
  codigo: string
  nombre: string
  tipo_servicio_codigo: string | null
  campos: Record<string, string>
  activa: boolean
}

export interface SolicitudAfiliacionRead {
  id: string
  familia_id: string
  plan_id: string
  valor_inicial: string
  referencia_pago: string
  estado: string
  origen: string
  contrato_id: string | null
  aceptacion: Record<string, unknown>
  completada_en: string | null
  error: string | null
  created_at: string
}

export interface PlantillaWhatsAppRead {
  id: string
  nombre: string
  idioma: string
  version: number
  categoria: string
  cuerpo: string
  variables: string[]
  estado_aprobacion: string
  activa: boolean
}
