"""F0-09 Catalogos maestros. Se identifican por `codigo` estable para que la carga sea
repetible (upsert) y para que el resto del sistema los referencie sin depender del id."""

from typing import Any

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, EnumDb, JSONTipo, TimestampMixin, UUIDMixin
from app.core.enums import TipoPreventivo, TipoServicio


class Ciudad(Base, UUIDMixin, TimestampMixin):
    """Codigo DANE de municipio. Las coordenadas sirven de respaldo al geocodificar (F1-FAM-05)."""

    __tablename__ = "ciudades"
    __checks__ = {
        "latitud_rango": "latitud IS NULL OR latitud BETWEEN -90 AND 90",
        "longitud_rango": "longitud IS NULL OR longitud BETWEEN -180 AND 180",
        "codigo_no_vacio": "btrim(codigo) <> ''",
        "nombre_no_vacio": "btrim(nombre) <> ''",
    }

    codigo: Mapped[str] = mapped_column(String(8), unique=True)
    nombre: Mapped[str] = mapped_column(String(80), index=True, unique=True)
    departamento: Mapped[str] = mapped_column(String(80))
    latitud: Mapped[float | None] = mapped_column(Float)
    longitud: Mapped[float | None] = mapped_column(Float)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)


class Especie(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "especies"

    codigo: Mapped[str] = mapped_column(String(24), unique=True)
    nombre: Mapped[str] = mapped_column(String(60))
    activa: Mapped[bool] = mapped_column(Boolean, default=True)


class TipoServicioCatalogo(Base, UUIDMixin, TimestampMixin):
    """Tipos concretos de atencion (consulta, vacunacion...), agrupados por modalidad (6.5)."""

    __tablename__ = "tipos_servicio"
    __checks__ = {
        "duracion_positiva": "duracion_min > 0",
    }

    codigo: Mapped[str] = mapped_column(String(40), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    modalidad: Mapped[str] = mapped_column(EnumDb(TipoServicio), index=True)  # enums.TipoServicio
    duracion_min: Mapped[int] = mapped_column(Integer, default=30)
    requiere_autorizacion: Mapped[bool] = mapped_column(Boolean, default=False)
    # F1-SER-02 Flujo del tipo: [{"codigo", "nombre", "obligatorio", "campos": [...]}].
    # El servicio no se completa hasta cerrar los pasos obligatorios.
    pasos: Mapped[list[dict[str, Any]]] = mapped_column(JSONTipo, default=list)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class EsquemaPreventivo(Base, UUIDMixin, TimestampMixin):
    """6.8 Esquema por especie y edad: serie inicial de dosis y refuerzo periodico.

    Ejemplo: polivalente canina desde la semana 6, 3 dosis cada 21 dias, refuerzo anual.
    """

    __tablename__ = "esquemas_preventivos"
    __checks__ = {
        "edad_no_negativa": "edad_minima_semanas >= 0",
        "dosis_minimo": "dosis_iniciales >= 1",
        "intervalos_no_negativos": (
            "(intervalo_inicial_dias IS NULL OR intervalo_inicial_dias >= 0)"
            " AND (intervalo_refuerzo_dias IS NULL OR intervalo_refuerzo_dias >= 0)"
        ),
        "serie_con_intervalo": "dosis_iniciales = 1 OR intervalo_inicial_dias > 0",
    }

    codigo: Mapped[str] = mapped_column(String(40), unique=True)
    especie_codigo: Mapped[str] = mapped_column(ForeignKey("especies.codigo"), index=True)
    tipo: Mapped[str] = mapped_column(
        EnumDb(TipoPreventivo)
    )  # vacuna | desparasitacion_interna | ...
    nombre: Mapped[str] = mapped_column(String(120))
    edad_minima_semanas: Mapped[int] = mapped_column(Integer, default=0)
    dosis_iniciales: Mapped[int] = mapped_column(Integer, default=1)
    intervalo_inicial_dias: Mapped[int] = mapped_column(Integer, default=0)
    intervalo_refuerzo_dias: Mapped[int | None] = mapped_column(Integer)
    requiere_autorizacion: Mapped[bool] = mapped_column(Boolean, default=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
