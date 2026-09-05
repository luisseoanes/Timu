"""Registro unico de modelos para Alembic (autogenerate) y para create_all en tests.

Importar aqui todo modelo nuevo, o su tabla no aparecera en las migraciones.
"""

from app.core.database import Base  # noqa: F401
from app.core.outbox import EventoSaliente  # noqa: F401
from app.modules.aliadas.models import ClinicaAliada, RemisionAliada  # noqa: F401
from app.modules.auth.models import Usuario  # noqa: F401
from app.modules.campanas.models import Campana  # noqa: F401
from app.modules.cartera.models import Contrato, Cuota, Pago  # noqa: F401
from app.modules.clinica.models import AdjuntoClinico, HistoriaClinica  # noqa: F401
from app.modules.comunicaciones.models import Mensaje  # noqa: F401
from app.modules.encuestas.models import Encuesta  # noqa: F401
from app.modules.familias.models import Familia, Mascota  # noqa: F401
from app.modules.planes.models import Plan, ReglaPlan  # noqa: F401
from app.modules.preventivos.models import EventoPreventivo  # noqa: F401
from app.modules.rutas.models import ParadaRuta, Ruta  # noqa: F401
from app.modules.servicios.models import Pendiente, Servicio  # noqa: F401
