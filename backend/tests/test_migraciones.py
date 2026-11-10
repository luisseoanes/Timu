"""Las migraciones tienen que describir exactamente los modelos.

Sin esta prueba, la deriva aparece en el despliegue: alguien anade una columna,
las pruebas pasan porque el esquema se construye desde las migraciones... pero la
migracion que falta no existe y produccion se queda sin esa columna.
"""

from uuid import uuid4

import pytest
from sqlalchemy import create_engine, make_url, text
from sqlalchemy.exc import IntegrityError

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from app.core.database import Base
from tests.conftest import URL_ASYNC, URL_SYNC, config_alembic

pytestmark = pytest.mark.integration


def test_no_hay_deriva_entre_modelos_y_migraciones():
    """Compara el esquema real —levantado por las migraciones en la fixture de
    sesion— contra los metadatos de SQLAlchemy. Cualquier diferencia es un modelo
    sin migracion, o una migracion que no corresponde a ningun modelo."""
    engine = create_engine(URL_SYNC)
    try:
        with engine.connect() as conn:
            # compare_server_default: un DEFAULT de servidor que el modelo no declara es deriva
            # (la 0015 y la 0019 quitaron 26 que habian quedado del relleno de columnas).
            contexto = MigrationContext.configure(
                conn, opts={"compare_server_default": True, "compare_type": True}
            )
            diferencias = compare_metadata(contexto, Base.metadata)
    finally:
        engine.dispose()

    assert diferencias == [], (
        "El esquema y los modelos no coinciden. Genera la migracion que falta:\n"
        "  alembic revision --autogenerate -m 'descripcion'\n"
        f"Diferencias: {diferencias}"
    )


# --- 0014: UUIDv7 sobre datos existentes ------------------------------------------------------
# Una migracion que reescribe datos no se prueba sobre la base vacia de la suite: se levanta
# una base aparte hasta la revision anterior, se llena con IDs v4 enlazados como los deja la
# aplicacion (llaves foraneas, IDs en texto y en JSON) y se migra.

_BASE_MIGRACION = "timu_migracion_uuidv7"


@pytest.fixture
def base_en_0013():
    yield from _base_en("0013")


def _base_en(revision: str):
    """Base aparte llevada hasta `revision`, para llenarla y migrar sobre datos."""
    url_async = make_url(URL_ASYNC).set(database=_BASE_MIGRACION)
    servidor = create_engine(URL_SYNC, isolation_level="AUTOCOMMIT")
    with servidor.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {_BASE_MIGRACION}"))
        conn.execute(text(f"CREATE DATABASE {_BASE_MIGRACION}"))
    cfg = config_alembic()
    cfg.set_main_option("sqlalchemy.url", url_async.render_as_string(hide_password=False))
    command.upgrade(cfg, revision)
    engine = create_engine(
        url_async.set(drivername="postgresql+psycopg").render_as_string(hide_password=False)
    )
    try:
        yield cfg, engine
    finally:
        engine.dispose()
        with servidor.connect() as conn:
            conn.execute(text(f"DROP DATABASE IF EXISTS {_BASE_MIGRACION} WITH (FORCE)"))
        servidor.dispose()


def _fks(conn) -> dict[str, str]:
    filas = conn.execute(
        text(
            "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint"
            " WHERE contype = 'f' AND connamespace = 'public'::regnamespace"
        )
    )
    return dict(filas.tuples().all())


def test_0014_reescribe_los_ids_existentes_sin_romper_referencias(base_en_0013):
    cfg, engine = base_en_0013
    usuario, token = uuid4(), uuid4()
    familias = [uuid4() for _ in range(3)]
    mascota = uuid4()
    ajeno = uuid4()  # un UUID que no es id de nada: no se toca
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO usuarios (id, nombre, hashed_password, rol, activo)"
                " VALUES (:u, 'Ana', 'x', 'familia', true)"
            ),
            {"u": usuario},
        )
        for i, f in enumerate(familias):
            conn.execute(
                text(
                    "INSERT INTO familias (id, titular_nombre, documento, telefono, ciudad,"
                    " estado, usuario_portal_id, created_at)"
                    " VALUES (:f, 'T', :doc, '573000000000', 'Bogota', 'activa', :u,"
                    " now() - make_interval(days => :dias))"
                ),
                {"f": f, "doc": str(i), "u": usuario if i == 0 else None, "dias": 30 - i},
            )
        conn.execute(
            text(
                "INSERT INTO mascotas (id, familia_id, nombre, especie)"
                " VALUES (:m, :f, 'Luna', 'canino')"
            ),
            {"m": mascota, "f": familias[0]},
        )
        conn.execute(
            text(
                "INSERT INTO auditoria (id, entidad, entidad_id, accion, cambios)"
                " VALUES (:a, 'mascotas', :texto, 'crear', CAST(:cambios AS jsonb))"
            ),
            {
                "a": uuid4(),
                "texto": str(mascota),
                "cambios": f'{{"familia_id": [null, "{familias[0]}"]}}',
            },
        )
        conn.execute(
            text(
                "INSERT INTO eventos_salientes (id, nombre, datos, intentos)"
                " VALUES (:e, 'familia.ubicacion', CAST(:datos AS jsonb), 0)"
            ),
            {"e": uuid4(), "datos": f'{{"familia_id": "{familias[1]}", "externo": "{ajeno}"}}'},
        )
        conn.execute(
            text(
                "INSERT INTO tareas (id, titulo, area, prioridad, estado, clave)"
                " VALUES (:t, 'Renovar', 'comercial', 'media', 'abierta', :clave)"
            ),
            {"t": uuid4(), "clave": f"renovacion:{familias[2]}:2026-12-01"},
        )
        conn.execute(
            text(
                "INSERT INTO tokens_uso_unico (id, usuario_id, proposito, token_hash, expira_en)"
                " VALUES (:t, :u, 'codigo', 'h', now() + interval '10 minutes')"
            ),
            {"t": token, "u": usuario},
        )
        fks_antes = _fks(conn)

    command.upgrade(cfg, "0014")

    with engine.connect() as conn:

        def uno(sql: str, **p):
            return conn.execute(text(sql), p).scalar_one()

        # Ningun id queda en v4, en ninguna de las 64 tablas.
        tablas = conn.execute(
            text(
                "SELECT relname FROM pg_class WHERE relnamespace = 'public'::regnamespace"
                " AND relkind = 'r' AND relname <> 'alembic_version'"
            )
        ).scalars()
        for t in tablas:
            assert uno(f"SELECT count(*) FROM {t} WHERE uuid_extract_version(id) <> 7") == 0, t
        assert uno("SELECT count(*) FROM familias WHERE id = ANY(:v)", v=familias) == 0

        # Las llaves foraneas siguieron al padre y volvieron a su definicion original.
        nueva_familia = uno("SELECT familia_id FROM mascotas")
        nueva_mascota = uno("SELECT id FROM mascotas")
        nuevo_usuario = uno("SELECT id FROM usuarios")
        assert uno("SELECT usuario_portal_id FROM familias WHERE id = :f", f=nueva_familia) == (
            nuevo_usuario
        )
        assert _fks(conn) == fks_antes

        # El orden cronologico se conserva: los v7 nuevos salen de created_at.
        por_id = conn.execute(text("SELECT created_at FROM familias ORDER BY id")).scalars()
        assert list(por_id) == sorted(
            conn.execute(text("SELECT created_at FROM familias")).scalars()
        )

        # IDs en texto y en JSON, reemplazados; el UUID ajeno, intacto.
        auditoria = conn.execute(text("SELECT entidad_id, cambios FROM auditoria")).one()
        assert auditoria.entidad_id == str(nueva_mascota)
        assert auditoria.cambios == {"familia_id": [None, str(nueva_familia)]}
        datos = uno("SELECT datos FROM eventos_salientes")
        assert datos["externo"] == str(ajeno)
        assert datos["familia_id"] != str(familias[1])
        assert (
            uno("SELECT count(*) FROM familias WHERE id = CAST(:f AS uuid)", f=datos["familia_id"])
            == 1
        )
        clave = uno("SELECT clave FROM tareas")
        assert str(familias[2]) not in clave
        assert (
            uno(
                "SELECT count(*) FROM familias WHERE :clave LIKE 'renovacion:' || id || ':%'",
                clave=clave,
            )
            == 1
        )

        # El codigo pendiente caduca: su hash dependia del id viejo.
        assert uno("SELECT expira_en <= now() FROM tokens_uso_unico")

    # A partir de aqui la base genera v7 y rechaza cualquier otra version.
    with engine.begin() as conn:
        generado = conn.execute(
            text(
                "INSERT INTO especies (codigo, nombre, activa) VALUES ('ave', 'Ave', true)"
                " RETURNING id"
            )
        ).scalar_one()
        assert generado.version == 7
    with pytest.raises(IntegrityError, match="ck_especies_id_uuidv7"), engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO especies (id, codigo, nombre, activa) VALUES (:i, 'pez', 'Pez', true)"
            ),
            {"i": uuid4()},
        )

    command.downgrade(cfg, "0013")
    with engine.connect() as conn:
        assert (
            conn.execute(
                text("SELECT count(*) FROM pg_constraint WHERE conname LIKE '%\\_id\\_uuidv7'")
            ).scalar_one()
            == 0
        )


def test_las_migraciones_de_persistencia_se_revierten_y_se_vuelven_a_aplicar(base_en_0013):
    """Ida y vuelta desde antes del plan de persistencia (0012) hasta head: cada migracion
    nueva tiene un downgrade que funciona y deja la base lista para volver a subir."""
    cfg, engine = base_en_0013
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "0012")
    with engine.connect() as conn:
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "0012"
        tipos = conn.execute(
            text(
                "SELECT count(*) FROM pg_type"
                " WHERE typtype = 'e' AND typnamespace = 'public'::regnamespace"
            )
        ).scalar_one()
        assert tipos == 0
    command.upgrade(cfg, "head")


# --- 0032: tarifas y ciudades de los planes existentes ----------------------------------------


@pytest.fixture
def base_en_0031():
    yield from _base_en("0031")


def test_0032_da_tarifas_y_ciudades_a_los_planes_existentes(base_en_0031):
    """Cada plan recibe cuatro tarifas con su valor mensual y sus ciudades: la suya o, si no
    tenia, todas las activas. Un plan de valor 0 no tiene tarifa que dar (el CHECK la exige
    positiva): queda sin tarifas y no se puede cotizar hasta que se le pongan."""
    cfg, engine = base_en_0031
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO ciudades (codigo, nombre, departamento, activa) VALUES"
                " ('11001', 'Bogota', 'Bogota', true), ('05001', 'Medellin', 'Antioquia', true),"
                " ('76001', 'Cali', 'Valle', false)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO planes (codigo, nombre, ciudad, valor_mensual, cupos_mascotas,"
                " especies, activo) VALUES"
                " ('todas', 'Todas', NULL, 45000, 1, '[]', true),"
                " ('paisa', 'Paisa', 'Medellin', 69000, 2, '[]', true),"
                " ('gratis', 'Gratis', 'Bogota', 0, 1, '[]', true)"
            )
        )
    command.upgrade(cfg, "0032")
    with engine.connect() as conn:
        tarifas = conn.execute(
            text(
                "SELECT p.codigo, array_agg(t.peludos ORDER BY t.peludos),"
                " min(t.valor), max(t.valor)"
                " FROM tarifas_plan t JOIN planes p ON p.id = t.plan_id GROUP BY p.codigo"
            )
        ).all()
        assert {c: (n, int(a), int(b)) for c, n, a, b in tarifas} == {
            "todas": ([1, 2, 3, 4], 45000, 45000),
            "paisa": ([1, 2, 3, 4], 69000, 69000),
        }
        ciudades = conn.execute(
            text(
                "SELECT p.codigo, array_agg(c.ciudad ORDER BY c.ciudad) FROM ciudades_plan c"
                " JOIN planes p ON p.id = c.plan_id WHERE c.activa GROUP BY p.codigo"
            )
        ).all()
        assert dict(ciudades) == {
            "todas": ["Bogota", "Medellin"],
            "paisa": ["Medellin"],
            "gratis": ["Bogota"],
        }
