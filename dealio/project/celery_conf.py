from __future__ import absolute_import, unicode_literals

import os
from datetime import timedelta

from celery import Celery
from kombu import Queue


app = Celery("dealio")
app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks([

])

app.conf.update(
    broker_transport_options={"max_connections": 20},
    result_backend_transport_options={"max_connections": 20},
    task_acks_late=True,
    task_queues=(Queue("high_priority", routing_key="high_priority"),),
)

app.conf.beat_schedule = {
    # "metric_gauge_task": {
    #     "task": "dealio.apps.asset.tasks.metric_gauges_task.metric_gauge_task",
    #     "schedule": timedelta(minutes=1),
    #     "options": {"queue": "high_priority"},
    # }
}
