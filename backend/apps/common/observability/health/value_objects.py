from __future__ import annotations


class HealthDependencyVO:
    DATABASE = "database"
    CACHE = "cache"
    CELERY_BROKER = "celery_broker"


class HealthResponseVO:
    CACHE_CONTROL = "no-store"
    LIVE_STATUS = "alive"
