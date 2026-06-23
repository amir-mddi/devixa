import logging
from pydoc_data.topics import topics

from dealio.apps.common.helpers.metaclasses.singleton import Singleton
from dealio.apps.shared.dtos.metric_data import MetricDataDto
# from dealio.apps.shared.repositories.adapters.kafka_adapter import KafkaProducerAdapter
from dealio.apps.shared.repositories.adapters.metric_provider_adapter import MetricProviderAdapter
from dealio.apps.shared.repositories.adapters.postgres_adapter import PostgresAdapter
import json

# from dealio.apps.shared.repositories.adapters.rabbitmq_adapter import RabbitMQProducerAdapter

logger = logging.getLogger("dealio")
log_identifier = "Shared Repository log"


class SharedApplicationLogic(metaclass=Singleton):
    def __init__(self):
        self.postgres_adapter = PostgresAdapter()
        self.metric_provider_adapter = MetricProviderAdapter()
        # self.kafka_adapter = KafkaProducerAdapter()
        # self.rabbitmq_adapter = RabbitMQProducerAdapter()

    def push_notification_into_kafka(self, message: json, kafka_topic: str = "notification"):
        self.kafka_adapter.commit(message=message, topic=kafka_topic)

    def push_notification_into_rabbitmq(self, message: str, queue_name: str = "notification"):
        self.rabbitmq_adapter.commit(message=message, queue_name=queue_name)

    def expire_an_api_key(self, expired_key):
        return self.postgres_adapter.expire_an_api_key(expired_key)

    def fetch_newest_api_key(self):
        return self.postgres_adapter.fetch_newest_api_key()

    def check_address_balance_exist(self, address: str, network: str, contract_address: str | None):
        return self.postgres_adapter.check_address_balance_exist(address, network, contract_address)

    def insert_address_balance(self, data):
        return self.postgres_adapter.insert_address_balance(data)

    def add_new_metric(self, metric_data: MetricDataDto):
        return self.metric_provider_adapter.add_new_metric(metric_data)
