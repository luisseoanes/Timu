from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, File, UploadFile, status
from pydantic import BaseModel

from app.core.deps import INTERNOS, TODOS, AlcanceActual, DbSession, Interno, publico, requiere
from app.core.enums import EstadoAfiliacion, Rol
from app.core.errores import ReglaNegocio
from app.modules.archivos import service as archivos
from app.modules.familias import service
from app.modules.familias.models import Familia, Mascota
from app.modules.familias.schemas import (
    Baja,
    CambioHistorial,
    FamiliaCreate,
    FamiliaRead,
    FamiliaUpdate,
    FormularioFamilia,
    MascotaCreate,
    MascotaRead,
    MascotaUpdate,
)
from app.schemas.common import Mensaje, Page, ParamsListado, paginar

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/familias", tags=["familias"])
mascotas_router = APIRouter(prefix="/mascotas", tags=["familias"])
formularios_router = APIRouter(prefix="/formularios", tags=["formularios"])

EQUIPO = Depends(requiere(*INTERNOS))
# Lectura: tambien el portal, acotado por el alcance a su propia familia.
LECTURA = Depends(requiere(*TODOS))
GESTION_ESTADO = Depends(requiere(Rol.ADMIN, Rol.COMERCIAL))


class CambioEstado(BaseModel):
    estado: EstadoAfiliacion
    motivo: str | None = None


@router.get("", response_model=Page[FamiliaRead], dependencies=[LECTURA])
async def listar_familias(
    db: DbSession,
    alcance: AlcanceActual,
    params: ParamsListado,
    q: str | None = None,
    ciudad: str | None = None,
    estado: EstadoAfiliacion | None = None,
    incluir_bajas: bool = False,
) -> Page[FamiliaRead]:
    return await paginar(
        db,
        service.consulta_listado(
            alcance, q=q, ciudad=ciudad, estado=estado, incluir_bajas=incluir_bajas
        ),
        params,
        FamiliaRead,
        campos_orden=service.ORDEN,
        orden_por_defecto="-created_at",
        desempate=Familia.id,
    )


@router.post(
    "", response_model=FamiliaRead, status_code=status.HTTP_201_CREATED, dependencies=[EQUIPO]
)
async def crear_familia(db: DbSession, data: FamiliaCreate) -> Familia:
    return await db.run_sync(service.crear, data)


@router.get("/{familia_id}", response_model=FamiliaRead, dependencies=[LECTURA])
async def obtener_familia(db: DbSession, alcance: AlcanceActual, familia_id: UUID) -> Familia:
    """Para el portal, una familia ajena da 404 y no 403: distinguirlos confirmaria que
    el recurso existe."""
    return await db.run_sync(service.obtener, familia_id, alcance)


@router.patch("/{familia_id}", response_model=FamiliaRead, dependencies=[EQUIPO])
async def actualizar_familia(db: DbSession, familia_id: UUID, data: FamiliaUpdate) -> Familia:
    familia = await db.run_sync(service.obtener, familia_id)
    if familia.dada_de_baja_en is not None:
        raise ReglaNegocio("La familia esta dada de baja")
    return await db.run_sync(service.actualizar, familia, data)


@router.post("/{familia_id}/estado", response_model=FamiliaRead, dependencies=[GESTION_ESTADO])
async def cambiar_estado(db: DbSession, familia_id: UUID, data: CambioEstado) -> Familia:
    """6.23 Cambio manual de estado de afiliacion (queda en el historial)."""
    familia = await db.run_sync(service.obtener, familia_id)
    return await db.run_sync(service.cambiar_estado, familia, data.estado, data.motivo)


@router.post("/{familia_id}/baja", response_model=FamiliaRead, dependencies=[GESTION_ESTADO])
async def dar_de_baja(db: DbSession, familia_id: UUID, data: Baja) -> Familia:
    """F1-FAM-01 Baja logica: se conserva toda la informacion y su historial."""
    familia = await db.run_sync(service.obtener, familia_id)
    return await db.run_sync(service.dar_de_baja, familia, data.motivo)


@router.post(
    "/{familia_id}/acceso-portal", response_model=FamiliaRead, dependencies=[GESTION_ESTADO]
)
async def habilitar_portal(db: DbSession, familia_id: UUID) -> Familia:
    """F1-AUT-04 Crea el usuario de portal de la familia y le envia el enlace de activacion."""
    familia = await db.run_sync(service.obtener, familia_id)
    return await db.run_sync(service.habilitar_portal, familia)


@router.get("/{familia_id}/historial", response_model=list[CambioHistorial], dependencies=[EQUIPO])
async def historial(
    db: DbSession, familia_id: UUID, solo_estado: bool = False
) -> list[CambioHistorial]:
    await db.run_sync(service.obtener, familia_id)
    return [
        CambioHistorial(
            fecha=r.created_at, accion=r.accion, usuario_id=r.usuario_id, cambios=r.cambios
        )
        for r in await db.run_sync(service.historial, familia_id, solo_estado)
    ]


@router.post(
    "/{familia_id}/mascotas",
    response_model=MascotaRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[EQUIPO],
)
async def agregar_mascota(db: DbSession, familia_id: UUID, data: MascotaCreate) -> Mascota:
    familia = await db.run_sync(service.obtener, familia_id)
    return await db.run_sync(service.agregar_mascota, familia, data)


# --- Mascotas (F1-FAM-02) ---------------------------------------------------------------------


@mascotas_router.get("/{mascota_id}", response_model=MascotaRead, dependencies=[EQUIPO])
async def obtener_mascota(db: DbSession, mascota_id: UUID) -> MascotaRead:
    return await db.run_sync(
        service.mascota_read, await db.run_sync(service.obtener_mascota, mascota_id)
    )


@mascotas_router.patch("/{mascota_id}", response_model=MascotaRead, dependencies=[EQUIPO])
async def actualizar_mascota(db: DbSession, mascota_id: UUID, data: MascotaUpdate) -> MascotaRead:
    mascota = await db.run_sync(service.obtener_mascota, mascota_id)
    return await db.run_sync(
        service.mascota_read, await db.run_sync(service.actualizar_mascota, mascota, data)
    )


@mascotas_router.post("/{mascota_id}/baja", response_model=MascotaRead, dependencies=[EQUIPO])
async def dar_de_baja_mascota(db: DbSession, mascota_id: UUID, data: Baja) -> MascotaRead:
    mascota = await db.run_sync(service.obtener_mascota, mascota_id)
    return await db.run_sync(
        service.mascota_read, await db.run_sync(service.dar_de_baja_mascota, mascota, data.motivo)
    )


@mascotas_router.put("/{mascota_id}/foto", response_model=MascotaRead)
async def subir_foto(
    db: DbSession,
    usuario: Interno,
    mascota_id: UUID,
    foto: Annotated[UploadFile, File(description="JPG, PNG o WEBP de hasta 5 MB")],
) -> MascotaRead:
    mascota = await db.run_sync(service.obtener_mascota, mascota_id)
    contenido = await archivos.leer(foto, "foto_mascota")
    mascota = await db.run_sync(service.subir_foto, mascota, contenido, foto.filename, usuario.id)
    return await db.run_sync(service.mascota_read, mascota)


# --- Formularios publicos (F1-FAM-03) ---------------------------------------------------------


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
        resultado = await db.run_sync(service.desde_formulario, data)
        logger.info("Formulario de familia procesado: %s", resultado.model_dump(mode="json"))
    return Mensaje(detail="Recibimos tus datos; te contactaremos pronto")
