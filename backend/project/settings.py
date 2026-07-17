import os
from pathlib import Path
from typing import ContextManager

from django.core.exceptions import ImproperlyConfigured
from corsheaders.defaults import default_headers, default_methods
from urllib.parse import quote

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from backend.apps.core_models.vo.common_vo import EnvVO
from backend.apps.permissions.access_control import AccessLimitPermission

BASE_DIR = Path(__file__).resolve().parent.parent.parent
# if os.environ.get("ENV", EnvVO.production) == EnvVO.production:
from dotenv import load_dotenv

env_name = os.environ.get("ENV", "local")
env_path = os.path.join(BASE_DIR, f"deployment/env/{env_name}.env")
root_env_path = os.path.join(BASE_DIR, ".env")

# Docker, systemd and shell environment values have the highest priority.
# Project dotenv files only fill variables that are not already defined.
for dotenv_path in (env_path, root_env_path):
    if os.path.isfile(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path, override=True)

BOT_RUNTIME_ENV_FILE_PATH = os.environ.get("BOT_RUNTIME_ENV_FILE_PATH", env_path)
BOT_RUNTIME_ENV_WRITE_ENABLED = os.environ.get("BOT_RUNTIME_ENV_WRITE_ENABLED", "false")
BOT_RUNTIME_ENV_WRITE_ALLOW_ANY_PATH = os.environ.get("BOT_RUNTIME_ENV_WRITE_ALLOW_ANY_PATH", "false")

from backend.apps.core_models.dtos.setup_config import env_bool, env_list
from backend.apps.core_models.dtos.setup_config import general_config, redis_config, celery_config, \
    pagination_config, \
    database_config, sentry_config, jwt_config, logging_config, swagger_config, session_config, rag_config

ENV = general_config.env
REDIS_AUTH_PART = f":{quote(redis_config.password, safe='')}@" if redis_config.password else ""
REDIS_LOCATION = f"redis://{REDIS_AUTH_PART}{redis_config.url}:{redis_config.port}/{redis_config.db_index}"
SECRET_KEY = general_config.secret_key
DEBUG = general_config.debug
ALLOWED_HOSTS = general_config.allowed_hosts
SITE_ID = 1
APPEND_SLASH = general_config.append_slash
ENCRYPTION_KEY = general_config.encryption_key
IS_PROD = general_config.env == EnvVO.production
RAG_CONFIG = rag_config

if IS_PROD and (not SECRET_KEY or SECRET_KEY.startswith('unsafe-local-')):
    raise ImproperlyConfigured('APP_SECRET_KEY must be configured with a strong value in production.')
if IS_PROD and not ALLOWED_HOSTS:
    raise ImproperlyConfigured('ALLOWED_HOSTS must be configured in production.')

# Public project/brand info is stored in the database after the initial bootstrap.
# The PROJECT_* env variables are read by shared.initial_data only when ProjectConfigModel does not exist.
PROJECT_LOGGER_NAME = general_config.project_logger_name
PROJECT_STATIC_ASSET_ROOT = general_config.static_asset_root
PROJECT_SERVE_STATIC_FILES = general_config.serve_static_files
SEO_CANONICAL_ORIGIN = os.environ.get("SEO_CANONICAL_ORIGIN", "").strip()

INSTALLED_APPS = [
    # pre-required apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.postgres',
    # packages
    'corsheaders',
    'channels',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',
    'django_password_validators',
    'django_cryptography',
    'drf_spectacular',
    'drf_spectacular_sidecar',
    'django_celery_beat',
    'django_celery_results',
    # apps
    'backend.apps.accounts',
    'backend.apps.common',
    'backend.apps.pages',
    'backend.apps.shared',
    'backend.apps.courses',
    'backend.apps.articles',
    'backend.apps.billing',
    'backend.apps.telegram_bot',
    'backend.apps.admin_panel',
    'backend.apps.rag',
    'django_prometheus',
]
if DEBUG:
    INSTALLED_APPS.append("debug_toolbar")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "backend.apps.common.web.seo.middleware.SeoRobotsHeaderMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    # "backend.project.middleware.PrimaryAfterWriteMiddleware",
    "backend.apps.common.helpers.middlewares.response_metrics.ResponseMetricsMiddleware",
    "backend.apps.common.helpers.middlewares.general_response.GeneralResponseMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "backend.apps.common.web.ajax.middleware.AjaxFormRedirectMiddleware",
    # "backend.apps.common.helpers.middlewares.block_token.BlockedTokenMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]
if DEBUG:
    MIDDLEWARE.insert(4, "debug_toolbar.middleware.DebugToolbarMiddleware")

ROOT_URLCONF = 'backend.project.urls'
WSGI_APPLICATION = 'backend.project.wsgi.application'
ASGI_APPLICATION = 'backend.project.asgi.application'
CORS_ALLOW_ALL_ORIGINS = general_config.cors_origin_allow_all
CORS_ALLOWED_ORIGINS = general_config.cors_allowed_origins
CORS_ALLOW_CREDENTIALS = general_config.core_allow_credential
CORS_ALLOW_HEADERS = general_config.core_allow_headers or list(default_headers)
CORS_ALLOW_METHODS = general_config.core_allow_methods or list(default_methods)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "backend.apps.accounts.security.jwt_authentication.ActiveUserJWTAuthentication",
    ],
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    'DEFAULT_PAGINATION_CLASS': 'backend.apps.common.helpers.pagination.cursor_pagination.HTTPSCursorPagination',
    "PAGE_SIZE": pagination_config.page_size,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.environ.get("DRF_ANON_THROTTLE_RATE", "120/minute"),
        "user": os.environ.get("DRF_USER_THROTTLE_RATE", "1200/minute"),
        "login": os.environ.get("DRF_LOGIN_THROTTLE_RATE", "10/minute"),
    },
}

AUTH_USER_MODEL = 'accounts.CustomUser'
LANGUAGE_CODE = 'fa-ir'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "backend/static"]
STATIC_ROOT = os.path.join(BASE_DIR, "deployment/staticfiles")
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "backend/apps/media/")

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_LOCATION,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PASSWORD": redis_config.password,
            "CONNECTION_POOL_KWARGS": {
                "max_connections": redis_config.max_connection,
            },
        },
    }
}
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_LOCATION],
        },
    },
}
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / "backend/templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'backend.apps.common.context_processors.project_context',
                'backend.apps.billing.web.context_processors.basket_context',
            ],
        },
    },
]

# Database configuration
DATABASES = database_config.databases

DATABASE_ROUTERS = [
    "backend.project.db_routers.PrimaryReplicaRouter",
]
READ_AFTER_WRITE_PRIMARY_SECONDS = int(
    os.environ.get("READ_AFTER_WRITE_PRIMARY_SECONDS", "5")
)

INTERNAL_IPS = [
    "127.0.0.1",
]
# --- Session Settings ---
SESSION_ENGINE = session_config.session_engine
SESSION_CACHE_ALIAS = session_config.session_cache_alias
SESSION_COOKIE_AGE = session_config.session_cookie_age
SESSION_EXPIRE_AT_BROWSER_CLOSE = session_config.session_expire_at_browser_close
SESSION_SAVE_EVERY_REQUEST = session_config.session_save_every_request

# --- Session Cookie Settings ---
SESSION_COOKIE_NAME = session_config.session_cookie_name
SESSION_COOKIE_DOMAIN = session_config.session_cookie_domain
SESSION_COOKIE_PATH = session_config.session_cookie_path
SESSION_COOKIE_SECURE = session_config.session_cookie_secure
SESSION_COOKIE_HTTPONLY = session_config.session_cookie_httponly
SESSION_COOKIE_SAMESITE = session_config.session_cookie_samesite

# --- CSRF Settings ---
CSRF_TRUSTED_ORIGINS = session_config.csrf_trusted_origins
CSRF_COOKIE_SAMESITE = session_config.csrf_cookie_samesite
CSRF_COOKIE_SECURE = session_config.csrf_cookie_secure
CSRF_FAILURE_VIEW = "backend.apps.common.web.error_views.csrf_failure"

if IS_PROD and not CSRF_TRUSTED_ORIGINS:
    raise ImproperlyConfigured(
        "CSRF_TRUSTED_ORIGINS must contain the production HTTPS origins."
    )
if IS_PROD and any(
    not origin.startswith("https://") for origin in CSRF_TRUSTED_ORIGINS
):
    raise ImproperlyConfigured(
        "Every production CSRF_TRUSTED_ORIGINS value must start with https://."
    )

# Celery configuration
CELERY_BROKER_URL = celery_config.broker_url
CELERY_RESULT_BACKEND = celery_config.result_backend
CELERY_ACCEPT_CONTENT = celery_config.accept_content
CELERY_TASK_SERIALIZER = celery_config.task_serializer
CELERY_RESULT_SERIALIZER = celery_config.result_serializer

# Sentry configuration
if sentry_config.use_sentry:
    sentry_sdk.init(
        dsn=sentry_config.dsn,
        integrations=[DjangoIntegration()],
        traces_sample_rate=sentry_config.traces_sample_rate,
        send_default_pii=sentry_config.send_default_pii,
    )
ACCESS_TOKEN_LIFE_TIME_HOUR = jwt_config.access_token_lifetime_minutes
# JWT Configuration
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": jwt_config.access_token_lifetime,
    "REFRESH_TOKEN_LIFETIME": jwt_config.refresh_token_lifetime,
    "ROTATE_REFRESH_TOKENS": jwt_config.rotate_refresh_tokens,
    "BLACKLIST_AFTER_ROTATION": jwt_config.blacklist_after_rotation,
    "ALGORITHM": jwt_config.algorithm,
    "VERIFYING_KEY": jwt_config.verifying_key,
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "UPDATE_LAST_LOGIN": True,
    # Access tokens include a password fingerprint and are rejected immediately
    # after a password change/reset.
    "CHECK_REVOKE_TOKEN": True,
}

# Logging configuration
LOGGING = logging_config.model_dump()

# Swagger Configuration
if swagger_config.use_swagger:
    SPECTACULAR_SETTINGS = swagger_config.spectacular_settings

LIST_OF_PROXIES = general_config.list_of_proxies
LIST_OF_WHITE_SHABA = general_config.list_of_white_shaba

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]
PERMISSIONS: ContextManager = None
DEFAULT_PERMISSION_CLS = AccessLimitPermission

# Security headers and proxy trust. Keep proxy trust opt-in and restricted.
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = os.environ.get("X_FRAME_OPTIONS", "DENY")
SECURE_REFERRER_POLICY = os.environ.get("SECURE_REFERRER_POLICY", "same-origin")
SECURE_CROSS_ORIGIN_OPENER_POLICY = os.environ.get(
    "SECURE_CROSS_ORIGIN_OPENER_POLICY", "same-origin"
)
SECURE_SSL_REDIRECT = IS_PROD and os.environ.get("SECURE_SSL_REDIRECT", "true").lower() in {"1", "true", "yes", "on"}
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "31536000" if IS_PROD else "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = IS_PROD and os.environ.get("SECURE_HSTS_INCLUDE_SUBDOMAINS", "true").lower() in {"1", "true", "yes", "on"}
SECURE_HSTS_PRELOAD = IS_PROD and os.environ.get("SECURE_HSTS_PRELOAD", "false").lower() in {"1", "true", "yes", "on"}
if os.environ.get("TRUST_PROXY_SSL_HEADER", "false").lower() in {"1", "true", "yes", "on"}:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

TRUST_X_FORWARDED_FOR = os.environ.get("TRUST_X_FORWARDED_FOR", "false").lower() in {"1", "true", "yes", "on"}
TRUSTED_PROXY_IPS = [item.strip() for item in os.environ.get("TRUSTED_PROXY_IPS", "").split(",") if item.strip()]
PROMETHEUS_METRICS_TOKEN = os.environ.get("PROMETHEUS_METRICS_TOKEN", "")
DATA_UPLOAD_MAX_MEMORY_SIZE = max(1024, min(
    int(os.environ.get("DATA_UPLOAD_MAX_MEMORY_SIZE", str(10 * 1024 * 1024))),
    20 * 1024 * 1024,
))
FILE_UPLOAD_MAX_MEMORY_SIZE = max(1024, min(
    int(os.environ.get("FILE_UPLOAD_MAX_MEMORY_SIZE", str(5 * 1024 * 1024))),
    10 * 1024 * 1024,
))
DATA_UPLOAD_MAX_NUMBER_FIELDS = max(20, min(
    int(os.environ.get("DATA_UPLOAD_MAX_NUMBER_FIELDS", "300")),
    1000,
))
DATA_UPLOAD_MAX_NUMBER_FILES = max(1, min(
    int(os.environ.get("DATA_UPLOAD_MAX_NUMBER_FILES", "10")),
    50,
))
PAYMENT_RECEIPT_MAX_BYTES = max(1024, min(
    int(os.environ.get("PAYMENT_RECEIPT_MAX_BYTES", str(5 * 1024 * 1024))),
    10 * 1024 * 1024,
))
PAYMENT_RECEIPT_MAX_PIXELS = max(1_000_000, min(
    int(os.environ.get("PAYMENT_RECEIPT_MAX_PIXELS", "40000000")),
    100_000_000,
))
COURSE_THUMBNAIL_MAX_BYTES = max(1024, min(
    int(os.environ.get("COURSE_THUMBNAIL_MAX_BYTES", str(3 * 1024 * 1024))),
    10 * 1024 * 1024,
))
COURSE_THUMBNAIL_MAX_PIXELS = max(1_000_000, min(
    int(os.environ.get("COURSE_THUMBNAIL_MAX_PIXELS", "25000000")),
    50_000_000,
))
VERIFICATION_CODE_MAX_ATTEMPTS = int(os.environ.get("VERIFICATION_CODE_MAX_ATTEMPTS", "5"))
KAVENEGAR_API_KEY = os.environ.get("KAVENEGAR_API_KEY", "")
KAVENEGAR_BASE_URL = os.environ.get("KAVENEGAR_BASE_URL", "https://api.kavenegar.com/v1").rstrip("/")
OAUTH_ALLOWED_REDIRECT_HOSTS = [item.strip().lower() for item in os.environ.get("OAUTH_ALLOWED_REDIRECT_HOSTS", "").split(",") if item.strip()]
CHANNEL_SYNC_ALLOWED_MEDIA_HOSTS = [
    item.strip().lower()
    for item in os.environ.get("CHANNEL_SYNC_ALLOWED_MEDIA_HOSTS", "").split(",")
    if item.strip()
]


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = (os.getenv("EMAIL_USE_TLS") or "true").lower() == "true"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET")
TELEGRAM_WEBAPP_URL = os.environ.get("TELEGRAM_WEBAPP_URL")
TELEGRAM_WEBHOOK_URL = os.environ.get("TELEGRAM_WEBHOOK_URL")
TELEGRAM_PAYMENT_PROVIDER = os.environ.get("TELEGRAM_PAYMENT_PROVIDER")
TELEGRAM_LIST_PAGE_SIZE = os.environ.get("TELEGRAM_LIST_PAGE_SIZE", "5")
PAYMENT_SANDBOX_ENABLED = os.environ.get("PAYMENT_SANDBOX_ENABLED")

BALE_BOT_TOKEN = os.environ.get("BALE_BOT_TOKEN")
BALE_BOT_BASE_URL = os.environ.get("BALE_BOT_BASE_URL")
BALE_WEBHOOK_SECRET = os.environ.get("BALE_WEBHOOK_SECRET")
BALE_WEBHOOK_URL = os.environ.get("BALE_WEBHOOK_URL")
BALE_WEBAPP_URL = os.environ.get("BALE_WEBAPP_URL")
BALE_PAYMENT_PROVIDER = os.environ.get("BALE_PAYMENT_PROVIDER")
BALE_POLLING_TIMEOUT = os.environ.get("BALE_POLLING_TIMEOUT")
BALE_POLLING_LIMIT = os.environ.get("BALE_POLLING_LIMIT")

PROXY_URL = os.environ.get("PROXY_URL")
BALE_PROXY_URL = os.environ.get("BALE_PROXY_URL")

# --- reCAPTCHA v3 Settings ---
RECAPTCHA_ENABLED = env_bool("RECAPTCHA_ENABLED", False)
RECAPTCHA_SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY", "").strip()
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY", "").strip()
RECAPTCHA_MIN_SCORE = float(os.getenv("RECAPTCHA_MIN_SCORE", "0.5"))
RECAPTCHA_ALLOWED_HOSTNAMES = [
    hostname.lower().rstrip(".")
    for hostname in env_list("RECAPTCHA_ALLOWED_HOSTNAMES")
]
RECAPTCHA_HTTP_TIMEOUT_SECONDS = max(
    1,
    min(int(os.getenv("RECAPTCHA_HTTP_TIMEOUT_SECONDS", "5")), 30),
)
RECAPTCHA_MAX_RESPONSE_BYTES = max(
    1024,
    min(int(os.getenv("RECAPTCHA_MAX_RESPONSE_BYTES", "65536")), 1024 * 1024),
)
RECAPTCHA_SEND_REMOTE_IP = env_bool("RECAPTCHA_SEND_REMOTE_IP", True)

if not 0.0 <= RECAPTCHA_MIN_SCORE <= 1.0:
    raise ImproperlyConfigured("RECAPTCHA_MIN_SCORE must be between 0.0 and 1.0.")
if RECAPTCHA_ENABLED:
    missing_recaptcha_settings = [
        setting_name
        for setting_name, value in (
            ("RECAPTCHA_SITE_KEY", RECAPTCHA_SITE_KEY),
            ("RECAPTCHA_SECRET_KEY", RECAPTCHA_SECRET_KEY),
            ("RECAPTCHA_ALLOWED_HOSTNAMES", RECAPTCHA_ALLOWED_HOSTNAMES),
        )
        if not value
    ]
    if missing_recaptcha_settings:
        raise ImproperlyConfigured(
            "Missing required reCAPTCHA settings: "
            + ", ".join(missing_recaptcha_settings)
        )


# --- Social OAuth Settings ---
GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
GITHUB_OAUTH_CLIENT_ID = os.getenv("GITHUB_OAUTH_CLIENT_ID", "")
GITHUB_OAUTH_CLIENT_SECRET = os.getenv("GITHUB_OAUTH_CLIENT_SECRET", "")
OAUTH_ALLOWED_REDIRECT_URIS = [
    uri.strip()
    for uri in os.getenv("OAUTH_ALLOWED_REDIRECT_URIS", "").split(",")
    if uri.strip()
]
OAUTH_HTTP_TIMEOUT_SECONDS = int(os.getenv("OAUTH_HTTP_TIMEOUT_SECONDS", "10"))
OAUTH_MAX_RESPONSE_BYTES = int(os.getenv("OAUTH_MAX_RESPONSE_BYTES", str(1024 * 1024)))
OAUTH_STATE_TTL_SECONDS = int(os.getenv("OAUTH_STATE_TTL_SECONDS", "600"))
GOOGLE_OAUTH_WEB_REDIRECT_URI = os.getenv("GOOGLE_OAUTH_WEB_REDIRECT_URI", "").strip()
GITHUB_OAUTH_WEB_REDIRECT_URI = os.getenv("GITHUB_OAUTH_WEB_REDIRECT_URI", "").strip()
# Kept for backward compatibility with previous deployments. OAuth now logs in
# existing accounts only and never provisions a role or creates a user.
OAUTH_DEFAULT_USER_ROLE_SYMBOL = os.getenv("OAUTH_DEFAULT_USER_ROLE_SYMBOL", "user")

RUBIKA_BOT_TOKEN = os.environ.get("RUBIKA_BOT_TOKEN")
RUBIKA_BOT_BASE_URL = os.environ.get("RUBIKA_BOT_BASE_URL")
RUBIKA_WEBHOOK_SECRET = os.environ.get("RUBIKA_WEBHOOK_SECRET")
RUBIKA_WEBHOOK_URL = os.environ.get("RUBIKA_WEBHOOK_URL")
RUBIKA_WEBAPP_URL = os.environ.get("RUBIKA_WEBAPP_URL")
RUBIKA_PAYMENT_PROVIDER = os.environ.get("RUBIKA_PAYMENT_PROVIDER")
RUBIKA_POLLING_LIMIT = os.environ.get("RUBIKA_POLLING_LIMIT")
RUBIKA_POLLING_SLEEP_SECONDS = os.environ.get("RUBIKA_POLLING_SLEEP_SECONDS")
RUBIKA_PROXY_URL = os.environ.get("RUBIKA_PROXY_URL")

CARD_TO_CARD_NUMBER = os.environ.get("CARD_TO_CARD_NUMBER", "")
CARD_TO_CARD_HOLDER = os.environ.get("CARD_TO_CARD_HOLDER", "")
CARD_TO_CARD_BANK_NAME = os.environ.get("CARD_TO_CARD_BANK_NAME", "")
CARD_TO_CARD_IBAN = os.environ.get("CARD_TO_CARD_IBAN", "")

PARDAKHTYAR_MERCHANT_ID = os.environ.get("PARDAKHTYAR_MERCHANT_ID", "")
PARDAKHTYAR_REQUEST_URL = os.environ.get("PARDAKHTYAR_REQUEST_URL", "")
PARDAKHTYAR_VERIFY_URL = os.environ.get("PARDAKHTYAR_VERIFY_URL", "")
PARDAKHTYAR_START_PAY_BASE_URL = os.environ.get("PARDAKHTYAR_START_PAY_BASE_URL", "")
PARDAKHTYAR_CALLBACK_URL = os.environ.get("PARDAKHTYAR_CALLBACK_URL", "")
PARDAKHTYAR_SUCCESS_CODES = os.environ.get("PARDAKHTYAR_SUCCESS_CODES", "100,0,ok,success,succeeded,paid")
PARDAKHTYAR_HTTP_TIMEOUT_SECONDS = os.environ.get("PARDAKHTYAR_HTTP_TIMEOUT_SECONDS", "12")
PARDAKHTYAR_FRONTEND_SUCCESS_URL = os.environ.get("PARDAKHTYAR_FRONTEND_SUCCESS_URL", "")
PARDAKHTYAR_FRONTEND_FAILED_URL = os.environ.get("PARDAKHTYAR_FRONTEND_FAILED_URL", "")
PARDAKHTYAR_ALLOWED_HOSTS = [
    item.strip() for item in os.environ.get("PARDAKHTYAR_ALLOWED_HOSTS", "").split(",") if item.strip()
]
PARDAKHTYAR_PAYMENT_ALLOWED_HOSTS = [
    item.strip() for item in os.environ.get("PARDAKHTYAR_PAYMENT_ALLOWED_HOSTS", "").split(",") if item.strip()
]
PARDAKHTYAR_CALLBACK_ALLOWED_HOSTS = [
    item.strip() for item in os.environ.get("PARDAKHTYAR_CALLBACK_ALLOWED_HOSTS", "").split(",") if item.strip()
]
PARDAKHTYAR_FRONTEND_ALLOWED_HOSTS = [
    item.strip() for item in os.environ.get("PARDAKHTYAR_FRONTEND_ALLOWED_HOSTS", "").split(",") if item.strip()
]
PARDAKHTYAR_MAX_RESPONSE_BYTES = max(1024, min(
    int(os.environ.get("PARDAKHTYAR_MAX_RESPONSE_BYTES", str(1024 * 1024))),
    5 * 1024 * 1024,
))


BOT_PROVIDER_MAX_RESPONSE_BYTES = max(1024, min(int(os.environ.get("BOT_PROVIDER_MAX_RESPONSE_BYTES", str(1024 * 1024))), 5 * 1024 * 1024))
