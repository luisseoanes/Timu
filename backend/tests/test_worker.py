"""El worker arranca sin app.main: lo que cargue debe bastar para escribir en la base."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

RAIZ = Path(__file__).resolve().parents[1]

# Proceso aparte: en la suite app.main ya cargo todos los modelos y ocultaria el fallo.
GUION = """
from app.workers.celery_app import celery_app
celery_app.loader.import_default_modules()
from app.core.database import Base
for tabla in Base.metadata.tables.values():
    for fk in tabla.foreign_keys:
        fk.column  # NoReferencedTableError si la tabla destino no esta registrada
print("ok")
"""


def test_el_worker_resuelve_todas_las_llaves_foraneas():
    resultado = subprocess.run(
        [sys.executable, "-c", GUION],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        timeout=120,
        env={**os.environ, "ENVIRONMENT": "test"},
    )
    assert resultado.returncode == 0, resultado.stderr[-2000:]
    assert resultado.stdout.strip().endswith("ok")
