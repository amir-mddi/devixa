import os


class RecaptchaConfig:
    risk_score = 0.3
    secret_key = os.environ.get('RECAPTCHA_SECRET_KEY', None)
    request_url = 'https://www.google.com/recaptcha/api/siteverify'
