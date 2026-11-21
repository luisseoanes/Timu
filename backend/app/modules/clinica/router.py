"""6.14 / 6.17 Historia clinica, adjuntos, formulas y atencion veterinaria virtual.

6.14 Solo el personal medico escribe. Para leer, cada perfil recibe su vista: el
medico y el admin la historia completa; comercial y operaciones un resumen (cuando, por
que, quien); la familia, desde el portal, todo menos lo de uso interno.
"""

from datetime import date, datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import AlcanceActual, DbSession, requiere
from app.core.enums import Rol
from app.core.errores import ReglaNegocio
from app.core.eventos import EventoDominio
from app.core.outbox import publicar
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
from app.schemas.common import Page

router = APIRouter(prefix="/clinica", tags=["clinica"])

# Perfiles de cada ruta (Seccion 12, docs/perfiles-y-permisos.md).
MEDICO = Depends(requiere(Rol.MEDICO))
Medico = Annotated[Usuario, Depends(requiere(Rol.MEDICO))]


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


NombrePlantilla = Annotated[str, Field(min_length=3, max_length=120)]
CamposPlantilla = dict[
    Literal[service.CAMPOS_CLINICOS],  # type: ignore[valid-type]
    Annotated[str, Field(max_length=4000)],
]


class PlantillaIn(BaseModel):
    """El codigo lo saca la API del nombre (`service.crear_plantilla`)."""

    nombre: NombrePlantilla
    tipo_servicio_codigo: str | None = None
    campos: CamposPlantilla = {}


class PlantillaUpdate(BaseModel):
    """Solo cambia lo que se manda; `campos` reemplaza los textos enteros."""

    nombre: NombrePlantilla | None = None
    tipo_servicio_codigo: str | None = None
    campos: CamposPlantilla | None = None
    activa: bool | None = None


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
    borrador_ia: dict[str, Any] | None = None
    borrador_en: datetime | None = None
    created_at: datetime


class ResponderIn(BaseModel):
    respuesta_codigo: str
    variables: list[str] = []
    diagnostico: str | None = None
    notas_internas: str | None = None


# --- 6.14 Historia ------------------------------------------------------------------


class MascotaClinica(BaseModel):
    """6.14 Lo que el medico necesita para abrir una historia: la mascota y de quien es."""

    id: UUID
    nombre: str
    especie: str
    raza: str | None
    activa: bool
    familia_id: UUID
    titular_nombre: str
    ciudad: str


def _clinica(mascota: Any, familia: Any) -> MascotaClinica:
    return MascotaClinica(
        id=mascota.id,
        nombre=mascota.nombre,
        especie=mascota.especie,
        raza=mascota.raza,
        activa=mascota.activa,
        familia_id=familia.id,
        titular_nombre=familia.titular_nombre,
        ciudad=familia.ciudad,
    )


@router.get("/mascotas", response_model=Page[MascotaClinica], dependencies=[MEDICO])
async def buscar_mascotas(
    db: DbSession,
    alcance: AlcanceActual,
    q: str | None = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[MascotaClinica]:
    """Las mascotas cuya historia puede abrir el medico, por nombre, titular o documento."""
    filas, total = await db.run_sync(service.buscar_mascotas, alcance, q, limit, offset)
    return Page[MascotaClinica](
        items=[_clinica(m, f) for m, f in filas], total=total, limit=limit, offset=offset
    )


@router.get("/mascotas/{mascota_id}", response_model=MascotaClinica, dependencies=[MEDICO])
async def mascota(db: DbSession, alcance: AlcanceActual, mascota_id: UUID) -> MascotaClinica:
    return _clinica(*await db.run_sync(service.mascota_con_titular, alcance, mascota_id))


@router.get("/mascotas/{mascota_id}/historia")
async def historia(
    db: DbSession, usuario: Medico, mascota_id: UUID, incluir_corregidas: bool = False
) -> list[dict[str, Any]]:
    vista = service.vista_para(usuario.rol)
    return await db.run_sync(
        lambda s: [
            service.presentar(e, vista)
            for e in service.historia(s, mascota_id, incluir_corregidas=incluir_corregidas)
        ]
    )


@router.get("/borradores")
async def borradores(db: DbSession, usuario: Medico) -> list[dict[str, Any]]:
    """R2-PAN-07 Las consultas que quien pregunta abrio y aun no firma."""
    return await db.run_sync(
        lambda s: [service.presentar(e, "completa") for e in service.borradores(s, usuario.id)]
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
async def obtener(db: DbSession, usuario: Medico, historia_id: UUID) -> dict[str, Any]:
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


# --- 6.14 Adjuntos -----------------------------------------------------------------------


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
    "/historias/{historia_id}/adjuntos", response_model=list[AdjuntoRead], dependencies=[MEDICO]
)
async def listar_adjuntos(db: DbSession, historia_id: UUID) -> list[AdjuntoClinico]:
    return await db.run_sync(service.adjuntos, historia_id)


@router.get("/adjuntos/{adjunto_id}/url")
async def url_adjunto(db: DbSession, usuario: Medico, adjunto_id: UUID) -> dict[str, str]:
    """URL firmada de vida corta; solo para quien ve la historia completa."""
    return await db.run_sync(service.url_adjunto, adjunto_id, service.vista_para(usuario.rol))


# --- 6.14 Plantillas y formulas ----------------------------------------------------------


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


@router.get("/plantillas", response_model=list[PlantillaRead], dependencies=[MEDICO])
async def plantillas(
    db: DbSession, tipo_servicio: str | None = None, incluir_inactivas: bool = False
) -> list[PlantillaConsulta]:
    return await db.run_sync(
        lambda s: service.listar_plantillas(
            s, tipo_servicio=tipo_servicio, incluir_inactivas=incluir_inactivas
        )
    )


@router.get("/plantillas/uso", response_model=dict[str, int], dependencies=[MEDICO])
async def uso_de_plantillas(db: DbSession) -> dict[str, int]:
    return await db.run_sync(service.uso_de_plantillas)


@router.post(
    "/plantillas",
    response_model=PlantillaRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[MEDICO],
)
async def crear_plantilla(db: DbSession, data: PlantillaIn) -> PlantillaConsulta:
    return await db.run_sync(
        service.crear_plantilla, data.nombre, data.campos, data.tipo_servicio_codigo
    )


@router.patch("/plantillas/{codigo}", response_model=PlantillaRead, dependencies=[MEDICO])
async def editar_plantilla(db: DbSession, codigo: str, data: PlantillaUpdate) -> PlantillaConsulta:
    return await db.run_sync(service.editar_plantilla, codigo, data.model_dump(exclude_unset=True))


# --- 6.17 Atencion virtual ---------------------------------------------------------------


@router.get("/respuestas-virtuales", response_model=list[RespuestaRead], dependencies=[MEDICO])
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
    dependencies=[MEDICO],
)
async def crear_respuesta(db: DbSession, data: RespuestaIn) -> RespuestaVirtual:
    """Nace en borrador: no se usa hasta que la direccion la aprueba."""
    return await db.run_sync(service.crear_respuesta, data.model_dump())


@router.post("/respuestas-virtuales/{codigo}/aprobacion", response_model=RespuestaRead)
async def aprobar_respuesta(db: DbSession, usuario: Medico, codigo: str) -> RespuestaVirtual:
    return await db.run_sync(service.aprobar_respuesta, codigo, usuario.id)


@router.get("/virtual/cola", response_model=list[SolicitudRead], dependencies=[MEDICO])
async def cola(db: DbSession) -> list[SolicitudVirtual]:
    return await db.run_sync(service.cola)


@router.post(
    "/virtual",
    response_model=SolicitudRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[MEDICO],
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


@router.post(
    "/virtual/{solicitud_id}/borrador",
    status_code=status.HTTP_202_ACCEPTED,
)
async def pedir_borrador(db: DbSession, medico: Medico, solicitud_id: UUID) -> dict[str, str]:
    """6.17 Pide a la IA un borrador para revisar. Llega a la solicitud en segundos;
    nunca se envia a la familia: la respuesta sigue saliendo de una plantilla aprobada."""

    solicitud = await db.run_sync(service.obtener_solicitud, solicitud_id)
    if solicitud.asignada_a_id != medico.id:
        raise ReglaNegocio("Tome la solicitud antes de pedir un borrador")
    publicar(db, EventoDominio(service.EVENTO_BORRADOR, {"solicitud_id": str(solicitud.id)}))
    return {"detail": "Borrador solicitado"}


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


@router.post("/virtual/{solicitud_id}/cierre", response_model=SolicitudRead, dependencies=[MEDICO])
async def cerrar(db: DbSession, solicitud_id: UUID) -> SolicitudVirtual:
    solicitud = await db.run_sync(service.obtener_solicitud, solicitud_id)
    return await db.run_sync(service.cerrar_solicitud, solicitud)
