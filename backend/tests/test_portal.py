"""F3-POR-01..07 Portal de familias: datos, historia, carnet, autogestion, pagos,
actualizacion de datos e ingreso con codigo por WhatsApp."""

import re
from datetime import datetime, time, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.auditoria import RegistroAuditoria
from app.core.config import settings
from app.core.enums import Rol
from app.core.security import hash_password
from app.core.tiempo import ZONA_NEGOCIO, hoy
from app.modules.auth.models import Usuario
from app.modules.cartera import pasarela
from app.modules.cartera.models import Pago
from app.modules.clinica import service as clinica
from app.modules.comunicaciones.models import Mensaje, PlantillaWhatsApp
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
    cuenta = (await client.get("/api/v1/portal/estado-cuenta", headers=h)).json()
    assert cuenta["contrato"]["familia_id"] == str(portal["familia_id"])


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
