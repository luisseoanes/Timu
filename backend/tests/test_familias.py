import pytest_asyncio
from httpx import AsyncClient

from app.core.enums import Rol
from app.core.security import hash_password
from app.modules.auth.models import Usuario


@pytest_asyncio.fixture
async def token(client: AsyncClient, db) -> str:
    db.add(
        Usuario(
            email="admin@timu.co",
            nombre="Admin",
            rol=Rol.ADMIN,
            hashed_password=hash_password("secreto123"),
        )
    )
    await db.commit()
    resp = await client.post(
        "/api/v1/auth/login", data={"username": "admin@timu.co", "password": "secreto123"}
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def test_crear_y_listar_familia(client: AsyncClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "titular_nombre": "Ana Ruiz",
        "documento": "1020304050",
        "telefono": "573001112233",
        "ciudad": "Bogota",
        "mascotas": [{"nombre": "Kira", "especie": "canino"}],
    }
    creada = await client.post("/api/v1/familias", json=payload, headers=headers)
    assert creada.status_code == 201, creada.text
    assert creada.json()["estado"] == "prospecto"
    assert len(creada.json()["mascotas"]) == 1

    listado = await client.get("/api/v1/familias", params={"q": "Ana"}, headers=headers)
    assert listado.status_code == 200
    assert listado.json()["total"] == 1


async def test_requiere_autenticacion(client: AsyncClient):
    resp = await client.get("/api/v1/familias")
    assert resp.status_code == 401
