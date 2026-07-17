from __future__ import annotations

from asgiref.sync import sync_to_async
from django.conf import settings

from backend.apps.accounts.dtos.recaptcha_dto import RecaptchaVerificationDTO
from backend.apps.accounts.entities.recaptcha_entity import (
    RecaptchaProviderResponseEntity,
    RecaptchaVerificationResultEntity,
)
from backend.apps.accounts.enums.recaptcha_enums import RecaptchaFailureReasonEnum
from backend.apps.accounts.exceptions.recaptcha_exceptions import RecaptchaProviderError
from backend.apps.accounts.repositories.recaptcha_repository import RecaptchaVerificationRepository
from backend.apps.accounts.vo.recaptcha_vo import RecaptchaLogMessageVO
from backend.apps.common.utils.common_utils import CommonUtils

logger = CommonUtils.get_project_logger(__name__)


class RecaptchaVerificationLogic:
    repository_class = RecaptchaVerificationRepository

    def __init__(self, repository: RecaptchaVerificationRepository | None = None):
        self._repository = repository or self.repository_class()

    async def verify_async(
        self,
        dto: RecaptchaVerificationDTO,
    ) -> RecaptchaVerificationResultEntity:
        preflight, normalized_dto = self._preflight(dto)
        if preflight is not None:
            return preflight

        try:
            async_verifier = getattr(self._repository, "verify_async", None)
            if async_verifier is not None:
                response = await async_verifier(normalized_dto)
            else:
                response = await sync_to_async(
                    self._repository.verify,
                    thread_sensitive=False,
                )(normalized_dto)
        except RecaptchaProviderError:
            return self._rejected(RecaptchaFailureReasonEnum.PROVIDER_UNAVAILABLE)

        return self._evaluate_response(dto=normalized_dto, response=response)

    def verify(
        self,
        dto: RecaptchaVerificationDTO,
    ) -> RecaptchaVerificationResultEntity:
        """Compatibility entry point for synchronous Django form views."""
        preflight, normalized_dto = self._preflight(dto)
        if preflight is not None:
            return preflight

        try:
            response = self._repository.verify(normalized_dto)
        except RecaptchaProviderError:
            return self._rejected(RecaptchaFailureReasonEnum.PROVIDER_UNAVAILABLE)

        return self._evaluate_response(dto=normalized_dto, response=response)

    @staticmethod
    def _preflight(
        dto: RecaptchaVerificationDTO,
    ) -> tuple[RecaptchaVerificationResultEntity | None, RecaptchaVerificationDTO]:
        if not settings.RECAPTCHA_ENABLED:
            return (
                RecaptchaVerificationResultEntity(
                    is_allowed=True,
                    reason=RecaptchaFailureReasonEnum.DISABLED,
                ),
                dto,
            )

        token = dto.token.strip()
        normalized_dto = RecaptchaVerificationDTO(
            token=token,
            expected_action=dto.expected_action,
            remote_ip=dto.remote_ip,
        )
        if not token:
            return (
                RecaptchaVerificationLogic._rejected(
                    RecaptchaFailureReasonEnum.MISSING_TOKEN
                ),
                normalized_dto,
            )
        return None, normalized_dto

    @classmethod
    def _evaluate_response(
        cls,
        *,
        dto: RecaptchaVerificationDTO,
        response: RecaptchaProviderResponseEntity,
    ) -> RecaptchaVerificationResultEntity:
        if not response.success:
            logger.info(
                RecaptchaLogMessageVO.PROVIDER_REJECTED.value.format(
                    error_codes=",".join(response.error_codes) or "unknown"
                )
            )
            return cls._rejected(
                RecaptchaFailureReasonEnum.PROVIDER_REJECTED,
                score=response.score,
                hostname=response.hostname,
            )

        if response.action != dto.expected_action.value:
            logger.info(
                RecaptchaLogMessageVO.ACTION_MISMATCH.value.format(
                    expected=dto.expected_action.value,
                    actual=response.action,
                )
            )
            return cls._rejected(
                RecaptchaFailureReasonEnum.ACTION_MISMATCH,
                score=response.score,
                hostname=response.hostname,
            )

        minimum_score = float(settings.RECAPTCHA_MIN_SCORE)
        if response.score < minimum_score:
            logger.info(
                RecaptchaLogMessageVO.SCORE_TOO_LOW.value.format(
                    score=response.score,
                    threshold=minimum_score,
                )
            )
            return cls._rejected(
                RecaptchaFailureReasonEnum.SCORE_TOO_LOW,
                score=response.score,
                hostname=response.hostname,
            )

        allowed_hostnames = {
            str(hostname).strip().lower().rstrip(".")
            for hostname in settings.RECAPTCHA_ALLOWED_HOSTNAMES
            if str(hostname).strip()
        }
        if response.hostname not in allowed_hostnames:
            logger.warning(
                RecaptchaLogMessageVO.HOSTNAME_MISMATCH.value.format(
                    hostname=response.hostname or "missing"
                )
            )
            return cls._rejected(
                RecaptchaFailureReasonEnum.HOSTNAME_MISMATCH,
                score=response.score,
                hostname=response.hostname,
            )

        return RecaptchaVerificationResultEntity(
            is_allowed=True,
            reason=RecaptchaFailureReasonEnum.VERIFIED,
            score=response.score,
            hostname=response.hostname,
        )

    @staticmethod
    def _rejected(
        reason: RecaptchaFailureReasonEnum,
        *,
        score: float | None = None,
        hostname: str = "",
    ) -> RecaptchaVerificationResultEntity:
        return RecaptchaVerificationResultEntity(
            is_allowed=False,
            reason=reason,
            score=score,
            hostname=hostname,
        )
