from __future__ import annotations

from typing import Any, Callable


class BotRuntimeAdapter:
    """Adapter that executes the concrete bot runtime/service.

    The application logic depends on this adapter instead of importing a concrete
    Telegram/Bale/Rubika service in controllers or webhook views.
    """

    def __init__(self, service_factory: Callable[[], Any]):
        self.service_factory = service_factory

    def process_update(self, update: dict[str, Any]) -> None:
        self.service_factory().handle_update(update)
