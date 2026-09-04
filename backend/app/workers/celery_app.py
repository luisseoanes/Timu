"""Celery + Redis: automatizaciones y tareas programadas (seccion C)."""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "timu",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.tasks.cartera",
        "app.workers.tasks.preventivos",
        "app.workers.tasks.comunicaciones",
        "app.workers.tasks.encuestas",
    ],
)

celery_app.conf.update(
    task_track_started=True,
    timezone="America/Bogota",
    beat_schedule={
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
        # 6.21 seguimiento post atencion
        "encuestas-seguimiento": {
            "task": "encuestas.enviar_seguimientos",
            "schedule": crontab(hour=15, minute=0),
        },
    },
)
