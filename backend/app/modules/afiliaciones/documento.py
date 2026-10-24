"""F1-AFI-02 Contrato de afiliacion en PDF con los datos reales de la familia.

El texto de las condiciones generales es provisional: TIMU debe entregar el texto legal
aprobado, que se versiona en TERMINOS_VERSION para que cada aceptacion quede atada a una
version concreta.
"""

from datetime import date
from typing import Any

from fpdf import FPDF

from app.modules.cartera.periodos import formato_cop

TERMINOS_VERSION = "2026-09-provisional"

CONDICIONES = [
    "El plan cubre los servicios y beneficios descritos para cada tipo de atencion, con los "
    "cupos indicados, durante la vigencia del contrato.",
    "La cuota mensual se paga a mas tardar en la fecha de corte. Pasado el plazo de gracia, "
    "la afiliacion entra en mora y, si la mora continua, se congela: no se agendan servicios "
    "hasta ponerse al dia. Al pagar, la afiliacion se reactiva automaticamente.",
    "El contrato tiene vigencia de un ano y se renueva previa gestion con la familia.",
    "Agregar mascotas por encima del cupo del plan puede generar un valor adicional segun las "
    "condiciones vigentes del plan.",
    "Los datos personales se tratan conforme a la politica de tratamiento de datos de TIMU "
    "(Ley 1581 de 2012).",
]


def _texto(valor: Any) -> str:
    # Las fuentes base del PDF son latin-1: se reemplazan caracteres fuera de ese rango.
    return str(valor).encode("latin-1", "replace").decode("latin-1")


def _cupo(beneficio: dict[str, Any]) -> str:
    if beneficio["cupo"] is None:
        return "Ilimitado"
    return f"{beneficio['cupo']} por {beneficio['periodo_cupo']}"


def generar_contrato(
    *,
    numero: str,
    fecha: date,
    familia: dict[str, Any],
    plan: dict[str, Any],
    mascotas: list[dict[str, Any]],
    contrato: dict[str, Any],
) -> bytes:
    pdf = FPDF(format="Letter")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 10, "Contrato de afiliacion TIMU", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, _texto(f"No. {numero}  -  {fecha:%d/%m/%Y}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    def seccion(titulo: str, filas: list[tuple[str, Any]]) -> None:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, _texto(titulo), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        for etiqueta, valor in filas:
            pdf.cell(55, 6, _texto(etiqueta))
            pdf.multi_cell(
                0,
                6,
                _texto(valor if valor not in (None, "") else "-"),
                new_x="LMARGIN",
                new_y="NEXT",
            )
        pdf.ln(2)

    seccion(
        "Titular",
        [
            ("Nombre", familia["titular_nombre"]),
            ("Documento", f"{familia['tipo_documento']} {familia['documento']}"),
            ("Telefono", familia["telefono"]),
            ("Correo", familia.get("email")),
            ("Direccion", f"{familia.get('direccion') or ''} - {familia['ciudad']}"),
        ],
    )
    seccion(
        "Plan",
        [
            ("Plan", plan["nombre"]),
            ("Valor del plan", formato_cop(contrato["valor_plan"])),
            ("Mascotas adicionales", contrato["mascotas_adicionales"]),
            ("Valor mensual total", formato_cop(contrato["valor_mensual"])),
            ("Dia de corte", contrato["dia_corte"]),
            ("Inicio", f"{contrato['fecha_inicio']:%d/%m/%Y}"),
            ("Renovacion", f"{contrato['fecha_renovacion']:%d/%m/%Y}"),
        ],
    )
    seccion(
        "Mascotas afiliadas",
        [(m["nombre"], f"{m['especie']} {m.get('raza') or ''}".strip()) for m in mascotas],
    )
    if plan.get("beneficios"):
        seccion(
            "Beneficios",
            [
                (b["tipo_servicio_codigo"], f"{_cupo(b)}, cobertura {b['cobertura_pct']}%")
                for b in plan["beneficios"]
            ],
        )
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Condiciones generales", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    for i, condicion in enumerate(CONDICIONES, start=1):
        pdf.multi_cell(0, 5, _texto(f"{i}. {condicion}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(
        0,
        4,
        _texto(
            f"Version de condiciones: {TERMINOS_VERSION}. La aceptacion queda registrada en la "
            "plataforma con fecha, medio y datos de la sesion."
        ),
        new_x="LMARGIN",
        new_y="NEXT",
    )
    return bytes(pdf.output())
