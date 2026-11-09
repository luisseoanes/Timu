from functools import lru_cache
from typing import Literal

from pydantic import PostgresDsn, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Ambiente = Literal["local", "test", "staging", "production"]

# Rol de PostgreSQL de la aplicacion. Lo crea una migracion (0013) y le concede los
# permisos sobre los datos; `inicializar` le da LOGIN con APP_DB_PASSWORD.
ROL_APLICACION = "timu_app"

# Valores de desarrollo que nunca pueden llegar a un ambiente desplegado. La clave de
# desarrollo tiene 32 caracteres o mas: PyJWT avisa con una HMAC mas corta.
_SECRET_KEY_LOCAL = "cambiar-en-produccion-solo-para-desarrollo-local"
_POSTGRES_PASSWORD_LOCAL = "timu"
_APP_DB_PASSWORD_LOCAL = "timu_app"
_STORAGE_ACCESS_KEY_LOCAL = "timu-local"
_STORAGE_SECRET_KEY_LOCAL = "timu-local-secreto"
_WHATSAPP_VERIFY_TOKEN_LOCAL = "timu-verify"

# F0-05 Variables sin las que el servicio no arranca, por ambiente desplegado.
OBLIGATORIAS: dict[str, tuple[str, ...]] = {
    "staging": ("SECRET_KEY", "POSTGRES_PASSWORD", "APP_DB_PASSWORD", "REDIS_URL"),
    "production": (
        "SECRET_KEY",
        "POSTGRES_PASSWORD",
        "APP_DB_PASSWORD",
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
    # F3-POR-07 Ingreso del portal con codigo por WhatsApp
    TOKEN_CODIGO_MINUTOS: int = 10
    CODIGO_MAX_INTENTOS: int = 5
    # F3-POR-04 Anticipacion minima para que la familia cambie un servicio desde el portal
    PORTAL_ANTELACION_HORAS: int = 4
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    # Dueno del esquema: solo lo usan las migraciones y la gestion del rol de la aplicacion.
    POSTGRES_USER: str = "timu"
    POSTGRES_PASSWORD: str = _POSTGRES_PASSWORD_LOCAL
    POSTGRES_DB: str = "timu"
    # Rol con el que se conectan API, workers, scripts y pruebas: sin superusuario ni
    # BYPASSRLS, asi que la base le aplica sus restricciones y politicas. El nombre es fijo
    # (ROL_APLICACION) porque las migraciones le conceden los permisos.
    APP_DB_PASSWORD: str = _APP_DB_PASSWORD_LOCAL
    # La aplicacion puede llegar a la base por un pooler (PgBouncer en compose); vacias, va
    # directo a POSTGRES_HOST:POSTGRES_PORT. Las migraciones van siempre directo.
    APP_DB_HOST: str | None = None
    APP_DB_PORT: int | None = None
    DATABASE_URL_OVERRIDE: str | None = None
    DATABASE_URL_PROPIETARIO_OVERRIDE: str | None = None

    REDIS_URL: str = "redis://localhost:6379/0"

    # F0-06 Endurecimiento HTTP
    RATE_LIMIT_POR_MINUTO: int = 120
    RATE_LIMIT_LOGIN_POR_MINUTO: int = 10
    MAX_TAMANO_CARGA_MB: int = 10

    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_VERIFY_TOKEN: str = _WHATSAPP_VERIFY_TOKEN_LOCAL
    WHATSAPP_API_VERSION: str = "v21.0"
    # Secreto de la app de Meta: firma X-Hub-Signature-256 de los webhooks.
    WHATSAPP_APP_SECRET: str = ""

    # Solo hay una pasarela implementada (app/integrations/payments.py). Otro valor no arranca
    # en lugar de quedarse cobrando por Wompi creyendo que es otra.
    PAYMENTS_PROVIDER: Literal["wompi"] = "wompi"
    WOMPI_PUBLIC_KEY: str = ""
    WOMPI_PRIVATE_KEY: str = ""
    WOMPI_EVENTS_SECRET: str = ""
    WOMPI_INTEGRITY_SECRET: str = ""
    WOMPI_API_URL: str = "https://sandbox.wompi.co/v1"

    # Cartera (F1-CAR): supuestos iniciales, ajustables por ambiente
    CUOTA_EMISION_DIAS_ANTES: int = 5
    COBRO_RECURRENTE_REINTENTOS_DIAS: list[int] = [0, 3, 7]

    GOOGLE_MAPS_API_KEY: str = ""

    # Preventivos (F2-PRE-04): con cuantos dias se avisa a la familia que se acerca la fecha.
    PREVENTIVO_ANTICIPACION_DIAS: int = 7

    # Rutas (F2-RUT): jornada, capacidad por tecnico y ventana de llegada acordada.
    RUTA_JORNADA_INICIO: str = "07:00"
    RUTA_JORNADA_FIN: str = "19:00"
    RUTA_MAX_ATENCIONES: int = 8
    RUTA_VENTANA_LLEGADA_MIN: int = 60
    RUTA_AVISO_MARGEN_MIN: int = 30
    RUTA_VELOCIDAD_KMH: float = 22.0
    RUTA_SEGUNDOS_OPTIMIZACION: int = 2
    # Distance Matrix se factura por elemento: tope diario antes de pasar a estimar.
    MAPS_TOPE_DIARIO: int = 2000

    # Campanas (F3-CAM-02): mensajes encolados por minuto, al ritmo que permite Meta.
    CAMPANA_MENSAJES_POR_MINUTO: int = 60

    # Clinicas aliadas (F2-ALI-02): dias de vigencia de una remision.
    REMISION_VIGENCIA_DIAS: int = 30

    # --- Sesion del navegador: el token viaja en cookie httpOnly -------------------------------
    # SECURE debe quedar en True en cualquier ambiente servido por HTTPS.
    COOKIE_NAME: str = "timu_sesion"
    COOKIE_REFRESH_NAME: str = "timu_renovacion"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    COOKIE_DOMAIN: str | None = None

    # --- Almacenamiento de adjuntos (F0-11), compatible S3 -------------------------------------
    # En desarrollo apunta al SeaweedFS del compose; en produccion, al S3 que entregue el
    # cliente. Cambiar de uno a otro es cambiar estas variables, no el codigo.
    STORAGE_ENDPOINT_URL: str | None = "http://almacenamiento:8333"
    # Host con el que el navegador llega al almacenamiento, si no es el mismo que usa la API
    # (en docker compose: almacenamiento:8333 por dentro, localhost por fuera). Vacio con S3.
    STORAGE_PUBLIC_ENDPOINT_URL: str | None = None
    STORAGE_REGION: str = "us-east-1"
    STORAGE_BUCKET: str = "timu-adjuntos"
    STORAGE_ACCESS_KEY: str = _STORAGE_ACCESS_KEY_LOCAL
    STORAGE_SECRET_KEY: str = _STORAGE_SECRET_KEY_LOCAL
    STORAGE_URL_TTL_SEGUNDOS: int = 300

    # Correo saliente (recuperacion de clave, reportes). Vacio = solo se registra en el log.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "TIMU <no-responder@timu.co>"

    # Clave del administrador que crea `scripts.seed`. Vacia en local (usa la de desarrollo);
    # en un ambiente desplegado es obligatoria para correr el seed.
    ADMIN_PASSWORD_INICIAL: str = ""

    # --- Apoyo de IA (F4-IAA) ------------------------------------------------------------------
    # Sin clave la capa queda apagada: todo sigue funcionando con el flujo sin IA.
    ANTHROPIC_API_KEY: str = ""
    IA_MODELO: str = "claude-opus-5-5"
    IA_PRESUPUESTO_MENSUAL_USD: float = 50.0
    IA_TIMEOUT_SEGUNDOS: float = 30.0

    # --- Observabilidad (F0-08) ----------------------------------------------------------------
    SENTRY_DSN: str = ""
    LOG_JSON: bool = False

    @field_validator("APP_DB_HOST", "APP_DB_PORT", mode="before")
    @classmethod
    def _vacio_es_no_definido(cls, valor: object) -> object:
        """`APP_DB_HOST=` en el .env significa "usa POSTGRES_*", no una cadena vacia."""
        return None if valor == "" else valor

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
        if self.APP_DB_PASSWORD == _APP_DB_PASSWORD_LOCAL:
            errores.append("APP_DB_PASSWORD no puede ser el valor de desarrollo")
        if self.DEBUG:
            errores.append("DEBUG debe estar apagado")
        if not self.COOKIE_SECURE:
            errores.append("COOKIE_SECURE debe estar encendido (el ambiente se sirve por HTTPS)")
        if (
            self.STORAGE_ACCESS_KEY == _STORAGE_ACCESS_KEY_LOCAL
            or self.STORAGE_SECRET_KEY == _STORAGE_SECRET_KEY_LOCAL
        ):
            errores.append(
                "STORAGE_ACCESS_KEY y STORAGE_SECRET_KEY no pueden ser las de desarrollo"
            )
        if self.WHATSAPP_VERIFY_TOKEN == _WHATSAPP_VERIFY_TOKEN_LOCAL:
            errores.append("WHATSAPP_VERIFY_TOKEN no puede ser el valor de desarrollo")
        if self.STORAGE_PUBLIC_ENDPOINT_URL and "localhost" in self.STORAGE_PUBLIC_ENDPOINT_URL:
            errores.append("STORAGE_PUBLIC_ENDPOINT_URL no admite localhost")
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
        """Conexion de la aplicacion, con el rol sin privilegios."""
        if self.DATABASE_URL_OVERRIDE:
            return self.DATABASE_URL_OVERRIDE
        return self._url(
            ROL_APLICACION,
            self.APP_DB_PASSWORD,
            host=self.APP_DB_HOST or self.POSTGRES_HOST,
            puerto=self.APP_DB_PORT or self.POSTGRES_PORT,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL_PROPIETARIO(self) -> str:
        """Conexion del dueno del esquema: migraciones y gestion de roles, nada mas."""
        if self.DATABASE_URL_PROPIETARIO_OVERRIDE:
            return self.DATABASE_URL_PROPIETARIO_OVERRIDE
        return self._url(
            self.POSTGRES_USER,
            self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            puerto=self.POSTGRES_PORT,
        )

    def _url(self, usuario: str, clave: str, *, host: str, puerto: int) -> str:
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=usuario,
                password=clave,
                host=host,
                port=puerto,
                path=self.POSTGRES_DB,
            )
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
