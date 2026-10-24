"""Reglas de arranque. Se crean solo si no existen: despues las administra TIMU desde el
panel y una nueva carga no pisa sus cambios. Los dias y cortes son supuestos iniciales
que TIMU debe confirmar."""

from typing import Any


def _desde(campo: str, n: int) -> dict[str, Any]:
    return {"campo": campo, "op": "gte", "valor": n}


REGLAS: list[dict[str, Any]] = [
    # F1-CAR-03 Estado de cartera por dias de mora de la cuota mas antigua sin pagar.
    {
        "codigo": "cartera_congelada",
        "nombre": "Congelar a los 30 dias de mora",
        "evento": "cartera.estado",
        "condicion": _desde("dias_mora", 30),
        "accion": {"tipo": "estado", "estado": "congelada"},
        "prioridad": 10,
        "detener": True,
    },
    {
        "codigo": "cartera_en_mora",
        "nombre": "En mora desde 5 dias de vencida la cuota",
        "evento": "cartera.estado",
        "condicion": _desde("dias_mora", 5),
        "accion": {"tipo": "estado", "estado": "en_mora"},
        "prioridad": 20,
        "detener": True,
    },
    {
        "codigo": "cartera_al_dia",
        "nombre": "Al dia",
        "evento": "cartera.estado",
        "condicion": {},
        "accion": {"tipo": "estado", "estado": "activa"},
        "prioridad": 100,
        "detener": True,
    },
    # F1-CAR-04 Avisos escalonados. Se envia el mas avanzado que aun no se haya enviado.
    *[
        {
            "codigo": f"alerta_mora_{dias}",
            "nombre": f"Aviso de mora a los {dias} dias",
            "evento": "cartera.alerta",
            "condicion": _desde("dias_mora", dias),
            "accion": {"tipo": "notificar", "plantilla": plantilla, "clave": f"mora_{dias}"},
            "prioridad": 100 - dias,
        }
        for dias, plantilla in (
            (1, "cuota_vencida"),
            (5, "aviso_mora"),
            (15, "aviso_mora"),
            (25, "aviso_congelamiento"),
        )
    ],
    # F1-CAR-07 Renovacion anual.
    {
        "codigo": "renovacion_30_dias",
        "nombre": "Gestionar renovacion 30 dias antes",
        "evento": "cartera.renovacion",
        "condicion": {"campo": "dias_para_renovacion", "op": "lte", "valor": 30},
        "accion": {
            "tipo": "tarea",
            "titulo": "Gestionar renovacion del contrato",
            "area": "comercial",
            "prioridad": "media",
            "vence_en_dias": 7,
        },
    },
    # F1-PLA-02 / F1-PLA-03 Planes.
    {
        "codigo": "cambio_plan_prorrateo",
        "nombre": "Cambio de plan con prorrateo diario",
        "evento": "plan.cambio",
        "condicion": {},
        "accion": {"tipo": "prorrateo", "modo": "diario"},
        "prioridad": 100,
        "detener": True,
    },
    {
        "codigo": "cambio_plan_en_mora",
        "nombre": "No cambiar de plan con cartera vencida",
        "evento": "plan.cambio",
        "condicion": {"campo": "familia.estado", "op": "in", "valor": ["en_mora", "congelada"]},
        "accion": {
            "tipo": "rechazar",
            "motivo": "La familia debe estar al dia para cambiar de plan",
        },
        "prioridad": 10,
        "detener": True,
    },
    {
        "codigo": "mascota_sobre_cupo",
        "nombre": "Sin cupo adicional por defecto",
        "evento": "plan.mascota",
        "condicion": {},
        "accion": {
            "tipo": "rechazar",
            "motivo": "El plan no tiene cupo para otra mascota; cambie a un plan con mas cupos",
        },
        "prioridad": 100,
        "detener": True,
    },
    # F1-PLA-04 Recomendacion.
    {
        "codigo": "recomendar_familiar",
        "nombre": "Dos o mas mascotas: plan familiar",
        "evento": "plan.recomendacion",
        "condicion": _desde("mascotas.total", 2),
        "accion": {
            "tipo": "recomendar",
            "plan_codigo": "familiar",
            "motivo": "Cubre varias mascotas con un solo valor mensual",
        },
        "prioridad": 50,
        "detener": True,
    },
    {
        "codigo": "recomendar_individual",
        "nombre": "Una mascota: plan individual",
        "evento": "plan.recomendacion",
        "condicion": {},
        "accion": {
            "tipo": "recomendar",
            "plan_codigo": "individual",
            "motivo": "Es el plan de menor valor para una sola mascota",
        },
        "prioridad": 100,
        "detener": True,
    },
    # F1-SER-03 Disparadores de servicios.
    {
        "codigo": "servicio_requiere_autorizacion",
        "nombre": "Autorizar servicio pendiente",
        "evento": "servicio.transicion",
        "condicion": {"campo": "estado_nuevo", "op": "eq", "valor": "pendiente_autorizacion"},
        "accion": {
            "tipo": "tarea",
            "titulo": "Autorizar servicio",
            "area": "medico",
            "prioridad": "alta",
            "vence_en_dias": 1,
        },
    },
    {
        "codigo": "servicio_reprogramado",
        "nombre": "Reagendar servicio reprogramado",
        "evento": "servicio.transicion",
        "condicion": {"campo": "estado_nuevo", "op": "eq", "valor": "reprogramado"},
        "accion": {
            "tipo": "tarea",
            "titulo": "Acordar nueva fecha con la familia",
            "area": "operaciones",
            "prioridad": "media",
            "vence_en_dias": 1,
        },
    },
]
