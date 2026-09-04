from enum import StrEnum


class Rol(StrEnum):
    """Perfiles de acceso a la plataforma."""

    ADMIN = "admin"
    COMERCIAL = "comercial"
    OPERACIONES = "operaciones"
    MEDICO = "medico"
    FAMILIA = "familia"  # portal de usuarios


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
