from __future__ import annotations

from collections.abc import Mapping

from asgiref.sync import async_to_sync
import httpx
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
    """Async Google reCAPTCHA v3 transport adapter.

    ``verify_async`` is the native contract used by ASGI workflows. ``verify``
    exists only as a compatibility boundary for the project's synchronous HTML
    form views and legacy tests.
    """

    def verify(self, dto: RecaptchaVerificationDTO) -> RecaptchaProviderResponseEntity:
        return async_to_sync(self.verify_async)(dto)

    async def verify_async(
        self,
        dto: RecaptchaVerificationDTO,
    ) -> RecaptchaProviderResponseEntity:
        payload = {
            RecaptchaRequestFieldVO.SECRET.value: settings.RECAPTCHA_SECRET_KEY,
            RecaptchaRequestFieldVO.RESPONSE.value: dto.token,
        }
        if settings.RECAPTCHA_SEND_REMOTE_IP and dto.remote_ip:
            payload[RecaptchaRequestFieldVO.REMOTE_IP.value] = dto.remote_ip

        response_payload = await self._post_json(payload)
        return self._to_entity(response_payload)

    @staticmethod
    async def _post_json(payload: Mapping[str, object]) -> Mapping[str, object]:
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
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(timeout),
                follow_redirects=False,
            ) as client:
                async with client.stream(
                    "POST",
                    RecaptchaEndpointVO.SITE_VERIFY.value,
                    data=dict(payload),
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/x-www-form-urlencoded",
                        "User-Agent": "Devixa-reCAPTCHA/1.0",
                    },
                ) as response:
                    response.raise_for_status()
                    content_length = response.headers.get("Content-Length")
                    try:
                        declared_size = int(content_length) if content_length else 0
                    except (TypeError, ValueError):
                        declared_size = 0
                    if declared_size > max_bytes:
                        raise RecaptchaProviderError(
                            RecaptchaLogMessageVO.PROVIDER_INVALID_RESPONSE.value
                        )

                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body) > max_bytes:
                            raise RecaptchaProviderError(
                                RecaptchaLogMessageVO.PROVIDER_INVALID_RESPONSE.value
                            )
        except httpx.HTTPStatusError as exc:
            logger.warning(
                RecaptchaLogMessageVO.PROVIDER_HTTP_ERROR.value.format(
                    status=exc.response.status_code
                )
            )
            raise RecaptchaProviderError(
                RecaptchaLogMessageVO.PROVIDER_INVALID_RESPONSE.value
            ) from exc
        except (httpx.TimeoutException, httpx.NetworkError, httpx.ProtocolError) as exc:
            logger.warning(
                RecaptchaLogMessageVO.PROVIDER_CONNECTION_ERROR.value.format(error=exc)
            )
            raise RecaptchaProviderError(
                RecaptchaLogMessageVO.PROVIDER_INVALID_RESPONSE.value
            ) from exc

        try:
            parsed = httpx.Response(200, content=bytes(body)).json()
        except ValueError as exc:
            logger.warning(RecaptchaLogMessageVO.PROVIDER_INVALID_RESPONSE.value)
            raise RecaptchaProviderError(
                RecaptchaLogMessageVO.PROVIDER_INVALID_RESPONSE.value
            ) from exc

        if not isinstance(parsed, Mapping):
            raise RecaptchaProviderError(
                RecaptchaLogMessageVO.PROVIDER_INVALID_RESPONSE.value
            )
        return parsed

    @staticmethod
    def _to_entity(payload: Mapping[str, object]) -> RecaptchaProviderResponseEntity:
        raw_score = payload.get(RecaptchaResponseFieldVO.SCORE.value, 0.0)
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            score = 0.0

        raw_error_codes = payload.get(RecaptchaResponseFieldVO.ERROR_CODES.value, ())
        if isinstance(raw_error_codes, (list, tuple)):
            error_codes = tuple(str(item) for item in raw_error_codes)
        else:
            error_codes = ()

        return RecaptchaProviderResponseEntity(
            success=payload.get(RecaptchaResponseFieldVO.SUCCESS.value) is True,
            score=score,
            action=str(payload.get(RecaptchaResponseFieldVO.ACTION.value) or "").strip(),
            hostname=str(payload.get(RecaptchaResponseFieldVO.HOSTNAME.value) or "")
            .strip()
            .lower()
            .rstrip("."),
            challenge_timestamp=str(
                payload.get(RecaptchaResponseFieldVO.CHALLENGE_TIMESTAMP.value) or ""
            ).strip(),
            error_codes=error_codes,
        )
