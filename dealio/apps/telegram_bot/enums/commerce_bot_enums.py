from enum import Enum


class TelegramPaymentProviderEnum(str, Enum):
    MANUAL = "manual"
    CARD_TO_CARD = "card_to_card"
    PARDAKHTYAR = "pardakhtyar"
    SANDBOX = "sandbox"


class TelegramReviewModerationActionEnum(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
