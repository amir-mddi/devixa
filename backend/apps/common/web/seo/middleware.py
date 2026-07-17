from __future__ import annotations

import os

from backend.apps.common.utils.async_middleware import AsyncCompatibleMiddleware
from backend.apps.common.web.seo.enums.seo_enums import SeoRobotsDirectiveEnum
from backend.apps.common.web.seo.value_objects.seo_vo import SeoNoIndexPathVO


class SeoRobotsHeaderMiddleware(AsyncCompatibleMiddleware):
    """Add an X-Robots-Tag to private and machine-only endpoints."""

    def __init__(self, get_response):
        super().__init__(get_response)
        admin_path = "/" + os.environ.get("ADMIN_PANEL_URL", "admin/").strip("/") + "/"
        configured_paths = tuple(item.value for item in SeoNoIndexPathVO)
        self._noindex_prefixes = tuple(dict.fromkeys((admin_path, *configured_paths)))

    def _apply_header(self, request, response):
        if (
            request.path.startswith(self._noindex_prefixes)
            and "X-Robots-Tag" not in response
        ):
            response["X-Robots-Tag"] = SeoRobotsDirectiveEnum.NOINDEX.value
        return response

    def process_sync(self, request):
        return self._apply_header(request, self.get_response(request))

    async def process_async(self, request):
        return self._apply_header(request, await self.get_response(request))
