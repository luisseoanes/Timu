"""F1-WHA-01..04 Mensajeria por WhatsApp."""

import hashlib
import hmac
import json
from datetime import timedelta
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.config import settings
from app.core.tiempo import ahora
from app.integrations.whatsapp import ErrorWhatsApp
from app.modules.comunicaciones import service
from app.modules.comunicaciones.models import ConversacionWhatsApp, Mensaje

TEL = "+573001112233"


class WhatsAppFalso:
    def __init__(self, fallos: list[ErrorWhatsApp] | None = None) -> None:
        self.fallos = list(fallos or [])
        self.enviados: list[tuple] = []

    def enviar_plantilla(self, telefono, plantilla, parametros=None, idioma="es"):
        if self.fallos:
            raise self.fallos.pop(0)
        self.enviados.append(("plantilla", telefono, plantilla, parametros))
        return f"wamid.{len(self.enviados)}"

    def enviar_texto(self, telefono, texto):
        self.enviados.append(("texto", telefono, texto))
        return f"wamid.{len(self.enviados)}"


async def _plantilla_aprobada(client: AsyncClient, headers, nombre="recordatorio_pago") -> dict:
    creada = await client.post(
        "/api/v1/comunicaciones/plantillas",
        json={
            "nombre": nombre,
            "cuerpo": "Hola {{1}}, tu cuota de {{2}} vence pronto.",
            "variables": ["nombre", "valor"],
        },
        headers=headers,
    )
    assert creada.status_code == 201, creada.text
    aprobada = await client.patch(
        f"/api/v1/comunicaciones/plantillas/{creada.json()['id']}/estado",
        json={"estado_aprobacion": "aprobada", "activa": True},
        headers=headers,
    )
    return aprobada.json()


async def _enviar(client, headers, **extra):
    return await client.post(
        "/api/v1/comunicaciones/mensajes/plantilla",
        json={
            "telefono": "300 111 2233",
            "plantilla": "recordatorio_pago",
            "variables": ["Ana", "$45.000"],
            **extra,
        },
        headers=headers,
    )


# --- F1-WHA-03 Plantillas ---------------------------------------------------------------------


async def test_version_nueva_vuelve_a_borrador(client: AsyncClient, headers):
    v1 = await _plantilla_aprobada(client, headers)
    v2 = await client.post(
        "/api/v1/comunicaciones/plantillas",
        json={
            "nombre": "recordatorio_pago",
            "cuerpo": "Hola {{1}}, recuerda tu pago de {{2}}.",
            "variables": ["nombre", "valor"],
        },
        headers=headers,
    )
    assert v2.json()["version"] == 2
    assert v2.json()["estado_aprobacion"] == "borrador"
    # Mientras la v2 no se apruebe, se sigue enviando la v1.
    resp = await _enviar(client, headers)
    assert resp.json()["contenido"] == "Hola Ana, tu cuota de $45.000 vence pronto."
    assert v1["activa"] is True


async def test_activar_una_version_desactiva_las_demas(client: AsyncClient, db, headers):
    await _plantilla_aprobada(client, headers)
    v2 = await _plantilla_aprobada(client, headers)
    assert v2["version"] == 2
    todas = (await client.get("/api/v1/comunicaciones/plantillas", headers=headers)).json()
    assert [(p["version"], p["activa"]) for p in todas] == [(2, True), (1, False)]


async def test_no_se_activa_sin_aprobacion(client: AsyncClient, headers):
    creada = await client.post(
        "/api/v1/comunicaciones/plantillas",
        json={"nombre": "x", "cuerpo": "Hola", "variables": []},
        headers=headers,
    )
    resp = await client.patch(
        f"/api/v1/comunicaciones/plantillas/{creada.json()['id']}/estado",
        json={"estado_aprobacion": "enviada", "activa": True},
        headers=headers,
    )
    assert resp.status_code == 422


async def test_variables_deben_coincidir_con_el_cuerpo(client: AsyncClient, headers):
    resp = await client.post(
        "/api/v1/comunicaciones/plantillas",
        json={"nombre": "x", "cuerpo": "Hola {{1}} {{3}}", "variables": ["a", "b"]},
        headers=headers,
    )
    assert resp.status_code == 422


async def test_envio_con_plantilla_no_aprobada(client: AsyncClient, headers):
    resp = await _enviar(client, headers)
    assert resp.status_code == 422
    assert "no esta aprobada" in resp.json()["detail"]


async def test_envio_con_variables_incompletas(client: AsyncClient, headers):
    await _plantilla_aprobada(client, headers)
    resp = await _enviar(client, headers, variables=["Ana"])
    assert resp.status_code == 422


# --- F1-WHA-01 Cola y reintentos --------------------------------------------------------------


async def test_envio_se_encola_despues_del_commit(client: AsyncClient, headers, tareas):
    await _plantilla_aprobada(client, headers)
    resp = await _enviar(client, headers)
    assert resp.status_code == 202
    assert resp.json()["estado"] == "encolado"
    assert resp.json()["destino"] == TEL
    assert await tareas.de(service.TAREA_ENVIO) == [(resp.json()["id"],)]


async def test_procesar_envio_exitoso(client: AsyncClient, db, headers):
    await _plantilla_aprobada(client, headers)
    mensaje_id = UUID((await _enviar(client, headers)).json()["id"])
    wa = WhatsAppFalso()
    assert await db.run_sync(service.procesar_envio, mensaje_id, wa) == "enviado"
    assert wa.enviados == [("plantilla", "573001112233", "recordatorio_pago", ["Ana", "$45.000"])]
    mensaje = await db.get(Mensaje, mensaje_id)
    assert mensaje.id_externo == "wamid.1"
    assert mensaje.intentos == 1
    # Una segunda ejecucion (tarea duplicada) no reenvia.
    assert await db.run_sync(service.procesar_envio, mensaje_id, wa) == "enviado"
    assert len(wa.enviados) == 1


async def test_fallo_temporal_reintenta_y_luego_falla(client: AsyncClient, db, headers):
    await _plantilla_aprobada(client, headers)
    mensaje_id = UUID((await _enviar(client, headers)).json()["id"])
    wa = WhatsAppFalso([ErrorWhatsApp("503", temporal=True)] * service.MAX_INTENTOS)
    for _ in range(service.MAX_INTENTOS - 1):
        assert await db.run_sync(service.procesar_envio, mensaje_id, wa) == "reintentar"
    assert await db.run_sync(service.procesar_envio, mensaje_id, wa) == "fallido"
    mensaje = await db.get(Mensaje, mensaje_id)
    assert (mensaje.intentos, mensaje.error) == (service.MAX_INTENTOS, "503")


async def test_fallo_permanente_no_reintenta(client: AsyncClient, db, headers):
    await _plantilla_aprobada(client, headers)
    mensaje_id = UUID((await _enviar(client, headers)).json()["id"])
    wa = WhatsAppFalso([ErrorWhatsApp("numero invalido", temporal=False)])
    assert await db.run_sync(service.procesar_envio, mensaje_id, wa) == "fallido"


async def test_traza_por_familia(client: AsyncClient, db, headers):
    await _plantilla_aprobada(client, headers)
    familia = await client.post(
        "/api/v1/familias",
        json={"titular_nombre": "Ana", "documento": "123456", "telefono": TEL, "ciudad": "Cali"},
        headers=headers,
    )
    await _enviar(client, headers, familia_id=familia.json()["id"])
    traza = await client.get(
        "/api/v1/comunicaciones/mensajes",
        params={"familia_id": familia.json()["id"]},
        headers=headers,
    )
    assert traza.json()["total"] == 1


# --- F1-WHA-02 Webhook: estados y entrantes ---------------------------------------------------


def _evento(**valor) -> dict:
    return {"entry": [{"changes": [{"value": valor}]}]}


async def test_estados_de_entrega_avanzan_sin_retroceder(client: AsyncClient, db, headers):
    await _plantilla_aprobada(client, headers)
    mensaje_id = UUID((await _enviar(client, headers)).json()["id"])
    await db.run_sync(service.procesar_envio, mensaje_id, WhatsAppFalso())

    await db.run_sync(
        service.procesar_evento_whatsapp,
        _evento(statuses=[{"id": "wamid.1", "status": "read", "timestamp": "1790000000"}]),
    )
    # El "delivered" llega tarde: no debe devolver el mensaje a entregado.
    await db.run_sync(
        service.procesar_evento_whatsapp,
        _evento(statuses=[{"id": "wamid.1", "status": "delivered", "timestamp": "1789999990"}]),
    )
    mensaje = await db.get(Mensaje, mensaje_id)
    assert mensaje.estado == "leido"
    assert mensaje.leido_en is not None and mensaje.entregado_en is not None


async def test_fallo_reportado_por_meta(client: AsyncClient, db, headers):
    await _plantilla_aprobada(client, headers)
    mensaje_id = UUID((await _enviar(client, headers)).json()["id"])
    await db.run_sync(service.procesar_envio, mensaje_id, WhatsAppFalso())
    await db.run_sync(
        service.procesar_evento_whatsapp,
        _evento(
            statuses=[
                {
                    "id": "wamid.1",
                    "status": "failed",
                    "errors": [{"title": "Re-engagement message"}],
                }
            ]
        ),
    )
    mensaje = await db.get(Mensaje, mensaje_id)
    assert (mensaje.estado, mensaje.error) == ("fallido", "Re-engagement message")


async def test_entrante_se_asocia_a_la_familia_una_sola_vez(client: AsyncClient, db, headers):
    familia = await client.post(
        "/api/v1/familias",
        json={"titular_nombre": "Ana", "documento": "123456", "telefono": TEL, "ciudad": "Cali"},
        headers=headers,
    )
    evento = _evento(
        messages=[
            {
                "from": "573001112233",
                "id": "wamid.in1",
                "type": "text",
                "text": {"body": "Hola, quiero agendar"},
            }
        ]
    )
    await db.run_sync(service.procesar_evento_whatsapp, evento)
    await db.run_sync(service.procesar_evento_whatsapp, evento)  # Meta reintenta
    entrantes = list(await db.scalars(select(Mensaje).where(Mensaje.direccion == "entrante")))
    assert len(entrantes) == 1
    assert str(entrantes[0].familia_id) == familia.json()["id"]


def _firmar(cuerpo: bytes, secreto: str) -> str:
    return "sha256=" + hmac.new(secreto.encode(), cuerpo, hashlib.sha256).hexdigest()


async def test_webhook_valida_firma_de_meta(client: AsyncClient, monkeypatch, tareas):
    monkeypatch.setattr(settings, "WHATSAPP_APP_SECRET", "secreto-app")
    cuerpo = json.dumps(_evento(statuses=[])).encode()
    malo = await client.post(
        "/api/v1/webhooks/whatsapp", content=cuerpo, headers={"x-hub-signature-256": "sha256=0"}
    )
    assert malo.status_code == 401
    bueno = await client.post(
        "/api/v1/webhooks/whatsapp",
        content=cuerpo,
        headers={"x-hub-signature-256": _firmar(cuerpo, "secreto-app")},
    )
    assert bueno.status_code == 202
    assert await tareas.de("comunicaciones.procesar_evento_whatsapp") == [(_evento(statuses=[]),)]


# --- F1-WHA-04 Ventana de 24 horas y bajas ----------------------------------------------------


async def test_texto_libre_solo_dentro_de_la_ventana(client: AsyncClient, db, headers):
    datos = {"telefono": TEL, "texto": "Ya vamos en camino"}
    fuera = await client.post("/api/v1/comunicaciones/mensajes/texto", json=datos, headers=headers)
    assert fuera.status_code == 422
    assert "24 horas" in fuera.json()["detail"]

    await db.run_sync(
        service.procesar_evento_whatsapp,
        _evento(messages=[{"from": "573001112233", "id": "w1", "text": {"body": "hola"}}]),
    )
    await db.commit()
    dentro = await client.post("/api/v1/comunicaciones/mensajes/texto", json=datos, headers=headers)
    assert dentro.status_code == 202


async def test_ventana_vencida(db):
    db.add(ConversacionWhatsApp(telefono=TEL, ultimo_entrante_en=ahora() - timedelta(hours=25)))
    await db.flush()
    assert not await db.run_sync(service.ventana_abierta, TEL)


@pytest.mark.parametrize("texto", ["BAJA", "stop", " No mas "])
async def test_pedir_baja_excluye_de_envios_masivos(
    client: AsyncClient, db, headers, tareas, texto
):
    await _plantilla_aprobada(client, headers)
    await db.run_sync(
        service.procesar_evento_whatsapp,
        _evento(messages=[{"from": "573001112233", "id": "w1", "text": {"body": texto}}]),
    )
    masivo = await db.run_sync(
        service.encolar_plantilla,
        telefono=TEL,
        plantilla="recordatorio_pago",
        variables=["Ana", "$1"],
        masivo=True,
    )
    assert masivo.estado == "omitido"
    # Los mensajes transaccionales (recordatorio de su propio pago) si le llegan.
    individual = await db.run_sync(
        service.encolar_plantilla,
        telefono=TEL,
        plantilla="recordatorio_pago",
        variables=["Ana", "$1"],
    )
    assert individual.estado == "encolado"
    await db.commit()
    assert await tareas.de(service.TAREA_ENVIO) == [(str(individual.id),)]


async def test_solo_admin_reactiva_envios(client: AsyncClient, db, headers):
    from app.core.enums import Rol
    from tests.conftest import crear_usuario, login

    await client.post("/api/v1/comunicaciones/bajas", json={"telefono": TEL}, headers=headers)
    await crear_usuario(db, "com@timu.co", Rol.COMERCIAL)
    comercial = await login(client, "com@timu.co")
    url = f"/api/v1/comunicaciones/bajas/{TEL}"
    assert (await client.delete(url, headers=comercial)).status_code == 403
    assert (await client.delete(url, headers=headers)).status_code == 204


async def test_numero_extranjero_no_tumba_el_webhook(db):
    """Revision F1: un remitente no colombiano hacia fallar el lote entero, incluidos los
    estados de entrega que venian en el mismo webhook."""
    evento = _evento(
        messages=[
            {"from": "14155550100", "id": "wamid.ext", "type": "text", "text": {"body": "Hi"}},
            {"from": "573001112233", "id": "wamid.co", "type": "text", "text": {"body": "Hola"}},
        ]
    )
    assert (await db.run_sync(service.procesar_evento_whatsapp, evento))["entrantes"] == 2
    destinos = set(await db.scalars(select(Mensaje.destino).where(Mensaje.direccion == "entrante")))
    assert destinos == {"+14155550100", "+573001112233"}
