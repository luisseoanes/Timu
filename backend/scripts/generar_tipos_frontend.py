"""Genera frontend/src/types/api.ts desde los schemas del OpenAPI del backend.

Los tipos del frontend son el espejo de los schemas de Pydantic (docs/frontend/
conventions.md). Generarlos evita que se desvien: si cambia un schema, se corre esto en
el mismo cambio de codigo.

Uso:  cd backend && python scripts/generar_tipos_frontend.py
"""

import os
import sys
from pathlib import Path
from typing import Any

os.environ.setdefault("ENVIRONMENT", "test")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402

DESTINO = Path(__file__).resolve().parents[2] / "frontend" / "src" / "types" / "api.ts"

# Lo que consume el panel. Agregar aqui un schema nuevo cuando una pantalla lo use.
ESQUEMAS = [
    "Rol",
    "EstadoAfiliacion",
    "EstadoServicio",
    "TipoDocumento",
    "MascotaRead",
    "FamiliaRead",
    "CambioHistorial",
    "UsuarioRead",
    "CiudadRead",
    "EspecieRead",
    "TipoServicioRead",
    "PlanRead",
    "BeneficioRead",
    "ContratoListado",
    "ContratoRead",
    "CuotaRead",
    "PagoRead",
    "PlanResumen",
    "ProximoCobro",
    "EstadoCuenta",
    "EventoPasarelaRead",
    "TareaRead",
    "ServicioRead",
    "PendienteRead",
    "PasoRead",
    "CupoRead",
    "ElegibilidadRead",
    "EventoRead",
    "CarnetEmitidoRead",
    "AdjuntoRead",
    "FormulaRead",
    "PlanificacionRead",
    "CampanaRead",
    "SegmentoRead",
    "EjecucionRead",
    "InteresadoRead",
    "ConversacionRead",
    "EncuestaRead",
    "ClinicaRead",
    "ConvenioRead",
    "RemisionRead",
    "ReporteRead",
    "PromptRead",
    "CasoRead",
    "ConsultaRead",
    "MensajeRead",
    "FranjaRead",
    "RespuestaRead",
]
# Nombres de schema repetidos entre modulos: se exponen con un nombre propio.
ALIAS = {
    "app__modules__clinica__router__SolicitudRead": "SolicitudVirtualRead",
    "app__modules__clinica__router__PlantillaRead": "PlantillaConsultaRead",
    "app__modules__afiliaciones__router__SolicitudRead": "SolicitudAfiliacionRead",
    "app__modules__comunicaciones__schemas__PlantillaRead": "PlantillaWhatsAppRead",
}
PRIMITIVOS = {
    "string": "string",
    "integer": "number",
    "number": "number",
    "boolean": "boolean",
    "null": "null",
}


def tipo(prop: dict[str, Any]) -> str:
    if "$ref" in prop:
        nombre = prop["$ref"].split("/")[-1]
        return ALIAS.get(nombre, nombre)
    if "anyOf" in prop:
        return " | ".join(dict.fromkeys(tipo(p) for p in prop["anyOf"]))
    if "enum" in prop:
        return " | ".join(f"'{v}'" for v in prop["enum"])
    if "const" in prop:
        return f"'{prop['const']}'"
    t = prop.get("type")
    if t == "array":
        return f"{tipo(prop.get('items', {}))}[]"
    if t == "object":
        extra = prop.get("additionalProperties")
        return f"Record<string, {tipo(extra) if isinstance(extra, dict) and extra else 'unknown'}>"
    return PRIMITIVOS.get(str(t), "unknown")


def generar() -> str:
    schemas = app.openapi()["components"]["schemas"]
    lineas = [
        "// Generado por backend/scripts/generar_tipos_frontend.py desde el OpenAPI.",
        "// No editar a mano: si cambia un schema de Pydantic, se regenera en el mismo cambio.",
        "// Los decimales llegan como string en JSON; se formatean con lib/formato.ts.",
        "",
    ]
    for nombre in [*ESQUEMAS, *ALIAS]:
        esquema = schemas[nombre]
        expuesto = ALIAS.get(nombre, nombre)
        if "enum" in esquema:
            lineas += [f"export type {expuesto} = {tipo(esquema)}", ""]
            continue
        requeridos = set(esquema.get("required", []))
        lineas.append(f"export interface {expuesto} {{")
        for campo, prop in esquema.get("properties", {}).items():
            opcional = "" if campo in requeridos else "?"
            lineas.append(f"  {campo}{opcional}: {tipo(prop)}")
        lineas += ["}", ""]
    return "\n".join(lineas)


if __name__ == "__main__":
    DESTINO.write_text(generar(), encoding="utf-8")
    print(f"Escrito {DESTINO}")
