from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable


class BotClientInterface(ABC):
    """Synchronous compatibility contract used by legacy bot workflows."""

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def send_message(
        self,
        chat_id: str | int,
        text: str,
        *,
        reply_markup: dict[str, Any] | None = None,
        disable_web_page_preview: bool = True,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def edit_message_text(
        self,
        chat_id: str | int,
        message_id: int,
        text: str,
        *,
        reply_markup: dict[str, Any] | None = None,
        disable_web_page_preview: bool = True,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def delete_message(
        self,
        chat_id: str | int,
        message_id: int,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_updates(self, **kwargs: Any):
        raise NotImplementedError


@runtime_checkable
class AsyncBotClientInterface(Protocol):
    """Native async contract for new controllers and use cases.

    Implementations keep Telegram/Bale/Rubika transport details outside domain
    logic. The protocol is structural so test doubles do not need inheritance.
    """

    @property
    def is_configured(self) -> bool: ...

    async def asend_message(
        self,
        chat_id: str | int,
        text: str,
        *,
        reply_markup: dict[str, Any] | None = None,
        disable_web_page_preview: bool = True,
    ) -> dict[str, Any]: ...

    async def aedit_message_text(
        self,
        chat_id: str | int,
        message_id: int,
        text: str,
        *,
        reply_markup: dict[str, Any] | None = None,
        disable_web_page_preview: bool = True,
    ) -> dict[str, Any]: ...

    async def adelete_message(
        self,
        chat_id: str | int,
        message_id: int,
    ) -> dict[str, Any]: ...

    async def aanswer_callback_query(
        self,
        callback_query_id: str,
        *,
        text: str | None = None,
        show_alert: bool = False,
    ) -> dict[str, Any]: ...

    async def aget_updates(self, **kwargs: Any) -> list[dict[str, Any]]: ...
