from __future__ import annotations

import os

from confluent_kafka import Producer
from django.core.exceptions import ImproperlyConfigured

from dealio.apps.common.helpers.metaclasses.singleton import Singleton
from dealio.apps.common.utils.common_utils import CommonUtils

logger = CommonUtils.get_project_logger(__name__)


class KafkaProducerAdapter(metaclass=Singleton):
    def __init__(self):
        bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "").strip()
        if not bootstrap_servers:
            raise ImproperlyConfigured("KAFKA_BOOTSTRAP_SERVERS is required.")

        config = {
            "bootstrap.servers": bootstrap_servers,
            "acks": "all",
            "retries": max(0, min(int(os.environ.get("KAFKA_RETRIES", "3")), 20)),
            "batch.num.messages": max(
                1,
                min(int(os.environ.get("KAFKA_BATCH_NUM_MESSAGES", "1000")), 10000),
            ),
            "linger.ms": max(0, min(int(os.environ.get("KAFKA_LINGER_MS", "10")), 5000)),
            "compression.codec": os.environ.get("KAFKA_COMPRESSION_CODEC", "gzip"),
            "max.in.flight.requests.per.connection": 5,
            "delivery.timeout.ms": max(
                1000,
                min(int(os.environ.get("KAFKA_DELIVERY_TIMEOUT_MS", "120000")), 600000),
            ),
        }
        security_protocol = os.environ.get("KAFKA_SECURITY_PROTOCOL", "").strip()
        if security_protocol:
            config["security.protocol"] = security_protocol
        sasl_username = os.environ.get("KAFKA_SASL_USERNAME", "").strip()
        sasl_password = os.environ.get("KAFKA_SASL_PASSWORD", "")
        if sasl_username or sasl_password:
            if not sasl_username or not sasl_password:
                raise ImproperlyConfigured(
                    "Both KAFKA_SASL_USERNAME and KAFKA_SASL_PASSWORD are required."
                )
            config.update(
                {
                    "sasl.username": sasl_username,
                    "sasl.password": sasl_password,
                    "sasl.mechanism": os.environ.get("KAFKA_SASL_MECHANISM", "PLAIN"),
                }
            )

        self.producer = Producer(**config)

    def commit(self, message, topic: str):
        topic = str(topic or "").strip()
        if not topic or len(topic) > 249:
            raise ValueError("Invalid Kafka topic name.")
        try:
            self.producer.produce(topic, value=message)
            remaining = self.producer.flush(
                timeout=max(1.0, min(float(os.environ.get("KAFKA_FLUSH_TIMEOUT", "10")), 60.0))
            )
            if remaining:
                raise RuntimeError("Kafka delivery timed out.")
            logger.info("Message pushed to Kafka topic %s.", topic)
        except Exception:
            logger.exception("Kafka publish failed for topic %s.", topic)
            raise
