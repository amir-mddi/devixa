from __future__ import annotations

from http import HTTPStatus

from django.conf import settings
from django.http import Http404
from django.urls import Resolver404

from backend.apps.common.dtos.http_error_dto import HttpErrorDTO
from backend.apps.common.vo.http_error_vo import HttpErrorCodeVO, HttpErrorTextVO


class NotFoundErrorLogic:
    """Build a safe browser/API 404 presentation for missing routes and objects."""

    MAX_PUBLIC_MESSAGE_LENGTH = 240

    @classmethod
    def from_exception(cls, exception: Exception | None) -> HttpErrorDTO:
        message = cls._public_message(exception)
        return HttpErrorDTO(
            code=HttpErrorCodeVO.NOT_FOUND,
            title=HttpErrorTextVO.NOT_FOUND_TITLE,
            message=message,
            status_code=HTTPStatus.NOT_FOUND.value,
        )

    @classmethod
    def _public_message(cls, exception: Exception | None) -> str:
        if exception is None or isinstance(exception, Resolver404):
            return HttpErrorTextVO.NOT_FOUND_MESSAGE

        if not isinstance(exception, Http404):
            return HttpErrorTextVO.NOT_FOUND_MESSAGE

        candidate = str(exception).strip()
        if not cls._is_safe_public_message(candidate):
            return HttpErrorTextVO.NOT_FOUND_OBJECT_MESSAGE
        return candidate

    @classmethod
    def _is_safe_public_message(cls, value: str) -> bool:
        if not value or len(value) > cls.MAX_PUBLIC_MESSAGE_LENGTH:
            return False
        if any(character in value for character in ("<", ">", "\n", "\r")):
            return False

        normalized = value.lower()
        technical_markers = (
            "resolver404",
            "tried",
            "url_patterns",
            "no ",
            " matches the given query",
            "doesnotexist",
            "queryset",
        )
        return not any(marker in normalized for marker in technical_markers)


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
