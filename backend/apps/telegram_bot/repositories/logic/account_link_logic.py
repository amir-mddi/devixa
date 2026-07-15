from __future__ import annotations

import json
from typing import Any, Callable

from backend.apps.accounts.repositories.adapters.verification_code_cache_adapter import (
    VerificationCodeCacheAdapter,
)
from backend.apps.core_models.dtos.sms_providers.kavenegar_params_dto import (
    KavenegarTemplateSmsDTO,
)
from backend.apps.core_models.vo.common_vo import KavenegarVo
from backend.apps.shared.repositories.logic import SharedApplicationLogic
from backend.apps.telegram_bot.dtos.account_link_dtos import (
    BotAccountLinkDispatchResultDTO,
    ConfirmBotAccountLinkCodeDTO,
    SendBotAccountLinkCodeDTO,
)
from backend.apps.telegram_bot.repositories.adapters.account_link_email_adapter import (
    BotAccountLinkEmailAdapter,
)
from backend.apps.telegram_bot.repositories.adapters.account_link_postgres_adapter import (
    BotAccountLinkPostgresAdapter,
)
from backend.apps.telegram_bot.repositories.bot_cache_repository import (
    TelegramBotCacheRepository,
)
from backend.apps.telegram_bot.vo.account_link_vo import (
    BotAccountLinkMethodVO,
    BotAccountLinkVO,
)


class BotAccountLinkLogicRepository:
    def __init__(
        self,
        *,
        postgres_adapter: BotAccountLinkPostgresAdapter | None = None,
        email_adapter: BotAccountLinkEmailAdapter | None = None,
        cache_repository: TelegramBotCacheRepository | None = None,
        verification_code_cache: VerificationCodeCacheAdapter | None = None,
        shared_logic: SharedApplicationLogic | None = None,
    ) -> None:
        self.postgres_adapter = postgres_adapter or BotAccountLinkPostgresAdapter()
        self.email_adapter = email_adapter or BotAccountLinkEmailAdapter()
        self.cache_repository = cache_repository or TelegramBotCacheRepository()
        self.verification_code_cache = (
            verification_code_cache or VerificationCodeCacheAdapter()
        )
        self.shared_logic = shared_logic or SharedApplicationLogic()

    def send_code_by_email(
        self,
        dto: SendBotAccountLinkCodeDTO,
    ) -> BotAccountLinkDispatchResultDTO:
        user = self.postgres_adapter.find_active_user_by_email(dto.identifier)
        if not user:
            return BotAccountLinkDispatchResultDTO.account_missing()
        return self._issue_and_dispatch_code(
            dto=dto,
            user=user,
            method=BotAccountLinkMethodVO.EMAIL,
            dispatcher=lambda code: self.email_adapter.send_code(
                user=user,
                code=code,
                provider=dto.provider,
                language=dto.language,
                expiration_minutes=BotAccountLinkVO.CODE_EXPIRATION_MINUTES,
            ),
        )

    def send_code_by_phone(
        self,
        dto: SendBotAccountLinkCodeDTO,
    ) -> BotAccountLinkDispatchResultDTO:
        user = self.postgres_adapter.find_active_user_by_phone(dto.identifier)
        if not user:
            return BotAccountLinkDispatchResultDTO.account_missing()
        return self._issue_and_dispatch_code(
            dto=dto,
            user=user,
            method=BotAccountLinkMethodVO.PHONE,
            dispatcher=lambda code: self.shared_logic.send_sms(
                KavenegarTemplateSmsDTO(
                    recipient_phone_number=user.phone_number,
                    template_name=KavenegarVo.CONNECT_ACCOUNT,
                    token=code,
                    token2=str(BotAccountLinkVO.CODE_EXPIRATION_MINUTES),
                )
            ),
        )

    def confirm_code(self, dto: ConfirmBotAccountLinkCodeDTO) -> bool:
        session_key = self._session_cache_key(
            provider=dto.provider,
            chat_id=dto.chat_id,
        )
        session = self._load_session(self.cache_repository.get(session_key))
        if not session:
            return False

        code_key = self._code_cache_key(session_key)
        timeout = self._expiration_seconds()
        if not self.verification_code_cache.verify_code(
            cache_key=code_key,
            code=dto.code,
            timeout_seconds=timeout,
        ):
            if not self.verification_code_cache.has_active_code(cache_key=code_key):
                self.cache_repository.delete(session_key)
            return False

        linked = self.postgres_adapter.link_profile(
            provider=dto.provider,
            chat_id=dto.chat_id,
            profile_id=dto.profile_id,
            user_id=str(session.get("user_id") or ""),
            verification_method=str(session.get("method") or ""),
        )
        if not linked:
            # Do not let a valid code be replayed against a different profile.
            self.cache_repository.delete(session_key)
            return False

        self.cache_repository.delete(session_key)
        return True

    def _issue_and_dispatch_code(
        self,
        *,
        dto: SendBotAccountLinkCodeDTO,
        user,
        method: str,
        dispatcher: Callable[[str], Any],
    ) -> BotAccountLinkDispatchResultDTO:
        session_key = self._session_cache_key(
            provider=dto.provider,
            chat_id=dto.chat_id,
        )
        timeout = self._expiration_seconds()
        session = {
            "user_id": str(user.id),
            "method": str(method),
        }
        if not self.cache_repository.add(
            session_key,
            json.dumps(session, ensure_ascii=False),
            timeout=timeout,
        ):
            return BotAccountLinkDispatchResultDTO.active_code()

        code_key = self._code_cache_key(session_key)
        code = self.verification_code_cache.issue_code(
            cache_key=code_key,
            timeout_seconds=timeout,
        )
        if code is None:
            self.cache_repository.delete(session_key)
            return BotAccountLinkDispatchResultDTO.active_code()

        try:
            dispatcher(code)
        except Exception:
            self.cache_repository.delete(session_key)
            self.verification_code_cache.delete_code(cache_key=code_key)
            raise
        return BotAccountLinkDispatchResultDTO.sent()

    @staticmethod
    def _expiration_seconds() -> int:
        return BotAccountLinkVO.CODE_EXPIRATION_MINUTES * 60

    @staticmethod
    def _session_cache_key(*, provider: str, chat_id: str) -> str:
        return BotAccountLinkVO.SESSION_CACHE_KEY_TEMPLATE.format(
            provider=provider,
            chat_id=chat_id,
        )

    @staticmethod
    def _code_cache_key(session_key: str) -> str:
        return f"{session_key}:code"

    @staticmethod
    def _load_session(raw_value: Any) -> dict[str, Any]:
        if not raw_value:
            return {}
        if isinstance(raw_value, dict):
            return raw_value
        try:
            value = json.loads(str(raw_value))
        except (TypeError, ValueError):
            return {}
        return value if isinstance(value, dict) else {}
