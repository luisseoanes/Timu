"""6.14 Historia versionada, adjuntos, plantillas y formulas, atencion virtual y
permisos por perfil."""

from datetime import timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.enums import EstadoServicio, Rol, TipoServicio
from app.core.tiempo import ahora, hoy
from app.modules.clinica.models import HistoriaClinica
from app.modules.comunicaciones.models import ConversacionWhatsApp, Mensaje
from app.modules.familias.models import Mascota
from app.modules.servicios import service as servicios
from app.modules.servicios.models import Servicio, ServicioPaso
from tests import fabricas
from tests.conftest import crear_usuario, login

pytestmark = pytest.mark.integration

PDF = b"%PDF-1.4\n" + b"0" * 64
CONSULTA = {"motivo": "Vomito desde ayer", "anamnesis": "Comio basura"}


@pytest.fixture
async def equipo(client: AsyncClient, db, admin) -> dict[str, dict[str, str]]:
    """Cabeceras por perfil: dos medicos, operaciones y admin."""
    for email, rol in (
        ("medica@timu.co", Rol.MEDICO),
        ("otro@timu.co", Rol.MEDICO),
        ("op@timu.co", Rol.OPERACIONES),
    ):
        await crear_usuario(db, email, rol)
    return {
        "medica": await login(client, "medica@timu.co"),
        "otro": await login(client, "otro@timu.co"),
        "op": await login(client, "op@timu.co"),
        "admin": await login(client, admin.email),
    }


@pytest.fixture
async def mascota_id(db):
    familia, _ = await fabricas.afiliada(db, hoy())
    mascota_id = familia.mascotas[0].id
    await db.commit()
    return mascota_id


async def _entrada(client, equipo, mascota_id, **extra) -> dict:
    resp = await client.post(
        "/api/v1/clinica/historias",
        json={"mascota_id": str(mascota_id), **CONSULTA, **extra},
        headers=equipo["medica"],
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _firmada(client, equipo, mascota_id) -> dict:
    entrada = await _entrada(client, equipo, mascota_id, diagnostico="Gastritis")
    resp = await client.post(
        f"/api/v1/clinica/historias/{entrada['id']}/firma", headers=equipo["medica"]
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _visita(db, mascota_id) -> str:
    """Una consulta a domicilio de la mascota, en atencion: la medica esta en la casa."""
    mascota = await db.get(Mascota, mascota_id)
    servicio = Servicio(
        familia_id=mascota.familia_id,
        mascota_id=mascota.id,
        tipo_codigo="consulta_domiciliaria",
        tipo=TipoServicio.DOMICILIARIO,
        ciudad="Cali",
        programado_para=ahora() - timedelta(hours=1),
        estado=EstadoServicio.EN_ATENCION,
    )
    db.add(servicio)
    await db.flush()
    servicio_id = str(servicio.id)
    await db.commit()
    return servicio_id


# --- 6.14 Historia firmada y versiones ---------------------------------------------------
async def test_firmada_no_se_edita_se_corrige_con_version(client, equipo, mascota_id):
    firmada = await _firmada(client, equipo, mascota_id)
    url = f"/api/v1/clinica/historias/{firmada['id']}"
    edicion = await client.patch(url, json={"diagnostico": "otro"}, headers=equipo["medica"])
    assert edicion.status_code == 422

    correccion = await client.post(
        f"{url}/correccion", json={"diagnostico": "Pancreatitis"}, headers=equipo["medica"]
    )
    assert correccion.status_code == 201
    nueva = correccion.json()
    assert (nueva["version"], nueva["estado"], nueva["reemplaza_id"]) == (
        2,
        "borrador",
        firmada["id"],
    )
    assert nueva["motivo"] == CONSULTA["motivo"]  # lo no corregido se conserva

    # Mientras la correccion no se firma, la original sigue vigente.
    historia = f"/api/v1/clinica/mascotas/{mascota_id}/historia"
    vigentes = (await client.get(historia, headers=equipo["medica"])).json()
    assert {e["id"]: e["estado"] for e in vigentes}[firmada["id"]] == "firmada"

    await client.post(f"/api/v1/clinica/historias/{nueva['id']}/firma", headers=equipo["medica"])
    vigentes = (await client.get(historia, headers=equipo["medica"])).json()
    assert [e["diagnostico"] for e in vigentes] == ["Pancreatitis"]
    completa = (
        await client.get(historia, params={"incluir_corregidas": True}, headers=equipo["medica"])
    ).json()
    assert {e["estado"] for e in completa} == {"firmada", "corregida"}


async def test_firmar_exige_diagnostico(client, equipo, mascota_id):
    entrada = await _entrada(client, equipo, mascota_id)
    resp = await client.post(
        f"/api/v1/clinica/historias/{entrada['id']}/firma", headers=equipo["medica"]
    )
    assert resp.status_code == 422


async def test_un_borrador_solo_lo_edita_quien_lo_abrio(client, equipo, mascota_id):
    entrada = await _entrada(client, equipo, mascota_id)
    resp = await client.patch(
        f"/api/v1/clinica/historias/{entrada['id']}",
        json={"diagnostico": "x"},
        headers=equipo["otro"],
    )
    assert resp.status_code == 403


async def test_plantilla_es_el_punto_de_partida(client, equipo, mascota_id):
    plantilla = {
        "nombre": "Control vacunal",
        "campos": {"motivo": "Control de vacunas", "examen_fisico": "Mucosas rosadas, T 38.5"},
    }
    creada = await client.post(
        "/api/v1/clinica/plantillas", json=plantilla, headers=equipo["medica"]
    )
    assert creada.status_code == 201, creada.text
    assert creada.json()["codigo"] == "control_vacunal"
    resp = await client.post(
        "/api/v1/clinica/historias",
        json={
            "mascota_id": str(mascota_id),
            "plantilla_codigo": "control_vacunal",
            "anamnesis": "Sin novedad",
        },
        headers=equipo["medica"],
    )
    entrada = resp.json()
    assert entrada["motivo"] == "Control de vacunas"
    assert entrada["examen_fisico"].startswith("Mucosas")
    assert entrada["anamnesis"] == "Sin novedad"


async def _plantilla(client, headers, nombre: str, **campos: str) -> dict:
    resp = await client.post(
        "/api/v1/clinica/plantillas", json={"nombre": nombre, "campos": campos}, headers=headers
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_el_codigo_de_la_plantilla_sale_del_nombre_y_no_se_repite(client, equipo):
    primera = await _plantilla(client, equipo["medica"], "Otitis externa", motivo="Rascado")
    # Otro nombre que da el mismo codigo: lleva sufijo.
    segunda = await _plantilla(client, equipo["otro"], "Otitis, externa", motivo="Rascado")
    tilde = await _plantilla(client, equipo["medica"], "Revisión", motivo="Control")
    assert (primera["codigo"], segunda["codigo"], tilde["codigo"]) == (
        "otitis_externa",
        "otitis_externa_2",
        "revision",
    )
    # El mismo nombre, sin distinguir mayusculas, no se puede repetir.
    repetida = await client.post(
        "/api/v1/clinica/plantillas",
        json={"nombre": "otitis externa", "campos": {"motivo": "x"}},
        headers=equipo["medica"],
    )
    assert repetida.status_code == 409


async def test_el_equipo_medico_corrige_la_plantilla_y_la_retira_sin_borrarla(
    client, equipo, mascota_id
):
    creada = await _plantilla(
        client, equipo["medica"], "Gastroenteritis", motivo="Vomito", diagnostico="Gastritis"
    )
    url = f"/api/v1/clinica/plantillas/{creada['codigo']}"
    corregida = await client.patch(
        url,
        json={
            "nombre": "Gastroenteritis leve",
            "campos": {"motivo": "Vomito y diarrea", "diagnostico": "  ", "tratamiento": "Dieta"},
        },
        headers=equipo["otro"],
    )
    assert corregida.status_code == 200, corregida.text
    # El codigo no cambia (es su identificador) y un apartado vacio deja de prellenar.
    assert corregida.json() == {
        "codigo": creada["codigo"],
        "nombre": "Gastroenteritis leve",
        "tipo_servicio_codigo": None,
        "campos": {"motivo": "Vomito y diarrea", "tratamiento": "Dieta"},
        "activa": True,
    }

    retirada = await client.patch(url, json={"activa": False}, headers=equipo["medica"])
    assert retirada.json()["activa"] is False
    assert retirada.json()["nombre"] == "Gastroenteritis leve"
    activas = (await client.get("/api/v1/clinica/plantillas", headers=equipo["otro"])).json()
    assert creada["codigo"] not in {p["codigo"] for p in activas}
    # La consulta ya no la ofrece ni la acepta.
    consulta = await client.post(
        "/api/v1/clinica/historias",
        json={"mascota_id": str(mascota_id), "plantilla_codigo": creada["codigo"]},
        headers=equipo["medica"],
    )
    assert consulta.status_code == 404

    otra = await _plantilla(client, equipo["medica"], "Control general", motivo="Control")
    todas = (
        await client.get(
            "/api/v1/clinica/plantillas",
            params={"incluir_inactivas": "true"},
            headers=equipo["medica"],
        )
    ).json()
    # Las retiradas siguen ahi, al final.
    assert [p["codigo"] for p in todas] == [otra["codigo"], creada["codigo"]]

    devuelta = await client.patch(url, json={"activa": True}, headers=equipo["medica"])
    assert devuelta.json()["activa"] is True


async def test_editar_una_plantilla_es_del_equipo_medico(client, equipo):
    creada = await _plantilla(client, equipo["medica"], "Control general", motivo="Control")
    url = f"/api/v1/clinica/plantillas/{creada['codigo']}"
    assert (
        await client.patch(url, json={"activa": False}, headers=equipo["op"])
    ).status_code == 403
    otra = await _plantilla(client, equipo["medica"], "Otitis externa", motivo="Rascado")
    choque = await client.patch(url, json={"nombre": otra["nombre"]}, headers=equipo["medica"])
    assert choque.status_code == 409
    falta = await client.patch(
        "/api/v1/clinica/plantillas/no_existe", json={"activa": False}, headers=equipo["medica"]
    )
    assert falta.status_code == 404


async def test_un_nulo_no_borra_lo_que_la_plantilla_ya_dice(client, equipo):
    creada = await _plantilla(client, equipo["medica"], "Control general", motivo="Control")
    resp = await client.patch(
        f"/api/v1/clinica/plantillas/{creada['codigo']}",
        json={"nombre": None, "campos": None, "activa": None},
        headers=equipo["medica"],
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == creada


async def test_la_plantilla_se_ata_a_un_tipo_de_atencion_del_catalogo(client, equipo):
    url = "/api/v1/clinica/plantillas"
    creada = await client.post(
        url,
        json={
            "nombre": "Otitis externa",
            "tipo_servicio_codigo": "consulta_domiciliaria",
            "campos": {"motivo": "Rascado"},
        },
        headers=equipo["medica"],
    )
    assert creada.status_code == 201, creada.text
    assert creada.json()["tipo_servicio_codigo"] == "consulta_domiciliaria"
    codigo = creada.json()["codigo"]

    # Un tipo que no existe se explica; no llega a la llave foranea.
    falsa = await client.patch(
        f"{url}/{codigo}", json={"tipo_servicio_codigo": "no_existe"}, headers=equipo["medica"]
    )
    assert falsa.status_code == 404
    otra = await client.post(
        url,
        json={"nombre": "Otra", "tipo_servicio_codigo": "no_existe"},
        headers=equipo["medica"],
    )
    assert otra.status_code == 404

    # Sin tipo vale para cualquier atencion.
    general = await client.patch(
        f"{url}/{codigo}", json={"tipo_servicio_codigo": None}, headers=equipo["medica"]
    )
    assert general.json()["tipo_servicio_codigo"] is None


async def test_el_uso_de_una_plantilla_cuenta_las_consultas_firmadas_y_vigentes(
    client, equipo, mascota_id
):
    plantilla = await _plantilla(
        client, equipo["medica"], "Otitis externa", motivo="Rascado", diagnostico="Otitis"
    )
    sin_usar = await _plantilla(client, equipo["medica"], "Control general", motivo="Control")
    firmada = await _entrada(
        client, equipo, mascota_id, plantilla_codigo=plantilla["codigo"], diagnostico="Otitis"
    )
    firma = await client.post(
        f"/api/v1/clinica/historias/{firmada['id']}/firma", headers=equipo["medica"]
    )
    assert firma.status_code == 200, firma.text
    # Un borrador todavia no cuenta.
    await _entrada(client, equipo, mascota_id, plantilla_codigo=plantilla["codigo"])

    url = "/api/v1/clinica/plantillas/uso"
    assert (await client.get(url, headers=equipo["medica"])).json() == {plantilla["codigo"]: 1}
    assert sin_usar["codigo"] not in (await client.get(url, headers=equipo["otro"])).json()
    assert (await client.get(url, headers=equipo["op"])).status_code == 403

    # Corregirla no la cuenta dos veces: la version anterior deja de estar vigente.
    correccion = await client.post(
        f"/api/v1/clinica/historias/{firmada['id']}/correccion",
        json={"diagnostico": "Otitis externa"},
        headers=equipo["medica"],
    )
    assert correccion.status_code == 201, correccion.text
    nueva = correccion.json()["id"]
    await client.post(f"/api/v1/clinica/historias/{nueva}/firma", headers=equipo["medica"])
    assert (await client.get(url, headers=equipo["medica"])).json() == {plantilla["codigo"]: 1}


# --- 6.14 Permisos -----------------------------------------------------------------------


async def test_solo_el_medico_escribe(client, equipo, mascota_id):
    for perfil in ("op", "admin"):
        resp = await client.post(
            "/api/v1/clinica/historias",
            json={"mascota_id": str(mascota_id), **CONSULTA},
            headers=equipo[perfil],
        )
        assert resp.status_code == 403, perfil


async def test_solo_el_personal_medico_lee_la_historia(client, equipo, mascota_id):
    """Seccion 12 (docs/perfiles-y-permisos.md): la historia clinica es del medico; operaciones y
    administracion ya no leen ni un resumen."""
    await _entrada(client, equipo, mascota_id, diagnostico="Gastritis", notas_internas="Ojo")
    historia = f"/api/v1/clinica/mascotas/{mascota_id}/historia"
    for perfil in ("op", "admin"):
        assert (await client.get(historia, headers=equipo[perfil])).status_code == 403, perfil
    (completa,) = (await client.get(historia, headers=equipo["otro"])).json()
    assert completa["notas_internas"] == "Ojo"


# --- 6.14 Adjuntos -----------------------------------------------------------------------


async def test_adjunto_solo_por_url_firmada_y_con_permiso(
    client, equipo, mascota_id, almacenamiento
):
    firmada = await _firmada(client, equipo, mascota_id)
    subida = await client.post(
        f"/api/v1/clinica/historias/{firmada['id']}/adjuntos",
        files={"archivo": ("hemograma.pdf", PDF, "application/pdf")},
        data={"descripcion": "Hemograma"},
        headers=equipo["medica"],
    )
    assert subida.status_code == 201, subida.text
    adjunto = subida.json()
    assert "url" not in adjunto  # el listado nunca trae enlaces
    ((clave, _),) = almacenamiento.objetos.items()
    assert clave.startswith("adjunto_clinico/")

    ruta = f"/api/v1/clinica/adjuntos/{adjunto['id']}/url"
    assert (await client.get(ruta, headers=equipo["op"])).status_code == 403
    abierto = await client.get(ruta, headers=equipo["medica"])
    assert abierto.status_code == 200 and "firma=" in abierto.json()["url"]


async def test_adjunto_rechaza_tipo_no_permitido(client, equipo, mascota_id):
    entrada = await _entrada(client, equipo, mascota_id)
    resp = await client.post(
        f"/api/v1/clinica/historias/{entrada['id']}/adjuntos",
        files={"archivo": ("x.exe", b"MZ\x90\x00" * 20, "application/pdf")},
        headers=equipo["medica"],
    )
    assert resp.status_code == 422


# --- 6.14 Formula ------------------------------------------------------------------------


async def test_formula_en_pdf(client, equipo, mascota_id, almacenamiento):
    firmada = await _firmada(client, equipo, mascota_id)
    resp = await client.post(
        f"/api/v1/clinica/historias/{firmada['id']}/formulas",
        json={
            "items": [
                {
                    "medicamento": "Omeprazol",
                    "dosis": "1 mg/kg",
                    "frecuencia": "cada 24 h",
                    "duracion": "7 dias",
                }
            ],
            "indicaciones": "Dieta blanda",
        },
        headers=equipo["medica"],
    )
    assert resp.status_code == 201, resp.text
    (pdf,) = [c for c, _ in almacenamiento.objetos.values()]
    assert pdf.startswith(b"%PDF-")


# --- 6.17 Atencion virtual ---------------------------------------------------------------
RESPUESTA = {
    "codigo": "observacion_casa",
    "titulo": "Observacion en casa",
    "cuerpo": "Hola {{1}}: por lo que describes, observa a {{2}} 24 horas y ofrece agua.",
    "variables": ["titular", "mascota"],
}


async def _respuesta_aprobada(client, equipo) -> None:
    creada = await client.post(
        "/api/v1/clinica/respuestas-virtuales", json=RESPUESTA, headers=equipo["medica"]
    )
    assert creada.status_code == 201, creada.text
    aprobada = await client.post(
        f"/api/v1/clinica/respuestas-virtuales/{RESPUESTA['codigo']}/aprobacion",
        headers=equipo["otro"],
    )
    assert aprobada.json()["estado"] == "aprobada"


async def test_respuesta_con_variables_mal_declaradas(client, equipo):
    mala = {**RESPUESTA, "variables": ["solo_una"]}
    resp = await client.post(
        "/api/v1/clinica/respuestas-virtuales", json=mala, headers=equipo["medica"]
    )
    assert resp.status_code == 422


async def test_ciclo_virtual_queda_en_la_historia(client, db, equipo, mascota_id):
    solicitud = (
        await client.post(
            "/api/v1/clinica/virtual",
            json={"mascota_id": str(mascota_id), "motivo": "Mi perro vomito dos veces"},
            headers=equipo["medica"],
        )
    ).json()
    url = f"/api/v1/clinica/virtual/{solicitud['id']}"
    respuesta = {"respuesta_codigo": RESPUESTA["codigo"], "variables": ["Ana", "Kira"]}

    await client.post(f"{url}/toma", headers=equipo["medica"])
    # Sin aprobar, la respuesta no se puede usar.
    await client.post(
        "/api/v1/clinica/respuestas-virtuales", json=RESPUESTA, headers=equipo["medica"]
    )
    assert (
        await client.post(f"{url}/respuesta", json=respuesta, headers=equipo["medica"])
    ).status_code == 422
    await client.post(
        f"/api/v1/clinica/respuestas-virtuales/{RESPUESTA['codigo']}/aprobacion",
        headers=equipo["otro"],
    )
    # Solo quien la tomo responde.
    assert (
        await client.post(f"{url}/respuesta", json=respuesta, headers=equipo["otro"])
    ).status_code == 422
    resp = await client.post(f"{url}/respuesta", json=respuesta, headers=equipo["medica"])
    assert resp.status_code == 200, resp.text
    cuerpo = resp.json()
    assert cuerpo["estado"] == "respondida"
    assert "observa a Kira" in cuerpo["respuesta"]

    entrada = await db.get(HistoriaClinica, cuerpo["historia_id"])
    assert (entrada.tipo, entrada.estado) == ("virtual", "firmada")
    assert "observa a Kira" in entrada.tratamiento


async def test_respuesta_virtual_va_por_texto_si_la_ventana_esta_abierta(
    client, db, equipo, mascota_id
):
    await _respuesta_aprobada(client, equipo)
    db.add(ConversacionWhatsApp(telefono="+573001112233", ultimo_entrante_en=ahora()))
    await db.commit()
    solicitud = (
        await client.post(
            "/api/v1/clinica/virtual",
            json={"mascota_id": str(mascota_id), "motivo": "Consulta por WhatsApp"},
            headers=equipo["medica"],
        )
    ).json()
    url = f"/api/v1/clinica/virtual/{solicitud['id']}"
    await client.post(f"{url}/toma", headers=equipo["medica"])
    await client.post(
        f"{url}/respuesta",
        json={"respuesta_codigo": RESPUESTA["codigo"], "variables": ["Ana", "Kira"]},
        headers=equipo["medica"],
    )
    mensaje = await db.scalar(select(Mensaje).where(Mensaje.destino == "+573001112233"))
    assert mensaje.plantilla is None and "observa a Kira" in mensaje.contenido


async def test_cola_prioriza_lo_urgente(client, equipo, mascota_id):
    for prioridad in ("baja", "alta", "media"):
        await client.post(
            "/api/v1/clinica/virtual",
            json={
                "mascota_id": str(mascota_id),
                "motivo": f"Caso {prioridad}",
                "prioridad": prioridad,
            },
            headers=equipo["medica"],
        )
    cola = (await client.get("/api/v1/clinica/virtual/cola", headers=equipo["medica"])).json()
    assert [s["prioridad"] for s in cola] == ["alta", "media", "baja"]


async def test_virtual_requiere_plan_vigente(client, db, equipo):
    familia = await db.run_sync(fabricas.familia)
    mascota_id = familia.mascotas[0].id
    await db.commit()
    resp = await client.post(
        "/api/v1/clinica/virtual",
        json={"mascota_id": str(mascota_id), "motivo": "Consulta sin plan"},
        headers=equipo["medica"],
    )
    assert resp.status_code == 422


def test_vista_por_rol():
    from app.modules.clinica.service import vista_para

    assert vista_para(Rol.MEDICO) == "completa"
    assert vista_para(Rol.COMERCIAL) == "resumen"
    assert vista_para(Rol.FAMILIA) == "familia"
    assert timedelta(0) == timedelta(0)


# --- R2-PAN-07 La consulta es el registro de la visita ----------------------------------------


async def test_firmar_la_consulta_de_la_visita_registra_los_pasos_del_servicio(
    client, db, equipo, mascota_id
):
    """El medico no escribe dos veces lo mismo: la consulta firmada llena los pasos de la
    consulta a domicilio y la visita se puede cerrar."""
    servicio_id = await _visita(db, mascota_id)
    entrada = await _entrada(
        client,
        equipo,
        mascota_id,
        servicio_id=servicio_id,
        examen_fisico="38,9 C, abdomen sensible",
        diagnostico="Gastritis aguda",
        tratamiento="Dieta blanda tres dias",
    )
    servicio = await db.get(Servicio, entrada["servicio_id"])
    assert await db.run_sync(servicios.pasos_faltantes, servicio) != []

    firma = await client.post(
        f"/api/v1/clinica/historias/{entrada['id']}/firma", headers=equipo["medica"]
    )
    assert firma.status_code == 200, firma.text
    pasos = {
        p.paso_codigo: p.datos
        for p in await db.scalars(
            select(ServicioPaso).where(ServicioPaso.servicio_id == servicio.id)
        )
    }
    assert pasos == {
        "valoracion": {"hallazgos": "38,9 C, abdomen sensible\nDiagnostico: Gastritis aguda"},
        "plan": {"recomendaciones": "Dieta blanda tres dias"},
    }
    assert await db.run_sync(servicios.pasos_faltantes, servicio) == []
    await db.run_sync(servicios.cambiar_estado, servicio, EstadoServicio.COMPLETADO)


async def test_sin_tratamiento_el_plan_del_servicio_sigue_pendiente(client, db, equipo, mascota_id):
    """Lo que la consulta no dice no se inventa: sin tratamiento, la visita no se cierra."""
    servicio_id = await _visita(db, mascota_id)
    entrada = await _entrada(
        client, equipo, mascota_id, servicio_id=servicio_id, diagnostico="Gastritis aguda"
    )
    firma = await client.post(
        f"/api/v1/clinica/historias/{entrada['id']}/firma", headers=equipo["medica"]
    )
    assert firma.status_code == 200, firma.text
    servicio = await db.get(Servicio, entrada["servicio_id"])
    assert await db.run_sync(servicios.pasos_faltantes, servicio) == ["Plan y recomendaciones"]


async def test_la_firma_no_toca_un_paso_ya_registrado_en_el_servicio(
    client, db, equipo, mascota_id
):
    servicio_id = await _visita(db, mascota_id)
    servicio = await db.get(Servicio, servicio_id)
    medica = (await client.get("/api/v1/auth/me", headers=equipo["medica"])).json()["id"]
    await db.run_sync(
        servicios.completar_paso, servicio, "valoracion", {"hallazgos": "Lo del servicio"}, medica
    )
    await db.commit()
    entrada = await _entrada(
        client,
        equipo,
        mascota_id,
        servicio_id=servicio_id,
        diagnostico="Gastritis aguda",
        tratamiento="Dieta blanda",
    )
    firma = await client.post(
        f"/api/v1/clinica/historias/{entrada['id']}/firma", headers=equipo["medica"]
    )
    assert firma.status_code == 200, firma.text
    pasos = {
        p.paso_codigo: p.datos
        for p in await db.scalars(
            select(ServicioPaso).where(ServicioPaso.servicio_id == servicio.id)
        )
    }
    assert pasos["valoracion"] == {"hallazgos": "Lo del servicio"}
    assert pasos["plan"] == {"recomendaciones": "Dieta blanda"}


async def test_la_consulta_no_se_enlaza_al_servicio_de_otra_mascota(client, db, equipo, mascota_id):
    otra_familia, _ = await fabricas.afiliada(db, hoy(), telefono="+573009998877")
    servicio_ajeno = await _visita(db, otra_familia.mascotas[0].id)
    resp = await client.post(
        "/api/v1/clinica/historias",
        json={"mascota_id": str(mascota_id), **CONSULTA, "servicio_id": servicio_ajeno},
        headers=equipo["medica"],
    )
    assert resp.status_code == 422
    assert resp.json()["detail"] == "El servicio no es de esta mascota"


async def test_cada_profesional_ve_sus_borradores(client, equipo, mascota_id):
    """El trabajo pendiente de quien abre Clinica: sus consultas sin firmar, no las de otros."""
    propia = await _entrada(client, equipo, mascota_id)
    await _firmada(client, equipo, mascota_id)
    ajena = await client.post(
        "/api/v1/clinica/historias",
        json={"mascota_id": str(mascota_id), **CONSULTA},
        headers=equipo["otro"],
    )
    assert ajena.status_code == 201

    mias = (await client.get("/api/v1/clinica/borradores", headers=equipo["medica"])).json()
    assert [e["id"] for e in mias] == [propia["id"]]
    assert (
        await client.get("/api/v1/clinica/borradores", headers=equipo["admin"])
    ).status_code == 403
    assert (await client.get("/api/v1/clinica/borradores", headers=equipo["op"])).status_code == 403
