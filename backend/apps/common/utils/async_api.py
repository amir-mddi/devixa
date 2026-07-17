from __future__ import annotations

from asgiref.sync import sync_to_async
from adrf.views import APIView as ADRFAPIView


class AsyncAPIView(ADRFAPIView):
    """ADRF APIView compatible with Django 5.2's uniform-handler check."""

    async def dispatch(self, request, *args, **kwargs):
        return await self.async_dispatch(request, *args, **kwargs)

    async def options(self, request, *args, **kwargs):
        return await sync_to_async(
            super().options,
            thread_sensitive=True,
        )(request, *args, **kwargs)
