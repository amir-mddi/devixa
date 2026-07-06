import json
from dealio.apps.common.utils.common_utils import CommonUtils
import pika

from dealio.apps.common.helpers.metaclasses.singleton import Singleton

logger = CommonUtils.get_project_logger(__name__)


class RabbitMQProducerAdapter(metaclass=Singleton):
    def __init__(self):
        self.credentials = pika.PlainCredentials('admin', 'admin')
        self.parameters = pika.ConnectionParameters(
            host='localhost',
            port=5672,
            virtual_host='/',
            credentials=self.credentials,
        )

        self.connection = pika.BlockingConnection(self.parameters)
        self.channel = self.connection.channel()

    def commit(self, message: str, queue_name: str):
        try:
            self.channel.queue_declare(queue=queue_name, durable=True)

            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=message.encode('utf-8'),
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
                )
            )
            logger.info(f"Message pushed to RabbitMQ queue {queue_name}: {message}")
        except Exception as e:
            logger.error(f"Error pushing message to RabbitMQ queue {queue_name}: {str(e)}")
