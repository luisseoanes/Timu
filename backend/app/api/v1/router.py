from fastapi import APIRouter

from app.api.v1 import webhooks
from app.modules.aliadas.router import router as aliadas_router
from app.modules.auth.router import router as auth_router
from app.modules.campanas.router import router as campanas_router
from app.modules.cartera.router import router as cartera_router
from app.modules.clinica.router import router as clinica_router
from app.modules.comunicaciones.router import router as comunicaciones_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.encuestas.router import router as encuestas_router
from app.modules.familias.router import router as familias_router
from app.modules.planes.router import router as planes_router
from app.modules.portal.router import router as portal_router
from app.modules.preventivos.router import router as preventivos_router
from app.modules.rutas.router import router as rutas_router
from app.modules.servicios.router import router as servicios_router

api_router = APIRouter()

# Un router por dominio (seccion A: arquitectura modular por dominios).
for r in (
    auth_router,
    familias_router,
    planes_router,
    cartera_router,
    servicios_router,
    preventivos_router,
    clinica_router,
    rutas_router,
    comunicaciones_router,
    campanas_router,
    encuestas_router,
    aliadas_router,
    portal_router,
    dashboard_router,
    webhooks.router,
):
    api_router.include_router(r)
