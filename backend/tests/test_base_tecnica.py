"""Pruebas de la base tecnica transversal (F0-02, F0-05, F0-06, F0-10)."""

import pytest
from fastapi import APIRouter
from httpx import AsyncClient

from app.core.config import ConfiguracionInvalida, Settings
from app.main import app
from tests.conftest import PASSWORD

# --- F0-02 Formato de errores e identificador de peticion --------------------------------------

_router_prueba = APIRouter()


@_router_prueba.get("/__explota")
async def _explota() -> None:
    raise RuntimeError("fallo inesperado")


app.include_router(_router_prueba)


async def test_toda_respuesta_lleva_request_id(client: AsyncClient):
    resp = await client.get("/health/live")
    assert len(resp.headers["X-Request-ID"]) == 32


async def test_request_id_entrante_se_propaga(client: AsyncClient):
    resp = await client.get("/api/v1/familias", headers={"X-Request-ID": "traza-externa-123"})
    assert resp.headers["X-Request-ID"] == "traza-externa-123"
    assert resp.json()["request_id"] == "traza-externa-123"


async def test_request_id_entrante_invalido_se_reemplaza(client: AsyncClient):
    resp = await client.get("/health/live", headers={"X-Request-ID": "<script>"})
    assert resp.headers["X-Request-ID"] != "<script>"


async def test_error_de_validacion_detalla_campos(client: AsyncClient, headers):
    resp = await client.post("/api/v1/familias", json={"titular_nombre": "A"}, headers=headers)
    assert resp.status_code == 422
    cuerpo = resp.json()
    assert cuerpo["codigo"] == "validacion"
    campos = {e["campo"] for e in cuerpo["errores"]}
    assert {"body.titular_nombre", "body.documento", "body.telefono"} <= campos


async def test_error_no_controlado_no_filtra_detalles(client: AsyncClient):
    resp = await client.get("/__explota")
    assert resp.status_code == 500
    assert resp.json()["codigo"] == "error_interno"
    assert "fallo inesperado" not in resp.text
    assert resp.json()["request_id"] == resp.headers["X-Request-ID"]


# --- F0-05 Configuracion por ambiente ---------------------------------------------------------

PRODUCCION_VALIDA = {
    "ENVIRONMENT": "production",
    "DEBUG": False,
    "SECRET_KEY": "x" * 40,
    "POSTGRES_PASSWORD": "clave-real",
    "REDIS_URL": "redis://redis:6379/0",
    "BACKEND_CORS_ORIGINS": ["https://panel.timu.co"],
    "WHATSAPP_PHONE_NUMBER_ID": "1",
    "WHATSAPP_ACCESS_TOKEN": "t",
    "WHATSAPP_VERIFY_TOKEN": "v",
    "WHATSAPP_APP_SECRET": "a",
    "WOMPI_PUBLIC_KEY": "p",
    "WOMPI_PRIVATE_KEY": "k",
    "WOMPI_EVENTS_SECRET": "s",
    "WOMPI_INTEGRITY_SECRET": "i",
    "GOOGLE_MAPS_API_KEY": "g",
    "COOKIE_SECURE": True,
    "STORAGE_ENDPOINT_URL": None,
    "STORAGE_BUCKET": "timu",
    "STORAGE_ACCESS_KEY": "k",
    "STORAGE_SECRET_KEY": "s",
}


def test_produccion_completa_arranca():
    assert Settings(_env_file=None, **PRODUCCION_VALIDA).es_desplegado


def test_produccion_sin_variable_obligatoria_no_arranca():
    with pytest.raises(ConfiguracionInvalida, match="WOMPI_EVENTS_SECRET"):
        Settings(_env_file=None, **{**PRODUCCION_VALIDA, "WOMPI_EVENTS_SECRET": ""})


@pytest.mark.parametrize(
    "cambio",
    [
        {"SECRET_KEY": "cambiar-en-produccion"},
        {"SECRET_KEY": "corta"},
        {"DEBUG": True},
        {"BACKEND_CORS_ORIGINS": ["*"]},
        {"POSTGRES_PASSWORD": "timu"},
        {"COOKIE_SECURE": False},
        {"STORAGE_ACCESS_KEY": "minioadmin"},
    ],
)
def test_produccion_con_valores_inseguros_no_arranca(cambio):
    with pytest.raises(ConfiguracionInvalida):
        Settings(_env_file=None, **{**PRODUCCION_VALIDA, **cambio})


def test_local_no_exige_secretos():
    assert not Settings(_env_file=None, ENVIRONMENT="local").es_desplegado


# --- F0-06 Endurecimiento HTTP ----------------------------------------------------------------


async def test_encabezados_de_seguridad(client: AsyncClient):
    resp = await client.get("/health/live")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'none'" in resp.headers["Content-Security-Policy"]


async def test_documentacion_no_bloquea_scripts(client: AsyncClient):
    resp = await client.get("/docs")
    assert "Content-Security-Policy" not in resp.headers


async def test_carga_por_encima_del_tope_responde_413(client: AsyncClient, headers):
    grande = b"x" * (11 * 1024 * 1024)
    resp = await client.post(
        "/api/v1/familias",
        content=grande,
        headers={**headers, "Content-Type": "application/json"},
    )
    assert resp.status_code == 413
    assert resp.json()["codigo"] == "carga_demasiado_grande"


async def test_login_limitado_por_ip(client: AsyncClient, admin, monkeypatch):
    # Reloj fijo: la ventana es de un minuto y la prueba no debe depender de no cruzarlo.
    from app.core import rate_limit

    monkeypatch.setattr(rate_limit.time, "time", lambda: 1_790_000_010.0)
    datos = {"username": admin.email, "password": "incorrecta"}
    for _ in range(10):
        assert (await client.post("/api/v1/auth/login", data=datos)).status_code == 401
    resp = await client.post("/api/v1/auth/login", data={**datos, "password": PASSWORD})
    assert resp.status_code == 429
    assert resp.json()["codigo"] == "demasiadas_peticiones"
    assert int(resp.headers["Retry-After"]) > 0


async def test_cors_solo_para_origenes_permitidos(client: AsyncClient):
    permitido = await client.options(
        "/api/v1/familias",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    assert permitido.headers["access-control-allow-origin"] == "http://localhost:5173"
    ajeno = await client.options(
        "/api/v1/familias",
        headers={"Origin": "https://malicioso.com", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in ajeno.headers


# --- F0-10 Contrato de listados ---------------------------------------------------------------


async def _crear_familias(client: AsyncClient, headers, nombres: list[str]) -> None:
    for i, nombre in enumerate(nombres):
        resp = await client.post(
            "/api/v1/familias",
            json={
                "titular_nombre": nombre,
                "documento": f"10{i}00",
                "telefono": "3001112233",
                "ciudad": "Cali",
            },
            headers=headers,
        )
        assert resp.status_code == 201


async def test_listado_ordena_y_pagina(client: AsyncClient, headers):
    await _crear_familias(client, headers, ["Carla", "Andres", "Beatriz"])
    resp = await client.get(
        "/api/v1/familias",
        params={"orden": "titular_nombre", "limit": 2, "offset": 1},
        headers=headers,
    )
    cuerpo = resp.json()
    assert cuerpo["total"] == 3
    assert [f["titular_nombre"] for f in cuerpo["items"]] == ["Beatriz", "Carla"]
    assert (cuerpo["limit"], cuerpo["offset"]) == (2, 1)

    desc = await client.get(
        "/api/v1/familias", params={"orden": "-titular_nombre"}, headers=headers
    )
    assert desc.json()["items"][0]["titular_nombre"] == "Carla"


async def test_listado_rechaza_orden_no_permitido(client: AsyncClient, headers):
    resp = await client.get("/api/v1/familias", params={"orden": "documento"}, headers=headers)
    assert resp.status_code == 422
    assert "Permitidos" in resp.json()["detail"]


async def test_listado_rechaza_limite_excesivo(client: AsyncClient, headers):
    resp = await client.get("/api/v1/familias", params={"limit": 500}, headers=headers)
    assert resp.status_code == 422
