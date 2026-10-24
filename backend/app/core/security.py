import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.core.config import settings

# bcrypt trunca a 72 bytes; se corta explicitamente para no depender del backend.
_MAX_BYTES = 72


def _encode(password: str) -> bytes:
    return password.encode("utf-8")[:_MAX_BYTES]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_encode(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_encode(plain), hashed.encode("utf-8"))
    except ValueError:
        return False


def password_inutilizable() -> str:
    """Hash de una clave aleatoria que nadie conoce: la cuenta se activa por enlace."""
    return hash_password(secrets.token_urlsafe(32))


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {"sub": subject, "exp": expire, "tipo": "acceso", **(extra or {})}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Devuelve el payload o None. El algoritmo se fija explicitamente: aceptar el
    del propio token permitiria un ataque de confusion de algoritmos."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        return None


def generar_token_opaco() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Los tokens opacos (refresh, enlaces) se guardan solo como SHA-256."""
    return hashlib.sha256(token.encode()).hexdigest()
