import time

from django.conf import settings

from backend.apps.core_models.constants.common_vo import ExcludeViewResponseVO
from backend.project.db_routing import (
    clear_force_primary_reads,
    force_primary_reads,
)


class PrimaryAfterWriteMiddleware:
    unsafe_methods = {"POST", "PUT", "PATCH", "DELETE"}

    def __init__(self, get_response):
        self.get_response = get_response
        self.ttl = getattr(settings, "READ_AFTER_WRITE_PRIMARY_SECONDS", 5)

    def __call__(self, request):
        if request.path.startswith(f"{ExcludeViewResponseVO.api_urls_include}"):

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

            response = self.get_response(request)

            if request.method.upper() in self.unsafe_methods:
                response.set_cookie(
                    cookie_name,
                    str(now + self.ttl),
                    max_age=self.ttl,
                    httponly=True,
                    secure=not settings.DEBUG,
                    samesite="Lax",
                )

            clear_force_primary_reads()

        else:
            response = self.get_response(request)

        return response