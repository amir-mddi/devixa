import os
from datetime import timedelta
from distutils.util import strtobool
from typing import ClassVar, Optional, List
from typing import Dict, Any
from urllib.parse import quote

from pydantic import Field
from requests_aws4auth import AWS4Auth

from dealio.apps.core_models.dtos.base_dto import BaseDTO


class RedisConfiguration(BaseDTO):
    password: str = os.environ.get("REDIS_PASSWORD", "")
    url: str = os.environ.get("REDIS_URL", "")
    port: str = os.environ.get("REDIS_PORT", "")
    db_index: str = os.environ.get("REDIS_DB", "0")
    max_connection: int = int(os.environ.get("REDIS_MAX_CONNECTION", "20"))

    class Config:
        frozen = True


redis_config = RedisConfiguration()


def build_redis_url(db_index: str) -> str:
    auth = f":{quote(redis_config.password, safe='')}@" if redis_config.password else ""
    return f"redis://{auth}{redis_config.url}:{redis_config.port}/{db_index}"


class CeleryConfiguration(BaseDTO):
    broker_url: str = build_redis_url(redis_config.db_index)
    result_backend: str = build_redis_url(os.environ.get("CELERY_BACKEND_REDIS_DB", ""))
    accept_content: list = ['application/json']
    task_serializer: str = 'json'
    result_serializer: str = 'json'

    class Config:
        frozen = True


class JWTConfiguration(BaseDTO):
    access_token_lifetime_minutes: int = int(os.environ.get("ACCESS_TOKEN_LIFETIME_MINUTE", "720"))
    refresh_token_lifetime_hours: int = int(os.environ.get("REFRESH_TOKEN_LIFETIME_HOUR", "154"))
    rotate_refresh_tokens: bool = bool(strtobool(os.environ.get("ROTATE_REFRESH_TOKENS", "false")))
    blacklist_after_rotation: bool = bool(strtobool(os.environ.get("BLACKLIST_AFTER_ROTATION", "true")))
    algorithm: str = "HS256"
    verifying_key: str | None = None

    access_token_lifetime: ClassVar[timedelta] = timedelta(minutes=access_token_lifetime_minutes)
    refresh_token_lifetime: ClassVar[timedelta] = timedelta(hours=refresh_token_lifetime_hours)

    class Config:
        frozen = True


class SentryConfiguration(BaseDTO):
    use_sentry: bool = bool(strtobool(os.environ.get("USE_SENTRY", "false")))
    dsn: str = os.environ.get("SENTRY_DSN", "")
    traces_sample_rate: float = 1.0
    send_default_pii: bool = True

    class Config:
        frozen = True


class DatabaseConfiguration(BaseDTO):
    use_sql_database: bool = bool(strtobool(os.environ.get("USE_SQL_DATABASE", "true")))
    use_database_replica: bool = bool(strtobool(os.environ.get("USE_DATABASE_REPLICA", "false")))
    database_engine: str = os.environ.get("DATABASE_ENGINE", "sqlite").strip().lower()

    sqlite_database_config: dict = {
        "ENGINE": os.environ.get("SQLITE_ENGINE", "django.db.backends.sqlite3"),
        "NAME": str(os.environ.get("SQLITE_NAME", "db/db.sqlite3")),
        "CONN_MAX_AGE": int(os.environ.get("SQLITE_CONN_MAX_AGE", "0")),
        "OPTIONS": {
            "timeout": int(os.environ.get("SQLITE_TIMEOUT", "20")),
        },
    }

    primary_database_config: dict = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_NAME", ""),
        "USER": os.environ.get("POSTGRES_USER", ""),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("POSTGRES_HOST", ""),
        "PORT": os.environ.get("POSTGRES_PORT", ""),
        "CONN_MAX_AGE": int(os.environ.get("POSTGRES_CONN_MAX_AGE", "60")),
    }

    replica_database_config: dict = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_REPLICA_NAME", os.environ.get("POSTGRES_NAME", "")),
        "USER": os.environ.get("POSTGRES_REPLICA_USER", os.environ.get("POSTGRES_USER", "")),
        "PASSWORD": os.environ.get("POSTGRES_REPLICA_PASSWORD", os.environ.get("POSTGRES_PASSWORD", "")),
        "HOST": os.environ.get("POSTGRES_REPLICA_HOST", ""),
        "PORT": os.environ.get("POSTGRES_REPLICA_PORT", os.environ.get("POSTGRES_PORT", "")),
        "CONN_MAX_AGE": int(os.environ.get("POSTGRES_REPLICA_CONN_MAX_AGE", "60")),
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
    env: str = os.environ.get("ENV", "local")
    debug: bool = bool(
        strtobool(
            os.environ.get(
                "IS_DEBUG",
                "true" if env in {"local", "development", "dev"} else "false",
            )
        )
    )
    serve_static_files: bool = bool(
        strtobool(
            os.environ.get(
                "PROJECT_SERVE_STATIC_FILES",
                "true" if env in {"local", "development", "dev"} else "false",
            )
        )
    )
    static_asset_root: str = os.environ.get("PROJECT_STATIC_ASSET_ROOT", "app/assets")
    allowed_hosts: list = os.environ.get("ALLOWED_HOSTS", "*").strip().split(",")
    secret_key: str = os.environ.get("APP_SECRET_KEY", "")
    cors_origin_allow_all: bool = bool(strtobool(os.environ.get("CORS_ORIGIN_ALLOW_ALL", "true")))
    cors_allowed_origins: list = os.environ.get("CROSS_ORIGIN_DOMAIN", "[]").split(",")
    core_allow_credential: bool = bool(strtobool(os.environ.get("CORS_ALLOW_CREDENTIALS", "true")))
    core_allow_headers: list = os.environ.get("CORS_ALLOW_HEADERS", "[]").split(",")
    core_allow_methods: list = os.environ.get("CORS_ALLOW_METHODS", "[]").split(",")
    append_slash: bool = True
    encryption_key: str = os.environ.get("ENCRYPTION_KEY", "")
    list_of_proxies: str = os.environ.get("LIST_OF_PROXIES", "")
    list_of_white_shaba: str = os.environ.get("WHITE_SHABA_LIST", "")
    admin_username: str = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
    admin_password: str = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "admin")
    admin_phone_number: str = os.environ.get("DJANGO_SUPERUSER_PHONE_NUMBER", "")
    admin_email: str = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@gmail.com")
    broker_id: str = os.environ.get("BROKER_ID", "")
    metric_service_endpoint: str = os.environ.get("METRIC_SERVICE_ENDPOINT", "http://172.16.16.49:8200/api/metrics/")
    project_name: str = os.environ.get("PROJECT_NAME", "Project")
    project_logger_name: str = os.environ.get("PROJECT_LOGGER_NAME", os.environ.get("PROJECT_SLUG", project_name.lower().replace(" ", "-")))

    class Config:
        frozen = True


general_config = GeneralConfiguration()


class LoggingConfiguration(BaseDTO):
    version: int = 1
    disable_existing_loggers: bool = True
    log_level: str = "INFO" if general_config.debug else "WARNING"

    formatters: Dict[str, Any] = Field(
        default_factory=lambda: {
            "base_format": {"format": "{levelname} {asctime} {message}", "style": "{"}
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
            "drf_spectacular.openapi": {
                "handlers": ["null"],
                "level": "CRITICAL",
                "propagate": False,
            },
            "drf_spectacular.plumbing": {
                "handlers": ["null"],
                "level": "CRITICAL",
                "propagate": False,
            },
        }
    )

    class Config:
        frozen = True


class SwaggerConfiguration(BaseDTO):
    use_swagger: bool = bool(strtobool(os.environ.get("USE_SWAGGER", "true")))
    swagger_title: str = os.environ.get("SWAGGER_DESCRIPTION", "Development")
    swagger_version: str = os.environ.get("SWAGGER_VERSION", "1.0.0")
    swagger_description: str = os.environ.get("SWAGGER_DOCUMENTATION", "")

    @property
    def spectacular_settings(self):
        if self.use_swagger:
            return {
                "TITLE": self.swagger_title,
                "DESCRIPTION": self.swagger_description,
                "VERSION": self.swagger_version,

                "COMPONENTS": {
                    "securitySchemes": {
                        "basicAuth": {
                            "type": "http",
                            "scheme": "basic",
                        }
                    }
                },
                "SECURITY": [{"basicAuth": []}],

                "SWAGGER_UI_DIST": "SIDECAR",
                "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
                "REDOC_DIST": "SIDECAR",

                "SWAGGER_UI_SETTINGS": {
                    "deepLinking": True,
                    "persistAuthorization": True,
                    "displayOperationId": True,
                },
            }
        return {
            "SERVE_INCLUDE_SCHEMA": False,
        }

    class Config:
        frozen = True


class PaginationConfiguration(BaseDTO):
    page_size: int = int(os.environ.get("PAGE_SIZE", "50"))

    class Config:
        frozen = True


class SessionSettings(BaseDTO):
    # Session Settings
    session_engine: str = os.environ.get("SESSION_ENGINE", "django.contrib.sessions.backends.cache")
    session_cache_alias: str = os.environ.get("SESSION_CACHE_ALIAS", "defualt")
    session_cookie_age: int = int(os.environ.get("SESSION_COOKIE_AGE", 3600))
    session_expire_at_browser_close: bool = bool(strtobool(os.environ.get("SESSION_EXPIRE_AT_BROWSER_CLOSE", "true")))
    session_save_every_request: bool = (strtobool(os.environ.get("SESSION_SAVE_EVERY_REQUEST", "true")))
    # Session Cookie Settings
    session_cookie_name: str = os.environ.get("SESSION_COOKIE_NAME", "sessionid")
    session_cookie_domain: Optional[str] = os.environ.get("SESSION_COOKIE_DOMAIN")
    session_cookie_path: str = os.environ.get("SESSION_COOKIE_PATH", "/")
    session_cookie_secure: bool = bool(strtobool(os.environ.get("SESSION_COOKIE_SECURE", "true")))
    session_cookie_httponly: bool = (strtobool(os.environ.get("SESSION_COOKIE_HTTPONLY", "true")))
    session_cookie_samesite: str = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")
    # CSRF Settings
    csrf_trusted_origins: List[str] = os.environ.get(
        "CSRF_TRUSTED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost,http://127.0.0.1"
    ).split(",")
    csrf_cookie_samesite: str = os.environ.get("CSRF_COOKIE_SAMESITE", "Lax")
    csrf_cookie_secure: bool = bool(strtobool(os.environ.get("CSRF_COOKIE_SECURE", "true")))

    class Config:
        frozen = True


class BackupSettings(BaseDTO):
    base_url: str = os.getenv("ARVAN_BASE_URL", "https://s3.ir-thr-at1.arvanstorage.ir/")
    secret_key: str = os.getenv("ARVAN_SECRET_KEY", "SECRET_KEY")
    access_key: str = os.getenv("ARVAN_ACCESS_KEY", "ACCESS_KEY")
    region: str = os.getenv("ARVAN_REGION", "us-east-1")
    service_name: str = os.getenv("ARVAN_SERVICE_NAME", "s3")
    bucket: str = os.getenv("ARVAN_BUCKET", "intervention/")
    auth: ClassVar[AWS4Auth] = AWS4Auth(access_key, secret_key, region, service_name)

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
