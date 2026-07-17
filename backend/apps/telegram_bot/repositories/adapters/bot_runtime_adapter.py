from __future__ import annotations

from collections.abc import Callable
from typing import Any

from backend.apps.common.async_utils import call_maybe_async


class BotRuntimeAdapter:
    """Execute a concrete bot runtime behind an async application boundary."""

    def __init__(self, service_factory: Callable[[], Any]):
        self.service_factory = service_factory

    async def process_update(self, update: dict[str, Any]) -> None:
        service = self.service_factory()
        await call_maybe_async(service.handle_update, update)
