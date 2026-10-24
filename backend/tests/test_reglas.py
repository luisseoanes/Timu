"""F0-12 Motor de reglas configurable."""

import pytest
from httpx import AsyncClient

from app.modules.reglas import service
from app.modules.reglas.motor import CondicionInvalida, cumple, validar_accion, validar_condicion

CTX = {"familia": {"ciudad": "Cali", "estado": "activa"}, "dias_mora": 12, "mascotas": 2}


@pytest.mark.parametrize(
    ("condicion", "esperado"),
    [
        ({}, True),
        ({"campo": "dias_mora", "op": "gte", "valor": 5}, True),
        ({"campo": "dias_mora", "op": "lt", "valor": 5}, False),
        ({"campo": "familia.ciudad", "op": "in", "valor": ["Cali", "Pasto"]}, True),
        ({"campo": "familia.ciudad", "op": "nin", "valor": ["Cali"]}, False),
        ({"campo": "familia.ciudad", "op": "contiene", "valor": "al"}, True),
        ({"campo": "familia.barrio", "op": "eq", "valor": "x"}, False),
        ({"campo": "familia.barrio", "op": "existe", "valor": False}, True),
        ({"campo": "familia.ciudad", "op": "gt", "valor": 3}, False),  # tipos incomparables
        (
            {
                "todas": [
                    {"campo": "mascotas", "op": "gte", "valor": 2},
                    {"no": {"campo": "familia.estado", "op": "eq", "valor": "congelada"}},
                ]
            },
            True,
        ),
        (
            {
                "alguna": [
                    {"campo": "mascotas", "op": "gt", "valor": 5},
                    {"campo": "dias_mora", "op": "eq", "valor": 12},
                ]
            },
            True,
        ),
    ],
)
def test_condiciones(condicion, esperado):
    validar_condicion(condicion)
    assert cumple(condicion, CTX) is esperado


@pytest.mark.parametrize(
    "condicion",
    [
        {"campo": "x", "op": "regex", "valor": ".*"},
        {"campo": "x", "op": "eq"},
        {"campo": "x", "op": "in", "valor": "no-lista"},
        {"todas": []},
        {"op": "eq", "valor": 1},
    ],
)
def test_condiciones_invalidas(condicion):
    with pytest.raises(CondicionInvalida):
        validar_condicion(condicion)


def test_accion_debe_corresponder_al_evento():
    with pytest.raises(CondicionInvalida):
        validar_accion("cartera.estado", {"tipo": "estado", "estado": "feliz"})
    with pytest.raises(CondicionInvalida):
        validar_accion("cartera.estado", {"tipo": "rechazar", "motivo": "x"})
    assert validar_accion("plan.cambio", {"tipo": "rechazar", "motivo": "x"})["tipo"] == "rechazar"


async def test_regla_nueva_opera_sin_desplegar(client: AsyncClient, db, headers):
    """El criterio de F0-12: una regla creada por API cambia el resultado de inmediato."""
    antes = await db.run_sync(service.primera, "cartera.estado", {"dias_mora": 3})
    assert antes.accion["estado"] == "activa"

    resp = await client.post(
        "/api/v1/reglas",
        json={
            "codigo": "mora_temprana",
            "nombre": "Mora desde el dia 2",
            "evento": "cartera.estado",
            "condicion": {"campo": "dias_mora", "op": "gte", "valor": 2},
            "accion": {"tipo": "estado", "estado": "en_mora"},
            "prioridad": 15,
            "detener": True,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text

    prueba = await client.post(
        "/api/v1/reglas/probar",
        json={"evento": "cartera.estado", "contexto": {"dias_mora": 3}},
        headers=headers,
    )
    assert prueba.json() == [
        {
            "regla": "mora_temprana",
            "nombre": "Mora desde el dia 2",
            "accion": {"tipo": "estado", "estado": "en_mora"},
        }
    ]


async def test_regla_invalida_se_rechaza_al_guardar(client: AsyncClient, headers):
    resp = await client.post(
        "/api/v1/reglas",
        json={
            "codigo": "rota",
            "nombre": "Rota",
            "evento": "cartera.estado",
            "condicion": {"campo": "dias_mora", "op": "gte"},
            "accion": {"tipo": "estado", "estado": "en_mora"},
        },
        headers=headers,
    )
    assert resp.status_code == 422


async def test_desactivar_y_vigencia(client: AsyncClient, db, headers):
    reglas = (
        await client.get("/api/v1/reglas", params={"evento": "cartera.estado"}, headers=headers)
    ).json()
    congelar = next(r for r in reglas if r["codigo"] == "cartera_congelada")
    await client.patch(f"/api/v1/reglas/{congelar['id']}", json={"activa": False}, headers=headers)
    resultado = await db.run_sync(service.primera, "cartera.estado", {"dias_mora": 40})
    assert resultado.accion["estado"] == "en_mora"

    await client.patch(
        f"/api/v1/reglas/{congelar['id']}",
        json={"activa": True, "vigente_desde": "2999-01-01"},
        headers=headers,
    )
    resultado = await db.run_sync(service.primera, "cartera.estado", {"dias_mora": 40})
    assert resultado.accion["estado"] == "en_mora"


async def test_solo_admin_crea_reglas(client: AsyncClient, db):
    from app.core.enums import Rol
    from tests.conftest import crear_usuario, login

    await crear_usuario(db, "com@timu.co", Rol.COMERCIAL)
    h = await login(client, "com@timu.co")
    resp = await client.post("/api/v1/reglas", json={}, headers=h)
    assert resp.status_code == 403
