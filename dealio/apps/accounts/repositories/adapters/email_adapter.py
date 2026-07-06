import hashlib
import secrets
from datetime import datetime, timedelta

from dealio.apps.common.email_service import send_html_email, send_html_email_async
from dealio.apps.common.project_config import get_project_name
from dealio.apps.common.helpers.metaclasses.singleton import Singleton
from django.core.cache import cache


class AccountEmailAdapter(metaclass=Singleton):
    VERIFICATION_CODE_EXPIRATION_MINUTES = 5


    @staticmethod
    def generate_verification_code() -> str:
        return str(secrets.randbelow(900000) + 100000)

    @staticmethod
    def hash_code(code: str) -> str:
        return hashlib.sha256(code.encode("utf-8")).hexdigest()

    @staticmethod
    def get_email_verification_cache_key(user_id: str) -> str:
        return f"email_verification:{user_id}"

    @staticmethod
    def get_forget_password_verification_cache_key(user_id: str) -> str:
        return f"forget_password_verification:{user_id}"

    def send_email_verification_code(self, user) -> None:
        code = self.generate_verification_code()

        cache.set(
            self.get_email_verification_cache_key(str(user.id)),
            self.hash_code(code),
            timeout=timedelta(minutes=self.VERIFICATION_CODE_EXPIRATION_MINUTES).total_seconds(),
        )

        send_html_email_async(
            subject="اعتباری سنجی ایمیل",
            template_name="emails/fa_verification_code.html",
            context={
                "subject": "کد اعتبار سنجی ایمیل شما",
                "app_name": get_project_name(),
                "user_name": user.first_name or user.username or "there",
                "code": code,
                "expiration_minutes": self.VERIFICATION_CODE_EXPIRATION_MINUTES,
                "current_year": datetime.now().year,
            },
            recipient_list=[user.email],
        )

    def send_forget_password_verification_code(self, user) -> None:
        code = self.generate_verification_code()
        cache.set(
            self.get_forget_password_verification_cache_key(str(user.id)),
            self.hash_code(code),
            timeout=timedelta(minutes=self.VERIFICATION_CODE_EXPIRATION_MINUTES).total_seconds(),
        )

        send_html_email_async(
            subject="اعتباری سنجی رمز عبور",
            template_name="emails/fa_forgot_password.html",
            context={
                "subject": "کد اعتبار سنجی فراموشی رمز عبور",
                "app_name": get_project_name(),
                "user_name": user.first_name or user.username or "there",
                "code": code,
                "expiration_minutes": self.VERIFICATION_CODE_EXPIRATION_MINUTES,
                "current_year": datetime.now().year,
            },
            recipient_list=[user.email],
        )

    def check_code(self, user, cache_key, code, *, mark_email_verified: bool = False):
        saved_code_hash = cache.get(cache_key)

        if not saved_code_hash:
            return False

        if saved_code_hash != self.hash_code(code):
            return False

        cache.delete(cache_key)

        if mark_email_verified:
            user.email_verified = True
            user.save(update_fields=["email_verified"])

        return True

    def verify_email_code(self, user, code: str) -> bool:
        cache_key = self.get_email_verification_cache_key(str(user.id))
        return self.check_code(user, cache_key, code, mark_email_verified=True)

    def verify_forget_password_code(self, user, code: str) -> bool:
        cache_key = self.get_forget_password_verification_cache_key(str(user.id))
        return self.check_code(user, cache_key, code)
