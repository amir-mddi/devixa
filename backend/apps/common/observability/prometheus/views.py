from __future__ import annotations

import hmac
import ipaddress

from asgiref.sync import sync_to_async
from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseServerError
from django.views.decorators.cache import never_cache
from prometheus_client import CONTENT_TYPE_LATEST

from backend.apps.common.utils.common_utils import CommonUtils

from .exporter import render_metrics
from .metrics import get_metrics
from .value_objects import PrometheusContentVO, PrometheusHeaderVO


def _extract_token(request) -> str:
    token = request.headers.get(PrometheusHeaderVO.TOKEN, "").strip()
    authorization = request.headers.get(PrometheusHeaderVO.AUTHORIZATION, "")
    if authorization.startswith(PrometheusHeaderVO.BEARER_PREFIX):
        token = authorization.removeprefix(PrometheusHeaderVO.BEARER_PREFIX).strip()
    return token


def _ip_is_allowed(client_ip: str | None, allowed_values: tuple[str, ...]) -> bool:
    if not client_ip:
        return False
    try:
        address = ipaddress.ip_address(client_ip)
    except ValueError:
        return False

    for value in allowed_values:
        try:
            if address in ipaddress.ip_network(value, strict=False):
                return True
        except ValueError:
            continue
    return False


def _is_authorized(request) -> bool:
    config = settings.PROMETHEUS_CONFIG
    if not config.require_auth:
        return True

    expected_token = config.metrics_token
    provided_token = _extract_token(request)
    if expected_token and hmac.compare_digest(provided_token, expected_token):
        return True

    client_ip = CommonUtils.get_client_ip(request)
    return _ip_is_allowed(client_ip, tuple(config.metrics_allowed_ips))


@never_cache
async def prometheus_metrics(request):
    if request.method != "GET" or not settings.PROMETHEUS_ENABLED:
        raise Http404
    if not _is_authorized(request):
        # Return 404 instead of revealing that a monitoring endpoint exists.
        raise Http404

    # Register project collectors even when the first request is a scrape.
    get_metrics()

    try:
        payload = await sync_to_async(
            render_metrics,
            thread_sensitive=False,
        )()
    except Exception:
        return HttpResponseServerError(
            PrometheusContentVO.UNAVAILABLE,
            content_type="text/plain; charset=utf-8",
        )

    response = HttpResponse(payload, content_type=CONTENT_TYPE_LATEST)
    response["Cache-Control"] = PrometheusHeaderVO.CACHE_CONTROL
    response["X-Content-Type-Options"] = "nosniff"
    return response
