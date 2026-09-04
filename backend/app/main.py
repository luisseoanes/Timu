import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

logging.basicConfig(level=logging.DEBUG if settings.DEBUG else logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger(__name__).info("Iniciando %s (%s)", settings.APP_NAME, settings.ENVIRONMENT)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Plataforma integral de gestion, operacion y automatizacion - TIMU",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["infra"])
async def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.ENVIRONMENT}
