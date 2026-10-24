"""F0-04 Bitacora de auditoria."""

from httpx import AsyncClient
from sqlalchemy import select

from app.core.auditoria import RegistroAuditoria


async def _registros(db, entidad_id: str) -> list[RegistroAuditoria]:
    stmt = (
        select(RegistroAuditoria)
        .where(RegistroAuditoria.entidad_id == entidad_id)
        .order_by(RegistroAuditoria.created_at)
    )
    return list((await db.execute(stmt)).scalars())


def _familia(documento: str, **extra) -> dict:
    return {
        "titular_nombre": "Ana",
        "documento": documento,
        "telefono": "3001112233",
        "ciudad": "Cali",
        **extra,
    }


async def test_alta_y_cambio_de_estado_quedan_auditados(client: AsyncClient, db, admin, headers):
    creada = await client.post(
        "/api/v1/familias",
        json=_familia("1001"),
        headers={**headers, "X-Request-ID": "peticion-alta-01"},
    )
    familia_id = creada.json()["id"]

    await client.post(
        f"/api/v1/familias/{familia_id}/estado", json={"estado": "activa"}, headers=headers
    )

    registros = await _registros(db, familia_id)
    assert [r.accion for r in registros] == ["crear", "cambio_estado"]
    alta, cambio = registros
    assert alta.usuario_id == admin.id
    assert alta.request_id == "peticion-alta-01"
    assert alta.cambios["titular_nombre"] == [None, "Ana"]
    assert cambio.cambios == {"estado": ["prospecto", "activa"]}
    assert cambio.usuario_id == admin.id


async def test_edicion_sin_cambios_reales_no_deja_rastro(client: AsyncClient, db, headers):
    creada = await client.post("/api/v1/familias", json=_familia("1002"), headers=headers)
    familia_id = creada.json()["id"]
    await client.patch(f"/api/v1/familias/{familia_id}", json={"ciudad": "Cali"}, headers=headers)
    await client.patch(f"/api/v1/familias/{familia_id}", json={"ciudad": "Pasto"}, headers=headers)

    registros = await _registros(db, familia_id)
    assert [r.accion for r in registros] == ["crear", "editar"]
    assert registros[1].cambios == {"ciudad": ["Cali", "Pasto"]}


async def test_mascota_anidada_tambien_se_audita(client: AsyncClient, db, headers):
    payload = _familia("1003", mascotas=[{"nombre": "Kira", "especie": "canino"}])
    creada = await client.post("/api/v1/familias", json=payload, headers=headers)
    mascota_id = creada.json()["mascotas"][0]["id"]
    registros = await _registros(db, mascota_id)
    assert registros[0].entidad == "mascotas"
    assert registros[0].accion == "crear"
