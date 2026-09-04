from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.modules.auth.models import Usuario
from app.modules.auth.schemas import UsuarioCreate


async def get_by_email(db: AsyncSession, email: str) -> Usuario | None:
    result = await db.execute(select(Usuario).where(Usuario.email == email))
    return result.scalar_one_or_none()


async def create_usuario(db: AsyncSession, data: UsuarioCreate) -> Usuario:
    usuario = Usuario(
        email=data.email,
        nombre=data.nombre,
        rol=data.rol,
        hashed_password=hash_password(data.password),
    )
    db.add(usuario)
    await db.flush()
    return usuario


async def authenticate(db: AsyncSession, email: str, password: str) -> Usuario | None:
    usuario = await get_by_email(db, email)
    if usuario is None or not verify_password(password, usuario.hashed_password):
        return None
    return usuario if usuario.activo else None
