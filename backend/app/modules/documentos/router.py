from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.api.deps import INTERNOS, DbSession, Interno, requiere
from app.core.enums import CategoriaDocumento
from app.modules.archivos import service as archivos
from app.modules.documentos import service
from app.modules.documentos.service import DocumentoIn, DocumentoRead, DocumentoUpdate
from app.modules.familias import service as familias

router = APIRouter(tags=["documentos"])
EQUIPO = Depends(requiere(*INTERNOS))


@router.get(
    "/familias/{familia_id}/documentos", response_model=list[DocumentoRead], dependencies=[EQUIPO]
)
async def listar(db: DbSession, familia_id: UUID, mascota_id: UUID | None = None) -> Any:
    """6.1 Todos los documentos de la familia: los subidos, sus contratos, sus carnets y los
    adjuntos y formulas de su historia clinica."""
    familia = await db.run_sync(familias.obtener, familia_id)
    return await db.run_sync(lambda s: service.listar(s, familia, mascota_id=mascota_id))


@router.post(
    "/familias/{familia_id}/documentos",
    response_model=DocumentoRead,
    status_code=status.HTTP_201_CREATED,
)
async def subir(
    db: DbSession,
    usuario: Interno,
    familia_id: UUID,
    archivo: Annotated[UploadFile, File(description="PDF, JPG, PNG o WEBP de hasta 10 MB")],
    categoria: Annotated[CategoriaDocumento, Form()],
    descripcion: Annotated[str | None, Form(max_length=255)] = None,
    mascota_id: Annotated[UUID | None, Form()] = None,
    visible_familia: Annotated[bool, Form()] = False,
) -> Any:
    familia = await db.run_sync(familias.obtener, familia_id)
    contenido = await archivos.leer(archivo, "documento_familia")
    datos = DocumentoIn(
        categoria=categoria,
        descripcion=descripcion,
        mascota_id=mascota_id,
        visible_familia=visible_familia,
    )
    documento = await db.run_sync(
        service.subir, familia, contenido, archivo.filename, datos, usuario.id
    )
    return await db.run_sync(service.leer, documento)


@router.patch("/documentos/{documento_id}", response_model=DocumentoRead, dependencies=[EQUIPO])
async def actualizar(db: DbSession, documento_id: UUID, data: DocumentoUpdate) -> Any:
    """Categoria, descripcion y si la familia lo ve en su portal."""
    documento = await db.run_sync(service.obtener, documento_id)
    documento = await db.run_sync(service.actualizar, documento, data)
    return await db.run_sync(service.leer, documento)


@router.post(
    "/documentos/{documento_id}/baja",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[EQUIPO],
)
async def dar_de_baja(db: DbSession, documento_id: UUID) -> None:
    """Deja de figurar en la ficha y en el portal; el registro y el fichero se conservan."""
    documento = await db.run_sync(service.obtener, documento_id)
    await db.run_sync(service.dar_de_baja, documento)
