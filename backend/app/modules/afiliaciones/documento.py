"""6.12 Contrato de afiliacion en PDF con los datos reales de la familia y la marca de
TIMU (como el carnet).

El texto de las condiciones generales es provisional: TIMU debe entregar el texto legal
aprobado, que se versiona en TERMINOS_VERSION para que cada aceptacion quede atada a una
version concreta.
"""

from collections.abc import Mapping
from datetime import date
from typing import Any

from app.core import marca_pdf as marca
from app.modules.cartera.periodos import formato_cop
from app.modules.planes.models import Plan
from app.modules.planes.service import texto_carencia

TERMINOS_VERSION = "2026-11-provisional"

CONDICIONES = [
    "El plan cubre los servicios y beneficios descritos para cada tipo de atención, con los "
    "cupos indicados, durante la vigencia del contrato.",
    "La cuota se paga, según la periodicidad elegida, a más tardar en la fecha de corte. "
    "Pasado el plazo de gracia, la afiliación entra en mora y, si la mora continúa, se congela: "
    "no se agendan servicios hasta ponerse al día. Al pagar, la afiliación se reactiva "
    "automáticamente.",
    "El contrato tiene vigencia de un año y se renueva previa gestión con la familia.",
    "Cada peludo paga la tarifa de su plan según el número de peludos afiliados. Si se agregan "
    "o se retiran peludos, el valor se recalcula desde la siguiente cuota. El precio por pago "
    "trimestral, semestral o anual aplica solo con un peludo.",
    "Los datos personales se tratan conforme a la política de tratamiento de datos de TIMU "
    "(Ley 1581 de 2012).",
]

_PERIODO_CUPO = {"mensual": "al mes", "anual": "al año"}


def _telefono(e164: str) -> str:
    """«+57 300 111 2233», como lo escribe el panel: un celular colombiano en grupos."""
    if len(e164) == 13 and e164.startswith("+57"):
        return f"+57 {e164[3:6]} {e164[6:9]} {e164[9:]}"
    return e164


def _cupo(beneficio: dict[str, Any]) -> str:
    """Lo que sí tiene un beneficio: nunca «ilimitado» (manual de marca, voz)."""
    periodo = _PERIODO_CUPO.get(beneficio["periodo_cupo"], f"por {beneficio['periodo_cupo']}")
    if beneficio["cupo"] is None:
        return f"Sin tope de usos {periodo}"
    return f"{beneficio['cupo']} {periodo}"


def plan_del_contrato(plan: Plan, tipos: Mapping[str, str]) -> dict[str, Any]:
    """Lo que el contrato dice de un plan: lo mismo que el catalogo y que la portada (R3-PUB-04).
    `tipos` nombra cada tipo de servicio."""
    return {
        "nombre": plan.nombre,
        "color": plan.color,
        "carencia": plan.carencia,
        "exclusiones": plan.exclusiones,
        "beneficios": [
            {
                "tipo_servicio": tipos.get(b.tipo_servicio_codigo, b.tipo_servicio_codigo),
                "cupo": b.cupo,
                "periodo_cupo": b.periodo_cupo,
                "cobertura_pct": b.cobertura_pct,
                "tope_episodio": b.tope_episodio,
                "carencia_dias": b.carencia_dias,
            }
            for b in plan.beneficios
        ],
        "adicionales": [
            {
                "nombre": a.nombre,
                "cubre": a.cubre,
                "carencia_dias": a.carencia_dias,
                "tercero": a.tercero,
            }
            for a in plan.adicionales
        ],
    }


def _cobertura(beneficio: dict[str, Any]) -> str:
    """«40 % · hasta $850.000 por episodio»."""
    texto = f"{beneficio['cobertura_pct']} %"
    if beneficio.get("tope_episodio") is not None:
        texto += f" · hasta {formato_cop(beneficio['tope_episodio'])} por episodio"
    return texto


def _desde(dias: int | None) -> str:
    return texto_carencia(dias) or "Desde la afiliación"


def generar_contrato(
    *,
    numero: str,
    fecha: date,
    familia: dict[str, Any],
    mascotas: list[dict[str, Any]],
    planes: list[dict[str, Any]],
    contrato: dict[str, Any],
) -> bytes:
    """`mascotas`: nombre, especie, raza, plan y valor_mensual de cada peludo. `planes`:
    nombre, color y beneficios (con el nombre de su tipo de servicio) de cada plan contratado."""
    pdf = marca.PdfMarca()
    pdf.set_title(f"Contrato de afiliación {numero}")
    pdf.set_author("TIMU")
    pdf.add_page()
    marca.cabecera(pdf, "Contrato de afiliación", f"N.º {numero} · {fecha:%d/%m/%Y}")

    marca.titulo_seccion(pdf, "Titular")
    marca.datos(
        pdf,
        [
            ("Nombre", familia["titular_nombre"]),
            ("Documento", f"{familia['tipo_documento']} {familia['documento']}"),
            ("Teléfono", _telefono(familia["telefono"])),
            ("Correo", familia.get("email") or "—"),
            ("Dirección", familia.get("direccion") or "—"),
            ("Ciudad", familia["ciudad"]),
        ],
        columnas=3,
    )
    marca.titulo_seccion(pdf, "Afiliación")
    marca.datos(
        pdf,
        [
            ("Forma de pago", str(contrato["periodicidad"]).capitalize()),
            ("Valor de cada cuota", formato_cop(contrato["valor_periodo"])),
            ("Valor mensual", formato_cop(contrato["valor_mensual"])),
            ("Día de corte", str(contrato["dia_corte"])),
            ("Inicio", f"{contrato['fecha_inicio']:%d/%m/%Y}"),
            ("Renovación", f"{contrato['fecha_renovacion']:%d/%m/%Y}"),
        ],
        columnas=3,
    )
    _peludos_planes_y_condiciones(pdf, mascotas, planes)
    return bytes(pdf.output())


def _peludos_planes_y_condiciones(
    pdf: marca.PdfMarca, mascotas: list[dict[str, Any]], planes: list[dict[str, Any]]
) -> None:
    """Lo que comparten el contrato y su modelo: los peludos, lo que cubre cada plan con sus
    condiciones y las condiciones generales con su version."""
    marca.titulo_seccion(pdf, "Peludos afiliados")
    marca.tabla(
        pdf,
        ("Peludo", "Especie y raza", "Plan", "Valor mensual"),
        [
            (
                m["nombre"],
                f"{m['especie']} {m.get('raza') or ''}".strip(),
                m["plan"],
                formato_cop(m["valor_mensual"]),
            )
            for m in mascotas
        ],
        (25, 30, 25, 20),
    )
    for plan in planes:
        if plan.get("beneficios"):
            marca.titulo_seccion(
                pdf,
                f"Beneficios de {plan['nombre']}",
                marca.COLOR_PLAN.get(plan.get("color") or "", marca.MARINO),
            )
            marca.tabla(
                pdf,
                ("Servicio", "Cupo", "Cobertura", "Aplica"),
                [
                    (b["tipo_servicio"], _cupo(b), _cobertura(b), _desde(b.get("carencia_dias")))
                    for b in plan["beneficios"]
                ],
                (30, 22, 28, 20),
            )
        if plan.get("adicionales"):
            marca.titulo_seccion(pdf, f"Beneficios adicionales de {plan['nombre']}")
            marca.tabla(
                pdf,
                ("Beneficio", "Cubre", "Aplica"),
                [
                    (
                        a["nombre"] + (" (lo presta un tercero)" if a["tercero"] else ""),
                        a["cubre"],
                        _desde(a["carencia_dias"]),
                    )
                    for a in plan["adicionales"]
                ],
                (45, 35, 20),
            )
        # Las condiciones del plan que el registro dijo de frente (R3-PUB-02), si TIMU las escribio.
        for etiqueta, texto in (
            ("Carencia", plan.get("carencia")),
            ("No cubre", plan.get("exclusiones")),
        ):
            if texto:
                marca.parrafo(pdf, f"{etiqueta}: {texto}")
    marca.titulo_seccion(pdf, "Condiciones generales")
    for i, condicion in enumerate(CONDICIONES, start=1):
        marca.parrafo(pdf, f"{i}. {condicion}")
    pdf.ln(2)
    marca.parrafo(
        pdf,
        f"Versión de las condiciones: {TERMINOS_VERSION}. La aceptación queda registrada en la "
        "plataforma con su fecha, el medio y los datos de la sesión.",
        tamano=8,
        color=marca.SUAVE,
    )


def generar_modelo(
    *, mascotas: list[dict[str, Any]], planes: list[dict[str, Any]], afiliacion: dict[str, Any]
) -> bytes:
    """El contrato antes de pagar (R3-PUB-02): lo que la familia eligio, con las mismas
    condiciones que firmara, y sin sus datos, que se piden despues del pago. Asi acepta un
    documento que puede leer."""
    pdf = marca.PdfMarca()
    pdf.set_title("Modelo del contrato de afiliación")
    pdf.set_author("TIMU")
    pdf.add_page()
    marca.cabecera(pdf, "Modelo del contrato de afiliación", "Con los planes que elegiste")
    marca.titulo_seccion(pdf, "Titular")
    marca.parrafo(
        pdf,
        "Los datos del titular y la dirección se completan después del pago; el contrato "
        "firmado los lleva, con su número y sus fechas.",
    )
    marca.titulo_seccion(pdf, "Afiliación")
    marca.datos(
        pdf,
        [
            ("Ciudad", afiliacion["ciudad"]),
            ("Forma de pago", str(afiliacion["periodicidad"]).capitalize()),
            ("Valor de cada cuota", formato_cop(afiliacion["valor_periodo"])),
            ("Valor mensual", formato_cop(afiliacion["valor_mensual"])),
            ("Inicio", "Al aprobarse el pago"),
            ("Vigencia", "Un año"),
        ],
        columnas=3,
    )
    _peludos_planes_y_condiciones(pdf, mascotas, planes)
    return bytes(pdf.output())
