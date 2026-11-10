"""Lo que la base garantiza por si misma, sin depender de Python (docs/plan-persistencia.md).

Base de todo lo demas: la aplicacion y las pruebas se conectan con un rol sin privilegios,
y cada transaccion lleva el contexto de quien la hace. Sin eso, las restricciones de la base
no se aplicarian a la aplicacion o no sabrian a quien aplicarlas.
"""

import contextlib
import json
import pathlib
import re
from datetime import date
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import CheckConstraint, create_engine, make_url, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from starlette.requests import Request

from app.api.deps import get_alcance, get_current_user
from app.core.config import ROL_APLICACION
from app.core.database import (
    BORRABLES,
    CLAVE_CONTEXTO,
    LLAVES_PUBLICAS,
    SISTEMA,
    SQL_ROL_CONECTADO,
    Base,
    ContextoDb,
    acotar_publico,
    fijar_contexto,
    motivo_rol_privilegiado,
    nombre_enum_db,
    nuevo_id,
)
from app.core.enums import Rol
from app.core.permisos_db import CATALOGOS, CONDICIONES
from app.core.security import hash_password
from app.modules.auth.models import Usuario
from app.modules.catalogos.models import Especie
from app.modules.familias.models import Familia
from tests import fabricas
from tests.conftest import URL_APP_ASYNC, URL_SYNC, login

_AJUSTES = text(
    "SELECT current_setting('app.rol', true) AS rol,"
    " current_setting('app.usuario_id', true) AS usuario_id,"
    " current_setting('app.familia_id', true) AS familia_id,"
    " current_setting('app.clinica_id', true) AS clinica_id"
)


async def _ajustes(db: AsyncSession) -> dict[str, str | None]:
    return dict((await db.execute(_AJUSTES)).mappings().one())


def _peticion(cookie: str) -> Request:
    return Request({"type": "http", "headers": [(b"cookie", cookie.encode())], "state": {}})


# --- Rol de conexion --------------------------------------------------------------------------


async def test_las_pruebas_corren_con_el_rol_de_la_aplicacion(db: AsyncSession):
    fila = (await db.execute(SQL_ROL_CONECTADO)).one()
    assert fila.current_user == ROL_APLICACION
    assert motivo_rol_privilegiado(fila) is None


@pytest.mark.integration
def test_el_dueno_del_esquema_no_sirve_para_la_aplicacion():
    """El guarda que impide arrancar API, worker y pruebas con un rol privilegiado."""
    engine = create_engine(URL_SYNC)
    with engine.connect() as conn:
        motivo = motivo_rol_privilegiado(conn.execute(SQL_ROL_CONECTADO).one())
    engine.dispose()
    assert motivo is not None and "BYPASSRLS" in motivo


async def test_la_aplicacion_no_puede_cambiar_el_esquema(db: AsyncSession):
    with pytest.raises(Exception, match="permission denied|permiso denegado"):
        await db.execute(text("CREATE TABLE intrusa (id int)"))


async def test_la_aplicacion_no_toca_el_historial_de_migraciones(db: AsyncSession):
    with pytest.raises(Exception, match="permission denied|permiso denegado"):
        await db.execute(text("SELECT * FROM alembic_version"))


# --- Contexto de la transaccion ---------------------------------------------------------------


@pytest.mark.integration
async def test_el_contexto_se_aplica_en_cada_transaccion_y_no_se_filtra():
    """Con una sesion real (no la de la prueba, que nunca confirma de verdad): el contexto
    se vuelve a fijar al empezar cada transaccion y muere con ella, asi que una conexion
    reutilizada no arrastra el usuario de la peticion anterior."""
    engine = create_async_engine(URL_APP_ASYNC, pool_size=1, max_overflow=0)
    usuario = uuid4()
    try:
        async with AsyncSession(
            engine, info={CLAVE_CONTEXTO: ContextoDb(rol=Rol.MEDICO, usuario_id=usuario)}
        ) as session:
            assert await _ajustes(session) == {
                "rol": "medico",
                "usuario_id": str(usuario),
                "familia_id": "",
                "clinica_id": "",
            }
            await session.commit()
            # Otra transaccion, sobre la misma (unica) conexion del pool.
            assert (await _ajustes(session))["usuario_id"] == str(usuario)
        async with AsyncSession(engine) as sin_contexto:
            # Misma conexion fisica, sesion sin contexto: no queda rastro del anterior.
            assert (await _ajustes(sin_contexto))["rol"] in (None, "")
    finally:
        await engine.dispose()


async def test_cambiar_el_contexto_aplica_en_la_transaccion_abierta(db: AsyncSession):
    assert (await _ajustes(db))["rol"] == "sistema"
    otro = ContextoDb(rol=Rol.OPERACIONES, usuario_id=uuid4())
    await db.run_sync(fijar_contexto, otro)
    assert await _ajustes(db) == {
        "rol": "operaciones",
        "usuario_id": str(otro.usuario_id),
        "familia_id": "",
        "clinica_id": "",
    }
    await db.run_sync(fijar_contexto, SISTEMA)


async def test_una_peticion_autenticada_lleva_su_usuario_a_la_base(
    client: AsyncClient, db: AsyncSession, admin: Usuario
):
    cabecera = await login(client, admin.email)
    await db.run_sync(fijar_contexto, ContextoDb(rol="publico"))
    usuario = await get_current_user(_peticion(cabecera["Cookie"]), db)
    assert await _ajustes(db) == {
        "rol": "admin",
        "usuario_id": str(admin.id),
        "familia_id": "",
        "clinica_id": "",
    }
    assert usuario.id == admin.id
    await db.run_sync(fijar_contexto, SISTEMA)


async def test_una_familia_lleva_su_familia_a_la_base(client: AsyncClient, db: AsyncSession):
    usuario = Usuario(
        email="ana@ejemplo.co", nombre="Ana", rol=Rol.FAMILIA, hashed_password=hash_password("x")
    )
    db.add(usuario)
    await db.flush()
    familia = Familia(
        titular_nombre="Ana",
        documento="111",
        telefono="+573000000000",
        ciudad="Bogota",
        barrio="Centro",
        usuario_portal_id=usuario.id,
    )
    db.add(familia)
    await db.commit()
    cabecera = await login(client, "ana@ejemplo.co", "x")

    await db.run_sync(fijar_contexto, ContextoDb(rol="publico"))
    sujeto = await get_current_user(_peticion(cabecera["Cookie"]), db)
    await get_alcance(sujeto, db)
    ajustes = await _ajustes(db)
    assert ajustes["rol"] == "familia"
    assert ajustes["familia_id"] == str(familia.id)
    await db.run_sync(fijar_contexto, SISTEMA)


async def test_una_peticion_sin_sesion_es_publica(client: AsyncClient, db: AsyncSession):
    """El sustituto de get_db de las pruebas empieza igual que el real: como peticion
    publica. Si empezara como sistema, las rutas abiertas se probarian con mas permisos de
    los que tienen en produccion."""
    vistos: list[str | None] = []
    from app.core.database import get_db
    from app.main import app

    sustituto = app.dependency_overrides[get_db]

    async def espia(request: Request):
        # Envuelve al sustituto sin cambiar su comportamiento: le entrega la excepcion de
        # la peticion (aqui, el 401) o lo deja terminar, para que corra su limpieza.
        real = sustituto(request)
        sesion = await anext(real)
        vistos.append((await _ajustes(sesion))["rol"])
        try:
            yield sesion
        except Exception as exc:
            with contextlib.suppress(type(exc)):
                await real.athrow(exc)
            raise
        else:
            with contextlib.suppress(StopAsyncIteration):
                await anext(real)

    app.dependency_overrides[get_db] = espia
    try:
        await client.post("/api/v1/auth/login", data={"username": "nadie@x.co", "password": "x"})
    finally:
        app.dependency_overrides[get_db] = sustituto
    assert vistos == ["publico"]
    assert (await _ajustes(db))["rol"] == "sistema"


# --- UUIDv7 -----------------------------------------------------------------------------------


async def test_toda_tabla_tiene_id_uuidv7_generado_y_exigido_por_la_base(db: AsyncSession):
    """Guarda: una tabla nueva sin UUIDMixin, o una migracion escrita a mano que olvide el
    default o el CHECK, hace fallar la suite."""
    filas = (
        await db.execute(
            text(
                """
                SELECT c.relname AS tabla,
                       (SELECT array_agg(a.attname) FROM pg_constraint k
                          JOIN pg_attribute a ON a.attrelid = k.conrelid
                                             AND a.attnum = ANY(k.conkey)
                         WHERE k.conrelid = c.oid AND k.contype = 'p') AS pk,
                       format_type(i.atttypid, i.atttypmod) AS tipo,
                       pg_get_expr(d.adbin, d.adrelid) AS por_defecto,
                       (SELECT pg_get_constraintdef(k.oid) FROM pg_constraint k
                         WHERE k.conrelid = c.oid
                           AND k.conname = 'ck_' || c.relname || '_id_uuidv7') AS chequeo
                FROM pg_class c
                LEFT JOIN pg_attribute i ON i.attrelid = c.oid AND i.attname = 'id'
                LEFT JOIN pg_attrdef d ON d.adrelid = c.oid AND d.adnum = i.attnum
                WHERE c.relnamespace = 'public'::regnamespace AND c.relkind = 'r'
                  AND c.relname <> 'alembic_version'
                """
            )
        )
    ).all()
    assert len(filas) >= 64
    malas = [
        f.tabla
        for f in filas
        if f.pk != ["id"]
        or f.tipo != "uuid"
        or f.por_defecto != "uuidv7()"
        or f.chequeo != "CHECK ((uuid_extract_version(id) = 7))"
    ]
    assert malas == [], f"Tablas sin id UUIDv7 generado y exigido por la base: {malas}"


@pytest.mark.unit
def test_nuevo_id_genera_uuidv7_ordenados():
    ids = [nuevo_id() for _ in range(1000)]
    assert {i.version for i in ids} == {7}
    assert ids == sorted(ids)
    assert len(set(ids)) == len(ids)


async def test_el_orm_y_la_base_rechazan_ids_que_no_son_v7(db: AsyncSession):
    especie = Especie(codigo="ave", nombre="Ave")
    db.add(especie)
    await db.flush()
    assert especie.id.version == 7
    with pytest.raises(IntegrityError, match="ck_especies_id_uuidv7"):
        db.add(Especie(id=uuid4(), codigo="pez", nombre="Pez"))
        await db.flush()


# --- Conjuntos cerrados: enums nativos ---------------------------------------------------------

# Columnas con nombre de conjunto cerrado que a proposito no lo son, con el porque.
_ABIERTAS = {
    ("eventos_pasarela", "tipo"): "lo define la pasarela",
    ("cuotas", "tipo"): "lleva un contador (ajuste, ajuste2...): CHECK de patron",
}
_NOMBRE_DE_CONJUNTO = re.compile(
    r"^(estado(_\w+)?|tipo|tipo_documento|canal(_\w+)?|rol|prioridad|area|etapa|modalidad"
    r"|proposito|periodicidad|recurrencia|categoria|medio_\w+|proveedor|sexo|geo_precision"
    r"|accion|evento|modo|periodo_cupo)$"
)


async def test_cada_enum_del_modelo_coincide_con_el_de_la_base(db: AsyncSession):
    """Guarda: un valor anadido al StrEnum sin su migracion (o al reves) hace fallar la
    suite. Sin esto, el valor nuevo explota en la primera escritura en produccion."""
    en_base = {
        nombre: list(etiquetas)
        for nombre, etiquetas in (
            await db.execute(
                text(
                    "SELECT t.typname, array_agg(e.enumlabel ORDER BY e.enumsortorder)"
                    " FROM pg_type t JOIN pg_enum e ON e.enumtypid = t.oid"
                    " WHERE t.typnamespace = 'public'::regnamespace GROUP BY t.typname"
                )
            )
        ).tuples()
    }
    usados: set[str] = set()
    for tabla in Base.metadata.tables.values():
        for columna in tabla.columns:
            if not isinstance(columna.type, SAEnum):
                continue
            clase = columna.type.enum_class
            assert clase is not None and issubclass(clase, StrEnum), f"{tabla.name}.{columna.name}"
            assert columna.type.name == nombre_enum_db(clase), f"{tabla.name}.{columna.name}"
            assert en_base.get(columna.type.name) == [m.value for m in clase], (
                f"El enum {columna.type.name} de la base no coincide con {clase.__name__}:"
                f" falta la migracion que lo actualice"
            )
            usados.add(columna.type.name)
    assert set(en_base) == usados, f"Enums de la base sin columna: {set(en_base) - usados}"


async def test_ningun_conjunto_cerrado_queda_como_texto_libre(db: AsyncSession):
    filas = await db.execute(
        text(
            "SELECT table_name, column_name FROM information_schema.columns"
            " WHERE table_schema = 'public' AND data_type IN ('character varying', 'text')"
        )
    )
    libres = [
        f"{t}.{c}"
        for t, c in filas.tuples()
        if _NOMBRE_DE_CONJUNTO.match(c) and (t, c) not in _ABIERTAS
    ]
    assert libres == [], (
        f"Columnas de conjunto cerrado como texto libre: {libres}. Tipalas con EnumDb(...) o,"
        " si de verdad son abiertas, anadelas a _ABIERTAS con el motivo."
    )


async def test_la_base_rechaza_un_valor_fuera_del_enum(db: AsyncSession):
    with pytest.raises(Exception, match="invalid input value for enum estado_tarea"):
        await db.execute(
            text(
                "INSERT INTO tareas (titulo, area, prioridad, estado)"
                " VALUES ('x', 'comercial', 'media', 'inventado')"
            )
        )


@pytest.mark.unit
def test_los_eventos_de_regla_son_los_del_motor():
    """El enum de la base y el registro del motor describen el mismo conjunto: un evento
    nuevo en el motor sin su valor en EventoRegla (y su migracion) no podria guardarse."""
    from app.core.enums import EventoRegla
    from app.modules.reglas.motor import EVENTOS

    assert {e.value for e in EventoRegla} == set(EVENTOS)


async def test_los_listados_ordenan_un_enum_por_su_texto(db: AsyncSession):
    """Un enum de PostgreSQL ordena por su declaracion (leido antes que fallido); los
    listados conservan el orden alfabetico que tenian cuando la columna era texto."""
    from sqlalchemy import select

    from app.modules.comunicaciones.models import Mensaje
    from app.schemas.common import aplicar_orden

    for estado in ("leido", "fallido", "encolado"):
        db.add(Mensaje(canal="whatsapp", destino="573000000000", estado=estado))
    await db.flush()
    stmt = aplicar_orden(
        select(Mensaje.estado), ["estado"], {"estado": Mensaje.estado}, "estado", Mensaje.id
    )
    assert list(await db.scalars(stmt)) == ["encolado", "fallido", "leido"]


# --- Referencias a catalogos -------------------------------------------------------------------

_REFERENCIAS_SIN_LLAVE = {
    ("interesados", "ciudad"): "un interesado puede venir de una ciudad sin cobertura",
    ("servicio_pasos", "paso_codigo"): "el paso lo define el JSON del tipo de servicio",
}
_NOMBRE_DE_REFERENCIA = re.compile(r"^(ciudad|especie|plan_sugerido|\w+_codigo)$")


async def test_toda_referencia_a_un_catalogo_tiene_llave_foranea(db: AsyncSession):
    """Guarda: una columna nueva que guarda un codigo o un nombre de catalogo sin su llave
    foranea hace fallar la suite. Los enums (codigos de prompt) no cuentan: ya son cerrados."""
    filas = await db.execute(
        text(
            """
            SELECT c.table_name, c.column_name
            FROM information_schema.columns c
            WHERE c.table_schema = 'public' AND c.data_type IN ('character varying', 'text')
              AND NOT EXISTS (
                SELECT 1 FROM pg_constraint k
                JOIN pg_attribute a ON a.attrelid = k.conrelid AND a.attnum = ANY(k.conkey)
                WHERE k.contype = 'f' AND k.conrelid = c.table_name::regclass
                  AND a.attname = c.column_name)
            """
        )
    )
    sueltas = [
        f"{t}.{c}"
        for t, c in filas.tuples()
        if _NOMBRE_DE_REFERENCIA.match(c) and (t, c) not in _REFERENCIAS_SIN_LLAVE
    ]
    assert sueltas == [], f"Referencias a catalogos sin llave foranea: {sueltas}"


async def test_la_base_rechaza_una_ciudad_fuera_del_catalogo(db: AsyncSession):
    with pytest.raises(IntegrityError, match="fk_familias_ciudad_ciudades"):
        db.add(
            Familia(
                titular_nombre="T",
                documento="9",
                telefono="+573000000000",
                ciudad="Narnia",
                barrio="Centro",
            )
        )
        await db.flush()


async def test_corregir_el_nombre_de_una_ciudad_se_propaga(db: AsyncSession):
    familia = Familia(
        titular_nombre="T",
        documento="9",
        telefono="+573000000000",
        ciudad="Bogota",
        barrio="Centro",
    )
    db.add(familia)
    await db.flush()
    await db.execute(text("UPDATE ciudades SET nombre = 'Bogotá D.C.' WHERE nombre = 'Bogota'"))
    await db.refresh(familia)
    assert familia.ciudad == "Bogotá D.C."


# --- Invariantes de fila (CHECK) y unicidad -----------------------------------------------------


async def test_cada_check_y_cada_unico_del_modelo_estan_en_la_base(db: AsyncSession):
    """Guarda: el autogenerate de Alembic no detecta un CHECK nuevo en una tabla existente
    (ni una condicion distinta en un indice parcial), asi que un `__checks__` o `__unicos__`
    sin su migracion pasaria inadvertido. Se comparan los nombres en los dos sentidos."""
    checks_base = set(
        await db.scalars(
            text(
                "SELECT conname FROM pg_constraint"
                " WHERE contype = 'c' AND connamespace = 'public'::regnamespace"
            )
        )
    )
    checks_modelo = {
        str(c.name)
        for t in Base.metadata.tables.values()
        for c in t.constraints
        if isinstance(c, CheckConstraint)
    }
    assert checks_modelo - checks_base == set(), "CHECK del modelo sin migracion"
    assert checks_base - checks_modelo == set(), "CHECK de la base que el modelo no declara"

    parciales_base = dict(
        (
            await db.execute(
                text(
                    "SELECT c.relname, i.indpred IS NOT NULL FROM pg_index i"
                    " JOIN pg_class c ON c.oid = i.indexrelid"
                    " WHERE c.relnamespace = 'public'::regnamespace AND i.indisunique"
                    " AND c.relname LIKE 'uq\\_%'"
                    " AND NOT EXISTS"
                    " (SELECT 1 FROM pg_constraint k WHERE k.conindid = i.indexrelid)"
                )
            )
        )
        .tuples()
        .all()
    )
    parciales_modelo = {
        str(i.name): i.dialect_options["postgresql"]["where"] is not None
        for t in Base.metadata.tables.values()
        for i in t.indexes
        if str(i.name).startswith("uq_")
    }
    assert parciales_base == parciales_modelo


async def _copia(db: AsyncSession, tabla: str, fila_id: Any, cambios: dict[str, Any]) -> None:
    """Inserta por SQL una copia de una fila con algunos campos cambiados, saltandose toda
    validacion de Python: lo que la detenga es la base."""
    await db.execute(
        text(
            f"INSERT INTO {tabla} SELECT (jsonb_populate_record(NULL::{tabla},"
            f" to_jsonb(t) || CAST(:cambios AS jsonb) || jsonb_build_object('id', uuidv7()))).*"
            f" FROM {tabla} t WHERE t.id = :id"
        ),
        {"id": fila_id, "cambios": json.dumps(cambios)},
    )


async def test_la_base_no_admite_dos_contratos_vigentes(db: AsyncSession):
    """La regla que `crear_contrato` comprobaba consultando antes de insertar: con dos
    peticiones simultaneas las dos pasaban la consulta. El indice parcial no deja."""
    _, contrato = await fabricas.afiliada(db, date(2026, 1, 10))
    with pytest.raises(IntegrityError, match="uq_contratos_familia_vigente"):
        await _copia(db, "contratos", contrato.id, {"numero": "OTRO-1"})


async def test_la_base_no_admite_una_cuota_pagada_sin_cubrir(db: AsyncSession):
    _, contrato = await fabricas.afiliada(db, date(2026, 1, 10))
    cuota_id = await db.scalar(
        text("SELECT id FROM cuotas WHERE contrato_id = :c"), {"c": contrato.id}
    )
    with pytest.raises(IntegrityError, match="ck_cuotas_pagada_cubre"):
        await db.execute(
            text("UPDATE cuotas SET estado = 'pagada', valor_pagado = 0 WHERE id = :i"),
            {"i": cuota_id},
        )


@pytest.mark.parametrize(
    ("sql", "restriccion"),
    [
        (
            "INSERT INTO tareas (titulo, area, prioridad, estado)"
            " VALUES ('x', 'comercial', 'media', 'cerrada')",
            "ck_tareas_cierre_coherente",
        ),
        (
            "INSERT INTO usuarios (nombre, hashed_password, rol, activo)"
            " VALUES ('x', 'h', 'operaciones', true)",
            "ck_usuarios_con_identificador",
        ),
        (
            "INSERT INTO usuarios (nombre, email, hashed_password, rol, activo)"
            " VALUES ('x', 'x@timu.co', 'h', 'aliada', true)",
            "ck_usuarios_aliada_con_clinica",
        ),
        (
            "INSERT INTO familias (titular_nombre, tipo_documento, documento, telefono, ciudad,"
            " barrio, estado, origen)"
            " VALUES ('T', 'CC', '1', '3001234567', 'Bogota', 'Centro', 'activa', 'panel')",
            "ck_familias_telefono_formato",
        ),
        (
            "INSERT INTO plantillas_whatsapp (nombre, idioma, version, categoria, cuerpo,"
            " variables, estado_aprobacion, activa)"
            " VALUES ('p', 'es', 1, 'utility', 'Hola', '[]', 'borrador', true)",
            "ck_plantillas_whatsapp_activa_aprobada",
        ),
    ],
)
async def test_la_base_rechaza_filas_incoherentes(db: AsyncSession, sql: str, restriccion: str):
    with pytest.raises(IntegrityError, match=restriccion):
        await db.execute(text(sql))


async def test_reactivar_una_version_antigua_de_plantilla(db: AsyncSession):
    """Con el indice unico parcial, retirar la activa y activar otra en el mismo flush
    depende del orden de los UPDATE (por id): reactivar la version vieja chocaba."""
    from app.modules.comunicaciones import service as comunicaciones
    from app.modules.comunicaciones.models import PlantillaWhatsApp

    v1, v2 = (
        PlantillaWhatsApp(nombre="aviso", version=n, cuerpo="Hola", variables=[]) for n in (1, 2)
    )
    db.add_all([v1, v2])
    await db.flush()
    await db.run_sync(comunicaciones.cambiar_estado_plantilla, v1.id, "aprobada", True)
    await db.run_sync(comunicaciones.cambiar_estado_plantilla, v2.id, "aprobada", True)
    await db.run_sync(comunicaciones.cambiar_estado_plantilla, v1.id, "aprobada", True)
    assert (v1.activa, v2.activa) == (True, False)


# --- Transiciones de estado ---------------------------------------------------------------------


@pytest.mark.integration
def test_los_grafos_de_la_base_son_los_del_codigo():
    """Guarda: una arista nueva en app/core/transiciones.py sin su migracion (o al reves), o
    un grafo sin su trigger, hace fallar la suite. La tabla solo la lee el dueno del esquema."""
    from app.transiciones import TRANSICIONES, aristas

    engine = create_engine(URL_SYNC)
    with engine.connect() as conn:
        en_base = set(
            conn.execute(text("SELECT tabla, columna, desde, hacia FROM transiciones_estado"))
            .tuples()
            .all()
        )
        triggers = set(
            conn.execute(
                text(
                    "SELECT tgname FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid"
                    " WHERE c.relnamespace = 'public'::regnamespace AND NOT t.tgisinternal"
                    " AND tgname LIKE 'tr\\_%\\_transicion\\_%'"
                )
            ).scalars()
        )
    engine.dispose()
    assert en_base == aristas()
    assert triggers == {f"tr_{t}_transicion_{c}" for t, c in TRANSICIONES}


async def test_la_base_rechaza_una_transicion_fuera_del_grafo(db: AsyncSession):
    tarea_id = await db.scalar(
        text(
            "INSERT INTO tareas (titulo, area, prioridad, estado)"
            " VALUES ('x', 'comercial', 'media', 'abierta') RETURNING id"
        )
    )
    await db.execute(
        text("UPDATE tareas SET estado = 'cerrada', cerrada_en = now() WHERE id = :i"),
        {"i": tarea_id},
    )
    with pytest.raises(IntegrityError, match="Transicion no permitida en tareas.estado"):
        await db.execute(
            text("UPDATE tareas SET estado = 'abierta', cerrada_en = NULL WHERE id = :i"),
            {"i": tarea_id},
        )


async def test_una_familia_dada_de_baja_no_tiene_contrato_vigente(db: AsyncSession):
    """La baja completa la orquesta afiliaciones.ciclo: cancela el contrato y marca la ficha.
    Marcarla sin cancelarlo antes lo rechaza la base, con el servicio de familias o por SQL,
    y tampoco deja reactivar despues el contrato de una familia que ya se fue."""
    from app.modules.cartera import service as cartera
    from app.modules.familias import service as familias

    familia, contrato = await fabricas.afiliada(db, date(2026, 1, 1))
    familia_id = familia.id  # el savepoint revertido expira el objeto
    with pytest.raises(IntegrityError, match="tiene un contrato vigente"):
        async with db.begin_nested():
            await db.run_sync(familias.dar_de_baja, familia, "sin cancelar el contrato")
    with pytest.raises(IntegrityError, match="tiene un contrato vigente"):
        async with db.begin_nested():
            await db.execute(
                text("UPDATE familias SET dada_de_baja_en = now() WHERE id = :i"),
                {"i": familia_id},
            )

    await db.refresh(familia)
    contrato_id = contrato.id
    await db.run_sync(cartera.cancelar, contrato, "Baja de la familia")
    await db.run_sync(familias.dar_de_baja, familia, "con el contrato cancelado")
    assert familia.dada_de_baja_en is not None

    # Y por el otro lado: una familia dada de baja no recupera un contrato vigente.
    with pytest.raises(IntegrityError, match="esta dada de baja"):
        async with db.begin_nested():
            await db.execute(
                text("UPDATE contratos SET estado = 'activa' WHERE id = :i"), {"i": contrato_id}
            )


async def test_la_aplicacion_no_puede_ampliar_los_grafos(db: AsyncSession):
    with pytest.raises(Exception, match="permission denied|permiso denegado"):
        await db.execute(
            text(
                "INSERT INTO transiciones_estado (tabla, columna, desde, hacia)"
                " VALUES ('tareas', 'estado', 'cerrada', 'abierta')"
            )
        )


# --- Auditoria e inmutabilidad ------------------------------------------------------------------


async def test_cada_tabla_auditable_e_inmutable_tiene_su_trigger(db: AsyncSession):
    """Guarda: un modelo nuevo con Auditable, o una tabla nueva en INMUTABLES, sin el trigger
    que lo hace cumplir, hace fallar la suite."""
    from app.core.auditoria import INMUTABLES, Auditable

    triggers = set(
        await db.scalars(
            text(
                "SELECT tgname FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid"
                " WHERE c.relnamespace = 'public'::regnamespace AND NOT t.tgisinternal"
            )
        )
    )
    auditables = {
        m.class_.__tablename__ for m in Base.registry.mappers if issubclass(m.class_, Auditable)
    }
    assert {f"tr_{t}_auditoria" for t in auditables} <= triggers
    assert {t[3:-10] for t in triggers if t.endswith("_auditoria")} == auditables
    assert {f"tr_{t}_inmutable" for t in INMUTABLES} <= triggers
    assert "tr_historias_clinicas_firmada" in triggers


async def test_un_cambio_por_sql_tambien_deja_rastro(db: AsyncSession):
    """Con la auditoria en Python, un UPDATE fuera del ORM no quedaba registrado."""
    familia = await db.run_sync(fabricas.familia)
    await db.run_sync(
        fijar_contexto, ContextoDb(rol="admin", usuario_id=uuid4(), request_id="sql-directo")
    )
    await db.execute(
        text("UPDATE familias SET ciudad = 'Pasto' WHERE id = :i"),
        {"i": familia.id},
    )
    fila = (
        await db.execute(
            text(
                "SELECT accion, request_id, cambios FROM auditoria"
                " WHERE entidad = 'familias' AND entidad_id = :i ORDER BY created_at DESC LIMIT 1"
            ),
            {"i": str(familia.id)},
        )
    ).one()
    await db.run_sync(fijar_contexto, SISTEMA)
    assert fila.accion == "editar" and fila.request_id == "sql-directo"
    assert fila.cambios == {"ciudad": ["Cali", "Pasto"]}


async def test_los_importes_se_auditan_como_texto(db: AsyncSession):
    _, contrato = await fabricas.afiliada(db, date(2026, 1, 10))
    cambios = await db.scalar(
        text(
            "SELECT cambios FROM auditoria WHERE entidad = 'contratos' AND entidad_id = :i"
            " AND accion = 'crear'"
        ),
        {"i": str(contrato.id)},
    )
    assert cambios["valor_mensual"] == [None, str(contrato.valor_mensual)]


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO auditoria (entidad, entidad_id, accion) VALUES ('x', 'x', 'crear')",
        "UPDATE auditoria SET entidad = 'x'",
        "DELETE FROM auditoria",
    ],
)
async def test_la_aplicacion_no_puede_escribir_la_bitacora(db: AsyncSession, sql: str):
    with pytest.raises(Exception, match="permission denied|permiso denegado"):
        await db.execute(text(sql))


async def test_una_historia_firmada_no_se_edita_ni_por_sql(db: AsyncSession):
    historia_id = await db.scalar(text("SELECT id FROM historias_clinicas LIMIT 1"))
    if historia_id is None:
        familia = await db.run_sync(fabricas.familia)
        mascota_id = await db.scalar(
            text("SELECT id FROM mascotas WHERE familia_id = :f LIMIT 1"), {"f": familia.id}
        )
        medico = await db.scalar(
            text(
                "INSERT INTO usuarios (nombre, email, hashed_password, rol, activo)"
                " VALUES ('Vet', 'vet@timu.co', 'h', 'medico', true) RETURNING id"
            )
        )
        historia_id = await db.scalar(
            text(
                "INSERT INTO historias_clinicas (mascota_id, familia_id, profesional_id, tipo,"
                " fecha, motivo, diagnostico, estado, version, firmada_en, firmada_por_id)"
                " VALUES (:m, :f, :p, 'presencial', current_date, 'Control', 'Sano',"
                " 'firmada', 1, now(), :p) RETURNING id"
            ),
            {"m": mascota_id, "f": familia.id, "p": medico},
        )
    with pytest.raises(IntegrityError, match="historia clinica firmada no se edita"):
        await db.execute(
            text("UPDATE historias_clinicas SET diagnostico = 'Otro' WHERE id = :i"),
            {"i": historia_id},
        )


# --- Sin borrado fisico -------------------------------------------------------------------------


async def test_la_aplicacion_solo_borra_estado_tecnico(db: AsyncSession):
    """Guarda: una tabla nueva hereda los permisos por defecto, que ya no dan DELETE; si
    alguien se lo concede a mano a una tabla de negocio, la suite falla."""
    filas = await db.execute(
        text(
            "SELECT relname FROM pg_class WHERE relnamespace = 'public'::regnamespace"
            " AND relkind = 'r' AND has_table_privilege('timu_app', oid, 'DELETE')"
        )
    )
    assert set(filas.scalars()) == BORRABLES


async def test_reactivar_los_envios_cierra_la_baja_sin_borrarla(db: AsyncSession):
    from app.modules.comunicaciones import service as comunicaciones

    await db.run_sync(comunicaciones.registrar_baja, "+573001110000")
    await db.run_sync(comunicaciones.quitar_baja, "+573001110000")
    assert not await db.run_sync(comunicaciones.esta_de_baja, "+573001110000")
    # Puede volver a darse de baja: la unicidad es entre bajas activas.
    await db.run_sync(comunicaciones.registrar_baja, "+573001110000")
    assert (
        await db.scalar(
            text("SELECT count(*) FROM bajas_comunicaciones WHERE destino = '+573001110000'")
        )
        == 2
    )


async def test_reemplazar_beneficios_conserva_los_anteriores(db: AsyncSession):
    from app.modules.planes import service as planes

    plan = await db.run_sync(
        fabricas.plan,
        "conservado",
        beneficios=[{"tipo_servicio_codigo": "consulta_clinica", "cupo": 2}],
    )
    await db.run_sync(
        planes.reemplazar_beneficios,
        plan,
        [{"tipo_servicio_codigo": "consulta_clinica", "cupo": 5}],
    )
    await db.refresh(plan, ["beneficios"])
    assert [b.cupo for b in plan.beneficios] == [5]
    filas = await db.execute(
        text("SELECT cupo, activo FROM beneficios_plan WHERE plan_id = :p ORDER BY cupo"),
        {"p": plan.id},
    )
    assert filas.tuples().all() == [(2, False), (5, True)]


# --- RLS: lo que cada perfil ve y escribe -------------------------------------------------------


async def test_toda_tabla_tiene_rls_y_las_politicas_de_la_matriz(db: AsyncSession):
    """Guarda: una tabla nueva sin RLS, o un cambio en app/core/permisos_db.py sin la
    migracion que regenera sus politicas, hace fallar la suite. La expresion se compara por
    el comentario de cada politica: PostgreSQL guarda la expresion normalizada."""
    from app.core.permisos_db import descripcion, politicas

    sin_rls = set(
        await db.scalars(
            text(
                "SELECT relname FROM pg_class WHERE relnamespace = 'public'::regnamespace"
                " AND relkind = 'r' AND NOT relrowsecurity AND relname <> 'alembic_version'"
            )
        )
    )
    assert sin_rls == set(), f"Tablas sin RLS: {sin_rls}"
    en_base = dict(
        (
            await db.execute(
                text(
                    "SELECT p.policyname, obj_description(o.oid, 'pg_policy')"
                    " FROM pg_policies p JOIN pg_policy o ON o.polname = p.policyname"
                    " AND o.polrelid = (p.schemaname || '.' || p.tablename)::regclass"
                    " WHERE p.schemaname = 'public'"
                )
            )
        )
        .tuples()
        .all()
    )
    esperadas = {
        nombre: descripcion(usar, comprobar)
        for nombre, _, _, _, usar, comprobar in politicas(list(Base.metadata.tables))
    }
    assert en_base == esperadas


async def _como(db: AsyncSession, contexto: ContextoDb, sql: str, **parametros: Any) -> Any:
    await db.run_sync(fijar_contexto, contexto)
    try:
        resultado = (await db.execute(text(sql), parametros)).scalar()
    except Exception:
        # La transaccion quedo abortada: se restaura el contexto sin ejecutar nada en ella.
        db.sync_session.info[CLAVE_CONTEXTO] = SISTEMA
        raise
    await db.run_sync(fijar_contexto, SISTEMA)
    return resultado


async def test_una_familia_no_ve_las_filas_de_otra_ni_por_sql(db: AsyncSession):
    ana, _ = await fabricas.afiliada(db, date(2026, 1, 10), telefono="+573001110101")
    beto, _ = await fabricas.afiliada(db, date(2026, 1, 10), telefono="+573001110102")
    como_ana = ContextoDb(rol="familia", usuario_id=uuid4(), familia_id=ana.id)
    for tabla in ("familias", "mascotas", "contratos", "cuotas"):
        total = await _como(db, como_ana, f"SELECT count(*) FROM {tabla}")
        visibles_de_beto = await _como(
            db,
            como_ana,
            f"SELECT count(*) FROM {tabla} t WHERE to_jsonb(t)::text LIKE :b",
            b=f"%{beto.id}%",
        )
        assert total >= 1 and visibles_de_beto == 0, tabla


async def test_una_familia_no_ve_historias_en_borrador(db: AsyncSession):
    familia = await db.run_sync(fabricas.familia)
    mascota_id = await db.scalar(
        text("SELECT id FROM mascotas WHERE familia_id = :f"), {"f": familia.id}
    )
    medico = await db.scalar(
        text(
            "INSERT INTO usuarios (nombre, email, hashed_password, rol, activo)"
            " VALUES ('Vet', 'vet2@timu.co', 'h', 'medico', true) RETURNING id"
        )
    )
    await db.execute(
        text(
            "INSERT INTO historias_clinicas (mascota_id, familia_id, profesional_id, tipo, fecha,"
            " motivo, estado, version) VALUES (:m, :f, :p, 'presencial', current_date,"
            " 'Control', 'borrador', 1)"
        ),
        {"m": mascota_id, "f": familia.id, "p": medico},
    )
    contexto = ContextoDb(rol="familia", usuario_id=uuid4(), familia_id=familia.id)
    assert await _como(db, contexto, "SELECT count(*) FROM historias_clinicas") == 0


async def test_un_perfil_sin_permiso_no_escribe_la_historia_ni_por_sql(db: AsyncSession):
    """F2-CLI-05: solo el personal medico escribe la historia clinica."""
    familia = await db.run_sync(fabricas.familia)
    mascota_id = await db.scalar(
        text("SELECT id FROM mascotas WHERE familia_id = :f"), {"f": familia.id}
    )
    with pytest.raises(Exception, match="row-level security"):
        await _como(
            db,
            ContextoDb(rol="comercial", usuario_id=uuid4()),
            "INSERT INTO historias_clinicas (mascota_id, familia_id, profesional_id, tipo,"
            " fecha, motivo, estado, version) VALUES (:m, :f, :p, 'presencial', current_date,"
            " 'Control', 'borrador', 1)",
            m=mascota_id,
            f=familia.id,
            p=uuid4(),
        )


async def test_sin_contexto_la_base_no_devuelve_nada(db: AsyncSession):
    await db.run_sync(fabricas.familia)
    sin_contexto = ContextoDb(rol="")
    assert await _como(db, sin_contexto, "SELECT count(*) FROM familias") == 0
    assert await _como(db, ContextoDb(rol="publico"), "SELECT count(*) FROM pagos") == 0


async def test_quien_agenda_bloquea_la_franja_pero_no_la_edita(db: AsyncSession):
    """Permiso L: SELECT ... FOR UPDATE exige la politica de UPDATE; la familia pasa su USING
    para bloquear el cupo al agendar, pero no su WITH CHECK."""
    franja_id = await db.scalar(
        text(
            "INSERT INTO franjas_agenda (ciudad, modalidad, dia_semana, hora_inicio, hora_fin,"
            " capacidad, activa) VALUES ('Cali', 'domiciliario', 0, '08:00', '12:00', 2, true)"
            " RETURNING id"
        )
    )
    familia = ContextoDb(rol="familia", usuario_id=uuid4(), familia_id=uuid4())
    bloqueada = await _como(
        db, familia, "SELECT id FROM franjas_agenda WHERE id = :i FOR UPDATE", i=franja_id
    )
    assert bloqueada == franja_id
    with pytest.raises(Exception, match="row-level security"):
        await _como(
            db, familia, "UPDATE franjas_agenda SET capacidad = 99 WHERE id = :i", i=franja_id
        )


async def test_una_aliada_no_alcanza_familias_sin_remision_de_su_clinica(db: AsyncSession):
    familia = await db.run_sync(fabricas.familia)
    aliada = ContextoDb(rol="aliada", usuario_id=uuid4(), clinica_id=uuid4())
    assert await _como(db, aliada, "SELECT count(*) FROM familias") == 0
    with pytest.raises(Exception, match="row-level security"):
        await _como(
            db,
            aliada,
            "INSERT INTO tareas (titulo, area, prioridad, estado, familia_id)"
            " VALUES ('x', 'operaciones', 'media', 'abierta', :f)",
            f=familia.id,
        )


def _publico(**llaves: object) -> ContextoDb:
    return ContextoDb(rol="publico", llaves=tuple(sorted((k, str(v)) for k, v in llaves.items())))


async def _usuario(db: AsyncSession, email: str, rol: str = "familia") -> UUID:
    return await db.scalar(
        text(
            "INSERT INTO usuarios (nombre, email, hashed_password, rol, activo)"
            " VALUES ('Prueba', :e, 'h', CAST(:r AS rol), true) RETURNING id"
        ),
        {"e": email, "r": rol},
    )


async def test_publico_sin_llaves_no_ve_ninguna_fila(db: AsyncSession):
    """Sin declarar sobre quien actua, una peticion publica no ve nada fuera de los catalogos,
    tampoco con SQL directo."""
    await db.run_sync(fabricas.familia)
    await _usuario(db, "sin-llaves@timu.co")
    con_datos = []
    for tabla in CONDICIONES["publico"]:
        if await db.scalar(text(f"SELECT count(*) FROM {tabla}")):
            con_datos.append(tabla)
            assert await _como(db, _publico(), f"SELECT count(*) FROM {tabla}") == 0, tabla
    assert {"familias", "mascotas", "usuarios"} <= set(con_datos)


async def test_un_formulario_publico_solo_alcanza_la_familia_de_su_documento(db: AsyncSession):
    ana = await db.run_sync(fabricas.familia, telefono="+573001110201")
    beto = await db.run_sync(fabricas.familia, telefono="+573001110202")
    como_ana = _publico(tipo_documento=ana.tipo_documento, documento=ana.documento)
    assert await _como(db, como_ana, "SELECT array_agg(id) FROM familias") == [ana.id]
    ajenas = "SELECT count(*) FROM mascotas WHERE familia_id <> :a"
    assert await _como(db, como_ana, ajenas, a=ana.id) == 0
    propias = "SELECT count(*) FROM mascotas WHERE familia_id = :a"
    assert await _como(db, como_ana, propias, a=ana.id) == 1
    with pytest.raises(Exception, match="row-level security"):
        await _como(
            db,
            como_ana,
            "INSERT INTO mascotas (familia_id, nombre, especie, activa)"
            " VALUES (:b, 'Intrusa', 'canino', true)",
            b=beto.id,
        )


_NUEVA_SESION = (
    "INSERT INTO sesiones (usuario_id, refresh_hash, expira_en)"
    " VALUES (:u, :h, now() + interval '1 day') RETURNING usuario_id"
)
_CAMBIAR_CLAVE = (
    "WITH c AS (UPDATE usuarios SET hashed_password = 'otra' WHERE id = :u RETURNING 1)"
    " SELECT count(*) FROM c"
)


async def _negado(db: AsyncSession, contexto: ContextoDb, sql: str, **parametros: Any) -> None:
    """La base rechaza la sentencia; el savepoint deja la transaccion de la prueba utilizable."""
    with pytest.raises(Exception, match="row-level security"):
        async with db.begin_nested():
            await _como(db, contexto, sql, **parametros)


async def test_identificar_una_cuenta_no_basta_para_abrirle_sesion(db: AsyncSession):
    """Recuperar la contrasena o pedir un codigo identifican la cuenta (llave `usuario`);
    abrir una sesion o cambiar la contrasena exige una credencial probada (`autenticado`)."""
    cuenta = await _usuario(db, "identificada@timu.co")
    identificada = _publico(usuario=cuenta)
    assert await _como(db, identificada, "SELECT count(*) FROM usuarios") == 1
    assert await _como(db, identificada, _CAMBIAR_CLAVE, u=cuenta) == 0
    await _negado(db, identificada, _NUEVA_SESION, u=cuenta, h="h1")

    autenticada = _publico(autenticado=cuenta)
    assert await _como(db, autenticada, _CAMBIAR_CLAVE, u=cuenta) == 1
    assert await _como(db, autenticada, _NUEVA_SESION, u=cuenta, h="h2") == cuenta
    otra = await _usuario(db, "otra@timu.co")
    await _negado(db, autenticada, _NUEVA_SESION, u=otra, h="h3")


async def test_un_token_reutilizado_revoca_las_sesiones_pero_no_abre_otra(db: AsyncSession):
    cuenta = await _usuario(db, "robada@timu.co")
    await db.execute(text(_NUEVA_SESION), {"u": cuenta, "h": "vigente"})
    revocar = _publico(revocar=cuenta)
    revocadas = await _como(
        db,
        revocar,
        "WITH c AS (UPDATE sesiones SET revocada_en = now() WHERE usuario_id = :u"
        " AND revocada_en IS NULL RETURNING 1) SELECT count(*) FROM c",
        u=cuenta,
    )
    assert revocadas == 1
    with pytest.raises(Exception, match="row-level security"):
        await _como(db, revocar, _NUEVA_SESION, u=cuenta, h="nueva")


async def test_el_reparto_comercial_cuenta_todos_los_interesados_aunque_pregunte_publico(
    db: AsyncSession,
):
    """Un formulario publico solo ve sus interesados; el reparto por carga los cuenta todos
    con comercial_con_menos_carga(), sin exponerlos."""
    cargado = await _usuario(db, "cargado@timu.co", "comercial")
    await _usuario(db, "libre@timu.co", "comercial")
    for k in range(2):
        await db.execute(
            text(
                "INSERT INTO interesados (telefono, origen, etapa, responsable_id, datos)"
                " VALUES (:t, 'web', 'nuevo', :r, '{}')"
            ),
            {"t": f"+57300222000{k}", "r": cargado},
        )
    consulta = "SELECT comercial_con_menos_carga(ARRAY['nuevo', 'contactado'])"
    assert await _como(db, _publico(), "SELECT count(*) FROM interesados") == 0
    elegido = await _como(db, _publico(), consulta)
    assert elegido is not None and elegido != cargado
    assert elegido == await db.scalar(text(consulta))


def test_las_politicas_de_publico_solo_usan_llaves_conocidas():
    """Una llave mal escrita en una politica nunca casaria y negaria en silencio; una llave
    que ninguna politica usa no acota nada."""
    usadas = set(re.findall(r"app_llave\('(\w+)'\)", json.dumps(CONDICIONES["publico"])))
    assert usadas == LLAVES_PUBLICAS
    with pytest.raises(ValueError, match="desconocidas"):
        acotar_publico(None, cuenta="x")  # type: ignore[arg-type]


# --- Volumen ------------------------------------------------------------------------------------


async def test_toda_llave_foranea_tiene_indice(db: AsyncSession):
    """Guarda: cruzar por una llave foranea sin indice (y las politicas de RLS que la
    consultan) recorre la tabla entera. Una llave nueva llega con `index=True`."""
    sin_indice = (
        await db.scalars(
            text(
                "SELECT c.conrelid::regclass || '.' || a.attname FROM pg_constraint c"
                " JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = c.conkey[1]"
                " WHERE c.contype = 'f' AND c.connamespace = 'public'::regnamespace"
                " AND NOT EXISTS (SELECT 1 FROM pg_index i"
                " WHERE i.indrelid = c.conrelid AND i.indkey[0] = c.conkey[1])"
            )
        )
    ).all()
    assert sin_indice == [], f"Llaves foraneas sin indice: {sin_indice}"


async def test_la_aplicacion_tiene_limites_de_tiempo(db: AsyncSession):
    limites = {
        ajuste: await db.scalar(text(f"SHOW {ajuste}"))
        for ajuste in ("statement_timeout", "lock_timeout", "idle_in_transaction_session_timeout")
    }
    assert limites == {
        "statement_timeout": "30s",
        "lock_timeout": "10s",
        "idle_in_transaction_session_timeout": "1min",
    }


async def test_restaurar_crea_el_rol_como_las_migraciones(db: AsyncSession):
    """El rol es del cluster y pg_dump no lo lleva: restaurar.sh lo crea en un servidor nuevo.
    Sus atributos y limites tienen que ser los que dejan las migraciones en la base."""
    guion = (
        pathlib.Path(__file__).resolve().parents[2] / "infra" / "respaldos" / "restaurar.sh"
    ).read_text()
    creacion = re.search(rf"CREATE ROLE {ROL_APLICACION} ([A-Z ]+);", guion)
    assert creacion is not None, "restaurar.sh ya no crea el rol de la aplicacion"
    atributos = set(creacion.group(1).split())
    rol = (
        await db.execute(
            text(
                "SELECT rolcanlogin, rolsuper, rolbypassrls, rolcreatedb, rolcreaterole"
                " FROM pg_roles WHERE rolname = :rol"
            ),
            {"rol": ROL_APLICACION},
        )
    ).one()
    # LOGIN lo da `inicializar` con la clave del entorno; el volcado no la conoce.
    assert atributos == {"NOLOGIN"} | {
        ("" if activo else "NO") + nombre
        for activo, nombre in zip(
            rol[1:], ("SUPERUSER", "BYPASSRLS", "CREATEDB", "CREATEROLE"), strict=True
        )
    }
    ajustes = dict(re.findall(rf"ALTER ROLE {ROL_APLICACION} SET (\w+) = '([^']+)';", guion))
    en_la_base = await db.scalar(
        text(
            "SELECT setconfig FROM pg_db_role_setting s JOIN pg_roles r ON r.oid = s.setrole"
            " WHERE r.rolname = :rol AND s.setdatabase = 0"
        ),
        {"rol": ROL_APLICACION},
    )
    assert ajustes == dict(a.split("=", 1) for a in en_la_base)


# Tablas acotadas por naturaleza: configuracion y catalogos, que no crecen con el negocio.
# Recorrerlas enteras es lo correcto.
_ACOTADAS = frozenset(
    {
        "arboles_conversacion",
        "campanas",
        "casos_prueba_ia",
        "clinicas_aliadas",
        "configuraciones_encuesta",
        "consumo_mapas",
        "convenios_aliadas",
        "plantillas_consulta",
        "prompts_ia",
        "reportes_programados",
        "respuestas_virtuales",
        "segmentos",
        "transiciones_estado",
    }
)
# Recorridos completos a proposito: procesos por lotes que leen casi toda la tabla, donde
# el Seq Scan es el plan optimo. (tabla, inicio del FROM) -> motivo.
_RECORRIDOS_A_PROPOSITO = {
    (
        "contratos",
        "FROM contratos WHERE contratos.estado != ",
    ): "revision diaria de cartera: todos los contratos no cancelados",
}
# Caminos calientes: los listados del panel y las tareas periodicas del worker.
_LISTADOS = (
    "/api/v1/familias?q=Ana",
    "/api/v1/familias?orden=titular_nombre",
    "/api/v1/tareas",
    "/api/v1/tareas?mias=true",
    "/api/v1/servicios",
    "/api/v1/pendientes",
    "/api/v1/cartera/contratos?solo_mora=true",
    "/api/v1/encuestas",
    "/api/v1/comercial/interesados",
    "/api/v1/rutas?fecha=2026-11-05",
    "/api/v1/dashboard/indicadores?desde=2026-10-01&hasta=2026-10-31",
    "/api/v1/preventivos",
)


def _tablas_recorridas(plan: dict[str, Any]) -> set[str]:
    propias = {plan["Relation Name"]} if plan.get("Node Type") == "Seq Scan" else set()
    return propias.union(*(_tablas_recorridas(hijo) for hijo in plan.get("Plans", [])))


async def test_los_caminos_calientes_no_recorren_tablas_enteras(
    client: AsyncClient, db: AsyncSession, headers, en_worker
):
    """Guarda de volumen: cada sentencia de los listados y de las tareas periodicas se
    analiza con EXPLAIN (GENERIC_PLAN) y enable_seqscan = off. Si aun asi recorre entera una
    tabla que crece con el negocio, ningun indice la sirve: con volumen real seria lenta."""
    import psycopg
    from sqlalchemy import event
    from sqlalchemy.engine import Engine

    from app.workers.celery_app import celery_app

    capturadas: set[str] = set()

    def capturar(conn, cursor, statement, parameters, context, executemany) -> None:
        if re.match(r"\s*(SELECT|UPDATE|DELETE|WITH)\b", statement, re.I) and (
            "set_config" not in statement
        ):
            capturadas.add(statement)

    event.listen(Engine, "before_cursor_execute", capturar)
    try:
        for url in _LISTADOS:
            resp = await client.get(url, headers=headers)
            assert resp.status_code == 200, (url, resp.text)
        celery_app.loader.import_default_modules()
        for entrada in celery_app.conf.beat_schedule.values():
            await en_worker(celery_app.tasks[entrada["task"]])
    finally:
        event.remove(Engine, "before_cursor_execute", capturar)

    # Protocolo simple (ClientCursor): un plan generico admite $1 sin valores.
    dsn = make_url(URL_SYNC).set(drivername="postgresql").render_as_string(hide_password=False)
    recorridas: dict[str, set[str]] = {}
    with psycopg.connect(dsn, cursor_factory=psycopg.ClientCursor, autocommit=True) as conn:
        conn.execute("SET enable_seqscan = off")
        for sql in capturadas:
            fila = conn.execute("EXPLAIN (GENERIC_PLAN, FORMAT JSON) " + sql).fetchone()
            assert fila is not None
            tablas = _tablas_recorridas(fila[0][0]["Plan"]) - _ACOTADAS - set(CATALOGOS)
            plano = " ".join(sql.split())
            tablas = {
                t
                for t in tablas
                if not any(t == tp and desde in plano for tp, desde in _RECORRIDOS_A_PROPOSITO)
            }
            for tabla in tablas:
                recorridas.setdefault(tabla, set()).add(plano[plano.find(" FROM ") :][:300])
    assert recorridas == {}, "Recorren la tabla entera:\n" + "\n".join(
        f"{t}: {q}" for t, qs in sorted(recorridas.items()) for q in sorted(qs)
    )
