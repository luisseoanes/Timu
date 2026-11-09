"""Outbox y eventos de dominio."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import eventos
from app.core.enums import EstadoServicio
from app.core.eventos import EventoDominio, EventoNoDeclarado, al_ocurrir, manejadores
from app.core.outbox import EventoSaliente, procesar_pendientes, publicar

# Eventos de mentira de este fichero: se declaran solo mientras corre cada prueba.
_DE_PRUEBA = {
    "prueba.a",
    "prueba.b",
    "prueba.bien",
    "prueba.concurrente",
    "prueba.falla",
    "prueba.intermitente",
    "prueba.lote",
    "prueba.ocurrida",
    "prueba.sin_manejador",
}


@pytest.fixture(autouse=True)
def _eventos_de_prueba(monkeypatch):
    monkeypatch.setattr(eventos, "_DECLARADOS", eventos._DECLARADOS | _DE_PRUEBA)


async def test_publicar_deja_el_evento_en_la_misma_transaccion(db: AsyncSession):
    publicar(db, EventoDominio(nombre="servicio.completado", datos={"servicio_id": "abc"}))
    await db.flush()

    fila = await db.scalar(select(EventoSaliente))
    assert fila is not None
    assert fila.nombre == "servicio.completado"
    assert fila.datos == {"servicio_id": "abc"}
    assert fila.procesado_en is None
    assert fila.intentos == 0


async def test_el_evento_se_va_con_el_rollback(db: AsyncSession):
    """El punto entero del outbox: si la transaccion no cuaja, el efecto externo
    tampoco. Con `tarea.delay()` el mensaje ya habria salido."""
    savepoint = await db.begin_nested()
    publicar(db, EventoDominio(nombre="servicio.cancelado"))
    await db.flush()
    await savepoint.rollback()

    assert await db.scalar(select(EventoSaliente)) is None


@pytest.mark.unit
def test_la_maquina_de_estados_publica_al_transicionar():
    from app.modules.servicios.state_machine import aplicar

    class SesionFalsa:
        def __init__(self):
            self.agregados = []

        def add(self, obj):
            self.agregados.append(obj)

    class ServicioFalso:
        id = "s-1"
        estado = EstadoServicio.AGENDADO

    db, servicio = SesionFalsa(), ServicioFalso()
    evento = aplicar(db, servicio, EstadoServicio.EN_RUTA)

    assert servicio.estado is EstadoServicio.EN_RUTA
    assert evento.nombre == "servicio.en_ruta"
    assert evento.datos["estado_anterior"] == "agendado"
    assert len(db.agregados) == 1, "la transicion debe dejar el evento en el outbox"


@pytest.mark.unit
def test_transicion_invalida_no_publica_nada():
    from app.modules.servicios.state_machine import TransicionInvalida, aplicar

    class SesionFalsa:
        def __init__(self):
            self.agregados = []

        def add(self, obj):
            self.agregados.append(obj)

    class ServicioFalso:
        id = "s-1"
        estado = EstadoServicio.COMPLETADO

    db, servicio = SesionFalsa(), ServicioFalso()
    with pytest.raises(TransicionInvalida):
        aplicar(db, servicio, EstadoServicio.EN_RUTA)
    assert db.agregados == []
    assert servicio.estado is EstadoServicio.COMPLETADO


@pytest.mark.unit
def test_registro_de_manejadores():
    @al_ocurrir("prueba.ocurrida")
    def _manejador(evento: EventoDominio) -> None:
        pass

    assert _manejador in manejadores("prueba.ocurrida")
    assert manejadores("prueba.inexistente") == []


@pytest.mark.unit
def test_suscribirse_a_un_evento_sin_declarar_falla_al_importar():
    """Un nombre mal escrito en el manejador lo dejaba sin llamar para siempre."""
    with pytest.raises(EventoNoDeclarado, match="servicio.completdo"):
        al_ocurrir("servicio.completdo")


@pytest.mark.unit
def test_publicar_un_evento_sin_declarar_falla_en_el_acto():
    """Y mal escrito al publicar, el evento se daba por procesado sin que nadie lo atendiera."""
    with pytest.raises(EventoNoDeclarado):
        EventoDominio("servicio.completdo")


@pytest.mark.unit
def test_cada_dominio_declara_los_eventos_que_publica():
    import app.main  # noqa: F401  carga todos los dominios, como la API
    import app.workers.celery_app  # noqa: F401  y todas las tareas, como el worker

    declarados = eventos.eventos_declarados() - _DE_PRUEBA
    assert {"servicio.completado", "mensaje.encolado", "pasarela.evento_recibido"} <= declarados
    assert set(eventos._MANEJADORES) - _DE_PRUEBA <= declarados


# --- Drenado (outbox.drenar) ------------------------------------------------------------------
# `procesar_pendientes` es lo que corre en produccion y lo que usa el fixture `tareas`.


@pytest.fixture
def registrar(monkeypatch):
    """Registra manejadores solo durante la prueba: el registro es global al proceso."""
    from app.core import eventos

    def _registrar(nombre: str, *funciones) -> None:
        monkeypatch.setitem(eventos._MANEJADORES, nombre, list(funciones))

    return _registrar


async def _evento(db: AsyncSession, nombre: str, **datos) -> EventoSaliente:
    fila = publicar(db, EventoDominio(nombre=nombre, datos=datos))
    await db.flush()
    return fila


async def test_drenar_despacha_en_orden_y_marca_procesado(db: AsyncSession, registrar):
    vistos: list[tuple[str, dict]] = []
    registrar("prueba.a", lambda e: vistos.append((e.nombre, e.datos)))
    registrar("prueba.b", lambda e: vistos.append((e.nombre, e.datos)))
    primero = await _evento(db, "prueba.a", n=1)
    segundo = await _evento(db, "prueba.b", n=2)

    resultado = await db.run_sync(procesar_pendientes)

    assert resultado == {"despachados": 2, "fallidos": 0}
    assert vistos == [("prueba.a", {"n": 1}), ("prueba.b", {"n": 2})]
    assert primero.procesado_en is not None and segundo.procesado_en is not None
    # Ya procesados: un segundo drenado no los repite.
    assert await db.run_sync(procesar_pendientes) == {"despachados": 0, "fallidos": 0}
    assert len(vistos) == 2


async def test_evento_sin_manejadores_se_da_por_procesado(db: AsyncSession):
    fila = await _evento(db, "prueba.sin_manejador")
    assert await db.run_sync(procesar_pendientes) == {"despachados": 1, "fallidos": 0}
    assert fila.procesado_en is not None


async def test_un_manejador_que_falla_deja_el_evento_pendiente_y_no_frena_el_lote(
    db: AsyncSession, registrar
):
    def revienta(_):
        raise RuntimeError("redis no responde " + "x" * 3000)

    vistos: list[str] = []
    registrar("prueba.falla", revienta)
    registrar("prueba.bien", lambda e: vistos.append(e.nombre))
    malo = await _evento(db, "prueba.falla")
    bueno = await _evento(db, "prueba.bien")

    assert await db.run_sync(procesar_pendientes) == {"despachados": 1, "fallidos": 1}
    assert bueno.procesado_en is not None and vistos == ["prueba.bien"]
    assert malo.procesado_en is None
    assert malo.intentos == 1
    assert malo.ultimo_error.startswith("redis no responde")
    assert len(malo.ultimo_error) == 2000, "el error se recorta para no inflar la tabla"


async def test_se_reintenta_hasta_max_intentos_y_luego_se_abandona(db: AsyncSession, registrar):
    from app.core.outbox import MAX_INTENTOS

    llamadas: list[int] = []

    def revienta(_):
        llamadas.append(1)
        raise RuntimeError("caido")

    registrar("prueba.falla", revienta)
    fila = await _evento(db, "prueba.falla")

    for _ in range(MAX_INTENTOS + 2):
        await db.run_sync(procesar_pendientes)

    assert len(llamadas) == MAX_INTENTOS
    assert fila.intentos == MAX_INTENTOS
    assert fila.procesado_en is None


async def test_un_evento_que_agota_los_intentos_avisa_como_error(
    db: AsyncSession, registrar, monkeypatch
):
    """Abandonado, el efecto no ocurre nunca: tiene que llegar a Sentry, no quedar en un
    warning mas entre los reintentos."""
    from app.core import outbox

    errores: list[tuple[str, dict]] = []

    class Registro:
        def warning(self, *_, **__):
            pass

        def error(self, mensaje, **datos):
            errores.append((mensaje, datos))

    monkeypatch.setattr(outbox, "logger", Registro())
    registrar("prueba.falla", lambda _: (_ for _ in ()).throw(RuntimeError("caido")))
    fila = await _evento(db, "prueba.falla")

    for _ in range(outbox.MAX_INTENTOS - 1):
        await db.run_sync(procesar_pendientes)
    assert errores == []
    await db.run_sync(procesar_pendientes)

    assert errores == [
        (
            "outbox.abandonado",
            {"evento": "prueba.falla", "evento_id": str(fila.id), "error": "caido"},
        )
    ]


async def test_un_reintento_que_sale_bien_cierra_el_evento(db: AsyncSession, registrar):
    respuestas = [RuntimeError("temporal"), None]

    def a_veces(_):
        error = respuestas.pop(0)
        if error:
            raise error

    registrar("prueba.intermitente", a_veces)
    fila = await _evento(db, "prueba.intermitente")

    assert await db.run_sync(procesar_pendientes) == {"despachados": 0, "fallidos": 1}
    assert await db.run_sync(procesar_pendientes) == {"despachados": 1, "fallidos": 0}
    assert fila.procesado_en is not None and fila.intentos == 1


async def test_el_lote_limita_cuantos_eventos_se_llevan(db: AsyncSession):
    for i in range(3):
        await _evento(db, "prueba.lote", i=i)
    assert await db.run_sync(procesar_pendientes, 2) == {"despachados": 2, "fallidos": 0}
    assert await db.run_sync(procesar_pendientes, 2) == {"despachados": 1, "fallidos": 0}


async def test_el_fixture_tareas_no_esconde_un_manejador_roto(db: AsyncSession, tareas, registrar):
    """En produccion el fallo se reintenta en silencio; en una prueba tiene que explotar."""

    def revienta(_):
        raise RuntimeError("manejador roto")

    registrar("prueba.falla", revienta)
    await _evento(db, "prueba.falla")
    with pytest.raises(AssertionError, match="manejador roto"):
        await tareas.drenar()


@pytest.mark.integration
def test_dos_workers_no_se_pisan_gracias_a_skip_locked(registrar, monkeypatch):
    """Con filas confirmadas de verdad (fuera de la transaccion de la prueba): mientras una
    conexion tiene bloqueado un evento, la tarea `outbox.drenar` lo salta en lugar de
    esperar o despacharlo dos veces, y se lleva el resto."""
    from contextlib import contextmanager

    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app.workers.tasks import outbox as tarea
    from tests.conftest import URL_SYNC

    vistos: list[str] = []
    registrar("prueba.concurrente", lambda e: vistos.append(e.datos["n"]))
    engine = create_engine(URL_SYNC)
    try:
        with Session(engine) as preparar:
            filas = [EventoSaliente(nombre="prueba.concurrente", datos={"n": n}) for n in "ab"]
            preparar.add_all(filas)
            preparar.commit()
            ids = [f.id for f in filas]

        with Session(engine) as otro_worker:
            # El otro worker se ha llevado el evento "a" y aun no ha confirmado.
            otro_worker.scalars(
                select(EventoSaliente).where(EventoSaliente.id == ids[0]).with_for_update()
            ).one()

            @contextmanager
            def sesion_real():
                with Session(engine) as s:
                    yield s
                    s.commit()

            monkeypatch.setattr(tarea, "sesion_worker", sesion_real)
            assert tarea.drenar() == {"despachados": 1, "fallidos": 0}
            assert vistos == ["b"]
            otro_worker.rollback()

        with Session(engine) as comprobar:
            estado = {
                f.datos["n"]: f.procesado_en is not None
                for f in comprobar.scalars(select(EventoSaliente).where(EventoSaliente.id.in_(ids)))
            }
        assert estado == {"a": False, "b": True}
    finally:
        with Session(engine) as limpiar:
            limpiar.query(EventoSaliente).filter(
                EventoSaliente.nombre == "prueba.concurrente"
            ).delete()
            limpiar.commit()
        engine.dispose()
