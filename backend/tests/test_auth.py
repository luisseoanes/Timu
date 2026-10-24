"""F1-AUT-01 sesion y cierre, F1-AUT-03 recuperacion, F1-AUT-04 usuario de portal."""

import re

from httpx import AsyncClient
from sqlalchemy import select

from app.core.config import settings
from app.core.enums import Rol
from app.modules.comunicaciones.models import Mensaje
from tests.conftest import PASSWORD, crear_usuario

LOGIN = "/api/v1/auth/login"


async def _login(client: AsyncClient, usuario: str, password: str = PASSWORD) -> dict:
    """Inicia sesion y devuelve el cuerpo mas las dos cookies de ESA sesion. Se vacia el
    tarro del cliente para poder manejar varias sesiones a la vez."""
    resp = await client.post(LOGIN, data={"username": usuario, "password": password})
    assert resp.status_code == 200, resp.text
    datos = resp.json()
    datos["acceso"] = resp.cookies[settings.COOKIE_NAME]
    datos["renovacion"] = resp.cookies[settings.COOKIE_REFRESH_NAME]
    client.cookies.clear()
    return datos


def _con(acceso: str) -> dict[str, str]:
    return {"Cookie": f"{settings.COOKIE_NAME}={acceso}"}


async def _renovar(client: AsyncClient, renovacion: str):
    resp = await client.post(
        "/api/v1/auth/refresh",
        headers={"Cookie": f"{settings.COOKIE_REFRESH_NAME}={renovacion}"},
    )
    client.cookies.clear()
    return resp


# --- F1-AUT-01 --------------------------------------------------------------------------------


async def test_la_cookie_de_renovacion_solo_viaja_a_auth(client: AsyncClient, admin):
    resp = await client.post(LOGIN, data={"username": admin.email, "password": PASSWORD})
    galletas = resp.headers.get_list("set-cookie")
    renovacion = next(c for c in galletas if c.startswith(settings.COOKIE_REFRESH_NAME))
    assert "Path=/api/v1/auth" in renovacion
    assert "HttpOnly" in renovacion


async def test_renovar_rota_el_refresh_token(client: AsyncClient, admin):
    sesion = await _login(client, admin.email)
    renovada = await _renovar(client, sesion["renovacion"])
    assert renovada.status_code == 200
    nuevo_acceso = renovada.cookies[settings.COOKIE_NAME]
    assert renovada.cookies[settings.COOKIE_REFRESH_NAME] != sesion["renovacion"]
    assert (await client.get("/api/v1/auth/me", headers=_con(nuevo_acceso))).status_code == 200


async def test_reusar_refresh_rotado_revoca_todas_las_sesiones(client: AsyncClient, admin):
    sesion = await _login(client, admin.email)
    renovada = await _renovar(client, sesion["renovacion"])
    nuevo_acceso = renovada.cookies[settings.COOKIE_NAME]
    robo = await _renovar(client, sesion["renovacion"])
    assert robo.status_code == 401
    # La sesion legitima tambien cae: no se sabe cual de las dos copias es la del usuario.
    me = await client.get("/api/v1/auth/me", headers=_con(nuevo_acceso))
    assert me.status_code == 401


async def test_logout_invalida_el_token_de_inmediato(client: AsyncClient, admin):
    sesion = await _login(client, admin.email)
    headers = _con(sesion["acceso"])
    assert (await client.post("/api/v1/auth/logout", headers=headers)).status_code == 200
    assert (await client.get("/api/v1/auth/me", headers=headers)).status_code == 401
    assert (await _renovar(client, sesion["renovacion"])).status_code == 401


async def test_logout_no_afecta_otras_sesiones(client: AsyncClient, admin):
    movil = await _login(client, admin.email)
    escritorio = await _login(client, admin.email)
    await client.post("/api/v1/auth/logout", headers=_con(movil["acceso"]))
    me = await client.get("/api/v1/auth/me", headers=_con(escritorio["acceso"]))
    assert me.status_code == 200


async def test_desactivar_usuario_cierra_sus_sesiones(client: AsyncClient, db, headers):
    operador = await crear_usuario(db, "op@timu.co", Rol.OPERACIONES)
    sesion = await _login(client, operador.email)
    resp = await client.patch(
        f"/api/v1/auth/usuarios/{operador.id}", json={"activo": False}, headers=headers
    )
    assert resp.status_code == 200
    me = await client.get("/api/v1/auth/me", headers=_con(sesion["acceso"]))
    assert me.status_code == 401


async def test_admin_no_puede_quitarse_su_propio_perfil(client: AsyncClient, admin, headers):
    resp = await client.patch(
        f"/api/v1/auth/usuarios/{admin.id}", json={"rol": "operaciones"}, headers=headers
    )
    assert resp.status_code == 422


async def test_login_por_telefono(client: AsyncClient, db):
    await crear_usuario(db, "tel@timu.co", Rol.COMERCIAL, telefono="+573001112233")
    sesion = await _login(client, "300 111 2233")
    assert sesion["usuario"]["email"] == "tel@timu.co"


# --- F1-AUT-03 --------------------------------------------------------------------------------


def _token_del_correo(contenido: str) -> str:
    return re.search(r"token=([\w-]+)", contenido).group(1)


async def _correo_para(db, email: str) -> Mensaje:
    return await db.scalar(
        select(Mensaje).where(Mensaje.destino == email).order_by(Mensaje.created_at.desc())
    )


async def test_recuperacion_con_enlace_de_un_solo_uso(client: AsyncClient, db, admin, tareas):
    resp = await client.post("/api/v1/auth/recuperar", json={"identificador": admin.email})
    assert resp.status_code == 202
    correo = await _correo_para(db, admin.email)
    assert correo.canal == "email"
    assert await tareas.de("comunicaciones.enviar_mensaje") == [(str(correo.id),)]

    token = _token_del_correo(correo.contenido)
    nueva = {"token": token, "password": "nueva-clave-segura"}
    assert (await client.post("/api/v1/auth/restablecer", json=nueva)).status_code == 204
    await _login(client, admin.email, "nueva-clave-segura")

    reuso = await client.post("/api/v1/auth/restablecer", json=nueva)
    assert reuso.status_code == 400
    assert reuso.json()["codigo"] == "enlace_invalido"


async def test_recuperacion_no_revela_si_la_cuenta_existe(client: AsyncClient, db):
    resp = await client.post("/api/v1/auth/recuperar", json={"identificador": "nadie@timu.co"})
    assert resp.status_code == 202
    assert await _correo_para(db, "nadie@timu.co") is None


async def test_restablecer_cierra_las_sesiones_abiertas(client: AsyncClient, db, admin):
    sesion = await _login(client, admin.email)
    await client.post("/api/v1/auth/recuperar", json={"identificador": admin.email})
    token = _token_del_correo((await _correo_para(db, admin.email)).contenido)
    await client.post("/api/v1/auth/restablecer", json={"token": token, "password": "otra-clave-1"})
    me = await client.get("/api/v1/auth/me", headers=_con(sesion["acceso"]))
    assert me.status_code == 401


async def test_nuevo_enlace_invalida_el_anterior(client: AsyncClient, db, admin):
    await client.post("/api/v1/auth/recuperar", json={"identificador": admin.email})
    viejo = _token_del_correo((await _correo_para(db, admin.email)).contenido)
    await client.post("/api/v1/auth/recuperar", json={"identificador": admin.email})
    resp = await client.post(
        "/api/v1/auth/restablecer", json={"token": viejo, "password": "x" * 10}
    )
    assert resp.status_code == 400


# --- F1-AUT-04 --------------------------------------------------------------------------------

FAMILIA = {
    "titular_nombre": "Ana Ruiz",
    "documento": "1020304050",
    "email": "ana@correo.com",
    "telefono": "3001112233",
    "ciudad": "Cali",
}


async def _familia_con_portal(client: AsyncClient, db, headers, datos=FAMILIA) -> tuple[str, dict]:
    familia = (await client.post("/api/v1/familias", json=datos, headers=headers)).json()
    resp = await client.post(f"/api/v1/familias/{familia['id']}/acceso-portal", headers=headers)
    assert resp.status_code == 200, resp.text
    correo = await _correo_para(db, datos["email"])
    token = _token_del_correo(correo.contenido)
    await client.post(
        "/api/v1/auth/restablecer", json={"token": token, "password": "clave-familia"}
    )
    sesion = await _login(client, datos["email"], "clave-familia")
    return familia["id"], _con(sesion["acceso"])


async def test_familia_activa_su_cuenta_y_ve_solo_lo_suyo(client: AsyncClient, db, headers):
    familia_id, portal = await _familia_con_portal(client, db, headers)
    otra = {
        **FAMILIA,
        "documento": "999888777",
        "email": "otra@correo.com",
        "telefono": "3109998877",
    }
    await client.post("/api/v1/familias", json=otra, headers=headers)

    mia = await client.get("/api/v1/portal/mi-familia", headers=portal)
    assert mia.status_code == 200
    assert mia.json()["id"] == familia_id

    # /familias le sirve acotado por alcance: solo se ve a si misma.
    listado = (await client.get("/api/v1/familias", headers=portal)).json()
    assert [f["id"] for f in listado["items"]] == [familia_id]
    # Lo que no es de lectura sigue cerrado al portal.
    cambio = await client.patch(
        f"/api/v1/familias/{familia_id}", json={"notas": "x"}, headers=portal
    )
    assert cambio.status_code == 403


async def test_acceso_portal_es_idempotente(client: AsyncClient, db, headers):
    familia = (await client.post("/api/v1/familias", json=FAMILIA, headers=headers)).json()
    url = f"/api/v1/familias/{familia['id']}/acceso-portal"
    primero = (await client.post(url, headers=headers)).json()["usuario_portal_id"]
    segundo = (await client.post(url, headers=headers)).json()["usuario_portal_id"]
    assert primero == segundo


async def test_portal_no_reutiliza_cuenta_interna(client: AsyncClient, db, headers):
    await crear_usuario(db, "ana@correo.com", Rol.COMERCIAL)
    familia = (await client.post("/api/v1/familias", json=FAMILIA, headers=headers)).json()
    resp = await client.post(f"/api/v1/familias/{familia['id']}/acceso-portal", headers=headers)
    assert resp.status_code == 409


# --- Equipo para asignar (rutas, tareas) --------------------------------------------------------


async def test_el_equipo_lo_consulta_cualquier_interno_sin_datos_de_contacto(
    client: AsyncClient, db
):
    from tests.conftest import login

    await crear_usuario(db, "operaciones@timu.co", Rol.OPERACIONES)
    await crear_usuario(db, "sara@timu.co", Rol.MEDICO)
    await crear_usuario(db, "inactivo@timu.co", Rol.MEDICO, activo=False)
    await crear_usuario(db, "familia@timu.co", Rol.FAMILIA)
    cabecera = await login(client, "operaciones@timu.co")

    resp = await client.get("/api/v1/auth/equipo", params={"rol": "medico"}, headers=cabecera)
    assert resp.status_code == 200
    assert [m["nombre"] for m in resp.json()] == ["sara"]
    assert set(resp.json()[0]) == {"id", "nombre", "rol"}

    todos = await client.get("/api/v1/auth/equipo", headers=cabecera)
    assert {m["rol"] for m in todos.json()} <= {"admin", "comercial", "operaciones", "medico"}


async def test_una_familia_no_ve_el_equipo(client: AsyncClient, db):
    from tests.conftest import login

    await crear_usuario(db, "familia@timu.co", Rol.FAMILIA)
    cabecera = await login(client, "familia@timu.co")
    assert (await client.get("/api/v1/auth/equipo", headers=cabecera)).status_code == 403
