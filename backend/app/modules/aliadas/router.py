"""6.22 Clinicas aliadas: directorio, convenios, remisiones, acceso de la aliada y
liquidacion."""

import csv
import io
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select

from app.core.deps import INTERNOS, DbSession, requiere
from app.core.enums import Rol
from app.core.errores import Prohibido
from app.modules.aliadas import service
from app.modules.aliadas.models import ClinicaAliada, ConvenioAliada, RemisionAliada
from app.modules.auth.models import Usuario

router = APIRouter(prefix="/aliadas", tags=["aliadas"])

EQUIPO = Depends(requiere(*INTERNOS))
ADMIN = Depends(requiere(Rol.ADMIN))
Emisor = Annotated[
    Usuario, Depends(requiere(Rol.ADMIN, Rol.OPERACIONES, Rol.MEDICO, Rol.COMERCIAL))
]
Aliada = Annotated[Usuario, Depends(requiere(Rol.ALIADA))]


class ClinicaIn(BaseModel):
    nombre: str = Field(min_length=3, max_length=160)
    nit: str | None = Field(default=None, max_length=20)
    ciudad: str
    direccion: str | None = Field(default=None, max_length=255)
    telefono: str | None = Field(default=None, max_length=32)
    email: EmailStr | None = None
    servicios: str | None = None


class ClinicaUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=3, max_length=160)
    direccion: str | None = None
    telefono: str | None = None
    email: EmailStr | None = None
    servicios: str | None = None
    activa: bool | None = None


class ClinicaRead(ClinicaIn):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str | None = None  # type: ignore[assignment]
    activa: bool


class ConvenioIn(BaseModel):
    plan_id: UUID | None = None
    beneficio: str = Field(min_length=3, max_length=160)
    cobertura_pct: int = Field(default=100, ge=0, le=100)
    tarifa: Decimal = Field(gt=0)
    tope_cubierto: Decimal | None = Field(default=None, gt=0)
    vigente_desde: date
    vigente_hasta: date | None = None


class ConvenioRead(ConvenioIn):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinica_id: UUID
    activo: bool


class RemisionIn(BaseModel):
    clinica_id: UUID
    mascota_id: UUID
    motivo: str = Field(min_length=5, max_length=2000)
    convenio_id: UUID | None = None


class RemisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    codigo: str
    clinica_id: UUID
    familia_id: UUID
    mascota_id: UUID
    servicio_id: UUID
    motivo: str
    beneficio_aplicado: str | None
    cobertura_pct: int
    tope_cubierto: Decimal | None
    vence_en: date
    estado: str
    fecha_atencion: date | None
    valor_atencion: Decimal | None
    valor_cubierto: Decimal | None
    created_at: datetime


class AnulacionIn(BaseModel):
    motivo: str = Field(min_length=3, max_length=255)


class AtencionIn(BaseModel):
    fecha: date
    valor_atencion: Decimal = Field(gt=0)
    resumen: str = Field(min_length=5, max_length=4000)


# --- F2-ALI-01 Directorio y convenios ---------------------------------------------------------


@router.get("", response_model=list[ClinicaRead], dependencies=[EQUIPO])
async def listar(
    db: DbSession, ciudad: str | None = None, incluir_inactivas: bool = False
) -> list[ClinicaAliada]:
    stmt = select(ClinicaAliada).order_by(ClinicaAliada.nombre)
    if ciudad:
        stmt = stmt.where(ClinicaAliada.ciudad == ciudad)
    if not incluir_inactivas:
        stmt = stmt.where(ClinicaAliada.activa.is_(True))
    return list(await db.scalars(stmt))


@router.post(
    "", response_model=ClinicaRead, status_code=status.HTTP_201_CREATED, dependencies=[ADMIN]
)
async def crear(db: DbSession, data: ClinicaIn) -> ClinicaAliada:
    from app.modules.catalogos import service as catalogos

    datos = data.model_dump()
    datos["ciudad"] = await db.run_sync(catalogos.ciudad_valida, data.ciudad)
    clinica = ClinicaAliada(**datos)
    db.add(clinica)
    await db.flush()
    return clinica


@router.patch("/{clinica_id}", response_model=ClinicaRead, dependencies=[ADMIN])
async def actualizar(db: DbSession, clinica_id: UUID, data: ClinicaUpdate) -> ClinicaAliada:
    clinica = await db.run_sync(service.obtener_clinica, clinica_id)
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(clinica, campo, valor)
    await db.flush()
    return clinica


@router.get("/{clinica_id}/convenios", response_model=list[ConvenioRead], dependencies=[EQUIPO])
async def convenios(db: DbSession, clinica_id: UUID) -> list[ConvenioAliada]:
    return list(
        await db.scalars(
            select(ConvenioAliada)
            .where(ConvenioAliada.clinica_id == clinica_id)
            .order_by(ConvenioAliada.vigente_desde.desc())
        )
    )


@router.post(
    "/{clinica_id}/convenios",
    response_model=ConvenioRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[ADMIN],
)
async def crear_convenio(db: DbSession, clinica_id: UUID, data: ConvenioIn) -> ConvenioAliada:
    clinica = await db.run_sync(service.obtener_clinica, clinica_id)
    return await db.run_sync(service.crear_convenio, clinica, data.model_dump())


# --- F2-ALI-02 Remisiones ---------------------------------------------------------------------


@router.post("/remisiones", response_model=RemisionRead, status_code=status.HTTP_201_CREATED)
async def emitir(db: DbSession, usuario: Emisor, data: RemisionIn) -> RemisionAliada:
    return await db.run_sync(
        lambda s: service.emitir(
            s,
            clinica_id=data.clinica_id,
            mascota_id=data.mascota_id,
            motivo=data.motivo,
            usuario_id=usuario.id,
            convenio_id=data.convenio_id,
        )
    )


@router.get("/remisiones", response_model=list[RemisionRead], dependencies=[EQUIPO])
async def remisiones(
    db: DbSession,
    clinica_id: UUID | None = None,
    familia_id: UUID | None = None,
    estado: str | None = None,
) -> list[RemisionAliada]:
    stmt = select(RemisionAliada).order_by(RemisionAliada.created_at.desc()).limit(500)
    if clinica_id:
        stmt = stmt.where(RemisionAliada.clinica_id == clinica_id)
    if familia_id:
        stmt = stmt.where(RemisionAliada.familia_id == familia_id)
    if estado:
        stmt = stmt.where(RemisionAliada.estado == estado)
    return list(await db.scalars(stmt))


@router.post("/remisiones/{remision_id}/anulacion", response_model=RemisionRead)
async def anular(
    db: DbSession, usuario: Emisor, remision_id: UUID, data: AnulacionIn
) -> RemisionAliada:
    remision = await db.run_sync(service.obtener_remision, remision_id)
    return await db.run_sync(service.anular, remision, data.motivo, usuario.id)


# --- F2-ALI-03 Acceso de la clinica aliada ----------------------------------------------------


def _clinica(usuario: Usuario) -> UUID:
    if usuario.clinica_aliada_id is None:
        raise Prohibido("El usuario no esta asociado a una clinica aliada")
    return usuario.clinica_aliada_id


@router.get("/mi-clinica/remisiones/{codigo}")
async def validar_remision(db: DbSession, usuario: Aliada, codigo: str) -> dict[str, Any]:
    """La aliada valida el beneficio con el codigo que presenta la familia."""
    return await db.run_sync(service.vista_aliada, codigo, _clinica(usuario))


@router.post("/mi-clinica/remisiones/{codigo}/atencion")
async def reportar_atencion(
    db: DbSession, usuario: Aliada, codigo: str, data: AtencionIn
) -> dict[str, Any]:
    clinica_id = _clinica(usuario)
    await db.run_sync(
        lambda s: service.reportar_atencion(
            s,
            codigo,
            clinica_id,
            fecha=data.fecha,
            valor_atencion=data.valor_atencion,
            resumen=data.resumen,
            usuario_id=usuario.id,
        )
    )
    return await db.run_sync(service.vista_aliada, codigo, clinica_id)


# --- F2-ALI-04 Liquidacion --------------------------------------------------------------------


@router.get("/liquidacion", dependencies=[ADMIN], response_model=None)
async def liquidacion(
    db: DbSession,
    desde: date,
    hasta: date,
    clinica_id: UUID | None = None,
    formato: str = "json",
) -> list[dict[str, Any]] | Response:
    filas = await db.run_sync(service.liquidacion, desde, hasta, clinica_id)
    if formato != "csv":
        return filas
    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(
        [
            "clinica",
            "nit",
            "codigo",
            "fecha_atencion",
            "beneficio",
            "valor_atencion",
            "valor_cubierto",
        ]
    )
    for fila in filas:
        for d in fila["detalle"]:
            escritor.writerow(
                [
                    fila["clinica"],
                    fila["nit"] or "",
                    d["codigo"],
                    d["fecha_atencion"],
                    d["beneficio"],
                    d["valor_atencion"],
                    d["valor_cubierto"],
                ]
            )
        escritor.writerow(
            [
                fila["clinica"],
                fila["nit"] or "",
                "TOTAL",
                "",
                f"{fila['atenciones']} atenciones",
                fila["valor_atenciones"],
                fila["saldo_a_pagar"],
            ]
        )
    return Response(
        salida.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="liquidacion-{desde}-{hasta}.csv"'},
    )
