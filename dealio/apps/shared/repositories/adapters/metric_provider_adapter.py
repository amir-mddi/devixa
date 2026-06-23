from dealio.apps.common.helpers.metaclasses.singleton import Singleton
from dealio.apps.common.utils.request_utils import RequestUtils
from dealio.apps.core_models.dtos.setup_config import general_config
from dealio.apps.core_models.enum.general_enum import RequestMethod
from dealio.apps.shared.dtos.metric_data import MetricDataDto


class MetricProviderAdapter(metaclass=Singleton):

    def add_new_metric(self, metric_data: MetricDataDto):
        url = general_config.metric_service_endpoint
        resp = RequestUtils.request(url=url, method=RequestMethod.POST, data=metric_data.model_dump(), timeout=(3, 1))
        if resp.status_code != 200:
            raise ValueError("Failed to add new metric")
