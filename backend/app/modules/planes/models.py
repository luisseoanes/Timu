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
from app.core.enums import ColorPlan, ModoCambioPlan, Periodicidad, PeriodoCupo, TipoCambioPlan


class Plan(Base, UUIDMixin, TimestampMixin, Auditable):
    """6.3 Plan de afiliacion. Cada peludo tiene el suyo; su precio sale de `tarifas` (por
    numero de peludos) y `tarifas_periodicidad`, y se vende en las `ciudades` del plan."""

    __tablename__ = "planes"
    __checks__ = {
        "codigo_no_vacio": "btrim(codigo) <> ''",
        "nombre_no_vacio": "btrim(nombre) <> ''",
        "terminos_https": "terminos_url IS NULL OR terminos_url ~ '^https://'",
    }

    codigo: Mapped[str] = mapped_column(String(40), unique=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True)
    descripcion: Mapped[str | None] = mapped_column(Text)
    especies: Mapped[list[str]] = mapped_column(JSONTipo, default=list)  # vacio = todas
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    color: Mapped[ColorPlan] = mapped_column(EnumDb(ColorPlan), default=ColorPlan.VERDE)
    # Las condiciones que el registro dice de frente (R3-PUB-02, manual de marca: «exclusiones y
    # carencias, de frente»). Las escribe TIMU; mientras no lo haga, valores provisionales.
    carencia: Mapped[str | None] = mapped_column(Text)
    exclusiones: Mapped[str | None] = mapped_column(Text)
    terminos_url: Mapped[str | None] = mapped_column(String(500))

    # Solo los beneficios vigentes. Los reemplazados quedan con activo = False: lo que cubria
    # el plan antes no se borra (fase 3 de docs/registros/plan-persistencia.md).
    beneficios: Mapped[list["Beneficio"]] = relationship(
        back_populates="plan",
        primaryjoin="and_(Plan.id == Beneficio.plan_id, Beneficio.activo.is_(True))",
        cascade="save-update, merge",
        lazy="selectin",
    )
    # R3-PUB-04 Lo que el plan da y no es un tipo de servicio que se agenda (servicio funebre,
    # desparasitante externo, beneficios de terceros), en el orden en que se dicen.
    adicionales: Mapped[list["BeneficioAdicional"]] = relationship(
        primaryjoin=(
            "and_(Plan.id == BeneficioAdicional.plan_id, BeneficioAdicional.activo.is_(True))"
        ),
        order_by="BeneficioAdicional.orden",
        lazy="selectin",
        viewonly=True,
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
    """6.2 Lo que cubre el plan por tipo de servicio. `cupo` vacio = sin tope de usos.
    Lo que la familia lee de el (R3-PUB-04): hasta cuanto cubre por episodio, desde cuantos
    dias de afiliada y el detalle (`detalle`: «el medicamento mas costoso, no superior a...»)."""

    __tablename__ = "beneficios_plan"
    __checks__ = {
        "cupo_no_negativo": "cupo IS NULL OR cupo >= 0",
        "cobertura_rango": "cobertura_pct BETWEEN 0 AND 100",
        "copago_no_negativo": "copago >= 0",
        "tope_positivo": "tope_episodio IS NULL OR tope_episodio > 0",
        "carencia_no_negativa": "carencia_dias IS NULL OR carencia_dias >= 0",
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
    tope_episodio: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    carencia_dias: Mapped[int | None] = mapped_column(Integer)
    detalle: Mapped[str | None] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    plan: Mapped[Plan] = relationship(back_populates="beneficios")


class BeneficioAdicional(Base, UUIDMixin, TimestampMixin, Auditable):
    """R3-PUB-04 Lo que el plan da sin ser un tipo de servicio que se agenda: el servicio
    funebre, el desparasitante externo con entrega, los precios preferenciales de terceros.
    Lo escribe la administracion y lo leen la portada, el registro y el contrato. Como los
    beneficios, se reemplazan marcando los anteriores inactivos: nada se borra."""

    __tablename__ = "beneficios_adicionales_plan"
    __checks__ = {
        "nombre_no_vacio": "btrim(nombre) <> ''",
        "cubre_no_vacio": "btrim(cubre) <> ''",
        "carencia_no_negativa": "carencia_dias IS NULL OR carencia_dias >= 0",
        "orden_no_negativo": "orden >= 0",
    }

    plan_id: Mapped[UUID] = mapped_column(ForeignKey("planes.id", ondelete="CASCADE"), index=True)
    nombre: Mapped[str] = mapped_column(String(160))
    # Lo que cubre, como se dice: «100 %», «30 % de descuento», «Cada 3 meses».
    cubre: Mapped[str] = mapped_column(String(160))
    detalle: Mapped[str | None] = mapped_column(Text)
    carencia_dias: Mapped[int | None] = mapped_column(Integer)
    # Lo presta un tercero con convenio: TIMU no garantiza siempre su disponibilidad.
    tercero: Mapped[bool] = mapped_column(Boolean, default=False)
    orden: Mapped[int] = mapped_column(Integer, default=0)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class CambioPlan(Base, UUIDMixin, TimestampMixin):
    """6.3 Registro de cada cambio de plan de un peludo, alta o retiro de un
    peludo y su efecto en lo que cobra cada cuota (`valor_anterior`, `valor_nuevo`)."""

    __tablename__ = "cambios_plan"
    __checks__ = {
        "valores_no_negativos": "valor_anterior >= 0 AND valor_nuevo >= 0",
    }

    contrato_id: Mapped[UUID] = mapped_column(ForeignKey("contratos.id"), index=True)
    mascota_id: Mapped[UUID | None] = mapped_column(ForeignKey("mascotas.id"), index=True)
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
