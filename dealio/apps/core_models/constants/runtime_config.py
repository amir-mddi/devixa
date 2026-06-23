import random

from dealio.apps.core_models.constants.kavenegar import KavenegarConfig


class RuntimeConfig(KavenegarConfig):
    password_generator_length: int = 8
    password_generator_rules_str: str = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"
    password_generator_rules_num: int = "0123456789"

    def generate_random_password(self):
        password = ""
        for _ in range(4):
            password += random.choice(self.password_generator_rules_str)
            password += random.choice(self.password_generator_rules_num)

        return password

    def generate_verification_code(self):
        verification_code = ""
        for _ in range(6):
            verification_code += random.choice(self.password_generator_rules_num)
        return verification_code
