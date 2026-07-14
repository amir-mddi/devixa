from __future__ import annotations

from dealio.apps.accounts.adapters.recaptcha_adapter import GoogleRecaptchaAdapter
from dealio.apps.accounts.dtos.recaptcha_dto import RecaptchaVerificationDTO
from dealio.apps.accounts.entities.recaptcha_entity import RecaptchaProviderResponseEntity


class RecaptchaVerificationRepository:
    adapter_class = GoogleRecaptchaAdapter

    def __init__(self, adapter: GoogleRecaptchaAdapter | None = None):
        self._adapter = adapter or self.adapter_class()

    def verify(
        self,
        dto: RecaptchaVerificationDTO,
    ) -> RecaptchaProviderResponseEntity:
        return self._adapter.verify(dto)
