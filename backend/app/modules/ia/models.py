from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.auditoria import Auditable
from app.core.database import Base, JSONTipo, TimestampMixin, UUIDMixin


class PromptIA(Base, UUIDMixin, TimestampMixin, Auditable):
    """F4-IAA-01 Prompt versionado. Solo una version activa por codigo, y solo despues de
    pasar su evaluacion (F4-IAA-04)."""

    __tablename__ = "prompts_ia"
    __table_args__ = (UniqueConstraint("codigo", "version"),)

    codigo: Mapped[str] = mapped_column(String(40), index=True)
    version: Mapped[int] = mapped_column(Integer)
    sistema: Mapped[str] = mapped_column(Text)
    # borrador | activo | retirado
    estado: Mapped[str] = mapped_column(String(12), default="borrador", index=True)
    nota: Mapped[str | None] = mapped_column(Text)
    evaluado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evaluacion: Mapped[dict[str, Any]] = mapped_column(JSONTipo, default=dict)
    activado_por_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"))


class ConsultaIA(Base, UUIDMixin, TimestampMixin):
    """F4-IAA-01 Registro de cada consulta: que prompt y version, cuanto costo, cuanto tardo
    y como termino. Es la base del limite de gasto."""

    __tablename__ = "consultas_ia"

    prompt_codigo: Mapped[str] = mapped_column(String(40), index=True)
    prompt_version: Mapped[int | None] = mapped_column(Integer)
    modelo: Mapped[str | None] = mapped_column(String(60))
    # ok | rechazo | error | presupuesto_agotado | desactivada
    estado: Mapped[str] = mapped_column(String(24), index=True)
    contexto: Mapped[str | None] = mapped_column(String(120), index=True)  # "solicitud:<id>"
    tokens_entrada: Mapped[int] = mapped_column(Integer, default=0)
    tokens_salida: Mapped[int] = mapped_column(Integer, default=0)
    tokens_cache_lectura: Mapped[int] = mapped_column(Integer, default=0)
    tokens_cache_escritura: Mapped[int] = mapped_column(Integer, default=0)
    costo_usd: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=0)
    latencia_ms: Mapped[int | None] = mapped_column(Integer)
    request_id: Mapped[str | None] = mapped_column(String(80))
    entrada: Mapped[str | None] = mapped_column(Text)
    salida: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)


class CasoPruebaIA(Base, UUIDMixin, TimestampMixin, Auditable):
    """F4-IAA-04 Caso de prueba con resultado esperado. Se corre contra una version antes de
    activarla: sin pasar todos, la version no entra en operacion."""

    __tablename__ = "casos_prueba_ia"

    prompt_codigo: Mapped[str] = mapped_column(String(40), index=True)
    nombre: Mapped[str] = mapped_column(String(160))
    entrada: Mapped[str] = mapped_column(Text)
    # {"campo": "alcance", "igual": "fuera"} | {"contiene": [...]} | {"no_contiene": [...]}
    esperado: Mapped[dict[str, Any]] = mapped_column(JSONTipo, default=dict)
