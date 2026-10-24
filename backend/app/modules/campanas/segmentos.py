"""F3-SEG-01 Segmentacion: filtros combinables (todos deben cumplirse) sobre familias.

Las bajas nunca entran a un segmento. Los filtros vacios no restringen.
"""

from datetime import date, datetime, time, timedelta
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import Select, and_, exists, func, select
from sqlalchemy.orm import Session

from app.core.enums import EstadoAfiliacion, EstadoServicio
from app.core.tiempo import ZONA_NEGOCIO, hoy
from app.modules.cartera.models import Contrato, Cuota, EstadoCuota
from app.modules.familias.models import Familia, Mascota
from app.modules.planes.models import Plan
from app.modules.servicios.models import Servicio

VIGENTES = (EstadoAfiliacion.ACTIVA, EstadoAfiliacion.EN_MORA, EstadoAfiliacion.CONGELADA)


class FiltrosSegmento(BaseModel):
    ciudades: list[str] = []
    estados: list[EstadoAfiliacion] = []
    planes: list[str] = Field(default=[], description="Codigos de plan del contrato vigente")
    especies: list[str] = Field(default=[], description="Tiene al menos una mascota activa de")
    origenes: list[str] = []
    dias_mora_min: int | None = Field(default=None, ge=1)
    sin_servicio_dias: int | None = Field(
        default=None, ge=1, description="Sin servicios completados en los ultimos N dias"
    )
    mascotas_min: int | None = Field(default=None, ge=1)
    afiliada_desde: date | None = None
    afiliada_hasta: date | None = None
    renovacion_en_dias: int | None = Field(
        default=None, ge=0, description="El contrato vence dentro de N dias"
    )


def consulta(filtros: FiltrosSegmento, dia: date | None = None) -> Select[Any]:
    """SELECT de las familias que cumplen todos los filtros."""
    dia = dia or hoy()
    stmt = select(Familia).where(Familia.dada_de_baja_en.is_(None))
    if filtros.ciudades:
        stmt = stmt.where(Familia.ciudad.in_(filtros.ciudades))
    if filtros.estados:
        stmt = stmt.where(Familia.estado.in_(filtros.estados))
    if filtros.origenes:
        stmt = stmt.where(Familia.origen.in_(filtros.origenes))

    contrato_vigente = and_(Contrato.familia_id == Familia.id, Contrato.estado.in_(VIGENTES))
    if filtros.planes:
        stmt = stmt.where(
            exists().where(
                contrato_vigente,
                Contrato.plan_id == Plan.id,
                Plan.codigo.in_(filtros.planes),
            )
        )
    if filtros.afiliada_desde or filtros.afiliada_hasta:
        condiciones = [contrato_vigente]
        if filtros.afiliada_desde:
            condiciones.append(Contrato.fecha_inicio >= filtros.afiliada_desde)
        if filtros.afiliada_hasta:
            condiciones.append(Contrato.fecha_inicio <= filtros.afiliada_hasta)
        stmt = stmt.where(exists().where(*condiciones))
    if filtros.renovacion_en_dias is not None:
        stmt = stmt.where(
            exists().where(
                contrato_vigente,
                Contrato.fecha_renovacion <= dia + timedelta(days=filtros.renovacion_en_dias),
            )
        )
    if filtros.dias_mora_min:
        stmt = stmt.where(
            exists().where(
                contrato_vigente,
                Cuota.contrato_id == Contrato.id,
                Cuota.estado.in_(EstadoCuota.ABIERTAS),
                Cuota.fecha_vencimiento <= dia - timedelta(days=filtros.dias_mora_min),
            )
        )

    mascota_activa = and_(Mascota.familia_id == Familia.id, Mascota.activa.is_(True))
    if filtros.especies:
        stmt = stmt.where(exists().where(mascota_activa, Mascota.especie.in_(filtros.especies)))
    if filtros.mascotas_min:
        conteo = (
            select(func.count(Mascota.id))
            .where(mascota_activa)
            .correlate(Familia)
            .scalar_subquery()
        )
        stmt = stmt.where(conteo >= filtros.mascotas_min)
    if filtros.sin_servicio_dias:
        desde = datetime.combine(
            dia - timedelta(days=filtros.sin_servicio_dias), time.min, ZONA_NEGOCIO
        )
        stmt = stmt.where(
            ~exists().where(
                Servicio.familia_id == Familia.id,
                Servicio.estado == EstadoServicio.COMPLETADO,
                Servicio.programado_para >= desde,
            )
        )
    return stmt


def contar(db: Session, filtros: FiltrosSegmento) -> int:
    return int(db.scalar(select(func.count()).select_from(consulta(filtros).subquery())) or 0)


def previsualizar(db: Session, filtros: FiltrosSegmento, muestra: int = 20) -> dict[str, Any]:
    stmt = consulta(filtros).order_by(Familia.titular_nombre).limit(muestra)
    return {
        "total": contar(db, filtros),
        "muestra": [
            {"id": f.id, "titular": f.titular_nombre, "ciudad": f.ciudad, "estado": f.estado}
            for f in db.scalars(stmt)
        ],
    }
