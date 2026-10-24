"""Portal de familias (F3-POR): todo parte de la familia del usuario conectado
(F1-AUT-04), asi que una familia nunca puede pedir datos de otra."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Response, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.deps import DbSession, FamiliaActual
from app.core.validaciones import TelefonoCO
from app.modules.cartera import service as cartera
from app.modules.cartera.schemas import EstadoCuenta
from app.modules.familias.models import Familia
from app.modules.familias.schemas import FamiliaRead
from app.modules.portal import service
from app.modules.servicios.models import Servicio

router = APIRouter(prefix="/portal", tags=["portal"])


class DatosFamiliaIn(BaseModel):
    """Lo que la familia puede actualizar sola. Documento, estado y plan, no."""

    email: EmailStr | None = None
    telefono: TelefonoCO | None = None
    direccion: str | None = Field(default=None, max_length=255)
    ciudad: str | None = Field(default=None, max_length=80)


class ServicioPortalIn(BaseModel):
    mascota_id: UUID
    tipo_codigo: str
    inicio: datetime
    observaciones: str | None = Field(default=None, max_length=1000)


class ReprogramacionIn(BaseModel):
    inicio: datetime
    motivo: str = Field(min_length=3, max_length=255)


class CancelacionIn(BaseModel):
    motivo: str = Field(min_length=3, max_length=255)


class ServicioPortalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    mascota_id: UUID | None
    tipo_codigo: str
    estado: str
    programado_para: datetime | None
    termina_en: datetime | None


class PagoIn(BaseModel):
    cuota_id: UUID | None = None


class PagoPortalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    referencia_externa: str
    valor: Decimal
    estado: str
    fecha_pago: datetime | None
    created_at: datetime


class InicioPago(BaseModel):
    pago: PagoPortalRead
    enlace_pago: str


class SolicitudVirtualIn(BaseModel):
    mascota_id: UUID
    motivo: str = Field(min_length=5, max_length=4000)


# --- F3-POR-01 Datos, plan y estado de cuenta -------------------------------------------------


@router.get("/mi-familia", response_model=FamiliaRead)
async def mi_familia(familia: FamiliaActual) -> Familia:
    return familia


@router.patch("/mi-familia", response_model=FamiliaRead)
async def actualizar_datos(db: DbSession, familia: FamiliaActual, data: DatosFamiliaIn) -> Familia:
    """F3-POR-06 Contacto y direccion, validados y auditados."""
    return await db.run_sync(service.actualizar_datos, familia, data.model_dump(exclude_unset=True))


@router.get("/plan")
async def plan(db: DbSession, familia: FamiliaActual) -> dict[str, Any]:
    return await db.run_sync(service.plan, familia)


@router.get("/contrato")
async def contrato(db: DbSession, familia: FamiliaActual) -> dict[str, str]:
    """F1-AFI-02 PDF del contrato vigente de la familia."""
    from app.modules.planes import service as planes

    vigente = await db.run_sync(planes.contrato_vigente, familia.id)
    if vigente is None:
        from app.core.errores import NoEncontrado

        raise NoEncontrado("La familia no tiene contrato vigente")
    return await db.run_sync(cartera.url_documento, vigente)


@router.get("/estado-cuenta", response_model=EstadoCuenta)
async def estado_cuenta(db: DbSession, familia: FamiliaActual) -> Any:
    """F1-CAR-10 La misma consulta del panel, siempre sobre la familia conectada."""
    return await db.run_sync(cartera.estado_cuenta, familia.id)


# --- F3-POR-02 / 03 Historia clinica y carnet -------------------------------------------------


@router.get("/mascotas/{mascota_id}/historia")
async def historia(db: DbSession, familia: FamiliaActual, mascota_id: UUID) -> list[dict[str, Any]]:
    """Solo lectura, solo lo firmado y sin las notas internas del equipo medico."""
    return await db.run_sync(service.historia, familia, mascota_id)


@router.get("/historias/{historia_id}/adjuntos")
async def adjuntos(
    db: DbSession, familia: FamiliaActual, historia_id: UUID
) -> list[dict[str, Any]]:
    filas = await db.run_sync(service.adjuntos, familia, historia_id)
    return [{"id": a.id, "nombre": a.nombre_archivo, "descripcion": a.descripcion} for a in filas]


@router.get("/adjuntos/{adjunto_id}/url")
async def url_adjunto(db: DbSession, familia: FamiliaActual, adjunto_id: UUID) -> dict[str, str]:
    return await db.run_sync(service.url_adjunto, familia, adjunto_id)


@router.get("/mascotas/{mascota_id}/carnet")
async def carnet(db: DbSession, familia: FamiliaActual, mascota_id: UUID) -> dict[str, Any]:
    from app.modules.preventivos import service as preventivos

    mascota = await db.run_sync(service.mascota_propia, familia, mascota_id)
    return await db.run_sync(preventivos.carnet, mascota.id)


@router.post("/mascotas/{mascota_id}/carnet/pdf", status_code=status.HTTP_201_CREATED)
async def carnet_pdf(db: DbSession, familia: FamiliaActual, mascota_id: UUID) -> dict[str, str]:
    from app.modules.archivos import service as archivos
    from app.modules.archivos.models import Archivo
    from app.modules.preventivos import service as preventivos

    mascota = await db.run_sync(service.mascota_propia, familia, mascota_id)
    registro = await db.run_sync(preventivos.emitir_carnet, mascota.id, familia.usuario_portal_id)
    archivo = await db.get(Archivo, registro.archivo_id)
    assert archivo is not None
    return {"codigo": registro.codigo, "url": archivos.url(archivo)}


# --- F3-POR-04 Autogestion de servicios -------------------------------------------------------


@router.get("/disponibilidad")
async def disponibilidad(
    db: DbSession, familia: FamiliaActual, fecha: date, tipo_codigo: str
) -> list[dict[str, Any]]:
    cupos = await db.run_sync(service.disponibilidad, familia, fecha, tipo_codigo)
    return [
        {"inicio": c.inicio, "fin": c.fin, "disponibles": c.disponibles}
        for c in cupos
        if c.disponibles > 0
    ]


@router.get("/servicios", response_model=list[ServicioPortalRead])
async def servicios(
    db: DbSession, familia: FamiliaActual, incluir_pasados: bool = False
) -> list[Servicio]:
    return await db.run_sync(service.servicios_de, familia, incluir_pasados)


@router.post("/servicios", response_model=ServicioPortalRead, status_code=status.HTTP_201_CREATED)
async def agendar(db: DbSession, familia: FamiliaActual, data: ServicioPortalIn) -> Servicio:
    return await db.run_sync(
        lambda s: service.agendar(
            s,
            familia,
            mascota_id=data.mascota_id,
            tipo_codigo=data.tipo_codigo,
            inicio=data.inicio,
            observaciones=data.observaciones,
        )
    )


@router.post("/servicios/{servicio_id}/reprogramacion", response_model=ServicioPortalRead)
async def reprogramar(
    db: DbSession, familia: FamiliaActual, servicio_id: UUID, data: ReprogramacionIn
) -> Servicio:
    return await db.run_sync(service.reprogramar, familia, servicio_id, data.inicio, data.motivo)


@router.post("/servicios/{servicio_id}/cancelacion", response_model=ServicioPortalRead)
async def cancelar(
    db: DbSession, familia: FamiliaActual, servicio_id: UUID, data: CancelacionIn
) -> Servicio:
    return await db.run_sync(service.cancelar, familia, servicio_id, data.motivo)


@router.post("/orientacion-virtual", status_code=status.HTTP_201_CREATED)
async def orientacion_virtual(
    db: DbSession, familia: FamiliaActual, data: SolicitudVirtualIn
) -> dict[str, Any]:
    """F2-CLI-04 La consulta entra a la cola del equipo medico."""
    from app.modules.clinica import service as clinica

    mascota = await db.run_sync(service.mascota_propia, familia, data.mascota_id)
    solicitud = await db.run_sync(
        lambda s: clinica.solicitar_virtual(s, mascota.id, data.motivo, canal="portal")
    )
    return {"id": solicitud.id, "estado": solicitud.estado}


# --- F3-POR-05 Pagos en linea -----------------------------------------------------------------


@router.get("/pagos", response_model=list[PagoPortalRead])
async def pagos(db: DbSession, familia: FamiliaActual) -> list[Any]:
    return await db.run_sync(service.pagos, familia)


@router.post("/pagos", response_model=InicioPago, status_code=status.HTTP_201_CREATED)
async def pagar(db: DbSession, familia: FamiliaActual, data: PagoIn) -> InicioPago:
    """Devuelve el enlace de pago; al aprobarse, el webhook aplica el pago y actualiza el
    estado de la familia."""
    pago, enlace = await db.run_sync(service.iniciar_pago, familia, data.cuota_id)
    return InicioPago(pago=PagoPortalRead.model_validate(pago), enlace_pago=enlace)


@router.get("/pagos/{pago_id}/comprobante", response_class=Response)
async def comprobante(db: DbSession, familia: FamiliaActual, pago_id: UUID) -> Response:
    """PDF del pago aprobado, para descargar."""
    contenido = await db.run_sync(service.comprobante, familia, pago_id)
    return Response(
        contenido,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="comprobante-{pago_id}.pdf"',
            "Cache-Control": "private, no-store",
        },
    )
