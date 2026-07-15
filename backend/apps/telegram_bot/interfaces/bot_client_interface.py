from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BotClientInterface(ABC):
    @property
    @abstractmethod
    def is_configured(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def send_message(self, chat_id: str | int, text: str, *, reply_markup: dict[str, Any] | None = None, disable_web_page_preview: bool = True) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def edit_message_text(self, chat_id: str | int, message_id: int, text: str, *, reply_markup: dict[str, Any] | None = None, disable_web_page_preview: bool = True) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def delete_message(self, chat_id: str | int, message_id: int) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_updates(self, **kwargs: Any):
        raise NotImplementedError
