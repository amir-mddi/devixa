from datetime import datetime

from dealio.apps.accounts.repositories.adapters.verification_code_cache_adapter import (
    VerificationCodeCacheAdapter,
)
from dealio.apps.common.email_service import send_html_email_async
from dealio.apps.common.helpers.metaclasses.singleton import Singleton
from dealio.apps.common.project_config import get_project_name


class AccountEmailAdapter(metaclass=Singleton):
    VERIFICATION_CODE_EXPIRATION_MINUTES = VerificationCodeCacheAdapter.EXPIRATION_MINUTES

    def __init__(self):
        self.verification_code_cache = VerificationCodeCacheAdapter()

    @staticmethod
    def generate_verification_code() -> str:
        return VerificationCodeCacheAdapter.generate_code()

    @staticmethod
    def hash_code(code: str) -> str:
        return VerificationCodeCacheAdapter.hash_code(code)

    @staticmethod
    def get_email_verification_cache_key(user_id: str, email: str) -> str:
        fingerprint = VerificationCodeCacheAdapter.fingerprint_identifier(email)
        return f"email_verification:{user_id}:{fingerprint}"

    @staticmethod
    def get_forget_password_verification_cache_key(user_id: str, email: str) -> str:
        fingerprint = VerificationCodeCacheAdapter.fingerprint_identifier(email)
        return f"forget_password_verification:{user_id}:{fingerprint}"

    def send_email_verification_code(self, user) -> bool:
        return self._send_code_email(
            user=user,
            cache_key=self.get_email_verification_cache_key(str(user.id), user.email),
            subject="اعتباری سنجی ایمیل",
            template_name="emails/fa_verification_code.html",
            context_subject="کد اعتبار سنجی ایمیل شما",
        )

    def send_forget_password_verification_code(self, user) -> bool:
        return self._send_code_email(
            user=user,
            cache_key=self.get_forget_password_verification_cache_key(str(user.id), user.email),
            subject="اعتباری سنجی رمز عبور",
            template_name="emails/fa_forgot_password.html",
            context_subject="کد اعتبار سنجی فراموشی رمز عبور",
        )

    def _send_code_email(
        self,
        *,
        user,
        cache_key: str,
        subject: str,
        template_name: str,
        context_subject: str,
    ) -> bool:
        code = self.generate_verification_code()
        if not self.verification_code_cache.store_code_if_absent(
            cache_key=cache_key,
            code=code,
        ):
            return False

        send_html_email_async(
            subject=subject,
            template_name=template_name,
            context={
                "subject": context_subject,
                "app_name": get_project_name(),
                "user_name": user.first_name or user.username or "there",
                "code": code,
                "expiration_minutes": self.VERIFICATION_CODE_EXPIRATION_MINUTES,
                "current_year": datetime.now().year,
            },
            recipient_list=[user.email],
        )
        return True

    def check_code(
        self,
        user,
        cache_key: str,
        code: str,
        *,
        mark_email_verified: bool = False,
    ) -> bool:
        is_valid = self.verification_code_cache.verify_code(
            cache_key=cache_key,
            code=code,
        )
        if not is_valid:
            return False

        if mark_email_verified:
            user.email_verified = True
            user.save(update_fields=["email_verified"])

        return True

    def verify_email_code(self, user, code: str) -> bool:
        cache_key = self.get_email_verification_cache_key(str(user.id), user.email)
        return self.check_code(user, cache_key, code, mark_email_verified=True)

    def verify_forget_password_code(self, user, code: str) -> bool:
        cache_key = self.get_forget_password_verification_cache_key(str(user.id), user.email)
        return self.check_code(user, cache_key, code)
