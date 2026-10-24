"""F2-PRE-01..06 Esquemas, proximas fechas, autorizacion, agenda y carnet verificable."""

from datetime import date, time, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.enums import Rol
from app.core.tiempo import hoy
from app.modules.comunicaciones.models import Mensaje, PlantillaWhatsApp
from app.modules.preventivos import service
from app.modules.preventivos.models import EventoPreventivo
from app.modules.servicios.models import Franja
from tests import fabricas
from tests.conftest import crear_usuario, login

pytestmark = pytest.mark.integration

HOY = hoy()


async def _cachorro(db, semanas: int = 10):
    """Familia afiliada con un cachorro de `semanas` y su calendario programado."""
    familia, contrato = await fabricas.afiliada(db, HOY)
    mascota = familia.mascotas[0]
    mascota.fecha_nacimiento = HOY - timedelta(weeks=semanas)
    await db.flush()
    await db.run_sync(service.calendario_inicial, mascota, HOY)
    return familia, mascota


async def _eventos(db, mascota, esquema: str) -> list[EventoPreventivo]:
    return list(
        await db.scalars(
            select(EventoPreventivo)
            .where(
                EventoPreventivo.mascota_id == mascota.id,
                EventoPreventivo.esquema_codigo == esquema,
            )
            .order_by(EventoPreventivo.dosis_numero)
        )
    )


async def _autorizado(db, evento, usuario_id) -> None:
    await db.run_sync(service.autorizar, evento, usuario_id, "whatsapp", True)


# --- F2-PRE-01 Calendario segun esquema --------------------------------------------------------


async def test_cachorro_recibe_la_serie_y_el_adulto_un_refuerzo(db):
    _, cachorro = await _cachorro(db, semanas=10)
    serie = await _eventos(db, cachorro, "can_polivalente")
    assert [e.dosis_numero for e in serie] == [1, 2, 3]
    assert [e.fecha_programada for e in serie] == [HOY + timedelta(days=21 * i) for i in range(3)]
    assert not any(e.es_refuerzo for e in serie)

    familia_adulto, _ = await fabricas.afiliada(db, HOY, telefono="+573002223344")
    adulto = familia_adulto.mascotas[0]
    await db.run_sync(service.calendario_inicial, adulto, HOY)
    (refuerzo,) = await _eventos(db, adulto, "can_polivalente")
    assert refuerzo.es_refuerzo and refuerzo.fecha_programada == HOY


async def test_esquema_nuevo_desde_el_catalogo_sin_desplegar(client: AsyncClient, db, headers):
    _, mascota = await _cachorro(db)
    await db.commit()
    nuevo = {
        "codigo": "can_leptospira",
        "especie_codigo": "canino",
        "tipo": "vacuna",
        "nombre": "Leptospirosis canina",
        "edad_minima_semanas": 8,
        "dosis_iniciales": 2,
        "intervalo_inicial_dias": 28,
        "intervalo_refuerzo_dias": 365,
    }
    creado = await client.post(
        "/api/v1/catalogos/esquemas-preventivos", json=nuevo, headers=headers
    )
    assert creado.status_code == 201, creado.text
    resp = await client.post(
        f"/api/v1/preventivos/mascotas/{mascota.id}/calendario", headers=headers
    )
    assert [e["esquema_codigo"] for e in resp.json()] == ["can_leptospira", "can_leptospira"]


async def test_serie_sin_intervalo_se_rechaza(client: AsyncClient, headers):
    malo = {
        "codigo": "can_x",
        "especie_codigo": "canino",
        "tipo": "vacuna",
        "nombre": "Serie rota",
        "dosis_iniciales": 3,
    }
    resp = await client.post("/api/v1/catalogos/esquemas-preventivos", json=malo, headers=headers)
    assert resp.status_code == 422


# --- F2-PRE-02 / 03 Autorizacion y aplicacion ------------------------------------------------


async def test_sin_autorizacion_no_se_aplica(db, admin):
    _, mascota = await _cachorro(db)
    primera = (await _eventos(db, mascota, "can_polivalente"))[0]
    from app.core.errores import ReglaNegocio

    with pytest.raises(ReglaNegocio, match="autorizacion"):
        await db.run_sync(
            lambda s: service.aplicar(
                s, primera, fecha=HOY, producto="Vanguard", lote="L1", usuario_id=admin.id
            )
        )


async def test_aplicar_reprograma_la_serie_desde_la_fecha_real(db, admin):
    _, mascota = await _cachorro(db)
    primera, segunda, tercera = await _eventos(db, mascota, "can_polivalente")
    await _autorizado(db, primera, admin.id)
    # Se aplico 5 dias despues de lo programado: la segunda dosis corre 21 dias desde ahi.
    aplicada = HOY - timedelta(days=0)
    await db.run_sync(
        lambda s: service.aplicar(
            s, primera, fecha=aplicada, producto="Vanguard", lote="L1", usuario_id=admin.id
        )
    )
    assert primera.estado == "aplicado"
    assert primera.proxima_fecha == aplicada + timedelta(days=21)
    assert segunda.fecha_programada == aplicada + timedelta(days=21)

    for evento in (segunda, tercera):
        await _autorizado(db, evento, admin.id)
        await db.run_sync(
            lambda s, e=evento: service.aplicar(
                s, e, fecha=HOY, producto="Vanguard", lote="L2", usuario_id=admin.id
            )
        )
    # Cerrada la serie, el refuerzo anual queda programado.
    refuerzo = (await _eventos(db, mascota, "can_polivalente"))[-1]
    assert (refuerzo.dosis_numero, refuerzo.es_refuerzo) == (4, True)
    assert refuerzo.fecha_programada == HOY + timedelta(days=365)


async def test_rechazo_de_la_familia_cancela(db, admin):
    _, mascota = await _cachorro(db)
    evento = (await _eventos(db, mascota, "can_rabia"))[0]
    await db.run_sync(service.autorizar, evento, admin.id, "telefono", False)
    assert evento.estado == "cancelado"


async def test_solo_personal_medico_aplica(client: AsyncClient, db, headers):
    _, mascota = await _cachorro(db)
    evento = (await _eventos(db, mascota, "can_rabia"))[0]
    evento_id = evento.id
    await crear_usuario(db, "op@timu.co", Rol.OPERACIONES)
    operaciones = await login(client, "op@timu.co")
    datos = {"fecha": str(HOY), "producto": "Rabisin"}
    resp = await client.post(
        f"/api/v1/preventivos/{evento_id}/aplicacion", json=datos, headers=operaciones
    )
    assert resp.status_code == 403


async def test_flujo_http_autorizar_y_aplicar(client: AsyncClient, db, headers):
    _, mascota = await _cachorro(db)
    evento_id = (await _eventos(db, mascota, "can_rabia"))[0].id
    await db.commit()
    url = f"/api/v1/preventivos/{evento_id}"
    autorizado = await client.post(
        f"{url}/autorizacion", json={"medio": "whatsapp"}, headers=headers
    )
    assert autorizado.json()["autorizado"] is True
    aplicado = await client.post(
        f"{url}/aplicacion",
        json={"fecha": str(HOY), "producto": "Rabisin", "lote": "R-77"},
        headers=headers,
    )
    assert aplicado.status_code == 200, aplicado.text
    assert aplicado.json()["proxima_fecha"] == str(HOY + timedelta(days=365))


# --- F2-PRE-04 Agenda --------------------------------------------------------------------------


async def test_agenda_diaria_avisa_una_sola_vez(db):
    db.add(
        PlantillaWhatsApp(
            nombre=service.PLANTILLA_RECORDATORIO,
            cuerpo="Hola {{1}}, a {{2}} le toca {{3}} el {{4}}",
            variables=["titular", "mascota", "preventivo", "fecha"],
            estado_aprobacion="aprobada",
            activa=True,
        )
    )
    familia, mascota = await _cachorro(db)
    resumen = await db.run_sync(service.agenda_diaria, HOY)
    # Los que caen dentro de la anticipacion (hoy): polivalente, rabia no (12 semanas),
    # desparasitaciones si.
    assert resumen["avisados"] >= 1
    otra_vez = await db.run_sync(service.agenda_diaria, HOY)
    assert otra_vez["avisados"] == 0
    mensajes = list(await db.scalars(select(Mensaje).where(Mensaje.familia_id == familia.id)))
    assert len(mensajes) == resumen["avisados"]
    assert mascota.nombre in mensajes[0].contenido


async def test_agenda_sin_plantilla_no_marca_como_avisado(db):
    _, mascota = await _cachorro(db)
    resumen = await db.run_sync(service.agenda_diaria, HOY)
    assert resumen["avisados"] == 0 and resumen["sin_aviso"] >= 1
    pendientes = await _eventos(db, mascota, "can_polivalente")
    assert pendientes[0].notificado_en is None


async def test_agendar_crea_el_servicio(client: AsyncClient, db, headers):
    dia = HOY + timedelta(days=7)
    db.add(
        Franja(
            ciudad="Cali",
            modalidad="preventivo",
            dia_semana=dia.weekday(),
            hora_inicio=time(8),
            hora_fin=time(12),
            capacidad=2,
        )
    )
    _, mascota = await _cachorro(db)
    evento_id = (await _eventos(db, mascota, "can_rabia"))[0].id
    await db.commit()
    resp = await client.post(
        f"/api/v1/preventivos/{evento_id}/agendar",
        json={"inicio": f"{dia}T09:00:00"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["servicio_id"]
    otra = await client.post(
        f"/api/v1/preventivos/{evento_id}/agendar",
        json={"inicio": f"{dia}T10:00:00"},
        headers=headers,
    )
    assert otra.status_code == 422


# --- F2-PRE-05 / 06 Carnet -----------------------------------------------------------------------


async def test_carnet_separa_aplicado_vencido_y_proximo(db, admin):
    _, mascota = await _cachorro(db)
    rabia = (await _eventos(db, mascota, "can_rabia"))[0]
    await _autorizado(db, rabia, admin.id)
    await db.run_sync(
        lambda s: service.aplicar(
            s, rabia, fecha=HOY, producto="Rabisin", lote="R1", usuario_id=admin.id
        )
    )
    externa = (await _eventos(db, mascota, "can_desp_externa"))[0]
    externa.fecha_programada = HOY - timedelta(days=3)
    await db.flush()

    datos = await db.run_sync(service.carnet, mascota.id, HOY)
    assert [a["nombre"] for a in datos["aplicados"]] == ["Antirrabica canina"]
    assert any(v["id"] == str(externa.id) for v in datos["vencidos"])
    assert all(p["fecha_programada"] >= str(HOY) for p in datos["proximos"])
    # Nada programado aparece como aplicado.
    assert all(a["fecha_aplicacion"] for a in datos["aplicados"])


async def test_carnet_pdf_verificable_sin_datos_de_la_familia(
    client: AsyncClient, db, headers, admin, almacenamiento
):
    familia, mascota = await _cachorro(db)
    rabia = (await _eventos(db, mascota, "can_rabia"))[0]
    await _autorizado(db, rabia, admin.id)
    await db.run_sync(
        lambda s: service.aplicar(
            s, rabia, fecha=HOY, producto="Rabisin", lote="R1", usuario_id=admin.id
        )
    )
    mascota_id, titular, documento = mascota.id, familia.titular_nombre, familia.documento
    await db.commit()

    emitido = await client.post(
        f"/api/v1/preventivos/mascotas/{mascota_id}/carnet/pdf", headers=headers
    )
    assert emitido.status_code == 201, emitido.text
    codigo = emitido.json()["codigo"]
    (pdf,) = [c for c, _ in almacenamiento.objetos.values()]
    assert pdf.startswith(b"%PDF-")

    client.cookies.clear()
    publico = await client.get(f"/api/v1/verificacion/carnets/{codigo.lower()}")
    assert publico.status_code == 200
    cuerpo = publico.text
    assert publico.json()["aplicados"][0]["lote"] == "R1"
    assert titular not in cuerpo and documento not in cuerpo
    assert (await client.get("/api/v1/verificacion/carnets/NOEXISTE00")).status_code == 404


async def test_carnet_emitido_no_cambia_si_luego_se_aplica_algo(db, admin):
    _, mascota = await _cachorro(db)
    registro = await db.run_sync(service.emitir_carnet, mascota.id, admin.id)
    rabia = (await _eventos(db, mascota, "can_rabia"))[0]
    await _autorizado(db, rabia, admin.id)
    await db.run_sync(
        lambda s: service.aplicar(
            s, rabia, fecha=HOY, producto="Rabisin", lote=None, usuario_id=admin.id
        )
    )
    verificado = await db.run_sync(service.verificar_carnet, registro.codigo)
    assert verificado["aplicados"] == []


def test_fechas_esquema_respeta_la_edad_minima():
    from app.modules.catalogos.models import EsquemaPreventivo

    esquema = EsquemaPreventivo(
        codigo="x",
        especie_codigo="canino",
        tipo="vacuna",
        nombre="x",
        edad_minima_semanas=12,
        dosis_iniciales=1,
        intervalo_inicial_dias=0,
        intervalo_refuerzo_dias=365,
    )
    nacio = date(2026, 1, 1)
    fechas, refuerzo = service.fechas_esquema(esquema, nacio, date(2026, 1, 15))
    assert fechas == [nacio + timedelta(weeks=12)] and not refuerzo
