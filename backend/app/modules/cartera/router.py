"""6.2 / 6.4 Cartera: contratos, cuotas, pagos, cobro recurrente y eventos de la pasarela."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select

from app.core.deps import INTERNOS, DbSession, requiere
from app.core.enums import Rol
from app.core.errores import NoEncontrado
from app.modules.auth.models import Usuario
from app.modules.cartera import pasarela, service
from app.modules.cartera.models import EventoPasarela, MedioPagoRecurrente
from app.modules.cartera.schemas import (
    Cancelacion,
    ContratoCreate,
    ContratoListado,
    ContratoRead,
    EstadoCuenta,
    EventoPasarelaRead,
    MedioPagoCreate,
    MedioPagoRead,
    PagoManual,
    PagoRead,
)
from app.modules.familias import service as familias
from app.modules.planes import service as planes
from app.schemas.common import Page, ParamsListado, paginar

router = APIRouter(prefix="/cartera", tags=["cartera"])

EQUIPO = Depends(requiere(*INTERNOS))
CARTERA = Depends(requiere(Rol.ADMIN, Rol.COMERCIAL))
ADMIN = Depends(requiere(Rol.ADMIN))
Cartera = Annotated[Usuario, Depends(requiere(Rol.ADMIN, Rol.COMERCIAL))]


@router.post(
    "/contratos",
    response_model=ContratoRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[CARTERA],
)
async def crear_contrato(db: DbSession, data: ContratoCreate) -> Any:
    """F1-CAR-01 Contrato directo (afiliacion asistida). La afiliacion completa, con pago y
    contrato en PDF, esta en /afiliaciones."""
    familia = await db.run_sync(familias.obtener, data.familia_id)
    plan = await db.run_sync(planes.obtener, data.plan_id)
    contrato, _ = await db.run_sync(
        service.crear_contrato, familia, plan, fecha_inicio=data.fecha_inicio
    )
    return contrato


@router.get("/contratos", response_model=Page[ContratoListado], dependencies=[EQUIPO])
async def listar_contratos(
    db: DbSession,
    estado: str | None = None,
    ciudad: str | None = None,
    q: str | None = None,
    solo_mora: bool = False,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> Page[ContratoListado]:
    """Cartera para gestionar: los contratos mas atrasados primero."""
    filas, total = await db.run_sync(
        lambda s: service.listar_contratos(
            s,
            estado=estado,
            ciudad=ciudad,
            q=q,
            solo_mora=solo_mora,
            limit=limit,
            offset=offset,
        )
    )
    return Page(
        items=[ContratoListado(**f) for f in filas], total=total, limit=limit, offset=offset
    )


@router.get("/contratos/{contrato_id}", response_model=ContratoRead, dependencies=[EQUIPO])
async def obtener_contrato(db: DbSession, contrato_id: UUID) -> Any:
    return await db.run_sync(service.obtener_contrato, contrato_id)


@router.get("/contratos/{contrato_id}/documento", dependencies=[EQUIPO])
async def documento(db: DbSession, contrato_id: UUID) -> dict[str, str]:
    """F1-AFI-02 Enlace firmado y de vida corta al PDF del contrato."""
    return await db.run_sync(
        service.url_documento, await db.run_sync(service.obtener_contrato, contrato_id)
    )


@router.post(
    "/contratos/{contrato_id}/renovar", response_model=ContratoRead, dependencies=[CARTERA]
)
async def renovar(db: DbSession, contrato_id: UUID) -> Any:
    """F1-CAR-07 Extiende un ano la vigencia del contrato."""
    return await db.run_sync(
        service.renovar, await db.run_sync(service.obtener_contrato, contrato_id)
    )


@router.post(
    "/contratos/{contrato_id}/cancelar", response_model=ContratoRead, dependencies=[CARTERA]
)
async def cancelar(db: DbSession, contrato_id: UUID, data: Cancelacion) -> Any:
    return await db.run_sync(
        service.cancelar, await db.run_sync(service.obtener_contrato, contrato_id), data.motivo
    )


@router.get(
    "/familias/{familia_id}/estado-cuenta", response_model=EstadoCuenta, dependencies=[EQUIPO]
)
async def estado_cuenta(db: DbSession, familia_id: UUID) -> Any:
    """F1-CAR-10 Cuotas, pagos, saldo y proximo cobro."""
    await db.run_sync(familias.obtener, familia_id)
    return await db.run_sync(service.estado_cuenta, familia_id)


@router.post("/pagos", response_model=PagoRead, status_code=status.HTTP_201_CREATED)
async def registrar_pago(db: DbSession, data: PagoManual, usuario: Cartera) -> Any:
    """F1-CAR-06 Pago recibido fuera de la pasarela. Se aplica a la cuota indicada o a la
    mas antigua, y actualiza el estado de la familia (reactiva si estaba congelada)."""
    await db.run_sync(familias.obtener, data.familia_id)
    return await db.run_sync(
        service.registrar_pago_manual,
        familia_id=data.familia_id,
        valor=data.valor,
        medio=data.medio,
        referencia=data.referencia,
        fecha_pago=data.fecha_pago,
        cuota_id=data.cuota_id,
        notas=data.notas,
        usuario_id=usuario.id,
    )


@router.post(
    "/medios-pago",
    response_model=MedioPagoRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[CARTERA],
)
async def registrar_medio(db: DbSession, data: MedioPagoCreate) -> Any:
    """F1-CAR-08 Autorizacion de cobro recurrente con tarjeta tokenizada."""
    familia = await db.run_sync(familias.obtener, data.familia_id)
    return await db.run_sync(
        pasarela.registrar_medio,
        familia,
        token_tarjeta=data.token_tarjeta,
        email=data.email,
        marca=data.marca,
        ultimos4=data.ultimos4,
    )


@router.delete(
    "/medios-pago/{medio_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[CARTERA]
)
async def revocar_medio(db: DbSession, medio_id: UUID) -> None:
    medio = await db.get(MedioPagoRecurrente, medio_id)
    if medio is None:
        raise NoEncontrado("Medio de pago no encontrado")
    medio.activo = False


@router.get("/eventos-pasarela", response_model=Page[EventoPasarelaRead], dependencies=[ADMIN])
async def eventos(
    db: DbSession, params: ParamsListado, estado: str | None = None
) -> Page[EventoPasarelaRead]:
    stmt = select(EventoPasarela)
    if estado:
        stmt = stmt.where(EventoPasarela.estado == estado)
    return await paginar(
        db,
        stmt,
        params,
        EventoPasarelaRead,
        campos_orden={"created_at": EventoPasarela.created_at},
        orden_por_defecto="-created_at",
        desempate=EventoPasarela.id,
    )


@router.post(
    "/eventos-pasarela/{evento_id}/reprocesar",
    response_model=EventoPasarelaRead,
    dependencies=[ADMIN],
)
async def reprocesar(db: DbSession, evento_id: UUID) -> Any:
    """F1-CAR-09 Vuelve a procesar un evento (p. ej. si fallo por datos incompletos)."""
    await db.run_sync(pasarela.procesar_evento, evento_id, forzar=True)
    return await db.get(EventoPasarela, evento_id)


@router.post(
    "/transacciones/{transaccion_id}/recuperar",
    response_model=EventoPasarelaRead,
    dependencies=[ADMIN],
)
async def recuperar(db: DbSession, transaccion_id: str) -> Any:
    """F1-CAR-09 Evento perdido: consulta la transaccion en la pasarela y la concilia."""
    return await db.run_sync(pasarela.recuperar_transaccion, transaccion_id)
