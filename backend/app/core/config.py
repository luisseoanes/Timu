from functools import lru_cache
from typing import Literal

from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "TIMU Plataforma"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "local"
    DEBUG: bool = True
    SECRET_KEY: str = "cambiar-en-produccion"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "timu"
    POSTGRES_PASSWORD: str = "timu"
    POSTGRES_DB: str = "timu"
    DATABASE_URL_OVERRIDE: str | None = None

    REDIS_URL: str = "redis://localhost:6379/0"

    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_VERIFY_TOKEN: str = "timu-verify"
    WHATSAPP_API_VERSION: str = "v21.0"

    PAYMENTS_PROVIDER: str = "wompi"
    WOMPI_PUBLIC_KEY: str = ""
    WOMPI_PRIVATE_KEY: str = ""
    WOMPI_EVENTS_SECRET: str = ""

    GOOGLE_MAPS_API_KEY: str = ""

    # --- Sesion del navegador (6.x portal): el token viaja en cookie httpOnly ---
    # SECURE debe quedar en True en cualquier ambiente servido por HTTPS.
    COOKIE_NAME: str = "timu_sesion"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    COOKIE_DOMAIN: str | None = None

    # --- Almacenamiento de adjuntos (F0-11), compatible S3 ---
    # En desarrollo apunta a MinIO; en produccion, al S3 que entregue el cliente.
    # Cambiar de uno a otro es cambiar estas variables, no el codigo.
    STORAGE_ENDPOINT_URL: str | None = "http://minio:9000"
    STORAGE_REGION: str = "us-east-1"
    STORAGE_BUCKET: str = "timu-adjuntos"
    STORAGE_ACCESS_KEY: str = "minioadmin"
    STORAGE_SECRET_KEY: str = "minioadmin"
    STORAGE_URL_TTL_SEGUNDOS: int = 300

    # --- Observabilidad (F0-08) ---
    SENTRY_DSN: str = ""
    LOG_JSON: bool = False

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL_SYNC(self) -> str:
        """URL sincrona para Alembic y para los workers de Celery.

        Celery no es async: sus tareas usan una sesion sincrona (ver
        app.core.database.sesion_worker), asi que necesitan el driver psycopg.
        """
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg://")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL(self) -> str:
        if self.DATABASE_URL_OVERRIDE:
            return self.DATABASE_URL_OVERRIDE
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_HOST,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
