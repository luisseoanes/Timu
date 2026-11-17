"""F0-12 Motor de reglas configurable."""

import pytest
from httpx import AsyncClient

from app.modules.reglas import motor, service
from app.modules.reglas.models import Regla
from app.modules.reglas.motor import (
    CondicionInvalida,
    campos,
    cumple,
    describir_accion,
    describir_condicion,
    validar_accion,
    validar_condicion,
)

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


@pytest.mark.parametrize(
    ("condicion", "texto"),
    [
        ({}, "Siempre"),
        ({"campo": "dias_mora", "op": "gte", "valor": 25}, "Días de mora: 25 o más"),
        (
            {"campo": "dias_para_renovacion", "op": "lte", "valor": 30},
            "Días para la renovación: 30 o menos",
        ),
        (
            {"campo": "familia.estado", "op": "in", "valor": ["en_mora", "congelada"]},
            "Estado de la familia: en mora o congelada",
        ),
        ({"campo": "sube", "op": "eq", "valor": True}, "Sube de valor: sí"),
        ({"campo": "otro.dato_raro", "op": "existe"}, "Otro de dato raro: registrado"),
        (
            {
                "todas": [
                    {"campo": "dias_mora", "op": "gt", "valor": 5},
                    {
                        "alguna": [
                            {"campo": "ciudad", "op": "eq", "valor": "Cali"},
                            {"no": {"campo": "estado", "op": "ne", "valor": "activa"}},
                        ]
                    },
                ]
            },
            "Días de mora: más de 5 y (Ciudad: Cali o No se cumple: Estado del contrato: "
            "distinto de al día)",
        ),
    ],
)
def test_cada_condicion_se_lee_en_palabras(condicion, texto):
    assert describir_condicion(condicion) == texto


def test_los_estados_se_leen_por_su_nombre():
    condicion = {"campo": "estado_nuevo", "op": "eq", "valor": "pendiente_autorizacion"}
    assert describir_condicion(condicion) == "Nuevo estado del servicio: por autorizar"


def test_los_campos_de_una_condicion_salen_una_vez_con_su_nombre():
    condicion = {
        "todas": [
            {"campo": "dias_mora", "op": "gte", "valor": 5},
            {"no": {"campo": "familia.estado", "op": "in", "valor": ["congelada"]}},
            {"campo": "dias_mora", "op": "lt", "valor": 30},
        ]
    }
    assert campos(condicion) == [
        {"campo": "dias_mora", "nombre": "Días de mora", "numerico": True},
        {"campo": "familia.estado", "nombre": "Estado de la familia", "numerico": False},
    ]


@pytest.mark.parametrize(
    ("accion", "texto"),
    [
        ({"tipo": "estado", "estado": "en_mora"}, "Pasa el contrato a «en mora»"),
        (
            {"tipo": "notificar", "plantilla": "mora_5", "clave": "m5"},
            "Envía un aviso por WhatsApp (plantilla mora_5)",
        ),
        (
            {"tipo": "tarea", "titulo": "Renovar", "area": "servicio_cliente", "vence_en_dias": 1},
            "Crea la tarea «Renovar» para servicio al cliente, prioridad media, que vence en 1 día",
        ),
        (
            {"tipo": "tarea", "titulo": "Autorizar", "area": "medico", "prioridad": "alta"},
            "Crea la tarea «Autorizar» para médico, prioridad alta, que vence en 2 días",
        ),
        ({"tipo": "prorrateo", "modo": "sin_cargo"}, "Cambia de plan sin cobrar la diferencia"),
        ({"tipo": "rechazar", "motivo": "Tiene mora"}, "No lo permite: Tiene mora"),
        (
            {"tipo": "recomendar", "plan_codigo": "familiar", "motivo": "Tres peludos"},
            "Recomienda el plan «familiar»: Tres peludos",
        ),
    ],
)
def test_cada_accion_se_lee_en_palabras(accion, texto):
    assert describir_accion(accion) == texto


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
            "accion_texto": "Pasa el contrato a «en mora»",
        }
    ]
    [creada] = [
        r
        for r in (await client.get("/api/v1/reglas", headers=headers)).json()
        if r["codigo"] == "mora_temprana"
    ]
    # Lo que hay que contarle al motor para probar la regla, y su evento por su nombre.
    assert creada["campos_condicion"] == [
        {"campo": "dias_mora", "nombre": "Días de mora", "numerico": True}
    ]
    assert creada["evento_nombre"] == "Estado de cartera según los días de mora"
    assert creada["retirada"] is None


async def test_una_regla_de_un_evento_retirado_dice_por_que(client: AsyncClient, db, headers):
    db.add(
        Regla(
            codigo="cupo_por_mascota",
            nombre="Sin cupo adicional",
            evento="plan.mascota",
            condicion={},
            accion={"tipo": "rechazar", "motivo": "x"},
        )
    )
    await db.commit()
    [regla] = [
        r
        for r in (await client.get("/api/v1/reglas", headers=headers)).json()
        if r["codigo"] == "cupo_por_mascota"
    ]
    assert regla["evento_nombre"] == "Precio por mascota"
    assert regla["retirada"] == motor.EVENTOS_RETIRADOS["plan.mascota"]


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


async def test_la_accion_nombra_la_plantilla_como_el_equipo(client: AsyncClient, headers):
    """DEU-10: «Envía por WhatsApp «Aviso de mora»», no el codigo con que se registra en Meta."""
    await client.post(
        "/api/v1/comunicaciones/plantillas",
        json={"nombre": "aviso_mora", "titulo": "Aviso de mora", "cuerpo": "Hola", "variables": []},
        headers=headers,
    )
    resp = await client.post(
        "/api/v1/reglas",
        json={
            "codigo": "aviso_prueba",
            "nombre": "Aviso de prueba",
            "evento": "cartera.alerta",
            "condicion": {},
            "accion": {"tipo": "notificar", "plantilla": "aviso_mora", "clave": "prueba"},
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["accion_texto"] == "Envía por WhatsApp «Aviso de mora»"
    sin_titulo = motor.describir_accion({"tipo": "notificar", "plantilla": "otra"})
    assert sin_titulo == "Envía un aviso por WhatsApp (plantilla otra)"
