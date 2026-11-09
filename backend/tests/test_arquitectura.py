"""Guarda de la arquitectura modular (Secciones 3 y 4 del documento de requerimientos).

Un modulo nuevo se incorpora sin reemplazar la base solo si la base no depende de ningun
dominio y los dominios no se enredan entre si. Esto se comprueba leyendo los imports de
`app/` con `ast`, incluidos los que van dentro de una funcion: un import diferido esquiva
el error de import circular, pero la dependencia sigue ahi.

Capas, de abajo arriba; cada una solo importa de las anteriores:

- `core`, `schemas`: la base. No conocen ningun dominio.
- `integrations`: clientes de terceros. Solo usan la base.
- `modules.<dominio>`: la logica. Usan la base, las integraciones y otros dominios, nunca
  las capas de entrada ni el router de otro dominio. Su `router.py` es el adaptador HTTP
  y es lo unico del modulo que usa `app.api.deps` (sesion, perfiles, alcance).
- `api`, `workers`, `main`, `models`, `transiciones`: entrada y registros. Lo componen todo.
"""

import ast
from collections import defaultdict
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

APP = Path(__file__).resolve().parents[1] / "app"

BASE = {"core", "schemas"}
PERMITIDAS: dict[str, set[str]] = {
    "core": BASE,
    "schemas": BASE,
    "integrations": BASE | {"integrations"},
    "modules": BASE | {"integrations", "modules"},
}
# El adaptador HTTP de cada dominio necesita la sesion y los guards de la capa de entrada.
DEPS_HTTP = ("app", "api", "deps")

# Dependencias entre dominios que forman ciclos y se aceptan como deuda. Vacia desde el
# 2026-11-10 (docs/deuda-ciclos-dominios.md): ninguna arista nueva puede cerrar un ciclo. Si
# alguna vez hiciera falta congelar una, va aqui con su motivo, y la prueba de abajo obliga a
# borrarla cuando deje de existir. Para romper un ciclo: un efecto sobre otro dominio va por
# evento del outbox; lo que un dominio de abajo necesita del de arriba se le inyecta (como
# los respondedores de `comunicaciones`), y un caso de uso que cruza dominios lo orquesta el
# de arriba (como `afiliaciones.ciclo`).
CICLOS_CONOCIDOS: dict[tuple[str, str], str] = {}


def _capa(partes: tuple[str, ...]) -> tuple[str, str | None]:
    """('app', 'modules', 'cartera', 'service') -> ('modules', 'cartera')."""
    if len(partes) > 2 and partes[1] == "modules":
        return "modules", partes[2]
    return partes[1], None


def _imports() -> list[tuple[tuple[str, ...], Path, int, tuple[str, ...]]]:
    """(modulo de origen, fichero, linea, ruta importada) de cada import de `app`."""
    encontrados = []
    for fichero in APP.rglob("*.py"):
        partes = ("app", *fichero.relative_to(APP).with_suffix("").parts)
        if len(partes) < 2 or partes[1] == "__init__":
            continue
        for nodo in ast.walk(ast.parse(fichero.read_text(encoding="utf-8"))):
            if isinstance(nodo, ast.ImportFrom) and nodo.module:
                rutas = [nodo.module, *(f"{nodo.module}.{a.name}" for a in nodo.names)]
            elif isinstance(nodo, ast.Import):
                rutas = [a.name for a in nodo.names]
            else:
                continue
            for ruta in rutas:
                destino = tuple(ruta.split("."))
                if destino[0] == "app" and len(destino) > 1:
                    encontrados.append((partes, fichero, nodo.lineno, destino))
    return encontrados


def _grafo_de_dominios() -> dict[str, set[str]]:
    grafo: dict[str, set[str]] = defaultdict(set)
    for origen, _, _, destino in _imports():
        (capa_o, dominio_o), (capa_d, dominio_d) = _capa(origen), _capa(destino)
        if capa_o == capa_d == "modules" and dominio_o != dominio_d:
            grafo[dominio_o].add(dominio_d)  # type: ignore[index]
    return grafo


def _componentes(grafo: dict[str, set[str]]) -> list[set[str]]:
    """Componentes fuertemente conexas (Tarjan): cada una con mas de un nodo es un ciclo."""
    indice: dict[str, int] = {}
    bajo: dict[str, int] = {}
    pila: list[str] = []
    componentes: list[set[str]] = []

    def visitar(nodo: str) -> None:
        indice[nodo] = bajo[nodo] = len(indice)
        pila.append(nodo)
        for vecino in grafo.get(nodo, ()):
            if vecino not in indice:
                visitar(vecino)
                bajo[nodo] = min(bajo[nodo], bajo[vecino])
            elif vecino in pila:
                bajo[nodo] = min(bajo[nodo], indice[vecino])
        if bajo[nodo] == indice[nodo]:
            componente = set()
            while (miembro := pila.pop()) != nodo:
                componente.add(miembro)
            componente.add(nodo)
            componentes.append(componente)

    for nodo in list(grafo):
        if nodo not in indice:
            visitar(nodo)
    return componentes


def _aristas_en_ciclo() -> set[tuple[str, str]]:
    grafo = _grafo_de_dominios()
    aristas = set()
    for componente in _componentes(grafo):
        for origen in componente:
            aristas |= {(origen, d) for d in grafo[origen] if d in componente}
    return aristas


def test_cada_capa_solo_importa_de_las_de_abajo():
    violaciones = []
    for origen, fichero, linea, destino in _imports():
        capa_o, _ = _capa(origen)
        capa_d, _ = _capa(destino)
        if capa_o not in PERMITIDAS or capa_d in PERMITIDAS[capa_o]:
            continue
        if capa_o == "modules" and fichero.name == "router.py" and destino[:3] == DEPS_HTTP:
            continue
        violaciones.append(f"{fichero.relative_to(APP.parent)}:{linea} -> {'.'.join(destino)}")
    assert violaciones == [], "una capa importa de otra superior (ver el docstring de este fichero)"


def test_un_dominio_no_usa_el_router_de_otro():
    violaciones = [
        f"{fichero.relative_to(APP.parent)}:{linea} -> {'.'.join(destino)}"
        for origen, fichero, linea, destino in _imports()
        if _capa(origen)[0] == "modules"
        and _capa(destino)[0] == "modules"
        and _capa(origen)[1] != _capa(destino)[1]
        and len(destino) > 3
        and destino[3] == "router"
    ]
    assert violaciones == [], "lo que comparte un dominio va en su service, no en su router"


def test_ninguna_dependencia_nueva_entre_dominios_cierra_un_ciclo():
    nuevas = sorted(_aristas_en_ciclo() - CICLOS_CONOCIDOS.keys())
    assert nuevas == [], (
        "estas dependencias cierran un ciclo entre dominios: invierte la dependencia "
        "(evento del outbox o funcion inyectada) en lugar de anadirlas a CICLOS_CONOCIDOS"
    )


def test_los_ciclos_conocidos_que_ya_no_existen_salen_de_la_lista():
    resueltas = sorted(CICLOS_CONOCIDOS.keys() - _aristas_en_ciclo())
    assert resueltas == [], "ya no forman ciclo: borralas de CICLOS_CONOCIDOS"


def test_los_imports_de_la_aplicacion_van_en_la_cabecera():
    """Un import de `app` dentro de una funcion solo servia para esquivar un ciclo, y ya no
    queda ninguno: diferido, un nombre mal escrito no falla hasta que se ejecuta esa rama, a
    veces en produccion. Arriba falla al arrancar o al recoger las pruebas. Los de terceros
    pueden ir dentro de la funcion cuando no siempre estan instalados o pesan (`ortools` solo
    existe en la imagen del worker, `openpyxl` solo hace falta al exportar)."""
    diferidos = []
    for fichero in APP.rglob("*.py"):
        for funcion in ast.walk(ast.parse(fichero.read_text(encoding="utf-8"))):
            if not isinstance(funcion, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            for nodo in ast.walk(funcion):
                if isinstance(nodo, ast.ImportFrom):
                    modulos = [nodo.module or ""]
                elif isinstance(nodo, ast.Import):
                    modulos = [a.name for a in nodo.names]
                else:
                    continue
                diferidos += [
                    f"{fichero.relative_to(APP.parent)}:{nodo.lineno} {m}"
                    for m in modulos
                    if m == "app" or m.startswith("app.")
                ]
    assert diferidos == [], "sube estos imports al principio del fichero"
