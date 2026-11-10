from fastapi import APIRouter

from app.api.v1 import webhooks
from app.modules.afiliaciones.router import familias_router as ciclo_familias_router
from app.modules.afiliaciones.router import formularios_router
from app.modules.afiliaciones.router import mascotas_router as ciclo_mascotas_router
from app.modules.afiliaciones.router import router as afiliaciones_router
from app.modules.aliadas.router import router as aliadas_router
from app.modules.auth.router import router as auth_router
from app.modules.campanas.router import router as campanas_router
from app.modules.campanas.router import segmentos_router
from app.modules.cartera.router import planes_router as cambio_plan_router
from app.modules.cartera.router import router as cartera_router
from app.modules.catalogos.router import router as catalogos_router
from app.modules.clinica.router import router as clinica_router
from app.modules.comercial.router import router as comercial_router
from app.modules.comunicaciones.router import router as comunicaciones_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.documentos.router import router as documentos_router
from app.modules.encuestas.router import router as encuestas_router
from app.modules.familias.router import mascotas_router
from app.modules.familias.router import router as familias_router
from app.modules.ia.router import router as ia_router
from app.modules.planes.router import router as planes_router
from app.modules.portal.router import router as portal_router
from app.modules.preventivos.router import router as preventivos_router
from app.modules.preventivos.router import verificacion_router
from app.modules.reglas.router import router as reglas_router
from app.modules.rutas.router import router as rutas_router
from app.modules.servicios.router import agenda_router, pendientes_router
from app.modules.servicios.router import router as servicios_router
from app.modules.tareas.router import router as tareas_router

api_router = APIRouter()

# Un router por dominio (seccion A: arquitectura modular por dominios).
for r in (
    auth_router,
    catalogos_router,
    familias_router,
    mascotas_router,
    ciclo_familias_router,
    ciclo_mascotas_router,
    formularios_router,
    reglas_router,
    planes_router,
    cambio_plan_router,
    cartera_router,
    afiliaciones_router,
    tareas_router,
    servicios_router,
    agenda_router,
    pendientes_router,
    preventivos_router,
    verificacion_router,
    clinica_router,
    rutas_router,
    comunicaciones_router,
    campanas_router,
    comercial_router,
    segmentos_router,
    documentos_router,
    encuestas_router,
    aliadas_router,
    portal_router,
    dashboard_router,
    ia_router,
    webhooks.router,
):
    api_router.include_router(r)
