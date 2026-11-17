"""DEU-24 Los documentos que recibe la familia llevan la marca de TIMU, como el carnet: las
fuentes de la marca (las base del PDF son latin-1 y estropean las tildes) y lo que dicen en
palabras, nunca un codigo del sistema ni «ilimitado»."""

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from app.modules.afiliaciones import documento as contrato
from app.modules.cartera.periodos import nombre_cuota, nombre_medio
from app.modules.clinica import documento as formula
from app.modules.portal import documento as comprobante

pytestmark = pytest.mark.unit


def _con_la_marca(pdf: bytes) -> None:
    assert pdf.startswith(b"%PDF")
    assert b"Inter" in pdf and b"GeosansLight" in pdf
    assert b"Helvetica" not in pdf


def test_el_contrato_lleva_la_marca():
    _con_la_marca(
        contrato.generar_contrato(
            numero="AFI-1",
            fecha=date(2026, 11, 15),
            familia={
                "titular_nombre": "Ana Ruiz",
                "tipo_documento": "CC",
                "documento": "1020304050",
                "telefono": "+573001112233",
                "email": "ana@example.com",
                "direccion": "Calle 10 # 20-30",
                "ciudad": "Medellín",
            },
            mascotas=[
                {
                    "nombre": "Luna",
                    "especie": "canino",
                    "raza": "Criolla",
                    "plan": "Mi Amigo Fiel",
                    "valor_mensual": Decimal("69000"),
                }
            ],
            planes=[
                {
                    "nombre": "Mi Amigo Fiel",
                    "color": "verde",
                    "beneficios": [
                        {
                            "tipo_servicio": "Consulta domiciliaria",
                            "cupo": None,
                            "periodo_cupo": "mensual",
                            "cobertura_pct": 100,
                        }
                    ],
                }
            ],
            contrato={
                "periodicidad": "mensual",
                "valor_periodo": Decimal("69000"),
                "valor_mensual": Decimal("69000"),
                "dia_corte": 5,
                "fecha_inicio": date(2026, 11, 15),
                "fecha_renovacion": date(2027, 11, 15),
            },
        )
    )


def test_el_modelo_del_contrato_dice_lo_elegido_y_las_condiciones_del_plan(monkeypatch):
    """R3-PUB-02: antes de pagar, sin datos de la familia; con la carencia y lo que no cubre
    cada plan, como el contrato que se firma."""
    dicho: list[str] = []
    parrafo = contrato.marca.parrafo
    monkeypatch.setattr(
        contrato.marca,
        "parrafo",
        lambda pdf, texto, **kw: (dicho.append(texto), parrafo(pdf, texto, **kw))[1],
    )
    pdf = contrato.generar_modelo(
        mascotas=[
            {
                "nombre": "Toby",
                "especie": "Canino",
                "plan": "Mi Amigo Fiel",
                "valor_mensual": Decimal("69000"),
            }
        ],
        planes=[
            {
                "nombre": "Mi Amigo Fiel",
                "color": "verde",
                "carencia": "Sin periodo de carencia.",
                "exclusiones": "Excluye preexistencias.",
                "beneficios": [
                    {
                        "tipo_servicio": "Consulta domiciliaria",
                        "cupo": 1,
                        "periodo_cupo": "mensual",
                        "cobertura_pct": 100,
                    }
                ],
            }
        ],
        afiliacion={
            "ciudad": "Medellín",
            "periodicidad": "trimestral",
            "valor_periodo": Decimal("207000"),
            "valor_mensual": Decimal("69000"),
        },
    )
    _con_la_marca(pdf)
    assert (
        "Carencia: Sin periodo de carencia." in dicho
        and "No cubre: Excluye preexistencias." in dicho
    )
    assert any(t.startswith("Los datos del titular") for t in dicho)


def test_el_telefono_del_contrato_va_en_grupos():
    assert contrato._telefono("+573001112233") == "+57 300 111 2233"
    assert contrato._telefono("+12025550123") == "+12025550123"


def test_el_cupo_se_dice_de_frente_sin_ilimitado():
    assert contrato._cupo({"cupo": None, "periodo_cupo": "mensual"}) == "Sin tope de usos al mes"
    assert contrato._cupo({"cupo": 2, "periodo_cupo": "anual"}) == "2 al año"


def test_la_formula_lleva_la_marca():
    _con_la_marca(
        formula.generar_formula(
            fecha=date(2026, 11, 15),
            mascota={"nombre": "Luna", "especie": "canino", "peso_kg": 12.5},
            titular="Ana Ruiz",
            profesional="Valentina Gómez",
            diagnostico="Otitis externa",
            items=[{"medicamento": "Otomax", "dosis": "5 gotas", "frecuencia": "cada 12 horas"}],
            indicaciones="Limpiar el oído antes de aplicar.",
        )
    )


def test_el_comprobante_lleva_la_marca():
    _con_la_marca(
        comprobante.generar_comprobante(
            familia={"titular": "Ana Ruiz", "documento": "1020304050"},
            pago={
                "referencia": "WEB-1",
                "fecha": datetime(2026, 11, 15, 15, 30, tzinfo=UTC),
                "medio": "CARD",
                "valor": Decimal("69000"),
            },
            aplicaciones=[("Cuota de noviembre de 2026", Decimal("69000"))],
        )
    )


def test_el_comprobante_nombra_la_cuota_por_su_mes_y_el_medio_en_palabras():
    assert nombre_cuota("2026-10", 1) == "Cuota de octubre de 2026"
    assert nombre_cuota("2027-01", 3) == "Cuota de enero a marzo de 2027"
    assert nombre_cuota("2026-11", 3) == "Cuota de noviembre de 2026 a enero de 2027"
    assert nombre_cuota("2026-10", 1, "ajuste", "Ajuste por cambio de plan") == (
        "Ajuste por cambio de plan"
    )
    assert nombre_medio("CARD") == "Tarjeta"
    assert nombre_medio("consignacion") == "Consignación"
    assert nombre_medio("algo_nuevo") == "algo_nuevo"
