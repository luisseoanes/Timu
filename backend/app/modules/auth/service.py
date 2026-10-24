from datetime import timedelta
from typing import Literal
from uuid import UUID

import structlog
from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import Rol
from app.core.errores import Conflicto, ErrorDominio, NoEncontrado, ReglaNegocio
from app.core.security import (
    generar_token_opaco,
    hash_password,
    hash_token,
    password_inutilizable,
    verify_password,
)
from app.core.tiempo import ahora, con_zona
from app.core.validaciones import normalizar_telefono
from app.modules.auth import sesiones
from app.modules.auth.models import TokenUsoUnico, Usuario
from app.modules.auth.schemas import UsuarioCreate, UsuarioUpdate

logger = structlog.get_logger(__name__)

Proposito = Literal["recuperacion", "activacion"]


class EnlaceInvalido(ErrorDominio):
    status_code = 400
    codigo = "enlace_invalido"


def _normalizar_identificador(identificador: str) -> tuple[str, str] | None:
    identificador = identificador.strip()
    if "@" in identificador:
        return "email", identificador.lower()
    try:
        return "telefono", normalizar_telefono(identificador)
    except ValueError:
        return None


def get_by_identificador(db: Session, identificador: str) -> Usuario | None:
    par = _normalizar_identificador(identificador)
    if par is None:
        return None
    campo, valor = par
    columna = Usuario.email if campo == "email" else Usuario.telefono
    return db.scalar(select(Usuario).where(columna == valor))


def get_by_email(db: Session, email: str) -> Usuario | None:
    return db.scalar(select(Usuario).where(Usuario.email == email.lower()))


def _verificar_disponible(
    db: Session, email: str | None, telefono: str | None, excluir: UUID | None = None
) -> None:
    condiciones = []
    if email:
        condiciones.append(Usuario.email == email)
    if telefono:
        condiciones.append(Usuario.telefono == telefono)
    stmt = select(Usuario.id).where(or_(*condiciones))
    if excluir:
        stmt = stmt.where(Usuario.id != excluir)
    if condiciones and db.scalar(stmt.limit(1)):
        raise Conflicto("Ya existe un usuario con ese email o telefono")


def create_usuario(db: Session, data: UsuarioCreate) -> Usuario:
    email = data.email.lower() if data.email else None
    _verificar_disponible(db, email, data.telefono)
    usuario = Usuario(
        email=email,
        telefono=data.telefono,
        nombre=data.nombre,
        rol=data.rol,
        hashed_password=hash_password(data.password),
    )
    db.add(usuario)
    db.flush()
    return usuario


def actualizar_usuario(
    db: Session, usuario_id: UUID, data: UsuarioUpdate, actor: Usuario
) -> Usuario:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise NoEncontrado("Usuario no encontrado")
    cambios = data.model_dump(exclude_unset=True)
    if usuario.id == actor.id and ("rol" in cambios or cambios.get("activo") is False):
        raise ReglaNegocio("No puede cambiar su propio perfil ni desactivarse")
    for campo, valor in cambios.items():
        setattr(usuario, campo, valor)
    if cambios.get("activo") is False or "rol" in cambios:
        # El rol viaja en el token: cualquier cambio obliga a volver a iniciar sesion.
        sesiones.cerrar_todas(db, usuario.id)
    db.flush()
    return usuario


def authenticate(db: Session, identificador: str, password: str) -> Usuario | None:
    usuario = get_by_identificador(db, identificador)
    if usuario is None or not verify_password(password, usuario.hashed_password):
        return None
    return usuario if usuario.activo else None


# --- Enlaces de un solo uso (F1-AUT-03 / F1-AUT-04) ---------------------------------------


def emitir_enlace(db: Session, usuario: Usuario, proposito: Proposito) -> str:
    # Un enlace nuevo invalida los anteriores del mismo proposito.
    db.execute(
        update(TokenUsoUnico)
        .where(
            TokenUsoUnico.usuario_id == usuario.id,
            TokenUsoUnico.proposito == proposito,
            TokenUsoUnico.usado_en.is_(None),
        )
        .values(usado_en=ahora())
    )
    vigencia = (
        timedelta(minutes=settings.TOKEN_RECUPERACION_MINUTOS)
        if proposito == "recuperacion"
        else timedelta(hours=settings.TOKEN_ACTIVACION_HORAS)
    )
    token = generar_token_opaco()
    db.add(
        TokenUsoUnico(
            usuario_id=usuario.id,
            proposito=proposito,
            token_hash=hash_token(token),
            expira_en=ahora() + vigencia,
        )
    )
    db.flush()
    _enviar_enlace(db, usuario, proposito, token)
    return token


def _enviar_enlace(db: Session, usuario: Usuario, proposito: Proposito, token: str) -> None:
    from app.modules.comunicaciones import service as comunicaciones

    ruta = "restablecer" if proposito == "recuperacion" else "activar"
    enlace = f"{settings.FRONTEND_URL}/{ruta}?token={token}"
    if usuario.email:
        asunto = (
            "Restablece tu contrasena de TIMU"
            if proposito == "recuperacion"
            else "Activa tu cuenta de TIMU"
        )
        accion = (
            "definir una contrasena nueva" if proposito == "recuperacion" else "activar tu cuenta"
        )
        cuerpo = (
            f"Hola {usuario.nombre},\n\nUsa este enlace para {accion}:\n{enlace}\n\n"
            "Si no lo solicitaste, ignora este mensaje."
        )
        comunicaciones.encolar_correo(db, email=usuario.email, asunto=asunto, cuerpo=cuerpo)
    elif usuario.telefono:
        plantilla = "recuperar_clave" if proposito == "recuperacion" else "activar_cuenta"
        try:
            comunicaciones.encolar_plantilla(
                db,
                telefono=usuario.telefono,
                plantilla=plantilla,
                variables=[usuario.nombre, enlace],
            )
        except ReglaNegocio:
            logger.error("No se pudo enviar el enlace de %s: plantilla %s", proposito, plantilla)


def solicitar_recuperacion(db: Session, identificador: str) -> None:
    """Siempre responde igual, exista o no la cuenta: no revela quien esta registrado."""
    usuario = get_by_identificador(db, identificador)
    if usuario is None or not usuario.activo:
        logger.info("Recuperacion solicitada para identificador inexistente o inactivo")
        return
    emitir_enlace(db, usuario, "recuperacion")


def restablecer(db: Session, token: str, password: str) -> Usuario:
    registro = db.scalar(select(TokenUsoUnico).where(TokenUsoUnico.token_hash == hash_token(token)))
    if registro is None or registro.usado_en is not None or con_zona(registro.expira_en) <= ahora():
        raise EnlaceInvalido("El enlace no es valido o ya expiro; solicite uno nuevo")
    usuario = db.get(Usuario, registro.usuario_id)
    if usuario is None or not usuario.activo:
        raise EnlaceInvalido("El enlace no es valido o ya expiro; solicite uno nuevo")
    registro.usado_en = ahora()
    usuario.hashed_password = hash_password(password)
    sesiones.cerrar_todas(db, usuario.id)
    db.flush()
    return usuario


# --- Usuario de portal (F1-AUT-04) ---------------------------------------------------------


def crear_usuario_portal(
    db: Session, *, nombre: str, email: str | None, telefono: str | None
) -> Usuario:
    """Crea (o reutiliza) el acceso de portal de una familia y le envia el enlace de activacion.

    La clave inicial es inutilizable: la familia la define desde el enlace.
    """
    email = email.lower() if email else None
    condiciones = []
    if email:
        condiciones.append(Usuario.email == email)
    if telefono:
        condiciones.append(Usuario.telefono == telefono)
    if not condiciones:
        raise ReglaNegocio("La familia necesita email o telefono para tener acceso al portal")
    existentes = list(db.scalars(select(Usuario).where(or_(*condiciones))))
    if any(u.rol != Rol.FAMILIA for u in existentes):
        raise Conflicto("El email o telefono de la familia pertenece a un usuario interno")
    if len(existentes) > 1:
        raise Conflicto("El email y el telefono pertenecen a cuentas de portal distintas")
    if existentes:
        return existentes[0]
    usuario = Usuario(
        email=email,
        telefono=telefono,
        nombre=nombre,
        rol=Rol.FAMILIA,
        hashed_password=password_inutilizable(),
    )
    db.add(usuario)
    db.flush()
    emitir_enlace(db, usuario, "activacion")
    return usuario
