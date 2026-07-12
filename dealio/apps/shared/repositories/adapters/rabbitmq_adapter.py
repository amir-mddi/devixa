from __future__ import annotations

import os

import pika
from django.core.exceptions import ImproperlyConfigured

from dealio.apps.common.helpers.metaclasses.singleton import Singleton
from dealio.apps.common.utils.common_utils import CommonUtils

logger = CommonUtils.get_project_logger(__name__)


class RabbitMQProducerAdapter(metaclass=Singleton):
    """Lazy RabbitMQ adapter with deployment-provided credentials."""

    def __init__(self):
        self._connection = None
        self._channel = None

    def _ensure_channel(self):
        if self._channel and getattr(self._channel, "is_open", False):
            return self._channel

        host = os.environ.get("RABBITMQ_HOST", "").strip()
        username = os.environ.get("RABBITMQ_USERNAME", "").strip()
        password = os.environ.get("RABBITMQ_PASSWORD", "")
        if not host or not username or not password:
            raise ImproperlyConfigured(
                "RABBITMQ_HOST, RABBITMQ_USERNAME, and RABBITMQ_PASSWORD are required."
            )

        credentials = pika.PlainCredentials(username, password)
        parameters = pika.ConnectionParameters(
            host=host,
            port=int(os.environ.get("RABBITMQ_PORT", "5672")),
            virtual_host=os.environ.get("RABBITMQ_VHOST", "/"),
            credentials=credentials,
            heartbeat=int(os.environ.get("RABBITMQ_HEARTBEAT", "60")),
            blocked_connection_timeout=float(
                os.environ.get("RABBITMQ_BLOCKED_CONNECTION_TIMEOUT", "10")
            ),
            connection_attempts=max(
                1,
                min(int(os.environ.get("RABBITMQ_CONNECTION_ATTEMPTS", "3")), 10),
            ),
            retry_delay=max(
                0.1,
                min(float(os.environ.get("RABBITMQ_RETRY_DELAY", "1")), 10.0),
            ),
        )
        self._connection = pika.BlockingConnection(parameters)
        self._channel = self._connection.channel()
        return self._channel

    def commit(self, message: str, queue_name: str):
        queue_name = str(queue_name or "").strip()
        if not queue_name or len(queue_name) > 255:
            raise ValueError("Invalid RabbitMQ queue name.")

        channel = self._ensure_channel()
        try:
            channel.queue_declare(queue=queue_name, durable=True)
            channel.basic_publish(
                exchange="",
                routing_key=queue_name,
                body=str(message).encode("utf-8"),
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
                ),
            )
            logger.info("Message pushed to RabbitMQ queue %s.", queue_name)
        except Exception:
            logger.exception("RabbitMQ publish failed for queue %s.", queue_name)
            raise
