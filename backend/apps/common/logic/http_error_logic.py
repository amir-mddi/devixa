from __future__ import annotations

from django.conf import settings

from backend.apps.common.dtos.http_error_dto import HttpErrorDTO
from backend.apps.common.vo.http_error_vo import HttpErrorCodeVO, HttpErrorTextVO


class RateLimitErrorLogic:
    @staticmethod
    def exceeded(*, waiting_time: int) -> HttpErrorDTO:
        normalized_wait = max(1, int(waiting_time))
        return HttpErrorDTO(
            code=HttpErrorCodeVO.RATE_LIMIT_EXCEEDED,
            title=HttpErrorTextVO.RATE_LIMIT_TITLE,
            message=HttpErrorTextVO.RATE_LIMIT_MESSAGE.format(
                waiting_time=normalized_wait,
            ),
            status_code=429,
            retry_after_seconds=normalized_wait,
        )

    @staticmethod
    def client_unknown(*, waiting_time: int) -> HttpErrorDTO:
        return HttpErrorDTO(
            code=HttpErrorCodeVO.RATE_LIMIT_CLIENT_UNKNOWN,
            title=HttpErrorTextVO.RATE_LIMIT_CLIENT_UNKNOWN_TITLE,
            message=HttpErrorTextVO.RATE_LIMIT_CLIENT_UNKNOWN_MESSAGE,
            status_code=400,
            retry_after_seconds=max(1, int(waiting_time)),
        )


class CsrfFailureErrorLogic:
    @classmethod
    def from_reason(cls, reason: str | None) -> HttpErrorDTO:
        raw_reason = str(reason or "").strip()
        normalized = raw_reason.lower()

        if "origin checking failed" in normalized or "trusted origins" in normalized:
            code = HttpErrorCodeVO.CSRF_ORIGIN_REJECTED
            message = HttpErrorTextVO.CSRF_ORIGIN_MESSAGE
        elif "referer checking failed" in normalized or "referer" in normalized:
            code = HttpErrorCodeVO.CSRF_REFERER_REJECTED
            message = HttpErrorTextVO.CSRF_REFERER_MESSAGE
        elif "csrf cookie not set" in normalized or "cookie" in normalized:
            code = HttpErrorCodeVO.CSRF_COOKIE_MISSING
            message = HttpErrorTextVO.CSRF_COOKIE_MISSING_MESSAGE
        elif "csrf token missing" in normalized or "token missing" in normalized:
            code = HttpErrorCodeVO.CSRF_TOKEN_MISSING
            message = HttpErrorTextVO.CSRF_TOKEN_MISSING_MESSAGE
        elif any(
            marker in normalized
            for marker in (
                "incorrect length",
                "invalid characters",
                "token from post",
                "token from the 'x-csrftoken'",
                "csrf token",
            )
        ):
            code = HttpErrorCodeVO.CSRF_TOKEN_INVALID
            message = HttpErrorTextVO.CSRF_TOKEN_INVALID_MESSAGE
        else:
            code = HttpErrorCodeVO.CSRF_VALIDATION_FAILED
            message = HttpErrorTextVO.CSRF_GENERIC_MESSAGE

        return HttpErrorDTO(
            code=code,
            title=HttpErrorTextVO.CSRF_TITLE,
            message=message,
            status_code=403,
            technical_detail=raw_reason if settings.DEBUG else "",
        )
