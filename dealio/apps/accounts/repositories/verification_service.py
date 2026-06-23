import hashlib
import secrets
from datetime import datetime

from django.core.cache import cache

from dealio.apps.common.email_service import send_html_email

VERIFICATION_CODE_TIMEOUT_SECONDS = 300
VERIFICATION_CODE_EXPIRATION_MINUTES = VERIFICATION_CODE_TIMEOUT_SECONDS // 60





def send_email_verification_code(user) -> None:
    code = generate_verification_code()

    cache.set(
        get_email_verification_cache_key(str(user.id)),
        hash_code(code),
        timeout=VERIFICATION_CODE_TIMEOUT_SECONDS,
    )

    send_html_email(
        subject="اعتباری سنجی ایمیل",
        template_name="emails/fa_verification_code.html",
        context={
            "subject": "کد اعتبار سنجی ایمیل شما",
            "app_name": "Devixa",
            "user_name": user.first_name or user.username or "there",
            "code": code,
            "expiration_minutes": VERIFICATION_CODE_EXPIRATION_MINUTES,
            "current_year": datetime.now().year,
        },
        recipient_list=[user.email],
    )
