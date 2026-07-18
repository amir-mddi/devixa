"""Deterministic settings used by the Django unit-test suite.

Production settings remain untouched. External infrastructure is replaced by
in-memory/local test doubles so tests never require Redis, PostgreSQL, email,
Celery workers, channel servers, or external observability services.
"""
import os

# Disable Sentry before importing the production settings module. This prevents
# developer/CI shell variables or production dotenv files from sending test
# failures to the real Sentry project.
os.environ["USE_SENTRY"] = "false"
os.environ["USE_PROMETHEUS"] = "false"
os.environ["USE_HEALTH_CHECKS"] = "true"

from .settings import *  # noqa: F401,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "TEST": {"NAME": ":memory:"},
    }
}
DATABASE_ROUTERS = []

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "backend-tests",
    }
}
CHANNEL_LAYERS = {
    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
}
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1", "acdevixa.ir"]
CORS_ALLOWED_ORIGINS = []
CORS_ALLOW_ALL_ORIGINS = True

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Test requests should exercise views, serializers and permissions, not
# monitoring/debug integrations or project-wide response wrapping.
MIDDLEWARE = [
    middleware
    for middleware in MIDDLEWARE
    if middleware
    not in {
        "debug_toolbar.middleware.DebugToolbarMiddleware",
        (
            "backend.apps.common.observability.prometheus.middleware."
            "PrometheusRequestMetricsMiddleware"
        ),
        "backend.apps.common.helpers.middlewares.general_response.GeneralResponseMiddleware",
    }
]

SILENCED_SYSTEM_CHECKS = ["fields.W340"]
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"null": {"class": "logging.NullHandler"}},
    "root": {"handlers": ["null"], "level": "CRITICAL"},
}
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_CACHE_ALIAS = "default"
SILENCED_SYSTEM_CHECKS = ["fields.W340", "debug_toolbar.W001"]
