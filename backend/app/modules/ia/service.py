"""F4-IAA Capa de IA con control: prompts versionados, limite de gasto, registro de cada
consulta y evaluacion obligatoria antes de activar una version.

Quien la usa debe tolerar que no este: sin clave, sin presupuesto, con el proveedor caido
o con una respuesta rechazada, `consultar` levanta `IANoDisponible` y el flujo sigue por
su camino sin IA (el bot pasa a un asesor, el profesional responde sin borrador).
"""

import json
import time
from datetime import date, datetime
from datetime import time as hora
from decimal import Decimal
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errores import NoEncontrado, ReglaNegocio
from app.core.tiempo import ZONA_NEGOCIO, ahora, hoy
from app.integrations import claude
from app.modules.ia import guiones
from app.modules.ia.models import CasoPruebaIA, ConsultaIA, PromptIA

logger = structlog.get_logger(__name__)

# Respuesta estructurada de cada prompt (JSON Schema). Un codigo sin esquema responde texto.
ESQUEMAS: dict[str, dict[str, Any]] = {
    "comercial_guion": {
        "type": "object",
        "properties": {
            "alcance": {"type": "string", "enum": ["dentro", "fuera"]},
            "respuesta": {"type": "string"},
        },
        "required": ["alcance", "respuesta"],
        "additionalProperties": False,
    },
    "veterinario_borrador": {
        "type": "object",
        "properties": {
            "borrador": {"type": "string"},
            "senales_alarma": {"type": "array", "items": {"type": "string"}},
            "recomendar_presencial": {"type": "boolean"},
        },
        "required": ["borrador", "senales_alarma", "recomendar_presencial"],
        "additionalProperties": False,
    },
}


class IANoDisponible(Exception):
    """La consulta no se hizo o no sirve; quien llama sigue sin IA."""


# --- Prompts versionados ----------------------------------------------------------------------


def prompt_activo(db: Session, codigo: str) -> PromptIA | None:
    return db.scalar(select(PromptIA).where(PromptIA.codigo == codigo, PromptIA.estado == "activo"))


def obtener_prompt(db: Session, prompt_id: UUID) -> PromptIA:
    prompt = db.get(PromptIA, prompt_id)
    if prompt is None:
        raise NoEncontrado("Prompt no encontrado")
    return prompt


def crear_version(db: Session, codigo: str, sistema: str, nota: str | None) -> PromptIA:
    if codigo not in ESQUEMAS:
        raise ReglaNegocio(f"Codigo de prompt desconocido: {codigo}")
    ultima = db.scalar(select(func.max(PromptIA.version)).where(PromptIA.codigo == codigo)) or 0
    prompt = PromptIA(
        codigo=codigo, version=ultima + 1, sistema=sistema, nota=nota, estado="borrador"
    )
    db.add(prompt)
    db.flush()
    return prompt


def activar(db: Session, prompt: PromptIA, usuario_id: UUID | None) -> PromptIA:
    """Solo entra en operacion una version que paso todos sus casos de prueba."""
    evaluacion = prompt.evaluacion or {}
    if not evaluacion.get("total"):
        raise ReglaNegocio("Evalue la version con sus casos de prueba antes de activarla")
    if evaluacion.get("aprobados") != evaluacion.get("total"):
        raise ReglaNegocio(
            f"La version fallo {evaluacion['total'] - evaluacion['aprobados']} de "
            f"{evaluacion['total']} casos de prueba"
        )
    for anterior in db.scalars(
        select(PromptIA).where(PromptIA.codigo == prompt.codigo, PromptIA.estado == "activo")
    ):
        anterior.estado = "retirado"
    prompt.estado = "activo"
    prompt.activado_por_id = usuario_id
    db.flush()
    return prompt


def sembrar(db: Session) -> int:
    """Primera version de cada prompt (en borrador: se activa tras evaluarla) y sus casos de
    prueba iniciales. No toca lo que ya exista."""
    creados = 0
    for codigo, sistema in guiones.PROMPTS.items():
        if not db.scalar(select(PromptIA.id).where(PromptIA.codigo == codigo)):
            crear_version(db, codigo, sistema, "Version inicial")
            creados += 1
        if not db.scalar(select(CasoPruebaIA.id).where(CasoPruebaIA.prompt_codigo == codigo)):
            for caso in guiones.CASOS[codigo]:
                db.add(CasoPruebaIA(prompt_codigo=codigo, **caso))
    db.flush()
    return creados


# --- Limite de gasto y consulta ---------------------------------------------------------------


def gasto_mes(db: Session, dia: date | None = None) -> Decimal:
    dia = dia or hoy()
    inicio = datetime.combine(dia.replace(day=1), hora.min, ZONA_NEGOCIO)
    return Decimal(
        db.scalar(select(func.sum(ConsultaIA.costo_usd)).where(ConsultaIA.created_at >= inicio))
        or 0
    )


def _registrar(db: Session, **datos: Any) -> None:
    with db.begin_nested():
        db.add(ConsultaIA(**datos))


def consultar(
    db: Session,
    codigo: str,
    entrada: str,
    *,
    contexto: str | None = None,
    prompt: PromptIA | None = None,
) -> Any:
    """Consulta con el prompt activo del codigo (o el indicado, para evaluarlo). Devuelve el
    JSON ya validado si el codigo tiene esquema. Toda consulta queda registrada, tambien las
    que no se hicieron por falta de clave o de presupuesto."""
    prompt = prompt or prompt_activo(db, codigo)
    base: dict[str, Any] = {
        "prompt_codigo": codigo,
        "prompt_version": prompt.version if prompt else None,
        "contexto": contexto,
        "entrada": entrada[:4000],
    }
    if not claude.configurado() or prompt is None:
        _registrar(db, **base, estado="desactivada")
        raise IANoDisponible("La capa de IA no esta configurada o no hay prompt activo")
    if gasto_mes(db) >= Decimal(str(settings.IA_PRESUPUESTO_MENSUAL_USD)):
        _registrar(db, **base, estado="presupuesto_agotado")
        raise IANoDisponible("Se agoto el presupuesto mensual de IA")

    inicio = time.perf_counter()
    try:
        respuesta = claude.completar(prompt.sistema, entrada, esquema=ESQUEMAS.get(codigo))
    except claude.ErrorIA as e:
        _registrar(db, **base, estado="error", error=str(e)[:2000])
        raise IANoDisponible(str(e)) from e
    latencia = int((time.perf_counter() - inicio) * 1000)
    uso = respuesta.uso
    registro = {
        **base,
        "modelo": respuesta.modelo,
        "tokens_entrada": uso.entrada,
        "tokens_salida": uso.salida,
        "tokens_cache_lectura": uso.cache_lectura,
        "tokens_cache_escritura": uso.cache_escritura,
        "costo_usd": claude.costo(respuesta.modelo, uso),
        "latencia_ms": latencia,
        "request_id": respuesta.request_id,
        "salida": respuesta.texto[:8000],
    }
    if respuesta.rechazada:
        _registrar(db, **registro, estado="rechazo")
        raise IANoDisponible("El modelo declino responder")
    if codigo not in ESQUEMAS:
        _registrar(db, **registro, estado="ok")
        return respuesta.texto
    try:
        datos = json.loads(respuesta.texto)
    except json.JSONDecodeError as e:
        _registrar(db, **registro, estado="error", error="Respuesta no es JSON valido")
        raise IANoDisponible("Respuesta no es JSON valido") from e
    _registrar(db, **registro, estado="ok")
    return datos


# --- F4-IAA-04 Evaluacion ---------------------------------------------------------------------


def _cumple(resultado: Any, esperado: dict[str, Any]) -> tuple[bool, str]:
    texto = (
        resultado.lower()
        if isinstance(resultado, str)
        else json.dumps(resultado, ensure_ascii=False).lower()
    )
    if "no_vacio" in esperado:
        valor = resultado.get(esperado["no_vacio"]) if isinstance(resultado, dict) else None
        if not valor:
            return False, f"{esperado['no_vacio']} vino vacio"
    if "campo" in esperado:
        valor = resultado.get(esperado["campo"]) if isinstance(resultado, dict) else None
        if valor != esperado["igual"]:
            return False, f"{esperado['campo']} fue {valor!r}, se esperaba {esperado['igual']!r}"
    for palabra in esperado.get("contiene", []):
        if palabra.lower() not in texto:
            return False, f"no menciona '{palabra}'"
    for palabra in esperado.get("no_contiene", []):
        if palabra.lower() in texto:
            return False, f"menciona '{palabra}', que no deberia"
    return True, "ok"


def evaluar(db: Session, prompt: PromptIA) -> dict[str, Any]:
    """Corre todos los casos de prueba del codigo contra ESTA version y guarda el resultado.
    Cada caso es una consulta real: cuesta, y queda registrada como tal."""
    casos = list(
        db.scalars(select(CasoPruebaIA).where(CasoPruebaIA.prompt_codigo == prompt.codigo))
    )
    if not casos:
        raise ReglaNegocio("No hay casos de prueba para este prompt")
    detalle = []
    for caso in casos:
        try:
            resultado = consultar(
                db, prompt.codigo, caso.entrada, contexto=f"evaluacion:{prompt.id}", prompt=prompt
            )
            aprobado, motivo = _cumple(resultado, caso.esperado)
        except IANoDisponible as e:
            aprobado, motivo = False, f"sin respuesta: {e}"
        detalle.append({"caso": caso.nombre, "aprobado": aprobado, "motivo": motivo})
    prompt.evaluacion = {
        "total": len(detalle),
        "aprobados": sum(d["aprobado"] for d in detalle),
        "detalle": detalle,
        "en": ahora().isoformat(),
    }
    prompt.evaluado_en = ahora()
    db.flush()
    return prompt.evaluacion


# --- F4-IAA-02 / 03 Usos ----------------------------------------------------------------------


def responder_comercial(db: Session, pregunta: str, telefono: str) -> str | None:
    """Respuesta dentro del guion aprobado, o None si la pregunta sale de el (y entonces la
    conversacion pasa a un asesor)."""
    from app.modules.planes.models import Plan

    planes = [
        f"{p.nombre}: {p.valor_mensual} COP/mes, hasta {p.cupos_mascotas} mascotas"
        for p in db.scalars(select(Plan).where(Plan.activo.is_(True)).order_by(Plan.valor_mensual))
    ]
    entrada = (
        "Planes vigentes:\n"
        + "\n".join(planes or ["(sin planes cargados)"])
        + f"\n\nMensaje de la persona:\n{pregunta}"
    )
    datos = consultar(db, "comercial_guion", entrada, contexto=f"whatsapp:{telefono}")
    if datos["alcance"] != "dentro" or not datos["respuesta"].strip():
        return None
    return str(datos["respuesta"]).strip()


def borrador_veterinario(db: Session, solicitud_id: UUID) -> dict[str, Any]:
    """Borrador para que el profesional lo revise. Nunca se envia solo: queda guardado en la
    solicitud y la respuesta a la familia sigue saliendo de una plantilla aprobada."""
    from app.modules.clinica.models import SolicitudVirtual
    from app.modules.familias.models import Mascota

    solicitud = db.get(SolicitudVirtual, solicitud_id)
    if solicitud is None:
        raise NoEncontrado("Solicitud no encontrada")
    mascota = db.get(Mascota, solicitud.mascota_id)
    assert mascota is not None
    edad = (
        f"{(hoy() - mascota.fecha_nacimiento).days // 365} anos"
        if mascota.fecha_nacimiento
        else "edad desconocida"
    )
    entrada = (
        f"Paciente: {mascota.especie}, {mascota.raza or 'raza no registrada'}, {edad}, "
        f"{mascota.peso_kg or 'peso no registrado'} kg.\n"
        f"Consulta de la familia:\n{solicitud.motivo}"
    )
    datos = consultar(db, "veterinario_borrador", entrada, contexto=f"solicitud:{solicitud.id}")
    solicitud.borrador_ia = datos
    solicitud.borrador_en = ahora()
    db.flush()
    return dict(datos)


def consumo(db: Session, dia: date | None = None) -> dict[str, Any]:
    dia = dia or hoy()
    inicio = datetime.combine(dia.replace(day=1), hora.min, ZONA_NEGOCIO)
    filas = db.execute(
        select(
            ConsultaIA.prompt_codigo,
            ConsultaIA.estado,
            func.count(),
            func.sum(ConsultaIA.costo_usd),
        )
        .where(ConsultaIA.created_at >= inicio)
        .group_by(ConsultaIA.prompt_codigo, ConsultaIA.estado)
    ).all()
    gasto = gasto_mes(db, dia)
    presupuesto = Decimal(str(settings.IA_PRESUPUESTO_MENSUAL_USD))
    return {
        "mes": f"{dia:%Y-%m}",
        "gasto_usd": float(gasto),
        "presupuesto_usd": float(presupuesto),
        "disponible_usd": float(max(presupuesto - gasto, Decimal(0))),
        "por_prompt": [
            {"prompt": p, "estado": e, "consultas": n, "costo_usd": float(c or 0)}
            for p, e, n, c in filas
        ],
    }
