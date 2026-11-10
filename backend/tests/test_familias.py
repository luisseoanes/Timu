"""F1-FAM-01..05 Familias y mascotas; F0-09 catalogos; F0-11 archivos."""

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError

from app.core.enums import Rol
from app.core.tiempo import hoy
from app.core.validaciones import normalizar_documento, normalizar_telefono
from app.integrations import geocodificacion
from app.modules.archivos.models import Archivo
from app.modules.auth.models import Usuario
from app.modules.catalogos.models import Ciudad
from app.modules.catalogos.service import cargar
from app.modules.comercial.models import Interesado
from app.modules.comunicaciones.models import Mensaje
from app.modules.documentos.models import DocumentoFamilia
from app.modules.familias import service
from app.modules.familias.models import ContactoFamilia, Familia
from tests import fabricas
from tests.conftest import autenticar, crear_usuario, login

PAYLOAD = {
    "barrio": "Centro",
    "titular_nombre": "Ana Ruiz",
    "documento": "1020304050",
    "telefono": "573001112233",
    "ciudad": "Bogota",
    "mascotas": [
        {"nombre": "Kira", "especie": "canino", "fecha_nacimiento": "2021-03-01", "peso_kg": 12.5}
    ],
}

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


async def _crear(client: AsyncClient, headers, **cambios) -> dict:
    resp = await client.post("/api/v1/familias", json={**PAYLOAD, **cambios}, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_crear_y_listar_familia(client: AsyncClient, headers):
    creada = await _crear(client, headers)
    assert creada["estado"] == "prospecto"
    assert creada["telefono"] == "+573001112233"
    assert len(creada["mascotas"]) == 1

    listado = await client.get("/api/v1/familias", params={"q": "Ana"}, headers=headers)
    assert listado.json()["total"] == 1


async def test_requiere_autenticacion(client: AsyncClient):
    resp = await client.get("/api/v1/familias")
    assert resp.status_code == 401
    assert resp.json()["codigo"] == "no_autenticado"


async def test_familia_inexistente_responde_404(client: AsyncClient, headers):
    resp = await client.get(
        "/api/v1/familias/00000000-0000-0000-0000-000000000000", headers=headers
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Familia no encontrada"


# --- F1-FAM-04 Validaciones colombianas -------------------------------------------------------


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("3001112233", "+573001112233"),
        ("+57 300 111 2233", "+573001112233"),
        ("(601) 234-5678", "+576012345678"),
        ("573001112233", "+573001112233"),
    ],
)
def test_normaliza_telefonos(entrada, esperado):
    assert normalizar_telefono(entrada) == esperado


@pytest.mark.parametrize("invalido", ["300111", "2001112233", "+1 305 111 2233", "abc"])
def test_rechaza_telefonos_invalidos(invalido):
    with pytest.raises(ValueError):
        normalizar_telefono(invalido)


def test_normaliza_documento():
    assert normalizar_documento("1.020.304-050") == "1020304050"


async def test_documento_con_puntos_es_duplicado(client: AsyncClient, headers):
    await _crear(client, headers)
    resp = await client.post(
        "/api/v1/familias", json={**PAYLOAD, "documento": "1.020.304.050"}, headers=headers
    )
    assert resp.status_code == 409
    assert "1020304050" in resp.json()["detail"]


async def test_mismo_numero_con_otro_tipo_no_es_duplicado(client: AsyncClient, headers):
    await _crear(client, headers)
    await _crear(client, headers, tipo_documento="PA")


async def test_ciudad_fuera_del_catalogo(client: AsyncClient, headers):
    resp = await client.post(
        "/api/v1/familias", json={**PAYLOAD, "ciudad": "Gotham"}, headers=headers
    )
    assert resp.status_code == 422
    assert resp.json()["codigo"] == "regla_negocio"


async def test_ciudad_se_guarda_con_nombre_canonico(client: AsyncClient, headers):
    creada = await _crear(client, headers, ciudad="  bogota ")
    assert creada["ciudad"] == "Bogota"


async def test_especie_fuera_del_catalogo(client: AsyncClient, headers):
    resp = await client.post(
        "/api/v1/familias",
        json={
            **PAYLOAD,
            "mascotas": [
                {
                    "nombre": "Nemo",
                    "especie": "pez",
                    "fecha_nacimiento": "2021-03-01",
                    "peso_kg": 12.5,
                }
            ],
        },
        headers=headers,
    )
    assert resp.status_code == 422


# --- F1-FAM-01 Ficha, baja logica e historial -------------------------------------------------


async def test_baja_logica_oculta_pero_conserva(client: AsyncClient, headers):
    familia = await _crear(client, headers)
    resp = await client.post(
        f"/api/v1/familias/{familia['id']}/baja",
        json={"motivo": "Se muda del pais"},
        headers=headers,
    )
    assert resp.json()["estado"] == "cancelada"
    assert resp.json()["dada_de_baja_en"] is not None

    assert (await client.get("/api/v1/familias", headers=headers)).json()["total"] == 0
    todas = await client.get("/api/v1/familias", params={"incluir_bajas": True}, headers=headers)
    assert todas.json()["total"] == 1

    editar = await client.patch(
        f"/api/v1/familias/{familia['id']}", json={"notas": "x"}, headers=headers
    )
    assert editar.status_code == 422


async def test_historial_de_estados(client: AsyncClient, headers):
    familia = await _crear(client, headers)
    url = f"/api/v1/familias/{familia['id']}"
    await client.post(f"{url}/estado", json={"estado": "activa"}, headers=headers)
    await client.patch(url, json={"notas": "Prefiere visitas en la tarde"}, headers=headers)
    await client.post(f"{url}/estado", json={"estado": "en_mora"}, headers=headers)

    estados = await client.get(f"{url}/historial", params={"solo_estado": True}, headers=headers)
    assert [c["cambios"]["estado"] for c in estados.json()] == [
        ["prospecto", "activa"],
        ["activa", "en_mora"],
    ]
    completo = await client.get(f"{url}/historial", headers=headers)
    assert [c["accion"] for c in completo.json()] == [
        "crear",
        "cambio_estado",
        "editar",
        "cambio_estado",
    ]


async def test_operaciones_no_cambia_estado_de_afiliacion(client: AsyncClient, db, headers):
    from app.core.enums import Rol
    from tests.conftest import crear_usuario, login

    familia = await _crear(client, headers)
    await crear_usuario(db, "op@timu.co", Rol.OPERACIONES)
    op = await login(client, "op@timu.co")
    resp = await client.post(
        f"/api/v1/familias/{familia['id']}/estado", json={"estado": "activa"}, headers=op
    )
    assert resp.status_code == 403


# --- F1-FAM-02 Mascotas -----------------------------------------------------------------------


async def test_ciclo_de_mascota(client: AsyncClient, headers):
    familia = await _crear(client, headers)
    nueva = await client.post(
        f"/api/v1/familias/{familia['id']}/mascotas",
        json={
            "nombre": "Milo",
            "especie": "felino",
            "sexo": "macho",
            "fecha_nacimiento": "2021-03-01",
            "peso_kg": 12.5,
        },
        headers=headers,
    )
    assert nueva.status_code == 201
    mascota_id = nueva.json()["id"]

    editada = await client.patch(
        f"/api/v1/mascotas/{mascota_id}", json={"peso_kg": 4.2}, headers=headers
    )
    assert editada.json()["peso_kg"] == 4.2

    baja = await client.post(
        f"/api/v1/mascotas/{mascota_id}/baja", json={"motivo": "Fallecimiento"}, headers=headers
    )
    assert baja.json()["activa"] is False

    ficha = await client.get(f"/api/v1/familias/{familia['id']}", headers=headers)
    assert {m["nombre"]: m["activa"] for m in ficha.json()["mascotas"]} == {
        "Kira": True,
        "Milo": False,
    }


async def test_mascota_no_cambia_de_familia(client: AsyncClient, headers):
    familia = await _crear(client, headers)
    mascota_id = familia["mascotas"][0]["id"]
    resp = await client.patch(
        f"/api/v1/mascotas/{mascota_id}",
        json={"familia_id": "00000000-0000-0000-0000-000000000000"},
        headers=headers,
    )
    assert resp.json()["familia_id"] == familia["id"]


async def test_fecha_de_nacimiento_futura(client: AsyncClient, headers):
    familia = await _crear(client, headers)
    resp = await client.post(
        f"/api/v1/familias/{familia['id']}/mascotas",
        json={"nombre": "X", "especie": "canino", "fecha_nacimiento": "2999-01-01", "peso_kg": 3},
        headers=headers,
    )
    assert resp.status_code == 422


async def test_el_panel_da_de_alta_mascotas_solo_con_peso_y_fecha(client: AsyncClient, headers):
    familia = await _crear(client, headers)
    for falta in ("peso_kg", "fecha_nacimiento"):
        cuerpo = {"nombre": "Milo", "especie": "felino", "fecha_nacimiento": "2022-01-01"}
        cuerpo["peso_kg"] = 4  # type: ignore[assignment]
        del cuerpo[falta]
        resp = await client.post(
            f"/api/v1/familias/{familia['id']}/mascotas", json=cuerpo, headers=headers
        )
        assert resp.status_code == 422 and falta in resp.text, falta
    sin_peso = {**PAYLOAD, "documento": "80123456"}
    sin_peso["mascotas"] = [
        {"nombre": "Kira", "especie": "canino", "fecha_nacimiento": "2021-03-01"}
    ]
    resp = await client.post("/api/v1/familias", json=sin_peso, headers=headers)
    assert resp.status_code == 422 and "peso_kg" in resp.text


async def test_editar_una_mascota_no_vacia_peso_ni_fecha_ni_pone_una_futura(
    client: AsyncClient, headers
):
    familia = await _crear(client, headers)
    mascota_id = familia["mascotas"][0]["id"]
    url = f"/api/v1/mascotas/{mascota_id}"
    for cuerpo in ({"peso_kg": None}, {"fecha_nacimiento": None}, {"nombre": None}):
        resp = await client.patch(url, json=cuerpo, headers=headers)
        assert resp.status_code == 422 and "vacio" in resp.text, cuerpo
    resp = await client.patch(url, json={"fecha_nacimiento": "2999-01-01"}, headers=headers)
    assert resp.status_code == 422 and "futura" in resp.text
    resp = await client.patch(url, json={"peso_kg": 13.2, "raza": None}, headers=headers)
    assert resp.status_code == 200
    assert (resp.json()["peso_kg"], resp.json()["raza"]) == (13.2, None)


# --- F0-11 Foto de mascota con enlace firmado -------------------------------------------------


async def test_foto_con_enlace_firmado(client: AsyncClient, headers, almacenamiento):
    familia = await _crear(client, headers)
    mascota_id = familia["mascotas"][0]["id"]
    resp = await client.put(
        f"/api/v1/mascotas/{mascota_id}/foto",
        files={"foto": ("kira.png", PNG, "image/png")},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert "firma=" in resp.json()["foto_url"]
    ((clave, (contenido, tipo)),) = almacenamiento.objetos.items()
    assert clave.startswith("foto_mascota/") and clave.endswith(".png")
    assert contenido == PNG and tipo == "image/png"


async def test_la_ficha_de_la_familia_trae_la_foto_de_cada_mascota(
    client: AsyncClient, headers, almacenamiento
):
    """La ficha del panel y el portal leen las mascotas desde la familia: sin esto la foto
    recien subida no se veria en ninguno de los dos."""
    familia = await _crear(client, headers)
    mascota_id = familia["mascotas"][0]["id"]
    await client.put(
        f"/api/v1/mascotas/{mascota_id}/foto",
        files={"foto": ("kira.png", PNG, "image/png")},
        headers=headers,
    )
    ficha = (await client.get(f"/api/v1/familias/{familia['id']}", headers=headers)).json()
    assert "firma=" in (ficha["mascotas"][0]["foto_url"] or "")
    listado = (
        await client.get(f"/api/v1/familias?q={familia['documento']}", headers=headers)
    ).json()
    assert "firma=" in (listado["items"][0]["mascotas"][0]["foto_url"] or "")


async def test_foto_rechaza_tipo_disfrazado(client: AsyncClient, headers, almacenamiento):
    familia = await _crear(client, headers)
    resp = await client.put(
        f"/api/v1/mascotas/{familia['mascotas'][0]['id']}/foto",
        files={"foto": ("kira.png", b"<script>alert(1)</script>", "image/png")},
        headers=headers,
    )
    assert resp.status_code == 422
    assert "no permitido" in resp.json()["detail"]
    assert almacenamiento.objetos == {}


@pytest.mark.unit
def test_url_firmada_de_vida_corta_y_con_nombre(monkeypatch, almacenamiento):
    """F0-11 Nada se sirve publico: la URL la firma el proveedor S3, con vencimiento corto
    y el nombre original para la descarga (no la clave interna)."""
    from app.core.config import settings
    from app.integrations import storage

    pedidos = []

    class ClienteFalso:
        def generate_presigned_url(self, operacion, Params, ExpiresIn):  # noqa: N803
            pedidos.append((operacion, Params, ExpiresIn))
            return "https://s3/firmada"

    monkeypatch.setattr(settings, "STORAGE_PUBLIC_ENDPOINT_URL", None)
    monkeypatch.setattr(storage, "_cliente", lambda: ClienteFalso())
    assert almacenamiento.url_firmada_real("foto/x.png", nombre="kira.png") == "https://s3/firmada"
    ((operacion, params, expira),) = pedidos
    assert operacion == "get_object"
    assert expira == settings.STORAGE_URL_TTL_SEGUNDOS <= 600
    assert params["ResponseContentDisposition"] == 'inline; filename="kira.png"'


@pytest.mark.unit
def test_url_firmada_con_el_host_que_ve_el_navegador(monkeypatch, almacenamiento):
    """En docker compose la API sube a almacenamiento:8333, pero el navegador solo llega por
    localhost: la URL se firma con el host publico, porque la firma lo incluye."""
    from app.core.config import settings
    from app.integrations import storage

    monkeypatch.setattr(settings, "STORAGE_ENDPOINT_URL", "http://almacenamiento:8333")
    monkeypatch.setattr(settings, "STORAGE_PUBLIC_ENDPOINT_URL", "http://localhost:9002")
    storage._cliente_publico.cache_clear()
    try:
        url = almacenamiento.url_firmada_real("foto/x.png")
    finally:
        storage._cliente_publico.cache_clear()
    assert url.startswith(f"http://localhost:9002/{settings.STORAGE_BUCKET}/foto/x.png?")
    assert "X-Amz-Signature=" in url


# --- F1-FAM-05 Geocodificacion ----------------------------------------------------------------


async def test_guardar_direccion_programa_geocodificacion(client: AsyncClient, headers, tareas):
    familia = await _crear(client, headers, direccion="Cra 7 # 72-41")
    assert await tareas.de("familias.geocodificar") == [(familia["id"],)]


async def test_coordenadas_manuales_no_se_geocodifican(client: AsyncClient, headers, tareas):
    await _crear(client, headers, direccion="Finca", latitud=4.6, longitud=-74.1)
    assert await tareas.de("familias.geocodificar") == []


async def test_geocodificacion_con_proveedor(client: AsyncClient, db, headers, monkeypatch):
    familia = await _crear(client, headers, direccion="Cra 7 # 72-41")

    def _ok(direccion, ciudad):
        return (4.6601, -74.0555)

    monkeypatch.setattr(geocodificacion, "geocodificar", _ok)
    from uuid import UUID

    assert await db.run_sync(service.geocodificar, UUID(familia["id"])) == "direccion"
    guardada = await db.get(Familia, UUID(familia["id"]))
    assert (guardada.latitud, guardada.longitud) == (4.6601, -74.0555)


async def test_geocodificacion_sin_resultado_usa_la_ciudad(client: AsyncClient, db, headers):
    from uuid import UUID

    familia = await _crear(client, headers, direccion="Direccion inexistente")
    assert await db.run_sync(service.geocodificar, UUID(familia["id"])) == "ciudad"
    guardada = await db.get(Familia, UUID(familia["id"]))
    assert guardada.latitud == pytest.approx(4.7110)


async def test_cambiar_direccion_limpia_coordenadas(client: AsyncClient, headers, tareas):
    familia = await _crear(client, headers, direccion="Calle 1", latitud=4.6, longitud=-74.1)
    resp = await client.patch(
        f"/api/v1/familias/{familia['id']}", json={"direccion": "Calle 2"}, headers=headers
    )
    assert resp.json()["latitud"] is None
    assert await tareas.de("familias.geocodificar") == [(familia["id"],)]


# --- F1-FAM-03 Formularios publicos -----------------------------------------------------------


FORMULARIO = {
    "barrio": "Centro",
    "titular_nombre": "Luisa Gomez",
    "documento": "52.111.222",
    "telefono": "3157778899",
    "ciudad": "Medellin",
    "mascotas": [{"nombre": "Toby", "especie": "canino"}],
}


async def test_formulario_crea_la_familia(client: AsyncClient, db):
    resp = await client.post("/api/v1/formularios/familia", json=FORMULARIO)
    assert resp.status_code == 202
    familia = await db.scalar(select(Familia).where(Familia.documento == "52111222"))
    assert familia.origen == "formulario"
    assert [m.nombre for m in familia.mascotas] == ["Toby"]


async def test_formulario_completa_sin_sobrescribir(client: AsyncClient, db, headers):
    existente = await _crear(
        client, headers, documento="52111222", titular_nombre="Luisa Gomez Validada"
    )
    resp = await client.post(
        "/api/v1/formularios/familia",
        json={
            **FORMULARIO,
            "barrio": "Centro",
            "titular_nombre": "Otro Nombre",
            "email": "luisa@correo.com",
            "mascotas": [
                {"nombre": "kira", "especie": "canino"},
                {"nombre": "Toby", "especie": "canino"},
            ],
        },
    )
    # Misma respuesta que para una familia nueva: no revela que ya existia.
    assert resp.json() == {"detail": "Recibimos tus datos; te contactaremos pronto"}
    ficha = (await client.get(f"/api/v1/familias/{existente['id']}", headers=headers)).json()
    assert ficha["titular_nombre"] == "Luisa Gomez Validada"
    assert ficha["email"] == "luisa@correo.com"
    assert sorted(m["nombre"] for m in ficha["mascotas"]) == ["Kira", "Toby"]


async def test_formulario_ignora_bots(client: AsyncClient, db):
    resp = await client.post(
        "/api/v1/formularios/familia", json={**FORMULARIO, "sitio_web": "http://spam"}
    )
    assert resp.status_code == 202
    assert await db.scalar(select(func.count()).select_from(Familia)) == 0


# --- F0-09 Catalogos --------------------------------------------------------------------------


async def test_carga_de_catalogos_es_repetible(db):
    antes = await db.scalar(select(func.count()).select_from(Ciudad))
    resultado = await db.run_sync(cargar)
    assert resultado["ciudades"] == {"creados": 0, "actualizados": 0}
    assert await db.scalar(select(func.count()).select_from(Ciudad)) == antes


async def test_carga_actualiza_cambios(db):
    bogota = await db.scalar(select(Ciudad).where(Ciudad.codigo == "11001"))
    bogota.nombre = "Santa Fe de Bogota"
    await db.flush()
    resultado = await db.run_sync(cargar)
    assert resultado["ciudades"]["actualizados"] == 1
    assert bogota.nombre == "Bogota"


async def test_ciudad_desactivada_sale_de_los_formularios(client: AsyncClient, headers):
    await client.patch(
        "/api/v1/catalogos/ciudades/11001/activo", json={"activo": False}, headers=headers
    )
    ciudades = await client.get("/api/v1/catalogos/ciudades", headers=headers)
    assert "Bogota" not in [c["nombre"] for c in ciudades.json()]
    resp = await client.post("/api/v1/familias", json=PAYLOAD, headers=headers)
    assert resp.status_code == 422


async def test_esquemas_por_especie(client: AsyncClient, headers):
    resp = await client.get(
        "/api/v1/catalogos/esquemas-preventivos", params={"especie": "felino"}, headers=headers
    )
    assert {e["especie_codigo"] for e in resp.json()} == {"felino"}


async def test_tipos_de_servicio_exponen_sus_pasos(client: AsyncClient, headers):
    """El panel arma el formulario de la atencion con los pasos de cada tipo (F1-SER-02)."""
    resp = await client.get("/api/v1/catalogos/tipos-servicio", headers=headers)
    consulta = next(t for t in resp.json() if t["codigo"] == "consulta_domiciliaria")
    valoracion = next(p for p in consulta["pasos"] if p["codigo"] == "valoracion")
    assert valoracion == {
        "codigo": "valoracion",
        "nombre": "Valoracion clinica",
        "obligatorio": True,
        "campos": ["hallazgos"],
    }


# --- Sesion por cookie (pruebas que trajo el remoto) ------------------------------------------


async def test_logout_invalida_la_sesion(client: AsyncClient, usuario_admin):
    await autenticar(client, "admin@timu.co", "secreto123")
    assert (await client.get("/api/v1/familias")).status_code == 200

    assert (await client.post("/api/v1/auth/logout")).status_code == 200
    assert (await client.get("/api/v1/familias")).status_code == 401


async def test_el_token_no_viaja_en_el_cuerpo(client: AsyncClient, usuario_admin):
    """La sesion va en cookie httpOnly: si el token apareciera en el JSON, una XSS
    podria leerlo y todo el cambio no serviria de nada."""
    resp = await client.post(
        "/api/v1/auth/login", data={"username": "admin@timu.co", "password": "secreto123"}
    )
    assert resp.status_code == 200
    assert "access_token" not in resp.text
    assert "refresh_token" not in resp.text
    cookie = resp.cookies.get("timu_sesion")
    assert cookie, "el login debe dejar la cookie de sesion"
    assert "httponly" in resp.headers["set-cookie"].lower()


async def test_patch_no_cambia_el_estado_de_afiliacion(client: AsyncClient, db, headers):
    """Revision F1: el PATCH general aceptaba `estado` y saltaba el permiso del endpoint
    dedicado (solo comercial o admin)."""
    from app.core.enums import Rol
    from tests.conftest import crear_usuario, login

    familia = await _crear(client, headers)
    await crear_usuario(db, "medico@timu.co", Rol.MEDICO)
    medico = await login(client, "medico@timu.co")
    resp = await client.patch(
        f"/api/v1/familias/{familia['id']}", json={"estado": "cancelada"}, headers=medico
    )
    assert resp.status_code == 200
    assert resp.json()["estado"] == "prospecto"


# --- Habeas data: anonimizacion ---------------------------------------------------------------


async def _familia_con_rastro(db) -> tuple[Familia, Usuario]:
    """Familia con todo lo que la identifica: usuario de portal, foto de su mascota,
    interesado, mensaje y su rastro en la bitacora."""
    familia = await db.run_sync(fabricas.familia, email="ana@ejemplo.co")
    portal = Usuario(
        email="ana@ejemplo.co", nombre="Ana Ruiz", rol=Rol.FAMILIA, hashed_password="x"
    )
    db.add(portal)
    await db.flush()
    familia.usuario_portal_id = portal.id
    # Barrio y complemento cambian despues del alta para que tambien queden en la bitacora.
    familia.barrio = "Rosales Alto"
    familia.complemento = "Torre 9 apto 1204"
    foto = Archivo(
        clave="foto_mascota/2026/11/abc.jpg",
        proposito="foto_mascota",
        nombre_original="luna.jpg",
        content_type="image/jpeg",
        tamano_bytes=10,
        sha256="0" * 64,
    )
    db.add(foto)
    await db.flush()
    familia.mascotas[0].foto_archivo_id = foto.id
    db.add(
        Interesado(
            nombre="Ana Ruiz", telefono=familia.telefono, origen="panel", familia_id=familia.id
        )
    )
    db.add(
        Mensaje(
            familia_id=familia.id, canal="whatsapp", destino=familia.telefono, contenido="Hola Ana"
        )
    )
    db.add(
        ContactoFamilia(
            familia_id=familia.id,
            posicion=1,
            nombre="Rocio Contacto",
            telefono="+573009998877",
            relacion="hermana",
            email="rocio@ejemplo.co",
        )
    )
    # Documentos subidos: el de identificacion se purga; el examen externo es clinico y queda.
    for clave, categoria, descripcion in (
        ("documento_familia/2026/11/cedula.pdf", "identificacion", "Cedula de Ana Ruiz"),
        ("documento_familia/2026/11/eco.pdf", "examen_externo", "Ecografia de Mascota0"),
    ):
        archivo = Archivo(
            clave=clave,
            proposito="documento_familia",
            nombre_original=f"{descripcion}.pdf",
            content_type="application/pdf",
            tamano_bytes=10,
            sha256="0" * 64,
        )
        db.add(archivo)
        await db.flush()
        db.add(
            DocumentoFamilia(
                familia_id=familia.id,
                mascota_id=familia.mascotas[0].id,
                archivo_id=archivo.id,
                categoria=categoria,
                descripcion=descripcion,
            )
        )
    await db.commit()
    return familia, portal


async def test_anonimizar_no_deja_datos_personales(client: AsyncClient, db, headers, tareas):
    familia, portal = await _familia_con_rastro(db)
    resp = await client.post(f"/api/v1/familias/{familia.id}/anonimizar", headers=headers)
    assert resp.status_code == 200, resp.text
    datos = resp.json()
    assert datos["titular_nombre"] == "Anonimizado" and datos["email"] is None
    assert datos["estado"] == "cancelada" and datos["documento"].startswith("ANON")

    # Nada de lo que la identificaba queda en la base, tampoco en la bitacora.
    for tabla in (
        "familias",
        "usuarios",
        "mascotas",
        "interesados",
        "mensajes",
        "contactos_familia",
        "documentos_familia",
        "auditoria",
    ):
        filas = await db.scalar(
            text(f"SELECT count(*) FROM {tabla} t WHERE to_jsonb(t)::text ~ :pii"),
            {
                "pii": "Ana Ruiz|ana@ejemplo\\.co|Hola Ana|3001112233|Mascota0|Rosales|Torre 9"
                "|Rocio|3009998877|rocio@ejemplo|hermana|Cedula de|Ecografia de"
            },
        )
        assert filas == 0, tabla
    await db.refresh(portal)
    assert portal.activo is False
    # Las fotos se borran del almacenamiento despues de confirmar, no dentro de la transaccion.
    ((purgadas,),) = await tareas.de("familias.purgar_archivos")
    assert sorted(purgadas) == [
        "documento_familia/2026/11/cedula.pdf",
        "foto_mascota/2026/11/abc.jpg",
    ]
    filas = await db.execute(
        text("SELECT clave, purgado_en IS NOT NULL, nombre_original FROM archivos")
    )
    estado = {clave: (purgado, nombre) for clave, purgado, nombre in filas.tuples()}
    assert estado["foto_mascota/2026/11/abc.jpg"] == (True, "anonimizado")
    assert estado["documento_familia/2026/11/cedula.pdf"] == (True, "anonimizado")
    # El examen externo es clinico: se conserva el fichero, no su descripcion ni su nombre.
    assert estado["documento_familia/2026/11/eco.pdf"] == (False, "anonimizado")


async def test_anonimizar_dos_veces_o_con_contrato_vigente(client: AsyncClient, db, headers):
    familia, _ = await fabricas.afiliada(db, hoy())
    await db.commit()
    resp = await client.post(f"/api/v1/familias/{familia.id}/anonimizar", headers=headers)
    assert resp.status_code == 422 and "contrato vigente" in resp.text

    otra = await db.run_sync(fabricas.familia)
    await db.commit()
    assert (
        await client.post(f"/api/v1/familias/{otra.id}/anonimizar", headers=headers)
    ).status_code == 200
    assert (
        await client.post(f"/api/v1/familias/{otra.id}/anonimizar", headers=headers)
    ).status_code == 409


async def test_solo_un_administrador_anonimiza(client: AsyncClient, db):
    familia_id = (await db.run_sync(fabricas.familia)).id
    await crear_usuario(db, "comercial@timu.co", Rol.COMERCIAL)
    cabecera = await login(client, "comercial@timu.co")
    resp = await client.post(f"/api/v1/familias/{familia_id}/anonimizar", headers=cabecera)
    assert resp.status_code == 403
    # Y la base tampoco lo admite fuera de un contexto de administrador.
    with pytest.raises(DBAPIError, match="Solo un administrador anonimiza"):
        await db.execute(text("SELECT anonimizar_familia(:i)"), {"i": familia_id})


# --- Contactos adicionales (6.1) -----------------------------------------------------------------


def _contacto(n: int, **cambios) -> dict:
    return {"nombre": f"Contacto {n}", "telefono": f"30011122{n:02d}", **cambios}


async def test_contactos_adicionales_como_mucho_tres_y_la_baja_libera_su_lugar(
    client: AsyncClient, db, headers
):
    familia = await db.run_sync(fabricas.familia)
    await db.commit()
    url = f"/api/v1/familias/{familia.id}/contactos"
    creados = []
    for n in range(1, 4):
        resp = await client.post(url, json=_contacto(n, relacion="hijo"), headers=headers)
        assert resp.status_code == 201, resp.text
        creados.append(resp.json())
    assert [c["posicion"] for c in creados] == [1, 2, 3]
    assert creados[0]["telefono"] == "+573001112201"

    cuarto = await client.post(url, json=_contacto(4), headers=headers)
    assert cuarto.status_code == 422 and "maximo 3" in cuarto.text

    baja = await client.post(f"{url}/{creados[1]['id']}/baja", headers=headers)
    assert baja.status_code == 204
    otro = await client.post(url, json=_contacto(5, email="otro@ejemplo.co"), headers=headers)
    assert otro.status_code == 201 and otro.json()["posicion"] == 2

    ficha = (await client.get(f"/api/v1/familias/{familia.id}", headers=headers)).json()
    assert [c["nombre"] for c in ficha["contactos"]] == ["Contacto 1", "Contacto 5", "Contacto 3"]
    # El dado de baja se conserva marcado, no se borra.
    assert await db.scalar(select(func.count()).select_from(ContactoFamilia)) == 4


async def test_editar_un_contacto_valida_el_telefono(client: AsyncClient, db, headers):
    familia = await db.run_sync(fabricas.familia)
    await db.commit()
    url = f"/api/v1/familias/{familia.id}/contactos"
    creado = (await client.post(url, json=_contacto(1), headers=headers)).json()
    malo = await client.patch(f"{url}/{creado['id']}", json={"telefono": "123"}, headers=headers)
    assert malo.status_code == 422
    bueno = await client.patch(
        f"{url}/{creado['id']}", json={"relacion": "vecina"}, headers=headers
    )
    assert bueno.status_code == 200 and bueno.json()["relacion"] == "vecina"


async def test_la_base_rechaza_un_cuarto_contacto_vigente(db):
    """Comprobar en Python y despues insertar deja una ventana a dos altas simultaneas: el
    limite lo pone la base, con la posicion unica entre los vigentes."""
    familia = await db.run_sync(fabricas.familia)
    for n in (1, 2, 3):
        db.add(
            ContactoFamilia(familia_id=familia.id, posicion=n, nombre="C", telefono="+573001112233")
        )
    await db.flush()
    with pytest.raises(DBAPIError):
        async with db.begin_nested():
            db.add(
                ContactoFamilia(
                    familia_id=familia.id, posicion=4, nombre="C", telefono="+573001112233"
                )
            )
            await db.flush()
    with pytest.raises(DBAPIError):
        async with db.begin_nested():
            db.add(
                ContactoFamilia(
                    familia_id=familia.id, posicion=2, nombre="C", telefono="+573001112233"
                )
            )
            await db.flush()
