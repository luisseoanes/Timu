"""Acceso: login, sesion renovable, cierre, recuperacion de clave y usuarios del equipo.

Los tokens nunca viajan en el cuerpo: el access token va en una cookie httpOnly y el
refresh token en otra, limitada a las rutas de /auth. El navegador no puede leerlos.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.core.config import settings
from app.core.deps import (
    INTERNOS,
    Admin,
    DbSession,
    borrar_cookie_sesion,
    establecer_cookie_sesion,
    publico,
    require_roles,
)
from app.core.enums import Rol
from app.modules.auth import service, sesiones
from app.modules.auth.models import Usuario
from app.modules.auth.schemas import (
    CodigoIn,
    MiembroEquipo,
    RecuperarIn,
    RestablecerIn,
    Sesion,
    UsuarioCreate,
    UsuarioRead,
    UsuarioUpdate,
    VerificacionCodigoIn,
)
from app.schemas.common import Mensaje, Page, ParamsListado, paginar

router = APIRouter(prefix="/auth", tags=["auth"])

# Cualquier sesion valida, la de una clinica aliada incluida: sin /me ni /logout esa cuenta
# podia ingresar pero el panel no la reconocia ni podia cerrarla.
Autenticado = Annotated[Usuario, Depends(require_roles(*Rol))]


def _sesion(usuario: Usuario) -> Sesion:
    return Sesion(usuario=UsuarioRead.model_validate(usuario))


@router.post("/login", response_model=Sesion, dependencies=[Depends(publico)])
async def login(
    db: DbSession,
    request: Request,
    response: Response,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Sesion:
    """`username` acepta el email o el telefono de la cuenta. Los tokens quedan en cookies
    httpOnly: el navegador no debe poder leerlos desde JavaScript."""
    usuario = await db.run_sync(service.authenticate, form.username, form.password)
    if usuario is None:
        raise sesiones.SesionInvalida("Usuario o contrasena incorrectos")
    access, refresh = await db.run_sync(
        sesiones.crear,
        usuario,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    establecer_cookie_sesion(response, access, refresh)
    return _sesion(usuario)


@router.post("/refresh", response_model=Sesion, dependencies=[Depends(publico)])
async def refresh(db: DbSession, request: Request, response: Response) -> Sesion | JSONResponse:
    """F1-AUT-01 Renueva el access token con la cookie de renovacion, que rota en cada uso:
    la anterior deja de servir."""
    token = request.cookies.get(settings.COOKIE_REFRESH_NAME)
    if not token:
        raise sesiones.SesionInvalida("Sesion invalida")
    resultado = await db.run_sync(sesiones.renovar, token)
    if resultado is None:
        # Token ya rotado: se revocaron todas las sesiones. Se responde sin excepcion para
        # que la revocacion se confirme.
        respuesta = JSONResponse(
            {"detail": "Sesion invalida", "codigo": "no_autenticado"}, status_code=401
        )
        borrar_cookie_sesion(respuesta)
        return respuesta
    usuario, access, nuevo = resultado
    establecer_cookie_sesion(response, access, nuevo)
    return _sesion(usuario)


@router.post("/logout", response_model=Mensaje)
async def logout(db: DbSession, request: Request, response: Response, _: Autenticado) -> Mensaje:
    """Cierra la sesion actual: su access y su refresh token dejan de servir de inmediato."""
    await db.run_sync(sesiones.cerrar, UUID(request.state.sid))
    borrar_cookie_sesion(response)
    return Mensaje(detail="Sesion cerrada")


@router.post("/logout-todas", response_model=Mensaje)
async def logout_todas(db: DbSession, response: Response, usuario: Autenticado) -> Mensaje:
    """Cierra todas las sesiones del usuario en todos sus dispositivos."""
    await db.run_sync(sesiones.cerrar_todas, usuario.id)
    borrar_cookie_sesion(response)
    return Mensaje(detail="Sesiones cerradas")


@router.post("/recuperar", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(publico)])
async def recuperar(db: DbSession, data: RecuperarIn) -> Mensaje:
    """F1-AUT-03 Envia un enlace de un solo uso por correo o WhatsApp. La respuesta es la misma
    exista o no la cuenta."""
    await db.run_sync(service.solicitar_recuperacion, data.identificador)
    return Mensaje(detail="Si la cuenta existe, enviamos un enlace para restablecer la contrasena")


@router.post(
    "/restablecer", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(publico)]
)
async def restablecer(db: DbSession, data: RestablecerIn) -> None:
    """Define la contrasena con un enlace de recuperacion o de activacion del portal."""
    await db.run_sync(service.restablecer, data.token, data.password)


@router.post("/codigo", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(publico)])
async def solicitar_codigo(db: DbSession, data: CodigoIn) -> Mensaje:
    """F3-POR-07 Codigo de ingreso de un solo uso por WhatsApp para el portal. La
    respuesta es la misma exista o no la cuenta."""
    await db.run_sync(service.solicitar_codigo, data.telefono)
    return Mensaje(detail="Si el numero tiene cuenta, enviamos un codigo por WhatsApp")


@router.post("/codigo/verificacion", response_model=Sesion, dependencies=[Depends(publico)])
async def verificar_codigo(
    db: DbSession, request: Request, response: Response, data: VerificacionCodigoIn
) -> Sesion | JSONResponse:
    """Intentos limitados y expiracion corta. Un codigo errado no levanta excepcion: el
    intento debe quedar contado aunque la respuesta sea 401."""
    usuario = await db.run_sync(service.verificar_codigo, data.telefono, data.codigo)
    if usuario is None:
        return JSONResponse(
            {"detail": "Codigo invalido o vencido", "codigo": "no_autenticado"}, status_code=401
        )
    access, refresh = await db.run_sync(
        sesiones.crear,
        usuario,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    establecer_cookie_sesion(response, access, refresh)
    return _sesion(usuario)


@router.get("/me", response_model=UsuarioRead)
async def me(usuario: Autenticado) -> Usuario:
    return usuario


@router.get(
    "/equipo",
    response_model=list[MiembroEquipo],
    dependencies=[Depends(require_roles(*INTERNOS))],
)
async def equipo(db: DbSession, rol: str | None = None) -> list[Usuario]:
    """Personas activas del equipo interno, para asignar rutas y tareas. Cualquier perfil
    interno lo consulta; la gestion de usuarios sigue siendo de admin."""
    stmt = select(Usuario).where(Usuario.activo.is_(True), Usuario.rol.in_(INTERNOS))
    if rol:
        stmt = stmt.where(Usuario.rol == rol)
    return list((await db.scalars(stmt.order_by(Usuario.nombre))).all())


@router.get("/usuarios", response_model=Page[UsuarioRead])
async def listar_usuarios(
    db: DbSession, _: Admin, params: ParamsListado, rol: str | None = None
) -> Page[UsuarioRead]:
    stmt = select(Usuario)
    if rol:
        stmt = stmt.where(Usuario.rol == rol)
    return await paginar(
        db,
        stmt,
        params,
        UsuarioRead,
        campos_orden={"nombre": Usuario.nombre, "created_at": Usuario.created_at},
        orden_por_defecto="nombre",
        desempate=Usuario.id,
    )


@router.post("/usuarios", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
async def crear_usuario(db: DbSession, _: Admin, data: UsuarioCreate) -> Usuario:
    return await db.run_sync(service.create_usuario, data)


@router.patch("/usuarios/{usuario_id}", response_model=UsuarioRead)
async def actualizar_usuario(
    db: DbSession, actor: Admin, usuario_id: UUID, data: UsuarioUpdate
) -> Usuario:
    """Cambiar el perfil o desactivar cierra todas las sesiones del usuario."""
    return await db.run_sync(service.actualizar_usuario, usuario_id, data, actor)
