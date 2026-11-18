"""R3-PUB-04 Lo institucional y de contacto de TIMU: lo lee la portada sin sesion y lo escribe
Administracion."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, EmailStr, Field

from app.api.deps import DbSession, publico, requiere
from app.core.enums import Rol
from app.core.validaciones import TelefonoCO
from app.modules.catalogos import service as catalogos
from app.modules.institucional import service

router = APIRouter(prefix="/institucional", tags=["institucional"])

ADMIN = Depends(requiere(Rol.ADMIN))
PUBLICO = Depends(publico)


def _vacio_es_nada(v: Any) -> Any:
    return (v.strip() or None) if isinstance(v, str) else v


def _limpios(v: list[str]) -> list[str]:
    return [x.strip() for x in v if x.strip()]


Texto = Annotated[Annotated[str, Field(max_length=4000)] | None, BeforeValidator(_vacio_es_nada)]
Linea = Annotated[Annotated[str, Field(max_length=255)] | None, BeforeValidator(_vacio_es_nada)]


class Red(BaseModel):
    nombre: str = Field(min_length=2, max_length=40)
    url: str = Field(max_length=300, pattern=r"^https://")


class DatosTimuIn(BaseModel):
    razon_social: Linea = None
    nit: Annotated[Annotated[str, Field(max_length=20)] | None, BeforeValidator(_vacio_es_nada)] = (
        None
    )
    presentacion: Texto = None
    mision: Texto = None
    vision: Texto = None
    valores: Annotated[list[Annotated[str, Field(max_length=60)]], AfterValidator(_limpios)] = (
        Field(default_factory=list, max_length=12)
    )
    clinica_nombre: Linea = None
    clinica_direccion: Linea = None
    clinica_barrio: Linea = None
    clinica_ciudad: Linea = None
    clinica_horario: Linea = None
    horario_atencion: Texto = None
    telefonos: list[TelefonoCO] = Field(default_factory=list, max_length=6)
    whatsapp: Annotated[TelefonoCO | None, BeforeValidator(_vacio_es_nada)] = None
    correo: Annotated[EmailStr | None, BeforeValidator(_vacio_es_nada)] = None
    redes: list[Red] = Field(default_factory=list, max_length=8)


class DatosTimuRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    razon_social: str | None
    nit: str | None
    presentacion: str | None
    mision: str | None
    vision: str | None
    valores: list[str]
    clinica_nombre: str | None
    clinica_direccion: str | None
    clinica_barrio: str | None
    clinica_ciudad: str | None
    clinica_horario: str | None
    horario_atencion: str | None
    telefonos: list[str]
    whatsapp: str | None
    correo: str | None
    redes: list[Red]


@router.get("", response_model=DatosTimuRead, dependencies=[PUBLICO])
async def obtener(db: DbSession) -> Any:
    """Lo que dice la portada de TIMU: no lleva datos de nadie, lo lee cualquiera."""
    return await db.run_sync(service.obtener)


@router.put("", response_model=DatosTimuRead, dependencies=[ADMIN])
async def actualizar(db: DbSession, data: DatosTimuIn) -> Any:
    cambios = data.model_dump()
    if data.clinica_ciudad:
        # El nombre canonico, con sus tildes: la llave foranea es el nombre del catalogo.
        cambios["clinica_ciudad"] = await db.run_sync(catalogos.ciudad_valida, data.clinica_ciudad)
    cambios["correo"] = str(data.correo).lower() if data.correo else None
    return await db.run_sync(service.actualizar, cambios)
