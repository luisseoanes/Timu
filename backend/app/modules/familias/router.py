from typing import Annotated, Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from pydantic import BaseModel

from app.api.deps import AlcanceActual, DbSession, requiere
from app.core.enums import EstadoAfiliacion, Rol
from app.core.errores import ReglaNegocio
from app.modules.archivos import service as archivos
from app.modules.auth.models import Usuario
from app.modules.familias import service
from app.modules.familias.models import Familia
from app.modules.familias.schemas import (
    CambioHistorial,
    ContactoIn,
    ContactoRead,
    ContactoUpdate,
    FamiliaAlta,
    FamiliaRead,
    FamiliaUpdate,
    MascotaRead,
    MascotaUpdate,
)
from app.schemas.common import Page, ParamsListado, paginar

logger = structlog.get_logger(__name__)

# La baja, el alta y la baja de mascotas, la anonimizacion y el formulario publico cruzan la
# ficha con el contrato: sus rutas viven en afiliaciones/router.py, que los orquesta.
router = APIRouter(prefix="/familias", tags=["familias"])
mascotas_router = APIRouter(prefix="/mascotas", tags=["familias"])

# Perfiles de cada ruta (Seccion 12, docs/perfiles-y-permisos.md).
ADMIN = Depends(requiere(Rol.ADMIN))
ATENCION = Depends(requiere(Rol.ATENCION_CLIENTE))
Atencion = Annotated[Usuario, Depends(requiere(Rol.ATENCION_CLIENTE))]
# Lectura de la ficha: tambien el portal, acotado por el alcance a su propia familia.
FICHA = Depends(requiere(Rol.COMERCIAL, Rol.ATENCION_CLIENTE, Rol.OPERACIONES, Rol.FAMILIA))
COMERCIAL_Y_ATENCION = Depends(requiere(Rol.COMERCIAL, Rol.ATENCION_CLIENTE))
OPERATIVO = Depends(requiere(Rol.COMERCIAL, Rol.ATENCION_CLIENTE, Rol.OPERACIONES, Rol.MEDICO))


class CambioEstado(BaseModel):
    estado: EstadoAfiliacion
    motivo: str | None = None


@router.get("", response_model=Page[FamiliaRead], dependencies=[FICHA])
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
    "",
    response_model=FamiliaRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[COMERCIAL_Y_ATENCION],
)
async def crear_familia(db: DbSession, data: FamiliaAlta) -> Familia:
    return await db.run_sync(service.crear, data)


class FamiliaParaSuprimir(BaseModel):
    """Lo minimo para confirmar a quien se anonimiza: ni contacto, ni direccion, ni mascotas."""

    id: UUID
    titular_nombre: str
    mascotas: int
    estado: EstadoAfiliacion
    anonimizada: bool
    # Con un contrato vigente la base no la deja anonimizar: Atencion lo cancela antes.
    con_contrato_vigente: bool


# Antes de /{familia_id}: si no, "supresion" se tomaria por el id de una familia.
@router.get("/supresion", response_model=FamiliaParaSuprimir, dependencies=[ADMIN])
async def para_suprimir(
    db: DbSession, documento: str = Query(min_length=3, max_length=20)
) -> FamiliaParaSuprimir:
    """Ley 1581 Supresion de datos: el administrador la hace sin ver la ficha (decidido con el
    usuario el 2026-11-19)."""
    familia = await db.run_sync(service.para_suprimir, documento)
    return FamiliaParaSuprimir(
        id=familia.id,
        titular_nombre=familia.titular_nombre,
        mascotas=len(familia.mascotas),
        estado=familia.estado,
        anonimizada=familia.anonimizada_en is not None,
        con_contrato_vigente=await db.run_sync(service.con_contrato_vigente, familia.id),
    )


@router.get(
    "/{familia_id}",
    response_model=FamiliaRead,
    dependencies=[FICHA],
)
async def obtener_familia(db: DbSession, alcance: AlcanceActual, familia_id: UUID) -> Familia:
    """Para el portal, una familia ajena da 404 y no 403: distinguirlos confirmaria que
    el recurso existe."""
    return await db.run_sync(service.obtener, familia_id, alcance)


@router.patch("/{familia_id}", response_model=FamiliaRead, dependencies=[COMERCIAL_Y_ATENCION])
async def actualizar_familia(db: DbSession, familia_id: UUID, data: FamiliaUpdate) -> Familia:
    familia = await db.run_sync(service.obtener, familia_id)
    if familia.dada_de_baja_en is not None:
        raise ReglaNegocio("La familia esta dada de baja")
    return await db.run_sync(service.actualizar, familia, data)


@router.post("/{familia_id}/estado", response_model=FamiliaRead, dependencies=[ATENCION])
async def cambiar_estado(db: DbSession, familia_id: UUID, data: CambioEstado) -> Familia:
    """6.23 Cambio manual de estado de afiliacion (queda en el historial)."""
    familia = await db.run_sync(service.obtener, familia_id)
    return await db.run_sync(service.cambiar_estado, familia, data.estado, data.motivo)


@router.post("/{familia_id}/acceso-portal", response_model=FamiliaRead, dependencies=[ATENCION])
async def habilitar_portal(db: DbSession, familia_id: UUID) -> Familia:
    """Seccion 14 Crea el usuario de portal de la familia y le envia el enlace de activacion."""
    familia = await db.run_sync(service.obtener, familia_id)
    return await db.run_sync(service.habilitar_portal, familia)


@router.get(
    "/{familia_id}/historial",
    response_model=list[CambioHistorial],
    dependencies=[COMERCIAL_Y_ATENCION],
)
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


# --- Contactos adicionales (6.1): solo consulta, sin acceso ni mensajes ----------------------


@router.post(
    "/{familia_id}/contactos",
    response_model=ContactoRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[ATENCION],
)
async def agregar_contacto(db: DbSession, familia_id: UUID, data: ContactoIn) -> Any:
    familia = await db.run_sync(service.obtener, familia_id)
    return await db.run_sync(service.agregar_contacto, familia, data)


@router.patch(
    "/{familia_id}/contactos/{contacto_id}", response_model=ContactoRead, dependencies=[ATENCION]
)
async def actualizar_contacto(
    db: DbSession, familia_id: UUID, contacto_id: UUID, data: ContactoUpdate
) -> Any:
    familia = await db.run_sync(service.obtener, familia_id)
    contacto = await db.run_sync(service.obtener_contacto, familia, contacto_id)
    return await db.run_sync(service.actualizar_contacto, familia, contacto, data)


@router.post(
    "/{familia_id}/contactos/{contacto_id}/baja",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[ATENCION],
)
async def dar_de_baja_contacto(db: DbSession, familia_id: UUID, contacto_id: UUID) -> None:
    familia = await db.run_sync(service.obtener, familia_id)
    contacto = await db.run_sync(service.obtener_contacto, familia, contacto_id)
    await db.run_sync(service.dar_de_baja_contacto, familia, contacto)


# --- Mascotas (6.1) ---------------------------------------------------------------------


@mascotas_router.get("/{mascota_id}", response_model=MascotaRead, dependencies=[OPERATIVO])
async def obtener_mascota(db: DbSession, mascota_id: UUID) -> MascotaRead:
    return await db.run_sync(
        service.mascota_read, await db.run_sync(service.obtener_mascota, mascota_id)
    )


@mascotas_router.patch("/{mascota_id}", response_model=MascotaRead, dependencies=[ATENCION])
async def actualizar_mascota(db: DbSession, mascota_id: UUID, data: MascotaUpdate) -> MascotaRead:
    mascota = await db.run_sync(service.obtener_mascota, mascota_id)
    return await db.run_sync(
        service.mascota_read, await db.run_sync(service.actualizar_mascota, mascota, data)
    )


@mascotas_router.delete("/{mascota_id}/foto", response_model=MascotaRead, dependencies=[ATENCION])
async def quitar_foto(db: DbSession, mascota_id: UUID) -> MascotaRead:
    mascota = await db.run_sync(service.obtener_mascota, mascota_id)
    mascota = await db.run_sync(service.quitar_foto, mascota)
    return await db.run_sync(service.mascota_read, mascota)


@mascotas_router.put("/{mascota_id}/foto", response_model=MascotaRead)
async def subir_foto(
    db: DbSession,
    usuario: Atencion,
    mascota_id: UUID,
    foto: Annotated[UploadFile, File(description="JPG, PNG o WEBP de hasta 5 MB")],
) -> MascotaRead:
    mascota = await db.run_sync(service.obtener_mascota, mascota_id)
    contenido = await archivos.leer(foto, "foto_mascota")
    mascota = await db.run_sync(service.subir_foto, mascota, contenido, foto.filename, usuario.id)
    return await db.run_sync(service.mascota_read, mascota)
