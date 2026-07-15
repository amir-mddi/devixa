from __future__ import absolute_import, unicode_literals

import os
from datetime import timedelta

from celery import Celery
from kombu import Queue


app = Celery(os.environ.get("PROJECT_CELERY_APP_NAME", os.environ.get("PROJECT_SLUG", "project")))
app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks([
    "backend.apps.telegram_bot",
    "backend.apps.shared",
])

app.conf.update(
    broker_transport_options={"max_connections": 20},
    result_backend_transport_options={"max_connections": 20},
    task_acks_late=True,
    task_queues=(Queue("high_priority", routing_key="high_priority"),),
)

app.conf.beat_schedule = {
    "telegram_scheduled_notifications": {
        "task": "backend.apps.telegram_bot.tasks.dispatch_due_telegram_scheduled_notifications",
        "schedule": timedelta(minutes=1),
        "options": {"queue": "high_priority"},
    },
    "cleanup_bot_update_logs": {
        "task": "backend.apps.telegram_bot.tasks.cleanup_bot_update_logs",
        "schedule": timedelta(days=1),
        "options": {"queue": "high_priority"},
    },
    # "metric_gauge_task": {
    #     "task": "backend.apps.asset.tasks.metric_gauges_task.metric_gauge_task",
    #     "schedule": timedelta(minutes=1),
    #     "options": {"queue": "high_priority"},
    # }
}
