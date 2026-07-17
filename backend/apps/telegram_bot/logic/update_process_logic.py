from __future__ import annotations

from backend.apps.telegram_bot.dtos.bot_update_dtos import BotUpdateProcessDTO
from backend.apps.telegram_bot.repositories.bot_runtime_repository import BotRuntimeRepository
from backend.apps.telegram_bot.repositories.update_log_repository import TelegramUpdateLogRepository


class BotUpdateProcessLogic:
    """Async idempotent update-processing use case.

    Flow:
        controller -> logic -> repositories -> adapters
    """

    def __init__(
        self,
        *,
        runtime_repository: BotRuntimeRepository,
        update_log_repository: TelegramUpdateLogRepository | None = None,
    ):
        self.runtime_repository = runtime_repository
        self.update_log_repository = update_log_repository or TelegramUpdateLogRepository()

    async def process(self, dto: BotUpdateProcessDTO) -> bool:
        update_log = None

        if dto.update_id is not None:
            update_log, created = await self.update_log_repository.get_or_create(
                provider=dto.provider,
                update_id=dto.update_id,
                payload=dto.update,
            )
            if not created and update_log.processed:
                return False

        try:
            await self.runtime_repository.process_update(dto.update)
        except Exception as exc:
            if update_log:
                await self.update_log_repository.mark_error(
                    update_log,
                    exc.__class__.__name__,
                )
            raise

        if update_log:
            await self.update_log_repository.mark_processed(update_log)

        return True
