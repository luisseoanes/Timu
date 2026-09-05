"""Autorizacion a nivel de fila: lo que ve el portal de familias.

Es la prueba mas importante de la suite. Un fallo aqui no rompe la aplicacion, la
convierte en una fuga de historias clinicas ajenas.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import Rol
from app.core.scope import Alcance, AlcanceNoDefinido, restringir
from app.core.security import hash_password
from app.modules.auth.models import Usuario
from app.modules.familias.models import Familia, Mascota
from tests.conftest import autenticar

pytestmark = pytest.mark.integration


async def _familia_con_portal(db: AsyncSession, nombre: str, documento: str, email: str):
    usuario = Usuario(
        email=email, nombre=nombre, rol=Rol.FAMILIA, hashed_password=hash_password("secreto123")
    )
    db.add(usuario)
    await db.flush()
    familia = Familia(
        titular_nombre=nombre,
        documento=documento,
        telefono="573000000000",
        ciudad="Bogota",
        usuario_portal_id=usuario.id,
    )
    db.add(familia)
    await db.flush()
    return usuario, familia


async def test_una_familia_solo_se_ve_a_si_misma(client: AsyncClient, db: AsyncSession):
    _, propia = await _familia_con_portal(db, "Ana", "111", "ana@ejemplo.co")
    _, ajena = await _familia_con_portal(db, "Beto", "222", "beto@ejemplo.co")
    await db.commit()

    await autenticar(client, "ana@ejemplo.co", "secreto123")

    listado = await client.get("/api/v1/familias")
    assert listado.status_code == 200
    ids = [f["id"] for f in listado.json()["items"]]
    assert ids == [str(propia.id)]
    assert str(ajena.id) not in ids


async def test_pedir_por_id_una_familia_ajena_da_404(client: AsyncClient, db: AsyncSession):
    """404 y no 403: distinguirlos confirmaria que el recurso existe."""
    await _familia_con_portal(db, "Ana", "111", "ana@ejemplo.co")
    _, ajena = await _familia_con_portal(db, "Beto", "222", "beto@ejemplo.co")
    await db.commit()

    await autenticar(client, "ana@ejemplo.co", "secreto123")
    resp = await client.get(f"/api/v1/familias/{ajena.id}")
    assert resp.status_code == 404


async def test_los_filtros_no_saltan_el_alcance(client: AsyncClient, db: AsyncSession):
    await _familia_con_portal(db, "Ana", "111", "ana@ejemplo.co")
    await _familia_con_portal(db, "Beto", "222", "beto@ejemplo.co")
    await db.commit()

    await autenticar(client, "ana@ejemplo.co", "secreto123")
    resp = await client.get("/api/v1/familias", params={"q": "Beto"})
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


async def test_el_personal_interno_ve_todo(client: AsyncClient, db: AsyncSession, usuario_admin):
    await _familia_con_portal(db, "Ana", "111", "ana@ejemplo.co")
    await _familia_con_portal(db, "Beto", "222", "beto@ejemplo.co")
    await db.commit()

    await autenticar(client, "admin@timu.co", "secreto123")
    resp = await client.get("/api/v1/familias")
    assert resp.json()["total"] == 2


@pytest.mark.unit
def test_un_modelo_sin_columna_familia_falla_cerrado():
    """Si alguien anade un modelo y olvida declarar como se ata a una familia, la
    consulta revienta. Es deliberado: el fallo por omision no puede ser 'ver todo'."""
    from sqlalchemy import select

    class ModeloSinDeclarar:
        pass

    alcance = Alcance(
        usuario_id=__import__("uuid").uuid4(),
        rol=Rol.FAMILIA,
        familia_id=__import__("uuid").uuid4(),
    )
    with pytest.raises(AlcanceNoDefinido):
        restringir(select(Familia), ModeloSinDeclarar, alcance)


@pytest.mark.unit
def test_familia_sin_ficha_asociada_no_ve_nada():
    from sqlalchemy import select

    alcance = Alcance(usuario_id=__import__("uuid").uuid4(), rol=Rol.FAMILIA, familia_id=None)
    with pytest.raises(AlcanceNoDefinido):
        restringir(select(Familia), Familia, alcance)


@pytest.mark.unit
def test_mascota_declara_su_columna_de_familia():
    assert Mascota.__columna_familia__ == "familia_id"
    assert Familia.__columna_familia__ == "id"
