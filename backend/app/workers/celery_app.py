"""Celery + Redis: automatizaciones y tareas programadas (seccion C)."""

from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_process_init

# El worker no carga app.main: sin el registro unico de modelos, SQLAlchemy no resuelve
# las llaves foraneas hacia tablas de otros modulos (p. ej. rutas -> usuarios) y el
# primer flush que las toque revienta.
import app.models  # noqa: F401
from app.core.config import settings
from app.core.database import SQL_ROL_CONECTADO, motivo_rol_privilegiado, sync_engine
from app.core.observabilidad import configurar_logging, configurar_sentry

celery_app = Celery(
    "timu",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.tasks.afiliaciones",
        "app.workers.tasks.aliadas",
        "app.workers.tasks.cartera",
        "app.workers.tasks.preventivos",
        "app.workers.tasks.comunicaciones",
        "app.workers.tasks.encuestas",
        "app.workers.tasks.familias",
        "app.workers.tasks.rutas",
        "app.workers.tasks.campanas",
        "app.workers.tasks.comercial",
        "app.workers.tasks.dashboard",
        "app.workers.tasks.ia",
        "app.workers.tasks.outbox",
    ],
)


@worker_process_init.connect
def _al_iniciar_worker(**_: object) -> None:
    """Seccion 11 Los errores de las tareas (cobros, avisos de mora) llegan al monitoreo igual
    que los de la API, y sus registros salen con el mismo formato."""
    configurar_logging(json=settings.LOG_JSON, debug=settings.DEBUG)
    configurar_sentry(settings.SENTRY_DSN, settings.ENVIRONMENT, celery=True)
    # Igual que la API: con un rol privilegiado la base no aplica sus politicas.
    with sync_engine.connect() as conexion:
        motivo = motivo_rol_privilegiado(conexion.execute(SQL_ROL_CONECTADO).one())
    if motivo:
        raise RuntimeError(f"El worker no se conecta con un rol privilegiado: {motivo}")


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
        # 6.1 Registro en linea pagado sin formulario: recordatorio a las 24 h, tarea a las 48.
        "recordar-registros": {
            "task": "afiliaciones.recordar_registros",
            "schedule": crontab(minute=20),
        },
        "cerrar-registros-sin-pago": {
            "task": "afiliaciones.cerrar_registros_sin_pago",
            "schedule": crontab(minute=40),
        },
        "anonimizar-registros-abandonados": {
            "task": "afiliaciones.anonimizar_registros_abandonados",
            "schedule": crontab(hour=3, minute=50),
        },
        # 6.19 mensajes cuya tarea se perdio (worker caido a mitad del envio)
        "comunicaciones-reencolar": {
            "task": "comunicaciones.reencolar_pendientes",
            "schedule": crontab(minute="*/15"),
        },
        # 6.2 emision de cuotas antes de su vencimiento
        "cartera-generar-cuotas": {
            "task": "cartera.generar_cuotas",
            "schedule": crontab(hour=5, minute=0),
        },
        # 6.2 cobro recurrente (antes de revisar mora, para no avisar a quien ya pago)
        "cartera-cobro-recurrente": {
            "task": "cartera.cobrar_recurrentes",
            "schedule": crontab(hour=5, minute=15),
        },
        # 6.2 cobros sin confirmacion de la pasarela
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
        # 6.8 / 6.13 agenda preventiva del dia. Envia WhatsApp a las familias: de dia, no de
        # madrugada como el resto de procesos diarios (DEU-82).
        "preventivos-generar-agenda": {
            "task": "preventivos.generar_agenda",
            "schedule": crontab(hour=9, minute=0),
        },
        # 6.18 campanas: lanzar las programadas y despachar al ritmo permitido
        "campanas-lanzar-programadas": {
            "task": "campanas.lanzar_programadas",
            "schedule": crontab(minute="*/5"),
        },
        "campanas-despachar": {
            "task": "campanas.despachar",
            "schedule": 60.0,
        },
        # Seccion 8 reportes gerenciales por correo
        "dashboard-reportes": {
            "task": "dashboard.enviar_reportes",
            "schedule": crontab(hour=7, minute=0),
        },
        # 6.22 remisiones sin usar pasado el plazo para reportar: vencen y liberan el cupo
        "aliadas-vencer-remisiones": {
            "task": "aliadas.vencer_remisiones",
            "schedule": crontab(hour=4, minute=10),
        },
        # 6.20 encuestas y seguimientos cuya hora llego
        "encuestas-enviar-pendientes": {
            "task": "encuestas.enviar_pendientes",
            "schedule": crontab(minute="*/15"),
        },
    },
)
