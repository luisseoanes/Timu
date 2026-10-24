import pytest

from app.core import salud


async def _ok() -> str:
    return "ok"


async def _falla() -> str:
    return "falla"


@pytest.fixture
def dependencias_ok(monkeypatch):
    monkeypatch.setattr(salud, "revisar_redis", _ok)
    monkeypatch.setattr(salud, "revisar_trabajadores", _ok)


async def test_health_ok(client, dependencias_ok):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert resp.json()["checks"] == {"db": "ok", "redis": "ok", "workers": "ok"}


async def test_health_degradado_sin_redis(client, monkeypatch):
    monkeypatch.setattr(salud, "revisar_redis", _falla)
    resp = await client.get("/health")
    assert resp.status_code == 503
    assert resp.json()["status"] == "degradado"
    assert resp.json()["checks"]["workers"] == "falla"


async def test_liveness_no_toca_dependencias(client):
    resp = await client.get("/health/live")
    assert resp.status_code == 200
