"""6.8 / 6.13 Calendario preventivo por especie y edad."""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.catalogos.models import EsquemaPreventivo
from app.modules.familias.models import Mascota
from app.modules.preventivos.models import EventoPreventivo

# Hasta esta edad se asume que la mascota no ha completado la serie inicial.
EDAD_SERIE_INICIAL_SEMANAS = 52


def fechas_esquema(esquema: EsquemaPreventivo, nacimiento: date | None, desde: date) -> list[date]:
    """Fechas de las dosis a programar para una mascota que entra al plan en `desde`.

    - Cachorro que aun no llega a la edad minima: la serie arranca en esa edad.
    - Cachorro que ya la paso: la serie completa arranca en `desde` (no se conoce su historia;
      el profesional ajusta si trae carnet).
    - Adulto o edad desconocida: una dosis de refuerzo en `desde`.
    """
    if nacimiento is not None:
        edad_semanas = (desde - nacimiento).days // 7
        if edad_semanas < EDAD_SERIE_INICIAL_SEMANAS:
            inicio = max(desde, nacimiento + timedelta(weeks=esquema.edad_minima_semanas))
            return [
                inicio + timedelta(days=esquema.intervalo_inicial_dias * i)
                for i in range(esquema.dosis_iniciales)
            ]
    return [desde] if esquema.intervalo_refuerzo_dias else []


def calendario_inicial(db: Session, mascota: Mascota, desde: date) -> list[EventoPreventivo]:
    """F1-AFI-03 Programa los preventivos de la mascota segun los esquemas de su especie.
    Repetible: no duplica esquemas que la mascota ya tenga programados."""
    esquemas = db.scalars(
        select(EsquemaPreventivo).where(
            EsquemaPreventivo.especie_codigo == mascota.especie,
            EsquemaPreventivo.activo.is_(True),
        )
    )
    ya_programados = set(
        db.scalars(
            select(EventoPreventivo.esquema_codigo).where(EventoPreventivo.mascota_id == mascota.id)
        )
    )
    eventos = []
    for esquema in esquemas:
        if esquema.codigo in ya_programados:
            continue
        fechas = fechas_esquema(esquema, mascota.fecha_nacimiento, desde)
        for numero, fecha in enumerate(fechas, start=1):
            evento = EventoPreventivo(
                mascota_id=mascota.id,
                esquema_codigo=esquema.codigo,
                tipo=esquema.tipo,
                dosis_numero=numero,
                fecha_programada=fecha,
                requiere_autorizacion=esquema.requiere_autorizacion,
            )
            db.add(evento)
            eventos.append(evento)
    db.flush()
    return eventos
