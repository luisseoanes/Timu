"""6.1 Documentos de la familia y de sus mascotas: los que sube el equipo y los generados."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.core.database import ContextoDb, fijar_contexto
from app.modules.archivos import service as archivos
from app.modules.cartera.models import Contrato
from app.modules.documentos.models import DocumentoFamilia
from app.modules.preventivos.models import CarnetEmitido
from tests.conftest import login
from tests.test_portal import _familia_portal

pytestmark = pytest.mark.integration

PDF = b"%PDF-1.4\n" + b"0" * 64
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


@pytest.fixture
async def familias(db, almacenamiento):
    """Una familia con portal, contrato en PDF y un carnet emitido; y otra ajena."""
    propia, contrato, _ = await _familia_portal(db, "+573001110001", "ana@correo.co")
    ajena, _, _ = await _familia_portal(db, "+573001110002", "beto@correo.co")
    mascota = propia.mascotas[0]

    def generados(s) -> None:
        pdf = archivos.guardar_bytes(
            s, contenido=PDF, nombre="contrato.pdf", proposito="contrato", usuario_id=None
        )
        s.get(Contrato, contrato.id).documento_archivo_id = pdf.id
        carnet = archivos.guardar_bytes(
            s, contenido=PDF, nombre="carnet.pdf", proposito="carnet", usuario_id=None
        )
        s.add(
            CarnetEmitido(
                codigo="CARNET01", mascota_id=mascota.id, archivo_id=carnet.id, sha256="a" * 64
            )
        )
        s.flush()

    await db.run_sync(generados)
    datos = {
        "familia": str(propia.id),
        "mascota": str(mascota.id),
        "numero": contrato.numero,
        "ajena": str(ajena.id),
        "mascota_ajena": str(ajena.mascotas[0].id),
    }
    await db.commit()
    return datos


async def _subir(client, headers, familia: str, contenido=PDF, nombre="cedula.pdf", **campos):
    return await client.post(
        f"/api/v1/familias/{familia}/documentos",
        files={"archivo": (nombre, contenido, "application/pdf")},
        data={"categoria": "identificacion", **campos},
        headers=headers,
    )


async def test_el_equipo_sube_un_documento_y_lo_ve_con_los_generados(
    client: AsyncClient, headers, familias, almacenamiento
):
    resp = await _subir(
        client,
        headers,
        familias["familia"],
        descripcion="  Cedula del titular ",
        mascota_id=familias["mascota"],
    )
    assert resp.status_code == 201, resp.text
    subido = resp.json()
    assert (subido["origen"], subido["categoria"], subido["descripcion"]) == (
        "subido",
        "identificacion",
        "Cedula del titular",
    )
    assert subido["mascota_id"] == familias["mascota"] and subido["visible_familia"] is False
    assert "firma=" in subido["url"]
    assert any(c.startswith("documento_familia/") for c in almacenamiento.objetos)

    todos = (
        await client.get(f"/api/v1/familias/{familias['familia']}/documentos", headers=headers)
    ).json()
    assert {d["origen"] for d in todos} == {"subido", "contrato", "carnet"}
    contrato = next(d for d in todos if d["origen"] == "contrato")
    assert contrato["descripcion"] == f"Contrato {familias['numero']}"
    assert contrato["documento_id"] is None

    # Por mascota: lo suyo, sin los contratos, que son de la familia.
    de_la_mascota = (
        await client.get(
            f"/api/v1/familias/{familias['familia']}/documentos?mascota_id={familias['mascota']}",
            headers=headers,
        )
    ).json()
    assert {d["origen"] for d in de_la_mascota} == {"subido", "carnet"}


async def test_rechaza_otro_tipo_un_fichero_grande_y_la_mascota_ajena(
    client: AsyncClient, headers, familias, almacenamiento
):
    texto = await _subir(client, headers, familias["familia"], contenido=b"hola", nombre="x.pdf")
    assert texto.status_code == 422 and "no permitido" in texto.text
    grande = await _subir(client, headers, familias["familia"], contenido=PDF + b"0" * 10 * 2**20)
    # El limite del cuerpo lo corta antes de llegar a la ruta (413); la politica, igual (422).
    assert grande.status_code in (413, 422) and "10 MB" in grande.text
    ajena = await _subir(client, headers, familias["familia"], mascota_id=familias["mascota_ajena"])
    assert ajena.status_code == 422 and "no pertenece" in ajena.text
    sin_categoria = await client.post(
        f"/api/v1/familias/{familias['familia']}/documentos",
        files={"archivo": ("x.png", PNG, "image/png")},
        headers=headers,
    )
    assert sin_categoria.status_code == 422
    # Nada rechazado llega al almacenamiento.
    assert not [c for c in almacenamiento.objetos if c.startswith("documento_familia/")]


async def test_la_base_rechaza_la_mascota_de_otra_familia(db, familias):
    def insertar(s) -> None:
        pdf = archivos.guardar_bytes(
            s, contenido=PDF, nombre="x.pdf", proposito="documento_familia", usuario_id=None
        )
        s.add(
            DocumentoFamilia(
                familia_id=familias["familia"],
                mascota_id=familias["mascota_ajena"],
                archivo_id=pdf.id,
                categoria="otro",
            )
        )
        s.flush()

    with pytest.raises(IntegrityError, match="fk_documentos_familia_mascota_de_la_familia"):
        await db.run_sync(insertar)


async def test_editar_y_quitar_un_documento(client: AsyncClient, headers, familias):
    doc = (await _subir(client, headers, familias["familia"], descripcion="Vieja")).json()
    url = f"/api/v1/documentos/{doc['documento_id']}"

    resp = await client.patch(
        url,
        json={"categoria": "examen_externo", "descripcion": " ", "visible_familia": True},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert (resp.json()["categoria"], resp.json()["descripcion"]) == ("examen_externo", None)
    assert resp.json()["visible_familia"] is True
    vaciar = await client.patch(url, json={"categoria": None}, headers=headers)
    assert vaciar.status_code == 422 and "vacio" in vaciar.text

    baja = await client.post(f"{url}/baja", headers=headers)
    assert baja.status_code == 204
    todos = (
        await client.get(f"/api/v1/familias/{familias['familia']}/documentos", headers=headers)
    ).json()
    assert all(d["documento_id"] != doc["documento_id"] for d in todos)
    assert (await client.patch(url, json={"descripcion": "x"}, headers=headers)).status_code == 404


async def test_la_familia_solo_ve_en_su_portal_lo_visible(
    client: AsyncClient, headers, familias, db
):
    oculto = (await _subir(client, headers, familias["familia"], descripcion="Interno")).json()
    visible = (
        await _subir(
            client, headers, familias["familia"], descripcion="Para ti", visible_familia="true"
        )
    ).json()
    quitado = (
        await _subir(
            client, headers, familias["familia"], descripcion="Ya no", visible_familia="true"
        )
    ).json()
    await client.post(f"/api/v1/documentos/{quitado['documento_id']}/baja", headers=headers)
    await _subir(client, headers, familias["ajena"], visible_familia="true")

    familia = await login(client, "ana@correo.co")
    propios = (await client.get("/api/v1/portal/documentos", headers=familia)).json()
    assert {d["documento_id"] for d in propios if d["origen"] == "subido"} == {
        visible["documento_id"]
    }
    assert {d["origen"] for d in propios} == {"subido", "contrato", "carnet"}
    assert all(d["url"] for d in propios)
    # El portal no edita documentos.
    resp = await client.patch(
        f"/api/v1/documentos/{visible['documento_id']}", json={"descripcion": "x"}, headers=familia
    )
    assert resp.status_code == 403

    # La base, no solo Python: con el contexto de la familia, ni el documento ni su fichero
    # oculto existen.
    def como_familia(s):
        usuario = s.scalar(text("SELECT id FROM usuarios WHERE email = 'ana@correo.co'"))
        fijar_contexto(
            s, ContextoDb(rol="familia", usuario_id=usuario, familia_id=familias["familia"])
        )
        ids = set(s.scalars(select(DocumentoFamilia.id)))
        archivos_vistos = set(
            s.scalars(text("SELECT id FROM archivos WHERE proposito = 'documento_familia'"))
        )
        return ids, archivos_vistos

    ids, archivos_vistos = await db.run_sync(como_familia)
    assert {str(i) for i in ids} == {visible["documento_id"]}
    assert {str(a) for a in archivos_vistos} == {visible["archivo_id"]}
    assert oculto["archivo_id"] not in {str(a) for a in archivos_vistos}
