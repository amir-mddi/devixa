import json
import logging

from confluent_kafka import Producer

from dealio.apps.common.helpers.metaclasses.singleton import Singleton

logger = logging.getLogger("root")


class KafkaProducerAdapter(metaclass=Singleton):
    def __init__(self):
        self.config = {
            'bootstrap.servers': 'localhost:29092',
            'acks': 'all',
            'retries': 3,
            'batch.num.messages': 1000,
            'linger.ms': 10,
            'compression.codec': 'gzip',
            'max.in.flight.requests.per.connection': 5,
            'delivery.timeout.ms': 120000,
        }

        self.producer = Producer(**self.config)

    def commit(self, message: json, topic: str):
        try:
            self.producer.produce(topic, value=message)
            self.producer.flush()
            logger.info(f"Message pushed to Kafka topic {topic}: {message}")
        except Exception as e:
            logger.error(f"Error pushing message to Kafka topic {topic}: {str(e)}")

    # def produce_arkham_address_transactions(self, address_data, topic=KafkaVo.address):
    #     addresses = self._convert_list_of_dtos_to_json(address_data, fields=['address', 'chain_type'])
    #     self.commit(message=addresses, topic=topic)
    #
    # def produce_arkham_entities(self, entities, topic=KafkaVo.entity):
    #     entities = self._convert_list_of_dtos_to_json(entities, ['arkham_entity', 'label'])
    #     self.commit(message=entities, topic=topic)

    # def produce_entities_address(self, addresses, topic=KafkaVo.entity_addresses):
    #     entities_address = self._convert_list_of_dtos_to_json(addresses,
    #                                                           fields=['address', 'chain_type', 'arkham_entity',
    #                                                                   'label'])
    #     self.commit(message=entities_address, topic=topic)
    #
    # @staticmethod
    # def _convert_list_of_dtos_to_json(dtos, fields):
    #     data = BaseDTO.convert_list_of_dtos_to_json(dtos=dtos, fields=fields)
    #     return data
