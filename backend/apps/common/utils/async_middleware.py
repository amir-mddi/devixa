from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from asgiref.sync import iscoroutinefunction, markcoroutinefunction


class AsyncCompatibleMiddleware(ABC):
    """Base class for middleware that preserves sync and ASGI async execution.

    Django adapts a middleware chain to synchronous execution when a custom
    middleware only exposes a synchronous ``__call__``.  This base keeps the
    selected request path native: synchronous servers call ``process_sync`` and
    ASGI servers await ``process_async``.
    """

    sync_capable = True
    async_capable = True

    def __init__(self, get_response):
        self.get_response = get_response
        self._is_async = iscoroutinefunction(get_response)
        if self._is_async:
            markcoroutinefunction(self)

    def __call__(self, request):
        if self._is_async:
            return self.process_async(request)
        return self.process_sync(request)

    @abstractmethod
    def process_sync(self, request):
        raise NotImplementedError

    @abstractmethod
    async def process_async(self, request):
        raise NotImplementedError

    @staticmethod
    def response_status(response: Any) -> int | None:
        return getattr(response, "status_code", None)
