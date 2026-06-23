import logging
from threading import Thread

from django.contrib.auth.models import User
from django.utils.timezone import now

from dealio.apps.accounts.repositories.adapters.email_adapter import AccountEmailAdapter
from dealio.apps.accounts.repositories.adapters.kavenegar_adapter import KavenegarSmsAdapter
from dealio.apps.accounts.repositories.adapters.postgres_adapter import PostgresAdapter
from dealio.apps.accounts.repositories.adapters.redis_adapter import RedisAdapter
from dealio.apps.common.helpers.metaclasses.singleton import Singleton
from dealio.apps.core_models.vo.common_vo import KavenegarVo

logger = logging.getLogger("dealio")


class AccountLogicRepository(metaclass=Singleton):
    def __init__(self):
        self.postgres_adapter = PostgresAdapter()
        self.redis_adapter = RedisAdapter()
        self.kavenegar_sms = KavenegarSmsAdapter()
        self.gmail_adapter = AccountEmailAdapter()

    def send_verification_email_code(self, user: User):
        self.gmail_adapter.send_email_verification_code(user)

    def send_verification_forget_password_code(self, user: User):
        self.gmail_adapter.send_forget_password_verification_code(user)

    def check_email_validation_code(self, user: User, code: str):
        return self.gmail_adapter.verify_email_code(user, code)

    def check_forget_password_code(self, user: User, code: str):
        return self.gmail_adapter.verify_forget_password_code(user, code)

    def update_user_role(self, id, user):
        role = self.postgres_adapter.fetch_role_base_id(id)
        user.role = role
        user.save()

    def update_user_verification(self, verification_code, phone_number):
        user = self.postgres_adapter.fetch_user_base_phone_number(phone_number)
        user.verification_code = verification_code
        user.created_verified = now()
        user.save()

    def send_sms_kavenegar(self, recipient_phone_number, template_name, first_value=None, second_value=None):
        self.kavenegar_sms.send_sms(
            receptor=recipient_phone_number,
            value_first=first_value,
            value_second=second_value,
            template=template_name
        )

    def send_change_password_in_separate_thread(self, phone_number, password, username):
        try:
            thread = Thread(
                target=self.send_sms_kavenegar,
                args=(
                    phone_number,
                    KavenegarVo.change_password,
                    password,
                    username,
                )
            )
            thread.start()
        except Exception as e:
            logger.info("Exception while sending sms kavenegar: ", str(e))

    def send_sms_recovery_password_in_separate_thread(self, phone_number, password, username):
        try:
            thread = Thread(
                target=self.send_sms_kavenegar,
                args=(
                    phone_number,
                    KavenegarVo.password_recovery,
                    password,
                    username,
                )
            )
            thread.start()
        except Exception as e:
            logger.info("Exception while sending sms kavenegar: ", str(e))

    def send_sms_create_user_in_separate_thread(self, phone_number, password, username):
        try:
            thread = Thread(
                target=self.send_sms_kavenegar,
                args=(
                    phone_number,
                    KavenegarVo.create_account,
                    password,
                    username,
                )
            )
            thread.start()
        except Exception as e:
            logger.info("Exception while sending sms kavenegar: ", str(e))

    def send_sms_verification_code_in_separate_thread(self, phone_number, verification_code):
        try:
            thread = Thread(
                target=self.send_sms_kavenegar,
                # args=(
                #     phone_number,
                #     KavenegarVo.verification_code,
                #     verification_code,
                # )
                args=(
                    phone_number,
                    KavenegarVo.create_account,
                    verification_code,
                    "Verification_code",
                )
            )
            thread.start()
        except Exception as e:
            logger.info("Exception while sending sms kavenegar: ", str(e))
