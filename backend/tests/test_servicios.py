"""F1-SER-01..06 Servicios, elegibilidad, estados, pendientes y bandeja de tareas."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.tiempo import ZONA_NEGOCIO, hoy
from app.modules.servicios.models import Franja, Pendiente, Servicio
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


async def test_bandeja_desempata_por_vencimiento_con_las_sin_fecha_al_final(
    client: AsyncClient, headers
):
    """Mismo orden que sirve el indice ix_tareas_bandeja: prioridad y luego vencimiento."""
    for titulo, prioridad, dias in (
        ("Sin fecha", "alta", None),
        ("En una semana", "alta", 7),
        ("Manana", "alta", 1),
        ("Baja hoy", "baja", 0),
    ):
        await client.post(
            "/api/v1/tareas",
            json={
                "titulo": titulo,
                "area": "operaciones",
                "prioridad": prioridad,
                "vence_en_dias": dias,
            },
            headers=headers,
        )
    bandeja = (await client.get("/api/v1/tareas", headers=headers)).json()
    assert [t["titulo"] for t in bandeja["items"]] == [
        "Manana",
        "En una semana",
        "Sin fecha",
        "Baja hoy",
    ]


# --- Agenda: franjas (F1-SER-02) y listados ---------------------------------------------------


async def test_operaciones_crea_franjas_con_la_ciudad_del_catalogo(client: AsyncClient, db):
    from app.core.enums import Rol
    from tests.conftest import crear_usuario, login

    await crear_usuario(db, "ops@timu.co", Rol.OPERACIONES)
    cabecera = await login(client, "ops@timu.co")
    franja = {
        "modalidad": "domiciliario",
        "dia_semana": 2,
        "hora_inicio": "08:00",
        "hora_fin": "12:00",
    }

    creada = await client.post(
        "/api/v1/agenda/franjas", json={**franja, "ciudad": " cali "}, headers=cabecera
    )
    assert creada.status_code == 201
    assert (creada.json()["ciudad"], creada.json()["capacidad"]) == ("Cali", 1)

    fuera = await client.post(
        "/api/v1/agenda/franjas", json={**franja, "ciudad": "Gotham"}, headers=cabecera
    )
    assert fuera.status_code == 422 and "catalogo" in fuera.json()["detail"]
    al_reves = await client.post(
        "/api/v1/agenda/franjas",
        json={**franja, "ciudad": "Cali", "hora_inicio": "12:00", "hora_fin": "08:00"},
        headers=cabecera,
    )
    assert al_reves.status_code == 422


async def test_un_medico_consulta_franjas_pero_no_las_administra(client: AsyncClient, db, agenda):
    from app.core.enums import Rol
    from tests.conftest import crear_usuario, login

    await crear_usuario(db, "vet@timu.co", Rol.MEDICO)
    cabecera = await login(client, "vet@timu.co")
    assert len((await client.get("/api/v1/agenda/franjas", headers=cabecera)).json()) == 2
    nueva = await client.post(
        "/api/v1/agenda/franjas",
        json={
            "ciudad": "Cali",
            "modalidad": "virtual",
            "dia_semana": 0,
            "hora_inicio": "08:00",
            "hora_fin": "09:00",
        },
        headers=cabecera,
    )
    assert nueva.status_code == 403


async def test_franjas_se_filtran_por_ciudad_y_se_ajustan(client: AsyncClient, headers, db, agenda):
    db.add(
        Franja(
            ciudad="Bogota",
            modalidad="domiciliario",
            dia_semana=0,
            hora_inicio=time(8),
            hora_fin=time(9),
        )
    )
    await db.flush()
    todas = (await client.get("/api/v1/agenda/franjas", headers=headers)).json()
    cali = (
        await client.get("/api/v1/agenda/franjas", params={"ciudad": "Cali"}, headers=headers)
    ).json()
    assert len(todas) == 3 and {f["ciudad"] for f in cali} == {"Cali"}

    url = f"/api/v1/agenda/franjas/{cali[0]['id']}"
    ajustada = (await client.patch(url, params={"capacidad": 4}, headers=headers)).json()
    assert (ajustada["capacidad"], ajustada["activa"]) == (4, True)
    apagada = (await client.patch(url, params={"activa": False}, headers=headers)).json()
    assert (apagada["capacidad"], apagada["activa"]) == (4, False), "cambiar uno no toca el otro"

    from uuid import uuid4

    inexistente = await client.patch(
        f"/api/v1/agenda/franjas/{uuid4()}", params={"activa": True}, headers=headers
    )
    assert inexistente.status_code == 404


async def test_listado_de_servicios_combina_filtros(client: AsyncClient, db, headers, afiliada):
    servicio = (await _agendar(client, headers, afiliada)).json()
    otra, _ = await fabricas.afiliada(db, hoy())
    await db.commit()
    await _agendar(client, headers, ids(otra), inicio=_hora(10))

    def contar(**filtros):
        return client.get("/api/v1/servicios", params=filtros, headers=headers)

    assert (await contar()).json()["total"] == 2
    propios = (await contar(familia_id=str(afiliada.id))).json()
    assert [s["id"] for s in propios["items"]] == [servicio["id"]]
    assert (await contar(estado="agendado", ciudad="Cali")).json()["total"] == 2
    assert (await contar(estado="completado")).json()["total"] == 0
    assert (await contar(ciudad="Bogota")).json()["total"] == 0
    assert (await contar(desde=str(DIA), hasta=str(DIA))).json()["total"] == 2
    assert (await contar(desde=str(DIA + timedelta(days=1)))).json()["total"] == 0
    assert (await contar(hasta=str(DIA - timedelta(days=1)))).json()["total"] == 0
    recientes = (await contar(orden="-programado_para")).json()["items"]
    assert recientes[0]["programado_para"] > recientes[1]["programado_para"]


async def test_un_servicio_inexistente_da_404_tambien_en_sus_pasos(
    client: AsyncClient, headers, afiliada
):
    from uuid import uuid4

    servicio = (await _agendar(client, headers, afiliada)).json()
    assert (await client.get(f"/api/v1/servicios/{servicio['id']}", headers=headers)).json()[
        "id"
    ] == servicio["id"]
    assert (
        await client.get(f"/api/v1/servicios/{servicio['id']}/pasos", headers=headers)
    ).json() == []
    assert (await client.get(f"/api/v1/servicios/{uuid4()}", headers=headers)).status_code == 404
    assert (
        await client.get(f"/api/v1/servicios/{uuid4()}/pasos", headers=headers)
    ).status_code == 404


async def test_pendientes_se_filtran_por_estado_y_servicio(client: AsyncClient, headers, afiliada):
    primero = (await _agendar(client, headers, afiliada)).json()
    segundo = (await _agendar(client, headers, afiliada, inicio=_hora(10))).json()
    for servicio, descripcion in ((primero, "Radiografia"), (segundo, "Ecografia")):
        await client.post(
            f"/api/v1/servicios/{servicio['id']}/pendientes",
            json={"descripcion": descripcion},
            headers=headers,
        )

    def pendientes(**filtros):
        return client.get("/api/v1/pendientes", params=filtros, headers=headers)

    assert [p["descripcion"] for p in (await pendientes()).json()] == ["Radiografia", "Ecografia"]
    del_segundo = (await pendientes(servicio_id=segundo["id"])).json()
    assert [p["descripcion"] for p in del_segundo] == ["Ecografia"]
    assert len((await pendientes(estado="pendiente_autorizacion")).json()) == 2
    assert (await pendientes(estado="resuelto")).json() == []


# --- Bandeja de tareas: filtros y ciclo ----------------------------------------------------------


async def test_la_bandeja_combina_area_estado_asignacion_vencimiento_y_familia(
    client: AsyncClient, db, admin, headers, afiliada
):
    async def crear(titulo: str, area: str = "operaciones", **extra) -> str:
        resp = await client.post(
            "/api/v1/tareas", json={"titulo": titulo, "area": area, **extra}, headers=headers
        )
        assert resp.status_code == 201, resp.text
        return resp.json()["id"]

    de_la_familia = await crear("Llamar a la familia", familia_id=str(afiliada.id))
    await crear("Cotizar plan", area="comercial", asignada_a_id=str(admin.id))
    vencida = await crear("Revisar ruta", vence_en_dias=0)
    tarea = await db.get(Tarea, UUID(vencida))
    tarea.vence_el = hoy() - timedelta(days=2)
    await db.commit()

    async def titulos(**filtros) -> set[str]:
        resp = await client.get("/api/v1/tareas", params=filtros, headers=headers)
        return {t["titulo"] for t in resp.json()["items"]}

    assert await titulos(area="comercial") == {"Cotizar plan"}
    assert await titulos(sin_asignar=True) == {"Llamar a la familia", "Revisar ruta"}
    assert await titulos(mias=True) == {"Cotizar plan"}
    assert await titulos(vencidas=True) == {"Revisar ruta"}
    assert await titulos(familia_id=str(afiliada.id)) == {"Llamar a la familia"}

    iniciada = (
        await client.post(f"/api/v1/tareas/{de_la_familia}/iniciar", headers=headers)
    ).json()
    assert iniciada["estado"] == "en_progreso"
    assert (
        await client.post(f"/api/v1/tareas/{de_la_familia}/iniciar", headers=headers)
    ).status_code == 422
    assert await titulos(estado="en_progreso") == {"Llamar a la familia"}

    await client.post(
        f"/api/v1/tareas/{vencida}/cerrar", json={"resolucion": "Ruta revisada"}, headers=headers
    )
    assert await titulos(vencidas=True) == set(), "una tarea cerrada ya no esta vencida"
    reasignar = await client.patch(
        f"/api/v1/tareas/{vencida}/asignacion", json={"usuario_id": str(admin.id)}, headers=headers
    )
    assert reasignar.status_code == 422 and "cerrada" in reasignar.json()["detail"]


async def test_una_tarea_inexistente_da_404(client: AsyncClient, headers):
    from uuid import uuid4

    assert (
        await client.post(f"/api/v1/tareas/{uuid4()}/iniciar", headers=headers)
    ).status_code == 404


# --- 6.1 Resumen de servicios de la familia --------------------------------------------------


MES = hoy().replace(day=1)
FIN_MES = (MES + timedelta(days=32)).replace(day=1) - timedelta(days=1)
MES_PASADO = (MES - timedelta(days=1)).replace(day=1)


def _rango(desde: date, hasta: date) -> str:
    return f"desde={desde.isoformat()}&hasta={hasta.isoformat()}"


async def _familia_con_servicios(db):
    """Dos mascotas y servicios en el mes en curso y el anterior, en los estados que cuentan.
    Las fechas son relativas a hoy: el cupo y el rango por defecto dependen del mes."""
    plan = await db.run_sync(
        fabricas.plan,
        codigo="resumen",
        cupos=2,
        beneficios=[
            {"tipo_servicio_codigo": "consulta_domiciliaria", "cupo": 5, "periodo_cupo": "mensual"}
        ],
    )
    familia, _ = await fabricas.afiliada(db, hoy(), p=plan, mascotas=2)
    luna, max_ = familia.mascotas

    def servicio(estado: str, dia: date | None, mascota) -> Servicio:
        s = Servicio(
            familia_id=familia.id,
            mascota_id=mascota.id,
            tipo_codigo="consulta_domiciliaria",
            tipo="domiciliario",
            estado=estado,
            ciudad=familia.ciudad,
            programado_para=datetime.combine(dia, time(10), ZONA_NEGOCIO) if dia else None,
            motivo_estado="La familia cancelo" if estado == "cancelado" else None,
        )
        db.add(s)
        return s

    hecho = servicio("completado", MES.replace(day=5), luna)
    servicio("agendado", MES.replace(day=20), luna)
    servicio("pendiente_autorizacion", MES.replace(day=25), max_)
    servicio("cancelado", MES.replace(day=12), max_)
    servicio("completado", MES_PASADO.replace(day=28), luna)  # fuera del mes en curso
    servicio("solicitado", None, max_)  # sin fecha: cuenta la de la solicitud (hoy)
    await db.flush()
    db.add(Pendiente(servicio_origen_id=hecho.id, descripcion="Ecografia abdominal"))
    db.add(Pendiente(servicio_origen_id=hecho.id, descripcion="Ya resuelto", estado="resuelto"))
    await db.commit()
    return familia.id, luna.id, max_.id


async def test_el_resumen_separa_utilizados_y_pendientes_en_el_rango(
    client: AsyncClient, db, headers
):
    familia_id, luna_id, _ = await _familia_con_servicios(db)
    url = f"/api/v1/servicios/resumen?familia_id={familia_id}&{_rango(MES, FIN_MES)}"
    datos = (await client.get(url, headers=headers)).json()
    assert [s["estado"] for s in datos["utilizados"]] == ["completado"]
    assert {s["estado"] for s in datos["pendientes"]} == {
        "agendado",
        "pendiente_autorizacion",
        "solicitado",
    }
    assert datos["cancelados"] == []
    assert (datos["desde"], datos["hasta"]) == (MES.isoformat(), FIN_MES.isoformat())

    con_cancelados = (await client.get(url + "&incluir_cancelados=true", headers=headers)).json()
    assert [s["estado"] for s in con_cancelados["cancelados"]] == ["cancelado"]

    de_luna = (await client.get(url + f"&mascota_id={luna_id}", headers=headers)).json()
    assert len(de_luna["utilizados"]) == 1
    assert [s["estado"] for s in de_luna["pendientes"]] == ["agendado"]
    assert de_luna["pendientes_atencion"][0]["descripcion"] == "Ecografia abdominal"

    pasado = (
        await client.get(
            f"/api/v1/servicios/resumen?familia_id={familia_id}"
            f"&{_rango(MES_PASADO, MES - timedelta(days=1))}",
            headers=headers,
        )
    ).json()
    assert [s["estado"] for s in pasado["utilizados"]] == ["completado"]
    assert pasado["pendientes"] == []
    # El pendiente se creo hoy: fuera del rango del mes pasado.
    assert pasado["pendientes_atencion"] == []


async def test_el_resumen_por_defecto_es_el_mes_en_curso_con_lo_abierto_de_una_atencion(
    client: AsyncClient, db, headers
):
    familia_id, _, max_id = await _familia_con_servicios(db)
    datos = (
        await client.get(f"/api/v1/servicios/resumen?familia_id={familia_id}", headers=headers)
    ).json()
    assert (datos["desde"], datos["hasta"]) == (MES.isoformat(), FIN_MES.isoformat())
    assert len(datos["utilizados"]) == 1 and len(datos["pendientes"]) == 3
    # El pendiente de la atencion sigue abierto; el resuelto no aparece.
    assert [p["descripcion"] for p in datos["pendientes_atencion"]] == ["Ecografia abdominal"]
    # El cupo del mes: lo programado este mes, sin lo cancelado ni lo que no tiene fecha.
    assert datos["cupos"] == [
        {"tipo_codigo": "consulta_domiciliaria", "cupo": 5, "usados": 3, "periodo": "mensual"}
    ]


async def test_el_resumen_rechaza_un_rango_invertido(client: AsyncClient, db, headers):
    familia_id, _, _ = await _familia_con_servicios(db)
    resp = await client.get(
        f"/api/v1/servicios/resumen?familia_id={familia_id}&{_rango(FIN_MES, MES)}",
        headers=headers,
    )
    assert resp.status_code == 422 and "anterior" in resp.text


async def test_el_listado_de_servicios_filtra_por_mascota(client: AsyncClient, db, headers):
    familia_id, luna_id, _ = await _familia_con_servicios(db)
    datos = (
        await client.get(
            f"/api/v1/servicios?familia_id={familia_id}&mascota_id={luna_id}", headers=headers
        )
    ).json()
    assert datos["total"] == 3
    assert {s["mascota_id"] for s in datos["items"]} == {str(luna_id)}
