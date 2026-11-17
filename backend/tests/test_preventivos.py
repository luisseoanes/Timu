"""F2-PRE-01..06 Esquemas, proximas fechas, autorizacion, agenda y carnet verificable."""

from datetime import date, time, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.enums import Rol
from app.core.tiempo import hoy
from app.modules.comunicaciones.models import Mensaje, PlantillaWhatsApp
from app.modules.preventivos import documento, service
from app.modules.preventivos.models import CarnetEmitido, EventoPreventivo
from app.modules.servicios.models import Franja
from tests import fabricas
from tests.conftest import crear_usuario, login

pytestmark = pytest.mark.integration

HOY = hoy()


async def _cachorro(db, semanas: int = 10, **familia_extra):
    """Familia afiliada con un cachorro de `semanas` y su calendario programado."""
    familia, contrato = await fabricas.afiliada(db, HOY, **familia_extra)
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


# --- F2-PRE-01 Calendario segun esquema -------------------------------------------------------


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


# --- F2-PRE-02 / 03 Autorizacion y aplicacion -------------------------------------------------


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


async def test_flujo_http_autorizar_y_aplicar(client: AsyncClient, db, headers, admin):
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
        json={"fecha": str(HOY), "producto": "Rabisin", "lote": "R-77", "peso_kg": 12.5},
        headers=headers,
    )
    assert aplicado.status_code == 200, aplicado.text
    assert aplicado.json()["proxima_fecha"] == str(HOY + timedelta(days=365))
    assert aplicado.json()["peso_kg"] == 12.5
    # Queda quien aplico, como el sello del carnet impreso.
    assert aplicado.json()["aplicado_por_nombre"] == admin.nombre


@pytest.mark.parametrize("peso", [0, -3, 150])
async def test_un_peso_imposible_no_se_registra(client: AsyncClient, db, headers, peso):
    _, mascota = await _cachorro(db)
    evento_id = (await _eventos(db, mascota, "can_desp_interna"))[0].id
    await db.commit()
    url = f"/api/v1/preventivos/{evento_id}"
    await client.post(f"{url}/autorizacion", json={"medio": "whatsapp"}, headers=headers)
    respuesta = await client.post(
        f"{url}/aplicacion",
        json={"fecha": str(HOY), "producto": "Drontal", "peso_kg": peso},
        headers=headers,
    )
    assert respuesta.status_code == 422


# --- F2-PRE-04 Agenda -------------------------------------------------------------------------


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


DIA_VISITA = HOY + timedelta(days=7)


def _franja_preventiva(db, dia: date = DIA_VISITA) -> None:
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


async def test_agendar_crea_el_servicio(client: AsyncClient, db, headers):
    dia = DIA_VISITA
    _franja_preventiva(db)
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


# --- R2-PAN-08 El servicio manda: la visita de un preventivo es su registro -------------------


async def _visita(client: AsyncClient, db, headers, *, autorizado: bool, esquema="can_rabia"):
    """Agenda la visita del primer preventivo del esquema (por defecto, el refuerzo de rabia)
    de un cachorro, autorizado o no antes."""
    _franja_preventiva(db)
    _, mascota = await _cachorro(db)
    evento = (await _eventos(db, mascota, esquema))[0]
    evento_id = evento.id
    await db.commit()
    url = f"/api/v1/preventivos/{evento_id}"
    if autorizado:
        await client.post(f"{url}/autorizacion", json={"medio": "whatsapp"}, headers=headers)
    agendado = await client.post(
        f"{url}/agendar", json={"inicio": f"{DIA_VISITA}T09:00:00"}, headers=headers
    )
    assert agendado.status_code == 200, agendado.text
    return evento_id, agendado.json()["servicio_id"]


async def _evento(client: AsyncClient, headers, evento_id) -> dict:
    eventos = (await client.get("/api/v1/preventivos", headers=headers)).json()["items"]
    return next(e for e in eventos if e["id"] == str(evento_id))


async def test_la_visita_de_un_preventivo_autorizado_nace_autorizada(
    client: AsyncClient, db, headers
):
    _, servicio_id = await _visita(client, db, headers, autorizado=True)
    servicio = (await client.get(f"/api/v1/servicios/{servicio_id}", headers=headers)).json()
    assert (servicio["estado"], servicio["autorizado"]) == ("agendado", True)


async def test_autorizar_el_preventivo_autoriza_su_visita(client: AsyncClient, db, headers):
    evento_id, servicio_id = await _visita(client, db, headers, autorizado=False)
    url = f"/api/v1/servicios/{servicio_id}"
    assert (await client.get(url, headers=headers)).json()["estado"] == "pendiente_autorizacion"
    await client.post(
        f"/api/v1/preventivos/{evento_id}/autorizacion", json={"medio": "telefono"}, headers=headers
    )
    assert (await client.get(url, headers=headers)).json()["estado"] == "agendado"


async def test_autorizar_la_visita_autoriza_el_preventivo(client: AsyncClient, db, headers):
    evento_id, servicio_id = await _visita(client, db, headers, autorizado=False)
    await client.post(f"/api/v1/servicios/{servicio_id}/autorizar", headers=headers)
    assert (await _evento(client, headers, evento_id))["autorizado"] is True


async def test_completar_la_visita_aplica_el_preventivo(client: AsyncClient, db, headers):
    evento_id, servicio_id = await _visita(client, db, headers, autorizado=True)
    await crear_usuario(db, "vet@timu.co", Rol.MEDICO)
    medico = await login(client, "vet@timu.co")
    url = f"/api/v1/servicios/{servicio_id}"
    await client.post(f"{url}/estado", json={"estado": "en_atencion"}, headers=medico)
    await client.put(
        f"{url}/pasos/aplicacion",
        json={"datos": {"producto": "Rabisin", "lote": "R-77"}},
        headers=medico,
    )
    completado = await client.post(f"{url}/estado", json={"estado": "completado"}, headers=medico)
    assert completado.status_code == 200, completado.text

    evento = await _evento(client, headers, evento_id)
    assert evento["estado"] == "aplicado"
    assert (evento["producto"], evento["lote"]) == ("Rabisin", "R-77")
    assert (evento["fecha_aplicacion"], evento["aplicado_por_nombre"]) == (str(HOY), "vet")
    # Y la siguiente dosis queda programada desde hoy, como al aplicarlo en Preventivos.
    assert evento["proxima_fecha"] == str(HOY + timedelta(days=365))


async def test_la_desparasitacion_en_visita_lleva_el_peso_al_carnet(
    client: AsyncClient, db, headers
):
    """DEU-4 / F2-PRE-07: el peso es opcional en la aplicacion de una desparasitacion."""
    evento_id, servicio_id = await _visita(
        client, db, headers, autorizado=True, esquema="can_desp_interna"
    )
    await crear_usuario(db, "vet@timu.co", Rol.MEDICO)
    medico = await login(client, "vet@timu.co")
    url = f"/api/v1/servicios/{servicio_id}"
    await client.post(f"{url}/estado", json={"estado": "en_atencion"}, headers=medico)
    paso = f"{url}/pasos/aplicacion"
    malo = await client.put(
        paso,
        json={"datos": {"producto": "Drontal", "lote": "D-1", "peso_kg": "doce"}},
        headers=medico,
    )
    assert malo.status_code == 422
    assert "Peso de la mascota (kg) debe ser una cifra" in malo.json()["detail"]
    sin_peso = await client.put(
        paso, json={"datos": {"producto": "Drontal", "lote": "D-1", "peso_kg": ""}}, headers=medico
    )
    assert sin_peso.status_code == 200, sin_peso.text
    con_peso = await client.put(
        paso,
        json={"datos": {"producto": "Drontal", "lote": "D-1", "peso_kg": "12,5"}},
        headers=medico,
    )
    assert con_peso.status_code == 200, con_peso.text
    await client.post(f"{url}/estado", json={"estado": "completado"}, headers=medico)
    evento = await _evento(client, headers, evento_id)
    assert (evento["estado"], evento["peso_kg"]) == ("aplicado", 12.5)


async def test_cancelar_la_visita_deja_el_preventivo_por_agendar(client: AsyncClient, db, headers):
    evento_id, servicio_id = await _visita(client, db, headers, autorizado=True)
    await client.post(
        f"/api/v1/servicios/{servicio_id}/estado",
        json={"estado": "cancelado", "motivo": "La familia viaja"},
        headers=headers,
    )
    assert (await _evento(client, headers, evento_id))["servicio_id"] is None
    otra = await client.post(
        f"/api/v1/preventivos/{evento_id}/agendar",
        json={"inicio": f"{DIA_VISITA}T10:00:00"},
        headers=headers,
    )
    assert otra.status_code == 200, otra.text


async def test_la_bandeja_agrupa_por_familia_con_el_siguiente_paso(
    client: AsyncClient, db, headers
):
    _franja_preventiva(db)
    familia, mascota = await _cachorro(db)
    otra, _ = await _cachorro(db, telefono="+573009998877")
    limite = HOY + timedelta(days=service.VENTANA_BANDEJA_DIAS)
    cerca = [
        e
        for e in await db.scalars(
            select(EventoPreventivo).where(EventoPreventivo.mascota_id == mascota.id)
        )
        if e.fecha_programada <= limite
    ]
    ids_cerca = [str(e.id) for e in cerca]
    familia_id, otra_id = str(familia.id), str(otra.id)
    await db.commit()
    url = "/api/v1/preventivos/bandeja"

    pagina = (await client.get(url, headers=headers)).json()
    assert {g["familia_id"] for g in pagina["items"]} == {familia_id, otra_id}
    # La de una familia, como la pide su linea en la ficha.
    una = (await client.get(url, params={"familia_id": otra_id}, headers=headers)).json()
    assert [g["familia_id"] for g in una["items"]] == [otra_id]
    grupo = next(g for g in pagina["items"] if g["familia_id"] == familia_id)
    assert {e["id"] for e in grupo["eventos"]} == set(ids_cerca)
    assert {e["siguiente"] for e in grupo["eventos"]} == {"autorizar"}
    assert grupo["eventos"][0]["mascota_nombre"] == mascota.nombre
    # El nombre del esquema, no el tipo: «Rabia», no «vacuna».
    assert all(e["nombre"] != e["tipo"] for e in grupo["eventos"])
    # Con que tipo de servicio se agenda cada uno: el panel pide con el las franjas (DEU-23).
    assert {(e["tipo"], e["tipo_servicio_codigo"]) for e in grupo["eventos"]} <= {
        ("vacuna", "vacunacion"),
        ("desparasitacion_interna", "desparasitacion"),
        ("desparasitacion_externa", "desparasitacion"),
    }

    # La familia autoriza de una vez lo que se le pidio.
    autorizados = await client.post(
        "/api/v1/preventivos/autorizaciones",
        json={"eventos": ids_cerca, "medio": "whatsapp"},
        headers=headers,
    )
    assert autorizados.status_code == 200, autorizados.text
    recuentos = (await client.get(f"{url}/recuentos", headers=headers)).json()
    assert recuentos["por_agendar"] == len(ids_cerca)
    por_agendar = (await client.get(url, params={"vista": "por_agendar"}, headers=headers)).json()
    assert [g["familia_id"] for g in por_agendar["items"]] == [familia_id]

    await client.post(
        f"/api/v1/preventivos/{ids_cerca[0]}/agendar",
        json={"inicio": f"{DIA_VISITA}T09:00:00"},
        headers=headers,
    )
    agendados = (await client.get(url, params={"vista": "agendados"}, headers=headers)).json()
    [evento] = agendados["items"][0]["eventos"]
    assert evento["siguiente"] == "visita"
    assert evento["visita"]["estado"] == "agendado"


async def test_autorizar_varios_es_todo_o_nada(client: AsyncClient, db, headers, admin):
    _, mascota = await _cachorro(db)
    primero, segundo = (await _eventos(db, mascota, "can_polivalente"))[:2]
    await db.run_sync(service.cancelar, segundo, "La familia lo aplico en otra clinica")
    ids = [str(primero.id), str(segundo.id)]
    primero_id = primero.id
    await db.commit()
    resp = await client.post(
        "/api/v1/preventivos/autorizaciones",
        json={"eventos": ids, "medio": "telefono"},
        headers=headers,
    )
    assert resp.status_code == 422
    assert (await db.get(EventoPreventivo, primero_id, populate_existing=True)).autorizado is False


# --- F2-PRE-05 / 06 Carnet --------------------------------------------------------------------


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
    assert [a["nombre"] for a in datos["aplicados"]] == ["Antirrábica canina"]
    assert datos["aplicados"][0]["peso_kg"] is None
    assert any(v["id"] == str(externa.id) for v in datos["vencidos"])
    assert all(p["fecha_programada"] >= str(HOY) for p in datos["proximos"])
    # Nada programado aparece como aplicado.
    assert all(a["fecha_aplicacion"] for a in datos["aplicados"])


async def test_el_carnet_lleva_el_peso_de_cada_desparasitacion(db, admin):
    _, mascota = await _cachorro(db)
    interna = (await _eventos(db, mascota, "can_desp_interna"))[0]
    await _autorizado(db, interna, admin.id)
    await db.run_sync(
        lambda s: service.aplicar(
            s, interna, fecha=HOY, producto="Drontal", lote=None, usuario_id=admin.id, peso_kg=8.4
        )
    )
    (fila,) = (await db.run_sync(service.carnet, mascota.id, HOY))["aplicados"]
    assert fila["peso_kg"] == 8.4
    # En el PDF, la tabla de la desparasitacion interna lleva el peso en su columna.
    (en_pdf,) = documento.filas_seccion("desparasitacion_interna", [fila])
    assert en_pdf[1] == "8,4 kg"
    assert (
        documento.filas_seccion("desparasitacion_interna", [{**fila, "peso_kg": 12.0}])[0][1]
        == "12 kg"
    )
    assert (
        documento.filas_seccion("desparasitacion_interna", [{**fila, "peso_kg": None}])[0][1] == "—"
    )
    # Una vacuna no va en esa tabla.
    assert documento.filas_seccion("vacuna", [fila]) == []


async def test_el_peso_de_la_aplicacion_pasa_a_la_ficha_si_es_el_mas_reciente(db, admin):
    _, mascota = await _cachorro(db)
    mascota.peso_kg = 6.0
    interna = (await _eventos(db, mascota, "can_desp_interna"))[0]
    externa = (await _eventos(db, mascota, "can_desp_externa"))[0]
    for evento in (interna, externa):
        await _autorizado(db, evento, admin.id)

    def aplicar(evento, fecha, peso):
        return db.run_sync(
            lambda s: service.aplicar(
                s, evento, fecha=fecha, producto="P", lote=None, usuario_id=admin.id, peso_kg=peso
            )
        )

    await aplicar(interna, HOY, 8.4)
    assert mascota.peso_kg == 8.4
    # Una aplicacion anotada con fecha anterior no pisa el peso mas reciente.
    await aplicar(externa, HOY - timedelta(days=10), 7.9)
    assert mascota.peso_kg == 8.4
    assert externa.peso_kg == 7.9


async def test_sin_peso_la_ficha_no_cambia(db, admin):
    _, mascota = await _cachorro(db)
    mascota.peso_kg = 6.0
    interna = (await _eventos(db, mascota, "can_desp_interna"))[0]
    await _autorizado(db, interna, admin.id)
    await db.run_sync(
        lambda s: service.aplicar(
            s, interna, fecha=HOY, producto="P", lote=None, usuario_id=admin.id
        )
    )
    assert mascota.peso_kg == 6.0


async def test_el_carnet_dice_quien_aplico_cada_preventivo(db, admin, almacenamiento):
    _, mascota = await _cachorro(db)
    interna = (await _eventos(db, mascota, "can_desp_interna"))[0]
    await _autorizado(db, interna, admin.id)
    await db.run_sync(
        lambda s: service.aplicar(
            s,
            interna,
            fecha=HOY,
            producto="Drontal",
            lote=None,
            usuario_id=admin.id,
            aplicado_por_nombre="Dra. Paula Gómez",
        )
    )
    (fila,) = (await db.run_sync(service.carnet, mascota.id, HOY))["aplicados"]
    assert fila["aplicado_por"] == "Dra. Paula Gómez"
    assert documento.filas_seccion("desparasitacion_interna", [fila])[0][-1] == "Dra. Paula Gómez"
    registro = await db.run_sync(service.emitir_carnet, mascota.id, admin.id)
    verificado = await db.run_sync(service.verificar_carnet, registro.codigo)
    interna = verificado["secciones"][1]
    assert (interna["titulo"], interna["aplicados"][0]["aplicado_por"]) == (
        "Desparasitación interna",
        "Dra. Paula Gómez",
    )


def test_el_carnet_pdf_lleva_las_fuentes_de_la_marca():
    """Con las fuentes base del PDF (latin-1) las tildes se perdian: ahora va con las de TIMU."""
    datos = {
        "mascota": {"nombre": "Ñoño", "especie": "Canino", "raza": None, "fecha_nacimiento": None},
        "aplicados": [],
        "vencidos": [{"nombre": "Antirrábica", "dosis": 1, "fecha_programada": "2026-01-01"}],
        "proximos": [],
    }
    pdf = documento.generar_carnet(datos, codigo="ABC234DEFG", url_verificacion="https://x/v")
    assert pdf.startswith(b"%PDF-")
    assert b"GeosansLight" in pdf
    assert b"Inter" in pdf
    assert b"Helvetica" not in pdf


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
    vacunas = publico.json()["secciones"][0]
    assert [s["tipo"] for s in publico.json()["secciones"]] == [
        "vacuna",
        "desparasitacion_interna",
        "desparasitacion_externa",
    ]
    (rabia,) = vacunas["aplicados"]
    assert (rabia["lote"], rabia["dosis"]) == ("R1", "Dosis 1")
    # El peso es de la mascota: lo ve el tercero que verifica (aqui no se anoto).
    assert rabia["peso_kg"] is None
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
    assert all(s["aplicados"] == [] for s in verificado["secciones"])


async def test_la_verificacion_dice_lo_pendiente_como_el_carnet_impreso(db, admin):
    """6.15: el carnet dice las proximas fechas, y la verificacion dice lo mismo que el PDF el
    dia que se emitio: lo vencido y lo proximo, y la proxima fecha de cada aplicacion."""
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
    datos = await db.run_sync(service.carnet, mascota.id)
    registro = await db.run_sync(service.emitir_carnet, mascota.id, admin.id)

    verificado = await db.run_sync(service.verificar_carnet, registro.codigo)
    (aplicada,) = verificado["secciones"][0]["aplicados"]
    assert aplicada["proxima_fecha"] == datos["aplicados"][0]["proxima_fecha"]
    pendientes = verificado["pendientes"]
    assert len(pendientes) == len(datos["vencidos"]) + len(datos["proximos"])
    vencida = next(p for p in pendientes if p["vencido"])
    assert vencida["fecha_programada"] == (HOY - timedelta(days=3)).isoformat()
    assert vencida["dosis"] is None  # las desparasitaciones no dicen dosis, como en el PDF


async def test_un_carnet_emitido_antes_no_inventa_lo_pendiente(db, admin):
    _, mascota = await _cachorro(db)
    nuevo = await db.run_sync(service.emitir_carnet, mascota.id, admin.id)
    # Un carnet de antes guardaba solo la mascota y lo aplicado (la fila no cambia: inmutable).
    antiguo = CarnetEmitido(
        codigo="ANTIGUO234",
        mascota_id=mascota.id,
        archivo_id=nuevo.archivo_id,
        sha256=nuevo.sha256,
        contenido={k: nuevo.contenido[k] for k in ("mascota", "aplicados")},
        emitido_por_id=admin.id,
    )
    db.add(antiguo)
    await db.flush()
    assert (await db.run_sync(service.verificar_carnet, "ANTIGUO234"))["pendientes"] is None


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
