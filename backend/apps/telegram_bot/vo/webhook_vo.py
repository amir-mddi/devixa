from __future__ import annotations

from enum import StrEnum


class BotWebhookResponseKeyVO(StrEnum):
    OK = "ok"
    DETAIL = "detail"
    PROCESSED = "processed"


class BotWebhookMessageVO(StrEnum):
    BOT_NOT_CONFIGURED = "Bot is not configured"
    WEBHOOK_READY = "Webhook endpoint is ready"
    FORBIDDEN = "Forbidden"
    INVALID_UPDATE = "Invalid update"
    UPDATE_PROCESSING_FAILED = "Update processing failed"
    NOT_FOUND = "Not found"
    TELEGRAM_NOT_CONFIGURED = "Telegram bot token is not configured"
    TELEGRAM_READY = "Telegram webhook endpoint is ready"
    BALE_NOT_CONFIGURED = "Bale bot token/base URL is not configured"
    BALE_READY = "Bale webhook endpoint is ready"
    RUBIKA_NOT_CONFIGURED = "Rubika bot token/base URL is not configured"
    RUBIKA_READY = "Rubika webhook endpoint is ready"


class BotWebhookHeaderVO(StrEnum):
    TELEGRAM_SECRET = "X-Telegram-Bot-Api-Secret-Token"
    BALE_SECRET = "X-Bale-Bot-Api-Secret-Token"
    RUBIKA_SECRET = "X-Rubika-Bot-Api-Secret-Token"
    GENERIC_SECRET = "X-Bot-Api-Secret-Token"


class BotWebhookEnvironmentVO(StrEnum):
    TELEGRAM_SECRET = "TELEGRAM_WEBHOOK_SECRET"
    BALE_SECRET = "BALE_WEBHOOK_SECRET"
    RUBIKA_SECRET = "RUBIKA_WEBHOOK_SECRET"
