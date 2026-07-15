from __future__ import annotations

import json
from collections.abc import Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings

from backend.apps.accounts.dtos.recaptcha_dto import RecaptchaVerificationDTO
from backend.apps.accounts.entities.recaptcha_entity import RecaptchaProviderResponseEntity
from backend.apps.accounts.exceptions.recaptcha_exceptions import RecaptchaProviderError
from backend.apps.accounts.vo.recaptcha_vo import (
    RecaptchaDefaultVO,
    RecaptchaEndpointVO,
    RecaptchaLogMessageVO,
    RecaptchaRequestFieldVO,
    RecaptchaResponseFieldVO,
)
from backend.apps.common.utils.common_utils import CommonUtils

logger = CommonUtils.get_project_logger(__name__)


class GoogleRecaptchaAdapter:
    """Google reCAPTCHA v3 transport adapter.

    This class is the only account component that knows the provider endpoint and
    wire response format. Tokens and secrets are deliberately never logged.
    """

    def verify(self, dto: RecaptchaVerificationDTO) -> RecaptchaProviderResponseEntity:
        payload = {
            RecaptchaRequestFieldVO.SECRET.value: settings.RECAPTCHA_SECRET_KEY,
            RecaptchaRequestFieldVO.RESPONSE.value: dto.token,
        }
        if settings.RECAPTCHA_SEND_REMOTE_IP and dto.remote_ip:
            payload[RecaptchaRequestFieldVO.REMOTE_IP.value] = dto.remote_ip

        request = Request(
            RecaptchaEndpointVO.SITE_VERIFY.value,
            data=urlencode(payload).encode("utf-8"),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "Devixa-reCAPTCHA/1.0",
            },
            method="POST",
        )
        response_payload = self._open_json(request)
        return self._to_entity(response_payload)

    @staticmethod
    def _open_json(request: Request) -> Mapping[str, object]:
        timeout = max(
            1,
            int(
                getattr(
                    settings,
                    "RECAPTCHA_HTTP_TIMEOUT_SECONDS",
                    RecaptchaDefaultVO.HTTP_TIMEOUT_SECONDS.value,
                )
            ),
        )
        max_bytes = max(
            1024,
            int(
                getattr(
                    settings,
                    "RECAPTCHA_MAX_RESPONSE_BYTES",
                    RecaptchaDefaultVO.MAX_RESPONSE_BYTES.value,
                )
            ),
        )

        try:
            with urlopen(request, timeout=timeout) as response:
                content_length = response.headers.get("Content-Length")
                try:
                    declared_size = int(content_length) if content_length else 0
                except (TypeError, ValueError):
                    declared_size = 0
                if declared_size > max_bytes:
                    raise RecaptchaProviderError(
                        RecaptchaLogMessageVO.PROVIDER_INVALID_RESPONSE.value
                    )

                raw_body = response.read(max_bytes + 1)
                if len(raw_body) > max_bytes:
                    raise RecaptchaProviderError(
                        RecaptchaLogMessageVO.PROVIDER_INVALID_RESPONSE.value
                    )
        except HTTPError as exc:
            logger.warning(
                RecaptchaLogMessageVO.PROVIDER_HTTP_ERROR.value.format(
                    status=exc.code
                )
            )
            raise RecaptchaProviderError(
                RecaptchaLogMessageVO.PROVIDER_INVALID_RESPONSE.value
            ) from exc
        except (URLError, TimeoutError, OSError) as exc:
            logger.warning(
                RecaptchaLogMessageVO.PROVIDER_CONNECTION_ERROR.value.format(
                    error=exc
                )
            )
            raise RecaptchaProviderError(
                RecaptchaLogMessageVO.PROVIDER_INVALID_RESPONSE.value
            ) from exc

        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            logger.warning(RecaptchaLogMessageVO.PROVIDER_INVALID_RESPONSE.value)
            raise RecaptchaProviderError(
                RecaptchaLogMessageVO.PROVIDER_INVALID_RESPONSE.value
            ) from exc

        if not isinstance(payload, Mapping):
            raise RecaptchaProviderError(
                RecaptchaLogMessageVO.PROVIDER_INVALID_RESPONSE.value
            )
        return payload

    @staticmethod
    def _to_entity(payload: Mapping[str, object]) -> RecaptchaProviderResponseEntity:
        raw_score = payload.get(RecaptchaResponseFieldVO.SCORE.value, 0.0)
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            score = 0.0

        raw_error_codes = payload.get(
            RecaptchaResponseFieldVO.ERROR_CODES.value,
            (),
        )
        if isinstance(raw_error_codes, (list, tuple)):
            error_codes = tuple(str(item) for item in raw_error_codes)
        else:
            error_codes = ()

        return RecaptchaProviderResponseEntity(
            success=payload.get(RecaptchaResponseFieldVO.SUCCESS.value) is True,
            score=score,
            action=str(payload.get(RecaptchaResponseFieldVO.ACTION.value) or "").strip(),
            hostname=str(
                payload.get(RecaptchaResponseFieldVO.HOSTNAME.value) or ""
            ).strip().lower().rstrip("."),
            challenge_timestamp=str(
                payload.get(RecaptchaResponseFieldVO.CHALLENGE_TIMESTAMP.value) or ""
            ).strip(),
            error_codes=error_codes,
        )
