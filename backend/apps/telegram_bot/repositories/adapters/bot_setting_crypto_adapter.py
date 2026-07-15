from __future__ import annotations

import base64
import hashlib
from typing import Final

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from backend.apps.common.utils.common_utils import CommonUtils

logger = CommonUtils.get_project_logger(__name__)


class BotSettingCryptoAdapter:
    """Encrypt/decrypt secret runtime settings with a stable application key."""

    PREFIX: Final[str] = "fernet:"

    @classmethod
    def encode(cls, value: str) -> str:
        value = value or ""
        if value == "":
            return ""
        token = cls._fernet().encrypt(value.encode("utf-8")).decode("utf-8")
        return f"{cls.PREFIX}{token}"

    @classmethod
    def decode(cls, value: str) -> str:
        value = value or ""
        if value == "":
            return ""
        if not value.startswith(cls.PREFIX):
            # Backward compatibility for existing rows. Saving the value through
            # the settings API encrypts it. Never write new plaintext secrets.
            logger.warning("A legacy plaintext bot secret was read; rotate and save it again.")
            return value
        token = value[len(cls.PREFIX) :]
        try:
            return cls._fernet().decrypt(token.encode("utf-8")).decode("utf-8")
        except Exception as exc:
            raise ImproperlyConfigured(
                "Unable to decrypt a bot runtime secret. Check ENCRYPTION_KEY/APP_SECRET_KEY."
            ) from exc

    @staticmethod
    def _fernet():
        try:
            from cryptography.fernet import Fernet
        except ImportError as exc:
            raise ImproperlyConfigured(
                "cryptography is required to store bot secrets securely."
            ) from exc

        secret = str(
            getattr(settings, "ENCRYPTION_KEY", "")
            or getattr(settings, "SECRET_KEY", "")
        )
        if not secret:
            raise ImproperlyConfigured(
                "ENCRYPTION_KEY or APP_SECRET_KEY is required for bot secrets."
            )
        digest = hashlib.sha256(secret.encode("utf-8")).digest()
        return Fernet(base64.urlsafe_b64encode(digest))
