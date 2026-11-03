"""Tareas de Celery: el contrato con el planificador y lo que cada envoltorio anade al servicio.

La logica vive en los servicios y se prueba alli. Aqui se prueba lo que solo existe en la
tarea: que el `beat_schedule` nombre tareas que existen, que cada una abra su sesion y
devuelva lo que espera quien la mira en Flower, y sus ramas propias (reintentos, fallo de
la planificacion, IA no disponible).
"""

from contextlib import contextmanager
from uuid import uuid4

import pytest
from celery.exceptions import Retry

from app.workers import celery_app as modulo_celery
from app.workers.celery_app import celery_app
from app.workers.tasks import (
    campanas,
    cartera,
    comunicaciones,
    dashboard,
    encuestas,
    familias,
    ia,
    outbox,
    preventivos,
    rutas,
)

MODULOS = (
    campanas,
    cartera,
    comunicaciones,
    dashboard,
    encuestas,
    familias,
    ia,
    outbox,
    preventivos,
    rutas,
)


@pytest.fixture
def en_worker(db, monkeypatch):
    """Ejecuta una tarea como lo haria el worker, pero con la sesion de la prueba: cada
    `with sesion_worker()` de la tarea recibe esa sesion, que se revierte al terminar."""

    async def ejecutar(tarea, *args):
        def dentro(sesion):
            @contextmanager
            def sesion_de_la_prueba():
                yield sesion

            for modulo in MODULOS:
                monkeypatch.setattr(modulo, "sesion_worker", sesion_de_la_prueba)
            return tarea(*args)

        return await db.run_sync(dentro)

    return ejecutar


@pytest.mark.unit
def test_el_planificador_solo_programa_tareas_que_existen():
    """El schedule referencia las tareas por cadena: una errata no falla al arrancar, el
    proceso diario simplemente no corre nunca."""
    celery_app.loader.import_default_modules()
    programadas = {
        entrada["task"] for entrada in modulo_celery.celery_app.conf.beat_schedule.values()
    }
    assert programadas, "el beat_schedule no puede estar vacio"
    assert programadas - set(celery_app.tasks) == set()


@pytest.mark.parametrize(
    ("tarea", "esperado"),
    [
        (cartera.generar_cuotas, {"emitidas": 0}),
        (cartera.detectar_renovaciones, {"tareas_creadas": 0}),
        (campanas.lanzar_programadas, {"lanzadas": 0}),
        (comunicaciones.reencolar_pendientes, {"reencolados": 0}),
        (outbox.drenar, {"despachados": 0, "fallidos": 0}),
    ],
    ids=lambda v: getattr(v, "name", None) or "",
)
async def test_las_tareas_periodicas_corren_sobre_una_base_sin_pendientes(
    en_worker, tarea, esperado
):
    assert await en_worker(tarea) == esperado


@pytest.mark.parametrize(
    "tarea",
    [
        cartera.revisar_mora,
        cartera.cobrar_recurrentes,
        cartera.conciliar_pendientes,
        campanas.despachar,
        dashboard.enviar_reportes,
        encuestas.enviar_pendientes,
        preventivos.generar_agenda,
    ],
    ids=lambda t: t.name,
)
async def test_las_tareas_periodicas_devuelven_un_resumen(en_worker, tarea):
    """Lo que devuelven es lo que se ve en Flower y en los logs: un resumen serializable."""
    import json

    resumen = await en_worker(tarea)
    assert isinstance(resumen, dict)
    json.dumps(resumen, default=str)


async def test_un_envio_temporalmente_fallido_se_reintenta_con_espera(en_worker, monkeypatch):
    recibidos = []

    def procesar_envio(db, mensaje_id):
        recibidos.append(mensaje_id)
        return "reintentar"

    monkeypatch.setattr(comunicaciones.service, "procesar_envio", procesar_envio)
    mensaje_id = uuid4()
    with pytest.raises(Retry):
        await en_worker(comunicaciones.enviar_mensaje, str(mensaje_id))
    assert recibidos == [mensaje_id], "la tarea recibe texto y el servicio un UUID"

    monkeypatch.setattr(comunicaciones.service, "procesar_envio", lambda db, mid: "enviado")
    assert await en_worker(comunicaciones.enviar_mensaje, str(mensaje_id)) == "enviado"


async def test_el_barrido_reencola_los_mensajes_perdidos(en_worker, monkeypatch):
    perdidos = [uuid4(), uuid4()]
    enviados = []
    monkeypatch.setattr(
        comunicaciones.service, "pendientes_por_reencolar", lambda db, antiguedad: perdidos
    )
    monkeypatch.setattr(
        celery_app, "send_task", lambda nombre, args: enviados.append((nombre, args))
    )
    assert await en_worker(comunicaciones.reencolar_pendientes) == {"reencolados": 2}
    assert enviados == [(comunicaciones.service.TAREA_ENVIO, [str(m)]) for m in perdidos]


async def test_una_planificacion_que_revienta_queda_marcada_como_fallida(en_worker, monkeypatch):
    fallos = []

    def planificar(db, planificacion_id):
        raise RuntimeError("OR-Tools sin solucion")

    monkeypatch.setattr(rutas.service, "planificar", planificar)
    monkeypatch.setattr(
        rutas.service, "fallo_planificacion", lambda db, pid, error: fallos.append((pid, error))
    )
    planificacion_id = uuid4()
    with pytest.raises(RuntimeError):
        await en_worker(rutas.planificar, str(planificacion_id))
    assert fallos == [
        (planificacion_id, "OR-Tools sin solucion")
    ], "si no, el panel la muestra pendiente para siempre"


async def test_sin_ia_disponible_el_borrador_se_omite_sin_fallar(en_worker, monkeypatch):
    def borrador(db, solicitud_id):
        raise ia.service.IANoDisponible("presupuesto agotado")

    monkeypatch.setattr(ia.service, "borrador_veterinario", borrador)
    assert await en_worker(ia.borrador_veterinario, str(uuid4())) == {"disponible": False}


@pytest.mark.parametrize(
    ("tarea", "modulo", "funcion", "devuelve", "esperado"),
    [
        (
            encuestas.programar_encuesta,
            encuestas.service,
            "programar",
            ["a", "b"],
            {"programadas": 2},
        ),
        (familias.geocodificar, familias.service, "geocodificar", "aproximada", "aproximada"),
        (
            cartera.procesar_evento_pasarela,
            cartera.pasarela,
            "procesar_evento",
            "procesado",
            "procesado",
        ),
        (
            ia.borrador_veterinario,
            ia.service,
            "borrador_veterinario",
            {"disponible": True},
            {"disponible": True},
        ),
    ],
    ids=lambda v: getattr(v, "name", None) or "",
)
async def test_las_tareas_con_argumento_lo_pasan_como_uuid(
    en_worker, monkeypatch, tarea, modulo, funcion, devuelve, esperado
):
    recibidos = []

    def doble(db, identificador, *args, **kwargs):
        recibidos.append(identificador)
        return devuelve

    monkeypatch.setattr(modulo, funcion, doble)
    identificador = uuid4()
    assert await en_worker(tarea, str(identificador)) == esperado
    assert recibidos == [identificador]


async def test_la_evaluacion_de_un_prompt_busca_la_version_y_la_evalua(en_worker, monkeypatch):
    version = object()
    evaluadas = []
    monkeypatch.setattr(ia.service, "obtener_prompt", lambda db, prompt_id: version)
    monkeypatch.setattr(
        ia.service,
        "evaluar",
        lambda db, prompt: evaluadas.append(prompt) or {"total": 4, "aprobados": 4},
    )
    assert await en_worker(ia.evaluar_prompt, str(uuid4())) == {"total": 4, "aprobados": 4}
    assert evaluadas == [version]


async def test_un_webhook_de_whatsapp_sin_mensajes_no_hace_nada(en_worker):
    resumen = await en_worker(comunicaciones.procesar_evento_whatsapp, {"entry": []})
    assert isinstance(resumen, dict) and not any(resumen.values())
