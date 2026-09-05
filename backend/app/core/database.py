from collections.abc import AsyncGenerator, Iterator
from contextlib import contextmanager
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, create_engine, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.types import JSON

from app.core.config import settings

# --- Capa async: la usan los endpoints de FastAPI ---
engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG, future=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# --- Capa sincrona: la usan las tareas de Celery ---
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


class Base(DeclarativeBase):
    """Base declarativa. Todos los modelos de dominio heredan de aqui."""


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class UUIDMixin:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
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
    session = SessionWorker()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
