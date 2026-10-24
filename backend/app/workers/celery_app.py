"""Celery + Redis: automatizaciones y tareas programadas (seccion C)."""

from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_process_init

from app.core.config import settings
from app.core.observabilidad import configurar_logging, configurar_sentry

celery_app = Celery(
    "timu",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.tasks.cartera",
        "app.workers.tasks.preventivos",
        "app.workers.tasks.comunicaciones",
        "app.workers.tasks.encuestas",
        "app.workers.tasks.familias",
        "app.workers.tasks.rutas",
        "app.workers.tasks.campanas",
        "app.workers.tasks.dashboard",
        "app.workers.tasks.ia",
        "app.workers.tasks.outbox",
    ],
)


@worker_process_init.connect
def _al_iniciar_worker(**_: object) -> None:
    """F0-08 Los errores de las tareas (cobros, avisos de mora) llegan al monitoreo igual
    que los de la API, y sus registros salen con el mismo formato."""
    configurar_logging(json=settings.LOG_JSON, debug=settings.DEBUG)
    configurar_sentry(settings.SENTRY_DSN, settings.ENVIRONMENT, celery=True)


celery_app.conf.update(
    task_track_started=True,
    timezone="America/Bogota",
    beat_schedule={
        # Efectos externos pendientes (ver app/core/outbox.py). Cada minuto para que
        # un WhatsApp no espere mas de eso desde que se confirmo la transaccion.
        "outbox-drenar": {
            "task": "outbox.drenar",
            "schedule": 60.0,
        },
        # F1-WHA-01 mensajes cuya tarea se perdio (worker caido a mitad del envio)
        "comunicaciones-reencolar": {
            "task": "comunicaciones.reencolar_pendientes",
            "schedule": crontab(minute="*/15"),
        },
        # F1-CAR-02 emision de cuotas antes de su vencimiento
        "cartera-generar-cuotas": {
            "task": "cartera.generar_cuotas",
            "schedule": crontab(hour=5, minute=0),
        },
        # F1-CAR-08 cobro recurrente (antes de revisar mora, para no avisar a quien ya pago)
        "cartera-cobro-recurrente": {
            "task": "cartera.cobrar_recurrentes",
            "schedule": crontab(hour=5, minute=15),
        },
        # F1-CAR-09 cobros sin confirmacion de la pasarela
        "cartera-conciliar-pendientes": {
            "task": "cartera.conciliar_pendientes",
            "schedule": crontab(minute=40),
        },
        # 6.2 mora, alertas, congelamiento y reactivacion
        "cartera-revisar-mora": {
            "task": "cartera.revisar_mora",
            "schedule": crontab(hour=6, minute=0),
        },
        # 6.4 deteccion de renovaciones anuales
        "cartera-renovaciones": {
            "task": "cartera.detectar_renovaciones",
            "schedule": crontab(hour=6, minute=30),
        },
        # 6.8 / 6.13 agenda preventiva del dia
        "preventivos-generar-agenda": {
            "task": "preventivos.generar_agenda",
            "schedule": crontab(hour=5, minute=30),
        },
        # F3-CAM-02 / 04 campanas: lanzar las programadas y despachar al ritmo permitido
        "campanas-lanzar-programadas": {
            "task": "campanas.lanzar_programadas",
            "schedule": crontab(minute="*/5"),
        },
        "campanas-despachar": {
            "task": "campanas.despachar",
            "schedule": 60.0,
        },
        # F4-DAS-03 reportes gerenciales por correo
        "dashboard-reportes": {
            "task": "dashboard.enviar_reportes",
            "schedule": crontab(hour=7, minute=0),
        },
        # F3-ENC-01 / 03 encuestas y seguimientos cuya hora llego
        "encuestas-enviar-pendientes": {
            "task": "encuestas.enviar_pendientes",
            "schedule": crontab(minute="*/15"),
        },
    },
)
