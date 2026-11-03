"""F3-COM-01..04 Embudo comercial, conversacion automatizada, recomendacion de plan y
paso a asesor."""

from datetime import timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.enums import Rol
from app.core.tiempo import hoy
from app.modules.comercial import conversacion
from app.modules.comercial.models import ConversacionComercial, Interesado
from app.modules.comunicaciones import service as comunicaciones
from app.modules.comunicaciones.models import Mensaje
from app.modules.tareas.models import Tarea
from tests import fabricas
from tests.conftest import crear_usuario

NUMERO = "573150001122"
TEL = "+573150001122"


def _mensaje(texto: str, n: int, numero: str = NUMERO) -> dict:
    return {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": numero,
                                    "id": f"wamid.{numero}.{n}",
                                    "type": "text",
                                    "text": {"body": texto},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }


class Chat:
    """Simula a una persona escribiendo por WhatsApp y lee lo que el bot responde."""

    def __init__(self, db, numero: str = NUMERO) -> None:
        self.db, self.numero, self.n = db, numero, 0

    async def escribir(self, texto: str) -> str:
        """Lo que el bot respondio a este mensaje (por id: en la prueba todo comparte la
        misma transaccion y por tanto la misma hora de creacion)."""
        self.n += 1
        antes = set(await self._salientes())
        await self.db.run_sync(
            comunicaciones.procesar_evento_whatsapp, _mensaje(texto, self.n, self.numero)
        )
        nuevos = [
            m
            for m in await self.db.scalars(
                select(Mensaje).where(
                    Mensaje.destino == "+" + self.numero, Mensaje.direccion == "saliente"
                )
            )
            if m.id not in antes
        ]
        return "\n".join(m.contenido or "" for m in nuevos)

    async def _salientes(self) -> list:
        return list(
            await self.db.scalars(
                select(Mensaje.id).where(
                    Mensaje.destino == "+" + self.numero, Mensaje.direccion == "saliente"
                )
            )
        )


@pytest.fixture
async def comerciales(db):
    return [
        await crear_usuario(db, "vende1@timu.co", Rol.COMERCIAL),
        await crear_usuario(db, "vende2@timu.co", Rol.COMERCIAL),
    ]


@pytest.fixture
async def planes(db):
    await db.run_sync(fabricas.plan, "individual", 45_000, 1)
    await db.run_sync(fabricas.plan, "familiar", 75_000, 3)


# --- F3-COM-02 / 03 Conversacion y recomendacion ----------------------------------------------


@pytest.mark.unit
def test_lectura_de_mascotas():
    assert conversacion.leer_mascotas("2 perros y un gato") == ["canino", "canino", "felino"]
    assert conversacion.leer_mascotas("tengo una gatita") == ["felino"]
    assert conversacion.leer_mascotas("Tres PERRITOS") == ["canino"] * 3
    assert conversacion.leer_mascotas("ninguna") == []


@pytest.mark.unit
def test_el_arbol_por_defecto_es_valido():
    conversacion.validar_arbol(conversacion.ARBOL_POR_DEFECTO)


async def test_de_hola_a_la_recomendacion_y_la_afiliacion(db, comerciales, planes):
    chat = Chat(db)
    bienvenida = await chat.escribir("Hola")
    assert "1. Conocer el plan ideal" in bienvenida
    interesado = await db.scalar(select(Interesado).where(Interesado.telefono == TEL))
    assert (interesado.origen, interesado.etapa) == ("whatsapp", "contactado")
    assert interesado.responsable_id is not None

    assert "ciudad" in await chat.escribir("1")
    assert "mascotas" in await chat.escribir("cali")
    recomendacion = await chat.escribir("2 perros y un gato")
    assert "Plan familiar" in recomendacion and "$75.000" in recomendacion
    await db.refresh(interesado)
    assert (interesado.etapa, interesado.plan_sugerido) == ("cotizado", "familiar")
    assert interesado.ciudad == "Cali"

    enlace = await chat.escribir("1")
    assert "/afiliacion?plan=familiar" in enlace


async def test_respuestas_no_entendidas_pasan_a_un_asesor(db, comerciales, planes):
    chat = Chat(db)
    await chat.escribir("Hola")
    assert "No te entendi" in await chat.escribir("quiero saber precios")
    await chat.escribir("???")
    final = await chat.escribir("eh")
    assert "asesor" in final
    conv = await db.scalar(select(ConversacionComercial))
    assert conv.estado == "con_asesor"
    tarea = await db.get(Tarea, conv.tarea_id)
    assert tarea.area == "comercial" and "no logro entender" in tarea.descripcion
    assert tarea.asignada_a_id == conv.asesor_id


async def test_pedir_asesor_con_contexto_y_el_bot_se_calla(
    client: AsyncClient, db, comerciales, planes, headers
):
    chat = Chat(db)
    await chat.escribir("Hola")
    await chat.escribir("1")
    await chat.escribir("Cali")
    await chat.escribir("quiero hablar con un asesor")
    conv = await db.scalar(select(ConversacionComercial))
    tarea = await db.get(Tarea, conv.tarea_id)
    assert "ciudad: Cali" in tarea.descripcion
    # Mientras atiende una persona, el bot no responde.
    assert await chat.escribir("hola?") == ""

    conv_id = conv.id
    await db.commit()
    liberada = await client.post(
        f"/api/v1/comercial/conversaciones/{conv_id}/liberacion", headers=headers
    )
    assert liberada.json()["estado"] == "automatica"
    assert "Conocer el plan" in await chat.escribir("menu")


async def test_ciudad_sin_cobertura_va_a_un_asesor(db, comerciales, planes):
    chat = Chat(db)
    await chat.escribir("Hola")
    await chat.escribir("1")
    respuesta = await chat.escribir("Leticia")
    assert "no atendemos en Leticia" in respuesta
    conv = await db.scalar(select(ConversacionComercial))
    assert conv.estado == "con_asesor"


async def test_arbol_editable_y_validado(client: AsyncClient, db, comerciales, planes, headers):
    roto = {"inicio": {"mensaje": "Hola", "opciones": {"1": "no_existe"}}}
    assert (
        await client.put("/api/v1/comercial/arbol", json={"nodos": roto}, headers=headers)
    ).status_code == 422
    nuevo = {
        "inicio": {"mensaje": "Bienvenido a TIMU v2\n1. Asesor", "opciones": {"1": "asesor"}},
        "asesor": {"accion": "asesor"},
    }
    resp = await client.put("/api/v1/comercial/arbol", json={"nodos": nuevo}, headers=headers)
    assert resp.json() == {"version": 1}
    assert "TIMU v2" in await Chat(db).escribir("hola")


# --- F3-COM-01 Embudo -------------------------------------------------------------------------


async def test_reparto_por_carga(db, comerciales, planes):
    for numero in ("573150000001", "573150000002", "573150000003", "573150000004"):
        await Chat(db, numero).escribir("hola")
    responsables = list(await db.scalars(select(Interesado.responsable_id)))
    assert responsables.count(comerciales[0].id) == 2
    assert responsables.count(comerciales[1].id) == 2


async def test_formulario_y_afiliacion_mueven_el_embudo(
    client: AsyncClient, db, comerciales, headers
):
    from tests.test_afiliaciones import FORMULARIO, _pagar

    await db.run_sync(fabricas.plan, "individual", 45_000, 1)
    await db.run_sync(fabricas.plantillas_aprobadas)
    await db.commit()
    datos = (await client.post("/api/v1/afiliaciones", json=FORMULARIO)).json()
    interesado = await db.scalar(select(Interesado))
    assert interesado.etapa == "en_afiliacion"
    await _pagar(db, datos["solicitud_id"])
    await db.refresh(interesado)
    assert interesado.etapa == "afiliado" and interesado.familia_id is not None

    embudo = (
        await client.get(
            "/api/v1/comercial/embudo",
            params={"desde": str(hoy() - timedelta(days=1)), "hasta": str(hoy())},
            headers=headers,
        )
    ).json()
    assert embudo["por_etapa"]["afiliado"] == 1 and embudo["conversion"] == 1.0


async def test_perder_y_reactivar(client: AsyncClient, db, comerciales, headers):
    creado = await client.post(
        "/api/v1/comercial/interesados",
        json={"nombre": "Luz", "telefono": "3159998877", "origen": "referido"},
        headers=headers,
    )
    assert creado.status_code == 201, creado.text
    iid = creado.json()["id"]
    perdido = await client.post(
        f"/api/v1/comercial/interesados/{iid}/perdida",
        json={"motivo": "Precio"},
        headers=headers,
    )
    assert perdido.json()["etapa"] == "perdido"
    reactivado = await client.post(
        f"/api/v1/comercial/interesados/{iid}/reactivacion", headers=headers
    )
    assert reactivado.json()["etapa"] == "contactado"


# --- Endpoints del embudo y de la bandeja de conversaciones -----------------------------------


async def _interesado(client, headers, nombre: str, telefono: str, origen: str) -> dict:
    resp = await client.post(
        "/api/v1/comercial/interesados",
        json={"nombre": nombre, "telefono": telefono, "origen": origen},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_listado_de_interesados_combina_filtros(
    client: AsyncClient, db, comerciales, headers
):
    luz = await _interesado(client, headers, "Luz Marina", "3159998877", "referido")
    pedro = await _interesado(client, headers, "Pedro Paez", "3201112233", "formulario")
    await _interesado(client, headers, "Sara", "3004445566", "referido")
    tercero = await crear_usuario(db, "vende3@timu.co", Rol.COMERCIAL)
    await client.patch(
        f"/api/v1/comercial/interesados/{pedro['id']}",
        json={"responsable_id": str(tercero.id)},
        headers=headers,
    )

    # En la prueba todo comparte transaccion y por tanto created_at: se comparan conjuntos.
    async def nombres(**filtros) -> set[str]:
        resp = await client.get("/api/v1/comercial/interesados", params=filtros, headers=headers)
        return {i["nombre"] for i in resp.json()["items"]}

    assert await nombres() == {"Sara", "Pedro Paez", "Luz Marina"}
    assert await nombres(origen="referido") == {"Luz Marina", "Sara"}
    assert await nombres(q="marina") == {"Luz Marina"}
    assert await nombres(q="999887") == {"Luz Marina"}, "tambien busca por celular"
    assert await nombres(responsable_id=str(tercero.id)) == {"Pedro Paez"}
    assert len(await nombres(etapa=luz["etapa"])) == 3
    assert await nombres(etapa="perdido") == set()


async def test_actualizar_un_interesado_solo_avanza_el_embudo(
    client: AsyncClient, comerciales, headers
):
    from uuid import uuid4

    luz = await _interesado(client, headers, "Luz", "3159998877", "referido")
    url = f"/api/v1/comercial/interesados/{luz['id']}"
    cotizado = (
        await client.patch(
            url,
            json={"etapa": "cotizado", "ciudad": "Cali", "nombre": "Luz Marina"},
            headers=headers,
        )
    ).json()
    assert (cotizado["etapa"], cotizado["ciudad"], cotizado["nombre"]) == (
        "cotizado",
        "Cali",
        "Luz Marina",
    )
    atras = (await client.patch(url, json={"etapa": "contactado"}, headers=headers)).json()
    assert atras["etapa"] == "cotizado", "el embudo no retrocede"
    assert (await client.patch(url, json={"etapa": "afiliado"}, headers=headers)).status_code == 422
    assert (
        await client.patch(f"/api/v1/comercial/interesados/{uuid4()}", json={}, headers=headers)
    ).status_code == 404


async def test_el_asesor_responde_desde_la_bandeja(
    client: AsyncClient, db, comerciales, planes, headers, admin
):
    from uuid import uuid4

    chat = Chat(db)
    await chat.escribir("Hola")
    await chat.escribir("quiero hablar con un asesor")
    conv = await db.scalar(select(ConversacionComercial))
    conv_id, asignado = conv.id, conv.asesor_id
    await db.commit()

    con_asesor = (await client.get("/api/v1/comercial/conversaciones", headers=headers)).json()
    assert [c["id"] for c in con_asesor] == [str(conv_id)]
    automaticas = (
        await client.get(
            "/api/v1/comercial/conversaciones", params={"estado": "automatica"}, headers=headers
        )
    ).json()
    assert automaticas == []

    url = f"/api/v1/comercial/conversaciones/{conv_id}/mensajes"
    assert (await client.post(url, json={"texto": ""}, headers=headers)).status_code == 422
    enviado = await client.post(url, json={"texto": "Hola, soy tu asesora"}, headers=headers)
    assert enviado.status_code == 201
    from uuid import UUID

    mensaje = await db.get(Mensaje, UUID(enviado.json()["mensaje_id"]))
    assert (mensaje.destino, mensaje.contenido) == (TEL, "Hola, soy tu asesora")
    await db.refresh(conv)
    assert conv.asesor_id == (asignado or admin.id), "quien responde queda como asesor si no habia"

    assert (
        await client.post(
            f"/api/v1/comercial/conversaciones/{uuid4()}/mensajes",
            json={"texto": "x"},
            headers=headers,
        )
    ).status_code == 404
    assert (
        await client.post(f"/api/v1/comercial/conversaciones/{uuid4()}/liberacion", headers=headers)
    ).status_code == 404


async def test_publicar_un_arbol_nuevo_retira_el_anterior(client: AsyncClient, db, headers):
    from app.modules.comercial.models import ArbolConversacion

    actual = (await client.get("/api/v1/comercial/arbol", headers=headers)).json()
    nodos = conversacion.ARBOL_POR_DEFECTO
    primera = (
        await client.put(
            "/api/v1/comercial/arbol", json={"nodos": nodos, "nota": "v1"}, headers=headers
        )
    ).json()
    segunda = (
        await client.put(
            "/api/v1/comercial/arbol", json={"nodos": nodos, "nota": "v2"}, headers=headers
        )
    ).json()
    assert segunda["version"] == primera["version"] + 1
    activos = list(
        await db.scalars(select(ArbolConversacion).where(ArbolConversacion.activo.is_(True)))
    )
    assert [a.version for a in activos] == [segunda["version"]]
    assert actual, "sin version publicada se sirve el arbol por defecto"
