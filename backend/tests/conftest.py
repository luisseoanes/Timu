"""Infraestructura de pruebas.

Las pruebas corren contra PostgreSQL, no contra SQLite. La razon es de fidelidad:
usamos JSONB, UUID nativo y `FOR UPDATE SKIP LOCKED`, y ninguna de las tres existe
en SQLite. Una suite verde sobre SQLite no diria nada sobre produccion.

Levantar la base:  docker compose up -d db-test

Los servicios de dominio son sincronos (los comparten endpoints y workers de Celery):
desde una prueba async se llaman con `await db.run_sync(servicio.funcion, ...)`, igual
que hacen los routers.
"""

import os

# Antes de importar la app: la configuracion se lee una sola vez al cargar el modulo.
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "false")

from collections.abc import AsyncGenerator, Iterator  # noqa: E402
from datetime import UTC, datetime  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any  # noqa: E402

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import create_engine, select, text  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402

import app.workers.tasks.cartera  # noqa: E402, F401  registra los manejadores del outbox
import app.workers.tasks.comunicaciones  # noqa: E402, F401
import app.workers.tasks.encuestas  # noqa: E402, F401
import app.workers.tasks.familias  # noqa: E402, F401
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.database import Base, get_db  # noqa: E402
from app.core.enums import Rol  # noqa: E402
from app.core.eventos import EventoDominio, manejadores  # noqa: E402
from app.core.outbox import EventoSaliente  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.integrations import storage  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base as _  # noqa: E402, F401  asegura el registro de todos los modelos
from app.modules.auth.models import Usuario  # noqa: E402
from app.modules.catalogos.service import cargar as cargar_catalogos  # noqa: E402
from app.modules.reglas.service import sembrar as sembrar_reglas  # noqa: E402
from app.workers.celery_app import celery_app  # noqa: E402

URL_ASYNC = os.getenv(
    "TEST_DATABASE_URL", "postgresql+asyncpg://timu:timu@localhost:5433/timu_test"
)
URL_SYNC = URL_ASYNC.replace("postgresql+asyncpg://", "postgresql+psycopg://")
PASSWORD = "secreto123"


@pytest.fixture(scope="session", autouse=True)
def esquema() -> Iterator[None]:
    """Crea el esquema aplicando las MIGRACIONES, no `create_all`.

    Es deliberado y cuesta un par de segundos: asi cada ejecucion de la suite prueba
    que las migraciones levantan una base vacia, y un modelo nuevo sin su migracion
    hace fallar las pruebas en vez de pasar inadvertido hasta el despliegue.
    """
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
    with engine.connect() as conn:
        # Esquema limpio aunque una ejecucion anterior haya quedado a medias.
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.commit()

    command.upgrade(config_alembic(), "head")
    yield
    Base.metadata.drop_all(engine)
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        conn.commit()
    engine.dispose()


def config_alembic() -> Config:
    """Alembic apuntando a la base de pruebas."""
    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    cfg.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "alembic"))
    cfg.set_main_option("sqlalchemy.url", URL_ASYNC)
    return cfg


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Sesion aislada: cada prueba corre dentro de una transaccion que se revierte
    al terminar, asi que las pruebas no se ven entre si y no hay que limpiar tablas.

    `join_transaction_mode="create_savepoint"` hace que un commit del codigo bajo
    prueba libere un savepoint en vez de escribir de verdad. Los catalogos y las reglas
    iniciales se cargan dentro de esa transaccion, como en un ambiente recien creado.
    """
    engine = create_async_engine(URL_ASYNC, poolclass=None)
    conn = await engine.connect()
    trans = await conn.begin()
    session = AsyncSession(
        bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )
    await session.run_sync(cargar_catalogos)
    await session.run_sync(sembrar_reglas)
    await session.commit()
    try:
        yield session
    finally:
        await session.close()
        await trans.rollback()
        await conn.close()
        await engine.dispose()


class Despachadas:
    """Lo que el outbox encolo en Celery. `de()` drena los eventos pendientes de la
    transaccion de la prueba con sus manejadores reales, como haria `outbox.drenar`."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.enviadas: list[tuple[str, tuple[Any, ...]]] = []

    def _send_task(self, nombre: str, args: list[Any] | None = None, **opciones: Any) -> None:
        self.enviadas.append((nombre, tuple(args or ())))

    async def drenar(self) -> None:
        await self.db.flush()
        filas = await self.db.scalars(
            select(EventoSaliente)
            .where(EventoSaliente.procesado_en.is_(None))
            .order_by(EventoSaliente.created_at)
        )
        for fila in filas.all():
            for manejador in manejadores(fila.nombre):
                manejador(EventoDominio(nombre=fila.nombre, datos=fila.datos))
            fila.procesado_en = datetime.now(UTC)
        await self.db.flush()

    async def de(self, tarea: str) -> list[tuple[Any, ...]]:
        await self.drenar()
        return [args for t, args in self.enviadas if t == tarea]


@pytest_asyncio.fixture
async def tareas(db: AsyncSession, monkeypatch) -> Despachadas:
    """Las tareas Celery no salen a Redis: quedan registradas para las aserciones."""
    registro = Despachadas(db)
    monkeypatch.setattr(celery_app, "send_task", registro._send_task)
    return registro


class AlmacenamientoMemoria:
    def __init__(self) -> None:
        self.objetos: dict[str, tuple[bytes, str]] = {}

    def guardar_contenido(self, contenido: bytes, *, clave: str, content_type: str) -> None:
        self.objetos[clave] = (contenido, content_type)

    def url_firmada(self, clave: str, *, ttl: int | None = None, nombre: str | None = None) -> str:
        return f"https://almacenamiento.test/{clave}?firma=prueba"


@pytest.fixture(autouse=True)
def almacenamiento(monkeypatch) -> AlmacenamientoMemoria:
    """Sin MinIO en las pruebas: los adjuntos quedan en memoria."""
    falso = AlmacenamientoMemoria()
    falso.url_firmada_real = storage.url_firmada  # type: ignore[attr-defined]
    monkeypatch.setattr(storage, "guardar_contenido", falso.guardar_contenido)
    monkeypatch.setattr(storage, "url_firmada", falso.url_firmada)
    return falso


@pytest.fixture(autouse=True)
def sin_envios_reales(monkeypatch) -> None:
    """Ningun manejador del outbox llega a Redis aunque la prueba no pida `tareas`."""
    monkeypatch.setattr(celery_app, "send_task", lambda *a, **k: None)


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _get_db():
        # Igual que get_db real: confirma al final, revierte si hubo error.
        try:
            yield db
            await db.commit()
        except Exception:
            await db.rollback()
            raise

    app.dependency_overrides[get_db] = _get_db
    app.state.contador_peticiones.reiniciar()
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def crear_usuario(db: AsyncSession, email: str, rol: Rol, **extra: Any) -> Usuario:
    usuario = Usuario(
        email=email,
        nombre=email.split("@")[0],
        rol=rol,
        hashed_password=hash_password(PASSWORD),
        **extra,
    )
    db.add(usuario)
    await db.commit()
    return usuario


async def autenticar(client: AsyncClient, email: str, password: str) -> None:
    """Inicia sesion y deja la cookie httpOnly en el cliente. No hay token que
    manejar a mano: es justo el punto de usar cookie."""
    resp = await client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text


async def login(client: AsyncClient, email: str, password: str = PASSWORD) -> dict[str, str]:
    """Inicia sesion y devuelve la cabecera Cookie de ESA sesion.

    Las pruebas que alternan usuarios con el mismo cliente pasan la cabecera en cada
    peticion; el tarro de cookies del cliente se vacia para que no se mezclen.
    """
    resp = await client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    token = resp.cookies[settings.COOKIE_NAME]
    client.cookies.clear()
    return {"Cookie": f"{settings.COOKIE_NAME}={token}"}


@pytest_asyncio.fixture
async def usuario_admin(db: AsyncSession) -> Usuario:
    return await crear_usuario(db, "admin@timu.co", Rol.ADMIN)


@pytest_asyncio.fixture
async def admin(usuario_admin: Usuario) -> Usuario:
    return usuario_admin


@pytest_asyncio.fixture
async def headers(client: AsyncClient, admin: Usuario) -> dict[str, str]:
    return await login(client, admin.email)
