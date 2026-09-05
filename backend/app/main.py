from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.observabilidad import (
    MiddlewareIdPeticion,
    configurar_logging,
    configurar_sentry,
)

configurar_logging(json=settings.LOG_JSON, debug=settings.DEBUG)
configurar_sentry(settings.SENTRY_DSN, settings.ENVIRONMENT)


@asynccontextmanager
async def lifespan(app: FastAPI):
    structlog.get_logger(__name__).info(
        "arranque", app=settings.APP_NAME, entorno=settings.ENVIRONMENT
    )
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Plataforma integral de gestion, operacion y automatizacion - TIMU",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(MiddlewareIdPeticion)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    # La sesion viaja en cookie: sin credenciales el navegador no la enviaria.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["infra"])
async def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.ENVIRONMENT}
