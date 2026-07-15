from __future__ import annotations

from django.utils.cache import patch_vary_headers

from backend.apps.common.web.performance.logic.cache_policy_logic import (
    PublicPageCachePolicyLogic,
)


class PublicPageCachePolicyMiddleware:
    """Keep public HTML bfcache-friendly while preserving per-user rendering."""

    def __init__(self, get_response):
        self._get_response = get_response
        self._logic = PublicPageCachePolicyLogic()

    def __call__(self, request):
        response = self._get_response(request)
        policy = self._logic.cache_control_for(
            path=request.path,
            method=request.method,
            content_type=response.get("Content-Type", ""),
        )
        if policy and response.status_code == 200:
            response["Cache-Control"] = policy
            patch_vary_headers(response, ("Cookie",))
        return response
