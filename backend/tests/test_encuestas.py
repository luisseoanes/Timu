"""F3-ENC-01..04 Encuesta al cierre, respuesta por enlace o WhatsApp, seguimiento y alerta
por calificacion baja."""

from datetime import timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.enums import EstadoServicio, Rol, TipoServicio
from app.core.tiempo import ahora, hoy
from app.modules.comunicaciones import service as comunicaciones
from app.modules.comunicaciones.models import Mensaje, PlantillaWhatsApp
from app.modules.encuestas import service
from app.modules.encuestas.models import ConfiguracionEncuesta, Encuesta
from app.modules.servicios import service as servicios
from app.modules.servicios.models import Servicio
from app.modules.tareas.models import Tarea
from tests import fabricas
from tests.conftest import crear_usuario

pytestmark = pytest.mark.integration


def _plantillas(db) -> None:
    for nombre in ("encuesta_satisfaccion", "seguimiento_post"):
        db.add(
            PlantillaWhatsApp(
                nombre=nombre,
                cuerpo="Hola {{1}}, como te fue con {{2}}? Califica aqui: {{3}}",
                variables=["titular", "mascota", "enlace"],
                estado_aprobacion="aprobada",
                activa=True,
            )
        )


async def _atendido(db, tipo="control_post", telefono="+573001112233") -> Servicio:
    """Servicio en atencion, atendido por una medica, listo para completarse."""
    familia, _ = await fabricas.afiliada(db, hoy(), telefono=telefono)
    medica = await crear_usuario(db, f"vet{telefono[-4:]}@timu.co", Rol.MEDICO)
    servicio = Servicio(
        familia_id=familia.id,
        mascota_id=familia.mascotas[0].id,
        tipo_codigo=tipo,
        tipo=TipoServicio.CLINICO,
        ciudad="Cali",
        programado_para=ahora() - timedelta(hours=1),
        profesional_id=medica.id,
        estado=EstadoServicio.EN_ATENCION,
    )
    db.add(servicio)
    await db.flush()
    return servicio


async def _completado_con_encuesta(db) -> Encuesta:
    servicio = await _atendido(db)
    await db.run_sync(servicios.cambiar_estado, servicio, EstadoServicio.COMPLETADO)
    (encuesta,) = await db.run_sync(service.programar, servicio.id)
    return encuesta


async def _enviada(db) -> Encuesta:
    _plantillas(db)
    encuesta = await _completado_con_encuesta(db)
    await db.run_sync(service.enviar_pendientes, ahora() + timedelta(hours=3))
    assert encuesta.estado == "enviada"
    return encuesta


# --- F3-ENC-01 / 03 Programacion y envio --------------------------------------------------------


async def test_completar_el_servicio_programa_la_encuesta(db, tareas):
    servicio = await _atendido(db)
    await db.run_sync(servicios.cambiar_estado, servicio, EstadoServicio.COMPLETADO)
    assert await tareas.de("encuestas.enviar_encuesta") == [(str(servicio.id),)]

    (encuesta,) = await db.run_sync(service.programar, servicio.id)
    assert encuesta.tipo == "satisfaccion" and encuesta.estado == "pendiente"
    assert encuesta.responsable_id == servicio.profesional_id
    demora = encuesta.programada_para - ahora()
    assert timedelta(hours=1, minutes=55) < demora <= timedelta(hours=2)
    # Repetible: no duplica.
    assert await db.run_sync(service.programar, servicio.id) == []


async def test_seguimiento_segun_el_tipo_de_atencion(db):
    db.add(
        ConfiguracionEncuesta(
            tipo_servicio_codigo="control_post", demora_horas=1, seguimiento_dias=3
        )
    )
    servicio = await _atendido(db)
    await db.run_sync(servicios.cambiar_estado, servicio, EstadoServicio.COMPLETADO)
    encuestas = await db.run_sync(service.programar, servicio.id)
    tipos = {e.tipo: e.programada_para - ahora() for e in encuestas}
    assert set(tipos) == {"satisfaccion", "seguimiento"}
    assert tipos["seguimiento"] > timedelta(days=2, hours=23)


async def test_envio_solo_cuando_llega_la_hora(db):
    _plantillas(db)
    encuesta = await _completado_con_encuesta(db)
    assert (await db.run_sync(service.enviar_pendientes, ahora()))["enviadas"] == 0
    resumen = await db.run_sync(service.enviar_pendientes, ahora() + timedelta(hours=3))
    assert resumen["enviadas"] == 1 and encuesta.estado == "enviada"
    mensaje = await db.scalar(select(Mensaje).where(Mensaje.plantilla == "encuesta_satisfaccion"))
    assert encuesta.token in mensaje.contenido


async def test_sin_plantilla_queda_pendiente(db):
    encuesta = await _completado_con_encuesta(db)
    resumen = await db.run_sync(service.enviar_pendientes, ahora() + timedelta(hours=3))
    assert resumen["fallidas"] == 1 and encuesta.estado == "pendiente"


# --- F3-ENC-02 / 04 Respuesta y alerta ----------------------------------------------------------


async def test_respuesta_por_enlace(client: AsyncClient, db):
    encuesta = await _enviada(db)
    token = encuesta.token
    await db.commit()
    contexto = await client.get(f"/api/v1/encuestas/respuesta/{token}")
    assert contexto.status_code == 200 and contexto.json()["atencion"] == "Control post atencion"
    assert "telefono" not in contexto.text

    ok = await client.post(f"/api/v1/encuestas/respuesta/{token}", json={"puntaje": 5})
    assert ok.status_code == 200
    otra = await client.post(f"/api/v1/encuestas/respuesta/{token}", json={"puntaje": 1})
    assert otra.status_code == 422
    assert (await client.get("/api/v1/encuestas/respuesta/no-existe")).status_code == 404
    assert await db.scalar(select(Tarea).where(Tarea.origen == "encuesta")) is None


async def test_encuesta_aun_no_enviada_no_se_responde(client: AsyncClient, db):
    encuesta = await _completado_con_encuesta(db)
    token = encuesta.token
    await db.commit()
    assert (await client.get(f"/api/v1/encuestas/respuesta/{token}")).status_code == 404


async def test_calificacion_baja_crea_tarea_con_contexto(client: AsyncClient, db):
    encuesta = await _enviada(db)
    token = encuesta.token
    await db.commit()
    await client.post(
        f"/api/v1/encuestas/respuesta/{token}",
        json={"puntaje": 2, "comentario": "Llegaron tarde"},
    )
    tarea = await db.scalar(select(Tarea).where(Tarea.origen == "encuesta"))
    assert (tarea.area, tarea.prioridad) == ("servicio_cliente", "alta")
    assert "Llegaron tarde" in tarea.descripcion and "vet2233" in tarea.descripcion
    assert tarea.vence_el == hoy()


async def test_respuesta_por_whatsapp(db):
    encuesta = await _enviada(db)
    evento = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "573001112233",
                                    "id": "wamid.encuesta",
                                    "type": "text",
                                    "text": {"body": " 1 "},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    await db.run_sync(comunicaciones.procesar_evento_whatsapp, evento)
    assert (encuesta.estado, encuesta.puntaje, encuesta.canal_respuesta) == (
        "respondida",
        1,
        "whatsapp",
    )
    assert encuesta.tarea_id is not None


async def test_texto_que_no_es_calificacion_se_ignora(db):
    encuesta = await _enviada(db)
    respuesta = await db.run_sync(service.respuesta_whatsapp, "+573001112233", "hola, gracias")
    assert respuesta is None and encuesta.estado == "enviada"


async def test_resumen_por_responsable(client: AsyncClient, db, headers):
    primera = await _enviada(db)
    await db.run_sync(service.responder, primera, 5, None, "enlace")
    datos = await db.run_sync(service.resumen, hoy() - timedelta(days=1), hoy() + timedelta(days=1))
    assert datos["respondidas"] == 1 and datos["promedio"] == 5.0
    assert datos["por_responsable"][0]["responsable"] == "vet2233"
    resp = await client.get(
        "/api/v1/encuestas/resumen",
        params={"desde": str(hoy() - timedelta(days=1)), "hasta": str(hoy() + timedelta(days=1))},
        headers=headers,
    )
    assert resp.status_code == 200
