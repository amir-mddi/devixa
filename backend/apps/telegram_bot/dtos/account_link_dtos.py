from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SendBotAccountLinkCodeDTO:
    provider: str
    chat_id: str
    identifier: str
    language: str


@dataclass(frozen=True, slots=True)
class ConfirmBotAccountLinkCodeDTO:
    provider: str
    chat_id: str
    profile_id: int
    code: str


@dataclass(frozen=True, slots=True)
class BotAccountLinkDispatchResultDTO:
    account_found: bool
    code_issued: bool

    @classmethod
    def account_missing(cls) -> "BotAccountLinkDispatchResultDTO":
        return cls(account_found=False, code_issued=False)

    @classmethod
    def active_code(cls) -> "BotAccountLinkDispatchResultDTO":
        return cls(account_found=True, code_issued=False)

    @classmethod
    def sent(cls) -> "BotAccountLinkDispatchResultDTO":
        return cls(account_found=True, code_issued=True)
