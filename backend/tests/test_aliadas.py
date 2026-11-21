"""6.22 Convenios, remision con validaciones, acceso minimo de la aliada y
liquidacion."""

from datetime import timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import text, update

from app.core.enums import EstadoServicio, Rol
from app.core.tiempo import hoy
from app.modules.aliadas.models import RemisionAliada
from app.modules.servicios.models import Servicio
from tests import fabricas
from tests.conftest import crear_usuario, login

pytestmark = pytest.mark.integration

HOY = hoy()


@pytest.fixture
async def escenario(client: AsyncClient, db, headers):
    """Clinica con convenio para el plan de una familia afiliada (cupo 1 al ano)."""
    plan = await db.run_sync(
        fabricas.plan,
        "con_aliada",
        60_000,
        1,
        None,
        [{"tipo_servicio_codigo": "atencion_aliada", "cupo": 1, "periodo_cupo": "anual"}],
    )
    familia, contrato = await fabricas.afiliada(db, HOY, plan)
    datos = {
        "familia_id": familia.id,
        "mascota_id": familia.mascotas[0].id,
        "plan_id": plan.id,
        "contrato_id": contrato.id,
        "titular": familia.titular_nombre,
        "telefono": familia.telefono,
        "documento": familia.documento,
    }
    await db.commit()
    clinica = (
        await client.post(
            "/api/v1/aliadas",
            json={"nombre": "Clinica Norte", "nit": "900123456", "ciudad": "Cali"},
            headers=headers,
        )
    ).json()
    convenio = await client.post(
        f"/api/v1/aliadas/{clinica['id']}/convenios",
        json={
            "plan_id": str(plan.id),
            "beneficio": "Consulta especializada",
            "cobertura_pct": 80,
            "tarifa": "120000",
            "tope_cubierto": "100000",
            "vigente_desde": str(HOY - timedelta(days=30)),
        },
        headers=headers,
    )
    assert convenio.status_code == 201, convenio.text
    return {**datos, "clinica_id": clinica["id"]}


async def _remitir(client, headers, escenario, **extra):
    return await client.post(
        "/api/v1/aliadas/remisiones",
        json={
            "clinica_id": escenario["clinica_id"],
            "mascota_id": str(escenario["mascota_id"]),
            "motivo": "Ecografia abdominal",
            **extra,
        },
        headers=headers,
    )


@pytest.fixture
async def aliada(client: AsyncClient, db, escenario):
    from uuid import UUID

    await crear_usuario(
        db, "recepcion@norte.co", Rol.ALIADA, clinica_aliada_id=UUID(escenario["clinica_id"])
    )
    return await login(client, "recepcion@norte.co")


# --- 6.22 Remision -----------------------------------------------------------------------


async def test_remision_valida_y_consume_el_cupo(client, db, headers, escenario):
    resp = await _remitir(client, headers, escenario)
    assert resp.status_code == 201, resp.text
    remision = resp.json()
    assert remision["beneficio_aplicado"] == "Consulta especializada"
    assert len(remision["codigo"]) == 8
    servicio = await db.get(Servicio, remision["servicio_id"])
    assert (servicio.estado, servicio.autorizado, servicio.tipo) == ("agendado", True, "aliada")

    # El cupo anual del beneficio ya se uso.
    otra = await _remitir(client, headers, escenario)
    assert otra.status_code == 422 and "cupo" in otra.json()["detail"]

    # Anular libera el cupo.
    anulada = await client.post(
        f"/api/v1/aliadas/remisiones/{remision['id']}/anulacion",
        json={"motivo": "La familia no asistio"},
        headers=headers,
    )
    assert anulada.json()["estado"] == "anulada"
    assert (await _remitir(client, headers, escenario)).status_code == 201


async def test_la_bandeja_dice_de_quien_es_cada_remision_y_cuantas_hay(
    client, db, headers, escenario
):
    remision = (await _remitir(client, headers, escenario)).json()
    bandeja = await client.get(
        "/api/v1/aliadas/remisiones", params={"estado": "emitida"}, headers=headers
    )
    [fila] = bandeja.json()
    assert (fila["titular"], fila["clinica"]) == (escenario["titular"], "Clinica Norte")
    assert fila["mascota"] and fila["vencida"] is False

    # Pasada su fecha sigue emitida, pero la clinica ya no la acepta: la API lo dice.
    await db.execute(
        update(RemisionAliada)
        .where(RemisionAliada.id == remision["id"])
        .values(vence_en=HOY - timedelta(days=1))
    )
    await db.commit()
    [fila] = (
        await client.get(
            "/api/v1/aliadas/remisiones", params={"estado": "emitida"}, headers=headers
        )
    ).json()
    assert fila["vencida"] is True

    recuentos = await client.get("/api/v1/aliadas/remisiones/recuentos", headers=headers)
    assert recuentos.json() == {
        "emitida": 1,
        "utilizada": 0,
        "anulada": 0,
        "vencida": 0,
        "todas": 1,
    }
    de_otra = await client.get(
        "/api/v1/aliadas/remisiones/recuentos",
        params={"clinica_id": str(uuid4())},
        headers=headers,
    )
    assert de_otra.json()["todas"] == 0


async def test_no_se_remite_con_cartera_en_mora(client, db, headers, escenario):
    from app.modules.cartera.models import Contrato

    contrato = await db.get(Contrato, escenario["contrato_id"])
    contrato.estado = "en_mora"
    await db.commit()
    resp = await _remitir(client, headers, escenario)
    assert resp.status_code == 422 and "cartera" in resp.json()["detail"]


async def test_sin_convenio_vigente_no_se_remite(client, db, headers, escenario):
    otra = (
        await client.post(
            "/api/v1/aliadas", json={"nombre": "Sin convenio", "ciudad": "Cali"}, headers=headers
        )
    ).json()
    resp = await _remitir(client, headers, {**escenario, "clinica_id": otra["id"]})
    assert resp.status_code == 422 and "convenio" in resp.json()["detail"]


# --- 6.22 Acceso de la aliada ------------------------------------------------------------


async def test_aliada_ve_lo_minimo_y_reporta(client, db, headers, escenario, aliada):
    remision = (await _remitir(client, headers, escenario)).json()
    url = f"/api/v1/aliadas/mi-clinica/remisiones/{remision['codigo'].lower()}"

    vista = await client.get(url, headers=aliada)
    assert vista.status_code == 200, vista.text
    datos = vista.json()
    assert datos["vigente"] is True and datos["cobertura_pct"] == 80
    assert datos["documento_ultimos"] == escenario["documento"][-4:]
    texto = vista.text
    assert escenario["telefono"] not in texto and escenario["documento"] not in texto
    assert "direccion" not in datos and "estado_cartera" not in datos

    reporte = await client.post(
        f"{url}/atencion",
        json={"fecha": str(HOY), "valor_atencion": "150000", "resumen": "Ecografia normal"},
        headers=aliada,
    )
    assert reporte.status_code == 200, reporte.text
    # 80% de 150.000 = 120.000, pero el tope del convenio es 100.000.
    assert Decimal(reporte.json()["valor_cubierto"]) == Decimal("100000.00")
    servicio = await db.get(Servicio, remision["servicio_id"])
    await db.refresh(servicio)
    assert servicio.estado == "completado"

    otra_vez = await client.post(
        f"{url}/atencion",
        json={"fecha": str(HOY), "valor_atencion": "1", "resumen": "Duplicado"},
        headers=aliada,
    )
    assert otra_vez.status_code == 422


async def test_la_vista_dice_si_sirve_entre_que_fechas_y_la_especie_en_palabras(
    client, db, headers, escenario, aliada
):
    remision = (await _remitir(client, headers, escenario)).json()
    url = f"/api/v1/aliadas/mi-clinica/remisiones/{remision['codigo']}"

    datos = (await client.get(url, headers=aliada)).json()
    assert datos["vencida"] is False and datos["emitida_en"] == str(HOY)
    assert datos["atencion_desde"] == str(HOY) and datos["atencion_hasta"] == str(HOY)
    assert datos["mascota"]["especie_nombre"] != datos["mascota"]["especie"]
    assert datos["fecha_atencion"] is None and datos["valor_familia"] is None

    await db.execute(
        update(RemisionAliada)
        .where(RemisionAliada.codigo == remision["codigo"])
        .values(vence_en=HOY - timedelta(days=1))
    )
    await db.commit()
    vencida = (await client.get(url, headers=aliada)).json()
    assert vencida["vigente"] is False and vencida["vencida"] is True
    # Vencio antes de emitirse (la fecha se forzo): no hay ningun dia que reportar.
    assert vencida["atencion_desde"] is None and vencida["atencion_hasta"] is None


async def test_la_cobertura_se_ve_antes_de_reportar_y_es_la_que_se_reporta(
    client, headers, escenario, aliada
):
    remision = (await _remitir(client, headers, escenario)).json()
    url = f"/api/v1/aliadas/mi-clinica/remisiones/{remision['codigo']}"

    # 80 % de 100.000, por debajo del tope de 100.000.
    sin_tope = (
        await client.get(f"{url}/cobertura", params={"valor_atencion": "100000"}, headers=aliada)
    ).json()
    assert Decimal(sin_tope["valor_cubierto"]) == Decimal("80000")
    assert Decimal(sin_tope["valor_familia"]) == Decimal("20000")
    assert sin_tope["con_tope"] is False

    # 80 % de 150.000 serian 120.000: el tope deja 100.000 y la familia asume 50.000.
    con_tope = (
        await client.get(f"{url}/cobertura", params={"valor_atencion": "150000"}, headers=aliada)
    ).json()
    assert Decimal(con_tope["valor_cubierto"]) == Decimal("100000")
    assert Decimal(con_tope["valor_familia"]) == Decimal("50000")
    assert con_tope["con_tope"] is True

    cero = await client.get(f"{url}/cobertura", params={"valor_atencion": "0"}, headers=aliada)
    assert cero.status_code == 422

    reporte = (
        await client.post(
            f"{url}/atencion",
            json={"fecha": str(HOY), "valor_atencion": "150000", "resumen": "Ecografia normal"},
            headers=aliada,
        )
    ).json()
    assert reporte["estado"] == "utilizada" and reporte["fecha_atencion"] == str(HOY)
    assert Decimal(reporte["valor_cubierto"]) == Decimal(con_tope["valor_cubierto"])
    assert Decimal(reporte["valor_familia"]) == Decimal(con_tope["valor_familia"])


async def test_la_aliada_ve_su_clinica_y_lo_que_atendio(client, db, headers, escenario, aliada):
    clinica = (await client.get("/api/v1/aliadas/mi-clinica", headers=aliada)).json()
    assert clinica == {"nombre": "Clinica Norte", "ciudad": "Cali"}

    remision = (await _remitir(client, headers, escenario)).json()
    await client.post(
        f"/api/v1/aliadas/mi-clinica/remisiones/{remision['codigo']}/atencion",
        json={"fecha": str(HOY), "valor_atencion": "100000", "resumen": "Consulta"},
        headers=aliada,
    )
    mes = {"desde": str(HOY.replace(day=1)), "hasta": str(HOY)}
    atendidas = (
        await client.get("/api/v1/aliadas/mi-clinica/atendidas", params=mes, headers=aliada)
    ).json()
    assert atendidas["atenciones"] == 1
    assert Decimal(atendidas["valor_atenciones"]) == Decimal("100000")
    assert Decimal(atendidas["valor_cubierto"]) == Decimal("80000")
    assert Decimal(atendidas["valor_familias"]) == Decimal("20000")
    (fila,) = atendidas["items"]
    assert fila["codigo"] == remision["codigo"] and fila["titular"] == escenario["titular"]
    assert "telefono" not in fila and "documento" not in fila

    # Lo mismo que liquida TIMU para esa clinica en el periodo.
    (liquidada,) = (
        await client.get("/api/v1/aliadas/liquidacion", params=mes, headers=headers)
    ).json()
    assert Decimal(liquidada["valor_cubierto"]) == Decimal(atendidas["valor_cubierto"])

    antes = {"desde": str(HOY - timedelta(days=60)), "hasta": str(HOY - timedelta(days=31))}
    vacio = (
        await client.get("/api/v1/aliadas/mi-clinica/atendidas", params=antes, headers=aliada)
    ).json()
    assert vacio["atenciones"] == 0 and vacio["items"] == []

    al_reves = {"desde": str(HOY), "hasta": str(HOY - timedelta(days=1))}
    malo = await client.get("/api/v1/aliadas/mi-clinica/atendidas", params=al_reves, headers=aliada)
    assert malo.status_code == 422


async def test_la_aliada_no_ve_lo_atendido_por_otra_clinica(client, db, headers, escenario):
    from uuid import UUID

    remision = (await _remitir(client, headers, escenario)).json()
    duena = UUID(escenario["clinica_id"])
    await crear_usuario(db, "recepcion@norte.co", Rol.ALIADA, clinica_aliada_id=duena)
    await client.post(
        f"/api/v1/aliadas/mi-clinica/remisiones/{remision['codigo']}/atencion",
        json={"fecha": str(HOY), "valor_atencion": "100000", "resumen": "Consulta"},
        headers=await login(client, "recepcion@norte.co"),
    )
    otra = (
        await client.post(
            "/api/v1/aliadas", json={"nombre": "Otra clinica", "ciudad": "Cali"}, headers=headers
        )
    ).json()
    await crear_usuario(db, "recepcion@otra.co", Rol.ALIADA, clinica_aliada_id=UUID(otra["id"]))
    ajena = await login(client, "recepcion@otra.co")

    mes = {"desde": str(HOY.replace(day=1)), "hasta": str(HOY)}
    vista = (
        await client.get("/api/v1/aliadas/mi-clinica/atendidas", params=mes, headers=ajena)
    ).json()
    assert vista["atenciones"] == 0
    assert (await client.get("/api/v1/aliadas/mi-clinica", headers=ajena)).json()[
        "nombre"
    ] == "Otra clinica"
    cobertura = await client.get(
        f"/api/v1/aliadas/mi-clinica/remisiones/{remision['codigo']}/cobertura",
        params={"valor_atencion": "1000"},
        headers=ajena,
    )
    assert cobertura.status_code == 404


@pytest.mark.parametrize("como", ["baja", "cancelacion"])
async def test_cancelar_el_contrato_corta_la_vigencia_de_las_remisiones_por_usar(
    client, db, headers, escenario, aliada, monkeypatch, como
):
    """Sin contrato no hay cobertura: la remision deja de servir el dia de la baja, pero una
    atencion hecha hasta ese dia se sigue pudiendo reportar (decidido con el usuario)."""
    remision = (await _remitir(client, headers, escenario)).json()
    url = f"/api/v1/aliadas/mi-clinica/remisiones/{remision['codigo']}"
    if como == "baja":
        resp = await client.post(
            f"/api/v1/familias/{escenario['familia_id']}/baja",
            json={"motivo": "Se muda de ciudad"},
            headers=headers,
        )
    else:
        resp = await client.post(
            f"/api/v1/cartera/contratos/{escenario['contrato_id']}/cancelar",
            json={"motivo": "Se muda de ciudad"},
            headers=headers,
        )
    assert resp.status_code == 200, resp.text
    await db.commit()
    corte = (await client.get(url, headers=aliada)).json()
    assert corte["estado"] == "emitida" and corte["vence_en"] == str(HOY)
    assert corte["atencion_hasta"] == str(HOY)

    # Al dia siguiente ya vencio: lo atendido despues de la baja no se reporta...
    monkeypatch.setattr("app.modules.aliadas.service.hoy", lambda: HOY + timedelta(days=1))
    vencida = (await client.get(url, headers=aliada)).json()
    assert vencida["vencida"] is True and vencida["atencion_hasta"] == str(HOY)
    despues = await client.post(
        f"{url}/atencion",
        json={
            "fecha": str(HOY + timedelta(days=1)),
            "valor_atencion": "100000",
            "resumen": "Radiografia",
        },
        headers=aliada,
    )
    assert despues.status_code == 422
    assert "fuera de la vigencia" in despues.json()["detail"]
    # ...pero lo atendido hasta ese dia, si.
    antes = await client.post(
        f"{url}/atencion",
        json={"fecha": str(HOY), "valor_atencion": "100000", "resumen": "Rx de cadera"},
        headers=aliada,
    )
    assert antes.status_code == 200, antes.text
    assert antes.json()["estado"] == "utilizada"


async def test_la_remision_sin_usar_vence_pasado_el_plazo_y_libera_el_cupo(
    client, db, headers, escenario, aliada, en_worker, monkeypatch
):
    """6.22 Antes, una remision que vencia sin usarse dejaba su servicio agendado para siempre y
    el cupo del beneficio ocupado. Pasado el plazo para reportar, vence y libera el cupo."""
    from app.core.config import settings
    from app.workers.tasks.aliadas import vencer_remisiones

    remision = (await _remitir(client, headers, escenario)).json()
    url = f"/api/v1/aliadas/mi-clinica/remisiones/{remision['codigo']}"
    vence = HOY + timedelta(days=settings.REMISION_VIGENCIA_DIAS)
    plazo = vence + timedelta(days=settings.REMISION_GRACIA_REPORTE_DIAS)
    assert (await client.get(url, headers=aliada)).json()["reportar_hasta"] == str(plazo)
    assert (await _remitir(client, headers, escenario)).status_code == 422  # cupo anual usado

    # El ultimo dia del plazo sigue por usar: la clinica aun puede reportar lo atendido.
    monkeypatch.setattr("app.modules.aliadas.service.hoy", lambda: plazo)
    assert await en_worker(vencer_remisiones) == {"vencidas": 0}

    monkeypatch.setattr("app.modules.aliadas.service.hoy", lambda: plazo + timedelta(days=1))
    assert await en_worker(vencer_remisiones) == {"vencidas": 1}
    await db.commit()
    fila = await db.get(RemisionAliada, remision["id"])
    servicio = await db.get(Servicio, remision["servicio_id"])
    await db.refresh(fila)
    await db.refresh(servicio)
    assert (fila.estado, servicio.estado) == ("vencida", "cancelado")
    assert (await en_worker(vencer_remisiones)) == {"vencidas": 0}

    vista = (await client.get(url, headers=aliada)).json()
    assert (vista["estado"], vista["vencida"], vista["reportar_hasta"]) == ("vencida", True, None)
    reporte = await client.post(
        f"{url}/atencion",
        json={"fecha": str(HOY), "valor_atencion": "100000", "resumen": "Consulta"},
        headers=aliada,
    )
    assert reporte.status_code == 422 and "plazo" in reporte.json()["detail"]
    recuentos = await client.get("/api/v1/aliadas/remisiones/recuentos", headers=headers)
    assert recuentos.json()["vencida"] == 1
    # El cupo del beneficio queda libre.
    assert (await _remitir(client, headers, escenario)).status_code == 201


async def test_pasado_el_plazo_no_se_reporta_aunque_aun_no_haya_vencido(
    client, headers, escenario, aliada, monkeypatch
):
    """El plazo vale por si mismo: no depende de la hora a la que corra el proceso diario."""
    from app.core.config import settings

    remision = (await _remitir(client, headers, escenario)).json()
    url = f"/api/v1/aliadas/mi-clinica/remisiones/{remision['codigo']}"
    dias = settings.REMISION_VIGENCIA_DIAS + settings.REMISION_GRACIA_REPORTE_DIAS + 1
    monkeypatch.setattr("app.modules.aliadas.service.hoy", lambda: HOY + timedelta(days=dias))
    vista = (await client.get(url, headers=aliada)).json()
    assert vista["estado"] == "emitida" and vista["reportar_hasta"] is None
    reporte = await client.post(
        f"{url}/atencion",
        json={"fecha": str(HOY), "valor_atencion": "100000", "resumen": "Consulta"},
        headers=aliada,
    )
    assert reporte.status_code == 422 and "plazo" in reporte.json()["detail"]


async def test_vence_aunque_su_servicio_ya_se_haya_cancelado(
    client, db, headers, escenario, en_worker, monkeypatch
):
    """Si alguien cancelo el servicio desde Servicios, no hay cupo que liberar: solo vence."""
    from app.modules.servicios import service as servicios
    from app.workers.tasks.aliadas import vencer_remisiones

    remision = (await _remitir(client, headers, escenario)).json()

    def cancelar(s):
        servicio = s.get(Servicio, UUID(remision["servicio_id"]))
        servicios.cambiar_estado(s, servicio, EstadoServicio.CANCELADO, "La familia desistio")

    await db.run_sync(cancelar)
    await db.commit()
    monkeypatch.setattr("app.modules.aliadas.service.hoy", lambda: HOY + timedelta(days=60))
    assert await en_worker(vencer_remisiones) == {"vencidas": 1}
    fila = await db.get(RemisionAliada, remision["id"])
    await db.refresh(fila)
    assert fila.estado == "vencida"


async def test_la_baja_no_toca_las_remisiones_ya_usadas(client, db, headers, escenario, aliada):
    remision = (await _remitir(client, headers, escenario)).json()
    url = f"/api/v1/aliadas/mi-clinica/remisiones/{remision['codigo']}"
    await client.post(
        f"{url}/atencion",
        json={"fecha": str(HOY), "valor_atencion": "100000", "resumen": "Consulta"},
        headers=aliada,
    )
    await client.post(
        f"/api/v1/familias/{escenario['familia_id']}/baja",
        json={"motivo": "Se muda de ciudad"},
        headers=headers,
    )
    await db.commit()
    usada = (await client.get(url, headers=aliada)).json()
    assert usada["estado"] == "utilizada" and usada["vence_en"] == remision["vence_en"]


async def test_aliada_no_ve_remisiones_de_otra_clinica(client, db, headers, escenario, aliada):
    otra = (
        await client.post(
            "/api/v1/aliadas", json={"nombre": "Otra clinica", "ciudad": "Cali"}, headers=headers
        )
    ).json()
    await client.post(
        f"/api/v1/aliadas/{otra['id']}/convenios",
        json={
            "beneficio": "General",
            "tarifa": "50000",
            "vigente_desde": str(HOY - timedelta(days=1)),
        },
        headers=headers,
    )
    ajena = (await _remitir(client, headers, {**escenario, "clinica_id": otra["id"]})).json()
    resp = await client.get(
        f"/api/v1/aliadas/mi-clinica/remisiones/{ajena['codigo']}", headers=aliada
    )
    assert resp.status_code == 404


async def test_aliada_no_entra_al_resto_del_sistema(client, aliada):
    for ruta in ("/api/v1/familias", "/api/v1/aliadas/remisiones", "/api/v1/servicios"):
        assert (await client.get(ruta, headers=aliada)).status_code == 403, ruta


async def test_usuario_aliado_exige_su_clinica(client, headers):
    resp = await client.post(
        "/api/v1/auth/usuarios",
        json={
            "email": "x@aliada.co",
            "nombre": "Recepcion",
            "password": "secreto123",
            "rol": "aliada",
        },
        headers=headers,
    )
    assert resp.status_code == 422


# --- 6.22 Liquidacion --------------------------------------------------------------------


async def test_liquidacion_por_periodo(client, db, headers, escenario, aliada):
    remision = (await _remitir(client, headers, escenario)).json()
    await client.post(
        f"/api/v1/aliadas/mi-clinica/remisiones/{remision['codigo']}/atencion",
        json={"fecha": str(HOY), "valor_atencion": "100000", "resumen": "Consulta"},
        headers=aliada,
    )
    params = {"desde": str(HOY - timedelta(days=1)), "hasta": str(HOY)}
    (fila,) = (
        await client.get("/api/v1/aliadas/liquidacion", params=params, headers=headers)
    ).json()
    assert fila["atenciones"] == 1
    assert Decimal(fila["valor_atenciones"]) == Decimal("100000")
    assert Decimal(fila["saldo_a_pagar"]) == Decimal("80000")
    assert Decimal(fila["valor_familias"]) == Decimal("20000")

    csv = await client.get(
        "/api/v1/aliadas/liquidacion", params={**params, "formato": "csv"}, headers=headers
    )
    assert csv.headers["content-type"].startswith("text/csv")
    assert remision["codigo"] in csv.text and "TOTAL" in csv.text


async def test_la_aliada_tiene_sesion_reconocible_y_la_cierra(client, aliada):
    """El panel sabe quien inicio sesion por /auth/me; sin el, la aliada quedaba por fuera."""
    me = await client.get("/api/v1/auth/me", headers=aliada)
    assert me.status_code == 200
    assert me.json()["rol"] == "aliada"
    assert (await client.post("/api/v1/auth/logout", headers=aliada)).status_code == 200


# --- R3-PUB-04 La red de aliadas de la portada ----------------------------------------------------

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32


async def _clinica(client: AsyncClient, headers, **extra) -> dict:
    datos = {"nombre": "Vida Animal", "ciudad": "Envigado", **extra}
    resp = await client.post("/api/v1/aliadas", json=datos, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_la_portada_muestra_solo_las_aliadas_que_se_eligen_en_su_orden(
    client: AsyncClient, headers, almacenamiento
):
    await _clinica(client, headers, nombre="Kahuana", en_portada=True, orden_portada=2)
    vida = await _clinica(
        client,
        headers,
        en_portada=True,
        orden_portada=1,
        tipo="clinica",
        atiende_24h=True,
        barrio=" Alcalá ",
        horario="24 horas",
        presentacion="Clínica con atención las 24 horas.",
        nit="900123456",
        email="vida@example.com",
    )
    await _clinica(client, headers, nombre="Interna sin portada")
    oculta = await _clinica(client, headers, nombre="Inactiva", en_portada=True)
    await client.patch(f"/api/v1/aliadas/{oculta['id']}", json={"activa": False}, headers=headers)
    resp = await client.put(
        f"/api/v1/aliadas/{vida['id']}/logo",
        files={"logo": ("vida.png", PNG, "image/png")},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["logo_url"]

    # Sin sesion: lo que lee la portada.
    publicas = (await client.get("/api/v1/aliadas/publicas")).json()
    assert [a["nombre"] for a in publicas] == ["Vida Animal", "Kahuana"]
    primera = publicas[0]
    assert (primera["tipo_nombre"], primera["atiende_24h"], primera["barrio"]) == (
        "Clínica veterinaria",
        True,
        "Alcalá",
    )
    assert primera["logo_url"]
    # Nada interno: ni el NIT, ni el correo, ni los convenios.
    assert "nit" not in primera and "email" not in primera


async def test_quitar_el_logo_lo_deja_sin_borrar_el_archivo(
    client: AsyncClient, db, headers, almacenamiento
):
    vida = await _clinica(client, headers, en_portada=True)
    await client.put(
        f"/api/v1/aliadas/{vida['id']}/logo",
        files={"logo": ("vida.png", PNG, "image/png")},
        headers=headers,
    )
    resp = await client.delete(f"/api/v1/aliadas/{vida['id']}/logo", headers=headers)
    assert resp.status_code == 200 and resp.json()["logo_url"] is None
    assert (
        await db.scalar(text("SELECT count(*) FROM archivos WHERE proposito = 'logo_aliada'")) == 1
    )


async def test_el_logo_solo_admite_una_imagen(client: AsyncClient, headers, almacenamiento):
    vida = await _clinica(client, headers)
    resp = await client.put(
        f"/api/v1/aliadas/{vida['id']}/logo",
        files={"logo": ("x.pdf", b"%PDF-1.4" + b"0" * 32, "application/pdf")},
        headers=headers,
    )
    assert resp.status_code == 422


async def test_solo_el_administrador_cambia_el_logo(
    client: AsyncClient, db, headers, almacenamiento
):
    vida = await _clinica(client, headers)
    await crear_usuario(db, "ventas@timu.co", Rol.COMERCIAL)
    h = await login(client, "ventas@timu.co")
    resp = await client.put(
        f"/api/v1/aliadas/{vida['id']}/logo", files={"logo": ("v.png", PNG, "image/png")}, headers=h
    )
    assert resp.status_code == 403
