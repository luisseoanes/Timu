"""Fechas y horas. Las marcas de tiempo se guardan en UTC; las fechas de negocio (corte,
vencimiento, agenda) se calculan en la hora de Colombia."""

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

ZONA_NEGOCIO = ZoneInfo("America/Bogota")


def ahora() -> datetime:
    return datetime.now(UTC)


def hoy() -> date:
    """Fecha de negocio actual en Colombia."""
    return datetime.now(ZONA_NEGOCIO).date()


def con_zona(dt: datetime) -> datetime:
    """Normaliza a UTC con zona. SQLite devuelve datetimes sin zona aunque se guarden en UTC."""
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
