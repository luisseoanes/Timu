"""Datos de demostracion para ver el panel con vida en desarrollo.

Recorre la API como lo haria el panel (no escribe en la base por debajo): asi los datos
pasan por las mismas reglas de negocio, auditoria y eventos que los reales. Es
repetible: lo que ya existe (por documento, codigo o nombre) no se duplica.

Uso, con el stack arriba y despues de cargar_catalogos y seed:
    docker compose exec api python -m scripts.datos_demo

Nunca contra produccion: se niega si ENVIRONMENT no es local.
"""

import os
import re
import sys
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from app.core.config import settings

API = os.environ.get("DEMO_API", "http://localhost:8000/api/v1")
BOGOTA = ZoneInfo("America/Bogota")

FAMILIAS: list[dict[str, Any]] = [
    {
        "titular_nombre": "Ana Ruiz",
        "documento": "1020304050",
        "telefono": "3001112233",
        "email": "ana@example.com",
        "ciudad": "Bogota",
        "direccion": "Calle 80 # 15-20",
        "mascotas": [
            {"nombre": "Luna", "especie": "canino", "sexo": "hembra", "raza": "Criolla"},
            {"nombre": "Michi", "especie": "felino", "sexo": "macho"},
        ],
        "plan": "familiar",
    },
    {
        "titular_nombre": "Carlos Perez",
        "documento": "79123456",
        "telefono": "3104445566",
        "ciudad": "Bogota",
        "direccion": "Carrera 7 # 120-45",
        "mascotas": [{"nombre": "Toby", "especie": "canino", "sexo": "macho", "raza": "Beagle"}],
        "plan": "individual",
    },
    {
        "titular_nombre": "Laura Gomez",
        "documento": "52987654",
        "telefono": "3157778899",
        "ciudad": "Bogota",
        "direccion": "Avenida 19 # 100-12",
        "mascotas": [{"nombre": "Nala", "especie": "felino", "sexo": "hembra"}],
        "plan": "individual",
    },
    {
        "titular_nombre": "Jorge Ramirez",
        "documento": "80456123",
        "telefono": "3209990011",
        "email": "jorge@example.com",
        "ciudad": "Bogota",
        "direccion": "Calle 140 # 9-30",
        "mascotas": [
            {"nombre": "Rocky", "especie": "canino", "sexo": "macho", "raza": "Labrador"},
            {"nombre": "Kira", "especie": "canino", "sexo": "hembra", "raza": "Golden"},
        ],
        "plan": "familiar",
    },
    {
        "titular_nombre": "Marcela Torres",
        "documento": "1032456789",
        "telefono": "3015556677",
        "ciudad": "Medellin",
        "mascotas": [{"nombre": "Simba", "especie": "felino", "sexo": "macho"}],
        "plan": None,
    },
]

INTERESADOS = [
    ("Paula Diaz", "3005551234", "whatsapp"),
    ("Andres Mejia", "3112223344", "referido"),
    ("Sofia Herrera", "3206667788", "evento"),
    ("Camilo Rojas", "3013334455", "formulario"),
]

# Barrios del norte de Bogota, para que el optimizador de rutas tenga donde trabajar.
UBICACIONES = [
    (4.6683, -74.0548),
    (4.7016, -74.0306),
    (4.6858, -74.0567),
    (4.7239, -74.0402),
]

BENEFICIOS = [
    {"tipo_servicio_codigo": "consulta_domiciliaria", "cupo": 6, "periodo_cupo": "anual"},
    {"tipo_servicio_codigo": "vacunacion", "cupo": 4, "periodo_cupo": "anual"},
    {"tipo_servicio_codigo": "desparasitacion", "cupo": 4, "periodo_cupo": "anual"},
    {"tipo_servicio_codigo": "control_post", "cupo": 4, "periodo_cupo": "anual"},
    {"tipo_servicio_codigo": "orientacion_virtual", "cupo": None, "periodo_cupo": "anual"},
    {"tipo_servicio_codigo": "atencion_aliada", "cupo": 2, "periodo_cupo": "anual"},
]


EQUIPO = [
    ("medico@timu.co", "Dra. Sara Martinez", "medico"),
    ("operaciones@timu.co", "Carlos Pena", "operaciones"),
    ("comercial@timu.co", "Valentina Rios", "comercial"),
]
CLAVE_EQUIPO = "demo12345"


class Cliente:
    def __init__(self, email: str = "admin@timu.co", clave: str = "cambiar123") -> None:
        self.http = httpx.Client(base_url=API, timeout=30)
        resp = self.http.post("/auth/login", data={"username": email, "password": clave})
        resp.raise_for_status()

    def get(self, ruta: str, **params: Any) -> Any:
        resp = self.http.get(ruta, params=params)
        resp.raise_for_status()
        return resp.json()

    def post(self, ruta: str, cuerpo: Any = None, *, permitir: tuple[int, ...] = ()) -> Any:
        resp = self.http.post(ruta, json=cuerpo)
        if resp.status_code in permitir:
            return None
        if resp.is_error:
            print(f"  ! {ruta}: {resp.status_code} {resp.text[:200]}")
            return None
        return resp.json() if resp.content else None

    def put(self, ruta: str, cuerpo: Any) -> Any:
        resp = self.http.put(ruta, json=cuerpo)
        resp.raise_for_status()
        return resp.json()


def proximo_habil(desde: date, dias: int) -> date:
    d = desde + timedelta(days=dias)
    while d.weekday() == 6:  # domingo sin franjas
        d += timedelta(days=1)
    return d


def main() -> None:
    if settings.ENVIRONMENT != "local":
        sys.exit("datos_demo solo corre en ENVIRONMENT=local")
    c = Cliente()
    hoy = datetime.now(BOGOTA).date()

    print("Planes y beneficios")
    planes = {p["codigo"]: p for p in c.get("/planes")}
    for plan in planes.values():
        codigos = {b["tipo_servicio_codigo"] for b in plan["beneficios"]}
        if codigos != {b["tipo_servicio_codigo"] for b in BENEFICIOS}:
            c.put(f"/planes/{plan['id']}/beneficios", BENEFICIOS)

    print("Franjas de agenda")
    existentes = {(f["ciudad"], f["dia_semana"], f["modalidad"]) for f in c.get("/agenda/franjas")}
    for ciudad in ("Bogota", "Medellin"):
        for modalidad in ("domiciliario", "preventivo"):
            for dia in range(6):
                if (ciudad, dia, modalidad) not in existentes:
                    c.post(
                        "/agenda/franjas",
                        {
                            "ciudad": ciudad,
                            "modalidad": modalidad,
                            "dia_semana": dia,
                            "hora_inicio": "08:00",
                            "hora_fin": "17:00",
                            "capacidad": 2,
                        },
                    )

    print("Familias y contratos")
    familias: list[dict[str, Any]] = []
    for datos in FAMILIAS:
        encontrada = c.get("/familias", q=datos["documento"])["items"]
        if encontrada:
            familia = encontrada[0]
        else:
            cuerpo = {k: v for k, v in datos.items() if k != "plan"}
            familia = c.post("/familias", cuerpo)
        familias.append(familia)
        if datos["plan"]:
            estado = c.http.get(f"/cartera/familias/{familia['id']}/estado-cuenta")
            if estado.status_code == 404:
                inicio = (hoy - timedelta(days=75)).isoformat()
                c.post(
                    "/cartera/contratos",
                    {
                        "familia_id": familia["id"],
                        "plan_id": planes[datos["plan"]]["id"],
                        "fecha_inicio": inicio,
                    },
                )

    print("Ubicaciones (sin Google Maps no se geocodifica: se fijan a mano)")
    for familia, (lat, lng) in zip(familias, UBICACIONES, strict=False):
        if familia.get("latitud") is None and familia["ciudad"] == "Bogota":
            resp = c.http.patch(
                f"/familias/{familia['id']}", json={"latitud": lat, "longitud": lng}
            )
            if resp.is_success:
                familia.update(resp.json())

    print("Servicios")
    if c.get("/servicios", limit=1)["total"] == 0:
        agenda = [
            (0, "consulta_domiciliaria", "Revisar oido izquierdo"),
            (0, "vacunacion", None),
            (1, "consulta_domiciliaria", "Control de peso"),
            (1, "desparasitacion", None),
            (2, "control_post", "Retiro de puntos"),
            (3, "consulta_domiciliaria", None),
        ]
        for i, (dias, tipo, obs) in enumerate(agenda):
            familia = familias[i % 4]
            dia = proximo_habil(hoy, dias)
            cupos = c.get(
                "/agenda/disponibilidad", fecha=dia.isoformat(), ciudad="Bogota", tipo_codigo=tipo
            )
            libres = [x for x in cupos if x["disponibles"] > 0]
            if not libres:
                continue
            mascota = (familia.get("mascotas") or [{}])[0].get("id")
            c.post(
                "/servicios",
                {
                    "familia_id": familia["id"],
                    "mascota_id": mascota,
                    "tipo_codigo": tipo,
                    "inicio": libres[min(i, len(libres) - 1)]["inicio"],
                    "observaciones": obs,
                },
            )

    print("Tareas")
    if c.get("/tareas", limit=1)["total"] == 0:
        tareas = [
            ("Confirmar direccion de la visita", "operaciones", "alta", 0),
            ("Llamar por cuota vencida", "cartera", "alta", -2),
            ("Enviar cotizacion del plan familiar", "comercial", "media", 3),
            ("Revisar resultado de laboratorio", "medico", "media", 1),
        ]
        for i, (titulo, area, prioridad, dias) in enumerate(tareas):
            c.post(
                "/tareas",
                {
                    "titulo": titulo,
                    "area": area,
                    "prioridad": prioridad,
                    "vence_en_dias": max(dias, 0),
                    "familia_id": familias[i % len(familias)]["id"],
                },
            )

    print("Equipo de prueba")
    existentes_u = {u["email"] for u in c.get("/auth/usuarios", limit=200)["items"]}
    for email, nombre, rol in EQUIPO:
        if email not in existentes_u:
            c.post(
                "/auth/usuarios",
                {"email": email, "nombre": nombre, "rol": rol, "password": CLAVE_EQUIPO},
            )

    print("Preventivos")
    for familia in familias:
        for mascota in familia.get("mascotas") or []:
            if c.get("/preventivos", mascota_id=mascota["id"], limit=1)["total"] == 0:
                c.post(f"/preventivos/mascotas/{mascota['id']}/calendario", permitir=(422,))

    print("Clinica")
    medico = Cliente("medico@timu.co", CLAVE_EQUIPO)
    luna = familias[0]["mascotas"][0]
    if not medico.get(f"/clinica/mascotas/{luna['id']}/historia"):
        entrada = medico.post(
            "/clinica/historias",
            {
                "mascota_id": luna["id"],
                "tipo": "domiciliaria",
                "fecha": (hoy - timedelta(days=20)).isoformat(),
                "motivo": "Rasca el oido izquierdo desde hace una semana",
                "anamnesis": "Sin cambios en alimentacion. Bano hace 10 dias.",
                "examen_fisico": "Conducto auditivo izquierdo eritematoso, cerumen oscuro.",
                "diagnostico": "Otitis externa izquierda",
                "tratamiento": "Limpieza otica y gotas cada 12 horas por 7 dias.",
            },
        )
        if entrada:
            medico.post(f"/clinica/historias/{entrada['id']}/firma")
        medico.post(
            "/clinica/historias",
            {
                "mascota_id": luna["id"],
                "tipo": "domiciliaria",
                "motivo": "Control de otitis",
                "examen_fisico": "Conducto sin eritema.",
            },
        )
    respuestas = {r["codigo"] for r in c.get("/clinica/respuestas-virtuales")}
    if "control_alimentacion" not in respuestas:
        c.post(
            "/clinica/respuestas-virtuales",
            {
                "codigo": "control_alimentacion",
                "titulo": "Cambio de alimento",
                "cuerpo": (
                    "Para {{1}} recomendamos hacer el cambio de alimento en 7 dias, mezclando "
                    "cada dia un poco mas del nuevo. Si hay vomito o diarrea, escribenos."
                ),
                "variables": ["mascota"],
            },
        )
        c.post("/clinica/respuestas-virtuales/control_alimentacion/aprobacion")
    if not c.get("/clinica/virtual/cola"):
        c.post(
            "/clinica/virtual",
            {
                "mascota_id": familias[1]["mascotas"][0]["id"],
                "motivo": "Queremos cambiarle el concentrado, como lo hacemos?",
                "prioridad": "baja",
            },
        )

    print("Rutas de hoy")
    if not c.get("/rutas", fecha=hoy.isoformat(), ciudad="Bogota"):
        equipo = [m["id"] for m in c.get("/auth/equipo") if m["rol"] in ("medico", "operaciones")]
        if equipo and c.get("/rutas/por-rutear", fecha=hoy.isoformat(), ciudad="Bogota"):
            c.post(
                "/rutas/planificaciones",
                {"fecha": hoy.isoformat(), "ciudad": "Bogota", "responsables": equipo[:2]},
            )

    print("Comercial")
    if c.get("/comercial/interesados", limit=1)["total"] == 0:
        for nombre, telefono, origen in INTERESADOS:
            c.post(
                "/comercial/interesados",
                {"nombre": nombre, "telefono": telefono, "ciudad": "Bogota", "origen": origen},
            )
        for i, interesado in enumerate(c.get("/comercial/interesados", limit=10)["items"]):
            etapa = ("contactado", "cotizado", "en_afiliacion")[i % 3]
            c.http.patch(f"/comercial/interesados/{interesado['id']}", json={"etapa": etapa})

    print("Campanas")
    plantillas = {p["nombre"]: p for p in c.get("/comunicaciones/plantillas")}
    if "recordatorio_renovacion" not in plantillas:
        nueva = c.post(
            "/comunicaciones/plantillas",
            {
                "nombre": "recordatorio_renovacion",
                "categoria": "utility",
                "cuerpo": "Hola {{1}}, tu {{2}} se renueva pronto. Gracias por confiar en TIMU.",
                "variables": ["1", "2"],
            },
        )
        if nueva:
            c.http.patch(
                f"/comunicaciones/plantillas/{nueva['id']}/estado",
                json={"estado_aprobacion": "aprobada", "activa": True},
            )
    if not c.get("/campanas"):
        c.post(
            "/campanas",
            {
                "nombre": "Renovaciones del mes",
                "plantilla": "recordatorio_renovacion",
                "variables": ["titular_nombre", "plan"],
                "segmento": {"estados": ["activa"], "renovacion_en_dias": 400},
            },
        )

    print("Clinicas aliadas")
    if not c.get("/aliadas"):
        clinica = c.post(
            "/aliadas",
            {
                "nombre": "Clinica Veterinaria del Norte",
                "nit": "900123456",
                "ciudad": "Bogota",
                "direccion": "Calle 127 # 15-30",
                "telefono": "6017654321",
                "servicios": "Rayos X, ecografia, hospitalizacion y cirugia",
            },
        )
        if clinica:
            c.post(
                f"/aliadas/{clinica['id']}/convenios",
                {
                    "beneficio": "Radiografia",
                    "cobertura_pct": 80,
                    "tarifa": "120000",
                    "tope_cubierto": "200000",
                    "vigente_desde": (hoy - timedelta(days=30)).isoformat(),
                },
            )
            c.post(
                "/auth/usuarios",
                {
                    "email": "aliada@timu.co",
                    "nombre": "Recepcion Clinica del Norte",
                    "rol": "aliada",
                    "password": CLAVE_EQUIPO,
                    "clinica_aliada_id": clinica["id"],
                },
            )
    clinicas = c.get("/aliadas")
    if clinicas and not c.get("/aliadas/remisiones"):
        c.post(
            "/aliadas/remisiones",
            {
                "clinica_id": clinicas[0]["id"],
                "mascota_id": familias[3]["mascotas"][0]["id"],
                "motivo": "Radiografia de cadera por cojera",
            },
        )

    print("Portal de Ana Ruiz")
    ana = c.get(f"/familias/{familias[0]['id']}")
    puede_entrar = httpx.post(
        f"{API}/auth/login", data={"username": ana["email"], "password": CLAVE_EQUIPO}
    ).is_success
    if not puede_entrar:
        if not ana.get("usuario_portal_id"):
            c.post(f"/familias/{ana['id']}/acceso-portal")
        # Sin WhatsApp ni correo configurados el enlace queda en el mensaje: se toma de ahi.
        # El aviso de activacion va al usuario, no a la familia: se busca entre los recientes.
        recientes = c.get("/comunicaciones/mensajes", limit=50, orden="-created_at")["items"]
        for mensaje in recientes:
            token = re.search(r"activar\?token=([\w-]+)", mensaje.get("contenido") or "")
            if token:
                c.post("/auth/restablecer", {"token": token.group(1), "password": CLAVE_EQUIPO})
                break

    print("Listo. Ingresa a http://localhost:5173 con admin@timu.co / cambiar123")
    print(f"Equipo de prueba (clave {CLAVE_EQUIPO}): " + ", ".join(e for e, _, _ in EQUIPO))
    print(f"Clinica aliada: aliada@timu.co · Portal: ana@example.com (clave {CLAVE_EQUIPO})")


if __name__ == "__main__":
    main()
