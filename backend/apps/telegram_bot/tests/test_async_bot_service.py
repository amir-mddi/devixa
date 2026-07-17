from __future__ import annotations

import asyncio
import threading
from unittest import IsolatedAsyncioTestCase

from backend.apps.telegram_bot.application_services.async_bot_service import (
    AsyncBotService,
)


class AsyncBotServiceTests(IsolatedAsyncioTestCase):
    async def test_sync_coordinator_does_not_block_event_loop(self):
        entered = threading.Event()
        release = threading.Event()

        class BlockingCoordinator:
            def handle_update(self, update):
                entered.set()
                release.wait(timeout=1)

        service = AsyncBotService(BlockingCoordinator())
        task = asyncio.create_task(service.handle_update({"update_id": 1}))

        for _ in range(100):
            if entered.is_set():
                break
            await asyncio.sleep(0.001)

        self.assertTrue(entered.is_set())
        self.assertFalse(task.done())

        # This coroutine can still run while the legacy coordinator is blocked.
        await asyncio.sleep(0)
        release.set()
        await asyncio.wait_for(task, timeout=1)
