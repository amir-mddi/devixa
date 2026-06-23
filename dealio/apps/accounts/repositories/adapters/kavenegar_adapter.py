from dealio.apps.common.helpers.metaclasses.singleton import Singleton
from dealio.apps.common.utils.request_utils import RequestUtils
from dealio.apps.core_models.constants.runtime_config import RuntimeConfig
from dealio.apps.core_models.enum.general_enum import RequestMethod


class KavenegarSmsAdapter(metaclass=Singleton):
    def __init__(self):
        self.api_key = RuntimeConfig.API_KEY

    def send_sms(self, receptor: str, template: str, value_first: str, value_second: str):
        return {"message": "ok"}
        # url = RuntimeConfig.base_url.format(API_KEY=self.api_key, receptor=receptor, token_value=value_first,
        #                                     token2=value_second,
        #                                     template=template)
        # response = RequestUtils.request(url=url, method=RequestMethod.GET)
        # return response.json()
