from __future__ import annotations


class SentryTagVO:
    COMPONENT = "component"
    OPERATION = "operation"
    EXPECTED = "expected"
    TEST_EVENT = "sentry_test"


class SentryComponentVO:
    DJANGO = "django"
    CELERY = "celery"
    TELEGRAM = "telegram"
    PAYMENT = "payment"
    EXTERNAL_API = "external_api"
    MANAGEMENT_COMMAND = "management_command"


class SentryContextVO:
    EXTRA = "extra"


class SentrySensitiveFieldVO:
    """Field names that must be removed recursively from Sentry payloads."""

    DEFAULT_DENYLIST = (
        "password",
        "password1",
        "password2",
        "old_password",
        "new_password",
        "new_password1",
        "new_password2",
        "token",
        "access_token",
        "refresh_token",
        "authorization",
        "proxy_authorization",
        "cookie",
        "set_cookie",
        "sessionid",
        "csrftoken",
        "api_key",
        "secret",
        "secret_key",
        "client_secret",
        "telegram_bot_token",
        "bale_bot_token",
        "kavenegar_api_key",
        "openai_api_key",
        "card_number",
        "cvv2",
        "pin",
        "otp",
        "verification_code",
    )
