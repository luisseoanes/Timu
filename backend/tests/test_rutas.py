"""F2-RUT-01..06 Planeacion, optimizacion con ventanas y capacidad, ejecucion, cambios en
caliente y avisos de llegada."""

from datetime import datetime, time, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from app.core.config import settings
from app.core.enums import Rol
from app.core.tiempo import ZONA_NEGOCIO, hoy
from app.integrations import mapas
from app.integrations.routing import Visita, insertar_mas_barato, optimizar
from app.modules.comunicaciones.models import Mensaje, PlantillaWhatsApp
from app.modules.rutas import distancias, service
from app.modules.rutas.models import ConsumoMapas, DistanciaCache, ParadaRuta, Ruta
from app.modules.servicios import service as servicios
from app.modules.servicios.models import Franja, Servicio
from tests import fabricas
from tests.conftest import crear_usuario, login

DIA = hoy() + timedelta(days=3)
# Casas en Cali alrededor de la base (3.4516, -76.5320).
CASAS = [(3.4600, -76.5300), (3.4700, -76.5250), (3.4400, -76.5400), (3.4550, -76.5100)]
H = 3600


# --- Optimizador (sin base de datos) ----------------------------------------------------------


@pytest.mark.unit
def test_optimizador_respeta_ventanas():
    # Tres visitas a 10 minutos entre si; las ventanas obligan el orden 3, 1, 2.
    tiempos = [[0 if i == j else 600 for j in range(4)] for i in range(4)]
    visitas = [
        Visita(10 * H, 10 * H + 1800, 1800),
        Visita(11 * H, 11 * H + 1800, 1800),
        Visita(8 * H, 8 * H + 1800, 1800),
    ]
    plan = optimizar(tiempos, visitas, vehiculos=1, capacidad=8, jornada=(7 * H, 19 * H))
    assert [nodo for nodo, _ in plan.rutas[0]] == [3, 1, 2]
    for nodo, llegada in plan.rutas[0]:
        assert visitas[nodo - 1].inicio_min <= llegada <= visitas[nodo - 1].inicio_max
    assert plan.descartados == []


@pytest.mark.unit
def test_optimizador_respeta_capacidad_y_descarta_lo_imposible():
    tiempos = [[0 if i == j else 300 for j in range(4)] for i in range(4)]
    visitas = [
        Visita(9 * H, 12 * H, 1200),
        Visita(9 * H, 12 * H, 1200),
        Visita(23 * H, 23 * H + 60, 1200),  # fuera de la jornada
    ]
    plan = optimizar(tiempos, visitas, vehiculos=2, capacidad=1, jornada=(7 * H, 19 * H))
    assert sorted(len(r) for r in plan.rutas) == [1, 1]
    assert plan.descartados == [3]


@pytest.mark.unit
def test_insercion_mas_barata_respeta_lo_recorrido():
    # Base 0, paradas 1 y 2 en linea; la nueva (3) queda entre ellas.
    t = [
        [0, 100, 300, 200],
        [100, 0, 200, 100],
        [300, 200, 0, 100],
        [200, 100, 100, 0],
    ]
    assert insertar_mas_barato(t, [1, 2], 3) == 1
    # Si la primera ya se recorrio, no se inserta antes de ella.
    assert insertar_mas_barato(t, [1, 2], 3, desde=1) >= 1


# --- Datos ------------------------------------------------------------------------------------


@pytest.fixture
async def agenda(db):
    db.add(
        Franja(
            ciudad="Cali",
            modalidad="domiciliario",
            dia_semana=DIA.weekday(),
            hora_inicio=time(8),
            hora_fin=time(17),
            capacidad=10,
        )
    )
    await db.flush()


async def _servicio(db, casa, hora: int, telefono: str) -> Servicio:
    familia, _ = await fabricas.afiliada(db, hoy(), telefono=telefono)
    if casa is not None:
        familia.latitud, familia.longitud = casa
    tipo = await db.run_sync(servicios.tipo_servicio, "consulta_domiciliaria")
    return await db.run_sync(
        lambda s: servicios.agendar(
            s,
            familia=familia,
            mascota=familia.mascotas[0],
            tipo=tipo,
            inicio=datetime.combine(DIA, time(hora), ZONA_NEGOCIO),
        )
    )


@pytest.fixture
async def dia_con_servicios(db, agenda) -> list[Servicio]:
    return [
        await _servicio(db, CASAS[0], 9, "+573001000001"),
        await _servicio(db, CASAS[1], 11, "+573001000002"),
        await _servicio(db, CASAS[2], 14, "+573001000003"),
        await _servicio(db, None, 10, "+573001000004"),  # sin ubicacion
    ]


@pytest.fixture
async def tecnico(db):
    return await crear_usuario(db, "tecnico@timu.co", Rol.MEDICO)


async def _planificar(db, responsables) -> object:
    p = await db.run_sync(service.solicitar, DIA, "Cali", responsables, None)
    return await db.run_sync(service.planificar, p.id)


def _plantilla(db, nombre: str, variables: int) -> None:
    db.add(
        PlantillaWhatsApp(
            nombre=nombre,
            cuerpo=" ".join(f"{{{{{i}}}}}" for i in range(1, variables + 1)),
            variables=[f"v{i}" for i in range(1, variables + 1)],
            estado_aprobacion="aprobada",
            activa=True,
        )
    )


# --- F2-RUT-01..03 Planeacion -----------------------------------------------------------------


async def test_planificacion_se_encola_al_worker(client: AsyncClient, db, headers, tecnico, tareas):
    resp = await client.post(
        "/api/v1/rutas/planificaciones",
        json={"fecha": str(DIA), "ciudad": "Cali", "responsables": [str(tecnico.id)]},
        headers=headers,
    )
    assert resp.status_code == 202, resp.text
    assert resp.json()["estado"] == "pendiente"
    assert await tareas.de("rutas.planificar") == [(resp.json()["id"],)]


async def test_planificar_agrupa_ordena_y_reporta_lo_que_no_cabe(db, dia_con_servicios, tecnico):
    planificacion = await _planificar(db, [tecnico.id])
    assert planificacion.estado == "lista"
    assert planificacion.resultado["asignados"] == 3
    sin = planificacion.resultado["sin_asignar"]
    assert sin == [{"servicio_id": str(dia_con_servicios[3].id), "motivo": "sin_ubicacion"}]

    (ruta,) = list(await db.scalars(select(Ruta)))
    assert ruta.responsable_id == tecnico.id
    assert [p.servicio_id for p in ruta.paradas] == [s.id for s in dia_con_servicios[:3]]
    for parada, servicio in zip(ruta.paradas, dia_con_servicios, strict=False):
        assert servicio.programado_para <= parada.llegada_estimada
        limite = servicio.programado_para + timedelta(minutes=settings.RUTA_VENTANA_LLEGADA_MIN)
        assert parada.llegada_estimada <= limite
        assert servicio.ruta_id == ruta.id and servicio.profesional_id == tecnico.id
    assert ruta.distancia_km > 0


async def test_dos_tecnicos_se_reparten_la_carga(db, dia_con_servicios, tecnico, monkeypatch):
    otro = await crear_usuario(db, "tecnico2@timu.co", Rol.MEDICO)
    monkeypatch.setattr(settings, "RUTA_MAX_ATENCIONES", 2)
    planificacion = await _planificar(db, [tecnico.id, otro.id])
    assert planificacion.resultado["asignados"] == 3
    rutas = list(await db.scalars(select(Ruta)))
    assert sorted(len(r.paradas) for r in rutas) == [1, 2]


async def test_planificar_avisa_la_ventana_de_llegada(db, dia_con_servicios, tecnico):
    _plantilla(db, service.PLANTILLA_VENTANA, 3)
    await _planificar(db, [tecnico.id])
    avisos = list(
        await db.scalars(select(Mensaje).where(Mensaje.plantilla == service.PLANTILLA_VENTANA))
    )
    assert len(avisos) == 3
    paradas = list(await db.scalars(select(ParadaRuta)))
    assert all(p.aviso_ventana_en is not None for p in paradas)


# --- F2-RUT-02 Distancias con cache y tope ----------------------------------------------------


async def test_distancias_se_cachean_y_respetan_el_tope(db, monkeypatch):
    llamadas = []

    def consultar(origenes, destinos):
        llamadas.append(len(destinos))
        return [[(1000, 120) for _ in destinos] for _ in origenes]

    monkeypatch.setattr(mapas, "configurado", lambda: True)
    monkeypatch.setattr(mapas, "consultar", consultar)
    puntos = CASAS[:3]

    _, segundos = await db.run_sync(distancias.matriz, puntos)
    assert segundos[0][1] == 120 and sum(llamadas) == 6
    await db.run_sync(distancias.matriz, puntos)
    assert sum(llamadas) == 6  # todo salio de la cache
    assert await db.scalar(select(func.count()).select_from(DistanciaCache)) == 6

    monkeypatch.setattr(settings, "MAPS_TOPE_DIARIO", 7)
    _, segundos = await db.run_sync(distancias.matriz, [*puntos, CASAS[3]])
    consumo = await db.scalar(select(ConsumoMapas))
    assert consumo.elementos <= 7
    # Lo que no cupo en el tope se estimo, y la matriz quedo completa.
    assert all(segundos[i][j] > 0 for i in range(4) for j in range(4) if i != j)


async def test_sin_proveedor_se_estima(db):
    _, segundos = await db.run_sync(distancias.matriz, CASAS[:2])
    assert 60 < segundos[0][1] < 1800
    assert await db.scalar(select(func.count()).select_from(DistanciaCache)) == 0


# --- F2-RUT-04 Ejecucion ----------------------------------------------------------------------


async def test_ejecucion_mueve_el_servicio_y_cierra_la_ruta(
    client: AsyncClient, db, dia_con_servicios, tecnico, almacenamiento
):
    _plantilla(db, service.PLANTILLA_EN_CAMINO, 2)
    await _planificar(db, [tecnico.id])
    ruta = await db.scalar(select(Ruta))
    ruta_id, paradas = ruta.id, [(p.id, p.servicio_id) for p in ruta.paradas]
    await db.commit()
    campo = await login(client, tecnico.email)

    assert (await client.post(f"/api/v1/rutas/{ruta_id}/inicio", headers=campo)).status_code == 200
    for parada_id, servicio_id in paradas:
        base = f"/api/v1/rutas/paradas/{parada_id}"
        r = await client.post(f"{base}/en-camino", headers=campo)
        assert r.status_code == 200, r.text
        assert (await client.post(f"{base}/llegada", headers=campo)).status_code == 200
        sin_pasos = await client.post(f"{base}/salida", data={"nota": "ok"}, headers=campo)
        assert sin_pasos.status_code == 422  # faltan los pasos obligatorios de la consulta
        for paso, campos in (
            ("valoracion", {"hallazgos": "Sano"}),
            ("plan", {"recomendaciones": "Ninguna"}),
        ):
            await client.put(
                f"/api/v1/servicios/{servicio_id}/pasos/{paso}",
                json={"datos": campos},
                headers=campo,
            )
        cierre = await client.post(
            f"{base}/salida",
            data={"nota": "Atendido"},
            files={"evidencia": ("foto.png", b"\x89PNG\r\n\x1a\n" + b"0" * 32, "image/png")},
            headers=campo,
        )
        assert cierre.status_code == 200, cierre.text

    final = (await client.get(f"/api/v1/rutas/{ruta_id}", headers=campo)).json()
    assert final["estado"] == "finalizada"
    assert all(p["estado"] == "completada" and p["salida_en"] for p in final["paradas"])
    estados = set(await db.scalars(select(Servicio.estado).where(Servicio.ruta_id == ruta_id)))
    assert estados == {"completado"}
    # F2-RUT-06 Cada familia recibio el aviso de "en camino".
    assert (
        await db.scalar(
            select(func.count())
            .select_from(Mensaje)
            .where(Mensaje.plantilla == service.PLANTILLA_EN_CAMINO)
        )
        == 3
    )


async def test_no_se_sale_hacia_dos_paradas_a_la_vez(db, dia_con_servicios, tecnico):
    await _planificar(db, [tecnico.id])
    ruta = await db.scalar(select(Ruta))
    await db.run_sync(service.iniciar, ruta, tecnico.id)
    primera, segunda = ruta.paradas[0], ruta.paradas[1]
    await db.run_sync(service.en_camino, primera, tecnico.id)
    from app.core.errores import ReglaNegocio

    with pytest.raises(ReglaNegocio):
        await db.run_sync(service.en_camino, segunda, tecnico.id)


# --- F2-RUT-05 Cambios en caliente ------------------------------------------------------------


async def test_omitir_renumera_y_libera_el_servicio(db, dia_con_servicios, tecnico):
    await _planificar(db, [tecnico.id])
    ruta = await db.scalar(select(Ruta))
    del_medio = ruta.paradas[1]
    await db.run_sync(
        lambda s: service.omitir(
            s, del_medio, "La familia no esta", cancelar_servicio=False, usuario_id=tecnico.id
        )
    )
    activas = [p for p in ruta.paradas if p.estado != "omitida"]
    assert [p.orden for p in sorted(activas, key=lambda p: p.orden)] == [1, 2]
    liberado = await db.get(Servicio, del_medio.servicio_id)
    assert liberado.ruta_id is None and liberado.estado == "agendado"


async def test_agregar_inserta_donde_menos_cuesta(db, agenda, tecnico):
    s1 = await _servicio(db, CASAS[0], 9, "+573001000001")
    s3 = await _servicio(db, (3.4800, -76.5200), 13, "+573001000003")
    await _planificar(db, [tecnico.id])
    ruta = await db.scalar(select(Ruta))
    # La nueva casa queda en medio del camino entre las dos anteriores.
    nuevo = await _servicio(db, (3.4700, -76.5250), 11, "+573001000002")
    parada = await db.run_sync(service.agregar, ruta, nuevo.id)
    orden = [p.servicio_id for p in sorted(ruta.paradas, key=lambda p: p.orden)]
    assert orden == [s1.id, nuevo.id, s3.id]
    assert parada.llegada_estimada is not None and nuevo.ruta_id == ruta.id


async def test_agregar_respeta_la_capacidad(db, dia_con_servicios, tecnico, monkeypatch):
    monkeypatch.setattr(settings, "RUTA_MAX_ATENCIONES", 3)
    await _planificar(db, [tecnico.id])
    ruta = await db.scalar(select(Ruta))
    extra = await _servicio(db, CASAS[3], 15, "+573001000009")
    from app.core.errores import ReglaNegocio

    with pytest.raises(ReglaNegocio, match="maximo"):
        await db.run_sync(service.agregar, ruta, extra.id)


async def test_cancelar_ruta_devuelve_los_servicios(db, dia_con_servicios, tecnico):
    await _planificar(db, [tecnico.id])
    ruta = await db.scalar(select(Ruta))
    await db.run_sync(service.cancelar, ruta)
    pendientes = await db.run_sync(service.por_rutear, DIA, "Cali")
    assert len(pendientes) == 4
