from contextlib import asynccontextmanager

import structlog
from fastapi import Depends, FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core import salud
from app.core.config import settings
from app.core.deps import DbSession, publico
from app.core.errores import RESPUESTAS_ERROR, registrar_manejadores
from app.core.middleware import (
    LimiteCargaMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)
from app.core.observabilidad import (
    HEADER_REQUEST_ID,
    MiddlewareIdPeticion,
    configurar_logging,
    configurar_sentry,
)
from app.core.rate_limit import ContadorMemoria, ContadorRedis

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
    responses=RESPUESTAS_ERROR,
)

registrar_manejadores(app)

app.state.contador_peticiones = (
    ContadorRedis(settings.REDIS_URL) if settings.es_desplegado else ContadorMemoria()
)

# add_middleware antepone: el ultimo agregado es el mas externo. Orden efectivo:
# IdPeticion > SecurityHeaders > CORS > LimiteCarga > RateLimit > app.
# CORS va por fuera de los limites para que el navegador pueda leer un 413 o un 429.
app.add_middleware(
    RateLimitMiddleware,
    contador=app.state.contador_peticiones,
    por_minuto=settings.RATE_LIMIT_POR_MINUTO,
    login_por_minuto=settings.RATE_LIMIT_LOGIN_POR_MINUTO,
    rutas_sensibles=tuple(
        f"{settings.API_V1_PREFIX}/auth/{r}"
        for r in ("login", "refresh", "recuperar", "restablecer")
    ),
    exentas=("/health", "/health/live"),
)
app.add_middleware(LimiteCargaMiddleware, max_bytes=settings.MAX_TAMANO_CARGA_MB * 1024 * 1024)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    # La sesion viaja en cookie: sin credenciales el navegador no la enviaria.
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", HEADER_REQUEST_ID],
    expose_headers=[HEADER_REQUEST_ID],
)
app.add_middleware(SecurityHeadersMiddleware, hsts=settings.es_desplegado)
app.add_middleware(MiddlewareIdPeticion)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health/live", tags=["infra"], dependencies=[Depends(publico)])
async def health_live() -> dict[str, str]:
    """El proceso responde. No toca dependencias: sirve para reiniciar contenedores colgados."""
    return {"status": "ok"}


@app.get("/health", tags=["infra"], dependencies=[Depends(publico)])
async def health(db: DbSession, response: Response) -> dict[str, object]:
    """F0-08 Estado de base de datos, Redis y trabajadores. 503 si alguno falla."""
    checks = {"db": await salud.revisar_db(db), "redis": await salud.revisar_redis()}
    checks["workers"] = await salud.revisar_trabajadores() if checks["redis"] == "ok" else "falla"
    ok = all(v == "ok" for v in checks.values())
    if not ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "ok" if ok else "degradado",
        "environment": settings.ENVIRONMENT,
        "checks": checks,
    }
