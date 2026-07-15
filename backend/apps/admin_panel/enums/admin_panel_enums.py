from enum import StrEnum


class AdminPanelSectionEnum(StrEnum):
    DASHBOARD = "dashboard"
    TICKETS = "tickets"
    REVIEWS = "reviews"
    BILLING = "billing"
    USERS = "users"
    COURSES = "courses"
    ARTICLES = "articles"
    DISCOUNTS = "discounts"
    NOTIFICATIONS = "notifications"
    BOT_SETTINGS = "bot_settings"


class AdminPanelUserActionEnum(StrEnum):
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"


class AdminPanelReceiptActionEnum(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"


class AdminPanelTicketActionEnum(StrEnum):
    REPLY = "reply"
    CLOSE = "close"
