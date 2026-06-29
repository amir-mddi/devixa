from enum import Enum


class TelegramPaymentProviderEnum(str, Enum):
    MANUAL = "manual"
    SANDBOX = "sandbox"


class TelegramReviewModerationActionEnum(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
