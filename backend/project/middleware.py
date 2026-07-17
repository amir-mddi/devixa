from __future__ import annotations

import time

from django.conf import settings

from backend.apps.common.utils.async_middleware import AsyncCompatibleMiddleware
from backend.apps.core_models.constants.common_vo import ExcludeViewResponseVO
from backend.project.db_routing import clear_force_primary_reads, force_primary_reads


class PrimaryAfterWriteMiddleware(AsyncCompatibleMiddleware):
    unsafe_methods = {"POST", "PUT", "PATCH", "DELETE"}

    def __init__(self, get_response):
        super().__init__(get_response)
        self.ttl = getattr(settings, "READ_AFTER_WRITE_PRIMARY_SECONDS", 5)

    def _prepare(self, request):
        if not request.path.startswith(f"{ExcludeViewResponseVO.api_urls_include}"):
            return None

        cookie_name = "primary_replica_read_priority_" + request.path
        clear_force_primary_reads()
        now = int(time.time())
        primary_until = request.COOKIES.get(cookie_name)

        if primary_until:
            try:
                if int(primary_until) > now:
                    force_primary_reads()
            except ValueError:
                pass
        return cookie_name, now

    def _finalize(self, request, response, state):
        try:
            if state and request.method.upper() in self.unsafe_methods:
                cookie_name, now = state
                response.set_cookie(
                    cookie_name,
                    str(now + self.ttl),
                    max_age=self.ttl,
                    httponly=True,
                    secure=not settings.DEBUG,
                    samesite="Lax",
                )
            return response
        finally:
            if state:
                clear_force_primary_reads()

    def process_sync(self, request):
        state = self._prepare(request)
        try:
            response = self.get_response(request)
        except Exception:
            if state:
                clear_force_primary_reads()
            raise
        return self._finalize(request, response, state)

    async def process_async(self, request):
        state = self._prepare(request)
        try:
            response = await self.get_response(request)
        except Exception:
            if state:
                clear_force_primary_reads()
            raise
        return self._finalize(request, response, state)
