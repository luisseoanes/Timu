from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.auditoria import Auditable
from app.core.database import Base, EnumDb, JSONTipo, TimestampMixin, UUIDMixin
from app.core.enums import ModoCambioPlan, Periodicidad, PeriodoCupo, TipoCambioPlan


class Plan(Base, UUIDMixin, TimestampMixin, Auditable):
    """6.3 Plan grupal. `ciudad` vacia = disponible en todas las ciudades."""

    __tablename__ = "planes"
    __checks__ = {
        "valor_no_negativo": "valor_mensual >= 0",
        "cupos_minimo": "cupos_mascotas >= 1",
        "codigo_no_vacio": "btrim(codigo) <> ''",
        "nombre_no_vacio": "btrim(nombre) <> ''",
    }

    codigo: Mapped[str] = mapped_column(String(40), unique=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True)
    descripcion: Mapped[str | None] = mapped_column(Text)
    ciudad: Mapped[str | None] = mapped_column(
        String(80), ForeignKey("ciudades.nombre", onupdate="CASCADE"), index=True
    )
    valor_mensual: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    cupos_mascotas: Mapped[int] = mapped_column(Integer, default=1)
    especies: Mapped[list[str]] = mapped_column(JSONTipo, default=list)  # vacio = todas
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    # Solo los beneficios vigentes. Los reemplazados quedan con activo = False: lo que cubria
    # el plan antes no se borra (fase 3 de docs/plan-persistencia.md).
    beneficios: Mapped[list["Beneficio"]] = relationship(
        back_populates="plan",
        primaryjoin="and_(Plan.id == Beneficio.plan_id, Beneficio.activo.is_(True))",
        cascade="save-update, merge",
        lazy="selectin",
    )
    # 6.3 Disponibilidad y precios. Se cargan con el plan: el catalogo es pequeno y casi
    # toda lectura de un plan los necesita para mostrar o cotizar.
    ciudades: Mapped[list["CiudadPlan"]] = relationship(
        primaryjoin="and_(Plan.id == CiudadPlan.plan_id, CiudadPlan.activa.is_(True))",
        order_by="CiudadPlan.ciudad",
        lazy="selectin",
        viewonly=True,
    )
    tarifas: Mapped[list["TarifaPlan"]] = relationship(
        order_by="TarifaPlan.peludos", lazy="selectin", viewonly=True
    )
    tarifas_periodicidad: Mapped[list["TarifaPeriodicidad"]] = relationship(
        primaryjoin=(
            "and_(Plan.id == TarifaPeriodicidad.plan_id, TarifaPeriodicidad.activa.is_(True))"
        ),
        lazy="selectin",
        viewonly=True,
    )


class CiudadPlan(Base, UUIDMixin, TimestampMixin, Auditable):
    """6.3 Ciudad donde se vende un plan. Quitarla es una marca: los contratos de esa ciudad
    conservan su plan."""

    __tablename__ = "ciudades_plan"
    __unicos__ = {"plan_ciudad": (["plan_id", "ciudad"], None)}

    plan_id: Mapped[UUID] = mapped_column(ForeignKey("planes.id"), index=True)
    ciudad: Mapped[str] = mapped_column(
        String(80), ForeignKey("ciudades.nombre", onupdate="CASCADE"), index=True
    )
    activa: Mapped[bool] = mapped_column(Boolean, default=True)


class TarifaPlan(Base, UUIDMixin, TimestampMixin, Auditable):
    """6.3 Valor mensual de cada peludo del plan segun cuantos peludos tiene la afiliacion,
    esten o no en el mismo plan: de 1 a 4; con mas, se aplica la de 4. Se guarda el valor
    tal cual, no un porcentaje, para que quepa cualquier precio especial."""

    __tablename__ = "tarifas_plan"
    __checks__ = {"peludos_rango": "peludos BETWEEN 1 AND 4", "valor_positivo": "valor > 0"}
    __unicos__ = {"plan_peludos": (["plan_id", "peludos"], None)}

    plan_id: Mapped[UUID] = mapped_column(ForeignKey("planes.id"), index=True)
    peludos: Mapped[int] = mapped_column(Integer)
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2))


class TarifaPeriodicidad(Base, UUIDMixin, TimestampMixin, Auditable):
    """6.2 Precio total del periodo para una afiliacion de un solo peludo: el descuento por
    pagar varios meses juntos. No se acumula con el de cantidad, asi que con dos o mas
    peludos no se usa."""

    __tablename__ = "tarifas_periodicidad"
    __checks__ = {"valor_positivo": "valor > 0", "periodo_largo": "periodicidad <> 'mensual'"}
    __unicos__ = {"plan_periodicidad": (["plan_id", "periodicidad"], None)}

    plan_id: Mapped[UUID] = mapped_column(ForeignKey("planes.id"), index=True)
    periodicidad: Mapped[str] = mapped_column(EnumDb(Periodicidad))
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    # Retirar el descuento es una marca: nada se borra.
    activa: Mapped[bool] = mapped_column(Boolean, default=True)


class Beneficio(Base, UUIDMixin, TimestampMixin, Auditable):
    """F1-PLA-01 Lo que cubre el plan por tipo de servicio. `cupo` vacio = ilimitado."""

    __tablename__ = "beneficios_plan"
    __checks__ = {
        "cupo_no_negativo": "cupo IS NULL OR cupo >= 0",
        "cobertura_rango": "cobertura_pct BETWEEN 0 AND 100",
        "copago_no_negativo": "copago >= 0",
    }
    __unicos__ = {"tipo_vigente": (["plan_id", "tipo_servicio_codigo"], "activo")}

    plan_id: Mapped[UUID] = mapped_column(ForeignKey("planes.id", ondelete="CASCADE"), index=True)
    tipo_servicio_codigo: Mapped[str] = mapped_column(
        ForeignKey("tipos_servicio.codigo"), index=True
    )
    cupo: Mapped[int | None] = mapped_column(Integer)
    periodo_cupo: Mapped[str] = mapped_column(
        EnumDb(PeriodoCupo), default="anual"
    )  # mensual | anual
    cobertura_pct: Mapped[int] = mapped_column(Integer, default=100)
    copago: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    plan: Mapped[Plan] = relationship(back_populates="beneficios")


class CambioPlan(Base, UUIDMixin, TimestampMixin):
    """F1-PLA-02 / F1-PLA-03 Registro de cada cambio de plan o de cupo y su efecto en el valor."""

    __tablename__ = "cambios_plan"
    __checks__ = {
        "valores_no_negativos": "valor_anterior >= 0 AND valor_nuevo >= 0",
    }

    contrato_id: Mapped[UUID] = mapped_column(ForeignKey("contratos.id"), index=True)
    tipo: Mapped[str] = mapped_column(
        EnumDb(TipoCambioPlan)
    )  # cambio_plan | mascota_alta | mascota_baja
    plan_anterior_id: Mapped[UUID | None] = mapped_column(ForeignKey("planes.id"), index=True)
    plan_nuevo_id: Mapped[UUID | None] = mapped_column(ForeignKey("planes.id"), index=True)
    valor_anterior: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    valor_nuevo: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    ajuste: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)  # + cobro, - credito
    modo: Mapped[str | None] = mapped_column(EnumDb(ModoCambioPlan))
    regla_codigo: Mapped[str | None] = mapped_column(
        String(60), ForeignKey("reglas.codigo", onupdate="CASCADE"), index=True
    )
    fecha_efectiva: Mapped[date] = mapped_column(Date)
    aplicado: Mapped[bool] = mapped_column(Boolean, default=True)
    registrado_por_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id"), index=True)
