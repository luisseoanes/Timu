"""F0-09 Datos iniciales de los catalogos.

Son valores de arranque, editables luego desde el panel. Los esquemas preventivos siguen
pautas veterinarias generales y deben ser validados por el equipo medico de TIMU antes de
produccion: cambiar aqui y volver a correr la carga actualiza sin duplicar.
"""

from typing import Any

CIUDADES: list[dict[str, Any]] = [
    {
        "codigo": "11001",
        "nombre": "Bogotá",
        "departamento": "Bogotá D.C.",
        "latitud": 4.7110,
        "longitud": -74.0721,
    },
    {
        "codigo": "05001",
        "nombre": "Medellín",
        "departamento": "Antioquia",
        "latitud": 6.2442,
        "longitud": -75.5812,
    },
    {
        "codigo": "76001",
        "nombre": "Cali",
        "departamento": "Valle del Cauca",
        "latitud": 3.4516,
        "longitud": -76.5320,
    },
    {
        "codigo": "08001",
        "nombre": "Barranquilla",
        "departamento": "Atlántico",
        "latitud": 10.9685,
        "longitud": -74.7813,
    },
    {
        "codigo": "13001",
        "nombre": "Cartagena",
        "departamento": "Bolívar",
        "latitud": 10.3910,
        "longitud": -75.4794,
    },
    {
        "codigo": "68001",
        "nombre": "Bucaramanga",
        "departamento": "Santander",
        "latitud": 7.1193,
        "longitud": -73.1227,
    },
    {
        "codigo": "66001",
        "nombre": "Pereira",
        "departamento": "Risaralda",
        "latitud": 4.8133,
        "longitud": -75.6961,
    },
    {
        "codigo": "17001",
        "nombre": "Manizales",
        "departamento": "Caldas",
        "latitud": 5.0703,
        "longitud": -75.5138,
    },
    {
        "codigo": "63001",
        "nombre": "Armenia",
        "departamento": "Quindío",
        "latitud": 4.5339,
        "longitud": -75.6811,
    },
    {
        "codigo": "54001",
        "nombre": "Cúcuta",
        "departamento": "Norte de Santander",
        "latitud": 7.8939,
        "longitud": -72.5078,
    },
    {
        "codigo": "73001",
        "nombre": "Ibagué",
        "departamento": "Tolima",
        "latitud": 4.4389,
        "longitud": -75.2322,
    },
    {
        "codigo": "47001",
        "nombre": "Santa Marta",
        "departamento": "Magdalena",
        "latitud": 11.2408,
        "longitud": -74.1990,
    },
    {
        "codigo": "50001",
        "nombre": "Villavicencio",
        "departamento": "Meta",
        "latitud": 4.1420,
        "longitud": -73.6266,
    },
    {
        "codigo": "52001",
        "nombre": "Pasto",
        "departamento": "Nariño",
        "latitud": 1.2136,
        "longitud": -77.2811,
    },
    {
        "codigo": "41001",
        "nombre": "Neiva",
        "departamento": "Huila",
        "latitud": 2.9273,
        "longitud": -75.2819,
    },
    {
        "codigo": "05088",
        "nombre": "Bello",
        "departamento": "Antioquia",
        "latitud": 6.3373,
        "longitud": -75.5580,
    },
    {
        "codigo": "05266",
        "nombre": "Envigado",
        "departamento": "Antioquia",
        "latitud": 6.1759,
        "longitud": -75.5917,
    },
    {
        "codigo": "05360",
        "nombre": "Itagüí",
        "departamento": "Antioquia",
        "latitud": 6.1846,
        "longitud": -75.5991,
    },
    # R3-PUB-04 El resto del Valle de Aburrá, donde hay aliadas de TIMU (la red de la portada).
    {
        "codigo": "05631",
        "nombre": "Sabaneta",
        "departamento": "Antioquia",
        "latitud": 6.1515,
        "longitud": -75.6166,
    },
    {
        "codigo": "05380",
        "nombre": "La Estrella",
        "departamento": "Antioquia",
        "latitud": 6.1576,
        "longitud": -75.643,
    },
    {
        "codigo": "05129",
        "nombre": "Caldas",
        "departamento": "Antioquia",
        "latitud": 6.0911,
        "longitud": -75.6357,
    },
    {
        "codigo": "05212",
        "nombre": "Copacabana",
        "departamento": "Antioquia",
        "latitud": 6.3487,
        "longitud": -75.5089,
    },
    {
        "codigo": "05308",
        "nombre": "Girardota",
        "departamento": "Antioquia",
        "latitud": 6.3772,
        "longitud": -75.4446,
    },
    {
        "codigo": "05079",
        "nombre": "Barbosa",
        "departamento": "Antioquia",
        "latitud": 6.4386,
        "longitud": -75.333,
    },
    {
        "codigo": "25175",
        "nombre": "Chía",
        "departamento": "Cundinamarca",
        "latitud": 4.8617,
        "longitud": -74.0325,
    },
    {
        "codigo": "25754",
        "nombre": "Soacha",
        "departamento": "Cundinamarca",
        "latitud": 4.5793,
        "longitud": -74.2168,
    },
]

ESPECIES: list[dict[str, Any]] = [
    {"codigo": "canino", "nombre": "Canino"},
    {"codigo": "felino", "nombre": "Felino"},
]


def _paso(
    codigo: str,
    nombre: str,
    *campos: str,
    obligatorio: bool = True,
    opcionales: tuple[dict[str, Any], ...] = (),
) -> dict[str, Any]:
    """`campos` se exigen para guardar el paso; `opcionales`, no: cada uno con su nombre en
    palabras y si es una cifra, para que el panel arme el campo sin adivinarlo."""
    paso = {"codigo": codigo, "nombre": nombre, "obligatorio": obligatorio, "campos": list(campos)}
    if opcionales:
        paso["opcionales"] = list(opcionales)
    return paso


# F2-PRE-07 el peso de la mascota el dia de la desparasitacion, que va al carnet.
PESO = {"campo": "peso_kg", "nombre": "Peso de la mascota (kg)", "numerico": True}


_PASOS_CONSULTA = [
    _paso("valoracion", "Valoración clínica", "hallazgos"),
    _paso("plan", "Plan y recomendaciones", "recomendaciones"),
]
_PASOS_PREVENTIVO = [
    _paso("aplicacion", "Aplicación", "producto", "lote"),
    _paso("evidencia", "Evidencia fotográfica", obligatorio=False),
]
_PASOS_DESPARASITACION = [
    _paso("aplicacion", "Aplicación", "producto", "lote", opcionales=(PESO,)),
    _paso("evidencia", "Evidencia fotográfica", obligatorio=False),
]

TIPOS_SERVICIO: list[dict[str, Any]] = [
    {
        "codigo": "consulta_domiciliaria",
        "nombre": "Consulta domiciliaria",
        "modalidad": "domiciliario",
        "duracion_min": 45,
        "pasos": _PASOS_CONSULTA,
    },
    {
        "codigo": "vacunacion",
        "nombre": "Vacunación",
        "modalidad": "preventivo",
        "duracion_min": 20,
        "requiere_autorizacion": True,
        "pasos": _PASOS_PREVENTIVO,
    },
    {
        "codigo": "desparasitacion",
        "nombre": "Desparasitación",
        "modalidad": "preventivo",
        "duracion_min": 15,
        "requiere_autorizacion": True,
        "pasos": _PASOS_DESPARASITACION,
    },
    {
        "codigo": "consulta_clinica",
        "nombre": "Consulta clínica",
        "modalidad": "clinico",
        "duracion_min": 30,
        "pasos": _PASOS_CONSULTA,
    },
    {
        "codigo": "control_post",
        "nombre": "Control post atención",
        "modalidad": "clinico",
        "duracion_min": 20,
    },
    {
        "codigo": "orientacion_virtual",
        "nombre": "Orientación veterinaria virtual",
        "modalidad": "virtual",
        "duracion_min": 20,
    },
    {
        "codigo": "atencion_aliada",
        "nombre": "Atención en clínica aliada",
        "modalidad": "aliada",
        "duracion_min": 60,
        "requiere_autorizacion": True,
    },
]

ESQUEMAS_PREVENTIVOS: list[dict[str, Any]] = [
    {
        "codigo": "can_polivalente",
        "especie_codigo": "canino",
        "tipo": "vacuna",
        "nombre": "Polivalente canina (moquillo, parvovirus, hepatitis, parainfluenza)",
        "edad_minima_semanas": 6,
        "dosis_iniciales": 3,
        "intervalo_inicial_dias": 21,
        "intervalo_refuerzo_dias": 365,
    },
    {
        "codigo": "can_rabia",
        "especie_codigo": "canino",
        "tipo": "vacuna",
        "nombre": "Antirrábica canina",
        "edad_minima_semanas": 12,
        "dosis_iniciales": 1,
        "intervalo_refuerzo_dias": 365,
    },
    {
        "codigo": "can_desp_interna",
        "especie_codigo": "canino",
        "tipo": "desparasitacion_interna",
        "nombre": "Desparasitación interna canina",
        "edad_minima_semanas": 2,
        "dosis_iniciales": 3,
        "intervalo_inicial_dias": 15,
        "intervalo_refuerzo_dias": 90,
    },
    {
        "codigo": "can_desp_externa",
        "especie_codigo": "canino",
        "tipo": "desparasitacion_externa",
        "nombre": "Desparasitación externa canina",
        "edad_minima_semanas": 8,
        "dosis_iniciales": 1,
        "intervalo_refuerzo_dias": 30,
    },
    {
        "codigo": "fel_triple",
        "especie_codigo": "felino",
        "tipo": "vacuna",
        "nombre": "Triple felina (panleucopenia, rinotraqueitis, calicivirus)",
        "edad_minima_semanas": 8,
        "dosis_iniciales": 2,
        "intervalo_inicial_dias": 21,
        "intervalo_refuerzo_dias": 365,
    },
    {
        "codigo": "fel_rabia",
        "especie_codigo": "felino",
        "tipo": "vacuna",
        "nombre": "Antirrábica felina",
        "edad_minima_semanas": 12,
        "dosis_iniciales": 1,
        "intervalo_refuerzo_dias": 365,
    },
    {
        "codigo": "fel_desp_interna",
        "especie_codigo": "felino",
        "tipo": "desparasitacion_interna",
        "nombre": "Desparasitación interna felina",
        "edad_minima_semanas": 3,
        "dosis_iniciales": 3,
        "intervalo_inicial_dias": 15,
        "intervalo_refuerzo_dias": 90,
    },
]
