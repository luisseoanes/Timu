"""6.14 / 6.17 Historia clinica, adjuntos, formulas y atencion veterinaria virtual.

F2-CLI-05 Solo el personal medico escribe. Para leer, cada perfil recibe su vista: el
medico y el admin la historia completa; comercial y operaciones un resumen (cuando, por
que, quien); la familia, desde el portal, todo menos lo de uso interno.
"""

from datetime import date, datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field

from app.core.deps import INTERNOS, DbSession, requiere
from app.core.enums import Rol
from app.modules.archivos import service as archivos
from app.modules.archivos.models import Archivo
from app.modules.auth.models import Usuario
from app.modules.clinica import service
from app.modules.clinica.models import (
    AdjuntoClinico,
    PlantillaConsulta,
    RespuestaVirtual,
    SolicitudVirtual,
)

router = APIRouter(prefix="/clinica", tags=["clinica"])

Equipo = Annotated[Usuario, Depends(requiere(*INTERNOS))]
Medico = Annotated[Usuario, Depends(requiere(Rol.MEDICO))]
GESTION = Depends(requiere(Rol.MEDICO, Rol.ADMIN))
ADMIN = Depends(requiere(Rol.ADMIN))
EQUIPO = Depends(requiere(*INTERNOS))


class EntradaIn(BaseModel):
    mascota_id: UUID
    servicio_id: UUID | None = None
    plantilla_codigo: str | None = None
    tipo: Literal["presencial", "domiciliaria"] = "presencial"
    fecha: date | None = None
    motivo: str | None = Field(default=None, max_length=4000)
    anamnesis: str | None = None
    examen_fisico: str | None = None
    diagnostico: str | None = None
    tratamiento: str | None = None
    notas_internas: str | None = None


class EntradaUpdate(BaseModel):
    fecha: date | None = None
    motivo: str | None = Field(default=None, max_length=4000)
    anamnesis: str | None = None
    examen_fisico: str | None = None
    diagnostico: str | None = None
    tratamiento: str | None = None
    notas_internas: str | None = None


class AdjuntoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    historia_id: UUID
    nombre_archivo: str
    content_type: str | None
    descripcion: str | None
    created_at: datetime


class ItemFormula(BaseModel):
    medicamento: str = Field(min_length=2, max_length=160)
    presentacion: str | None = Field(default=None, max_length=120)
    dosis: str | None = Field(default=None, max_length=60)
    frecuencia: str | None = Field(default=None, max_length=60)
    duracion: str | None = Field(default=None, max_length=60)
    indicaciones: str | None = Field(default=None, max_length=500)


class FormulaIn(BaseModel):
    items: list[ItemFormula] = Field(min_length=1, max_length=20)
    indicaciones: str | None = Field(default=None, max_length=2000)


class FormulaRead(BaseModel):
    id: UUID
    url: str


class PlantillaIn(BaseModel):
    codigo: str = Field(pattern=r"^[a-z0-9_]{3,40}$")
    nombre: str = Field(min_length=3, max_length=120)
    tipo_servicio_codigo: str | None = None
    campos: dict[Literal[service.CAMPOS_CLINICOS], str] = {}  # type: ignore[valid-type]


class PlantillaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    codigo: str
    nombre: str
    tipo_servicio_codigo: str | None
    campos: dict[str, str]
    activa: bool


class RespuestaIn(BaseModel):
    codigo: str = Field(pattern=r"^[a-z0-9_]{3,40}$")
    titulo: str = Field(min_length=3, max_length=160)
    cuerpo: str = Field(min_length=10, max_length=4000)
    variables: list[str] = []


class RespuestaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    codigo: str
    titulo: str
    cuerpo: str
    variables: list[str]
    estado: str


class SolicitudIn(BaseModel):
    mascota_id: UUID
    motivo: str = Field(min_length=5, max_length=4000)
    canal: Literal["panel", "whatsapp", "portal"] = "panel"
    prioridad: Literal["alta", "media", "baja"] = "media"


class SolicitudRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    familia_id: UUID
    mascota_id: UUID
    canal: str
    motivo: str
    estado: str
    prioridad: str
    asignada_a_id: UUID | None
    respuesta: str | None
    historia_id: UUID | None
    created_at: datetime


class ResponderIn(BaseModel):
    respuesta_codigo: str
    variables: list[str] = []
    diagnostico: str | None = None
    notas_internas: str | None = None


# --- F2-CLI-01 / 05 Historia -------------------------------------------------------------------


@router.get("/mascotas/{mascota_id}/historia")
async def historia(
    db: DbSession, usuario: Equipo, mascota_id: UUID, incluir_corregidas: bool = False
) -> list[dict[str, Any]]:
    vista = service.vista_para(usuario.rol)
    return await db.run_sync(
        lambda s: [
            service.presentar(e, vista)
            for e in service.historia(s, mascota_id, incluir_corregidas=incluir_corregidas)
        ]
    )


@router.post("/historias", status_code=status.HTTP_201_CREATED)
async def crear_entrada(db: DbSession, medico: Medico, data: EntradaIn) -> dict[str, Any]:
    datos = data.model_dump(exclude={"mascota_id", "servicio_id", "plantilla_codigo", "tipo"})
    return await db.run_sync(
        lambda s: service.presentar(
            service.crear_entrada(
                s,
                data.mascota_id,
                datos,
                medico.id,
                servicio_id=data.servicio_id,
                plantilla_codigo=data.plantilla_codigo,
                tipo=data.tipo,
            ),
            "completa",
        )
    )


@router.get("/historias/{historia_id}")
async def obtener(db: DbSession, usuario: Equipo, historia_id: UUID) -> dict[str, Any]:
    vista = service.vista_para(usuario.rol)
    return await db.run_sync(lambda s: service.presentar(service.obtener(s, historia_id), vista))


@router.patch("/historias/{historia_id}")
async def editar(
    db: DbSession, medico: Medico, historia_id: UUID, data: EntradaUpdate
) -> dict[str, Any]:
    cambios = data.model_dump(exclude_unset=True)
    return await db.run_sync(
        lambda s: service.presentar(
            service.editar(s, service.obtener(s, historia_id), cambios, medico.id), "completa"
        )
    )


@router.post("/historias/{historia_id}/firma")
async def firmar(db: DbSession, medico: Medico, historia_id: UUID) -> dict[str, Any]:
    # Se presenta dentro de la sesion: tras el flush, updated_at queda por recargar.
    return await db.run_sync(
        lambda s: service.presentar(
            service.firmar(s, service.obtener(s, historia_id), medico.id), "completa"
        )
    )


@router.post("/historias/{historia_id}/correccion", status_code=status.HTTP_201_CREATED)
async def corregir(
    db: DbSession, medico: Medico, historia_id: UUID, data: EntradaUpdate
) -> dict[str, Any]:
    """Una entrada firmada no se edita: la correccion es una version nueva en borrador."""
    cambios = data.model_dump(exclude_unset=True)
    return await db.run_sync(
        lambda s: service.presentar(
            service.corregir(s, service.obtener(s, historia_id), cambios, medico.id), "completa"
        )
    )


# --- F2-CLI-02 Adjuntos --------------------------------------------------------------------------


@router.post(
    "/historias/{historia_id}/adjuntos",
    response_model=AdjuntoRead,
    status_code=status.HTTP_201_CREATED,
)
async def adjuntar(
    db: DbSession,
    medico: Medico,
    historia_id: UUID,
    archivo: Annotated[UploadFile, File(description="Examen o imagen: JPG, PNG, WEBP o PDF")],
    descripcion: Annotated[str | None, Form(max_length=255)] = None,
) -> AdjuntoClinico:
    entrada = await db.run_sync(service.obtener, historia_id)
    contenido = await archivos.leer(archivo, "adjunto_clinico")
    return await db.run_sync(
        lambda s: service.adjuntar(
            s,
            entrada,
            contenido,
            nombre=archivo.filename,
            descripcion=descripcion,
            usuario_id=medico.id,
        )
    )


@router.get(
    "/historias/{historia_id}/adjuntos", response_model=list[AdjuntoRead], dependencies=[EQUIPO]
)
async def listar_adjuntos(db: DbSession, historia_id: UUID) -> list[AdjuntoClinico]:
    return await db.run_sync(service.adjuntos, historia_id)


@router.get("/adjuntos/{adjunto_id}/url")
async def url_adjunto(db: DbSession, usuario: Equipo, adjunto_id: UUID) -> dict[str, str]:
    """URL firmada de vida corta; solo para quien ve la historia completa."""
    return await db.run_sync(service.url_adjunto, adjunto_id, service.vista_para(usuario.rol))


# --- F2-CLI-03 Plantillas y formulas -----------------------------------------------------------


@router.post(
    "/historias/{historia_id}/formulas",
    response_model=FormulaRead,
    status_code=status.HTTP_201_CREATED,
)
async def emitir_formula(
    db: DbSession, medico: Medico, historia_id: UUID, data: FormulaIn
) -> FormulaRead:
    entrada = await db.run_sync(service.obtener, historia_id)
    formula = await db.run_sync(
        service.emitir_formula,
        entrada,
        [i.model_dump(exclude_none=True) for i in data.items],
        data.indicaciones,
        medico.id,
    )
    archivo = await db.get(Archivo, formula.archivo_id)
    assert archivo is not None
    return FormulaRead(id=formula.id, url=archivos.url(archivo))


@router.get("/plantillas", response_model=list[PlantillaRead], dependencies=[EQUIPO])
async def plantillas(db: DbSession, tipo_servicio: str | None = None) -> list[PlantillaConsulta]:
    from sqlalchemy import select

    stmt = select(PlantillaConsulta).where(PlantillaConsulta.activa.is_(True))
    if tipo_servicio:
        stmt = stmt.where(PlantillaConsulta.tipo_servicio_codigo == tipo_servicio)
    return list(await db.scalars(stmt.order_by(PlantillaConsulta.nombre)))


@router.post(
    "/plantillas",
    response_model=PlantillaRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[GESTION],
)
async def crear_plantilla(db: DbSession, data: PlantillaIn) -> PlantillaConsulta:
    from sqlalchemy import select

    from app.core.errores import Conflicto

    if await db.scalar(select(PlantillaConsulta.id).where(PlantillaConsulta.codigo == data.codigo)):
        raise Conflicto(f"Ya existe la plantilla {data.codigo}")
    plantilla = PlantillaConsulta(**data.model_dump())
    db.add(plantilla)
    await db.flush()
    return plantilla


# --- F2-CLI-04 Atencion virtual ----------------------------------------------------------------


@router.get("/respuestas-virtuales", response_model=list[RespuestaRead], dependencies=[GESTION])
async def respuestas(db: DbSession, estado: str | None = None) -> list[RespuestaVirtual]:
    from sqlalchemy import select

    stmt = select(RespuestaVirtual).order_by(RespuestaVirtual.codigo)
    if estado:
        stmt = stmt.where(RespuestaVirtual.estado == estado)
    return list(await db.scalars(stmt))


@router.post(
    "/respuestas-virtuales",
    response_model=RespuestaRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[GESTION],
)
async def crear_respuesta(db: DbSession, data: RespuestaIn) -> RespuestaVirtual:
    """Nace en borrador: no se usa hasta que la direccion la aprueba."""
    return await db.run_sync(service.crear_respuesta, data.model_dump())


@router.post("/respuestas-virtuales/{codigo}/aprobacion", response_model=RespuestaRead)
async def aprobar_respuesta(
    db: DbSession, usuario: Annotated[Usuario, Depends(requiere(Rol.ADMIN))], codigo: str
) -> RespuestaVirtual:
    return await db.run_sync(service.aprobar_respuesta, codigo, usuario.id)


@router.get("/virtual/cola", response_model=list[SolicitudRead], dependencies=[GESTION])
async def cola(db: DbSession) -> list[SolicitudVirtual]:
    return await db.run_sync(service.cola)


@router.post(
    "/virtual",
    response_model=SolicitudRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[EQUIPO],
)
async def solicitar(db: DbSession, data: SolicitudIn) -> SolicitudVirtual:
    """Registro desde el panel (p. ej. una consulta que entro por telefono)."""
    return await db.run_sync(
        lambda s: service.solicitar_virtual(
            s, data.mascota_id, data.motivo, canal=data.canal, prioridad=data.prioridad
        )
    )


@router.post("/virtual/{solicitud_id}/toma", response_model=SolicitudRead)
async def tomar(db: DbSession, medico: Medico, solicitud_id: UUID) -> SolicitudVirtual:
    solicitud = await db.run_sync(service.obtener_solicitud, solicitud_id)
    return await db.run_sync(service.tomar, solicitud, medico.id)


@router.post("/virtual/{solicitud_id}/respuesta", response_model=SolicitudRead)
async def responder(
    db: DbSession, medico: Medico, solicitud_id: UUID, data: ResponderIn
) -> SolicitudVirtual:
    solicitud = await db.run_sync(service.obtener_solicitud, solicitud_id)
    return await db.run_sync(
        lambda s: service.responder(
            s,
            solicitud,
            respuesta_codigo=data.respuesta_codigo,
            variables=data.variables,
            medico_id=medico.id,
            diagnostico=data.diagnostico,
            notas_internas=data.notas_internas,
        )
    )


@router.post("/virtual/{solicitud_id}/cierre", response_model=SolicitudRead, dependencies=[GESTION])
async def cerrar(db: DbSession, solicitud_id: UUID) -> SolicitudVirtual:
    solicitud = await db.run_sync(service.obtener_solicitud, solicitud_id)
    return await db.run_sync(service.cerrar_solicitud, solicitud)
