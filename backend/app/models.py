"""Registro unico de modelos para Alembic (autogenerate) y para create_all en tests.

Importar aqui todo modelo nuevo, o su tabla no aparecera en las migraciones.
"""

from app.core.auditoria import RegistroAuditoria  # noqa: F401
from app.core.database import Base  # noqa: F401
from app.core.outbox import EventoSaliente  # noqa: F401
from app.modules.afiliaciones.models import SolicitudAfiliacion  # noqa: F401
from app.modules.aliadas.models import ClinicaAliada, ConvenioAliada, RemisionAliada  # noqa: F401
from app.modules.archivos.models import Archivo  # noqa: F401
from app.modules.auth.models import Sesion, TokenUsoUnico, Usuario  # noqa: F401
from app.modules.campanas.models import Campana  # noqa: F401
from app.modules.cartera.models import (  # noqa: F401
    AplicacionPago,
    AvisoCartera,
    Contrato,
    Cuota,
    EventoPasarela,
    IntentoCobro,
    MedioPagoRecurrente,
    Pago,
)
from app.modules.catalogos.models import (  # noqa: F401
    Ciudad,
    Especie,
    EsquemaPreventivo,
    TipoServicioCatalogo,
)
from app.modules.clinica.models import (  # noqa: F401
    AdjuntoClinico,
    Formula,
    HistoriaClinica,
    PlantillaConsulta,
    RespuestaVirtual,
    SolicitudVirtual,
)
from app.modules.comunicaciones.models import (  # noqa: F401
    BajaComunicaciones,
    ConversacionWhatsApp,
    Mensaje,
    PlantillaWhatsApp,
)
from app.modules.encuestas.models import ConfiguracionEncuesta, Encuesta  # noqa: F401
from app.modules.familias.models import Familia, Mascota  # noqa: F401
from app.modules.planes.models import Beneficio, CambioPlan, Plan  # noqa: F401
from app.modules.preventivos.models import CarnetEmitido, EventoPreventivo  # noqa: F401
from app.modules.reglas.models import Regla  # noqa: F401
from app.modules.rutas.models import (  # noqa: F401
    ConsumoMapas,
    DistanciaCache,
    ParadaRuta,
    PlanificacionRuta,
    Ruta,
)
from app.modules.servicios.models import (  # noqa: F401
    BloqueoAgenda,
    Franja,
    Pendiente,
    Servicio,
    ServicioPaso,
)
from app.modules.tareas.models import Tarea  # noqa: F401
