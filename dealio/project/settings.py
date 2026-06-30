import os
from pathlib import Path
from typing import ContextManager
from urllib.parse import quote

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from dealio.apps.core_models.vo.common_vo import EnvVO
from dealio.apps.permissions.access_control import AccessLimitPermission

BASE_DIR = Path(__file__).resolve().parent.parent.parent
# if os.environ.get("ENV", EnvVO.production) == EnvVO.production:
from dotenv import load_dotenv

env_path = os.path.join(BASE_DIR, f"deployment/env/{os.environ.get('ENV', 'local')}.env")
load_dotenv(dotenv_path=env_path, override=True)

from dealio.apps.core_models.dtos.setup_config import general_config, redis_config, celery_config, \
    pagination_config, \
    database_config, sentry_config, jwt_config, logging_config, swagger_config, session_config

ENV = general_config.env
REDIS_AUTH_PART = f":{quote(redis_config.password, safe='')}@" if redis_config.password else ""
REDIS_LOCATION = f"redis://{REDIS_AUTH_PART}{redis_config.url}:{redis_config.port}/{redis_config.db_index}"
SECRET_KEY = general_config.secret_key
DEBUG = general_config.debug
ALLOWED_HOSTS = general_config.allowed_hosts
SITE_ID = 1
APPEND_SLASH = general_config.append_slash
ENCRYPTION_KEY = general_config.encryption_key
IS_PROD = os.environ.get("ENV", EnvVO.production) == EnvVO.production
INSTALLED_APPS = [
    # pre-required apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    # packages
    "debug_toolbar",
    'corsheaders',
    'channels',
    'rest_framework_simplejwt',
    'django_filters',
    'django_password_validators',
    'django_cryptography',
    'drf_spectacular',
    'drf_spectacular_sidecar',
    'django_celery_beat',
    'django_celery_results',
    # apps
    'dealio.apps.accounts',
    'dealio.apps.shared',
    'dealio.apps.courses',
    'dealio.apps.billing',
    'dealio.apps.telegram_bot',
    'django_prometheus',
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    # "dealio.project.middleware.PrimaryAfterWriteMiddleware",
    "dealio.apps.common.helpers.middlewares.response_metrics.ResponseMetricsMiddleware",
    "dealio.apps.common.helpers.middlewares.general_response.GeneralResponseMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    # "dealio.apps.common.helpers.middlewares.block_token.BlockedTokenMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = 'dealio.project.urls'
WSGI_APPLICATION = 'dealio.project.wsgi.application'
ASGI_APPLICATION = 'dealio.project.application'
CORS_ALLOW_ALL_ORIGINS = general_config.cors_origin_allow_all
CORS_ALLOWED_ORIGINS = general_config.cors_allowed_origins
CORS_ALLOW_CREDENTIALS = general_config.core_allow_credential
CORS_ALLOW_HEADERS = general_config.core_allow_headers
CORS_ALLOW_METHODS = general_config.core_allow_methods

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    # "DEFAULT_PERMISSION_CLASSES": [
    #     "dealio.apps.permissions.access_control.AccessLimitPermission",
    # ],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    'DEFAULT_PAGINATION_CLASS': 'dealio.apps.common.helpers.pagination.cursor_pagination.HTTPSCursorPagination',
    "PAGE_SIZE": pagination_config.page_size,
    # "DEFAULT_THROTTLE_CLASSES": [
    #     "rest_framework.throttling.AnonRateThrottle",
    #     "rest_framework.throttling.UserRateThrottle",
    # ],
    # "DEFAULT_THROTTLE_RATES": {"anon": "100/minute", "user": "100000/minute"},
}

AUTH_USER_MODEL = 'accounts.CustomUser'
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "deployment/staticfiles")
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "dealio/apps/media/")

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

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
            BASE_DIR / "dealio/templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Database configuration
DATABASES = database_config.databases

DATABASE_ROUTERS = [
    "dealio.project.db_routers.PrimaryReplicaRouter",
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
SESSION_COOKIE_AGE = int(jwt_config.access_token_lifetime.total_seconds())
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
        traces_sample_rate=1.0,
        send_default_pii=True,
    )
ACCESS_TOKEN_LIFE_TIME_HOUR = jwt_config.refresh_token_lifetime_hours
# JWT Configuration
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": jwt_config.access_token_lifetime,
    "REFRESH_TOKEN_LIFETIME": jwt_config.refresh_token_lifetime,
    "ROTATE_REFRESH_TOKENS": jwt_config.rotate_refresh_tokens,
    "BLACKLIST_AFTER_ROTATION": jwt_config.blacklist_after_rotation,
    "ALGORITHM": jwt_config.algorithm,
    "VERIFYING_KEY": jwt_config.verifying_key,
}

# Logging configuration
LOGGING = logging_config.model_dump()

# Swagger Configuration
if swagger_config.use_swagger:
    SPECTACULAR_SETTINGS = swagger_config.spectacular_settings

LIST_OF_PROXIES = general_config.list_of_proxies
LIST_OF_WHITE_SHABA = general_config.list_of_white_shaba

# AUTH_PASSWORD_VALIDATORS = [
#     {
#         "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
#     },
#     {
#         "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
#         "OPTIONS": {"min_length": 8},
#     },
#     {
#         "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
#     },
#     {
#         "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
#     },
# ]
PERMISSIONS: ContextManager = None
DEFAULT_PERMISSION_CLS = AccessLimitPermission

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
