from __future__ import annotations

from django.conf import settings
from django.http import Http404, JsonResponse
from django.views.decorators.cache import never_cache

from .logic import HealthCheckLogic
from .value_objects import HealthResponseVO


def _response(payload: dict[str, object], *, status: int) -> JsonResponse:
    response = JsonResponse(payload, status=status)
    response["Cache-Control"] = HealthResponseVO.CACHE_CONTROL
    response["X-Content-Type-Options"] = "nosniff"
    return response


@never_cache
async def liveness(request):
    if request.method != "GET" or not settings.HEALTH_CHECKS_ENABLED:
        raise Http404
    return _response({"status": HealthResponseVO.LIVE_STATUS}, status=200)


@never_cache
async def readiness(request):
    if request.method != "GET" or not settings.HEALTH_CHECKS_ENABLED:
        raise Http404

    report = await HealthCheckLogic().readiness()
    return _response(
        report.as_public_dict(),
        status=200 if report.healthy else 503,
    )
