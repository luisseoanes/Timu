"""F3-POR-01..07 Portal de familias: datos, historia, carnet, autogestion, pagos,
actualizacion de datos e ingreso con codigo por WhatsApp."""

import re
from datetime import datetime, time, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text

from app.core.auditoria import RegistroAuditoria
from app.core.config import settings
from app.core.database import ContextoDb, fijar_contexto
from app.core.enums import EstadoEventoPreventivo, Rol, TipoPreventivo
from app.core.security import hash_password
from app.core.tiempo import ZONA_NEGOCIO, hoy
from app.modules.auth.models import Usuario
from app.modules.cartera import pasarela
from app.modules.cartera.models import Pago
from app.modules.clinica import service as clinica
from app.modules.comunicaciones.models import Mensaje, PlantillaWhatsApp
from app.modules.familias.models import Mascota
from app.modules.preventivos.models import EventoPreventivo
from app.modules.servicios.models import Franja
from tests import fabricas
from tests.conftest import PASSWORD, crear_usuario, login
from tests.test_cartera import _evento

pytestmark = pytest.mark.integration

DIA = hoy() + timedelta(days=5)


async def _familia_portal(db, telefono: str, email: str):
    familia, contrato = await fabricas.afiliada(db, hoy(), telefono=telefono)
    usuario = Usuario(
        email=email,
        telefono=telefono,
        nombre=familia.titular_nombre,
        rol=Rol.FAMILIA,
        hashed_password=hash_password(PASSWORD),
    )
    db.add(usuario)
    await db.flush()
    familia.usuario_portal_id = usuario.id
    await db.flush()
    return familia, contrato, usuario


@pytest.fixture
async def portal(client: AsyncClient, db):
    """Dos familias con portal; se entra como la primera."""
    propia, contrato, usuario = await _familia_portal(db, "+573001110001", "ana@correo.co")
    ajena, _, _ = await _familia_portal(db, "+573001110002", "beto@correo.co")
    db.add(
        Franja(
            ciudad="Cali",
            modalidad="domiciliario",
            dia_semana=DIA.weekday(),
            hora_inicio=time(8),
            hora_fin=time(12),
            capacidad=2,
        )
    )
    datos = {
        "familia_id": propia.id,
        "mascota_id": propia.mascotas[0].id,
        "contrato_id": contrato.id,
        "usuario_id": usuario.id,
        "ajena_id": ajena.id,
        "mascota_ajena_id": ajena.mascotas[0].id,
    }
    await db.commit()
    return {**datos, "headers": await login(client, "ana@correo.co")}


# --- F3-POR-01 / 06 Datos y plan --------------------------------------------------------------


async def test_ve_su_plan_y_estado_de_cuenta(client, portal):
    h = portal["headers"]
    plan = (await client.get("/api/v1/portal/plan", headers=h)).json()
    assert plan["estado"] == "activa"
    assert [m["color"] for m in plan["mascotas"]] == ["verde"]
    cuenta = (await client.get("/api/v1/portal/estado-cuenta", headers=h)).json()
    assert cuenta["contrato"]["familia_id"] == str(portal["familia_id"])


async def test_ve_su_linea_y_no_la_de_otra_familia(client, db, portal):
    """R3-POR-01 El inicio del portal es la linea de la familia: la misma que ve el equipo,
    con cada estacion ligada a su peludo, y sin nada de otra familia."""
    propio, ajeno = (
        EventoPreventivo(
            mascota_id=mascota_id,
            tipo=TipoPreventivo.VACUNA,
            fecha_programada=hoy() + timedelta(days=10),
            estado=EstadoEventoPreventivo.PROGRAMADO,
        )
        for mascota_id in (portal["mascota_id"], portal["mascota_ajena_id"])
    )
    db.add_all([propio, ajeno])
    await db.commit()

    resp = await client.get("/api/v1/portal/linea", headers=portal["headers"])
    assert resp.status_code == 200, resp.text
    cuerpo = resp.json()
    assert cuerpo["familia_id"] == str(portal["familia_id"])
    assert [p["color"] for p in cuerpo["planes"]] == ["verde"]
    preventivos = [e for e in cuerpo["estaciones"] if e["tipo"] == "preventivo"]
    assert [(e["referencia_id"], e["mascota_id"]) for e in preventivos] == [
        (str(propio.id), str(portal["mascota_id"]))
    ]
    assert any(e["tipo"] == "cuota" for e in cuerpo["estaciones"])


async def test_actualiza_contacto_auditado_pero_no_su_documento(client, db, portal):
    resp = await client.patch(
        "/api/v1/portal/mi-familia",
        json={"telefono": "310 555 1234", "direccion": "Cra 10 # 5-20", "documento": "999"},
        headers=portal["headers"],
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["telefono"] == "+573105551234"
    assert resp.json()["documento"] != "999"
    registro = await db.scalar(
        select(RegistroAuditoria)
        .where(RegistroAuditoria.entidad_id == str(portal["familia_id"]))
        .order_by(RegistroAuditoria.created_at.desc())
    )
    assert registro.usuario_id == portal["usuario_id"]
    assert "telefono" in registro.cambios


async def test_telefono_invalido_se_rechaza(client, portal):
    resp = await client.patch(
        "/api/v1/portal/mi-familia", json={"telefono": "123"}, headers=portal["headers"]
    )
    assert resp.status_code == 422


# --- F3-POR-02 / 03 Historia y carnet ---------------------------------------------------------


async def test_historia_solo_lo_firmado_y_sin_notas_internas(client, db, portal):
    medico = await crear_usuario(db, "vet@timu.co", Rol.MEDICO)
    firmada = await db.run_sync(
        clinica.crear_entrada,
        portal["mascota_id"],
        {"motivo": "Control", "diagnostico": "Sano", "notas_internas": "Familia ansiosa"},
        medico.id,
    )
    await db.run_sync(clinica.firmar, firmada, medico.id)
    await db.run_sync(
        clinica.crear_entrada, portal["mascota_id"], {"motivo": "Borrador"}, medico.id
    )
    await db.commit()

    h = portal["headers"]
    historia = (
        await client.get(f"/api/v1/portal/mascotas/{portal['mascota_id']}/historia", headers=h)
    ).json()
    assert [e["motivo"] for e in historia] == ["Control"]
    assert "notas_internas" not in historia[0]

    ajena = await client.get(
        f"/api/v1/portal/mascotas/{portal['mascota_ajena_id']}/historia", headers=h
    )
    assert ajena.status_code == 404


async def test_carnet_de_sus_mascotas(client, portal):
    h = portal["headers"]
    propio = await client.get(f"/api/v1/portal/mascotas/{portal['mascota_id']}/carnet", headers=h)
    assert propio.status_code == 200
    ajeno = await client.get(
        f"/api/v1/portal/mascotas/{portal['mascota_ajena_id']}/carnet", headers=h
    )
    assert ajeno.status_code == 404


# --- F3-POR-04 Autogestion --------------------------------------------------------------------


def _hora(h: int, dia=DIA) -> str:
    return datetime.combine(dia, time(h), ZONA_NEGOCIO).isoformat()


async def test_agenda_reprograma_y_cancela_dentro_de_las_reglas(client, portal):
    h = portal["headers"]
    cupos = await client.get(
        "/api/v1/portal/disponibilidad",
        params={"fecha": str(DIA), "tipo_codigo": "consulta_domiciliaria"},
        headers=h,
    )
    assert cupos.status_code == 200 and cupos.json()
    agendado = await client.post(
        "/api/v1/portal/servicios",
        json={
            "mascota_id": str(portal["mascota_id"]),
            "tipo_codigo": "consulta_domiciliaria",
            "inicio": _hora(9),
        },
        headers=h,
    )
    assert agendado.status_code == 201, agendado.text
    servicio_id = agendado.json()["id"]

    movido = await client.post(
        f"/api/v1/portal/servicios/{servicio_id}/reprogramacion",
        json={"inicio": _hora(10, DIA), "motivo": "Cambio de turno"},
        headers=h,
    )
    assert movido.status_code == 200, movido.text
    cancelado = await client.post(
        f"/api/v1/portal/servicios/{servicio_id}/cancelacion",
        json={"motivo": "Viaje"},
        headers=h,
    )
    assert cancelado.json()["estado"] == "cancelado"


async def test_no_agenda_lo_que_no_es_autogestionable(client, portal):
    resp = await client.post(
        "/api/v1/portal/servicios",
        json={
            "mascota_id": str(portal["mascota_id"]),
            "tipo_codigo": "atencion_aliada",
            "inicio": _hora(9),
        },
        headers=portal["headers"],
    )
    assert resp.status_code == 422


async def test_no_toca_servicios_de_otra_familia(client, db, portal, monkeypatch):
    from app.modules.familias.models import Familia
    from app.modules.servicios import service as servicios

    ajena = await db.get(Familia, portal["ajena_id"])
    tipo = await db.run_sync(servicios.tipo_servicio, "consulta_domiciliaria")
    servicio = await db.run_sync(
        lambda s: servicios.agendar(
            s,
            familia=ajena,
            mascota=ajena.mascotas[0],
            tipo=tipo,
            inicio=datetime.combine(DIA, time(11), ZONA_NEGOCIO),
        )
    )
    servicio_id = servicio.id
    await db.commit()
    resp = await client.post(
        f"/api/v1/portal/servicios/{servicio_id}/cancelacion",
        json={"motivo": "No es mio"},
        headers=portal["headers"],
    )
    assert resp.status_code == 404


async def test_cambios_con_poca_antelacion_van_por_el_equipo(client, portal, monkeypatch):
    h = portal["headers"]
    agendado = await client.post(
        "/api/v1/portal/servicios",
        json={
            "mascota_id": str(portal["mascota_id"]),
            "tipo_codigo": "consulta_domiciliaria",
            "inicio": _hora(9),
        },
        headers=h,
    )
    monkeypatch.setattr(settings, "PORTAL_ANTELACION_HORAS", 24 * 30)
    resp = await client.post(
        f"/api/v1/portal/servicios/{agendado.json()['id']}/cancelacion",
        json={"motivo": "Tarde"},
        headers=h,
    )
    assert resp.status_code == 422 and "anticipacion" in resp.json()["detail"]


# --- F3-POR-05 Pagos --------------------------------------------------------------------------


async def test_pago_en_linea_actualiza_y_da_comprobante(client, db, portal):
    h = portal["headers"]
    inicio = await client.post("/api/v1/portal/pagos", json={}, headers=h)
    assert inicio.status_code == 201, inicio.text
    pago = inicio.json()["pago"]
    assert pago["referencia_externa"] in inicio.json()["enlace_pago"]
    pendiente = await client.get(f"/api/v1/portal/pagos/{pago['id']}/comprobante", headers=h)
    assert pendiente.status_code == 422

    # Llega el webhook de la pasarela.
    registro, _ = await db.run_sync(
        pasarela.registrar_evento, _evento(pago["referencia_externa"], 4_500_000)
    )
    assert await db.run_sync(pasarela.procesar_evento, registro.id) == "procesado"
    await db.commit()

    cuenta = (await client.get("/api/v1/portal/estado-cuenta", headers=h)).json()
    assert float(cuenta["saldo_pendiente"]) == 0
    comprobante = await client.get(f"/api/v1/portal/pagos/{pago['id']}/comprobante", headers=h)
    assert comprobante.status_code == 200
    assert comprobante.content.startswith(b"%PDF-")


async def test_comprobante_de_otra_familia_no(client, db, portal):
    otro = Pago(
        familia_id=portal["ajena_id"],
        referencia_externa="AJENO-1",
        valor=1000,
        estado="aprobado",
    )
    db.add(otro)
    await db.commit()
    resp = await client.get(
        f"/api/v1/portal/pagos/{otro.id}/comprobante", headers=portal["headers"]
    )
    assert resp.status_code == 404


# --- F3-POR-07 Codigo por WhatsApp ------------------------------------------------------------


async def _codigo_enviado(db, telefono: str) -> str:
    mensaje = await db.scalar(
        select(Mensaje)
        .where(Mensaje.destino == telefono, Mensaje.plantilla == "codigo_ingreso")
        .order_by(Mensaje.created_at.desc())
    )
    return re.search(r"\b(\d{6})\b", mensaje.contenido).group(1)


@pytest.fixture
async def plantilla_codigo(db):
    db.add(
        PlantillaWhatsApp(
            nombre="codigo_ingreso",
            cuerpo="Hola {{1}}, tu codigo de ingreso es {{2}}",
            variables=["nombre", "codigo"],
            estado_aprobacion="aprobada",
            activa=True,
        )
    )
    await db.commit()


async def test_ingreso_con_codigo(client, db, portal, plantilla_codigo):
    client.cookies.clear()
    resp = await client.post("/api/v1/auth/codigo", json={"telefono": "300 111 0001"})
    assert resp.status_code == 202
    codigo = await _codigo_enviado(db, "+573001110001")
    ingreso = await client.post(
        "/api/v1/auth/codigo/verificacion", json={"telefono": "3001110001", "codigo": codigo}
    )
    assert ingreso.status_code == 200, ingreso.text
    assert (await client.get("/api/v1/portal/mi-familia")).status_code == 200
    # Un solo uso.
    client.cookies.clear()
    otra = await client.post(
        "/api/v1/auth/codigo/verificacion", json={"telefono": "3001110001", "codigo": codigo}
    )
    assert otra.status_code == 401


async def test_codigo_con_intentos_limitados(client, db, portal, plantilla_codigo, monkeypatch):
    client.cookies.clear()
    await client.post("/api/v1/auth/codigo", json={"telefono": "3001110001"})
    codigo = await _codigo_enviado(db, "+573001110001")
    errado = "000000" if codigo != "000000" else "111111"
    for _ in range(settings.CODIGO_MAX_INTENTOS):
        r = await client.post(
            "/api/v1/auth/codigo/verificacion", json={"telefono": "3001110001", "codigo": errado}
        )
        assert r.status_code == 401
    # Agotados los intentos, ni el correcto sirve.
    correcto = await client.post(
        "/api/v1/auth/codigo/verificacion", json={"telefono": "3001110001", "codigo": codigo}
    )
    assert correcto.status_code == 401


async def test_codigo_no_revela_si_el_numero_existe(client, db, plantilla_codigo):
    resp = await client.post("/api/v1/auth/codigo", json={"telefono": "3009998877"})
    assert resp.status_code == 202
    assert await db.scalar(select(Mensaje).where(Mensaje.destino == "+573009998877")) is None


async def test_familia_no_entra_a_lo_interno(client, portal):
    for ruta in (
        "/api/v1/servicios",
        "/api/v1/cartera/contratos/x",
        "/api/v1/clinica/virtual/cola",
    ):
        resp = await client.get(ruta, headers=portal["headers"])
        assert resp.status_code in (403, 422), ruta


# --- Lo que el portal no deja hacer y lo que lista -------------------------------------------


async def test_el_plan_muestra_cada_beneficio_con_lo_que_queda(client, db, portal):
    from app.modules.cartera import contratos
    from app.modules.planes.models import Beneficio

    plan = await db.run_sync(contratos.plan_de_mascota, portal["mascota_id"])
    db.add_all(
        [
            Beneficio(
                plan_id=plan.id,
                tipo_servicio_codigo="consulta_domiciliaria",
                cupo=6,
                periodo_cupo="anual",
                cobertura_pct=100,
            ),
            Beneficio(
                plan_id=plan.id,
                tipo_servicio_codigo="orientacion_virtual",
                cupo=None,
                cobertura_pct=100,
            ),
        ]
    )
    await db.commit()
    await db.refresh(plan, ["beneficios"])  # la prueba lo cargo antes de anadirlos
    # Cada peludo con su plan y sus beneficios: la familia tiene uno.
    (peludo,) = (await client.get("/api/v1/portal/plan", headers=portal["headers"])).json()[
        "mascotas"
    ]
    assert peludo["mascota_id"] == str(portal["mascota_id"])
    beneficios = peludo["beneficios"]
    por_tipo = {b["tipo_servicio"]: b for b in beneficios}
    assert (
        por_tipo["consulta_domiciliaria"]["usados"],
        por_tipo["consulta_domiciliaria"]["disponibles"],
    ) == (0, 6)
    assert (
        por_tipo["orientacion_virtual"]["disponibles"] is None
    ), "sin cupo no hay tope que mostrar"


async def test_sin_contrato_vigente_no_hay_plan_ni_pago(client, db, portal):
    from app.modules.cartera import service as cartera
    from app.modules.cartera.models import Contrato

    contrato = await db.get(Contrato, portal["contrato_id"])
    await db.run_sync(cartera.cancelar, contrato, "Se muda")
    await db.commit()
    h = portal["headers"]
    assert (await client.get("/api/v1/portal/plan", headers=h)).status_code == 404
    pago = await client.post("/api/v1/portal/pagos", json={}, headers=h)
    assert pago.status_code == 422 and "contrato vigente" in pago.json()["detail"]


async def test_lista_sus_pagos_y_no_paga_lo_que_no_debe(client, db, portal):
    from uuid import uuid4

    h = portal["headers"]
    iniciado = (await client.post("/api/v1/portal/pagos", json={}, headers=h)).json()["pago"]
    assert [p["id"] for p in (await client.get("/api/v1/portal/pagos", headers=h)).json()] == [
        iniciado["id"]
    ]
    cuota_ajena = await client.post(
        "/api/v1/portal/pagos", json={"cuota_id": str(uuid4())}, headers=h
    )
    assert cuota_ajena.status_code == 404

    registro, _ = await db.run_sync(
        pasarela.registrar_evento, _evento(iniciado["referencia_externa"], 4_500_000)
    )
    await db.run_sync(pasarela.procesar_evento, registro.id)
    await db.commit()
    sin_saldo = await client.post("/api/v1/portal/pagos", json={}, headers=h)
    assert sin_saldo.status_code == 422 and "saldo" in sin_saldo.json()["detail"]


async def test_sus_servicios_activos_y_los_pasados_a_pedido(client, portal):
    h = portal["headers"]
    agendado = await client.post(
        "/api/v1/portal/servicios",
        json={
            "mascota_id": str(portal["mascota_id"]),
            "tipo_codigo": "consulta_domiciliaria",
            "inicio": _hora(9),
        },
        headers=h,
    )
    servicio_id = agendado.json()["id"]
    assert [s["id"] for s in (await client.get("/api/v1/portal/servicios", headers=h)).json()] == [
        servicio_id
    ]

    await client.post(
        f"/api/v1/portal/servicios/{servicio_id}/cancelacion", json={"motivo": "Viaje"}, headers=h
    )
    assert (await client.get("/api/v1/portal/servicios", headers=h)).json() == []
    pasados = (
        await client.get("/api/v1/portal/servicios", params={"incluir_pasados": True}, headers=h)
    ).json()
    assert [s["estado"] for s in pasados] == ["cancelado"]

    # Lo cancelado ya no se mueve ni se vuelve a cancelar desde el portal.
    otra_vez = await client.post(
        f"/api/v1/portal/servicios/{servicio_id}/cancelacion", json={"motivo": "Viaje"}, headers=h
    )
    assert otra_vez.status_code == 422
    mover = await client.post(
        f"/api/v1/portal/servicios/{servicio_id}/reprogramacion",
        json={"inicio": _hora(10), "motivo": "Otro dia"},
        headers=h,
    )
    assert mover.status_code == 422 and "reprogramar" in mover.json()["detail"]


async def test_actualizar_sin_cambios_se_rechaza(client, portal):
    resp = await client.patch("/api/v1/portal/mi-familia", json={}, headers=portal["headers"])
    assert resp.status_code == 422 and "cambios" in resp.json()["detail"]


async def test_adjuntos_solo_de_su_historia_firmada(client, db, portal, almacenamiento):
    from uuid import uuid4

    medico = await crear_usuario(db, "vet@timu.co", Rol.MEDICO)
    firmada = await db.run_sync(
        clinica.crear_entrada,
        portal["mascota_id"],
        {"motivo": "Control", "diagnostico": "Sano"},
        medico.id,
    )
    await db.run_sync(clinica.firmar, firmada, medico.id)
    borrador = await db.run_sync(
        clinica.crear_entrada, portal["mascota_id"], {"motivo": "Borrador"}, medico.id
    )
    pdf = b"%PDF-1.4 examen"
    adjunto = await db.run_sync(
        lambda s: clinica.adjuntar(
            s, firmada, pdf, nombre="examen.pdf", descripcion="Hemograma", usuario_id=medico.id
        )
    )
    oculto = await db.run_sync(
        lambda s: clinica.adjuntar(
            s, borrador, pdf, nombre="borrador.pdf", descripcion=None, usuario_id=medico.id
        )
    )
    ids = {
        "firmada": firmada.id,
        "borrador": borrador.id,
        "adjunto": adjunto.id,
        "oculto": oculto.id,
    }
    await db.commit()
    h = portal["headers"]

    lista = (
        await client.get(f"/api/v1/portal/historias/{ids['firmada']}/adjuntos", headers=h)
    ).json()
    assert [(a["nombre"], a["descripcion"]) for a in lista] == [("examen.pdf", "Hemograma")]
    assert (
        await client.get(f"/api/v1/portal/historias/{ids['borrador']}/adjuntos", headers=h)
    ).status_code == 404
    assert (
        await client.get(f"/api/v1/portal/historias/{uuid4()}/adjuntos", headers=h)
    ).status_code == 404

    url = (await client.get(f"/api/v1/portal/adjuntos/{ids['adjunto']}/url", headers=h)).json()
    assert url["nombre"] == "examen.pdf" and url["url"].startswith("https://")
    assert (
        await client.get(f"/api/v1/portal/adjuntos/{ids['oculto']}/url", headers=h)
    ).status_code == 404
    assert (
        await client.get(f"/api/v1/portal/adjuntos/{uuid4()}/url", headers=h)
    ).status_code == 404


async def test_adjuntos_de_otra_familia_no(client, db, portal):
    medico = await crear_usuario(db, "vet@timu.co", Rol.MEDICO)
    ajena = await db.run_sync(
        clinica.crear_entrada,
        portal["mascota_ajena_id"],
        {"motivo": "Control", "diagnostico": "Sano"},
        medico.id,
    )
    await db.run_sync(clinica.firmar, ajena, medico.id)
    adjunto = await db.run_sync(
        lambda s: clinica.adjuntar(
            s, ajena, b"%PDF-1.4 x", nombre="ajeno.pdf", descripcion=None, usuario_id=medico.id
        )
    )
    ids = (ajena.id, adjunto.id)
    await db.commit()
    h = portal["headers"]
    assert (
        await client.get(f"/api/v1/portal/historias/{ids[0]}/adjuntos", headers=h)
    ).status_code == 404
    assert (await client.get(f"/api/v1/portal/adjuntos/{ids[1]}/url", headers=h)).status_code == 404


async def test_codigo_sin_plantilla_o_para_numeros_que_no_son_de_una_cuenta(client, db, portal):
    client.cookies.clear()
    # Sin la plantilla aprobada el codigo no sale, pero la respuesta no lo delata.
    assert (
        await client.post("/api/v1/auth/codigo", json={"telefono": "300 111 0001"})
    ).status_code == 202
    assert await db.scalar(select(Mensaje).where(Mensaje.plantilla == "codigo_ingreso")) is None
    for telefono in ("3009990000", "no es un celular"):
        resp = await client.post(
            "/api/v1/auth/codigo/verificacion", json={"telefono": telefono, "codigo": "123456"}
        )
        assert resp.status_code == 401, telefono


# --- 6.1 Fotos de sus mascotas ----------------------------------------------------------------

FOTO = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


async def test_la_familia_sube_cambia_y_quita_la_foto_de_su_mascota(client, portal, almacenamiento):
    h = portal["headers"]
    url = f"/api/v1/portal/mascotas/{portal['mascota_id']}/foto"
    for nombre in ("luna.png", "luna2.png"):
        resp = await client.put(url, files={"foto": (nombre, FOTO, "image/png")}, headers=h)
        assert resp.status_code == 200, resp.text
        assert "firma=" in resp.json()["foto_url"]
    ficha = (await client.get("/api/v1/portal/mi-familia", headers=h)).json()
    assert "firma=" in ficha["mascotas"][0]["foto_url"]

    quitada = await client.delete(url, headers=h)
    assert quitada.status_code == 200 and quitada.json()["foto_url"] is None
    # El tipo se valida igual que en el panel.
    disfrazada = await client.put(url, files={"foto": ("x.png", b"<svg/>", "image/png")}, headers=h)
    assert disfrazada.status_code == 422


async def test_la_familia_no_toca_la_foto_de_una_mascota_ajena_ni_de_baja(
    client, portal, db, almacenamiento
):
    h = portal["headers"]
    ajena = f"/api/v1/portal/mascotas/{portal['mascota_ajena_id']}/foto"
    resp = await client.put(ajena, files={"foto": ("x.png", FOTO, "image/png")}, headers=h)
    assert resp.status_code == 404
    assert (await client.delete(ajena, headers=h)).status_code == 404

    propia = await db.get(Mascota, portal["mascota_id"])
    propia.activa = False
    propia.dada_de_baja_en = datetime.now(ZONA_NEGOCIO)
    propia.motivo_baja = "Fallecio"
    await db.commit()
    resp = await client.put(
        f"/api/v1/portal/mascotas/{portal['mascota_id']}/foto",
        files={"foto": ("x.png", FOTO, "image/png")},
        headers=h,
    )
    assert resp.status_code == 404


async def test_la_base_no_deja_a_la_familia_cambiar_una_mascota_ajena(db, portal):
    """Si Python fallara, RLS sigue filtrando: la familia solo actualiza sus mascotas."""

    def como_familia(s) -> tuple[int, int]:
        fijar_contexto(
            s,
            ContextoDb(
                rol="familia", usuario_id=portal["usuario_id"], familia_id=portal["familia_id"]
            ),
        )
        consulta = text("UPDATE mascotas SET foto_archivo_id = NULL WHERE id = :m")
        ajena = s.execute(consulta, {"m": portal["mascota_ajena_id"]}).rowcount
        propia = s.execute(consulta, {"m": portal["mascota_id"]}).rowcount
        return ajena, propia

    assert await db.run_sync(como_familia) == (0, 1)


async def test_el_equipo_quita_la_foto_de_una_mascota(client, portal, headers, almacenamiento):
    url = f"/api/v1/mascotas/{portal['mascota_id']}/foto"
    await client.put(url, files={"foto": ("x.png", FOTO, "image/png")}, headers=headers)
    resp = await client.delete(url, headers=headers)
    assert resp.status_code == 200 and resp.json()["foto_url"] is None
