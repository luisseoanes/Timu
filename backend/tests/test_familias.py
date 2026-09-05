import pytest
from httpx import AsyncClient

from app.modules.auth.models import Usuario
from tests.conftest import autenticar

pytestmark = pytest.mark.integration

PAYLOAD = {
    "titular_nombre": "Ana Ruiz",
    "documento": "1020304050",
    "telefono": "573001112233",
    "ciudad": "Bogota",
    "mascotas": [{"nombre": "Kira", "especie": "canino"}],
}


async def test_crear_y_listar_familia(client: AsyncClient, usuario_admin: Usuario):
    await autenticar(client, "admin@timu.co", "secreto123")

    creada = await client.post("/api/v1/familias", json=PAYLOAD)
    assert creada.status_code == 201, creada.text
    assert creada.json()["estado"] == "prospecto"
    assert len(creada.json()["mascotas"]) == 1

    listado = await client.get("/api/v1/familias", params={"q": "Ana"})
    assert listado.status_code == 200
    assert listado.json()["total"] == 1


async def test_requiere_autenticacion(client: AsyncClient):
    resp = await client.get("/api/v1/familias")
    assert resp.status_code == 401


async def test_logout_invalida_la_sesion(client: AsyncClient, usuario_admin: Usuario):
    await autenticar(client, "admin@timu.co", "secreto123")
    assert (await client.get("/api/v1/familias")).status_code == 200

    assert (await client.post("/api/v1/auth/logout")).status_code == 200
    assert (await client.get("/api/v1/familias")).status_code == 401


async def test_el_token_no_viaja_en_el_cuerpo(client: AsyncClient, usuario_admin: Usuario):
    """La sesion va en cookie httpOnly: si el token apareciera en el JSON, una XSS
    podria leerlo y todo el cambio no serviria de nada."""
    resp = await client.post(
        "/api/v1/auth/login", data={"username": "admin@timu.co", "password": "secreto123"}
    )
    assert resp.status_code == 200
    assert "access_token" not in resp.text
    cookie = resp.cookies.get("timu_sesion")
    assert cookie, "el login debe dejar la cookie de sesion"
    assert "httponly" in resp.headers["set-cookie"].lower()
