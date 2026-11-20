"""6.16 Segmentacion: filtros combinables (todos deben cumplirse) sobre familias.

Las bajas nunca entran a un segmento. Los filtros vacios no restringen.
"""

from datetime import date, datetime, time, timedelta
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import Select, and_, exists, func, or_, select
from sqlalchemy.orm import Session

from app.core.enums import (
    EstadoAfiliacion,
    EstadoEventoPreventivo,
    EstadoServicio,
    TipoPreventivo,
)
from app.core.tiempo import ZONA_NEGOCIO, hoy
from app.modules.cartera.models import AfiliacionMascota, Contrato, Cuota, EstadoCuota
from app.modules.cartera.periodos import sumar_meses
from app.modules.familias.models import Familia, Mascota
from app.modules.planes.models import Plan
from app.modules.preventivos.models import EventoPreventivo
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
    # 6.16 Zona: el barrio de la familia, sin distinguir mayusculas ni espacios de mas.
    barrios: list[str] = Field(default=[], max_length=50)
    # 6.16 Edad: tiene al menos una mascota activa con esa edad, en anos cumplidos.
    edad_min_anios: int | None = Field(default=None, ge=0, le=40)
    edad_max_anios: int | None = Field(default=None, ge=0, le=40)
    # 6.16 Condiciones preventivas (6.18 campanas preventivas): alguna mascota activa con un
    # preventivo programado ya vencido, o que vence dentro de N dias; de esos tipos, si se dicen.
    preventivo_vencido: bool = False
    preventivo_en_dias: int | None = Field(default=None, ge=1, le=365)
    tipos_preventivo: list[TipoPreventivo] = []


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
        # Cada peludo tiene su plan: entra la familia con alguno en esos planes.
        stmt = stmt.where(
            exists().where(
                contrato_vigente,
                AfiliacionMascota.contrato_id == Contrato.id,
                AfiliacionMascota.activa.is_(True),
                AfiliacionMascota.plan_id == Plan.id,
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
    if filtros.barrios:
        barrios = [b.strip().lower() for b in filtros.barrios if b.strip()]
        stmt = stmt.where(func.lower(func.btrim(Familia.barrio)).in_(barrios))
    if filtros.edad_min_anios is not None or filtros.edad_max_anios is not None:
        edad = [mascota_activa, Mascota.fecha_nacimiento.is_not(None)]
        if filtros.edad_min_anios is not None:
            # Cumplio N anos: nacio hace N anos o antes.
            edad.append(Mascota.fecha_nacimiento <= sumar_meses(dia, -12 * filtros.edad_min_anios))
        if filtros.edad_max_anios is not None:
            # Aun no cumple N + 1.
            edad.append(
                Mascota.fecha_nacimiento > sumar_meses(dia, -12 * (filtros.edad_max_anios + 1))
            )
        stmt = stmt.where(exists().where(*edad))
    if filtros.preventivo_vencido or filtros.preventivo_en_dias:
        programado = [
            mascota_activa,
            EventoPreventivo.mascota_id == Mascota.id,
            EventoPreventivo.estado == EstadoEventoPreventivo.PROGRAMADO,
        ]
        if filtros.tipos_preventivo:
            programado.append(EventoPreventivo.tipo.in_(filtros.tipos_preventivo))
        cuando = []
        if filtros.preventivo_vencido:
            cuando.append(EventoPreventivo.fecha_programada < dia)
        if filtros.preventivo_en_dias:
            cuando.append(
                EventoPreventivo.fecha_programada.between(
                    dia, dia + timedelta(days=filtros.preventivo_en_dias)
                )
            )
        stmt = stmt.where(exists().where(*programado, or_(*cuando)))
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
