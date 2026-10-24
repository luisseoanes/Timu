"""F1-AUT-01 Sesion larga con renovacion y cierre inmediato.

- El access token (JWT) dura poco y lleva el id de la sesion (`sid`).
- El refresh token es opaco, se guarda como hash y rota en cada renovacion.
- Cerrar sesion la revoca: el access token deja de servir en la siguiente peticion.
- Reusar un refresh token ya rotado indica robo: se revocan todas las sesiones del usuario.
"""

from datetime import timedelta
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errores import ErrorDominio
from app.core.security import create_access_token, generar_token_opaco, hash_token
from app.core.tiempo import ahora, con_zona
from app.modules.auth.models import Sesion, Usuario

logger = structlog.get_logger(__name__)


class SesionInvalida(ErrorDominio):
    status_code = 401
    codigo = "no_autenticado"


def _access_token(usuario: Usuario, sesion: Sesion) -> str:
    return create_access_token(str(usuario.id), {"rol": usuario.rol, "sid": str(sesion.id)})


def crear(
    db: Session, usuario: Usuario, *, ip: str | None = None, user_agent: str | None = None
) -> tuple[str, str]:
    refresh = generar_token_opaco()
    sesion = Sesion(
        usuario_id=usuario.id,
        refresh_hash=hash_token(refresh),
        expira_en=ahora() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        ip=ip,
        user_agent=(user_agent or "")[:255] or None,
    )
    db.add(sesion)
    db.flush()
    return _access_token(usuario, sesion), refresh


def renovar(db: Session, refresh: str) -> tuple[Usuario, str, str] | None:
    """Rota el refresh token. Devuelve None si el token ya habia sido rotado (robo): en
    ese caso se revocan todas las sesiones del usuario y quien llama responde 401 SIN
    levantar excepcion, para que la transaccion se confirme y la revocacion persista."""
    h = hash_token(refresh)
    sesion = db.scalar(select(Sesion).where(Sesion.refresh_hash == h))
    if sesion is None:
        robada = db.scalar(select(Sesion).where(Sesion.refresh_hash_anterior == h))
        if robada is not None:
            logger.warning(
                "Refresh token reutilizado; se revocan las sesiones de %s", robada.usuario_id
            )
            cerrar_todas(db, robada.usuario_id)
            return None
        raise SesionInvalida("Sesion invalida")
    if sesion.revocada_en is not None:
        raise SesionInvalida("Sesion invalida")
    if con_zona(sesion.expira_en) <= ahora():
        raise SesionInvalida("La sesion expiro; inicie sesion de nuevo")
    usuario = db.get(Usuario, sesion.usuario_id)
    if usuario is None or not usuario.activo:
        raise SesionInvalida("Sesion invalida")

    nuevo = generar_token_opaco()
    sesion.refresh_hash_anterior = h
    sesion.refresh_hash = hash_token(nuevo)
    db.flush()
    return usuario, _access_token(usuario, sesion), nuevo


def cerrar(db: Session, sid: UUID) -> None:
    db.execute(
        update(Sesion)
        .where(Sesion.id == sid, Sesion.revocada_en.is_(None))
        .values(revocada_en=ahora())
    )


def cerrar_todas(db: Session, usuario_id: UUID) -> None:
    db.execute(
        update(Sesion)
        .where(Sesion.usuario_id == usuario_id, Sesion.revocada_en.is_(None))
        .values(revocada_en=ahora())
    )


def token_revocado(db: Session, payload: dict[str, Any]) -> bool:
    sid = payload.get("sid")
    if not sid:
        return True
    try:
        sesion = db.get(Sesion, UUID(sid))
    except ValueError:
        return True
    return sesion is None or sesion.revocada_en is not None
