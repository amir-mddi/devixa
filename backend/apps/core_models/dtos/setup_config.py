import os
from datetime import timedelta
from distutils.util import strtobool
from typing import Any, ClassVar, Dict, List, Optional
from urllib.parse import quote

from pydantic import Field
from requests_aws4auth import AWS4Auth

from backend.apps.core_models.dtos.base_dto import BaseDTO


_LOCAL_ENVS = {"local", "development", "dev", "testing", "test"}


def env_bool(name: str, default: bool) -> bool:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    return bool(strtobool(raw_value))


def env_list(name: str, default: str = "") -> list[str]:
    raw_value = os.environ.get(name, default).strip()
    if not raw_value or raw_value in {"[]", "()"}:
        return []
    return [item.strip() for item in raw_value.split(",") if item.strip()]


class RedisConfiguration(BaseDTO):
    password: str = os.environ.get("REDIS_PASSWORD", "")
    url: str = os.environ.get("REDIS_URL", "localhost")
    port: str = os.environ.get("REDIS_PORT", "6379")
    db_index: str = os.environ.get("REDIS_DB", "0")
    max_connection: int = int(os.environ.get("REDIS_MAX_CONNECTION", "20"))

    class Config:
        frozen = True


redis_config = RedisConfiguration()


def build_redis_url(db_index: str) -> str:
    auth = f":{quote(redis_config.password, safe='')}@" if redis_config.password else ""
    return f"redis://{auth}{redis_config.url}:{redis_config.port}/{db_index or '0'}"


class CeleryConfiguration(BaseDTO):
    broker_url: str = build_redis_url(redis_config.db_index)
    result_backend: str = build_redis_url(
        os.environ.get("CELERY_BACKEND_REDIS_DB", redis_config.db_index)
    )
    accept_content: list = ["application/json"]
    task_serializer: str = "json"
    result_serializer: str = "json"

    class Config:
        frozen = True


class JWTConfiguration(BaseDTO):
    access_token_lifetime_minutes: int = int(
        os.environ.get("ACCESS_TOKEN_LIFETIME_MINUTE", "15")
    )
    refresh_token_lifetime_hours: int = int(
        os.environ.get("REFRESH_TOKEN_LIFETIME_HOUR", "168")
    )
    rotate_refresh_tokens: bool = env_bool("ROTATE_REFRESH_TOKENS", True)
    blacklist_after_rotation: bool = env_bool("BLACKLIST_AFTER_ROTATION", True)
    algorithm: str = os.environ.get("JWT_ALGORITHM", "HS256")
    verifying_key: str | None = os.environ.get("JWT_VERIFYING_KEY") or None

    access_token_lifetime: ClassVar[timedelta] = timedelta(
        minutes=access_token_lifetime_minutes
    )
    refresh_token_lifetime: ClassVar[timedelta] = timedelta(
        hours=refresh_token_lifetime_hours
    )

    class Config:
        frozen = True


class SentryConfiguration(BaseDTO):
    use_sentry: bool = env_bool("USE_SENTRY", False)
    dsn: str = os.environ.get("SENTRY_DSN", "")
    traces_sample_rate: float = float(
        os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")
    )
    send_default_pii: bool = env_bool("SENTRY_SEND_DEFAULT_PII", False)

    class Config:
        frozen = True


class DatabaseConfiguration(BaseDTO):
    use_sql_database: bool = env_bool("USE_SQL_DATABASE", True)
    use_database_replica: bool = env_bool("USE_DATABASE_REPLICA", False)
    database_engine: str = os.environ.get("DATABASE_ENGINE", "sqlite").strip().lower()

    sqlite_database_config: dict = {
        "ENGINE": os.environ.get("SQLITE_ENGINE", "django.db.backends.sqlite3"),
        "NAME": str(os.environ.get("SQLITE_NAME", "db/db.sqlite3")),
        "CONN_MAX_AGE": int(os.environ.get("SQLITE_CONN_MAX_AGE", "0")),
        "OPTIONS": {"timeout": int(os.environ.get("SQLITE_TIMEOUT", "20"))},
    }

    primary_database_config: dict = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_NAME", ""),
        "USER": os.environ.get("POSTGRES_USER", ""),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("POSTGRES_HOST", ""),
        "PORT": os.environ.get("POSTGRES_PORT", ""),
        "CONN_MAX_AGE": int(os.environ.get("POSTGRES_CONN_MAX_AGE", "60")),
        "OPTIONS": {"sslmode": os.environ.get("POSTGRES_SSLMODE", "prefer")},
    }

    replica_database_config: dict = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get(
            "POSTGRES_REPLICA_NAME", os.environ.get("POSTGRES_NAME", "")
        ),
        "USER": os.environ.get(
            "POSTGRES_REPLICA_USER", os.environ.get("POSTGRES_USER", "")
        ),
        "PASSWORD": os.environ.get(
            "POSTGRES_REPLICA_PASSWORD", os.environ.get("POSTGRES_PASSWORD", "")
        ),
        "HOST": os.environ.get("POSTGRES_REPLICA_HOST", ""),
        "PORT": os.environ.get(
            "POSTGRES_REPLICA_PORT", os.environ.get("POSTGRES_PORT", "")
        ),
        "CONN_MAX_AGE": int(
            os.environ.get("POSTGRES_REPLICA_CONN_MAX_AGE", "60")
        ),
        "OPTIONS": {"sslmode": os.environ.get("POSTGRES_REPLICA_SSLMODE", "prefer")},
    }

    dummy_database_config: dict = {
        "ENGINE": "django.db.backends.dummy",
        "NAME": "dummy",
    }

    @property
    def databases(self):
        if not self.use_sql_database:
            return {"default": self.dummy_database_config}
        if self.database_engine == "sqlite":
            return {"default": self.sqlite_database_config}
        if self.database_engine not in {"postgres", "postgresql"}:
            raise ValueError(
                "Unsupported DATABASE_ENGINE. Use 'sqlite', 'postgres', or 'postgresql'."
            )

        databases = {"default": self.primary_database_config}
        if self.use_database_replica:
            databases["replica"] = self.replica_database_config
        return databases

    @property
    def database(self):
        return self.databases["default"]

    class Config:
        frozen = True


class GeneralConfiguration(BaseDTO):
    env: str = os.environ.get("ENV", "local").strip().lower()
    is_local_environment: ClassVar[bool] = env in _LOCAL_ENVS
    debug: bool = env_bool("IS_DEBUG", is_local_environment)
    serve_static_files: bool = env_bool(
        "PROJECT_SERVE_STATIC_FILES", is_local_environment
    )
    static_asset_root: str = os.environ.get("PROJECT_STATIC_ASSET_ROOT", "app/assets")
    allowed_hosts: list = env_list(
        "ALLOWED_HOSTS",
        "localhost,127.0.0.1,testserver" if is_local_environment else "",
    )
    secret_key: str = os.environ.get(
        "APP_SECRET_KEY",
        "unsafe-local-development-key-change-me" if is_local_environment else "",
    )
    cors_origin_allow_all: bool = env_bool(
        "CORS_ORIGIN_ALLOW_ALL", is_local_environment
    )
    cors_allowed_origins: list = env_list("CROSS_ORIGIN_DOMAIN")
    core_allow_credential: bool = env_bool("CORS_ALLOW_CREDENTIALS", False)
    core_allow_headers: list = env_list("CORS_ALLOW_HEADERS")
    core_allow_methods: list = env_list("CORS_ALLOW_METHODS")
    append_slash: bool = env_bool("APPEND_SLASH", True)
    encryption_key: str = os.environ.get("ENCRYPTION_KEY", "")
    list_of_proxies: str = os.environ.get("LIST_OF_PROXIES", "")
    list_of_white_shaba: str = os.environ.get("WHITE_SHABA_LIST", "")
    admin_username: str = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
    admin_password: str = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
    admin_phone_number: str = os.environ.get("DJANGO_SUPERUSER_PHONE_NUMBER", "")
    admin_email: str = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")
    broker_id: str = os.environ.get("BROKER_ID", "")
    metric_service_endpoint: str = os.environ.get("METRIC_SERVICE_ENDPOINT", "")
    project_name: str = os.environ.get("PROJECT_NAME", "devixa")
    project_logger_name: str = os.environ.get(
        "PROJECT_LOGGER_NAME",
        os.environ.get("PROJECT_SLUG", project_name.lower().replace(" ", "-")),
    )

    class Config:
        frozen = True


general_config = GeneralConfiguration()


class LoggingConfiguration(BaseDTO):
    version: int = 1
    disable_existing_loggers: bool = False
    log_level: str = "INFO" if general_config.debug else "WARNING"

    formatters: Dict[str, Any] = Field(
        default_factory=lambda: {
            "base_format": {
                "format": "{levelname} {asctime} {name} {message}",
                "style": "{",
            }
        }
    )
    handlers: Dict[str, Any] = Field(
        default_factory=lambda: {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO" if general_config.debug else "WARNING",
                "formatter": "base_format",
            },
            "null": {"class": "logging.NullHandler"},
        }
    )
    loggers: Dict[str, Any] = Field(
        default_factory=lambda: {
            general_config.project_logger_name: {
                "handlers": ["console"],
                "level": "INFO" if general_config.debug else "WARNING",
                "propagate": False,
            },
            "drf_spectacular": {
                "handlers": ["null"],
                "level": "CRITICAL",
                "propagate": False,
            },
        }
    )

    class Config:
        frozen = True


class SwaggerConfiguration(BaseDTO):
    use_swagger: bool = env_bool("USE_SWAGGER", general_config.debug)
    swagger_title: str = os.environ.get("SWAGGER_DESCRIPTION", "Devixa API")
    swagger_version: str = os.environ.get("SWAGGER_VERSION", "1.0.0")
    swagger_description: str = os.environ.get("SWAGGER_DOCUMENTATION", "")

    @property
    def spectacular_settings(self):
        if not self.use_swagger:
            return {"SERVE_INCLUDE_SCHEMA": False}
        return {
            "TITLE": self.swagger_title,
            "DESCRIPTION": self.swagger_description,
            "VERSION": self.swagger_version,
            "SERVE_INCLUDE_SCHEMA": False,
            "SWAGGER_UI_DIST": "SIDECAR",
            "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
            "REDOC_DIST": "SIDECAR",
            "SWAGGER_UI_SETTINGS": {
                "deepLinking": True,
                "persistAuthorization": False,
                "displayOperationId": True,
            },
        }

    class Config:
        frozen = True


class PaginationConfiguration(BaseDTO):
    page_size: int = max(1, min(int(os.environ.get("PAGE_SIZE", "50")), 200))

    class Config:
        frozen = True


class SessionSettings(BaseDTO):
    session_engine: str = os.environ.get(
        "SESSION_ENGINE", "django.contrib.sessions.backends.cache"
    )
    session_cache_alias: str = os.environ.get("SESSION_CACHE_ALIAS", "default")
    session_cookie_age: int = int(os.environ.get("SESSION_COOKIE_AGE", "3600"))
    session_expire_at_browser_close: bool = env_bool(
        "SESSION_EXPIRE_AT_BROWSER_CLOSE", True
    )
    session_save_every_request: bool = env_bool("SESSION_SAVE_EVERY_REQUEST", False)
    session_cookie_name: str = os.environ.get("SESSION_COOKIE_NAME", "sessionid")
    session_cookie_domain: Optional[str] = os.environ.get("SESSION_COOKIE_DOMAIN") or None
    session_cookie_path: str = os.environ.get("SESSION_COOKIE_PATH", "/")
    session_cookie_secure: bool = env_bool(
        "SESSION_COOKIE_SECURE", not general_config.is_local_environment
    )
    session_cookie_httponly: bool = env_bool("SESSION_COOKIE_HTTPONLY", True)
    session_cookie_samesite: str = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")
    csrf_trusted_origins: List[str] = env_list(
        "CSRF_TRUSTED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000"
        if general_config.is_local_environment
        else "",
    )
    csrf_cookie_samesite: str = os.environ.get("CSRF_COOKIE_SAMESITE", "Lax")
    csrf_cookie_secure: bool = env_bool(
        "CSRF_COOKIE_SECURE", not general_config.is_local_environment
    )

    class Config:
        frozen = True


class BackupSettings(BaseDTO):
    base_url: str = os.getenv("ARVAN_BASE_URL", "")
    secret_key: str = os.getenv("ARVAN_SECRET_KEY", "")
    access_key: str = os.getenv("ARVAN_ACCESS_KEY", "")
    region: str = os.getenv("ARVAN_REGION", "us-east-1")
    service_name: str = os.getenv("ARVAN_SERVICE_NAME", "s3")
    bucket: str = os.getenv("ARVAN_BUCKET", "")
    auth: ClassVar[AWS4Auth | None] = (
        AWS4Auth(access_key, secret_key, region, service_name)
        if access_key and secret_key
        else None
    )

    class Config:
        frozen = True


celery_config = CeleryConfiguration()
jwt_config = JWTConfiguration()
sentry_config = SentryConfiguration()
database_config = DatabaseConfiguration()
logging_config = LoggingConfiguration()
swagger_config = SwaggerConfiguration()
pagination_config = PaginationConfiguration()
session_config = SessionSettings()
backup_config = BackupSettings()

PARDAKHTYAR_MERCHANT_ID = os.environ.get("PARDAKHTYAR_MERCHANT_ID", "")
PARDAKHTYAR_REQUEST_URL = os.environ.get("PARDAKHTYAR_REQUEST_URL", "")
PARDAKHTYAR_VERIFY_URL = os.environ.get("PARDAKHTYAR_VERIFY_URL", "")
PARDAKHTYAR_START_PAY_BASE_URL = os.environ.get("PARDAKHTYAR_START_PAY_BASE_URL", "")
PARDAKHTYAR_CALLBACK_URL = os.environ.get("PARDAKHTYAR_CALLBACK_URL", "")
PARDAKHTYAR_SUCCESS_CODES = os.environ.get(
    "PARDAKHTYAR_SUCCESS_CODES", "100,0,ok,success,succeeded,paid"
)
PARDAKHTYAR_HTTP_TIMEOUT_SECONDS = os.environ.get(
    "PARDAKHTYAR_HTTP_TIMEOUT_SECONDS", "12"
)
PARDAKHTYAR_FRONTEND_SUCCESS_URL = os.environ.get(
    "PARDAKHTYAR_FRONTEND_SUCCESS_URL", ""
)
PARDAKHTYAR_FRONTEND_FAILED_URL = os.environ.get(
    "PARDAKHTYAR_FRONTEND_FAILED_URL", ""
)
PARDAKHTYAR_ALLOWED_HOSTS = env_list("PARDAKHTYAR_ALLOWED_HOSTS", "")
PARDAKHTYAR_PAYMENT_ALLOWED_HOSTS = env_list("PARDAKHTYAR_PAYMENT_ALLOWED_HOSTS", "")
PARDAKHTYAR_CALLBACK_ALLOWED_HOSTS = env_list("PARDAKHTYAR_CALLBACK_ALLOWED_HOSTS", "")
PARDAKHTYAR_FRONTEND_ALLOWED_HOSTS = env_list("PARDAKHTYAR_FRONTEND_ALLOWED_HOSTS", "")
PARDAKHTYAR_MAX_RESPONSE_BYTES = max(1024, min(
    int(os.environ.get("PARDAKHTYAR_MAX_RESPONSE_BYTES", str(1024 * 1024))),
    5 * 1024 * 1024,
))

KAVENEGAR_API_KEY = os.environ.get("KAVENEGAR_API_KEY", "")
