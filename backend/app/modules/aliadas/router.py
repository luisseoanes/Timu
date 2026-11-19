"""6.22 Clinicas aliadas: directorio, convenios, remisiones, acceso de la aliada y
liquidacion."""

import csv
import io
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status
from pydantic import BaseModel, BeforeValidator, ConfigDict, EmailStr, Field, computed_field
from sqlalchemy import select

from app.api.deps import DbSession, publico, requiere
from app.core.enums import Rol, TipoAliada
from app.core.errores import Prohibido
from app.core.tiempo import hoy
from app.modules.aliadas import service
from app.modules.aliadas.models import ClinicaAliada, ConvenioAliada, RemisionAliada
from app.modules.archivos import service as archivos
from app.modules.auth.models import Usuario
from app.modules.catalogos import service as catalogos

router = APIRouter(prefix="/aliadas", tags=["aliadas"])

# Perfiles de cada ruta (Seccion 12, docs/perfiles-y-permisos.md).
ATENCION = Depends(requiere(Rol.ATENCION_CLIENTE))
ATENCION_Y_OPERACIONES = Depends(requiere(Rol.ATENCION_CLIENTE, Rol.OPERACIONES))
Atencion = Annotated[Usuario, Depends(requiere(Rol.ATENCION_CLIENTE))]
GERENCIA_Y_OPERACIONES = Depends(requiere(Rol.GERENCIA, Rol.OPERACIONES))
OPERACIONES = Depends(requiere(Rol.OPERACIONES))
Operaciones = Annotated[Usuario, OPERACIONES]
Aliada = Annotated[Usuario, Depends(requiere(Rol.ALIADA))]


def _vacio_es_nada(v: Any) -> Any:
    return (v.strip() or None) if isinstance(v, str) else v


Linea = Annotated[Annotated[str, Field(max_length=255)] | None, BeforeValidator(_vacio_es_nada)]
Texto = Annotated[Annotated[str, Field(max_length=2000)] | None, BeforeValidator(_vacio_es_nada)]


class ClinicaIn(BaseModel):
    nombre: str = Field(min_length=3, max_length=160)
    nit: str | None = Field(default=None, max_length=20)
    ciudad: str
    direccion: str | None = Field(default=None, max_length=255)
    telefono: str | None = Field(default=None, max_length=32)
    email: EmailStr | None = None
    servicios: str | None = None
    # R3-PUB-04 Lo que dice de ella la portada.
    tipo: TipoAliada = TipoAliada.CLINICA
    en_portada: bool = False
    atiende_24h: bool = False
    barrio: Linea = None
    horario: Linea = None
    presentacion: Texto = None
    orden_portada: int = Field(default=0, ge=0, le=1000)


class ClinicaUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=3, max_length=160)
    direccion: str | None = None
    telefono: str | None = None
    email: EmailStr | None = None
    servicios: str | None = None
    activa: bool | None = None
    tipo: TipoAliada | None = None
    en_portada: bool | None = None
    atiende_24h: bool | None = None
    barrio: Linea = None
    horario: Linea = None
    presentacion: Texto = None
    orden_portada: int | None = Field(default=None, ge=0, le=1000)


class ClinicaRead(ClinicaIn):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str | None = None  # type: ignore[assignment]
    activa: bool
    tipo_nombre: str = ""
    logo_url: str | None = None


class AliadaPublica(BaseModel):
    """Lo que la portada dice de una aliada de la red: nada interno (ni NIT, ni correo, ni
    convenios)."""

    id: UUID
    nombre: str
    tipo: TipoAliada
    tipo_nombre: str
    atiende_24h: bool
    ciudad: str
    barrio: str | None
    direccion: str | None
    telefono: str | None
    horario: str | None
    presentacion: str | None
    logo_url: str | None


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
    # De quien es y adonde va, en la bandeja (GET /remisiones); al emitir o anular no se piden.
    titular: str | None = None
    mascota: str | None = None
    clinica: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def vencida(self) -> bool:
        """Emitida y sin usar pasada su fecha: la clinica ya no la acepta."""
        return self.estado == "emitida" and self.vence_en < hoy()


class RecuentosRemisiones(BaseModel):
    emitida: int
    utilizada: int
    anulada: int
    todas: int


class AnulacionIn(BaseModel):
    motivo: str = Field(min_length=3, max_length=255)


class AtencionIn(BaseModel):
    fecha: date
    valor_atencion: Decimal = Field(gt=0)
    resumen: str = Field(min_length=5, max_length=4000)


class MascotaRemitida(BaseModel):
    nombre: str
    especie: str
    especie_nombre: str
    raza: str | None


class RemisionVistaAliada(BaseModel):
    """Lo que ve la clinica aliada al validar un codigo (6.22): lo minimo para atender."""

    codigo: str
    estado: str
    vigente: bool
    vencida: bool
    vence_en: date
    emitida_en: date
    # Entre que fechas se puede reportar la atencion: con la remision sin usar, tambien vencida
    # (una atencion hecha dentro de su vigencia se reporta despues); sin valor si ya se uso o se
    # anulo.
    atencion_desde: date | None
    atencion_hasta: date | None
    titular: str
    documento_ultimos: str
    mascota: MascotaRemitida
    motivo: str
    beneficio: str | None
    cobertura_pct: int
    tope_cubierto: Decimal | None
    fecha_atencion: date | None
    valor_atencion: Decimal | None
    valor_cubierto: Decimal | None
    valor_familia: Decimal | None


class CoberturaAliada(BaseModel):
    valor_atencion: Decimal
    valor_cubierto: Decimal
    valor_familia: Decimal
    # Lo cubierto llego al tope de la remision: la familia asume el resto.
    con_tope: bool


class MiClinica(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nombre: str
    ciudad: str


class AtendidaAliada(BaseModel):
    codigo: str
    fecha_atencion: date
    titular: str
    mascota: str
    motivo: str
    beneficio: str | None
    valor_atencion: Decimal
    valor_cubierto: Decimal
    valor_familia: Decimal


class AtendidasAliada(BaseModel):
    desde: date
    hasta: date
    atenciones: int
    valor_atenciones: Decimal
    valor_cubierto: Decimal
    valor_familias: Decimal
    items: list[AtendidaAliada]


# --- 6.22 Directorio y convenios ---------------------------------------------------------


async def _leida(db: DbSession, clinica: ClinicaAliada) -> ClinicaRead:
    return ClinicaRead.model_validate(clinica).model_copy(
        update={
            "tipo_nombre": service.NOMBRES_TIPO[TipoAliada(clinica.tipo)],
            "logo_url": await db.run_sync(service.logo_url, clinica),
        }
    )


@router.get("", response_model=list[ClinicaRead], dependencies=[ATENCION_Y_OPERACIONES])
async def listar(
    db: DbSession, ciudad: str | None = None, incluir_inactivas: bool = False
) -> list[ClinicaRead]:
    stmt = select(ClinicaAliada).order_by(ClinicaAliada.nombre)
    if ciudad:
        stmt = stmt.where(ClinicaAliada.ciudad == ciudad)
    if not incluir_inactivas:
        stmt = stmt.where(ClinicaAliada.activa.is_(True))
    return [await _leida(db, c) for c in await db.scalars(stmt)]


@router.get("/publicas", response_model=list[AliadaPublica], dependencies=[Depends(publico)])
async def publicas(db: DbSession) -> list[AliadaPublica]:
    """R3-PUB-04 La red de aliadas que muestra la portada, en su orden: la lee cualquiera."""
    return [
        AliadaPublica(
            id=c.id,
            nombre=c.nombre,
            tipo=TipoAliada(c.tipo),
            tipo_nombre=service.NOMBRES_TIPO[TipoAliada(c.tipo)],
            atiende_24h=c.atiende_24h,
            ciudad=c.ciudad,
            barrio=c.barrio,
            direccion=c.direccion,
            telefono=c.telefono,
            horario=c.horario,
            presentacion=c.presentacion,
            logo_url=url,
        )
        for c, url in await db.run_sync(service.de_la_portada)
    ]


@router.post(
    "", response_model=ClinicaRead, status_code=status.HTTP_201_CREATED, dependencies=[OPERACIONES]
)
async def crear(db: DbSession, data: ClinicaIn) -> ClinicaRead:
    datos = data.model_dump()
    datos["ciudad"] = await db.run_sync(catalogos.ciudad_valida, data.ciudad)
    clinica = ClinicaAliada(**datos)
    db.add(clinica)
    await db.flush()
    return await _leida(db, clinica)


@router.patch("/{clinica_id}", response_model=ClinicaRead, dependencies=[OPERACIONES])
async def actualizar(db: DbSession, clinica_id: UUID, data: ClinicaUpdate) -> ClinicaRead:
    clinica = await db.run_sync(service.obtener_clinica, clinica_id)
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(clinica, campo, valor)
    await db.flush()
    return await _leida(db, clinica)


@router.put("/{clinica_id}/logo", response_model=ClinicaRead)
async def subir_logo(
    db: DbSession,
    usuario: Operaciones,
    clinica_id: UUID,
    logo: Annotated[UploadFile, File(description="JPG, PNG o WEBP de hasta 2 MB")],
) -> ClinicaRead:
    clinica = await db.run_sync(service.obtener_clinica, clinica_id)
    contenido = await archivos.leer(logo, "logo_aliada")
    clinica = await db.run_sync(service.subir_logo, clinica, contenido, logo.filename, usuario.id)
    return await _leida(db, clinica)


@router.delete("/{clinica_id}/logo", response_model=ClinicaRead, dependencies=[OPERACIONES])
async def quitar_logo(db: DbSession, clinica_id: UUID) -> ClinicaRead:
    clinica = await db.run_sync(service.obtener_clinica, clinica_id)
    return await _leida(db, await db.run_sync(service.quitar_logo, clinica))


@router.get(
    "/{clinica_id}/convenios",
    response_model=list[ConvenioRead],
    dependencies=[ATENCION_Y_OPERACIONES],
)
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
    dependencies=[OPERACIONES],
)
async def crear_convenio(db: DbSession, clinica_id: UUID, data: ConvenioIn) -> ConvenioAliada:
    clinica = await db.run_sync(service.obtener_clinica, clinica_id)
    return await db.run_sync(service.crear_convenio, clinica, data.model_dump())


# --- 6.22 Remisiones ---------------------------------------------------------------------


@router.post("/remisiones", response_model=RemisionRead, status_code=status.HTTP_201_CREATED)
async def emitir(db: DbSession, usuario: Atencion, data: RemisionIn) -> RemisionAliada:
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


@router.get("/remisiones", response_model=list[RemisionRead], dependencies=[ATENCION])
async def remisiones(
    db: DbSession,
    clinica_id: UUID | None = None,
    familia_id: UUID | None = None,
    estado: str | None = None,
) -> list[RemisionRead]:
    # Las que estan por usar, por la que vence antes; las demas, de la mas reciente a la antigua
    # (el id es UUIDv7: ordena por creacion con el indice de la clave primaria).
    orden = (
        (RemisionAliada.vence_en, RemisionAliada.id)
        if estado == "emitida"
        else (RemisionAliada.id.desc(),)
    )
    stmt = select(RemisionAliada).order_by(*orden).limit(500)
    if clinica_id:
        stmt = stmt.where(RemisionAliada.clinica_id == clinica_id)
    if familia_id:
        stmt = stmt.where(RemisionAliada.familia_id == familia_id)
    if estado:
        stmt = stmt.where(RemisionAliada.estado == estado)
    lista = list(await db.scalars(stmt))
    nombres = await db.run_sync(service.quienes, lista)
    return [RemisionRead.model_validate(r).model_copy(update=nombres[r.id]) for r in lista]


@router.get("/remisiones/recuentos", response_model=RecuentosRemisiones, dependencies=[ATENCION])
async def recuentos(db: DbSession, clinica_id: UUID | None = None) -> dict[str, int]:
    return await db.run_sync(service.recuentos, clinica_id)


@router.post("/remisiones/{remision_id}/anulacion", response_model=RemisionRead)
async def anular(
    db: DbSession, usuario: Atencion, remision_id: UUID, data: AnulacionIn
) -> RemisionAliada:
    remision = await db.run_sync(service.obtener_remision, remision_id)
    return await db.run_sync(service.anular, remision, data.motivo, usuario.id)


# --- 6.22 Acceso de la clinica aliada ----------------------------------------------------


def _clinica(usuario: Usuario) -> UUID:
    if usuario.clinica_aliada_id is None:
        raise Prohibido("El usuario no esta asociado a una clinica aliada")
    return usuario.clinica_aliada_id


@router.get("/mi-clinica", response_model=MiClinica)
async def mi_clinica(db: DbSession, usuario: Aliada) -> ClinicaAliada:
    """En que clinica esta quien ingresa (R3-ALI-01)."""
    return await db.run_sync(service.mi_clinica, _clinica(usuario))


@router.get("/mi-clinica/atendidas", response_model=AtendidasAliada)
async def atendidas(db: DbSession, usuario: Aliada, desde: date, hasta: date) -> dict[str, Any]:
    """Lo que la clinica reporto en el periodo y lo que cubrio TIMU, para cuadrar la
    liquidacion (R3-ALI-01)."""
    return await db.run_sync(service.atendidas, _clinica(usuario), desde, hasta)


@router.get("/mi-clinica/remisiones/{codigo}", response_model=RemisionVistaAliada)
async def validar_remision(db: DbSession, usuario: Aliada, codigo: str) -> dict[str, Any]:
    """La aliada valida el beneficio con el codigo que presenta la familia."""
    return await db.run_sync(service.vista_aliada, codigo, _clinica(usuario))


@router.get("/mi-clinica/remisiones/{codigo}/cobertura", response_model=CoberturaAliada)
async def cobertura(
    db: DbSession, usuario: Aliada, codigo: str, valor_atencion: Annotated[Decimal, Query(gt=0)]
) -> dict[str, Any]:
    """Lo que cubre TIMU de un valor y lo que paga la familia, antes de reportar (R3-ALI-01)."""
    return await db.run_sync(service.cobertura_de, codigo, _clinica(usuario), valor_atencion)


@router.post("/mi-clinica/remisiones/{codigo}/atencion", response_model=RemisionVistaAliada)
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


# --- 6.22 Liquidacion --------------------------------------------------------------------


@router.get("/liquidacion", dependencies=[GERENCIA_Y_OPERACIONES], response_model=None)
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
