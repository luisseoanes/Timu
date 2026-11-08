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
from pathlib import Path  # noqa: E402
from typing import Any  # noqa: E402

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from fastapi import Request  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import create_engine, make_url, select, text  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402

import app.workers.tasks.cartera  # noqa: E402, F401  registra los manejadores del outbox
import app.workers.tasks.comunicaciones  # noqa: E402, F401
import app.workers.tasks.encuestas  # noqa: E402, F401
import app.workers.tasks.familias  # noqa: E402, F401
import app.workers.tasks.ia  # noqa: E402, F401
import app.workers.tasks.rutas  # noqa: E402, F401
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from app.core.config import ROL_APLICACION, settings  # noqa: E402
from app.core.database import (  # noqa: E402
    CLAVE_CONTEXTO,
    SISTEMA,
    SQL_ROL_CONECTADO,
    Base,
    ContextoDb,
    fijar_contexto,
    get_db,
    habilitar_rol_aplicacion,
    motivo_rol_privilegiado,
)
from app.core.enums import Rol  # noqa: E402
from app.core.outbox import EventoSaliente, procesar_pendientes  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.integrations import storage  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base as _  # noqa: E402, F401  asegura el registro de todos los modelos
from app.modules.auth.models import Usuario  # noqa: E402
from app.modules.catalogos.service import cargar as cargar_catalogos  # noqa: E402
from app.modules.reglas.service import sembrar as sembrar_reglas  # noqa: E402
from app.workers.celery_app import celery_app  # noqa: E402

# Dueno del esquema: solo aplica las migraciones y da LOGIN al rol de la aplicacion.
URL_ASYNC = os.getenv(
    "TEST_DATABASE_URL", "postgresql+asyncpg://timu:timu@localhost:5433/timu_test"
)
URL_SYNC = URL_ASYNC.replace("postgresql+asyncpg://", "postgresql+psycopg://")
# Las pruebas corren con el mismo rol que la aplicacion. Con el dueno del esquema, que es
# superusuario, la base no aplicaria sus politicas y la suite quedaria en verde aunque
# estuvieran rotas.
URL_APP_ASYNC = (
    make_url(URL_ASYNC)
    .set(username=ROL_APLICACION, password=settings.APP_DB_PASSWORD)
    .render_as_string(hide_password=False)
)
URL_APP_SYNC = URL_APP_ASYNC.replace("postgresql+asyncpg://", "postgresql+psycopg://")
PASSWORD = "secreto123"


# --- Registro de accesos por perfil (para derivar la matriz de RLS) ------------------------
# Con TIMU_REGISTRO_ACCESOS=<ruta>, cada (perfil, operacion, tabla) distinto que ejecuta la
# suite se anota en esa ruta, una linea JSON por combinacion. Es la evidencia de que lee y
# escribe cada perfil; docs/plan-persistencia.md (fase 4) explica como se usa.

_RUTA_ACCESOS = os.getenv("TIMU_REGISTRO_ACCESOS")
if _RUTA_ACCESOS:
    import json as _json
    import re as _re

    from sqlalchemy import event as _event
    from sqlalchemy.engine import Engine as _Engine

    from app.core.database import CLAVE_ROL_CONEXION as _CLAVE_ROL

    _tablas = set(Base.metadata.tables)
    _vistos: set[tuple[str, str, str, str]] = set()

    def _accesos(sql: str) -> set[tuple[str, str]]:
        texto = " ".join(sql.split()).lower()
        escritas: set[tuple[str, str]] = set()
        for op, patron in (
            ("insert", r"\binsert into ([a-z_]+)"),
            ("update", r"\bupdate ([a-z_]+) set\b"),
            ("delete", r"\bdelete from ([a-z_]+)"),
        ):
            escritas |= {(op, t) for t in _re.findall(patron, texto)}
        leidas = {("select", t) for t in _re.findall(r"\b(?:from|join) ([a-z_]+)", texto)}
        borradas = {t for op, t in escritas if op == "delete"}
        leidas = {(op, t) for op, t in leidas if t not in borradas or "where" in texto}
        return {(op, t) for op, t in escritas | leidas if t in _tablas}

    @_event.listens_for(_Engine, "before_cursor_execute")
    def _registrar_acceso(conn, cursor, statement, parameters, context, executemany) -> None:
        rol = conn.info.get(_CLAVE_ROL)
        if rol is None:
            return
        ruta = conn.info.get("ruta", "-")
        nuevos = {(str(rol), ruta, op, t) for op, t in _accesos(statement)} - _vistos
        if nuevos:
            _vistos.update(nuevos)
            with open(_RUTA_ACCESOS, "a") as fichero:
                for fila in sorted(nuevos):
                    fichero.write(_json.dumps(fila) + "\n")


# --- Guardas de la suite ----------------------------------------------------------------------
# El CI tiene que ejecutar todas las pruebas y todas tienen que comprobar algo. pytest no
# falla ni ante una prueba saltada ni ante un marcador que miente, asi que se fuerza aqui.


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Cada prueba queda marcada `unit` o `integration`, sin depender de que alguien se
    acuerde: la que usa el fixture `db` es de integracion. `pytest -m unit` y
    `pytest -m integration` suman asi la suite entera, sin pruebas huerfanas de marcador.
    Una marcada `integration` a mano sin `db` se respeta (puede tocar la base por otra via,
    como las migraciones); una marcada `unit` que usa la base es un error."""
    for item in items:
        usa_db = "db" in getattr(item, "fixturenames", ())
        marcas = {m.name for m in item.iter_markers()} & {"unit", "integration"}
        if usa_db and "unit" in marcas:
            raise pytest.UsageError(f"{item.nodeid} esta marcada unit pero usa la base de datos")
        if len(marcas) == 2:
            # Pasa con un `pytestmark` de modulo y una marca distinta en la funcion: pytest
            # aplica las dos y la prueba cuenta en ambos grupos.
            raise pytest.UsageError(f"{item.nodeid} esta marcada unit e integration a la vez")
        if not marcas:
            item.add_marker("integration" if usa_db else "unit")


_no_ejecutadas: set[str] = set()


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    if report.skipped or hasattr(report, "wasxfail"):
        _no_ejecutadas.add(report.nodeid)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Una prueba saltada o marcada xfail no comprueba nada y deja la suite en verde: se
    trata como un fallo. Si no puede pasar, se arregla o se borra."""
    if _no_ejecutadas and exitstatus == pytest.ExitCode.OK:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED


def pytest_terminal_summary(terminalreporter: Any) -> None:
    if _no_ejecutadas:
        terminalreporter.section("pruebas saltadas o xfail (no se admiten)", red=True)
        for nodeid in sorted(_no_ejecutadas):
            terminalreporter.write_line(nodeid)


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
    with engine.begin() as conn:
        habilitar_rol_aplicacion(conn, settings.APP_DB_PASSWORD)
    app_engine = create_engine(URL_APP_SYNC)
    with app_engine.connect() as conn:
        motivo = motivo_rol_privilegiado(conn.execute(SQL_ROL_CONECTADO).one())
    app_engine.dispose()
    if motivo:
        pytest.exit(f"Las pruebas no corren con un rol privilegiado: {motivo}", returncode=1)
    yield
    # Todo el esquema y no tabla a tabla: las politicas de RLS de una tabla dependen de otras.
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
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
    engine = create_async_engine(URL_APP_ASYNC, poolclass=None)
    conn = await engine.connect()
    trans = await conn.begin()
    # Las fabricas y las aserciones directas actuan como el sistema; cada peticion del
    # fixture `client` cambia al contexto de su usuario y al terminar vuelve a este.
    session = AsyncSession(
        bind=conn,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
        info={CLAVE_CONTEXTO: SISTEMA},
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
    transaccion de la prueba con `procesar_pendientes`, la misma funcion que usa la
    tarea `outbox.drenar`, y con los manejadores reales."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.enviadas: list[tuple[str, tuple[Any, ...]]] = []

    def _send_task(self, nombre: str, args: list[Any] | None = None, **opciones: Any) -> None:
        self.enviadas.append((nombre, tuple(args or ())))

    async def drenar(self) -> None:
        """Drena por lotes hasta vaciar. En produccion un manejador que falla se reintenta
        en silencio; en una prueba eso esconderia el fallo, asi que se hace explotar."""
        while True:
            resultado = await self.db.run_sync(procesar_pendientes)
            if resultado["fallidos"]:
                errores = await self.db.scalars(
                    select(EventoSaliente.ultimo_error).where(
                        EventoSaliente.procesado_en.is_(None),
                        EventoSaliente.ultimo_error.is_not(None),
                    )
                )
                raise AssertionError(f"un manejador del outbox fallo: {errores.all()}")
            if not resultado["despachados"]:
                return

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
    """Sin almacenamiento S3 en las pruebas: los adjuntos quedan en memoria."""
    falso = AlmacenamientoMemoria()
    falso.url_firmada_real = storage.url_firmada  # type: ignore[attr-defined]
    monkeypatch.setattr(storage, "guardar_contenido", falso.guardar_contenido)
    monkeypatch.setattr(storage, "url_firmada", falso.url_firmada)
    return falso


@pytest.fixture(autouse=True)
def cache_limpia() -> Iterator[None]:
    """La cache del dashboard vive en memoria del proceso: cada prueba arranca sin ella."""
    from app.core import cache

    cache.obtener().limpiar()
    yield
    cache.obtener().limpiar()


@pytest.fixture(autouse=True)
def sin_envios_reales(monkeypatch) -> None:
    """Ningun manejador del outbox llega a Redis aunque la prueba no pida `tareas`."""
    monkeypatch.setattr(celery_app, "send_task", lambda *a, **k: None)


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _get_db(request: Request):
        # Igual que get_db real: arranca como peticion sin sesion (la autenticacion cambia el
        # contexto), confirma al final y revierte si hubo error.
        await db.run_sync(
            fijar_contexto,
            ContextoDb(rol="publico", request_id=getattr(request.state, "request_id", None)),
        )
        if _RUTA_ACCESOS:
            # Modo registro: la peticion usa su propia sesion sobre la misma conexion y
            # transaccion, con el identity map vacio. Asi toda lectura llega a la base y queda
            # anotada; con la sesion compartida, un objeto ya cargado por la prueba se servia
            # de memoria y su lectura no aparecia en la matriz.
            ruta = request.scope.get("route")
            conexion = await db.connection()
            conexion.sync_connection.info["ruta"] = (  # type: ignore[union-attr]
                f"{request.method} {getattr(ruta, 'path', request.url.path)}"
            )
            propia = AsyncSession(
                bind=conexion,
                expire_on_commit=False,
                join_transaction_mode="create_savepoint",
                info={CLAVE_CONTEXTO: db.sync_session.info[CLAVE_CONTEXTO]},
            )
            try:
                yield propia
                await propia.commit()
            except Exception:
                await propia.rollback()
                raise
            finally:
                await propia.close()
                conexion.sync_connection.info.pop("ruta", None)  # type: ignore[union-attr]
                await db.run_sync(fijar_contexto, SISTEMA)
            return
        try:
            yield db
            await db.commit()
        except Exception:
            await db.rollback()
            raise
        finally:
            await db.run_sync(fijar_contexto, SISTEMA)

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
