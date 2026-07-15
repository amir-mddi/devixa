from __future__ import annotations

from django.conf import settings

from backend.apps.common.web.security.adapters.nonce_adapter import SecurityNonceAdapter
from backend.apps.common.web.security.logic.content_security_policy_logic import (
    ContentSecurityPolicyLogic,
)
from backend.apps.common.web.security.value_objects.security_header_vo import SecurityHeaderVO


class SecurityHeadersMiddleware:
    """Attach security policies without leaking presentation rules into views."""

    def __init__(self, get_response):
        self._get_response = get_response
        self._nonce_adapter = SecurityNonceAdapter()
        self._policy_logic = ContentSecurityPolicyLogic()

    def __call__(self, request):
        nonce = self._nonce_adapter.generate()
        request.csp_nonce = nonce
        response = self._get_response(request)

        self._set_default_headers(response)

        if not getattr(settings, "CONTENT_SECURITY_POLICY_ENABLED", False):
            return response

        policy = self._policy_logic.build(
            nonce,
            is_production=getattr(settings, "IS_PROD", False),
        )
        header_name = (
            SecurityHeaderVO.CSP_REPORT_ONLY_HEADER
            if getattr(settings, "CONTENT_SECURITY_POLICY_REPORT_ONLY", False)
            else SecurityHeaderVO.CSP_HEADER
        )
        response[header_name] = policy
        return response

    @staticmethod
    def _set_default_headers(response) -> None:
        for header_name, header_value in SecurityHeaderVO.DEFAULT_HEADERS:
            if header_name not in response:
                response[header_name] = header_value
