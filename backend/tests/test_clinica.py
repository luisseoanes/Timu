"""F2-CLI-01..05 Historia versionada, adjuntos, plantillas y formulas, atencion virtual y
permisos por perfil."""

from datetime import timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.enums import Rol
from app.core.tiempo import ahora, hoy
from app.modules.clinica.models import HistoriaClinica
from app.modules.comunicaciones.models import ConversacionWhatsApp, Mensaje
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


# --- F2-CLI-01 Historia firmada y versiones -----------------------------------------------------
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
        "codigo": "control_vacunal",
        "nombre": "Control vacunal",
        "campos": {"motivo": "Control de vacunas", "examen_fisico": "Mucosas rosadas, T 38.5"},
    }
    creada = await client.post(
        "/api/v1/clinica/plantillas", json=plantilla, headers=equipo["medica"]
    )
    assert creada.status_code == 201, creada.text
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


# --- F2-CLI-05 Permisos -------------------------------------------------------------------------


async def test_solo_el_medico_escribe(client, equipo, mascota_id):
    for perfil in ("op", "admin"):
        resp = await client.post(
            "/api/v1/clinica/historias",
            json={"mascota_id": str(mascota_id), **CONSULTA},
            headers=equipo[perfil],
        )
        assert resp.status_code == 403, perfil


async def test_cada_perfil_ve_lo_suyo(client, equipo, mascota_id):
    await _entrada(client, equipo, mascota_id, diagnostico="Gastritis", notas_internas="Ojo")
    historia = f"/api/v1/clinica/mascotas/{mascota_id}/historia"
    (resumen,) = (await client.get(historia, headers=equipo["op"])).json()
    assert "diagnostico" not in resumen and "notas_internas" not in resumen
    assert resumen["motivo"] == CONSULTA["motivo"]
    (completa,) = (await client.get(historia, headers=equipo["admin"])).json()
    assert completa["notas_internas"] == "Ojo"


# --- F2-CLI-02 Adjuntos -------------------------------------------------------------------------


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


# --- F2-CLI-03 Formula --------------------------------------------------------------------------


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


# --- F2-CLI-04 Atencion virtual -----------------------------------------------------------------
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
        headers=equipo["admin"],
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
            headers=equipo["op"],
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
        headers=equipo["admin"],
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
            headers=equipo["op"],
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
            headers=equipo["op"],
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
        headers=equipo["op"],
    )
    assert resp.status_code == 422


def test_vista_por_rol():
    from app.modules.clinica.service import vista_para

    assert vista_para(Rol.MEDICO) == "completa"
    assert vista_para(Rol.COMERCIAL) == "resumen"
    assert vista_para(Rol.FAMILIA) == "familia"
    assert timedelta(0) == timedelta(0)
