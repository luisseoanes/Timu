"""F0-09 Datos iniciales de los catalogos.

Son valores de arranque, editables luego desde el panel. Los esquemas preventivos siguen
pautas veterinarias generales y deben ser validados por el equipo medico de TIMU antes de
produccion: cambiar aqui y volver a correr la carga actualiza sin duplicar.
"""

from typing import Any

CIUDADES: list[dict[str, Any]] = [
    {
        "codigo": "11001",
        "nombre": "Bogota",
        "departamento": "Bogota D.C.",
        "latitud": 4.7110,
        "longitud": -74.0721,
    },
    {
        "codigo": "05001",
        "nombre": "Medellin",
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
        "departamento": "Atlantico",
        "latitud": 10.9685,
        "longitud": -74.7813,
    },
    {
        "codigo": "13001",
        "nombre": "Cartagena",
        "departamento": "Bolivar",
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
        "departamento": "Quindio",
        "latitud": 4.5339,
        "longitud": -75.6811,
    },
    {
        "codigo": "54001",
        "nombre": "Cucuta",
        "departamento": "Norte de Santander",
        "latitud": 7.8939,
        "longitud": -72.5078,
    },
    {
        "codigo": "73001",
        "nombre": "Ibague",
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
        "departamento": "Narino",
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
        "nombre": "Itagui",
        "departamento": "Antioquia",
        "latitud": 6.1846,
        "longitud": -75.5991,
    },
    {
        "codigo": "25175",
        "nombre": "Chia",
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


def _paso(codigo: str, nombre: str, *campos: str, obligatorio: bool = True) -> dict[str, Any]:
    return {"codigo": codigo, "nombre": nombre, "obligatorio": obligatorio, "campos": list(campos)}


_PASOS_CONSULTA = [
    _paso("valoracion", "Valoracion clinica", "hallazgos"),
    _paso("plan", "Plan y recomendaciones", "recomendaciones"),
]
_PASOS_PREVENTIVO = [
    _paso("aplicacion", "Aplicacion", "producto", "lote"),
    _paso("evidencia", "Evidencia fotografica", obligatorio=False),
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
        "nombre": "Vacunacion",
        "modalidad": "preventivo",
        "duracion_min": 20,
        "requiere_autorizacion": True,
        "pasos": _PASOS_PREVENTIVO,
    },
    {
        "codigo": "desparasitacion",
        "nombre": "Desparasitacion",
        "modalidad": "preventivo",
        "duracion_min": 15,
        "requiere_autorizacion": True,
        "pasos": _PASOS_PREVENTIVO,
    },
    {
        "codigo": "consulta_clinica",
        "nombre": "Consulta clinica",
        "modalidad": "clinico",
        "duracion_min": 30,
        "pasos": _PASOS_CONSULTA,
    },
    {
        "codigo": "control_post",
        "nombre": "Control post atencion",
        "modalidad": "clinico",
        "duracion_min": 20,
    },
    {
        "codigo": "orientacion_virtual",
        "nombre": "Orientacion veterinaria virtual",
        "modalidad": "virtual",
        "duracion_min": 20,
    },
    {
        "codigo": "atencion_aliada",
        "nombre": "Atencion en clinica aliada",
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
        "nombre": "Antirrabica canina",
        "edad_minima_semanas": 12,
        "dosis_iniciales": 1,
        "intervalo_refuerzo_dias": 365,
    },
    {
        "codigo": "can_desp_interna",
        "especie_codigo": "canino",
        "tipo": "desparasitacion_interna",
        "nombre": "Desparasitacion interna canina",
        "edad_minima_semanas": 2,
        "dosis_iniciales": 3,
        "intervalo_inicial_dias": 15,
        "intervalo_refuerzo_dias": 90,
    },
    {
        "codigo": "can_desp_externa",
        "especie_codigo": "canino",
        "tipo": "desparasitacion_externa",
        "nombre": "Desparasitacion externa canina",
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
        "nombre": "Antirrabica felina",
        "edad_minima_semanas": 12,
        "dosis_iniciales": 1,
        "intervalo_refuerzo_dias": 365,
    },
    {
        "codigo": "fel_desp_interna",
        "especie_codigo": "felino",
        "tipo": "desparasitacion_interna",
        "nombre": "Desparasitacion interna felina",
        "edad_minima_semanas": 3,
        "dosis_iniciales": 3,
        "intervalo_inicial_dias": 15,
        "intervalo_refuerzo_dias": 90,
    },
]
