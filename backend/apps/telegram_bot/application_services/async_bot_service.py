from __future__ import annotations

from typing import Any

from asgiref.sync import sync_to_async


class AsyncBotService:
    """Event-loop-safe façade for the existing conversation coordinator.

    The legacy coordinator still contains synchronous Django workflows. Running
    one complete update in a regular worker thread keeps its transactions and
    in-memory call stack together while allowing independent webhook requests to
    execute concurrently through ASGI's bounded thread pool.

    New bot features should be implemented as native async use cases and may be
    injected behind the same ``handle_update`` contract. This façade is only the
    compatibility boundary for workflows that have not yet been decomposed.
    """

    def __init__(self, service: Any):
        self._service = service

    @property
    def service(self) -> Any:
        return self._service

    async def handle_update(self, update: dict[str, Any]) -> None:
        await sync_to_async(
            self._service.handle_update,
            thread_sensitive=False,
        )(update)
