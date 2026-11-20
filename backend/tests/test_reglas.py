"""Seccion 7 Motor de reglas configurable."""

import pytest
from httpx import AsyncClient

from app.core.enums import Rol
from app.modules.comunicaciones.models import PlantillaWhatsApp
from app.modules.reglas import acciones, motor, service
from app.modules.reglas.contextos import CONTEXTOS, CarteraEstado, campos_del_evento
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
from tests import fabricas


def _mora(dias: int) -> CarteraEstado:
    return CarteraEstado(
        dias_mora=dias, cuotas_vencidas=1, saldo_pendiente=50_000.0, estado_actual="activa"
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
        ({"campo": "dias_mora", "op": "gte", "valor": 25}, "Días de mora: al menos 25"),
        (
            {"campo": "dias_para_renovacion", "op": "lte", "valor": 30},
            "Días para la renovación: como mucho 30",
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
    """El criterio de Seccion 7: una regla creada por API cambia el resultado de inmediato."""
    antes = await db.run_sync(service.primera, _mora(3))
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
    resultado = await db.run_sync(service.primera, _mora(40))
    assert resultado.accion["estado"] == "en_mora"

    await client.patch(
        f"/api/v1/reglas/{congelar['id']}",
        json={"activa": True, "vigente_desde": "2999-01-01"},
        headers=headers,
    )
    resultado = await db.run_sync(service.primera, _mora(40))
    assert resultado.accion["estado"] == "en_mora"


async def test_solo_admin_crea_reglas(client: AsyncClient, db):
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


# --- DEU-8 Lo que da cada evento y el editor por campos ---------------------------------------


@pytest.fixture
async def planes(db):
    plan = await db.run_sync(fabricas.plan, "mi_amigo_fiel", 75_000, 3)
    plan.nombre = "Mi Amigo Fiel"  # la fabrica lo llama por su codigo
    await db.flush()


def test_cada_evento_declara_su_contexto_y_cada_campo_tiene_nombre():
    """El editor ofrece cada campo por su nombre: uno sin nombre saldria como su ruta."""
    assert CONTEXTOS.keys() == motor.EVENTOS.keys()
    for evento in CONTEXTOS:
        for campo in campos_del_evento(evento):
            assert campo in motor._CAMPOS, f"{evento}: {campo} sin nombre en _CAMPOS"


def test_los_campos_salen_con_su_tipo_y_su_catalogo():
    campos = campos_del_evento("servicio.elegibilidad")
    assert list(campos) == [
        "familia.ciudad",
        "familia.estado",
        "plan.codigo",
        "servicio.tipo",
        "servicio.modalidad",
        "mascota.especie",
    ]
    assert campos["familia.ciudad"].opciones.fuente == "ciudades"
    assert campos["mascota.especie"].tipo == "opcion"
    recomendacion = campos_del_evento("plan.recomendacion")
    assert recomendacion["mascotas.total"].tipo == "numero"
    assert recomendacion["mascotas.especies"].tipo == "lista"
    assert campos_del_evento("plan.cambio")["sube"].tipo == "si_no"


@pytest.mark.parametrize(
    ("condicion", "error"),
    [
        # Un dato que el evento no da: antes se guardaba y la regla no aplicaba nunca.
        ({"campo": "familia.ciudad", "op": "eq", "valor": "Cali"}, "no da el dato"),
        ({"campo": "dias_mora", "op": "in", "valor": [1]}, "no se compara"),
        ({"campo": "dias_mora", "op": "gte", "valor": "5"}, "Valor no valido"),
        ({"campo": "dias_mora", "op": "gte", "valor": True}, "Valor no valido"),
        ({"todas": [{"campo": "saldo", "op": "gt", "valor": 1}]}, "no da el dato"),
    ],
)
def test_una_condicion_solo_usa_lo_que_da_su_evento(condicion, error):
    with pytest.raises(CondicionInvalida, match=error):
        validar_condicion(condicion, "cartera.alerta")


def test_una_condicion_valida_para_su_evento():
    validar_condicion(
        {
            "alguna": [
                {"campo": "familia.estado", "op": "in", "valor": ["en_mora", "congelada"]},
                {"campo": "sube", "op": "eq", "valor": True},
                {"campo": "plan_nuevo.valor", "op": "gt", "valor": 50_000.5},
            ]
        },
        "plan.cambio",
    )


def test_las_acciones_dicen_sus_parametros():
    [tarea] = acciones.ACCIONES_POR_EVENTO["cartera.renovacion"][1]
    parametros = {p.nombre: p for p in acciones.parametros_de_accion(tarea)}
    assert list(parametros) == ["titulo", "area", "prioridad", "vence_en_dias"]
    assert parametros["area"].valores["medico"] == "Médico"
    assert parametros["prioridad"].por_defecto == "media" and not parametros["prioridad"].requerido
    assert parametros["vence_en_dias"].tipo == "numero"
    [notificar] = acciones.ACCIONES_POR_EVENTO["cartera.alerta"][1]
    # La clave del aviso no la escribe el equipo.
    assert [p.nombre for p in acciones.parametros_de_accion(notificar)] == ["plantilla"]


def test_un_valor_de_catalogo_se_dice_por_su_nombre():
    nombres = {"planes": {"mi_amigo_fiel": "Mi Amigo Fiel"}, "ciudades": {"Bogotá": "Bogotá"}}
    condicion = {"campo": "plan.codigo", "op": "in", "valor": ["mi_amigo_fiel", "otro"]}
    assert (
        describir_condicion(condicion, "servicio.elegibilidad", nombres)
        == "Plan: Mi Amigo Fiel o otro"
    )
    accion = {"tipo": "recomendar", "plan_codigo": "mi_amigo_fiel", "motivo": "Es el principal"}
    assert describir_accion(accion, nombres=nombres) == (
        "Recomienda el plan «Mi Amigo Fiel»: Es el principal"
    )
    modalidad = {"campo": "servicio.modalidad", "op": "eq", "valor": "clinico"}
    assert describir_condicion(modalidad) == "Modalidad del servicio: en la clínica"


async def test_los_eventos_dicen_campos_opciones_y_acciones(client: AsyncClient, db, planes, admin):
    """Lo lee administracion, que configura las reglas (Seccion 12): con la base filtrando por
    perfil (RLS), un catalogo que el perfil no puede leer saldria vacio sin error."""
    from tests.conftest import login

    resp = await client.get("/api/v1/reglas/eventos", headers=await login(client, admin.email))
    assert resp.status_code == 200, resp.text
    eventos = {e["evento"]: e for e in resp.json()}
    assert set(eventos) == set(motor.EVENTOS)  # el retirado no se ofrece

    alerta = eventos["cartera.alerta"]
    assert alerta["nombre"] == "Avisos escalonados de mora"
    assert alerta["cuando"].startswith("Cada día")
    assert alerta["admite_plan"] is False and alerta["planes"] == []
    [dias] = alerta["campos"]
    assert dias["nombre"] == "Días de mora" and dias["tipo"] == "numero"
    assert dias["operadores"][0] == {"valor": "gte", "nombre": "al menos"}
    [notificar] = alerta["acciones"]
    assert notificar["nombre"] == "Avisar por WhatsApp"
    [plantilla] = notificar["parametros"]
    # Las plantillas de mora esperan su registro en Meta: se ofrecen igual, por su nombre.
    assert {"valor": "aviso_mora", "nombre": "Aviso de mora · aún sin registrar"} in plantilla[
        "opciones"
    ]

    elegibilidad = eventos["servicio.elegibilidad"]
    assert elegibilidad["admite_plan"] is True and elegibilidad["planes"]
    campos = {c["campo"]: c for c in elegibilidad["campos"]}
    assert {"valor": "Bogotá", "nombre": "Bogotá"} in campos["familia.ciudad"]["opciones"]
    assert {"valor": "en_mora", "nombre": "En mora"} in campos["familia.estado"]["opciones"]
    assert campos["plan.codigo"]["opciones"], "los planes llegan por conectar_planes"
    [recomendar] = eventos["plan.recomendacion"]["acciones"]
    plan = next(p for p in recomendar["parametros"] if p["nombre"] == "plan_codigo")
    assert plan["opciones"] == campos["plan.codigo"]["opciones"]


async def test_describir_un_borrador_sin_guardarlo(client: AsyncClient, headers):
    resp = await client.post(
        "/api/v1/reglas/describir",
        json={
            "evento": "servicio.elegibilidad",
            "condicion": {
                "todas": [
                    {"campo": "familia.ciudad", "op": "eq", "valor": "Medellín"},
                    {"campo": "servicio.modalidad", "op": "eq", "valor": "domiciliario"},
                ]
            },
            "accion": {"tipo": "rechazar", "motivo": "Sin médicos a domicilio"},
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == {
        "condicion_texto": "Ciudad de la familia: Medellín y Modalidad del servicio: a domicilio",
        "accion_texto": "No lo permite: Sin médicos a domicilio",
    }
    invalida = await client.post(
        "/api/v1/reglas/describir",
        json={
            "evento": "cartera.alerta",
            "condicion": {"campo": "ciudad", "op": "eq", "valor": "x"},
        },
        headers=headers,
    )
    assert invalida.status_code == 422
    assert "no da el dato" in invalida.json()["detail"]


async def test_crear_por_campos_sin_codigo_ni_clave(client: AsyncClient, headers):
    """El editor no pide el codigo interno ni la clave del aviso: salen del nombre."""
    datos = {
        "nombre": "Aviso de mora a los 3 días",
        "evento": "cartera.alerta",
        "condicion": {"campo": "dias_mora", "op": "gte", "valor": 3},
        "accion": {"tipo": "notificar", "plantilla": "aviso_mora"},
    }
    primera = await client.post("/api/v1/reglas", json=datos, headers=headers)
    assert primera.status_code == 201, primera.text
    assert primera.json()["codigo"] == "aviso_de_mora_a_los_3_dias"
    assert primera.json()["accion"]["clave"] == "aviso_de_mora_a_los_3_dias"
    segunda = await client.post("/api/v1/reglas", json=datos, headers=headers)
    assert segunda.json()["codigo"] == "aviso_de_mora_a_los_3_dias_2"


async def test_editar_un_aviso_conserva_su_clave(client: AsyncClient, headers):
    """La clave dice que avisos ya se enviaron por cada cuota: cambiarla los repetiria."""
    reglas = (await client.get("/api/v1/reglas", headers=headers)).json()
    aviso = next(r for r in reglas if r["codigo"] == "alerta_mora_5")
    resp = await client.patch(
        f"/api/v1/reglas/{aviso['id']}",
        json={"accion": {"tipo": "notificar", "plantilla": "cuota_vencida"}},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["accion"] == {
        "tipo": "notificar",
        "plantilla": "cuota_vencida",
        "clave": "mora_5",
    }


async def test_un_valor_que_no_esta_en_el_catalogo_se_rechaza(client: AsyncClient, headers):
    """Una ciudad mal escrita haria una regla que no aplica nunca."""
    reglas = (await client.get("/api/v1/reglas", headers=headers)).json()
    regla = next(r for r in reglas if r["codigo"] == "cambio_plan_en_mora")
    resp = await client.patch(
        f"/api/v1/reglas/{regla['id']}",
        json={"condicion": {"campo": "familia.ciudad", "op": "eq", "valor": "Gotham"}},
        headers=headers,
    )
    assert resp.status_code == 422 and "no está en el catálogo" in resp.json()["detail"]


async def test_un_plan_que_no_existe_o_en_un_evento_que_no_lo_admite(
    client: AsyncClient, headers, planes
):
    base = {
        "nombre": "Avisar distinto en un plan",
        "evento": "cartera.alerta",
        "condicion": {},
        "accion": {"tipo": "notificar", "plantilla": "aviso_mora"},
    }
    planes = (await client.get("/api/v1/reglas/eventos", headers=headers)).json()
    plan_id = next(e for e in planes if e["admite_plan"])["planes"][0]["id"]
    resp = await client.post("/api/v1/reglas", json={**base, "plan_id": plan_id}, headers=headers)
    assert resp.status_code == 422 and "no admite reglas de un solo plan" in resp.json()["detail"]
    otro = {
        **base,
        "evento": "servicio.elegibilidad",
        "accion": {"tipo": "rechazar", "motivo": "No"},
        "plan_id": "0190f5d6-0000-7000-8000-000000000000",
    }
    resp = await client.post("/api/v1/reglas", json=otro, headers=headers)
    assert resp.status_code == 422 and "no existe" in resp.json()["detail"]
    del otro["plan_id"]
    resp = await client.post("/api/v1/reglas", json={**otro, "plan_id": plan_id}, headers=headers)
    assert resp.status_code == 201, resp.text


async def test_probar_solo_acepta_lo_que_da_el_evento(client: AsyncClient, headers):
    resp = await client.post(
        "/api/v1/reglas/probar",
        json={"evento": "cartera.alerta", "contexto": {"familia": {"ciudad": "Cali"}}},
        headers=headers,
    )
    assert resp.status_code == 422 and "familia.ciudad" in resp.json()["detail"]


async def test_una_regla_de_un_evento_retirado_no_se_edita(client: AsyncClient, db, headers):
    db.add(
        Regla(
            codigo="retirada",
            nombre="Retirada",
            evento="plan.mascota",
            condicion={},
            accion={"tipo": "rechazar", "motivo": "x"},
        )
    )
    await db.commit()
    regla = next(
        r
        for r in (await client.get("/api/v1/reglas", headers=headers)).json()
        if r["codigo"] == "retirada"
    )
    resp = await client.patch(
        f"/api/v1/reglas/{regla['id']}", json={"nombre": "Otra"}, headers=headers
    )
    assert resp.status_code == 422


async def test_lo_sembrado_se_lee_sin_codigos(client: AsyncClient, headers, planes):
    """Seccion 13: ni la regla en palabras ni una opcion del editor ensenan un codigo interno
    (`aviso_mora`, `mi_amigo_fiel`). Las plantillas de mora, sin registrar aun, por su nombre."""
    reglas = (await client.get("/api/v1/reglas", headers=headers)).json()
    for r in reglas:
        assert "_" not in r["condicion_texto"] + r["accion_texto"], r["codigo"]
    aviso = next(r for r in reglas if r["codigo"] == "alerta_mora_5")
    assert aviso["accion_texto"] == "Envía por WhatsApp «Aviso de mora»"
    for evento in (await client.get("/api/v1/reglas/eventos", headers=headers)).json():
        nombres = [o["nombre"] for c in evento["campos"] for o in c["opciones"] or []]
        nombres += [
            o["nombre"]
            for a in evento["acciones"]
            for p in a["parametros"]
            for o in p["opciones"] or []
        ]
        assert not [n for n in nombres if "_" in n], evento["evento"]


@pytest.mark.parametrize(
    ("condicion", "texto"),
    [
        ({"campo": "dias_mora", "op": "eq", "valor": 3}, "Días de mora: igual a 3"),
        ({"campo": "dias_mora", "op": "lte", "valor": 30}, "Días de mora: como mucho 30"),
    ],
)
def test_la_frase_usa_las_palabras_del_editor(condicion, texto):
    """El control dice «al menos», «como mucho», «igual a»: la frase, lo mismo."""
    assert describir_condicion(condicion) == texto


async def test_el_administrador_ve_las_plantillas_que_citan_las_reglas_y_faltan(
    client: AsyncClient, db, admin
):
    """Las reglas sembradas de mora citan plantillas que no estan en el catalogo: sus avisos no
    salen, y el Inicio del administrador lo dice (docs/perfiles-y-permisos.md)."""
    from tests.conftest import login

    resp = await client.get(
        "/api/v1/reglas/plantillas-faltantes", headers=await login(client, admin.email)
    )
    assert resp.status_code == 200, resp.text
    faltantes = {p["codigo"]: p for p in resp.json()}
    assert "aviso_mora" in faltantes
    assert faltantes["aviso_mora"]["reglas"], "dice que reglas la citan"
    # No esta en el catalogo: hay que registrarla, no esperar a que Meta la apruebe.
    assert faltantes["aviso_mora"]["registrada"] is False

    # Registrada pero sin aprobar: sigue faltando, y ya no es por registrarla.
    db.add(
        PlantillaWhatsApp(
            nombre="aviso_mora",
            cuerpo="Hola {{1}}",
            variables=["v1"],
            estado_aprobacion="enviada",
            activa=False,  # solo una aprobada puede estar activa (la base lo exige)
        )
    )
    await db.commit()
    resp = await client.get(
        "/api/v1/reglas/plantillas-faltantes", headers=await login(client, admin.email)
    )
    assert {p["codigo"]: p for p in resp.json()}["aviso_mora"]["registrada"] is True
