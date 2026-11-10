import json
import re
from collections.abc import AsyncGenerator, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from fastapi import Request
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    MetaData,
    Table,
    create_engine,
    event,
    func,
    text,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    SessionTransaction,
    mapped_column,
    sessionmaker,
)
from sqlalchemy.types import JSON
from uuid_utils.compat import uuid7

from app.core.config import ROL_APLICACION, settings

# --- Capa async: la usan los endpoints de FastAPI ----------------------------------------------
engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG, future=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# --- Capa sincrona: la usan las tareas de Celery -----------------------------------------------
# Celery no es async. Mezclar asyncio.run() con sesiones async dentro de una tarea
# produce loops por tarea y conexiones que no se reutilizan, asi que los workers
# hablan con la base de datos en modo sincrono. Ver sesion_worker().
sync_engine = create_engine(
    settings.DATABASE_URL_SYNC, echo=settings.DEBUG, future=True, pool_pre_ping=True
)
SessionWorker = sessionmaker(sync_engine, class_=Session, expire_on_commit=False)

# JSONB en PostgreSQL (indexable con GIN, consultable por operadores) y JSON en
# cualquier otro dialecto. Todo campo JSON de un modelo usa este tipo.
JSONTipo = JSON().with_variant(JSONB(), "postgresql")


# F0-01: los indices y las restricciones se nombran segun esta convencion en lugar
# de dejar que PostgreSQL invente el nombre. Sin ella, una migracion que quiera
# borrar o alterar una restriccion no tiene forma estable de referirse a ella.
CONVENCION_NOMBRES = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


# --- Contexto de la transaccion -----------------------------------------------------------------
# La base decide que filas ve y que puede escribir cada peticion (RLS, triggers de auditoria),
# y para eso necesita saber quien la hace. Cada sesion guarda su contexto en `session.info` y
# `_aplicar_contexto` lo fija con set_config(..., true) al comenzar cada transaccion: es local a
# la transaccion, asi que no se filtra a la siguiente peticion que reutilice la conexion (ni
# siquiera con PgBouncer en modo transaccion). Sin contexto, los ajustes quedan vacios y las
# politicas no devuelven filas: se falla cerrado.

CLAVE_CONTEXTO = "contexto_db"
# El rol vigente tambien queda en la conexion, para atribuir cada sentencia a un perfil al
# derivar la matriz de RLS (TIMU_REGISTRO_ACCESOS en tests/conftest.py).
CLAVE_ROL_CONEXION = "app.rol"


@dataclass(frozen=True)
class ContextoDb:
    """Quien hace la transaccion. `rol` es un `Rol`, "sistema" (workers, scripts, webhooks
    validados por firma) o "publico" (peticion sin sesion). `llaves` son los identificadores
    sobre los que actua una peticion publica (ver `acotar_publico`)."""

    rol: str
    usuario_id: UUID | None = None
    familia_id: UUID | None = None
    clinica_id: UUID | None = None
    request_id: str | None = None
    llaves: tuple[tuple[str, str], ...] = ()


SISTEMA = ContextoDb(rol="sistema")
PUBLICO = "publico"

# Identificadores con los que una peticion publica declara sobre quien actua. Las politicas
# de `publico` (app/core/permisos_db.py) solo admiten las filas que casan con ellos:
# - lo que trae la peticion: ingreso_email e ingreso_telefono (buscar la cuenta), renovacion
#   y token (hash del token de renovacion o del enlace), documento y tipo_documento, contacto_*
#   (formularios), encuesta (token del enlace), carnet (codigo);
# - lo que se deduce: usuario (cuenta identificada, aun sin credencial), autenticado (cuenta
#   que probo una credencial: contrasena, codigo, token o JWT firmado), sesion (sid del JWT),
#   revocar (cuenta cuyas sesiones se revocan por reuso de un token), familia.
LLAVES_PUBLICAS = frozenset(
    {
        "autenticado",
        "carnet",
        "contacto_email",
        "contacto_telefono",
        "documento",
        "encuesta",
        "familia",
        "ingreso_email",
        "ingreso_telefono",
        "referencia_pago",
        "registro",
        "renovacion",
        "revocar",
        "sesion",
        "tipo_documento",
        "token",
        "token_registro",
        "usuario",
    }
)

# Las unicas tablas en las que la aplicacion puede borrar: estado tecnico, sin valor de
# negocio ni de rastro. En el resto, las bajas y anulaciones son estados, y el unico borrado
# es la funcion anonimizar_familia() (fase 3 de docs/plan-persistencia.md).
BORRABLES = frozenset(
    {"sesiones", "tokens_uso_unico", "distancias_cache", "consumo_mapas", "eventos_salientes"}
)

_SQL_CONTEXTO = text(
    "SELECT set_config('app.rol', :rol, true), set_config('app.usuario_id', :usuario_id, true),"
    " set_config('app.familia_id', :familia_id, true),"
    " set_config('app.clinica_id', :clinica_id, true),"
    " set_config('app.request_id', :request_id, true),"
    " set_config('app.llaves', :llaves, true)"
)


def _parametros(contexto: ContextoDb) -> dict[str, str]:
    def texto(valor: Any) -> str:
        return "" if valor is None else str(valor)

    return {
        "rol": contexto.rol,
        "usuario_id": texto(contexto.usuario_id),
        "familia_id": texto(contexto.familia_id),
        "clinica_id": texto(contexto.clinica_id),
        "request_id": texto(contexto.request_id),
        "llaves": json.dumps(dict(contexto.llaves)) if contexto.llaves else "",
    }


@event.listens_for(Session, "after_begin")
def _aplicar_contexto(session: Session, _: SessionTransaction, conexion: Connection) -> None:
    contexto = session.info.get(CLAVE_CONTEXTO)
    if contexto is not None:
        conexion.execute(_SQL_CONTEXTO, _parametros(contexto))
        conexion.info[CLAVE_ROL_CONEXION] = contexto.rol


def fijar_contexto(session: Session, contexto: ContextoDb) -> None:
    """Cambia el contexto de la sesion. Si ya hay una transaccion abierta lo aplica en ella;
    las siguientes lo reciben al comenzar. Desde codigo async:
    `await db.run_sync(fijar_contexto, contexto)`."""
    session.info[CLAVE_CONTEXTO] = contexto
    if session.in_transaction():
        session.execute(_SQL_CONTEXTO, _parametros(contexto))
        session.connection().info[CLAVE_ROL_CONEXION] = contexto.rol


def contexto_de(session: Session) -> ContextoDb | None:
    return session.info.get(CLAVE_CONTEXTO)


def acotar_publico(session: Session, **llaves: object) -> None:
    """Declara sobre quien actua una peticion publica: la base solo le deja ver y escribir
    las filas que casan con estas llaves (LLAVES_PUBLICAS). Se llama donde el codigo ya sabe
    a quien busca o a quien identifico, con el mismo valor que usa la consulta. Con cualquier
    otro perfil no hace nada: los servicios que la llaman tambien los usa el equipo.
    Las llaves se acumulan; una llave en None no se fija."""
    desconocidas = set(llaves) - LLAVES_PUBLICAS
    if desconocidas:
        raise ValueError(f"Llaves publicas desconocidas: {sorted(desconocidas)}")
    contexto = contexto_de(session)
    if contexto is None or contexto.rol != PUBLICO:
        return
    nuevas = dict(contexto.llaves) | {k: str(v) for k, v in llaves.items() if v is not None}
    fijar_contexto(session, replace(contexto, llaves=tuple(sorted(nuevas.items()))))


def habilitar_rol_aplicacion(conexion: Connection, clave: str) -> None:
    """Da LOGIN y clave al rol de la aplicacion, que crea la migracion 0013. Corre con el
    dueno del esquema despues de las migraciones (`inicializar`, pruebas). La clave pasa
    por set_config y %L para no armar SQL concatenando texto."""
    conexion.execute(text("SELECT set_config('timu.clave_app', :clave, true)"), {"clave": clave})
    conexion.execute(
        text(
            f"DO $$ BEGIN EXECUTE format('ALTER ROLE {ROL_APLICACION} WITH LOGIN PASSWORD %L',"
            " current_setting('timu.clave_app')); END $$"
        )
    )


SQL_ROL_CONECTADO = text(
    "SELECT current_user, rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user"
)


def motivo_rol_privilegiado(fila: Any) -> str | None:
    """Recibe la fila de SQL_ROL_CONECTADO y devuelve el motivo si el rol salta las
    protecciones de la base (superusuario o BYPASSRLS), o None si es un rol de aplicacion.
    Ni la app, ni los workers, ni las pruebas corren asi: con un rol privilegiado RLS no se
    aplica y una politica rota pasaria inadvertida."""
    if fila.rolsuper or fila.rolbypassrls:
        return f"el rol {fila.current_user} es superusuario o tiene BYPASSRLS"
    return None


async def rol_con_privilegios(conexion: Any) -> str | None:
    return motivo_rol_privilegiado((await conexion.execute(SQL_ROL_CONECTADO)).one())


def nombre_enum_db(clase: type[StrEnum]) -> str:
    """Nombre del enum de PostgreSQL de un StrEnum: su nombre de clase en snake_case."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", clase.__name__).lower()


def EnumDb(clase: type[StrEnum]) -> SAEnum:  # noqa: N802 - se usa como un tipo de columna
    """Tipo de columna para un conjunto cerrado: enum nativo de PostgreSQL con los valores del
    StrEnum. La base rechaza cualquier otro valor y Python tambien (`validate_strings`), asi
    que un literal mal escrito falla en la prueba, no en produccion."""
    return SAEnum(
        clase,
        name=nombre_enum_db(clase),
        native_enum=True,
        create_constraint=False,
        validate_strings=True,
        values_callable=lambda e: [m.value for m in e],
    )


class Base(DeclarativeBase):
    """Base declarativa. Todos los modelos de dominio heredan de aqui."""

    metadata = MetaData(naming_convention=CONVENCION_NOMBRES)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


def nuevo_id() -> UUID:
    """UUIDv7 (RFC 9562): los primeros 48 bits son el milisegundo de creacion, asi que los IDs
    nuevos caen al final del indice en vez de repartirse por todo el arbol como los v4. Solo
    hace falta llamarlo cuando el ID se necesita antes del flush; si no, lo pone la columna."""
    return uuid7()


class UUIDMixin:
    # Tres capas para el mismo estandar: el ORM lo genera en Python, la base lo genera si
    # alguien inserta por SQL sin id, y un CHECK (`_restricciones_de_la_tabla`) rechaza
    # cualquier id que no sea v7.
    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=nuevo_id, server_default=text("uuidv7()")
    )


@event.listens_for(Base, "after_mapper_constructed", propagate=True)
def _restricciones_de_la_tabla(_: Any, clase: type) -> None:
    """Restricciones que la base hace cumplir, declaradas junto al modelo:

    - el CHECK de version 7 de cada modelo con UUIDMixin;
    - `__checks__ = {"nombre": "expresion SQL"}`: invariantes de la fila (rangos, formatos,
      campos que exige un estado). Se llaman `ck_<tabla>_<nombre>`;
    - `__unicos__ = {"nombre": (["columnas"], "condicion" | None)}`: unicidad, parcial si
      lleva condicion ("solo un contrato vigente por familia"). Se llaman `uq_<tabla>_<nombre>`.

    Van a nivel de tabla porque el autogenerate de Alembic descarta los CHECK de columna. El
    autogenerate tampoco detecta un CHECK nuevo en una tabla existente: su migracion se
    escribe a mano, y `test_persistencia` falla si el modelo y la base no coinciden."""
    tabla = getattr(clase, "__table__", None)
    if not isinstance(tabla, Table):
        return
    if issubclass(clase, UUIDMixin):
        tabla.append_constraint(CheckConstraint("uuid_extract_version(id) = 7", name="id_uuidv7"))
    for nombre, expresion in getattr(clase, "__checks__", {}).items():
        tabla.append_constraint(CheckConstraint(expresion, name=nombre))
    for nombre, (columnas, condicion) in getattr(clase, "__unicos__", {}).items():
        Index(
            f"uq_{tabla.name}_{nombre}",
            *(tabla.c[c] for c in columnas),
            unique=True,
            postgresql_where=text(condicion) if condicion else None,
        )


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Sesion de la peticion. Empieza con contexto "publico"; la autenticacion lo sustituye
    por el del usuario (`app.api.deps`)."""
    async with SessionLocal() as session:
        session.sync_session.info[CLAVE_CONTEXTO] = ContextoDb(
            rol=PUBLICO, request_id=getattr(request.state, "request_id", None)
        )
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@contextmanager
def sesion_worker() -> Iterator[Session]:
    """Sesion sincrona para las tareas de Celery, con la misma politica que get_db:
    commit al terminar bien, rollback ante cualquier excepcion.

    Uso:
        with sesion_worker() as db:
            db.add(...)
    """
    session = SessionWorker(info={CLAVE_CONTEXTO: SISTEMA})
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
