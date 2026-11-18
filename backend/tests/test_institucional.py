"""R3-PUB-04 Los datos de TIMU que dice la portada: los escribe Administracion y los lee
cualquiera, sin sesion."""

from httpx import AsyncClient

from app.core.enums import Rol
from tests.conftest import crear_usuario, login

API = "/api/v1/institucional"


async def test_la_portada_lee_los_datos_de_timu_sin_sesion(client: AsyncClient):
    resp = await client.get(API)
    assert resp.status_code == 200, resp.text
    datos = resp.json()
    # La migracion crea la fila vacia: nada inventado hasta que TIMU lo escriba.
    assert (datos["mision"], datos["whatsapp"], datos["valores"], datos["redes"]) == (
        None,
        None,
        [],
        [],
    )


async def test_el_administrador_escribe_los_datos_de_timu(client: AsyncClient, headers):
    resp = await client.put(
        API,
        json={
            "razon_social": "TIMU S.A.S.",
            "nit": "901635168-2",
            "mision": " Creemos en el lazo de amor entre cada peludo y su familia. ",
            "valores": ["Confianza", " ", "Empatía"],
            "clinica_nombre": "TIMU clínica veterinaria",
            "clinica_direccion": "Calle 35 # 66a 51",
            "clinica_barrio": "Los Conquistadores, Laureles",
            "clinica_ciudad": "medellin",
            "telefonos": ["301 624 4775", "318 414 0551"],
            "whatsapp": "3016244775",
            "correo": "Administracion@TIMU.com.co",
            "redes": [
                {"nombre": "Instagram", "url": "https://instagram.com/timumedicinaprepagada"}
            ],
            "vision": "",
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    datos = (await client.get(API)).json()
    assert datos["mision"] == "Creemos en el lazo de amor entre cada peludo y su familia."
    assert datos["valores"] == ["Confianza", "Empatía"]
    # La ciudad por su nombre del catalogo, los telefonos en E.164 y el correo en minuscula.
    assert datos["clinica_ciudad"] == "Medellín"
    assert datos["telefonos"] == ["+573016244775", "+573184140551"]
    assert (datos["whatsapp"], datos["correo"]) == ("+573016244775", "administracion@timu.com.co")
    assert datos["vision"] is None


async def test_un_dato_mal_escrito_se_rechaza(client: AsyncClient, headers):
    for malo in (
        {"whatsapp": "12345"},
        {"correo": "no-es-un-correo"},
        {"redes": [{"nombre": "Instagram", "url": "http://instagram.com/x"}]},
        {"clinica_ciudad": "Gotham"},
    ):
        resp = await client.put(API, json=malo, headers=headers)
        assert resp.status_code == 422, malo


async def test_solo_el_administrador_escribe_los_datos_de_timu(client: AsyncClient, db):
    await crear_usuario(db, "ventas@timu.co", Rol.COMERCIAL)
    h = await login(client, "ventas@timu.co")
    assert (await client.put(API, json={"mision": "x"}, headers=h)).status_code == 403
