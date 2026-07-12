import logging
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any

from django.core.exceptions import ImproperlyConfigured

from dealio.apps.common.utils.request_utils import RequestUtils
from dealio.apps.core_models.constants.runtime_config import RuntimeConfig
from dealio.apps.core_models.dtos.sms_providers.kavenegar_params_dto import (
    KavenegarTemplateSmsDTO,
)
from dealio.apps.core_models.enum.general_enum import RequestMethod

logger = logging.getLogger(__name__)


class KavenegarSmsService:
    _executor = ThreadPoolExecutor(
        max_workers=5,
        thread_name_prefix="kavenegar-sms",
    )

    def __init__(self):
        self.api_key = RuntimeConfig.API_KEY
        self.base_url = RuntimeConfig.base_url

    def send_sms(self, dto: KavenegarTemplateSmsDTO) -> Any:
        if not self.api_key:
            raise ImproperlyConfigured("KAVENEGAR_API_KEY is not configured.")

        params = {
            "receptor": dto.recipient_phone_number,
            "template": dto.template_name,
            "token": dto.token,
            "token2": dto.token2,
            "token3": dto.token3,
            "token10": dto.token10,
            "token20": dto.token20,
        }
        params = {
            key: value
            for key, value in params.items()
            if value is not None
        }

        response = RequestUtils.request(
            url=self.base_url.format(API_KEY=self.api_key),
            method=RequestMethod.GET,
            params=params,
            rotate_proxy_on_error=False,
            redact_url=True,
        )
        return response.json()

    def send_in_thread(self, dto: KavenegarTemplateSmsDTO) -> Future[Any]:
        future = self._executor.submit(self.send_sms, dto)
        future.add_done_callback(self._handle_result)
        return future

    @staticmethod
    def _handle_result(future: Future[Any]) -> None:
        try:
            future.result()
        except Exception:
            logger.exception("Kavenegar SMS delivery failed.")
