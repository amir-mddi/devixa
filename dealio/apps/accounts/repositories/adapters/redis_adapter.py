from redis import Redis

from dealio.apps.common.helpers.metaclasses.singleton import Singleton
from dealio.apps.core_models.dtos.setup_config import redis_config


class RedisAdapter(metaclass=Singleton):
    def __init__(self):
        super().__init__()
        self.redis_client = Redis(
            host=redis_config.url,
            port=redis_config.port,
            password=redis_config.password,
            decode_responses=True,
            db=redis_config.db_index,
            max_connections=redis_config.max_connection
        )
