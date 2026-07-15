import secrets
import string

from backend.apps.core_models.constants.kavenegar import KavenegarConfig


class RuntimeConfig(KavenegarConfig):
    """Runtime-safe generators used by account workflows.

    Security-sensitive values must come from ``secrets`` rather than the
    deterministic pseudo-random generator from ``random``.
    """

    password_generator_length: int = 12
    password_generator_rules_str: str = (
        "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"
    )
    password_generator_rules_num: str = string.digits

    def generate_random_password(self) -> str:
        # Guarantee both character classes, then securely shuffle the result.
        letters = [
            secrets.choice(self.password_generator_rules_str)
            for _ in range(self.password_generator_length - 3)
        ]
        digits = [secrets.choice(self.password_generator_rules_num) for _ in range(3)]
        characters = letters + digits
        secrets.SystemRandom().shuffle(characters)
        return "".join(characters)

    def generate_verification_code(self) -> str:
        return "".join(
            secrets.choice(self.password_generator_rules_num)
            for _ in range(6)
        )
