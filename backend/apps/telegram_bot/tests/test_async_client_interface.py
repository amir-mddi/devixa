from __future__ import annotations

from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

from backend.apps.telegram_bot.interfaces.bot_client_interface import (
    AsyncBotClientInterface,
)
from backend.apps.telegram_bot.repositories.adapters.telegram_api_adapter import (
    TelegramApiAdapter,
)


class TelegramAsyncClientContractTests(IsolatedAsyncioTestCase):
    async def test_core_message_methods_use_async_transport(self):
        client = TelegramApiAdapter(token="test-token")
        client.arequest = AsyncMock(return_value={"ok": True, "result": {}})

        await client.asend_message(1, "hello")
        await client.aedit_message_text(1, 2, "updated")
        await client.adelete_message(1, 2)
        await client.aanswer_callback_query("callback-id")

        self.assertIsInstance(client, AsyncBotClientInterface)
        self.assertEqual(client.arequest.await_count, 4)
