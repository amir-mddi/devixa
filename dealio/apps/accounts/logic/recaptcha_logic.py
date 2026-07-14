from __future__ import annotations

from django.conf import settings

from dealio.apps.accounts.dtos.recaptcha_dto import RecaptchaVerificationDTO
from dealio.apps.accounts.entities.recaptcha_entity import RecaptchaVerificationResultEntity
from dealio.apps.accounts.enums.recaptcha_enums import RecaptchaFailureReasonEnum
from dealio.apps.accounts.exceptions.recaptcha_exceptions import RecaptchaProviderError
from dealio.apps.accounts.repositories.recaptcha_repository import RecaptchaVerificationRepository
from dealio.apps.accounts.vo.recaptcha_vo import RecaptchaLogMessageVO
from dealio.apps.common.utils.common_utils import CommonUtils

logger = CommonUtils.get_project_logger(__name__)


class RecaptchaVerificationLogic:
    repository_class = RecaptchaVerificationRepository

    def __init__(self, repository: RecaptchaVerificationRepository | None = None):
        self._repository = repository or self.repository_class()

    def verify(
        self,
        dto: RecaptchaVerificationDTO,
    ) -> RecaptchaVerificationResultEntity:
        if not settings.RECAPTCHA_ENABLED:
            return RecaptchaVerificationResultEntity(
                is_allowed=True,
                reason=RecaptchaFailureReasonEnum.DISABLED,
            )

        token = dto.token.strip()
        if not token:
            return self._rejected(RecaptchaFailureReasonEnum.MISSING_TOKEN)

        try:
            response = self._repository.verify(
                RecaptchaVerificationDTO(
                    token=token,
                    expected_action=dto.expected_action,
                    remote_ip=dto.remote_ip,
                )
            )
        except RecaptchaProviderError:
            return self._rejected(
                RecaptchaFailureReasonEnum.PROVIDER_UNAVAILABLE
            )

        if not response.success:
            logger.info(
                RecaptchaLogMessageVO.PROVIDER_REJECTED.value.format(
                    error_codes=",".join(response.error_codes) or "unknown"
                )
            )
            return self._rejected(
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
            return self._rejected(
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
            return self._rejected(
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
            return self._rejected(
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
