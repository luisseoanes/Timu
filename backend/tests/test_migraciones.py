"""Las migraciones tienen que describir exactamente los modelos.

Sin esta prueba, la deriva aparece en el despliegue: alguien anade una columna,
las pruebas pasan porque el esquema se construye desde las migraciones... pero la
migracion que falta no existe y produccion se queda sin esa columna.
"""

import pytest
from sqlalchemy import create_engine

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from app.core.database import Base
from tests.conftest import URL_SYNC

pytestmark = pytest.mark.integration


def test_no_hay_deriva_entre_modelos_y_migraciones():
    """Compara el esquema real —levantado por las migraciones en la fixture de
    sesion— contra los metadatos de SQLAlchemy. Cualquier diferencia es un modelo
    sin migracion, o una migracion que no corresponde a ningun modelo."""
    engine = create_engine(URL_SYNC)
    try:
        with engine.connect() as conn:
            contexto = MigrationContext.configure(conn)
            diferencias = compare_metadata(contexto, Base.metadata)
    finally:
        engine.dispose()

    assert diferencias == [], (
        "El esquema y los modelos no coinciden. Genera la migracion que falta:\n"
        "  alembic revision --autogenerate -m 'descripcion'\n"
        f"Diferencias: {diferencias}"
    )
