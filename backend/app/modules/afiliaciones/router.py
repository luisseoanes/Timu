"""F1-AFI Afiliacion en linea y asistida."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any, Literal
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Query, Request, Response, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select

from app.api.deps import (
    INTERNOS,
    DbSession,
    Interno,
    establecer_cookie_sesion,
    publico,
    requiere,
)
from app.core.database import ContextoDb, fijar_contexto
from app.core.enums import EstadoPago, Periodicidad, Rol
from app.core.errores import ReglaNegocio
from app.core.validaciones import DocumentoCO, TelefonoCO, TipoDocumento
from app.modules.afiliaciones import ciclo, linea, registro, service
from app.modules.afiliaciones.models import SolicitudAfiliacion
from app.modules.afiliaciones.schemas import LineaFamiliaRead
from app.modules.auth import sesiones
from app.modules.auth.models import Usuario
from app.modules.catalogos import service as catalogos
from app.modules.familias import service as familias
from app.modules.familias.models import Familia, Mascota
from app.modules.familias.schemas import (
    Baja,
    ContactoIn,
    FamiliaRead,
    FormularioFamilia,
    MascotaAlta,
    MascotaRead,
)
from app.modules.planes import service as planes
from app.modules.planes.schemas import CotizacionRead, PlanPublico, cotizacion_read
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


class PlanDeMascota(BaseModel):
    mascota_id: UUID
    plan_id: UUID


class AfiliacionAsistida(BaseModel):
    """Todos los peludos activos de la familia, cada uno con su plan, y la forma de pago."""

    familia_id: UUID
    peludos: list[PlanDeMascota] = Field(min_length=1)
    periodicidad: Periodicidad = Periodicidad.MENSUAL
    medio_aceptacion: Literal["presencial", "whatsapp", "llamada"]
    detalle_aceptacion: str | None = Field(default=None, description="Quien, como, soporte")


class AltaMascota(MascotaAlta):
    plan_id: UUID | None = Field(
        default=None, description="Obligatorio si la familia tiene una afiliacion vigente"
    )


class PeludoSolicitudRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    mascota_id: UUID | None
    nombre: str
    especie: str
    plan_id: UUID
    valor_mensual: Decimal


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
    periodicidad: Periodicidad
    peludos: list[PeludoSolicitudRead]
    valor_inicial: Decimal
    referencia_pago: str
    estado: str
    origen: str
    contrato_id: UUID | None
    aceptacion: dict[str, Any]
    completada_en: datetime | None
    error: str | None
    created_at: datetime


@router.post("/asistida", response_model=InicioAfiliacion, status_code=status.HTTP_201_CREATED)
async def afiliacion_asistida(
    db: DbSession, usuario: Comercial, data: AfiliacionAsistida
) -> InicioAfiliacion:
    """Comercial afilia a una familia ya registrada; la aceptacion queda con su medio."""
    familia = await db.run_sync(familias.obtener, data.familia_id)
    solicitud, enlace = await db.run_sync(
        service.iniciar,
        familia=familia,
        planes_por_mascota={p.mascota_id: p.plan_id for p in data.peludos},
        periodicidad=data.periodicidad,
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


# Antes de GET /{solicitud_id}: si no, /lineas se leeria como un id de solicitud.
@router.get("/lineas", response_model=list[LineaFamiliaRead], dependencies=[EQUIPO])
async def lineas_de_familias(
    db: DbSession,
    familia_id: Annotated[list[UUID], Query(min_length=1, max_length=linea.MAX_FAMILIAS)],
) -> list[LineaFamiliaRead]:
    """R2-PAN-02 La linea de varias familias a la vez, para el listado del panel: una sola
    peticion por pagina, no una por fila. Una familia que no existe vuelve con la linea vacia."""
    return await db.run_sync(linea.leer, list(dict.fromkeys(familia_id)))


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


@familias_router.get("/{familia_id}/linea", response_model=LineaFamiliaRead, dependencies=[EQUIPO])
async def linea_de_familia(db: DbSession, familia_id: UUID) -> LineaFamiliaRead:
    """R2-PAN-02 Cuotas, preventivos y servicios de la familia en una sola linea por fecha:
    seis meses atras y seis adelante, mas todo lo vencido."""
    await db.run_sync(familias.obtener, familia_id)
    return (await db.run_sync(linea.leer, [familia_id]))[0]


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
)
async def agregar_mascota(
    db: DbSession, usuario: Interno, familia_id: UUID, data: AltaMascota
) -> Mascota:
    """Con afiliacion vigente, la mascota entra con su plan y el contrato se recalcula."""
    familia = await db.run_sync(familias.obtener, familia_id)
    mascota = MascotaAlta(**data.model_dump(exclude={"plan_id"}))
    return await db.run_sync(ciclo.alta_desde_panel, familia, mascota, data.plan_id, usuario.id)


@mascotas_router.post("/{mascota_id}/baja", response_model=MascotaRead)
async def dar_de_baja_mascota(
    db: DbSession, usuario: Interno, mascota_id: UUID, data: Baja
) -> MascotaRead:
    mascota = await db.run_sync(familias.obtener_mascota, mascota_id)
    mascota = await db.run_sync(ciclo.dar_de_baja_mascota, mascota, data.motivo, usuario.id)
    return await db.run_sync(familias.mascota_read, mascota)


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


# --- 6.1 Registro en linea ---------------------------------------------------------------------

PUBLICO = Depends(publico)


class PeludoCotizar(BaseModel):
    especie: str = Field(max_length=40)
    plan_id: UUID


class CotizacionPublica(BaseModel):
    ciudad: str = Field(max_length=80)
    peludos: list[PeludoCotizar] = Field(min_length=1, max_length=10)


class PeludoRegistro(PeludoCotizar):
    nombre: str = Field(min_length=1, max_length=120)


class ContactoRegistro(BaseModel):
    """Para el comprobante y para enviarle el enlace del formulario si cierra el navegador."""

    nombre: str = Field(min_length=2, max_length=160)
    telefono: TelefonoCO
    email: EmailStr


class RegistroIn(BaseModel):
    ciudad: str = Field(max_length=80)
    peludos: list[PeludoRegistro] = Field(min_length=1, max_length=10)
    periodicidad: Periodicidad = Periodicidad.MENSUAL
    contacto: ContactoRegistro
    acepta_condiciones: bool = Field(description="Debe ser true: aceptacion expresa")
    acepta_tratamiento_datos: bool
    # Campo trampa: los humanos no lo ven ni lo llenan; los bots si.
    sitio_web: str | None = Field(default=None, exclude=True)


class InicioRegistro(BaseModel):
    referencia: str
    valor: Decimal
    enlace_pago: str
    token: str = Field(description="Para continuar en este navegador sin esperar el mensaje")


class Token(BaseModel):
    token: str = Field(min_length=20, max_length=128)


class ReintentoRegistro(BaseModel):
    referencia: str
    enlace_pago: str


class PeludoRegistroRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    posicion: int
    nombre: str
    especie: str
    plan_id: UUID
    valor_mensual: Decimal


class RegistroRead(BaseModel):
    """Lo que necesita el formulario posterior al pago (y la pagina de resultado)."""

    model_config = ConfigDict(from_attributes=True)

    estado: str
    ciudad: str
    periodicidad: Periodicidad
    valor_inicial: Decimal
    contacto_nombre: str | None
    contacto_telefono: str | None
    contacto_email: str | None
    peludos: list[PeludoRegistroRead]
    estado_pago: EstadoPago | None = None


class TitularRegistro(BaseModel):
    titular_nombre: str = Field(min_length=2, max_length=160)
    tipo_documento: TipoDocumento = TipoDocumento.CC
    documento: DocumentoCO
    telefono: TelefonoCO
    email: EmailStr
    barrio: str = Field(min_length=2, max_length=120)
    direccion: str = Field(min_length=3, max_length=255)
    complemento: str | None = Field(default=None, max_length=255)


class PeludoFormulario(BaseModel):
    """La especie no se cambia: de ella dependen los planes que pudo elegir."""

    posicion: int = Field(ge=1)
    nombre: str = Field(min_length=1, max_length=120)
    raza: str | None = Field(default=None, max_length=80)
    sexo: Literal["macho", "hembra"] | None = None
    fecha_nacimiento: date
    peso_kg: float = Field(gt=0, lt=150)
    esterilizada: bool | None = None


class FormularioRegistro(Token):
    titular: TitularRegistro
    contactos: list[ContactoIn] = Field(default_factory=list, max_length=3)
    clave: str = Field(min_length=8, max_length=128)
    peludos: list[PeludoFormulario] = Field(min_length=1, max_length=10)


class ResultadoRegistro(BaseModel):
    estado: Literal["completada", "revision"]
    mensaje: str


@router.get("/registro/ciudades", response_model=list[str], dependencies=[PUBLICO])
async def ciudades_con_cobertura(db: DbSession) -> list[str]:
    """Las otras ciudades ven el aviso de que aun no hay cobertura."""
    return await db.run_sync(registro.ciudades_con_cobertura)


@router.get("/registro/planes", response_model=list[PlanPublico], dependencies=[PUBLICO])
async def planes_en(db: DbSession, ciudad: str) -> Any:
    ciudad = await db.run_sync(catalogos.ciudad_valida, ciudad)
    return await db.run_sync(registro.planes_en, ciudad)


@router.post("/registro/cotizacion", response_model=list[CotizacionRead], dependencies=[PUBLICO])
async def cotizar_registro(db: DbSession, data: CotizacionPublica) -> list[CotizacionRead]:
    """El mismo calculo que cobra: cada peludo con su plan, en cada periodicidad."""
    ciudad = await db.run_sync(catalogos.ciudad_valida, data.ciudad)
    peludos = [(p.especie, p.plan_id) for p in data.peludos]
    return [
        cotizacion_read(await db.run_sync(planes.cotizar, ciudad, peludos, periodicidad))
        for periodicidad in Periodicidad
    ]


@router.post(
    "/registro",
    response_model=InicioRegistro,
    status_code=status.HTTP_201_CREATED,
    dependencies=[PUBLICO],
)
async def iniciar_registro(db: DbSession, request: Request, data: RegistroIn) -> InicioRegistro:
    """Ciudad, peludos con su plan, forma de pago y contacto: devuelve el enlace de pago con
    el valor que calcula el backend. Los datos de la familia se piden despues del pago."""
    if not (data.acepta_condiciones and data.acepta_tratamiento_datos):
        raise ReglaNegocio("Debe aceptar las condiciones y el tratamiento de datos")
    if data.sitio_web:
        raise ReglaNegocio("Solicitud rechazada")
    ciudad = await db.run_sync(catalogos.ciudad_valida, data.ciudad)
    solicitud, enlace, token = await db.run_sync(
        lambda s: registro.iniciar(
            s,
            ciudad=ciudad,
            peludos=[registro.Peludo(p.nombre, p.especie, p.plan_id) for p in data.peludos],
            periodicidad=data.periodicidad,
            contacto=registro.Contacto(
                data.contacto.nombre, data.contacto.telefono, str(data.contacto.email)
            ),
            aceptacion={
                "medio": "formulario_web",
                "ip": request.client.host if request.client else None,
                "agente": request.headers.get("user-agent", "")[:255],
                "tratamiento_datos": True,
            },
        )
    )
    return InicioRegistro(
        referencia=solicitud.referencia_pago,
        valor=solicitud.valor_inicial,
        enlace_pago=enlace,
        token=token,
    )


@router.post("/registro/consulta", response_model=RegistroRead, dependencies=[PUBLICO])
async def consultar_registro(db: DbSession, data: Token) -> Any:
    """Estado del registro y lo que eligio, con el token del navegador o del enlace. Va por
    POST para que el token no quede en los registros de acceso."""
    solicitud = await db.run_sync(registro.por_token, data.token)
    lectura = RegistroRead.model_validate(solicitud)
    lectura.estado_pago = await db.run_sync(registro.estado_pago, solicitud)
    return lectura


@router.post("/registro/reintentar", response_model=ReintentoRegistro, dependencies=[PUBLICO])
async def reintentar_registro(db: DbSession, request: Request, data: Token) -> ReintentoRegistro:
    """Tras un pago rechazado, otro enlace de pago para el mismo registro: lo elegido se
    conserva y no queda otra solicitud colgada."""
    solicitud = await db.run_sync(registro.por_token, data.token)
    # Como en `completar`: el token ya probo quien es, y el pago nuevo se escribe como sistema.
    await db.run_sync(
        fijar_contexto,
        ContextoDb(rol="sistema", request_id=getattr(request.state, "request_id", None)),
    )
    enlace = await db.run_sync(registro.reintentar, solicitud)
    return ReintentoRegistro(referencia=solicitud.referencia_pago, enlace_pago=enlace)


@router.post("/registro/completar", response_model=ResultadoRegistro, dependencies=[PUBLICO])
async def completar_registro(
    db: DbSession, request: Request, response: Response, data: FormularioRegistro
) -> ResultadoRegistro:
    """Formulario posterior al pago. Con la afiliacion activa y una cuenta nueva, la sesion
    queda abierta para seguir en el portal (subir las fotos de los peludos)."""
    solicitud = await db.run_sync(registro.por_token, data.token)
    # El token ya probo quien es: como la firma de un webhook, la afiliacion sigue como
    # `sistema` (crea familia, contrato, cuotas y acceso, que `publico` no escribe).
    await db.run_sync(
        fijar_contexto,
        ContextoDb(rol="sistema", request_id=getattr(request.state, "request_id", None)),
    )
    resultado = await db.run_sync(
        lambda s: registro.completar(
            s,
            solicitud,
            titular=data.titular.model_dump(mode="python"),
            contactos=data.contactos,
            clave=data.clave,
            peludos=[registro.DatosPeludo(**p.model_dump()) for p in data.peludos],
        )
    )
    if resultado.estado == "completada" and resultado.clave_nueva and resultado.familia:
        usuario = await db.get(Usuario, resultado.familia.usuario_portal_id)
        assert usuario is not None
        access, refresh = await db.run_sync(
            sesiones.crear,
            usuario,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        establecer_cookie_sesion(response, access, refresh)
    return ResultadoRegistro(estado=resultado.estado, mensaje=resultado.mensaje)  # type: ignore[arg-type]
