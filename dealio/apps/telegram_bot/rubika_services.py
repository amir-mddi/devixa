from __future__ import annotations

import hashlib
import html
import os
import re
from typing import Any

import requests

from dealio.apps.telegram_bot.services import TelegramBotService
from dealio.apps.telegram_bot.repositories.logic.commerce_bot_logic import TelegramCommerceBotLogicRepository


class RubikaBotClient:
    """Rubika Bot API client compatible with the shared TelegramBotService interface.

    Rubika requests are sent to: {RUBIKA_BOT_BASE_URL}/{RUBIKA_BOT_TOKEN}/{method}.
    Required environment variables are read directly from os.environ.
    """

    CHAT_KEYPAD_TYPE_NEW = "New"
    CHAT_KEYPAD_TYPE_REMOVE = "Remove"
    BUTTON_TYPE_SIMPLE = "Simple"

    def __init__(self, token: str | None = None, base_url: str | None = None, proxy_url: str | None = None):
        self.token = (token or os.environ.get("RUBIKA_BOT_TOKEN") or "").strip()
        self.base_api_url = (base_url or os.environ.get("RUBIKA_BOT_BASE_URL") or "").strip().rstrip("/")
        self.proxy_url = (proxy_url or os.environ.get("RUBIKA_PROXY_URL") or os.environ.get("PROXY_URL") or "").strip()
        self.base_url = f"{self.base_api_url}/{self.token}" if self.token and self.base_api_url else ""

    @property
    def is_configured(self) -> bool:
        return bool(self.token and self.base_api_url)

    @property
    def proxies(self) -> dict[str, str] | None:
        if not self.proxy_url:
            return None
        return {"http": self.proxy_url, "https": self.proxy_url}

    def _request(self, method_name: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.is_configured:
            raise RuntimeError("RUBIKA_BOT_TOKEN and RUBIKA_BOT_BASE_URL are required.")

        response = requests.post(
            f"{self.base_url}/{method_name}",
            json=payload or {},
            timeout=(3.0, 20.0),
            proxies=self.proxies,
        )

        try:
            body = response.json()
        except ValueError:
            body = {"status": "ERROR", "description": response.text}

        if not response.ok or not self._is_success(body):
            raise RuntimeError(f"Rubika API error in {method_name}: {body}")

        return body

    @staticmethod
    def _is_success(body: dict[str, Any]) -> bool:
        status = str(body.get("status") or body.get("Status") or "").upper()
        return bool(body.get("ok") is True or status in {"OK", "SUCCESS"} or body.get("data") is not None)

    @staticmethod
    def _data(body: dict[str, Any]) -> dict[str, Any]:
        data = body.get("data")
        return data if isinstance(data, dict) else body

    @staticmethod
    def _plain_text(text: str) -> str:
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</p\s*>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", "", text)
        return html.unescape(text)

    @classmethod
    def _button_id(cls, button: dict[str, Any] | str) -> str:
        if isinstance(button, str):
            return button[:250]
        callback_data = button.get("callback_data") or button.get("id") or button.get("text") or "button"
        return str(callback_data)[:250]

    @classmethod
    def _button_text(cls, button: dict[str, Any] | str) -> str:
        if isinstance(button, str):
            return button
        return str(button.get("text") or button.get("button_text") or button.get("callback_data") or "")

    @classmethod
    def _convert_inline_keyboard(cls, reply_markup: dict[str, Any]) -> dict[str, Any] | None:
        inline_keyboard = reply_markup.get("inline_keyboard")
        if not isinstance(inline_keyboard, list):
            return None

        rows: list[dict[str, Any]] = []
        for row in inline_keyboard:
            buttons: list[dict[str, Any]] = []
            for button in row or []:
                buttons.append(
                    {
                        "id": cls._button_id(button),
                        "type": cls.BUTTON_TYPE_SIMPLE,
                        "button_text": cls._button_text(button),
                    }
                )
            if buttons:
                rows.append({"buttons": buttons})
        return {"rows": rows} if rows else None

    @classmethod
    def _convert_chat_keyboard(cls, reply_markup: dict[str, Any]) -> dict[str, Any] | None:
        keyboard = reply_markup.get("keyboard")
        if not isinstance(keyboard, list):
            return None

        rows: list[dict[str, Any]] = []
        for row in keyboard:
            buttons: list[dict[str, Any]] = []
            for button in row or []:
                buttons.append(
                    {
                        "id": cls._button_id(button),
                        "type": cls.BUTTON_TYPE_SIMPLE,
                        "button_text": cls._button_text(button),
                    }
                )
            if buttons:
                rows.append({"buttons": buttons})

        if not rows:
            return None

        return {
            "rows": rows,
            "resize_keyboard": bool(reply_markup.get("resize_keyboard", True)),
            "one_time_keyboard": bool(reply_markup.get("one_time_keyboard", False)),
        }

    @classmethod
    def _apply_reply_markup(cls, payload: dict[str, Any], reply_markup: dict[str, Any] | None) -> None:
        if not reply_markup:
            return

        inline_keypad = cls._convert_inline_keyboard(reply_markup)
        if inline_keypad:
            payload["inline_keypad"] = inline_keypad
            return

        chat_keypad = cls._convert_chat_keyboard(reply_markup)
        if chat_keypad:
            payload["chat_keypad_type"] = cls.CHAT_KEYPAD_TYPE_NEW
            payload["chat_keypad"] = chat_keypad

    def get_me(self) -> dict[str, Any]:
        return self._request("getMe")


    def get_file_url(self, file_id: str) -> str:
        return ""

    def send_photo(self, chat_id: int | str, photo: str, *, caption: str = "") -> dict[str, Any]:
        text = caption.strip()
        if photo:
            text = f"{text}\n{photo}".strip()
        return self.send_message(chat_id, text or photo)

    def send_video(self, chat_id: int | str, video: str, *, caption: str = "") -> dict[str, Any]:
        text = caption.strip()
        if video:
            text = f"{text}\n{video}".strip()
        return self.send_message(chat_id, text or video)

    def send_document(self, chat_id: int | str, document: str, *, caption: str = "") -> dict[str, Any]:
        text = caption.strip()
        if document:
            text = f"{text}\n{document}".strip()
        return self.send_message(chat_id, text or document)

    def edit_message_caption(self, chat_id: int | str, message_id: int | str, caption: str) -> dict[str, Any]:
        return self.edit_message_text(chat_id, message_id, caption)

    def send_message(
        self,
        chat_id: int | str,
        text: str,
        *,
        reply_markup: dict[str, Any] | None = None,
        disable_web_page_preview: bool = True,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "chat_id": str(chat_id),
            "text": self._plain_text(text),
            "disable_notification": False,
        }
        self._apply_reply_markup(payload, reply_markup)
        body = self._request("sendMessage", payload)
        data = self._data(body)
        message_id = data.get("message_id") or data.get("new_message_id")
        return {"ok": True, "result": {"message_id": message_id}, "raw": body}

    def edit_message_text(
        self,
        chat_id: int | str,
        message_id: int | str,
        text: str,
        *,
        reply_markup: dict[str, Any] | None = None,
        disable_web_page_preview: bool = True,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "chat_id": str(chat_id),
            "message_id": str(message_id),
            "text": self._plain_text(text),
        }
        body = self._request("editMessageText", payload)

        inline_keypad = self._convert_inline_keyboard(reply_markup or {})
        if inline_keypad:
            self._request(
                "editMessageKeypad",
                {"chat_id": str(chat_id), "message_id": str(message_id), "inline_keypad": inline_keypad},
            )

        return {"ok": True, "result": {"message_id": message_id}, "raw": body}

    def delete_message(self, chat_id: int | str, message_id: int | str) -> dict[str, Any]:
        body = self._request("deleteMessage", {"chat_id": str(chat_id), "message_id": str(message_id)})
        return {"ok": True, "result": True, "raw": body}

    def answer_callback_query(
        self,
        callback_query_id: str,
        *,
        text: str | None = None,
        show_alert: bool = False,
    ) -> dict[str, Any]:
        return {"ok": True, "result": True}

    def set_my_description(self, description: str, *, language_code: str | None = None) -> dict[str, Any]:
        return {"ok": True, "result": True}

    def set_my_short_description(self, short_description: str, *, language_code: str | None = None) -> dict[str, Any]:
        return {"ok": True, "result": True}

    def set_my_commands(self, commands: list[dict[str, str]], *, language_code: str | None = None) -> dict[str, Any]:
        bot_commands = [
            {"command": item["command"].lstrip("/"), "description": item["description"]}
            for item in commands
        ]
        body = self._request("setCommands", {"bot_commands": bot_commands})
        return {"ok": True, "result": True, "raw": body}

    def update_bot_endpoint(self, *, url: str, endpoint_type: str) -> dict[str, Any]:
        body = self._request("updateBotEndpoints", {"url": url, "type": endpoint_type})
        return {"ok": True, "result": True, "raw": body}

    def get_updates(
        self,
        *,
        offset_id: str | None = None,
        limit: int | None = None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        limit_value = limit if limit is not None else int(os.environ["RUBIKA_POLLING_LIMIT"])
        payload: dict[str, Any] = {"limit": limit_value}
        if offset_id:
            payload["offset_id"] = offset_id
        body = self._request("getUpdates", payload)
        data = self._data(body)
        updates = data.get("updates") or body.get("updates") or []
        next_offset_id = data.get("next_offset_id") or body.get("next_offset_id")
        return updates if isinstance(updates, list) else [], next_offset_id


class RubikaUpdateNormalizer:
    PRIVATE_CHAT_TYPE = "private"

    @classmethod
    def normalize(cls, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            return {}

        if "callback_query" in payload or "message" in payload:
            return payload

        inline_message = payload.get("inline_message")
        if isinstance(inline_message, dict):
            return cls._normalize_inline_message(inline_message)

        update = payload.get("update") if isinstance(payload.get("update"), dict) else payload
        if isinstance(update, dict):
            update_type = update.get("type") or update.get("update_type")
            if update_type in {"NewMessage", "UpdatedMessage", "Message"} or "new_message" in update:
                return cls._normalize_message_update(update)

        return {}

    @classmethod
    def update_log_id(cls, payload: dict[str, Any]) -> int | None:
        raw_id = cls.raw_update_id(payload)
        if raw_id is None:
            return None
        try:
            return int(str(raw_id))
        except (TypeError, ValueError):
            digest = hashlib.sha256(str(raw_id).encode("utf-8")).hexdigest()[:15]
            return int(digest, 16)

    @classmethod
    def raw_update_id(cls, payload: dict[str, Any]) -> str | int | None:
        if not isinstance(payload, dict):
            return None

        if payload.get("update_id") is not None:
            return payload.get("update_id")

        inline_message = payload.get("inline_message") if isinstance(payload.get("inline_message"), dict) else None
        if inline_message:
            return ":".join(
                str(part)
                for part in [
                    inline_message.get("chat_id"),
                    inline_message.get("message_id"),
                    (inline_message.get("aux_data") or {}).get("button_id") or inline_message.get("text"),
                ]
                if part is not None
            )

        update = payload.get("update") if isinstance(payload.get("update"), dict) else payload
        if not isinstance(update, dict):
            return None
        message = update.get("new_message") or update.get("message") or update.get("updated_message") or {}
        if not isinstance(message, dict):
            return None
        return ":".join(
            str(part)
            for part in [update.get("chat_id"), message.get("message_id"), message.get("time")]
            if part is not None
        )

    @classmethod
    def _normalize_message_update(cls, update: dict[str, Any]) -> dict[str, Any]:
        message = update.get("new_message") or update.get("message") or update.get("updated_message") or {}
        if not isinstance(message, dict):
            return {}

        chat_id = update.get("chat_id") or message.get("chat_id")
        sender_id = message.get("sender_id") or update.get("sender_id") or chat_id
        aux_data = message.get("aux_data") if isinstance(message.get("aux_data"), dict) else {}
        text = message.get("text") or aux_data.get("button_id") or ""

        return {
            "update_id": cls.update_log_id(update),
            "message": {
                "message_id": cls._int_or_original(message.get("message_id")),
                "text": text,
                "chat": {"id": cls._int_or_original(chat_id), "type": cls.PRIVATE_CHAT_TYPE},
                "from": {
                    "id": cls._int_or_original(sender_id),
                    "username": "",
                    "first_name": "",
                    "last_name": "",
                    "language_code": "fa",
                },
            },
            "raw_rubika_update": update,
        }

    @classmethod
    def _normalize_inline_message(cls, inline_message: dict[str, Any]) -> dict[str, Any]:
        chat_id = inline_message.get("chat_id")
        sender_id = inline_message.get("sender_id") or chat_id
        aux_data = inline_message.get("aux_data") if isinstance(inline_message.get("aux_data"), dict) else {}
        callback_data = aux_data.get("button_id") or inline_message.get("text") or ""
        message_id = inline_message.get("message_id")
        callback_query_id = ":".join(str(part) for part in [chat_id, message_id, callback_data] if part is not None)

        return {
            "update_id": cls.update_log_id({"inline_message": inline_message}),
            "callback_query": {
                "id": callback_query_id,
                "data": callback_data,
                "from": {
                    "id": cls._int_or_original(sender_id),
                    "username": "",
                    "first_name": "",
                    "last_name": "",
                    "language_code": "fa",
                },
                "message": {
                    "message_id": cls._int_or_original(message_id),
                    "chat": {"id": cls._int_or_original(chat_id), "type": cls.PRIVATE_CHAT_TYPE},
                },
            },
            "raw_rubika_inline_message": inline_message,
        }

    @staticmethod
    def _int_or_original(value: Any) -> Any:
        try:
            return int(value)
        except (TypeError, ValueError):
            return value


class RubikaCommerceBotLogicRepository(TelegramCommerceBotLogicRepository):
    @staticmethod
    def default_payment_provider() -> str:
        provider = os.environ.get("RUBIKA_PAYMENT_PROVIDER")
        if not provider:
            raise RuntimeError("RUBIKA_PAYMENT_PROVIDER is required.")
        return provider


class RubikaBotService(TelegramBotService):
    MESSENGER_PROVIDER = "rubika"
    CACHE_PREFIX = "rubika"

    def __init__(self, client: RubikaBotClient | None = None):
        super().__init__(client=client or RubikaBotClient())
        self.commerce_logic = RubikaCommerceBotLogicRepository()

    @staticmethod
    def web_app_url() -> str:
        return os.environ.get("RUBIKA_WEBAPP_URL") or ""

    def handle_update(self, update: dict[str, Any]) -> None:
        normalized_update = RubikaUpdateNormalizer.normalize(update)
        if normalized_update:
            super().handle_update(normalized_update)
