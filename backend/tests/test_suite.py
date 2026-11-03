"""Guarda de la suite: que el CI ejecute todas las pruebas que existen.

pytest solo recoge `tests/test_*.py` (pytest.ini). Una prueba escrita en otro fichero no
la corre nadie y no hace fallar nada. Las saltadas y los marcadores los vigila conftest.
"""

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

RAIZ = Path(__file__).resolve().parents[1]


def _define_pruebas(fichero: Path) -> bool:
    arbol = ast.parse(fichero.read_text(encoding="utf-8"))
    funciones = (ast.FunctionDef, ast.AsyncFunctionDef)
    for nodo in arbol.body:
        if isinstance(nodo, funciones) and nodo.name.startswith("test_"):
            return True
        if isinstance(nodo, ast.ClassDef) and nodo.name.startswith("Test"):
            return True
    return False


def test_toda_prueba_vive_donde_pytest_la_recoge():
    huerfanas = [
        str(f.relative_to(RAIZ))
        for carpeta in ("tests", "app", "scripts")
        for f in (RAIZ / carpeta).rglob("*.py")
        if not (carpeta == "tests" and f.name.startswith("test_")) and _define_pruebas(f)
    ]
    assert huerfanas == [], "pruebas que pytest no ejecuta: renombralas a tests/test_*.py"
