from functools import lru_cache

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
