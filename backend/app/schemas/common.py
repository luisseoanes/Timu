"""F0-10 Contrato unico de listados: paginacion, orden y respuesta `Page`.

Uso en un router:

    @router.get("", response_model=Page[FamiliaRead])
    async def listar(db: DbSession, _: CurrentUser, params: ParamsListado) -> Page[FamiliaRead]:
        stmt = select(Familia).where(...)
        return await paginar(db, stmt, params, ORDEN_FAMILIAS, FamiliaRead)

`orden` recibe una lista separada por comas; el prefijo `-` indica descendente:
`?orden=-created_at,titular_nombre`. Solo se aceptan campos declarados en el mapa del
modulo, y siempre se agrega el id como desempate para que la paginacion sea estable.
"""

from collections.abc import Mapping
from typing import Annotated, Any, Generic, TypeVar

from fastapi import Depends, Query
from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.core.errores import ErrorDominio

T = TypeVar("T")
S = TypeVar("S", bound=BaseModel)

LIMITE_POR_DEFECTO = 50
LIMITE_MAXIMO = 200


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


class Mensaje(BaseModel):
    detail: str


class Paginacion(BaseModel):
    limit: int
    offset: int
    orden: list[str]


def _params_listado(
    limit: Annotated[int, Query(ge=1, le=LIMITE_MAXIMO)] = LIMITE_POR_DEFECTO,
    offset: Annotated[int, Query(ge=0)] = 0,
    orden: Annotated[
        str | None, Query(description="Campos separados por coma; prefijo '-' = descendente")
    ] = None,
) -> Paginacion:
    campos = [c.strip() for c in (orden or "").split(",") if c.strip()]
    return Paginacion(limit=limit, offset=offset, orden=campos)


ParamsListado = Annotated[Paginacion, Depends(_params_listado)]


class OrdenInvalido(ErrorDominio):
    status_code = 422
    codigo = "validacion"


def aplicar_orden(
    stmt: Select[Any],
    orden: list[str],
    campos: Mapping[str, InstrumentedAttribute[Any]],
    por_defecto: str,
    desempate: InstrumentedAttribute[Any],
) -> Select[Any]:
    clausulas = []
    for campo in orden or [por_defecto]:
        nombre = campo.lstrip("-")
        if nombre not in campos:
            permitidos = ", ".join(sorted(campos))
            raise OrdenInvalido(f"No se puede ordenar por '{nombre}'. Permitidos: {permitidos}")
        col = campos[nombre]
        clausulas.append(col.desc() if campo.startswith("-") else col.asc())
    return stmt.order_by(*clausulas, desempate.asc())


async def paginar(
    db: AsyncSession,
    stmt: Select[Any],
    params: Paginacion,
    schema: type[S],
    *,
    campos_orden: Mapping[str, InstrumentedAttribute[Any]],
    orden_por_defecto: str,
    desempate: InstrumentedAttribute[Any],
) -> Page[S]:
    total = await db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    ordenado = aplicar_orden(stmt, params.orden, campos_orden, orden_por_defecto, desempate)
    filas = (await db.execute(ordenado.limit(params.limit).offset(params.offset))).scalars()
    return Page[schema](  # type: ignore[valid-type]
        items=[schema.model_validate(f) for f in filas],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )
