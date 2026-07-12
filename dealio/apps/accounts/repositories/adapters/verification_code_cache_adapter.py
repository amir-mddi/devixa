import hashlib
import secrets
from datetime import timedelta

from django.core.cache import cache

from dealio.apps.common.helpers.metaclasses.singleton import Singleton


class VerificationCodeCacheAdapter(metaclass=Singleton):
    CODE_LENGTH = 6
    EXPIRATION_MINUTES = 5
    _MIN_CODE_VALUE = 10 ** (CODE_LENGTH - 1)
    _CODE_RANGE = 9 * _MIN_CODE_VALUE

    @classmethod
    def generate_code(cls) -> str:
        return str(secrets.randbelow(cls._CODE_RANGE) + cls._MIN_CODE_VALUE)

    @staticmethod
    def hash_code(code: str) -> str:
        return hashlib.sha256(code.encode("utf-8")).hexdigest()

    @classmethod
    def expiration_seconds(cls) -> int:
        return int(timedelta(minutes=cls.EXPIRATION_MINUTES).total_seconds())

    def store_code(self, *, cache_key: str, code: str) -> None:
        cache.set(
            cache_key,
            self.hash_code(code),
            timeout=self.expiration_seconds(),
        )

    def issue_code(self, *, cache_key: str) -> str:
        code = self.generate_code()
        self.store_code(cache_key=cache_key, code=code)
        return code

    def verify_code(
        self,
        *,
        cache_key: str,
        code: str,
        consume: bool = True,
    ) -> bool:
        saved_code_hash = cache.get(cache_key)
        if not saved_code_hash:
            return False

        submitted_code_hash = self.hash_code(code)
        if not secrets.compare_digest(saved_code_hash, submitted_code_hash):
            return False

        if consume:
            cache.delete(cache_key)

        return True

    @staticmethod
    def delete_code(*, cache_key: str) -> None:
        cache.delete(cache_key)
