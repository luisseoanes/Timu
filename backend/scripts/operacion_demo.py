"""Dos meses de operacion para explorar el sistema con datos que recorren todos sus casos (DEU-14).

`datos_demo` deja lo minimo que piden las pruebas del panel; este script, encima, siembra ocho
semanas de operacion: familias en cada estado de cartera con sus pagos, rutas de dias pasados
con sus visitas, consultas firmadas, una parada omitida y servicios cancelados, preventivos
aplicados y encuestas respondidas.

Como se hace (decidido con el usuario el 2026-11-16): todo se crea por la API, con sus reglas,
y despues se corre al pasado. La API no agenda en el pasado, asi que cada dia de operacion se
agenda y se recorre en un dia futuro de reserva y, al terminarlo, sus fechas se llevan al dia
que le toca. Ese paso escribe con la conexion del dueno del esquema: es la unica que puede
fechar una consulta ya firmada. Las marcas que la operacion pone con la hora real (la llegada a
una parada, la firma) se recalculan al final a partir de la hora de cada visita.

Uso, con el stack arriba y despues de datos_demo:
    docker compose exec api python -m scripts.operacion_demo

Es repetible: si ya sembro (su primera familia existe), no hace nada. Corre en local y en
staging; nunca contra produccion: se niega con cualquier otro ENVIRONMENT.
"""

import importlib
import random
import sys
import time
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import create_engine, select, text

from app.core.config import settings
from app.core.database import sesion_worker
from app.core.enums import Rol
from app.modules.encuestas import service as encuestas
from app.modules.encuestas.models import Encuesta
from app.modules.tareas.service import AREAS_POR_ROL
from app.workers.celery_app import celery_app
from app.workers.tasks import campanas as tareas_campanas
from app.workers.tasks import cartera as tareas_cartera
from app.workers.tasks import outbox
from scripts.datos_demo import (
    BOGOTA,
    CLAVE_EQUIPO,
    Cliente,
    Equipo,
    comprobar_ambiente,
    equipo,
    pagar_lo_vencido,
    sin_sesion,
)

# El script drena el outbox como el worker: necesita los mismos manejadores y eventos, que se
# registran al importar los modulos de tareas.
for _modulo in celery_app.conf.include:
    importlib.import_module(_modulo)

# Siempre la misma semilla: dos pasadas sobre stacks limpios siembran lo mismo.
azar = random.Random(20261116)  # noqa: S311 - datos de demostracion, no secretos

SEMANAS = 8
# Dias con ruta: lunes, miercoles y viernes en Bogota; martes y sabado en Medellin.
DIAS_RUTA = {0: "Bogotá", 2: "Bogotá", 4: "Bogotá", 1: "Medellín", 5: "Medellín"}
VISITAS_POR_RUTA = 3
# Cada cuantas rutas una parada se omite (la familia no estaba) y un servicio se cancela antes.
CADA_OMISION = 6
CADA_CANCELACION = 7
# Una de cada tantas consultas parte de una plantilla de datos_demo (DEU-15), como haria la medica
# en una consulta frecuente; el resto escribe cada apartado.
CADA_PLANTILLA = 3
# Cada ruta lleva ademas una parada preventiva, que alterna vacuna y desparasitacion: el carnet
# se alimenta de las rutas preventivas (6.8, 6.15; DEU-14).
TIPOS_PREVENTIVOS = ("vacunacion", "desparasitacion")
# Los jueves hay citas en la clinica de Laureles, la unica sede, en Medellin (DEU-14).
DIA_CLINICA = 3
CITAS_CLINICA = ("consulta_clinica", "consulta_clinica", "control_post")

MEDICO_MEDELLIN = ("medico.medellin@timu.co", "Dr. Andrés Villa")

# Familias de la operacion, por perfil de cartera. `inicio` son los dias desde que se afilio.
# Las coordenadas son de barrios reales, para que el optimizador tenga donde trabajar.
FAMILIAS: list[dict[str, Any]] = [
    {
        "titular_nombre": "Patricia Lozano",
        "documento": "1018456001",
        "telefono": "3001230001",
        "email": "patricia@example.com",
        "ciudad": "Bogotá",
        "barrio": "Cedritos",
        "direccion": "Calle 147 # 12-40",
        "coordenadas": (4.7268, -74.0381),
        "mascotas": [("Max", "canino", "macho", "Schnauzer", "2017-03-02", 9.4)],
        "planes": ["mi_amigo_fiel"],
        "perfil": "al_dia",
        "inicio": 200,
    },
    {
        "titular_nombre": "Hernán Castillo",
        "documento": "79456002",
        "telefono": "3001230002",
        "ciudad": "Bogotá",
        "barrio": "Chicó",
        "direccion": "Carrera 11 # 93-20",
        "coordenadas": (4.6779, -74.0487),
        "mascotas": [
            ("Lola", "canino", "hembra", "Poodle", "2019-07-11", 5.6),
            ("Tom", "felino", "macho", None, "2021-02-19", 4.9),
        ],
        "planes": ["colita_feliz", "colita_feliz"],
        "perfil": "al_dia",
        "inicio": 150,
    },
    {
        "titular_nombre": "Diana Morales",
        "documento": "52456003",
        "telefono": "3001230003",
        "email": "diana@example.com",
        "ciudad": "Bogotá",
        "barrio": "Niza",
        "direccion": "Calle 125 # 58-15",
        "coordenadas": (4.7115, -74.0712),
        "mascotas": [("Canela", "canino", "hembra", "Criolla", "2020-10-05", 14.0)],
        "planes": ["colita_feliz"],
        "perfil": "mora",
        "inicio": 130,
    },
    {
        "titular_nombre": "Ricardo Salazar",
        "documento": "80456004",
        "telefono": "3001230004",
        "ciudad": "Bogotá",
        "barrio": "Modelia",
        "direccion": "Carrera 75 # 24-60",
        "coordenadas": (4.6702, -74.1201),
        "mascotas": [("Bruno", "canino", "macho", "Bulldog", "2018-12-01", 22.0)],
        "planes": ["mi_amigo_fiel"],
        "perfil": "congelada",
        "inicio": 160,
    },
    {
        "titular_nombre": "Claudia Rincón",
        "documento": "52456005",
        "telefono": "3001230005",
        "ciudad": "Bogotá",
        "barrio": "Santa Bárbara",
        "direccion": "Calle 116 # 15-30",
        "coordenadas": (4.6981, -74.0441),
        "mascotas": [
            ("Mia", "felino", "hembra", None, "2022-04-14", 3.6),
            ("Oliver", "felino", "macho", None, "2022-04-14", 4.4),
            ("Coco", "canino", "macho", "Pug", "2016-09-23", 8.8),
        ],
        "planes": ["colita_feliz", "colita_feliz", "mi_amigo_fiel"],
        "perfil": "al_dia",
        "inicio": 95,
    },
    {
        "titular_nombre": "Felipe Arango",
        "documento": "1018456006",
        "telefono": "3001230006",
        "ciudad": "Bogotá",
        "barrio": "Galerías",
        "direccion": "Calle 53 # 24-11",
        "coordenadas": (4.6438, -74.0758),
        "mascotas": [("Zeus", "canino", "macho", "Pastor alemán", "2019-01-30", 34.0)],
        "planes": ["mi_amigo_fiel"],
        "perfil": "anual",
        "inicio": 120,
    },
    {
        "titular_nombre": "Gloria Pardo",
        "documento": "41456007",
        "telefono": "3001230007",
        "ciudad": "Bogotá",
        "barrio": "Colina Campestre",
        "direccion": "Calle 138 # 55-70",
        "coordenadas": (4.7230, -74.0623),
        "mascotas": [("Pelusa", "felino", "hembra", "Angora", "2015-06-12", 4.1)],
        "planes": ["colita_feliz"],
        "perfil": "renovacion",
        "inicio": 345,
    },
    {
        "titular_nombre": "Sebastián Vargas",
        "documento": "1018456008",
        "telefono": "3001230008",
        "ciudad": "Bogotá",
        "barrio": "Chapinero Alto",
        "direccion": "Carrera 4 # 57-30",
        "coordenadas": (4.6487, -74.0571),
        "mascotas": [("Thor", "canino", "macho", "Husky", "2021-08-08", 25.0)],
        "planes": ["colita_feliz"],
        "perfil": "baja",
        "inicio": 110,
    },
    {
        "titular_nombre": "Valeria Ochoa",
        "documento": "1018456009",
        "telefono": "3001230009",
        "email": "valeria@example.com",
        "ciudad": "Bogotá",
        "barrio": "Usaquén",
        "direccion": "Carrera 6 # 119-24",
        "coordenadas": (4.6955, -74.0310),
        "mascotas": [("Frida", "canino", "hembra", "Beagle", "2024-02-01", 10.2)],
        "planes": ["colita_feliz"],
        "perfil": "nueva",
        "inicio": 9,
    },
    {
        "titular_nombre": "Andrea Restrepo",
        "documento": "43456010",
        "telefono": "3001230010",
        "email": "andrea@example.com",
        "ciudad": "Medellín",
        "barrio": "Laureles",
        "direccion": "Circular 73 # 39-12",
        "coordenadas": (6.2449, -75.5949),
        "mascotas": [
            ("Rufo", "canino", "macho", "Labrador", "2018-05-20", 30.0),
            ("Nina", "felino", "hembra", None, "2020-11-02", 3.9),
        ],
        "planes": ["amigos_por_siempre", "amigos_por_siempre"],
        "perfil": "al_dia",
        "inicio": 140,
    },
    {
        "titular_nombre": "Juan David Mejía",
        "documento": "71456011",
        "telefono": "3001230011",
        "ciudad": "Medellín",
        "barrio": "Envigado",
        "direccion": "Carrera 43A # 38 Sur-20",
        "coordenadas": (6.1719, -75.5866),
        "mascotas": [("Kaiser", "canino", "macho", "Rottweiler", "2017-10-10", 41.0)],
        "planes": ["mi_amigo_fiel"],
        "perfil": "al_dia",
        "inicio": 180,
    },
    {
        "titular_nombre": "Luisa Fernanda Gil",
        "documento": "43456012",
        "telefono": "3001230012",
        "ciudad": "Medellín",
        "barrio": "Belén",
        "direccion": "Calle 30A # 76-15",
        "coordenadas": (6.2286, -75.6012),
        "mascotas": [("Manchas", "felino", "macho", None, "2019-03-03", 5.3)],
        "planes": ["colita_feliz"],
        "perfil": "mora",
        "inicio": 100,
    },
    {
        "titular_nombre": "Carolina Uribe",
        "documento": "43456013",
        "telefono": "3001230013",
        "ciudad": "Medellín",
        "barrio": "El Poblado",
        "direccion": "Carrera 37 # 8A-40",
        "coordenadas": (6.2088, -75.5698),
        "mascotas": [("Luna", "canino", "hembra", "Golden", "2020-01-15", 27.0)],
        "planes": ["amigos_por_siempre"],
        "perfil": "al_dia",
        "inicio": 75,
    },
]

PERFILES_CON_PAGOS = {"al_dia", "anual", "renovacion", "baja", "nueva"}
MEDIOS = ["transferencia", "transferencia", "datafono", "efectivo", "consignacion"]

# Lo que dice una consulta: (motivo, anamnesis, examen fisico, diagnostico, tratamiento).
CONSULTAS = [
    (
        "Control general anual",
        "Come bien, activo. Sin vómito ni diarrea.",
        "Mucosas rosadas, condición corporal 3/5, sin hallazgos.",
        "Paciente sano",
        "Mantener alimentación y actividad. Próximo control en seis meses.",
    ),
    (
        "Se rasca las orejas",
        "Sacude la cabeza desde hace cuatro días.",
        "Cerumen oscuro en ambos conductos, leve eritema.",
        "Otitis externa bilateral",
        "Limpieza ótica y gotas cada 12 horas por 7 días.",
    ),
    (
        "Vómito ocasional",
        "Dos vómitos en la semana, después de comer rápido.",
        "Abdomen blando, sin dolor a la palpación. Hidratado.",
        "Gastritis leve",
        "Dieta blanda tres días y comedero lento.",
    ),
    (
        "Cojea de la pata trasera",
        "Cojera desde el paseo del fin de semana.",
        "Dolor leve a la flexión de la rodilla derecha, sin inflamación.",
        "Esguince leve de rodilla",
        "Reposo relativo una semana y antiinflamatorio por cinco días.",
    ),
    (
        "Piel irritada",
        "Se lame el abdomen; cambió de champú hace dos semanas.",
        "Eritema en abdomen ventral, sin pulgas.",
        "Dermatitis por contacto",
        "Suspender el champú nuevo, baños con avena una vez por semana.",
    ),
    (
        "Control de peso",
        "La familia nota que subió de peso.",
        "Condición corporal 4/5. Resto normal.",
        "Sobrepeso",
        "Reducir la ración un 10 % y paseos de 30 minutos diarios.",
    ),
    (
        "Tos seca",
        "Tos en las noches desde hace una semana.",
        "Auscultación con leve aumento de ruidos bronquiales, sin fiebre.",
        "Traqueobronquitis",
        "Antitusivo por siete días y pretal en vez de collar.",
    ),
]
OMISIONES = ["La familia no estaba en casa", "No contestaron en portería", "Dirección incompleta"]
CANCELACIONES = ["La familia canceló por viaje", "La mascota ya fue atendida en otra parte"]
VACUNAS = [("Nobivac", "NB24"), ("Vanguard Plus", "VP31"), ("Felocell", "FC12")]
ANTIPARASITARIOS = [("Bravecto", "BR07"), ("Drontal", "DR15"), ("Milbemax", "MX22")]
COMENTARIOS = [
    (5, "Excelente atención, muy amable la doctora."),
    (5, None),
    (4, "Todo bien, llegaron un poco tarde."),
    (5, "Mi perro quedó feliz."),
    (3, "La visita fue muy corta."),
    (2, "Llegaron dos horas tarde y nadie avisó."),
    (4, None),
]


@dataclass
class Visita:
    """Un servicio recorrido en una ruta, con el dia que le toca en el pasado."""

    servicio_id: str
    dia: date
    omitida: bool = False


@dataclass
class Operacion:
    visitas: list[Visita] = field(default_factory=list)
    rutas: list[tuple[str, date]] = field(default_factory=list)
    cancelados: list[str] = field(default_factory=list)
    citas: list[str] = field(default_factory=list)


def dias_habiles(desde: date, hasta: date) -> Iterator[date]:
    d = desde
    while d <= hasta:
        if d.weekday() != 6:
            yield d
        d += timedelta(days=1)


def reserva(hoy: date, dia: date) -> date:
    """El dia futuro donde se agenda y se recorre la operacion de `dia`: el mismo dia de la
    semana (las franjas son por dia de la semana), dos semanas despues de hoy."""
    d = hoy + timedelta(days=14)
    while d.weekday() != dia.weekday():
        d += timedelta(days=1)
    return d


def dueno() -> Any:
    """Conexion del dueno del esquema: puede fechar en el pasado lo ya firmado."""
    return create_engine(settings.DATABASE_URL_PROPIETARIO.replace("+asyncpg", "+psycopg"))


# --- Familias, contratos y pagos --------------------------------------------------------------


def familias_y_cartera(c: Cliente, hoy: date) -> list[dict[str, Any]]:
    planes = {p["codigo"]: p for p in c.get("/planes")}
    creadas = []
    for datos in FAMILIAS:
        cuerpo = {
            k: v
            for k, v in datos.items()
            if k not in ("coordenadas", "planes", "perfil", "inicio", "mascotas")
        }
        cuerpo["mascotas"] = [
            {
                "nombre": n,
                "especie": e,
                "sexo": s,
                **({"raza": r} if r else {}),
                "fecha_nacimiento": f,
                "peso_kg": p,
            }
            for n, e, s, r, f, p in datos["mascotas"]
        ]
        familia = c.post("/familias", cuerpo)
        if familia is None:
            continue
        lat, lng = datos["coordenadas"]
        c.http.patch(f"/familias/{familia['id']}", json={"latitud": lat, "longitud": lng})
        perfil = datos["perfil"]
        inicio = hoy - timedelta(days=datos["inicio"])
        c.post(
            "/cartera/contratos",
            {
                "familia_id": familia["id"],
                "peludos": [
                    {"mascota_id": m["id"], "plan_id": planes[codigo]["id"]}
                    for m, codigo in zip(familia["mascotas"], datos["planes"], strict=True)
                ],
                "periodicidad": {"anual": "anual", "renovacion": "trimestral"}.get(
                    perfil, "mensual"
                ),
                "fecha_inicio": inicio.isoformat(),
            },
        )
        familia["perfil"] = perfil
        creadas.append(familia)
    # El beat emite a diario las cuotas que van venciendo: con contratos que empezaron hace
    # meses, se emiten de una vez todas las que ya vencieron, antes de pagarlas.
    tareas_cartera.generar_cuotas()
    # Eso tambien emite las de las familias de datos_demo: Jorge, la del portal al dia, sigue
    # al dia.
    for jorge in c.get("/familias", q="80456123")["items"]:
        pagar_lo_vencido(c, jorge)
    for familia in creadas:
        pagar_cuotas(c, familia, familia["perfil"], hoy)
        if familia["perfil"] == "baja":
            c.post(f"/familias/{familia['id']}/baja", {"motivo": "Se mudó de ciudad"})
    # Y revisa la mora a diario: aqui, una vez, para que cada familia quede en su estado.
    tareas_cartera.revisar_mora()
    return creadas


def pagar_cuotas(c: Cliente, familia: dict[str, Any], perfil: str, hoy: date) -> None:
    """Paga cada cuota vencida el dia que vencia (o unos dias antes), salvo las que el perfil
    deja sin pagar: la ultima en mora, las dos ultimas en congelada."""
    cuenta = c.get(f"/cartera/familias/{familia['id']}/estado-cuenta")
    vencidas = sorted(
        (q for q in cuenta["cuotas"] if date.fromisoformat(q["fecha_vencimiento"]) <= hoy),
        key=lambda q: q["fecha_vencimiento"],
    )
    sin_pagar = {"mora": 1, "congelada": 2}.get(perfil, 0)
    a_pagar = vencidas[: len(vencidas) - sin_pagar] if sin_pagar else vencidas
    if perfil == "nueva":
        a_pagar = vencidas[:1] or [
            min(cuenta["cuotas"], key=lambda q: q["fecha_vencimiento"], default=None)
        ]
    for n, cuota in enumerate(q for q in a_pagar if q):
        saldo = float(cuota["valor"]) - float(cuota["valor_pagado"])
        if saldo <= 0:
            continue
        vence = date.fromisoformat(cuota["fecha_vencimiento"])
        pagado = min(vence - timedelta(days=azar.randint(0, 3)), hoy)
        c.post(
            "/cartera/pagos",
            {
                "familia_id": familia["id"],
                "cuota_id": cuota["id"],
                "valor": f"{saldo:.2f}",
                "medio": azar.choice(MEDIOS),
                "referencia": f"OP-{familia['documento']}-{n}",
                "fecha_pago": datetime.combine(pagado, datetime.min.time())
                .replace(hour=azar.randint(8, 18), tzinfo=BOGOTA)
                .isoformat(),
            },
        )


# --- Preventivos ----------------------------------------------------------------------------


def preventivos(
    c: Cliente, medico: Cliente, familias: list[dict[str, Any]], hoy: date, motor: Any
) -> None:
    """El calendario de cada peludo nuevo empieza hoy: la primera dosis de cada esquema se
    aplica en una fecha de las ultimas semanas (autorizada antes por la familia), y la
    siguiente se programa desde ella. De lo que queda sin aplicar, uno de cada tres se lleva al
    pasado: vencido, para la bandeja de preventivos."""
    sin_aplicar: list[str] = []
    aplicados: list[tuple[str, date]] = []
    for familia in familias:
        if familia["perfil"] == "baja":
            continue
        for mascota in familia["mascotas"]:
            eventos = c.post(f"/preventivos/mascotas/{mascota['id']}/calendario") or []
            primeros: dict[str, dict[str, Any]] = {}
            for e in sorted(eventos, key=lambda e: e["fecha_programada"]):
                primeros.setdefault(e["esquema_codigo"] or e["tipo"], e)
            aplicar = [e for i, e in enumerate(primeros.values()) if i % 4 != 3]
            sin_aplicar.extend(e["id"] for e in eventos if e not in aplicar)
            if not aplicar:
                continue
            c.post(
                "/preventivos/autorizaciones",
                {"eventos": [e["id"] for e in aplicar], "medio": "whatsapp"},
            )
            for e in aplicar:
                producto, lote = azar.choice(
                    ANTIPARASITARIOS if "desparasit" in e["tipo"] else VACUNAS
                )
                fecha = hoy - timedelta(days=azar.randint(10, 7 * SEMANAS))
                aplicado = medico.post(
                    f"/preventivos/{e['id']}/aplicacion",
                    {
                        "fecha": fecha.isoformat(),
                        "producto": producto,
                        "lote": lote,
                        **({"peso_kg": mascota["peso_kg"]} if "desparasit" in e["tipo"] else {}),
                    },
                )
                if aplicado:
                    aplicados.append((e["id"], fecha))
    with motor.begin() as cx:
        # Lo aplicado estaba programado para cuando se aplico, no para hoy.
        for evento_id, fecha in aplicados:
            cx.execute(
                text("UPDATE eventos_preventivos SET fecha_programada = :f WHERE id = :i"),
                {"f": fecha, "i": UUID(evento_id)},
            )
        for evento_id in sin_aplicar[::3]:
            cx.execute(
                text("UPDATE eventos_preventivos SET fecha_programada = :f WHERE id = :i"),
                {"f": hoy - timedelta(days=azar.randint(3, 25)), "i": UUID(evento_id)},
            )


# --- Rutas de dias pasados ------------------------------------------------------------------


def candidatas(c: Cliente, ciudad: str) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """(familia, mascota) de la ciudad con ubicacion y contrato: a quienes se puede visitar.
    Cada familia lleva `afiliada_desde`: antes de esa fecha no se le visita ni se le remite."""
    pares: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for familia in c.get("/familias", ciudad=ciudad, limit=100)["items"]:
        if familia.get("latitud") is None:
            continue
        cuenta = c.http.get(f"/cartera/familias/{familia['id']}/estado-cuenta")
        if cuenta.status_code != 200:
            continue
        familia["afiliada_desde"] = date.fromisoformat(cuenta.json()["contrato"]["fecha_inicio"])
        pares.extend((familia, m) for m in familia["mascotas"] if m.get("activa", True))
    return pares


def operar_dias(c: Cliente, medicos: dict[str, tuple[Cliente, str]], hoy: date) -> Operacion:
    op = Operacion()
    pendientes_por_ciudad = {ciudad: candidatas(c, ciudad) for ciudad in set(DIAS_RUTA.values())}
    turno = dict.fromkeys(pendientes_por_ciudad, 0)
    motor = dueno()
    plantillas = c.get("/clinica/plantillas")
    numero = 0
    for dia in dias_habiles(hoy - timedelta(weeks=SEMANAS), hoy - timedelta(days=1)):
        if dia.weekday() == DIA_CLINICA:
            citas_en_clinica(
                c,
                medicos["Medellín"][0],
                dia,
                hoy,
                pendientes_por_ciudad["Medellín"],
                op,
                motor,
                plantillas,
            )
            continue
        ciudad = DIAS_RUTA.get(dia.weekday())
        if ciudad is None:
            continue
        numero += 1
        futuro = reserva(hoy, dia)
        corrimiento = (futuro - dia).days
        medico, medico_id = medicos[ciudad]
        cupos = [
            x
            for x in c.get(
                "/agenda/disponibilidad",
                fecha=futuro.isoformat(),
                ciudad=ciudad,
                tipo_codigo="consulta_domiciliaria",
            )
            if x["disponibles"] > 0
        ]
        horas: list[str] = []
        for cupo in cupos:
            inicio = datetime.fromisoformat(cupo["inicio"])
            if not horas or inicio >= datetime.fromisoformat(horas[-1]) + timedelta(minutes=90):
                horas.append(cupo["inicio"])
        servicios: list[str] = []
        pares = pendientes_por_ciudad[ciudad]
        intentos = 0
        while len(servicios) < VISITAS_POR_RUTA and horas and intentos < len(pares):
            familia, mascota = pares[turno[ciudad] % len(pares)]
            turno[ciudad] += 1
            intentos += 1
            if familia["afiliada_desde"] > dia:
                continue
            # La API dice si se puede (plan vigente, cartera al dia, cupo): si no, la siguiente.
            if not c.get(
                "/servicios/elegibilidad",
                familia_id=familia["id"],
                mascota_id=mascota["id"],
                tipo_codigo="consulta_domiciliaria",
            )["elegible"]:
                continue
            nuevo = c.post(
                "/servicios",
                {
                    "familia_id": familia["id"],
                    "mascota_id": mascota["id"],
                    "tipo_codigo": "consulta_domiciliaria",
                    "inicio": horas.pop(0),
                },
            )
            if nuevo:
                servicios.append(nuevo["id"])
        if not servicios:
            continue
        if numero % CADA_CANCELACION == 0 and len(servicios) > 1:
            cancelado = servicios.pop()
            c.post(
                f"/servicios/{cancelado}/estado",
                {"estado": "cancelado", "motivo": azar.choice(CANCELACIONES)},
            )
            op.cancelados.append(cancelado)
            correr(motor, servicios=[cancelado], dias=corrimiento)
        tipo = TIPOS_PREVENTIVOS[numero % len(TIPOS_PREVENTIVOS)]
        preventivo = agendar_preventivo(c, futuro, ciudad, dia, pares, tipo)
        if preventivo:
            servicios.append(preventivo)
        ruta = planear(c, futuro, ciudad, medico_id)
        if ruta is None:
            print(f"  ! sin ruta para {dia} en {ciudad}")
            correr(motor, servicios=servicios, dias=corrimiento)
            continue
        recorrer(medico, ruta, dia, omitir=numero % CADA_OMISION == 0, op=op, plantillas=plantillas)
        aplicados_al_pasado(motor, servicios=servicios, dia=dia)
        correr(motor, servicios=servicios, dias=corrimiento, ruta_id=ruta["id"])
        op.rutas.append((ruta["id"], dia))
    return op


def plantilla_para(plantillas: list[dict[str, Any]], tipo: str) -> str | None:
    """Una plantilla que la consulta de ese tipo de atencion ofreceria: la suya o una general."""
    validas = [p["codigo"] for p in plantillas if p["tipo_servicio_codigo"] in (None, tipo)]
    return azar.choice(validas) if validas else None


def agendar_preventivo(
    c: Cliente,
    futuro: date,
    ciudad: str,
    dia: date,
    pares: list[tuple[dict[str, Any], dict[str, Any]]],
    tipo: str,
) -> str | None:
    """La parada preventiva de la ruta: un peludo afiliado ese dia con un preventivo de `tipo`
    por aplicar. Se autoriza y se agenda desde el preventivo, como en la bandeja, y su visita
    lo aplica al completarse (el servicio manda)."""
    cupos = [
        x
        for x in c.get(
            "/agenda/disponibilidad", fecha=futuro.isoformat(), ciudad=ciudad, tipo_codigo=tipo
        )
        if x["disponibles"] > 0
    ]
    if not cupos:
        return None
    # Pocos intentos: cada uno son dos consultas y el cupo de peticiones es por usuario.
    for familia, mascota in azar.sample(pares, min(len(pares), 6)):
        if familia["afiliada_desde"] > dia:
            continue
        eventos = [
            e
            for e in c.get("/preventivos", mascota_id=mascota["id"], estado="programado", limit=50)[
                "items"
            ]
            if e["tipo_servicio_codigo"] == tipo and e["servicio_id"] is None
        ]
        if (
            not eventos
            or not c.get(
                "/servicios/elegibilidad",
                familia_id=familia["id"],
                mascota_id=mascota["id"],
                tipo_codigo=tipo,
            )["elegible"]
        ):
            continue
        evento = min(eventos, key=lambda e: e["fecha_programada"])
        if evento["requiere_autorizacion"] and not evento["autorizado"]:
            c.post("/preventivos/autorizaciones", {"eventos": [evento["id"]], "medio": "whatsapp"})
        # La ultima franja del dia: la manana es de las consultas.
        agendado = c.post(f"/preventivos/{evento['id']}/agendar", {"inicio": cupos[-1]["inicio"]})
        return agendado["servicio_id"] if agendado else None
    return None


def aplicados_al_pasado(motor: Any, *, servicios: list[str], dia: date) -> None:
    """Una visita preventiva aplica el preventivo con la fecha de hoy: se lleva al dia de la
    visita, con su proxima fecha y la dosis siguiente que se programo desde ella."""
    ids = [UUID(s) for s in servicios]
    with motor.begin() as cx:
        cx.execute(
            text(
                "UPDATE eventos_preventivos n"
                " SET fecha_programada = n.fecha_programada - (e.fecha_aplicacion - :dia)"
                " FROM eventos_preventivos e"
                " WHERE e.servicio_id = ANY(:ids) AND e.estado = 'aplicado'"
                " AND n.mascota_id = e.mascota_id AND n.esquema_codigo = e.esquema_codigo"
                " AND n.dosis_numero = e.dosis_numero + 1 AND n.estado = 'programado'"
            ),
            {"ids": ids, "dia": dia},
        )
        cx.execute(
            text(
                "UPDATE eventos_preventivos"
                " SET proxima_fecha = proxima_fecha - (fecha_aplicacion - :dia),"
                " fecha_aplicacion = :dia"
                " WHERE servicio_id = ANY(:ids) AND estado = 'aplicado'"
            ),
            {"ids": ids, "dia": dia},
        )


def citas_en_clinica(
    c: Cliente,
    medico: Cliente,
    dia: date,
    hoy: date,
    pares: list[tuple[dict[str, Any], dict[str, Any]]],
    op: Operacion,
    motor: Any,
    plantillas: list[dict[str, Any]],
) -> None:
    """Las citas de un jueves en la clinica: cada mascota llega, se atiende con su consulta
    presencial y el servicio se completa. Como las rutas, se agenda y se atiende en el dia de
    reserva y despues se lleva al pasado."""
    futuro = reserva(hoy, dia)
    hechas: list[str] = []
    for tipo in CITAS_CLINICA:
        cupos = [
            x
            for x in c.get(
                "/agenda/disponibilidad",
                fecha=futuro.isoformat(),
                ciudad="Medellín",
                tipo_codigo=tipo,
            )
            if x["disponibles"] > 0
        ]
        if not cupos:
            continue
        nuevo = None
        for familia, mascota in azar.sample(pares, min(len(pares), 6)):
            if (
                familia["afiliada_desde"] > dia
                or not c.get(
                    "/servicios/elegibilidad",
                    familia_id=familia["id"],
                    mascota_id=mascota["id"],
                    tipo_codigo=tipo,
                )["elegible"]
            ):
                continue
            nuevo = c.post(
                "/servicios",
                {
                    "familia_id": familia["id"],
                    "mascota_id": mascota["id"],
                    "tipo_codigo": tipo,
                    "inicio": cupos[0]["inicio"],
                },
            )
            break
        if not nuevo:
            continue
        c.post(f"/servicios/{nuevo['id']}/estado", {"estado": "en_atencion"})
        consulta: dict[str, Any] = {
            "mascota_id": nuevo["mascota_id"],
            "servicio_id": nuevo["id"],
            "tipo": "presencial",
            "fecha": dia.isoformat(),
        }
        codigo = plantilla_para(plantillas, tipo) if len(op.citas) % CADA_PLANTILLA == 0 else None
        if codigo:
            consulta["plantilla_codigo"] = codigo
        else:
            motivo, anamnesis, examen, diagnostico, tratamiento = azar.choice(CONSULTAS)
            consulta |= {
                "motivo": motivo,
                "anamnesis": anamnesis,
                "examen_fisico": examen,
                "diagnostico": diagnostico,
                "tratamiento": tratamiento,
            }
        entrada = medico.post("/clinica/historias", consulta)
        if entrada:
            medico.post(f"/clinica/historias/{entrada['id']}/firma")
        # La consulta firmada registro los pasos del servicio: ya se puede completar.
        c.post(f"/servicios/{nuevo['id']}/estado", {"estado": "completado"})
        op.citas.append(nuevo["id"])
        hechas.append(nuevo["id"])
    correr(motor, servicios=hechas, dias=(futuro - dia).days)


def planear(c: Cliente, dia: date, ciudad: str, responsable: str) -> dict[str, Any] | None:
    plan = c.post(
        "/rutas/planificaciones",
        {"fecha": dia.isoformat(), "ciudad": ciudad, "responsables": [responsable]},
    )
    # El beat drena el outbox una vez por minuto: se drena ya, para no esperar.
    for _ in range(40):
        if plan is None or plan["estado"] != "pendiente":
            break
        outbox.drenar()
        time.sleep(1)
        plan = c.get(f"/rutas/planificaciones/{plan['id']}")
    if plan is None or plan["estado"] != "lista":
        return None
    rutas = c.get("/rutas", fecha=dia.isoformat(), ciudad=ciudad, responsable_id=responsable)
    return next((r for r in rutas if r["estado"] == "planificada"), None)


def recorrer(
    medico: Cliente,
    ruta: dict[str, Any],
    dia: date,
    *,
    omitir: bool,
    op: Operacion,
    plantillas: list[dict[str, Any]],
) -> None:
    """La medica sale, atiende cada parada con su consulta firmada y cierra la ruta. Parte de
    las consultas salen de una plantilla, que da todos los apartados."""
    medico.post(f"/rutas/{ruta['id']}/inicio")
    detalle = medico.get(f"/rutas/{ruta['id']}")
    paradas = sorted(detalle["paradas"], key=lambda p: p["orden"])
    for n, parada in enumerate(paradas):
        servicio_id = parada["servicio_id"]
        if omitir and n == len(paradas) - 1:
            medico.post(
                f"/rutas/paradas/{parada['id']}/omision",
                {"motivo": azar.choice(OMISIONES)},
            )
            op.visitas.append(Visita(servicio_id, dia, omitida=True))
            continue
        medico.post(f"/rutas/paradas/{parada['id']}/en-camino")
        medico.post(f"/rutas/paradas/{parada['id']}/llegada")
        if parada["tipo_codigo"] in TIPOS_PREVENTIVOS:
            # Sin consulta: la aplicacion es el paso que exige el servicio (el carnet sale de aqui).
            producto, lote = azar.choice(
                ANTIPARASITARIOS if parada["tipo_codigo"] == "desparasitacion" else VACUNAS
            )
            datos: dict[str, Any] = {"producto": producto, "lote": lote}
            peso = (parada["mascota"] or {}).get("peso_kg")
            if parada["tipo_codigo"] == "desparasitacion" and peso:
                datos["peso_kg"] = peso
            medico.put(f"/servicios/{servicio_id}/pasos/aplicacion", {"datos": datos})
            salir(medico, parada["id"])
            op.visitas.append(Visita(servicio_id, dia))
            continue
        consulta: dict[str, Any] = {
            "mascota_id": parada["mascota"]["id"],
            "servicio_id": servicio_id,
            "tipo": "domiciliaria",
            "fecha": dia.isoformat(),
        }
        codigo = (
            plantilla_para(plantillas, parada["tipo_codigo"])
            if len(op.visitas) % CADA_PLANTILLA == 0
            else None
        )
        if codigo:
            consulta["plantilla_codigo"] = codigo
        else:
            motivo, anamnesis, examen, diagnostico, tratamiento = azar.choice(CONSULTAS)
            consulta |= {
                "motivo": motivo,
                "anamnesis": anamnesis,
                "examen_fisico": examen,
                "diagnostico": diagnostico,
                "tratamiento": tratamiento,
            }
        entrada = medico.post("/clinica/historias", consulta)
        if entrada:
            medico.post(f"/clinica/historias/{entrada['id']}/firma")
        salir(medico, parada["id"])
        op.visitas.append(Visita(servicio_id, dia))


def salir(medico: Cliente, parada_id: str) -> None:
    """Terminar la visita: la salida va como formulario, porque admite una evidencia."""
    resp = medico.http.post(
        f"/rutas/paradas/{parada_id}/salida", data={"nota": "Visita sin novedad."}
    )
    if resp.is_error:
        print(f"  ! salida {parada_id}: {resp.status_code} {resp.text[:200]}")


def correr(motor: Any, *, servicios: list[str], dias: int, ruta_id: str | None = None) -> None:
    """Lleva al pasado lo que se agendo en el dia de reserva: los servicios, su ruta y su
    planificacion. Libera el dia de reserva para el siguiente y deja los cupos del mes como si
    la visita hubiera sido en su fecha."""
    if not servicios:
        return
    intervalo = timedelta(days=dias)
    with motor.begin() as cx:
        cx.execute(
            text(
                "UPDATE servicios SET programado_para = programado_para - :i,"
                " termina_en = termina_en - :i WHERE id = ANY(:ids)"
            ),
            {"i": intervalo, "ids": [UUID(s) for s in servicios]},
        )
        if ruta_id:
            cx.execute(
                text(
                    "UPDATE paradas_ruta SET llegada_estimada = llegada_estimada - :i"
                    " WHERE ruta_id = :r"
                ),
                {"i": intervalo, "r": UUID(ruta_id)},
            )
            cx.execute(
                text(
                    "UPDATE planificaciones_ruta SET fecha = planificaciones_ruta.fecha - :d"
                    " FROM rutas"
                    " WHERE rutas.id = :r AND planificaciones_ruta.id = rutas.planificacion_id"
                ),
                {"d": dias, "r": UUID(ruta_id)},
            )
            cx.execute(
                text("UPDATE rutas SET fecha = fecha - :d WHERE id = :r"),
                {"d": dias, "r": UUID(ruta_id)},
            )


def fechar(motor: Any, op: Operacion) -> None:
    """Las marcas que la operacion puso con la hora real, a partir de la hora de cada visita:
    cuando se agendo, cuando se llego y se salio, cuando se firmo la consulta y cuando arranco
    y termino la ruta."""
    hechas = [UUID(v.servicio_id) for v in op.visitas if not v.omitida]
    citas = [UUID(s) for s in op.citas]
    todas = [UUID(v.servicio_id) for v in op.visitas] + [UUID(s) for s in op.cancelados] + citas
    rutas = [UUID(r) for r, _ in op.rutas]
    with motor.begin() as cx:
        # Se agenda entre dos y seis dias antes de la visita.
        cx.execute(
            text(
                "UPDATE servicios SET"
                " created_at = programado_para"
                " - make_interval(days => 2 + abs(hashtext(id::text)) % 5),"
                " updated_at = termina_en WHERE id = ANY(:ids)"
            ),
            {"ids": todas},
        )
        cx.execute(
            text(
                "UPDATE paradas_ruta SET"
                " aviso_en_camino_en = llegada_estimada - interval '25 minutes',"
                " llegada_en = llegada_estimada"
                " + make_interval(mins => abs(hashtext(id::text)) % 15),"
                " salida_en = llegada_estimada + interval '50 minutes',"
                " created_at = llegada_estimada - interval '1 day',"
                " updated_at = llegada_estimada + interval '50 minutes'"
                " WHERE servicio_id = ANY(:ids)"
            ),
            {"ids": hechas},
        )
        cx.execute(
            text(
                "UPDATE historias_clinicas h SET"
                " created_at = p.llegada_en + interval '10 minutes',"
                " firmada_en = p.salida_en - interval '5 minutes',"
                " updated_at = p.salida_en - interval '5 minutes'"
                " FROM paradas_ruta p WHERE p.servicio_id = h.servicio_id"
                " AND h.servicio_id = ANY(:ids)"
            ),
            {"ids": hechas},
        )
        cx.execute(
            text(
                "UPDATE historias_clinicas SET firmada_en = (fecha + time '11:30') AT TIME ZONE"
                " 'America/Bogota', updated_at = (fecha + time '11:30') AT TIME ZONE"
                " 'America/Bogota' WHERE estado = 'firmada' AND servicio_id IS NULL"
                " AND firmada_en > fecha + interval '2 days'"
            )
        )
        cx.execute(
            text(
                "UPDATE servicio_pasos sp SET created_at = p.salida_en - interval '5 minutes',"
                " updated_at = p.salida_en - interval '5 minutes'"
                " FROM paradas_ruta p WHERE p.servicio_id = sp.servicio_id"
                " AND sp.servicio_id = ANY(:ids)"
            ),
            {"ids": hechas},
        )
        # En la clinica no hay parada: la consulta se abre al empezar la cita y se firma al final.
        cx.execute(
            text(
                "UPDATE historias_clinicas h"
                " SET created_at = s.programado_para + interval '5 minutes',"
                " firmada_en = s.termina_en - interval '3 minutes',"
                " updated_at = s.termina_en - interval '3 minutes'"
                " FROM servicios s WHERE s.id = h.servicio_id AND h.servicio_id = ANY(:ids)"
            ),
            {"ids": citas},
        )
        cx.execute(
            text(
                "UPDATE servicio_pasos sp SET created_at = s.termina_en - interval '3 minutes',"
                " updated_at = s.termina_en - interval '3 minutes'"
                " FROM servicios s WHERE s.id = sp.servicio_id AND sp.servicio_id = ANY(:ids)"
            ),
            {"ids": citas},
        )
        cx.execute(
            text(
                "UPDATE rutas r SET"
                " inicio_real = x.primera - interval '35 minutes', fin_real = x.ultima,"
                " created_at = r.fecha - interval '7 hours', updated_at = x.ultima"
                " FROM (SELECT ruta_id, min(llegada_estimada) AS primera,"
                " max(coalesce(salida_en, llegada_estimada)) AS ultima"
                " FROM paradas_ruta GROUP BY ruta_id) x"
                " WHERE x.ruta_id = r.id AND r.id = ANY(:ids)"
            ),
            {"ids": rutas},
        )


# --- Encuestas ------------------------------------------------------------------------------


PLANTILLA_ENCUESTA = {
    "nombre": "encuesta_satisfaccion",
    "titulo": "Encuesta de satisfacción",
    "categoria": "utility",
    "cuerpo": "Hola {{1}}, ¿cómo te pareció la visita a {{2}}? Califícala aquí: {{3}}",
    "variables": ["titular", "mascota", "enlace"],
}


def encuestas_respondidas(c: Cliente, op: Operacion, motor: Any) -> None:
    """Cada visita completada deja su encuesta (la programa el outbox): se envia y se responde
    como lo haria la familia, y despues se fecha unas horas tras la visita. La plantilla de
    WhatsApp de la encuesta se da por aprobada, como la de campanas en datos_demo: la
    aprobacion en Meta es un pendiente de TIMU."""
    plantillas = {p["nombre"]: p for p in c.get("/comunicaciones/plantillas")}
    if PLANTILLA_ENCUESTA["nombre"] not in plantillas:
        nueva = c.post("/comunicaciones/plantillas", PLANTILLA_ENCUESTA)
        if nueva:
            c.http.patch(
                f"/comunicaciones/plantillas/{nueva['id']}/estado",
                json={"estado_aprobacion": "aprobada", "activa": True},
            )
    hechas = [UUID(v.servicio_id) for v in op.visitas if not v.omitida]
    hechas += [UUID(s) for s in op.citas]
    for _ in range(30):
        outbox.drenar()
        with sesion_worker() as db:
            n = len(db.scalars(select(Encuesta.id).where(Encuesta.servicio_id.in_(hechas))).all())
        if n >= len(hechas):
            break
        time.sleep(2)
    with motor.begin() as cx:
        cx.execute(
            text(
                "UPDATE encuestas e SET programada_para = s.termina_en + interval '2 hours'"
                " FROM servicios s WHERE s.id = e.servicio_id AND e.servicio_id = ANY(:ids)"
            ),
            {"ids": hechas},
        )
    with sesion_worker() as db:
        encuestas.enviar_pendientes(db)
        tokens = list(
            db.scalars(
                select(Encuesta.token).where(
                    Encuesta.servicio_id.in_(hechas), Encuesta.estado == "enviada"
                )
            )
        )
    # La familia responde desde el enlace, sin sesion.
    familia = sin_sesion()
    for n, token in enumerate(tokens):
        if n % 10 >= 7:  # tres de cada diez no responden
            continue
        puntaje, comentario = azar.choice(COMENTARIOS)
        resp = familia.post(
            f"/encuestas/respuesta/{token}",
            json={"puntaje": puntaje, **({"comentario": comentario} if comentario else {})},
        )
        if resp.is_error:
            print(f"  ! encuesta: {resp.status_code} {resp.text[:200]}")
    with motor.begin() as cx:
        cx.execute(
            text(
                "UPDATE encuestas SET enviada_en = programada_para,"
                " respondida_en = CASE WHEN respondida_en IS NULL THEN NULL"
                " ELSE programada_para + make_interval(mins => 20 + abs(hashtext(id::text)) % 280)"
                " END WHERE servicio_id = ANY(:ids)"
            ),
            {"ids": hechas},
        )
        # La tarea que deja una calificacion baja nace cuando la familia respondio, y vencia
        # ese mismo dia: las que siguen abiertas quedan vencidas, como pasaria.
        cx.execute(
            text(
                "UPDATE tareas t SET created_at = e.respondida_en, updated_at = e.respondida_en,"
                " vence_el = (e.respondida_en AT TIME ZONE 'America/Bogota')::date"
                " FROM encuestas e WHERE e.servicio_id = t.servicio_id"
                " AND t.origen = 'encuesta' AND e.respondida_en IS NOT NULL"
                " AND t.servicio_id = ANY(:ids)"
            ),
            {"ids": hechas},
        )


# --- Lo demas de la operacion: comercial, tareas, aliadas, clinica virtual y campanas --------

# Cada fila se crea hoy por la API y despues se lleva `dias` al pasado: estas son sus columnas
# de fecha (las de tipo date se restan en dias; las de instante, como intervalo).
FECHAS: dict[str, dict[str, str]] = {
    "interesados": {"created_at": "marca", "updated_at": "marca", "ultimo_contacto": "marca"},
    "tareas": {
        "created_at": "marca",
        "updated_at": "marca",
        "cerrada_en": "marca",
        "vence_el": "dia",
    },
    "remisiones_aliadas": {
        "created_at": "marca",
        "updated_at": "marca",
        "reportada_en": "marca",
        "vence_en": "dia",
    },
    "solicitudes_virtuales": {
        "created_at": "marca",
        "updated_at": "marca",
        "tomada_en": "marca",
        "respondida_en": "marca",
        "borrador_en": "marca",
    },
    "campanas": {"created_at": "marca", "updated_at": "marca", "programada_para": "marca"},
    "ejecuciones_campana": {
        "created_at": "marca",
        "updated_at": "marca",
        "iniciada_en": "marca",
        "terminada_en": "marca",
    },
}


def al_pasado(cx: Any, tabla: str, fila_id: str, dias: int, *, donde: str = "id") -> None:
    """Lleva `dias` al pasado las fechas de una fila (o de las filas de `donde`). La tabla y
    sus columnas salen de FECHAS, nunca de fuera."""
    columnas = ", ".join(
        f"{c} = {c} - :d" if tipo == "dia" else f"{c} = {c} - make_interval(days => :d)"
        for c, tipo in FECHAS[tabla].items()
    )
    cx.execute(
        text(f"UPDATE {tabla} SET {columnas} WHERE {donde} = :i"),  # noqa: S608 - nombres fijos
        {"d": dias, "i": UUID(fila_id)},
    )


# (nombre, celular, ciudad, origen, etapa a la que llega, dias atras, motivo si se perdio)
INTERESADOS = [
    ("Marta Lucía Ospina", "3112340001", "Bogotá", "whatsapp", "nuevo", 2, None),
    ("Jaime Cárdenas", "3112340002", "Bogotá", "formulario", "nuevo", 5, None),
    ("Paola Jiménez", "3112340003", "Medellín", "referido", "contactado", 9, None),
    ("Oscar Duarte", "3112340004", "Bogotá", "evento", "contactado", 16, None),
    ("Natalia Ruiz", "3112340005", "Bogotá", "campana", "contactado", 23, None),
    ("Mauricio Peña", "3112340006", "Medellín", "whatsapp", "cotizado", 12, None),
    ("Lina Marcela Rojas", "3112340007", "Bogotá", "referido", "cotizado", 30, None),
    ("Esteban Quintero", "3112340008", "Bogotá", "formulario", "cotizado", 38, None),
    ("Daniela Cano", "3112340009", "Medellín", "evento", "en_afiliacion", 20, None),
    ("Alejandro Torres", "3112340010", "Bogotá", "whatsapp", "en_afiliacion", 44, None),
    ("Mónica Herrera", "3112340011", "Bogotá", "campana", "perdido", 35, "Precio"),
    ("Iván Gaviria", "3112340012", "Medellín", "formulario", "perdido", 50, "Eligió otra opción"),
]
ORDEN_EMBUDO = ["contactado", "cotizado", "en_afiliacion"]


def comercial(c: Cliente, motor: Any) -> None:
    """El embudo en el tiempo: interesados que llegaron en las ultimas semanas, cada uno en la
    etapa a la que llego. Ninguno llega a afiliado: eso lo pone la afiliacion en linea al
    aprobarse el pago, y la pasarela de pruebas aun no esta (pendientes-externos, Wompi)."""
    with motor.begin() as cx:
        for nombre, telefono, ciudad, origen, etapa, dias, motivo in INTERESADOS:
            nuevo = c.post(
                "/comercial/interesados",
                {"nombre": nombre, "telefono": telefono, "ciudad": ciudad, "origen": origen},
            )
            if nuevo is None:
                continue
            if etapa == "perdido":
                c.http.patch(f"/comercial/interesados/{nuevo['id']}", json={"etapa": "contactado"})
                c.post(f"/comercial/interesados/{nuevo['id']}/perdida", {"motivo": motivo})
            elif etapa != "nuevo":
                for paso in ORDEN_EMBUDO[: ORDEN_EMBUDO.index(etapa) + 1]:
                    c.http.patch(f"/comercial/interesados/{nuevo['id']}", json={"etapa": paso})
            al_pasado(cx, "interesados", nuevo["id"], dias)


# (titulo, area, prioridad, plazo en dias, dias atras, como se cerro; sin cierre sigue abierta)
TAREAS = [
    ("Confirmar dirección nueva de la familia", "operaciones", "media", 2, 40, "Confirmada"),
    ("Llamar por la cuota de septiembre", "cartera", "alta", 1, 35, "Pagó por transferencia"),
    ("Enviar la cotización de Amigos por Siempre", "comercial", "media", 3, 30, "Enviada"),
    ("Revisar el examen de sangre de Bruno", "medico", "alta", 2, 26, "Valores normales"),
    ("Reponer el inventario de vacunas", "operaciones", "baja", 7, 21, "Pedido hecho"),
    ("Atender la queja por la demora de la visita", "servicio_cliente", "alta", 1, 14, None),
    ("Llamar a la familia en mora de Medellín", "cartera", "media", 3, 12, None),
    ("Agendar el control de la cirugía", "medico", "media", 5, 6, None),
    ("Actualizar el teléfono del titular", "servicio_cliente", "baja", 7, 3, None),
    ("Preparar la campaña de diciembre", "comercial", "baja", 14, 2, None),
]


def tareas(c: Equipo, motor: Any) -> None:
    """Tareas de las ultimas semanas: las mas viejas cerradas y unas abiertas ya vencidas.

    Cada una la cierra el perfil de su area: los demas no la ven (Seccion 12)."""
    de_su_area = {area: Rol(rol) for rol, areas in AREAS_POR_ROL.items() for area in areas}
    with motor.begin() as cx:
        for titulo, area, prioridad, plazo, dias, cierre in TAREAS:
            nueva = c.post(
                "/tareas",
                {"titulo": titulo, "area": area, "prioridad": prioridad, "vence_en_dias": plazo},
            )
            if nueva is None:
                continue
            if cierre:
                c.como(de_su_area[area]).post(
                    f"/tareas/{nueva['id']}/cerrar", {"resolucion": cierre}
                )
            al_pasado(cx, "tareas", nueva["id"], dias)


# (motivo, dias atras, que paso: atendida, anulada, vencida o por usar, valor de la atencion)
REMISIONES = [
    ("Radiografía de cadera por cojera", 45, "atendida", "180000"),
    ("Ecografía abdominal por vómito persistente", 33, "atendida", "180000"),
    ("Limpieza dental bajo anestesia", 24, "atendida", "180000"),
    ("Hospitalización por deshidratación", 18, "anulada", None),
    ("Radiografía de tórax por tos", 40, "vencida", None),
    ("Ecografía de control", 4, "por usar", None),
    ("Radiografía de control de la cadera", 7, "atendida", "180000"),
]

# Dos aliadas de Medellin del catalogo, con su convenio, su usuario y lo que reportaron en los
# ultimos tres meses, tambien en el mes en curso: la liquidacion que ve Gerencia (6.22) tiene asi
# varias clinicas y meses. Cada atencion se reporta dos dias despues de emitida la remision.
ALIADAS_MEDELLIN = [
    (
        "AnesVet",
        "aliada.anesvet@timu.co",
        "Recepción AnesVet",
        {
            "beneficio": "Ecografía",
            "cobertura_pct": 70,
            "tarifa": "150000",
            "tope_cubierto": "250000",
        },
        [
            ("Ecografía abdominal por diarrea crónica", 75, "atendida", "150000"),
            ("Ecografía de control renal", 48, "atendida", "160000"),
            ("Ecografía por masa abdominal", 16, "atendida", "170000"),
            ("Ecografía cardíaca", 8, "atendida", "190000"),
        ],
    ),
    (
        "Centro Veterinario Buenos Aires",
        "aliada.buenosaires@timu.co",
        "Recepción Buenos Aires",
        {
            "beneficio": "Hospitalización",
            "cobertura_pct": 60,
            "tarifa": "300000",
            "tope_cubierto": "400000",
        },
        [
            ("Hospitalización por gastroenteritis", 62, "atendida", "320000"),
            ("Hospitalización por deshidratación", 30, "atendida", "280000"),
            ("Hospitalización tras cirugía de piel", 12, "atendida", "350000"),
            ("Hospitalización por intoxicación", 4, "atendida", "300000"),
        ],
    ),
]


def _remitir(
    c: Cliente,
    aliada: Cliente,
    clinica_id: str,
    pares: Any,
    lista: Sequence[tuple[str, int, str, str | None]],
    motor: Any,
    hoy: date,
) -> None:
    """Atencion al cliente emite cada remision y la clinica reporta las atendidas, por la API;
    despues se llevan al pasado. `pares` se consume: una mascota no recibe dos remisiones."""
    with motor.begin() as cx:
        for (motivo, dias, final, valor), (_, mascota) in zip(lista, pares, strict=False):
            remision = c.post(
                "/aliadas/remisiones",
                {"clinica_id": clinica_id, "mascota_id": mascota["id"], "motivo": motivo},
            )
            if remision is None:
                continue
            if final == "atendida":
                aliada.post(
                    f"/aliadas/mi-clinica/remisiones/{remision['codigo']}/atencion",
                    {
                        # Dentro de la vigencia de la remision, que se emitio hoy: despues se
                        # lleva al pasado con ella.
                        "fecha": hoy.isoformat(),
                        "valor_atencion": valor,
                        "resumen": "Procedimiento sin complicaciones; se envía el informe.",
                    },
                )
            elif final == "anulada":
                c.post(
                    f"/aliadas/remisiones/{remision['id']}/anulacion",
                    {"motivo": "La familia prefirió esperar"},
                )
            al_pasado(cx, "remisiones_aliadas", remision["id"], dias)
            # Se atendio dos dias despues de emitirse, y la clinica lo reporto esa tarde.
            cx.execute(
                text(
                    "UPDATE remisiones_aliadas SET fecha_atencion = fecha_atencion - :d,"
                    " reportada_en = (fecha_atencion - :d + time '17:00')"
                    " AT TIME ZONE 'America/Bogota'"
                    " WHERE id = :i AND fecha_atencion IS NOT NULL"
                ),
                {"d": dias - 2, "i": UUID(remision["id"])},
            )


def _remitibles(c: Cliente, ciudad: str, hoy: date, dias: int) -> Any:
    """(familia, mascota) de la ciudad afiliadas desde antes de la remision mas antigua y con el
    beneficio de atencion en aliada disponible."""
    return iter(
        (f, m)
        for f, m in candidatas(c, ciudad)
        if f["afiliada_desde"] <= hoy - timedelta(days=dias)
        and c.get(
            "/servicios/elegibilidad",
            familia_id=f["id"],
            mascota_id=m["id"],
            tipo_codigo="atencion_aliada",
        )["elegible"]
    )


def remisiones(c: Cliente, motor: Any, hoy: date) -> None:
    """Remisiones a la clinica aliada de Bogota: atendidas y reportadas por la clinica, una
    anulada, una que vencio sin usarse y una por usar. Despues, las de Medellin."""
    clinica = next((x for x in c.get("/aliadas") if x["ciudad"] == "Bogotá"), None)
    if clinica is not None:
        pares = _remitibles(c, "Bogotá", hoy, max(d for _, d, _, _ in REMISIONES))
        aliada = Cliente("aliada@timu.co", CLAVE_EQUIPO)
        _remitir(c, aliada, clinica["id"], pares, REMISIONES, motor, hoy)
    aliadas_medellin(c, motor, hoy)


def aliadas_medellin(c: Cliente, motor: Any, hoy: date) -> None:
    """Convenio, usuario y atenciones reportadas de las aliadas de Medellin. Repetible por su
    cuenta (una clinica con remisiones ya esta sembrada): se aplica tambien sobre una base que ya
    tenia la operacion, sin vaciarla (docs/datos-de-demostracion.md)."""
    clinicas = {x["nombre"]: x for x in c.get("/aliadas")}
    usuarios = {u["email"] for u in c.get("/auth/usuarios", limit=200)["items"]}
    for nombre, email, recepcion, convenio, lista in ALIADAS_MEDELLIN:
        clinica = clinicas.get(nombre)
        # Sembrada: ya tiene remisiones. El convenio y el usuario, solo si faltan.
        if clinica is None or c.get("/aliadas/remisiones", clinica_id=clinica["id"]):
            continue
        if not c.get(f"/aliadas/{clinica['id']}/convenios"):
            c.post(
                f"/aliadas/{clinica['id']}/convenios",
                {**convenio, "vigente_desde": (hoy - timedelta(days=120)).isoformat()},
            )
        if email not in usuarios:
            c.post(
                "/auth/usuarios",
                {
                    "email": email,
                    "nombre": recepcion,
                    "rol": "aliada",
                    "password": CLAVE_EQUIPO,
                    "clinica_aliada_id": clinica["id"],
                },
            )
        # Cada clinica parte de todas las de Medellin: hay pocas, y el cupo del beneficio es por
        # periodo, asi que una remision llevada a un mes pasado no gasta el de hoy.
        pares = _remitibles(c, "Medellín", hoy, max(d for _, d, _, _ in lista))
        _remitir(c, Cliente(email, CLAVE_EQUIPO), clinica["id"], pares, lista, motor, hoy)


VIRTUALES = [
    ("Queremos cambiarle el concentrado, ¿cómo lo hacemos?", 28),
    ("¿Cada cuánto debo bañar a mi gato?", 15),
    ("Le salió una mancha en la piel, ¿es grave?", 7),
]


def clinica_virtual(c: Cliente, medico: Cliente, motor: Any, hoy: date) -> None:
    """Orientaciones virtuales ya respondidas y cerradas por la medica."""
    antigua = hoy - timedelta(days=max(d for _, d in VIRTUALES))
    pares = [(f, m) for f, m in candidatas(c, "Bogotá") if f["afiliada_desde"] <= antigua]
    with motor.begin() as cx:
        for (motivo, dias), (_, mascota) in zip(VIRTUALES, pares[3:], strict=False):
            solicitud = c.post(
                "/clinica/virtual",
                {"mascota_id": mascota["id"], "motivo": motivo, "prioridad": "media"},
            )
            if solicitud is None:
                continue
            medico.post(f"/clinica/virtual/{solicitud['id']}/toma")
            medico.post(
                f"/clinica/virtual/{solicitud['id']}/respuesta",
                {"respuesta_codigo": "control_alimentacion", "variables": [mascota["nombre"]]},
            )
            c.post(f"/clinica/virtual/{solicitud['id']}/cierre")
            al_pasado(cx, "solicitudes_virtuales", solicitud["id"], dias)


def campana_enviada(c: Cliente, motor: Any) -> None:
    """Una campana que ya salio hace tres semanas, con sus mensajes."""
    campana = c.post(
        "/campanas",
        {
            "nombre": "Renovaciones de octubre",
            "plantilla": "recordatorio_renovacion",
            "variables": ["titular_nombre", "plan"],
            "segmento": {"estados": ["activa"], "renovacion_en_dias": 400},
        },
    )
    if campana is None:
        return
    c.post(f"/campanas/{campana['id']}/programacion", {"recurrencia": "ninguna"})
    # El beat la lanza y despacha cada minuto: aqui, ya.
    tareas_campanas.lanzar_programadas()
    tareas_campanas.despachar()
    dias = 21
    with motor.begin() as cx:
        al_pasado(cx, "campanas", campana["id"], dias)
        al_pasado(cx, "ejecuciones_campana", campana["id"], dias, donde="campana_id")
        cx.execute(
            text(
                "UPDATE mensajes SET created_at = created_at - make_interval(days => :d),"
                " updated_at = updated_at - make_interval(days => :d),"
                " enviado_en = enviado_en - make_interval(days => :d)"
                " WHERE campana_id = :i"
            ),
            {"d": dias, "i": UUID(campana["id"])},
        )


# --- Orquestacion ---------------------------------------------------------------------------


def main() -> None:
    comprobar_ambiente(settings, "operacion_demo")
    # Cada ruta, con el perfil al que le toca (Seccion 12); los medicos, con su propia sesion.
    c = equipo()
    hoy = datetime.now(BOGOTA).date()
    if c.get("/familias", q=FAMILIAS[0]["documento"])["total"]:
        print("La operación ya estaba sembrada: no se hace nada.")
        return

    print("Médico de Medellín")
    usuarios = {u["email"]: u for u in c.get("/auth/usuarios", limit=200)["items"]}
    email, nombre = MEDICO_MEDELLIN
    if email not in usuarios:
        usuarios[email] = c.post(
            "/auth/usuarios",
            {"email": email, "nombre": nombre, "rol": "medico", "password": CLAVE_EQUIPO},
        )
    medico = Cliente("medico@timu.co", CLAVE_EQUIPO)
    medicos = {
        "Bogotá": (medico, usuarios["medico@timu.co"]["id"]),
        "Medellín": (Cliente(email, CLAVE_EQUIPO), usuarios[email]["id"]),
    }

    print("Familias, contratos y pagos")
    familias = familias_y_cartera(c, hoy)
    motor = dueno()
    print("Preventivos")
    preventivos(c, medico, familias, hoy, motor)
    print(f"Rutas de las ultimas {SEMANAS} semanas")
    op = operar_dias(c, medicos, hoy)
    print("Fechas de la operación")
    fechar(motor, op)
    print("Encuestas")
    encuestas_respondidas(c, op, motor)
    print("Comercial, tareas, remisiones, clínica virtual y una campaña")
    comercial(c, motor)
    tareas(c, motor)
    remisiones(c, motor, hoy)
    clinica_virtual(c, medico, motor, hoy)
    campana_enviada(c, motor)
    print(
        f"Listo: {len(op.rutas)} rutas, {sum(not v.omitida for v in op.visitas)} visitas,"
        f" {sum(v.omitida for v in op.visitas)} omitidas, {len(op.cancelados)} canceladas"
        f" y {len(op.citas)} citas en la clínica."
    )
    comprobar(op)


# Lo minimo que tiene que dejar la siembra. Cliente.post solo avisa de un error y sigue: sin esta
# comprobacion, un cambio en la API podria vaciar la operacion sin que el CI lo notara.
MINIMOS = {
    "rutas": 30,
    "visitas": 80,
    "omitidas": 3,
    "canceladas": 3,
    "encuestas respondidas": 40,
    "preventivos aplicados": 30,
    "familias en mora": 2,
    "familias congeladas": 1,
    "interesados perdidos": 1,
    "remisiones atendidas": 2,
    # La liquidacion que ve Gerencia, con varias clinicas (6.22).
    "aliadas con atenciones": 3,
    "tareas cerradas": 3,
    "orientaciones cerradas": 2,
    "campanas enviadas": 1,
    "consultas desde una plantilla": 20,
    "preventivos aplicados en ruta": 20,
    "consultas en clínica": 10,
    "controles en clínica": 5,
}


def comprobar(op: Operacion) -> None:
    with sesion_worker() as db:

        def contar(sql: str) -> int:
            return int(db.execute(text(sql)).scalar() or 0)

        hechos = {
            "rutas": len(op.rutas),
            "visitas": sum(not v.omitida for v in op.visitas),
            "omitidas": sum(v.omitida for v in op.visitas),
            "canceladas": len(op.cancelados),
            "encuestas respondidas": contar(
                "SELECT count(*) FROM encuestas WHERE estado = 'respondida'"
            ),
            "preventivos aplicados": contar(
                "SELECT count(*) FROM eventos_preventivos WHERE estado = 'aplicado'"
            ),
            "familias en mora": contar("SELECT count(*) FROM contratos WHERE estado = 'en_mora'"),
            "familias congeladas": contar(
                "SELECT count(*) FROM contratos WHERE estado = 'congelada'"
            ),
            "interesados perdidos": contar(
                "SELECT count(*) FROM interesados WHERE etapa = 'perdido'"
            ),
            "remisiones atendidas": contar(
                "SELECT count(*) FROM remisiones_aliadas WHERE estado = 'utilizada'"
            ),
            "aliadas con atenciones": contar(
                "SELECT count(DISTINCT clinica_id) FROM remisiones_aliadas"
                " WHERE estado = 'utilizada'"
            ),
            "tareas cerradas": contar("SELECT count(*) FROM tareas WHERE estado = 'cerrada'"),
            "orientaciones cerradas": contar(
                "SELECT count(*) FROM solicitudes_virtuales WHERE estado = 'cerrada'"
            ),
            "campanas enviadas": contar("SELECT count(*) FROM ejecuciones_campana"),
            "preventivos aplicados en ruta": contar(
                "SELECT count(*) FROM eventos_preventivos"
                " WHERE estado = 'aplicado' AND servicio_id IS NOT NULL"
            ),
            "consultas en clínica": contar(
                "SELECT count(*) FROM servicios"
                " WHERE tipo_codigo = 'consulta_clinica' AND estado = 'completado'"
            ),
            "controles en clínica": contar(
                "SELECT count(*) FROM servicios"
                " WHERE tipo_codigo = 'control_post' AND estado = 'completado'"
            ),
            "consultas desde una plantilla": contar(
                "SELECT count(*) FROM historias_clinicas"
                " WHERE plantilla_codigo IS NOT NULL AND estado = 'firmada'"
            ),
        }
    faltan = [f"{k}: {hechos[k]} de {v}" for k, v in MINIMOS.items() if hechos[k] < v]
    if faltan:
        sys.exit("La operación quedó corta: " + "; ".join(faltan))


if __name__ == "__main__":
    main()
