from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import EstadoAfiliacion
from app.core.scope import Alcance, restringir
from app.modules.familias.models import Familia, Mascota
from app.modules.familias.schemas import FamiliaCreate, FamiliaUpdate, MascotaCreate


async def listar(
    db: AsyncSession,
    alcance: Alcance,
    *,
    q: str | None = None,
    ciudad: str | None = None,
    estado: EstadoAfiliacion | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Familia], int]:
    """6.16 Segmentacion: filtros combinables para campanas y reportes.

    El alcance se aplica antes que cualquier filtro: para el portal, una familia solo
    se ve a si misma por mucho que juegue con los parametros de busqueda.
    """
    stmt = restringir(select(Familia), Familia, alcance)
    if q:
        patron = f"%{q}%"
        stmt = stmt.where(
            or_(
                Familia.titular_nombre.ilike(patron),
                Familia.documento.ilike(patron),
                Familia.telefono.ilike(patron),
            )
        )
    if ciudad:
        stmt = stmt.where(Familia.ciudad == ciudad)
    if estado:
        stmt = stmt.where(Familia.estado == estado)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    result = await db.execute(stmt.order_by(Familia.created_at.desc()).limit(limit).offset(offset))
    return list(result.scalars().all()), total


async def obtener(db: AsyncSession, alcance: Alcance, familia_id: UUID) -> Familia | None:
    """Lectura por id, tambien acotada: pedir el id de otra familia devuelve None,
    que el router traduce a 404. No se distingue "no existe" de "no es tuya"."""
    stmt = restringir(select(Familia).where(Familia.id == familia_id), Familia, alcance)
    return await db.scalar(stmt)


async def crear(db: AsyncSession, data: FamiliaCreate) -> Familia:
    familia = Familia(**data.model_dump(exclude={"mascotas"}))
    familia.mascotas = [Mascota(**m.model_dump()) for m in data.mascotas]
    db.add(familia)
    await db.flush()
    return familia


async def actualizar(db: AsyncSession, familia: Familia, data: FamiliaUpdate) -> Familia:
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(familia, campo, valor)
    await db.flush()
    return familia


async def agregar_mascota(db: AsyncSession, familia: Familia, data: MascotaCreate) -> Mascota:
    mascota = Mascota(familia_id=familia.id, **data.model_dump())
    db.add(mascota)
    await db.flush()
    return mascota
