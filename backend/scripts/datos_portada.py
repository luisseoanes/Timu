"""R3-PUB-04 Lo que la portada publica muestra en local: valores PROVISIONALES sacados de la web
actual de TIMU (https://timu.com.co, revisada el 2026-11-17), pendientes de que TIMU los confirme
(docs/pendientes-externos.md, «Valores provisionales»). Desplegado, los escribe Administracion.

Lo siembra `datos_demo` por la API. Lo que la web no dice entero (la mision, cortada a media
frase) no se inventa: se deja vacio.
"""

from typing import Any

# Administracion -> Datos de TIMU. El WhatsApp es el numero ficticio de local, como antes en
# `.env.example`: el de TIMU lo escribe Administracion.
DATOS_TIMU: dict[str, Any] = {
    "razon_social": "TIMU S.A.S.",
    "nit": "901635168-2",
    "presentacion": (
        "Integramos profesionales y entidades de salud física y mental para perros y gatos, y "
        "facilitamos el acceso a esos servicios con nuestros planes de salud. Somos un equipo "
        "capacitado en salud veterinaria y servicio, con entidades aliadas que nos permiten dar "
        "una atención más especializada, oportuna y humana: medicina veterinaria prepagada y "
        "clínica veterinaria."
    ),
    "mision": None,
    "vision": (
        "En 2027 estaremos brindando servicio a nivel nacional, reconocidos por nuestros valores "
        "y sin dejar de ser un aliado para cada familia perruna y gatuna."
    ),
    "valores": [
        "Confianza",
        "Innovación",
        "Servicio",
        "Conocimiento",
        "Empatía",
        "Trabajo en equipo",
        "Integridad",
    ],
    "clinica_nombre": "TIMU clínica veterinaria",
    "clinica_direccion": "Calle 35 # 66a 51",
    "clinica_barrio": "Los Conquistadores, Laureles",
    "clinica_ciudad": "Medellín",
    "clinica_horario": (
        "Lunes a viernes de 9:00 a. m. a 6:00 p. m.; " "sábados de 9:00 a. m. a 5:00 p. m."
    ),
    "horario_atencion": (
        "Medicina prepagada y clínicas aliadas las 24 horas; nuestra clínica, de lunes a sábado."
    ),
    "telefonos": ["+573016244775", "+573184140551"],
    "whatsapp": "+573000000000",
    "correo": "administracion@timu.com.co",
    "redes": [
        {"nombre": "Instagram", "url": "https://www.instagram.com/timumedicinaprepagada/"},
        {
            "nombre": "Instagram de la clínica",
            "url": "https://www.instagram.com/timuclinicaveterinaria/",
        },
    ],
}

# Administracion -> Aliadas: las de la pagina /aliados/ de la web, en el orden de la red del
# valle (de norte a sur) y despues las que no tienen sede. Sin logos: son marcas de terceros
# que la administracion sube.
ALIADAS: list[dict[str, Any]] = [
    {
        "nombre": "The Dog's Club",
        "tipo": "hospedaje",
        "ciudad": "Girardota",
        "telefono": "3013365229",
        "presentacion": "Hotel canino, con ruta de transporte.",
    },
    {
        "nombre": "Clínica Veterinaria Cabañitas",
        "tipo": "clinica",
        "ciudad": "Bello",
        "direccion": "Calle 23 # 57a 16",
        "telefono": "3042223956",
        "horario": (
            "Lunes a viernes de 10:00 a. m. a 7:00 p. m.; " "sábados de 10:00 a. m. a 6:00 p. m."
        ),
    },
    {
        "nombre": "Centro Veterinario Buenos Aires",
        "tipo": "clinica",
        "ciudad": "Medellín",
        "barrio": "Buenos Aires",
        "direccion": "Calle 49 # 30-45, avenida Ayacucho",
        "telefono": "6042693066",
    },
    {
        "nombre": "Clínica Veterinaria Mira Bosques",
        "tipo": "clinica",
        "ciudad": "Medellín",
        "barrio": "Laureles",
        "direccion": "Carrera 86 # 34-4",
        "telefono": "6042536999",
        "presentacion": "Con el Dr. Juan David Patiño, especialista en dermatología veterinaria.",
    },
    {
        "nombre": "Consultorio médico Macarena",
        "tipo": "clinica",
        "ciudad": "Medellín",
        "barrio": "Laureles",
        "direccion": "Calle 35 # 73a-22",
        "telefono": "3105955825",
        "horario": (
            "Lunes a sábado de 10:00 a. m. a 7:00 p. m.; " "domingos de 10:00 a. m. a 2:00 p. m."
        ),
    },
    {
        "nombre": "Consultorio médico y spa Cosmo Pets",
        "tipo": "peluqueria",
        "ciudad": "Medellín",
        "direccion": "Circular 74a # 39b 147, interior 102",
        "telefono": "3122177872",
        "horario": "Lunes a sábado de 10:00 a. m. a 6:00 p. m.",
    },
    {
        "nombre": "Clínica veterinaria Integral Vet",
        "tipo": "clinica",
        "atiende_24h": True,
        "ciudad": "Medellín",
        "barrio": "Aguacatala",
        "direccion": "Calle 15 sur # 48-144",
        "telefono": "3052276909",
        "horario": "24 horas",
    },
    {
        "nombre": "Clínica veterinaria La Vete",
        "tipo": "clinica",
        "atiende_24h": True,
        "ciudad": "Itagüí",
        "barrio": "Las Margaritas",
        "direccion": "Calle 34a # 54-40",
        "telefono": "6042812058",
        "horario": "24 horas",
    },
    {
        "nombre": "Centro Veterinario Agrosanti",
        "tipo": "clinica",
        "ciudad": "Itagüí",
        "barrio": "Santa María",
        "direccion": "Calle 77 # 50-30",
        "telefono": "6044334974",
        "horario": "12 horas",
    },
    {
        "nombre": "Clínica Veterinaria Vida Animal",
        "tipo": "clinica",
        "atiende_24h": True,
        "ciudad": "Envigado",
        "barrio": "Alcalá",
        "direccion": "Calle 39 sur # 43a 26",
        "telefono": "3147234881",
        "horario": "24 horas",
    },
    {
        "nombre": "Peluquería Amascotas",
        "tipo": "peluqueria",
        "ciudad": "Envigado",
        "barrio": "Alcalá",
        "direccion": "Calle 39a sur # 46-24",
        "telefono": "3506276400",
        "horario": "Lunes a sábado de 10:00 a. m. a 7:00 p. m.",
    },
    {
        "nombre": "Clínica veterinaria Kahuana",
        "tipo": "clinica",
        "ciudad": "La Estrella",
        "direccion": "Carrera 57 # 76b sur 12",
        "telefono": "3003889231",
        "horario": (
            "Lunes a viernes de 10:00 a. m. a 7:00 p. m.; " "sábados de 10:00 a. m. a 5:00 p. m."
        ),
    },
    {
        "nombre": "Safari campamento de mascotas",
        "tipo": "hospedaje",
        "ciudad": "Medellín",
        "barrio": "Santa Elena",
        "telefono": "3022611480",
        "presentacion": "Guardería canina, con ruta de transporte.",
    },
    {
        "nombre": "Dr. Henry González",
        "tipo": "especialista",
        "ciudad": "Medellín",
        "presentacion": (
            "Especialista clínico en pequeñas especies (medicina interna y cirugía), con "
            "diplomado en oftalmología de perros y gatos."
        ),
    },
    {
        "nombre": "AnesVet",
        "tipo": "especialista",
        "ciudad": "Medellín",
        "presentacion": "Especialistas en anestesia segura.",
    },
    {
        "nombre": "Farmacia veterinaria domiciliaria",
        "tipo": "farmacia",
        "ciudad": "Medellín",
        "telefono": "3017099052",
        "horario": "Lunes a viernes de 8:00 a. m. a 8:00 p. m.; sábados de 8:00 a. m. a 5:00 p. m.",
    },
    {
        "nombre": "Trafunpet",
        "tipo": "funeraria",
        "ciudad": "Medellín",
        "telefono": "3053564555",
        "presentacion": "Transporte y funeraria para mascotas.",
    },
]

# Administracion -> Planes -> Beneficios adicionales: lo que la web dice de cada plan y no es un
# tipo de servicio que se agenda. Donde la web se contradice consigo misma o con el plegable
# 2026 (la hospitalizacion de Mi Amigo Fiel), manda el plegable, que ya siembra `datos_demo`.
_FUNEBRE = {
    "nombre": "Servicio fúnebre",
    "cubre": "100 %",
    "carencia_dias": 30,
    "detalle": (
        "Traslado las 24 horas, biocremación individual, cofre de cenizas, dos recordatorios, un "
        "portarretrato, una planta para sembrar y certificado del procedimiento. Para peludos de "
        "9 años o más, desde los 90 días."
    ),
}
_DESPARASITANTE_EXTERNO = {
    "nombre": "Desparasitante externo para perros",
    "cubre": "Cada 3 meses",
    "carencia_dias": 1,
    "detalle": "De una marca que elige TIMU, con entrega a domicilio.",
}
_ESPECIALISTA = {
    "nombre": "Consulta con especialista",
    "cubre": "30 %",
    "carencia_dias": 90,
    "detalle": (
        "Dermatología, oftalmología, neurología, etología, cardiología, ortopedia y nefrología."
    ),
}


def _coberturas(
    pct: int, cirugia: str | None = None, examenes: str | None = None
) -> list[dict[str, Any]]:
    return [
        {"nombre": "Cirugía", "cubre": f"{pct} %", "carencia_dias": 30, "detalle": cirugia},
        {"nombre": "Exámenes", "cubre": f"{pct} %", "carencia_dias": 30, "detalle": examenes},
        {"nombre": "Procedimientos no quirúrgicos", "cubre": f"{pct} %", "carencia_dias": 30},
        {"nombre": "Profilaxis", "cubre": f"{pct} %", "carencia_dias": 30},
    ]


ADICIONALES: dict[str, list[dict[str, Any]]] = {
    "colita_feliz": [
        _FUNEBRE,
        _DESPARASITANTE_EXTERNO,
        _ESPECIALISTA,
        *_coberturas(10),
        {
            "nombre": "Certificados de salud",
            "cubre": "20 % de descuento",
            "detalle": "En nuestra clínica.",
        },
    ],
    "mi_amigo_fiel": [
        _FUNEBRE,
        _DESPARASITANTE_EXTERNO,
        _ESPECIALISTA,
        *_coberturas(
            40,
            cirugia="Hasta $850.000 por episodio.",
            examenes="Hasta $350.000 por episodio.",
        ),
        {
            "nombre": "Certificados de salud",
            "cubre": "40 % de descuento",
            "detalle": "En nuestra clínica.",
        },
        {
            "nombre": "Baño y peluquería",
            "cubre": "30 %",
            "tercero": True,
            "detalle": "Lo presta un tercero: TIMU no garantiza siempre su disponibilidad.",
        },
        {
            "nombre": "Precios preferenciales",
            "cubre": "Desde el 5 %",
            "tercero": True,
            "detalle": (
                "Microchip, hospedaje, guardería, transporte, dieta BARF, medicamentos de fórmula "
                "y accesorios, con los terceros que tengan convenio."
            ),
        },
    ],
    "amigos_por_siempre": [
        _FUNEBRE,
        _DESPARASITANTE_EXTERNO,
        _ESPECIALISTA,
        *_coberturas(80),
        {
            "nombre": "Certificados de salud",
            "cubre": "60 % de descuento",
            "detalle": "En nuestra clínica.",
        },
    ],
}
