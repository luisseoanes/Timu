"""F4-DAS-03 Exportacion de indicadores a CSV y Excel."""

import csv
import io
from typing import Any

from app.modules.dashboard.service import definiciones, filas_planas

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def a_csv(resultado: dict[str, Any]) -> bytes:
    salida = io.StringIO()
    escritor = csv.writer(salida)
    p = resultado["periodo"]
    escritor.writerow(["periodo", p["desde"], p["hasta"], p["ciudad"] or "todas"])
    escritor.writerow(["indicador", "detalle", "valor"])
    escritor.writerows(filas_planas(resultado))
    # BOM para que Excel abra bien las tildes al hacer doble clic.
    return ("\ufeff" + salida.getvalue()).encode("utf-8")


def a_xlsx(resultado: dict[str, Any]) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Font

    libro = Workbook()
    hoja = libro.active
    assert hoja is not None
    hoja.title = "Indicadores"
    p = resultado["periodo"]
    hoja.append(["Periodo", str(p["desde"]), str(p["hasta"]), p["ciudad"] or "todas"])
    hoja.append([])
    hoja.append(["Indicador", "Detalle", "Valor"])
    for celda in hoja[3]:
        celda.font = Font(bold=True)
    for fila in filas_planas(resultado):
        hoja.append(list(fila))
    hoja.column_dimensions["A"].width = 34
    hoja.column_dimensions["B"].width = 24
    hoja.column_dimensions["C"].width = 16

    formulas = libro.create_sheet("Definiciones")
    formulas.append(["Codigo", "Indicador", "Formula", "Unidad"])
    for celda in formulas[1]:
        celda.font = Font(bold=True)
    for d in definiciones():
        formulas.append([d["codigo"], d["nombre"], d["formula"], d["unidad"]])
    formulas.column_dimensions["C"].width = 90

    salida = io.BytesIO()
    libro.save(salida)
    return salida.getvalue()
