from backend.apps.accounts.repositories.adapters.verification_code_cache_adapter import (
    VerificationCodeCacheAdapter,
)
from backend.apps.core_models.constants.runtime_config import RuntimeConfig


class AccountRepositoryHandler:
    def __init__(self):
        self.runtime_config = RuntimeConfig()
        self.verification_code_cache = VerificationCodeCacheAdapter()

    def generate_password(self) -> str:
        return self.runtime_config.generate_random_password()

    def generate_verification_code(self) -> str:
        return self.verification_code_cache.generate_code()
