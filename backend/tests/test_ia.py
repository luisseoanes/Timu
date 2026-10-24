"""F4-IAA-01..04 Capa de IA con control: prompts versionados, limite de gasto, registro,
uso comercial con paso a asesor, borrador veterinario y evaluacion antes de activar.

Ninguna prueba llama a la API real: el proveedor se sustituye por uno falso.
"""

import json
from decimal import Decimal
from types import SimpleNamespace

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from app.core.config import settings
from app.core.enums import Rol
from app.core.tiempo import hoy
from app.integrations import claude
from app.modules.clinica import service as clinica
from app.modules.comercial.models import ConversacionComercial
from app.modules.comunicaciones.models import Mensaje
from app.modules.ia import service
from app.modules.ia.models import ConsultaIA, PromptIA
from tests import fabricas
from tests.conftest import crear_usuario, login
from tests.test_comercial import Chat

pytestmark = pytest.mark.integration


class ProveedorFalso:
    """Responde lo que la prueba programe y guarda lo que se le pidio."""

    def __init__(self) -> None:
        self.respuestas: list = []
        self.llamadas: list[dict] = []

    def __call__(self, sistema, entrada, *, esquema=None, max_tokens=2000, effort="low"):
        self.llamadas.append({"sistema": sistema, "entrada": entrada, "esquema": esquema})
        r = self.respuestas.pop(0) if self.respuestas else {"alcance": "fuera", "respuesta": ""}
        if isinstance(r, Exception):
            raise r
        rechazada = r == "RECHAZO"
        texto = "" if rechazada else (r if isinstance(r, str) else json.dumps(r))
        return claude.Respuesta(
            texto=texto,
            modelo="claude-opus-5-5",
            uso=claude.Uso(entrada=1000, salida=500),
            rechazada=rechazada,
            request_id="req_prueba",
        )


@pytest.fixture
def proveedor(monkeypatch) -> ProveedorFalso:
    falso = ProveedorFalso()
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "clave-de-prueba")
    monkeypatch.setattr(claude, "completar", falso)
    return falso


async def _activo(db, codigo: str) -> PromptIA:
    """Version activa sin pasar por la API: evaluacion marcada como aprobada."""
    prompt = await db.run_sync(service.crear_version, codigo, "Prompt de prueba " * 10, None)
    prompt.evaluacion = {"total": 1, "aprobados": 1}
    await db.run_sync(service.activar, prompt, None)
    return prompt


# --- F4-IAA-01 Punto unico, costo, presupuesto y registro -------------------------------------


@pytest.mark.unit
def test_costo_por_tokens():
    uso = claude.Uso(entrada=1000, salida=500, cache_lectura=10_000, cache_escritura=2000)
    # 1000*4 + 500*20 + 10000*0.4 + 2000*5 = 28000 por millon
    assert claude.costo("claude-opus-5-5", uso) == Decimal("0.028")
    # Un modelo sin precio conocido se cobra al mas caro: nunca se subestima el gasto.
    assert claude.costo("modelo-nuevo", claude.Uso(entrada=1_000_000)) == Decimal("10")


@pytest.mark.unit
def test_la_consulta_cachea_el_sistema_y_pide_json(monkeypatch):
    pedidos = []

    class Mensajes:
        def create(self, **kwargs):
            pedidos.append(kwargs)
            return SimpleNamespace(
                content=[SimpleNamespace(type="text", text='{"alcance": "dentro"}')],
                model="claude-opus-5-5",
                stop_reason="end_turn",
                usage=SimpleNamespace(
                    input_tokens=10,
                    output_tokens=5,
                    cache_read_input_tokens=100,
                    cache_creation_input_tokens=0,
                ),
            )

    cliente = SimpleNamespace(beta=SimpleNamespace(messages=Mensajes()))
    monkeypatch.setattr(claude, "_cliente", lambda: cliente)
    r = claude.completar("Guion fijo", "pregunta", esquema={"type": "object"})
    (pedido,) = pedidos
    assert pedido["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert pedido["output_config"]["format"]["type"] == "json_schema"
    assert pedido["fallbacks"] == "default"
    assert (r.texto, r.uso.cache_lectura, r.rechazada) == ('{"alcance": "dentro"}', 100, False)


async def test_sin_clave_no_consulta_pero_registra(db):
    await _activo(db, "comercial_guion")
    with pytest.raises(service.IANoDisponible):
        await db.run_sync(service.consultar, "comercial_guion", "hola")
    estado = await db.scalar(select(ConsultaIA.estado))
    assert estado == "desactivada"


async def test_limite_de_gasto_mensual(db, proveedor, monkeypatch):
    await _activo(db, "comercial_guion")
    monkeypatch.setattr(settings, "IA_PRESUPUESTO_MENSUAL_USD", 0.02)  # cada consulta: 0,014
    proveedor.respuestas = [{"alcance": "dentro", "respuesta": "ok"}] * 3
    await db.run_sync(service.consultar, "comercial_guion", "uno")
    await db.run_sync(service.consultar, "comercial_guion", "dos")
    with pytest.raises(service.IANoDisponible, match="presupuesto"):
        await db.run_sync(service.consultar, "comercial_guion", "tres")
    estados = list(await db.scalars(select(ConsultaIA.estado).order_by(ConsultaIA.created_at)))
    assert sorted(estados) == ["ok", "ok", "presupuesto_agotado"]
    assert len(proveedor.llamadas) == 2
    consumo = await db.run_sync(service.consumo)
    assert consumo["gasto_usd"] == pytest.approx(0.028)


async def test_rechazo_y_json_invalido_no_se_usan(db, proveedor):
    await _activo(db, "comercial_guion")
    proveedor.respuestas = ["RECHAZO", "esto no es json"]
    for _ in range(2):
        with pytest.raises(service.IANoDisponible):
            await db.run_sync(service.consultar, "comercial_guion", "x")
    assert set(await db.scalars(select(ConsultaIA.estado))) == {"rechazo", "error"}


# --- F4-IAA-04 Versiones y evaluacion ---------------------------------------------------------


async def test_no_se_activa_sin_pasar_la_evaluacion(client: AsyncClient, db, proveedor, headers):
    await db.run_sync(service.sembrar)
    await db.commit()
    v1 = await db.scalar(select(PromptIA).where(PromptIA.codigo == "comercial_guion"))
    assert (v1.version, v1.estado) == (1, "borrador")
    assert (
        await client.post(f"/api/v1/ia/prompts/{v1.id}/activacion", headers=headers)
    ).status_code == 422

    # Casos sembrados: dentro, fuera, fuera, fuera. Responde bien solo tres de cuatro.
    proveedor.respuestas = [
        {"alcance": "dentro", "respuesta": "Si, vamos a tu casa."},
        {"alcance": "fuera", "respuesta": ""},
        {"alcance": "dentro", "respuesta": "Claro, 50%"},  # error: inventa un descuento
        {"alcance": "fuera", "respuesta": ""},
    ]
    resultado = await db.run_sync(service.evaluar, v1)
    assert (resultado["total"], resultado["aprobados"]) == (4, 3)
    await db.commit()
    rechazo = await client.post(f"/api/v1/ia/prompts/{v1.id}/activacion", headers=headers)
    assert rechazo.status_code == 422 and "fallo 1 de 4" in rechazo.json()["detail"]


async def test_version_aprobada_reemplaza_a_la_anterior(
    client: AsyncClient, db, proveedor, headers
):
    anterior = await _activo(db, "comercial_guion")
    await db.run_sync(service.sembrar)  # agrega los casos de prueba
    nueva = await db.run_sync(service.crear_version, "comercial_guion", "Version dos " * 10, "v2")
    proveedor.respuestas = [
        {"alcance": "dentro", "respuesta": "Si, vamos a tu casa."},
        {"alcance": "fuera", "respuesta": ""},
        {"alcance": "fuera", "respuesta": ""},
        {"alcance": "fuera", "respuesta": ""},
    ]
    await db.run_sync(service.evaluar, nueva)
    # La evaluacion uso el texto de ESTA version, no el de la activa.
    assert all(llamada["sistema"].startswith("Version dos") for llamada in proveedor.llamadas)
    await db.commit()
    resp = await client.post(f"/api/v1/ia/prompts/{nueva.id}/activacion", headers=headers)
    assert resp.status_code == 200 and resp.json()["estado"] == "activo"
    await db.refresh(anterior)
    assert anterior.estado == "retirado"


async def test_evaluar_se_encola_al_worker(client: AsyncClient, db, headers, tareas):
    await db.run_sync(service.sembrar)
    prompt = await db.scalar(select(PromptIA))
    prompt_id = str(prompt.id)
    await db.commit()
    resp = await client.post(f"/api/v1/ia/prompts/{prompt_id}/evaluacion", headers=headers)
    assert resp.status_code == 202
    assert await tareas.de("ia.evaluar_prompt") == [(prompt_id,)]


# --- F4-IAA-02 Comercial ----------------------------------------------------------------------


@pytest.fixture
async def comerciales(db):
    await crear_usuario(db, "vende@timu.co", Rol.COMERCIAL)


async def test_pregunta_abierta_dentro_del_guion(db, proveedor, comerciales):
    await _activo(db, "comercial_guion")
    chat = Chat(db)
    await chat.escribir("Hola")
    proveedor.respuestas = [{"alcance": "dentro", "respuesta": "Si, vamos a tu casa con todo."}]
    respuesta = await chat.escribir("Ustedes vienen a la casa a vacunar?")
    assert "vamos a tu casa" in respuesta and "*menu*" in respuesta
    conv = await db.scalar(select(ConversacionComercial))
    assert (conv.estado, conv.fallos) == ("automatica", 0)
    # El modelo recibio los planes vigentes como contexto, no inventados.
    assert "Planes vigentes" in proveedor.llamadas[0]["entrada"]


async def test_pregunta_fuera_del_guion_pasa_a_asesor(db, proveedor, comerciales):
    await _activo(db, "comercial_guion")
    chat = Chat(db)
    await chat.escribir("Hola")
    proveedor.respuestas = [{"alcance": "fuera", "respuesta": ""}]
    await chat.escribir("Mi perro vomita sangre, que le doy?")
    conv = await db.scalar(select(ConversacionComercial))
    assert conv.estado == "con_asesor"


async def test_sin_ia_el_bot_sigue_como_antes(db, comerciales):
    chat = Chat(db)
    await chat.escribir("Hola")
    assert "No te entendi" in await chat.escribir("Ustedes vienen a la casa a vacunar?")


# --- F4-IAA-03 Borrador veterinario -----------------------------------------------------------


async def test_borrador_para_el_profesional_nunca_se_envia(
    client: AsyncClient, db, proveedor, tareas
):
    await _activo(db, "veterinario_borrador")
    familia, _ = await fabricas.afiliada(db, hoy())
    medica = await crear_usuario(db, "vet@timu.co", Rol.MEDICO)
    solicitud = await db.run_sync(
        lambda s: clinica.solicitar_virtual(
            s, familia.mascotas[0].id, "Tiene diarrea desde ayer", canal="portal"
        )
    )
    await db.run_sync(clinica.tomar, solicitud, medica.id)
    solicitud_id = str(solicitud.id)
    await db.commit()

    resp = await client.post(
        f"/api/v1/clinica/virtual/{solicitud_id}/borrador",
        headers=await login(client, "vet@timu.co"),
    )
    assert resp.status_code == 202
    assert await tareas.de("ia.borrador_veterinario") == [(solicitud_id,)]

    proveedor.respuestas = [
        {
            "borrador": "Observa si sigue comiendo y ofrece agua.",
            "senales_alarma": ["sangre en heces", "decaimiento"],
            "recomendar_presencial": False,
        }
    ]
    await db.run_sync(service.borrador_veterinario, solicitud.id)
    await db.refresh(solicitud)
    assert solicitud.borrador_ia["senales_alarma"] == ["sangre en heces", "decaimiento"]
    assert solicitud.estado == "en_atencion"  # sigue esperando la respuesta del profesional
    enviados = await db.scalar(
        select(func.count()).select_from(Mensaje).where(Mensaje.familia_id == familia.id)
    )
    assert enviados == 0
