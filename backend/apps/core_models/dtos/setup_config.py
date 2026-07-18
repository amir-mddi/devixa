import ipaddress
import os
from datetime import timedelta
from distutils.util import strtobool
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional
from urllib.parse import quote

from pydantic import Field, field_validator
from requests_aws4auth import AWS4Auth

from backend.apps.core_models.dtos.base_dto import BaseDTO


_LOCAL_ENVS = {"local", "development", "dev", "testing", "test"}
_PROJECT_ROOT = Path(__file__).resolve().parents[4]


def env_text(name: str, default: str = "") -> str:
    """Return a stripped environment value and treat blank values as missing.

    Empty assignments such as ``SQLITE_ENGINE=`` are common in shared env
    templates. They must not erase safe framework defaults.
    """

    raw_value = os.environ.get(name)
    if raw_value is None or not raw_value.strip():
        return default
    return raw_value.strip()


def env_bool(name: str, default: bool) -> bool:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    return bool(strtobool(raw_value))


def env_list(
    name: str,
    default: str = "",
    *,
    use_default_if_blank: bool = False,
) -> list[str]:
    raw_value = os.environ.get(name)
    if raw_value is None or (use_default_if_blank and not raw_value.strip()):
        raw_value = default
    raw_value = raw_value.strip()
    if not raw_value or raw_value in {"[]", "()"}:
        return []
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def env_float_tuple(name: str, default: str) -> tuple[float, ...]:
    values = env_list(name, default)
    try:
        parsed = tuple(float(value) for value in values)
    except ValueError as exc:
        raise ValueError(f"{name} must contain comma-separated numbers.") from exc
    if not parsed or any(value <= 0 for value in parsed):
        raise ValueError(f"{name} must contain positive numbers.")
    if tuple(sorted(set(parsed))) != parsed:
        raise ValueError(f"{name} values must be unique and sorted ascending.")
    return parsed


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
    """Environment-backed Sentry SDK configuration.

    Error monitoring is fully opt-in through USE_SENTRY. Performance tracing,
    profiling, structured logs, PII, and trace propagation are independently
    switchable to keep production data collection explicit.
    """

    use_sentry: bool = Field(
        default_factory=lambda: env_bool("USE_SENTRY", False)
    )
    dsn: str = Field(
        default_factory=lambda: os.environ.get("SENTRY_DSN", "").strip()
    )
    environment: str = Field(
        default_factory=lambda: os.environ.get(
            "SENTRY_ENVIRONMENT",
            os.environ.get("ENV", "local"),
        ).strip()
    )
    release: str = Field(
        default_factory=lambda: (
            os.environ.get("SENTRY_RELEASE")
            or os.environ.get("GIT_COMMIT_SHA")
            or os.environ.get("SOURCE_VERSION")
            or ""
        ).strip()
    )
    server_name: str = Field(
        default_factory=lambda: os.environ.get("SENTRY_SERVER_NAME", "").strip()
    )

    error_sample_rate: float = Field(
        default_factory=lambda: float(
            os.environ.get("SENTRY_ERROR_SAMPLE_RATE", "1.0")
        )
    )
    enable_tracing: bool = Field(
        default_factory=lambda: env_bool("SENTRY_ENABLE_TRACING", False)
    )
    traces_sample_rate: float = Field(
        default_factory=lambda: float(
            os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.05")
        )
    )
    profiles_sample_rate: float = Field(
        default_factory=lambda: float(
            os.environ.get("SENTRY_PROFILES_SAMPLE_RATE", "0.0")
        )
    )

    send_default_pii: bool = Field(
        default_factory=lambda: env_bool("SENTRY_SEND_DEFAULT_PII", False)
    )
    enable_logs: bool = Field(
        default_factory=lambda: env_bool("SENTRY_ENABLE_LOGS", False)
    )
    debug: bool = Field(
        default_factory=lambda: env_bool("SENTRY_DEBUG", False)
    )
    attach_stacktrace: bool = Field(
        default_factory=lambda: env_bool("SENTRY_ATTACH_STACKTRACE", True)
    )
    include_local_variables: bool = Field(
        default_factory=lambda: env_bool(
            "SENTRY_INCLUDE_LOCAL_VARIABLES",
            False,
        )
    )
    max_request_body_size: str = Field(
        default_factory=lambda: os.environ.get(
            "SENTRY_MAX_REQUEST_BODY_SIZE",
            "never",
        ).strip().lower()
    )
    max_breadcrumbs: int = Field(
        default_factory=lambda: int(
            os.environ.get("SENTRY_MAX_BREADCRUMBS", "100")
        )
    )
    shutdown_timeout_seconds: float = Field(
        default_factory=lambda: float(
            os.environ.get("SENTRY_SHUTDOWN_TIMEOUT_SECONDS", "2")
        )
    )
    flush_timeout_seconds: float = Field(
        default_factory=lambda: float(
            os.environ.get("SENTRY_FLUSH_TIMEOUT_SECONDS", "5")
        )
    )

    trace_propagation_targets: list[str] = Field(
        default_factory=lambda: env_list("SENTRY_TRACE_PROPAGATION_TARGETS")
    )
    ignored_path_prefixes: list[str] = Field(
        default_factory=lambda: env_list(
            "SENTRY_IGNORED_PATH_PREFIXES",
            "/health,/healthz,/ready,/readiness,/metrics,/static/,/media/,/favicon.ico",
        )
    )
    strict_trace_continuation: bool = Field(
        default_factory=lambda: env_bool(
            "SENTRY_STRICT_TRACE_CONTINUATION",
            True,
        )
    )

    transaction_style: str = Field(
        default_factory=lambda: os.environ.get(
            "SENTRY_TRANSACTION_STYLE",
            "url",
        ).strip().lower()
    )
    middleware_spans: bool = Field(
        default_factory=lambda: env_bool("SENTRY_MIDDLEWARE_SPANS", True)
    )
    signals_spans: bool = Field(
        default_factory=lambda: env_bool("SENTRY_SIGNALS_SPANS", True)
    )
    cache_spans: bool = Field(
        default_factory=lambda: env_bool("SENTRY_CACHE_SPANS", True)
    )
    db_transaction_spans: bool = Field(
        default_factory=lambda: env_bool(
            "SENTRY_DB_TRANSACTION_SPANS",
            True,
        )
    )
    celery_propagate_traces: bool = Field(
        default_factory=lambda: env_bool(
            "SENTRY_CELERY_PROPAGATE_TRACES",
            True,
        )
    )
    monitor_celery_beat_tasks: bool = Field(
        default_factory=lambda: env_bool(
            "SENTRY_MONITOR_CELERY_BEAT_TASKS",
            True,
        )
    )
    redis_max_data_size: int = Field(
        default_factory=lambda: max(
            0,
            int(os.environ.get("SENTRY_REDIS_MAX_DATA_SIZE", "1024")),
        )
    )

    @field_validator(
        "error_sample_rate",
        "traces_sample_rate",
        "profiles_sample_rate",
    )
    @classmethod
    def validate_sample_rate(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("Sentry sample rates must be between 0.0 and 1.0.")
        return value

    @field_validator("max_request_body_size")
    @classmethod
    def validate_request_body_size(cls, value: str) -> str:
        allowed_values = {"never", "small", "medium", "always"}
        if value not in allowed_values:
            raise ValueError(
                "SENTRY_MAX_REQUEST_BODY_SIZE must be one of: "
                "never, small, medium, always."
            )
        return value

    @field_validator("transaction_style")
    @classmethod
    def validate_transaction_style(cls, value: str) -> str:
        if value not in {"url", "function_name"}:
            raise ValueError(
                "SENTRY_TRANSACTION_STYLE must be 'url' or 'function_name'."
            )
        return value

    @field_validator(
        "max_breadcrumbs",
        "shutdown_timeout_seconds",
        "flush_timeout_seconds",
    )
    @classmethod
    def validate_positive_number(cls, value):
        if value < 0:
            raise ValueError("Sentry limits and timeouts cannot be negative.")
        return value

    class Config:
        frozen = True


class PrometheusConfiguration(BaseDTO):
    """Environment-backed metrics configuration with a single master switch."""

    use_prometheus: bool = Field(
        default_factory=lambda: env_bool("USE_PROMETHEUS", False)
    )
    namespace: str = Field(
        default_factory=lambda: os.environ.get(
            "PROMETHEUS_NAMESPACE",
            "devixa",
        ).strip().lower()
    )
    require_auth: bool = Field(
        default_factory=lambda: env_bool(
            "PROMETHEUS_REQUIRE_AUTH",
            os.environ.get("ENV", "local").strip().lower() not in _LOCAL_ENVS,
        )
    )
    metrics_token: str = Field(
        default_factory=lambda: os.environ.get(
            "PROMETHEUS_METRICS_TOKEN",
            "",
        ).strip()
    )
    metrics_allowed_ips: list[str] = Field(
        default_factory=lambda: env_list("PROMETHEUS_METRICS_ALLOWED_IPS")
    )
    excluded_path_prefixes: list[str] = Field(
        default_factory=lambda: env_list(
            "PROMETHEUS_EXCLUDED_PATH_PREFIXES",
            "/metrics,/health,/static/,/media/,/favicon.ico",
        )
    )
    enable_celery_metrics: bool = Field(
        default_factory=lambda: env_bool("PROMETHEUS_ENABLE_CELERY_METRICS", True)
    )
    request_duration_buckets: tuple[float, ...] = Field(
        default_factory=lambda: env_float_tuple(
            "PROMETHEUS_REQUEST_DURATION_BUCKETS",
            "0.01,0.025,0.05,0.1,0.25,0.5,1,2.5,5,10",
        )
    )
    response_size_buckets: tuple[float, ...] = Field(
        default_factory=lambda: env_float_tuple(
            "PROMETHEUS_RESPONSE_SIZE_BUCKETS",
            "256,1024,4096,16384,65536,262144,1048576,4194304",
        )
    )
    health_duration_buckets: tuple[float, ...] = Field(
        default_factory=lambda: env_float_tuple(
            "PROMETHEUS_HEALTH_DURATION_BUCKETS",
            "0.005,0.01,0.025,0.05,0.1,0.25,0.5,1,2.5,5",
        )
    )
    celery_duration_buckets: tuple[float, ...] = Field(
        default_factory=lambda: env_float_tuple(
            "PROMETHEUS_CELERY_DURATION_BUCKETS",
            "0.05,0.1,0.25,0.5,1,2.5,5,10,30,60,300",
        )
    )

    @field_validator("namespace")
    @classmethod
    def validate_namespace(cls, value: str) -> str:
        normalized = value.replace("-", "_")
        if not normalized or not normalized[0].isalpha():
            raise ValueError("PROMETHEUS_NAMESPACE must start with a letter.")
        if not all(character.isalnum() or character == "_" for character in normalized):
            raise ValueError(
                "PROMETHEUS_NAMESPACE may contain only letters, numbers, and underscores."
            )
        return normalized

    @field_validator("metrics_allowed_ips")
    @classmethod
    def validate_allowed_ips(cls, values: list[str]) -> list[str]:
        for value in values:
            try:
                ipaddress.ip_network(value, strict=False)
            except ValueError as exc:
                raise ValueError(
                    "PROMETHEUS_METRICS_ALLOWED_IPS must contain valid IP or CIDR values."
                ) from exc
        return values

    @field_validator("excluded_path_prefixes")
    @classmethod
    def normalize_excluded_paths(cls, values: list[str]) -> list[str]:
        return [
            value if value.startswith("/") else f"/{value}"
            for value in values
        ]

    class Config:
        frozen = True


class HealthCheckConfiguration(BaseDTO):
    """Independent health endpoints for load balancers and orchestrators."""

    enabled: bool = Field(
        default_factory=lambda: env_bool("USE_HEALTH_CHECKS", True)
    )
    timeout_seconds: float = Field(
        default_factory=lambda: float(
            os.environ.get("HEALTH_CHECK_TIMEOUT_SECONDS", "2")
        )
    )
    check_database: bool = Field(
        default_factory=lambda: env_bool("HEALTH_CHECK_DATABASE", True)
    )
    database_alias: str = Field(
        default_factory=lambda: os.environ.get(
            "HEALTH_CHECK_DATABASE_ALIAS",
            "default",
        ).strip()
    )
    check_cache: bool = Field(
        default_factory=lambda: env_bool("HEALTH_CHECK_CACHE", True)
    )
    cache_alias: str = Field(
        default_factory=lambda: os.environ.get(
            "HEALTH_CHECK_CACHE_ALIAS",
            "default",
        ).strip()
    )
    check_celery_broker: bool = Field(
        default_factory=lambda: env_bool("HEALTH_CHECK_CELERY_BROKER", False)
    )

    @field_validator("timeout_seconds")
    @classmethod
    def validate_timeout(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("HEALTH_CHECK_TIMEOUT_SECONDS must be positive.")
        return value

    class Config:
        frozen = True


class DatabaseConfiguration(BaseDTO):
    """Database settings with safe local defaults and explicit validation."""

    use_sql_database: bool = Field(
        default_factory=lambda: env_bool("USE_SQL_DATABASE", True)
    )
    use_database_replica: bool = Field(
        default_factory=lambda: env_bool("USE_DATABASE_REPLICA", False)
    )
    database_engine: str = Field(
        default_factory=lambda: env_text("DATABASE_ENGINE", "sqlite").lower()
    )

    sqlite_engine: str = Field(
        default_factory=lambda: env_text(
            "SQLITE_ENGINE",
            "django.db.backends.sqlite3",
        )
    )
    sqlite_name: str = Field(
        default_factory=lambda: env_text(
            "SQLITE_NAME",
            str(_PROJECT_ROOT / "db" / "db.sqlite3"),
        )
    )
    sqlite_conn_max_age: int = Field(
        default_factory=lambda: int(env_text("SQLITE_CONN_MAX_AGE", "0"))
    )
    sqlite_timeout: int = Field(
        default_factory=lambda: int(env_text("SQLITE_TIMEOUT", "20"))
    )

    postgres_name: str = Field(
        default_factory=lambda: env_text("POSTGRES_NAME")
    )
    postgres_user: str = Field(
        default_factory=lambda: env_text("POSTGRES_USER")
    )
    postgres_password: str = Field(
        default_factory=lambda: os.environ.get("POSTGRES_PASSWORD", "")
    )
    postgres_host: str = Field(
        default_factory=lambda: env_text("POSTGRES_HOST", "localhost")
    )
    postgres_port: str = Field(
        default_factory=lambda: env_text("POSTGRES_PORT", "5432")
    )
    postgres_conn_max_age: int = Field(
        default_factory=lambda: int(env_text("POSTGRES_CONN_MAX_AGE", "60"))
    )
    postgres_sslmode: str = Field(
        default_factory=lambda: env_text("POSTGRES_SSLMODE", "prefer")
    )

    postgres_replica_name: str = Field(
        default_factory=lambda: env_text(
            "POSTGRES_REPLICA_NAME",
            env_text("POSTGRES_NAME"),
        )
    )
    postgres_replica_user: str = Field(
        default_factory=lambda: env_text(
            "POSTGRES_REPLICA_USER",
            env_text("POSTGRES_USER"),
        )
    )
    postgres_replica_password: str = Field(
        default_factory=lambda: os.environ.get(
            "POSTGRES_REPLICA_PASSWORD",
            os.environ.get("POSTGRES_PASSWORD", ""),
        )
    )
    postgres_replica_host: str = Field(
        default_factory=lambda: env_text("POSTGRES_REPLICA_HOST")
    )
    postgres_replica_port: str = Field(
        default_factory=lambda: env_text(
            "POSTGRES_REPLICA_PORT",
            env_text("POSTGRES_PORT", "5432"),
        )
    )
    postgres_replica_conn_max_age: int = Field(
        default_factory=lambda: int(
            env_text("POSTGRES_REPLICA_CONN_MAX_AGE", "60")
        )
    )
    postgres_replica_sslmode: str = Field(
        default_factory=lambda: env_text(
            "POSTGRES_REPLICA_SSLMODE",
            "prefer",
        )
    )

    @field_validator("database_engine")
    @classmethod
    def validate_database_engine(cls, value: str) -> str:
        aliases = {
            "postgres": "postgresql",
            "postgresql": "postgresql",
            "sqlite": "sqlite",
            "sqlite3": "sqlite",
        }
        try:
            return aliases[value]
        except KeyError as exc:
            raise ValueError(
                "DATABASE_ENGINE must be sqlite, sqlite3, postgres, or postgresql."
            ) from exc

    @property
    def sqlite_database_config(self) -> dict[str, Any]:
        return {
            "ENGINE": self.sqlite_engine,
            "NAME": self.sqlite_name,
            "CONN_MAX_AGE": self.sqlite_conn_max_age,
            "OPTIONS": {"timeout": self.sqlite_timeout},
        }

    @property
    def primary_database_config(self) -> dict[str, Any]:
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": self.postgres_name,
            "USER": self.postgres_user,
            "PASSWORD": self.postgres_password,
            "HOST": self.postgres_host,
            "PORT": self.postgres_port,
            "CONN_MAX_AGE": self.postgres_conn_max_age,
            "OPTIONS": {"sslmode": self.postgres_sslmode},
        }

    @property
    def replica_database_config(self) -> dict[str, Any]:
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": self.postgres_replica_name,
            "USER": self.postgres_replica_user,
            "PASSWORD": self.postgres_replica_password,
            "HOST": self.postgres_replica_host,
            "PORT": self.postgres_replica_port,
            "CONN_MAX_AGE": self.postgres_replica_conn_max_age,
            "OPTIONS": {"sslmode": self.postgres_replica_sslmode},
        }

    @property
    def dummy_database_config(self) -> dict[str, str]:
        return {
            "ENGINE": "django.db.backends.dummy",
            "NAME": "dummy",
        }

    @property
    def databases(self) -> dict[str, dict[str, Any]]:
        if not self.use_sql_database:
            return {"default": self.dummy_database_config}
        if self.database_engine == "sqlite":
            return {"default": self.sqlite_database_config}

        databases = {"default": self.primary_database_config}
        if self.use_database_replica:
            databases["replica"] = self.replica_database_config
        return databases

    @property
    def database(self) -> dict[str, Any]:
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
        use_default_if_blank=is_local_environment,
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


class RagConfiguration(BaseDTO):
    enabled: bool = env_bool("RAG_ENABLED", True)
    embedding_provider: str = os.environ.get("RAG_EMBEDDING_PROVIDER", "openai").strip().lower()
    llm_provider: str = os.environ.get("RAG_LLM_PROVIDER", "openai").strip().lower()
    openai_api_key: str = os.environ.get("OPENAI_API_KEY", "").strip()
    openai_base_url: str = os.environ.get("OPENAI_BASE_URL", "").strip()
    embedding_model: str = os.environ.get("RAG_EMBEDDING_MODEL", "text-embedding-3-small").strip()
    llm_model: str = os.environ.get("RAG_LLM_MODEL", "gpt-5.5").strip()
    embedding_dimensions: int = 1536
    embedding_batch_size: int = max(1, min(int(os.environ.get("RAG_EMBEDDING_BATCH_SIZE", "64")), 512))
    embedding_timeout_seconds: float = max(1.0, float(os.environ.get("RAG_EMBEDDING_TIMEOUT_SECONDS", "60")))
    generation_timeout_seconds: float = max(1.0, float(os.environ.get("RAG_GENERATION_TIMEOUT_SECONDS", "180")))

    class Config:
        frozen = True


celery_config = CeleryConfiguration()
jwt_config = JWTConfiguration()
sentry_config = SentryConfiguration()
prometheus_config = PrometheusConfiguration()
health_check_config = HealthCheckConfiguration()
database_config = DatabaseConfiguration()
logging_config = LoggingConfiguration()
swagger_config = SwaggerConfiguration()
pagination_config = PaginationConfiguration()
session_config = SessionSettings()
backup_config = BackupSettings()
rag_config = RagConfiguration()

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
