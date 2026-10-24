"""F3-SEG-01 segmentos; F3-CAM-01..04 campanas con previsualizacion, envio controlado,
resultados y programacion recurrente."""

from datetime import timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from app.core.enums import Rol
from app.core.tiempo import ahora, hoy
from app.modules.campanas import segmentos, service
from app.modules.campanas.models import Campana, DestinatarioCampana, EjecucionCampana
from app.modules.cartera import service as cartera
from app.modules.comunicaciones.models import BajaComunicaciones, Mensaje, PlantillaWhatsApp
from app.modules.familias import service as familias
from tests import fabricas
from tests.conftest import crear_usuario, login

pytestmark = pytest.mark.integration

PLANTILLA = "promo_vacunas"


@pytest.fixture
async def base(db):
    """Cali con perro, Bogota con gato, Cali en mora y una baja (que nunca cuenta)."""
    db.add(
        PlantillaWhatsApp(
            nombre=PLANTILLA,
            cuerpo="Hola {{1}}, {{2}} tiene descuento en vacunas",
            variables=["titular", "mascota"],
            estado_aprobacion="aprobada",
            activa=True,
        )
    )
    cali, _ = await fabricas.afiliada(db, hoy(), telefono="+573001000001")
    bogota, _ = await fabricas.afiliada(db, hoy(), ciudad="Bogota", telefono="+573001000002")
    bogota.mascotas[0].especie = "felino"
    morosa, contrato = await fabricas.afiliada(
        db, hoy() - timedelta(days=40), telefono="+573001000003"
    )
    await db.run_sync(cartera.generar_cuotas, hoy())
    await db.run_sync(cartera.revisar_cartera, hoy())
    retirada, _ = await fabricas.afiliada(db, hoy(), telefono="+573001000004")
    await db.run_sync(familias.dar_de_baja, retirada, "se mudo")
    cali.titular_nombre, morosa.titular_nombre = "Ana Cali", "Mora Cali"
    await db.flush()
    return {"cali": cali, "bogota": bogota, "morosa": morosa}


# --- F3-SEG-01 Segmentos ----------------------------------------------------------------------


async def test_filtros_combinables(db, base):
    def contar(**filtros):
        return db.run_sync(segmentos.contar, segmentos.FiltrosSegmento(**filtros))

    assert await contar() == 3  # la baja nunca entra
    assert await contar(ciudades=["Cali"]) == 2
    assert await contar(especies=["felino"]) == 1
    assert await contar(dias_mora_min=5) == 1
    assert await contar(ciudades=["Cali"], dias_mora_min=5) == 1
    assert await contar(ciudades=["Bogota"], dias_mora_min=5) == 0
    assert await contar(sin_servicio_dias=30) == 3


async def test_segmento_guardado_muestra_su_alcance(client: AsyncClient, db, base, headers):
    await db.commit()
    creado = await client.post(
        "/api/v1/segmentos",
        json={"nombre": "Cali al dia", "filtros": {"ciudades": ["Cali"], "estados": ["activa"]}},
        headers=headers,
    )
    assert creado.status_code == 201, creado.text
    conteo = await client.get(f"/api/v1/segmentos/{creado.json()['id']}/conteo", headers=headers)
    assert conteo.json()["total"] == 1
    assert conteo.json()["muestra"][0]["titular"] == "Ana Cali"


# --- F3-CAM-01 Creacion y previsualizacion ----------------------------------------------------


async def _campana(client, headers, **extra) -> dict:
    datos = {
        "nombre": "Vacunas de octubre",
        "plantilla": PLANTILLA,
        "variables": ["titular_nombre", "mascota_nombre"],
        "segmento": {"ciudades": ["Cali"]},
        **extra,
    }
    return await client.post("/api/v1/campanas", json=datos, headers=headers)


async def test_campana_se_valida_contra_la_plantilla(client, db, base, headers):
    await db.commit()
    assert (await _campana(client, headers, plantilla="no_aprobada")).status_code == 422
    assert (await _campana(client, headers, variables=["titular_nombre"])).status_code == 422
    assert (
        await _campana(client, headers, variables=["titular_nombre", "cumpleanos"])
    ).status_code == 422
    assert (await _campana(client, headers)).status_code == 201


async def test_previsualizacion_con_exclusiones(client, db, base, headers):
    db.add(BajaComunicaciones(destino="+573001000003", canal="whatsapp"))
    await db.commit()
    campana = (await _campana(client, headers)).json()
    vista = (
        await client.get(f"/api/v1/campanas/{campana['id']}/previsualizacion", headers=headers)
    ).json()
    assert (vista["audiencia"], vista["excluidos_por_baja"], vista["se_enviaran"]) == (2, 1, 1)
    assert vista["ejemplos"][0]["mensaje"].startswith("Hola Ana Cali, Mascota0")


async def test_solo_comercial_o_admin_crean_campanas(client, db, base):
    await crear_usuario(db, "op@timu.co", Rol.OPERACIONES)
    resp = await _campana(client, await login(client, "op@timu.co"))
    assert resp.status_code == 403


# --- F3-CAM-02 Envio controlado ---------------------------------------------------------------


async def _lanzada(db, base, **campana) -> Campana:
    c = await db.run_sync(
        service.guardar,
        None,
        {
            "nombre": "Prueba",
            "plantilla": PLANTILLA,
            "variables": ["titular_nombre", "mascota_nombre"],
            "segmento": {},
            **campana,
        },
        None,
    )
    await db.run_sync(service.programar, c, None, campana.get("recurrencia", "ninguna"))
    assert await db.run_sync(service.lanzar_programadas, ahora() + timedelta(seconds=1)) == 1
    return c


async def test_envio_al_ritmo_permitido_y_respetando_bajas(db, base):
    db.add(BajaComunicaciones(destino="+573001000002", canal="whatsapp"))
    campana = await _lanzada(db, base)
    ejecucion = await db.scalar(select(EjecucionCampana))
    assert (ejecucion.audiencia, ejecucion.excluidos) == (3, 1)

    primera = await db.run_sync(service.despachar, 1)
    assert primera["encolados"] == 1 and campana.estado == "en_envio"
    segunda = await db.run_sync(service.despachar, 10)
    assert segunda == {"encolados": 1, "excluidos": 0, "terminadas": 1}
    assert campana.estado == "finalizada"

    mensajes = list(await db.scalars(select(Mensaje).where(Mensaje.campana_id == campana.id)))
    assert len(mensajes) == 2 and all(m.masivo for m in mensajes)
    excluido = await db.scalar(
        select(DestinatarioCampana).where(DestinatarioCampana.estado == "excluido")
    )
    assert (excluido.telefono, excluido.motivo_exclusion) == ("+573001000002", "baja_voluntaria")


async def test_baja_posterior_a_congelar_la_audiencia_tambien_se_respeta(db, base):
    campana = await _lanzada(db, base)
    db.add(BajaComunicaciones(destino="+573001000001", canal="whatsapp"))
    await db.flush()
    await db.run_sync(service.despachar, 10)
    traza = await db.scalar(
        select(DestinatarioCampana).where(DestinatarioCampana.telefono == "+573001000001")
    )
    assert traza.estado == "excluido"
    assert (
        await db.scalar(
            select(func.count())
            .select_from(Mensaje)
            .where(Mensaje.campana_id == campana.id, Mensaje.estado == "encolado")
        )
        == 2
    )


async def test_cancelar_detiene_lo_pendiente(db, base):
    campana = await _lanzada(db, base)
    await db.run_sync(service.despachar, 1)
    await db.run_sync(service.cancelar, campana)
    await db.run_sync(service.despachar, 10)
    assert (
        await db.scalar(
            select(func.count()).select_from(Mensaje).where(Mensaje.campana_id == campana.id)
        )
        == 1
    )


# --- F3-CAM-03 Resultados ---------------------------------------------------------------------


async def test_resultados_y_exportacion(client, db, base, headers):
    campana = await _lanzada(db, base)
    await db.run_sync(service.despachar, 10)
    mensajes = list(
        await db.scalars(
            select(Mensaje).where(Mensaje.campana_id == campana.id).order_by(Mensaje.destino)
        )
    )
    mensajes[0].estado, mensajes[0].entregado_en, mensajes[0].leido_en = "leido", ahora(), ahora()
    mensajes[1].estado = "entregado"
    mensajes[2].estado = "fallido"
    db.add(
        Mensaje(
            canal="whatsapp",
            direccion="entrante",
            destino=mensajes[0].destino,
            contenido="Quiero agendar",
            estado="recibido",
            # En produccion llega en su propia transaccion, despues del envio.
            created_at=ahora() + timedelta(minutes=5),
        )
    )
    campana_id = campana.id
    await db.commit()

    r = (await client.get(f"/api/v1/campanas/{campana_id}/resultados", headers=headers)).json()
    assert r["audiencia"] == 3 and r["encolados"] == 3
    assert (r["entregados"], r["leidos"], r["respondidos"], r["fallidos"]) == (2, 1, 1, 1)

    csv = await client.get(
        f"/api/v1/campanas/{campana_id}/resultados", params={"formato": "csv"}, headers=headers
    )
    assert csv.headers["content-type"].startswith("text/csv")
    assert csv.text.count("\n") == 4 and "respondio" in csv.text.splitlines()[0]


# --- F3-CAM-04 Programadas y recurrentes ------------------------------------------------------


async def test_campana_programada_a_futuro(db, base):
    c = await db.run_sync(
        service.guardar,
        None,
        {"nombre": "Futuro", "plantilla": PLANTILLA, "variables": ["titular_nombre", "ciudad"]},
        None,
    )
    await db.run_sync(service.programar, c, ahora() + timedelta(days=2), "ninguna")
    assert await db.run_sync(service.lanzar_programadas, ahora()) == 0
    assert (
        await db.run_sync(service.lanzar_programadas, ahora() + timedelta(days=2, minutes=1)) == 1
    )


async def test_campana_recurrente_se_repite_sola(db, base):
    campana = await _lanzada(db, base, recurrencia="semanal")
    await db.run_sync(service.despachar, 10)
    assert campana.estado == "programada"
    assert campana.proxima_ejecucion > ahora() + timedelta(days=6)
    otra = await db.run_sync(service.lanzar_programadas, ahora() + timedelta(days=7, minutes=1))
    assert otra == 1
    assert await db.scalar(select(func.count()).select_from(EjecucionCampana)) == 2
