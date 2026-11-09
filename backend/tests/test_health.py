import pytest

from app.api import salud


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


# --- Los chequeos en si -----------------------------------------------------------------------
# Las pruebas de arriba sustituyen los chequeos; estas los ejecutan con dobles solo en el borde
# (cliente de Redis, ping de Celery), que es donde un fallo real se convierte en "falla".


async def test_db_responde(db):
    assert await salud.revisar_db(db) == "ok"


class _SesionRota:
    def __init__(self, efecto):
        self._efecto = efecto

    async def execute(self, _):
        return await self._efecto()


async def test_db_que_falla_o_no_contesta_a_tiempo(monkeypatch):
    import asyncio

    async def revienta():
        raise ConnectionError("sin base")

    async def cuelga():
        await asyncio.sleep(1)

    monkeypatch.setattr(salud, "TIMEOUT_SEGUNDOS", 0.01)
    assert await salud.revisar_db(_SesionRota(revienta)) == "falla"
    assert await salud.revisar_db(_SesionRota(cuelga)) == "falla"


class _RedisFalso:
    creados: list["_RedisFalso"] = []

    def __init__(self, url, error=None):
        self.url, self.error, self.cerrado = url, error, False

    async def ping(self):
        if self.error:
            raise self.error
        return True

    async def aclose(self):
        self.cerrado = True


@pytest.fixture
def redis_falso(monkeypatch):
    from redis.asyncio import Redis

    _RedisFalso.creados = []

    def instalar(error=None):
        def from_url(url, **_):
            cliente = _RedisFalso(url, error)
            _RedisFalso.creados.append(cliente)
            return cliente

        monkeypatch.setattr(Redis, "from_url", staticmethod(from_url))

    return instalar


async def test_redis_responde_y_se_cierra_la_conexion(redis_falso):
    from app.core.config import settings

    redis_falso()
    assert await salud.revisar_redis() == "ok"
    (cliente,) = _RedisFalso.creados
    assert cliente.url == settings.REDIS_URL
    assert cliente.cerrado


async def test_redis_caido_da_falla_y_tambien_cierra(redis_falso):
    redis_falso(ConnectionError("redis caido"))
    assert await salud.revisar_redis() == "falla"
    assert _RedisFalso.creados[0].cerrado, "una conexion fallida no puede quedar abierta"


def _broker_caido():
    raise OSError("broker caido")


@pytest.mark.parametrize(
    ("ping", "esperado"),
    [
        (lambda timeout: [{"celery@worker": {"ok": "pong"}}], "ok"),
        (lambda timeout: [], "falla"),  # Redis contesta pero no hay ningun worker vivo
        (lambda timeout: _broker_caido(), "falla"),
    ],
)
async def test_trabajadores(monkeypatch, ping, esperado):
    from app.workers.celery_app import celery_app

    monkeypatch.setattr(celery_app.control, "ping", ping)
    assert await salud.revisar_trabajadores() == esperado


async def test_health_degradado_sin_workers(client, monkeypatch):
    monkeypatch.setattr(salud, "revisar_redis", _ok)
    monkeypatch.setattr(salud, "revisar_trabajadores", _falla)
    resp = await client.get("/health")
    assert resp.status_code == 503
    assert resp.json()["checks"] == {"db": "ok", "redis": "ok", "workers": "falla"}


async def test_health_degradado_sin_base(client, monkeypatch, dependencias_ok):
    monkeypatch.setattr(salud, "revisar_db", _falla_con_sesion)
    resp = await client.get("/health")
    assert resp.status_code == 503
    assert resp.json()["status"] == "degradado"
    assert resp.json()["checks"]["db"] == "falla"


async def _falla_con_sesion(_db) -> str:
    return "falla"
