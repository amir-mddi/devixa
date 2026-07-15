import secrets
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.utils.crypto import salted_hmac

from backend.apps.common.helpers.metaclasses.singleton import Singleton


class VerificationCodeCacheAdapter(metaclass=Singleton):
    """Cache-backed one-time-code storage.

    Codes are protected with a keyed digest, issuance is atomic, verification is
    attempt-limited, and successful consumption is guarded by a short cache lock
    so the same code cannot be used concurrently by two workers.
    """

    CODE_LENGTH = 6
    EXPIRATION_MINUTES = 5
    _MIN_CODE_VALUE = 10 ** (CODE_LENGTH - 1)
    _CODE_RANGE = 9 * _MIN_CODE_VALUE
    _HMAC_SALT = "backend.verification-code.v2"
    _IDENTIFIER_SALT = "backend.verification-identifier.v1"
    _VERIFY_LOCK_SECONDS = 10

    @classmethod
    def generate_code(cls) -> str:
        return str(secrets.randbelow(cls._CODE_RANGE) + cls._MIN_CODE_VALUE)

    @classmethod
    def hash_code(cls, code: str) -> str:
        """Use a keyed digest so a cache leak cannot be brute-forced offline."""
        return salted_hmac(
            cls._HMAC_SALT,
            str(code),
            secret=settings.SECRET_KEY,
            algorithm="sha256",
        ).hexdigest()

    @classmethod
    def fingerprint_identifier(cls, value: str) -> str:
        """Return a non-reversible cache-key fragment for email/phone values."""
        normalized = str(value or "").strip().lower()
        return salted_hmac(
            cls._IDENTIFIER_SALT,
            normalized,
            secret=settings.SECRET_KEY,
            algorithm="sha256",
        ).hexdigest()[:24]

    @classmethod
    def expiration_seconds(cls) -> int:
        return int(timedelta(minutes=cls.EXPIRATION_MINUTES).total_seconds())

    @staticmethod
    def _attempts_key(cache_key: str) -> str:
        return f"{cache_key}:attempts"

    @staticmethod
    def _lock_key(cache_key: str) -> str:
        return f"{cache_key}:verify-lock"

    @staticmethod
    def max_attempts() -> int:
        return max(1, int(getattr(settings, "VERIFICATION_CODE_MAX_ATTEMPTS", 5)))

    def store_code(
        self,
        *,
        cache_key: str,
        code: str,
        timeout_seconds: int | None = None,
    ) -> None:
        timeout = timeout_seconds or self.expiration_seconds()
        cache.set(cache_key, self.hash_code(code), timeout=timeout)
        cache.delete_many([
            self._attempts_key(cache_key),
            self._lock_key(cache_key),
        ])

    def store_code_if_absent(
        self,
        *,
        cache_key: str,
        code: str,
        timeout_seconds: int | None = None,
    ) -> bool:
        timeout = timeout_seconds or self.expiration_seconds()
        added = cache.add(cache_key, self.hash_code(code), timeout=timeout)
        if added:
            cache.delete_many([
                self._attempts_key(cache_key),
                self._lock_key(cache_key),
            ])
        return added

    def issue_code(
        self,
        *,
        cache_key: str,
        timeout_seconds: int | None = None,
    ) -> str | None:
        code = self.generate_code()
        return (
            code
            if self.store_code_if_absent(
                cache_key=cache_key,
                code=code,
                timeout_seconds=timeout_seconds,
            )
            else None
        )

    @staticmethod
    def has_active_code(*, cache_key: str) -> bool:
        return cache.get(cache_key) is not None

    def verify_code(
        self,
        *,
        cache_key: str,
        code: str,
        consume: bool = True,
        timeout_seconds: int | None = None,
    ) -> bool:
        lock_key = self._lock_key(cache_key)
        if not cache.add(lock_key, "1", timeout=self._VERIFY_LOCK_SECONDS):
            return False

        try:
            saved_code_hash = cache.get(cache_key)
            if not saved_code_hash:
                return False

            submitted_code_hash = self.hash_code(code)
            if not secrets.compare_digest(str(saved_code_hash), submitted_code_hash):
                self._record_failed_attempt(cache_key, timeout_seconds=timeout_seconds)
                return False

            cache.delete(self._attempts_key(cache_key))
            if consume:
                cache.delete(cache_key)
            return True
        finally:
            cache.delete(lock_key)

    def _record_failed_attempt(
        self,
        cache_key: str,
        *,
        timeout_seconds: int | None = None,
    ) -> None:
        attempts_key = self._attempts_key(cache_key)
        timeout = timeout_seconds or self.expiration_seconds()
        if cache.add(attempts_key, 1, timeout=timeout):
            attempts = 1
        else:
            try:
                attempts = cache.incr(attempts_key)
            except ValueError:
                cache.set(attempts_key, 1, timeout=timeout)
                attempts = 1

        if attempts >= self.max_attempts():
            self.delete_code(cache_key=cache_key)

    @classmethod
    def delete_code(cls, *, cache_key: str) -> None:
        cache.delete_many([
            cache_key,
            cls._attempts_key(cache_key),
            cls._lock_key(cache_key),
        ])
