from functools import lru_cache
from typing import Literal

from pydantic import PostgresDsn, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Ambiente = Literal["local", "test", "staging", "production"]

# Valores de desarrollo que nunca pueden llegar a un ambiente desplegado.
_SECRET_KEY_LOCAL = "cambiar-en-produccion"
_POSTGRES_PASSWORD_LOCAL = "timu"

# F0-05 Variables sin las que el servicio no arranca, por ambiente desplegado.
OBLIGATORIAS: dict[str, tuple[str, ...]] = {
    "staging": ("SECRET_KEY", "POSTGRES_PASSWORD", "REDIS_URL"),
    "production": (
        "SECRET_KEY",
        "POSTGRES_PASSWORD",
        "REDIS_URL",
        "WHATSAPP_PHONE_NUMBER_ID",
        "WHATSAPP_ACCESS_TOKEN",
        "WHATSAPP_VERIFY_TOKEN",
        "WHATSAPP_APP_SECRET",
        "WOMPI_PUBLIC_KEY",
        "WOMPI_PRIVATE_KEY",
        "WOMPI_EVENTS_SECRET",
        "WOMPI_INTEGRITY_SECRET",
        "GOOGLE_MAPS_API_KEY",
    ),
}


class ConfiguracionInvalida(RuntimeError):
    """El servicio se niega a arrancar con una configuracion incompleta o insegura."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "TIMU Plataforma"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: Ambiente = "local"
    DEBUG: bool = True
    SECRET_KEY: str = _SECRET_KEY_LOCAL
    ALGORITHM: str = "HS256"
    # F1-AUT-01 Access token corto; la sesion se sostiene con el refresh token.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    # F1-AUT-03 / F1-AUT-04 Enlaces de un solo uso
    TOKEN_RECUPERACION_MINUTOS: int = 30
    TOKEN_ACTIVACION_HORAS: int = 72
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "timu"
    POSTGRES_PASSWORD: str = _POSTGRES_PASSWORD_LOCAL
    POSTGRES_DB: str = "timu"
    DATABASE_URL_OVERRIDE: str | None = None

    REDIS_URL: str = "redis://localhost:6379/0"

    # F0-06 Endurecimiento HTTP
    RATE_LIMIT_POR_MINUTO: int = 120
    RATE_LIMIT_LOGIN_POR_MINUTO: int = 10
    MAX_TAMANO_CARGA_MB: int = 10

    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_VERIFY_TOKEN: str = "timu-verify"
    WHATSAPP_API_VERSION: str = "v21.0"
    # Secreto de la app de Meta: firma X-Hub-Signature-256 de los webhooks.
    WHATSAPP_APP_SECRET: str = ""

    PAYMENTS_PROVIDER: str = "wompi"
    WOMPI_PUBLIC_KEY: str = ""
    WOMPI_PRIVATE_KEY: str = ""
    WOMPI_EVENTS_SECRET: str = ""
    WOMPI_INTEGRITY_SECRET: str = ""
    WOMPI_API_URL: str = "https://sandbox.wompi.co/v1"

    # Cartera (F1-CAR): supuestos iniciales, ajustables por ambiente
    CUOTA_EMISION_DIAS_ANTES: int = 5
    COBRO_RECURRENTE_REINTENTOS_DIAS: list[int] = [0, 3, 7]

    GOOGLE_MAPS_API_KEY: str = ""

    # --- Sesion del navegador: el token viaja en cookie httpOnly ---
    # SECURE debe quedar en True en cualquier ambiente servido por HTTPS.
    COOKIE_NAME: str = "timu_sesion"
    COOKIE_REFRESH_NAME: str = "timu_renovacion"
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

    # Correo saliente (recuperacion de clave, reportes). Vacio = solo se registra en el log.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "TIMU <no-responder@timu.co>"

    # --- Observabilidad (F0-08) ---
    SENTRY_DSN: str = ""
    LOG_JSON: bool = False

    @property
    def es_desplegado(self) -> bool:
        return self.ENVIRONMENT in ("staging", "production")

    @model_validator(mode="after")
    def _validar_ambiente(self) -> "Settings":
        if not self.es_desplegado:
            return self
        faltantes = [v for v in OBLIGATORIAS[self.ENVIRONMENT] if not getattr(self, v)]
        if faltantes:
            raise ConfiguracionInvalida(
                f"Faltan variables obligatorias para {self.ENVIRONMENT}: {', '.join(faltantes)}"
            )
        errores = []
        if self.SECRET_KEY == _SECRET_KEY_LOCAL or len(self.SECRET_KEY) < 32:
            errores.append("SECRET_KEY debe ser propia del ambiente y tener 32 caracteres o mas")
        if self.POSTGRES_PASSWORD == _POSTGRES_PASSWORD_LOCAL:
            errores.append("POSTGRES_PASSWORD no puede ser el valor de desarrollo")
        if self.DEBUG:
            errores.append("DEBUG debe estar apagado")
        if not self.COOKIE_SECURE:
            errores.append("COOKIE_SECURE debe estar encendido (el ambiente se sirve por HTTPS)")
        if self.STORAGE_ACCESS_KEY == "minioadmin" or self.STORAGE_SECRET_KEY == "minioadmin":
            errores.append("STORAGE_ACCESS_KEY y STORAGE_SECRET_KEY no pueden ser las de MinIO")
        if any("localhost" in o or o == "*" for o in self.BACKEND_CORS_ORIGINS):
            errores.append("BACKEND_CORS_ORIGINS no admite localhost ni comodin")
        if errores:
            raise ConfiguracionInvalida(
                f"Configuracion insegura para {self.ENVIRONMENT}: " + "; ".join(errores)
            )
        return self

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
