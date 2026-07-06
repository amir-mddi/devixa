from __future__ import annotations

import base64
import hashlib
from dealio.apps.common.utils.common_utils import CommonUtils
from typing import Final

from django.conf import settings

logger = CommonUtils.get_project_logger(__name__)


class BotSettingCryptoAdapter:
    """Small reversible encoder for secret runtime settings.

    Values are encrypted when the optional cryptography dependency is available.
    If it is not available, the app still works and stores the value as plain text.
    """

    PREFIX: Final[str] = "fernet:"

    @classmethod
    def encode(cls, value: str) -> str:
        value = value or ""
        if value == "":
            return ""
        fernet = cls._fernet()
        if fernet is None:
            return value
        token = fernet.encrypt(value.encode("utf-8")).decode("utf-8")
        return f"{cls.PREFIX}{token}"

    @classmethod
    def decode(cls, value: str) -> str:
        value = value or ""
        if not value.startswith(cls.PREFIX):
            return value
        fernet = cls._fernet()
        if fernet is None:
            return ""
        token = value[len(cls.PREFIX) :]
        try:
            return fernet.decrypt(token.encode("utf-8")).decode("utf-8")
        except Exception:
            logger.exception("Failed to decrypt bot runtime setting.")
            return ""

    @staticmethod
    def _fernet():
        try:
            from cryptography.fernet import Fernet
        except Exception:
            return None

        secret = str(getattr(settings, "SECRET_KEY", "") or "dealio-bot-settings")
        digest = hashlib.sha256(secret.encode("utf-8")).digest()
        key = base64.urlsafe_b64encode(digest)
        return Fernet(key)
