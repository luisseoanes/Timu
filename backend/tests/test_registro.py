"""6.1 Registro en linea: ciudad, peludos con su plan, pago y formulario posterior."""

from datetime import datetime, timedelta
from decimal import Decimal
from urllib.parse import parse_qs, urlparse
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select, text

from app.core.config import settings
from app.core.database import ContextoDb, fijar_contexto
from app.core.tiempo import ahora, hoy
from app.modules.afiliaciones import registro
from app.modules.afiliaciones.models import SolicitudAfiliacion
from app.modules.cartera import pasarela
from app.modules.cartera.models import Contrato, Cuota, Pago
from app.modules.comercial import service as comercial
from app.modules.comercial.models import Interesado
from app.modules.comunicaciones.models import Mensaje
from app.modules.familias.models import ContactoFamilia, Familia
from app.modules.preventivos.models import EventoPreventivo
from app.modules.tareas.models import Tarea
from scripts import seed
from tests import fabricas
from tests.test_cartera import _evento

pytestmark = pytest.mark.integration

API = "/api/v1/afiliaciones/registro"


@pytest.fixture
async def timu(db, monkeypatch) -> dict[str, UUID]:
    """Los planes de TIMU (Medellin y Bogota) y la pasarela de pruebas."""
    monkeypatch.setattr(settings, "WOMPI_EVENTS_SECRET", "secreto-eventos")
    monkeypatch.setattr(settings, "WOMPI_INTEGRITY_SECRET", "secreto-integridad")
    planes = {p.codigo: p.id for p in await db.run_sync(seed.crear_planes_timu)}
    await db.run_sync(fabricas.plantillas_aprobadas)
    await db.commit()
    return planes


def _registro(timu, **cambios) -> dict:
    datos = {
        "ciudad": "Medellin",
        "peludos": [
            {"nombre": "Luna", "especie": "felino", "plan_id": str(timu["colita_feliz"])},
            {"nombre": "Max", "especie": "canino", "plan_id": str(timu["mi_amigo_fiel"])},
        ],
        "periodicidad": "mensual",
        "contacto": {"nombre": "Ana Ruiz", "telefono": "3001234567", "email": "ana@correo.co"},
        "acepta_condiciones": True,
        "acepta_tratamiento_datos": True,
    }
    return {**datos, **cambios}


def _formulario(token: str, documento: str = "52111222", **cambios) -> dict:
    datos = {
        "token": token,
        "titular": {
            "titular_nombre": "Ana Ruiz Gomez",
            "tipo_documento": "CC",
            "documento": documento,
            "telefono": "3001234567",
            "email": "ana@correo.co",
            "barrio": "El Poblado",
            "direccion": "Calle 10 # 43-12",
            "complemento": "Torre 2 apto 501",
        },
        "contactos": [{"nombre": "Pedro Ruiz", "telefono": "3009876543", "relacion": "esposo"}],
        "clave": "clave-segura-1",
        "peludos": [
            {
                "posicion": 1,
                "nombre": "Lunita",
                "sexo": "hembra",
                "fecha_nacimiento": "2022-01-01",
                "peso_kg": 4.2,
            },
            {"posicion": 2, "nombre": "Max", "fecha_nacimiento": "2020-06-01", "peso_kg": 18},
        ],
    }
    return {**datos, **cambios}


async def _pagar(db, referencia: str, valor: Decimal) -> None:
    evento, _ = await db.run_sync(pasarela.registrar_evento, _evento(referencia, int(valor * 100)))
    assert await db.run_sync(pasarela.procesar_evento, evento.id) == "procesado"
    await db.commit()


async def _iniciar_y_pagar(client, db, timu, **cambios) -> dict:
    inicio = await client.post(API, json=_registro(timu, **cambios))
    assert inicio.status_code == 201, inicio.text
    datos = inicio.json()
    await _pagar(db, datos["referencia"], Decimal(datos["valor"]))
    return datos


async def test_la_ciudad_y_los_planes_salen_del_catalogo(client: AsyncClient, timu):
    assert (await client.get(f"{API}/ciudades")).json() == ["Bogota", "Medellin"]
    bogota = (await client.get(f"{API}/planes", params={"ciudad": "bogota"})).json()
    assert [p["codigo"] for p in bogota] == ["colita_feliz", "mi_amigo_fiel"]
    assert bogota[0]["tarifas"][0] == {"peludos": 1, "valor": "35500.00"}
    cotizacion = await client.post(
        f"{API}/cotizacion",
        json={
            "ciudad": "Medellin",
            "peludos": [{"especie": "felino", "plan_id": str(timu["colita_feliz"])}],
        },
    )
    anual = next(c for c in cotizacion.json() if c["periodicidad"] == "anual")
    assert (anual["valor_periodo"], anual["descuento"]) == ("378000.00", True)


async def test_el_valor_lo_calcula_el_backend_y_no_hay_familia_hasta_el_formulario(
    client: AsyncClient, db, timu
):
    inicio = await client.post(API, json=_registro(timu, periodicidad="trimestral"))
    assert inicio.status_code == 201, inicio.text
    datos = inicio.json()
    # 2 peludos: tarifa de 2 de cada plan (30.500 + 61.000) por tres meses, sin descuento.
    assert datos["valor"] == "274500.00"
    enlace = parse_qs(urlparse(datos["enlace_pago"]).query)
    assert enlace["amount-in-cents"] == ["27450000"]
    assert enlace["customer-data:email"] == ["ana@correo.co"]
    assert len(datos["token"]) > 20
    solicitud = await db.scalar(
        select(SolicitudAfiliacion).where(
            SolicitudAfiliacion.referencia_pago == datos["referencia"]
        )
    )
    assert (solicitud.familia_id, solicitud.ciudad, solicitud.estado) == (
        None,
        "Medellin",
        "pendiente_pago",
    )
    assert solicitud.contacto_telefono == "+573001234567"
    assert solicitud.token_hash != datos["token"]  # solo la huella
    pago = await db.get(Pago, solicitud.pago_id)
    assert (pago.familia_id, pago.valor) == (None, Decimal("274500.00"))
    assert await db.scalar(select(func.count()).select_from(Familia)) == 0


@pytest.mark.parametrize(
    ("cambios", "mensaje"),
    [
        ({"acepta_condiciones": False}, "aceptar las condiciones"),
        ({"sitio_web": "http://spam"}, "rechazada"),
        ({"ciudad": "Cali"}, "cobertura en Cali"),
    ],
)
async def test_rechaza_sin_aceptar_un_bot_o_una_ciudad_sin_cobertura(
    client: AsyncClient, timu, cambios, mensaje
):
    resp = await client.post(API, json=_registro(timu, **cambios))
    assert resp.status_code == 422 and mensaje in resp.text


async def test_rechaza_nombres_repetidos_y_planes_que_no_se_venden_en_la_ciudad(
    client: AsyncClient, timu
):
    repetidos = _registro(timu)
    repetidos["peludos"][1]["nombre"] = " luna "
    resp = await client.post(API, json=repetidos)
    assert resp.status_code == 422 and "nombre distinto" in resp.text
    bogota = _registro(timu, ciudad="Bogota")
    bogota["peludos"][1]["plan_id"] = str(timu["amigos_por_siempre"])
    resp = await client.post(API, json=bogota)
    assert resp.status_code == 422 and "no esta disponible en Bogota" in resp.text


async def test_el_pago_deja_el_registro_pagado_y_envia_el_enlace(client: AsyncClient, db, timu):
    datos = await _iniciar_y_pagar(client, db, timu)
    consulta = (await client.post(f"{API}/consulta", json={"token": datos["token"]})).json()
    assert consulta["estado"] == "pagada"
    assert [(p["nombre"], p["valor_mensual"]) for p in consulta["peludos"]] == [
        ("Luna", "30500.00"),
        ("Max", "61000.00"),
    ]
    correo = await db.scalar(select(Mensaje).where(Mensaje.destino == "ana@correo.co"))
    whatsapp = await db.scalar(select(Mensaje).where(Mensaje.plantilla == "completar_afiliacion"))
    assert whatsapp is not None and whatsapp.destino == "+573001234567"
    assert "/afiliacion/completar?token=" in correo.contenido
    # El token del enlace tambien abre el registro.
    token_enlace = correo.contenido.split("token=")[1].split()[0]
    otra = await client.post(f"{API}/consulta", json={"token": token_enlace})
    assert otra.json()["estado"] == "pagada"


async def test_el_formulario_crea_la_familia_la_afiliacion_y_abre_la_sesion(
    client: AsyncClient, db, timu, almacenamiento
):
    datos = await _iniciar_y_pagar(client, db, timu)
    resp = await client.post(f"{API}/completar", json=_formulario(datos["token"]))
    assert resp.status_code == 200, resp.text
    assert resp.json()["estado"] == "completada"
    assert "timu_sesion" in resp.cookies or settings.COOKIE_NAME in resp.cookies

    familia = await db.scalar(select(Familia).where(Familia.documento == "52111222"))
    await db.refresh(familia, ["mascotas"])
    assert (familia.estado, familia.barrio, familia.complemento) == (
        "activa",
        "El Poblado",
        "Torre 2 apto 501",
    )
    # El nombre se corrige en el formulario; la especie no se cambia.
    assert sorted((m.nombre, m.especie) for m in familia.mascotas) == [
        ("Lunita", "felino"),
        ("Max", "canino"),
    ]
    contactos = await db.scalar(
        select(func.count())
        .select_from(ContactoFamilia)
        .where(ContactoFamilia.familia_id == familia.id)
    )
    assert contactos == 1
    contrato = await db.scalar(select(Contrato).where(Contrato.familia_id == familia.id))
    assert contrato.valor_periodo == Decimal("91500.00")
    cuota = await db.scalar(select(Cuota).where(Cuota.contrato_id == contrato.id))
    assert cuota.estado == "pagada"
    assert len(contrato.evidencia_aceptacion["sha256_documento"]) == 64
    assert any(c.startswith("contrato/") for c in almacenamiento.objetos)
    preventivos = await db.scalar(
        select(func.count())
        .select_from(EventoPreventivo)
        .where(EventoPreventivo.mascota_id.in_([m.id for m in familia.mascotas]))
    )
    assert preventivos > 0
    plantillas = set(
        await db.scalars(select(Mensaje.plantilla).where(Mensaje.familia_id == familia.id))
    )
    assert "bienvenida" in plantillas and "activar_cuenta" not in plantillas
    # El enlace del formulario salio antes de que existiera la familia: ahora es suyo, sale en
    # su historial y se anonimiza con ella.
    previos = (
        select(func.count())
        .select_from(Mensaje)
        .where(Mensaje.destino.in_(["ana@correo.co", "+573001234567"]))
    )
    assert await db.scalar(previos.where(Mensaje.familia_id.is_(None))) == 0
    assert await db.scalar(previos.where(Mensaje.familia_id == familia.id)) >= 2

    # Con la clave elegida entra al portal; el formulario no se repite.
    ingreso = await client.post(
        "/api/v1/auth/login", data={"username": "ana@correo.co", "password": "clave-segura-1"}
    )
    assert ingreso.status_code == 200
    otra_vez = await client.post(f"{API}/completar", json=_formulario(datos["token"]))
    assert otra_vez.json()["estado"] == "completada"
    assert await db.scalar(select(func.count()).select_from(Contrato)) == 1


async def test_el_registro_mueve_el_embudo_comercial(client: AsyncClient, db, timu, almacenamiento):
    datos = await _iniciar_y_pagar(client, db, timu)
    # Quien pago y no completa el formulario ya esta en el embudo, con su contacto.
    interesado = await db.scalar(select(Interesado).where(Interesado.email == "ana@correo.co"))
    assert (interesado.etapa, interesado.origen, interesado.plan_sugerido) == (
        "en_afiliacion",
        "afiliacion",
        "colita_feliz",
    )
    assert interesado.familia_id is None
    resp = await client.post(f"{API}/completar", json=_formulario(datos["token"]))
    assert resp.json()["estado"] == "completada"
    await db.refresh(interesado)
    assert interesado.etapa == "afiliado" and interesado.familia_id is not None
    assert await db.scalar(select(func.count()).select_from(Interesado)) == 1
    embudo = await db.run_sync(comercial.embudo, hoy() - timedelta(days=1), hoy())
    assert embudo["por_etapa"]["afiliado"] == 1 and embudo["conversion"] == 1.0


async def test_antes_de_confirmar_el_pago_no_se_completa(client: AsyncClient, timu):
    inicio = (await client.post(API, json=_registro(timu))).json()
    resp = await client.post(f"{API}/completar", json=_formulario(inicio["token"]))
    assert resp.status_code == 422 and "confirmacion de tu pago" in resp.text


async def test_la_consulta_dice_si_la_pasarela_rechazo_el_pago(client: AsyncClient, db, timu):
    inicio = (await client.post(API, json=_registro(timu))).json()
    consulta = (await client.post(f"{API}/consulta", json={"token": inicio["token"]})).json()
    assert (consulta["estado"], consulta["estado_pago"]) == ("pendiente_pago", "pendiente")
    centavos = int(Decimal(inicio["valor"]) * 100)
    evento, _ = await db.run_sync(
        pasarela.registrar_evento, _evento(inicio["referencia"], centavos, "DECLINED")
    )
    await db.run_sync(pasarela.procesar_evento, evento.id)
    await db.commit()
    consulta = (await client.post(f"{API}/consulta", json={"token": inicio["token"]})).json()
    assert (consulta["estado"], consulta["estado_pago"]) == ("pendiente_pago", "rechazado")


async def test_un_token_que_no_existe_no_abre_nada(client: AsyncClient, timu):
    resp = await client.post(f"{API}/consulta", json={"token": "x" * 43})
    assert resp.status_code == 404


async def test_un_documento_existente_completa_su_ficha(client: AsyncClient, db, timu):
    existente = await db.run_sync(fabricas.familia, ciudad="Medellin", mascotas=0)
    existente.email = None
    documento = existente.documento
    await db.commit()
    datos = await _iniciar_y_pagar(client, db, timu)
    resp = await client.post(f"{API}/completar", json=_formulario(datos["token"], documento))
    assert resp.json()["estado"] == "completada", resp.text
    familias = list(await db.scalars(select(Familia).where(Familia.documento == documento)))
    assert len(familias) == 1
    await db.refresh(familias[0])
    # Llena lo que faltaba, sin sobrescribir lo que el equipo ya tenia.
    assert (familias[0].email, familias[0].titular_nombre) == ("ana@correo.co", "Ana Ruiz")


async def test_una_mascota_de_la_ficha_fuera_del_registro_va_a_revision(
    client: AsyncClient, db, timu
):
    """La tarifa depende de cuantos peludos hay: una mascota activa de la ficha que no se
    eligio en el registro no queda fuera sin que el equipo lo decida."""
    existente = await db.run_sync(fabricas.familia, ciudad="Medellin")
    documento = existente.documento
    await db.commit()
    datos = await _iniciar_y_pagar(client, db, timu)
    resp = await client.post(f"{API}/completar", json=_formulario(datos["token"], documento))
    assert resp.json()["estado"] == "revision"
    assert await db.scalar(select(func.count()).select_from(Contrato)) == 0
    tarea = await db.scalar(select(Tarea).where(Tarea.origen == "afiliacion"))
    assert "Elige el plan de: Mascota0" in tarea.descripcion


async def test_con_un_contrato_vigente_no_se_afilia_dos_veces(client: AsyncClient, db, timu):
    plan = await db.run_sync(fabricas.plan, "otro")
    familia, _ = await fabricas.afiliada(db, hoy(), plan, ciudad="Medellin")
    documento = familia.documento
    await db.commit()
    datos = await _iniciar_y_pagar(client, db, timu)
    resp = await client.post(f"{API}/completar", json=_formulario(datos["token"], documento))
    assert resp.json()["estado"] == "revision"
    assert await db.scalar(select(func.count()).select_from(Contrato)) == 1
    tarea = await db.scalar(select(Tarea).where(Tarea.titulo.like("Registro en linea%")))
    assert tarea is not None and "suman los peludos" in tarea.descripcion
    solicitud = await db.scalar(
        select(SolicitudAfiliacion).where(
            SolicitudAfiliacion.referencia_pago == datos["referencia"]
        )
    )
    await db.refresh(solicitud)
    assert solicitud.estado == "error"


async def test_recuerda_a_las_24_horas_y_avisa_al_equipo_a_las_48(
    client: AsyncClient, db, timu, en_worker
):
    from app.workers.tasks.afiliaciones import recordar_registros

    datos = await _iniciar_y_pagar(client, db, timu)
    solicitud = await db.scalar(
        select(SolicitudAfiliacion).where(
            SolicitudAfiliacion.referencia_pago == datos["referencia"]
        )
    )
    primer_enlace = solicitud.token_enlace_hash
    assert await en_worker(recordar_registros) == {"recordados": 0, "tareas": 0}

    solicitud.pagada_en = ahora() - timedelta(hours=25)
    await db.flush()
    assert await en_worker(recordar_registros) == {"recordados": 1, "tareas": 0}
    await db.refresh(solicitud)
    assert solicitud.token_enlace_hash != primer_enlace  # enlace nuevo
    assert await en_worker(recordar_registros) == {"recordados": 0, "tareas": 0}

    solicitud.pagada_en = ahora() - timedelta(hours=49)
    await db.flush()
    assert await en_worker(recordar_registros) == {"recordados": 0, "tareas": 1}
    assert await en_worker(recordar_registros) == {"recordados": 0, "tareas": 0}


async def test_la_base_solo_deja_ver_a_publico_el_registro_de_sus_llaves(
    client: AsyncClient, db, timu
):
    """Si Python fallara, RLS sigue: sin las llaves de un registro, publico no lo ve."""
    uno = (await client.post(API, json=_registro(timu))).json()
    (await client.post(API, json=_registro(timu))).json()
    solicitud = await db.scalar(
        select(SolicitudAfiliacion).where(SolicitudAfiliacion.referencia_pago == uno["referencia"])
    )

    def como_publico(s, llaves: tuple) -> tuple[int, int, int]:
        fijar_contexto(s, ContextoDb(rol="publico", llaves=llaves))
        return (
            s.scalar(text("SELECT count(*) FROM solicitudes_afiliacion")),
            s.scalar(text("SELECT count(*) FROM peludos_solicitud")),
            s.scalar(text("SELECT count(*) FROM pagos")),
        )

    assert await db.run_sync(como_publico, ()) == (0, 0, 0)
    con_llaves = (("registro", str(solicitud.id)), ("referencia_pago", uno["referencia"]))
    assert await db.run_sync(como_publico, con_llaves) == (1, 2, 1)
    assert registro.RECORDAR_DESPUES < registro.TAREA_DESPUES


# --- Lo que no se paga: reintento, cierre a las 48 horas y borrado a los seis meses -----------


async def _rechazar(db, referencia: str, valor: Decimal, **tx) -> None:
    evento_wompi = _evento(referencia, int(valor * 100), "DECLINED", tx_id=f"tx-{referencia}")
    evento_wompi["data"]["transaction"].update(tx)
    evento, _ = await db.run_sync(pasarela.registrar_evento, evento_wompi)
    await db.run_sync(pasarela.procesar_evento, evento.id)
    await db.commit()


async def _envejecer_enlace(db, *referencias: str) -> None:
    """El ultimo enlace se dio hace 49 horas: pasa el plazo del cierre."""
    await db.execute(
        text(
            "UPDATE pagos SET created_at = now() - interval '49 hours'"
            " WHERE referencia_externa = ANY(:referencias)"
        ),
        {"referencias": list(referencias)},
    )
    await db.commit()


async def _solicitud(db, referencia: str) -> SolicitudAfiliacion:
    solicitud = await db.scalar(
        select(SolicitudAfiliacion).where(SolicitudAfiliacion.referencia_pago == referencia)
    )
    await db.refresh(solicitud)
    return solicitud


async def test_el_enlace_de_pago_vence_a_las_24_horas(client: AsyncClient, timu):
    inicio = (await client.post(API, json=_registro(timu))).json()
    vence = parse_qs(urlparse(inicio["enlace_pago"]).query)["expiration-time"][0]
    restante = datetime.fromisoformat(vence) - ahora()
    assert timedelta(hours=23, minutes=59) < restante <= timedelta(hours=24)


async def test_tras_un_rechazo_se_reintenta_en_la_misma_solicitud(client: AsyncClient, db, timu):
    inicio = (await client.post(API, json=_registro(timu))).json()
    token = {"token": inicio["token"]}
    # Mientras el pago no se rechaza no hay reintento: el primero aun puede aprobarse.
    assert (await client.post(f"{API}/reintentar", json=token)).status_code == 422
    await _rechazar(db, inicio["referencia"], Decimal(inicio["valor"]))

    resp = await client.post(f"{API}/reintentar", json=token)
    assert resp.status_code == 200, resp.text
    nuevo = resp.json()
    assert nuevo["referencia"] != inicio["referencia"]
    assert parse_qs(urlparse(nuevo["enlace_pago"]).query)["reference"] == [nuevo["referencia"]]
    consulta = (await client.post(f"{API}/consulta", json=token)).json()
    assert (consulta["estado"], consulta["estado_pago"]) == ("pendiente_pago", "pendiente")
    solicitud = await _solicitud(db, nuevo["referencia"])
    assert solicitud.referencias_anteriores == [inicio["referencia"]]
    assert await db.scalar(select(func.count()).select_from(SolicitudAfiliacion)) == 1

    # El pago nuevo completa el registro como el primero.
    await _pagar(db, nuevo["referencia"], Decimal(inicio["valor"]))
    assert (await client.post(f"{API}/consulta", json=token)).json()["estado"] == "pagada"


async def test_un_aprobado_con_la_referencia_anterior_paga_y_uno_doble_va_al_equipo(
    client: AsyncClient, db, timu
):
    """El reintento propio de Wompi aprueba con la referencia rechazada aunque ya hayamos
    dado otra: ese pago cuenta, y si despues tambien se paga el enlace nuevo, es doble."""
    inicio = (await client.post(API, json=_registro(timu))).json()
    valor = Decimal(inicio["valor"])
    await _rechazar(db, inicio["referencia"], valor)
    nuevo = (await client.post(f"{API}/reintentar", json={"token": inicio["token"]})).json()

    evento, _ = await db.run_sync(
        pasarela.registrar_evento, _evento(inicio["referencia"], int(valor * 100), tx_id="tx-2")
    )
    assert await db.run_sync(pasarela.procesar_evento, evento.id) == "procesado"
    await db.commit()
    solicitud = await _solicitud(db, inicio["referencia"])
    assert solicitud.estado == "pagada"
    assert solicitud.referencias_anteriores == [nuevo["referencia"]]
    vigente = await db.scalar(select(Pago).where(Pago.referencia_externa == nuevo["referencia"]))
    assert vigente.estado == "anulado"

    evento, _ = await db.run_sync(
        pasarela.registrar_evento, _evento(nuevo["referencia"], int(valor * 100), tx_id="tx-3")
    )
    await db.run_sync(pasarela.procesar_evento, evento.id)
    await db.commit()
    doble = await db.scalar(
        select(Tarea).where(Tarea.clave == f"registro_pago_doble:{nuevo['referencia']}")
    )
    assert doble is not None and doble.prioridad == "alta"
    await db.refresh(solicitud)
    assert solicitud.estado == "pagada"


async def test_a_las_48_horas_sin_pago_se_cierra_y_comercial_recibe_la_tarea(
    client: AsyncClient, db, timu, en_worker
):
    from app.workers.tasks.afiliaciones import cerrar_registros_sin_pago

    vencido = (await client.post(API, json=_registro(timu))).json()
    rechazado = (
        await client.post(
            API,
            json=_registro(
                timu,
                contacto={
                    "nombre": "Luis Mora",
                    "telefono": "3017778899",
                    "email": "luis@correo.co",
                },
            ),
        )
    ).json()
    reciente = (
        await client.post(
            API,
            json=_registro(
                timu,
                contacto={"nombre": "Eva Paz", "telefono": "3024445566", "email": "eva@correo.co"},
            ),
        )
    ).json()
    await _rechazar(db, rechazado["referencia"], Decimal(rechazado["valor"]))
    # Luis ya es familia (se afilio con el equipo): no hace falta llamarlo.
    familia = await db.run_sync(fabricas.familia, ciudad="Medellin", mascotas=0)
    familia.email = "luis@correo.co"
    await _envejecer_enlace(db, vencido["referencia"], rechazado["referencia"])

    assert await en_worker(cerrar_registros_sin_pago) == {
        "canceladas": 2,
        "tareas": 1,
        "altas_canceladas": 0,
    }
    assert await en_worker(cerrar_registros_sin_pago) == {
        "canceladas": 0,
        "tareas": 0,
        "altas_canceladas": 0,
    }
    estados = {
        r: (await _solicitud(db, r)).estado
        for r in (vencido["referencia"], rechazado["referencia"], reciente["referencia"])
    }
    assert estados == {
        vencido["referencia"]: "cancelada",
        rechazado["referencia"]: "cancelada",
        reciente["referencia"]: "pendiente_pago",
    }
    pagos = dict((await db.execute(select(Pago.referencia_externa, Pago.estado))).tuples().all())
    assert pagos[vencido["referencia"]] == "anulado"
    assert pagos[rechazado["referencia"]] == "rechazado"
    tarea = await db.scalar(select(Tarea).where(Tarea.titulo == "Registro en linea sin pagar"))
    solicitud = await _solicitud(db, vencido["referencia"])
    assert tarea.clave == f"registro_sin_pago:{solicitud.id}" and tarea.area == "comercial"
    assert "Ana Ruiz (+573001234567, ana@correo.co)" in tarea.descripcion
    assert "Luna (felino), Max (canino)" in tarea.descripcion

    # Si aun asi llega el pago (un evento tardio), no se afilia solo: lo decide el equipo.
    await _pagar(db, vencido["referencia"], Decimal(vencido["valor"]))
    tardio = await db.scalar(
        select(Tarea).where(Tarea.titulo == "Pago recibido de un registro en linea ya cerrado")
    )
    assert tardio is not None and tardio.prioridad == "alta"


async def test_a_los_seis_meses_se_borra_el_contacto_de_lo_que_nunca_se_pago(
    client: AsyncClient, db, timu, en_worker
):
    from app.workers.tasks.afiliaciones import (
        anonimizar_registros_abandonados,
        cerrar_registros_sin_pago,
    )

    abandonado = (await client.post(API, json=_registro(timu))).json()
    await _rechazar(
        db,
        abandonado["referencia"],
        Decimal(abandonado["valor"]),
        customer_email="ana@correo.co",
        customer_data={"full_name": "Ana Ruiz", "phone_number": "+573001234567"},
    )
    # Uno pagado del mismo periodo no se toca: es un cliente.
    pagado = await _iniciar_y_pagar(
        client,
        db,
        timu,
        contacto={"nombre": "Luis Mora", "telefono": "3017778899", "email": "luis@correo.co"},
    )
    await _envejecer_enlace(db, abandonado["referencia"])
    assert await en_worker(cerrar_registros_sin_pago) == {
        "canceladas": 1,
        "tareas": 1,
        "altas_canceladas": 0,
    }
    assert await en_worker(anonimizar_registros_abandonados) == {"anonimizados": 0}

    hace_siete_meses = "now() - interval '7 months'"
    await db.execute(text(f"UPDATE solicitudes_afiliacion SET created_at = {hace_siete_meses}"))
    await db.execute(
        text(
            f"UPDATE interesados SET created_at = {hace_siete_meses},"
            f" ultimo_contacto = {hace_siete_meses}"
        )
    )
    await db.commit()
    assert await en_worker(anonimizar_registros_abandonados) == {"anonimizados": 1}
    assert await en_worker(anonimizar_registros_abandonados) == {"anonimizados": 0}

    for tabla in (
        "solicitudes_afiliacion",
        "peludos_solicitud",
        "interesados",
        "tareas",
        "pagos",
        "eventos_pasarela",
        "auditoria",
    ):
        filas = await db.scalar(
            text(f"SELECT count(*) FROM {tabla} t WHERE to_jsonb(t)::text ~ :pii"),
            {"pii": "Ana Ruiz|ana@correo|3001234567"},
        )
        assert filas == 0, tabla
    solicitud = await _solicitud(db, abandonado["referencia"])
    assert solicitud.anonimizada_en is not None and solicitud.contacto_nombre == "Anonimizado"
    # La evidencia de aceptacion se conserva sin la IP ni el navegador.
    assert {"ip", "agente"}.isdisjoint(solicitud.aceptacion)
    assert solicitud.aceptacion["medio"] == "formulario_web"
    # El pagado conserva todo.
    conservado = await _solicitud(db, pagado["referencia"])
    assert (conservado.contacto_nombre, conservado.anonimizada_en) == ("Luis Mora", None)
    assert {"ip", "agente"} <= set(conservado.aceptacion)
    assert (
        await db.scalar(
            select(func.count()).select_from(Interesado).where(Interesado.email == "luis@correo.co")
        )
        == 1
    )


async def test_solo_el_sistema_borra_los_registros_abandonados(db):
    await db.run_sync(fijar_contexto, ContextoDb(rol="admin"))
    with pytest.raises(Exception, match="Solo el sistema"):
        await db.execute(text("SELECT anonimizar_registros_abandonados(now())"))
