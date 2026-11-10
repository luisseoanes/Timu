"""F1-AFI Afiliacion en linea y asistida."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Literal
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from app.api.deps import INTERNOS, DbSession, publico, requiere
from app.core.enums import Rol
from app.core.errores import ReglaNegocio
from app.modules.afiliaciones import ciclo, service
from app.modules.afiliaciones.models import SolicitudAfiliacion
from app.modules.auth.models import Usuario
from app.modules.familias import service as familias
from app.modules.familias.models import Familia, Mascota
from app.modules.familias.schemas import (
    Baja,
    FamiliaRead,
    FormularioFamilia,
    MascotaAlta,
    MascotaRead,
)
from app.modules.planes import service as planes
from app.schemas.common import Mensaje

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/afiliaciones", tags=["afiliaciones"])
# Rutas de la ficha que cruzan con el contrato (ciclo.py): misma ruta y etiqueta que el resto
# de las de familias, para que el panel y el OpenAPI no distingan donde viven.
familias_router = APIRouter(prefix="/familias", tags=["familias"])
mascotas_router = APIRouter(prefix="/mascotas", tags=["familias"])
formularios_router = APIRouter(prefix="/formularios", tags=["formularios"])
GESTION_ESTADO = Depends(requiere(Rol.ADMIN, Rol.COMERCIAL))

Comercial = Annotated[Usuario, Depends(requiere(Rol.ADMIN, Rol.COMERCIAL))]
EQUIPO = Depends(requiere(*INTERNOS))


class FormularioAfiliacion(FormularioFamilia):
    plan_codigo: str
    acepta_condiciones: bool = Field(description="Debe ser true: aceptacion expresa")
    acepta_tratamiento_datos: bool


class AfiliacionAsistida(BaseModel):
    familia_id: UUID
    plan_id: UUID
    medio_aceptacion: Literal["presencial", "whatsapp", "llamada"]
    detalle_aceptacion: str | None = Field(default=None, description="Quien, como, soporte")


class PagoManualAfiliacion(BaseModel):
    medio: Literal["efectivo", "transferencia", "consignacion", "datafono"]
    comprobante: str = Field(min_length=3, max_length=120)


class InicioAfiliacion(BaseModel):
    solicitud_id: UUID
    valor: Decimal
    enlace_pago: str


class SolicitudRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    familia_id: UUID
    plan_id: UUID
    valor_inicial: Decimal
    referencia_pago: str
    estado: str
    origen: str
    contrato_id: UUID | None
    aceptacion: dict[str, Any]
    completada_en: datetime | None
    error: str | None
    created_at: datetime


@router.post(
    "",
    response_model=InicioAfiliacion,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(publico)],
)
async def afiliacion_en_linea(
    db: DbSession, request: Request, data: FormularioAfiliacion
) -> InicioAfiliacion:
    """F1-AFI-01 Formulario publico: crea o completa el perfil (sin redigitar) y devuelve el
    enlace de pago. El pago aprobado completa la afiliacion sola."""
    if not (data.acepta_condiciones and data.acepta_tratamiento_datos):
        raise ReglaNegocio("Debe aceptar las condiciones y el tratamiento de datos")
    if data.sitio_web:
        raise ReglaNegocio("Solicitud rechazada")
    plan = await db.run_sync(planes.por_codigo, data.plan_codigo)
    formulario = data.model_dump(
        exclude={"plan_codigo", "acepta_condiciones", "acepta_tratamiento_datos", "origen"}
    )
    resultado = await db.run_sync(
        ciclo.recibir_formulario, FormularioFamilia(**formulario, origen="afiliacion")
    )
    familia = await db.run_sync(familias.obtener, resultado.familia_id)
    await db.refresh(familia, ["mascotas"])
    solicitud, enlace = await db.run_sync(
        service.iniciar,
        familia=familia,
        plan=plan,
        origen="formulario",
        aceptacion={
            "medio": "formulario_web",
            "ip": request.client.host if request.client else None,
            "agente": request.headers.get("user-agent", "")[:255],
            "tratamiento_datos": True,
        },
    )
    return InicioAfiliacion(
        solicitud_id=solicitud.id, valor=solicitud.valor_inicial, enlace_pago=enlace
    )


@router.post("/asistida", response_model=InicioAfiliacion, status_code=status.HTTP_201_CREATED)
async def afiliacion_asistida(
    db: DbSession, usuario: Comercial, data: AfiliacionAsistida
) -> InicioAfiliacion:
    """Comercial afilia a una familia ya registrada; la aceptacion queda con su medio."""
    familia = await db.run_sync(familias.obtener, data.familia_id)
    plan = await db.run_sync(planes.obtener, data.plan_id)
    solicitud, enlace = await db.run_sync(
        service.iniciar,
        familia=familia,
        plan=plan,
        origen="asistida",
        aceptacion={
            "medio": data.medio_aceptacion,
            "detalle": data.detalle_aceptacion,
            "registrada_por": str(usuario.id),
        },
    )
    return InicioAfiliacion(
        solicitud_id=solicitud.id, valor=solicitud.valor_inicial, enlace_pago=enlace
    )


@router.get("", response_model=list[SolicitudRead], dependencies=[EQUIPO])
async def listar(
    db: DbSession, estado: str | None = None, familia_id: UUID | None = None
) -> list[SolicitudAfiliacion]:
    stmt = select(SolicitudAfiliacion).order_by(SolicitudAfiliacion.created_at.desc()).limit(200)
    if estado:
        stmt = stmt.where(SolicitudAfiliacion.estado == estado)
    if familia_id:
        stmt = stmt.where(SolicitudAfiliacion.familia_id == familia_id)
    return list(await db.scalars(stmt))


@router.get("/{solicitud_id}", response_model=SolicitudRead, dependencies=[EQUIPO])
async def obtener(db: DbSession, solicitud_id: UUID) -> SolicitudAfiliacion:
    return await db.run_sync(service.obtener, solicitud_id)


@router.post("/{solicitud_id}/pago-manual", response_model=SolicitudRead)
async def pago_manual(
    db: DbSession, usuario: Comercial, solicitud_id: UUID, data: PagoManualAfiliacion
) -> SolicitudAfiliacion:
    """Pago recibido fuera de la pasarela: completa la afiliacion igual que el webhook."""
    solicitud = await db.run_sync(service.obtener, solicitud_id)
    return await db.run_sync(
        service.registrar_pago_manual,
        solicitud,
        medio=data.medio,
        comprobante=data.comprobante,
        usuario_id=usuario.id,
    )


# --- Ciclo de vida de la familia afiliada (ciclo.py) ------------------------------------------


@familias_router.post(
    "/{familia_id}/baja", response_model=FamiliaRead, dependencies=[GESTION_ESTADO]
)
async def dar_de_baja(db: DbSession, familia_id: UUID, data: Baja) -> Familia:
    """F1-FAM-01 Baja logica: se conserva toda la informacion y su historial."""
    familia = await db.run_sync(familias.obtener, familia_id)
    return await db.run_sync(ciclo.dar_de_baja, familia, data.motivo)


@familias_router.post(
    "/{familia_id}/anonimizar",
    response_model=FamiliaRead,
    dependencies=[Depends(requiere(Rol.ADMIN))],
)
async def anonimizar(db: DbSession, familia_id: UUID) -> Familia:
    """Habeas data (Ley 1581): sustituye los datos personales de la familia. No se deshace."""
    familia = await db.run_sync(familias.obtener, familia_id)
    return await db.run_sync(ciclo.anonimizar, familia)


@familias_router.post(
    "/{familia_id}/mascotas",
    response_model=MascotaRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[EQUIPO],
)
async def agregar_mascota(db: DbSession, familia_id: UUID, data: MascotaAlta) -> Mascota:
    familia = await db.run_sync(familias.obtener, familia_id)
    return await db.run_sync(ciclo.agregar_mascota, familia, data)


@mascotas_router.post("/{mascota_id}/baja", response_model=MascotaRead, dependencies=[EQUIPO])
async def dar_de_baja_mascota(db: DbSession, mascota_id: UUID, data: Baja) -> MascotaRead:
    mascota = await db.run_sync(familias.obtener_mascota, mascota_id)
    return await db.run_sync(
        familias.mascota_read, await db.run_sync(ciclo.dar_de_baja_mascota, mascota, data.motivo)
    )


@formularios_router.post(
    "/familia",
    response_model=Mensaje,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(publico)],
)
async def formulario_familia(db: DbSession, data: FormularioFamilia) -> Mensaje:
    """Autollenado del perfil desde un formulario publico, sin redigitacion.

    La respuesta es la misma si la familia es nueva o ya existia: un formulario publico no
    puede servir para averiguar quien esta afiliado.
    """
    if not data.sitio_web:
        resultado = await db.run_sync(ciclo.recibir_formulario, data)
        logger.info("Formulario de familia procesado: %s", resultado.model_dump(mode="json"))
    return Mensaje(detail="Recibimos tus datos; te contactaremos pronto")
