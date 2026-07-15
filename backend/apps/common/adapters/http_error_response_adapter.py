from __future__ import annotations

from django.http import JsonResponse
from django.shortcuts import render
from django.utils.cache import patch_vary_headers

from backend.apps.common.dtos.http_error_dto import HttpErrorDTO
from backend.apps.common.logic.request_format_logic import RequestFormatLogic


class HttpErrorResponseAdapter:
    template_name = "web/errors/http_error.html"

    @classmethod
    def build(cls, *, request, error: HttpErrorDTO, view=None):
        if RequestFormatLogic.wants_json(request):
            response = cls._build_json(error)
        else:
            resolved_view = view or cls._resolve_view(request)
            custom_handler = getattr(resolved_view, "handle_http_error_response", None)
            if callable(custom_handler):
                response = custom_handler(error)
            else:
                response = render(
                    request,
                    cls.template_name,
                    {"http_error": error},
                    status=error.status_code,
                )

        cls._apply_headers(response=response, error=error)
        return response

    @staticmethod
    def _resolve_view(request):
        resolver_match = getattr(request, "resolver_match", None)
        view_class = getattr(getattr(resolver_match, "func", None), "view_class", None)
        if view_class is None:
            return None

        view = view_class()
        setup = getattr(view, "setup", None)
        if callable(setup):
            setup(
                request,
                *(getattr(resolver_match, "args", ()) or ()),
                **(getattr(resolver_match, "kwargs", {}) or {}),
            )
        return view

    @staticmethod
    def _build_json(error: HttpErrorDTO) -> JsonResponse:
        payload = {
            "code": error.code,
            "detail": error.message,
        }
        if error.retry_after_seconds is not None:
            payload["waiting_time"] = error.retry_after_seconds
        if error.technical_detail:
            payload["technical_detail"] = error.technical_detail

        return JsonResponse(payload, status=error.status_code)

    @staticmethod
    def _apply_headers(*, response, error: HttpErrorDTO) -> None:
        response["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        if error.retry_after_seconds is not None:
            response["Retry-After"] = str(error.retry_after_seconds)
        patch_vary_headers(response, ("Accept",))
