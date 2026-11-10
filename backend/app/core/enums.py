from enum import StrEnum


class Rol(StrEnum):
    """Perfiles de acceso a la plataforma."""

    ADMIN = "admin"
    COMERCIAL = "comercial"
    OPERACIONES = "operaciones"
    MEDICO = "medico"
    FAMILIA = "familia"  # portal de usuarios
    # F2-ALI-03 Clinica aliada: valida remisiones de SU clinica y reporta la atencion.
    ALIADA = "aliada"


class EstadoAfiliacion(StrEnum):
    """6.23 Estados de afiliacion."""

    PROSPECTO = "prospecto"
    ACTIVA = "activa"
    EN_MORA = "en_mora"
    CONGELADA = "congelada"
    CANCELADA = "cancelada"


class EstadoServicio(StrEnum):
    """6.10 Estados de los servicios (maquina de estados)."""

    SOLICITADO = "solicitado"
    AGENDADO = "agendado"
    EN_RUTA = "en_ruta"
    EN_ATENCION = "en_atencion"
    COMPLETADO = "completado"
    PENDIENTE_AUTORIZACION = "pendiente_autorizacion"
    REPROGRAMADO = "reprogramado"
    CANCELADO = "cancelado"


class TipoServicio(StrEnum):
    DOMICILIARIO = "domiciliario"
    PREVENTIVO = "preventivo"
    CLINICO = "clinico"
    VIRTUAL = "virtual"
    ALIADA = "aliada"


class EstadoPago(StrEnum):
    PENDIENTE = "pendiente"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"
    REVERSADO = "reversado"
    ANULADO = "anulado"  # enlace de pago reemplazado antes de pagarse (afiliaciones)


# --- Conjuntos cerrados de la base -------------------------------------------------------------
# Cada StrEnum que tipa una columna tiene un enum de PostgreSQL con su nombre en snake_case
# (`EnumDb` en app/core/database.py). Anadir un valor exige la migracion que lo anada a la
# base: `test_persistencia` compara las dos listas. Ver docs/plan-persistencia.md (fase 2a).


class EstadoAltaPeludo(StrEnum):
    """6.1 Un peludo mas desde el portal: espera el pago de la parte del periodo en curso."""

    PENDIENTE_PAGO = "pendiente_pago"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"
    # El pago entro pero el peludo no pudo entrar al contrato: lo resuelve el equipo.
    ERROR = "error"


class ProveedorPago(StrEnum):
    MANUAL = "manual"
    WOMPI = "wompi"


class EstadoEventoPasarela(StrEnum):
    RECIBIDO = "recibido"
    PROCESADO = "procesado"
    IGNORADO = "ignorado"
    ERROR = "error"


class MedioAceptacion(StrEnum):
    FORMULARIO_WEB = "formulario_web"
    PRESENCIAL = "presencial"
    WHATSAPP = "whatsapp"
    LLAMADA = "llamada"


class OrigenSolicitudAfiliacion(StrEnum):
    FORMULARIO = "formulario"
    ASISTIDA = "asistida"


class SexoMascota(StrEnum):
    MACHO = "macho"
    HEMBRA = "hembra"


class GeoPrecision(StrEnum):
    DIRECCION = "direccion"
    CIUDAD = "ciudad"
    MANUAL = "manual"


class PropositoArchivo(StrEnum):
    FOTO_MASCOTA = "foto_mascota"
    ADJUNTO_CLINICO = "adjunto_clinico"
    CONTRATO = "contrato"
    FORMULA = "formula"
    CARNET = "carnet"
    DOCUMENTO_FAMILIA = "documento_familia"


class CategoriaDocumento(StrEnum):
    """6.1 Categoria de un documento que el equipo adjunta a la familia o a una mascota."""

    IDENTIFICACION = "identificacion"
    EXAMEN_EXTERNO = "examen_externo"
    OTRO = "otro"


class PropositoToken(StrEnum):
    RECUPERACION = "recuperacion"
    ACTIVACION = "activacion"
    CODIGO_INGRESO = "codigo_ingreso"


class CanalComunicacion(StrEnum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"


class DireccionMensaje(StrEnum):
    ENTRANTE = "entrante"
    SALIENTE = "saliente"


class CategoriaPlantilla(StrEnum):
    UTILITY = "utility"
    MARKETING = "marketing"
    AUTHENTICATION = "authentication"


class EstadoAprobacionPlantilla(StrEnum):
    BORRADOR = "borrador"
    ENVIADA = "enviada"
    APROBADA = "aprobada"
    RECHAZADA = "rechazada"
    PAUSADA = "pausada"


class EstadoCampana(StrEnum):
    BORRADOR = "borrador"
    PROGRAMADA = "programada"
    EN_ENVIO = "en_envio"
    FINALIZADA = "finalizada"
    CANCELADA = "cancelada"


class RecurrenciaCampana(StrEnum):
    NINGUNA = "ninguna"
    DIARIA = "diaria"
    SEMANAL = "semanal"
    MENSUAL = "mensual"


class EstadoEjecucionCampana(StrEnum):
    EN_ENVIO = "en_envio"
    TERMINADA = "terminada"
    CANCELADA = "cancelada"


class EstadoDestinatario(StrEnum):
    PENDIENTE = "pendiente"
    ENCOLADO = "encolado"
    EXCLUIDO = "excluido"


class PeriodicidadReporte(StrEnum):
    DIARIA = "diaria"
    SEMANAL = "semanal"
    MENSUAL = "mensual"


class TipoEncuesta(StrEnum):
    SATISFACCION = "satisfaccion"
    SEGUIMIENTO = "seguimiento"


class CanalRespuestaEncuesta(StrEnum):
    ENLACE = "enlace"
    WHATSAPP = "whatsapp"


class EstadoEncuesta(StrEnum):
    PENDIENTE = "pendiente"
    ENVIADA = "enviada"
    RESPONDIDA = "respondida"
    VENCIDA = "vencida"
    OMITIDA = "omitida"


class TipoHistoria(StrEnum):
    PRESENCIAL = "presencial"
    DOMICILIARIA = "domiciliaria"
    VIRTUAL = "virtual"


class EstadoHistoria(StrEnum):
    BORRADOR = "borrador"
    FIRMADA = "firmada"
    CORREGIDA = "corregida"


class EstadoRespuestaVirtual(StrEnum):
    BORRADOR = "borrador"
    APROBADA = "aprobada"
    RETIRADA = "retirada"


class CanalVirtual(StrEnum):
    PORTAL = "portal"
    WHATSAPP = "whatsapp"
    PANEL = "panel"


class EstadoSolicitudVirtual(StrEnum):
    EN_COLA = "en_cola"
    EN_ATENCION = "en_atencion"
    RESPONDIDA = "respondida"
    CERRADA = "cerrada"


class Prioridad(StrEnum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


class EtapaInteresado(StrEnum):
    NUEVO = "nuevo"
    CONTACTADO = "contactado"
    COTIZADO = "cotizado"
    EN_AFILIACION = "en_afiliacion"
    AFILIADO = "afiliado"
    PERDIDO = "perdido"


class EstadoConversacion(StrEnum):
    AUTOMATICA = "automatica"
    CON_ASESOR = "con_asesor"


class EstadoPrompt(StrEnum):
    BORRADOR = "borrador"
    ACTIVO = "activo"
    RETIRADO = "retirado"


class EstadoConsultaIa(StrEnum):
    OK = "ok"
    RECHAZO = "rechazo"
    ERROR = "error"
    PRESUPUESTO_AGOTADO = "presupuesto_agotado"
    DESACTIVADA = "desactivada"


class PeriodoCupo(StrEnum):
    MENSUAL = "mensual"
    ANUAL = "anual"


class ColorPlan(StrEnum):
    """Color con el que la interfaz reconoce un plan: uno de los colores del logo
    (docs/manual-de-marca.md, secciones 4 y 10). La interfaz lo toma de aqui, nunca del nombre."""

    VERDE = "verde"
    NARANJA = "naranja"
    AZUL = "azul"


class Periodicidad(StrEnum):
    """6.2 Cada cuanto paga la familia. Con un solo peludo, los periodos largos tienen su
    propio precio (tarifas_periodicidad); con mas, se paga el mensual por los meses."""

    MENSUAL = "mensual"
    TRIMESTRAL = "trimestral"
    SEMESTRAL = "semestral"
    ANUAL = "anual"


MESES_PERIODICIDAD: dict[str, int] = {
    Periodicidad.MENSUAL: 1,
    Periodicidad.TRIMESTRAL: 3,
    Periodicidad.SEMESTRAL: 6,
    Periodicidad.ANUAL: 12,
}


class TipoCambioPlan(StrEnum):
    CAMBIO_PLAN = "cambio_plan"
    MASCOTA_ALTA = "mascota_alta"
    MASCOTA_BAJA = "mascota_baja"


class ModoCambioPlan(StrEnum):
    DIARIO = "diario"
    SIN_CARGO = "sin_cargo"
    PROXIMO_CICLO = "proximo_ciclo"
    PROXIMA_CUOTA = "proxima_cuota"


class TipoPreventivo(StrEnum):
    VACUNA = "vacuna"
    DESPARASITACION_INTERNA = "desparasitacion_interna"
    DESPARASITACION_EXTERNA = "desparasitacion_externa"


class EstadoEventoPreventivo(StrEnum):
    PROGRAMADO = "programado"
    APLICADO = "aplicado"
    CANCELADO = "cancelado"


class MedioAutorizacion(StrEnum):
    WHATSAPP = "whatsapp"
    TELEFONO = "telefono"
    LLAMADA = "llamada"
    PRESENCIAL = "presencial"
    PORTAL = "portal"
    FORMULARIO = "formulario"
    CORREO = "correo"


class EstadoRemision(StrEnum):
    EMITIDA = "emitida"
    UTILIZADA = "utilizada"
    ANULADA = "anulada"


class EstadoRuta(StrEnum):
    PLANIFICADA = "planificada"
    EN_CURSO = "en_curso"
    FINALIZADA = "finalizada"
    CANCELADA = "cancelada"


class EstadoParada(StrEnum):
    PENDIENTE = "pendiente"
    EN_CAMINO = "en_camino"
    EN_SITIO = "en_sitio"
    COMPLETADA = "completada"
    OMITIDA = "omitida"


class EstadoPlanificacion(StrEnum):
    PENDIENTE = "pendiente"
    LISTA = "lista"
    FALLIDA = "fallida"


class AreaTarea(StrEnum):
    COMERCIAL = "comercial"
    OPERACIONES = "operaciones"
    MEDICO = "medico"
    CARTERA = "cartera"
    SERVICIO_CLIENTE = "servicio_cliente"


class EstadoTarea(StrEnum):
    ABIERTA = "abierta"
    EN_PROGRESO = "en_progreso"
    CERRADA = "cerrada"


class EventoRegla(StrEnum):
    CARTERA_ESTADO = "cartera.estado"
    CARTERA_ALERTA = "cartera.alerta"
    CARTERA_RENOVACION = "cartera.renovacion"
    PLAN_CAMBIO = "plan.cambio"
    # Retirado: el cupo y las mascotas adicionales los sustituyen las tarifas por numero de
    # peludos (migracion 0033). Sigue en la base por las reglas y cambios de plan que lo citan.
    PLAN_MASCOTA = "plan.mascota"
    PLAN_RECOMENDACION = "plan.recomendacion"
    SERVICIO_TRANSICION = "servicio.transicion"
    SERVICIO_ELEGIBILIDAD = "servicio.elegibilidad"


class CodigoPrompt(StrEnum):
    COMERCIAL_GUION = "comercial_guion"
    VETERINARIO_BORRADOR = "veterinario_borrador"
