from asgiref.sync import sync_to_async
import json

from backend.apps.common.helpers.metaclasses.singleton import Singleton
from backend.apps.common.utils.common_utils import CommonUtils
from backend.apps.core_models.dtos.sms_providers.kavenegar_params_dto import KavenegarTemplateSmsDTO
from backend.apps.shared.dtos.metric_data import MetricDataDto
from backend.apps.shared.dtos.project_config_dto import ProjectConfigDTO
from backend.apps.shared.initial_data.initial_data.project_config_initial import initialize_project_config
from backend.apps.shared.repositories.adapters.kavenegar_adapter import KavenegarSmsService
# from backend.apps.shared.repositories.adapters.kafka_adapter import KafkaProducerAdapter
from backend.apps.shared.repositories.adapters.metric_provider_adapter import MetricProviderAdapter
from backend.apps.shared.repositories.adapters.postgres_adapter import PostgresAdapter

# from backend.apps.shared.repositories.adapters.rabbitmq_adapter import RabbitMQProducerAdapter

logger = CommonUtils.get_project_logger(__name__)
log_identifier = "Shared Repository log"


class SharedApplicationLogic(metaclass=Singleton):
    def __init__(self):
        self.postgres_adapter = PostgresAdapter()
        self.metric_provider_adapter = MetricProviderAdapter()
        self.sms_provider = KavenegarSmsService()
        # self.kafka_adapter = KafkaProducerAdapter()
        # self.rabbitmq_adapter = RabbitMQProducerAdapter()

    def push_notification_into_kafka(self, message: json, kafka_topic: str = "notification"):
        from backend.apps.shared.repositories.adapters.kafka_adapter import KafkaProducerAdapter

        KafkaProducerAdapter().commit(message=message, topic=kafka_topic)

    def send_sms(self, data_dto: KavenegarTemplateSmsDTO):
        return self.sms_provider.send_in_thread(data_dto)

    def push_notification_into_rabbitmq(self, message: str, queue_name: str = "notification"):
        from backend.apps.shared.repositories.adapters.rabbitmq_adapter import RabbitMQProducerAdapter

        RabbitMQProducerAdapter().commit(message=message, queue_name=queue_name)

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

    async def get_project_config_async(self) -> ProjectConfigDTO | None:
        return await sync_to_async(
            self.get_project_config,
            thread_sensitive=True,
        )()

    async def change_project_config_async(
        self,
        data: dict,
        user=None,
    ) -> ProjectConfigDTO:
        return await sync_to_async(
            self.change_project_config,
            thread_sensitive=True,
        )(data=data, user=user)

    def get_project_config(self) -> ProjectConfigDTO | None:
        project_config = self.postgres_adapter.fetch_project_config()

        if not project_config:
            project_config, _ = initialize_project_config()

        if not project_config:
            return None

        return ProjectConfigDTO.from_model(project_config)

    def change_project_config(self, data: dict, user=None) -> ProjectConfigDTO:
        project_config = self.postgres_adapter.change_project_config(data=data, user=user)
        return ProjectConfigDTO.from_model(project_config)
