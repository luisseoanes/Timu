"""F1-SER-01..06 Servicios, elegibilidad, estados, pendientes y bandeja de tareas."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.tiempo import hoy
from app.modules.servicios.models import Franja
from app.modules.tareas.models import Tarea
from tests import fabricas

DIA = hoy() + timedelta(days=7)


def _hora(h: int, m: int = 0, dia: date = DIA) -> str:
    return datetime.combine(dia, time(h, m)).isoformat()  # sin zona: hora de Colombia


@pytest.fixture
async def agenda(db):
    for modalidad in ("domiciliario", "preventivo"):
        db.add(
            Franja(
                ciudad="Cali",
                modalidad=modalidad,
                dia_semana=DIA.weekday(),
                hora_inicio=time(8),
                hora_fin=time(12),
                capacidad=1,
            )
        )
    await db.flush()


@dataclass
class Ids:
    """Solo ids: una peticion fallida revierte la sesion y expira los objetos ORM."""

    id: UUID
    mascota_id: UUID


def ids(familia) -> Ids:
    return Ids(familia.id, familia.mascotas[0].id)


@pytest.fixture
async def afiliada(db, agenda) -> Ids:
    familia, _ = await fabricas.afiliada(db, hoy())
    await db.commit()
    return ids(familia)


async def _agendar(client, headers, familia: Ids, tipo="consulta_domiciliaria", inicio=None):
    return await client.post(
        "/api/v1/servicios",
        json={
            "familia_id": str(familia.id),
            "mascota_id": str(familia.mascota_id),
            "tipo_codigo": tipo,
            "inicio": inicio or _hora(9),
        },
        headers=headers,
    )


# --- F1-SER-01 --------------------------------------------------------------------------------


async def test_disponibilidad_descuenta_lo_agendado(client: AsyncClient, headers, afiliada):
    params = {"fecha": str(DIA), "ciudad": "Cali", "tipo_codigo": "consulta_domiciliaria"}
    antes = (
        await client.get("/api/v1/agenda/disponibilidad", params=params, headers=headers)
    ).json()
    assert len(antes) == 5  # 08:00-12:00 en bloques de 45 minutos
    assert all(c["disponibles"] == 1 for c in antes)

    await _agendar(client, headers, afiliada, inicio=_hora(8, 45))
    despues = (
        await client.get("/api/v1/agenda/disponibilidad", params=params, headers=headers)
    ).json()
    assert [c["disponibles"] for c in despues] == [1, 0, 1, 1, 1]


async def test_rechaza_cupo_tomado(client: AsyncClient, db, headers, afiliada):
    assert (await _agendar(client, headers, afiliada)).status_code == 201
    otra, _ = await fabricas.afiliada(db, hoy(), telefono="+573109998877")
    otra = ids(otra)
    await db.commit()
    # 09:30 se cruza con la atencion de 09:00 a 09:45.
    resp = await _agendar(client, headers, otra, inicio=_hora(9, 30))
    assert resp.status_code == 422
    assert "cupo" in resp.json()["detail"]


async def test_fuera_de_franja_y_dia_bloqueado(client: AsyncClient, headers, afiliada):
    fuera = await _agendar(client, headers, afiliada, inicio=_hora(11, 30))
    assert "No hay agenda" in fuera.json()["detail"]
    await client.post(
        "/api/v1/agenda/bloqueos", json={"fecha": str(DIA), "motivo": "Festivo"}, headers=headers
    )
    bloqueado = await _agendar(client, headers, afiliada)
    assert "Festivo" in bloqueado.json()["detail"]


async def test_no_agenda_en_el_pasado(client: AsyncClient, headers, afiliada):
    resp = await _agendar(client, headers, afiliada, inicio=_hora(9, dia=hoy() - timedelta(days=1)))
    assert resp.status_code == 422


# --- F1-SER-05 --------------------------------------------------------------------------------


async def test_elegibilidad_explica_los_motivos(client: AsyncClient, db, headers, agenda):
    sin_plan = await db.run_sync(fabricas.familia)
    congelada, contrato = await fabricas.afiliada(db, hoy(), telefono="+573109998877")
    contrato.estado = "congelada"
    congelada = ids(congelada)
    await db.commit()

    resp = await client.get(
        "/api/v1/servicios/elegibilidad",
        params={"familia_id": str(sin_plan.id), "tipo_codigo": "consulta_domiciliaria"},
        headers=headers,
    )
    assert resp.json() == {"elegible": False, "motivos": ["La familia no tiene un plan vigente"]}

    agendar = await _agendar(client, headers, congelada)
    assert agendar.status_code == 422
    assert "congelada por mora" in agendar.json()["detail"]


async def test_cupo_del_beneficio(client: AsyncClient, db, headers, agenda):
    p = await db.run_sync(
        fabricas.plan,
        "con_cupo",
        beneficios=[{"tipo_servicio_codigo": "consulta_domiciliaria", "cupo": 1}],
    )
    familia, _ = await fabricas.afiliada(db, hoy(), p)
    familia = ids(familia)
    await db.commit()
    assert (await _agendar(client, headers, familia)).status_code == 201
    segunda = await _agendar(client, headers, familia, inicio=_hora(10, 30))
    assert "Se agoto el cupo" in segunda.json()["detail"]
    no_incluido = await _agendar(client, headers, familia, tipo="vacunacion", inicio=_hora(11))
    assert "no incluye" in no_incluido.json()["detail"]


# --- F1-SER-02 / 03 Estados, autorizacion y pasos ---------------------------------------------


async def test_ciclo_de_vacunacion(client: AsyncClient, db, headers, afiliada, tareas):
    creado = await _agendar(client, headers, afiliada, tipo="vacunacion")
    servicio = creado.json()
    assert servicio["estado"] == "pendiente_autorizacion"
    # La regla servicio_requiere_autorizacion dejo tarea para el equipo medico.
    tarea = await db.scalar(select(Tarea).where(Tarea.servicio_id == UUID(servicio["id"])))
    assert (tarea.area, tarea.prioridad) == ("medico", "alta")

    url = f"/api/v1/servicios/{servicio['id']}"
    sin_autorizar = await client.post(
        f"{url}/estado", json={"estado": "en_atencion"}, headers=headers
    )
    assert sin_autorizar.status_code == 422

    autorizado = await client.post(f"{url}/autorizar", headers=headers)
    assert autorizado.json()["estado"] == "agendado"
    await client.post(f"{url}/estado", json={"estado": "en_atencion"}, headers=headers)

    incompleto = await client.post(f"{url}/estado", json={"estado": "completado"}, headers=headers)
    assert "Aplicacion" in incompleto.json()["detail"]

    paso = await client.put(
        f"{url}/pasos/aplicacion", json={"datos": {"producto": "Nobivac"}}, headers=headers
    )
    assert "lote" in paso.json()["detail"]
    await client.put(
        f"{url}/pasos/aplicacion",
        json={"datos": {"producto": "Nobivac", "lote": "A12"}},
        headers=headers,
    )

    completado = await client.post(f"{url}/estado", json={"estado": "completado"}, headers=headers)
    assert completado.json()["estado"] == "completado"
    assert await tareas.de("encuestas.enviar_encuesta") == [(servicio["id"],)]


async def test_transicion_invalida(client: AsyncClient, headers, afiliada):
    servicio = (await _agendar(client, headers, afiliada)).json()
    resp = await client.post(
        f"/api/v1/servicios/{servicio['id']}/estado", json={"estado": "completado"}, headers=headers
    )
    assert resp.status_code == 422
    assert "No se puede pasar de agendado a completado" in resp.json()["detail"]


async def test_cancelar_exige_motivo_y_libera_cupo(client: AsyncClient, headers, afiliada):
    servicio = (await _agendar(client, headers, afiliada)).json()
    url = f"/api/v1/servicios/{servicio['id']}/estado"
    assert (
        await client.post(url, json={"estado": "cancelado"}, headers=headers)
    ).status_code == 422
    await client.post(url, json={"estado": "cancelado", "motivo": "Viaje"}, headers=headers)
    assert (await _agendar(client, headers, afiliada)).status_code == 201


async def test_reprogramar_dispara_tarea_de_operaciones(client: AsyncClient, db, headers, afiliada):
    servicio = (await _agendar(client, headers, afiliada)).json()
    resp = await client.post(
        f"/api/v1/servicios/{servicio['id']}/reprogramar",
        json={"inicio": _hora(10, 30), "motivo": "La familia no estara"},
        headers=headers,
    )
    assert resp.json()["estado"] == "agendado"
    assert resp.json()["programado_para"].startswith(f"{DIA}T15:30")  # 10:30 Colombia en UTC
    tarea = await db.scalar(select(Tarea).where(Tarea.origen == "servicio_reprogramado"))
    assert tarea.area == "operaciones"


# --- F1-SER-04 Pendientes ---------------------------------------------------------------------


async def test_pendiente_no_avanza_sin_autorizacion(client: AsyncClient, headers, afiliada):
    servicio = (await _agendar(client, headers, afiliada)).json()
    pendiente = (
        await client.post(
            f"/api/v1/servicios/{servicio['id']}/pendientes",
            json={"descripcion": "Radiografia de cadera"},
            headers=headers,
        )
    ).json()
    url = f"/api/v1/pendientes/{pendiente['id']}"
    bloqueado = await client.post(f"{url}/avance", json={"estado": "en_gestion"}, headers=headers)
    assert "sin autorizacion" in bloqueado.json()["detail"]

    autorizado = await client.post(
        f"{url}/autorizacion", json={"medio": "whatsapp"}, headers=headers
    )
    assert autorizado.json()["estado"] == "autorizado"
    assert autorizado.json()["medio_autorizacion"] == "whatsapp"
    await client.post(f"{url}/avance", json={"estado": "en_gestion"}, headers=headers)
    sin_resolucion = await client.post(
        f"{url}/avance", json={"estado": "resuelto"}, headers=headers
    )
    assert sin_resolucion.status_code == 422
    resuelto = await client.post(
        f"{url}/avance", json={"estado": "resuelto", "resolucion": "Sin hallazgos"}, headers=headers
    )
    assert resuelto.json()["estado"] == "resuelto"


async def test_pendiente_rechazado_no_se_agenda(client: AsyncClient, headers, afiliada):
    servicio = (await _agendar(client, headers, afiliada)).json()
    pendiente = (
        await client.post(
            f"/api/v1/servicios/{servicio['id']}/pendientes",
            json={"descripcion": "Control"},
            headers=headers,
        )
    ).json()
    await client.post(
        f"/api/v1/pendientes/{pendiente['id']}/autorizacion",
        json={"medio": "llamada", "aprobado": False},
        headers=headers,
    )
    resp = await client.post(
        "/api/v1/servicios",
        json={
            "familia_id": str(afiliada.id),
            "tipo_codigo": "consulta_domiciliaria",
            "inicio": _hora(10, 30),
            "pendiente_id": pendiente["id"],
        },
        headers=headers,
    )
    assert resp.status_code == 422


# --- F1-SER-06 Bandeja de tareas --------------------------------------------------------------


async def test_bandeja_asigna_prioriza_y_cierra(client: AsyncClient, admin, headers):
    for titulo, prioridad in (("Llamar", "baja"), ("Urgente", "alta"), ("Revisar", "media")):
        await client.post(
            "/api/v1/tareas",
            json={"titulo": titulo, "area": "operaciones", "prioridad": prioridad},
            headers=headers,
        )
    bandeja = (await client.get("/api/v1/tareas", headers=headers)).json()
    assert [t["titulo"] for t in bandeja["items"]] == ["Urgente", "Revisar", "Llamar"]

    tarea_id = bandeja["items"][0]["id"]
    await client.patch(
        f"/api/v1/tareas/{tarea_id}/asignacion", json={"usuario_id": str(admin.id)}, headers=headers
    )
    mias = (await client.get("/api/v1/tareas", params={"mias": True}, headers=headers)).json()
    assert [t["titulo"] for t in mias["items"]] == ["Urgente"]

    cerrada = await client.post(
        f"/api/v1/tareas/{tarea_id}/cerrar",
        json={"resolucion": "Resuelto por telefono"},
        headers=headers,
    )
    assert cerrada.json()["estado"] == "cerrada"
    otra_vez = await client.post(
        f"/api/v1/tareas/{tarea_id}/cerrar", json={"resolucion": "x" * 5}, headers=headers
    )
    assert otra_vez.status_code == 422
