"""Infraestructura de pruebas.

Las pruebas corren contra PostgreSQL, no contra SQLite. La razon es de fidelidad:
usamos JSONB, UUID nativo y `FOR UPDATE SKIP LOCKED`, y ninguna de las tres existe
en SQLite. Una suite verde sobre SQLite no diria nada sobre produccion.

Levantar la base:  docker compose up -d db-test
"""

import os
from collections.abc import AsyncGenerator, Iterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.database import Base, get_db
from app.core.enums import Rol
from app.core.security import hash_password
from app.main import app
from app.models import Base as _  # noqa: F401  asegura el registro de todos los modelos
from app.modules.auth.models import Usuario

URL_ASYNC = os.getenv(
    "TEST_DATABASE_URL", "postgresql+asyncpg://timu:timu@localhost:5433/timu_test"
)
URL_SYNC = URL_ASYNC.replace("postgresql+asyncpg://", "postgresql+psycopg://")


@pytest.fixture(scope="session", autouse=True)
def esquema() -> Iterator[None]:
    """Crea el esquema una vez para toda la sesion, con un engine sincrono para no
    pelearnos con el event loop de pytest-asyncio."""
    engine = create_engine(URL_SYNC)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover
        pytest.exit(
            f"No hay PostgreSQL de pruebas en {URL_SYNC}.\n"
            f"Arrancalo con: docker compose up -d db-test\n({exc})",
            returncode=1,
        )
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Sesion aislada: cada prueba corre dentro de una transaccion que se revierte
    al terminar, asi que las pruebas no se ven entre si y no hay que limpiar tablas.

    `join_transaction_mode="create_savepoint"` hace que un commit del codigo bajo
    prueba libere un savepoint en vez de escribir de verdad.
    """
    engine = create_async_engine(URL_ASYNC, poolclass=None)
    conn = await engine.connect()
    trans = await conn.begin()
    session = AsyncSession(
        bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )
    try:
        yield session
    finally:
        await session.close()
        await trans.rollback()
        await conn.close()
        await engine.dispose()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _get_db():
        yield db

    app.dependency_overrides[get_db] = _get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def usuario_admin(db: AsyncSession) -> Usuario:
    usuario = Usuario(
        email="admin@timu.co",
        nombre="Admin",
        rol=Rol.ADMIN,
        hashed_password=hash_password("secreto123"),
    )
    db.add(usuario)
    await db.commit()
    return usuario


async def autenticar(client: AsyncClient, email: str, password: str) -> None:
    """Inicia sesion y deja la cookie httpOnly en el cliente. No hay token que
    manejar a mano: es justo el punto de usar cookie."""
    resp = await client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
