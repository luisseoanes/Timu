"""Seccion 11 Matriz de permisos: ningun endpoint queda abierto por omision."""

import re
from typing import Any

import pytest
from httpx import AsyncClient

from app.api import perfiles
from app.core.enums import Rol
from app.main import app
from tests.conftest import crear_usuario, login


def rutas() -> dict[str, Any]:
    return perfiles.rutas(app)


def matriz() -> dict[str, frozenset[Rol] | str]:
    return perfiles.matriz(app)


def test_la_guarda_recorre_todas_las_rutas_de_la_api():
    """Si FastAPI vuelve a cambiar como guarda las rutas, esta guarda no puede quedarse
    mirando un subconjunto: todo lo que publica el OpenAPI tiene que estar en `rutas()`."""
    publicadas = {
        f"{metodo.upper()} {ruta}"
        for ruta, operaciones in app.openapi()["paths"].items()
        for metodo in operaciones
        if not ruta.startswith("/__")  # las que montan las propias pruebas
    }
    recorridas = {f"{metodo} {ruta.path}" for ruta in rutas().values() for metodo in ruta.methods}
    assert publicadas - recorridas == set()


def test_toda_ruta_declara_permisos():
    declaradas = matriz()
    sin_declarar = [clave for clave in rutas() if clave not in declaradas]
    assert not sin_declarar, f"Rutas sin permisos declarados: {sin_declarar}"


# Unico conjunto de rutas abiertas admitido. Agregar aqui exige una razon.
PUBLICAS_ESPERADAS = {
    "GET /health",
    "GET /health/live",
    "POST /api/v1/auth/login",
    "POST /api/v1/auth/refresh",
    "POST /api/v1/auth/recuperar",
    # R3-PUB-01 la pantalla del enlace dice de entrada si sirve, sin gastarlo.
    "POST /api/v1/auth/enlace",
    "POST /api/v1/auth/restablecer",
    "POST /api/v1/auth/codigo",  # Seccion 11 ingreso del portal por WhatsApp
    "POST /api/v1/auth/codigo/verificacion",
    "POST /api/v1/formularios/familia",
    # 6.1 Registro en linea: catalogo y cotizacion publicos; el formulario posterior al
    # pago se autoriza con el token del registro.
    "GET /api/v1/afiliaciones/registro/ciudades",
    "GET /api/v1/afiliaciones/registro/planes",
    "POST /api/v1/afiliaciones/registro/cotizacion",
    "POST /api/v1/afiliaciones/registro",
    "POST /api/v1/afiliaciones/registro/consulta",
    "POST /api/v1/afiliaciones/registro/completar",
    "POST /api/v1/afiliaciones/registro/reintentar",
    # R3-PUB-02: el modelo del contrato antes de pagar y el contacto de TIMU.
    "POST /api/v1/afiliaciones/registro/contrato-modelo",
    "GET /api/v1/afiliaciones/registro/contacto",
    # R3-PUB-04: lo institucional y de contacto de TIMU que dice la portada.
    "GET /api/v1/institucional",
    "GET /api/v1/aliadas/publicas",
    "POST /api/v1/comercial/contacto",  # el formulario de la portada
    "GET /api/v1/webhooks/whatsapp",
    "POST /api/v1/webhooks/whatsapp",  # autorizada por firma de Meta
    "POST /api/v1/webhooks/pagos",  # autorizada por firma de la pasarela
    "GET /api/v1/verificacion/carnets/{codigo}",  # 6.15 la valida un tercero
    "GET /api/v1/encuestas/respuesta/{token}",  # 6.20 autorizada por el token
    "POST /api/v1/encuestas/respuesta/{token}",
}


def test_rutas_publicas_son_exactamente_las_esperadas():
    publicas = {k for k, v in matriz().items() if v == "publico"}
    assert publicas == PUBLICAS_ESPERADAS


# Lecturas compartidas con el portal: las acota el alcance por fila (app/core/scope.py),
# que tiene su propia prueba en test_alcance.py.
LECTURAS_CON_ALCANCE = {"GET /api/v1/familias", "GET /api/v1/familias/{familia_id}"}


def test_ninguna_ruta_interna_admite_al_portal():
    """El rol familia solo entra a /portal, /auth, a los catalogos de lectura y a las
    lecturas acotadas por alcance."""
    permitidas_familia = ("/api/v1/portal", "/api/v1/auth", "/api/v1/catalogos")
    for clave, roles in matriz().items():
        if roles == "publico" or Rol.FAMILIA not in roles or clave in LECTURAS_CON_ALCANCE:
            continue
        ruta = clave.split(" ", 1)[1]
        assert ruta.startswith(permitidas_familia), f"{clave} admite al rol familia"


# Perfiles de cada ruta del equipo, de docs/perfiles-y-permisos.md (Seccion 12: "cada perfil
# debera contar con permisos diferenciados de acuerdo con sus funciones"). Letras: A admin,
# G gerencia, C comercial, T atencion al cliente, O operaciones, M medico, F familia. El portal,
# la clinica aliada y las rutas publicas tienen sus propias pruebas arriba y en test_alcance.py.
_LETRAS = {
    "A": Rol.ADMIN,
    "G": Rol.GERENCIA,
    "C": Rol.COMERCIAL,
    "T": Rol.ATENCION_CLIENTE,
    "O": Rol.OPERACIONES,
    "M": Rol.MEDICO,
    "F": Rol.FAMILIA,
    "L": Rol.ALIADA,
}
MATRIZ = {
    "GET /afiliaciones": "C",
    "POST /afiliaciones/asistida": "C",
    "GET /afiliaciones/lineas": "CTO",
    "GET /afiliaciones/{solicitud_id}": "C",
    "POST /afiliaciones/{solicitud_id}/pago-manual": "C",
    "POST /agenda/bloqueos": "O",
    "GET /agenda/disponibilidad": "TO",
    "GET /agenda/franjas": "TO",
    "POST /agenda/franjas": "O",
    "PATCH /agenda/franjas/{franja_id}": "O",
    "GET /aliadas": "TO",
    "POST /aliadas": "O",
    "GET /aliadas/liquidacion": "GO",
    "GET /aliadas/remisiones": "T",
    "POST /aliadas/remisiones": "T",
    "GET /aliadas/remisiones/recuentos": "T",
    "POST /aliadas/remisiones/{remision_id}/anulacion": "T",
    "PATCH /aliadas/{clinica_id}": "O",
    "GET /aliadas/{clinica_id}/convenios": "TO",
    "POST /aliadas/{clinica_id}/convenios": "O",
    "DELETE /aliadas/{clinica_id}/logo": "O",
    "PUT /aliadas/{clinica_id}/logo": "O",
    "GET /auth/equipo": "CTOM",
    "POST /auth/logout": "AGCTOMFL",
    "POST /auth/logout-todas": "AGCTOMFL",
    "GET /auth/me": "AGCTOMFL",
    "GET /auth/usuarios": "A",
    "POST /auth/usuarios": "A",
    "GET /auth/usuarios/recuentos": "A",
    "PATCH /auth/usuarios/{usuario_id}": "A",
    "GET /campanas": "C",
    "POST /campanas": "C",
    "PUT /campanas/{campana_id}": "C",
    "POST /campanas/{campana_id}/cancelacion": "C",
    "GET /campanas/{campana_id}/ejecuciones": "C",
    "GET /campanas/{campana_id}/previsualizacion": "C",
    "POST /campanas/{campana_id}/programacion": "C",
    "GET /campanas/{campana_id}/resultados": "C",
    "GET /cartera/contratos": "CT",
    "POST /cartera/contratos": "C",
    "GET /cartera/contratos/recuentos": "CT",
    "GET /cartera/contratos/{contrato_id}": "CT",
    "POST /cartera/contratos/{contrato_id}/cancelar": "T",
    "GET /cartera/contratos/{contrato_id}/documento": "CT",
    "POST /cartera/contratos/{contrato_id}/renovar": "C",
    "GET /cartera/eventos-pasarela": "T",
    "GET /cartera/eventos-pasarela/recuentos": "T",
    "POST /cartera/eventos-pasarela/{evento_id}/reprocesar": "T",
    "GET /cartera/familias/{familia_id}/estado-cuenta": "CT",
    "POST /cartera/medios-pago": "T",
    "DELETE /cartera/medios-pago/{medio_id}": "T",
    "POST /cartera/pagos": "T",
    "POST /cartera/transacciones/{transaccion_id}/recuperar": "T",
    "POST /catalogos/cargar": "A",
    "GET /catalogos/ciudades": "AGCTOMF",
    "GET /catalogos/especies": "AGCTOMF",
    "GET /catalogos/esquemas-preventivos": "AGCTOMF",
    "POST /catalogos/esquemas-preventivos": "A",
    "PATCH /catalogos/esquemas-preventivos/{codigo}": "A",
    "GET /catalogos/tipos-servicio": "AGCTOMF",
    "PATCH /catalogos/{catalogo}/{codigo}/activo": "A",
    "GET /clinica/adjuntos/{adjunto_id}/url": "M",
    "GET /clinica/borradores": "M",
    "POST /clinica/historias": "M",
    "GET /clinica/historias/{historia_id}": "M",
    "PATCH /clinica/historias/{historia_id}": "M",
    "GET /clinica/historias/{historia_id}/adjuntos": "M",
    "POST /clinica/historias/{historia_id}/adjuntos": "M",
    "POST /clinica/historias/{historia_id}/correccion": "M",
    "POST /clinica/historias/{historia_id}/firma": "M",
    "POST /clinica/historias/{historia_id}/formulas": "M",
    "GET /clinica/mascotas/{mascota_id}/historia": "M",
    "GET /clinica/plantillas": "M",
    "POST /clinica/plantillas": "M",
    "GET /clinica/plantillas/uso": "M",
    "PATCH /clinica/plantillas/{codigo}": "M",
    "GET /clinica/respuestas-virtuales": "M",
    "POST /clinica/respuestas-virtuales": "M",
    "POST /clinica/respuestas-virtuales/{codigo}/aprobacion": "M",
    "POST /clinica/virtual": "M",
    "GET /clinica/virtual/cola": "M",
    "POST /clinica/virtual/{solicitud_id}/borrador": "M",
    "POST /clinica/virtual/{solicitud_id}/cierre": "M",
    "POST /clinica/virtual/{solicitud_id}/respuesta": "M",
    "POST /clinica/virtual/{solicitud_id}/toma": "M",
    "GET /comercial/arbol": "AC",
    "PUT /comercial/arbol": "A",
    "GET /comercial/conversaciones": "C",
    "POST /comercial/conversaciones/{conversacion_id}/liberacion": "C",
    "POST /comercial/conversaciones/{conversacion_id}/mensajes": "C",
    "GET /comercial/embudo": "C",
    "GET /comercial/interesados": "C",
    "POST /comercial/interesados": "C",
    "GET /comercial/interesados/recuentos": "C",
    "GET /comercial/interesados/{interesado_id}": "C",
    "PATCH /comercial/interesados/{interesado_id}": "C",
    "GET /comercial/interesados/{interesado_id}/conversacion": "C",
    "POST /comercial/interesados/{interesado_id}/perdida": "C",
    "POST /comercial/interesados/{interesado_id}/reactivacion": "C",
    "GET /comunicaciones/bajas": "CT",
    "POST /comunicaciones/bajas": "CT",
    "DELETE /comunicaciones/bajas/{destino}": "T",
    "GET /comunicaciones/mensajes": "CT",
    "POST /comunicaciones/mensajes/plantilla": "CT",
    "POST /comunicaciones/mensajes/texto": "CT",
    "GET /comunicaciones/plantillas": "ACT",
    "POST /comunicaciones/plantillas": "A",
    "PATCH /comunicaciones/plantillas/{plantilla_id}/estado": "A",
    "GET /dashboard/definiciones": "GCTO",
    "GET /dashboard/evolucion": "GCTO",
    "GET /dashboard/indicadores": "GCTO",
    "GET /dashboard/reportes": "G",
    "POST /dashboard/reportes": "G",
    "PUT /dashboard/reportes/{reporte_id}": "G",
    "PATCH /documentos/{documento_id}": "T",
    "POST /documentos/{documento_id}/baja": "T",
    "GET /encuestas": "GT",
    "GET /encuestas/configuracion": "A",
    "PUT /encuestas/configuracion": "A",
    "GET /encuestas/resumen": "G",
    "GET /familias": "CTOF",
    "POST /familias": "CT",
    "GET /familias/supresion": "A",
    "GET /familias/{familia_id}": "CTOF",
    "PATCH /familias/{familia_id}": "CT",
    "POST /familias/{familia_id}/acceso-portal": "T",
    "POST /familias/{familia_id}/anonimizar": "A",
    "POST /familias/{familia_id}/baja": "T",
    "POST /familias/{familia_id}/contactos": "T",
    "PATCH /familias/{familia_id}/contactos/{contacto_id}": "T",
    "POST /familias/{familia_id}/contactos/{contacto_id}/baja": "T",
    "GET /familias/{familia_id}/documentos": "T",
    "POST /familias/{familia_id}/documentos": "T",
    "POST /familias/{familia_id}/estado": "T",
    "GET /familias/{familia_id}/historial": "CT",
    "GET /familias/{familia_id}/linea": "CTO",
    "POST /familias/{familia_id}/mascotas": "CT",
    "GET /ia/casos": "A",
    "POST /ia/casos": "A",
    "GET /ia/consultas": "A",
    "GET /ia/consumo": "A",
    "PUT /ia/presupuesto": "A",
    "GET /ia/prompts": "A",
    "POST /ia/prompts": "A",
    "POST /ia/prompts/sembrar": "A",
    "POST /ia/prompts/{prompt_id}/activacion": "A",
    "POST /ia/prompts/{prompt_id}/evaluacion": "A",
    "PUT /institucional": "A",
    "GET /mascotas/{mascota_id}": "CTOM",
    "PATCH /mascotas/{mascota_id}": "T",
    "POST /mascotas/{mascota_id}/baja": "T",
    "DELETE /mascotas/{mascota_id}/foto": "T",
    "PUT /mascotas/{mascota_id}/foto": "T",
    "GET /pendientes": "TOM",
    "POST /pendientes/{pendiente_id}/autorizacion": "T",
    "POST /pendientes/{pendiente_id}/avance": "TO",
    "GET /planes": "AGCTOM",
    "POST /planes": "A",
    "POST /planes/contratos/{contrato_id}/cambio": "T",
    "POST /planes/cotizacion": "CT",
    "GET /planes/recomendacion": "C",
    "GET /planes/{plan_id}": "AGCTOM",
    "PATCH /planes/{plan_id}": "A",
    "PUT /planes/{plan_id}/adicionales": "A",
    "PUT /planes/{plan_id}/beneficios": "A",
    "PUT /planes/{plan_id}/ciudades": "A",
    "PUT /planes/{plan_id}/tarifas": "A",
    "GET /preventivos": "TOM",
    "POST /preventivos/autorizaciones": "T",
    "GET /preventivos/bandeja": "TOM",
    "GET /preventivos/bandeja/recuentos": "TOM",
    "POST /preventivos/mascotas/{mascota_id}/calendario": "TM",
    "GET /preventivos/mascotas/{mascota_id}/carnet": "TM",
    "POST /preventivos/mascotas/{mascota_id}/carnet/pdf": "TM",
    "POST /preventivos/{evento_id}/agendar": "TO",
    "POST /preventivos/{evento_id}/aplicacion": "M",
    "POST /preventivos/{evento_id}/autorizacion": "T",
    "POST /preventivos/{evento_id}/cancelacion": "T",
    "GET /reglas": "A",
    "POST /reglas": "A",
    "POST /reglas/describir": "A",
    "GET /reglas/eventos": "A",
    "POST /reglas/probar": "A",
    "GET /reglas/plantillas-faltantes": "A",
    "PATCH /reglas/{regla_id}": "A",
    "GET /rutas": "OM",
    "POST /rutas/paradas/{parada_id}/en-camino": "OM",
    "POST /rutas/paradas/{parada_id}/llegada": "OM",
    "POST /rutas/paradas/{parada_id}/omision": "OM",
    "POST /rutas/paradas/{parada_id}/salida": "OM",
    "POST /rutas/planificaciones": "O",
    "GET /rutas/planificaciones/{planificacion_id}": "O",
    "GET /rutas/por-rutear": "O",
    "GET /rutas/{ruta_id}": "OM",
    "POST /rutas/{ruta_id}/cancelacion": "O",
    "POST /rutas/{ruta_id}/inicio": "OM",
    "POST /rutas/{ruta_id}/paradas": "O",
    "GET /segmentos": "C",
    "POST /segmentos": "C",
    "POST /segmentos/previsualizacion": "C",
    "GET /segmentos/{segmento_id}/conteo": "C",
    "GET /servicios": "TOM",
    "POST /servicios": "TO",
    "GET /servicios/elegibilidad": "TO",
    "GET /servicios/resumen": "TOM",
    "GET /servicios/{servicio_id}": "TOM",
    "POST /servicios/{servicio_id}/autorizar": "M",
    "POST /servicios/{servicio_id}/estado": "TOM",
    "GET /servicios/{servicio_id}/pasos": "TOM",
    "PUT /servicios/{servicio_id}/pasos/{paso_codigo}": "M",
    "POST /servicios/{servicio_id}/pendientes": "M",
    "POST /servicios/{servicio_id}/reprogramar": "TO",
    "GET /tareas": "CTOM",
    "POST /tareas": "CTOM",
    "PATCH /tareas/{tarea_id}/asignacion": "CTOM",
    "POST /tareas/{tarea_id}/cerrar": "CTOM",
    "POST /tareas/{tarea_id}/iniciar": "CTOM",
}


def test_cada_ruta_del_equipo_admite_exactamente_sus_perfiles():
    """Un perfil de mas en una ruta es informacion o una accion que no le toca; uno de menos,
    una pantalla rota. La matriz cambia aqui y en docs/perfiles-y-permisos.md a la vez."""
    reales = {
        clave.split(" ", 1)[0] + " " + clave.split(" ", 1)[1].removeprefix("/api/v1"): roles
        for clave, roles in matriz().items()
        if roles != "publico"
        and not clave.split(" ", 1)[1].startswith(("/api/v1/portal", "/health"))
        and "/mi-clinica" not in clave
    }
    esperadas = {
        ruta: frozenset(_LETRAS[letra] for letra in letras) for ruta, letras in MATRIZ.items()
    }
    distintas = {
        ruta: (sorted(reales.get(ruta, set())), sorted(esperadas.get(ruta, set())))
        for ruta in reales.keys() | esperadas.keys()
        if reales.get(ruta) != esperadas.get(ruta)
    }
    assert not distintas, f"Perfiles distintos de los esperados (reales, esperados): {distintas}"


def test_el_administrador_no_ve_nada_operativo():
    """Decidido con el usuario el 2026-11-19: configura la plataforma y nada mas."""
    operativas = (
        "/familias",
        "/mascotas",
        "/cartera",
        "/servicios",
        "/rutas",
        "/clinica",
        "/tareas",
        "/preventivos",
        "/aliadas/remisiones",
        "/comercial/interesados",
    )
    abiertas = [
        ruta
        for ruta, letras in MATRIZ.items()
        if "A" in letras
        and ruta.split(" ", 1)[1].startswith(operativas)
        and ruta not in ("POST /familias/{familia_id}/anonimizar", "GET /familias/supresion")
    ]
    assert abiertas == []


def _ejemplo(path: str) -> str:
    return re.sub(r"\{[^}]+\}", "00000000-0000-0000-0000-000000000000", path)


PROTEGIDAS = sorted(k for k, v in matriz().items() if v != "publico")


@pytest.mark.parametrize("clave", PROTEGIDAS)
async def test_sin_token_responde_401(client: AsyncClient, clave: str):
    metodos, ruta = clave.split(" ", 1)
    metodo = metodos.split(",")[0]
    resp = await client.request(metodo, _ejemplo(ruta))
    assert resp.status_code == 401, f"{clave} respondio {resp.status_code}"


async def test_perfil_no_autorizado_recibe_403(client: AsyncClient, db):
    await crear_usuario(db, "medico@timu.co", Rol.MEDICO)
    headers = await login(client, "medico@timu.co")
    resp = await client.post(
        "/api/v1/auth/usuarios",
        json={"email": "x@timu.co", "nombre": "X", "password": "12345678"},
        headers=headers,
    )
    assert resp.status_code == 403
    assert resp.json()["codigo"] == "prohibido"
