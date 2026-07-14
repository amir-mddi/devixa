"""Deprecated compatibility constants.

Use Django settings and `dealio.apps.accounts.vo.recaptcha_vo` for new code.
"""

from django.conf import settings

from dealio.apps.accounts.vo.recaptcha_vo import RecaptchaEndpointVO


class RecaptchaConfig:
    risk_score = settings.RECAPTCHA_MIN_SCORE
    secret_key = settings.RECAPTCHA_SECRET_KEY
    request_url = RecaptchaEndpointVO.SITE_VERIFY.value
