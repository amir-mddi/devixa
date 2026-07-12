from django.conf import settings


class KavenegarConfig:
    API_KEY: str = settings.KAVENEGAR_API_KEY
    base_url: str = "https://api.kavenegar.com/v1/{API_KEY}/verify/lookup.json"
