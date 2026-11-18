from typing import Any

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.auditoria import Auditable
from app.core.database import Base, JSONTipo, TimestampMixin, UUIDMixin


class DatosTimu(Base, UUIDMixin, TimestampMixin, Auditable):
    """R3-PUB-04 Lo institucional y de contacto de TIMU, que dice la portada publica y que
    Administracion edita sin desplegar (decidido con el usuario el 2026-11-17): quienes son, su
    clinica, como se les escribe. Una sola fila, que crea la migracion."""

    __tablename__ = "datos_timu"
    __checks__ = {
        "una_sola_fila": "unica",
        "whatsapp_formato": "whatsapp IS NULL OR whatsapp ~ '^\\+[1-9][0-9]{7,14}$'",
        "correo_formato": "correo IS NULL OR correo ~ '^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$'",
    }
    __unicos__ = {"unica": (["unica"], None)}

    unica: Mapped[bool] = mapped_column(Boolean, default=True)
    razon_social: Mapped[str | None] = mapped_column(String(160))
    nit: Mapped[str | None] = mapped_column(String(20))
    presentacion: Mapped[str | None] = mapped_column(Text)
    mision: Mapped[str | None] = mapped_column(Text)
    vision: Mapped[str | None] = mapped_column(Text)
    valores: Mapped[list[str]] = mapped_column(JSONTipo, default=list)
    clinica_nombre: Mapped[str | None] = mapped_column(String(160))
    clinica_direccion: Mapped[str | None] = mapped_column(String(255))
    clinica_barrio: Mapped[str | None] = mapped_column(String(120))
    clinica_ciudad: Mapped[str | None] = mapped_column(
        String(80), ForeignKey("ciudades.nombre", onupdate="CASCADE"), index=True
    )
    clinica_horario: Mapped[str | None] = mapped_column(String(255))
    # «Medicina prepagada 24 horas; clinica de lunes a sabado...»: como se atiende cada canal.
    horario_atencion: Mapped[str | None] = mapped_column(Text)
    telefonos: Mapped[list[str]] = mapped_column(JSONTipo, default=list)  # E.164
    # El numero al que escribe quien se afilia o llega a la portada (antes, una variable de
    # entorno). Vacio: no se ofrece contacto por WhatsApp.
    whatsapp: Mapped[str | None] = mapped_column(String(32))
    correo: Mapped[str | None] = mapped_column(String(255))
    # [{"nombre": "Instagram", "url": "https://..."}]
    redes: Mapped[list[dict[str, Any]]] = mapped_column(JSONTipo, default=list)
