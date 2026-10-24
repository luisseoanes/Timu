"""F2-ALI-01..04 Convenios, remision con validaciones, acceso minimo de la aliada y
liquidacion."""

from datetime import timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.core.enums import Rol
from app.core.tiempo import hoy
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


# --- F2-ALI-02 Remision -----------------------------------------------------------------------


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


# --- F2-ALI-03 Acceso de la aliada ------------------------------------------------------------


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


# --- F2-ALI-04 Liquidacion --------------------------------------------------------------------


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
