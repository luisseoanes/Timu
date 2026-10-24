"""Datos de demostracion para ver el panel con vida en desarrollo.

Recorre la API como lo haria el panel (no escribe en la base por debajo): asi los datos
pasan por las mismas reglas de negocio, auditoria y eventos que los reales. Es
repetible: lo que ya existe (por documento, codigo o nombre) no se duplica.

Uso, con el stack arriba y despues de cargar_catalogos y seed:
    docker compose exec api python -m scripts.datos_demo

Nunca contra produccion: se niega si ENVIRONMENT no es local.
"""

import os
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

BENEFICIOS = [
    {"tipo_servicio_codigo": "consulta_domiciliaria", "cupo": 6, "periodo_cupo": "anual"},
    {"tipo_servicio_codigo": "vacunacion", "cupo": 4, "periodo_cupo": "anual"},
    {"tipo_servicio_codigo": "desparasitacion", "cupo": 4, "periodo_cupo": "anual"},
    {"tipo_servicio_codigo": "control_post", "cupo": 4, "periodo_cupo": "anual"},
    {"tipo_servicio_codigo": "orientacion_virtual", "cupo": None, "periodo_cupo": "anual"},
]


class Cliente:
    def __init__(self) -> None:
        self.http = httpx.Client(base_url=API, timeout=30)
        resp = self.http.post(
            "/auth/login", data={"username": "admin@timu.co", "password": "cambiar123"}
        )
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
        if not plan["beneficios"]:
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

    print("Listo. Ingresa a http://localhost:5173 con admin@timu.co / cambiar123")


if __name__ == "__main__":
    main()
